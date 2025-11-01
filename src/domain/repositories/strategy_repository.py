#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略仓储
"""

from typing import List, Optional, Dict, Any

from .base_repository import BaseRepository
from ..entities import Strategy
from ..value_objects import StrategyId


class StrategyRepository(BaseRepository[Strategy, str]):
    """策略仓储实现"""

    def __init__(self):
        super().__init__(Strategy)
        self._strategies: Dict[str, Strategy] = {}

    async def save(self, strategy: Strategy) -> Strategy:
        """保存策略"""
        strategy_id = str(strategy.strategy_id)
        self._strategies[strategy_id] = strategy
        return strategy

    async def get_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """根据ID获取策略"""
        return self._strategies.get(strategy_id)

    async def get_all(self) -> List[Strategy]:
        """获取所有策略"""
        return list(self._strategies.values())

    async def delete(self, strategy_id: str) -> bool:
        """删除策略"""
        if strategy_id in self._strategies:
            del self._strategies[strategy_id]
            return True
        return False

    async def exists(self, strategy_id: str) -> bool:
        """检查策略是否存在"""
        return strategy_id in self._strategies

    async def find_by_status(self, status) -> List[Strategy]:
        """根据状态查找策略"""
        from ..entities.strategy import StrategyStatus
        return [strategy for strategy in self._strategies.values()
                if strategy.status == status]