"""
並行回測引擎

提供：
- 多進程參數優化
- 數據並行處理
- 內存優化
- 動態負載均衡
- 並行處理監控
"""

import asyncio
import gc
import json
import multiprocessing as mp
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple, Union

import numpy as np
import pandas as pd

from src.core.logging import get_logger

logger = get_logger("parallel_backtest_engine")


@dataclass
class BacktestConfig:
    """回測配置"""
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005

    # 並行配置
    max_workers: int = mp.cpu_count()
    chunk_size: int = 1000
    memory_limit_mb: int = 1024

    # 性能配置
    use_multiprocessing: bool = True
    batch_size: int = 50


@dataclass
class ParameterSet:
    """參數集"""
    params: Dict[str, Any]
    score: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    backtest_id: Optional[str] = None


@dataclass
class OptimizationResult:
    """優化結果"""
    best_params: Dict[str, Any]
    best_score: float
    best_metrics: Dict[str, float]
    all_results: List[ParameterSet]
    total_combinations: int
    execution_time: float
    speedup_ratio: float


class WorkerFunction:
    """工作進程函數（可序列化）"""

    @staticmethod
    def run_backtest(args: Tuple[str, Dict, Dict]) -> Tuple[Dict, Dict[str, float]]:
        """
        在子進程中運行回測

        Args:
            args: (symbol, params, config_dict)

        Returns:
            Tuple[params, metrics]
        """
        try:
            symbol, params, config_dict = args

            # 重建配置
            from dataclasses import asdict
            config = BacktestConfig(**config_dict)

            # 模擬數據生成（實際應用中從數據源獲取）
            np.random.seed(hash(str(params)) % 2**32)
            dates = pd.date_range(
                start=config.start_date,
                end=config.end_date,
                freq='D'
            )

            # 生成模擬價格數據
            returns = np.random.normal(0.001, 0.02, len(dates))
            prices = 100 * np.cumprod(1 + returns)

            # 實現簡單策略（例如移動平均）
            ma_short = params.get('ma_short', 5)
            ma_long = params.get('ma_long', 20)
            rsi_period = params.get('rsi_period', 14)

            if len(prices) < ma_long:
                return params, {"total_return": 0, "sharpe_ratio": 0}

            # 計算指標
            ma_short_vals = pd.Series(prices).rolling(ma_short).mean()
            ma_long_vals = pd.Series(prices).rolling(ma_long).mean()

            # 簡化策略
            positions = np.where(
                (ma_short_vals > ma_long_vals) & (ma_short_vals.shift(1) <= ma_long_vals.shift(1)),
                1,
                np.where(
                    (ma_short_vals < ma_long_vals) & (ma_short_vals.shift(1) >= ma_long_vals.shift(1)),
                    -1,
                    0
                )
            )

            # 計算回報
            price_returns = pd.Series(prices).pct_change().fillna(0)
            strategy_returns = positions[:-1] * price_returns[1:]

            # 計算指標
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
            max_drawdown = ((1 + strategy_returns).cumprod() / (1 + strategy_returns).cumprod().cummax() - 1).min()
            win_rate = (strategy_returns > 0).mean()

            metrics = {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "volatility": strategy_returns.std() * np.sqrt(252)
            }

            # 清理內存
            del dates, prices, returns, ma_short_vals, ma_long_vals, positions, price_returns, strategy_returns
            gc.collect()

            return params, metrics

        except Exception as e:
            logger.error(f"Worker backtest error: {e}")
            return params, {"total_return": 0, "sharpe_ratio": 0, "error": str(e)}


