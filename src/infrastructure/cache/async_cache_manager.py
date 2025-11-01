"""
異步緩存管理器

支持多級緩存架構：
- L1: 內存緩存 (LRU Cache)
- L2: Redis緩存 (分佈式)
- L3: 數據庫緩存 (持久化)

所有操作均為異步，支持連接池、超時控制、緩存失效策略
"""

import asyncio
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

import aioredis
from cachetools import TTLCache, LRUCache

from src.core.logging import get_logger


logger = get_logger("async_cache_manager")


@dataclass
class CacheConfig:
    """緩存配置"""
    # L1 內存緩存配置
    l1_enabled: bool = True
    l1_max_size: int = 10000  # 最大緩存項數
    l1_ttl: int = 300  # 生存時間(秒)

    # L2 Redis緩存配置
    l2_enabled: bool = True
    l2_host: str = "localhost"
    l2_port: int = 6379
    l2_db: int = 0
    l2_password: Optional[str] = None
    l2_ttl: int = 3600  # 生存時間(秒)
    l2_max_connections: int = 50
    l2_socket_timeout: int = 5
    l2_socket_connect_timeout: int = 5

    # L3 數據庫緩存配置
    l3_enabled: bool = False  # 可選，預設為False
    l3_ttl: int = 86400  # 24小時

    # 緩存策略
    cache_strategy: str = "write_through"  # write_through, write_back, write_around
    preload_on_miss: bool = True  # 緩存未命中時是否預加載

    # 監控
    enable_metrics: bool = True
    metrics_interval: int = 60  # 秒


@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    size_bytes: Optional[int] = None


@dataclass
class CacheMetrics:
    """緩存指標"""
    hits: int = 0
    misses: int = 0
    hits_l1: int = 0
    hits_l2: int = 0
    hits_l3: int = 0
    sets: int = 0
    deletes: int = 0
    evictions_l1: int = 0
    evictions_l2: int = 0
    errors: int = 0

    @property
    def hit_ratio(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def total_requests(self) -> int:
        """總請求數"""
        return self.hits + self.misses


class CacheLevel(ABC):
    """緩存層抽象基類"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置緩存"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """刪除緩存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """清空緩存"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        pass

    async def close(self) -> None:
        """關閉連接"""
        pass


class L1MemoryCache(CacheLevel):
    """L1 內存緩存 (LRU + TTL)"""

    def __init__(self, max_size: int = 10000, ttl: int = 300):
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # LRU追蹤
        self.max_size = max_size
        self.ttl = ttl
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            entry = self.cache.get(key)
            if entry:
                # 檢查TTL
                if self.ttl and (time.time() - entry.created_at.timestamp()) > self.ttl:
                    del self.cache[key]
                    self.access_order.remove(key)
                    return None

                # 更新LRU
                self.access_order.remove(key)
                self.access_order.append(key)
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.value
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self.lock:
            effective_ttl = ttl if ttl is not None else self.ttl

            # 檢查是否已存在
            if key in self.cache:
                self.cache[key].value = value
                self.cache[key].last_accessed = datetime.now()
                self.access_order.remove(key)
                self.access_order.append(key)
                return True

            # 檢查是否需要驅逐
            if len(self.cache) >= self.max_size:
                # 驅逐最少使用的項
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]

            # 添加新項
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=effective_ttl
            )
            self.cache[key] = entry
            self.access_order.append(key)
            return True

    async def delete(self, key: str) -> bool:
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return True
            return False

    async def exists(self, key: str) -> bool:
        async with self.lock:
            return key in self.cache

    async def clear(self) -> bool:
        async with self.lock:
            self.cache.clear()
            self.access_order.clear()
            return True

    async def get_stats(self) -> Dict[str, Any]:
        async with self.lock:
            return {
                "type": "L1_Memory",
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "utilization": len(self.cache) / self.max_size
            }


class L2RedisCache(CacheLevel):
    """L2 Redis緩存"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 password: Optional[str] = None, ttl: int = 3600,
                 max_connections: int = 50):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ttl = ttl
        self.max_connections = max_connections
        self._pool: Optional[aioredis.Redis] = None

    async def _get_pool(self) -> aioredis.Redis:
        """獲取Redis連接池"""
        if self._pool is None:
            self._pool = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=5,
                socket_connect_timeout=5
            )
        return self._pool

    async def get(self, key: str) -> Optional[Any]:
        try:
            redis = await self._get_pool()
            data = await redis.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"L2 Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            redis = await self._get_pool()
            effective_ttl = ttl if ttl is not None else self.ttl
            await redis.set(key, pickle.dumps(value), ex=effective_ttl)
            return True
        except Exception as e:
            logger.error(f"L2 Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            redis = await self._get_pool()
            result = await redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"L2 Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            redis = await self._get_pool()
            result = await redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"L2 Redis exists error: {e}")
            return False

    async def clear(self) -> bool:
        try:
            redis = await self._get_pool()
            await redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"L2 Redis clear error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        try:
            redis = await self._get_pool()
            info = await redis.info()
            return {
                "type": "L2_Redis",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "ttl": self.ttl
            }
        except Exception as e:
            logger.error(f"L2 Redis stats error: {e}")
            return {"type": "L2_Redis", "error": str(e)}

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None


