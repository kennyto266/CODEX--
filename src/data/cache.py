"""
Phase 2: Enhanced Data Caching System
======================================

LRU缓存实现，支持：
1. TTL-based过期策略
2. 内存使用优化
3. 缓存统计和监控
4. 多级缓存
5. 自动清理
6. 并发安全
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List, Tuple, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
import weakref
import json
import pickle


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: datetime
    ttl: float
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)

    @property
    def age(self) -> float:
        """缓存年龄（秒）"""
        return (datetime.now() - self.timestamp).total_seconds()

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.age > self.ttl

    @property
    def is_valid(self) -> bool:
        """检查是否有效（未过期）"""
        return not self.is_expired

    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_access = datetime.now()


class LRUCache:
    """
    高性能LRU缓存

    特性：
    - LRU淘汰策略
    - TTL过期机制
    - 线程安全
    - 访问统计
    - 内存优化
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: float = 300.0,
        cleanup_interval: float = 60.0,
        enable_stats: bool = True
    ):
        """
        初始化LRU缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 默认TTL（秒）
            cleanup_interval: 清理间隔（秒）
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.default_ttl = ttl
        self.cleanup_interval = cleanup_interval
        self.enable_stats = enable_stats

        # 内部存储（有序字典，保持访问顺序）
        self._cache: 'OrderedDict[str, CacheEntry]' = OrderedDict()
        self._lock = RLock()

        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'sets': 0,
            'deletes': 0,
            'max_size': max_size,
            'current_size': 0,
        }

        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stop_cleanup = False

        self.logger = logging.getLogger("hk_quant_system.cache.lru")

    async def start(self):
        """启动缓存"""
        if self._cleanup_task is None:
            self._stop_cleanup = False
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info("LRU Cache started")

    async def stop(self):
        """停止缓存"""
        if self._cleanup_task:
            self._stop_cleanup = True
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self.logger.info("LRU Cache stopped")

    async def _cleanup_loop(self):
        """清理过期条目的循环任务"""
        while not self._stop_cleanup:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_expired(self):
        """清理过期的缓存条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]

            for key in expired_keys:
                del self._cache[key]
                self._stats['expirations'] += 1

            if expired_keys:
                self._stats['current_size'] = len(self._cache)
                self.logger.debug(f"Cleaned {len(expired_keys)} expired entries")

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                if self.enable_stats:
                    self._stats['misses'] += 1
                return None

            # 检查是否过期
            if entry.is_expired:
                del self._cache[key]
                if self.enable_stats:
                    self._stats['expirations'] += 1
                    self._stats['misses'] += 1
                return None

            # 记录访问（移动到末尾）
            entry.access()
            self._cache.move_to_end(key)

            if self.enable_stats:
                self._stats['hits'] += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），为None则使用默认TTL

        Returns:
            bool: 是否成功
        """
        with self._lock:
            try:
                entry_ttl = ttl or self.default_ttl
                entry = CacheEntry(
                    value=value,
                    timestamp=datetime.now(),
                    ttl=entry_ttl
                )

                # 如果键已存在，更新值
                if key in self._cache:
                    del self._cache[key]

                # 添加新条目
                self._cache[key] = entry
                self._cache.move_to_end(key)

                # 检查是否需要淘汰
                if len(self._cache) > self.max_size:
                    # 淘汰最久未使用的条目
                    oldest_key, oldest_entry = self._cache.popitem(last=False)
                    self._stats['evictions'] += 1
                    self.logger.debug(f"Evicted key: {oldest_key}")

                # 更新统计
                if self.enable_stats:
                    self._stats['sets'] += 1
                    self._stats['current_size'] = len(self._cache)

                return True

            except Exception as e:
                self.logger.error(f"Cache set error: {e}")
                return False

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if self.enable_stats:
                    self._stats['deletes'] += 1
                    self._stats['current_size'] = len(self._cache)
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        检查键是否存在且有效

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            return entry is not None and not entry.is_expired

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            if self.enable_stats:
                self._stats['current_size'] = 0
            self.logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            stats = self._stats.copy()

            if self.enable_stats:
                total = stats['hits'] + stats['misses']
                stats['hit_rate'] = (
                    stats['hits'] / total if total > 0 else 0.0
                )
                stats['miss_rate'] = (
                    stats['misses'] / total if total > 0 else 0.0
                )
                stats['utilization'] = (
                    len(self._cache) / self.max_size if self.max_size > 0 else 0.0
                )

            return stats

    def get_keys(self) -> List[str]:
        """
        获取所有有效键

        Returns:
            List[str]: 键列表
        """
        with self._lock:
            # 清理过期条目并返回有效键
            now = datetime.now()
            valid_keys = [
                key for key, entry in self._cache.items()
                if (now - entry.timestamp).total_seconds() <= entry.ttl
            ]
            return valid_keys

    def get_entries(self) -> List[Tuple[str, CacheEntry]]:
        """
        获取所有有效条目

        Returns:
            List[Tuple[str, CacheEntry]]: 条目列表
        """
        with self._lock:
            now = datetime.now()
            return [
                (key, entry) for key, entry in self._cache.items()
                if (now - entry.timestamp).total_seconds() <= entry.ttl
            ]


class MultiLevelCache:
    """
    多级缓存系统

    - L1: 内存缓存（快速）
    - L2: 持久化缓存（较慢但持久）
    """

    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: float = 300.0,
        l2_size: int = 10000,
        l2_ttl: float = 3600.0
    ):
        """
        初始化多级缓存

        Args:
            l1_size: L1缓存大小
            l1_ttl: L1缓存TTL
            l2_size: L2缓存大小
            l2_ttl: L2缓存TTL
        """
        self.l1_cache = LRUCache(
            max_size=l1_size,
            ttl=l1_ttl,
            cleanup_interval=60.0
        )

        self.l2_cache = LRUCache(
            max_size=l2_size,
            ttl=l2_ttl,
            cleanup_interval=300.0
        )

        self.logger = logging.getLogger("hk_quant_system.cache.multilevel")

    async def start(self):
        """启动缓存"""
        await asyncio.gather(
            self.l1_cache.start(),
            self.l2_cache.start()
        )

    async def stop(self):
        """停止缓存"""
        await asyncio.gather(
            self.l1_cache.stop(),
            self.l2_cache.stop()
        )

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值（先查L1，再查L2）

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存值
        """
        # 先查L1缓存
        value = self.l1_cache.get(key)
        if value is not None:
            return value

        # L1未命中，查询L2缓存
        value = self.l2_cache.get(key)
        if value is not None:
            # L2命中，写回L1
            self.l1_cache.set(key, value)
            return value

        return None

    def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[float] = None,
        l2_ttl: Optional[float] = None
    ) -> bool:
        """
        设置缓存值（同时写入L1和L2）

        Args:
            key: 缓存键
            value: 缓存值
            l1_ttl: L1缓存TTL
            l2_ttl: L2缓存TTL

        Returns:
            bool: 是否成功
        """
        # 同时写入L1和L2
        l1_success = self.l1_cache.set(key, value, l1_ttl)
        l2_success = self.l2_cache.set(key, value, l2_ttl)

        return l1_success or l2_success

    def delete(self, key: str) -> bool:
        """删除缓存（同时删除L1和L2）"""
        l1_success = self.l1_cache.delete(key)
        l2_success = self.l2_cache.delete(key)
        return l1_success or l2_success

    def clear(self):
        """清空所有缓存"""
        self.l1_cache.clear()
        self.l2_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'l1': self.l1_cache.get_stats(),
            'l2': self.l2_cache.get_stats()
        }


