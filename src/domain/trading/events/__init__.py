"""
Trading Domain Events
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from ...entities import DomainEvent
from ..entities import Order, Trade, OrderSide


class OrderPlacedEvent(DomainEvent):
    """Event fired when an order is placed"""

    def __init__(self, order: Order):
        super().__init__()
        self.event_type = "Order.Placed"
        self.event_data = {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "order_type": order.order_type.value,
            "price": order.price,
            "timestamp": datetime.now().isoformat()
        }


class OrderExecutedEvent(DomainEvent):
    """Event fired when an order is executed"""

    def __init__(self, order: Order):
        super().__init__()
        self.event_type = "Order.Executed"
        self.event_data = {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side.value,
            "executed_quantity": order.executed_quantity,
            "executed_price": order.executed_price,
            "remaining_quantity": order.remaining_quantity,
            "is_completed": order.is_completed(),
            "timestamp": datetime.now().isoformat()
        }


class OrderCancelledEvent(DomainEvent):
    """Event fired when an order is cancelled"""

    def __init__(self, order: Order):
        super().__init__()
        self.event_type = "Order.Cancelled"
        self.event_data = {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "executed_quantity": order.executed_quantity,
            "timestamp": datetime.now().isoformat()
        }


class TradeExecutedEvent(DomainEvent):
    """Event fired when a trade is executed"""

    def __init__(self, trade: Trade):
        super().__init__()
        self.event_type = "Trade.Executed"
        self.event_data = {
            "trade_id": str(trade.id),
            "symbol": trade.symbol,
            "side": trade.side.value,
            "quantity": trade.quantity,
            "price": trade.price,
            "gross_amount": trade.gross_amount,
            "net_amount": trade.net_amount,
            "commission": trade.commission,
            "timestamp": datetime.now().isoformat()
        }


class PositionUpdatedEvent(DomainEvent):
    """Event fired when a position is updated"""

    def __init__(self, symbol: str, old_quantity: int, new_quantity: int, avg_price: float):
        super().__init__()
        self.event_type = "Position.Updated"
        self.event_data = {
            "symbol": symbol,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "avg_price": avg_price,
            "change": new_quantity - old_quantity,
            "timestamp": datetime.now().isoformat()
        }


class PortfolioRebalanceRequiredEvent(DomainEvent):
    """Event fired when portfolio rebalancing is required"""

    def __init__(self, portfolio_id: UUID, deviation_threshold: float):
        super().__init__()
        self.event_type = "Portfolio.RebalanceRequired"
        self.event_data = {
            "portfolio_id": str(portfolio_id),
            "deviation_threshold": deviation_threshold,
            "timestamp": datetime.now().isoformat()
        }
