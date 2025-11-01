#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合实体
"""

from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum

from ..value_objects import Money, Price, Timestamp, Percentage
from .position import Position
from .strategy import Strategy
from ..events import DomainEvent


class PortfolioType(Enum):
    """投资组合类型"""
    LONG_ONLY = "long_only"           # 仅多头
    LONG_SHORT = "long_short"        # 多空
    MARKET_NEUTRAL = "market_neutral"  # 市场中性
    SECTOR_SPECIFIC = "sector_specific"  # 行业特定


@dataclass
class Portfolio:
    """投资组合实体"""
    name: str
    portfolio_type: PortfolioType
    initial_capital: Money
    cash: Money
    positions: Dict[str, Position] = field(default_factory=dict)  # symbol -> Position
    strategies: Dict[str, Strategy] = field(default_factory=dict)  # strategy_id -> Strategy
    total_value: Money = field(init=False)
    realized_pnl: Money = field(init=False)
    unrealized_pnl: Money = field(init=False)
    total_return: Money = field(init=False)
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        self.total_value = self.cash
        self.realized_pnl = Money.from_float(0, self.cash.currency)
        self.unrealized_pnl = Money.from_float(0, self.cash.currency)
        self.total_return = Money.from_float(0, self.cash.currency)

    def add_position(self, position: Position):
        """添加仓位"""
        symbol = str(position.symbol)
        self.positions[symbol] = position
        self.updated_at = Timestamp.now()

        # 更新投资组合价值
        self._recalculate_portfolio_value()

        # 触发仓位添加事件
        self._events.append(
            PositionAddedEvent(
                portfolio_name=self.name,
                symbol=position.symbol,
                quantity=position.quantity,
                timestamp=self.updated_at
            )
        )

    def remove_position(self, symbol: str):
        """移除仓位"""
        if symbol in self.positions:
            position = self.positions.pop(symbol)
            self.updated_at = Timestamp.now()

            # 更新投资组合价值
            self._recalculate_portfolio_value()

            # 触发仓位移除事件
            self._events.append(
                PositionRemovedEvent(
                    portfolio_name=self.name,
                    symbol=position.symbol,
                    timestamp=self.updated_at
                )
            )

    def update_position(self, symbol: str, quantity, avg_price: Price, market_price: Price):
        """更新仓位"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.update(quantity, avg_price, market_price)
            self.updated_at = Timestamp.now()

            # 更新投资组合价值
            self._recalculate_portfolio_value()

            # 触发仓位更新事件
            self._events.append(
                PositionUpdatedEvent(
                    portfolio_name=self.name,
                    symbol=position.symbol,
                    quantity=quantity,
                    price=avg_price,
                    timestamp=self.updated_at
                )
            )

    def add_strategy(self, strategy: Strategy):
        """添加策略"""
        strategy_id = str(strategy.strategy_id)
        self.strategies[strategy_id] = strategy
        self.updated_at = Timestamp.now()

        # 触发策略添加事件
        self._events.append(
            StrategyAddedEvent(
                portfolio_name=self.name,
                strategy_id=strategy.strategy_id,
                strategy_name=strategy.name,
                timestamp=self.updated_at
            )
        )

    def remove_strategy(self, strategy_id: str):
        """移除策略"""
        if strategy_id in self.strategies:
            strategy = self.strategies.pop(strategy_id)
            self.updated_at = Timestamp.now()

            # 触发策略移除事件
            self._events.append(
                StrategyRemovedEvent(
                    portfolio_name=self.name,
                    strategy_id=strategy.strategy_id,
                    strategy_name=strategy.name,
                    timestamp=self.updated_at
                )
            )

    def deposit(self, amount: Money):
        """存入资金"""
        if amount.currency != self.cash.currency:
            raise ValueError(f"货币不匹配: {amount.currency} vs {self.cash.currency}")

        self.cash = Money(self.cash.value + amount.value, self.cash.currency)
        self.updated_at = Timestamp.now()

        # 更新投资组合价值
        self._recalculate_portfolio_value()

        # 触发资金存入事件
        self._events.append(
            CashDepositedEvent(
                portfolio_name=self.name,
                amount=amount,
                timestamp=self.updated_at
            )
        )

    def withdraw(self, amount: Money):
        """提取资金"""
        if amount.currency != self.cash.currency:
            raise ValueError(f"货币不匹配: {amount.currency} vs {self.cash.currency}")

        if amount.value > self.cash.value:
            raise ValueError("提取金额不能超过可用现金")

        self.cash = Money(self.cash.value - amount.value, self.cash.currency)
        self.updated_at = Timestamp.now()

        # 更新投资组合价值
        self._recalculate_portfolio_value()

        # 触发资金提取事件
        self._events.append(
            CashWithdrawnEvent(
                portfolio_name=self.name,
                amount=amount,
                timestamp=self.updated_at
            )
        )

    def _recalculate_portfolio_value(self):
        """重新计算投资组合价值"""
        # 计算总仓位价值
        total_positions_value = Money.from_float(0, self.cash.currency)
        total_unrealized_pnl = Money.from_float(0, self.cash.currency)

        for position in self.positions.values():
            total_positions_value = Money(
                total_positions_value.value + position.market_value.value,
                total_positions_value.currency
            )
            total_unrealized_pnl = Money(
                total_unrealized_pnl.value + position.unrealized_pnl.value,
                total_unrealized_pnl.currency
            )

        # 更新总价值
        self.total_value = Money(
            self.cash.value + total_positions_value.value,
            self.cash.currency
        )

        # 更新未实现盈亏
        self.unrealized_pnl = total_unrealized_pnl

        # 计算总收益
        self.total_return = Money(
            self.total_value.value - self.initial_capital.value,
            self.cash.currency
        )

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取仓位"""
        return self.positions.get(symbol)

    def get_total_positions_value(self) -> Money:
        """获取总仓位价值"""
        total = Money.from_float(0, self.cash.currency)
        for position in self.positions.values():
            total = Money(
                total.value + position.market_value.value,
                total.currency
            )
        return total

    def get_leverage_ratio(self) -> float:
        """获取杠杆比率"""
        if self.total_value.value == 0:
            return 0.0

        positions_value = self.get_total_positions_value().value
        return positions_value / self.total_value.value

    def get_cash_percentage(self) -> float:
        """获取现金占比"""
        if self.total_value.value == 0:
            return 0.0

        return (self.cash.value / self.total_value.value) * 100

    def get_number_of_positions(self) -> int:
        """获取仓位数量"""
        return len(self.positions)

    def get_number_of_strategies(self) -> int:
        """获取策略数量"""
        return len(self.strategies)

    def get_symbols(self) -> Set[str]:
        """获取所有股票代码"""
        return set(self.positions.keys())

    def get_top_positions(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """获取前N大仓位"""
        positions_list = []
        for symbol, position in self.positions.items():
            positions_list.append({
                'symbol': symbol,
                'quantity': position.quantity.value,
                'market_value': position.market_value.value,
                'unrealized_pnl': position.unrealized_pnl.value,
                'position_type': position.position_type.value
            })

        # 按市场价值排序
        positions_list.sort(key=lambda x: x['market_value'], reverse=True)
        return positions_list[:top_n]

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
            'name': self.name,
            'portfolio_type': self.portfolio_type.value,
            'initial_capital': self.initial_capital.value,
            'cash': self.cash.value,
            'total_value': self.total_value.value,
            'realized_pnl': self.realized_pnl.value,
            'unrealized_pnl': self.unrealized_pnl.value,
            'total_return': self.total_return.value,
            'number_of_positions': self.get_number_of_positions(),
            'number_of_strategies': self.get_number_of_strategies(),
            'cash_percentage': self.get_cash_percentage(),
            'leverage_ratio': self.get_leverage_ratio(),
            'created_at': self.created_at.to_string(),
            'updated_at': self.updated_at.to_string()
        }


# 投资组合事件类
from ..events import DomainEvent as DomainEventBase


class PositionAddedEvent(DomainEventBase):
    """仓位添加事件"""
    portfolio_name: str
    symbol: str
    quantity: 'Quantity'
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, symbol: str, quantity: 'Quantity', timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.symbol = symbol
        self.quantity = quantity
        self.timestamp = timestamp
        super().__init__()


class PositionRemovedEvent(DomainEventBase):
    """仓位移除事件"""
    portfolio_name: str
    symbol: str
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, symbol: str, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.symbol = symbol
        self.timestamp = timestamp
        super().__init__()


class PositionUpdatedEvent(DomainEventBase):
    """仓位更新事件"""
    portfolio_name: str
    symbol: str
    quantity: 'Quantity'
    price: Price
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, symbol: str, quantity: 'Quantity',
                 price: Price, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        super().__init__()


class StrategyAddedEvent(DomainEventBase):
    """策略添加事件"""
    portfolio_name: str
    strategy_id: str
    strategy_name: str
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, strategy_id: str, strategy_name: str, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.timestamp = timestamp
        super().__init__()


class StrategyRemovedEvent(DomainEventBase):
    """策略移除事件"""
    portfolio_name: str
    strategy_id: str
    strategy_name: str
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, strategy_id: str, strategy_name: str, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.timestamp = timestamp
        super().__init__()


class CashDepositedEvent(DomainEventBase):
    """现金存入事件"""
    portfolio_name: str
    amount: Money
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, amount: Money, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.amount = amount
        self.timestamp = timestamp
        super().__init__()


class CashWithdrawnEvent(DomainEventBase):
    """现金提取事件"""
    portfolio_name: str
    amount: Money
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, amount: Money, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.amount = amount
        self.timestamp = timestamp
        super().__init__()