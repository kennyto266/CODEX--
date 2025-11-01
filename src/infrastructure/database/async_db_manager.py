"""
異步數據庫管理器

提供：
- 異步連接池
- 事務管理
- 查詢優化
- 批量操作
- 連接健康監控
"""

import asyncio
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import asyncpg
import aiosqlite

from src.core.logging import get_logger

logger = get_logger("async_db_manager")


class DatabaseType(Enum):
    """數據庫類型"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"


@dataclass
class DatabaseConfig:
    """數據庫配置"""
    db_type: DatabaseType = DatabaseType.POSTGRESQL

    # PostgreSQL配置
    host: str = "localhost"
    port: int = 5432
    database: str = "hk_quant"
    user: str = "postgres"
    password: str = ""

    # SQLite配置
    sqlite_path: str = ":memory:"

    # 連接池配置
    min_connections: int = 5
    max_connections: int = 50
    connection_timeout: float = 60.0
    command_timeout: float = 30.0

    # 健康檢查
    health_check_interval: int = 60  # 秒
    max_failures: int = 3

    # 事務配置
    default_transaction_isolation: str = "read_committed"  # PostgreSQL
    max_transaction_retry: int = 3
    transaction_retry_delay: float = 0.5


@dataclass
class ConnectionMetrics:
    """連接指標"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    queries_executed: int = 0
    slow_queries: int = 0
    transactions_committed: int = 0
    transactions_rolled_back: int = 0
    average_query_time: float = 0.0
    last_health_check: Optional[float] = None


class AsyncDBConnection(ABC):
    """異步數據庫連接抽象基類"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.metrics = ConnectionMetrics()
        self._closed = False

    @abstractmethod
    async def execute(self, query: str, *args) -> Any:
        """執行查詢"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """獲取單條記錄"""
        pass

    @abstractmethod
    async def fetch_many(self, query: str, *args, size: int = 100) -> List[Dict]:
        """獲取多條記錄"""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, *args) -> List[Dict]:
        """獲取所有記錄"""
        pass

    @abstractmethod
    async def execute_many(self, query: str, args_list: List[Tuple]) -> int:
        """批量執行"""
        pass

    @abstractmethod
    async def begin(self) -> Any:
        """開始事務"""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """提交事務"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """回滾事務"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """關閉連接"""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Ping連接"""
        pass


