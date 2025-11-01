#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓位仓储
"""

from typing import List, Optional, Dict, Any

from .base_repository import BaseRepository
from ..entities import Position


class PositionRepository(BaseRepository[Position, str]):
    """仓位仓储实现"""

    def __init__(self):
        super().__init__(Position)
        self._positions: Dict[str, Position] = {}

    async def save(self, position: Position) -> Position:
        """保存仓位"""
        symbol = str(position.symbol)
        self._positions[symbol] = position
        return position

    async def get_by_id(self, symbol: str) -> Optional[Position]:
        """根据股票代码获取仓位"""
        return self._positions.get(symbol)

    async def get_all(self) -> List[Position]:
        """获取所有仓位"""
        return list(self._positions.values())

    async def delete(self, symbol: str) -> bool:
        """删除仓位"""
        if symbol in self._positions:
            del self._positions[symbol]
            return True
        return False

    async def exists(self, symbol: str) -> bool:
        """检查仓位是否存在"""
        return symbol in self._positions