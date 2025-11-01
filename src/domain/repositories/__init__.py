"""
Repository Interfaces - Abstract data access patterns
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar
from uuid import UUID
from ..entities import DomainEntity

T = TypeVar('T', bound=DomainEntity)


class Repository(ABC, Generic[T]):
    """Base repository interface"""

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Optional[T]:
        """Find entity by ID"""
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """Find all entities"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)"""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""
        pass


class Command(ABC):
    """Base command interface"""
    pass


class Query(ABC):
    """Base query interface"""
    pass


class UnitOfWork(ABC):
    """Unit of Work pattern for transaction management"""

    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction"""
        pass

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
