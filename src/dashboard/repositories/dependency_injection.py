"""
Repository依賴注入
提供統一的數據庫會話和Repository實例管理
"""

from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session
from fastapi import Depends
import logging

from .task_repository import TaskRepository
from .sprint_repository import SprintRepository

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Repository工廠
    管理所有Repository實例的創建和依賴注入
    """

    _instances: Dict[str, Any] = {}

    @classmethod
    def get_task_repository(
        cls,
        db: Session,
        cache_manager=None
    ) -> TaskRepository:
        """
        獲取TaskRepository實例

        Args:
            db: SQLAlchemy數據庫會話
            cache_manager: 緩存管理器

        Returns:
            TaskRepository實例
        """
        cache_key = f"task_repo:{id(db)}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = TaskRepository(db, cache_manager)
        return cls._instances[cache_key]

    @classmethod
    def get_sprint_repository(
        cls,
        db: Session,
        cache_manager=None
    ) -> SprintRepository:
        """
        獲取SprintRepository實例

        Args:
            db: SQLAlchemy數據庫會話
            cache_manager: 緩存管理器

        Returns:
            SprintRepository實例
        """
        cache_key = f"sprint_repo:{id(db)}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = SprintRepository(db, cache_manager)
        return cls._instances[cache_key]

    @classmethod
    def clear_instances(cls):
        """清除所有Repository實例緩存"""
        cls._instances.clear()
        logger.info("已清除所有Repository實例緩存")


# FastAPI依賴注入函數
def get_task_repository(db: Session) -> TaskRepository:
    """
    FastAPI依�賴：獲取TaskRepository實例

    Args:
        db: 數據庫會話

    Returns:
        TaskRepository實例
    """
    return RepositoryFactory.get_task_repository(db)


def get_sprint_repository(db: Session) -> SprintRepository:
    """
    FastAPI依賴：獲取SprintRepository實例

    Args:
        db: 數據庫會話

    Returns:
        SprintRepository實例
    """
    return RepositoryFactory.get_sprint_repository(db)


# 數據庫會話管理器
class DatabaseManager:
    """
    數據庫會話管理器
    管理數據庫連接和會話生命週期
    """

    def __init__(self, database_url: str):
        """
        初始化數據庫管理器

        Args:
            database_url: 數據庫連接URL
        """
        self.database_url = database_url
        self._engine = None
        self._session_factory = None

    def initialize(self):
        """初始化數據庫引擎和會話工廠"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        self._engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # 設為True可查看SQL日誌
        )

        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        logger.info(f"數據庫初始化完成: {self.database_url}")

    def get_session(self) -> Session:
        """
        獲取數據庫會話

        Returns:
            數據庫會話
        """
        if not self._session_factory:
            raise RuntimeError("數據庫未初始化，請先調用 initialize()")

        return self._session_factory()

    def close(self):
        """關閉數據庫連接"""
        if self._engine:
            self._engine.dispose()
            logger.info("數據庫連接已關閉")


# 全局數據庫管理器實例
_db_manager: Optional[DatabaseManager] = None


def initialize_database(database_url: str):
    """
    初始化全局數據庫管理器

    Args:
        database_url: 數據庫連接URL
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    _db_manager.initialize()


def get_db() -> Session:
    """
    FastAPI依賴：獲取數據庫會話

    Yields:
        數據庫會話
    """
    global _db_manager
    if not _db_manager:
        # 默認使用SQLite內存數據庫進行測試
        _db_manager = DatabaseManager("sqlite:///./tasks.db")
        _db_manager.initialize()

    db = _db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


def get_cache_manager():
    """
    獲取緩存管理器

    Returns:
        緩存管理器實例或None
    """
    # TODO: 實現緩存管理器集成
    # 目前返回None，可以集成Redis等緩存
    return None


# Repository管理器
class RepositoryManager:
    """
    Repository管理器
    統一管理所有Repository實例
    """

    def __init__(self, db: Session, cache_manager=None):
        """
        初始化Repository管理器

        Args:
            db: SQLAlchemy數據庫會話
            cache_manager: 緩存管理器
        """
        self.db = db
        self.cache_manager = cache_manager
        self.task_repo = TaskRepository(db, cache_manager)
        self.sprint_repo = SprintRepository(db, cache_manager)

    async def get_repository(self, name: str):
        """
        獲取指定Repository

        Args:
            name: Repository名稱 ('task' 或 'sprint')

        Returns:
            Repository實例
        """
        repositories = {
            'task': self.task_repo,
            'sprint': self.sprint_repo
        }

        if name not in repositories:
            raise ValueError(f"未知的Repository: {name}")

        return repositories[name]


async def get_repository_manager(db: Session) -> RepositoryManager:
    """
    FastAPI依賴：獲取Repository管理器

    Args:
        db: 數據庫會話

    Returns:
        Repository管理器實例
    """
    cache_manager = get_cache_manager()
    return RepositoryManager(db, cache_manager)


# 數據庫健康檢查
async def check_database_health() -> Dict[str, Any]:
    """
    檢查數據庫健康狀態

    Returns:
        健康狀態信息
    """
    try:
        global _db_manager
        if not _db_manager or not _db_manager._engine:
            return {
                "status": "error",
                "message": "數據庫未初始化"
            }

        # 測試連接
        with _db_manager._engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()

        return {
            "status": "healthy",
            "message": "數據庫連接正常",
            "database_url": _db_manager.database_url
        }

    except Exception as e:
        logger.error(f"數據庫健康檢查失敗: {e}")
        return {
            "status": "error",
            "message": f"數據庫連接失敗: {str(e)}"
        }
