#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话工厂模块
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .database_config import DatabaseConfig
from .async_db_manager import AsyncDatabaseManager

# 全局会话工厂实例
_session_factory: Optional[async_sessionmaker] = None
_database_manager: Optional[AsyncDatabaseManager] = None


def create_async_session_factory(
    config: Optional[DatabaseConfig] = None
) -> async_sessionmaker:
    """
    创建异步会话工厂

    Args:
        config: 数据库配置，如果为None则使用默认配置

    Returns:
        异步会话工厂
    """
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    if config is None:
        config = DatabaseConfig.from_env()

    db_manager = AsyncDatabaseManager(config)

    # 初始化数据库
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在异步环境中，使用线程池执行同步初始化
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, db_manager.initialize())
                future.result()
        else:
            # 如果不在异步环境中，直接初始化
            asyncio.run(db_manager.initialize())
    except RuntimeError:
        # 没有事件循环，创建一个
        asyncio.run(db_manager.initialize())

    _session_factory = db_manager.session_factory
    return _session_factory


def get_async_session_factory() -> async_sessionmaker:
    """
    获取异步会话工厂（单例模式）

    Returns:
        异步会话工厂
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = create_async_session_factory()
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（用于依赖注入）

    Returns:
        异步数据库会话生成器
    """
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_database_manager() -> AsyncDatabaseManager:
    """
    获取数据库管理器

    Returns:
        数据库管理器实例
    """
    global _database_manager
    if _database_manager is None:
        _database_manager = AsyncDatabaseManager(DatabaseConfig.from_env())
    return _database_manager


def create_db_session_dependency():
    """
    创建数据库会话依赖（用于FastAPI）
    """
    async def get_session():
        async for session in get_db_session():
            yield session

    return get_session
