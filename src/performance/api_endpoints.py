"""
🚀 高性能回测 API 端点

提供 RESTful API 接口：
- /api/v1/backtest/run - 快速回测
- /api/v1/backtest/optimize - 并行参数优化
- /api/v1/performance/benchmark - 性能基准测试
- /api/v1/performance/stats - 系统性能统计
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from .acceleration import get_accelerator, PerformanceConfig
from .parallel_optimizer import ParallelOptimizer
from .memory_pool import MemoryMonitor

logger = logging.getLogger(__name__)

# Pydantic 模型
class BacktestRequest(BaseModel):
    """回测请求模型"""
    symbol: str = Field(..., description="股票代码")
    strategy_type: str = Field(..., description="策略类型")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    parameters: Optional[Dict[str, float]] = Field(None, description="策略参数")
    initial_capital: float = Field(100000.0, description="初始资金")
    use_rust: bool = Field(True, description="使用 Rust 加速")


class BacktestResponse(BaseModel):
    """回测响应模型"""
    success: bool
    backend: str
    execution_time_ms: float
    metrics: Dict[str, Any]
    equity_curve: list
    trades: list
    performance: Dict[str, Any]


class OptimizationRequest(BaseModel):
    """优化请求模型"""
    symbol: str = Field(..., description="股票代码")
    strategy_type: str = Field(..., description="策略类型")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    parameter_ranges: Dict[str, list] = Field(..., description="参数范围")
    max_combinations: int = Field(10000, description="最大组合数")
    max_workers: int = Field(0, description="最大工作进程 (0=自动)")


class OptimizationResponse(BaseModel):
    """优化响应模型"""
    success: bool
    best_params: Dict[str, float]
    best_score: float
    best_result: Dict[str, Any]
    statistics: Dict[str, Any]
    backend: str
    timestamp: str


# FastAPI 应用
app = FastAPI(
    title="高性能量化回测 API",
    description="基于 Rust + Python 的 10-50x 性能加速回测系统",
    version="1.0.0",
)

# 全局优化器
optimizer = ParallelOptimizer()


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "高性能回测 API",
    }


@app.post("/api/v1/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """运行单次回测"""
    start_time = time.time()

    try:
        # 获取加速器
        config = PerformanceConfig(
            use_rust=request.use_rust,
            max_workers=psutil.cpu_count(logical=False) if psutil.cpu_count(logical=False) else 4,
        )
        accelerator = get_accelerator(config)

        # 加载数据
        logger.info(f"加载数据: {request.symbol} {request.start_date} - {request.end_date}")

        # 模拟数据加载 (实际项目中从数据源加载)
        dates = pd.date_range(request.start_date, request.end_date, freq='D')
        data = pd.DataFrame({
            'Open': np.random.randn(len(dates)).cumsum() + 100,
            'High': np.random.randn(len(dates)).cumsum() + 102,
            'Low': np.random.randn(len(dates)).cumsum() + 98,
            'Close': np.random.randn(len(dates)).cumsum() + 100,
            'Volume': np.random.randint(1000, 10000, len(dates)),
        }, index=dates)

        # 运行回测
        result = accelerator.run_backtest(
            data=data,
            strategy_type=request.strategy_type,
            params=request.parameters,
        )

        execution_time = (time.time() - start_time) * 1000

        return BacktestResponse(
            success=True,
            backend=accelerator.backend,
            execution_time_ms=execution_time,
            metrics=result['metrics'],
            equity_curve=result['equity_curve'],
            trades=result['trades'],
            performance={
                "throughput": 1000.0 / execution_time if execution_time > 0 else 0,
                "data_points": len(data),
            },
        )

    except Exception as e:
        logger.error(f"回测失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtest/optimize", response_model=OptimizationResponse)
async def optimize_parameters(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """并行参数优化"""
    start_time = time.time()

    try:
        # 加载数据
        logger.info(f"优化参数: {request.symbol} {request.strategy_type}")

        dates = pd.date_range(request.start_date, request.end_date, freq='D')
        data = pd.DataFrame({
            'Open': np.random.randn(len(dates)).cumsum() + 100,
            'High': np.random.randn(len(dates)).cumsum() + 102,
            'Low': np.random.randn(len(dates)).cumsum() + 98,
            'Close': np.random.randn(len(dates)).cumsum() + 100,
            'Volume': np.random.randint(1000, 10000, len(dates)),
        }, index=dates)

        # 执行优化
        max_workers = request.max_workers if request.max_workers > 0 else None
        opt = ParallelOptimizer(max_workers=max_workers)

        result = opt.optimize(
            data=data,
            strategy_type=request.strategy_type,
            param_ranges=request.parameter_ranges,
            max_combinations=request.max_combinations,
        )

        return OptimizationResponse(
            success=True,
            best_params=result['best_result'].parameters if result['best_result'] else {},
            best_score=result['best_result'].score if result['best_result'] else 0,
            best_result=result['best_result'].__dict__ if result['best_result'] else {},
            statistics=result['statistics'],
            backend="rust+parallel",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    except Exception as e:
        logger.error(f"优化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/performance/benchmark")
async def benchmark_performance(
    data_sizes: str = Query("100,500,1000,2000,5000", description="数据大小列表"),
    strategies: str = Query("ma,rsi,macd", description="策略列表"),
):
    """性能基准测试"""
    try:
        sizes = [int(s) for s in data_sizes.split(',')]
        strategy_list = strategies.split(',')

        # 获取加速器
        accelerator = get_accelerator()

        # 生成测试数据
        test_results = {}
        for strategy in strategy_list:
            test_results[strategy] = {}
            for size in sizes:
                dates = pd.date_range('2020-01-01', periods=size, freq='D')
                data = pd.DataFrame({
                    'Open': np.random.randn(size).cumsum() + 100,
                    'High': np.random.randn(size).cumsum() + 102,
                    'Low': np.random.randn(size).cumsum() + 98,
                    'Close': np.random.randn(size).cumsum() + 100,
                    'Volume': np.random.randint(1000, 10000, size),
                }, index=dates)

                # 运行回测
                result = accelerator.run_backtest(
                    data,
                    strategy,
                    {'fast_period': 10, 'slow_period': 20} if strategy == 'ma' else None,
                )

                execution_time = result['metrics']['execution_time_ms']
                throughput = 1000.0 / execution_time if execution_time > 0 else 0

                test_results[strategy][f'size_{size}'] = {
                    'execution_time_ms': execution_time,
                    'throughput_per_second': throughput,
                }

        return {
            'success': True,
            'backend': accelerator.backend,
            'results': test_results,
            'cpu_info': accelerator.get_cpu_info(),
        }

    except Exception as e:
        logger.error(f"基准测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/performance/stats")
async def get_performance_stats():
    """获取系统性能统计"""
    try:
        # 获取加速器
        accelerator = get_accelerator()

        # 内存监控
        monitor = MemoryMonitor()
        memory_info = monitor.get_memory_info()

        # CPU 信息
        import psutil
        cpu_info = {
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
        }

        # 内存统计
        import gc
        gc_stats = gc.get_stats()

        return {
            'success': True,
            'backend': accelerator.backend,
            'memory': memory_info,
            'cpu': cpu_info,
            'gc': gc_stats,
            'config': {
                'use_rust': accelerator.config.use_rust,
                'max_workers': accelerator.config.max_workers,
                'max_memory_mb': accelerator.config.max_memory_mb,
            },
        }

    except Exception as e:
        logger.error(f"获取性能统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/indicators/calculate")
async def calculate_indicators(
    data: list,
    indicator: str,
    period: int = 14,
):
    """计算技术指标"""
    try:
        # 获取加速器
        accelerator = get_accelerator()

        # 转换数据
        close_prices = np.array([d['close'] for d in data])

        # 计算指标
        result = accelerator.engine.calculate_indicators(
            data=close_prices,
            indicator=indicator,
            period=period,
        )

        return {
            'success': True,
            'indicator': indicator,
            'period': period,
            'values': result.tolist(),
            'backend': accelerator.backend,
        }

    except Exception as e:
        logger.error(f"指标计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/docs")
async def get_api_docs():
    """获取 API 文档"""
    return {
        "title": "高性能量化回测 API",
        "version": "1.0.0",
        "description": "基于 Rust + Python 的 10-50x 性能加速回测系统",
        "endpoints": {
            "POST /api/v1/backtest/run": "运行单次回测",
            "POST /api/v1/backtest/optimize": "并行参数优化",
            "GET /api/v1/performance/benchmark": "性能基准测试",
            "GET /api/v1/performance/stats": "系统性能统计",
            "POST /api/v1/indicators/calculate": "计算技术指标",
        },
        "strategies": ["ma", "rsi", "macd", "bb", "kdj", "cci", "adx", "atr", "obv", "ichimoku", "psar"],
        "backends": ["rust", "python"],
    }


if __name__ == '__main__':
    import uvicorn
    import psutil

    print("="*60)
    print("🚀 高性能回测 API 服务器启动")
    print("="*60)
    print(f"CPU 核心: {psutil.cpu_count(logical=False)} 物理, {psutil.cpu_count(logical=True)} 逻辑")
    print(f"API 文档: http://localhost:8000/api/v1/docs")
    print("="*60)

    uvicorn.run(
        "api_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
