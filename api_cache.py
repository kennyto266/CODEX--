#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API缓存机制 - 提升API响应性能
"""

import json
import time
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class APICache:
    """高性能API缓存"""

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        初始化缓存

        Args:
            default_ttl: 默认缓存时间（秒）
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _generate_key(self, endpoint: str, params: Dict = None) -> str:
        """生成缓存键"""
        key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        return time.time() > cache_entry['expires_at']

    def _evict_old_entries(self):
        """淘汰旧缓存条目"""
        if len(self.cache) <= self.max_size:
            return

        # 按访问时间排序，删除最旧的条目
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1]['access_time']
        )

        # 删除最旧的20%
        num_to_delete = max(1, len(sorted_entries) // 5)
        for i in range(num_to_delete):
            del self.cache[sorted_entries[i][0]]

    def get(self, endpoint: str, params: Dict = None) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            缓存的数据或None
        """
        key = self._generate_key(endpoint, params)

        if key not in self.cache:
            self.misses += 1
            return None

        cache_entry = self.cache[key]

        if self._is_expired(cache_entry):
            del self.cache[key]
            self.misses += 1
            return None

        # 更新访问时间
        cache_entry['access_time'] = time.time()
        cache_entry['hits'] += 1
        self.hits += 1

        return cache_entry['data']

    def set(self, endpoint: str, data: Any, params: Dict = None, ttl: int = None) -> None:
        """
        设置缓存数据

        Args:
            endpoint: API端点
            data: 要缓存的数据
            params: 请求参数
            ttl: 缓存时间（秒）
        """
        key = self._generate_key(endpoint, params)
        ttl = ttl or self.default_ttl

        cache_entry = {
            'data': data,
            'created_at': time.time(),
            'expires_at': time.time() + ttl,
            'access_time': time.time(),
            'hits': 0
        }

        self.cache[key] = cache_entry

        # 淘汰旧条目
        self._evict_old_entries()

    def delete(self, endpoint: str, params: Dict = None) -> bool:
        """删除缓存条目"""
        key = self._generate_key(endpoint, params)
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "default_ttl": self.default_ttl
        }

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)


# 创建全局缓存实例
api_cache = APICache(default_ttl=300, max_size=1000)


def cache_response(ttl: int = 300):
    """
    缓存装饰器

    Args:
        ttl: 缓存时间（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成端点标识
            endpoint = f"{func.__name__}"
            params = kwargs.copy()

            # 尝试从缓存获取
            cached_result = api_cache.get(endpoint, params)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            api_cache.set(endpoint, result, params, ttl)

            return result
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return api_cache.get_stats()


def clear_cache():
    """清空缓存"""
    api_cache.clear()


if __name__ == "__main__":
    # 测试缓存
    print("Testing API Cache...")

    # 设置缓存
    api_cache.set("test_endpoint", {"data": "test_value"}, ttl=5)
    print(f"1. Set cache: {api_cache.cache}")

    # 获取缓存
    result = api_cache.get("test_endpoint")
    print(f"2. Get cache: {result}")

    # 获取统计信息
    stats = api_cache.get_stats()
    print(f"3. Cache stats: {stats}")

    # 等待过期
    time.sleep(6)
    result = api_cache.get("test_endpoint")
    print(f"4. Get expired cache: {result}")

    print("\nCache test completed!")
