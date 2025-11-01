#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易系统 API 路由

根据 OpenSpec 提案 enhance-futu-paper-trading 实现
提供完整的模拟交易功能 RESTful API
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field
import asyncio

logger = logging.getLogger(__name__)

# ==================== Data Models ====================

class PaperTradingStatus(BaseModel):
    """模拟交易状态"""
    is_initialized: bool = Field(..., description="是否已初始化")
    is_trading: bool = Field(..., description="是否正在交易")
    trading_enabled: bool = Field(..., description="交易是否启用")
    emergency_stop: bool = Field(..., description="是否紧急停止")
    last_update: str = Field(..., description="最后更新时间")
    total_trades: int = Field(default=0, description="总交易次数")
    daily_trades: int = Field(default=0, description="当日交易次数")


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    symbol: str = Field(..., description="股票代码, 例如: 0700.HK")
    side: str = Field(..., description="交易方向: BUY 或 SELL")
    order_type: str = Field(default="LIMIT", description="订单类型: LIMIT 或 MARKET")
    quantity: int = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格 (限价单必填)")


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="交易方向")
    quantity: int = Field(..., description="数量")
    price: float = Field(..., description="价格")
    filled_quantity: int = Field(default=0, description="已成交数量")
    status: str = Field(..., description="订单状态")
    created_time: str = Field(..., description="创建时间")
    updated_time: str = Field(..., description="更新时间")


class Position(BaseModel):
    """持仓"""
    symbol: str = Field(..., description="股票代码")
    quantity: int = Field(..., description="持仓数量")
    avg_price: float = Field(..., description="平均成本")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    unrealized_pnl_pct: float = Field(..., description="未实现盈亏百分比")


class AccountInfo(BaseModel):
    """账户信息"""
    balance: float = Field(..., description="现金余额")
    equity: float = Field(..., description="总资产")
    available_balance: float = Field(..., description="可用资金")
    market_value: float = Field(..., description="持仓市值")
    total_pnl: float = Field(..., description="总盈亏")
    total_pnl_pct: float = Field(..., description="总盈亏百分比")


class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_return: float = Field(..., description="总收益率 (%)")
    annual_return: float = Field(..., description="年化收益率 (%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤 (%)")
    win_rate: float = Field(..., description="胜率 (%)")
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利交易次数")
    losing_trades: int = Field(..., description="亏损交易次数")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    initial_balance: Optional[Decimal] = Field(None, description="初始资金")
    max_position_size: Optional[Decimal] = Field(None, description="单笔最大仓位")
    max_daily_trades: Optional[int] = Field(None, description="每日最大交易次数")
    trading_enabled: Optional[bool] = Field(None, description="是否启用交易")


# ==================== Global Controller Instance ====================

# 全局模拟交易控制器实例
_paper_controller = None


def get_paper_controller():
    """获取模拟交易控制器实例"""
    global _paper_controller
    if _paper_controller is None:
        try:
            from src.trading.futu_paper_trading_controller import FutuPaperTradingController, TradingControllerConfig
            config_obj = TradingControllerConfig()
            # 转换为字典格式
            config_dict = {
                'trading': {
                    'initial_balance': config_obj.initial_balance,
                    'max_position_size': config_obj.max_position_size,
                    'max_daily_trades': config_obj.max_daily_trades,
                    'trading_enabled': config_obj.trading_enabled,
                    'commission_rate': config_obj.commission_rate,
                    'min_commission': config_obj.min_commission,
                    'emergency_stop': config_obj.emergency_stop
                },
                'futu': {
                    'host': '127.0.0.1',
                    'port': 11111
                },
                'auth': {
                    'user_id': '2860386'
                }
            }
            _paper_controller = FutuPaperTradingController(config_dict)
        except Exception as e:
            logger.error(f"无法初始化模拟交易控制器: {e}")
            raise HTTPException(status_code=503, detail=f"模拟交易服务不可用: {e}")
    return _paper_controller


# ==================== API Routes ====================

router = APIRouter(prefix="/api/paper-trading", tags=["Paper Trading"])


