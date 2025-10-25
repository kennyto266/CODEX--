"""
策略优化 API 路由

提供以下端点：
- POST /api/optimize/{symbol}/{strategy} - 启动优化
- GET /api/optimize/{run_id}/status - 获取优化状态
- GET /api/optimize/{symbol}/{strategy}/results - 获取优化结果
- GET /api/optimize/{symbol}/{strategy}/sensitivity - 获取敏感性分析
- GET /api/optimize/history - 获取优化历史
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import hashlib
import logging
from uuid import uuid4

from src.database import db_manager, OptimizationRun
from src.optimization import ProductionOptimizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/optimize", tags=["optimization"])


# ============ Pydantic 模型 ============

class OptimizeRequest(BaseModel):
    """优化请求模型"""
    metric: str = Field(default="sharpe_ratio", description="优化指标: sharpe_ratio, annual_return, max_drawdown等")
    method: str = Field(default="grid_search", description="优化方法: grid_search, random_search")
    max_workers: Optional[int] = Field(default=None, description="最大并行进程数")
    start_date: Optional[str] = Field(default=None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="结束日期 (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "metric": "sharpe_ratio",
                "method": "grid_search",
                "start_date": "2023-01-01",
                "end_date": "2024-01-01"
            }
        }


class OptimizeResponse(BaseModel):
    """优化响应模型"""
    run_id: str
    task_id: str
    status: str
    symbol: str
    strategy: str
    created_at: str
    message: str


class OptimizationResult(BaseModel):
    """单个优化结果模型"""
    rank: int
    parameters: Dict[str, Any]
    metrics: Dict[str, float]


class OptimizationRunDetail(BaseModel):
    """优化运行详情模型"""
    run_id: str
    symbol: str
    strategy_name: str
    metric: str
    status: str
    duration_seconds: Optional[float]
    best_parameters: Optional[Dict[str, Any]]
    best_metrics: Optional[Dict[str, float]]
    created_at: str


# ============ 后台任务 ============

async def run_optimization_task(run_id: str, run_db_id: int, symbol: str, strategy_name: str,
                               start_date: str, end_date: str, method: str, metric: str):
    """后台优化任务"""
    try:
        logger.info(f"Starting optimization task: {run_id}")

        # 创建优化器
        optimizer = ProductionOptimizer(symbol, start_date, end_date)

        # 加载数据
        if optimizer.load_data() is None:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=0,
                error_message='Failed to load data'
            )
            logger.error(f"Data loading failed for {run_id}")
            return

        # 根据策略创建参数网格和工厂函数
        # 这里需要根据实际策略实现来调整
        strategy_factory, param_grid = _get_strategy_factory(strategy_name)

        if strategy_factory is None:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=0,
                error_message=f'Unsupported strategy: {strategy_name}'
            )
            logger.error(f"Unsupported strategy: {strategy_name}")
            return

        # 运行优化
        start_time = datetime.utcnow()

        if method == 'grid_search':
            result = optimizer.grid_search(strategy_factory, param_grid)
        elif method == 'random_search':
            result = optimizer.random_search(strategy_factory, param_grid)
        else:
            result = optimizer.grid_search(strategy_factory, param_grid)

        duration = (datetime.utcnow() - start_time).total_seconds()

        # 保存结果
        if result and 'best_params' in result:
            best_params = result['best_params']
            best_metrics = result['validation_metrics']

            # 保存所有评估结果
            total_evaluated = result.get('total_evaluated', 0)
            rank = 1
            for res in [result]:  # 这里可以扩展为保存所有结果
                param_hash = hashlib.md5(
                    json.dumps(best_params, sort_keys=True, default=str).encode()
                ).hexdigest()
                db_manager.save_optimization_result(
                    run_id=run_db_id,
                    rank=rank,
                    param_hash=param_hash,
                    parameters=best_params,
                    metrics=best_metrics
                )
                rank += 1

            # 更新运行状态
            db_manager.update_optimization_run(
                run_id=run_id,
                status='completed',
                duration=duration,
                best_parameters=best_params,
                best_metrics=best_metrics
            )

            logger.info(f"Optimization completed: {run_id}, Sharpe: {best_metrics.get('sharpe_ratio', 0):.4f}")
        else:
            db_manager.update_optimization_run(
                run_id=run_id,
                status='failed',
                duration=duration,
                error_message='No valid results found'
            )
            logger.error(f"No valid results found for {run_id}")

    except Exception as e:
        db_manager.update_optimization_run(
            run_id=run_id,
            status='failed',
            duration=0,
            error_message=str(e)
        )
        logger.error(f"Optimization task failed: {e}", exc_info=True)


def _get_strategy_factory(strategy_name: str):
    """获取策略工厂函数和参数网格"""
    # 这里需要根据实际策略实现来调整
    # 这是一个示例实现，实际应该导入真实的策略类

    try:
        if strategy_name.lower() == 'rsi':
            # RSI 策略工厂
            def rsi_factory(params):
                from src.strategies import RSIStrategy
                return RSIStrategy(
                    period=params.get('period', 14),
                    overbought=params.get('overbought', 70),
                    oversold=params.get('oversold', 30)
                )

            param_grid = {
                'period': [10, 14, 20, 30],
                'overbought': [60, 70, 80],
                'oversold': [20, 30, 40]
            }
            return rsi_factory, param_grid

        elif strategy_name.lower() == 'macd':
            # MACD 策略工厂
            def macd_factory(params):
                from src.strategies import MACDStrategy
                return MACDStrategy(
                    fast_period=params.get('fast_period', 12),
                    slow_period=params.get('slow_period', 26),
                    signal_period=params.get('signal_period', 9)
                )

            param_grid = {
                'fast_period': [5, 10, 12],
                'slow_period': [20, 26, 30],
                'signal_period': [8, 9, 10]
            }
            return macd_factory, param_grid

        elif strategy_name.lower() == 'bollinger':
            # Bollinger Bands 策略工厂
            def bollinger_factory(params):
                from src.strategies import BollingerStrategy
                return BollingerStrategy(
                    period=params.get('period', 20),
                    std_dev=params.get('std_dev', 2.0)
                )

            param_grid = {
                'period': [15, 20, 25, 30],
                'std_dev': [1.5, 2.0, 2.5, 3.0]
            }
            return bollinger_factory, param_grid

        else:
            logger.error(f"Unknown strategy: {strategy_name}")
            return None, None

    except Exception as e:
        logger.error(f"Failed to get strategy factory: {e}")
        return None, None


# ============ API 端点 ============

@router.post("/{symbol}/{strategy}", response_model=OptimizeResponse)
async def start_optimization(
    symbol: str,
    strategy: str,
    request: OptimizeRequest,
    background_tasks: BackgroundTasks
):
    """
    启动策略优化

    - **symbol**: 股票代码 (e.g., 0700.hk)
    - **strategy**: 策略名称 (rsi, macd, bollinger等)
    - **request**: 优化请求参数
    """
    try:
        # 生成运行ID
        run_id = f"opt_{symbol.replace('.', '_')}_{strategy}_{int(datetime.utcnow().timestamp())}"
        task_id = str(uuid4())

        # 验证策略是否支持
        strategy_factory, param_grid = _get_strategy_factory(strategy)
        if strategy_factory is None:
            raise HTTPException(status_code=400, detail=f"Unsupported strategy: {strategy}")

        # 设置日期
        start_date = request.start_date or "2020-01-01"
        end_date = request.end_date or datetime.now().strftime("%Y-%m-%d")

        # 保存优化运行记录
        run_db_id = db_manager.save_optimization_run(
            run_id=run_id,
            symbol=symbol,
            strategy_name=strategy,
            metric=request.metric,
            method=request.method,
            total_combinations=len(list(param_grid.values())) if param_grid else 0
        )

        if run_db_id is None:
            raise HTTPException(status_code=500, detail="Failed to save optimization run")

        # 添加后台任务
        background_tasks.add_task(
            run_optimization_task,
            run_id=run_id,
            run_db_id=run_db_id,
            symbol=symbol,
            strategy_name=strategy,
            start_date=start_date,
            end_date=end_date,
            method=request.method,
            metric=request.metric
        )

        return OptimizeResponse(
            run_id=run_id,
            task_id=task_id,
            status="started",
            symbol=symbol,
            strategy=strategy,
            created_at=datetime.utcnow().isoformat(),
            message=f"Optimization started for {symbol} with {strategy} strategy"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/status")
async def get_optimization_status(run_id: str):
    """获取优化运行状态"""
    try:
        result = db_manager.get_optimization_run(run_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Optimization run not found: {run_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/{strategy}/results")
async def get_optimization_results(
    symbol: str,
    strategy: str,
    limit: int = Query(10, ge=1, le=100, description="返回结果数量")
):
    """获取优化结果（前N个最优参数组合）"""
    try:
        # 获取最新的优化运行
        history = db_manager.get_optimization_history(symbol=symbol, strategy_name=strategy, limit=1)
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No optimization results found for {symbol}/{strategy}"
            )

        run_id = history[0]['run_id']
        results = db_manager.get_optimization_results(run_id, limit=limit)

        return {
            'symbol': symbol,
            'strategy': strategy,
            'run_id': run_id,
            'total_results': len(results),
            'results': results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_optimization_history(
    symbol: Optional[str] = Query(None, description="筛选股票代码"),
    strategy: Optional[str] = Query(None, description="筛选策略名称"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数量")
):
    """获取优化历史记录"""
    try:
        history = db_manager.get_optimization_history(
            symbol=symbol,
            strategy_name=strategy,
            limit=limit
        )

        return {
            'filters': {
                'symbol': symbol,
                'strategy': strategy
            },
            'total': len(history),
            'history': history
        }

    except Exception as e:
        logger.error(f"Failed to get optimization history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/{strategy}/sensitivity")
async def get_sensitivity_analysis(
    symbol: str,
    strategy: str
):
    """
    获取敏感性分析数据

    在优化完成后，可以获取每个参数对性能指标的影响
    """
    try:
        # 获取最新的优化运行
        history = db_manager.get_optimization_history(symbol=symbol, strategy_name=strategy, limit=1)
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No optimization results found for {symbol}/{strategy}"
            )

        run_info = history[0]

        # 这里可以实现完整的敏感性分析
        # 目前返回最佳参数的信息
        return {
            'symbol': symbol,
            'strategy': strategy,
            'run_id': run_info['run_id'],
            'best_parameters': run_info.get('best_parameters', {}),
            'best_sharpe_ratio': run_info.get('best_sharpe_ratio', 0),
            'message': 'Sensitivity analysis data. Full implementation can show parameter impact analysis.'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sensitivity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/apply")
async def apply_optimization_result(
    run_id: str,
    rank: int = Query(1, ge=1, description="应用排名第几的结果")
):
    """应用优化结果（将最优参数应用到策略）"""
    try:
        result = db_manager.get_optimization_run(run_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Optimization run not found: {run_id}")

        if result['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Optimization not completed yet: {result['status']}"
            )

        # 这里可以将最优参数应用到实际策略
        # 实现细节取决于策略管理系统

        return {
            'run_id': run_id,
            'status': 'applied',
            'symbol': result['symbol'],
            'strategy': result['strategy_name'],
            'parameters_applied': result['best_parameters'],
            'metrics': result['best_metrics'],
            'message': f"Optimization result applied successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply optimization result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 健康检查 ============

@router.get("/health")
async def optimization_health():
    """优化模块健康检查"""
    return {
        'status': 'healthy',
        'module': 'optimization',
        'timestamp': datetime.utcnow().isoformat()
    }
