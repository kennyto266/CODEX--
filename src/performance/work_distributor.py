"""
Phase 3: 工作分发器

T052: 工作分发算法
- 数据分块策略
- 工作窃取
- 负载均衡
- 通信优化
- 容错机制
"""

import asyncio
import logging
import random
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from threading import Lock, RLock, Condition
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, Future
import threading
from multiprocessing import cpu_count
import numpy as np
from collections import deque


logger = logging.getLogger(__name__)


class WorkloadType(Enum):
    """工作负载类型"""
    CPU_BOUND = "cpu_bound"
    IO_BOUND = "io_bound"
    MEMORY_INTENSIVE = "memory_intensive"
    NETWORK_BOUND = "network_bound"


@dataclass
class WorkItem:
    """工作项"""
    id: str
    data: Any
    workload_type: WorkloadType = WorkloadType.CPU_BOUND
    priority: int = 0  # 数值越小优先级越高
    size: int = 1  # 工作量单位
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    assigned_worker: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def is_running(self) -> bool:
        return self.started_at is not None and self.completed_at is None

    @property
    def waiting_time(self) -> float:
        if self.started_at:
            return self.started_at - self.created_at
        return time.time() - self.created_at

    @property
    def execution_time(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workload_type': self.workload_type.value,
            'priority': self.priority,
            'size': self.size,
            'waiting_time': self.waiting_time,
            'execution_time': self.execution_time,
            'retry_count': self.retry_count,
            'is_completed': self.is_completed,
        }


class WorkStealingQueue:
    """工作窃取队列 (多生产者多消费者)"""

    def __init__(self):
        self._local_queue: deque = deque()
        self._steal_queue: deque = deque()
        self._lock = RLock()
        self._empty = Condition(self._lock)

    def push_local(self, item):
        """添加到本地队列头部"""
        with self._lock:
            self._local_queue.appendleft(item)
            self._empty.notify()

    def pop_local(self):
        """从本地队列尾部弹出"""
        with self._lock:
            if self._local_queue:
                item = self._local_queue.pop()
                return item
            return None

    def push_steal(self, item):
        """添加到窃取队列尾部"""
        with self._lock:
            self._steal_queue.append(item)
            self._empty.notify()

    def pop_steal(self):
        """从窃取队列头部窃取"""
        with self._lock:
            if self._steal_queue:
                item = self._steal_queue.popleft()
                return item
            return None

    def is_empty(self) -> bool:
        """检查队列是否为空"""
        with self._lock:
            return not self._local_queue and not self._steal_queue

    def size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._local_queue) + len(self._steal_queue)


