"""
Phase 2: Enhanced Base Data Adapter
====================================

BaseAdapter抽象基类 - 统一数据接口定义
支持异步操作、数据验证、错误处理和缓存

改进点：
1. 增强的异步支持 (asyncio)
2. 统一OHLCV数据格式
3. 高级错误处理和重试机制
4. 内置缓存系统
5. 数据验证和清洗
6. 性能监控
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator, model_validator
import pandas as pd
import time


class DataSourceType(str, Enum):
    """数据源类型枚举"""
    RAW_DATA = "raw_data"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    HTTP_API = "http_api"
    CUSTOM = "custom"
    UNIFIED = "unified"


class DataQuality(str, Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class AdapterStatus(str, Enum):
    """适配器状态"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class OHLCV(BaseModel):
    """
    统一OHLCV数据模型

    标准化的市场数据格式，用于所有数据适配器
    """
    model_config = ConfigDict(
        json_encoders={Decimal: str},
        str_strip_whitespace=True
    )

    timestamp: datetime = Field(..., description="数据时间戳")
    open: float = Field(..., gt=0, description="开盘价")
    high: float = Field(..., gt=0, description="最高价")
    low: float = Field(..., gt=0, description="最低价")
    close: float = Field(..., gt=0, description="收盘价")
    volume: int = Field(..., ge=0, description="成交量")

    # 可选字段
    adj_close: Optional[float] = Field(None, description="调整后收盘价")
    turnover: Optional[float] = Field(None, description="成交额")
    symbol: Optional[str] = Field(None, description="股票代码")

    @validator('high', 'low')
    def validate_price_hierarchy(cls, v, values):
        """验证价格层级关系"""
        if 'high' in values and v > values['high']:
            raise ValueError(f'Low price ({v}) cannot exceed high price ({values["high"]})')
        return v

    @validator('close')
    def validate_close_price(cls, v, values):
        """验证收盘价"""
        if 'high' in values and v > values['high']:
            raise ValueError(f'Close price ({v}) cannot exceed high price ({values["high"]})')
        if 'low' in values and v < values['low']:
            raise ValueError(f'Close price ({v}) cannot be below low price ({values["low"]})')
        return v

    @model_validator(mode='after')
    def validate_ohlcv_consistency(self):
        """验证OHLCV数据一致性"""
        if not (self.low <= self.open <= self.high and self.low <= self.close <= self.high):
            raise ValueError('OHLCV data is inconsistent')
        return self

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adj_close': self.adj_close,
            'turnover': self.turnover,
            'symbol': self.symbol
        }


class DataValidationResult(BaseModel):
    """数据验证结果"""
    is_valid: bool = Field(..., description="数据是否有效")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="质量评分")
    quality_level: DataQuality = Field(..., description="质量等级")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="验证元数据")


class AdapterConfig(BaseModel):
    """数据适配器配置"""
    source_type: DataSourceType = Field(..., description="数据源类型")
    source_name: str = Field(..., description="数据源名称")
    update_frequency: int = Field(60, ge=1, description="数据更新频率（秒）")
    max_retries: int = Field(3, ge=1, le=10, description="最大重试次数")
    timeout: int = Field(30, ge=5, le=300, description="连接超时时间（秒）")
    cache_enabled: bool = Field(True, description="是否启用缓存")
    cache_ttl: int = Field(300, ge=60, description="缓存生存时间（秒）")
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0, description="数据质量阈值")
    rate_limit: Optional[int] = Field(None, description="API速率限制（请求/分钟）")

    class Config:
        use_enum_values = True


class PerformanceMetrics(BaseModel):
    """性能指标"""
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None


