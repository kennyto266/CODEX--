"""
Performance Optimization Module - Parallel Computing
Phase 3: Performance Optimization - Parallel Computing

This module provides comprehensive parallel computing features:
- T050: Rayon-based parallel optimizer
- T051: Dynamic thread pool manager
- T052: Work distribution algorithm
- T053: CPU core detection and auto-configuration
"""

# Import from individual modules
from .parallel_optimizer import (
    ParallelOptimizer,
    OptimizationResult,
    MemoryMonitor,
    WorkerPool
)

from .thread_manager import (
    ThreadPoolManager,
    TaskPriority,
    Task,
    AsyncThreadPool
)

from .work_distributor import (
    WorkDistributor,
    WorkloadType,
    WorkItem,
    WorkStealingQueue,
    Worker
)

from .cpu_detector import (
    CPUDetector,
    CPUInfo,
    SystemLoad,
    ArchitectureType,
    HyperThreading
)

# Aliases for compatibility
RayonParallelOptimizer = ParallelOptimizer

__all__ = [
    # Parallel Optimizer (T050)
    'ParallelOptimizer',
    'RayonParallelOptimizer',  # Compatibility alias
    'OptimizationResult',
    'MemoryMonitor',
    'WorkerPool',

    # Thread Manager (T051)
    'ThreadPoolManager',
    'TaskPriority',
    'Task',
    'AsyncThreadPool',

    # Work Distributor (T052)
    'WorkDistributor',
    'WorkloadType',
    'WorkItem',
    'WorkStealingQueue',
    'Worker',

    # CPU Detector (T053)
    'CPUDetector',
    'CPUInfo',
    'SystemLoad',
    'ArchitectureType',
    'HyperThreading',
]

# Performance optimization version info
__version__ = "1.0.0"
__phase__ = "Phase 3: Performance Optimization - Parallel Computing"
__targets__ = {
    "1000_combinations_under_10s": "< 10s for 1000 combinations on 8 cores",
    "32_concurrent_backtests": "< 300ms total time",
    "speedup_ratio": "7-8x (close to core count)",
    "memory_overhead": "< 100MB",
}

# Parallel computing targets
PARALLEL_TARGETS = {
    "optimization_time_seconds": 10.0,      # 1000组合优化: < 10秒
    "concurrent_backtests_ms": 300,         # 32并发回测: < 300ms
    "speedup_factor": 7.0,                  # 加速比: 接近核心数
    "memory_overhead_mb": 100,              # 内存开销: < 100MB
}

# Performance requirements
PERFORMANCE_REQUIREMENTS = {
    "max_workers": 32,                      # 最大工作线程数
    "chunk_size": 1000,                     # 数据块大小
    "timeout_seconds": 30.0,                # 任务超时时间
    "max_retries": 3,                       # 最大重试次数
}
