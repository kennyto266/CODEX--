"""
Domain Entities - Core business objects with identity and behavior
"""
from abc import ABC
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Any, Dict
from dataclasses import dataclass, field


class DomainEntity(ABC):
    """Base domain entity with identity and business logic"""

    def __init__(self, id: UUID, created_at: datetime = None, updated_at: datetime = None):
        self._id = id
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    @property
    def id(self) -> UUID:
        """Get entity identity"""
        return self._id

    @property
    def created_at(self) -> datetime:
        """Get creation timestamp"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get last update timestamp"""
        return self._updated_at

    def _mark_updated(self):
        """Mark entity as updated"""
        self._updated_at = datetime.now()

    def __eq__(self, other) -> bool:
        """Entities are equal if they have the same ID"""
        if not isinstance(other, DomainEntity):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on ID"""
        return hash(self._id)


class ValueObject(ABC):
    """Base value object without identity"""

    def __eq__(self, other) -> bool:
        """Value objects are equal if all attributes match"""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hash based on all attributes"""
        return hash(tuple(sorted(self.__dict__.items())))


@dataclass
class DomainEvent:
    """Base domain event"""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def occurred_on(self) -> datetime:
        """When the event occurred"""
        return self.timestamp