class BaseAdapter(ABC):
    """
    增强型数据适配器基类

    提供统一的数据接口，支持：
    - 异步操作
    - 数据验证和清洗
    - 错误处理和重试
    - 缓存机制
    - 性能监控
    """

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.logger = logging.getLogger(f"hk_quant_system.adapters.{config.source_type}")
        self.status = AdapterStatus.IDLE
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._performance = PerformanceMetrics()
        self._request_semaphore = asyncio.Semaphore(10)  # 限制并发请求数

        self.logger.info(f"Initialized {self.__class__.__name__} with config: {config.source_name}")

    # ==================== 核心抽象方法 ====================

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到数据源

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开数据源连接

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    async def fetch_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[OHLCV]:
        """
        获取市场数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数

        Returns:
            List[OHLCV]: 市场数据列表
        """
        pass

    @abstractmethod
    async def validate_data(self, data: List[OHLCV]) -> DataValidationResult:
        """
        验证数据质量

        Args:
            data: 待验证的数据列表

        Returns:
            DataValidationResult: 验证结果
        """
        pass

    # ==================== 便利方法 ====================

    async def get_latest(self, symbol: str, **kwargs) -> Optional[OHLCV]:
        """
        获取最新数据

        Args:
            symbol: 股票代码
            **kwargs: 额外参数

        Returns:
            Optional[OHLCV]: 最新数据点
        """
        try:
            data = await self.fetch_data(symbol, **kwargs)
            return data[-1] if data else None
        except Exception as e:
            self.logger.error(f"Error fetching latest data for {symbol}: {e}")
            return None

    async def get_data_range(
        self,
        symbol: str,
        days: int = 30,
        **kwargs
    ) -> List[OHLCV]:
        """
        获取指定天数的数据

        Args:
            symbol: 股票代码
            days: 天数
            **kwargs: 额外参数

        Returns:
            List[OHLCV]: 数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return await self.fetch_data(symbol, start_date, end_date, **kwargs)

    # ==================== 缓存系统 ====================

    def _get_cache_key(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> str:
        """生成缓存键"""
        date_range = f"{start_date or 'all'}_{end_date or 'all'}"
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{self.config.source_type}:{symbol}:{date_range}:{params}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if not self.config.cache_enabled:
            return False

        if cache_key not in self._cache:
            return False

        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp:
            return False

        age = (datetime.now() - timestamp).total_seconds()
        return age < self.config.cache_ttl

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """设置缓存"""
        if self.config.cache_enabled:
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if self._is_cache_valid(cache_key):
            self._performance.cache_hit_rate = (
                self._performance.cache_hit_rate * 0.9 + 1.0 * 0.1
            )
            return self._cache.get(cache_key)
        return None

    def _invalidate_cache(self, pattern: Optional[str] = None) -> None:
        """
        失效缓存

        Args:
            pattern: 缓存键匹配模式，为None则清空所有缓存
        """
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()

    # ==================== 错误处理和重试 ====================

    async def _execute_with_retry(
        self,
        operation,
        *args,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        带重试的操作执行

        Args:
            operation: 异步操作
            *args: 操作参数
            max_retries: 最大重试次数
            **kwargs: 额外参数

        Returns:
            操作结果
        """
        max_retries = max_retries or self.config.max_retries
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                async with self._request_semaphore:
                    start_time = time.time()
                    result = await operation(*args, **kwargs)
                    response_time = time.time() - start_time

                    # 更新性能指标
                    self._update_performance_metrics(response_time, success=True)

                    return result

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}"
                )

                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    await asyncio.sleep(wait_time)

        # 所有重试都失败了
        self._update_performance_metrics(0, success=False)
        self.logger.error(f"All {max_retries + 1} attempts failed. Last error: {last_exception}")
        raise last_exception

    def _update_performance_metrics(self, response_time: float, success: bool) -> None:
        """更新性能指标"""
        self._performance.request_count += 1

        if success:
            # 更新平均响应时间（指数移动平均）
            alpha = 0.1
            self._performance.avg_response_time = (
                alpha * response_time + (1 - alpha) * self._performance.avg_response_time
            )
        else:
            self._performance.error_count += 1
            self._performance.last_error_time = datetime.now()

        self._performance.last_request_time = datetime.now()

    # ==================== 数据验证 ====================

    def calculate_quality_score(self, data: List[OHLCV]) -> float:
        """
        计算数据质量评分

        Args:
            data: OHLCV数据列表

        Returns:
            float: 质量评分 (0.0 - 1.0)
        """
        if not data:
            return 0.0

        total_score = 0.0
        for item in data:
            item_score = 1.0

            # 检查价格完整性
            if not all([item.open, item.high, item.low, item.close]):
                item_score -= 0.3

            # 检查价格合理性
            if item.high < item.low:
                item_score -= 0.5

            # 检查成交量
            if item.volume < 0:
                item_score -= 0.2

            # 检查时间戳
            if item.timestamp > datetime.now():
                item_score -= 0.3

            total_score += max(0.0, item_score)

        return total_score / len(data)

    def get_quality_level(self, score: float) -> DataQuality:
        """
        根据评分获取质量等级

        Args:
            score: 质量评分

        Returns:
            DataQuality: 质量等级
        """
        if score >= 0.9:
            return DataQuality.EXCELLENT
        elif score >= 0.8:
            return DataQuality.GOOD
        elif score >= 0.6:
            return DataQuality.FAIR
        elif score >= 0.4:
            return DataQuality.POOR
        else:
            return DataQuality.UNKNOWN

    # ==================== 健康检查和监控 ====================

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            is_connected = await self.connect()
            if is_connected:
                await self.disconnect()

            return {
                "status": "healthy" if is_connected else "unhealthy",
                "source_type": self.config.source_type,
                "source_name": self.config.source_name,
                "adapter_status": self.status.value,
                "last_update": self._performance.last_request_time,
                "cache_size": len(self._cache),
                "performance": self._performance.dict(),
                "config": self.config.dict()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "source_type": self.config.source_type,
                "source_name": self.config.source_name
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        return {
            "request_count": self._performance.request_count,
            "error_count": self._performance.error_count,
            "error_rate": (
                self._performance.error_count / max(1, self._performance.request_count)
            ),
            "avg_response_time": self._performance.avg_response_time,
            "cache_hit_rate": self._performance.cache_hit_rate,
            "last_request": self._performance.last_request_time,
            "last_error": self._performance.last_error_time
        }

    # ==================== 数据转换 ====================

    def ohlcv_to_dataframe(self, data: List[OHLCV]) -> pd.DataFrame:
        """
        将OHLCV数据转换为DataFrame

        Args:
            data: OHLCV数据列表

        Returns:
            pd.DataFrame: 转换后的DataFrame
        """
        return pd.DataFrame([item.dict() for item in data])

    def dataframe_to_ohlcv(self, df: pd.DataFrame) -> List[OHLCV]:
        """
        将DataFrame转换为OHLCV数据

        Args:
            df: DataFrame数据

        Returns:
            List[OHLCV]: 转换后的OHLCV列表
        """
        if df.empty:
            return []

        data = []
        for _, row in df.iterrows():
            ohlcv = OHLCV(
                timestamp=pd.to_datetime(row['timestamp']),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                adj_close=float(row.get('adj_close', 0)) if pd.notna(row.get('adj_close')) else None,
                turnover=float(row.get('turnover', 0)) if pd.notna(row.get('turnover')) else None,
                symbol=row.get('symbol')
            )
            data.append(ohlcv)

        return data

    # ==================== 资源管理 ====================

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
