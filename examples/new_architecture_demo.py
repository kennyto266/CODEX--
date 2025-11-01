#!/usr/bin/env python3
"""
Demo: New Layered Architecture
Demonstrates the new DDD-based layered architecture
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from uuid import uuid4

# Import new architecture components
from src.domain.entities import DomainEntity, DomainEvent
from src.domain.trading.entities import Order, OrderId, OrderSide, OrderType
from src.domain.repositories import Repository
from src.domain.services import DomainService
from src.core.di import get_container
from src.core.events import get_event_bus, event_handler
from src.core.logging import get_logger
from src.core.config import get_settings

# Setup logger
logger = get_logger("demo")


class OrderExecutedEvent(DomainEvent):
    """Domain event for order execution"""
    def __init__(self, order_id: str, symbol: str, quantity: int, price: float):
        super().__init__()
        self.event_type = "Order.Executed"
        self.event_data = {
            "order_id": order_id,
            "symbol": symbol,
            "quantity": quantity,
            "price": price
        }


class OrderRepository(Repository[Order]):
    """In-memory order repository"""

    def __init__(self):
        self._orders = {}

    async def find_by_id(self, id):
        """Find order by ID"""
        return self._orders.get(id)

    async def find_all(self):
        """Find all orders"""
        return list(self._orders.values())

    async def save(self, order: Order) -> Order:
        """Save order"""
        self._orders[order.id] = order
        return order

    async def delete(self, id) -> bool:
        """Delete order"""
        if id in self._orders:
            del self._orders[id]
            return True
        return False

    async def exists(self, id) -> bool:
        """Check if order exists"""
        return id in self._orders


class OrderService(DomainService):
    """Domain service for order operations"""

    def __init__(self, repository: Repository[Order]):
        self._repository = repository

    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        price: float = None
    ) -> Order:
        """Create a new order"""
        order_id = OrderId.create()
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price
        )

        await self._repository.save(order)
        logger.info("Order created", order_id=str(order.id), symbol=symbol)

        return order

    async def execute_order(self, order_id, executed_quantity: int, executed_price: float):
        """Execute an order"""
        order = await self._repository.find_by_id(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        order.execute(executed_quantity, executed_price)
        await self._repository.save(order)

        # Publish domain event
        event_bus = get_event_bus()
        event = OrderExecutedEvent(
            order_id=str(order.id),
            symbol=order.symbol,
            quantity=executed_quantity,
            price=executed_price
        )
        await event_bus.publish(event)

        logger.info("Order executed",
                   order_id=str(order.id),
                   symbol=order.symbol,
                   quantity=executed_quantity,
                   price=executed_price)

        return order


@event_handler(OrderExecutedEvent)
def handle_order_executed(event: OrderExecutedEvent):
    """Event handler for order execution"""
    logger.info("Handling order executed event",
               order_id=event.event_data["order_id"],
               symbol=event.event_data["symbol"])


async def main():
    """Main demo function"""
    # Load configuration
    settings = get_settings()
    logger.info("Configuration loaded",
               environment=settings.app.environment,
               debug=settings.app.debug)

    # Setup dependency injection
    container = get_container()
    container.register(OrderRepository, OrderRepository, singleton=True)

    # Get order service
    repo = await container.resolve(OrderRepository)
    service = OrderService(repo)

    # Create an order
    logger.info("=== Creating Order ===")
    order = await service.create_order(
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )
    print(f"Created order: {order.to_dict()}")

    # Execute the order
    logger.info("=== Executing Order ===")
    executed_order = await service.execute_order(
        order_id=order.id,
        executed_quantity=1000,
        executed_price=350.0
    )
    print(f"Executed order: {executed_order.to_dict()}")

    # List all orders
    logger.info("=== Listing All Orders ===")
    all_orders = await repo.find_all()
    print(f"Total orders: {len(all_orders)}")

    logger.info("Demo completed successfully")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
