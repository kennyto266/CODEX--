"""
交易模块

提供统一的交易接口和模拟交易功能
"""

from .base_trading_api import (
    Order, OrderType, OrderSide, OrderStatus,
    Position, AccountInfo, MarketData, BaseTradingAPI
)

from .realtime_execution_engine import (
    TradeSignal, ExecutionStrategy, ExecutionReport, RiskManager
)

from .futu_trading_api import FutuTradingAPI, create_futu_trading_api

from .paper_trading_engine import PaperTradingEngine

from .paper_trading_risk_manager import (
    PaperTradingRiskManager,
    RiskLimits,
    create_risk_manager
)

from .futu_paper_trading_controller import (
    FutuPaperTradingController,
    TradingControllerConfig,
    create_paper_trading_controller
)

__all__ = [
    # 基础类
    'Order', 'OrderType', 'OrderSide', 'OrderStatus',
    'Position', 'AccountInfo', 'MarketData', 'BaseTradingAPI',

    # 执行引擎
    'TradeSignal', 'ExecutionStrategy', 'ExecutionReport', 'RiskManager',

    # 富途API
    'FutuTradingAPI', 'create_futu_trading_api',

    # 模拟交易
    'PaperTradingEngine',
    'PaperTradingRiskManager', 'RiskLimits', 'create_risk_manager',
    'FutuPaperTradingController', 'TradingControllerConfig',
    'create_paper_trading_controller'
]
