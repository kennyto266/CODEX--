#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易DTO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TradeDTO(BaseModel):
    """交易DTO"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    trade_time: str
    status: str

    class Config:
        schema_extra = {
            "example": {
                "trade_id": "trade_001",
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "symbol": "0700.HK",
                "side": "buy",
                "quantity": 1000,
                "price": 350.50,
                "commission": 350.50,
                "trade_time": "2025-11-01 10:00:00",
                "status": "filled"
            }
        }


class TradeResponse(BaseModel):
    """交易响应"""
    success: bool
    data: Optional[TradeDTO] = None
    error: Optional[str] = None
    message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "trade_id": "trade_001",
                    "symbol": "0700.HK",
                    "quantity": 1000,
                    "price": 350.50
                },
                "error": None,
                "message": None
            }
        }


class TradeListResponse(BaseModel):
    """交易列表响应"""
    success: bool
    data: List[TradeDTO] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "trade_id": "trade_001",
                        "symbol": "0700.HK",
                        "quantity": 1000,
                        "price": 350.50
                    }
                ],
                "error": None
            }
        }


class TradeStatisticsDTO(BaseModel):
    """交易统计DTO"""
    total_trades: int
    total_volume: int
    total_value: float
    average_price: float
    buy_trades: int
    sell_trades: int

    class Config:
        schema_extra = {
            "example": {
                "total_trades": 100,
                "total_volume": 50000,
                "total_value": 17500000.0,
                "average_price": 350.0,
                "buy_trades": 60,
                "sell_trades": 40
            }
        }