#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class DatabaseConfig:
    """
    数据库配置类
    """

    # 连接URL
    url: str

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 连接选项
    echo: bool = False
    echo_pool: bool = False

    # 连接验证
    pool_pre_ping: bool = True

    # 超时设置
    connect_args: dict = None

    def __post_init__(self):
        if self.connect_args is None:
            self.connect_args = {
                "timeout": 10,
                "command_timeout": 30
            }

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        从环境变量创建配置
        """
        # 从环境变量获取数据库URL
        database_url = os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./codex_trading.db"
        )

        return cls(
            url=database_url,
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            echo_pool=os.getenv("DB_ECHO_POOL", "false").lower() == "true",
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
        )

    @classmethod
    def sqlite(cls, db_path: str = "./codex_trading.db") -> "DatabaseConfig":
        """
        SQLite配置
        """
        return cls(
            url=f"sqlite+aiosqlite:///{db_path}",
            pool_size=1,
            max_overflow=0,
            connect_args={"check_same_thread": False},
        )

    @classmethod
    def postgresql(
        cls,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
        database: str = "codex_trading",
        **kwargs
    ) -> "DatabaseConfig":
        """
        PostgreSQL配置
        """
        url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        return cls(url=url, **kwargs)

    @classmethod
    def mysql(
        cls,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "codex_trading",
        **kwargs
    ) -> "DatabaseConfig":
        """
        MySQL配置
        """
        url = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"
        return cls(url=url, **kwargs)

    def __str__(self) -> str:
        """安全的配置字符串（隐藏密码）"""
        if "://" in self.url:
            parts = self.url.split("://")
            if "@" in parts[1]:
                auth_info, rest = parts[1].split("@", 1)
                auth_parts = auth_info.split(":")
                if len(auth_parts) >= 2:
                    auth_info = f"{auth_parts[0]}:***"
                return f"{parts[0]}://{auth_info}@{rest}"
        return self.url
