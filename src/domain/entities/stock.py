#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票实体
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..value_objects import StockSymbol, Price, Timestamp
from ..events import DomainEvent


@dataclass
class Stock:
    """股票实体"""
    symbol: StockSymbol
    name: str
    market: str
    currency: str = 'HKD'
    last_price: Optional[Price] = None
    volume: int = 0
    market_cap: Optional[float] = None
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)
    _events: list = field(default_factory=list, init=False, repr=False)

    def update_price(self, new_price: Price, timestamp: Optional[Timestamp] = None):
        """更新价格"""
        if timestamp is None:
            timestamp = Timestamp.now()

        old_price = self.last_price
        self.last_price = new_price
        self.updated_at = timestamp

        # 触发价格变动事件
        if old_price:
            self._events.append(
                PriceChangedEvent(
                    symbol=self.symbol,
                    old_price=old_price,
                    new_price=new_price,
                    timestamp=timestamp
                )
            )

    def update_volume(self, new_volume: int):
        """更新成交量"""
        self.volume = new_volume
        self.updated_at = Timestamp.now()

    def get_daily_change(self) -> Optional[float]:
        """获取日涨跌"""
        # 这里需要从历史数据计算，暂时返回None
        return None

    def add_domain_event(self, event: DomainEvent):
        """添加领域事件"""
        self._events.append(event)

    def get_domain_events(self) -> list:
        """获取所有领域事件"""
        return self._events.copy()

    def clear_domain_events(self):
        """清除领域事件"""
        self._events.clear()


class PriceChangedEvent(DomainEvent):
    """价格变动事件"""
    symbol: StockSymbol
    old_price: Price
    new_price: Price
    timestamp: Timestamp

    def __init__(self, symbol: StockSymbol, old_price: Price, new_price: Price, timestamp: Timestamp):
        self.symbol = symbol
        self.old_price = old_price
        self.new_price = new_price
        self.timestamp = timestamp
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.__class__.__name__,
            'symbol': str(self.symbol),
            'old_price': float(self.old_price.value),
            'new_price': float(self.new_price.value),
            'timestamp': self.timestamp.to_string()
        }