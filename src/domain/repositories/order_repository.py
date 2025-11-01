#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单仓储
"""

from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from .base_repository import BaseRepository
from ..entities import Order
from ..value_objects import OrderId, StockSymbol
from ..events import DomainEvent


class OrderRepository(BaseRepository[Order, str]):
    """订单仓储实现"""

    def __init__(self):
        super().__init__(Order)
        self._orders: Dict[str, Order] = {}
        self._storage_file = "data/orders.json"

        # 确保数据目录存在
        os.makedirs(os.path.dirname(self._storage_file), exist_ok=True)

        # 从文件加载数据
        self._load_from_file()

    async def save(self, order: Order) -> Order:
        """保存订单"""
        order_id = str(order.order_id)
        self._orders[order_id] = order

        # 保存到文件
        await self._save_to_file()

        # 获取并发布领域事件
        events = order.get_domain_events()
        for event in events:
            # 这里应该发布事件到事件总线
            pass
        order.clear_domain_events()

        return order

    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        return self._orders.get(order_id)

    async def get_all(self) -> List[Order]:
        """获取所有订单"""
        return list(self._orders.values())

    async def delete(self, order_id: str) -> bool:
        """删除订单"""
        if order_id in self._orders:
            del self._orders[order_id]
            await self._save_to_file()
            return True
        return False

    async def exists(self, order_id: str) -> bool:
        """检查订单是否存在"""
        return order_id in self._orders

    async def find_by_symbol(self, symbol: StockSymbol) -> List[Order]:
        """根据股票代码查找订单"""
        return [order for order in self._orders.values() if order.symbol == symbol]

    async def find_by_status(self, status) -> List[Order]:
        """根据状态查找订单"""
        return [order for order in self._orders.values() if order.status == status]

    async def find_pending_orders(self) -> List[Order]:
        """查找待处理订单"""
        from ..entities.order import OrderStatus
        return [order for order in self._orders.values()
                if order.is_active()]

    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """根据日期范围查找订单"""
        return [order for order in self._orders.values()
                if start_date <= order.created_at.value <= end_date]

    def _serialize_order(self, order: Order) -> Dict[str, Any]:
        """序列化订单"""
        return {
            'order_id': str(order.order_id),
            'symbol': str(order.symbol),
            'side': order.side.value,
            'order_type': order.order_type.value,
            'quantity': order.quantity.value,
            'price': order.price.value if order.price else None,
            'status': order.status.value,
            'filled_quantity': order.filled_quantity,
            'created_at': order.created_at.to_string(),
            'updated_at': order.updated_at.to_string()
        }

    def _deserialize_order(self, data: Dict[str, Any]) -> Order:
        """反序列化订单"""
        from ..value_objects import Quantity, Price, Timestamp
        from ..value_objects import OrderType, OrderSide
        from ..entities.order import OrderStatus

        order = Order(
            order_id=OrderId.from_string(data['order_id']),
            symbol=StockSymbol(data['symbol']),
            side=OrderSide(data['side']),
            order_type=OrderType(data['order_type']),
            quantity=Quantity.from_int(data['quantity']),
            status=OrderStatus(data['status']),
            filled_quantity=data['filled_quantity'],
            created_at=Timestamp.from_string(data['created_at']),
            updated_at=Timestamp.from_string(data['updated_at'])
        )

        if data['price']:
            order.price = Price.from_float(data['price'])

        return order

    async def _save_to_file(self):
        """保存到文件"""
        try:
            orders_data = [self._serialize_order(order) for order in self._orders.values()]
            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(orders_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存订单数据失败: {e}")

    def _load_from_file(self):
        """从文件加载"""
        try:
            if os.path.exists(self._storage_file):
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)

                for order_data in orders_data:
                    try:
                        order = self._deserialize_order(order_data)
                        self._orders[str(order.order_id)] = order
                    except Exception as e:
                        print(f"加载订单失败: {e}")
        except Exception as e:
            print(f"加载订单数据失败: {e}")