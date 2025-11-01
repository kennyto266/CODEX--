#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合仓储
"""

from typing import List, Optional, Dict, Any
import json
import os

from .base_repository import BaseRepository
from ..entities import Portfolio
from ..value_objects import Money, Timestamp
from ..events import DomainEvent


class PortfolioRepository(BaseRepository[Portfolio, str]):
    """投资组合仓储实现"""

    def __init__(self):
        super().__init__(Portfolio)
        self._portfolios: Dict[str, Portfolio] = {}
        self._storage_file = "data/portfolios.json"

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self._storage_file), exist_ok=True)

        # 从文件加载数据
        self._load_from_file()

    async def save(self, portfolio: Portfolio) -> Portfolio:
        """保存投资组合"""
        portfolio_name = portfolio.name
        self._portfolios[portfolio_name] = portfolio

        # 保存到文件
        await self._save_to_file()

        # 获取并发布领域事件
        events = portfolio.get_domain_events()
        for event in events:
            # 这里应该发布事件到事件总线
            pass
        portfolio.clear_domain_events()

        return portfolio

    async def get_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        """根据ID获取投资组合"""
        return self._portfolios.get(portfolio_id)

    async def get_all(self) -> List[Portfolio]:
        """获取所有投资组合"""
        return list(self._portfolios.values())

    async def delete(self, portfolio_id: str) -> bool:
        """删除投资组合"""
        if portfolio_id in self._portfolios:
            del self._portfolios[portfolio_id]
            await self._save_to_file()
            return True
        return False

    async def exists(self, portfolio_id: str) -> bool:
        """检查投资组合是否存在"""
        return portfolio_id in self._portfolios

    async def find_by_type(self, portfolio_type) -> List[Portfolio]:
        """根据类型查找投资组合"""
        return [portfolio for portfolio in self._portfolios.values()
                if portfolio.portfolio_type == portfolio_type]

    async def find_active_portfolios(self) -> List[Portfolio]:
        """查找活跃投资组合"""
        # 这里可以根据具体业务逻辑定义什么是"活跃"
        return [portfolio for portfolio in self._portfolios.values()
                if portfolio.total_value.value > 0]

    def _serialize_portfolio(self, portfolio: Portfolio) -> Dict[str, Any]:
        """序列化投资组合"""
        return {
            'name': portfolio.name,
            'portfolio_type': portfolio.portfolio_type.value,
            'initial_capital': portfolio.initial_capital.value,
            'cash': portfolio.cash.value,
            'total_value': portfolio.total_value.value,
            'realized_pnl': portfolio.realized_pnl.value,
            'unrealized_pnl': portfolio.unrealized_pnl.value,
            'created_at': portfolio.created_at.to_string(),
            'updated_at': portfolio.updated_at.to_string(),
            'positions': {symbol: {
                'quantity': position.quantity.value,
                'avg_price': position.avg_price.value,
                'market_value': position.market_value.value,
                'unrealized_pnl': position.unrealized_pnl.value
            } for symbol, position in portfolio.positions.items()},
            'strategies': {strategy_id: {
                'name': strategy.name,
                'status': strategy.status.value
            } for strategy_id, strategy in portfolio.strategies.items()}
        }

    def _deserialize_portfolio(self, data: Dict[str, Any]) -> Portfolio:
        """反序列化投资组合"""
        from ..entities import Position, Strategy
        from ..value_objects import Quantity, Price
        from ..value_objects import PortfolioType
        from ..entities.strategy import StrategyStatus

        # 创建投资组合
        portfolio = Portfolio(
            name=data['name'],
            portfolio_type=PortfolioType(data['portfolio_type']),
            initial_capital=Money.from_float(data['initial_capital']),
            cash=Money.from_float(data['cash'])
        )

        # 设置其他属性
        portfolio.total_value = Money.from_float(data['total_value'])
        portfolio.realized_pnl = Money.from_float(data['realized_pnl'])
        portfolio.unrealized_pnl = Money.from_float(data['unrealized_pnl'])
        portfolio.created_at = Timestamp.from_string(data['created_at'])
        portfolio.updated_at = Timestamp.from_string(data['updated_at'])

        # 恢复仓位
        for symbol, position_data in data.get('positions', {}).items():
            position = Position(
                symbol=symbol,
                quantity=Quantity.from_int(position_data['quantity']),
                avg_price=Price.from_float(position_data['avg_price']),
                market_value=Money.from_float(position_data['market_value']),
                realized_pnl=Money.from_float(0),  # 默认值
                unrealized_pnl=Money.from_float(position_data['unrealized_pnl'])
            )
            portfolio.positions[symbol] = position

        # 恢复策略
        for strategy_id, strategy_data in data.get('strategies', {}).items():
            strategy = Strategy(
                strategy_id=strategy_id,
                name=strategy_data['name'],
                description="",  # 默认值
                parameters={}  # 默认值
            )
            strategy.status = StrategyStatus(strategy_data['status'])
            portfolio.strategies[strategy_id] = strategy

        return portfolio

    async def _save_to_file(self):
        """保存到文件"""
        try:
            portfolios_data = [self._serialize_portfolio(portfolio)
                             for portfolio in self._portfolios.values()]
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(portfolios_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存投资组合数据失败: {e}")

    def _load_from_file(self):
        """从文件加载"""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    portfolios_data = json.load(f)

                for portfolio_data in portfolios_data:
                    try:
                        portfolio = self._deserialize_portfolio(portfolio_data)
                        self._portfolios[portfolio.name] = portfolio
                    except Exception as e:
                        print(f"加载投资组合失败: {e}")
        except Exception as e:
            print(f"加载投资组合数据失败: {e}")