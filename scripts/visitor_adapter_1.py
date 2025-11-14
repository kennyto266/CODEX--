"""
訪客數據適配器
Sprint 2 - US-009

實現香港訪客數據的獲取和處理。
支持3個訪客指標：訪客總數、內地訪客、增長率。
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


class VisitorAdapter(BaseDataAdapter, IDataAdapter):
    """
    訪客數據適配器

    獲取香港訪客數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 訪客指標列表
    VISITOR_INDICATORS = {
        'visitor_arrivals_total': '訪客總數',
        'visitor_arrivals_mainland': '內地訪客',
        'visitor_growth': '訪客增長率',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化訪客適配器

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
        self.data_source_url = self.config.get('data_source_url', 'https://www.discoverhongkong.com')
        self.update_interval = self.config.get('update_interval', 86400)  # 24小時

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化訪客適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_visitor_arrivals_total(self) -> float:
        """
        獲取訪客總數

        Returns:
            float: 訪客總數 (萬人次)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_visitor_indicators()
        total = data.get('visitor_arrivals_total')

        if total is None:
            raise ValueError("無法獲取訪客總數")

        logger.info(f"獲取訪客總數: {total:.2f} 萬人次")
        return total

    async def fetch_visitor_arrivals_mainland(self) -> float:
        """
        獲取內地訪客人數

        Returns:
            float: 內地訪客人數 (萬人次)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_visitor_indicators()
        mainland = data.get('visitor_arrivals_mainland')

        if mainland is None:
            raise ValueError("無法獲取內地訪客人數")

        logger.info(f"獲取內地訪客人數: {mainland:.2f} 萬人次")
        return mainland

    async def fetch_visitor_growth(self) -> float:
        """
        獲取訪客增長率

        Returns:
            float: 增長率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_visitor_indicators()
        growth = data.get('visitor_growth')

        if growth is None:
            raise ValueError("無法獲取訪客增長率")

        logger.info(f"獲取訪客增長率: {growth:.2f}%")
        return growth

    async def fetch_all_visitor_indicators(self) -> Dict[str, float]:
        """
        獲取全部3個訪客指標

        Returns:
            Dict[str, float]: 訪客指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的訪客數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_visitor_data()
            else:
                data = await self._fetch_real_visitor_data()

            # 驗證數據
            await self._validate_visitor_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取訪客指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取訪客數據失敗: {e}")
            raise

    async def get_historical_visitor(self, years: int = 5) -> DataFrame:
        """
        獲取歷史訪客數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項訪客指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史訪客數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的訪客數據
            monthly_data = await self._generate_monthly_visitor(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.VISITOR_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史訪客數據")
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
            DataFrame: 訪客歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_visitor(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時訪客數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時訪客數據
        """
        data = await self.fetch_all_visitor_indicators()

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
        return list(self.VISITOR_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義訪客數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查訪客數值的合理性
        for indicator, name in self.VISITOR_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值
                    if indicator == 'visitor_growth':
                        # 增長率可以為負
                        negative_count = (values < -50).sum()  # 小於-50%認為異常
                        if negative_count > 0:
                            raise DataValidationError(
                                f"{name} 增長率過低 (<-50%): {negative_count} 個"
                            )
                    else:
                        # 其他指標不應該為負
                        negative_count = (values < 0).sum()
                        if negative_count > 0:
                            raise DataValidationError(
                                f"{name} 存在負值: {negative_count} 個"
                            )

                    # 檢查是否過高
                    if indicator == 'visitor_growth':
                        high_count = (values > 50).sum()  # 大於50%認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 增長率過高 (>50%): {high_count} 個"
                            )
                    elif indicator == 'visitor_arrivals_total':
                        high_count = (values > 1000).sum()  # 大於1000萬人次認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>1,000萬人次): {high_count} 個"
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

    async def _fetch_mock_visitor_data(self) -> Dict[str, float]:
        """
        獲取模擬訪客數據

        Returns:
            Dict[str, float]: 訪客數據字典
        """
        # 模擬訪客數據（基於香港實際訪客水平）
        base_values = {
            'visitor_arrivals_total': 520.0,   # 520萬人次
            'visitor_arrivals_mainland': 380.0, # 內地380萬人次
            'visitor_growth': 5.2,             # 5.2%增長率
        }

        # 添加隨機波動
        import random
        data = {}
        for indicator, value in base_values.items():
            # 根據指標類型調整波動範圍
            if indicator == 'visitor_growth':
                fluctuation = random.uniform(-2.0, 2.0)  # ±2%
            else:
                fluctuation = random.uniform(-0.10, 0.10) * value  # ±10%

            data[indicator] = round(value + fluctuation, 4)

        logger.debug(f"生成模擬訪客數據: {data}")
        return data

    async def _fetch_real_visitor_data(self) -> Dict[str, float]:
        """
        獲取真實訪客數據

        Returns:
            Dict[str, float]: 訪客數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的旅遊發展局或入境事務處API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_visitor_data(self, data: Dict[str, float]) -> None:
        """
        驗證訪客數據

        Args:
            data: 訪客數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.VISITOR_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少訪客指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'visitor_arrivals_total' in data and data['visitor_arrivals_total'] <= 0:
            raise DataValidationError("訪客總數必須大於0")

        if 'visitor_arrivals_mainland' in data and data['visitor_arrivals_mainland'] <= 0:
            raise DataValidationError("內地訪客數必須大於0")

        if 'visitor_growth' in data and data['visitor_growth'] < -100:
            raise DataValidationError("訪客增長率過低")

        if 'visitor_growth' in data and data['visitor_growth'] > 100:
            raise DataValidationError("訪客增長率過高")

        # 檢查內地訪客不應該超過總訪客
        if 'visitor_arrivals_mainland' in data and 'visitor_arrivals_total' in data:
            if data['visitor_arrivals_mainland'] > data['visitor_arrivals_total']:
                raise DataValidationError("內地訪客數不能超過訪客總數")

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

    async def _generate_monthly_visitor(self, date: datetime) -> Dict[str, float]:
        """
        生成月度訪客數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度訪客數據
        """
        # 基於實際訪客市場生成數據
        base_total = 520.0
        base_growth = 5.2

        # 根據年份添加趨勢（疫情後復甦）
        if date.year < 2020:
            year_factor = (date.year - 2015) * 0.02  # 疫情前穩定增長
            recovery_factor = 1.0
        elif date.year < 2023:
            year_factor = -0.15  # 疫情影響
            recovery_factor = 0.6
        else:
            year_factor = (date.year - 2023) * 0.15  # 復甦期快速增長
            recovery_factor = 1.0

        total = base_total * (1 + year_factor) * recovery_factor

        # 根據月份添加季節性（旅遊旺季/淡季）
        month_factors = {
            1: 0.75,   # 1月（淡季）
            2: 0.80,   # 2月（農曆新年，部分內地遊客返鄉）
            3: 0.90,   # 3月
            4: 0.95,   # 4月（復活節）
            5: 1.00,   # 5月
            6: 0.95,   # 6月
            7: 1.15,   # 7月（暑假旺季）
            8: 1.20,   # 8月（暑假高峰期）
            9: 1.00,   # 9月
            10: 1.10,  # 10月（國慶黄金周）
            11: 1.05,  # 11月
            12: 1.15,  # 12月（聖誕、新年假期）
        }
        monthly_factor = month_factors.get(date.month, 1.0)
        total *= monthly_factor

        # 增長率有波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        growth = base_growth + random.normalvariate(0, 1.5)

        # 內地訪客比例（疫情後有所波動）
        if date.year < 2020:
            mainland_ratio = 0.75  # 疫情前內地訪客約佔75%
        elif date.year < 2023:
            mainland_ratio = 0.60  # 疫情中降至60%
        else:
            mainland_ratio = 0.70  # 復甦期逐步恢復至70%

        # 添加一定波動
        mainland_ratio += random.uniform(-0.05, 0.05)
        mainland_ratio = max(0.5, min(0.85, mainland_ratio))  # 限制在50%-85%之間

        mainland_total = total * mainland_ratio

        return {
            'visitor_arrivals_total': round(total, 4),
            'visitor_arrivals_mainland': round(mainland_total, 4),
            'visitor_growth': round(growth, 4),
        }