class Worker:
    """工作线程"""

    def __init__(
        self,
        worker_id: str,
        distributor: 'WorkDistributor',
        queue: WorkStealingQueue,
    ):
        self.worker_id = worker_id
        self.distributor = distributor
        self.queue = queue
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self.current_work: Optional[WorkItem] = None
        self.stats = {
            'processed': 0,
            'stolen': 0,
            'errors': 0,
            'total_time': 0.0,
        }
        self._stop_event = threading.Event()

    def start(self):
        """启动工作线程"""
        if self.thread and self.thread.is_alive():
            return

        self.is_running = True
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name=f"Worker-{self.worker_id}",
            daemon=True
        )
        self.thread.start()
        logger.debug(f"工作线程 {self.worker_id} 已启动")

    def stop(self, timeout: float = 5.0):
        """停止工作线程"""
        if not self.thread or not self.thread.is_alive():
            return

        self.is_running = False
        self._stop_event.set()
        self.thread.join(timeout)
        logger.debug(f"工作线程 {self.worker_id} 已停止")

    def _run(self):
        """工作线程主循环"""
        while self.is_running:
            # 尝试从本地队列获取工作
            work = self.queue.pop_local()

            if work is None:
                # 尝试从窃取队列获取工作
                work = self.queue.pop_steal()
                if work:
                    self.stats['stolen'] += 1
                    logger.debug(f"工作线程 {self.worker_id} 窃取了工作 {work.id}")

            if work is None:
                # 队列为空，等待
                with self.queue._lock:
                    if self.queue.is_empty() and self.is_running:
                        self.queue._empty.wait(timeout=1.0)
                continue

            # 执行工作
            self._execute_work(work)

    def _execute_work(self, work: WorkItem):
        """执行工作项"""
        work.assigned_worker = self.worker_id
        work.started_at = time.time()
        self.current_work = work

        logger.debug(f"工作线程 {self.worker_id} 开始执行工作 {work.id}")

        try:
            # 检查依赖
            if not self._check_dependencies(work):
                raise RuntimeError(f"工作 {work.id} 的依赖未满足")

            # 执行工作
            start_time = time.time()
            work.result = self.distributor.execute_work(work)
            work.completed_at = time.time()

            # 更新统计
            self.stats['processed'] += 1
            self.stats['total_time'] += (work.completed_at - start_time)

            logger.debug(f"工作线程 {self.worker_id} 完成工作 {work.id}")

        except Exception as e:
            work.error = e
            work.completed_at = time.time()
            work.retry_count += 1
            self.stats['errors'] += 1

            logger.error(f"工作线程 {self.worker_id} 执行工作 {work.id} 失败: {e}")

            # 重试逻辑
            if work.retry_count < 3:
                logger.info(f"重新排队工作 {work.id}")
                self.distributor.requeue_work(work)

        finally:
            self.current_work = None

    def _check_dependencies(self, work: WorkItem) -> bool:
        """检查依赖是否满足"""
        for dep_id in work.dependencies:
            if not self.distributor.is_work_completed(dep_id):
                return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取工作线程统计"""
        return {
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'queue_size': self.queue.size(),
            'current_work': self.current_work.id if self.current_work else None,
            **self.stats
        }


class WorkDistributor:
    """
    工作分发器

    功能特性：
    - 工作窃取算法
    - 动态负载均衡
    - 数据分块策略
    - 容错与重试
    - 性能监控
    """

    def __init__(
        self,
        num_workers: Optional[int] = None,
        chunk_size: int = 1000,
        enable_load_balancing: bool = True,
        max_retries: int = 3,
    ):
        # 配置
        self.num_workers = num_workers or cpu_count()
        self.chunk_size = chunk_size
        self.enable_load_balancing = enable_load_balancing
        self.max_retries = max_retries

        # 工作队列
        self.work_queues: List[WorkStealingQueue] = [
            WorkStealingQueue() for _ in range(self.num_workers)
        ]

        # 工作线程
        self.workers: Dict[str, Worker] = {}
        self.worker_locks = [Lock() for _ in range(self.num_workers)]

        # 工作状态跟踪
        self.work_items: Dict[str, WorkItem] = {}
        self.completed_works: Set[str] = set()
        self.failed_works: Dict[str, Exception] = {}
        self.work_lock = RLock()

        # 统计
        self.stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_stolen': 0,
            'avg_execution_time': 0.0,
            'load_balance_score': 0.0,
        }
        self.stats_lock = Lock()

        # 负载均衡
        self.load_weights = {i: 1.0 for i in range(self.num_workers)}
        self.performance_history: Dict[str, List[float]] = defaultdict(list)

        logger.info(f"初始化工作分发器: {self.num_workers} workers")

    def start(self):
        """启动工作分发器"""
        # 创建并启动工作线程
        for i in range(self.num_workers):
            worker_id = f"worker_{i}"
            worker = Worker(worker_id, self, self.work_queues[i])
            worker.start()
            self.workers[worker_id] = worker

        logger.info("工作分发器已启动")

    def stop(self, timeout: float = 10.0):
        """停止工作分发器"""
        # 停止所有工作线程
        for worker in self.workers.values():
            worker.stop(timeout)

        logger.info("工作分发器已停止")

    def submit_work(
        self,
        work_id: str,
        data: Any,
        workload_type: WorkloadType = WorkloadType.CPU_BOUND,
        priority: int = 0,
        size: int = 1,
        dependencies: Optional[Set[str]] = None,
        **metadata
    ) -> WorkItem:
        """提交工作项"""
        work = WorkItem(
            id=work_id,
            data=data,
            workload_type=workload_type,
            priority=priority,
            size=size,
            dependencies=dependencies or set(),
            metadata=metadata
        )

        # 存储工作项
        with self.work_lock:
            self.work_items[work_id] = work
            self.stats['total_submitted'] += 1

        # 分发工作
        self._distribute_work(work)

        logger.debug(f"工作项已提交: {work_id}")

        return work

    def submit_batch(
        self,
        batch_id: str,
        data_list: List[Any],
        workload_type: WorkloadType = WorkloadType.CPU_BOUND,
        **kwargs
    ) -> List[WorkItem]:
        """批量提交工作项"""
        works = []
        chunk_size = self.chunk_size

        for i in range(0, len(data_list), chunk_size):
            chunk = data_list[i:i + chunk_size]
            work_id = f"{batch_id}_chunk_{i // chunk_size}"

            work = self.submit_work(
                work_id,
                chunk,
                workload_type,
                **kwargs
            )
            works.append(work)

        logger.info(f"批量提交完成: {batch_id}, {len(works)} 个工作项")

        return works

    def _distribute_work(self, work: WorkItem):
        """分发工作到工作队列"""
        # 选择工作队列
        if self.enable_load_balancing:
            target_queue = self._select_best_queue(work)
        else:
            target_queue = hash(work.id) % self.num_workers

        # 添加到队列
        self.work_queues[target_queue].push_local(work)

        logger.debug(f"工作 {work.id} 已分发到队列 {target_queue}")

    def _select_best_queue(self, work: WorkItem) -> int:
        """选择最佳工作队列"""
        # 基于负载权重和历史性能选择
        best_queue = 0
        best_score = float('inf')

        for i in range(self.num_workers):
            # 计算队列负载评分
            queue_size = self.work_queues[i].size()
            load_weight = self.load_weights[i]
            performance = self.performance_history.get(i, [1.0])[-1] if i in self.performance_history else 1.0

            # 综合评分（越小越好）
            score = (queue_size * load_weight) / performance

            if score < best_score:
                best_score = score
                best_queue = i

        return best_queue

    def requeue_work(self, work: WorkItem):
        """重新排队工作项"""
        if work.retry_count < self.max_retries:
            work.completed_at = None
            work.error = None
            self._distribute_work(work)
            logger.debug(f"工作 {work.id} 已重新排队")
        else:
            with self.work_lock:
                self.failed_works[work.id] = work.error or RuntimeError("Max retries exceeded")
                self.stats['total_failed'] += 1
            logger.error(f"工作 {work.id} 重试次数超限，已标记为失败")

    def is_work_completed(self, work_id: str) -> bool:
        """检查工作是否完成"""
        return work_id in self.completed_works

    def get_work_result(self, work_id: str) -> Optional[Any]:
        """获取工作结果"""
        with self.work_lock:
            if work_id in self.completed_works:
                work = self.work_items.get(work_id)
                return work.result if work else None
        return None

    def execute_work(self, work: WorkItem) -> Any:
        """执行工作项（由工作线程调用）"""
        # 模拟工作执行
        # 实际应用中这里会调用具体的工作函数
        time.sleep(0.01)  # 模拟执行时间

        # 根据工作负载类型执行不同逻辑
        if work.workload_type == WorkloadType.CPU_BOUND:
            # CPU密集型工作
            result = sum(i * i for i in range(int(work.size * 100)))
        elif work.workload_type == WorkloadType.IO_BOUND:
            # I/O密集型工作
            time.sleep(0.05)  # 模拟I/O等待
            result = f"IO result for {work.id}"
        else:
            # 默认处理
            result = f"Default result for {work.id}"

        # 标记为完成
        with self.work_lock:
            self.completed_works.add(work.id)
            self.stats['total_completed'] += 1

        return result

    def _update_load_balancing(self):
        """更新负载均衡权重"""
        # 计算每个工作队列的平均执行时间
        for i, worker in enumerate(self.workers.values()):
            stats = worker.get_stats()
            if stats['processed'] > 0:
                avg_time = stats['total_time'] / stats['processed']
                self.performance_history[i].append(avg_time)

                # 保留历史记录
                if len(self.performance_history[i]) > 10:
                    self.performance_history[i].pop(0)

                # 更新权重（执行时间越短，权重越低）
                self.load_weights[i] = 1.0 / (1.0 + avg_time)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            stats = dict(self.stats)

        # 计算平均执行时间
        if stats['total_completed'] > 0:
            total_time = sum(
                worker.stats['total_time']
                for worker in self.workers.values()
            )
            stats['avg_execution_time'] = total_time / stats['total_completed']

        # 工作队列状态
        queue_status = [queue.size() for queue in self.work_queues]
        stats['queue_sizes'] = {
            'min': min(queue_status),
            'max': max(queue_status),
            'avg': sum(queue_status) / len(queue_status),
            'all': queue_status
        }

        # 工作线程状态
        worker_stats = {
            wid: worker.get_stats()
            for wid, worker in self.workers.items()
        }
        stats['workers'] = worker_stats

        # 负载均衡评分
        if self.enable_load_balancing:
            queue_std = np.std(queue_status)
            stats['load_balance_score'] = 1.0 / (1.0 + queue_std)

        return stats

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """等待所有工作完成"""
        start_time = time.time()

        while True:
            with self.work_lock:
                pending = len(self.work_items) - len(self.completed_works) - len(self.failed_works)

            if pending == 0:
                return True

            if timeout and (time.time() - start_time) > timeout:
                logger.warning("等待工作完成超时")
                return False

            time.sleep(0.1)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        worker_health = []
        for worker in self.workers.values():
            stats = worker.get_stats()
            is_healthy = stats['is_running']
            worker_health.append({
                'worker_id': stats['worker_id'],
                'healthy': is_healthy,
                'queue_size': stats['queue_size'],
                'processed': stats['processed'],
                'errors': stats['errors'],
            })

        return {
            'overall_healthy': all(w['healthy'] for w in worker_health),
            'worker_count': len(worker_health),
            'workers': worker_health,
            'total_queue_size': sum(q.size() for q in self.work_queues),
            'completed_works': len(self.completed_works),
            'failed_works': len(self.failed_works),
        }


# 示例使用
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建工作分发器
    distributor = WorkDistributor(
        num_workers=8,
        chunk_size=100,
        enable_load_balancing=True
    )

    # 启动
    distributor.start()

    try:
        # 提交工作项
        print("\n=== 提交工作项 ===")
        for i in range(50):
            distributor.submit_work(
                f"work_{i}",
                list(range(100)),
                WorkloadType.CPU_BOUND,
                priority=i % 3
            )

        # 等待完成
        distributor.wait_for_completion(timeout=30)

        # 获取统计信息
        stats = distributor.get_statistics()
        print("\n=== 工作分发器统计 ===")
        for key, value in stats.items():
            if key != 'workers':
                print(f"{key}: {value}")

        # 负载均衡评分
        print(f"\n负载均衡评分: {stats['load_balance_score']:.4f}")

    finally:
        # 停止
        distributor.stop()
