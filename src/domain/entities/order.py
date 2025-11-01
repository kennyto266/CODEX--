#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单实体
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects import (
    OrderId, StockSymbol, Price, Money, Quantity,
    OrderType, OrderSide, Timestamp
)
from ..events import DomainEvent


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"        # 待处理
    SUBMITTED = "submitted"    # 已提交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    FILLED = "filled"          # 完全成交
    CANCELLED = "cancelled"    # 已取消
    REJECTED = "rejected"      # 已拒绝
    EXPIRED = "expired"        # 已过期


@dataclass
class Order:
    """订单实体"""
    order_id: OrderId
    symbol: StockSymbol
    side: OrderSide
    order_type: OrderType
    quantity: Quantity
    price: Optional[Price] = None  # 市价单为None
    stop_price: Optional[Price] = None  # 止损价格
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[Price] = None
    filled_value: Optional[Money] = None
    remaining_quantity: int = 0
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)
    expires_at: Optional[Timestamp] = None
    notes: str = ""
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        self.remaining_quantity = self.quantity.value

    def submit(self) -> bool:
        """提交订单"""
        if self.status != OrderStatus.PENDING:
            return False

        self.status = OrderStatus.SUBMITTED
        self.updated_at = Timestamp.now()

        # 触发订单提交事件
        self._events.append(
            OrderSubmittedEvent(
                order_id=self.order_id,
                symbol=self.symbol,
                side=self.side,
                quantity=self.quantity,
                price=self.price,
                timestamp=self.updated_at
            )
        )

        return True

    def cancel(self, reason: str = ""):
        """取消订单"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False

        self.status = OrderStatus.CANCELLED
        self.updated_at = Timestamp.now()
        self.notes = reason

        # 触发订单取消事件
        self._events.append(
            OrderCancelledEvent(
                order_id=self.order_id,
                symbol=self.symbol,
                reason=reason,
                timestamp=self.updated_at
            )
        )

        return True

    def fill(self, filled_quantity: int, filled_price: Price) -> bool:
        """部分或完全成交"""
        if self.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            return False

        if filled_quantity <= 0 or filled_quantity > self.remaining_quantity:
            return False

        # 更新成交数量
        old_filled = self.filled_quantity
        self.filled_quantity += filled_quantity
        self.remaining_quantity -= filled_quantity
        self.filled_price = filled_price

        # 计算成交金额
        filled_value = filled_price.value * filled_quantity
        self.filled_value = Money.from_float(filled_value, self.get_currency())

        # 更新状态
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

        self.updated_at = Timestamp.now()

        # 触发订单成交事件
        self._events.append(
            OrderFilledEvent(
                order_id=self.order_id,
                symbol=self.symbol,
                filled_quantity=filled_quantity,
                filled_price=filled_price,
                total_filled=self.filled_quantity,
                remaining=self.remaining_quantity,
                timestamp=self.updated_at
            )
        )

        return True

    def reject(self, reason: str):
        """拒绝订单"""
        if self.status != OrderStatus.PENDING:
            return False

        self.status = OrderStatus.REJECTED
        self.updated_at = Timestamp.now()
        self.notes = reason

        # 触发订单拒绝事件
        self._events.append(
            OrderRejectedEvent(
                order_id=self.order_id,
                symbol=self.symbol,
                reason=reason,
                timestamp=self.updated_at
            )
        )

        return True

    def expire(self):
        """过期订单"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return

        self.status = OrderStatus.EXPIRED
        self.updated_at = Timestamp.now()

        # 触发订单过期事件
        self._events.append(
            OrderExpiredEvent(
                order_id=self.order_id,
                symbol=self.symbol,
                timestamp=self.updated_at
            )
        )

    def get_currency(self) -> str:
        """获取订单货币"""
        # 从股票代码推断货币
        if '.HK' in str(self.symbol):
            return 'HKD'
        elif '.US' in str(self.symbol):
            return 'USD'
        return 'HKD'  # 默认港币

    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.status == OrderStatus.FILLED

    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == OrderStatus.CANCELLED

    def is_active(self) -> bool:
        """是否处于活动状态"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIALLY_FILLED
        ]

    def can_cancel(self) -> bool:
        """是否可以取消"""
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIALLY_FILLED
        ]

    def get_fill_ratio(self) -> float:
        """获取成交比例"""
        if self.quantity.value == 0:
            return 0.0
        return self.filled_quantity / self.quantity.value

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """获取所有领域事件"""
        return self._events.copy()

    def clear_domain_events(self):
        """清除领域事件"""
        self._events.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'order_id': str(self.order_id),
            'symbol': str(self.symbol),
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity.value,
            'price': float(self.price.value) if self.price else None,
            'stop_price': float(self.stop_price.value) if self.stop_price else None,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'filled_price': float(self.filled_price.value) if self.filled_price else None,
            'filled_value': float(self.filled_value.value) if self.filled_value else None,
            'remaining_quantity': self.remaining_quantity,
            'created_at': self.created_at.to_string(),
            'updated_at': self.updated_at.to_string(),
            'expires_at': self.expires_at.to_string() if self.expires_at else None,
            'notes': self.notes,
            'currency': self.get_currency(),
            'fill_ratio': self.get_fill_ratio()
        }


# 订单事件类
class OrderSubmittedEvent(DomainEvent):
    """订单提交事件"""
    order_id: OrderId
    symbol: StockSymbol
    side: OrderSide
    quantity: 'Quantity'
    price: Optional[Price]
    timestamp: Timestamp

    def __init__(self, order_id: OrderId, symbol: StockSymbol, side: OrderSide,
                 quantity: 'Quantity', price: Optional[Price], timestamp: Timestamp):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.__class__.__name__,
            'order_id': str(self.order_id),
            'symbol': str(self.symbol),
            'side': self.side.value,
            'quantity': self.quantity.value,
            'price': float(self.price.value) if self.price else None,
            'timestamp': self.timestamp.to_string()
        }


class OrderFilledEvent(DomainEvent):
    """订单成交事件"""
    order_id: OrderId
    symbol: StockSymbol
    filled_quantity: int
    filled_price: Price
    total_filled: int
    remaining: int
    timestamp: Timestamp

    def __init__(self, order_id: OrderId, symbol: StockSymbol, filled_quantity: int,
                 filled_price: Price, total_filled: int, remaining: int, timestamp: Timestamp):
        self.order_id = order_id
        self.symbol = symbol
        self.filled_quantity = filled_quantity
        self.filled_price = filled_price
        self.total_filled = total_filled
        self.remaining = remaining
        self.timestamp = timestamp
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.__class__.__name__,
            'order_id': str(self.order_id),
            'symbol': str(self.symbol),
            'filled_quantity': self.filled_quantity,
            'filled_price': float(self.filled_price.value),
            'total_filled': self.total_filled,
            'remaining': self.remaining,
            'timestamp': self.timestamp.to_string()
        }


class OrderCancelledEvent(DomainEvent):
    """订单取消事件"""
    order_id: OrderId
    symbol: StockSymbol
    reason: str
    timestamp: Timestamp

    def __init__(self, order_id: OrderId, symbol: StockSymbol, reason: str, timestamp: Timestamp):
        self.order_id = order_id
        self.symbol = symbol
        self.reason = reason
        self.timestamp = timestamp
        super().__init__()


class OrderRejectedEvent(DomainEvent):
    """订单拒绝事件"""
    order_id: OrderId
    symbol: StockSymbol
    reason: str
    timestamp: Timestamp

    def __init__(self, order_id: OrderId, symbol: StockSymbol, reason: str, timestamp: Timestamp):
        self.order_id = order_id
        self.symbol = symbol
        self.reason = reason
        self.timestamp = timestamp
        super().__init__()


class OrderExpiredEvent(DomainEvent):
    """订单过期事件"""
    order_id: OrderId
    symbol: StockSymbol
    timestamp: Timestamp

    def __init__(self, order_id: OrderId, symbol: StockSymbol, timestamp: Timestamp):
        self.order_id = order_id
        self.symbol = symbol
        self.timestamp = timestamp
        super().__init__()