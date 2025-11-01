"""
動態負載均衡器

提供：
- 任務分配
- 性能監控
- 動態調整
- 故障恢復
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor

from src.core.logging import get_logger

logger = get_logger("load_balancer")


@dataclass
class WorkerStats:
    """工作進程統計"""
    worker_id: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0


class DynamicLoadBalancer:
    """動態負載均衡器"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or asyncio.cpu_count() * 2
        self.logger = get_logger("load_balancer")

        # 工作進程管理
        self._workers: Dict[str, WorkerStats] = {}
        self._active_workers: set = set()
        self._available_workers: set = set()

        # 性能歷史
        self._performance_history: Dict[str, deque] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

        # 監控
        self._monitor_interval = 5  # 秒
        self._rebalance_threshold = 0.5  # 50%

    async def start(self):
        """啟動負載均衡器"""
        self._running = True
        asyncio.create_task(self._monitor_loop())
        self.logger.info(f"Load balancer started with {self.max_workers} max workers")

    async def stop(self):
        """停止負載均衡器"""
        self._running = False
        self.logger.info("Load balancer stopped")

    async def submit_task(
        self,
        task_func: Callable,
        args: tuple = (),
        kwargs: dict = None
    ) -> Future:
        """提交任務"""
        if not self._running:
            raise RuntimeError("Load balancer not running")

        kwargs = kwargs or {}
        future = asyncio.Future()

        # 選擇最佳工作進程
        worker_id = await self._select_best_worker()
        if not worker_id:
            # 沒有可用工作進程，創建新的
            worker_id = await self._create_worker()

        # 分配任務
        await self._assign_task(worker_id, task_func, args, kwargs, future)

        return future

    async def _select_best_worker(self) -> Optional[str]:
        """選擇最佳工作進程"""
        if not self._available_workers:
            return None

        # 根據歷史性能選擇
        best_worker = None
        best_score = float('-inf')

        for worker_id in self._available_workers:
            stats = self._workers[worker_id]
            score = self._calculate_worker_score(stats)

            if score > best_score:
                best_score = score
                best_worker = worker_id

        return best_worker

    def _calculate_worker_score(self, stats: WorkerStats) -> float:
        """計算工作進程得分"""
        # 綜合考慮：完成任務數、執行時間、系統負載
        base_score = stats.completed_tasks * 10

        # 執行時間越短越好
        time_score = 100 / max(stats.average_execution_time, 0.1)

        # 系統負載越低越好
        load_score = 100 - stats.cpu_usage

        # 綜合得分
        score = base_score + time_score + load_score

        return score

    async def _create_worker(self) -> str:
        """創建新的工作進程"""
        worker_id = f"worker_{len(self._workers)}"
        stats = WorkerStats(worker_id=worker_id)

        self._workers[worker_id] = stats
        self._active_workers.add(worker_id)
        self._available_workers.add(worker_id)
        self._performance_history[worker_id] = deque(maxlen=100)

        self.logger.debug(f"Created worker: {worker_id}")
        return worker_id

    async def _assign_task(
        self,
        worker_id: str,
        task_func: Callable,
        args: tuple,
        kwargs: dict,
        future: Future
    ):
        """分配任務到工作進程"""
        if worker_id not in self._workers:
            raise ValueError(f"Worker {worker_id} not found")

        stats = self._workers[worker_id]
        stats.active_tasks += 1
        self._available_workers.discard(worker_id)

        start_time = time.time()

        try:
            # 執行任務
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, task_func, *args, **kwargs)

            future.set_result(result)
            stats.completed_tasks += 1

        except Exception as e:
            future.set_exception(e)
            stats.failed_tasks += 1
            self.logger.error(f"Task failed on worker {worker_id}: {e}")

        finally:
            # 更新統計
            execution_time = time.time() - start_time
            stats.active_tasks -= 1
            stats.average_execution_time = (
                (stats.average_execution_time * (stats.completed_tasks - 1) + execution_time)
                / stats.completed_tasks
            )
            stats.last_heartbeat = time.time()

            # 重新加入可用列表
            self._available_workers.add(worker_id)

            # 記錄性能歷史
            self._performance_history[worker_id].append({
                "execution_time": execution_time,
                "success": not future.exception(),
                "timestamp": time.time()
            })

    async def _monitor_loop(self):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(self._monitor_interval)
                await self._check_worker_health()
                await self._rebalance_load()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")

    async def _check_worker_health(self):
        """檢查工作進程健康狀態"""
        current_time = time.time()
        unhealthy_workers = []

        for worker_id, stats in self._workers.items():
            # 檢查心跳
            if current_time - stats.last_heartbeat > 30:
                self.logger.warning(f"Worker {worker_id} heartbeat timeout")
                unhealthy_workers.append(worker_id)

            # 檢查失敗率
            total_tasks = stats.completed_tasks + stats.failed_tasks
            if total_tasks > 0:
                failure_rate = stats.failed_tasks / total_tasks
                if failure_rate > 0.5:
                    self.logger.warning(
                        f"Worker {worker_id} high failure rate: {failure_rate:.2%}"
                    )
                    unhealthy_workers.append(worker_id)

        # 移除不健康的工作進程
        for worker_id in unhealthy_workers:
            self._remove_worker(worker_id)

    async def _rebalance_load(self):
        """重新平衡負載"""
        if len(self._available_workers) < 2:
            return

        # 獲取負載最重的工作進程
        max_active = max(
            (stats.active_tasks for stats in self._workers.values()),
            default=0
        )

        # 如果最大負載超過閾值，重新分配
        if max_active > self._rebalance_threshold * self.max_workers:
            self.logger.info("Rebalancing workload...")
            # 這裡可以實現更複雜的負載重新分配邏輯

    def _remove_worker(self, worker_id: str):
        """移除工作進程"""
        if worker_id in self._workers:
            del self._workers[worker_id]
        self._active_workers.discard(worker_id)
        self._available_workers.discard(worker_id)
        self._performance_history.pop(worker_id, None)

        self.logger.info(f"Removed worker: {worker_id}")

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "max_workers": self.max_workers,
            "active_workers": len(self._active_workers),
            "available_workers": len(self._available_workers),
            "total_workers": len(self._workers),
            "workers": {
                worker_id: {
                    "active_tasks": stats.active_tasks,
                    "completed_tasks": stats.completed_tasks,
                    "failed_tasks": stats.failed_tasks,
                    "average_execution_time": stats.average_execution_time,
                    "cpu_usage": stats.cpu_usage,
                    "memory_usage": stats.memory_usage
                }
                for worker_id, stats in self._workers.items()
            }
        }
