"""
零售銷售數據適配器
Sprint 2 - US-007

實現香港統計處(C&SD)零售銷售數據的獲取和處理。
支持6個零售銷售指標：總額、服裝、超市、餐飲、電子、年增長率。
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


class RetailAdapter(BaseDataAdapter, IDataAdapter):
    """
    零售銷售數據適配器

    獲取香港統計處零售銷售數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 零售銷售指標列表
    RETAIL_INDICATORS = {
        'retail_total': '零售銷售總額',
        'retail_clothing': '服裝銷售',
        'retail_supermarket': '超市銷售',
        'retail_restaurants': '餐飲銷售',
        'retail_electronics': '電子產品銷售',
        'retail_yoy_growth': '零售銷售年增長率',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化零售銷售適配器

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

        logger.info(f"初始化零售銷售適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_retail_total(self) -> float:
        """
        獲取零售銷售總額

        Returns:
            float: 零售銷售總額 (億港元)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_retail_indicators()
        total_value = data.get('retail_total')

        if total_value is None:
            raise ValueError("無法獲取零售銷售總額")

        logger.info(f"獲取零售銷售總額: {total_value:.2f} 億港元")
        return total_value

    async def fetch_retail_categories(self) -> Dict[str, float]:
        """
        獲取各類別零售銷售數據

        Returns:
            Dict[str, float]: 各類別銷售字典，包含服裝、超市、餐飲、電子

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_retail_indicators()

        categories_data = {
            'retail_clothing': data.get('retail_clothing'),
            'retail_supermarket': data.get('retail_supermarket'),
            'retail_restaurants': data.get('retail_restaurants'),
            'retail_electronics': data.get('retail_electronics')
        }

        # 檢查是否有缺失值
        missing = [k for k, v in categories_data.items() if v is None]
        if missing:
            raise ValueError(f"缺少零售類別數據: {missing}")

        logger.info(f"獲取零售類別數據: {categories_data}")
        return categories_data

    async def fetch_retail_growth(self) -> float:
        """
        獲取零售銷售年增長率

        Returns:
            float: 年增長率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_retail_indicators()
        growth_rate = data.get('retail_yoy_growth')

        if growth_rate is None:
            raise ValueError("無法獲取零售銷售增長率")

        logger.info(f"獲取零售銷售增長率: {growth_rate:.2f}%")
        return growth_rate

    async def fetch_all_retail_indicators(self) -> Dict[str, float]:
        """
        獲取全部6個零售銷售指標

        Returns:
            Dict[str, float]: 零售銷售指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的零售銷售數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_retail_data()
            else:
                data = await self._fetch_real_retail_data()

            # 驗證數據
            await self._validate_retail_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取零售銷售指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取零售銷售數據失敗: {e}")
            raise

    async def get_historical_retail(self, years: int = 5) -> DataFrame:
        """
        獲取歷史零售銷售數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項零售銷售指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史零售銷售數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的零售銷售數據
            monthly_data = await self._generate_monthly_retail(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.RETAIL_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史零售銷售數據")
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
            DataFrame: 零售銷售歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_retail(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時零售銷售數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時零售銷售數據
        """
        data = await self.fetch_all_retail_indicators()

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
        return list(self.RETAIL_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義零售銷售數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查零售銷售數值的合理性
        for indicator, name in self.RETAIL_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值（零售銷售不應該是負的，但允許輕微負增長）
                    if indicator == 'retail_yoy_growth':
                        # 年增長率可以為負
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
                    if indicator == 'retail_yoy_growth':
                        high_count = (values > 50).sum()  # 大於50%認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 增長率過高 (>50%): {high_count} 個"
                            )
                    elif indicator == 'retail_total':
                        high_count = (values > 500).sum()  # 大於500億認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>500億): {high_count} 個"
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

    async def _fetch_mock_retail_data(self) -> Dict[str, float]:
        """
        獲取模擬零售銷售數據

        Returns:
            Dict[str, float]: 零售銷售數據字典
        """
        # 模擬零售銷售數據（基於香港實際零售市場水平）
        base_values = {
            'retail_total': 380.0,      # 380億港元
            'retail_clothing': 45.0,    # 服裝 45億
            'retail_supermarket': 80.0, # 超市 80億
            'retail_restaurants': 120.0, # 餐飲 120億
            'retail_electronics': 65.0,  # 電子產品 65億
            'retail_yoy_growth': 3.2,    # 3.2%增長率
        }

        # 添加隨機波動
        import random
        data = {}
        for indicator, value in base_values.items():
            # 根據指標類型調整波動範圍
            if indicator == 'retail_yoy_growth':
                fluctuation = random.uniform(-1.5, 1.5)  # ±1.5%
            elif indicator == 'retail_total':
                fluctuation = random.uniform(-15, 15)    # ±15億
            else:
                fluctuation = random.uniform(-0.03, 0.03) * value  # ±3%

            data[indicator] = round(value + fluctuation, 4)

        logger.debug(f"生成模擬零售銷售數據: {data}")
        return data

    async def _fetch_real_retail_data(self) -> Dict[str, float]:
        """
        獲取真實零售銷售數據

        Returns:
            Dict[str, float]: 零售銷售數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的香港統計處API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_retail_data(self, data: Dict[str, float]) -> None:
        """
        驗證零售銷售數據

        Args:
            data: 零售銷售數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.RETAIL_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少零售銷售指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'retail_total' in data and data['retail_total'] <= 0:
            raise DataValidationError("零售銷售總額必須大於0")

        if 'retail_yoy_growth' in data and data['retail_yoy_growth'] < -100:
            raise DataValidationError("零售銷售增長率過低")

        if 'retail_yoy_growth' in data and data['retail_yoy_growth'] > 100:
            raise DataValidationError("零售銷售增長率過高")

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

    async def _generate_monthly_retail(self, date: datetime) -> Dict[str, float]:
        """
        生成月度零售銷售數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度零售銷售數據
        """
        # 基於實際零售市場生成數據
        base_total = 380.0
        base_growth = 3.2

        # 根據年份添加趨勢
        year_factor = (date.year - 2020) * 0.02  # 每年增長2%
        total = base_total * (1 + year_factor)

        # 根據月份添加季節性（零售業有明顯季節性）
        month_factors = {
            1: 0.90,   # 1月（春節後淡季）
            2: 0.85,   # 2月（春節）
            3: 0.95,   # 3月
            4: 0.98,   # 4月
            5: 1.00,   # 5月
            6: 1.02,   # 6月（夏季消費）
            7: 1.05,   # 7月（暑假）
            8: 1.03,   # 8月
            9: 1.00,   # 9月
            10: 1.02,  # 10月
            11: 1.08,  # 11月（雙11、聖誕購物季開始）
            12: 1.15   # 12月（聖誕、新年）
        }
        monthly_factor = month_factors.get(date.month, 1.0)
        total *= monthly_factor

        # 增長率有波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        growth = base_growth + random.normalvariate(0, 1.0)

        # 類別分配（基於香港零售市場結構）
        category_ratios = {
            'retail_clothing': 0.12,      # 12%
            'retail_supermarket': 0.21,   # 21%
            'retail_restaurants': 0.32,   # 32%
            'retail_electronics': 0.17,   # 17%
        }

        category_data = {
            'retail_total': round(total, 4),
            'retail_yoy_growth': round(growth, 4),
            'retail_clothing': round(total * category_ratios['retail_clothing'], 4),
            'retail_supermarket': round(total * category_ratios['retail_supermarket'], 4),
            'retail_restaurants': round(total * category_ratios['retail_restaurants'], 4),
            'retail_electronics': round(total * category_ratios['retail_electronics'], 4),
        }

        return category_data
