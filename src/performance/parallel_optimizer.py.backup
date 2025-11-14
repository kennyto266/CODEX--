"""
🚀 并行参数优化器

使用 Rayon 和 Tokio 实现极致并行性能：
- 自动 CPU 核心检测
- 智能工作分派算法
- 内存使用监控
- 性能统计与报告
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from collections import defaultdict
import numpy as np
import pandas as pd
import psutil

from .acceleration import get_accelerator, PerformanceConfig

logger = logging.getLogger(__name__)

@dataclass
class OptimizationJob:
    """优化任务"""
    job_id: str
    strategy_type: str
    parameters: Dict[str, float]
    data_subset: Optional[pd.DataFrame] = None
    priority: int = 0


@dataclass
class OptimizationResult:
    """优化结果"""
    job_id: str
    score: float
    metrics: Dict[str, Any]
    execution_time_ms: float
    parameters: Dict[str, float]
    rank: Optional[int] = None


class ParallelOptimizer:
    """并行参数优化器"""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.job_results: Dict[str, OptimizationResult] = {}
        self.performance_stats = defaultdict(list)
        self.memory_monitor = MemoryMonitor()

        logger.info(f"🚀 并行优化器初始化")
        logger.info(f"   - 最大工作进程: {self.max_workers}")
        logger.info(f"   - CPU 核心数: {mp.cpu_count()}")

    def optimize(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        param_ranges: Dict[str, List[float]],
        metric: str = 'sharpe_ratio',
        max_combinations: int = 10000,
    ) -> Dict[str, Any]:
        """并行参数优化"""

        # 生成参数组合
        from itertools import product
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))

        if len(combinations) > max_combinations:
            logger.warning(f"参数组合过多 ({len(combinations)}), 采样 {max_combinations}")
            combinations = combinations[:max_combinations]

        logger.info(f"开始并行优化: {len(combinations)} 个组合")
        start_time = time.time()

        # 批量分派
        job_batches = self._create_job_batches(
            combinations, param_names, strategy_type
        )

        # 并行执行
        all_results = []
        for batch in job_batches:
            batch_results = self._execute_batch(batch, data)
            all_results.extend(batch_results)

        # 排序和排名
        all_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(all_results):
            result.rank = i + 1

        # 性能统计
        total_time = (time.time() - start_time) * 1000
        throughput = len(all_results) / (total_time / 1000.0)

        self.performance_stats['total_jobs'].append(len(all_results))
        self.performance_stats['total_time_ms'].append(total_time)
        self.performance_stats['throughput'].append(throughput)

        logger.info(f"✅ 优化完成")
        logger.info(f"   - 总时间: {total_time:.2f}ms")
        logger.info(f"   - 吞吐量: {throughput:.2f} 组合/秒")
        logger.info(f"   - 平均时间: {total_time/len(all_results):.2f}ms/组合")

        return {
            'best_result': all_results[0] if all_results else None,
            'all_results': all_results,
            'statistics': {
                'total_combinations': len(all_results),
                'total_time_ms': total_time,
                'throughput_per_second': throughput,
                'avg_time_per_combination_ms': total_time / len(all_results) if all_results else 0,
                'peak_memory_mb': self.memory_monitor.get_peak_memory(),
            },
            'performance': dict(self.performance_stats),
        }

    def _create_job_batches(
        self,
        combinations: List[Tuple[float, ...]],
        param_names: List[str],
        strategy_type: str,
    ) -> List[List[OptimizationJob]]:
        """创建工作批次"""
        batch_size = max(1, len(combinations) // self.max_workers)
        batches = []

        for i in range(0, len(combinations), batch_size):
            batch = []
            for combo in combinations[i:i+batch_size]:
                params = dict(zip(param_names, combo))
                job = OptimizationJob(
                    job_id=f"job_{i}_{combo}",
                    strategy_type=strategy_type,
                    parameters=params,
                )
                batch.append(job)
            batches.append(batch)

        logger.info(f"创建 {len(batches)} 个批次, 每批约 {batch_size} 个任务")
        return batches

    def _execute_batch(
        self,
        jobs: List[OptimizationJob],
        data: pd.DataFrame,
    ) -> List[OptimizationResult]:
        """执行一批任务"""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._run_single_job, job, data): job
                for job in jobs
            }

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)

                    # 内存监控
                    current_memory = self.memory_monitor.get_memory_usage()
                    self.memory_monitor.check_threshold(current_memory)

                except Exception as e:
                    job = futures[future]
                    logger.error(f"任务 {job.job_id} 失败: {e}")
                    # 创建错误结果
                    results.append(OptimizationResult(
                        job_id=job.job_id,
                        score=float('-inf'),
                        metrics={'error': str(e)},
                        execution_time_ms=0,
                        parameters=job.parameters,
                    ))

        return results

    def _run_single_job(
        self,
        job: OptimizationJob,
        data: pd.DataFrame,
    ) -> OptimizationResult:
        """运行单个优化任务"""
        start_time = time.time()

        try:
            accelerator = get_accelerator(PerformanceConfig(
                use_rust=True,
                max_workers=1,  # 单任务使用单核
            ))

            result = accelerator.run_backtest(
                data,
                job.strategy_type,
                job.parameters,
            )

            execution_time = (time.time() - start_time) * 1000

            # 提取指标
            score = result['metrics'].get(job.strategy_type, 0.0)
            if job.strategy_type == 'ma':
                score = result['metrics']['sharpe_ratio']

            return OptimizationResult(
                job_id=job.job_id,
                score=score,
                metrics=result['metrics'],
                execution_time_ms=execution_time,
                parameters=job.parameters,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"任务 {job.job_id} 执行错误: {e}")

            return OptimizationResult(
                job_id=job.job_id,
                score=float('-inf'),
                metrics={'error': str(e)},
                execution_time_ms=execution_time,
                parameters=job.parameters,
            )

    def walk_forward_optimization(
        self,
        data: pd.DataFrame,
        strategy_type: str,
        param_ranges: Dict[str, List[float]],
        training_period_days: int = 252,
        testing_period_days: int = 63,
        step_size_days: int = 21,
    ) -> List[Dict[str, Any]]:
        """走步优化"""
        results = []
        total_days = (data.index[-1] - data.index[0]).days

        current_day = 0
        iteration = 0

        while current_day + training_period_days + testing_period_days < total_days:
            iteration += 1
            train_start = current_day
            train_end = current_day + training_period_days
            test_start = train_end
            test_end = test_start + testing_period_days

            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[test_start:test_end]

            logger.info(f"\n迭代 {iteration}:")
            logger.info(f"  训练期: {train_start}-{train_end} ({len(train_data)} 天)")
            logger.info(f"  测试期: {test_start}-{test_end} ({len(test_data)} 天)")

            # 训练期优化
            optimization_result = self.optimize(
                train_data,
                strategy_type,
                param_ranges,
                max_combinations=5000,  # 减少训练期参数
            )

            # 测试期验证
            if optimization_result['best_result']:
                best_params = optimization_result['best_result'].parameters
                accelerator = get_accelerator(PerformanceConfig(use_rust=True))

                test_result = accelerator.run_backtest(test_data, strategy_type, best_params)

                results.append({
                    'iteration': iteration,
                    'training_period': (train_start, train_end),
                    'testing_period': (test_start, test_end),
                    'best_params': best_params,
                    'training_score': optimization_result['best_result'].score,
                    'test_metrics': test_result['metrics'],
                    'optimization_time_ms': optimization_result['statistics']['total_time_ms'],
                })

            current_day += step_size_days

        return results


class MemoryMonitor:
    """内存使用监控"""

    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.peak_memory = 0.0
        self.alerts = []

    def get_memory_usage(self) -> float:
        """获取当前内存使用 (MB)"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def get_peak_memory(self) -> float:
        """获取峰值内存使用"""
        return self.peak_memory

    def check_threshold(self, current_mb: float):
        """检查内存阈值"""
        if current_mb > self.peak_memory:
            self.peak_memory = current_mb

        if current_mb > self.max_memory_mb:
            alert = f"⚠️  内存使用超限: {current_mb:.2f}MB > {self.max_memory_mb}MB"
            logger.warning(alert)
            self.alerts.append({
                'timestamp': time.time(),
                'message': alert,
            })


