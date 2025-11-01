#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API依赖注入
"""

from typing import AsyncGenerator
from ...application.services import (
    OrderApplicationService, PortfolioApplicationService, TradingApplicationService
)
from ...domain.services import (
    TradingService, RiskManagementService, PortfolioService, MarketDataService
)
from ...domain.repositories import (
    OrderRepository, PortfolioRepository, TradeRepository
)
from ...domain.events import EventBus


# 领域层依赖
async def get_event_bus() -> EventBus:
    """获取事件总线"""
    event_bus = EventBus()
    await event_bus.start()
    return event_bus


async def get_order_repository() -> OrderRepository:
    """获取订单仓储"""
    return OrderRepository()


async def get_portfolio_repository() -> PortfolioRepository:
    """获取投资组合仓储"""
    return PortfolioRepository()


async def get_trade_repository() -> TradeRepository:
    """获取交易仓储"""
    return TradeRepository()


# 领域服务依赖
async def get_trading_service(event_bus: EventBus = Depends(get_event_bus)) -> TradingService:
    """获取交易服务"""
    return TradingService(event_bus)


async def get_risk_service(event_bus: EventBus = Depends(get_event_bus)) -> RiskManagementService:
    """获取风险管理服务"""
    return RiskManagementService(event_bus)


async def get_portfolio_service(event_bus: EventBus = Depends(get_event_bus)) -> PortfolioService:
    """获取投资组合服务"""
    return PortfolioService(event_bus)


async def get_market_data_service(event_bus: EventBus = Depends(get_event_bus)) -> MarketDataService:
    """获取市场数据服务"""
    service = MarketDataService(event_bus)
    await service.start()
    return service


# 应用服务依赖
async def get_order_app_service(
    trading_service: TradingService = Depends(get_trading_service),
    order_repository: OrderRepository = Depends(get_order_repository)
) -> OrderApplicationService:
    """获取订单应用服务"""
    return OrderApplicationService(trading_service, order_repository)


async def get_portfolio_app_service(
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    risk_service: RiskManagementService = Depends(get_risk_service),
    portfolio_repository: PortfolioRepository = Depends(get_portfolio_repository)
) -> PortfolioApplicationService:
    """获取投资组合应用服务"""
    return PortfolioApplicationService(portfolio_service, risk_service, portfolio_repository)


async def get_trading_app_service(
    trading_service: TradingService = Depends(get_trading_service),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    trade_repository: TradeRepository = Depends(get_trade_repository)
) -> TradingApplicationService:
    """获取交易应用服务"""
    return TradingApplicationService(trading_service, market_data_service, trade_repository)