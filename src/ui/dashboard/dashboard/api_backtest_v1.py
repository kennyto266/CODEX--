"""
Phase 3: Performance Optimization - Backtest API v1
实现高性能回测API端点，集成Rust引擎

任务:
- T058: /api/v1/backtest/run - 使用Rust引擎运行回测
- T059: /api/v1/backtest/optimize - 参数优化端点
- T060: /api/v1/backtest/metrics - 性能指标端点
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import psutil

from .rust_engine_client import rust_engine

logger = logging.getLogger(__name__)

# ==================== Data Models ====================

class BacktestRunRequest(BaseModel):
    """回测运行请求"""
    symbol: str = Field(..., description="股票代码 (例如: 0700.hk)")
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)")
    strategy: str = Field(..., description="策略类型 (ma, rsi, macd, bb, kdj, cci, adx, atr, obv, ichimoku, sar)")
    parameters: Dict[str, float] = Field(
        default_factory=dict,
        description="策略参数，例如: {'period': 20, 'fast_period': 10}"
    )
    initial_capital: float = Field(default=100000.0, description="初始资金")


class BacktestOptimizeRequest(BaseModel):
    """参数优化请求"""
    symbol: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    strategy: str = Field(..., description="策略类型")
    param_grid: Dict[str, List[float]] = Field(
        ...,
        description="参数网格，例如: {'period': [10, 20, 30], 'fast_period': [5, 10, 15]}"
    )
    initial_capital: float = Field(default=100000.0, description="初始资金")
    max_workers: int = Field(default=4, description="最大并行数")


class PerformanceMetrics(BaseModel):
    """性能指标"""
    execution_time_ms: float = Field(..., description="执行时间 (毫秒)")
    memory_before_mb: float = Field(..., description="执行前内存 (MB)")
    memory_after_mb: float = Field(..., description="执行后内存 (MB)")
    memory_delta_mb: float = Field(..., description="内存增量 (MB)")
    timestamp: str = Field(..., description="时间戳")


class BacktestRunResponse(BaseModel):
    """回测运行响应"""
    result_id: str = Field(..., description="结果ID")
    status: str = Field(..., description="状态 (completed/failed)")
    metrics: Dict[str, Any] = Field(..., description="回测指标")
    performance: PerformanceMetrics = Field(..., description="性能指标")
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="交易列表")
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="权益曲线")


class BacktestOptimizeResponse(BaseModel):
    """参数优化响应"""
    optimization_id: str = Field(..., description="优化ID")
    status: str = Field(..., description="状态")
    best_params: Dict[str, float] = Field(..., description="最佳参数")
    best_metrics: Dict[str, Any] = Field(..., description="最佳指标")
    total_combinations: int = Field(..., description="总参数组合数")
    performance: PerformanceMetrics = Field(..., description="性能指标")
    top_results: List[Dict[str, Any]] = Field(default_factory=list, description="前N个结果")


class ApiMetrics(BaseModel):
    """API性能指标"""
    timestamp: str = Field(..., description="时间戳")
    uptime_seconds: float = Field(..., description="运行时间 (秒)")
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    avg_response_time_ms: float = Field(..., description="平均响应时间 (毫秒)")
    cpu_usage_percent: float = Field(..., description="CPU使用率 (%)")
    memory_usage_mb: float = Field(..., description="内存使用 (MB)")
    active_connections: int = Field(..., description="活跃连接数")


# ==================== API Router ====================

def create_backtest_v1_router() -> APIRouter:
    """创建Backtest v1 API路由"""
    router = APIRouter(prefix="/api/v1/backtest", tags=["Backtest v1"])

    # 性能统计
    stats = {
        "start_time": datetime.now(),
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_response_time": 0.0,
        "active_connections": 0
    }

    @router.post("/run", response_model=BacktestRunResponse)
    async def run_backtest(request: BacktestRunRequest):
        """
        T058: 运行回测 - 使用Rust引擎

        高性能回测端点，集成了Rust引擎的11种技术指标策略
        - 支持MA, RSI, MACD, Bollinger Bands, KDJ, CCI, ADX, ATR, OBV, Ichimoku, SAR
        - 异步处理，响应时间 < 50ms
        - 包含完整的性能指标
        """
        result_id = str(uuid4())
        request_start = datetime.now()

        stats["total_requests"] += 1
        stats["active_connections"] += 1

        try:
            logger.info(
                f"[T058] 回测请求: {result_id}, {request.symbol}, "
                f"策略: {request.strategy}"
            )

            # 验证请求参数
            _validate_backtest_request(request)

            # 调用Rust引擎运行回测
            result = await rust_engine.run_backtest(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                strategy_type=request.strategy,
                parameters=request.parameters,
                initial_capital=request.initial_capital
            )

            # 构建响应
            response = BacktestRunResponse(
                result_id=result_id,
                status="completed",
                metrics=result.get("metrics", {}),
                performance=PerformanceMetrics(**result.get("performance", {})),
                trades=result.get("trades", []),
                equity_curve=result.get("equity_curve", [])
            )

            # 更新统计
            response_time = (datetime.now() - request_start).total_seconds() * 1000
            stats["successful_requests"] += 1
            stats["total_response_time"] += response_time

            logger.info(
                f"[T058] 回测完成: {result_id}, "
                f"响应时间: {response_time:.2f}ms, "
                f"策略: {request.strategy}"
            )

            return response

        except Exception as e:
            stats["failed_requests"] += 1
            logger.error(f"[T058] 回测失败: {result_id}, 错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            stats["active_connections"] -= 1

    @router.post("/optimize", response_model=BacktestOptimizeResponse)
    async def optimize_parameters(request: BacktestOptimizeRequest):
        """
        T059: 参数优化 - 并行处理

        高性能参数优化端点，使用Rayon进行并行计算
        - 支持网格搜索所有参数组合
        - 并行处理，提高吞吐量
        - WebSocket实时进度推送 (future)
        - 结果缓存
        """
        optimization_id = str(uuid4())
        request_start = datetime.now()

        stats["total_requests"] += 1
        stats["active_connections"] += 1

        try:
            # 计算参数组合数
            total_combinations = 1
            for param, values in request.param_grid.items():
                total_combinations *= len(values)

            logger.info(
                f"[T059] 优化请求: {optimization_id}, {request.symbol}, "
                f"策略: {request.strategy}, 组合数: {total_combinations}"
            )

            # 验证请求参数
            _validate_optimize_request(request, total_combinations)

            # 调用Rust引擎进行优化
            result = await rust_engine.run_optimization(
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                strategy_type=request.strategy,
                param_grid=request.param_grid,
                initial_capital=request.initial_capital,
                max_workers=request.max_workers
            )

            # 构建响应
            response = BacktestOptimizeResponse(
                optimization_id=optimization_id,
                status="completed",
                best_params=result.get("best_params", {}),
                best_metrics=result.get("best_metrics", {}),
                total_combinations=total_combinations,
                performance=PerformanceMetrics(**result.get("performance", {})),
                top_results=result.get("top_results", [])
            )

            # 更新统计
            response_time = (datetime.now() - request_start).total_seconds() * 1000
            stats["successful_requests"] += 1
            stats["total_response_time"] += response_time

            logger.info(
                f"[T059] 优化完成: {optimization_id}, "
                f"响应时间: {response_time:.2f}ms, "
                f"最佳Sharpe: {response.best_metrics.get('sharpe_ratio', 'N/A')}"
            )

            return response

        except Exception as e:
            stats["failed_requests"] += 1
            logger.error(f"[T059] 优化失败: {optimization_id}, 错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            stats["active_connections"] -= 1

    @router.get("/metrics", response_model=ApiMetrics)
    async def get_api_metrics():
        """
        T060: 获取API性能指标

        返回API性能监控数据
        - 请求统计
        - 响应时间
        - 资源使用
        - 错误率
        """
        try:
            now = datetime.now()
            uptime = (now - stats["start_time"]).total_seconds()

            # 计算平均响应时间
            avg_response_time = (
                stats["total_response_time"] / stats["successful_requests"]
                if stats["successful_requests"] > 0 else 0
            )

            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.Process().memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 计算错误率
            error_rate = (
                stats["failed_requests"] / stats["total_requests"] * 100
                if stats["total_requests"] > 0 else 0
            )

            metrics = ApiMetrics(
                timestamp=now.isoformat(),
                uptime_seconds=round(uptime, 2),
                total_requests=stats["total_requests"],
                successful_requests=stats["successful_requests"],
                failed_requests=stats["failed_requests"],
                error_rate_percent=round(error_rate, 2),
                avg_response_time_ms=round(avg_response_time, 2),
                cpu_usage_percent=round(cpu_percent, 2),
                memory_usage_mb=round(memory_mb, 2),
                active_connections=stats["active_connections"]
            )

            logger.debug(
                f"[T060] 性能指标: 成功率: {100-error_rate:.1f}%, "
                f"平均响应: {avg_response_time:.2f}ms"
            )

            return metrics

        except Exception as e:
            logger.error(f"[T060] 获取指标失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


# ==================== Helper Functions ====================

def _validate_backtest_request(request: BacktestRunRequest):
    """验证回测请求参数"""
    # 验证股票代码
    if not request.symbol.endswith('.hk'):
        raise ValueError("股票代码必须以 '.hk' 结尾 (例如: 0700.hk)")
    if request.symbol != request.symbol.lower():
        raise ValueError("股票代码必须为小写 (例如: 0700.hk)")

    # 验证日期
    try:
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = datetime.strptime(request.end_date, "%Y-%m-%d")
        if start >= end:
            raise ValueError("开始日期必须早于结束日期")

        duration = (end - start).days
        if duration < 1:
            raise ValueError("回测期间至少1天")
        if duration > 3650:
            raise ValueError("回测期间不能超过10年")
    except ValueError as e:
        raise ValueError(f"日期格式错误: {e}")

    # 验证资金
    if request.initial_capital <= 0:
        raise ValueError("初始资金必须大于0")

    # 验证策略类型
    valid_strategies = [
        "ma", "rsi", "macd", "bb", "kdj", "cci", "adx", "atr", "obv", "ichimoku", "sar"
    ]
    if request.strategy.lower() not in valid_strategies:
        raise ValueError(f"策略类型必须是: {', '.join(valid_strategies)}")


def _validate_optimize_request(request: BacktestOptimizeRequest, total_combinations: int):
    """验证优化请求参数"""
    # 先验证基本回测参数
    _validate_backtest_request(
        BacktestRunRequest(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy=request.strategy,
            parameters={},  # 优化不需要具体参数
            initial_capital=request.initial_capital
        )
    )

    # 验证参数网格
    if not request.param_grid:
        raise ValueError("参数网格不能为空")

    # 验证参数组合数
    if total_combinations > 10000:
        raise ValueError("参数组合数不能超过10,000 (性能考虑)")

    # 验证并行数
    if request.max_workers < 1 or request.max_workers > 16:
        raise ValueError("并行数必须在1-16之间")

    # 验证每个参数至少有一个值
    for param, values in request.param_grid.items():
        if not values:
            raise ValueError(f"参数 '{param}' 必须至少有一个值")
        if len(values) > 100:
            raise ValueError(f"参数 '{param}' 的值不能超过100个")
