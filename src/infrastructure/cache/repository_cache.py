"""
Repository Caching Mechanism
"""
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from uuid import UUID


class CacheEntry:
    """Cache entry with expiration"""

    def __init__(self, value: Any, ttl: int = 300):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl

    @property
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


class RepositoryCache:
    """Simple repository cache with TTL support"""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            return entry.value
        elif entry:
            # Remove expired entry
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self._default_ttl
        self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()

    def clear_expired(self) -> None:
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]


def cache_result(cache: RepositoryCache, key_func: Callable, ttl: Optional[int] = None):
    """Decorator to cache repository method results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_func(*args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


# Global cache instance
_global_cache = RepositoryCache()


def get_cache() -> RepositoryCache:
    """Get global cache instance"""
    return _global_cache


# Cache decorators for common repository operations
def cache_find_by_id(entity_type: str, ttl: int = 300):
    """Decorator to cache find_by_id results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, id: UUID, *args, **kwargs):
            cache_key = f"{entity_type}:find_by_id:{id}"
            cached = get_cache().get(cache_key)
            if cached is not None:
                return cached

            result = await func(self, id, *args, **kwargs)
            if result:
                get_cache().set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def cache_find_all(entity_type: str, ttl: int = 60):
    """Decorator to cache find_all results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache_key = f"{entity_type}:find_all"
            cached = get_cache().get(cache_key)
            if cached is not None:
                return cached

            result = await func(self, *args, **kwargs)
            get_cache().set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(cache_key_patterns: list):
    """Decorator to invalidate specific cache entries"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Invalidate cache entries
            cache = get_cache()
            for pattern in cache_key_patterns:
                # Simple pattern matching - in real implementation, use more sophisticated pattern matching
                keys_to_delete = [
                    key for key in cache._cache.keys()
                    if pattern in key
                ]
                for key in keys_to_delete:
                    cache.delete(key)

            return result
        return wrapper
    return decorator
