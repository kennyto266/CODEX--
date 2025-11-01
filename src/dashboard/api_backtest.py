"""
回測系統 API 路由

提供回測執行、狀態監控和結果查詢的 REST 端點
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import json

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

class BacktestConfig(BaseModel):
    """回測配置"""
    strategy_id: str = Field(..., description="策略ID")
    symbol: str = Field(..., description="股票代碼")
    start_date: str = Field(..., description="開始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="結束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000, description="初始資本")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略參數")


class BacktestRequest(BaseModel):
    """回測請求"""
    config: BacktestConfig
    run_name: Optional[str] = Field(None, description="回測名稱")


class BacktestStatus(BaseModel):
    """回測狀態"""
    backtest_id: str
    status: str  # pending, running, completed, failed
    progress: int = Field(default=0, ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PerformanceMetrics(BaseModel):
    """性能指標"""
    total_return_pct: float = Field(description="總收益率 (%)")
    annual_return_pct: float = Field(description="年化收益率 (%)")
    volatility: float = Field(description="波動率")
    sharpe_ratio: float = Field(description="Sharpe 比率")
    sortino_ratio: float = Field(description="Sortino 比率")
    max_drawdown: float = Field(description="最大回撤 (%)")
    win_rate: float = Field(description="勝率")
    total_trades: int = Field(description="交易次數")


class BacktestResults(BaseModel):
    """回測結果"""
    backtest_id: str
    strategy_id: str
    symbol: str
    period: Dict[str, str]  # {start_date, end_date}
    metrics: PerformanceMetrics
    equity_curve: List[Dict[str, Any]] = Field(description="權益曲線數據")
    trade_list: List[Dict[str, Any]] = Field(description="交易列表")
    created_at: datetime


# ==================== API Router ====================

def create_backtest_router() -> APIRouter:
    """創建回測 API 路由"""
    router = APIRouter(prefix="/api/backtest", tags=["Backtest"])
    logger = logging.getLogger("hk_quant_system.dashboard.api_backtest")

    # 內存中的回測記錄（生產環境應使用數據庫）
    backtest_records: Dict[str, Dict[str, Any]] = {}
    backtest_results: Dict[str, BacktestResults] = {}

    # ==================== POST: 提交回測 ====================

    @router.post("/run", response_model=Dict[str, str])
    async def run_backtest(request: BacktestRequest) -> Dict[str, str]:
        """
        提交回測任務

        - **strategy_id**: 策略ID
        - **symbol**: 股票代碼
        - **start_date**: 開始日期
        - **end_date**: 結束日期
        - **initial_capital**: 初始資本

        Returns:
            backtest_id: 回測ID，用於查詢狀態和結果
        """
        try:
            backtest_id = str(uuid4())
            config = request.config

            # 記錄回測信息
            backtest_records[backtest_id] = {
                "backtest_id": backtest_id,
                "config": config.dict(),
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "error_message": None
            }

            logger.info(f"提交回測任務: {backtest_id}, 策略: {config.strategy_id}, 股票: {config.symbol}")

            # 異步執行回測（簡化實現，實際應調用真實回測引擎）
            asyncio.create_task(_execute_backtest_async(
                backtest_id,
                config,
                backtest_records,
                backtest_results,
                logger
            ))

            return {
                "backtest_id": backtest_id,
                "status": "pending",
                "message": f"回測已提交，ID: {backtest_id}"
            }

        except Exception as e:
            logger.error(f"提交回測失敗: {e}")
            raise HTTPException(status_code=500, detail=f"回測提交失敗: {str(e)}")

    # ==================== GET: 查詢回測狀態 ====================

    @router.get("/status/{backtest_id}", response_model=BacktestStatus)
    async def get_backtest_status(backtest_id: str) -> BacktestStatus:
        """
        查詢回測狀態

        - **backtest_id**: 回測ID

        Returns:
            回測狀態對象，包含進度和當前狀態
        """
        if backtest_id not in backtest_records:
            raise HTTPException(status_code=404, detail=f"回測ID不存在: {backtest_id}")

        record = backtest_records[backtest_id]
        return BacktestStatus(
            backtest_id=record["backtest_id"],
            status=record["status"],
            progress=record["progress"],
            started_at=record.get("started_at"),
            completed_at=record.get("completed_at"),
            error_message=record.get("error_message")
        )

    # ==================== GET: 獲取回測結果 ====================

    @router.get("/results/{backtest_id}", response_model=BacktestResults)
    async def get_backtest_results(backtest_id: str) -> BacktestResults:
        """
        獲取回測結果

        - **backtest_id**: 回測ID

        Returns:
            完整的回測結果，包含性能指標和交易列表
        """
        if backtest_id not in backtest_records:
            raise HTTPException(status_code=404, detail=f"回測ID不存在: {backtest_id}")

        record = backtest_records[backtest_id]
        if record["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"回測未完成，當前狀態: {record['status']}"
            )

        if backtest_id not in backtest_results:
            raise HTTPException(status_code=404, detail=f"未找到回測結果: {backtest_id}")

        return backtest_results[backtest_id]

    # ==================== GET: 獲取回測列表 ====================

    @router.get("/list")
    @cached(ttl=30, key_prefix="backtest_list")
    async def list_backtests(
        status: Optional[str] = Query(None, description="按狀態過濾"),
        strategy_id: Optional[str] = Query(None, description="按策略ID過濾"),
        symbol: Optional[str] = Query(None, description="按股票過濾"),
        sort_by: str = Query("created_at", description="排序字段 (created_at/status/progress)"),
        sort_order: str = Query("desc", description="排序方向 (asc/desc)"),
        limit: int = Query(20, ge=1, le=100, description="返回數量限制"),
        offset: int = Query(0, ge=0, description="偏移位置")
    ) -> Dict[str, Any]:
        """
        獲取回測列表 - 帶緩存、分頁和過濾功能

        Returns:
            回測記錄列表
        """
        try:
            logger.info(f"獲取回測列表: status={status}, strategy_id={strategy_id}, symbol={symbol}, limit={limit}, offset={offset}")

            records = list(backtest_records.values())

            # 應用過濾器
            if status:
                records = [r for r in records if r["status"] == status]

            if strategy_id:
                records = [r for r in records if r["config"]["strategy_id"] == strategy_id]

            if symbol:
                records = [r for r in records if r["config"]["symbol"] == symbol]

            # 應用排序
            reverse = sort_order.lower() == "desc"
            if sort_by == "created_at":
                records.sort(key=lambda x: x["created_at"], reverse=reverse)
            elif sort_by == "status":
                records.sort(key=lambda x: x["status"], reverse=reverse)
            elif sort_by == "progress":
                records.sort(key=lambda x: x["progress"], reverse=reverse)

            # 計算總數和分頁
            total = len(records)
            paginated = records[offset:offset + limit]

            # 轉換為可序列化的格式
            result = []
            for record in paginated:
                result.append({
                    "backtest_id": record["backtest_id"],
                    "strategy_id": record["config"]["strategy_id"],
                    "symbol": record["config"]["symbol"],
                    "status": record["status"],
                    "progress": record["progress"],
                    "created_at": record["created_at"].isoformat(),
                    "started_at": record["started_at"].isoformat() if record["started_at"] else None,
                    "completed_at": record["completed_at"].isoformat() if record["completed_at"] else None
                })

            filters = {
                "status": status,
                "strategy_id": strategy_id,
                "symbol": symbol,
                "sort_by": sort_by,
                "sort_order": sort_order
            }

            logger.info(f"返回 {len(result)} 個回測 (總數: {total})")

            return create_paginated_response(
                items=result,
                total=total,
                page=(offset // limit) + 1,
                size=limit,
                filters=filters
            )

        except Exception as e:
            logger.error(f"獲取回測列表失敗: {e}")
            return create_error_response(f"獲取回測列表失敗: {str(e)}")

    # ==================== POST: 優化參數 ====================

    @router.post("/optimize", response_model=Dict[str, str])
    async def optimize_parameters(request: BacktestRequest) -> Dict[str, str]:
        """
        運行參數優化

        自動搜索最優參數組合

        Returns:
            優化任務ID
        """
        try:
            backtest_id = str(uuid4())
            config = request.config

            # 記錄優化任務
            backtest_records[backtest_id] = {
                "backtest_id": backtest_id,
                "config": config.dict(),
                "status": "pending",
                "progress": 0,
                "optimization": True,
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "error_message": None
            }

            logger.info(f"提交參數優化任務: {backtest_id}")

            # 異步執行優化
            asyncio.create_task(_execute_optimization_async(
                backtest_id,
                config,
                backtest_records,
                backtest_results,
                logger
            ))

            return {
                "optimization_id": backtest_id,
                "status": "pending",
                "message": "參數優化已啟動"
            }

        except Exception as e:
            logger.error(f"提交參數優化失敗: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


# ==================== Background Tasks ====================

async def _execute_backtest_async(
    backtest_id: str,
    config: BacktestConfig,
    records: Dict[str, Dict[str, Any]],
    results: Dict[str, BacktestResults],
    logger: logging.Logger
) -> None:
    """異步執行回測"""
    try:
        if backtest_id not in records:
            return

        record = records[backtest_id]
        record["status"] = "running"
        record["started_at"] = datetime.now()

        logger.info(f"開始執行回測: {backtest_id}")

        # 模擬回測執行（實際應調用 enhanced_backtest_engine）
        for progress in range(0, 101, 10):
            record["progress"] = progress
            await asyncio.sleep(1)  # 模擬耗時操作

        # 生成模擬結果
        equity_curve = [
            {
                "date": f"2023-{i//30 + 1:02d}-{i%30 + 1:02d}",
                "portfolio_value": 100000 * (1 + i * 0.001)
            }
            for i in range(100)
        ]

        trade_list = [
            {
                "date": "2023-01-15",
                "signal": "BUY",
                "price": 325.50,
                "quantity": 100,
                "profit": 500.0
            }
        ]

        metrics = PerformanceMetrics(
            total_return_pct=10.5,
            annual_return_pct=12.3,
            volatility=0.15,
            sharpe_ratio=1.8,
            sortino_ratio=2.1,
            max_drawdown=5.2,
            win_rate=0.65,
            total_trades=25
        )

        # 存儲結果
        results[backtest_id] = BacktestResults(
            backtest_id=backtest_id,
            strategy_id=config.strategy_id,
            symbol=config.symbol,
            period={
                "start_date": config.start_date,
                "end_date": config.end_date
            },
            metrics=metrics,
            equity_curve=equity_curve,
            trade_list=trade_list,
            created_at=datetime.now()
        )

        record["status"] = "completed"
        record["completed_at"] = datetime.now()
        record["progress"] = 100

        logger.info(f"回測完成: {backtest_id}")

    except Exception as e:
        logger.error(f"回測執行失敗: {backtest_id}, 錯誤: {e}")
        if backtest_id in records:
            records[backtest_id]["status"] = "failed"
            records[backtest_id]["error_message"] = str(e)


async def _execute_optimization_async(
    optimization_id: str,
    config: BacktestConfig,
    records: Dict[str, Dict[str, Any]],
    results: Dict[str, BacktestResults],
    logger: logging.Logger
) -> None:
    """異步執行參數優化"""
    try:
        if optimization_id not in records:
            return

        record = records[optimization_id]
        record["status"] = "running"
        record["started_at"] = datetime.now()

        logger.info(f"開始參數優化: {optimization_id}")

        # 模擬優化過程
        for progress in range(0, 101, 5):
            record["progress"] = progress
            await asyncio.sleep(0.5)

        # 生成優化結果（最佳參數）
        best_result = BacktestResults(
            backtest_id=optimization_id,
            strategy_id=config.strategy_id,
            symbol=config.symbol,
            period={
                "start_date": config.start_date,
                "end_date": config.end_date
            },
            metrics=PerformanceMetrics(
                total_return_pct=15.8,
                annual_return_pct=18.5,
                volatility=0.14,
                sharpe_ratio=2.2,
                sortino_ratio=2.8,
                max_drawdown=4.1,
                win_rate=0.72,
                total_trades=32
            ),
            equity_curve=[],
            trade_list=[],
            created_at=datetime.now()
        )

        results[optimization_id] = best_result
        record["status"] = "completed"
        record["completed_at"] = datetime.now()
        record["progress"] = 100

        logger.info(f"參數優化完成: {optimization_id}")

    except Exception as e:
        logger.error(f"參數優化失敗: {optimization_id}, 錯誤: {e}")
        if optimization_id in records:
            records[optimization_id]["status"] = "failed"
            records[optimization_id]["error_message"] = str(e)
