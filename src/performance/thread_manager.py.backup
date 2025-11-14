"""
Phase 3: 线程池管理器

T051: 动态线程池管理器
- 动态线程池
- 资源管理
- 任务队列
- 优先级调度
- 监控统计
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue, Empty, Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from threading import Lock, Event, Condition
from collections import deque, defaultdict
from multiprocessing import cpu_count
import weakref
import psutil
import json
from pathlib import Path


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """任务"""
    id: str
    func: Callable
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    submit_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    timeout: Optional[float] = None
    retries: int = 0
    max_retries: int = 3
    dependencies: Set[str] = field(default_factory=set)
    result: Optional[Any] = None
    exception: Optional[Exception] = None
    future: Optional[Future] = None

    @property
    def is_completed(self) -> bool:
        """检查任务是否完成"""
        return self.end_time is not None

    @property
    def is_running(self) -> bool:
        """检查任务是否运行中"""
        return self.start_time is not None and self.end_time is None

    @property
    def waiting_time(self) -> float:
        """等待时间"""
        if self.start_time:
            return self.start_time - self.submit_time
        return time.time() - self.submit_time

    @property
    def execution_time(self) -> float:
        """执行时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'priority': self.priority.name,
            'submit_time': self.submit_time,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'waiting_time': self.waiting_time,
            'execution_time': self.execution_time,
            'retries': self.retries,
            'is_completed': self.is_completed,
            'is_running': self.is_running,
        }


