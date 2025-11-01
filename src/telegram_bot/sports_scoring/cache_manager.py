"""
緩存管理器
實現多層緩存策略
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import hashlib


logger = logging.getLogger(__name__)


class CacheManager:
    """緩存管理器"""

    def __init__(self, default_ttl: int = 120):  # 默認 2 分鐘
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, namespace: str, **kwargs) -> str:
        """
        生成緩存鍵

        Args:
            namespace: 命名空間
            **kwargs: 參數

        Returns:
            str: 緩存鍵
        """
        # 將參數轉換為字符串並排序
        params = sorted([f"{k}={v}" for k, v in kwargs.items()])
        param_str = "&".join(params)

        # 生成哈希
        key_data = f"{namespace}:{param_str}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]

        return f"{namespace}:{key_hash}"

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """檢查緩存是否過期"""
        expiry = entry.get("expiry")
        return datetime.now() > expiry

    async def get(self, namespace: str, **kwargs) -> Optional[Any]:
        """
        獲取緩存

        Args:
            namespace: 命名空間
            **kwargs: 參數

        Returns:
            Optional[Any]: 緩存值，如果不存在或已過期則返回 None
        """
        key = self._generate_key(namespace, **kwargs)

        if key not in self.cache:
            self.misses += 1
            logger.debug(f"[Cache] Key not found: {key}")
            return None

        entry = self.cache[key]

        if self._is_expired(entry):
            # 過期了，刪除並返回 None
            del self.cache[key]
            self.misses += 1
            logger.debug(f"[Cache] Key expired: {key}")
            return None

        # 命中
        self.hits += 1
        logger.debug(f"[Cache] Hit: {key}")
        return entry["data"]

    async def set(self, namespace: str, data: Any, ttl: Optional[int] = None, **kwargs) -> None:
        """
        設置緩存

        Args:
            namespace: 命名空間
            data: 要緩存的數據
            ttl: 生存時間（秒），如果為 None 則使用默認值
            **kwargs: 參數
        """
        key = self._generate_key(namespace, **kwargs)

        ttl = ttl if ttl is not None else self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)

        self.cache[key] = {
            "data": data,
            "created": datetime.now(),
            "expiry": expiry,
            "namespace": namespace,
            "params": kwargs
        }

        logger.debug(f"[Cache] Set: {key}, TTL: {ttl}s")

    async def delete(self, namespace: str, **kwargs) -> bool:
        """
        刪除緩存

        Args:
            namespace: 命名空間
            **kwargs: 參數

        Returns:
            bool: 是否成功刪除
        """
        key = self._generate_key(namespace, **kwargs)

        if key in self.cache:
            del self.cache[key]
            logger.debug(f"[Cache] Deleted: {key}")
            return True

        return False

    async def clear(self, namespace: Optional[str] = None) -> int:
        """
        清空緩存

        Args:
            namespace: 如果指定，則只清空指定命名空間

        Returns:
            int: 刪除的條目數
        """
        if namespace is None:
            count = len(self.cache)
            self.cache.clear()
            logger.debug(f"[Cache] Cleared all entries ({count})")
            return count

        keys_to_delete = [k for k, v in self.cache.items() if v["namespace"] == namespace]
        for key in keys_to_delete:
            del self.cache[key]

        logger.debug(f"[Cache] Cleared namespace '{namespace}' ({len(keys_to_delete)} entries)")
        return len(keys_to_delete)

    async def cleanup_expired(self) -> int:
        """
        清理過期的緩存

        Returns:
            int: 清理的條目數
        """
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]

        for key in keys_to_delete:
            del self.cache[key]

        logger.debug(f"[Cache] Cleaned up {len(keys_to_delete)} expired entries")
        return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        # 按命名空間統計
        namespaces = {}
        for entry in self.cache.values():
            ns = entry["namespace"]
            namespaces[ns] = namespaces.get(ns, 0) + 1

        return {
            "total_entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "namespaces": namespaces,
            "default_ttl": self.default_ttl
        }

    async def bulk_get(self, namespace: str, param_sets: list) -> Dict[str, Optional[Any]]:
        """
        批量獲取緩存

        Args:
            namespace: 命名空間
            param_sets: 參數集列表，每個元素是一個 kwargs 字典

        Returns:
            Dict[str, Optional[Any]]: 結果字典，鍵為參數哈希，值為緩存值
        """
        results = {}

        # 清理過期緩存
        await self.cleanup_expired()

        for params in param_sets:
            key = self._generate_key(namespace, **params)
            value = await self.get(namespace, **params)
            results[key] = value

        return results

    async def get_or_set(self, namespace: str, factory_func, ttl: Optional[int] = None, **kwargs) -> Any:
        """
        獲取或設置：如果緩存存在則返回，否則調用 factory_func 生成數據

        Args:
            namespace: 命名空間
            factory_func: 生成數據的異步函數
            ttl: 生存時間
            **kwargs: 參數

        Returns:
            Any: 數據
        """
        # 先嘗試獲取
        cached_value = await self.get(namespace, **kwargs)
        if cached_value is not None:
            return cached_value

        # 緩存不存在，生成數據
        logger.debug(f"[Cache] Cache miss, generating data for: {namespace}")
        value = await factory_func()

        # 設置緩存
        await self.set(namespace, value, ttl, **kwargs)

        return value
