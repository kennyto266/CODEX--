"""
Event Bus - Lightweight event-driven architecture
"""
from typing import Dict, List, Callable, Any, Type
from collections import defaultdict
import inspect


class EventBus:
    """Simple in-memory event bus"""

    def __init__(self):
        self._handlers: Dict[Any, List[Callable]] = defaultdict(list)
        self._middlewares: List[Callable] = []

    def subscribe(self, event_type, handler: Callable):
        """Subscribe to an event type"""
        self._handlers[event_type].append(handler)

    def add_middleware(self, middleware: Callable):
        """Add event processing middleware"""
        self._middlewares.append(middleware)

    async def publish(self, event):
        """Publish an event"""
        # Apply middlewares
        for middleware in self._middlewares:
            await middleware(event)

        # Notify handlers
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

    def clear(self):
        """Clear all subscriptions"""
        self._handlers.clear()
        self._middlewares.clear()


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    return _event_bus


# Convenience decorators
def event_handler(event_type):
    """Decorator to register an event handler"""
    def decorator(func: Callable):
        get_event_bus().subscribe(event_type, func)
        return func
    return decorator


import inspect