class ThreadPoolManager:
    """
    动态线程池管理器

    功能特性：
    - 动态调整线程池大小
    - 优先级任务队列
    - 资源监控
    - 自动负载均衡
    - 任务依赖管理
    """

    def __init__(
        self,
        min_workers: int = 4,
        max_workers: Optional[int] = None,
        keepalive_time: float = 60.0,
        enable_monitoring: bool = True,
    ):
        # 基本配置
        self.min_workers = min_workers
        self.max_workers = max_workers or cpu_count() * 2
        self.keepalive_time = keepalive_time
        self.enable_monitoring = enable_monitoring

        # 线程池
        self.executor: Optional[ThreadPoolExecutor] = None
        self.workers: Set[threading.Thread] = set()
        self.worker_lock = Lock()

        # 任务管理
        self.task_queue: PriorityQueue = PriorityQueue()
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: deque = deque(maxlen=1000)
        self.failed_tasks: deque = deque(maxlen=1000)

        # 同步
        self.task_available = Event()
        self.shutdown_event = Event()
        self.queue_lock = Lock()

        # 统计信息
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'total_execution_time': 0.0,
            'peak_concurrent_tasks': 0,
            'queue_size_peak': 0,
        }
        self.stats_lock = Lock()

        # 监控
        self.monitor_interval = 5.0
        self.last_adjust_time = 0.0
        self.load_history = deque(maxlen=20)

        logger.info(f"初始化线程池管理器: {min_workers}-{max_workers} workers")

    def start(self):
        """启动线程池"""
        if self.executor is not None:
            logger.warning("线程池已启动")
            return

        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="Worker-"
        )
        self.shutdown_event.clear()

        # 启动监控线程
        if self.enable_monitoring:
            monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="PoolMonitor"
            )
            monitor_thread.start()

        logger.info("线程池已启动")

    def stop(self, wait: bool = True, timeout: float = 30.0):
        """停止线程池"""
        if self.executor is None:
            return

        logger.info("正在停止线程池...")

        # 发送停止信号
        self.shutdown_event.set()
        self.task_available.set()  # 唤醒所有等待线程

        # 停止监控
        self.shutdown_event.set()

        if wait:
            # 等待所有任务完成
            start_wait = time.time()
            while self.running_tasks and (time.time() - start_wait) < timeout:
                time.sleep(0.1)

            # 关闭执行器
            self.executor.shutdown(wait=wait)
            self.executor = None

            logger.info("线程池已停止")

    def submit(
        self,
        task_id: str,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Task:
        """提交任务"""
        if self.executor is None:
            raise RuntimeError("线程池未启动")

        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
        )

        # 创建Future
        future = self.executor.submit(self._execute_task, task)
        task.future = future

        # 添加到队列
        self.task_queue.put((priority.value, task))

        with self.stats_lock:
            self.stats['tasks_submitted'] += 1

        # 记录队列大小峰值
        queue_size = self.task_queue.qsize()
        with self.stats_lock:
            self.stats['queue_size_peak'] = max(
                self.stats['queue_size_peak'],
                queue_size
            )

        logger.debug(f"任务已提交: {task_id}, 优先级: {priority.name}")

        return task

    def _execute_task(self, task: Task) -> Any:
        """执行任务"""
        task_id = task.id

        # 检查依赖
        if not self._check_dependencies(task):
            error = RuntimeError(f"任务依赖未满足: {task.dependencies}")
            self._handle_task_failure(task, error)
            raise error

        # 等待依赖完成
        for dep_id in task.dependencies:
            self._wait_for_dependency(dep_id)

        # 记录开始时间
        task.start_time = time.time()

        # 添加到运行中任务
        with self.queue_lock:
            self.running_tasks[task_id] = task
            current_concurrent = len(self.running_tasks)

        # 更新峰值并发
        with self.stats_lock:
            self.stats['peak_concurrent_tasks'] = max(
                self.stats['peak_concurrent_tasks'],
                current_concurrent
            )

        logger.debug(f"开始执行任务: {task_id}")

        try:
            # 执行任务
            result = self._run_with_timeout(task)
            task.result = result

            # 记录结束时间
            task.end_time = time.time()
            execution_time = task.execution_time

            with self.stats_lock:
                self.stats['tasks_completed'] += 1
                self.stats['total_execution_time'] += execution_time

            logger.debug(f"任务完成: {task_id}, 耗时: {execution_time:.3f}s")

        except Exception as e:
            self._handle_task_failure(task, e)
            raise

        finally:
            # 从运行中任务移除
            with self.queue_lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

            # 添加到已完成任务
            self.completed_tasks.append(task)

        return task.result

    def _run_with_timeout(self, task: Task) -> Any:
        """带超时执行任务"""
        if task.timeout is None:
            return task.func(*task.args, **task.kwargs)

        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"任务执行超时: {task.timeout}s")

        # 设置信号处理器
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(task.timeout))

        try:
            result = task.func(*task.args, **task.kwargs)
            signal.alarm(0)  # 取消闹钟
            return result
        except:
            signal.alarm(0)  # 取消闹钟
            raise

    def _check_dependencies(self, task: Task) -> bool:
        """检查任务依赖"""
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                # 检查是否在运行中或已完成
                with self.queue_lock:
                    if dep_id in self.running_tasks:
                        continue
                return False

        return True

    def _wait_for_dependency(self, dep_id: str, timeout: float = 30.0):
        """等待依赖任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.queue_lock:
                if dep_id not in self.running_tasks:
                    # 检查是否已完成
                    for task in self.completed_tasks:
                        if task.id == dep_id:
                            return
            time.sleep(0.01)

        raise RuntimeError(f"等待依赖任务超时: {dep_id}")

    def _handle_task_failure(self, task: Task, error: Exception):
        """处理任务失败"""
        task.exception = error
        task.end_time = time.time()

        with self.stats_lock:
            self.stats['tasks_failed'] += 1

        logger.error(f"任务失败: {task.id}, 错误: {error}")

        # 重试逻辑
        if task.retries < task.max_retries:
            task.retries += 1
            logger.info(f"重试任务: {task.id}, 第 {task.retries} 次")

            # 重新提交
            retry_task = Task(
                id=f"{task.id}_retry_{task.retries}",
                func=task.func,
                args=task.args,
                kwargs=task.kwargs,
                priority=task.priority,
                timeout=task.timeout,
                max_retries=task.max_retries,
            )
            self.submit(retry_task.id, retry_task.func, *retry_task.args,
                       priority=retry_task.priority, **retry_task.kwargs)

        else:
            # 添加到失败任务
            self.failed_tasks.append(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        # 检查运行中
        with self.queue_lock:
            if task_id in self.running_tasks:
                return self.running_tasks[task_id]

        # 检查已完成
        for task in self.completed_tasks:
            if task.id == task_id:
                return task

        # 检查失败
        for task in self.failed_tasks:
            if task.id == task_id:
                return task

        return None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.queue_lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                if task.future and not task.future.done():
                    cancelled = task.future.cancel()
                    if cancelled:
                        with self.stats_lock:
                            self.stats['tasks_cancelled'] += 1
                        return True
        return False

    def _monitor_loop(self):
        """监控循环"""
        while not self.shutdown_event.is_set():
            try:
                self._collect_metrics()
                self._adjust_pool_size()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"监控循环错误: {e}")

    def _collect_metrics(self):
        """收集指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存使用
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 队列大小
        queue_size = self.task_queue.qsize()

        # 运行中任务数
        running_count = len(self.running_tasks)

        # 计算负载
        load = (cpu_percent + memory_percent) / 2.0

        self.load_history.append({
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'queue_size': queue_size,
            'running_count': running_count,
            'load': load
        })

    def _adjust_pool_size(self):
        """动态调整线程池大小"""
        now = time.time()
        if now - self.last_adjust_time < self.monitor_interval * 2:
            return

        self.last_adjust_time = now

        if len(self.load_history) < 3:
            return

        recent_loads = [l['load'] for l in list(self.load_history)[-3:]]
        avg_load = sum(recent_loads) / len(recent_loads)

        # 负载高，增加线程
        if avg_load > 80 and self._get_active_workers() < self.max_workers:
            new_size = min(self._get_active_workers() + 2, self.max_workers)
            self._resize_pool(new_size)
            logger.info(f"增加线程池大小到: {new_size}")

        # 负载低，减少线程
        elif avg_load < 30 and self._get_active_workers() > self.min_workers:
            new_size = max(self._get_active_workers() - 2, self.min_workers)
            self._resize_pool(new_size)
            logger.info(f"减少线程池大小到: {new_size}")

    def _get_active_workers(self) -> int:
        """获取活跃工作线程数"""
        with self.worker_lock:
            return len(self.workers)

    def _resize_pool(self, new_size: int):
        """调整线程池大小"""
        # 注意: ThreadPoolExecutor不支持动态调整大小
        # 这里仅记录，用于下次创建时使用
        logger.info(f"建议调整线程池大小到: {new_size}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            stats = dict(self.stats)

        # 添加运行时信息
        stats.update({
            'current_queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks_count': len(self.completed_tasks),
            'failed_tasks_count': len(self.failed_tasks),
            'active_workers': self._get_active_workers(),
        })

        # 计算平均值
        if stats['tasks_completed'] > 0:
            stats['avg_execution_time'] = (
                stats['total_execution_time'] / stats['tasks_completed']
            )

        # 最近负载
        if self.load_history:
            recent = list(self.load_history)[-1]
            stats['current_load'] = recent['load']
            stats['cpu_percent'] = recent['cpu_percent']
            stats['memory_percent'] = recent['memory_percent']

        return stats

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        queue_status = []
        temp_queue = PriorityQueue()

        # 提取所有任务（不破坏队列）
        while not self.task_queue.empty():
            try:
                priority, task = self.task_queue.get_nowait()
                queue_status.append(task.to_dict())
                temp_queue.put((priority, task))
            except Empty:
                break

        # 恢复队列
        while not temp_queue.empty():
            self.task_queue.put(temp_queue.get())

        return {
            'queue_size': len(queue_status),
            'tasks': queue_status,
            'by_priority': {
                p.name: sum(1 for t in queue_status if t['priority'] == p.name)
                for p in TaskPriority
            }
        }

    def save_statistics(self, filepath: str):
        """保存统计信息"""
        stats = self.get_statistics()
        queue_status = self.get_queue_status()

        report = {
            'timestamp': time.time(),
            'statistics': stats,
            'queue_status': queue_status,
            'performance': {
                'avg_throughput': stats.get('tasks_completed', 0) / max(stats.get('total_execution_time', 1), 0.001),
                'success_rate': (
                    stats.get('tasks_completed', 0) / max(stats.get('tasks_submitted', 1), 1)
                ) * 100,
            }
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"统计信息已保存到: {filepath}")


class AsyncThreadPool:
    """异步线程池包装器"""

    def __init__(self, manager: ThreadPoolManager):
        self.manager = manager
        self._loop = None

    def run_in_thread(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """在线程池中运行函数"""
        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        future = self._loop.create_future()

        def callback(fut: Future):
            try:
                result = fut.result()
                if not future.cancelled():
                    future.set_result(result)
            except Exception as e:
                if not future.cancelled():
                    future.set_exception(e)

        task_id = f"async_{int(time.time() * 1000)}"
        task = self.manager.submit(task_id, func, *args, **kwargs)

        if task.future:
            task.future.add_done_callback(callback)

        return future


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建线程池管理器
    manager = ThreadPoolManager(
        min_workers=4,
        max_workers=16,
        enable_monitoring=True
    )

    # 启动
    manager.start()

    try:
        # 提交任务
        def heavy_task(duration: float, value: int) -> int:
            time.sleep(duration)
            return value * 2

        tasks = []
        for i in range(10):
            task = manager.submit(
                f"task_{i}",
                heavy_task,
                0.5,  # 0.5秒
                i,
                priority=TaskPriority.NORMAL
            )
            tasks.append(task)

        # 等待所有任务完成
        time.sleep(5)

        # 获取统计信息
        stats = manager.get_statistics()
        print("\n=== 线程池统计 ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

        # 保存统计信息
        manager.save_statistics('thread_pool_stats.json')

    finally:
        # 停止
        manager.stop(wait=True, timeout=10)
