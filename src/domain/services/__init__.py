"""
Domain Services - Cross-aggregate business logic
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class DomainService(ABC):
    """Base domain service interface"""
    pass


class ApplicationService(ABC):
    """Base application service interface"""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute application logic"""
        pass
