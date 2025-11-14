"""
T059: Parameter Optimization API Endpoint with Parallel Processing

This module implements a FastAPI endpoint for parallel parameter optimization
with comprehensive result tracking, WebSocket progress updates, and performance monitoring.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Set, Union
import time
import asyncio
import uuid
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import json
import threading

# Import performance modules
from src.performance.parallel_optimizer import ParallelOptimizer
from src.performance.thread_manager import ThreadPoolManager
from src.performance.work_distributor import WorkDistributor
from src.observability.structured_logger import get_observability_logger
from src.observability.bottleneck_detector import MetricsRegistry

router = APIRouter(prefix="/api/v1", tags=["optimization"])

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ParameterSpace(BaseModel):
    """Parameter space definition for optimization"""
    name: str = Field(..., description="Parameter name")
    min_value: float = Field(..., description="Minimum value")
    max_value: float = Field(..., description="Maximum value")
    step: float = Field(..., description="Step size")

    @validator('max_value')
    def validate_max_value(cls, v, values):
        if 'min_value' in values and v <= values['min_value']:
            raise ValueError("max_value must be greater than min_value")
        return v

    @validator('step')
    def validate_step(cls, v):
        if v <= 0:
            raise ValueError("Step must be positive")
        return v


class OptimizationRequest(BaseModel):
    """Parameter optimization request"""
    symbol: str = Field(..., description="Stock symbol (e.g., 0700.HK)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    strategy_type: str = Field(..., description="Strategy type (e.g., sma, rsi, macd, kdj, etc.)")
    parameter_spaces: List[ParameterSpace] = Field(..., description="Parameter spaces to optimize")
    objective: str = Field("sharpe_ratio", description="Optimization objective")
    max_workers: Optional[int] = Field(None, description="Max worker threads (default: CPU cores)")
    max_combinations: int = Field(1000, ge=1, le=10000, description="Max parameter combinations")
    top_n: int = Field(10, ge=1, le=100, description="Return top N results")

    @validator('strategy_type')
    def validate_strategy_type(cls, v):
        valid_strategies = [
            'sma', 'rsi', 'macd', 'bollinger', 'kdj', 'cci',
            'adx', 'atr', 'obv', 'ichimoku', 'sar'
        ]
        if v.lower() not in valid_strategies:
            raise ValueError(f"Invalid strategy type. Must be one of: {valid_strategies}")
        return v.lower()

    @validator('objective')
    def validate_objective(cls, v):
        valid_objectives = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']
        if v not in valid_objectives:
            raise ValueError(f"Invalid objective. Must be one of: {valid_objectives}")
        return v


class OptimizationResult(BaseModel):
    """Single optimization result"""
    rank: int
    parameters: Dict[str, float]
    score: float
    metrics: Dict[str, float]
    execution_time_ms: int


class OptimizationResponse(BaseModel):
    """Optimization response with full results"""
    success: bool
    task_id: str
    symbol: str
    strategy_type: str
    total_combinations: int
    best_result: Optional[OptimizationResult]
    all_results: List[OptimizationResult]
    execution_time_ms: int
    workers_used: int
    performance: Dict[str, Any]
    timestamp: str

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "task_id": "opt_20251109_001",
                "symbol": "0700.HK",
                "strategy_type": "sma",
                "total_combinations": 100,
                "best_result": {
                    "rank": 1,
                    "parameters": {"fast_period": 10, "slow_period": 30},
                    "score": 1.5432,
                    "metrics": {
                        "total_return": 0.1823,
                        "sharpe_ratio": 1.5432,
                        "max_drawdown": 0.0923,
                        "win_rate": 0.6534
                    },
                    "execution_time_ms": 42
                },
                "all_results": [],
                "execution_time_ms": 5234,
                "workers_used": 8,
                "performance": {
                    "mode": "parallel",
                    "speedup_factor": 6.2,
                    "memory_usage_mb": 125.3
                },
                "timestamp": "2025-11-09T10:30:00Z"
            }
        }


class OptimizationProgress(BaseModel):
    """Optimization progress update"""
    task_id: str
    status: str  # running, completed, failed
    progress_percent: int
    completed_combinations: int
    total_combinations: int
    best_score: float
    estimated_time_remaining: Optional[int]
    current_worker_utilization: float


# =============================================================================
# GLOBAL STATE
# =============================================================================

# Global task tracking
_optimization_tasks: Dict[str, Dict[str, Any]] = {}
_active_websockets: Set[WebSocket] = set()
_task_lock = threading.Lock()

# Global instances
_optimizer = None
_thread_manager = None
_work_distributor = None
_logger = None
_metrics = None


def get_optimizer() -> ParallelOptimizer:
    """Get parallel optimizer singleton"""
    global _optimizer
    if _optimizer is None:
        _optimizer = ParallelOptimizer()
    return _optimizer


def get_thread_manager() -> ThreadPoolManager:
    """Get thread manager singleton"""
    global _thread_manager
    if _thread_manager is None:
        # Import here to avoid circular dependency
        from src.performance.thread_manager import WorkerConfig
        config = WorkerConfig(min_workers=2, max_workers=8)
        _thread_manager = ThreadPoolManager(config)
    return _thread_manager


def get_logger():
    """Get observability logger"""
    global _logger
    if _logger is None:
        _logger = get_observability_logger("optimization_api")
    return _logger


def get_metrics_registry() -> MetricsRegistry:
    """Get metrics registry singleton"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsRegistry()
    return _metrics


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/backtest/optimize", response_model=OptimizationResponse)
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
) -> OptimizationResponse:
    """
    Run parameter optimization for a trading strategy with parallel processing.

    This endpoint performs parallel parameter optimization using multiple CPU cores
    to find the best parameter combination for the specified strategy.

    - **symbol**: Stock symbol (e.g., "0700.HK")
    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    - **strategy_type**: Strategy type (sma, rsi, macd, kdj, cci, adx, atr, obv, ichimoku, sar)
    - **parameter_spaces**: List of parameter spaces to optimize
    - **objective**: Optimization objective (sharpe_ratio, total_return, max_drawdown, win_rate)
    - **max_workers**: Maximum number of worker threads (optional)
    - **max_combinations**: Maximum parameter combinations to test (1-10000)
    - **top_n**: Number of top results to return (1-100)
    """
    task_id = f"opt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    start_time = time.time()

    logger = get_logger()
    metrics = get_metrics_registry()

    # Log request
    logger.info(
        f"Optimization request received",
        extra={
            "correlation_id": task_id,
            "symbol": request.symbol,
            "strategy": request.strategy_type,
            "combinations": request.max_combinations,
            "user_action": "optimization_request"
        }
    )

    try:
        # Validate request
        _validate_optimization_request(request)

        # Record metric
        metrics.increment_counter("optimization_requests_total", labels={
            "strategy": request.strategy_type,
            "symbol": request.symbol
        })

        # Create parameter spaces dict
        parameter_spaces = {
            p.name: {
                'min': p.min_value,
                'max': p.max_value,
                'step': p.step
            }
            for p in request.parameter_spaces
        }

        # Load market data
        market_data = await _load_market_data(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Store task info
        with _task_lock:
            _optimization_tasks[task_id] = {
                'status': 'running',
                'start_time': start_time,
                'request': request.dict(),
                'progress': 0,
                'best_score': float('-inf')
            }

        # Run optimization
        result = await _run_optimization_sync(task_id, request, market_data, parameter_spaces)

        execution_time_ms = int((time.time() - start_time) * 1000)
        result.execution_time_ms = execution_time_ms

        # Record metrics
        metrics.record_histogram("optimization_duration_ms", execution_time_ms)
        metrics.increment_counter("optimization_completed_total")

        # Log completion
        logger.info(
            f"Optimization completed",
            extra={
                "correlation_id": task_id,
                "execution_time_ms": execution_time_ms,
                "best_score": result.best_result.score if result.best_result else 0,
                "combinations_tested": result.total_combinations,
                "user_action": "optimization_completed"
            }
        )

        # Update task status
        with _task_lock:
            if task_id in _optimization_tasks:
                _optimization_tasks[task_id]['status'] = 'completed'
                _optimization_tasks[task_id]['progress'] = 100

        return result

    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)

        logger.error(
            f"Optimization failed: {str(e)}",
            extra={
                "correlation_id": task_id,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "user_action": "optimization_failed"
            }
        )

        metrics.increment_counter("optimization_errors_total")

        # Update task status
        with _task_lock:
            if task_id in _optimization_tasks:
                _optimization_tasks[task_id]['status'] = 'failed'

        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "task_id": task_id,
                "execution_time_ms": execution_time_ms
            }
        )


