"""
房地產數據適配器
Sprint 2 - US-008

實現香港房地產市場數據的獲取和處理。
支持5個房地產指標：樓價、租金、回報率、交易量、成交額。
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


class PropertyAdapter(BaseDataAdapter, IDataAdapter):
    """
    房地產數據適配器

    獲取香港房地產市場數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 房地產指標列表
    PROPERTY_INDICATORS = {
        'property_price': '平均樓價',
        'property_rental': '平均租金',
        'property_return': '房地產回報率',
        'property_transactions': '房地產交易量',
        'property_volume': '房地產成交額',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化房地產適配器

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
        self.data_source_url = self.config.get('data_source_url', 'https://www.rvd.gov.hk')
        self.update_interval = self.config.get('update_interval', 86400)  # 24小時

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化房地產適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_property_price(self) -> float:
        """
        獲取平均樓價

        Returns:
            float: 平均樓價 (港元/平方米)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_property_indicators()
        price = data.get('property_price')

        if price is None:
            raise ValueError("無法獲取房地產價格")

        logger.info(f"獲取平均樓價: {price:.2f} 港元/平方米")
        return price

    async def fetch_property_rental(self) -> float:
        """
        獲取平均租金

        Returns:
            float: 平均租金 (港元/平方米/月)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_property_indicators()
        rental = data.get('property_rental')

        if rental is None:
            raise ValueError("無法獲取房地產租金")

        logger.info(f"獲取平均租金: {rental:.2f} 港元/平方米/月")
        return rental

    async def fetch_property_return(self) -> float:
        """
        獲取房地產回報率

        Returns:
            float: 回報率 (%)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_property_indicators()
        return_rate = data.get('property_return')

        if return_rate is None:
            raise ValueError("無法獲取房地產回報率")

        logger.info(f"獲取房地產回報率: {return_rate:.2f}%")
        return return_rate

    async def fetch_property_transactions(self) -> Dict[str, float]:
        """
        獲取房地產交易數據

        Returns:
            Dict[str, float]: 交易數據字典，包含交易量和成交額

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_property_indicators()

        transactions_data = {
            'property_transactions': data.get('property_transactions'),
            'property_volume': data.get('property_volume')
        }

        # 檢查是否有缺失值
        missing = [k for k, v in transactions_data.items() if v is None]
        if missing:
            raise ValueError(f"缺少房地產交易數據: {missing}")

        logger.info(f"獲取房地產交易數據: {transactions_data}")
        return transactions_data

    async def fetch_all_property_indicators(self) -> Dict[str, float]:
        """
        獲取全部5個房地產指標

        Returns:
            Dict[str, float]: 房地產指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的房地產數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_property_data()
            else:
                data = await self._fetch_real_property_data()

            # 驗證數據
            await self._validate_property_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取房地產指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取房地產數據失敗: {e}")
            raise

    async def get_historical_property(self, years: int = 5) -> DataFrame:
        """
        獲取歷史房地產數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項房地產指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史房地產數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的房地產數據
            monthly_data = await self._generate_monthly_property(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.PROPERTY_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史房地產數據")
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
            DataFrame: 房地產歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_property(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時房地產數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時房地產數據
        """
        data = await self.fetch_all_property_indicators()

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
        return list(self.PROPERTY_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義房地產數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查房地產數值的合理性
        for indicator, name in self.PROPERTY_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值
                    negative_count = (values < 0).sum()
                    if negative_count > 0:
                        raise DataValidationError(
                            f"{name} 存在負值: {negative_count} 個"
                        )

                    # 檢查是否過高
                    if indicator == 'property_price':
                        high_count = (values > 300000).sum()  # 大於30萬港元/平方米認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>300,000港元/平方米): {high_count} 個"
                            )
                    elif indicator == 'property_rental':
                        high_count = (values > 1000).sum()  # 大於1000港元/平方米/月認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>1,000港元/平方米/月): {high_count} 個"
                            )
                    elif indicator == 'property_return':
                        high_count = (values > 20).sum()  # 大於20%認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 回報率過高 (>20%): {high_count} 個"
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

    async def _fetch_mock_property_data(self) -> Dict[str, float]:
        """
        獲取模擬房地產數據

        Returns:
            Dict[str, float]: 房地產數據字典
        """
        # 模擬房地產數據（基於香港實際房地產市場水平）
        base_values = {
            'property_price': 185000.0,      # 185,000港元/平方米
            'property_rental': 380.0,        # 380港元/平方米/月
            'property_return': 2.4,          # 2.4%回報率
            'property_transactions': 8500.0, # 8,500宗交易
            'property_volume': 650.0,        # 650億港元成交額
        }

        # 添加隨機波動
        import random
        data = {}
        for indicator, value in base_values.items():
            # 根據指標類型調整波動範圍
            if indicator == 'property_return':
                fluctuation = random.uniform(-0.3, 0.3)  # ±0.3%
            elif indicator == 'property_transactions':
                fluctuation = random.uniform(-0.15, 0.15) * value  # ±15%
            else:
                fluctuation = random.uniform(-0.05, 0.05) * value  # ±5%

            data[indicator] = round(value + fluctuation, 4)

        logger.debug(f"生成模擬房地產數據: {data}")
        return data

    async def _fetch_real_property_data(self) -> Dict[str, float]:
        """
        獲取真實房地產數據

        Returns:
            Dict[str, float]: 房地產數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的土地註冊處或房委會API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_property_data(self, data: Dict[str, float]) -> None:
        """
        驗證房地產數據

        Args:
            data: 房地產數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.PROPERTY_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少房地產指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'property_price' in data and data['property_price'] <= 0:
            raise DataValidationError("房地產價格必須大於0")

        if 'property_rental' in data and data['property_rental'] <= 0:
            raise DataValidationError("房地產租金必須大於0")

        if 'property_return' in data and data['property_return'] < 0:
            raise DataValidationError("房地產回報率不應該為負")

        if 'property_transactions' in data and data['property_transactions'] <= 0:
            raise DataValidationError("房地產交易量必須大於0")

        if 'property_volume' in data and data['property_volume'] <= 0:
            raise DataValidationError("房地產成交額必須大於0")

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

    async def _generate_monthly_property(self, date: datetime) -> Dict[str, float]:
        """
        生成月度房地產數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度房地產數據
        """
        # 基於實際房地產市場生成數據
        base_price = 185000.0
        base_rental = 380.0
        base_return = 2.4

        # 根據年份添加趨勢
        year_factor = (date.year - 2020) * 0.03  # 每年增長3%
        price = base_price * (1 + year_factor)
        rental = base_rental * (1 + year_factor)

        # 根據月份添加季節性
        month_factors = {
            1: 0.95,   # 1月（農曆新年前淡季）
            2: 0.90,   # 2月（農曆新年）
            3: 1.00,   # 3月
            4: 1.02,   # 4月
            5: 1.05,   # 5月
            6: 1.03,   # 6月
            7: 1.00,   # 7月
            8: 0.98,   # 8月（暑假）
            9: 1.02,   # 9月
            10: 1.08,  # 10月（傳統旺季）
            11: 1.10,  # 11月（聖誕前旺季）
            12: 1.05   # 12月（年底）
        }
        monthly_factor = month_factors.get(date.month, 1.0)
        price *= monthly_factor
        rental *= monthly_factor

        # 回報率穩定但有微小波動
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        return_rate = base_return + random.normalvariate(0, 0.2)

        # 交易量和成交額
        base_transactions = 8500
        base_volume = 650

        # 交易量與價格負相關（價格高時交易量低）
        transaction_factor = 1.2 - (price / base_price - 1) * 0.5
        transactions = base_transactions * transaction_factor * monthly_factor

        # 成交額 = 交易量 * 平均成交價
        avg_deal_price = price * 50  # 假設平均成交面積50平方米
        volume = (transactions * avg_deal_price) / 100000000  # 轉換為億

        return {
            'property_price': round(price, 4),
            'property_rental': round(rental, 4),
            'property_return': round(return_rate, 4),
            'property_transactions': round(transactions, 4),
            'property_volume': round(volume, 4),
        }