@router.get("/status", response_model=PaperTradingStatus)
async def get_status():
    """
    获取模拟交易状态
    GET /api/paper-trading/status
    """
    try:
        controller = get_paper_controller()
        status = await controller.get_status()

        # 处理嵌套的 stats
        stats = status.get('stats', {})

        return PaperTradingStatus(
            is_initialized=status.get('initialized', False),
            is_trading=status.get('running', False),
            trading_enabled=status.get('trading_enabled', True),
            emergency_stop=status.get('emergency_stop', False),
            last_update=datetime.now().isoformat(),
            total_trades=stats.get('total_trades', 0),
            daily_trades=stats.get('daily_trade_count', 0)
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", response_model=OrderResponse)
async def create_order(order: CreateOrderRequest):
    """
    创建订单
    POST /api/paper-trading/orders
    """
    try:
        controller = get_paper_controller()

        # 检查交易是否启用
        if not controller.config.trading_enabled:
            raise HTTPException(status_code=403, detail="交易已禁用")

        # 创建交易信号
        from src.trading.realtime_execution_engine import TradeSignal
        signal = TradeSignal(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=Decimal(str(order.price)) if order.price else None,
            timestamp=datetime.now(),
            source="manual"
        )

        # 执行信号
        result = await controller.execute_signal(signal)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', '订单创建失败'))

        # 获取订单详情
        orders = await controller.get_orders()
        if orders:
            latest_order = orders[-1]
            return OrderResponse(
                order_id=latest_order.order_id,
                symbol=str(latest_order.symbol),
                side=latest_order.side,
                quantity=latest_order.quantity,
                price=float(latest_order.price),
                filled_quantity=latest_order.filled_quantity,
                status=latest_order.status.value,
                created_time=latest_order.created_time.isoformat(),
                updated_time=datetime.now().isoformat()
            )

        raise HTTPException(status_code=500, detail="订单创建成功但获取失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status_filter: Optional[str] = Query(None, description="订单状态过滤")
):
    """
    获取订单列表
    GET /api/paper-trading/orders
    """
    try:
        controller = get_paper_controller()
        orders = await controller.get_orders()

        result = []
        for order in orders:
            if status_filter and order.status.value != status_filter:
                continue

            result.append(OrderResponse(
                order_id=order.order_id,
                symbol=str(order.symbol),
                side=order.side,
                quantity=order.quantity,
                price=float(order.price),
                filled_quantity=order.filled_quantity,
                status=order.status.value,
                created_time=order.created_time.isoformat(),
                updated_time=datetime.now().isoformat()
            ))

        return result

    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """
    取消订单
    DELETE /api/paper-trading/orders/{order_id}
    """
    try:
        controller = get_paper_controller()
        success = await controller.cancel_order(order_id)

        if not success:
            raise HTTPException(status_code=404, detail="订单不存在或无法取消")

        return {"success": True, "message": "订单已取消"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=List[Position])
async def get_positions():
    """
    获取持仓列表
    GET /api/paper-trading/positions
    """
    try:
        controller = get_paper_controller()
        positions = await controller.get_positions()

        result = []
        for pos in positions:
            result.append(Position(
                symbol=str(pos.symbol),
                quantity=pos.quantity,
                avg_price=float(pos.avg_price),
                current_price=float(pos.current_price),
                market_value=float(pos.market_value),
                unrealized_pnl=float(pos.unrealized_pnl),
                unrealized_pnl_pct=float(pos.unrealized_pnl_pct)
            ))

        return result

    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account", response_model=AccountInfo)
async def get_account_info():
    """
    获取账户信息
    GET /api/paper-trading/account
    """
    try:
        controller = get_paper_controller()
        account = await controller.get_account_info()

        return AccountInfo(
            balance=float(account.get('balance', 0)),
            equity=float(account.get('equity', 0)),
            available_balance=float(account.get('available_balance', 0)),
            market_value=float(account.get('market_value', 0)),
            total_pnl=float(account.get('total_pnl', 0)),
            total_pnl_pct=float(account.get('total_pnl_pct', 0))
        )

    except Exception as e:
        logger.error(f"获取账户信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """
    获取性能指标
    GET /api/paper-trading/performance
    """
    try:
        controller = get_paper_controller()
        metrics = await controller.get_performance_metrics()

        return PerformanceMetrics(
            total_return=float(metrics.get('total_return', 0)),
            annual_return=float(metrics.get('annual_return', 0)),
            sharpe_ratio=float(metrics.get('sharpe_ratio', 0)),
            max_drawdown=float(metrics.get('max_drawdown', 0)),
            win_rate=float(metrics.get('win_rate', 0)),
            total_trades=int(metrics.get('total_trades', 0)),
            winning_trades=int(metrics.get('winning_trades', 0)),
            losing_trades=int(metrics.get('losing_trades', 0))
        )

    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """
    获取交易配置
    GET /api/paper-trading/config
    """
    try:
        controller = get_paper_controller()
        config = controller.config

        return {
            "initial_balance": float(config.initial_balance),
            "max_position_size": float(config.max_position_size),
            "max_daily_trades": config.max_daily_trades,
            "trading_enabled": config.trading_enabled,
            "commission_rate": float(config.commission_rate),
            "min_commission": float(config.min_commission)
        }

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(config: ConfigUpdateRequest):
    """
    更新交易配置
    PUT /api/paper-trading/config
    """
    try:
        controller = get_paper_controller()

        # 更新配置
        if config.initial_balance is not None:
            controller.config.initial_balance = config.initial_balance

        if config.max_position_size is not None:
            controller.config.max_position_size = config.max_position_size

        if config.max_daily_trades is not None:
            controller.config.max_daily_trades = config.max_daily_trades

        if config.trading_enabled is not None:
            controller.config.trading_enabled = config.trading_enabled

        return {"success": True, "message": "配置已更新"}

    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop():
    """
    紧急停止所有交易
    POST /api/paper-trading/emergency-stop
    """
    try:
        controller = get_paper_controller()
        success = await controller.emergency_stop()

        if not success:
            raise HTTPException(status_code=500, detail="紧急停止失败")

        return {"success": True, "message": "已启动紧急停止"}

    except Exception as e:
        logger.error(f"紧急停止失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unlock")
async def unlock_trading():
    """
    解锁交易功能
    POST /api/paper-trading/unlock
    """
    try:
        controller = get_paper_controller()
        success = await controller.unlock_trading()

        if not success:
            raise HTTPException(status_code=500, detail="解锁失败")

        return {"success": True, "message": "交易功能已解锁"}

    except Exception as e:
        logger.error(f"解锁交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_account(balance: Optional[float] = Body(None, description="新初始资金")):
    """
    重置模拟账户
    POST /api/paper-trading/reset
    """
    try:
        controller = get_paper_controller()
        new_balance = Decimal(str(balance)) if balance else None
        success = await controller.reset_account(new_balance)

        if not success:
            raise HTTPException(status_code=500, detail="重置账户失败")

        return {
            "success": True,
            "message": "账户已重置",
            "initial_balance": float(new_balance) if new_balance else float(controller.config.initial_balance)
        }

    except Exception as e:
        logger.error(f"重置账户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize():
    """
    初始化模拟交易系统
    POST /api/paper-trading/initialize
    """
    try:
        controller = get_paper_controller()
        success = await controller.initialize()

        if not success:
            raise HTTPException(status_code=500, detail="初始化失败")

        return {"success": True, "message": "模拟交易系统已初始化"}

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_trading():
    """
    开始交易
    POST /api/paper-trading/start
    """
    try:
        controller = get_paper_controller()
        await controller.start_trading()

        return {"success": True, "message": "交易已启动"}

    except Exception as e:
        logger.error(f"启动交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_trading():
    """
    停止交易
    POST /api/paper-trading/stop
    """
    try:
        controller = get_paper_controller()
        await controller.stop_trading()

        return {"success": True, "message": "交易已停止"}

    except Exception as e:
        logger.error(f"停止交易失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_paper_trading_router():
    """创建模拟交易路由"""
    return router
