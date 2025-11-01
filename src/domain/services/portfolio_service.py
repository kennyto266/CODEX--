#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合服务
处理投资组合管理和优化的业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
import asyncio

from ..entities import Portfolio, Position
from ..value_objects import (
    StockSymbol, Price, Money, Timestamp, Percentage
)
from ..events import DomainEvent


class PortfolioService:
    """投资组合服务"""

    def __init__(self, event_bus):
        """初始化投资组合服务"""
        self.event_bus = event_bus
        self._portfolios: Dict[str, Portfolio] = {}

    async def create_portfolio(self, name: str, portfolio_type: str,
                              initial_capital: float, currency: str = 'HKD') -> Portfolio:
        """创建投资组合"""
        portfolio = Portfolio(
            name=name,
            portfolio_type=portfolio_type,
            initial_capital=Money.from_float(initial_capital, currency),
            cash=Money.from_float(initial_capital, currency)
        )

        self._portfolios[name] = portfolio

        # 发布投资组合创建事件
        await self.event_bus.publish(PortfolioCreatedEvent(
            portfolio_name=name,
            initial_capital=initial_capital,
            currency=currency,
            timestamp=Timestamp.now()
        ))

        return portfolio

    async def update_portfolio_value(self, portfolio: Portfolio, market_prices: Dict[str, Price]):
        """更新投资组合价值"""
        for symbol_str, market_price in market_prices.items():
            symbol = StockSymbol(symbol_str)

            if symbol_str in portfolio.positions:
                position = portfolio.positions[symbol_str]

                # 更新仓位价值
                new_market_value = Money.from_float(
                    position.quantity.value * market_price.value,
                    'HKD'
                )
                unrealized_pnl = self._calculate_unrealized_pnl(position, market_price)

                position.market_value = new_market_value
                position.unrealized_pnl = unrealized_pnl

        # 重新计算投资组合价值
        portfolio._recalculate_portfolio_value()

    async def rebalance_portfolio(self, portfolio: Portfolio,
                                 target_allocations: Dict[str, float]) -> List[str]:
        """重新平衡投资组合"""
        trades = []

        for symbol, target_allocation in target_allocations.items():
            current_position = portfolio.get_position(symbol)

            # 计算目标金额
            target_value = portfolio.total_value.value * target_allocation

            if current_position:
                # 现有仓位调整
                current_value = current_position.market_value.value
                difference = target_value - current_value

                if abs(difference) > 1000:  # 调整阈值
                    if difference > 0:
                        # 需要买入
                        buy_quantity = int(difference / current_position.avg_price.value)
                        if buy_quantity > 0:
                            trades.append(f"BUY {symbol} {buy_quantity}")
                            # 更新仓位
                            current_position.add_quantity(Quantity(buy_quantity), current_position.avg_price)
                    else:
                        # 需要卖出
                        sell_quantity = min(abs(difference) // current_position.avg_price.value,
                                          current_position.quantity.value)
                        if sell_quantity > 0:
                            trades.append(f"SELL {symbol} {sell_quantity}")
                            # 更新仓位
                            current_position.reduce_quantity(Quantity(sell_quantity), current_position.avg_price)
            else:
                # 新建仓位
                if target_value > 1000:  # 最小仓位阈值
                    # 这里需要获取当前价格
                    trades.append(f"BUY {symbol} {int(target_value / 100)}")  # 简化计算

        return trades

    async def calculate_performance_metrics(self, portfolio: Portfolio) -> Dict[str, float]:
        """计算投资组合性能指标"""
        metrics = {}

        # 基础指标
        metrics['total_return'] = portfolio.total_return.value
        metrics['return_percentage'] = (portfolio.total_return.value / portfolio.initial_capital.value) * 100
        metrics['unrealized_pnl'] = portfolio.unrealized_pnl.value
        metrics['realized_pnl'] = portfolio.realized_pnl.value

        # 仓位指标
        metrics['number_of_positions'] = portfolio.get_number_of_positions()
        metrics['cash_percentage'] = portfolio.get_cash_percentage()
        metrics['leverage_ratio'] = portfolio.get_leverage_ratio()

        # 风险指标
        metrics['max_single_position'] = self._get_max_position_weight(portfolio)
        metrics['concentration_risk'] = self._calculate_concentration_risk(portfolio)

        return metrics

    def get_portfolio_summary(self, portfolio: Portfolio) -> Dict[str, Any]:
        """获取投资组合摘要"""
        summary = portfolio.to_dict()

        # 添加详细仓位信息
        summary['detailed_positions'] = []
        for symbol, position in portfolio.positions.items():
            summary['detailed_positions'].append({
                'symbol': symbol,
                'quantity': position.quantity.value,
                'avg_price': position.avg_price.value,
                'market_price': position.market_value.value,
                'unrealized_pnl': position.unrealized_pnl.value,
                'realized_pnl': position.realized_pnl.value,
                'position_type': position.position_type.value
            })

        return summary

    def _calculate_unrealized_pnl(self, position: Position, current_price: Price) -> Money:
        """计算未实现盈亏"""
        if position.quantity.value > 0:  # 多头仓位
            return Money.from_float(
                position.quantity.value * (current_price.value - position.avg_price.value)
            )
        elif position.quantity.value < 0:  # 空头仓位
            return Money.from_float(
                abs(position.quantity.value) * (position.avg_price.value - current_price.value)
            )
        else:  # 空仓
            return Money.from_float(0)

    def _get_max_position_weight(self, portfolio: Portfolio) -> float:
        """获取最大仓位权重"""
        if portfolio.total_value.value == 0:
            return 0.0

        max_weight = 0.0
        for position in portfolio.positions.values():
            weight = abs(position.market_value.value) / portfolio.total_value.value
            max_weight = max(max_weight, weight)

        return max_weight * 100

    def _calculate_concentration_risk(self, portfolio: Portfolio) -> float:
        """计算集中度风险（简化计算）"""
        if not portfolio.positions:
            return 0.0

        # 使用赫芬达尔指数（HHI）衡量集中度
        hhi = 0.0
        total_value = sum(abs(pos.market_value.value) for pos in portfolio.positions.values())

        if total_value > 0:
            for position in portfolio.positions.values():
                weight = abs(position.market_value.value) / total_value
                hhi += weight ** 2

        return hhi * 100  # 返回百分比

    def get_portfolio(self, name: str) -> Optional[Portfolio]:
        """获取投资组合"""
        return self._portfolios.get(name)

    def get_all_portfolios(self) -> List[Portfolio]:
        """获取所有投资组合"""
        return list(self._portfolios.values())


# 导入依赖
from ..entities import Portfolio as PortfolioEntity
from ..value_objects import Quantity


class PortfolioCreatedEvent(DomainEvent):
    """投资组合创建事件"""
    portfolio_name: str
    initial_capital: float
    currency: str
    timestamp: Timestamp

    def __init__(self, portfolio_name: str, initial_capital: float, currency: str, timestamp: Timestamp):
        self.portfolio_name = portfolio_name
        self.initial_capital = initial_capital
        self.currency = currency
        self.timestamp = timestamp
        super().__init__()