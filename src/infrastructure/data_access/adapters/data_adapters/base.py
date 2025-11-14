"""
基础数据适配器抽象类
为5个香港政府数据源提供统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import pandas as pd
from enum import Enum
import logging


class DataSourceType(Enum):
    """数据源类型枚举"""
    VISITOR = "visitor"  # 访客数据
    PROPERTY = "property"  # 地产数据
    GDP = "gdp"  # GDP数据
    RETAIL = "retail"  # 零售数据
    TRADE = "trade"  # 贸易数据


class DataQuality(Enum):
    """数据质量枚举"""
    REAL = "real"  # 真实数据
    SIMULATED = "simulated"  # 模拟数据
    MOCK = "mock"  # 模拟数据
    UNKNOWN = "unknown"  # 未知


class BaseDataAdapter(ABC):
    """
    基础数据适配器抽象类
    所有数据源适配器必须继承此类
    """

    def __init__(self, data_source_type: DataSourceType):
        """
        初始化基础适配器

        Args:
            data_source_type: 数据源类型
        """
        self.data_source_type = data_source_type
        self.logger = logging.getLogger(f'nonprice_data.{data_source_type.value}')
        self._cache = {}

    @abstractmethod
    async def fetch_data(
        self,
        indicator: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        获取数据

        Args:
            indicator: 指标名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 包含(symbol, date, value, source)列的DataFrame

        Raises:
            DataFetchError: 数据获取失败
            ValidationError: 数据验证失败
        """
        pass

    @abstractmethod
    async def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证数据质量

        Args:
            df: 要验证的DataFrame

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        pass

    @abstractmethod
    async def detect_mock_data(self, df: pd.DataFrame) -> Tuple[bool, float, List[str]]:
        """
        检测模拟数据

        Args:
            df: 要检测的DataFrame

        Returns:
            Tuple[bool, float, List[str]]: (是否为模拟数据, 置信度, 检测到的指标)
        """
        pass

    @abstractmethod
    def get_supported_indicators(self) -> List[str]:
        """
        获取支持的指标列表

        Returns:
            List[str]: 指标名称列表
        """
        pass

    def get_data_source_name(self) -> str:
        """获取数据源名称"""
        return self.data_source_type.value

    def get_cache_key(self, indicator: str, start_date: date, end_date: date) -> str:
        """生成缓存键"""
        return f"{self.data_source_type.value}:{indicator}:{start_date}:{end_date}"

    def is_cached(self, cache_key: str) -> bool:
        """检查是否有缓存"""
        return cache_key in self._cache

    def get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        return self._cache.get(cache_key)

    def save_to_cache(self, cache_key: str, df: pd.DataFrame):
        """保存数据到缓存"""
        self._cache[cache_key] = df.copy()

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """验证日期范围"""
        if start_date >= end_date:
            self.logger.error(
                f"Invalid date range: start_date {start_date} >= end_date {end_date}"
            )
            return False

        # 检查日期是否合理（不超出5年范围）
        today = date.today()
        if (today - start_date).days > 5 * 365:
            self.logger.warning(f"Start date {start_date} is more than 5 years ago")
        if (end_date - today).days > 30:
            self.logger.warning(f"End date {end_date} is more than 30 days in the future")

        return True

    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame格式

        Args:
            df: 原始DataFrame

        Returns:
            DataFrame: 标准化后的DataFrame，包含(symbol, date, value, source)列
        """
        # 确保必要的列存在
        required_columns = ['symbol', 'date', 'value', 'source']

        # 如果有额外的列，重命名以匹配标准格式
        column_mapping = {
            'indicator': 'symbol',
            'metric': 'symbol',
            'date': 'date',
            'value': 'value',
            'source': 'source',
            'data_source': 'source'
        }

        # 应用列重命名
        df_copy = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_copy.columns and new_col not in df_copy.columns:
                df_copy = df_copy.rename(columns={old_col: new_col})

        # 检查必需列
        missing_columns = [col for col in required_columns if col not in df_copy.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # 确保数据类型正确
        df_copy['date'] = pd.to_datetime(df_copy['date']).dt.date
        df_copy['value'] = pd.to_numeric(df_copy['value'], errors='coerce')

        # 删除包含NaN的行
        df_copy = df_copy.dropna()

        # 按日期排序
        df_copy = df_copy.sort_values('date')

        return df_copy[required_columns]

    async def get_data(
        self,
        indicator: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取数据的统一接口

        Args:
            indicator: 指标名称
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            DataFrame: 验证后的标准格式数据
        """
        # 验证日期范围
        if not self.validate_date_range(start_date, end_date):
            raise ValueError(f"Invalid date range: {start_date} to {end_date}")

        # 检查缓存
        cache_key = self.get_cache_key(indicator, start_date, end_date)
        if use_cache and self.is_cached(cache_key):
            self.logger.info(f"Using cached data for {indicator}")
            return self.get_from_cache(cache_key)

        # 获取数据
        self.logger.info(f"Fetching {indicator} data from {start_date} to {end_date}")
        df = await self.fetch_data(indicator, start_date, end_date)

        # 标准化格式
        df = self.standardize_dataframe(df)

        # 验证数据
        is_valid, errors = await self.validate_data(df)
        if not is_valid:
            self.logger.error(f"Data validation failed: {errors}")
            raise ValueError(f"Data validation failed: {errors}")

        # 模拟数据检测
        is_mock, confidence, mock_indicators = await self.detect_mock_data(df)
        if is_mock:
            self.logger.warning(
                f"Mock data detected with {confidence:.2%} confidence: {mock_indicators}"
            )

        # 缓存数据
        if use_cache:
            self.save_to_cache(cache_key, df)

        return df

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(data_source={self.data_source_type.value})>"
