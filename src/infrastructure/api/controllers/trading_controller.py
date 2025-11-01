#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易API控制器
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from ...application.services import TradingApplicationService
from ...application.dto import (
    TradeResponse, TradeListResponse, TradeStatisticsDTO
)


router = APIRouter(prefix="/trading", tags=["trading"])


@router.get("/trades", response_model=TradeListResponse)
async def get_all_trades(
    symbol: Optional[str] = Query(None, description="股票代码"),
    trading_service: TradingApplicationService = Depends()
):
    """获取所有交易"""
    response = await trading_service.get_all_trades(symbol)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error
        )

    return TradeListResponse(success=True, data=response.data)


@router.get("/statistics", response_model=TradeResponse)
async def get_trade_statistics(
    trading_service: TradingApplicationService = Depends()
):
    """获取交易统计"""
    response = await trading_service.get_trade_statistics()

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error
        )

    return response


@router.get("/market-data/{symbol}", response_model=TradeResponse)
async def get_market_data(
    symbol: str,
    trading_service: TradingApplicationService = Depends()
):
    """获取市场数据"""
    response = await trading_service.get_market_data(symbol)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.get("/historical/{symbol}", response_model=TradeResponse)
async def get_historical_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="历史数据天数"),
    trading_service: TradingApplicationService = Depends()
):
    """获取历史数据"""
    response = await trading_service.get_historical_data(symbol, days)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "trading-api",
        "version": "1.0.0"
    }