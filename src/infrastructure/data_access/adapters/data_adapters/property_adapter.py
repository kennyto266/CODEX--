"""
PropertyAdapter - 房地产数据适配器
从香港政府数据源获取房地产数据并转换为技术指标
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import aiohttp
from dataclasses import dataclass

from .base import BaseDataAdapter, DataSourceType, DataQuality
from scraping.rvd_scraper import RVDScraper
from scraping.landreg_scraper import LandRegScraper
from validators.data_validator import DataValidator


@dataclass
class PropertyData:
    """房地产数据结构"""
    price_index: float
    transactions: int
    volume: float
    rental_price: float
    date: datetime
    source: str


class PropertyAdapter(BaseDataAdapter):
    """
    房地产数据适配器

    从RVD（差饷物业估价署）和土地注册处获取房地产数据
    支持价格指数、交易量、成交量、租金价格等指标
    """

    def __init__(self):
        """初始化房地产数据适配器"""
        super().__init__(DataSourceType.PROPERTY)
        self.rvd_scraper = RVDScraper()
        self.landreg_scraper = LandRegScraper()
        self.validator = DataValidator()
        self.logger = logging.getLogger('property_adapter')

    async def fetch_data(
        self,
        source: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        获取房地产数据

        Args:
            source: 数据源 ('rvd' 或 'landreg')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 包含房地产数据的DataFrame

        Raises:
            ValueError: 无效的数据源
            Exception: 数据获取失败
        """
        try:
            if source == 'rvd':
                data = await self._fetch_from_rvd(start_date, end_date)
            elif source == 'landreg':
                data = await self._fetch_from_landreg(start_date, end_date)
            else:
                raise ValueError(f"Invalid data source: {source}")

            self.logger.info(f"Successfully fetched {len(data)} records from {source}")
            return data

        except Exception as e:
            self.logger.error(f"Failed to fetch data from {source}: {e}")
            raise

    async def _fetch_from_rvd(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """从RVD获取数据"""
        price_index = await self.rvd_scraper.scrape_price_index(start_date, end_date)
        transactions = await self.rvd_scraper.scrape_transactions(start_date, end_date)

        # 合并数据
        data = price_index.join(transactions, how='outer')
        return data

    async def _fetch_from_landreg(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """从土地注册处获取数据"""
        volume = await self.landreg_scraper.scrape_property_volume(start_date, end_date)
        rental = await self.landreg_scraper.scrape_rental_price(start_date, end_date)

        # 合并数据
        data = volume.join(rental, how='outer')
        return data

    async def get_realtime_data(self) -> Dict[str, Any]:
        """获取最新房地产数据"""
        try:
            # 从RVD获取最新价格指数
            latest_price = await self.rvd_scraper.get_latest()
            return {
                'property_price_index': latest_price.get('price_index', 0),
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Failed to get realtime data: {e}")
            return {}

    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        标准化房地产数据

        Args:
            data: 原始数据DataFrame

        Returns:
            DataFrame: 标准化后的数据
        """
        if data is None or data.empty:
            return pd.DataFrame()

        # 确保列名标准化
        column_mapping = {
            'price_index': 'property_price_index',
            'transactions': 'property_transactions',
            'volume': 'property_volume',
            'rental_price': 'property_rental_price'
        }

        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})

        # 确保所有必要列都存在
        required_columns = [
            'property_price_index',
            'property_transactions',
            'property_volume',
            'property_rental_price'
        ]

        for col in required_columns:
            if col not in data.columns:
                data[col] = np.nan

        # 填充缺失值
        data = self.handle_missing_data(data)

        # 数据类型转换
        data['property_transactions'] = data['property_transactions'].astype('Int64')
        numeric_columns = ['property_price_index', 'property_volume', 'property_rental_price']
        for col in numeric_columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')

        self.logger.info("Data normalization completed")
        return data

    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        验证房地产数据

        Args:
            data: 待验证的DataFrame

        Returns:
            Dict: 验证结果
        """
        if data is None or data.empty:
            return {
                'is_valid': False,
                'errors': ['No data provided'],
                'warnings': []
            }

        errors = []
        warnings = []

        # 检查必要列
        required_columns = [
            'property_price_index',
            'property_transactions',
            'property_volume',
            'property_rental_price'
        ]

        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # 检查数据质量
        for col in required_columns:
            if col in data.columns:
                # 检查负值
                if (data[col] < 0).any():
                    errors.append(f"Column {col} contains negative values")

                # 检查异常值
                q1 = data[col].quantile(0.25)
                q3 = data[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
                if len(outliers) > 0:
                    warnings.append(f"Column {col} has {len(outliers)} outliers")

        # 检查完整性
        completeness = 1.0 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
        if completeness < 0.8:
            errors.append(f"Data completeness ({completeness:.2%}) is below 80%")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'completeness': completeness
        }

    def detect_mock_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检测模拟/虚假数据

        Args:
            data: 待检测的DataFrame

        Returns:
            Dict: 检测结果
        """
        issues = []
        confidence = 0.5  # 初始置信度

        if data is None or data.empty:
            issues.append("No data provided")
            return {
                'is_real': False,
                'confidence': 0.0,
                'issues': issues
            }

        # 检查数据模式
        # 真实数据应该有随机性
        numeric_columns = ['property_price_index', 'property_volume', 'property_rental_price']
        for col in numeric_columns:
            if col in data.columns:
                # 计算变异系数
                cv = data[col].std() / data[col].mean() if data[col].mean() != 0 else 0

                # 如果变异系数太小，可能是模拟数据
                if cv < 0.01:
                    issues.append(f"Column {col} has suspiciously low variation (CV: {cv:.4f})")
                    confidence -= 0.2

                # 检查是否有完美的模式
                diff = data[col].diff().dropna()
                if len(diff) > 0:
                    # 连续相同的差异可能是模拟的
                    if len(set(diff.round(2))) / len(diff) < 0.1:
                        issues.append(f"Column {col} has suspicious pattern")
                        confidence -= 0.1

        # 检查日期模式
        if isinstance(data.index, pd.DatetimeIndex):
            # 真实数据应该有不规则的时间间隔
            date_gaps = data.index.to_series().diff().dropna()
            if len(set(date_gaps.days)) <= 2:
                issues.append("Data has suspiciously regular date intervals")
                confidence -= 0.1

        # 调整置信度
        confidence = max(0.0, min(1.0, confidence))

        return {
            'is_real': confidence > 0.5,
            'confidence': confidence,
            'issues': issues
        }

    def handle_missing_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理缺失数据

        Args:
            data: 包含缺失值的DataFrame

        Returns:
            DataFrame: 处理后的数据
        """
        if data is None or data.empty:
            return data

        # 前向填充
        data = data.fillna(method='ffill')

        # 如果仍有缺失值，后向填充
        data = data.fillna(method='bfill')

        # 剩余的缺失值用均值填充
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if data[col].isnull().any():
                data[col] = data[col].fillna(data[col].mean())

        return data

    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算房地产数据的12个技术指标

        Args:
            data: 房地产数据DataFrame

        Returns:
            DataFrame: 包含技术指标的DataFrame
        """
        if data is None or data.empty:
            return data

        result = data.copy()
        price_col = 'property_price_index'

        if price_col not in data.columns or data[price_col].isnull().all():
            self.logger.warning("No price index data available for indicators")
            return result

        try:
            # 1. 简单移动平均线 (SMA)
            result['sma_20'] = data[price_col].rolling(window=20).mean()
            result['sma_50'] = data[price_col].rolling(window=50).mean()

            # 2. 指数移动平均线 (EMA)
            result['ema_12'] = data[price_col].ewm(span=12).mean()
            result['ema_26'] = data[price_col].ewm(span=26).mean()

            # 3. MACD
            result['macd'] = result['ema_12'] - result['ema_26']
            result['macd_signal'] = result['macd'].ewm(span=9).mean()
            result['macd_histogram'] = result['macd'] - result['macd_signal']

            # 4. RSI
            delta = data[price_col].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            result['rsi'] = 100 - (100 / (1 + rs))

            # 5. 布林带
            sma_20 = data[price_col].rolling(window=20).mean()
            std_20 = data[price_col].rolling(window=20).std()
            result['bollinger_upper'] = sma_20 + (2 * std_20)
            result['bollinger_lower'] = sma_20 - (2 * std_20)
            result['bollinger_middle'] = sma_20

            # 6. 随机指标 (KDJ)
            low_14 = data[price_col].rolling(window=14).min()
            high_14 = data[price_col].rolling(window=14).max()
            k_percent = 100 * ((data[price_col] - low_14) / (high_14 - low_14))
            result['k_percent'] = k_percent.rolling(window=3).mean()
            result['d_percent'] = result['k_percent'].rolling(window=3).mean()
            result['j_percent'] = 3 * result['k_percent'] - 2 * result['d_percent']

            # 7. ATR (平均真实波幅)
            high = data[price_col]
            low = data[price_col]
            close = data[price_col].shift(1)
            tr = pd.concat([
                high - low,
                (high - close).abs(),
                (low - close).abs()
            ], axis=1).max(axis=1)
            result['atr'] = tr.rolling(window=14).mean()

            self.logger.info(f"Calculated 12 technical indicators for {len(result)} data points")

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            # 返回原始数据

        return result

    def validate_data_source(self, source: Any) -> bool:
        """
        验证数据源

        Args:
            source: 数据源对象

        Returns:
            bool: 是否有效
        """
        # 验证政府域名
        if hasattr(source, 'domain'):
            return self._validate_govt_domain(source.domain)
        return False

    def _validate_govt_domain(self, domain: str) -> bool:
        """验证政府域名"""
        valid_domains = ['rvd.gov.hk', 'landreg.gov.hk', 'gov.hk']
        return any(valid_domain in domain.lower() for valid_domain in valid_domains)

    def get_supported_sources(self) -> List[str]:
        """获取支持的数据源"""
        return ['rvd', 'landreg']

    def _log_error(self, message: str, exception: Optional[Exception] = None):
        """记录错误"""
        if exception:
            self.logger.error(f"{message}: {exception}")
        else:
            self.logger.error(message)

    async def close(self):
        """清理资源"""
        try:
            await self.rvd_scraper.close()
            await self.landreg_scraper.close()
            self.logger.info("PropertyAdapter resources closed")
        except Exception as e:
            self.logger.error(f"Error closing resources: {e}")
