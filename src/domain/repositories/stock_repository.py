#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票仓储
"""

from typing import List, Optional, Dict, Any

from .base_repository import BaseRepository
from ..entities import Stock
from ..value_objects import StockSymbol


class StockRepository(BaseRepository[Stock, str]):
    """股票仓储实现"""

    def __init__(self):
        super().__init__(Stock)
        self._stocks: Dict[str, Stock] = {}

    async def save(self, stock: Stock) -> Stock:
        """保存股票"""
        symbol = str(stock.symbol)
        self._stocks[symbol] = stock
        return stock

    async def get_by_id(self, symbol: str) -> Optional[Stock]:
        """根据股票代码获取股票"""
        return self._stocks.get(symbol)

    async def get_all(self) -> List[Stock]:
        """获取所有股票"""
        return list(self._stocks.values())

    async def delete(self, symbol: str) -> bool:
        """删除股票"""
        if symbol in self._stocks:
            del self._stocks[symbol]
            return True
        return False

    async def exists(self, symbol: str) -> bool:
        """检查股票是否存在"""
        return symbol in self._stocks

    async def find_by_market(self, market: str) -> List[Stock]:
        """根据市场查找股票"""
        return [stock for stock in self._stocks.values()
                if stock.market == market]