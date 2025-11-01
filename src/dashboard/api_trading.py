"""
交易系統 API 路由

提供訂單執行、頭寸管理和交易歷史查詢的 REST 端點
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

# 導入緩存和統一響應
try:
    from ..cache.cache_manager import cache_manager, cached
    from ..models.api_response import create_success_response, create_error_response, create_paginated_response
except ImportError:
    # 如果導入失敗，創建空的緩存管理器
    class DummyCache:
        def cache_result(self, *args, **kwargs):
            def decorator(func):
                return func
    cache_manager = DummyCache()
    cached = cache_manager.cache_result

    def create_success_response(data=None):
        return {"success": True, "data": data}

    def create_error_response(error):
        return {"success": False, "error": error}

    def create_paginated_response(items, total, page, size, filters=None):
        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size if total > 0 else 0,
                },
                "filters": filters or {}
            }
        }


# ==================== Data Models ====================

class OrderType(str, Enum):
    """訂單類型"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """訂單狀態"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Position(BaseModel):
    """頭寸"""
    symbol: str = Field(..., description="股票代碼")
    quantity: int = Field(..., description="頭寸數量")
    entry_price: float = Field(..., description="建倉價格")
    current_price: float = Field(..., description="當前價格")
    position_value: float = Field(..., description="頭寸價值")
    unrealized_pnl: float = Field(..., description="未實現損益")
    unrealized_pnl_pct: float = Field(..., description="未實現損益百分比 (%)")


class Order(BaseModel):
    """訂單"""
    order_id: str = Field(..., description="訂單ID")
    symbol: str = Field(..., description="股票代碼")
    order_type: OrderType = Field(..., description="訂單類型")
    quantity: int = Field(..., description="訂單數量")
    price: float = Field(..., description="訂單價格")
    status: OrderStatus = Field(..., description="訂單狀態")
    filled_quantity: int = Field(default=0, description="已成交數量")
    created_at: datetime = Field(..., description="創建時間")
    filled_at: Optional[datetime] = Field(None, description="成交時間")


class OrderRequest(BaseModel):
    """訂單請求"""
    symbol: str = Field(..., description="股票代碼")
    order_type: OrderType = Field(..., description="訂單類型: BUY or SELL")
    quantity: int = Field(..., ge=1, description="訂單數量")
    price: float = Field(..., gt=0, description="訂單價格")


class Trade(BaseModel):
    """成交記錄"""
    trade_id: str = Field(..., description="成交ID")
    symbol: str = Field(..., description="股票代碼")
    order_type: OrderType = Field(..., description="訂單類型")
    quantity: int = Field(..., description="成交數量")
    price: float = Field(..., description="成交價格")
    commission: float = Field(..., description="手續費")
    executed_at: datetime = Field(..., description="成交時間")
    profit_loss: Optional[float] = Field(None, description="實現損益")


# ==================== API Router ====================

