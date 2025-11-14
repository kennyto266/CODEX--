"""
貿易數據適配器
Sprint 3 - US-010

實現香港貿易數據的獲取和處理。
支持3個貿易指標：出口額、進口額、貿易餘額。
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


class TradeAdapter(BaseDataAdapter, IDataAdapter):
    """
    貿易數據適配器

    獲取香港貿易數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 貿易指標列表
    TRADE_INDICATORS = {
        'trade_export': '出口額',
        'trade_import': '進口額',
        'trade_balance': '貿易餘額',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化貿易適配器

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

        logger.info(f"初始化貿易適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_trade_export(self) -> float:
        """
        獲取出口額

        Returns:
            float: 出口額 (億港元)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_trade_indicators()
        export_value = data.get('trade_export')

        if export_value is None:
            raise ValueError("無法獲取出口額")

        logger.info(f"獲取出口額: {export_value:.2f} 億港元")
        return export_value

    async def fetch_trade_import(self) -> float:
        """
        獲取進口額

        Returns:
            float: 進口額 (億港元)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_trade_indicators()
        import_value = data.get('trade_import')

        if import_value is None:
            raise ValueError("無法獲取進口額")

        logger.info(f"獲取進口額: {import_value:.2f} 億港元")
        return import_value

    async def fetch_trade_balance(self) -> float:
        """
        獲取貿易餘額

        Returns:
            float: 貿易餘額 (億港元)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_trade_indicators()
        balance = data.get('trade_balance')

        if balance is None:
            raise ValueError("無法獲取貿易餘額")

        logger.info(f"獲取貿易餘額: {balance:.2f} 億港元")
        return balance

    async def fetch_all_trade_indicators(self) -> Dict[str, float]:
        """
        獲取全部3個貿易指標

        Returns:
            Dict[str, float]: 貿易指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的貿易數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_trade_data()
            else:
                data = await self._fetch_real_trade_data()

            # 驗證數據
            await self._validate_trade_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取貿易指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取貿易數據失敗: {e}")
            raise

    async def get_historical_trade(self, years: int = 5) -> DataFrame:
        """
        獲取歷史貿易數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項貿易指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史貿易數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的貿易數據
            monthly_data = await self._generate_monthly_trade(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.TRADE_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史貿易數據")
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
            DataFrame: 貿易歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_trade(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時貿易數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時貿易數據
        """
        data = await self.fetch_all_trade_indicators()

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
        return list(self.TRADE_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義貿易數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查貿易數值的合理性
        for indicator, name in self.TRADE_INDICATORS.items():
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
                    if indicator == 'trade_export':
                        high_count = (values > 10000).sum()  # 大於10,000億認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>10,000億): {high_count} 個"
                            )
                    elif indicator == 'trade_import':
                        high_count = (values > 10000).sum()  # 大於10,000億認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>10,000億): {high_count} 個"
                            )
                    elif indicator == 'trade_balance':
                        high_count = (values > 2000).sum()  # 大於2,000億認為異常
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>2,000億): {high_count} 個"
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

    async def _fetch_mock_trade_data(self) -> Dict[str, float]:
        """
        獲取模擬貿易數據

        Returns:
            Dict[str, float]: 貿易數據字典
        """
        # 模擬貿易數據（基於香港實際貿易水平）
        base_values = {
            'trade_export': 6000.0,    # 6,000億港元出口額
            'trade_import': 5500.0,    # 5,500億港元進口額
            'trade_balance': 500.0,    # 500億港元貿易餘額
        }

        # 添加隨機波動
        import random
        data = {}
        for indicator, value in base_values.items():
            # 根據指標類型調整波動範圍
            if indicator == 'trade_balance':
                fluctuation = random.uniform(-0.20, 0.20) * value  # ±20%
            else:
                fluctuation = random.uniform(-0.08, 0.08) * value  # ±8%

            data[indicator] = round(value + fluctuation, 4)

        logger.debug(f"生成模擬貿易數據: {data}")
        return data

    async def _fetch_real_trade_data(self) -> Dict[str, float]:
        """
        獲取真實貿易數據

        Returns:
            Dict[str, float]: 貿易數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的香港統計處貿易統計API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_trade_data(self, data: Dict[str, float]) -> None:
        """
        驗證貿易數據

        Args:
            data: 貿易數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.TRADE_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少貿易指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'trade_export' in data and data['trade_export'] <= 0:
            raise DataValidationError("出口額必須大於0")

        if 'trade_import' in data and data['trade_import'] <= 0:
            raise DataValidationError("進口額必須大於0")

        if 'trade_balance' in data:
            # 貿易餘額應該等於出口額減進口額（允許小誤差）
            expected_balance = data['trade_export'] - data['trade_import']
            if abs(data['trade_balance'] - expected_balance) > 1.0:
                logger.warning(
                    f"貿易餘額與出口減進口不匹配: {data['trade_balance']:.2f} vs {expected_balance:.2f}"
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

    async def _generate_monthly_trade(self, date: datetime) -> Dict[str, float]:
        """
        生成月度貿易數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度貿易數據
        """
        # 基於實際貿易市場生成數據
        base_export = 6000.0
        base_import = 5500.0
        base_balance = 500.0

        # 根據年份添加趨勢
        year_factor = (date.year - 2020) * 0.03  # 每年增長3%
        export = base_export * (1 + year_factor)
        import_val = base_import * (1 + year_factor)

        # 根據月份添加季節性
        month_factors = {
            1: 0.92,   # 1月（春節前淡季）
            2: 0.88,   # 2月（春節）
            3: 0.98,   # 3月
            4: 1.00,   # 4月
            5: 1.02,   # 5月
            6: 1.05,   # 6月（夏季消費）
            7: 1.03,   # 7月
            8: 1.00,   # 8月
            9: 1.02,   # 9月
            10: 1.08,  # 10月（聖誕節前出貨高峰）
            11: 1.15,  # 11月（聖誕節前出貨高峰）
            12: 1.05,  # 12月（年底）
        }
        monthly_factor = month_factors.get(date.month, 1.0)
        export *= monthly_factor
        import_val *= monthly_factor

        # 進出口有一定相關性（基於實際貿易模式）
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        correlation_factor = random.normalvariate(1.0, 0.05)  # 相關性波動±5%
        import_val *= correlation_factor

        # 計算貿易餘額
        balance = export - import_val

        return {
            'trade_export': round(export, 4),
            'trade_import': round(import_val, 4),
            'trade_balance': round(balance, 4),
        }