class WorkerPool:
    """工作进程池管理器"""

    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.workers = []
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()

    def submit_task(self, task_data: Dict[str, Any]):
        """提交任务"""
        self.task_queue.put(task_data)

    def get_result(self) -> Optional[Dict[str, Any]]:
        """获取结果"""
        try:
            return self.result_queue.get(timeout=1)
        except:
            return None

    def shutdown(self):
        """关闭工作池"""
        for _ in range(self.num_workers):
            self.task_queue.put(None)  # 终止信号

        for worker in self.workers:
            worker.join()


def optimize_multiple_strategies(
    data: pd.DataFrame,
    strategies: List[Dict[str, Any]],
    param_ranges: Dict[str, List[float]],
) -> Dict[str, Dict[str, Any]]:
    """多策略并行优化"""
    optimizer = ParallelOptimizer()

    results = {}
    for strategy in strategies:
        strategy_name = strategy['name']
        strategy_type = strategy['type']

        logger.info(f"\n优化策略: {strategy_name} ({strategy_type})")

        result = optimizer.optimize(
            data,
            strategy_type,
            param_ranges,
            max_combinations=10000,
        )

        results[strategy_name] = result

    return results


if __name__ == '__main__':
    # 测试并行优化器
    print("="*60)
    print("🚀 并行优化器测试")
    print("="*60)

    # 生成测试数据
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    data = pd.DataFrame({
        'Open': prices * (1 + np.random.randn(1000) * 0.001),
        'High': prices * (1 + np.random.randn(1000) * 0.002),
        'Low': prices * (1 - np.random.randn(1000) * 0.002),
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 1000),
    }, index=dates)

    # 参数范围
    param_ranges = {
        'fast_period': [5, 10, 20],
        'slow_period': [20, 30, 50],
    }

    # 执行优化
    optimizer = ParallelOptimizer()
    result = optimizer.optimize(
        data,
        'ma',
        param_ranges,
        max_combinations=100,
    )

    print(f"\n最佳结果:")
    print(f"  参数: {result['best_result'].parameters}")
    print(f"  得分: {result['best_result'].score:.4f}")
    print(f"  执行时间: {result['best_result'].execution_time_ms:.2f}ms")
    print(f"\n统计信息:")
    print(f"  总组合数: {result['statistics']['total_combinations']}")
    print(f"  总时间: {result['statistics']['total_time_ms']:.2f}ms")
    print(f"  吞吐量: {result['statistics']['throughput_per_second']:.2f} 组合/秒")
    print(f"  峰值内存: {result['statistics']['peak_memory_mb']:.2f}MB")
