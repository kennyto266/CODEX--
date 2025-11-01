"""
数据缓存系统 - 支持内存缓存和Redis缓存

用于缓存金融数据，减少API调用次数
提高系统性能并降低成本

使用方法:
1. 使用@cached装饰器缓存函数结果
2. 使用CacheManager管理缓存
"""

from typing import Any, Optional, Dict, Callable, Union
import time
import hashlib
import json
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存 - 使用LRU算法"""

    def __init__(self, maxsize: int = 128, ttl: int = 3600):
        """
        初始化内存缓存

        Args:
            maxsize: 最大缓存条目数
            ttl: 默认TTL（秒）
        """
        self.maxsize = maxsize
        self.default_ttl = ttl
        self._cache = {}  # {(key, params_hash): (value, expire_time)}
        self._access_order = []  # 用于LRU

    def _make_key(self, key: str, params: Dict) -> str:
        """生成缓存键"""
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{key}:{params_hash}"

    def _is_expired(self, expire_time: float) -> bool:
        """检查是否过期"""
        return time.time() > expire_time

    def get(self, key: str, params: Dict = None) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            params: 参数

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if params is None:
            params = {}

        cache_key = self._make_key(key, params)

        # 查找缓存
        if cache_key in self._cache:
            value, expire_time = self._cache[cache_key]

            # 检查是否过期
            if not self._is_expired(expire_time):
                # 更新访问顺序（LRU）
                if cache_key in self._access_order:
                    self._access_order.remove(cache_key)
                self._access_order.append(cache_key)

                logger.debug(f"缓存命中: {key}")
                return value
            else:
                # 过期，删除
                del self._cache[cache_key]
                self._access_order.remove(cache_key)
                logger.debug(f"缓存过期: {key}")

        logger.debug(f"缓存未命中: {key}")
        return None

    def set(self, key: str, value: Any, params: Dict = None, ttl: int = None) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            params: 参数
            ttl: TTL（秒）
        """
        if params is None:
            params = {}

        if ttl is None:
            ttl = self.default_ttl

        cache_key = self._make_key(key, params)
        expire_time = time.time() + ttl

        # 检查容量限制
        if len(self._cache) >= self.maxsize and cache_key not in self._cache:
            # 删除最久未使用的项
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            logger.debug(f"缓存容量已满，删除最久未使用的项")

        # 设置缓存
        self._cache[cache_key] = (value, expire_time)

        # 更新访问顺序
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)

        logger.debug(f"缓存设置: {key} (TTL: {ttl}s)")

    def delete(self, key: str, params: Dict = None) -> None:
        """删除缓存"""
        if params is None:
            params = {}

        cache_key = self._make_key(key, params)

        if cache_key in self._cache:
            del self._cache[cache_key]
            self._access_order.remove(cache_key)
            logger.debug(f"缓存删除: {key}")

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("内存缓存已清空")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        current_time = time.time()
        expired_count = sum(1 for _, expire_time in self._cache.values() if self._is_expired(expire_time))
        active_count = len(self._cache) - expired_count

        return {
            'total_entries': len(self._cache),
            'active_entries': active_count,
            'expired_entries': expired_count,
            'max_size': self.maxsize,
            'default_ttl': self.default_ttl,
            'hit_rate': getattr(self, '_hit_rate', 0.0)
        }


