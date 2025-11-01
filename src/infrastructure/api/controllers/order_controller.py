#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单API控制器
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ...application.services import OrderApplicationService
from ...application.dto import (
    CreateOrderRequest, OrderResponse, OrderListResponse
)


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    order_service: OrderApplicationService = Depends()
):
    """创建新订单"""
    response = await order_service.create_order(request)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )

    return response


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    order_service: OrderApplicationService = Depends()
):
    """获取所有订单"""
    response = await order_service.get_all_orders(symbol, status)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error
        )

    return OrderListResponse(success=True, data=response.data)


@router.get("/pending", response_model=OrderListResponse)
async def get_pending_orders(
    order_service: OrderApplicationService = Depends()
):
    """获取待处理订单"""
    response = await order_service.get_pending_orders()

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error
        )

    return OrderListResponse(success=True, data=response.data)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    order_service: OrderApplicationService = Depends()
):
    """获取订单详情"""
    response = await order_service.get_order(order_id)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    order_service: OrderApplicationService = Depends()
):
    """取消订单"""
    response = await order_service.cancel_order(order_id)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )

    return response


@router.post("/{order_id}/execute", response_model=OrderResponse)
async def execute_order(
    order_id: str,
    trade_quantity: int,
    trade_price: float,
    order_service: OrderApplicationService = Depends()
):
    """执行订单"""
    response = await order_service.execute_order(order_id, trade_quantity, trade_price)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )

    return response