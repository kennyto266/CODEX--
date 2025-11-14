"""
回测引擎API端点
提供策略回测和优化功能
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.insert(0, 'src')

import structlog
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.backtest.python_engine import PythonBacktestEngine

logger = structlog.get_logger("api.backtest")

router = APIRouter()


class BacktestRequest(BaseModel):
    """回测请求模型"""
    symbol: str = Field(..., description="股票代码，如：0700.HK")
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    strategy: str = Field(..., description="策略类型，如：kdj, rsi, macd")
    initial_capital: float = Field(100000.0, description="初始资金")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="策略参数"
    )


class BatchBacktestRequest(BaseModel):
    """批量回测请求模型"""
    symbols: List[str] = Field(..., description="股票代码列表", min_length=1)
    strategy: str = Field(default="rsi", description="策略类型")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    initial_capital: float = Field(1000000.0, description="初始资金")
    max_workers: int = Field(4, ge=1, le=16, description="并行工作线程数")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="策略参数"
    )


class BacktestResult(BaseModel):
    """回测结果模型"""
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    final_value: float
    parameters: Dict[str, Any]


@router.post(
    "/run",
    response_model=BacktestResult,
    summary="运行策略回测",
    description="根据指定策略和参数运行回测分析",
)
async def run_backtest(request: BacktestRequest) -> BacktestResult:
    """
    运行策略回测

    - **symbol**: 股票代码（港股格式，如0700.HK）
    - **start_date**: 回测开始日期
    - **end_date**: 回测结束日期
    - **strategy**: 策略类型（kdj, rsi, macd, ma, bb等）
    - **initial_capital**: 初始资金，默认10万元
    - **parameters**: 策略参数（可选）
    """
    try:
        logger.info(
            "backtest_start",
            symbol=request.symbol,
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # Generate realistic stock data
        market_data = _generate_realistic_stock_data(request.symbol)

        # Create backtest engine
        engine = PythonBacktestEngine(
            initial_capital=request.initial_capital,
            commission=0.001
        )

        # Run backtest with actual engine
        backtest_result = engine.run_backtest(
            data=market_data,
            strategy_type=request.strategy,
            params=request.parameters
        )

        # Calculate final value
        final_value = request.initial_capital * (1 + backtest_result.total_return)

        # Create response
        result = BacktestResult(
            strategy=request.strategy,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            total_return=backtest_result.total_return * 100,  # Convert to percentage
            annualized_return=backtest_result.annualized_return * 100,  # Convert to percentage
            sharpe_ratio=backtest_result.sharpe_ratio,
            max_drawdown=backtest_result.max_drawdown * 100,  # Convert to percentage
            win_rate=backtest_result.win_rate * 100,  # Convert to percentage
            trades_count=backtest_result.total_trades,
            final_value=final_value,
            parameters=request.parameters or {},
        )

        logger.info("backtest_complete", symbol=request.symbol, sharpe_ratio=result.sharpe_ratio)

        return result

    except Exception as e:
        # Use repr() to avoid encoding issues
        error_type = type(e).__name__
        error_msg = repr(e)
        logger.error("backtest_failed", error_type=error_type, error=error_msg)
        raise HTTPException(status_code=500, detail=f"Backtest failed: {error_type}: {error_msg}")


@router.get(
    "/backtest/optimize",
    response_model=List[BacktestResult],
    summary="策略参数优化",
    description="自动搜索最优策略参数",
)
async def optimize_strategy(
    symbol: str = Query(..., description="股票代码"),
    strategy: str = Query(..., description="策略类型"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    max_workers: int = Query(8, description="并行工作线程数"),
) -> List[BacktestResult]:
    """
    策略参数优化

    自动搜索指定策略的最优参数组合
    """
    try:
        logger.info(
            "optimization_start",
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            max_workers=max_workers,
        )

        # TODO: Call actual optimization engine
        # Return mock optimization results
        results = [
            BacktestResult(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                total_return=15.67,
                annualized_return=8.32,
                sharpe_ratio=1.23,
                max_drawdown=-5.45,
                win_rate=62.5,
                trades_count=48,
                final_value=115670.0,
                parameters={"k_period": 9, "d_period": 3, "oversold": 20, "overbought": 80},
            ),
            BacktestResult(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                total_return=14.23,
                annualized_return=7.65,
                sharpe_ratio=1.15,
                max_drawdown=-6.12,
                win_rate=60.4,
                trades_count=52,
                final_value=114230.0,
                parameters={"k_period": 12, "d_period": 3, "oversold": 25, "overbought": 75},
            ),
        ]

        logger.info("optimization_complete", results_count=len(results))

        return results

    except Exception as e:
        logger.error("optimization_failed", error=repr(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {repr(e)}")


@router.get(
    "/backtest/strategies",
    response_model=List[str],
    summary="获取可用策略列表",
    description="返回所有支持的回测策略类型",
)
async def get_strategies() -> List[str]:
    """
    获取支持的策略列表
    """
    strategies = [
        "kdj",
        "rsi",
        "macd",
        "ma",
        "bb",
        "cci",
        "adx",
        "atr",
        "obv",
        "ichimoku",
        "sar",
    ]

    return strategies


@router.get(
    "/backtest/history",
    response_model=List[BacktestResult],
    summary="获取历史回测记录",
    description="分页获取历史回测结果",
)
async def get_backtest_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> List[BacktestResult]:
    """
    获取历史回测记录

    支持分页查询
    """
    # TODO: 从数据库查询历史记录
    # 暂时返回空列表
    return []


def _generate_realistic_stock_data(symbol: str, days: int = 252) -> List[Dict[str, Any]]:
    """
    生成逼真的股票模拟数据

    Args:
        symbol: 股票代码
        days: 生成天数

    Returns:
        市场数据列表
    """
    np.random.seed(hash(symbol) % (2**32))

    # 生成价格序列（几何布朗运动）
    returns = np.random.normal(0.0005, 0.02, days)
    prices = 100.0 * np.cumprod(1 + returns)

    # 生成OHLC数据
    open_price = np.roll(prices, 1)
    open_price[0] = prices[0]

    daily_vol = 0.01
    high = prices * (1 + np.abs(np.random.normal(0, daily_vol, days)))
    low = prices * (1 - np.abs(np.random.normal(0, daily_vol, days)))

    # 确保OHLC关系正确
    for i in range(days):
        high[i] = max(high[i], prices[i], open_price[i])
        low[i] = min(low[i], prices[i], open_price[i])

    volume = np.random.randint(1000000, 10000000, days)

    # 构建市场数据
    market_data = []
    base_date = date.today() - timedelta(days=days)

    for i in range(days):
        market_data.append({
            'timestamp': (base_date + timedelta(days=i)).isoformat(),
            'open': float(open_price[i]),
            'high': float(high[i]),
            'low': float(low[i]),
            'close': float(prices[i]),
            'volume': int(volume[i])
        })

    return market_data


def _run_single_backtest(
    symbol: str,
    strategy: str,
    initial_capital: float,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    执行单个股票的回测

    Args:
        symbol: 股票代码
        strategy: 策略类型
        initial_capital: 初始资金
        params: 策略参数

    Returns:
        回测结果字典
    """
    try:
        # 生成模拟数据
        market_data = _generate_realistic_stock_data(symbol)

        # 创建回测引擎
        engine = PythonBacktestEngine(
            initial_capital=initial_capital,
            commission=0.001
        )

        # 执行回测
        result = engine.run_backtest(
            data=market_data,
            strategy_type=strategy,
            params=params
        )

        # 根据PythonBacktestResult的实际属性计算
        profit_trades = int(result.total_trades * result.win_rate) if result.total_trades > 0 else 0
        loss_trades = result.total_trades - profit_trades
        final_value = initial_capital * (1 + result.total_return)

        return {
            'symbol': symbol,
            'strategy': strategy,
            'status': 'SUCCESS',
            'total_return': result.total_return,
            'annualized_return': result.annualized_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'profit_trades': profit_trades,
            'loss_trades': loss_trades,
            'final_value': final_value,
            'execution_time_ms': result.execution_time_ms
        }

    except Exception as e:
        logger.error("single_backtest_failed", symbol=symbol, error=str(e))
        return {
            'symbol': symbol,
            'strategy': strategy,
            'status': 'FAILED',
            'error': str(e),
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0
        }


