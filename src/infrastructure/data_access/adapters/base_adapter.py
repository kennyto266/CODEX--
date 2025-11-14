"""
统一数据适配器基础类

为量化交易系统提供标准化的非价格数据适配器接口。
支持政府数据源（如HIBOR、GDP、房价指数等）转换为技术指标，
进而生成交易信号进行回测。

架构设计：
- 真实数据收集 → 技术指标转换 → 交易信号生成 → 回测验证
- 11个香港政府数据源 → 81种转换组合 → 批量回测80只HSI股票

计算sharpe ratio和maxdrawdown
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np


class DataSourceCategory(str, Enum):
    """数据源类别"""
    GOVERNMENT = "government"
    CENTRAL_BANK = "central_bank"
    MARKET_DATA = "market_data"
    ALTERNATIVE = "alternative"


class DataQualityLevel(str, Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class NonPriceDataPoint(BaseModel):
    """非价格数据点模型

    用于存储政府统计数据等非价格数据，如利率、GDP、CPI等
    """
    timestamp: datetime = Field(..., description="数据时间戳")
    value: float = Field(..., description="数据值")
    value_type: str = Field(..., description="数据类型（如rate、index、volume等）")
    source_id: str = Field(..., description="数据源标识")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="数据质量评分")
    is_estimated: bool = Field(default=False, description="是否为估算值")

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """验证时间戳不能是未来时间"""
        if v > datetime.now() + timedelta(days=1):
            raise ValueError('数据时间戳不能是未来时间')
        return v


class TechnicalIndicatorConfig(BaseModel):
    """技术指标配置"""
    indicator_type: str = Field(..., description="指标类型（sma、ema、rsi、macd等）")
    params: Dict[str, Any] = Field(default_factory=dict, description="指标参数")
    output_name: str = Field(..., description="输出字段名")


class DataValidationResult(BaseModel):
    """数据验证结果"""
    is_valid: bool = Field(..., description="数据是否有效")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="质量评分")
    quality_level: DataQualityLevel = Field(..., description="质量等级")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    statistics: Dict[str, float] = Field(default_factory=dict, description="统计信息")


class BaseDataAdapter(ABC):
    """
    统一数据适配器基类

    所有数据适配器必须继承此类并实现抽象方法。
    支持非价格数据的获取、验证、转换和缓存。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化适配器

        Args:
            config: 配置参数字典
                - source_id: 数据源标识（如 'hibor_overnight', 'gdp_nominal'）
                - provider: 数据提供商（如 'HKMA', 'CSD'）
                - update_frequency: 更新频率（天）
                - cache_enabled: 是否启用缓存
                - quality_threshold: 数据质量阈值
        """
        self.config = config or {}
        self.source_id = self.config.get('source_id', self._extract_source_id())
        self.provider = self.config.get('provider', 'Unknown')
        self.category = self.config.get('category', DataSourceCategory.GOVERNMENT)
        self.update_frequency = self.config.get('update_frequency', 30)
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.quality_threshold = self.config.get('quality_threshold', 0.8)

        # 初始化日志
        self.logger = logging.getLogger(
            f"quant_system.data_adapter.{self.__class__.__name__}"
        )

        # 缓存管理
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = self.config.get('cache_ttl', 3600)  # 默认1小时

        # 数据统计
        self._fetch_count = 0
        self._error_count = 0

        self.logger.info(f"初始化适配器: {self.source_id} ({self.provider})")

    @property
    def name(self) -> str:
        """适配器名称"""
        return self.__class__.__name__

    @property
    def data_source(self) -> str:
        """数据源标识"""
        return self.source_id

    def _extract_source_id(self) -> str:
        """从类名提取数据源标识"""
        name = self.__class__.__name__
        if 'Adapter' in name:
            return name.replace('Adapter', '').lower()
        return name.lower()

    @abstractmethod
    async def fetch_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[NonPriceDataPoint]:
        """
        获取原始数据

        子类必须实现此方法从数据源获取数据。

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            List[NonPriceDataPoint]: 原始数据点列表

        Raises:
            DataFetchError: 数据获取失败
            DataValidationError: 数据验证失败
        """
        pass

    @abstractmethod
    def validate_data(self, data: List[NonPriceDataPoint]) -> DataValidationResult:
        """
        验证数据质量和完整性

        Args:
            data: 待验证的数据点列表

        Returns:
            DataValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def to_ohlcv(
        self,
        data: List[NonPriceDataPoint]
    ) -> pd.DataFrame:
        """
        将非价格数据转换为OHLCV格式

        对于非价格数据（如利率、GDP），需要通过技术指标转换。
        默认实现将value字段映射为close_price，生成OHLCV结构。

        Args:
            data: 原始数据点列表

        Returns:
            pd.DataFrame: 包含OHLCV列的DataFrame
        """
        if not data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # 转换为DataFrame
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'value': d.value,
            'quality_score': d.quality_score
        } for d in data])

        # 按时间排序
        df = df.sort_values('timestamp')

        # 生成OHLCV
        # 对于非价格数据，直接使用value作为close
        df['close'] = df['value']

        # 使用rolling window生成OHLC（简化实现）
        window = min(5, len(df))
        if window > 1:
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close'].rolling(window=window, min_periods=1).max()
            df['low'] = df['close'].rolling(window=window, min_periods=1).min()
        else:
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']

        # 成交量：使用质量评分的倒数作为权重
        df['volume'] = (df['quality_score'] * 1000).round().astype(int)

        # 只保留需要的列
        result = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        result['timestamp'] = pd.to_datetime(result['timestamp'])

        return result

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取适配器元数据

        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            'source_id': self.source_id,
            'provider': self.provider,
            'category': self.category,
            'name': self.name,
            'update_frequency_days': self.update_frequency,
            'quality_threshold': self.quality_threshold,
            'fetch_count': self._fetch_count,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(1, self._fetch_count),
            'has_cache': bool(self._cache)
        }

    def get_cache_key(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> str:
        """
        生成缓存键

        Args:
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            str: 缓存键
        """
        key_parts = [
            self.source_id,
            start_date.isoformat() if start_date else 'none',
            end_date.isoformat() if end_date else 'none'
        ]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)

    def is_cache_valid(self, cache_key: str) -> bool:
        """
        检查缓存是否有效

        Args:
            cache_key: 缓存键

        Returns:
            bool: 缓存是否有效
        """
        if not self.cache_enabled or cache_key not in self._cache:
            return False

        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return False

        age = (datetime.now() - cache_time).total_seconds()
        return age < self._cache_ttl

    def set_cache(self, cache_key: str, data: Any) -> None:
        """
        设置缓存

        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        if self.cache_enabled:
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

    def get_cache(self, cache_key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            cache_key: 缓存键

        Returns:
            Optional[Any]: 缓存的数据，如果没有则返回None
        """
        if self.is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.info("缓存已清空")

    async def get_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: Optional[bool] = None,
        force_refresh: bool = False,
        **kwargs
    ) -> List[NonPriceDataPoint]:
        """
        获取数据（带缓存和重试机制）

        这是主要的数据获取接口，会处理缓存、重试和错误处理。

        Args:
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存（None=自动）
            force_refresh: 是否强制刷新
            **kwargs: 额外参数

        Returns:
            List[NonPriceDataPoint]: 数据点列表

        Raises:
            DataFetchError: 所有重试均失败
        """
        # 确定是否使用缓存
        use_cache_flag = use_cache if use_cache is not None else self.cache_enabled
        cache_key = self.get_cache_key(start_date, end_date, **kwargs)

        # 尝试从缓存获取
        if use_cache_flag and not force_refresh:
            cached_data = self.get_cache(cache_key)
            if cached_data is not None:
                self.logger.debug(f"从缓存获取数据: {cache_key}")
                return cached_data

        # 重试获取数据
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)

        last_error = None
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"获取数据尝试 {attempt + 1}/{max_retries}: {cache_key}")
                data = await self.fetch_data(start_date, end_date, **kwargs)

                # 验证数据
                validation_result = self.validate_data(data)
                if not validation_result.is_valid:
                    raise ValueError(f"数据验证失败: {validation_result.errors}")

                # 缓存数据
                if use_cache_flag:
                    self.set_cache(cache_key, data)

                self._fetch_count += 1
                self.logger.info(
                    f"成功获取 {len(data)} 条数据 (质量评分: {validation_result.quality_score:.2f})"
                )
                return data

            except Exception as e:
                last_error = e
                self._error_count += 1
                self.logger.warning(
                    f"获取数据失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))

        # 所有重试均失败
        self.logger.error(f"获取数据最终失败，已重试 {max_retries} 次: {str(last_error)}")
        raise last_error

    def calculate_quality_score(
        self,
        data: List[NonPriceDataPoint]
    ) -> Tuple[float, DataQualityLevel]:
        """
        计算数据质量评分

        Args:
            data: 数据点列表

        Returns:
            Tuple[float, DataQualityLevel]: (质量评分, 质量等级)
        """
        if not data:
            return 0.0, DataQualityLevel.UNKNOWN

        total_score = 0.0
        for point in data:
            score = point.quality_score

            # 时间戳合理性检查
            if point.timestamp > datetime.now():
                score -= 0.3
            elif point.timestamp < datetime.now() - timedelta(days=3650):  # 超过10年
                score -= 0.2

            # 数据值合理性检查
            if np.isnan(point.value) or np.isinf(point.value):
                score -= 0.5

            # 估算值标记
            if point.is_estimated:
                score -= 0.1

            total_score += max(0.0, min(1.0, score))

        avg_score = total_score / len(data)

        # 确定质量等级
        if avg_score >= 0.95:
            level = DataQualityLevel.EXCELLENT
        elif avg_score >= 0.85:
            level = DataQualityLevel.GOOD
        elif avg_score >= 0.70:
            level = DataQualityLevel.FAIR
        elif avg_score >= 0.50:
            level = DataQualityLevel.POOR
        else:
            level = DataQualityLevel.UNKNOWN

        return avg_score, level

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 尝试获取少量数据
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            data = await self.get_data(
                start_date=start_date,
                end_date=end_date,
                use_cache=False,
                force_refresh=True
            )

            return {
                'status': 'healthy',
                'source_id': self.source_id,
                'provider': self.provider,
                'data_points': len(data),
                'cache_size': len(self._cache),
                'fetch_count': self._fetch_count,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(1, self._fetch_count),
                'metadata': self.get_metadata()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'source_id': self.source_id,
                'error': str(e),
                'error_type': type(e).__name__
            }

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<{self.name}("
            f"source_id='{self.source_id}', "
            f"provider='{self.provider}', "
            f"category='{self.category}'"
            f")>"
        )
