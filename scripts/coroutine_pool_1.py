"""
高性能协程池管理器
实现动态扩缩容的任务调度系统
"""

import asyncio
import logging
import time
import weakref
from typing import Any, Callable, Awaitable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

# Mock Prometheus 指标
class MockCounter:
    def __init__(self, name, description, labels=None):
        pass

    def inc(self, count=1):
        pass


class MockGauge:
    def __init__(self, name, description, labels=None):
        pass

    def inc(self, count=1):
        pass

    def dec(self, count=1):
        pass

    def set(self, value):
        pass


class MockHistogram:
    def __init__(self, name, description, labels=None):
        pass

    def observe(self, value):
        pass


# Prometheus 监控指标 (使用 Mock)
COROUTINE_POOL_TASKS_SUBMITTED = MockCounter(
    'sprint4_coroutine_pool_tasks_submitted_total',
    'Tasks submitted',
    ['pool_name']
)
COROUTINE_POOL_TASKS_COMPLETED = MockCounter(
    'sprint4_coroutine_pool_tasks_completed_total',
    'Tasks completed',
    ['pool_name']
)
COROUTINE_POOL_TASKS_FAILED = MockCounter(
    'sprint4_coroutine_pool_tasks_failed_total',
    'Tasks failed',
    ['pool_name']
)
COROUTINE_POOL_ACTIVE_WORKERS = MockGauge(
    'sprint4_coroutine_pool_active_workers',
    'Active workers',
    ['pool_name']
)
COROUTINE_POOL_QUEUE_SIZE = MockGauge(
    'sprint4_coroutine_pool_queue_size',
    'Queue size',
    ['pool_name']
)
COROUTINE_POOL_TASK_DURATION = MockHistogram(
    'sprint4_coroutine_pool_task_duration_seconds',
    'Task duration',
    ['pool_name', 'status']
)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0
    status: str = "pending"  # pending, running, completed, failed

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'duration': self.duration,
            'status': self.status
        }


@dataclass
class PoolConfig:
    """协程池配置"""
    max_workers: int = 100  # 最大工作者数量
    min_workers: int = 10   # 最小工作者数量
    max_queue_size: int = 1000  # 队列最大大小
    task_timeout: float = 30.0  # 任务超时时间
    worker_idle_timeout: float = 60.0  # 工作者空闲超时
    scale_up_threshold: float = 0.8   # 扩容阈值
    scale_down_threshold: float = 0.3  # 缩容阈值
    scale_up_cooldown: float = 10.0   # 扩容冷却时间
    scale_down_cooldown: float = 60.0 # 缩容冷却时间


class Worker:
    """工作者类"""

    def __init__(self, worker_id: str, pool: 'CoroutinePool'):
        self.worker_id = worker_id
        self.pool = pool
        self.current_task: Optional[asyncio.Task] = None
        self.current_task_id: Optional[str] = None
        self.is_busy = False
        self.created_at = time.time()
        self.last_active = time.time()

    async def run(self):
        """运行工作者"""
        try:
            while True:
                try:
                    # 从队列获取任务
                    task_info = await self.pool._get_task_from_queue()

                    if task_info is None:
                        # 检查是否需要缩容
                        if await self.pool._should_scale_down():
                            break
                        # 等待任务
                        await asyncio.sleep(self.pool.config.worker_idle_timeout)
                        continue

                    self.is_busy = True
                    self.last_active = time.time()
                    task_id, task_func, args, kwargs, timeout = task_info
                    self.current_task_id = task_id

                    start_time = time.time()

                    try:
                        # 执行任务
                        result = await asyncio.wait_for(
                            task_func(*args, **kwargs),
                            timeout=timeout
                        )

                        duration = time.time() - start_time
                        await self.pool._complete_task(
                            task_id,
                            result=result,
                            duration=duration
                        )

                    except asyncio.TimeoutError:
                        duration = time.time() - start_time
                        error = asyncio.TimeoutError(f"Task {task_id} timed out after {timeout}s")
                        await self.pool._complete_task(
                            task_id,
                            error=error,
                            duration=duration
                        )

                    except Exception as e:
                        duration = time.time() - start_time
                        await self.pool._complete_task(
                            task_id,
                            error=e,
                            duration=duration
                        )

                except asyncio.CancelledError:
                    logger.info(f"Worker {self.worker_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error: {e}")
                    await asyncio.sleep(1)
                finally:
                    self.is_busy = False
                    self.current_task = None
                    self.current_task_id = None

        except Exception as e:
            logger.error(f"Worker {self.worker_id} fatal error: {e}")
        finally:
            self.is_busy = False

    async def stop(self):
        """停止工作者"""
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass


