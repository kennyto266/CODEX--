#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合DTO
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CreatePortfolioRequest(BaseModel):
    """创建投资组合请求"""
    name: str = Field(..., description="投资组合名称")
    portfolio_type: str = Field(default="long_only", description="投资组合类型")
    initial_capital: float = Field(..., gt=0, description="初始资金")
    currency: str = Field(default="HKD", description="货币")

    class Config:
        schema_extra = {
            "example": {
                "name": "我的投资组合",
                "portfolio_type": "long_only",
                "initial_capital": 1000000.0,
                "currency": "HKD"
            }
        }


class PortfolioDTO(BaseModel):
    """投资组合DTO"""
    name: str
    portfolio_type: str
    initial_capital: float
    cash: float
    total_value: float
    realized_pnl: float
    unrealized_pnl: float
    total_return: float
    number_of_positions: int
    number_of_strategies: int
    cash_percentage: float
    leverage_ratio: float
    created_at: str
    updated_at: str

    class Config:
        schema_extra = {
            "example": {
                "name": "我的投资组合",
                "portfolio_type": "long_only",
                "initial_capital": 1000000.0,
                "cash": 500000.0,
                "total_value": 1050000.0,
                "realized_pnl": 10000.0,
                "unrealized_pnl": 40000.0,
                "total_return": 50000.0,
                "number_of_positions": 5,
                "number_of_strategies": 2,
                "cash_percentage": 47.6,
                "leverage_ratio": 0.524,
                "created_at": "2025-11-01 10:00:00",
                "updated_at": "2025-11-01 10:00:00"
            }
        }


class PositionDTO(BaseModel):
    """仓位DTO"""
    symbol: str
    quantity: int
    avg_price: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    position_type: str

    class Config:
        schema_extra = {
            "example": {
                "symbol": "0700.HK",
                "quantity": 1000,
                "avg_price": 350.50,
                "market_price": 355.00,
                "market_value": 355000.0,
                "unrealized_pnl": 4500.0,
                "position_type": "long"
            }
        }


class PortfolioDetailDTO(PortfolioDTO):
    """投资组合详细信息DTO"""
    detailed_positions: List[PositionDTO] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "name": "我的投资组合",
                "detailed_positions": [
                    {
                        "symbol": "0700.HK",
                        "quantity": 1000,
                        "avg_price": 350.50,
                        "market_price": 355.00,
                        "market_value": 355000.0,
                        "unrealized_pnl": 4500.0,
                        "position_type": "long"
                    }
                ]
            }
        }


class PortfolioResponse(BaseModel):
    """投资组合响应"""
    success: bool
    data: Optional[PortfolioDTO] = None
    error: Optional[str] = None
    message: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "name": "我的投资组合",
                    "total_value": 1050000.0
                },
                "error": None,
                "message": None
            }
        }


class PortfolioListResponse(BaseModel):
    """投资组合列表响应"""
    success: bool
    data: List[PortfolioDTO] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "name": "我的投资组合",
                        "total_value": 1050000.0
                    }
                ],
                "error": None
            }
        }