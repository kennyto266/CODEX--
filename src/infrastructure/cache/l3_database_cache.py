"""
L3 數據庫緩存層

提供持久化緩存存儲，支持：
- SQLite/PostgreSQL 持久化
- 緩存條目管理
- 自動過期清理
- 查詢優化
- 批量操作
"""

import asyncio
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.infrastructure.database.async_db_manager import (
    AsyncDBManager,
    DatabaseConfig,
    DatabaseType,
    get_db_manager
)

from src.core.logging import get_logger

logger = get_logger("l3_database_cache")


class L3DatabaseCache:
    """L3 數據庫緩存實現"""

    def __init__(self, db_manager: AsyncDBManager, default_ttl: int = 86400):
        """
        初始化L3緩存

        Args:
            db_manager: 異步數據庫管理器
            default_ttl: 默認生存時間（秒），默認24小時
        """
        self.db_manager = db_manager
        self.default_ttl = default_ttl
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化緩存表"""
        try:
            logger.info("Initializing L3 database cache...")

            # 創建緩存表
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS cache_l3 (
                    cache_key TEXT PRIMARY KEY,
                    cache_value BLOB NOT NULL,
                    value_type TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    ttl INTEGER NOT NULL,
                    expires_at REAL NOT NULL,
                    metadata TEXT,
                    checksum TEXT
                )
            """)

            # 創建索引以提升查詢性能
            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_l3_expires_at
                ON cache_l3(expires_at)
            """)

            await self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_l3_last_accessed
                ON cache_l3(last_accessed)
            """)

            # 創建統計表
            await self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS cache_l3_stats (
                    stat_date TEXT PRIMARY KEY,
                    total_hits INTEGER DEFAULT 0,
                    total_misses INTEGER DEFAULT 0,
                    total_sets INTEGER DEFAULT 0,
                    total_deletes INTEGER DEFAULT 0,
                    avg_access_time REAL DEFAULT 0,
                    cache_size INTEGER DEFAULT 0
                )
            """)

            self._initialized = True
            logger.info("L3 database cache initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize L3 cache: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        獲取緩存值

        Args:
            key: 緩存鍵

        Returns:
            緩存值或None（如果不存在或已過期）
        """
        if not self._initialized:
            logger.warning("L3 cache not initialized")
            return None

        try:
            # 查詢緩存
            row = await self.db_manager.fetch_one(
                "SELECT * FROM cache_l3 WHERE cache_key = ?",
                key
            )

            if not row:
                await self._record_stat("miss")
                return None

            # 檢查是否過期
            if row["expires_at"] < time.time():
                # 過期，刪除
                await self.delete(key)
                await self._record_stat("miss")
                return None

            # 更新訪問統計
            await self.db_manager.execute(
                """
                UPDATE cache_l3
                SET last_accessed = ?, access_count = access_count + 1
                WHERE cache_key = ?
                """,
                time.time(),
                key
            )

            # 反序列化值
            try:
                value = pickle.loads(row["cache_value"])
                await self._record_stat("hit")
                return value
            except Exception as e:
                logger.error(f"Failed to deserialize cache value for key {key}: {e}")
                await self.delete(key)
                return None

        except Exception as e:
            logger.error(f"L3 cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        設置緩存值

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒），None使用默認值

        Returns:
            是否設置成功
        """
        if not self._initialized:
            logger.warning("L3 cache not initialized")
            return False

        try:
            effective_ttl = ttl if ttl is not None else self.default_ttl
            now = time.time()
            expires_at = now + effective_ttl

            # 序列化值
            try:
                serialized_value = pickle.dumps(value)
                value_type = type(value).__name__
            except Exception as e:
                logger.error(f"Failed to serialize cache value for key {key}: {e}")
                return False

            # 計算校驗和
            import hashlib
            checksum = hashlib.sha256(serialized_value).hexdigest()

            # 插入或更新
            await self.db_manager.execute(
                """
                INSERT OR REPLACE INTO cache_l3 (
                    cache_key, cache_value, value_type,
                    created_at, last_accessed, access_count,
                    ttl, expires_at, metadata, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                key,
                serialized_value,
                value_type,
                now,
                now,
                1,
                effective_ttl,
                expires_at,
                None,  # metadata
                checksum
            )

            await self._record_stat("set")
            return True

        except Exception as e:
            logger.error(f"L3 cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        刪除緩存

        Args:
            key: 緩存鍵

        Returns:
            是否刪除成功
        """
        if not self._initialized:
            return False

        try:
            result = await self.db_manager.execute(
                "DELETE FROM cache_l3 WHERE cache_key = ?",
                key
            )

            await self._record_stat("delete")
            return result > 0

        except Exception as e:
            logger.error(f"L3 cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在且未過期"""
        if not self._initialized:
            return False

        try:
            row = await self.db_manager.fetch_one(
                "SELECT expires_at FROM cache_l3 WHERE cache_key = ?",
                key
            )

            if not row:
                return False

            # 檢查過期
            if row["expires_at"] < time.time():
                await self.delete(key)
                return False

            return True

        except Exception as e:
            logger.error(f"L3 cache exists error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """清空所有緩存"""
        if not self._initialized:
            return False

        try:
            await self.db_manager.execute("DELETE FROM cache_l3")
            logger.info("L3 cache cleared")
            return True

        except Exception as e:
            logger.error(f"L3 cache clear error: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量獲取緩存"""
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results

    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """批量設置緩存"""
        success_count = 0
        for key, value in items.items():
            if await self.set(key, value, ttl):
                success_count += 1
        return success_count

    async def delete_many(self, keys: List[str]) -> int:
        """批量刪除緩存"""
        success_count = 0
        for key in keys:
            if await self.delete(key):
                success_count += 1
        return success_count

    async def expire_keys(self, pattern: str = "%") -> int:
        """
        批量過期鍵（適用於模式匹配）

        Args:
            pattern: 鍵模式，默認所有鍵

        Returns:
            過期的鍵數量
        """
        if not self._initialized:
            return 0

        try:
            now = time.time()
            result = await self.db_manager.execute(
                "DELETE FROM cache_l3 WHERE cache_key LIKE ? AND expires_at < ?",
                pattern,
                now
            )
            return result
        except Exception as e:
            logger.error(f"L3 cache expire error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        if not self._initialized:
            return {"status": "not_initialized"}

        try:
            # 基本統計
            total_keys = await self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM cache_l3"
            )
            total_keys = total_keys["count"] if total_keys else 0

            # 過期鍵數量
            expired_keys = await self.db_manager.fetch_one(
                "SELECT COUNT(*) as count FROM cache_l3 WHERE expires_at < ?",
                time.time()
            )
            expired_keys = expired_keys["count"] if expired_keys else 0

            # 最近訪問的鍵
            recent_keys = await self.db_manager.fetch_all(
                """
                SELECT cache_key, last_accessed, access_count
                FROM cache_l3
                ORDER BY last_accessed DESC
                LIMIT 10
                """
            )

            # 數據庫大小
            db_size = await self.db_manager.fetch_one(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )

            return {
                "status": "active",
                "total_keys": total_keys,
                "expired_keys": expired_keys,
                "active_keys": total_keys - expired_keys,
                "db_size_bytes": db_size["size"] if db_size else 0,
                "default_ttl": self.default_ttl,
                "recent_keys": [
                    {
                        "key": row["cache_key"],
                        "last_accessed": row["last_accessed"],
                        "access_count": row["access_count"]
                    }
                    for row in recent_keys
                ] if recent_keys else []
            }

        except Exception as e:
            logger.error(f"L3 cache get_stats error: {e}")
            return {"status": "error", "error": str(e)}

    async def cleanup_expired(self) -> int:
        """清理過期的緩存項"""
        if not self._initialized:
            return 0

        try:
            now = time.time()
            result = await self.db_manager.execute(
                "DELETE FROM cache_l3 WHERE expires_at < ?",
                now
            )
            logger.info(f"Cleaned up {result} expired cache entries")
            return result
        except Exception as e:
            logger.error(f"L3 cache cleanup error: {e}")
            return 0

    async def _record_stat(self, stat_type: str) -> None:
        """記錄統計信息"""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")

            if stat_type == "hit":
                await self.db_manager.execute(
                    """
                    INSERT INTO cache_l3_stats (stat_date, total_hits)
                    VALUES (?, 1)
                    ON CONFLICT(stat_date) DO UPDATE SET
                        total_hits = total_hits + 1
                    """,
                    date_str
                )
            elif stat_type == "miss":
                await self.db_manager.execute(
                    """
                    INSERT INTO cache_l3_stats (stat_date, total_misses)
                    VALUES (?, 1)
                    ON CONFLICT(stat_date) DO UPDATE SET
                        total_misses = total_misses + 1
                    """,
                    date_str
                )
            elif stat_type == "set":
                await self.db_manager.execute(
                    """
                    INSERT INTO cache_l3_stats (stat_date, total_sets)
                    VALUES (?, 1)
                    ON CONFLICT(stat_date) DO UPDATE SET
                        total_sets = total_sets + 1
                    """,
                    date_str
                )
            elif stat_type == "delete":
                await self.db_manager.execute(
                    """
                    INSERT INTO cache_l3_stats (stat_date, total_deletes)
                    VALUES (?, 1)
                    ON CONFLICT(stat_date) DO UPDATE SET
                        total_deletes = total_deletes + 1
                    """,
                    date_str
                )

        except Exception as e:
            logger.error(f"Failed to record stat {stat_type}: {e}")

    async def get_hit_ratio(self, days: int = 1) -> float:
        """獲取命中率"""
        if not self._initialized:
            return 0.0

        try:
            date_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            stats = await self.db_manager.fetch_one(
                """
                SELECT total_hits, total_misses
                FROM cache_l3_stats
                WHERE stat_date >= ?
                """,
                date_str
            )

            if not stats or (stats["total_hits"] + stats["total_misses"]) == 0:
                return 0.0

            hits = stats["total_hits"]
            misses = stats["total_misses"]
            return hits / (hits + misses)

        except Exception as e:
            logger.error(f"Failed to get hit ratio: {e}")
            return 0.0


# 全局L3緩存實例
_global_l3_cache: Optional[L3DatabaseCache] = None


def get_l3_cache(db_manager: Optional[AsyncDBManager] = None) -> L3DatabaseCache:
    """獲取全局L3緩存實例"""
    global _global_l3_cache
    if _global_l3_cache is None:
        if db_manager is None:
            db_manager = get_db_manager()
        _global_l3_cache = L3DatabaseCache(db_manager)
    return _global_l3_cache


async def init_l3_cache(db_manager: Optional[AsyncDBManager] = None) -> bool:
    """初始化全局L3緩存"""
    l3_cache = get_l3_cache(db_manager)
    return await l3_cache.initialize()


async def close_l3_cache() -> None:
    """關閉全局L3緩存"""
    global _global_l3_cache
    _global_l3_cache = None
