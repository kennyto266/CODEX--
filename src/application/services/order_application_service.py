#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单应用服务
处理订单相关的用例和协调
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.entities import Order
from ...domain.value_objects import (
    OrderId, StockSymbol, Price, Quantity,
    OrderType, OrderSide, Timestamp
)
from ...domain.services import TradingService
from ...domain.repositories import OrderRepository
from ...application.dto import (
    OrderCreateDTO, OrderDTO, OrderResponseDTO,
    CreateOrderRequest, OrderResponse
)
from ...application.mappers import OrderMapper


class OrderApplicationService:
    """订单应用服务"""

    def __init__(self, trading_service: TradingService, order_repository: OrderRepository):
        """初始化订单应用服务"""
        self.trading_service = trading_service
        self.order_repository = order_repository

    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        """创建订单"""
        try:
            # 验证输入
            if not request.symbol:
                return OrderResponse(
                    success=False,
                    error="股票代码不能为空"
                )

            if request.quantity <= 0:
                return OrderResponse(
                    success=False,
                    error="数量必须大于零"
                )

            # 转换请求为领域对象
            symbol = StockSymbol(request.symbol)
            side = OrderSide(request.side)
            order_type = OrderType(request.order_type)
            quantity = Quantity.from_int(request.quantity)

            price = None
            if request.price and request.price > 0:
                price = Price.from_float(request.price)

            # 提交订单
            order = await self.trading_service.submit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                price=price
            )

            # 转换为响应DTO
            order_dto = OrderMapper.to_dto(order)
            return OrderResponse(
                success=True,
                data=order_dto
            )

        except ValueError as e:
            return OrderResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"创建订单失败: {str(e)}"
            )

    async def cancel_order(self, order_id: str) -> OrderResponse:
        """取消订单"""
        try:
            order_id_obj = OrderId.from_string(order_id)
            success = await self.trading_service.cancel_order(order_id_obj, "用户取消")

            if success:
                return OrderResponse(
                    success=True,
                    message="订单已取消"
                )
            else:
                return OrderResponse(
                    success=False,
                    error="取消订单失败"
                )

        except ValueError as e:
            return OrderResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"取消订单失败: {str(e)}"
            )

    async def get_order(self, order_id: str) -> OrderResponse:
        """获取订单"""
        try:
            order = self.order_repository.get_by_id(order_id)
            if not order:
                return OrderResponse(
                    success=False,
                    error="订单不存在"
                )

            order_dto = OrderMapper.to_dto(order)
            return OrderResponse(
                success=True,
                data=order_dto
            )

        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"获取订单失败: {str(e)}"
            )

    async def get_all_orders(self, symbol: Optional[str] = None,
                           status: Optional[str] = None) -> OrderResponse:
        """获取所有订单"""
        try:
            orders = await self.order_repository.get_all()

            # 应用过滤
            if symbol:
                symbol_obj = StockSymbol(symbol)
                orders = await self.order_repository.find_by_symbol(symbol_obj)

            if status:
                from ...domain.entities.order import OrderStatus
                status_enum = OrderStatus(status)
                orders = await self.order_repository.find_by_status(status_enum)

            # 转换为DTO列表
            order_dtos = [OrderMapper.to_dto(order) for order in orders]
            return OrderResponse(
                success=True,
                data=order_dtos
            )

        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"获取订单列表失败: {str(e)}"
            )

    async def get_pending_orders(self) -> OrderResponse:
        """获取待处理订单"""
        try:
            orders = await self.order_repository.find_pending_orders()
            order_dtos = [OrderMapper.to_dto(order) for order in orders]
            return OrderResponse(
                success=True,
                data=order_dtos
            )

        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"获取待处理订单失败: {str(e)}"
            )

    async def execute_order(self, order_id: str, trade_quantity: int,
                          trade_price: float) -> OrderResponse:
        """执行订单（模拟交易）"""
        try:
            order_id_obj = OrderId.from_string(order_id)
            trade_price_obj = Price.from_float(trade_price)

            trade = await self.trading_service.execute_trade(
                order_id=order_id_obj,
                trade_quantity=trade_quantity,
                trade_price=trade_price_obj
            )

            if trade:
                return OrderResponse(
                    success=True,
                    message=f"交易执行成功: {trade.trade_id}"
                )
            else:
                return OrderResponse(
                    success=False,
                    error="交易执行失败"
                )

        except ValueError as e:
            return OrderResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return OrderResponse(
                success=False,
                error=f"执行订单失败: {str(e)}"
            )