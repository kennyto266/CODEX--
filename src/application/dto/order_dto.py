#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单DTO
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="订单方向 (buy/sell)")
    order_type: str = Field(..., description="订单类型 (market/limit)")
    quantity: int = Field(..., gt=0, description="数量")
    price: Optional[float] = Field(None, gt=0, description="价格（限价单必填）")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "0700.HK",
                "side": "buy",
                "order_type": "limit",
                "quantity": 1000,
                "price": 350.50
            }
        }


class OrderDTO(BaseModel):
    """订单DTO"""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: int
    price: Optional[float]
    status: str
    filled_quantity: int
    filled_price: Optional[float]
    created_at: str
    updated_at: str

    class Config:
        schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "symbol": "0700.HK",
                "side": "buy",
                "order_type": "limit",
                "quantity": 1000,
                "price": 350.50,
                "status": "submitted",
                "filled_quantity": 0,
                "filled_price": None,
                "created_at": "2025-11-01 10:00:00",
                "updated_at": "2025-11-01 10:00:00"
            }
        }


class OrderResponse(BaseModel):
    """订单响应"""
    success: bool
    data: Optional[OrderDTO] = None
    error: Optional[str] = None
    message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "order_id": "550e8400-e29b-41d4-a716-446655440000",
                    "symbol": "0700.HK",
                    "side": "buy",
                    "order_type": "limit",
                    "quantity": 1000,
                    "price": 350.50,
                    "status": "submitted",
                    "filled_quantity": 0,
                    "filled_price": None,
                    "created_at": "2025-11-01 10:00:00",
                    "updated_at": "2025-11-01 10:00:00"
                },
                "error": None,
                "message": None
            }
        }


class OrderListResponse(BaseModel):
    """订单列表响应"""
    success: bool
    data: list[OrderDTO] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "order_id": "550e8400-e29b-41d4-a716-446655440000",
                        "symbol": "0700.HK",
                        "side": "buy",
                        "status": "submitted"
                    }
                ],
                "error": None
            }
        }