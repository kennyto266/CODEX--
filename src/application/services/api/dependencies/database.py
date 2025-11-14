"""
Database Dependencies
数据库依赖管理
提供数据库会话和连接管理
"""

from typing import Generator, Optional
import os
import structlog

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger("api.database")


class DatabaseManager:
    """数据库管理器"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def _create_engine(self):
        """创建数据库引擎"""
        # SQLite数据库
        db_url = os.getenv("DATABASE_URL", "sqlite:///./layout_config.db")

        logger.info("创建数据库引擎", db_url=db_url)

        engine = create_engine(
            db_url,
            # SQLite特定配置
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
            # 池配置
            pool_pre_ping=True,
            pool_recycle=300,
            # 回显SQL（开发环境）
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )

        return engine

    def get_session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
            )
        return self._session_factory

    def get_db_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（依赖注入）"""
        session_factory = self.get_session_factory()
        session = session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("数据库会话错误", error=str(e))
            raise
        finally:
            session.close()

    def create_tables(self):
        """创建所有表"""
        from src.database import Base

        engine = self.get_engine()
        logger.info("创建数据库表")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")

    def drop_tables(self):
        """删除所有表"""
        from src.database import Base

        engine = self.get_engine()
        logger.warning("删除所有数据库表")
        Base.metadata.drop_all(bind=engine)
        logger.info("数据库表删除完成")

    def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接正常")
            return True
        except Exception as e:
            logger.error("数据库连接失败", error=str(e))
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI依赖注入：获取数据库会话

    Yields:
        Session: SQLAlchemy会话
    """
    yield from db_manager.get_db_session()


def get_layout_repository() -> Generator[Session, None, None]:
    """
    FastAPI依赖注入：获取布局仓储

    Yields:
        Session: SQLAlchemy会话
    """
    yield from get_db()
