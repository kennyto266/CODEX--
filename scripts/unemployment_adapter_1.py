"""
失業率數據適配器
Sprint 3 - US-011

實現香港失業率相關數據的獲取和處理。
支持3個失業率指標：失業率、就業率、勞動參與率。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pandas import DataFrame, date_range
import pandas as pd

from src.core.interfaces.data_adapter import IDataAdapter, DataValidationError
from .base_data_adapter import BaseDataAdapter


logger = logging.getLogger(__name__)


class UnemploymentAdapter(BaseDataAdapter, IDataAdapter):
    """
    失業率數據適配器

    獲取香港失業率相關數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 失業率指標列表
    UNEMPLOYMENT_INDICATORS = {
        'unemployment_rate': '失業率',
        'employment_rate': '就業率',
        'labor_participation_rate': '勞動參與率',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化失業率適配器

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
        self.data_source_url = self.config.get('data_source_url', 'https://www.censtatd.gov.hk')
        self.update_interval = self.config.get('update_interval', 86400)  # 24小時

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化失業率適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_unemployment_rate(self) -> float:
        """
        獲取失業率

        Returns:
            float: 失業率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_unemployment_indicators()
        rate = data.get('unemployment_rate')

        if rate is None:
            raise ValueError("無法獲取失業率")

        logger.info(f"獲取失業率: {rate:.2f}%")
        return rate

    async def fetch_employment_rate(self) -> float:
        """
        獲取就業率

        Returns:
            float: 就業率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_unemployment_indicators()
        rate = data.get('employment_rate')

        if rate is None:
            raise ValueError("無法獲取就業率")

        logger.info(f"獲取就業率: {rate:.2f}%")
        return rate

    async def fetch_labor_participation_rate(self) -> float:
        """
        獲取勞動參與率

        Returns:
            float: 勞動參與率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_unemployment_indicators()
        rate = data.get('labor_participation_rate')

        if rate is None:
            raise ValueError("無法獲取勞動參與率")

        logger.info(f"獲取勞動參與率: {rate:.2f}%")
        return rate

    async def fetch_all_unemployment_indicators(self) -> Dict[str, float]:
        """
        獲取全部3個失業率指標

        Returns:
            Dict[str, float]: 失業率指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的失業率數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_unemployment_data()
            else:
                data = await self._fetch_real_unemployment_data()

            # 驗證數據
            await self._validate_unemployment_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取失業率指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取失業率數據失敗: {e}")
            raise

    async def get_historical_unemployment(self, years: int = 5) -> DataFrame:
        """
        獲取歷史失業率數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項失業率指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史失業率數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的失業率數據
            monthly_data = await self._generate_monthly_unemployment(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.UNEMPLOYMENT_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史失業率數據")
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
            DataFrame: 失業率歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_unemployment(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時失業率數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時失業率數據
        """
        data = await self.fetch_all_unemployment_indicators()

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
        return list(self.UNEMPLOYMENT_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義失業率數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查失業率數值的合理性
        for indicator, name in self.UNEMPLOYMENT_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值
                    negative_count = (values < 0).sum()
                    if negative_count > 0:
                        raise DataValidationError(
                            f"{name} 存在負值: {negative_count} 個"
                        )

                    # 檢查失業率是否過高（超過20%認為異常）
                    if indicator == 'unemployment_rate':
                        high_count = (values > 20.0).sum()
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>20%): {high_count} 個"
                            )

                    # 檢查就業率是否過低（低於50%認為異常）
                    elif indicator == 'employment_rate':
                        low_count = (values < 50.0).sum()
                        if low_count > 0:
                            logger.warning(
                                f"{name} 過低 (<50%): {low_count} 個"
                            )

                    # 檢查勞動參與率是否合理（低於40%或高於80%認為異常）
                    elif indicator == 'labor_participation_rate':
                        abnormal_count = ((values < 40.0) | (values > 80.0)).sum()
                        if abnormal_count > 0:
                            logger.warning(
                                f"{name} 異常 (<40% 或 >80%): {abnormal_count} 個"
                            )

                    # 檢查異常值
                    if len(values) > 12:  # 至少有12個月的數據
                        q1 = values.quantile(0.25)
                        q3 = values.quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 3 * iqr
                        upper_bound = q3 + 3 * iqr

                        outliers = values[(values < lower_bound) | (values > upper_bound)]
                        if len(outliers) > len(values) * 0.1:  # 超過10%異常值
                            logger.warning(
                                f"{name} 異常值較多: {len(outliers)}/{len(values)}"
                            )

    # ==================== 私有方法 ====================

    async def _fetch_mock_unemployment_data(self) -> Dict[str, float]:
        """
        獲取模擬失業率數據

        Returns:
            Dict[str, float]: 失業率數據字典
        """
        # 模擬失業率數據（基於香港實際失業率水平）
        # 正常情況下失業率在2-5%之間，疫情期間可能上升到6-7%
        base_unemployment_rate = 3.5  # 基礎失業率3.5%

        # 添加隨機波動
        import random
        unemployment_rate = base_unemployment_rate + random.uniform(-0.5, 0.5)

        # 就業率 = 100% - 失業率
        employment_rate = 100.0 - unemployment_rate

        # 勞動參與率（相對穩定，在60-65%之間）
        labor_participation_rate = 62.0 + random.uniform(-1.0, 1.0)

        data = {
            'unemployment_rate': round(unemployment_rate, 4),
            'employment_rate': round(employment_rate, 4),
            'labor_participation_rate': round(labor_participation_rate, 4),
        }

        logger.debug(f"生成模擬失業率數據: {data}")
        return data

    async def _fetch_real_unemployment_data(self) -> Dict[str, float]:
        """
        獲取真實失業率數據

        Returns:
            Dict[str, float]: 失業率數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的香港統計處勞工統計API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_unemployment_data(self, data: Dict[str, float]) -> None:
        """
        驗證失業率數據

        Args:
            data: 失業率數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.UNEMPLOYMENT_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少失業率指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'unemployment_rate' in data:
            if data['unemployment_rate'] < 0 or data['unemployment_rate'] > 20:
                raise DataValidationError("失業率必須在0-20%之間")

        if 'employment_rate' in data:
            if data['employment_rate'] < 50 or data['employment_rate'] > 100:
                raise DataValidationError("就業率必須在50-100%之間")

        if 'labor_participation_rate' in data:
            if data['labor_participation_rate'] < 40 or data['labor_participation_rate'] > 80:
                raise DataValidationError("勞動參與率必須在40-80%之間")

        # 檢查就業率和失業率的一致性
        if 'unemployment_rate' in data and 'employment_rate' in data:
            expected_employment = 100.0 - data['unemployment_rate']
            if abs(data['employment_rate'] - expected_employment) > 0.5:
                logger.warning(
                    f"就業率與失業率不匹配: {data['employment_rate']:.2f} vs {expected_employment:.2f}"
                )

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

    async def _generate_monthly_unemployment(self, date: datetime) -> Dict[str, float]:
        """
        生成月度失業率數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度失業率數據
        """
        # 基礎失業率（基於香港實際情況）
        base_unemployment = 3.5  # 3.5%

        # 疫情影響建模（2020-2022年較高，2023年後恢復）
        pandemic_factor = 1.0
        if date.year == 2020:
            pandemic_factor = 1.8  # 疫情初期影響
        elif date.year == 2021:
            pandemic_factor = 1.6  # 疫情持續
        elif date.year == 2022:
            pandemic_factor = 1.4  # 疫情末期
        elif date.year >= 2023:
            pandemic_factor = 1.1  # 疫後恢復

        # 根據年份添加趨勢
        year_factor = (date.year - 2020) * 0.02  # 每年恢復2%
        base_unemployment *= pandemic_factor * (1 - year_factor)

        # 根據月份添加季節性（春節後求職高峰，失業率略高）
        month_factors = {
            1: 1.02,   # 1月（新年求職高峰）
            2: 1.05,   # 2月（春節後求職高峰）
            3: 1.03,   # 3月
            4: 1.00,   # 4月
            5: 0.98,   # 5月（就業穩定）
            6: 1.00,   # 6月
            7: 0.99,   # 7月
            8: 0.98,   # 8月
            9: 1.00,   # 9月
            10: 1.01,  # 10月
            11: 1.00,  # 11月
            12: 1.02,  # 12月（年底轉職高峰）
        }
        monthly_factor = month_factors.get(date.month, 1.0)
        unemployment_rate = base_unemployment * monthly_factor

        # 添加隨機波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        noise = random.normalvariate(0, 0.2)  # ±0.2%的標準差
        unemployment_rate += noise
        unemployment_rate = max(unemployment_rate, 0.5)  # 最低0.5%

        # 就業率 = 100% - 失業率
        employment_rate = 100.0 - unemployment_rate

        # 勞動參與率（相對穩定，輕微波動）
        base_participation = 62.0
        participation_factor = random.normalvariate(0, 0.3)  # ±0.3%的標準差
        labor_participation_rate = base_participation + participation_factor
        labor_participation_rate = max(labor_participation_rate, 55.0)  # 最低55%
        labor_participation_rate = min(labor_participation_rate, 70.0)  # 最高70%

        return {
            'unemployment_rate': round(unemployment_rate, 4),
            'employment_rate': round(employment_rate, 4),
            'labor_participation_rate': round(labor_participation_rate, 4),
        }
