#!/usr/bin/env python3
"""
統一緩存管理模組
為整個系統提供高效的緩存機制
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime
from collections import OrderedDict, defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class LRUCache:
    """LRU緩存實現"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_count = defaultdict(int)
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        with self.lock:
            if key not in self.cache:
                return None

            # LRU: 移動到末尾
            value = self.cache.pop(key)
            self.cache[key] = value
            self.access_count[key] += 1

            return value

    def set(self, key: str, value: Any) -> None:
        """設置緩存值"""
        with self.lock:
            if key in self.cache:
                # 更新現有key
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最少使用的key
                lru_key = min(self.access_count, key=lambda k: self.access_count[k])
                del self.cache[lru_key]
                del self.access_count[lru_key]

            self.cache[key] = value
            self.access_count[key] = 1

    def delete(self, key: str) -> bool:
        """刪除緩存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_count:
                    del self.access_count[key]
                return True
            return False

    def clear(self) -> None:
        """清空所有緩存"""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()

    def size(self) -> int:
        """獲取當前大小"""
        with self.lock:
            return len(self.cache)

    def get_stats(self) -> Dict:
        """獲取統計信息"""
        with self.lock:
            return {
                "current_size": len(self.cache),
                "max_size": self.max_size,
                "total_access": sum(self.access_count.values()),
                "unique_keys": len(self.access_count)
            }


class UnifiedCacheManager:
    """統一緩存管理器"""

    def __init__(self):
        self.memory_cache = {}
        self.cache_time = {}
        self.cache_config = self._load_config()
        self._setup_cleanup_task()
        self._stats = defaultdict(int)

    def _load_config(self) -> Dict[str, Dict]:
        """加載緩存配置"""
        return {
            "stock_data": {
                "ttl": 300,        # 5分鐘
                "max_size": 100,
                "description": "股票技術分析數據"
            },
            "weather_data": {
                "ttl": 900,        # 15分鐘
                "max_size": 50,
                "description": "天氣數據"
            },
            "sports_scores": {
                "ttl": 60,         # 1分鐘
                "max_size": 200,
                "description": "體育比分"
            },
            "mark6_data": {
                "ttl": 3600,       # 1小時
                "max_size": 10,
                "description": "六合彩數據"
            },
            "portfolio_data": {
                "ttl": 600,        # 10分鐘
                "max_size": 100,
                "description": "投資組合數據"
            },
            "heatmap_data": {
                "ttl": 1800,       # 30分鐘
                "max_size": 20,
                "description": "熱力圖數據"
            },
            "ai_response": {
                "ttl": 3600,       # 1小時
                "max_size": 50,
                "description": "AI回應"
            }
        }

    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存數據"""
        cache_type = self._get_cache_type(key)
        if not cache_type:
            return None

        config = self.cache_config.get(cache_type, {})
        ttl = config.get("ttl", 300)

        try:
            if key in self.memory_cache and key in self.cache_time:
                elapsed = time.time() - self.cache_time[key]
                if elapsed < ttl:
                    self._stats[f"{cache_type}_hit"] += 1
                    return self.memory_cache[key]
                else:
                    # 緩存過期，刪除
                    del self.memory_cache[key]
                    del self.cache_time[key]
                    self._stats[f"{cache_type}_expired"] += 1

            self._stats[f"{cache_type}_miss"] += 1
            return None

        except Exception as e:
            logger.error(f"獲取緩存失敗: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設置緩存數據"""
        cache_type = self._get_cache_type(key)
        if not cache_type:
            return

        try:
            self.memory_cache[key] = value
            self.cache_time[key] = time.time()
            self._stats[f"{cache_type}_set"] += 1

            # 清理過期的同類型緩存
            await self._cleanup_expired(cache_type)

        except Exception as e:
            logger.error(f"設置緩存失敗: {e}")

    async def delete(self, key: str) -> bool:
        """刪除緩存數據"""
        try:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_time:
                del self.cache_time[key]
            return True
        except Exception as e:
            logger.error(f"刪除緩存失敗: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """按模式清理緩存"""
        count = 0
        keys_to_delete = []

        try:
            for key in self.memory_cache.keys():
                if pattern in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                await self.delete(key)
                count += 1

            logger.info(f"清理了 {count} 個匹配的緩存項")
            return count

        except Exception as e:
            logger.error(f"按模式清理緩存失敗: {e}")
            return 0

    def _get_cache_type(self, key: str) -> Optional[str]:
        """根據key獲取緩存類型"""
        for cache_type in self.cache_config.keys():
            if cache_type.replace("_", "") in key.replace("_", ""):
                return cache_type
        return None

    async def _cleanup_expired(self, cache_type: str) -> None:
        """清理過期的緩存"""
        config = self.cache_config.get(cache_type, {})
        ttl = config.get("ttl", 300)

        keys_to_delete = []
        try:
            current_time = time.time()
            for key in list(self.memory_cache.keys()):
                if self._get_cache_type(key) == cache_type:
                    if key in self.cache_time:
                        elapsed = current_time - self.cache_time[key]
                        if elapsed > ttl:
                            keys_to_delete.append(key)

            for key in keys_to_delete:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.cache_time:
                    del self.cache_time[key]

            if keys_to_delete:
                logger.debug(f"清理了 {len(keys_to_delete)} 個過期的{cache_type}緩存")

        except Exception as e:
            logger.error(f"清理過期緩存失敗: {e}")

    def _setup_cleanup_task(self) -> None:
        """啟動定期清理任務"""
        async def periodic_cleanup():
            while True:
                try:
                    await asyncio.sleep(3600)  # 每小時清理一次
                    await self._cleanup_all_expired()
                except Exception as e:
                    logger.error(f"定期清理任務失敗: {e}")

        # 啟動清理任務
        asyncio.create_task(periodic_cleanup())

    async def _cleanup_all_expired(self) -> None:
        """清理所有過期緩存"""
        try:
            for cache_type in self.cache_config.keys():
                await self._cleanup_expired(cache_type)
            logger.info("定期清理完成")
        except Exception as e:
            logger.error(f"清理所有過期緩存失敗: {e}")

    def get_cache_status(self) -> Dict:
        """獲取緩存狀態"""
        status = {}
        total_items = 0
        total_size = 0

        for cache_type in self.cache_config.keys():
            config = self.cache_config[cache_type]
            ttl = config.get("ttl", 300)

            items = 0
            expired = 0
            for key in self.memory_cache:
                if self._get_cache_type(key) == cache_type:
                    items += 1
                    if key in self.cache_time:
                        elapsed = time.time() - self.cache_time[key]
                        if elapsed > ttl:
                            expired += 1

            status[cache_type] = {
                "items": items,
                "expired": expired,
                "ttl": ttl,
                "max_size": config.get("max_size", 100)
            }
            total_items += items

        status["total"] = {
            "items": total_items,
            "size_mb": total_size / (1024 * 1024)
        }

        return status

    def get_performance_report(self) -> Dict:
        """獲取性能報告"""
        report = {
            "cache_stats": dict(self._stats),
            "timestamp": datetime.now().isoformat(),
            "hit_rates": {}
        }

        # 計算命中率
        for cache_type in self.cache_config.keys():
            hits = self._stats.get(f"{cache_type}_hit", 0)
            misses = self._stats.get(f"{cache_type}_miss", 0)
            total = hits + misses

            if total > 0:
                hit_rate = hits / total * 100
                report["hit_rates"][cache_type] = {
                    "hit_rate": f"{hit_rate:.2f}%",
                    "hits": hits,
                    "misses": misses,
                    "total": total
                }

        return report


# 創建全局實例
cache_manager = UnifiedCacheManager()
