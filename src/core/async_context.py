"""
異步上下文管理器

提供異步資源管理、超時控制、並發限制等功能
"""

import asyncio
import contextvars
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncContextManager, Dict, List, Optional, Set

from src.core.logging import get_logger

logger = get_logger("async_context")


@dataclass
class AsyncContextConfig:
    """異步上下文配置"""
    max_concurrent_tasks: int = 1000
    default_timeout: float = 30.0
    enable_metrics: bool = True
    metrics_window: int = 60  # 秒


@dataclass
class ResourceTracker:
    """資源追蹤器"""
    resource_id: str
    resource_type: str
    acquired_at: float
    context_data: Dict[str, Any] = field(default_factory=dict)


class AsyncContextManager:
    """異步上下文管理器"""

    def __init__(self, config: AsyncContextConfig):
        self.config = config
        self.logger = get_logger("async_context_manager")

        # 資源追蹤
        self._resources: Dict[str, ResourceTracker] = {}
        self._resource_lock = asyncio.Lock()

        # 信號量限制
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

        # 指標
        self._active_contexts: Set[str] = set()
        self._completed_contexts = 0
        self._failed_contexts = 0
        self._total_tasks = 0
        self._start_time = time.time()

    @asynccontextmanager
    async def async_context(
        self,
        context_id: Optional[str] = None,
        timeout: Optional[float] = None,
        acquire_resources: Optional[List[str]] = None
    ):
        """
        異步上下文管理器

        Args:
            context_id: 上下文ID，自動生成如果未提供
            timeout: 上下文超時時間
            acquire_resources: 需要獲取的資源列表
        """
        ctx_id = context_id or f"ctx_{int(time.time() * 1000)}"
        effective_timeout = timeout or self.config.default_timeout
        start_time = time.time()

        # 設置當前上下文
        current_context.set(ctx_id)

        # 獲取信號量
        async with self._semaphore:
            self._active_contexts.add(ctx_id)
            self._total_tasks += 1

            # 獲取資源
            acquired_resources = []
            try:
                if acquire_resources:
                    for resource_id in acquire_resources:
                        resource = await self._acquire_resource(resource_id)
                        if resource:
                            acquired_resources.append(resource)

                # 創建上下文
                context_data = {
                    "context_id": ctx_id,
                    "start_time": start_time,
                    "timeout": effective_timeout,
                    "acquired_resources": acquired_resources
                }

                self.logger.debug(f"Context started: {ctx_id}", extra=context_data)

                try:
                    # 使用戶代碼
                    yield context_data

                    elapsed = time.time() - start_time
                    if elapsed > effective_timeout:
                        self.logger.warning(
                            f"Context {ctx_id} exceeded timeout: {elapsed:.2f}s > {effective_timeout}s"
                        )

                except asyncio.TimeoutError:
                    self.logger.error(f"Context {ctx_id} timed out after {effective_timeout}s")
                    raise
                except Exception as e:
                    self.logger.error(f"Context {ctx_id} failed: {e}")
                    self._failed_contexts += 1
                    raise
                finally:
                    elapsed = time.time() - start_time
                    self.logger.debug(
                        f"Context completed: {ctx_id} in {elapsed:.2f}s",
                        extra={"context_id": ctx_id, "duration": elapsed}
                    )
                    self._completed_contexts += 1

            finally:
                # 釋放資源
                for resource in acquired_resources:
                    await self._release_resource(resource.resource_id)

                self._active_contexts.discard(ctx_id)

    async def _acquire_resource(self, resource_id: str) -> Optional[ResourceTracker]:
        """獲取資源"""
        async with self._resource_lock:
            if resource_id in self._resources:
                self.logger.warning(f"Resource {resource_id} already acquired")
                return None

            tracker = ResourceTracker(
                resource_id=resource_id,
                resource_type="generic",
                acquired_at=time.time()
            )
            self._resources[resource_id] = tracker
            self.logger.debug(f"Resource acquired: {resource_id}")
            return tracker

    async def _release_resource(self, resource_id: str) -> None:
        """釋放資源"""
        async with self._resource_lock:
            if resource_id in self._resources:
                del self._resources[resource_id]
                self.logger.debug(f"Resource released: {resource_id}")

    async def acquire_semaphore(self, context_id: Optional[str] = None) -> str:
        """
        手動獲取信號量

        Returns:
            獲取令牌ID
        """
        await self._semaphore.acquire()
        token_id = f"token_{int(time.time() * 1000)}"
        current_ctx = current_context.get()
        self.logger.debug(f"Semaphore acquired by {current_ctx or context_id}: {token_id}")
        return token_id

    def release_semaphore(self, token_id: str) -> None:
        """釋放信號量"""
        self._semaphore.release()
        current_ctx = current_context.get()
        self.logger.debug(f"Semaphore released by {current_ctx}: {token_id}")

    async def with_timeout(
        self,
        coro,
        timeout: Optional[float] = None,
        context_id: Optional[str] = None
    ):
        """
        異步超時包裝器

        Args:
            coro: 異步協程
            timeout: 超時時間
            context_id: 上下文ID

        Returns:
            協程結果或超時異常
        """
        effective_timeout = timeout or self.config.default_timeout
        ctx_id = context_id or current_context.get()

        try:
            return await asyncio.wait_for(coro, timeout=effective_timeout)
        except asyncio.TimeoutError:
            self.logger.error(f"Operation timed out after {effective_timeout}s in context {ctx_id}")
            raise

    async def batch_execute(
        self,
        tasks: List[asyncio.Task],
        max_concurrent: Optional[int] = None,
        return_exceptions: bool = True
    ) -> List[Any]:
        """
        批量執行異步任務

        Args:
            tasks: 異步任務列表
            max_concurrent: 最大並發數
            return_exceptions: 是否返回異常

        Returns:
            執行結果列表
        """
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent_tasks

        # 分批執行
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=return_exceptions)
            results.extend(batch_results)

        return results

    async def run_with_retry(
        self,
        coro,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        帶重試的異步執行

        Args:
            coro: 異步協程
            max_retries: 最大重試次數
            retry_delay: 初始重試延遲
            backoff_factor: 退避因子
            exceptions: 需要重試的異常類型

        Returns:
            協程結果
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await coro
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    delay = retry_delay * (backoff_factor ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {max_retries + 1} attempts failed")
                    break

        raise last_exception or Exception("Max retries exceeded")

    def get_context_id(self) -> str:
        """獲取當前上下文ID"""
        return current_context.get()

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取指標"""
        uptime = time.time() - self._start_time

        return {
            "active_contexts": len(self._active_contexts),
            "active_contexts_list": list(self._active_contexts),
            "completed_contexts": self._completed_contexts,
            "failed_contexts": self._failed_contexts,
            "total_tasks": self._total_tasks,
            "success_rate": (
                self._completed_contexts / max(self._total_tasks, 1) * 100
            ),
            "resources": {
                "total": len(self._resources),
                "list": [
                    {
                        "resource_id": r.resource_id,
                        "resource_type": r.resource_type,
                        "acquired_at": r.acquired_at
                    }
                    for r in self._resources.values()
                ]
            },
            "semaphore": {
                "max_value": self.config.max_concurrent_tasks,
                "acquired": self._semaphore._value,  # 獲取剩餘許可數
                "waiting": self._semaphore._waiters._qsize()  # 等待數量
            },
            "uptime": uptime,
            "average_task_duration": (
                uptime / max(self._total_tasks, 1) if self._total_tasks > 0 else 0
            )
        }


# 全局上下文變量
current_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_context",
    default="default"
)

# 全局異步上下文管理器
_global_async_context: Optional[AsyncContextManager] = None


def get_async_context(config: Optional[AsyncContextConfig] = None) -> AsyncContextManager:
    """獲取全局異步上下文管理器"""
    global _global_async_context
    if _global_async_context is None:
        if config is None:
            config = AsyncContextConfig()
        _global_async_context = AsyncContextManager(config)
    return _global_async_context


@asynccontextmanager
async def async_operation(
    context_id: Optional[str] = None,
    timeout: Optional[float] = None,
    acquire_resources: Optional[List[str]] = None
):
    """
    異步操作上下文管理器 - 全局實例

    Example:
        async with async_operation(context_id="my_op", timeout=10.0):
            # 異步操作
            await some_async_function()
    """
    context_manager = get_async_context()
    async with context_manager.async_context(
        context_id=context_id,
        timeout=timeout,
        acquire_resources=acquire_resources
    ):
        yield


async def with_timeout(coro, timeout: Optional[float] = None):
    """帶超時的異步執行 - 全局實例"""
    context_manager = get_async_context()
    return await context_manager.with_timeout(coro, timeout)


async def batch_execute(tasks: List[asyncio.Task], max_concurrent: Optional[int] = None):
    """批量執行任務 - 全局實例"""
    context_manager = get_async_context()
    return await context_manager.batch_execute(tasks, max_concurrent)


async def run_with_retry(
    coro,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """帶重試的異步執行 - 全局實例"""
    context_manager = get_async_context()
    return await context_manager.run_with_retry(
        coro, max_retries, retry_delay, backoff_factor, exceptions
    )
