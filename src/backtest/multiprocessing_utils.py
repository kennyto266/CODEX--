"""
多进程工具模块

解决Windows平台多进程序列化问题
使用进程池的标准方法，避免内联函数
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Callable, Any, Optional, List, Tuple
import functools
import pickle


def _worker_function(args):
    """
    标准worker函数，可以被正确序列化

    Args:
        args: (func, args_tuple, kwargs_dict)

    Returns:
        执行结果
    """
    func, args_tuple, kwargs_dict = args
    return func(*args_tuple, **kwargs_dict)


def execute_in_process(
    func: Callable,
    *args,
    max_workers: Optional[int] = None,
    use_threads: bool = False
):
    """
    在进程/线程中执行函数

    Args:
        func: 要执行的函数
        *args: 位置参数
        max_workers: 最大工作进程数/线程数
        use_threads: 如果为True，使用线程池；否则使用进程池

    Returns:
        执行结果
    """
    if max_workers is None:
        max_workers = mp.cpu_count()

    # 选择执行器
    if use_threads:
        executor_class = ThreadPoolExecutor
    else:
        executor_class = ProcessPoolExecutor

    with executor_class(max_workers=max_workers) as executor:
        future = executor.submit(_worker_function, (func, args, {}))
        return future.result()


def batch_execute(
    func: Callable,
    batch_args: List[tuple],
    max_workers: Optional[int] = None,
    use_threads: bool = True
):
    """
    批量执行任务

    Args:
        func: 要执行的函数（必须是全局定义或在模块顶层）
        batch_args: 参数列表，每个元素是参数元组
        max_workers: 最大工作进程数/线程数
        use_threads: 如果为True，使用线程池；否则使用进程池

    Returns:
        执行结果列表
    """
    if max_workers is None:
        max_workers = min(32, (mp.cpu_count() or 1) + 4)

    # 选择执行器
    if use_threads:
        executor_class = ThreadPoolExecutor
    else:
        executor_class = ProcessPoolExecutor

    with executor_class(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = [
            executor.submit(_worker_function, (func, arg, {}))
            for arg in batch_args
        ]

        # 收集结果
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                results.append(None)

        return results


def safe_multiprocessing_executor(max_workers: Optional[int] = None):
    """
    创建安全的多进程执行器

    总是使用spawn方法，确保跨平台兼容性

    Args:
        max_workers: 最大工作进程数

    Returns:
        ProcessPoolExecutor实例
    """
    if max_workers is None:
        max_workers = mp.cpu_count()

    # 使用spawn上下文
    ctx = mp.get_context('spawn')
    return ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx)


# 预定义的worker函数
def simple_math_worker(x: int) -> int:
    """简单的数学计算worker"""
    return x ** 2


def sum_worker(data: List[float]) -> float:
    """求和worker"""
    return sum(data)


def backtest_worker(config_tuple):
    """
    回测worker函数（示例）

    Args:
        config_tuple: (symbol, params, config_dict)

    Returns:
        (params, metrics)
    """
    try:
        symbol, params, config_dict = config_tuple

        # 这里应该是实际的回测逻辑
        # 为了简化，返回模拟结果
        import random
        metrics = {
            'total_return': random.uniform(-0.1, 0.3),
            'sharpe_ratio': random.uniform(0, 2),
            'max_drawdown': random.uniform(-0.2, 0),
            'win_rate': random.uniform(0.3, 0.8)
        }

        return params, metrics

    except Exception as e:
        return None, {'error': str(e)}


# 便捷函数
def run_backtest_batch(
    config_tuples: List[Tuple],
    max_workers: Optional[int] = None
) -> List[Tuple]:
    """
    批量运行回测

    Args:
        config_tuples: 配置元组列表
        max_workers: 最大工作进程数

    Returns:
        结果列表
    """
    return batch_execute(
        backtest_worker,
        config_tuples,
        max_workers=max_workers,
        use_threads=False
    )


def run_calculation_batch(
    calculations: List[Tuple],
    max_workers: Optional[int] = None
) -> List[Any]:
    """
    批量执行计算

    Args:
        calculations: 计算任务列表，每个元素是参数元组
        max_workers: 最大工作进程数

    Returns:
        计算结果列表
    """
    return batch_execute(
        simple_math_worker,
        [(x,) for x in calculations],
        max_workers=max_workers,
        use_threads=True
    )
