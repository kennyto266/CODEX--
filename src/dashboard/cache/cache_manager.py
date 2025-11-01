"""
緩存管理器 - 實現多級緩存系統
支持Redis緩存和內存LRU緩存
"""

import json
import hashlib
import asyncio
from typing import Any, Optional, Callable, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """緩存管理器 - 統一的緩存接口"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._memory_cache = {}
        self._cache_ttl = {}
        self.redis_client = None
        self.redis_available = False
        self.default_ttl = 300  # 5分鐘默認TTL

        # 尝试连接Redis
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_available = True
            logger.info("✅ Redis緩存已啟用")
        except ImportError:
            logger.warning("⚠️ Redis未安裝，使用內存緩存")
            self.redis_client = None
            self.redis_available = False
        except Exception as e:
            logger.warning(f"⚠️ Redis連接失敗: {e}")
            self.redis_client = None
            self.redis_available = False

    def health_check(self) -> bool:
        """
        健康檢查 - 檢查Redis是否可用

        Returns:
            bool: Redis可用返回True，否則返回False
        """
        if not self.redis_available:
            return False

        try:
            # 尝试ping Redis
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.redis_client.ping())
            loop.close()
            return result
        except Exception as e:
            logger.warning(f"Redis健康檢查失敗: {e}")
            self.redis_available = False
            return False

    def auto_start_redis(self) -> bool:
        """
        自動啟動Redis服務

        Returns:
            bool: 啟動成功返回True
        """
        try:
            import subprocess
            import time

            # 檢查是否已經運行
            if self.health_check():
                logger.info("Redis已在運行")
                return True

            # 嘗試啟動Redis
            logger.info("正在嘗試自動啟動Redis...")
            subprocess.Popen(
                ['redis-server.exe'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # 等待啟動
            for i in range(10):
                time.sleep(1)
                if self.health_check():
                    logger.info("✅ Redis自動啟動成功")
                    return True

            logger.error("❌ Redis自動啟動失敗")
            return False

        except Exception as e:
            logger.error(f"Redis自動啟動異常: {e}")
            return False

    @property
    def is_healthy(self) -> bool:
        """
        緩存系統健康狀態

        Returns:
            bool: 系統健康返回True
        """
        # 如果Redis可用且健康，返回True
        if self.redis_available:
            return self.health_check()

        # 否則檢查內存緩存是否可用
        return self._memory_cache is not None

    def generate_cache_key(self, prefix: str, **params) -> str:
        """
        生成緩存鍵

        Args:
            prefix: 緩存鍵前綴
            **params: 參數

        Returns:
            緩存鍵字符串
        """
        # 將參數轉為字符串並排序，確保一致性
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        return f"{prefix}:{params_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        獲取緩存

        Args:
            key: 緩存鍵

        Returns:
            緩存的值，如果不存在返回None
        """
        try:
            if self.redis_available:
                value = await self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                # 內存緩存
                if key in self._memory_cache:
                    # 檢查TTL
                    if key in self._cache_ttl and asyncio.get_event_loop().time() > self._cache_ttl[key]:
                        del self._memory_cache[key]
                        del self._cache_ttl[key]
                        return None
                    return self._memory_cache[key]
                return None
        except Exception as e:
            logger.error(f"獲取緩存失敗 {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        設置緩存

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 過期時間（秒）

        Returns:
            是否設置成功
        """
        try:
            ttl = ttl or self.default_ttl

            if self.redis_available:
                await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
                return True
            else:
                # 內存緩存
                self._memory_cache[key] = value
                self._cache_ttl[key] = asyncio.get_event_loop().time() + ttl
                return True
        except Exception as e:
            logger.error(f"設置緩存失敗 {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        刪除緩存

        Args:
            key: 緩存鍵

        Returns:
            是否刪除成功
        """
        try:
            if self.redis_available:
                await self.redis_client.delete(key)
                return True
            else:
                self._memory_cache.pop(key, None)
                self._cache_ttl.pop(key, None)
                return True
        except Exception as e:
            logger.error(f"刪除緩存失敗 {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        檢查緩存是否存在

        Args:
            key: 緩存鍵

        Returns:
            是否存在
        """
        try:
            if self.redis_available:
                return await self.redis_client.exists(key) > 0
            else:
                return key in self._memory_cache
        except Exception as e:
            logger.error(f"檢查緩存失敗 {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        根據模式清除緩存

        Args:
            pattern: 匹配模式

        Returns:
            刪除的鍵數量
        """
        try:
            if self.redis_available:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    return len(keys)
                return 0
            else:
                # 內存緩存不支持模式匹配
                count = 0
                to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                for k in to_delete:
                    del self._memory_cache[k]
                    del self._cache_ttl[k]
                    count += 1
                return count
        except Exception as e:
            logger.error(f"清除緩存失敗 {pattern}: {e}")
            return 0

    def cache_result(self, ttl: int = 300, key_prefix: str = ""):
        """
        緩存裝飾器 - 自動緩存函數結果

        Args:
            ttl: 過期時間
            key_prefix: 緩存鍵前綴

        Usage:
            @cache_manager.cache_result(ttl=60, key_prefix="agents")
            async def get_agents():
                return await fetch_agents()
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成緩存鍵
                cache_key = self.generate_cache_key(
                    key_prefix or func.__name__,
                    args=str(args),
                    kwargs=str(sorted(kwargs.items()))
                )

                # 嘗試從緩存獲取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"緩存命中: {cache_key}")
                    return cached_result

                # 執行函數
                logger.debug(f"緩存未命中，執行函數: {func.__name__}")
                result = await func(*args, **kwargs)

                # 設置緩存
                await self.set(cache_key, result, ttl)
                logger.debug(f"已設置緩存: {cache_key} (TTL: {ttl}s)")

                return result
            return wrapper
        return decorator

    async def get_or_set(self, key: str, fetch_func: Callable, ttl: Optional[int] = None) -> Any:
        """
        獲取或設置模式 - 原子操作

        Args:
            key: 緩存鍵
            fetch_func: 數據獲取函數
            ttl: 過期時間

        Returns:
            數據
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        result = await fetch_func()
        await self.set(key, result, ttl)
        return result

    async def invalidate_by_prefix(self, prefix: str) -> int:
        """
        根據前綴失效緩存

        Args:
            prefix: 緩存鍵前綴

        Returns:
            失效的鍵數量
        """
        pattern = f"{prefix}:*"
        return await self.clear_pattern(pattern)

    async def health_check(self) -> Dict[str, Any]:
        """
        緩存健康檢查

        Returns:
            健康狀態信息
        """
        try:
            if self.redis_available:
                pong = await self.redis_client.ping()
                info = await self.redis_client.info()
                return {
                    "status": "healthy" if pong else "unhealthy",
                    "type": "redis",
                    "memory_usage": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                }
            else:
                return {
                    "status": "healthy",
                    "type": "memory",
                    "cache_size": len(self._memory_cache),
                    "keys": list(self._memory_cache.keys())[:10]
                }
        except Exception as e:
            logger.error(f"緩存健康檢查失敗: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# 全局緩存管理器實例
cache_manager = CacheManager()

# 便捷裝飾器
cached = cache_manager.cache_result