class RedisCache:
    """Redis缓存 - 用于分布式环境"""

    def __init__(self, redis_client=None, ttl: int = 3600):
        """
        初始化Redis缓存

        Args:
            redis_client: Redis客户端实例
            ttl: 默认TTL（秒）
        """
        self.redis_client = redis_client
        self.default_ttl = ttl
        self.enabled = redis_client is not None

        if self.enabled:
            logger.info("Redis缓存已启用")
        else:
            logger.warning("Redis缓存未启用，使用内存缓存作为回退")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled:
            return None

        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis获取缓存失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存"""
        if not self.enabled:
            return

        if ttl is None:
            ttl = self.default_ttl

        try:
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Redis缓存设置: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis设置缓存失败: {e}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        if not self.enabled:
            return

        try:
            self.redis_client.delete(key)
            logger.debug(f"Redis缓存删除: {key}")
        except Exception as e:
            logger.error(f"Redis删除缓存失败: {e}")

    def clear(self) -> None:
        """清空缓存"""
        if not self.enabled:
            return

        try:
            self.redis_client.flushdb()
            logger.info("Redis缓存已清空")
        except Exception as e:
            logger.error(f"Redis清空缓存失败: {e}")


class CacheManager:
    """统一缓存管理器"""

    def __init__(self, use_redis: bool = False, redis_client=None, memory_cache_size: int = 128):
        """
        初始化缓存管理器

        Args:
            use_redis: 是否使用Redis
            redis_client: Redis客户端
            memory_cache_size: 内存缓存大小
        """
        self.memory_cache = MemoryCache(maxsize=memory_cache_size)
        self.redis_cache = RedisCache(redis_client=redis_client)
        self.use_redis = use_redis and redis_client is not None

        logger.info(f"缓存管理器初始化完成，Redis: {self.use_redis}, 内存缓存: {memory_cache_size}")

    def get(self, key: str, namespace: str = 'default') -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键
            namespace: 命名空间

        Returns:
            缓存值
        """
        full_key = f"{namespace}:{key}"

        # 优先使用Redis缓存
        if self.use_redis:
            value = self.redis_cache.get(full_key)
            if value is not None:
                return value

        # 回退到内存缓存
        return self.memory_cache.get(full_key)

    def set(self, key: str, value: Any, namespace: str = 'default', ttl: int = 3600) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            namespace: 命名空间
            ttl: TTL（秒）
        """
        full_key = f"{namespace}:{key}"

        # 同时设置Redis和内存缓存
        if self.use_redis:
            self.redis_cache.set(full_key, value, ttl)

        self.memory_cache.set(full_key, value, ttl=ttl)

    def delete(self, key: str, namespace: str = 'default') -> None:
        """
        删除缓存

        Args:
            key: 缓存键
            namespace: 命名空间
        """
        full_key = f"{namespace}:{key}"

        if self.use_redis:
            self.redis_cache.delete(full_key)

        self.memory_cache.delete(full_key)

    def clear(self, namespace: str = None) -> None:
        """
        清空缓存

        Args:
            namespace: 命名空间，如果为None则清空所有
        """
        if namespace:
            # 清空指定命名空间的缓存
            if self.use_redis:
                # Redis需要遍历删除（简化处理）
                self.redis_cache.clear()

            self.memory_cache.clear()
        else:
            # 清空所有缓存
            if self.use_redis:
                self.redis_cache.clear()

            self.memory_cache.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'memory_cache': self.memory_cache.get_stats(),
            'redis_enabled': self.use_redis
        }


# 全局缓存管理器实例
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(key: str, ttl: int = 3600, namespace: str = 'default'):
    """
    缓存装饰器

    Args:
        key: 缓存键前缀
        ttl: TTL（秒）
        namespace: 命名空间

    Example:
        @cached('stock_data', ttl=3600)
        async def get_stock_data(symbol: str, start_date: str, end_date: str):
            # 获取股票数据
            return data
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # 生成缓存键
            params = {
                'args': args,
                'kwargs': kwargs
            }
            cache_key = f"{key}:{hashlib.md5(str(params).encode()).hexdigest()}"

            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key, namespace)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            cache_manager.set(cache_key, result, namespace=namespace, ttl=ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # 生成缓存键
            params = {
                'args': args,
                'kwargs': kwargs
            }
            cache_key = f"{key}:{hashlib.md5(str(params).encode()).hexdigest()}"

            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key, namespace)
            if cached_value is not None:
                return cached_value

            # 缓存未命中，执行函数
            result = func(*args, **kwargs)

            # 设置缓存
            cache_manager.set(cache_key, result, namespace=namespace, ttl=ttl)

            return result

        # 根据函数类型返回装饰器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 便捷函数
def cache_data(key: str, data: Any, ttl: int = 3600, namespace: str = 'data') -> None:
    """手动缓存数据"""
    cache_manager = get_cache_manager()
    cache_manager.set(key, data, namespace=namespace, ttl=ttl)


def get_cached_data(key: str, namespace: str = 'data') -> Optional[Any]:
    """手动获取缓存数据"""
    cache_manager = get_cache_manager()
    return cache_manager.get(key, namespace=namespace)


def invalidate_cache(key: str, namespace: str = 'data') -> None:
    """使缓存失效"""
    cache_manager = get_cache_manager()
    cache_manager.delete(key, namespace=namespace)


def clear_cache(namespace: str = None) -> None:
    """清空缓存"""
    cache_manager = get_cache_manager()
    cache_manager.clear(namespace=namespace)
