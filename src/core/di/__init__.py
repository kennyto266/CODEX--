"""
Dependency Injection Container
"""
from typing import Dict, Type, Any, Callable, Optional
import inspect


class DIContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register(self,
                 interface: Type,
                 implementation: Type = None,
                 singleton: bool = True,
                 factory: Callable = None):
        """Register a service"""
        if factory:
            self._factories[interface] = factory
        else:
            if implementation:
                self._services[interface] = implementation
            self._singletons[interface] = singleton

    def register_singleton(self, interface: Type, instance: Any):
        """Register a singleton instance directly"""
        self._singletons[interface] = instance

    async def resolve(self, interface: Type) -> Any:
        """Resolve a dependency"""
        # Check for existing singleton
        if interface in self._singletons and not isinstance(self._singletons[interface], bool):
            return self._singletons[interface]

        # Get implementation
        implementation = self._services.get(interface)
        if not implementation:
            raise ValueError(f"Service not registered: {interface}")

        # Create instance
        instance = implementation()

        # Store singleton if needed
        if self._singletons.get(interface, False):
            self._singletons[interface] = instance

        return instance

    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered"""
        return interface in self._services

    def clear(self):
        """Clear all registrations"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """Get global container instance"""
    return _container


def inject(func: Callable) -> Callable:
    """Decorator for automatic dependency injection"""
    sig = inspect.signature(func)

    async def wrapper(*args, **kwargs):
        # Inject dependencies
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty and get_container().is_registered(param.annotation):
                injected = await get_container().resolve(param.annotation)
                kwargs[param_name] = injected

        return await func(*args, **kwargs)

    return wrapper