class L3DatabaseCache(CacheLevel):
    """L3 數據庫緩存 (可選)"""

    def __init__(self, ttl: int = 86400):
        self.ttl = ttl
        # 這裡可以集成實際的數據庫，比如SQLite、PostgreSQL等
        # 為了簡化，這裡使用內存字典作為占位符

    async def get(self, key: str) -> Optional[Any]:
        # TODO: 實現數據庫查詢
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # TODO: 實現數據庫插入
        return False

    async def delete(self, key: str) -> bool:
        # TODO: 實現數據庫刪除
        return False

    async def exists(self, key: str) -> bool:
        # TODO: 實現數據庫查詢
        return False

    async def clear(self) -> bool:
        # TODO: 實現數據庫清空
        return False

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "type": "L3_Database",
            "ttl": self.ttl,
            "status": "not_implemented"
        }


class AsyncCacheManager:
    """異步多級緩存管理器"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = get_logger("cache_manager")
        self.metrics = CacheMetrics()
        self._l1_cache: Optional[L1MemoryCache] = None
        self._l2_cache: Optional[L2RedisCache] = None
        self._l3_cache: Optional[L3DatabaseCache] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """初始化緩存"""
        try:
            self.logger.info("Initializing cache manager...")

            # 初始化 L1
            if self.config.l1_enabled:
                self._l1_cache = L1MemoryCache(
                    max_size=self.config.l1_max_size,
                    ttl=self.config.l1_ttl
                )
                self.logger.info(f"L1 Memory cache initialized: {self.config.l1_max_size} items")

            # 初始化 L2
            if self.config.l2_enabled:
                self._l2_cache = L2RedisCache(
                    host=self.config.l2_host,
                    port=self.config.l2_port,
                    db=self.config.l2_db,
                    password=self.config.l2_password,
                    ttl=self.config.l2_ttl,
                    max_connections=self.config.l2_max_connections
                )
                # 測試連接
                if await self._l2_cache.get("__test__") is not None:
                    self.logger.info("L2 Redis cache initialized")
                else:
                    self.logger.warning("L2 Redis cache initialized (with test)")

            # 初始化 L3
            if self.config.l3_enabled:
                self._l3_cache = L3DatabaseCache(ttl=self.config.l3_ttl)
                self.logger.info("L3 Database cache initialized")

            self.logger.info("Cache manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {e}")
            return False

    async def get(self, key: str) -> Tuple[Optional[Any], str]:
        """
        獲取緩存 (從L1 -> L2 -> L3)

        Returns:
            Tuple[value, cache_level]: 值和命中緩存層
        """
        try:
            # L1 查詢
            if self._l1_cache:
                value = await self._l1_cache.get(key)
                if value is not None:
                    self.metrics.hits += 1
                    self.metrics.hits_l1 += 1
                    return value, "L1"

            # L2 查詢
            if self._l2_cache:
                value = await self._l2_cache.get(key)
                if value is not None:
                    self.metrics.hits += 1
                    self.metrics.hits_l2 += 1
                    # 回寫L1
                    if self._l1_cache:
                        await self._l1_cache.set(key, value)
                    return value, "L2"

            # L3 查詢
            if self._l3_cache:
                value = await self._l3_cache.get(key)
                if value is not None:
                    self.metrics.hits += 1
                    self.metrics.hits_l3 += 1
                    # 回寫L1和L2
                    if self._l1_cache:
                        await self._l1_cache.set(key, value)
                    if self._l2_cache:
                        await self._l2_cache.set(key, value)
                    return value, "L3"

            # 緩存未命中
            self.metrics.misses += 1
            return None, "MISS"

        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.metrics.errors += 1
            return None, "ERROR"

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置緩存 (寫通/寫回/繞過策略)"""
        try:
            strategy = self.config.cache_strategy

            if strategy == "write_through":
                # 寫通：同時寫入所有層
                tasks = []

                if self._l1_cache:
                    tasks.append(self._l1_cache.set(key, value, ttl))
                if self._l2_cache:
                    tasks.append(self._l2_cache.set(key, value, ttl))
                if self._l3_cache:
                    tasks.append(self._l3_cache.set(key, value, ttl))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                success = all(not isinstance(r, Exception) for r in results)

            elif strategy == "write_back":
                # 寫回：只寫L1，異步寫入L2/L3
                l1_success = True
                if self._l1_cache:
                    l1_success = await self._l1_cache.set(key, value, ttl)

                if l1_success:
                    asyncio.create_task(self._async_write_back(key, value, ttl))

                success = l1_success

            elif strategy == "write_around":
                # 繞過：直接寫L2/L3，跳過L1
                tasks = []

                if self._l2_cache:
                    tasks.append(self._l2_cache.set(key, value, ttl))
                if self._l3_cache:
                    tasks.append(self._l3_cache.set(key, value, ttl))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                success = all(not isinstance(r, Exception) for r in results)

            else:
                self.logger.warning(f"Unknown cache strategy: {strategy}")
                success = False

            if success:
                self.metrics.sets += 1

            return success

        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            self.metrics.errors += 1
            return False

    async def _async_write_back(self, key: str, value: Any, ttl: Optional[int]) -> None:
        """異步寫回 L2/L3"""
        try:
            if self._l2_cache:
                await self._l2_cache.set(key, value, ttl)
            if self._l3_cache:
                await self._l3_cache.set(key, value, ttl)
        except Exception as e:
            self.logger.error(f"Async write back error for key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """刪除緩存"""
        try:
            tasks = []
            if self._l1_cache:
                tasks.append(self._l1_cache.delete(key))
            if self._l2_cache:
                tasks.append(self._l2_cache.delete(key))
            if self._l3_cache:
                tasks.append(self._l3_cache.delete(key))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = any(r is True for r in results)

            if success:
                self.metrics.deletes += 1

            return success

        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            self.metrics.errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        try:
            if self._l1_cache and await self._l1_cache.exists(key):
                return True
            if self._l2_cache and await self._l2_cache.exists(key):
                return True
            if self._l3_cache and await self._l3_cache.exists(key):
                return True
            return False
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {e}")
            self.metrics.errors += 1
            return False

    async def clear(self, level: Optional[str] = None) -> bool:
        """
        清空緩存

        Args:
            level: 指定層 (L1, L2, L3)，None表示清空所有層
        """
        try:
            tasks = []

            if level is None or level == "L1":
                if self._l1_cache:
                    tasks.append(self._l1_cache.clear())
            if level is None or level == "L2":
                if self._l2_cache:
                    tasks.append(self._l2_cache.clear())
            if level is None or level == "L3":
                if self._l3_cache:
                    tasks.append(self._l3_cache.clear())

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(not isinstance(r, Exception) for r in results)

        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            self.metrics.errors += 1
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取緩存指標"""
        return {
            "metrics": self.metrics.__dict__,
            "l1_stats": await self._l1_cache.get_stats() if self._l1_cache else None,
            "l2_stats": await self._l2_cache.get_stats() if self._l2_cache else None,
            "l3_stats": await self._l3_cache.get_stats() if self._l3_cache else None,
        }

    async def preload(self, keys: List[str], fetcher_func) -> None:
        """
        預加載緩存

        Args:
            keys: 要預加載的鍵列表
            fetcher_func: 異步獲取值函數，接受key參數
        """
        if not self.config.preload_on_miss:
            return

        try:
            self.logger.info(f"Preloading {len(keys)} cache entries")

            async def fetch_and_cache(key: str):
                try:
                    value = await fetcher_func(key)
                    if value is not None:
                        await self.set(key, value)
                        self.logger.debug(f"Preloaded cache for key: {key}")
                except Exception as e:
                    self.logger.error(f"Error preloading key {key}: {e}")

            tasks = [fetch_and_cache(key) for key in keys]
            await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.info("Cache preloading completed")

        except Exception as e:
            self.logger.error(f"Cache preloading error: {e}")

    async def close(self) -> None:
        """關閉緩存連接"""
        try:
            if self._l2_cache:
                await self._l2_cache.close()
            self.logger.info("Cache manager closed")
        except Exception as e:
            self.logger.error(f"Error closing cache manager: {e}")


# 全局緩存實例
_global_cache_manager: Optional[AsyncCacheManager] = None


def get_cache_manager(config: Optional[CacheConfig] = None) -> AsyncCacheManager:
    """獲取全局緩存管理器實例"""
    global _global_cache_manager
    if _global_cache_manager is None:
        if config is None:
            config = CacheConfig()
        _global_cache_manager = AsyncCacheManager(config)
    return _global_cache_manager


async def init_cache(config: Optional[CacheConfig] = None) -> bool:
    """初始化全局緩存"""
    cache_manager = get_cache_manager(config)
    return await cache_manager.initialize()


async def close_cache() -> None:
    """關閉全局緩存"""
    global _global_cache_manager
    if _global_cache_manager:
        await _global_cache_manager.close()
        _global_cache_manager = None
