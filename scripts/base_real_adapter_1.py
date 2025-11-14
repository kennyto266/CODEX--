"""
真实数据适配器基类
基于OpenSpec规范设计
确保所有数据源均为真实API数据
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """数据源状态枚举"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class RealDataConfig:
    """真实数据配置"""
    api_key: str
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: int = 100  # 每分钟请求数限制


@dataclass
class RealData:
    """真实数据结构"""
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    is_verified: bool = False
    quality_score: float = 1.0


class RealDataAdapter(ABC):
    """真实数据适配器基类 - 必须从实际API获取数据"""

    def __init__(self, config: RealDataConfig):
        self.config = config
        self.status = DataSourceStatus.ACTIVE
        self.last_updated = None
        self.session = None
        self._request_count = 0
        self._rate_limit_window = datetime.now()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'User-Agent': 'HKQuantSystem/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_real_data(self, params: Dict[str, Any]) -> List[RealData]:
        """
        获取真实数据 - 抽象方法
        必须从实际API获取，禁止使用mock数据

        Args:
            params: 查询参数

        Returns:
            List[RealData]: 真实数据列表

        Raises:
            DataSourceError: 数据源错误
            ValidationError: 数据验证错误
        """
        pass

    @abstractmethod
    def validate_data_integrity(self, data: Dict[str, Any]) -> bool:
        """
        验证数据完整性

        Args:
            data: 待验证的数据

        Returns:
            bool: 验证是否通过
        """
        pass

    @abstractmethod
    async def schedule_update(self):
        """安排定期数据更新 - 抽象方法"""
        pass

    async def _make_authenticated_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = 'GET'
    ) -> Dict[str, Any]:
        """
        发送认证请求到真实API

        Args:
            endpoint: API端点
            params: 请求参数
            method: HTTP方法

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            DataSourceError: 请求失败
        """
        if not self.session:
            raise RuntimeError("请使用 async with 上下文管理器")

        # 检查速率限制
        await self._check_rate_limit()

        # 构建完整URL
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # 准备请求头
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}',
            'Accept': 'application/json'
        }

        # 设置请求参数
        request_params = params.copy() if params else {}
        request_params.update({
            'format': 'json',
            'timestamp': datetime.now().isoformat()
        })

        try:
            # 发送请求
            async with self.session.request(
                method=method,
                url=url,
                params=request_params,
                headers=headers,
                ssl=self._get_ssl_context()
            ) as response:

                # 检查响应状态
                if response.status == 429:
                    raise DataSourceError("API速率限制触发")
                elif response.status == 401:
                    raise DataSourceError("API认证失败")
                elif response.status == 403:
                    raise DataSourceError("API访问被拒绝")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise DataSourceError(f"API错误 {response.status}: {error_text}")

                # 解析JSON响应
                try:
                    data = await response.json()
                except Exception as e:
                    raise DataSourceError(f"JSON解析失败: {e}")

                # 记录请求成功
                self._record_request()
                self.status = DataSourceStatus.ACTIVE

                return data

        except asyncio.TimeoutError:
            self.status = DataSourceStatus.DEGRADED
            raise DataSourceError(f"API请求超时 ({self.config.timeout}秒)")
        except aiohttp.ClientError as e:
            self.status = DataSourceStatus.FAILED
            raise DataSourceError(f"网络请求失败: {e}")

    async def _check_rate_limit(self):
        """检查API速率限制"""
        now = datetime.now()

        # 重置窗口（每分钟）
        if (now - self._rate_limit_window).total_seconds() >= 60:
            self._request_count = 0
            self._rate_limit_window = now

        # 检查是否超出限制
        if self._request_count >= self.config.rate_limit:
            wait_time = 60 - (now - self._rate_limit_window).total_seconds()
            if wait_time > 0:
                logger.warning(f"API速率限制触发，等待 {wait_time:.1f} 秒")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._rate_limit_window = datetime.now()

    def _record_request(self):
        """记录请求计数"""
        self._request_count += 1
        self.last_updated = datetime.now()

    def _get_ssl_context(self) -> bool:
        """获取SSL上下文"""
        return True  # 生产环境必须使用HTTPS

    async def _retry_request(
        self,
        request_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带重试的请求执行

        Args:
            request_func: 请求函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Dict[str, Any]: 响应数据

        Raises:
            DataSourceError: 重试次数耗尽后仍然失败
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return await request_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"请求失败，{wait_time}秒后重试 (第{attempt+1}次)")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求失败，已重试{self.config.max_retries}次")

        # 所有重试都失败
        raise last_exception

    def validate_data_source(self, data: Dict[str, Any]) -> bool:
        """
        验证数据源是否可信

        Args:
            data: 原始数据

        Returns:
            bool: 数据源是否可信
        """
        # 检查数据源标识
        if 'source' not in data:
            logger.error("数据缺少源标识")
            return False

        # 检查时间戳
        if 'timestamp' in data:
            try:
                ts = datetime.fromisoformat(data['timestamp'])
                if ts > datetime.now() + timedelta(hours=24):
                    logger.error("数据时间戳为未来时间")
                    return False
            except Exception:
                logger.error("数据时间戳格式错误")
                return False

        # 检查数据完整性
        if 'data' not in data or not isinstance(data['data'], dict):
            logger.error("数据缺少有效载荷")
            return False

        return True

    def calculate_quality_score(self, data: List[RealData]) -> float:
        """
        计算数据质量分数

        Args:
            data: 真实数据列表

        Returns:
            float: 质量分数 (0-1)
        """
        if not data:
            return 0.0

        total_score = sum(item.quality_score for item in data)
        return total_score / len(data)

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            'status': self.status.value,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'request_count': self._request_count,
            'rate_limit_window': self._rate_limit_window.isoformat()
        }

    def get_data_source_info(self) -> Dict[str, Any]:
        """
        获取数据源信息

        Returns:
            Dict[str, Any]: 数据源配置信息
        """
        return {
            'source_name': self.__class__.__name__,
            'base_url': self.config.base_url,
            'timeout': self.config.timeout,
            'max_retries': self.config.max_retries,
            'rate_limit': self.config.rate_limit
        }


class DataSourceError(Exception):
    """数据源错误异常"""
    pass


class ValidationError(Exception):
    """数据验证错误异常"""
    pass