def create_trading_router() -> APIRouter:
    """創建交易 API 路由"""
    router = APIRouter(prefix="/api/trading", tags=["Trading"])
    logger = logging.getLogger("hk_quant_system.dashboard.api_trading")

    # 模擬數據存儲
    positions_store: Dict[str, Dict[str, Any]] = {
        "0700.HK": {
            "symbol": "0700.HK",
            "name": "騰訊",
            "quantity": 1000,
            "entry_price": 300.50,
            "current_price": 325.50,
            "position_value": 325500,
            "unrealized_pnl": 25000,
            "unrealized_pnl_pct": 8.33
        },
        "0939.HK": {
            "symbol": "0939.HK",
            "name": "中國建設銀行",
            "quantity": 5000,
            "entry_price": 6.50,
            "current_price": 6.85,
            "position_value": 34250,
            "unrealized_pnl": 1750,
            "unrealized_pnl_pct": 5.38
        },
        "0388.HK": {
            "symbol": "0388.HK",
            "name": "香港交易所",
            "quantity": 500,
            "entry_price": 400.20,
            "current_price": 420.80,
            "position_value": 210400,
            "unrealized_pnl": 10300,
            "unrealized_pnl_pct": 5.14
        }
    }

    orders_store: Dict[str, Dict[str, Any]] = {}
    trades_store: Dict[str, Dict[str, Any]] = {}

    # ==================== GET: 獲取開倉頭寸 ====================

    @router.get("/positions")
    @cached(ttl=60, key_prefix="positions")
    async def get_positions(
        sort_by: str = Query("position_value", description="排序字段 (symbol/name/position_value/unrealized_pnl)"),
        sort_order: str = Query("desc", description="排序方向 (asc/desc)"),
        min_pnl_pct: Optional[float] = Query(None, description="最小收益率過濾"),
        page: int = Query(1, ge=1, description="頁碼"),
        size: int = Query(50, ge=1, le=100, description="每頁數量"),
        fields: Optional[str] = Query(None, description="返回字段，逗號分隔")
    ) -> Dict[str, Any]:
        """
        獲取所有開倉頭寸 - 帶緩存、分頁和排序功能

        Returns:
            分頁的開倉頭寸列表
        """
        try:
            logger.info(f"獲取頭寸列表: sort_by={sort_by}, sort_order={sort_order}, page={page}, size={size}")

            positions_list = []
            for symbol, position in positions_store.items():
                # 應用過濾器
                if min_pnl_pct is not None and position["unrealized_pnl_pct"] < min_pnl_pct:
                    continue

                position_dict = {
                    "symbol": position["symbol"],
                    "name": position["name"],
                    "quantity": position["quantity"],
                    "entry_price": position["entry_price"],
                    "current_price": position["current_price"],
                    "position_value": position["position_value"],
                    "unrealized_pnl": position["unrealized_pnl"],
                    "unrealized_pnl_pct": position["unrealized_pnl_pct"]
                }
                positions_list.append(position_dict)

            # 應用排序
            reverse = sort_order.lower() == "desc"
            if sort_by in ["symbol", "name"]:
                positions_list.sort(key=lambda x: x[sort_by].lower(), reverse=reverse)
            elif sort_by in ["position_value", "unrealized_pnl"]:
                positions_list.sort(key=lambda x: x[sort_by], reverse=reverse)
            elif sort_by == "unrealized_pnl_pct":
                positions_list.sort(key=lambda x: x["unrealized_pnl_pct"], reverse=reverse)

            # 計算總數和分頁
            total = len(positions_list)
            start = (page - 1) * size
            end = start + size
            paginated_positions = positions_list[start:end]

            # 字段過濾
            if fields:
                requested_fields = [f.strip() for f in fields.split(",")]
                filtered_positions = []
                for position in paginated_positions:
                    filtered_position = {k: v for k, v in position.items() if k in requested_fields}
                    filtered_positions.append(filtered_position)
                paginated_positions = filtered_positions

            # 構建過濾條件
            filters = {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "min_pnl_pct": min_pnl_pct
            }

            logger.info(f"返回 {len(paginated_positions)} 個頭寸 (總數: {total})")

            return create_paginated_response(
                items=paginated_positions,
                total=total,
                page=page,
                size=size,
                filters=filters
            )

        except Exception as e:
            logger.error(f"獲取頭寸失敗: {e}")
            return create_error_response(f"獲取頭寸失敗: {str(e)}")

    # ==================== GET: 獲取特定頭寸詳情 ====================

    @router.get("/positions/{symbol}")
    @cached(ttl=30, key_prefix="position_detail")
    async def get_position_detail(symbol: str) -> Dict[str, Any]:
        """
        獲取特定股票的頭寸詳情 - 帶緩存

        - **symbol**: 股票代碼

        Returns:
            頭寸詳細信息
        """
        logger.debug(f"獲取頭寸詳情: {symbol}")

        if symbol not in positions_store:
            return create_error_response(f"沒有持倉: {symbol}")

        position = positions_store[symbol]
        position_detail = {
            "symbol": position["symbol"],
            "name": position["name"],
            "quantity": position["quantity"],
            "entry_price": position["entry_price"],
            "current_price": position["current_price"],
            "position_value": position["position_value"],
            "unrealized_pnl": position["unrealized_pnl"],
            "unrealized_pnl_pct": position["unrealized_pnl_pct"],
            "percentage_of_portfolio": position["position_value"] / 570150 * 100  # 總價值
        }

        return create_success_response(data=position_detail)

    # ==================== POST: 下單 ====================

    @router.post("/order", response_model=Dict[str, Any])
    async def place_order(request: OrderRequest) -> Dict[str, Any]:
        """
        提交訂單

        - **symbol**: 股票代碼
        - **order_type**: BUY 或 SELL
        - **quantity**: 訂單數量
        - **price**: 訂單價格

        Returns:
            訂單確認信息
        """
        try:
            order_id = str(uuid4())[:8]

            # 執行訂單驗證
            if request.order_type == OrderType.SELL:
                symbol = request.symbol
                if symbol not in positions_store:
                    raise HTTPException(
                        status_code=400,
                        detail=f"沒有持倉無法賣出: {symbol}"
                    )
                if positions_store[symbol]["quantity"] < request.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"持倉不足：要求 {request.quantity}，實際 {positions_store[symbol]['quantity']}"
                    )

            # 創建訂單
            order = {
                "order_id": order_id,
                "symbol": request.symbol,
                "order_type": request.order_type.value,
                "quantity": request.quantity,
                "price": request.price,
                "status": OrderStatus.PENDING.value,
                "filled_quantity": 0,
                "created_at": datetime.now(),
                "filled_at": None
            }

            orders_store[order_id] = order
            logger.info(f"訂單已提交: {order_id}, {request.order_type.value} {request.quantity} {request.symbol} @ {request.price}")

            # 模擬自動成交
            order["status"] = OrderStatus.FILLED.value
            order["filled_quantity"] = request.quantity
            order["filled_at"] = datetime.now()

            # 記錄成交
            trade_id = str(uuid4())[:8]
            trade = {
                "trade_id": trade_id,
                "symbol": request.symbol,
                "order_type": request.order_type.value,
                "quantity": request.quantity,
                "price": request.price,
                "commission": request.price * request.quantity * 0.001,  # 0.1% 手續費
                "executed_at": datetime.now(),
                "profit_loss": None
            }
            trades_store[trade_id] = trade

            # 更新頭寸
            if request.symbol not in positions_store:
                if request.order_type == OrderType.BUY:
                    positions_store[request.symbol] = {
                        "symbol": request.symbol,
                        "name": request.symbol,
                        "quantity": request.quantity,
                        "entry_price": request.price,
                        "current_price": request.price,
                        "position_value": request.price * request.quantity,
                        "unrealized_pnl": 0,
                        "unrealized_pnl_pct": 0
                    }
            else:
                position = positions_store[request.symbol]
                if request.order_type == OrderType.BUY:
                    # 加倉：更新平均建倉價
                    total_value = position["position_value"] + request.price * request.quantity
                    total_quantity = position["quantity"] + request.quantity
                    position["entry_price"] = total_value / total_quantity
                    position["quantity"] = total_quantity
                    position["position_value"] = total_value
                else:  # SELL
                    # 減倉
                    position["quantity"] -= request.quantity
                    position["position_value"] = position["quantity"] * position["current_price"]
                    if position["quantity"] == 0:
                        del positions_store[request.symbol]

            return {
                "order_id": order_id,
                "status": "filled",
                "filled_quantity": request.quantity,
                "filled_price": request.price,
                "message": f"訂單已成交: {order_id}"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"下單失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取訂單列表 ====================

    @router.get("/orders", response_model=List[Dict[str, Any]])
    async def get_orders(
        status: Optional[str] = Query(None, description="按狀態過濾"),
        limit: int = Query(50, ge=1, le=100)
    ) -> List[Dict[str, Any]]:
        """
        獲取訂單列表

        - **status**: 訂單狀態 (PENDING, FILLED, CANCELLED)
        - **limit**: 返回數量

        Returns:
            訂單列表
        """
        try:
            orders = list(orders_store.values())

            # 按狀態過濾
            if status:
                orders = [o for o in orders if o["status"] == status.upper()]

            # 按時間排序（最新在前）
            orders.sort(key=lambda x: x["created_at"], reverse=True)

            # 轉換格式
            result = []
            for order in orders[:limit]:
                result.append({
                    "order_id": order["order_id"],
                    "symbol": order["symbol"],
                    "order_type": order["order_type"],
                    "quantity": order["quantity"],
                    "price": order["price"],
                    "status": order["status"],
                    "filled_quantity": order["filled_quantity"],
                    "created_at": order["created_at"].isoformat(),
                    "filled_at": order["filled_at"].isoformat() if order["filled_at"] else None
                })

            return result

        except Exception as e:
            logger.error(f"獲取訂單列表失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== DELETE: 取消訂單 ====================

    @router.delete("/orders/{order_id}", response_model=Dict[str, str])
    async def cancel_order(order_id: str) -> Dict[str, str]:
        """
        取消未成交訂單

        - **order_id**: 訂單ID

        Returns:
            取消結果
        """
        try:
            if order_id not in orders_store:
                raise HTTPException(status_code=404, detail=f"訂單不存在: {order_id}")

            order = orders_store[order_id]
            if order["status"] == OrderStatus.FILLED.value:
                raise HTTPException(status_code=400, detail="已成交訂單無法取消")

            order["status"] = OrderStatus.CANCELLED.value
            logger.info(f"訂單已取消: {order_id}")

            return {"status": "success", "message": f"訂單 {order_id} 已取消"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"取消訂單失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取成交歷史 ====================

    @router.get("/trades", response_model=List[Dict[str, Any]])
    async def get_trade_history(
        symbol: Optional[str] = Query(None, description="按股票過濾"),
        limit: int = Query(100, ge=1, le=500)
    ) -> List[Dict[str, Any]]:
        """
        獲取成交歷史

        - **symbol**: 股票代碼過濾
        - **limit**: 返回數量

        Returns:
            成交記錄列表
        """
        try:
            trades = list(trades_store.values())

            # 按股票過濾
            if symbol:
                trades = [t for t in trades if t["symbol"] == symbol]

            # 按時間排序（最新在前）
            trades.sort(key=lambda x: x["executed_at"], reverse=True)

            # 轉換格式
            result = []
            for trade in trades[:limit]:
                result.append({
                    "trade_id": trade["trade_id"],
                    "symbol": trade["symbol"],
                    "order_type": trade["order_type"],
                    "quantity": trade["quantity"],
                    "price": trade["price"],
                    "commission": trade["commission"],
                    "executed_at": trade["executed_at"].isoformat(),
                    "profit_loss": trade.get("profit_loss")
                })

            return result

        except Exception as e:
            logger.error(f"獲取成交歷史失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== GET: 獲取交易統計 ====================

    @router.get("/statistics", response_model=Dict[str, Any])
    async def get_trading_statistics() -> Dict[str, Any]:
        """
        獲取交易統計信息

        Returns:
            交易統計數據
        """
        try:
            total_trades = len(trades_store)
            buy_trades = sum(1 for t in trades_store.values() if t["order_type"] == "BUY")
            sell_trades = sum(1 for t in trades_store.values() if t["order_type"] == "SELL")
            total_commission = sum(t.get("commission", 0) for t in trades_store.values())
            total_volume = sum(t["quantity"] * t["price"] for t in trades_store.values())

            stats = {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "total_volume": total_volume,
                "total_commission": total_commission,
                "average_trade_size": total_volume / total_trades if total_trades > 0 else 0,
                "win_trades": 0,  # 模擬數據
                "loss_trades": total_trades,  # 模擬數據
                "win_rate": 0.0,
                "timestamp": datetime.now().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"獲取交易統計失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
