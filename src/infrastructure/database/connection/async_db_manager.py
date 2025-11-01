#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步数据库管理器
"""

import os
import logging
from typing import AsyncGenerator, Optional, Any, Dict
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    async_scoped_session
)
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .database_config import DatabaseConfig
from ..models import Base

logger = logging.getLogger("codex.database.manager")


class AsyncDatabaseManager:
    """
    异步数据库管理器
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._initialized = False

    def _create_engine(self) -> AsyncEngine:
        """
        创建SQLAlchemy异步引擎
        """
        logger.info(
            f"Creating async database engine: {self.config}, "
            f"pool_size={self.config.pool_size}, max_overflow={self.config.max_overflow}"
        )

        # 创建引擎配置字典
        engine_kwargs = {
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool,
            "pool_pre_ping": self.config.pool_pre_ping,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
        }

        # 根据URL确定连接池类型
        if self.config.url.startswith("sqlite"):
            # SQLite使用静态池
            engine_kwargs["poolclass"] = StaticPool
            if self.config.connect_args:
                engine_kwargs["connect_args"] = self.config.connect_args
        else:
            # PostgreSQL/MySQL使用队列池
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = self.config.pool_size
            engine_kwargs["max_overflow"] = self.config.max_overflow
            if self.config.connect_args:
                engine_kwargs["connect_args"] = self.config.connect_args

        engine = create_async_engine(self.config.url, **engine_kwargs)

        # 添加SQL日志（如果启用）
        if self.config.echo:
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if self.config.url.startswith("sqlite"):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.close()

        return engine

    async def initialize(self) -> None:
        """
        初始化数据库连接
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return

        try:
            self.engine = self._create_engine()

            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            # 创建作用域会话（用于Web框架）
            self.scoped_session = async_scoped_session(
                self.session_factory,
                scopefunc=None  # 使用默认的作用域
            )

            self._initialized = True
            logger.info("Database manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """
        关闭数据库连接
        """
        if not self._initialized:
            return

        try:
            if hasattr(self, 'scoped_session'):
                await self.scoped_session.remove()

            if self.session_factory:
                # 关闭所有会话
                self.session_factory.close_all()

            if self.engine:
                await self.engine.dispose()

            self._initialized = False
            logger.info("Database manager closed successfully")

        except Exception as e:
            logger.error(f"Error closing database manager: {e}", exc_info=True)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话的上下文管理器
        """
        if not self._initialized:
            await self.initialize()

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}", exc_info=True)
                raise
            finally:
                await session.close()

    async def create_tables(self, checkfirst: bool = True) -> None:
        """
        创建数据库表
        """
        if not self._initialized:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, checkfirst=checkfirst)
            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise

    async def drop_tables(self) -> None:
        """
        删除数据库表
        """
        if not self._initialized:
            await self.initialize()

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")

        except Exception as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        生成数据库会话（用于FastAPI依赖注入）
        """
        async with self.get_session() as session:
            yield session

    def get_engine_url(self) -> str:
        """
        获取数据库引擎URL（隐藏敏感信息）
        """
        return str(self.config)

    @property
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        """
        return self._initialized

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        """
        try:
            async with self.get_session() as session:
                # 执行简单查询检查连接
                result = await session.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "database": "connected",
                    "engine_url": self.get_engine_url()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "engine_url": self.get_engine_url()
            }


# 全局数据库管理器实例
_db_manager: Optional[AsyncDatabaseManager] = None


def get_database_manager() -> AsyncDatabaseManager:
    """
    获取全局数据库管理器实例（单例模式）
    """
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig.from_env()
        _db_manager = AsyncDatabaseManager(config)
    return _db_manager


def create_async_session_factory(config: DatabaseConfig) -> async_sessionmaker:
    """
    创建异步会话工厂
    """
    manager = AsyncDatabaseManager(config)
    return manager.session_factory


def get_async_session_factory() -> async_sessionmaker:
    """
    获取异步会话工厂
    """
    return get_database_manager().session_factory
