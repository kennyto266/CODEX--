#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单映射器
"""

from typing import Optional
from ...application.dto import OrderDTO
from ...domain.entities import Order


class OrderMapper:
    """订单映射器"""

    @staticmethod
    def to_dto(order: Order) -> OrderDTO:
        """将订单实体转换为DTO"""
        return OrderDTO(
            order_id=str(order.order_id),
            symbol=str(order.symbol),
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=order.quantity.value,
            price=order.price.value if order.price else None,
            status=order.status.value,
            filled_quantity=order.filled_quantity,
            filled_price=order.filled_price.value if order.filled_price else None,
            created_at=order.created_at.to_string(),
            updated_at=order.updated_at.to_string()
        )

    @staticmethod
    def from_dto(order_dto: OrderDTO) -> Order:
        """将DTO转换为订单实体"""
        from ...domain.value_objects import (
            OrderId, StockSymbol, Quantity, Price, OrderType, OrderSide
        )
        from ...domain.entities.order import OrderStatus
        from ...domain.value_objects import Timestamp

        return Order(
            order_id=OrderId.from_string(order_dto.order_id),
            symbol=StockSymbol(order_dto.symbol),
            side=OrderSide(order_dto.side),
            order_type=OrderType(order_dto.order_type),
            quantity=Quantity.from_int(order_dto.quantity),
            price=Price.from_float(order_dto.price) if order_dto.price else None,
            status=OrderStatus(order_dto.status),
            filled_quantity=order_dto.filled_quantity,
            filled_price=Price.from_float(order_dto.filled_price) if order_dto.filled_price else None,
            created_at=Timestamp.from_string(order_dto.created_at),
            updated_at=Timestamp.from_string(order_dto.updated_at)
        )