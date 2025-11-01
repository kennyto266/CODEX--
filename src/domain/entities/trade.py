#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易实体
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects import (
    OrderId, StockSymbol, Price, Money, Quantity,
    OrderSide, Timestamp
)
from ..events import DomainEvent


class TradeStatus(Enum):
    """交易状态"""
    NEW = "new"              # 新建
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    FILLED = "filled"        # 完全成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"    # 已拒绝


@dataclass
class Trade:
    """交易实体"""
    trade_id: str
    order_id: OrderId
    symbol: StockSymbol
    side: OrderSide
    quantity: Quantity
    price: Price
    commission: Money
    trade_time: Timestamp
    status: TradeStatus = TradeStatus.NEW
    filled_quantity: Optional[Quantity] = None
    _events: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        if self.filled_quantity is None:
            self.filled_quantity = self.quantity

    def fill(self, fill_quantity: Quantity, fill_price: Price):
        """成交"""
        self.filled_quantity = fill_quantity
        self.status = TradeStatus.FILLED

        # 触发交易成交事件
        self._events.append(
            TradeExecutedEvent(
                trade_id=self.trade_id,
                order_id=self.order_id,
                symbol=self.symbol,
                side=self.side,
                quantity=fill_quantity,
                price=fill_price,
                timestamp=self.trade_time
            )
        )

    def cancel(self):
        """取消交易"""
        self.status = TradeStatus.CANCELLED

        # 触发交易取消事件
        self._events.append(
            TradeCancelledEvent(
                trade_id=self.trade_id,
                symbol=self.symbol,
                timestamp=self.trade_time
            )
        )

    def reject(self, reason: str):
        """拒绝交易"""
        self.status = TradeStatus.REJECTED

        # 触发交易拒绝事件
        self._events.append(
            TradeRejectedEvent(
                trade_id=self.trade_id,
                symbol=self.symbol,
                reason=reason,
                timestamp=self.trade_time
            )
        )

    def get_total_value(self) -> Money:
        """获取交易总价值"""
        return Money.from_float(self.price.to_float() * self.quantity.value)

    def get_net_value(self) -> Money:
        """获取交易净额"""
        total_value = self.get_total_value()
        return Money(total_value.value - self.commission.value, self.commission.currency)

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._events.append(event)

    def get_domain_events(self) -> list:
        """获取所有领域事件"""
        return self._events.copy()

    def clear_domain_events(self):
        """清除领域事件"""
        self._events.clear()


# 交易事件类
from ..events import DomainEvent as DomainEventBase


class TradeExecutedEvent(DomainEventBase):
    """交易成交事件"""
    trade_id: str
    order_id: OrderId
    symbol: StockSymbol
    side: OrderSide
    quantity: Quantity
    price: Price
    timestamp: Timestamp

    def __init__(self, trade_id: str, order_id: OrderId, symbol: StockSymbol,
                 side: OrderSide, quantity: Quantity, price: Price, timestamp: Timestamp):
        self.trade_id = trade_id
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        super().__init__()


class TradeCancelledEvent(DomainEventBase):
    """交易取消事件"""
    trade_id: str
    symbol: StockSymbol
    timestamp: Timestamp

    def __init__(self, trade_id: str, symbol: StockSymbol, timestamp: Timestamp):
        self.trade_id = trade_id
        self.symbol = symbol
        self.timestamp = timestamp
        super().__init__()


class TradeRejectedEvent(DomainEventBase):
    """交易拒绝事件"""
    trade_id: str
    symbol: StockSymbol
    reason: str
    timestamp: Timestamp

    def __init__(self, trade_id: str, symbol: StockSymbol, reason: str, timestamp: Timestamp):
        self.trade_id = trade_id
        self.symbol = symbol
        self.reason = reason
        self.timestamp = timestamp
        super().__init__()