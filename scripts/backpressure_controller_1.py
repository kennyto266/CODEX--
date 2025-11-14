"""
背压控制器
实现信号量 + 优先级队列 + 熔断器机制
"""

import asyncio
import time
from typing import Optional, Dict, List, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
# from prometheus_client import Counter, Gauge
import logging

logger = logging.getLogger(__name__)
n# Mock Prometheus 指标
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

# 监控指标
BACKPRESSURE_REJECTED = MockCounter(
    'sprint4_backpressure_rejected_total',
    'Rejected requests',
    ['reason']
)
BACKPRESSURE_QUEUE_SIZE = MockGauge(
    'sprint4_backpressure_queue_size',
    'Queue size'
)
BACKPRESSURE_RATE_LIMIT = MockCounter(
    'sprint4_backpressure_rate_limited_total',
    'Rate limited requests',
    ['resource']
)
BACKPRESSURE_CIRCUIT_BREAKER = MockCounter(
    'sprint4_backpressure_circuit_breaker_total',
    'Circuit breaker triggers',
    ['resource']
)


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"      # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class PriorityEntry:
    """优先级队列条目"""
    priority: int  # 越小优先级越高
    entry_time: float
    resource_id: str
    future: asyncio.Future
    data: Any

    def __lt__(self, other):
        """优先级比较"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.entry_time < other.entry_time


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    max_requests: int = 1000  # 最大请求数
    time_window: float = 1.0  # 时间窗口（秒）
    max_queue_size: int = 500  # 最大队列大小
    queue_timeout: float = 5.0  # 队列等待超时


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 50  # 失败阈值
    recovery_timeout: float = 60.0  # 恢复超时时间
    expected_exception: type = Exception  # 预期的异常类型


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_attempts = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """调用熔断器保护的方法"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_attempts = 0
                BACKPRESSURE_CIRCUIT_BREAKER.labels(resource="default").inc()
                logger.info("Circuit breaker half-open")
            else:
                raise RuntimeError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        return (
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )

    def _on_success(self):
        """成功回调"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_attempts += 1
            if self.half_open_attempts >= 3:  # 连续3次成功则关闭熔断器
                self.state = CircuitBreakerState.CLOSED
                logger.info("Circuit breaker closed")

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class BackpressureController:
    """背压控制器"""

    def __init__(self, config: RateLimitConfig):
        """
        初始化背压控制器

        Args:
            config: 速率限制配置
        """
        self.config = config
        self.request_counts: Dict[str, List[float]] = {}
        self.priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=config.max_queue_size
        )
        self._semaphore = asyncio.Semaphore(config.max_requests)
        self._lock = asyncio.Lock()
        self._resource_circuit_breakers: Dict[str, CircuitBreaker] = {}

    async def acquire(
        self,
        resource_id: str = "default",
        priority: int = 10
    ) -> bool:
        """
        获取资源许可

        Args:
            resource_id: 资源ID
            priority: 优先级（越小越高）

        Returns:
            是否获取成功
        """
        # 检查速率限制
        if not await self._check_rate_limit(resource_id):
            BACKPRESSURE_REJECTED.labels(reason="rate_limit").inc()
            logger.warning(f"Rate limit exceeded for {resource_id}")
            return False

        # 检查熔断器
        if not await self._check_circuit_breaker(resource_id):
            BACKPRESSURE_REJECTED.labels(reason="circuit_breaker").inc()
            logger.warning(f"Circuit breaker open for {resource_id}")
            return False

        # 检查信号量
        if self._semaphore.locked():
            # 尝试加入优先级队列
            return await self._try_queue_request(resource_id, priority)

        # 获取信号量
        async with self._semaphore:
            BACKPRESSURE_RATE_LIMIT.labels(resource=resource_id).inc()
            BACKPRESSURE_QUEUE_SIZE.set(self.priority_queue.qsize())
            return True

    async def _check_rate_limit(self, resource_id: str) -> bool:
        """检查速率限制"""
        current_time = time.time()
        window_start = current_time - self.config.time_window

        async with self._lock:
            # 初始化资源计数
            if resource_id not in self.request_counts:
                self.request_counts[resource_id] = []

            # 清理过期计数
            self.request_counts[resource_id] = [
                t for t in self.request_counts[resource_id]
                if t > window_start
            ]

            # 检查是否超过限制
            if len(self.request_counts[resource_id]) >= self.config.max_requests:
                return False

            # 添加当前请求
            self.request_counts[resource_id].append(current_time)
            return True

    async def _check_circuit_breaker(self, resource_id: str) -> bool:
        """检查熔断器"""
        if resource_id not in self._resource_circuit_breakers:
            self._resource_circuit_breakers[resource_id] = CircuitBreaker(
                CircuitBreakerConfig()
            )

        breaker = self._resource_circuit_breakers[resource_id]
        return breaker.state != CircuitBreakerState.OPEN

    async def _try_queue_request(
        self,
        resource_id: str,
        priority: int
    ) -> bool:
        """尝试将请求加入队列"""
        current_time = time.time()

        # 创建Future
        future = asyncio.Future()

        # 创建优先级条目
        entry = PriorityEntry(
            priority=priority,
            entry_time=current_time,
            resource_id=resource_id,
            future=future,
            data=None
        )

        try:
            # 尝试加入队列
            self.priority_queue.put_nowait(entry)
            BACKPRESSURE_QUEUE_SIZE.set(self.priority_queue.qsize())

            # 等待队列处理
            try:
                await asyncio.wait_for(future, timeout=self.config.queue_timeout)
                return True
            except asyncio.TimeoutError:
                BACKPRESSURE_REJECTED.labels(reason="queue_timeout").inc()
                return False

        except asyncio.QueueFull:
            BACKPRESSURE_REJECTED.labels(reason="queue_full").inc()
            logger.warning(f"Queue is full for {resource_id}")
            return False

    async def process_queue(self):
        """处理优先级队列"""
        while True:
            try:
                # 从队列获取请求
                entry = await asyncio.wait_for(
                    self.priority_queue.get(),
                    timeout=1.0
                )

                # 检查信号量
                if self._semaphore.locked():
                    # 重新放回队列
                    self.priority_queue.put_nowait(entry)
                    await asyncio.sleep(0.01)
                    continue

                # 获取信号量并执行
                async with self._semaphore:
                    BACKPRESSURE_RATE_LIMIT.labels(
                        resource=entry.resource_id
                    ).inc()
                    BACKPRESSURE_QUEUE_SIZE.set(self.priority_queue.qsize())

                    # 设置Future结果
                    entry.future.set_result(True)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    async def release(self):
        """释放资源许可"""
        # 信号量自动释放
        pass

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        current_time = time.time()
        window_start = current_time - self.config.time_window

        stats = {
            'queue_size': self.priority_queue.qsize(),
            'queue_max_size': self.config.max_queue_size,
            'max_requests': self.config.max_requests,
            'time_window': self.config.time_window,
            'resource_stats': {}
        }

        for resource_id, timestamps in self.request_counts.items():
            recent_requests = [
                t for t in timestamps if t > window_start
            ]
            stats['resource_stats'][resource_id] = {
                'requests_in_window': len(recent_requests),
                'requests_remaining': self.config.max_requests - len(recent_requests),
                'circuit_breaker_state': (
                    self._resource_circuit_breakers[resource_id].state.value
                    if resource_id in self._resource_circuit_breakers
                    else 'unknown'
                )
            }

        return stats

    async def shutdown(self):
        """关闭背压控制器"""
        logger.info("Shutting down backpressure controller...")
        # 取消队列处理任务
        # 注意：实际使用时需要保存队列处理任务的引用以便取消
