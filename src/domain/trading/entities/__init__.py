"""
Trading Domain Entities
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Dict, Any, List
from ...entities import DomainEntity, ValueObject


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TradeType(Enum):
    """Trade type enumeration"""
    TRADE = "trade"
    ADJUSTMENT = "adjustment"
    DIVIDEND = "dividend"
    FEE = "fee"


@dataclass
class OrderId:
    """Value object for order ID"""
    value: UUID

    @staticmethod
    def create() -> OrderId:
        return OrderId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class TradeId:
    """Value object for trade ID"""
    value: UUID

    @staticmethod
    def create() -> TradeId:
        return TradeId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class PositionId:
    """Value object for position ID"""
    value: UUID

    @staticmethod
    def create() -> PositionId:
        return PositionId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


class Order(DomainEntity):
    """
    Order aggregate root
    Contains order details and business logic
    """

    def __init__(
        self,
        order_id: OrderId,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None
    ):
        from datetime import datetime
        super().__init__(id=order_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._symbol = symbol
        self._side = side
        self._quantity = quantity
        self._order_type = order_type
        self._price = price
        self._status = OrderStatus.PENDING
        self._executed_quantity = 0
        self._executed_price = 0.0

    @property
    def symbol(self) -> str:
        """Get order symbol"""
        return self._symbol

    @property
    def side(self) -> OrderSide:
        """Get order side"""
        return self._side

    @property
    def quantity(self) -> int:
        """Get order quantity"""
        return self._quantity

    @property
    def order_type(self) -> OrderType:
        """Get order type"""
        return self._order_type

    @property
    def price(self) -> Optional[float]:
        """Get order price"""
        return self._price

    @property
    def status(self) -> OrderStatus:
        """Get order status"""
        return self._status

    @property
    def executed_quantity(self) -> int:
        """Get executed quantity"""
        return self._executed_quantity

    @property
    def executed_price(self) -> float:
        """Get executed price"""
        return self._executed_price

    @property
    def remaining_quantity(self) -> int:
        """Get remaining quantity to execute"""
        return self._quantity - self._executed_quantity

    def execute(self, executed_quantity: int, executed_price: float) -> None:
        """
        Execute the order
        """
        if self._status != OrderStatus.PENDING:
            raise ValueError(f"Cannot execute order in status {self._status}")

        if executed_quantity > self.remaining_quantity:
            raise ValueError("Executed quantity cannot exceed remaining quantity")

        if executed_quantity <= 0:
            raise ValueError("Executed quantity must be positive")

        self._executed_quantity += executed_quantity
        self._executed_price = executed_price

        if self._executed_quantity == self._quantity:
            self._status = OrderStatus.EXECUTED
        else:
            # Partial execution
            self._status = OrderStatus.PENDING

        self._mark_updated()

    def cancel(self) -> None:
        """Cancel the order"""
        if self._status != OrderStatus.PENDING:
            raise ValueError(f"Cannot cancel order in status {self._status}")

        self._status = OrderStatus.CANCELLED
        self._mark_updated()

    def reject(self, reason: str) -> None:
        """Reject the order"""
        if self._status != OrderStatus.PENDING:
            raise ValueError(f"Cannot reject order in status {self._status}")

        self._status = OrderStatus.REJECTED
        self._mark_updated()

    def is_completed(self) -> bool:
        """Check if order is fully executed"""
        return self._status == OrderStatus.EXECUTED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "symbol": self._symbol,
            "side": self._side.value,
            "quantity": self._quantity,
            "order_type": self._order_type.value,
            "price": self._price,
            "status": self._status.value,
            "executed_quantity": self._executed_quantity,
            "executed_price": self._executed_price,
            "remaining_quantity": self.remaining_quantity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Trade(DomainEntity):
    """
    Trade entity
    Represents a completed transaction
    """

    def __init__(
        self,
        trade_id: TradeId,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float,
        trade_type: TradeType = TradeType.TRADE,
        commission: float = 0.0
    ):
        from datetime import datetime
        super().__init__(id=trade_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._symbol = symbol
        self._side = side
        self._quantity = quantity
        self._price = price
        self._trade_type = trade_type
        self._commission = commission
        self._gross_amount = quantity * price
        self._net_amount = self._gross_amount - commission

    @property
    def symbol(self) -> str:
        """Get trade symbol"""
        return self._symbol

    @property
    def side(self) -> OrderSide:
        """Get trade side"""
        return self._side

    @property
    def quantity(self) -> int:
        """Get trade quantity"""
        return self._quantity

    @property
    def price(self) -> float:
        """Get trade price"""
        return self._price

    @property
    def trade_type(self) -> TradeType:
        """Get trade type"""
        return self._trade_type

    @property
    def commission(self) -> float:
        """Get commission"""
        return self._commission

    @property
    def gross_amount(self) -> float:
        """Get gross amount (quantity * price)"""
        return self._gross_amount

    @property
    def net_amount(self) -> float:
        """Get net amount (gross - commission)"""
        return self._net_amount

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "symbol": self._symbol,
            "side": self._side.value,
            "quantity": self._quantity,
            "price": self._price,
            "trade_type": self._trade_type.value,
            "commission": self._commission,
            "gross_amount": self._gross_amount,
            "net_amount": self._net_amount,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Position(DomainEntity):
    """
    Position entity
    Represents holdings in a security
    """

    def __init__(
        self,
        position_id: PositionId,
        symbol: str,
        quantity: int = 0,
        avg_price: float = 0.0
    ):
        from datetime import datetime
        super().__init__(id=position_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._symbol = symbol
        self._quantity = quantity
        self._avg_price = avg_price
        self._cost_basis = quantity * avg_price

    @property
    def symbol(self) -> str:
        """Get position symbol"""
        return self._symbol

    @property
    def quantity(self) -> int:
        """Get position quantity"""
        return self._quantity

    @property
    def avg_price(self) -> float:
        """Get average price"""
        return self._avg_price

    @property
    def cost_basis(self) -> float:
        """Get cost basis"""
        return self._cost_basis

    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self._quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self._quantity < 0

    @property
    def is_flat(self) -> bool:
        """Check if position is flat"""
        return self._quantity == 0

    def update_position(self, trade: Trade) -> None:
        """
        Update position based on a trade
        """
        if trade.symbol != self._symbol:
            raise ValueError(f"Trade symbol {trade.symbol} doesn't match position symbol {self._symbol}")

        # Calculate new quantity and avg price
        if trade.side == OrderSide.BUY:
            new_quantity = self._quantity + trade.quantity
            if new_quantity != 0:
                new_cost_basis = self._cost_basis + trade.net_amount
                new_avg_price = abs(new_cost_basis / new_quantity)
            else:
                new_avg_price = 0.0
        else:  # SELL
            new_quantity = self._quantity - trade.quantity
            # For sells, avg price remains the same unless we're closing the position
            new_cost_basis = new_quantity * self._avg_price if new_quantity > 0 else 0
            new_avg_price = self._avg_price if new_quantity > 0 else 0.0

        self._quantity = new_quantity
        self._avg_price = new_avg_price
        self._cost_basis = new_cost_basis

        self._mark_updated()

    def market_value(self, current_price: float) -> float:
        """Calculate current market value"""
        return self._quantity * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        return self.market_value(current_price) - self._cost_basis

    def unrealized_pnl_percent(self, current_price: float) -> float:
        """Calculate unrealized P&L percentage"""
        if self._cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl(current_price) / abs(self._cost_basis)) * 100

    def to_dict(self, current_price: Optional[float] = None) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "id": str(self.id),
            "symbol": self._symbol,
            "quantity": self._quantity,
            "avg_price": self._avg_price,
            "cost_basis": self._cost_basis,
            "is_long": self.is_long,
            "is_short": self.is_short,
            "is_flat": self.is_flat,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

        if current_price is not None:
            result.update({
                "current_price": current_price,
                "market_value": self.market_value(current_price),
                "unrealized_pnl": self.unrealized_pnl(current_price),
                "unrealized_pnl_percent": self.unrealized_pnl_percent(current_price)
            })

        return result
