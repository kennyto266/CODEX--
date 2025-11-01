#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用程序主入口
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .controllers import (
    OrderController, PortfolioController, TradingController
)
from ...domain.events import EventBus
from ...domain.services import (
    TradingService, RiskManagementService,
    PortfolioService, MarketDataService
)
from ...domain.repositories import (
    OrderRepository, PortfolioRepository,
    TradeRepository
)
from ...application.services import (
    OrderApplicationService, PortfolioApplicationService,
    TradingApplicationService
)


def create_app() -> FastAPI:
    """创建FastAPI应用程序"""

    # 创建FastAPI应用
    app = FastAPI(
        title="CODEX Trading System API",
        description="基于领域驱动设计的量化交易系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 初始化事件系统
    event_bus = EventBus()

    # 初始化仓储
    order_repository = OrderRepository()
    portfolio_repository = PortfolioRepository()
    trade_repository = TradeRepository()

    # 初始化领域服务
    trading_service = TradingService(event_bus)
    risk_service = RiskManagementService(event_bus)
    portfolio_service = PortfolioService(event_bus)
    market_data_service = MarketDataService(event_bus)

    # 启动事件总线
    @app.on_event("startup")
    async def startup_event():
        await event_bus.start()
        await market_data_service.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        await market_data_service.stop()
        await event_bus.stop()

    # 注册控制器
    app.include_router(OrderController.router)
    app.include_router(PortfolioController.router)
    app.include_router(TradingController.router)

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "内部服务器错误",
                "detail": str(exc)
            }
        )

    # 根路径
    @app.get("/")
    async def root():
        return {
            "message": "欢迎使用CODEX Trading System API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "codex-trading-api",
            "version": "1.0.0"
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )