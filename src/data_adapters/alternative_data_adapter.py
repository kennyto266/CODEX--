"""
替代数据适配器基类

为经济指标、政府数据、市场结构数据等非价格数据提供统一接口。
支持多种数据频率、元数据管理和异步操作。
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import pandas as pd
from functools import lru_cache


logger = logging.getLogger("hk_quant_system.alternative_data_adapter")


class DataFrequency(str, Enum):
    """数据更新频率枚举"""
    REALTIME = "realtime"      # 实时
    MINUTELY = "minutely"      # 每分钟
    HOURLY = "hourly"          # 每小时
    DAILY = "daily"            # 每天
    WEEKLY = "weekly"          # 每周
    MONTHLY = "monthly"        # 每月
    QUARTERLY = "quarterly"    # 每季度
    YEARLY = "yearly"          # 每年


class IndicatorMetadata(BaseModel):
    """指标元数据模型"""
    indicator_code: str = Field(..., description="指标代码")
    indicator_name: str = Field(..., description="指标名称")
    description: str = Field(..., description="指标描述")
    data_source: str = Field(..., description="数据源")
    frequency: DataFrequency = Field(..., description="更新频率")
    unit: Optional[str] = Field(None, description="数据单位")
    country_code: str = Field(..., description="国家/地区代码")
    category: str = Field(..., description="指标分类")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    next_update: Optional[datetime] = Field(None, description="下次更新预期时间")
    data_availability: str = Field(..., description="数据可用性说明")
    quality_notes: Optional[str] = Field(None, description="数据质量说明")

    class Config:
        use_enum_values = True


class AlternativeDataPoint(BaseModel):
    """单个替代数据点"""
    timestamp: datetime = Field(..., description="时间戳")
    value: Any = Field(..., description="数据值")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="该数据点的元数据")
    source: str = Field(..., description="数据源")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0, description="数据质量分数")


class AlternativeDataAdapter(ABC):
    """替代数据适配器基类

    所有替代数据适配器都应继承此类，提供统一的接口。
    支持多种数据频率、缓存、重试机制和元数据管理。
    """

    def __init__(
        self,
        adapter_name: str,
        data_source_url: str,
        cache_ttl: int = 3600,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """初始化适配器

        Args:
            adapter_name: 适配器名称
            data_source_url: 数据源URL
            cache_ttl: 缓存生存时间（秒）
            max_retries: 最大重试次数
            timeout: 连接超时（秒）
        """
        self.adapter_name = adapter_name
        self.data_source_url = data_source_url
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        # 缓存和状态
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._metadata_cache: Dict[str, IndicatorMetadata] = {}
        self._last_error: Optional[str] = None
        self._is_connected = False
        self._connection_attempts = 0

        # 日志
        self.logger = logging.getLogger(f"hk_quant_system.alt_adapter.{adapter_name}")

    async def connect(self) -> bool:
        """连接到数据源

        Returns:
            bool: 连接是否成功
        """
        try:
            self._connection_attempts += 1
            success = await self._do_connect()
            if success:
                self._is_connected = True
                self.logger.info(f"✓ 成功连接到 {self.adapter_name}")
            else:
                self.logger.error(f"✗ 连接到 {self.adapter_name} 失败")
            return success
        except Exception as e:
            self.logger.error(f"✗ 连接错误: {e}")
            self._last_error = str(e)
            return False

    async def disconnect(self) -> bool:
        """断开连接

        Returns:
            bool: 断开是否成功
        """
        try:
            success = await self._do_disconnect()
            if success:
                self._is_connected = False
                self.logger.info(f"✓ 成功断开 {self.adapter_name}")
            return success
        except Exception as e:
            self.logger.error(f"✗ 断开连接错误: {e}")
            return False

    async def fetch_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """获取指标数据

        Args:
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            pd.DataFrame: 包含timestamp和value列的数据框
        """
        # 检查缓存
        cache_key = f"{indicator_code}_{start_date}_{end_date}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.cache_ttl:
                self.logger.debug(f"使用缓存数据 ({age:.0f}秒)")
                return cached_data

        # 执行数据获取（带重试）
        data = await self._fetch_with_retry(indicator_code, start_date, end_date, **kwargs)

        # 缓存结果
        self._cache[cache_key] = (datetime.now(), data)

        return data

    async def get_realtime_data(self, indicator_code: str, **kwargs) -> Dict[str, Any]:
        """获取实时数据

        Args:
            indicator_code: 指标代码
            **kwargs: 其他参数

        Returns:
            Dict: 最新数据点
        """
        try:
            data_point = await self._get_realtime_impl(indicator_code, **kwargs)
            self.logger.debug(f"✓ 获得实时数据: {indicator_code}")
            return data_point
        except Exception as e:
            self.logger.error(f"✗ 获取实时数据失败: {e}")
            self._last_error = str(e)
            raise

    async def validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据质量

        Args:
            df: 数据框

        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必要列
            if 'timestamp' not in df.columns or 'value' not in df.columns:
                self.logger.error("缺少必要列: timestamp 或 value")
                return False

            # 检查数据类型
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                self.logger.error("timestamp列数据类型错误")
                return False

            # 检查缺失值
            missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
            if missing_pct > 0.1:  # 超过10%的缺失值
                self.logger.warning(f"缺失值过多: {missing_pct:.1%}")

            return True
        except Exception as e:
            self.logger.error(f"✗ 数据验证失败: {e}")
            return False

    async def get_metadata(self, indicator_code: str) -> IndicatorMetadata:
        """获取指标元数据

        Args:
            indicator_code: 指标代码

        Returns:
            IndicatorMetadata: 元数据对象
        """
        # 检查缓存
        if indicator_code in self._metadata_cache:
            return self._metadata_cache[indicator_code]

        # 获取元数据
        metadata = await self._get_metadata_impl(indicator_code)

        # 缓存
        self._metadata_cache[indicator_code] = metadata

        return metadata

    async def list_indicators(self) -> List[str]:
        """列出所有可用指标

        Returns:
            List[str]: 指标代码列表
        """
        try:
            indicators = await self._list_indicators_impl()
            self.logger.info(f"✓ 列出{len(indicators)}个指标")
            return indicators
        except Exception as e:
            self.logger.error(f"✗ 列出指标失败: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """检查适配器健康状态

        Returns:
            Dict: 健康检查结果
        """
        status = {
            "adapter_name": self.adapter_name,
            "is_connected": self._is_connected,
            "last_error": self._last_error,
            "connection_attempts": self._connection_attempts,
            "cache_size": len(self._cache),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 检查连接
            is_reachable = await self._check_connectivity()
            status["is_reachable"] = is_reachable
            status["status"] = "healthy" if is_reachable else "unhealthy"
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)

        return status

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._metadata_cache.clear()
        self.logger.info("✓ 缓存已清空")

    # 抽象方法 - 子类必须实现

    @abstractmethod
    async def _do_connect(self) -> bool:
        """实现连接逻辑"""
        pass

    @abstractmethod
    async def _do_disconnect(self) -> bool:
        """实现断开连接逻辑"""
        pass

    @abstractmethod
    async def _fetch_with_retry(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """实现带重试的数据获取"""
        pass

    @abstractmethod
    async def _get_realtime_impl(self, indicator_code: str, **kwargs) -> Dict[str, Any]:
        """实现实时数据获取"""
        pass

    @abstractmethod
    async def _get_metadata_impl(self, indicator_code: str) -> IndicatorMetadata:
        """实现元数据获取"""
        pass

    @abstractmethod
    async def _list_indicators_impl(self) -> List[str]:
        """实现指标列表获取"""
        pass

    @abstractmethod
    async def _check_connectivity(self) -> bool:
        """检查连接状态"""
        pass

    # 辅助方法

    async def _retry_operation(self, coro_func, *args, **kwargs):
        """通用重试机制

        Args:
            coro_func: 协程函数
            *args, **kwargs: 函数参数

        Returns:
            任何返回值
        """
        for attempt in range(self.max_retries):
            try:
                return await coro_func(*args, **kwargs)
            except Exception as e:
                wait_time = 2 ** attempt  # 指数退避
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"第{attempt+1}次重试失败: {e}. "
                        f"等待{wait_time}秒后重试..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"所有{self.max_retries}次重试均失败")
                    raise

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False

        cached_time, _ = self._cache[cache_key]
        age = (datetime.now() - cached_time).total_seconds()
        return age < self.cache_ttl


__all__ = [
    "AlternativeDataAdapter",
    "IndicatorMetadata",
    "AlternativeDataPoint",
    "DataFrequency",
]