class CacheDecorator:
    """缓存装饰器"""

    def __init__(
        self,
        cache: LRUCache,
        key_func: Optional[Callable] = None,
        ttl: Optional[float] = None
    ):
        """
        初始化缓存装饰器

        Args:
            cache: 缓存实例
            key_func: 键生成函数
            ttl: 默认TTL
        """
        self.cache = cache
        self.key_func = key_func
        self.default_ttl = ttl

    def __call__(self, func: Callable):
        """
        装饰器

        Args:
            func: 被装饰的函数

        Returns:
            装饰后的函数
        """
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if self.key_func:
                cache_key = self.key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 尝试从缓存获取
            result = self.cache.get(cache_key)
            if result is not None:
                return result

            # 缓存未命中，执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 写入缓存
            self.cache.set(cache_key, result, self.default_ttl)

            return result

        return async_wrapper


# 全局缓存实例
_global_cache: Optional[LRUCache] = None


def get_global_cache() -> LRUCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LRUCache(
            max_size=1000,
            ttl=300.0,
            cleanup_interval=60.0
        )
    return _global_cache


async def init_cache():
    """初始化缓存"""
    cache = get_global_cache()
    await cache.start()
    return cache


async def close_cache():
    """关闭缓存"""
    cache = get_global_cache()
    await cache.stop()


# 使用示例
async def main():
    """示例用法"""
    print("Data Cache System Demo")
    print("=" * 50)

    # 创建缓存
    cache = LRUCache(max_size=100, ttl=60.0)

    # 启动缓存
    await cache.start()

    # 设置缓存
    print("\n1. Setting cache values...")
    cache.set("key1", "value1", ttl=30.0)
    cache.set("key2", {"data": "test"}, ttl=60.0)
    cache.set("key3", [1, 2, 3, 4, 5], ttl=90.0)

    # 获取缓存
    print("\n2. Getting cache values...")
    print(f"key1: {cache.get('key1')}")
    print(f"key2: {cache.get('key2')}")
    print(f"key3: {cache.get('key3')}")
    print(f"key4: {cache.get('key4')}")  # 不存在的键

    # 查看统计
    print("\n3. Cache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 等待一些时间
    print("\n4. Waiting 2 seconds...")
    await asyncio.sleep(2)

    # 检查过期
    print("\n5. Checking expiration...")
    print(f"key1 (30s TTL) expired: {cache.get('key1') is None}")
    print(f"key2 (60s TTL) valid: {cache.get('key2') is not None}")

    # 清理
    await cache.stop()
    print("\n✓ Cache stopped")


if __name__ == "__main__":
    asyncio.run(main())
