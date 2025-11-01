#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓位实体
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects import StockSymbol, Quantity, Price, Money, Timestamp
from ..events import DomainEvent


class PositionType(Enum):
    """仓位类型"""
    LONG = "long"    # 多头
    SHORT = "short"  # 空头
    FLAT = "flat"    # 空仓


@dataclass
class Position:
    """仓位实体"""
    symbol: StockSymbol
    quantity: Quantity
    avg_price: Price
    market_value: Money
    realized_pnl: Money
    unrealized_pnl: Money
    last_updated: Timestamp = field(default_factory=Timestamp.now)
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        if self.quantity.value == 0:
            self.position_type = PositionType.FLAT
        elif self.quantity.value > 0:
            self.position_type = PositionType.LONG
        else:
            self.position_type = PositionType.SHORT

    def update(self, new_quantity: Quantity, new_avg_price: Price, market_price: Price):
        """更新仓位"""
        old_quantity = self.quantity
        old_market_value = self.market_value

        self.quantity = new_quantity
        self.avg_price = new_avg_price
        self.last_updated = Timestamp.now()

        # 更新市场价值
        self.market_value = Money.from_float(
            new_quantity.value * new_avg_price.value,
            market_price.currency if hasattr(market_price, 'currency') else 'HKD'
        )

        # 计算未实现盈亏
        if new_quantity.value > 0:  # 多头仓位
            self.unrealized_pnl = Money.from_float(
                new_quantity.value * (market_price.to_float() - new_avg_price.value)
            )
        elif new_quantity.value < 0:  # 空头仓位
            self.unrealized_pnl = Money.from_float(
                abs(new_quantity.value) * (new_avg_price.value - market_price.to_float())
            )
        else:  # 空仓
            self.unrealized_pnl = Money.from_float(0)

        # 更新仓位类型
        if self.quantity.value == 0:
            self.position_type = PositionType.FLAT
        elif self.quantity.value > 0:
            self.position_type = PositionType.LONG
        else:
            self.position_type = PositionType.SHORT

        # 触发仓位更新事件
        self._events.append(
            PositionUpdatedEvent(
                symbol=self.symbol,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                old_market_value=old_market_value,
                new_market_value=self.market_value,
                timestamp=self.last_updated
            )
        )

    def add_quantity(self, add_quantity: Quantity, add_price: Price):
        """增加仓位"""
        if add_quantity.value <= 0:
            raise ValueError("增加的数量必须大于零")

        # 计算新的平均价格
        total_quantity = self.quantity.value + add_quantity.value
        total_cost = (
            self.quantity.value * self.avg_price.value +
            add_quantity.value * add_price.value
        )
        new_avg_price = Price.from_float(total_cost / total_quantity)

        self.quantity = Quantity(total_quantity)
        self.avg_price = new_avg_price

        # 触发仓位变化事件
        self._events.append(
            PositionChangedEvent(
                symbol=self.symbol,
                change_type="ADD",
                quantity=add_quantity,
                price=add_price,
                timestamp=Timestamp.now()
            )
        )

    def reduce_quantity(self, reduce_quantity: Quantity, reduce_price: Price):
        """减少仓位"""
        if reduce_quantity.value <= 0:
            raise ValueError("减少的数量必须大于零")

        if reduce_quantity.value > self.quantity.value:
            raise ValueError("减少的数量不能超过当前仓位")

        # 计算实现盈亏
        if reduce_price.to_float() > self.avg_price.value:
            # 盈利
            pnl = (reduce_price.to_float() - self.avg_price.value) * reduce_quantity.value
            self.realized_pnl = Money.from_float(
                self.realized_pnl.value + pnl,
                self.realized_pnl.currency
            )
        else:
            # 亏损
            pnl = (self.avg_price.value - reduce_price.to_float()) * reduce_quantity.value
            self.realized_pnl = Money.from_float(
                self.realized_pnl.value - pnl,
                self.realized_pnl.currency
            )

        # 更新剩余仓位
        self.quantity = Quantity(self.quantity.value - reduce_quantity.value)
        self.last_updated = Timestamp.now()

        # 触发仓位变化事件
        self._events.append(
            PositionChangedEvent(
                symbol=self.symbol,
                change_type="REDUCE",
                quantity=reduce_quantity,
                price=reduce_price,
                timestamp=Timestamp.now()
            )
        )

    def close_position(self, close_price: Price):
        """平仓"""
        self.reduce_quantity(self.quantity, close_price)

    def get_total_pnl(self) -> Money:
        """获取总盈亏"""
        return Money.from_float(
            self.realized_pnl.value + self.unrealized_pnl.value,
            self.realized_pnl.currency
        )

    def get_position_value(self) -> Money:
        """获取仓位价值"""
        return self.market_value

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """获取所有领域事件"""
        return self._events.copy()

    def clear_domain_events(self):
        """清除领域事件"""
        self._events.clear()


# 仓位事件类
from ..events import DomainEvent as DomainEventBase


class PositionUpdatedEvent(DomainEventBase):
    """仓位更新事件"""
    symbol: StockSymbol
    old_quantity: Quantity
    new_quantity: Quantity
    old_market_value: Money
    new_market_value: Money
    timestamp: Timestamp

    def __init__(self, symbol: StockSymbol, old_quantity: Quantity, new_quantity: Quantity,
                 old_market_value: Money, new_market_value: Money, timestamp: Timestamp):
        self.symbol = symbol
        self.old_quantity = old_quantity
        self.new_quantity = new_quantity
        self.old_market_value = old_market_value
        self.new_market_value = new_market_value
        self.timestamp = timestamp
        super().__init__()


class PositionChangedEvent(DomainEventBase):
    """仓位变化事件"""
    symbol: StockSymbol
    change_type: str  # ADD, REDUCE
    quantity: Quantity
    price: Price
    timestamp: Timestamp

    def __init__(self, symbol: StockSymbol, change_type: str, quantity: Quantity,
                 price: Price, timestamp: Timestamp):
        self.symbol = symbol
        self.change_type = change_type
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        super().__init__()