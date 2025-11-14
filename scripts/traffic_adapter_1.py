"""
交通數據適配器
Sprint 3 - US-012

實現香港交通相關數據的獲取和處理。
支持3個交通指標：交通流量、平均車速、交通擁堵指數。
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


class TrafficAdapter(BaseDataAdapter, IDataAdapter):
    """
    交通數據適配器

    獲取香港交通相關數據。
    目前使用模擬數據，後續可集成真實數據源。
    """

    # 交通指標列表
    TRAFFIC_INDICATORS = {
        'traffic_flow': '交通流量',
        'traffic_speed': '平均車速',
        'traffic_congestion': '交通擁堵指數',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化交通適配器

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
        self.data_source_url = self.config.get('data_source_url', 'https://td.gov.hk')
        self.update_interval = self.config.get('update_interval', 3600)  # 1小時（交通數據更新較頻繁）

        # 緩存
        self._last_update: Optional[datetime] = None
        self._cached_data: Dict[str, float] = {}

        logger.info(f"初始化交通適配器 - 使用模擬數據: {self.use_mock_data}")

    async def fetch_traffic_flow(self) -> float:
        """
        獲取交通流量

        Returns:
            float: 交通流量 (輛/小時)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_traffic_indicators()
        flow = data.get('traffic_flow')

        if flow is None:
            raise ValueError("無法獲取交通流量")

        logger.info(f"獲取交通流量: {flow:.2f} 輛/小時")
        return flow

    async def fetch_traffic_speed(self) -> float:
        """
        獲取平均車速

        Returns:
            float: 平均車速 (公里/小時)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_traffic_indicators()
        speed = data.get('traffic_speed')

        if speed is None:
            raise ValueError("無法獲取平均車速")

        logger.info(f"獲取平均車速: {speed:.2f} 公里/小時")
        return speed

    async def fetch_traffic_congestion(self) -> float:
        """
        獲取交通擁堵指數

        Returns:
            float: 交通擁堵指數 (0-100)

        Raises:
            Exception: 獲取失敗
        """
        data = await self.fetch_all_traffic_indicators()
        congestion = data.get('traffic_congestion')

        if congestion is None:
            raise ValueError("無法獲取交通擁堵指數")

        logger.info(f"獲取交通擁堵指數: {congestion:.2f}")
        return congestion

    async def fetch_all_traffic_indicators(self) -> Dict[str, float]:
        """
        獲取全部3個交通指標

        Returns:
            Dict[str, float]: 交通指標字典

        Raises:
            Exception: 獲取失敗
        """
        # 檢查緩存
        if self._is_cache_valid():
            logger.debug("使用緩存的交通數據")
            return self._cached_data.copy()

        # 獲取數據
        try:
            if self.use_mock_data:
                data = await self._fetch_mock_traffic_data()
            else:
                data = await self._fetch_real_traffic_data()

            # 驗證數據
            await self._validate_traffic_data(data)

            # 更新緩存
            self._cached_data = data
            self._last_update = datetime.now()

            logger.info(f"獲取交通指標完成: {data}")
            return data

        except Exception as e:
            logger.error(f"獲取交通數據失敗: {e}")
            raise

    async def get_historical_traffic(self, years: int = 5) -> DataFrame:
        """
        獲取歷史交通數據

        Args:
            years: 年數

        Returns:
            DataFrame: 歷史數據，包含日期和各項交通指標

        Raises:
            Exception: 獲取失敗
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        logger.info(f"獲取 {years} 年歷史交通數據: {start_date.date()} - {end_date.date()}")

        # 生成日期範圍（月度數據）
        dates = date_range(start=start_date, end=end_date, freq='MS')  # 月初

        # 生成歷史數據（使用模擬數據）
        historical_data = []

        for date in dates:
            # 生成該月份的交通數據
            monthly_data = await self._generate_monthly_traffic(date)
            monthly_data['date'] = date
            historical_data.append(monthly_data)

        # 轉換為 DataFrame
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # 標準化數據格式
        df = self._standardize_dataframe(df, list(self.TRAFFIC_INDICATORS.keys()))

        self._log_data_info(df, "獲取歷史交通數據")
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
            DataFrame: 交通歷史數據
        """
        # 計算年份
        if start_date and end_date:
            years = (end_date - start_date).days / 365
        else:
            years = kwargs.get('years', 5)

        return await self.get_historical_traffic(years=int(years))

    async def _fetch_realtime_data_impl(self, symbol: str, **kwargs) -> Dict:
        """
        獲取實時交通數據的實現

        Args:
            symbol: 股票代碼（此處不使用）
            **kwargs: 其他參數

        Returns:
            Dict: 實時交通數據
        """
        data = await self.fetch_all_traffic_indicators()

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
        return list(self.TRAFFIC_INDICATORS.keys()) + ['date']

    async def _custom_validate(self, data: DataFrame) -> None:
        """
        自定義交通數據驗證

        Args:
            data: 待驗證的數據

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查交通數值的合理性
        for indicator, name in self.TRAFFIC_INDICATORS.items():
            if indicator in data.columns:
                values = data[indicator].dropna()

                if len(values) > 0:
                    # 檢查是否為負值
                    negative_count = (values < 0).sum()
                    if negative_count > 0:
                        raise DataValidationError(
                            f"{name} 存在負值: {negative_count} 個"
                        )

                    # 檢查交通流量（超過10000輛/小時認為異常）
                    if indicator == 'traffic_flow':
                        high_count = (values > 10000).sum()
                        if high_count > 0:
                            logger.warning(
                                f"{name} 過高 (>10,000): {high_count} 個"
                            )

                    # 檢查平均車速（超過100公里/小時或低於10認為異常）
                    elif indicator == 'traffic_speed':
                        abnormal_count = ((values > 100) | (values < 10)).sum()
                        if abnormal_count > 0:
                            logger.warning(
                                f"{name} 異常 (>100 或 <10): {abnormal_count} 個"
                            )

                    # 檢查擁堵指數（超過100或為負數認為異常）
                    elif indicator == 'traffic_congestion':
                        abnormal_count = ((values > 100) | (values < 0)).sum()
                        if abnormal_count > 0:
                            logger.warning(
                                f"{name} 異常 (>100 或 <0): {abnormal_count} 個"
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

    async def _fetch_mock_traffic_data(self) -> Dict[str, float]:
        """
        獲取模擬交通數據

        Returns:
            Dict[str, float]: 交通數據字典
        """
        # 模擬交通數據（基於香港實際交通水平）
        base_speed = 45.0  # 基礎平均車速45公里/小時
        base_flow = 5000.0  # 基礎交通流量5000輛/小時
        base_congestion = 40.0  # 基礎擁堵指數40

        # 添加隨機波動
        import random
        speed = base_speed + random.uniform(-10, 10)
        speed = max(speed, 20.0)  # 最低20公里/小時

        flow = base_flow + random.uniform(-1000, 1000)
        flow = max(flow, 1000.0)  # 最低1000輛/小時

        # 根據車速計算擁堵指數（車速越慢，擁堵越嚴重）
        congestion_factor = (60 - speed) / 40  # 速度60時擁堵0，20時擁堵100
        congestion = max(0, min(100, base_congestion + congestion_factor * 20 + random.uniform(-5, 5)))

        data = {
            'traffic_flow': round(flow, 4),
            'traffic_speed': round(speed, 4),
            'traffic_congestion': round(congestion, 4),
        }

        logger.debug(f"生成模擬交通數據: {data}")
        return data

    async def _fetch_real_traffic_data(self) -> Dict[str, float]:
        """
        獲取真實交通數據

        Returns:
            Dict[str, float]: 交通數據字典

        Raises:
            NotImplementedError: 尚未實現真實數據源
        """
        # TODO: 集成真實的香港運輸署交通數據API
        logger.warning("真實數據源尚未實現，使用模擬數據")
        raise NotImplementedError("真實數據源尚未實現")

    async def _validate_traffic_data(self, data: Dict[str, float]) -> None:
        """
        驗證交通數據

        Args:
            data: 交通數據字典

        Raises:
            DataValidationError: 驗證失敗
        """
        # 檢查是否包含所有必需的指標
        missing_indicators = set(self.TRAFFIC_INDICATORS.keys()) - set(data.keys())
        if missing_indicators:
            raise DataValidationError(f"缺少交通指標: {missing_indicators}")

        # 檢查數值是否為數字
        for indicator, value in data.items():
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    f"{indicator} 值類型錯誤: {type(value)}"
                )

        # 檢查數值是否合理
        if 'traffic_flow' in data:
            if data['traffic_flow'] < 0:
                raise DataValidationError("交通流量不能為負")

        if 'traffic_speed' in data:
            if data['traffic_speed'] < 0:
                raise DataValidationError("平均車速不能為負")

        if 'traffic_congestion' in data:
            if data['traffic_congestion'] < 0 or data['traffic_congestion'] > 100:
                raise DataValidationError("交通擁堵指數必須在0-100之間")

        # 檢查交通流量與擁堵指數的正相關性
        if 'traffic_flow' in data and 'traffic_congestion' in data:
            # 高流量通常伴隨高擁堵，但允許例外情況
            if data['traffic_flow'] > 8000 and data['traffic_congestion'] < 30:
                logger.warning(
                    f"交通流量高({data['traffic_flow']:.2f})但擁堵指數低({data['traffic_congestion']:.2f})"
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

    async def _generate_monthly_traffic(self, date: datetime) -> Dict[str, float]:
        """
        生成月度交通數據

        Args:
            date: 日期

        Returns:
            Dict[str, float]: 月度交通數據
        """
        # 基礎值（基於香港實際情況）
        base_speed = 45.0  # 公里/小時
        base_flow = 5000.0  # 輛/小時
        base_congestion = 40.0

        # 根據年份添加趨勢（輕微波動）
        year_factor = (date.year - 2020) * 0.01  # 每年1%變化
        base_speed *= (1 + year_factor)
        base_flow *= (1 + year_factor)

        # 根據月份添加季節性（春節、暑假等影響）
        month_factors = {
            1: {'speed': 0.85, 'flow': 0.70, 'congestion': 1.30},  # 1月（春節前返鄉）
            2: {'speed': 0.90, 'flow': 0.75, 'congestion': 1.20},  # 2月（春節）
            3: {'speed': 1.00, 'flow': 1.00, 'congestion': 1.00},  # 3月
            4: {'speed': 1.05, 'flow': 1.05, 'congestion': 0.95},  # 4月
            5: {'speed': 1.02, 'flow': 1.02, 'congestion': 0.98},  # 5月
            6: {'speed': 0.98, 'flow': 0.98, 'congestion': 1.02},  # 6月
            7: {'speed': 0.95, 'flow': 0.90, 'congestion': 1.10},  # 7月（暑假）
            8: {'speed': 0.95, 'flow': 0.90, 'congestion': 1.10},  # 8月（暑假）
            9: {'speed': 1.00, 'flow': 1.05, 'congestion': 0.98},  # 9月（開學）
            10: {'speed': 1.05, 'flow': 1.10, 'congestion': 0.95}, # 10月
            11: {'speed': 1.08, 'flow': 1.15, 'congestion': 0.90}, # 11月
            12: {'speed': 1.10, 'flow': 1.20, 'congestion': 0.85}, # 12月（年底活動）
        }
        monthly_factor = month_factors.get(date.month, {'speed': 1.0, 'flow': 1.0, 'congestion': 1.0})
        speed = base_speed * monthly_factor['speed']
        flow = base_flow * monthly_factor['flow']

        # 根據星期添加隨機性（工作日vs週末）
        import random
        random.seed(int(date.strftime('%Y%m%d')))
        weekday_factor = random.normalvariate(1.0, 0.05)  # ±5%波動
        speed *= weekday_factor
        flow *= weekday_factor

        # 計算擁堵指數（基於車速和流量）
        # 車速越慢，流量越大，擁堵越嚴重
        speed_congestion = max(0, (60 - speed) / 40 * 100)
        flow_congestion = max(0, (flow - 3000) / 7000 * 100)
        congestion = (speed_congestion + flow_congestion) / 2 * monthly_factor['congestion']
        congestion = max(0, min(100, congestion))

        # 添加隨機噪聲
        speed += random.uniform(-2, 2)
        flow += random.uniform(-200, 200)
        congestion += random.uniform(-5, 5)

        # 確保合理範圍
        speed = max(20, min(80, speed))
        flow = max(1000, min(12000, flow))
        congestion = max(0, min(100, congestion))

        return {
            'traffic_flow': round(flow, 4),
            'traffic_speed': round(speed, 4),
            'traffic_congestion': round(congestion, 4),
        }