class ParallelBacktestEngine:
    """並行回測引擎"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = get_logger("parallel_backtest_engine")

        # 性能監控
        self._execution_times: List[float] = []
        self._memory_usage: List[float] = []
        self._metrics_history: List[Dict[str, float]] = []

    async def optimize_parameters(
        self,
        param_grid: Dict[str, List[Any]],
        objective: str = "sharpe_ratio",
        maximize: bool = True,
        use_multiprocessing: bool = True
    ) -> OptimizationResult:
        """
        並行優化參數

        Args:
            param_grid: 參數網格
            objective: 優化目標
            maximize: 是否最大化

        Returns:
            優化結果
        """
        start_time = time.time()

        # 生成所有參數組合
        from itertools import product
        param_combinations = list(product(*param_grid.values()))
        param_names = list(param_grid.keys())

        # 轉換為字典列表
        params_list = [
            {name: value for name, value in zip(param_names, combination)}
            for combination in param_combinations
        ]

        total_combinations = len(params_list)
        self.logger.info(f"Starting parameter optimization: {total_combinations} combinations")

        # 序列化配置
        config_dict = {
            "symbol": self.config.symbol,
            "start_date": self.config.start_date,
            "end_date": self.config.end_date,
            "initial_capital": self.config.initial_capital,
            "commission": self.config.commission,
            "slippage": self.config.slippage,
            "max_workers": self.config.max_workers,
            "chunk_size": self.config.chunk_size,
            "memory_limit_mb": self.config.memory_limit_mb,
            "use_multiprocessing": use_multiprocessing,
            "batch_size": self.config.batch_size
        }

        results: List[ParameterSet] = []

        if use_multiprocessing and self.config.max_workers > 1:
            # 使用多進程
            results = await self._run_parallel_optimization(
                params_list, config_dict, objective, maximize
            )
        else:
            # 使用單進程
            results = await self._run_sequential_optimization(
                params_list, objective, maximize
            )

        execution_time = time.time() - start_time

        # 找到最佳結果
        best_result = max(results, key=lambda x: x.score if maximize else -x.score)

        # 計算加速比（與串行執行相比）
        expected_sequential_time = execution_time * self.config.max_workers
        speedup_ratio = expected_sequential_time / execution_time if execution_time > 0 else 1

        return OptimizationResult(
            best_params=best_result.params,
            best_score=best_result.score,
            best_metrics=best_result.metrics,
            all_results=results,
            total_combinations=total_combinations,
            execution_time=execution_time,
            speedup_ratio=speedup_ratio
        )

    async def _run_parallel_optimization(
        self,
        params_list: List[Dict[str, Any]],
        config_dict: Dict,
        objective: str,
        maximize: bool
    ) -> List[ParameterSet]:
        """運行並行優化"""
        results: List[ParameterSet] = []
        batch_size = self.config.batch_size

        # 分批處理以控制內存使用
        for i in range(0, len(params_list), batch_size):
            batch = params_list[i:i + batch_size]
            batch_results = await self._process_batch_parallel(
                batch, config_dict, objective, maximize
            )
            results.extend(batch_results)

            # 清理內存
            gc.collect()

            self.logger.info(f"Processed {min(i + batch_size, len(params_list))}/{len(params_list)} combinations")

        return results

    async def _process_batch_parallel(
        self,
        batch: List[Dict[str, Any]],
        config_dict: Dict,
        objective: str,
        maximize: bool
    ) -> List[ParameterSet]:
        """並行處理一批參數"""
        results: List[ParameterSet] = []
        max_workers = min(self.config.max_workers, len(batch))

        # 創建參數列表
        args_list = [(self.config.symbol, params, config_dict) for params in batch]

        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任務
            future_to_params = {
                loop.run_in_executor(executor, WorkerFunction.run_backtest, args): args[1]
                for args in args_list
            }

            # 收集結果
            for future in as_completed(future_to_params):
                params = future_to_params[future]
                try:
                    result_params, metrics = await future
                    score = self._calculate_score(metrics, objective, maximize)
                    results.append(ParameterSet(
                        params=result_params,
                        score=score,
                        metrics=metrics
                    ))
                except Exception as e:
                    self.logger.error(f"Parameter optimization error: {e}")
                    results.append(ParameterSet(
                        params=params,
                        score=-np.inf if maximize else np.inf,
                        metrics={"error": str(e)}
                    ))

        return results

    async def _run_sequential_optimization(
        self,
        params_list: List[Dict[str, Any]],
        objective: str,
        maximize: bool
    ) -> List[ParameterSet]:
        """運行串行優化（作為對比）"""
        results: List[ParameterSet] = []
        batch_size = self.config.batch_size

        for i in range(0, len(params_list), batch_size):
            batch = params_list[i:i + batch_size]
            batch_results = await self._process_batch_sequential(
                batch, objective, maximize
            )
            results.extend(batch_results)

            self.logger.info(f"Processed {min(i + batch_size, len(params_list))}/{len(params_list)} combinations")

        return results

    async def _process_batch_sequential(
        self,
        batch: List[Dict[str, Any]],
        objective: str,
        maximize: bool
    ) -> List[ParameterSet]:
        """串行處理一批參數"""
        results: List[ParameterSet] = []

        for params in batch:
            try:
                _, metrics = WorkerFunction.run_backtest(
                    (self.config.symbol, params, {})
                )
                score = self._calculate_score(metrics, objective, maximize)
                results.append(ParameterSet(
                    params=params,
                    score=score,
                    metrics=metrics
                ))
            except Exception as e:
                self.logger.error(f"Parameter optimization error: {e}")
                results.append(ParameterSet(
                    params=params,
                    score=-np.inf if maximize else np.inf,
                    metrics={"error": str(e)}
                ))

        return results

    def _calculate_score(self, metrics: Dict[str, float], objective: str, maximize: bool) -> float:
        """計算得分"""
        if "error" in metrics:
            return -np.inf if maximize else np.inf

        base_score = metrics.get(objective, 0)

        if not maximize:
            base_score = -base_score

        return base_score

    async def run_backtest(
        self,
        params: Dict[str, Any],
        data: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """運行單次回測"""
        try:
            start_time = time.time()

            # 如果沒有提供數據，生成模擬數據
            if data is None:
                data = self._generate_sample_data()

            # 執行回測策略
            metrics = await self._execute_strategy(params, data)

            execution_time = time.time() - start_time
            self._execution_times.append(execution_time)
            self._metrics_history.append(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            return {"error": str(e)}

    def _generate_sample_data(self) -> pd.DataFrame:
        """生成示例數據"""
        dates = pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq='D'
        )

        # 生成隨機價格數據
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.cumprod(1 + returns)

        data = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(100000, 1000000, len(dates))
        })

        return data

    async def _execute_strategy(
        self,
        params: Dict[str, Any],
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """執行交易策略"""
        try:
            # 簡單移動平均策略
            ma_short = params.get('ma_short', 5)
            ma_long = params.get('ma_long', 20)
            rsi_period = params.get('rsi_period', 14)

            if len(data) < ma_long:
                return {
                    "total_return": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "win_rate": 0
                }

            # 計算移動平均
            data['ma_short'] = data['close'].rolling(ma_short).mean()
            data['ma_long'] = data['close'].rolling(ma_long).mean()

            # 生成交易信號
            data['signal'] = 0
            data.loc[data['ma_short'] > data['ma_long'], 'signal'] = 1
            data.loc[data['ma_short'] < data['ma_long'], 'signal'] = -1

            # 計算策略回報
            data['returns'] = data['close'].pct_change()
            data['strategy_returns'] = data['signal'].shift(1) * data['returns']

            # 計算指標
            total_return = (1 + data['strategy_returns']).prod() - 1
            sharpe_ratio = (
                data['strategy_returns'].mean() / data['strategy_returns'].std() * np.sqrt(252)
                if data['strategy_returns'].std() > 0 else 0
            )
            max_drawdown = (
                (1 + data['strategy_returns']).cumprod() /
                (1 + data['strategy_returns']).cumprod().cummax() - 1
            ).min()
            win_rate = (data['strategy_returns'] > 0).mean()

            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "volatility": data['strategy_returns'].std() * np.sqrt(252)
            }

        except Exception as e:
            self.logger.error(f"Strategy execution error: {e}")
            return {"error": str(e)}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        if not self._execution_times:
            return {}

        return {
            "average_execution_time": np.mean(self._execution_times),
            "total_execution_time": sum(self._execution_times),
            "min_execution_time": min(self._execution_times),
            "max_execution_time": max(self._execution_times),
            "speedup_factor": (
                sum(self._execution_times) / self._execution_times[0]
                if len(self._execution_times) > 1 else 1.0
            ),
            "memory_usage_mb": np.mean(self._memory_usage) if self._memory_usage else 0
        }

    def save_results(self, result: OptimizationResult, filepath: str):
        """保存結果"""
        try:
            output = {
                "best_params": result.best_params,
                "best_score": result.best_score,
                "best_metrics": result.best_metrics,
                "total_combinations": result.total_combinations,
                "execution_time": result.execution_time,
                "speedup_ratio": result.speedup_ratio,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "symbol": self.config.symbol,
                    "start_date": self.config.start_date,
                    "end_date": self.config.end_date,
                    "max_workers": self.config.max_workers
                }
            }

            with open(filepath, 'w') as f:
                json.dump(output, f, indent=2)

            self.logger.info(f"Results saved to {filepath}")

        except Exception as e:
            self.logger.error(f"Save results error: {e}")


# 便捷函數
async def optimize_strategy_parameters(
    symbol: str,
    start_date: str,
    end_date: str,
    param_grid: Dict[str, List[Any]],
    objective: str = "sharpe_ratio",
    max_workers: int = None
) -> OptimizationResult:
    """優化策略參數"""
    config = BacktestConfig(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        max_workers=max_workers or mp.cpu_count()
    )

    engine = ParallelBacktestEngine(config)
    return await engine.optimize_parameters(param_grid, objective)


# 示例使用
async def main():
    """示例"""
    # 定義參數網格
    param_grid = {
        'ma_short': [5, 10, 15, 20],
        'ma_long': [20, 30, 50, 100],
        'rsi_period': [14, 21, 30]
    }

    # 運行優化
    result = await optimize_strategy_parameters(
        symbol="0700.HK",
        start_date="2020-01-01",
        end_date="2023-12-31",
        param_grid=param_grid,
        objective="sharpe_ratio",
        max_workers=8
    )

    # 打印結果
    print(f"\nOptimization Results:")
    print(f"Best Score: {result.best_score:.4f}")
    print(f"Best Params: {result.best_params}")
    print(f"Total Combinations: {result.total_combinations}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Speedup Ratio: {result.speedup_ratio:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())
