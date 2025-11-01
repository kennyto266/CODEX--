"""
Test suite for new layered architecture
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime

# Import new architecture components
from src.domain.entities import DomainEntity
from src.domain.trading.entities import Order, OrderId, OrderSide, OrderType
from src.domain.repositories import Repository
from src.core.di import get_container
from src.core.events import get_event_bus, event_handler
from src.core.config import get_settings


class InMemoryOrderRepository(Repository[Order]):
    """Test implementation of order repository"""

    def __init__(self):
        self._orders = {}

    async def find_by_id(self, id):
        return self._orders.get(id)

    async def find_all(self):
        return list(self._orders.values())

    async def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    async def delete(self, id) -> bool:
        if id in self._orders:
            del self._orders[id]
            return True
        return False

    async def exists(self, id) -> bool:
        return id in self._orders


@pytest.mark.asyncio
async def test_layered_architecture():
    """Test that the new layered architecture is working"""
    # 1. Test configuration
    settings = get_settings()
    assert settings.app.name == "CODEX Trading System"
    assert settings.app.version == "7.0.0"

    # 2. Test DI container
    container = get_container()
    container.register(Order, InMemoryOrderRepository, singleton=True)

    # 3. Test domain entities
    order_id = OrderId.create()
    order = Order(
        order_id=order_id,
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )

    assert order.symbol == "0700.HK"
    assert order.status.value == "pending"
    assert isinstance(order.id, uuid4().__class__)

    # 4. Test business logic
    order.execute(1000, 350.0)
    assert order.status.value == "executed"
    assert order.executed_quantity == 1000
    assert order.executed_price == 350.0

    # 5. Test repository pattern
    repo = await container.resolve(Order)
    await repo.save(order)

    found_order = await repo.find_by_id(order.id)
    assert found_order is not None
    assert found_order.symbol == "0700.HK"

    # 6. Test event system
    events_received = []

    async def event_handler(event):
        events_received.append(event)

    event_bus = get_event_bus()
    event_bus.subscribe(type(order), event_handler)

    await event_bus.publish(order)
    assert len(events_received) == 1

    print("✅ All architecture tests passed!")


@pytest.mark.asyncio
async def test_domain_business_rules():
    """Test domain business rules"""
    order_id = OrderId.create()
    order = Order(
        order_id=order_id,
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )

    # Test that we can't execute a cancelled order
    order.cancel()
    assert order.status.value == "cancelled"

    with pytest.raises(ValueError):
        order.execute(1000, 350.0)

    print("✅ Domain business rules validated!")


if __name__ == "__main__":
    asyncio.run(test_layered_architecture())
    asyncio.run(test_domain_business_rules())