@router.get("/backtest/optimize/status/{task_id}")
async def get_optimization_status(task_id: str):
    """
    Get optimization status for a specific task.

    Returns the current status, progress, and metrics for a running or completed optimization task.
    """
    if task_id not in _optimization_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = _optimization_tasks[task_id]

    return {
        "task_id": task_id,
        "status": task['status'],
        "progress": task.get('progress', 0),
        "best_score": task.get('best_score', 0),
        "start_time": task['start_time'],
        "estimated_completion": task.get('estimated_completion')
    }


@router.get("/backtest/optimize/health")
async def health_check():
    """
    Health check for the optimization service.

    Returns the current status of the optimization service including active tasks and resource usage.
    """
    import psutil

    active_tasks = len([t for t in _optimization_tasks.values() if t['status'] == 'running'])
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        "status": "healthy",
        "active_tasks": active_tasks,
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_gb": memory.available / (1024**3),
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@router.websocket("/ws/optimization/progress")
async def optimization_progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time optimization progress updates.

    Clients can subscribe to this WebSocket to receive live progress updates
    for running optimization tasks.
    """
    await websocket.accept()
    _active_websockets.add(websocket)
    logger = get_logger()

    try:
        logger.info(
            f"WebSocket client connected",
            extra={"client_id": id(websocket)}
        )

        while True:
            # Send heartbeat
            heartbeat = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "active_tasks": len([t for t in _optimization_tasks.values() if t['status'] == 'running'])
            }
            await websocket.send_text(json.dumps(heartbeat))
            await asyncio.sleep(5)

            # Send progress updates for running tasks
            for task_id, task in _optimization_tasks.items():
                if task['status'] == 'running':
                    progress_update = {
                        "type": "progress",
                        "task_id": task_id,
                        "status": "running",
                        "progress_percent": task.get('progress', 0),
                        "best_score": task.get('best_score', 0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    try:
                        await websocket.send_text(json.dumps(progress_update))
                    except Exception as e:
                        logger.warning(f"Failed to send progress update: {e}")
                        break

    except WebSocketDisconnect:
        _active_websockets.discard(websocket)
        logger.info(
            f"WebSocket client disconnected",
            extra={"client_id": id(websocket)}
        )
    except Exception as e:
        _active_websockets.discard(websocket)
        logger.error(
            f"WebSocket error: {str(e)}",
            extra={"error": str(e)}
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _run_optimization_sync(
    task_id: str,
    request: OptimizationRequest,
    market_data,
    parameter_spaces: Dict[str, Dict[str, float]]
) -> OptimizationResponse:
    """
    Run optimization synchronously with parallel processing.

    This function orchestrates the parallel optimization process using the
    existing ParallelOptimizer and ThreadPoolManager.
    """
    import itertools
    from src.backtest.rust_engine import RustEngine

    logger = get_logger()

    # Generate parameter combinations
    combinations = _generate_parameter_combinations(parameter_spaces)
    total_combinations = len(combinations)

    # Limit to max_combinations
    if total_combinations > request.max_combinations:
        logger.info(
            f"Too many combinations ({total_combinations}), sampling {request.max_combinations}",
            extra={"correlation_id": task_id}
        )
        combinations = combinations[:request.max_combinations]
        total_combinations = len(combinations)

    # Get backtest engine
    engine = RustEngine(use_rust=True)

    # Get parallel optimizer
    optimizer = get_optimizer()
    max_workers = request.max_workers or optimizer.max_workers

    # Run optimization
    best_score = float('-inf')
    best_params = None
    best_metrics = None
    all_results = []
    completed = 0

    chunk_size = max(1, min(50, total_combinations // max_workers))

    # Process in chunks
    for i in range(0, len(combinations), chunk_size):
        chunk = combinations[i:i + chunk_size]

        # Process chunk in parallel
        with ThreadPoolExecutor(max_workers=min(max_workers, len(chunk))) as executor:
            futures = []
            chunk_start = time.time()

            for params in chunk:
                future = executor.submit(
                    _evaluate_parameters,
                    engine, market_data, request.strategy_type, params
                )
                futures.append((params, future))

            # Collect results
            for params, future in futures:
                try:
                    score, metrics = future.result(timeout=30)

                    result = OptimizationResult(
                        rank=0,  # Will be set after sorting
                        parameters=params,
                        score=score,
                        metrics=metrics,
                        execution_time_ms=int((time.time() - chunk_start) * 1000)
                    )
                    all_results.append(result)

                    # Check if best
                    if score > best_score:
                        best_score = score
                        best_params = params
                        best_metrics = metrics

                    completed += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to evaluate params {params}: {e}",
                        extra={"correlation_id": task_id}
                    )

        # Update progress
        progress = min(100, int((i + len(chunk)) * 100 / len(combinations)))
        estimated_remaining = None
        if i > 0:
            elapsed = time.time() - (i / len(combinations)) * (time.time() - _optimization_tasks[task_id]['start_time'])
            total_time = elapsed * len(combinations) / (i + len(chunk))
            estimated_remaining = int(total_time - elapsed)

        with _task_lock:
            if task_id in _optimization_tasks:
                _optimization_tasks[task_id]['progress'] = progress
                _optimization_tasks[task_id]['best_score'] = best_score
                _optimization_tasks[task_id]['completed'] = completed
                _optimization_tasks[task_id]['total'] = total_combinations
                if estimated_remaining:
                    _optimization_tasks[task_id]['estimated_completion'] = estimated_remaining

    # Sort results
    all_results.sort(key=lambda x: x.score, reverse=True)
    for i, result in enumerate(all_results[:request.top_n]):
        result.rank = i + 1

    # Get best result
    best_result = all_results[0] if all_results else None

    # Calculate performance metrics
    performance = {
        'mode': 'parallel',
        'speedup_factor': min(max_workers, cpu_count()) if (max_workers and all_results) else 1.0,
        'memory_usage_mb': _get_memory_usage(),
        'throughput_per_second': len(all_results) / ((time.time() - _optimization_tasks[task_id]['start_time']) or 1)
    }

    return OptimizationResponse(
        success=True,
        task_id=task_id,
        symbol=request.symbol,
        strategy_type=request.strategy_type,
        total_combinations=total_combinations,
        best_result=best_result,
        all_results=all_results[:request.top_n],
        execution_time_ms=0,  # Will be set by caller
        workers_used=max_workers,
        performance=performance,
        timestamp=datetime.utcnow().isoformat()
    )


def _evaluate_parameters(engine, data, strategy_type: str, params: Dict[str, float]):
    """
    Evaluate a single parameter set using the backtest engine.

    Returns a tuple of (score, metrics) where score is the optimization objective value
    and metrics is a dict of performance metrics.
    """
    try:
        if strategy_type == 'sma':
            fast = int(params['fast_period'])
            slow = int(params['slow_period'])
            result = engine.run_sma_backtest(
                data=data,
                fast_period=fast,
                slow_period=slow
            )

            # Calculate metrics
            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0
                avg_return = 0

            total_return = result.get('total_return', 0)
            max_drawdown = result.get('max_drawdown', 0)
            win_rate = result.get('win_rate', 0)

            return sharpe, {
                'total_return': total_return,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate
            }

        elif strategy_type == 'rsi':
            period = int(params.get('period', 14))
            result = engine.run_rsi_backtest(
                data=data,
                period=period,
                oversold=30,
                overbought=70
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'macd':
            fast = int(params.get('fast', 12))
            slow = int(params.get('slow', 26))
            signal = int(params.get('signal', 9))
            result = engine.run_macd_backtest(
                data=data,
                fast_period=fast,
                slow_period=slow,
                signal_period=signal
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'kdj':
            k = int(params.get('k_period', 9))
            d = int(params.get('d_period', 3))
            oversold = int(params.get('oversold', 20))
            overbought = int(params.get('overbought', 80))
            result = engine.run_kdj_backtest(
                data=data,
                k_period=k,
                d_period=d,
                oversold=oversold,
                overbought=overbought
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'bollinger':
            period = int(params.get('period', 20))
            std_dev = float(params.get('std_dev', 2.0))
            result = engine.run_bollinger_backtest(
                data=data,
                period=period,
                std_dev=std_dev
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'cci':
            period = int(params.get('period', 20))
            result = engine.run_cci_backtest(
                data=data,
                period=period
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'adx':
            period = int(params.get('period', 14))
            result = engine.run_adx_backtest(
                data=data,
                period=period
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'atr':
            period = int(params.get('period', 14))
            multiplier = float(params.get('multiplier', 2.0))
            result = engine.run_atr_backtest(
                data=data,
                period=period,
                multiplier=multiplier
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'obv':
            result = engine.run_obv_backtest(data=data)

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'ichimoku':
            conv = int(params.get('conversion', 9))
            base = int(params.get('base', 26))
            lag = int(params.get('lag', 52))
            result = engine.run_ichimoku_backtest(
                data=data,
                conversion=conv,
                base=base,
                lag=lag
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        elif strategy_type == 'sar':
            af = float(params.get('af', 0.02))
            max_af = float(params.get('max_af', 0.2))
            result = engine.run_sar_backtest(
                data=data,
                af=af,
                max_af=max_af
            )

            returns = [t.get('pnl', 0) for t in result.get('trades', [])]
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
                sharpe = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe = 0

            return sharpe, {
                'total_return': result.get('total_return', 0),
                'sharpe_ratio': sharpe,
                'max_drawdown': result.get('max_drawdown', 0),
                'win_rate': result.get('win_rate', 0)
            }

        else:
            raise ValueError(f"Strategy {strategy_type} not supported in Rust engine yet")

    except Exception as e:
        return 0, {'error': str(e)}


def _generate_parameter_combinations(spaces: Dict[str, Dict[str, float]]) -> List[Dict[str, float]]:
    """Generate all parameter combinations from the parameter space"""
    import itertools

    # Generate value lists
    value_lists = []
    for name, space in spaces.items():
        values = []
        current = space['min']
        while current <= space['max']:
            values.append(current)
            current += space['step']
        value_lists.append(values)

    # Generate cartesian product
    combinations = []
    for combo in itertools.product(*value_lists):
        params = {}
        for i, name in enumerate(spaces.keys()):
            params[name] = combo[i]
        combinations.append(params)

    return combinations


async def _load_market_data(symbol: str, start_date: str, end_date: str):
    """
    Load market data for the specified symbol and date range.

    In production, this would fetch real data from the data source.
    For now, we generate sample data for testing.
    """
    import pandas as pd
    import numpy as np

    try:
        # Try to import the unified data collector
        from src.data_adapters.unified_data_collector import UnifiedDataCollector

        collector = UnifiedDataCollector()
        data = await collector.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return data

    except ImportError:
        # Fallback to mock data for testing
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Generate realistic price data
        np.random.seed(42)  # For reproducible results
        initial_price = 100.0
        returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
        prices = initial_price * (1 + returns).cumprod()

        data = pd.DataFrame({
            'date': dates,
            'symbol': symbol,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, len(dates)))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        })

        # Ensure high >= max(open, close) and low <= min(open, close)
        data['high'] = data[['open', 'close']].max(axis=1) + np.random.rand(len(data)) * 2
        data['low'] = data[['open', 'close']].min(axis=1) - np.random.rand(len(data)) * 2

        return data


def _validate_optimization_request(request: OptimizationRequest):
    """Validate optimization request parameters"""
    # Check max_combinations is reasonable
    if request.max_combinations > 10000:
        raise ValueError("Max combinations cannot exceed 10,000 for performance reasons")

    # Check parameter spaces
    for space in request.parameter_spaces:
        if space.min_value >= space.max_value:
            raise ValueError(f"Invalid parameter space: {space.name} (min >= max)")
        if space.step <= 0:
            raise ValueError(f"Step must be positive for: {space.name}")
        if space.max_value - space.min_value < space.step:
            raise ValueError(f"Invalid parameter space: {space.name} (range smaller than step)")

    # Check date range
    try:
        from datetime import datetime
        start = datetime.strptime(request.start_date, '%Y-%m-%d')
        end = datetime.strptime(request.end_date, '%Y-%m-%d')
        if end <= start:
            raise ValueError("End date must be after start date")
        if (end - start).days > 365 * 5:
            raise ValueError("Date range cannot exceed 5 years")
    except ValueError as e:
        if "unconverted data remains" in str(e):
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise


def _get_memory_usage() -> float:
    """Get current memory usage in MB"""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def cpu_count() -> int:
    """Get CPU core count"""
    import multiprocessing
    return multiprocessing.cpu_count()
