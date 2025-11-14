"""
HKMA 數據適配器
Sprint 1 - US-004

實現香港金管局(HKMA)HIBOR利率數據的獲取和處理。
支持5個HIBOR指標：隔夜、1個月、3個月、6個月、12個月。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pandas import DataFrame, date_range
import pandas as pd

from src.core.interfaces.data_adapter import IHKMAAdapter, DataValidationError
from .base_data_adapter import BaseDataAdapter


logger = logging.getLogger(__name__)


class HKMAdapter(BaseDataAdapter, IHKMAAdapter):
    """
    HKMA 數據適配器

    獲取香港金管局 HIBOR 利率數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # HIBOR 指標列表
    HIBOR_TERMS = {
        'hibor_overnight': '隔夜',
        'hibor_1m': '1個月',
        'hibor_3m': '3個月',
        'hibor_6m': '6個月',
        'hibor_12m': '12個月'
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 HKMA 適配器

        Args:
            config: 配置參數
                - use_mock_data: 是否使用模擬數據 (默認: True)
                - data_source_url: 真實數據源URL
                - api_key: API密鑰（如需要）
                - update_interval: 更新間隔（秒）
        """
        super().__init__(config)

        # 配置參數
        self.use_mock_data = self.config.get('use_mock_data', True)
        self.data_source_url = self.config.get('data_source_url', 'https://api.hkma.gov.hk')
        self.update_interval = self.config.get('update_interval', 3600)  # 1小時

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化 HKMA 適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_hibor_overnight(self) -> float:
        """
        獲取隔夜 HIBOR 利率

        Returns:
            float: 隔夜 HIBOR 利率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_hibor_indicators()
        rate = data.get('hibor_overnight')

        if rate is None:
            raise ValueError("無法獲取隔夜 HIBOR 利率")

        logger.info(f"獲取隔夜 HIBOR: {rate:.4f}%")
        return rate

    async def fetch_hibor_terms(self) -> Dict[str, float]:
        """
        獲取 1m, 3m, 6m, 12m HIBOR 利率

        Returns:
            Dict[str, float]: 期限利率字典，鍵為指標名，值為利率(%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_hibor_indicators()

        # 提取期限利率
        terms_data = {
            'hibor_1m': data.get('hibor_1m'),
            'hibor_3m': data.get('hibor_3m'),
            'hibor_6m': data.get('hibor_6m'),
            'hibor_12m': data.get('hibor_12m')
        }

        # 檢查是否有缺失值
        missing = [k for k, v in terms_data.items() if v is None]
        if missing:
            raise ValueError(f"缺少期限利率數據: {missing}")

        logger.info(f"獲取 HIBOR 期限利率: {terms_data}")
        return terms_data

    async def fetch_all_hibor_indicators(self) -> Dict[str, float]:
        """
        獲取全部 5 個 HIBOR 指標

        Returns:
            Dict[str, float]: 指標字典，包含隔夜、1m、3m、6m、12m

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的 HIBOR 數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_hibor_data()
            else:
                data = await self._fetch_real_hibor_data()

            # 驗證數據
            await self._validate_hibor_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取 HIBOR 指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取 HIBOR 數據失敗: {e}")
            raise

    async def get_historical_hibor(self, days: int = 365) -> DataFrame:
        """
        獲取歷史 HIBOR 數據

        Args:
            days: 天數

        Returns:
            DataFrame: 歷史數據，包含日期和各期限利率

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"獲取 {days} 天歷史 HIBOR 數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍
        dates = date_range(start=start_date, end=end_date, freq='D')

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 跳過週末（非工作日）
            if date.weekday() >= 5:  # 5=週六, 6=週日
                continue

            # 生成該日期的 HIBOR 數據
            day_data = await self._generate_daily_hibor(date)
            day_data['date'] = date
            historical_data.append(day_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.HIBOR_TERMS.keys()))

        self._log_data_info(df, "獲取歷史 HIBOR 數據")
        return df

    # ==================== 實現 IDataAdapter 接口 ====================

    async def _fetch_data_impl(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> DataFrame:
        """
        獲取歷史數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            start_date: 開始日期
            end_date: 結束日期
            **kwargs: 其他參數

        Returns:
            DataFrame: HIBOR 歷史數據
        """
        # 計算天數
        if start_date and end_date:
            days = (end_date - start_date).days
        else:
            days = kwargs.get('days', 365)

        return await self.get_historical_hibor(days=days)

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時 HIBOR 數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時 HIBOR 數據
        """
        data = await self.fetch_all_hibor_indicators()

        # 添加時間戳
        result = {
            'timestamp': datetime.now(),
            'indicators': data,
            'data_source': self.data_source,
            'adapter': self.name
        }

        return result

    async def _get_required_columns(self) -> List[str]:
        """
        獲取必需的列名

        Returns:
            List[str]: 必需的列名列表
        """
        return list(self.HIBOR_TERMS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義 HIBOR 數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查 HIBOR 數值的合理性
        for term, name in self.HIBOR_TERMS.items():
            if term in data.columns:
                values = data[term].dropna()

                if len(values) > 0:
                    # 檢查是否為負值（HIKBOR不應該是負的）
                    negative_count = (values < 0).sum()
                    if negative_count > 0:
                        raise DataValidationError(
                            f"{name} 利率存在負值: {negative_count} 個"
                        )

                    # 檢查是否過高（> 20%）
                    high_count = (values > 20).sum()
                    if high_count > 0:
                        logger.warning(
                            f"{name} 利率過高 (>20%): {high_count} 個"
                        )

                    # 檢查異常值
                    if len(values) > 10:
                        q1 = values.quantile(0.25)
                        q3 = values.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 3 * iqr
                        upper_bound = q3 + 3 * iqr

                        outliers = values[(values < lower_bound) | (values > upper_bound)]
                        if len(outliers) > len(values) * 0.05:  # 超過5%異常值
                            logger.warning(
                                f"{name} 異常值較多: {len(outliers)}/{len(values)}"
                            )

    # ==================== 私有方法 ====================

    async def _fetch_mock_hibor_data(self) -> Dict[str, float]:
        """
        獲取模擬 HIBOR 數據

        Returns:
            Dict[str, float]: HIBOR 數據字典
        """
        # 模擬 HIBOR 利率（基於當前市場利率水平）
        base_rates = {
            'hibor_overnight': 3.65,
            'hibor_1m': 3.70,
            'hibor_3m': 3.75,
            'hibor_6m': 3.85,
            'hibor_12m': 4.00
        }

        # 添加隨機波動
        import random
        data = {}
        for term, rate in base_rates.items():
            # ±0.1% 的隨機波動
            fluctuation = random.uniform(-0.1, 0.1)
            data[term] = round(rate + fluctuation, 4)

        logger.debug(f"生成模擬 HIBOR 數據: {data}")
        return data

    async def _fetch_real_hibor_data(self) -> Dict[str, float]:
        """
        獲取真實 HIBOR 數據

        Returns:
            Dict[str, float]: HIBOR 數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的 HKMA API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_hibor_data(self, data: Dict[str, float]) -> None:
        """
        驗證 HIBOR 數據

        Args:
            data: HIBOR 數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_terms = set(self.HIBOR_TERMS.keys()) - set(data.keys())
        if missing_terms:
            raise DataValidationError(f"缺少 HIBOR 指標: {missing_terms}")

        # 檢查數值是否為數字
        for term, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{term} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if any(v < 0 for v in data.values()):
            raise DataValidationError("HIBOR 利率不能為負數")

        if any(v > 50 for v in data.values()):
            raise DataValidationError("HIBOR 利率異常高 (>50%)")

    def _is_cache_valid(self) -> bool:
        """
        檢查緩存是否有效

        Returns:
            bool: 緩存是否有效
        """
        if not self._cached_data or not self._last_update:
            return False

        age = (datetime.now() - self._last_update).total_seconds()
        return age < self.update_interval

    async def _generate_daily_hibor(self, date: datetime) -> Dict[str, float]:
        """
        生成單日 HIBOR 數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 單日 HIBOR 數據
        """
        # 基於期限的基準利率
        base_rates = {
            'hibor_overnight': 3.65,
            'hibor_1m': 3.70,
            'hibor_3m': 3.75,
            'hibor_6m': 3.85,
            'hibor_12m': 4.00
        }

        # 根據日期生成小幅波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))  # 使用日期作為隨機種子

        daily_data = {}
        for term, rate in base_rates.items():
            # 基於正態分佈的小幅波動
            fluctuation = random.normalvariate(0, 0.05)  # 標準差0.05%
            daily_data[term] = round(rate + fluctuation, 4)

        return daily_data
