"""
異步Agent消息處理器

提供：
- 異步消息隊列
- 批量消息處理
- 優先級隊列
- 消息重試機制
- 消息速率限制
- 指標收集
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue, SimpleQueue
from typing import Any, Dict, List, Optional, Callable, Set
from uuid import UUID, uuid4

from src.core.logging import get_logger
from src.core.async_context import get_async_context, async_operation

logger = get_logger("async_agent_processor")


class MessagePriority(Enum):
    """消息優先級"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class AgentMessage:
    """Agent消息"""
    id: UUID = field(default_factory=uuid4)
    sender_id: str = ""
    receiver_id: str = ""
    message_type: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """支持優先級比較"""
        return self.priority.value < other.priority.value


@dataclass
class MessageMetrics:
    """消息指標"""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    messages_retried: int = 0
    average_processing_time: float = 0.0
    messages_in_queue: int = 0
    processing_rate: float = 0.0
    last_message_time: Optional[float] = None


class AsyncMessageQueue:
    """異步消息隊列"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queue = PriorityQueue(maxsize=max_size)
        self._regular_queue: List[AgentMessage] = []
        self._high_priority_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.metrics = MessageMetrics()

    async def put(self, message: AgentMessage) -> bool:
        """添加消息到隊列"""
        async with self._lock:
            try:
                if message.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
                    # 高優先級消息使用專用隊列
                    await self._high_priority_queue.put(message)
                else:
                    # 普通消息使用優先級隊列
                    self._queue.put((message.priority.value, message))

                self.metrics.messages_received += 1
                self.metrics.messages_in_queue = self.qsize()
                return True
            except:
                return False

    async def get(self) -> Optional[AgentMessage]:
        """從隊列獲取消息（優先級隊列+高優先級隊列）"""
        # 優先檢查高優先級隊列
        if not self._high_priority_queue.empty():
            try:
                message = await asyncio.wait_for(
                    self._high_priority_queue.get(),
                    timeout=0.1
                )
                self.metrics.messages_in_queue = self.qsize()
                return message
            except asyncio.TimeoutError:
                pass

        # 檢查普通優先級隊列
        try:
            _, message = self._queue.get_nowait()
            self.metrics.messages_in_queue = self.qsize()
            return message
        except:
            return None

    async def get_batch(self, size: int = 10) -> List[AgentMessage]:
        """批量獲取消息"""
        batch = []
        for _ in range(size):
            message = await self.get()
            if message is None:
                break
            batch.append(message)
        return batch

    def qsize(self) -> int:
        """獲取隊列大小"""
        return self._queue.qsize() + self._high_priority_queue.qsize()

    def empty(self) -> bool:
        """檢查隊列是否為空"""
        return self.qsize() == 0

    def full(self) -> bool:
        """檢查隊列是否已滿"""
        return self.qsize() >= self.max_size


class MessageProcessor(ABC):
    """消息處理器抽象基類"""

    @abstractmethod
    async def process(self, message: AgentMessage) -> bool:
        """處理消息"""
        pass


class RetryMessageProcessor(MessageProcessor):
    """帶重試的消息處理器"""

    def __init__(self, base_processor: MessageProcessor):
        self.base_processor = base_processor
        self.logger = get_logger("retry_processor")
        self._retry_delays = [1, 5, 10, 30]  # 重試延遲列表（秒）

    async def process(self, message: AgentMessage) -> bool:
        """處理消息，支持重試"""
        max_retries = message.max_retries or 3

        for attempt in range(max_retries + 1):
            try:
                result = await self.base_processor.process(message)
                return result

            except Exception as e:
                message.retry_count += 1
                self.logger.warning(
                    f"Message processing failed (attempt {attempt + 1}): {e}"
                )

                if attempt < max_retries:
                    # 使用指數退避
                    delay = self._retry_delays[
                        min(attempt, len(self._retry_delays) - 1)
                    ]
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"Message processing failed after {max_retries + 1} attempts"
                    )
                    return False

        return False


class RateLimitProcessor(MessageProcessor):
    """速率限制消息處理器"""

    def __init__(self, base_processor: MessageProcessor, max_rate: int = 100):
        self.base_processor = base_processor
        self.max_rate = max_rate
        self._tokens = max_rate
        self._last_update = time.time()
        self._lock = asyncio.Lock()
        self.logger = get_logger("rate_limit_processor")

    async def _acquire_token(self) -> bool:
        """獲取令牌"""
        async with self._lock:
            now = time.time()
            # 每秒填充令牌
            elapsed = now - self._last_update
            self._tokens = min(
                self.max_rate,
                self._tokens + elapsed * self.max_rate
            )
            self._last_update = now

            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    async def process(self, message: AgentMessage) -> bool:
        """處理消息，應用速率限制"""
        # 高優先級消息跳過速率限制
        if message.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
            return await self.base_processor.process(message)

        # 獲取令牌
        if not await self._acquire_token():
            self.logger.warning("Rate limit exceeded, message deferred")
            return False

        return await self.base_processor.process(message)


class AsyncAgentProcessor:
    """異步Agent消息處理器"""

    def __init__(
        self,
        agent_id: str,
        message_queue: AsyncMessageQueue,
        processor: MessageProcessor,
        max_concurrent: int = 100,
        batch_size: int = 50
    ):
        self.agent_id = agent_id
        self.message_queue = message_queue
        self.processor = processor
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size

        self.logger = get_logger(f"agent_processor.{agent_id}")
        self._running = False
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Set[asyncio.Task] = set()

    async def start(self):
        """啟動消息處理器"""
        self.logger.info(f"Starting agent processor for {self.agent_id}")
        self._running = True

        # 啟動批量處理任務
        asyncio.create_task(self._batch_processing_loop())
        self.logger.info(f"Agent processor started for {self.agent_id}")

    async def stop(self):
        """停止消息處理器"""
        self.logger.info(f"Stopping agent processor for {self.agent_id}")
        self._running = False

        # 取消所有活動任務
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

        # 等待所有任務完成
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        self.logger.info(f"Agent processor stopped for {self.agent_id}")

    async def _batch_processing_loop(self):
        """批量處理循環"""
        while self._running:
            try:
                # 批量獲取消息
                messages = await self.message_queue.get_batch(self.batch_size)

                if messages:
                    # 創建處理任務
                    for message in messages:
                        task = asyncio.create_task(
                            self._process_message(message)
                        )
                        self._active_tasks.add(task)

                        # 清理已完成任務
                        self._active_tasks = {
                            t for t in self._active_tasks if not t.done()
                        }

                    # 等待一批任務完成
                    if self._active_tasks:
                        await asyncio.gather(
                            *self._active_tasks,
                            return_exceptions=True
                        )
                        self._active_tasks.clear()

                else:
                    # 沒有消息，短暫休眠
                    await asyncio.sleep(0.01)

            except Exception as e:
                self.logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message: AgentMessage) -> bool:
        """處理單個消息"""
        async with self._semaphore:
            async with async_operation(
                context_id=f"msg_{message.id}",
                timeout=message.timeout
            ):
                start_time = time.time()

                try:
                    # 處理消息
                    success = await self.processor.process(message)

                    # 更新指標
                    elapsed = time.time() - start_time
                    await self._update_metrics(success, elapsed)

                    return success

                except Exception as e:
                    self.logger.error(
                        f"Message processing failed: {e}",
                        extra={"message_id": str(message.id)}
                    )
                    await self._update_metrics(False, time.time() - start_time)
                    return False

    async def _update_metrics(self, success: bool, processing_time: float):
        """更新處理指標"""
        self.message_queue.metrics.messages_processed += 1

        if not success:
            self.message_queue.metrics.messages_failed += 1
        else:
            # 更新平均處理時間
            current_avg = self.message_queue.metrics.average_processing_time
            count = self.message_queue.metrics.messages_processed
            self.message_queue.metrics.average_processing_time = (
                (current_avg * (count - 1) + processing_time) / count
            )

        # 更新處理速率
        now = time.time()
        if self.message_queue.metrics.last_message_time:
            elapsed = now - self.message_queue.metrics.last_message_time
            if elapsed > 0:
                self.message_queue.metrics.processing_rate = 1 / elapsed

        self.message_queue.metrics.last_message_time = now

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取處理器指標"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "max_concurrent": self.max_concurrent,
            "batch_size": self.batch_size,
            "active_tasks": len(self._active_tasks),
            "queue_metrics": {
                "messages_received": self.message_queue.metrics.messages_received,
                "messages_processed": self.message_queue.metrics.messages_processed,
                "messages_failed": self.message_queue.metrics.messages_failed,
                "messages_retried": self.message_queue.metrics.messages_retried,
                "average_processing_time": self.message_queue.metrics.average_processing_time,
                "messages_in_queue": self.message_queue.metrics.messages_in_queue,
                "processing_rate": self.message_queue.metrics.processing_rate,
                "queue_size": self.message_queue.qsize()
            }
        }


class AsyncMessageRouter:
    """異步消息路由器"""

    def __init__(self):
        self.logger = get_logger("message_router")
        self._agents: Dict[str, AsyncAgentProcessor] = {}
        self._agent_subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def register_agent(self, agent_id: str, processor: AsyncAgentProcessor):
        """註冊Agent"""
        async with self._lock:
            self._agents[agent_id] = processor
            self.logger.info(f"Agent registered: {agent_id}")

    async def unregister_agent(self, agent_id: str):
        """註銷Agent"""
        async with self._lock:
            if agent_id in self._agents:
                await self._agents[agent_id].stop()
                del self._agents[agent_id]
                del self._agent_subscriptions[agent_id]
                self.logger.info(f"Agent unregistered: {agent_id}")

    async def send_message(self, message: AgentMessage) -> bool:
        """發送消息"""
        receiver_id = message.receiver_id

        async with self._lock:
            # 檢查是否有特定接收者
            if receiver_id in self._agents:
                queue = self._agents[receiver_id].message_queue
                return await queue.put(message)

            # 廣播消息
            subscribed_agents = self._agent_subscriptions.get(message.message_type, set())
            success_count = 0

            for agent_id in subscribed_agents:
                if agent_id in self._agents:
                    queue = self._agents[agent_id].message_queue
                    if await queue.put(message):
                        success_count += 1

            return success_count > 0

    async def subscribe(self, agent_id: str, message_type: str):
        """訂閱消息類型"""
        async with self._lock:
            if message_type not in self._agent_subscriptions:
                self._agent_subscriptions[message_type] = set()
            self._agent_subscriptions[message_type].add(agent_id)
            self.logger.info(f"Agent {agent_id} subscribed to {message_type}")

    async def get_routing_stats(self) -> Dict[str, Any]:
        """獲取路由統計"""
        async with self._lock:
            return {
                "registered_agents": list(self._agents.keys()),
                "message_types": list(self._agent_subscriptions.keys()),
                "total_subscriptions": sum(
                    len(subs) for subs in self._agent_subscriptions.values()
                )
            }


# 全局消息路由器
_global_router: Optional[AsyncMessageRouter] = None


def get_message_router() -> AsyncMessageRouter:
    """獲取全局消息路由器"""
    global _global_router
    if _global_router is None:
        _global_router = AsyncMessageRouter()
    return _global_router


def create_agent_message(
    sender_id: str,
    receiver_id: str,
    message_type: str,
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
    max_retries: int = 3
) -> AgentMessage:
    """創建Agent消息"""
    return AgentMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=message_type,
        content=content,
        priority=priority,
        max_retries=max_retries
    )


async def send_agent_message(
    sender_id: str,
    receiver_id: str,
    message_type: str,
    content: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL
) -> bool:
    """發送Agent消息 - 全局接口"""
    router = get_message_router()
    message = create_agent_message(sender_id, receiver_id, message_type, content, priority)
    return await router.send_message(message)
