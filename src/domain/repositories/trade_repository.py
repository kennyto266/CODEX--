#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易仓储
"""

from typing import List, Optional, Dict, Any
import json
import os

from .base_repository import BaseRepository
from ..entities import Trade
from ..value_objects import Money, Timestamp, Quantity
from ..events import DomainEvent


class TradeRepository(BaseRepository[Trade, str]):
    """交易仓储实现"""

    def __init__(self):
        super().__init__(Trade)
        self._trades: Dict[str, Trade] = {}
        self._storage_file = "data/trades.json"

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self._storage_file), exist_ok=True)

        # 从文件加载数据
        self._load_from_file()

    async def save(self, trade: Trade) -> Trade:
        """保存交易"""
        trade_id = trade.trade_id
        self._trades[trade_id] = trade

        # 保存到文件
        await self._save_to_file()

        # 获取并发布领域事件
        events = trade.get_domain_events()
        for event in events:
            # 这里应该发布事件到事件总线
            pass
        trade.clear_domain_events()

        return trade

    async def get_by_id(self, trade_id: str) -> Optional[Trade]:
        """根据ID获取交易"""
        return self._trades.get(trade_id)

    async def get_all(self) -> List[Trade]:
        """获取所有交易"""
        return list(self._trades.values())

    async def delete(self, trade_id: str) -> bool:
        """删除交易"""
        if trade_id in self._trades:
            del self._trades[trade_id]
            await self._save_to_file()
            return True
        return False

    async def exists(self, trade_id: str) -> bool:
        """检查交易是否存在"""
        return trade_id in self._trades

    def _serialize_trade(self, trade: Trade) -> Dict[str, Any]:
        """序列化交易"""
        return {
            'trade_id': trade.trade_id,
            'order_id': str(trade.order_id),
            'symbol': str(trade.symbol),
            'side': trade.side.value,
            'quantity': trade.quantity.value,
            'price': trade.price.value,
            'commission': trade.commission.value,
            'trade_time': trade.trade_time.to_string(),
            'status': trade.status.value
        }

    def _deserialize_trade(self, data: Dict[str, Any]) -> Trade:
        """反序列化交易"""
        from ..value_objects import OrderId, StockSymbol, Price
        from ..value_objects import OrderSide, Quantity
        from ..entities.trade import TradeStatus

        trade = Trade(
            trade_id=data['trade_id'],
            order_id=OrderId.from_string(data['order_id']),
            symbol=StockSymbol(data['symbol']),
            side=OrderSide(data['side']),
            quantity=Quantity.from_int(data['quantity']),
            price=Price.from_float(data['price']),
            commission=Money.from_float(data['commission']),
            trade_time=Timestamp.from_string(data['trade_time']),
            status=TradeStatus(data['status'])
        )

        return trade

    async def _save_to_file(self):
        """保存到文件"""
        try:
            trades_data = [self._serialize_trade(trade) for trade in self._trades.values()]
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(trades_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存交易数据失败: {e}")

    def _load_from_file(self):
        """从文件加载"""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    trades_data = json.load(f)

                for trade_data in trades_data:
                    try:
                        trade = self._deserialize_trade(trade_data)
                        self._trades[trade.trade_id] = trade
                    except Exception as e:
                        print(f"加载交易失败: {e}")
        except Exception as e:
            print(f"加载交易数据失败: {e}")