class AsyncPostgreSQLConnection(AsyncDBConnection):
    """異步PostgreSQL連接"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._pool: Optional[asyncpg.Pool] = None
        self._connection: Optional[asyncpg.Connection] = None

    async def initialize(self) -> bool:
        """初始化連接池"""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    "jit": "off"  # 禁用JIT提升性能
                }
            )
            logger.info(f"PostgreSQL pool initialized: {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            return False

    async def execute(self, query: str, *args) -> Any:
        start_time = time.time()
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(query, *args)
                self.metrics.queries_executed += 1

                elapsed = time.time() - start_time
                if elapsed > 1.0:  # 慢查詢閾值
                    self.metrics.slow_queries += 1
                    logger.warning(f"Slow query detected: {elapsed:.2f}s - {query[:100]}")

                return result
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise

    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_many(self, query: str, *args, size: int = 100) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows[:size]]

    async def fetch_all(self, query: str, *args) -> List[Dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute_many(self, query: str, args_list: List[Tuple]) -> int:
        async with self._pool.acquire() as conn:
            await conn.executemany(query, args_list)
            return len(args_list)

    async def begin(self) -> Any:
        # PostgreSQL使用asyncpg的事務上下文管理器
        async with self._pool.acquire() as conn:
            tx = conn.transaction()
            await tx.start()
            return tx

    async def commit(self, tx: Any) -> None:
        await tx.commit()

    async def rollback(self, tx: Any) -> None:
        await tx.rollback()

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def ping(self) -> bool:
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except:
            return False


class AsyncSQLiteConnection(AsyncDBConnection):
    """異步SQLite連接"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> bool:
        try:
            self._db = await aiosqlite.connect(
                self.config.sqlite_path,
                timeout=self.config.connection_timeout
            )
            # 啟用WAL模式提升並發性能
            await self._db.execute("PRAGMA journal_mode=WAL")
            await self._db.execute("PRAGMA synchronous=NORMAL")
            await self._db.execute("PRAGMA cache_size=10000")
            await self._db.execute("PRAGMA temp_store=MEMORY")

            logger.info(f"SQLite initialized: {self.config.sqlite_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            return False

    async def execute(self, query: str, *args) -> Any:
        start_time = time.time()
        try:
            await self._db.execute(query, *args)
            await self._db.commit()
            self.metrics.queries_executed += 1

            elapsed = time.time() - start_time
            if elapsed > 1.0:
                self.metrics.slow_queries += 1
                logger.warning(f"Slow query detected: {elapsed:.2f}s - {query[:100]}")

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Execute error: {e}")
            raise

    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        async with self._db.execute(query, *args) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_many(self, query: str, *args, size: int = 100) -> List[Dict]:
        async with self._db.execute(query, *args) as cursor:
            rows = await cursor.fetchmany(size)
            return [dict(row) for row in rows]

    async def fetch_all(self, query: str, *args) -> List[Dict]:
        async with self._db.execute(query, *args) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def execute_many(self, query: str, args_list: List[Tuple]) -> int:
        await self._db.executemany(query, args_list)
        await self._db.commit()
        return len(args_list)

    async def begin(self) -> None:
        await self._db.execute("BEGIN")

    async def commit(self, tx: None) -> None:
        await self._db.commit()

    async def rollback(self, tx: None) -> None:
        await self._db.rollback()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def ping(self) -> bool:
        try:
            await self._db.execute("SELECT 1")
            return True
        except:
            return False


class AsyncDBManager:
    """異步數據庫管理器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = get_logger("db_manager")
        self._connection: Optional[AsyncDBConnection] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def initialize(self) -> bool:
        """初始化數據庫連接"""
        try:
            # 根據數據庫類型創建連接
            if self.config.db_type == DatabaseType.POSTGRESQL:
                self._connection = AsyncPostgreSQLConnection(self.config)
            elif self.config.db_type == DatabaseType.SQLITE:
                self._connection = AsyncSQLiteConnection(self.config)
            else:
                raise ValueError(f"Unsupported database type: {self.config.db_type}")

            # 初始化連接
            if not await self._connection.initialize():
                return False

            # 啟動健康檢查
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info("Database manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {e}")
            return False

    async def _health_check_loop(self) -> None:
        """健康檢查循環"""
        while not self._stop_event.is_set():
            try:
                if self._connection:
                    is_healthy = await self._connection.ping()
                    self._connection.metrics.last_health_check = time.time()

                    if not is_healthy:
                        self.logger.warning("Database connection unhealthy, attempting reconnect...")
                        await self._connection.initialize()

                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.config.health_check_interval)

    async def execute(self, query: str, *args) -> Any:
        """執行查詢"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return await self._connection.execute(query, *args)

    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """獲取單條記錄"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return await self._connection.fetch_one(query, *args)

    async def fetch_many(self, query: str, *args, size: int = 100) -> List[Dict]:
        """獲取多條記錄"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return await self._connection.fetch_many(query, *args, size=size)

    async def fetch_all(self, query: str, *args) -> List[Dict]:
        """獲取所有記錄"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return await self._connection.fetch_all(query, *args)

    async def execute_many(self, query: str, args_list: List[Tuple]) -> int:
        """批量執行"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return await self._connection.execute_many(query, args_list)

    @asynccontextmanager
    async def transaction(self):
        """事務上下文管理器"""
        if not self._connection:
            raise RuntimeError("Database not initialized")

        tx = None
        try:
            tx = await self._connection.begin()

            class TransactionContext:
                def __init__(self, db_manager):
                    self._db_manager = db_manager

                async def execute(self, query: str, *args):
                    return await self._db_manager.execute(query, *args)

                async def fetch_one(self, query: str, *args):
                    return await self._db_manager.fetch_one(query, *args)

                async def fetch_many(self, query: str, *args, size: int = 100):
                    return await self._db_manager.fetch_many(query, *args, size=size)

                async def fetch_all(self, query: str, *args):
                    return await self._db_manager.fetch_all(query, *args)

            context = TransactionContext(self)

            # 嘗試執行用戶代碼
            try:
                yield context
                await self._connection.commit(tx)
                self._connection.metrics.transactions_committed += 1
            except Exception as e:
                await self._connection.rollback(tx)
                self._connection.metrics.transactions_rolled_back += 1
                self.logger.error(f"Transaction rolled back: {e}")
                raise

        except Exception as e:
            if tx is not None:
                await self._connection.rollback(tx)
            raise

    async def with_retry(
        self,
        coro,
        max_retries: Optional[int] = None,
        retry_delay: float = 0.5
    ):
        """
        帶重試的數據庫操作

        Args:
            coro: 異步協程
            max_retries: 最大重試次數
            retry_delay: 重試延遲
        """
        max_retries = max_retries or self.config.max_transaction_retry

        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return await coro()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(
                        f"Database operation failed (attempt {attempt + 1}): {e}. Retrying..."
                    )
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    self.logger.error(f"Database operation failed after {max_retries + 1} attempts")
                    break

        raise last_exception or Exception("Max retries exceeded")

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取數據庫指標"""
        if not self._connection:
            return {}

        metrics = {
            "db_type": self.config.db_type.value,
            "connection_metrics": self._connection.metrics.__dict__,
            "pool_config": {
                "min_connections": self.config.min_connections,
                "max_connections": self.config.max_connections,
                "connection_timeout": self.config.connection_timeout
            }
        }

        return metrics

    async def close(self) -> None:
        """關閉數據庫連接"""
        try:
            # 停止健康檢查
            if self._health_check_task:
                self._stop_event.set()
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # 關閉連接
            if self._connection:
                await self._connection.close()

            logger.info("Database manager closed")

        except Exception as e:
            self.logger.error(f"Error closing database manager: {e}")


# 全局數據庫管理器
_global_db_manager: Optional[AsyncDBManager] = None


def get_db_manager(config: Optional[DatabaseConfig] = None) -> AsyncDBManager:
    """獲取全局數據庫管理器實例"""
    global _global_db_manager
    if _global_db_manager is None:
        if config is None:
            config = DatabaseConfig()
        _global_db_manager = AsyncDBManager(config)
    return _global_db_manager


async def init_db(config: Optional[DatabaseConfig] = None) -> bool:
    """初始化全局數據庫"""
    db_manager = get_db_manager(config)
    return await db_manager.initialize()


async def close_db() -> None:
    """關閉全局數據庫"""
    global _global_db_manager
    if _global_db_manager:
        await _global_db_manager.close()
        _global_db_manager = None
