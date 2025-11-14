#!/usr/bin/env python3
"""
Redis Caching Layer - Story 3.2.1 Implementation
實現Redis緩存層以提高API性能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import json
import hashlib
import pickle

from .models.api_response import APIResponse

logger = logging.getLogger(__name__)

# Pydantic Models for Cache Management

class CacheStats(BaseModel):
    """緩存統計數據"""
    cache_type: str
    hit_count: int
    miss_count: int
    hit_rate: float
    total_requests: int
    avg_response_time_ms: float


class CacheInfo(BaseModel):
    """緩存信息"""
    key: str
    size_bytes: int
    ttl_seconds: int
    created_at: str
    last_accessed: str
    access_count: int


class CacheListResponse(BaseModel):
    """緩存列表響應"""
    cache_keys: List[CacheInfo]
    total_items: int
    total_size_bytes: int


class CacheClearResponse(BaseModel):
    """緩存清除響應"""
    cleared_keys: List[str]
    cleared_count: int
    cleared_size_bytes: int


# Mock Redis Cache Implementation
class MockRedisCache:
    """模擬Redis緩存實現"""

    def __init__(self):
        self.cache = {}
        self.stats = {
            "hit_count": 0,
            "miss_count": 0,
            "total_requests": 0
        }

    def _generate_key(self, namespace: str, resource: str, params: dict) -> str:
        """生成緩存鍵"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{namespace}:{resource}:{params_hash}"

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        self.stats["total_requests"] += 1

        if key in self.cache:
            item = self.cache[key]
            # 檢查TTL
            if item["expires_at"] > datetime.now():
                self.stats["hit_count"] += 1
                item["last_accessed"] = datetime.now()
                item["access_count"] += 1
                return item["value"]
            else:
                # 過期，刪除
                del self.cache[key]

        self.stats["miss_count"] += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """設置緩存值"""
        self.cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 1,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "size_bytes": len(pickle.dumps(value))
        }

    def delete(self, key: str) -> bool:
        """刪除緩存鍵"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self, pattern: str = "*") -> int:
        """清除匹配模式的緩存"""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k or pattern == "*"]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        total = self.stats["hit_count"] + self.stats["miss_count"]
        hit_rate = (self.stats["hit_count"] / total) if total > 0 else 0

        total_size = sum(item["size_bytes"] for item in self.cache.values())

        return {
            "hit_count": self.stats["hit_count"],
            "miss_count": self.stats["miss_count"],
            "total_requests": total,
            "hit_rate": round(hit_rate, 4),
            "total_items": len(self.cache),
            "total_size_bytes": total_size,
            "memory_usage": f"{total_size / 1024:.2f} KB"
        }

    def get_all_keys(self) -> List[CacheInfo]:
        """獲取所有緩存鍵信息"""
        keys_info = []
        for key, item in self.cache.items():
            keys_info.append(CacheInfo(
                key=key,
                size_bytes=item["size_bytes"],
                ttl_seconds=max(0, int((item["expires_at"] - datetime.now()).total_seconds())),
                created_at=item["created_at"].strftime('%Y-%m-%d %H:%M:%S'),
                last_accessed=item["last_accessed"].strftime('%Y-%m-%d %H:%M:%S'),
                access_count=item["access_count"]
            ))
        return sorted(keys_info, key=lambda x: x.last_accessed, reverse=True)


# Initialize mock cache
cache = MockRedisCache()

# FastAPI Router
router = APIRouter(prefix="/api/v2/cache", tags=["cache"])

# Cache decorator for API endpoints
def cached(ttl: int = 3600, key_prefix: str = "api"):
    """緩存裝飾器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成緩存鍵
            params = {**kwargs, **{"func_name": func.__name__}}
            cache_key = cache._generate_key(key_prefix, func.__name__, params)

            # 嘗試從緩存獲取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 執行函數
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # 存儲到緩存
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

@router.get("/stats", response_model=APIResponse)
async def get_cache_stats():
    """獲取緩存統計"""
    try:
        stats = cache.get_stats()

        return APIResponse(
            success=True,
            data=stats,
            message="緩存統計查詢成功"
        )

    except Exception as e:
        logger.error(f"獲取緩存統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=APIResponse)
async def list_cache_keys():
    """列出所有緩存鍵"""
    try:
        keys_info = cache.get_all_keys()
        total_size = sum(key.size_bytes for key in keys_info)

        return APIResponse(
            success=True,
            data=CacheListResponse(
                cache_keys=keys_info,
                total_items=len(keys_info),
                total_size_bytes=total_size
            ).dict(),
            message=f"緩存列表查詢成功 (共 {len(keys_info)} 項)"
        )

    except Exception as e:
        logger.error(f"列出緩存鍵失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear", response_model=APIResponse)
async def clear_cache(
    pattern: Optional[str] = Query(None, description="清除模式 (支持 * 通配符)")
):
    """清除緩存"""
    try:
        cleared_count = cache.clear(pattern or "*")

        # 獲取清除前的大小
        all_keys = cache.get_all_keys()
        cleared_size = sum(key.size_bytes for key in all_keys)

        return APIResponse(
            success=True,
            data=CacheClearResponse(
                cleared_keys=[],  # 簡化，不返回具體鍵列表
                cleared_count=cleared_count,
                cleared_size_bytes=cleared_size
            ).dict(),
            message=f"緩存清除成功 (清除了 {cleared_count} 項)"
        )

    except Exception as e:
        logger.error(f"清除緩存失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/key/{key}", response_model=APIResponse)
async def delete_cache_key(key: str):
    """刪除指定緩存鍵"""
    try:
        deleted = cache.delete(key)

        if deleted:
            return APIResponse(
                success=True,
                data={"deleted_key": key},
                message=f"緩存鍵 {key} 刪除成功"
            )
        else:
            raise HTTPException(status_code=404, detail="緩存鍵不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除緩存鍵失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=APIResponse)
async def cache_health_check():
    """緩存健康檢查"""
    try:
        stats = cache.get_stats()
        health_status = "healthy" if stats["hit_rate"] > 0.5 else "degraded"

        return APIResponse(
            success=True,
            data={
                "status": health_status,
                "version": "3.2.1",
                "engine": "mock_redis",
                "stats": stats,
                "last_check": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message=f"緩存健康狀態: {health_status}"
        )

    except Exception as e:
        logger.error(f"緩存健康檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warmup", response_model=APIResponse)
async def warmup_cache():
    """預熱緩存"""
    try:
        # 模擬緩存預熱
        warmup_keys = [
            "hibor:current:latest",
            "economic:gdp:latest",
            "economic:cpi:latest",
            "property:market:latest"
        ]

        # 模擬添加數據到緩存
        for key in warmup_keys:
            cache.set(key, {"data": "warmed_up", "timestamp": datetime.now().isoformat()}, 3600)

        return APIResponse(
            success=True,
            data={
                "warmed_keys": warmup_keys,
                "count": len(warmup_keys)
            },
            message=f"緩存預熱完成 (預熱了 {len(warmup_keys)} 項)"
        )

    except Exception as e:
        logger.error(f"緩存預熱失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Example: Cached HIBOR API endpoint
@router.get("/hibor/cached-current")
@cached(ttl=3600, key_prefix="hibor")
async def get_cached_hibor_current():
    """獲取緩存的HIBOR當前利率"""
    # 模擬API響應
    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "rates": {
            "overnight": 4.25,
            "one_week": 4.30,
            "one_month": 4.35,
            "three_months": 4.40,
            "six_months": 4.45,
            "twelve_months": 4.50
        },
        "cached": True
    }


__all__ = ['router', 'cached', 'cache']