class CoroutinePool:
    """高性能协程池管理器"""

    def __init__(
        self,
        name: str,
        config: PoolConfig
    ):
        """
        初始化协程池

        Args:
            name: 池名称
            config: 池配置
        """
        self.name = name
        self.config = config
        self._workers: Dict[str, Worker] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self._task_results: Dict[str, TaskResult] = {}
        self._result_futures: Dict[str, asyncio.Future] = {}
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._last_scale_up = 0.0
        self._last_scale_down = 0.0

        # 使用WeakSet跟踪活跃任务，防止内存泄漏
        self._active_tasks: weakref.WeakSet = weakref.WeakSet()

    async def initialize(self):
        """初始化协程池"""
        # 创建最小工作者数量
        for i in range(self.config.min_workers):
            await self._create_worker()

        logger.info(
            f"Coroutine pool {self.name} initialized with "
            f"{self.config.min_workers} workers"
        )

    async def _create_worker(self) -> Worker:
        """创建工作者"""
        async with self._lock:
            worker_id = f"{self.name}-worker-{len(self._workers)}"
            worker = Worker(worker_id, self)
            self._workers[worker_id] = worker

            # 启动工作者
            task = asyncio.create_task(worker.run())
            worker.current_task = task
            self._active_tasks.add(task)

            COROUTINE_POOL_ACTIVE_WORKERS.labels(pool_name=self.name).inc()

            logger.debug(f"Created worker: {worker_id}")
            return worker

    async def _remove_worker(self, worker: Worker):
        """移除工作者"""
        async with self._lock:
            await worker.stop()
            del self._workers[worker.worker_id]
            COROUTINE_POOL_ACTIVE_WORKERS.labels(pool_name=self.name).dec()
            logger.debug(f"Removed worker: {worker.worker_id}")

    async def _get_task_from_queue(self) -> Optional[tuple]:
        """从队列获取任务"""
        try:
            task_info = await asyncio.wait_for(
                self._task_queue.get(),
                timeout=1.0
            )
            return task_info
        except asyncio.TimeoutError:
            return None

    async def _complete_task(
        self,
        task_id: str,
        result: Any = None,
        error: Exception = None,
        duration: float = 0.0
    ):
        """完成任务"""
        # 记录结果
        task_result = TaskResult(
            task_id=task_id,
            result=result,
            error=error,
            duration=duration,
            status="completed" if error is None else "failed"
        )
        self._task_results[task_id] = task_result

        # 更新指标
        if error is None:
            COROUTINE_POOL_TASKS_COMPLETED.labels(pool_name=self.name).inc()
            COROUTINE_POOL_TASK_DURATION.labels(
                pool_name=self.name,
                status="success"
            ).observe(duration)
        else:
            COROUTINE_POOL_TASKS_FAILED.labels(pool_name=self.name).inc()
            COROUTINE_POOL_TASK_DURATION.labels(
                pool_name=self.name,
                status="failed"
            ).observe(duration)

        # 通知等待者
        if task_id in self._result_futures:
            future = self._result_futures.pop(task_id)
            if error:
                future.set_exception(error)
            else:
                future.set_result(result)

    async def submit_task(
        self,
        task_func: Callable,
        *args,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        提交任务

        Args:
            task_func: 任务函数
            *args: 位置参数
            task_id: 任务ID
            timeout: 超时时间
            **kwargs: 关键字参数

        Returns:
            任务ID
        """
        task_id = task_id or f"task-{int(time.time() * 1000)}-{len(self._task_results)}"
        timeout = timeout or self.config.task_timeout

        # 检查队列是否满
        if self._task_queue.full():
            raise asyncio.QueueFull(
                f"Task queue is full (max size: {self.config.max_queue_size})"
            )

        # 检查是否需要扩容
        await self._maybe_scale_up()

        # 添加任务到队列
        task_info = (task_id, task_func, args, kwargs, timeout)
        await self._task_queue.put(task_info)

        # 创建结果future
        result_future = asyncio.Future()
        self._result_futures[task_id] = result_future

        # 更新指标
        COROUTINE_POOL_TASKS_SUBMITTED.labels(pool_name=self.name).inc()
        COROUTINE_POOL_QUEUE_SIZE.labels(pool_name=self.name).set(
            self._task_queue.qsize()
        )

        logger.debug(f"Task submitted: {task_id}")
        return task_id

    async def submit_and_wait(
        self,
        task_func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        提交任务并等待结果

        Args:
            task_func: 任务函数
            *args: 位置参数
            timeout: 超时时间
            **kwargs: 关键字参数

        Returns:
            任务结果
        """
        task_id = await self.submit_task(
            task_func,
            *args,
            timeout=timeout,
            **kwargs
        )

        # 等待结果
        future = self._result_futures.get(task_id)
        if future:
            result = await future
            return result
        else:
            raise RuntimeError(f"Task {task_id} not found")

    async def _maybe_scale_up(self):
        """可能的扩容"""
        current_time = time.time()

        # 检查冷却时间
        if current_time - self._last_scale_up < self.config.scale_up_cooldown:
            return

        # 计算队列使用率
        queue_usage = self._task_queue.qsize() / self.config.max_queue_size

        # 计算工作者使用率
        active_workers = sum(1 for w in self._workers.values() if w.is_busy)
        worker_usage = (
            active_workers / len(self._workers) if self._workers else 0
        )

        # 检查是否需要扩容
        if (
            queue_usage > self.config.scale_up_threshold or
            worker_usage > self.config.scale_up_threshold
        ):
            if len(self._workers) < self.config.max_workers:
                await self._create_worker()
                self._last_scale_up = current_time
                logger.info(f"Scaled up to {len(self._workers)} workers")

    async def _should_scale_down(self) -> bool:
        """是否应该缩容"""
        current_time = time.time()

        # 检查冷却时间
        if current_time - self._last_scale_down < self.config.scale_down_cooldown:
            return False

        # 不能少于最小工作者数量
        if len(self._workers) <= self.config.min_workers:
            return False

        # 检查空闲工作者
        idle_workers = [
            w for w in self._workers.values()
            if not w.is_busy and
            current_time - w.last_active > self.config.worker_idle_timeout
        ]

        # 如果有空闲工作者且队列为空
        if idle_workers and self._task_queue.empty():
            # 移除一个空闲工作者
            worker = idle_workers[0]
            await self._remove_worker(worker)
            self._last_scale_down = current_time
            logger.info(f"Scaled down to {len(self._workers)} workers")
            return True

        return False

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_workers = sum(1 for w in self._workers.values() if w.is_busy)
        idle_workers = len(self._workers) - active_workers

        return {
            'name': self.name,
            'total_workers': len(self._workers),
            'active_workers': active_workers,
            'idle_workers': idle_workers,
            'min_workers': self.config.min_workers,
            'max_workers': self.config.max_workers,
            'queue_size': self._task_queue.qsize(),
            'queue_max_size': self.config.max_queue_size,
            'total_tasks': len(self._task_results),
            'pending_tasks': len(self._result_futures),
            'completed_tasks': sum(
                1 for t in self._task_results.values()
                if t.status == "completed"
            ),
            'failed_tasks': sum(
                1 for t in self._task_results.values()
                if t.status == "failed"
            ),
            'queue_usage': (
                self._task_queue.qsize() / self.config.max_queue_size
            ),
            'worker_usage': (
                active_workers / len(self._workers) if self._workers else 0
            )
        }

    async def shutdown(self, timeout: float = 30.0):
        """关闭协程池"""
        logger.info(f"Shutting down coroutine pool {self.name}...")

        # 等待所有任务完成或超时
        start_time = time.time()
        while self._result_futures and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        # 取消所有工作者
        for worker in list(self._workers.values()):
            await worker.stop()

        self._shutdown_event.set()
        logger.info(f"Coroutine pool {self.name} shutdown complete")