@router.post(
    "/batch",
    summary="批量回测",
    description="对多个股票同时执行回测，支持并行处理，计算Sharpe Ratio和Max Drawdown",
)
async def run_batch_backtest(request: BatchBacktestRequest) -> Dict[str, Any]:
    """
    批量回测多个股票

    - **symbols**: 股票代码列表
    - **strategy**: 策略类型（rsi, macd, ma, bb, kdj等）
    - **initial_capital**: 初始资金
    - **max_workers**: 并行线程数
    - **parameters**: 策略参数（可选）

    返回所有股票的回测结果，包含：
    - Sharpe Ratio（夏普比率）
    - Max Drawdown（最大回撤）
    - 总收益率
    - 交易次数
    """
    try:
        logger.info(
            "batch_backtest_start",
            symbols_count=len(request.symbols),
            strategy=request.strategy,
            max_workers=request.max_workers
        )

        start_time = datetime.now()
        results = []

        # 使用线程池并行执行回测
        with ThreadPoolExecutor(max_workers=request.max_workers) as executor:
            # 提交所有回测任务
            future_to_symbol = {
                executor.submit(
                    _run_single_backtest,
                    symbol,
                    request.strategy,
                    request.initial_capital,
                    request.parameters
                ): symbol
                for symbol in request.symbols
            }

            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(
                        "symbol_backtest_complete",
                        symbol=symbol,
                        sharpe_ratio=result.get('sharpe_ratio', 0),
                        max_drawdown=result.get('max_drawdown', 0)
                    )
                except Exception as e:
                    logger.error(f"symbol_backtest_error", symbol=symbol, error=str(e))
                    results.append({
                        'symbol': symbol,
                        'strategy': request.strategy,
                        'status': 'ERROR',
                        'error': str(e)
                    })

        # 计算统计信息
        successful_results = [r for r in results if r.get('status') == 'SUCCESS']

        execution_time = (datetime.now() - start_time).total_seconds()

        summary = {
            'total_symbols': len(request.symbols),
            'successful': len(successful_results),
            'failed': len(results) - len(successful_results),
            'avg_sharpe_ratio': float(np.mean([r['sharpe_ratio'] for r in successful_results])) if successful_results else 0,
            'avg_max_drawdown': float(np.mean([r['max_drawdown'] for r in successful_results])) if successful_results else 0,
            'avg_return': float(np.mean([r['total_return'] for r in successful_results])) if successful_results else 0,
            'execution_time_seconds': round(execution_time, 2)
        }

        logger.info(
            "batch_backtest_complete",
            total=len(results),
            successful=len(successful_results),
            execution_time=execution_time
        )

        return {
            'success': True,
            'message': f'Batch backtest complete: {len(successful_results)}/{len(request.symbols)} successful',
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error("batch_backtest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch backtest execution failed: {str(e)}")
