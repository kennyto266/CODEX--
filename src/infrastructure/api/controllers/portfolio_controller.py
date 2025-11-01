#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合API控制器
"""

from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ...application.services import PortfolioApplicationService
from ...application.dto import (
    CreatePortfolioRequest, PortfolioResponse, PortfolioListResponse
)


router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    request: CreatePortfolioRequest,
    portfolio_service: PortfolioApplicationService = Depends()
):
    """创建新投资组合"""
    response = await portfolio_service.create_portfolio(request)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )

    return response


@router.get("/", response_model=PortfolioListResponse)
async def get_all_portfolios(
    portfolio_service: PortfolioApplicationService = Depends()
):
    """获取所有投资组合"""
    response = await portfolio_service.get_all_portfolios()

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error
        )

    return PortfolioListResponse(success=True, data=response.data)


@router.get("/{name}", response_model=PortfolioResponse)
async def get_portfolio(
    name: str,
    portfolio_service: PortfolioApplicationService = Depends()
):
    """获取投资组合详情"""
    response = await portfolio_service.get_portfolio(name)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.get("/{name}/summary", response_model=PortfolioResponse)
async def get_portfolio_summary(
    name: str,
    portfolio_service: PortfolioApplicationService = Depends()
):
    """获取投资组合摘要"""
    response = await portfolio_service.get_portfolio_summary(name)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.get("/{name}/risk", response_model=PortfolioResponse)
async def assess_portfolio_risk(
    name: str,
    portfolio_service: PortfolioApplicationService = Depends()
):
    """评估投资组合风险"""
    response = await portfolio_service.assess_portfolio_risk(name)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.error
        )

    return response


@router.post("/{name}/rebalance", response_model=PortfolioResponse)
async def rebalance_portfolio(
    name: str,
    target_allocations: Dict[str, float],
    portfolio_service: PortfolioApplicationService = Depends()
):
    """重新平衡投资组合"""
    response = await portfolio_service.rebalance_portfolio(name, target_allocations)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error
        )

    return response