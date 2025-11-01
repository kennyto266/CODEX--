"""
緩存失效策略管理器

支持多種緩存失效策略：
- TTL (Time To Live)
- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- FIFO (First In First Out)
- 手動失效
- 基於依賴的失效
- 事件驅動失效
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4

from src.core.logging import get_logger

logger = get_logger("cache_invalidation")


class InvalidationStrategy(Enum):
    """緩存失效策略類型"""
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    MANUAL = "manual"
    DEPENDENCY = "dependency"
    EVENT_DRIVEN = "event_driven"


@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    strategy: Optional[InvalidationStrategy] = None
    expires_at: Optional[float] = None


class InvalidationPolicy(ABC):
    """緩存失效策略抽象基類"""

    @abstractmethod
    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        """判斷哪些條目應該被驅逐"""
        pass

    @abstractmethod
    async def on_access(self, entry: CacheEntry):
        """記錄訪問"""
        pass

    @abstractmethod
    async def on_update(self, entry: CacheEntry):
        """記錄更新"""
        pass


class TTLPolicy(InvalidationPolicy):
    """TTL失效策略"""

    def __init__(self, default_ttl: float = 3600):
        self.default_ttl = default_ttl

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        now = time.time()
        evict_keys = []

        for entry in entries:
            if entry.expires_at and entry.expires_at < now:
                evict_keys.append(entry.key)

        return evict_keys

    async def on_access(self, entry: CacheEntry):
        # TTL策略不根據訪問更新
        pass

    async def on_update(self, entry: CacheEntry):
        # 更新過期時間
        if not entry.expires_at or entry.expires_at < time.time() + self.default_ttl:
            entry.expires_at = time.time() + self.default_ttl


class LRUEvictionPolicy(InvalidationPolicy):
    """LRU失效策略"""

    def __init__(self, max_size: Optional[int] = None):
        self.max_size = max_size

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        evict_keys = []

        # 如果超過最大大小，驅逐最少最近使用的
        if self.max_size and len(entries) > self.max_size:
            sorted_entries = sorted(entries, key=lambda e: e.last_accessed)
            evict_count = len(entries) - self.max_size
            evict_keys = [e.key for e in sorted_entries[:evict_count]]

        # 驅逐過期的條目
        now = time.time()
        for entry in entries:
            if entry.expires_at and entry.expires_at < now:
                if entry.key not in evict_keys:
                    evict_keys.append(entry.key)

        return evict_keys

    async def on_access(self, entry: CacheEntry):
        entry.last_accessed = time.time()

    async def on_update(self, entry: CacheEntry):
        entry.last_accessed = time.time()


class LFUEvictionPolicy(InvalidationPolicy):
    """LFU失效策略"""

    def __init__(self, max_size: Optional[int] = None):
        self.max_size = max_size

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        evict_keys = []

        # 如果超過最大大小，驅逐最少使用頻率的
        if self.max_size and len(entries) > self.max_size:
            sorted_entries = sorted(entries, key=lambda e: e.access_count)
            evict_count = len(entries) - self.max_size
            evict_keys = [e.key for e in sorted_entries[:evict_count]]

        # 驅逐過期的條目
        now = time.time()
        for entry in entries:
            if entry.expires_at and entry.expires_at < now:
                if entry.key not in evict_keys:
                    evict_keys.append(entry.key)

        return evict_keys

    async def on_access(self, entry: CacheEntry):
        entry.access_count += 1
        entry.last_accessed = time.time()

    async def on_update(self, entry: CacheEntry):
        entry.last_accessed = time.time()


class FIFOEvictionPolicy(InvalidationPolicy):
    """FIFO失效策略"""

    def __init__(self, max_size: Optional[int] = None):
        self.max_size = max_size

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        evict_keys = []

        # 如果超過最大大小，驅逐最早創建的
        if self.max_size and len(entries) > self.max_size:
            sorted_entries = sorted(entries, key=lambda e: e.created_at)
            evict_count = len(entries) - self.max_size
            evict_keys = [e.key for e in sorted_entries[:evict_count]]

        # 驅逐過期的條目
        now = time.time()
        for entry in entries:
            if entry.expires_at and entry.expires_at < now:
                if entry.key not in evict_keys:
                    evict_keys.append(entry.key)

        return evict_keys

    async def on_access(self, entry: CacheEntry):
        pass  # FIFO不關心訪問

    async def on_update(self, entry: CacheEntry):
        pass  # FIFO不關心更新


class ManualInvalidationPolicy(InvalidationPolicy):
    """手動失效策略"""

    def __init__(self):
        self._manual_evict_keys: Set[str] = set()

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        evict_keys = list(self._manual_evict_keys)
        # 清除已處理的手動失效請求
        self._manual_evict_keys.clear()
        return evict_keys

    def invalidate_key(self, key: str):
        """手動失效指定鍵"""
        self._manual_evict_keys.add(key)

    def invalidate_pattern(self, pattern: str, entries: List[CacheEntry]) -> List[str]:
        """基於模式失效"""
        import fnmatch
        matched_keys = []

        for entry in entries:
            if fnmatch.fnmatch(entry.key, pattern):
                matched_keys.append(entry.key)
                self._manual_evict_keys.add(entry.key)

        return matched_keys

    async def on_access(self, entry: CacheEntry):
        pass

    async def on_update(self, entry: CacheEntry):
        pass


class DependencyInvalidationPolicy(InvalidationPolicy):
    """基於依賴的失效策略"""

    def __init__(self):
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_dependency_graph: Dict[str, Set[str]] = {}

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        evict_keys = []

        # 檢查過期的條目
        now = time.time()
        for entry in entries:
            if entry.expires_at and entry.expires_at < now:
                evict_keys.append(entry.key)
                # 同時失效依賴項
                evict_keys.extend(self._get_dependents(entry.key))

        return list(set(evict_keys))  # 去重

    def add_dependency(self, key: str, depends_on: str):
        """添加依賴關係"""
        if key not in self._dependency_graph:
            self._dependency_graph[key] = set()
        self._dependency_graph[key].add(depends_on)

        if depends_on not in self._reverse_dependency_graph:
            self._reverse_dependency_graph[depends_on] = set()
        self._reverse_dependency_graph[depends_on].add(key)

    def _get_dependents(self, key: str) -> List[str]:
        """獲取依賴於指定鍵的所有鍵"""
        return list(self._reverse_dependency_graph.get(key, set()))

    async def on_access(self, entry: CacheEntry):
        entry.last_accessed = time.time()

    async def on_update(self, entry: CacheEntry):
        entry.last_accessed = time.time()


class EventDrivenInvalidationPolicy(InvalidationPolicy):
    """事件驅動失效策略"""

    def __init__(self):
        self._event_handlers: Dict[str, List[Callable]] = {}

    async def should_evict(self, entries: List[CacheEntry], **kwargs) -> List[str]:
        # 檢查過期的條目
        now = time.time()
        return [
            entry.key for entry in entries
            if entry.expires_at and entry.expires_at < now
        ]

    async def on_access(self, entry: CacheEntry):
        entry.last_accessed = time.time()

    async def on_update(self, entry: CacheEntry):
        entry.last_accessed = time.time()

    def register_event_handler(self, event_type: str, handler: Callable):
        """註冊事件處理器"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def emit_event(self, event_type: str, **kwargs):
        """發射事件"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(**kwargs)
            except Exception as e:
                logger.error(f"Event handler error: {e}")


class CacheInvalidationManager:
    """緩存失效管理器"""

    def __init__(self):
        self.logger = get_logger("cache_invalidation_manager")
        self._policies: Dict[InvalidationStrategy, InvalidationPolicy] = {}
        self._active_strategy = InvalidationStrategy.LRU
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        # 初始化默認策略
        self._init_default_policies()

    def _init_default_policies(self):
        """初始化默認策略"""
        self._policies[InvalidationStrategy.TTL] = TTLPolicy()
        self._policies[InvalidationStrategy.LRU] = LRUEvictionPolicy(max_size=10000)
        self._policies[InvalidationStrategy.LFU] = LFUEvictionPolicy(max_size=10000)
        self._policies[InvalidationStrategy.FIFO] = FIFOEvictionPolicy(max_size=10000)
        self._policies[InvalidationStrategy.MANUAL] = ManualInvalidationPolicy()
        self._policies[InvalidationStrategy.DEPENDENCY] = DependencyInvalidationPolicy()
        self._policies[InvalidationStrategy.EVENT_DRIVEN] = EventDrivenInvalidationPolicy()

    def set_strategy(self, strategy: InvalidationStrategy):
        """設置失效策略"""
        self._active_strategy = strategy
        self.logger.info(f"Cache invalidation strategy set to: {strategy.value}")

    def get_policy(self, strategy: Optional[InvalidationStrategy] = None) -> InvalidationPolicy:
        """獲取失效策略"""
        strategy = strategy or self._active_strategy
        return self._policies[strategy]

    async def should_evict(
        self,
        entries: List[CacheEntry],
        strategy: Optional[InvalidationStrategy] = None
    ) -> List[str]:
        """判斷需要驅逐的鍵"""
        policy = self.get_policy(strategy)
        evict_keys = await policy.should_evict(entries)

        if evict_keys:
            self.logger.debug(f"Evicting keys: {evict_keys}")

        return evict_keys

    async def on_cache_access(
        self,
        entry: CacheEntry,
        strategy: Optional[InvalidationStrategy] = None
    ):
        """記錄緩存訪問"""
        policy = self.get_policy(strategy)
        await policy.on_access(entry)

    async def on_cache_update(
        self,
        entry: CacheEntry,
        strategy: Optional[InvalidationStrategy] = None
    ):
        """記錄緩存更新"""
        policy = self.get_policy(strategy)
        await policy.on_update(entry)

    def invalidate_key(self, key: str, strategy: Optional[InvalidationStrategy] = None):
        """手動失效鍵"""
        strategy = strategy or InvalidationStrategy.MANUAL
        policy = self.get_policy(strategy)

        if isinstance(policy, ManualInvalidationPolicy):
            policy.invalidate_key(key)
            self.logger.info(f"Manually invalidated key: {key}")

    def invalidate_pattern(
        self,
        pattern: str,
        entries: List[CacheEntry],
        strategy: Optional[InvalidationStrategy] = None
    ) -> List[str]:
        """基於模式失效"""
        strategy = strategy or InvalidationStrategy.MANUAL
        policy = self.get_policy(strategy)

        if isinstance(policy, ManualInvalidationPolicy):
            matched_keys = policy.invalidate_pattern(pattern, entries)
            self.logger.info(f"Invalidated {len(matched_keys)} keys matching pattern: {pattern}")
            return matched_keys

        return []

    def add_dependency(self, key: str, depends_on: str):
        """添加依賴關係"""
        policy = self.get_policy(InvalidationStrategy.DEPENDENCY)
        if isinstance(policy, DependencyInvalidationPolicy):
            policy.add_dependency(key, depends_on)
            self.logger.info(f"Added dependency: {key} -> {depends_on}")

    def register_event_handler(self, event_type: str, handler: Callable):
        """註冊事件處理器"""
        policy = self.get_policy(InvalidationStrategy.EVENT_DRIVEN)
        if isinstance(policy, EventDrivenInvalidationPolicy):
            policy.register_event_handler(event_type, handler)
            self.logger.info(f"Registered event handler for: {event_type}")

    async def emit_event(self, event_type: str, **kwargs):
        """發射事件"""
        policy = self.get_policy(InvalidationStrategy.EVENT_DRIVEN)
        if isinstance(policy, EventDrivenInvalidationPolicy):
            await policy.emit_event(event_type, **kwargs)

    async def start_cleanup_task(self, interval: int = 60):
        """啟動定期清理任務"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(interval))
        self.logger.info(f"Started cache cleanup task (interval: {interval}s)")

    async def stop_cleanup_task(self):
        """停止定期清理任務"""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped cache cleanup task")

    async def _cleanup_loop(self, interval: int):
        """清理循環"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break

                # 執行清理操作
                await self._perform_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")

    async def _perform_cleanup(self):
        """執行清理操作"""
        self.logger.debug("Performing cache cleanup...")
        # 這裡可以添加自定義清理邏輯
        # 例如：清理過期的統計信息、優化數據庫等


# 全局失效管理器
_global_invalidation_manager: Optional[CacheInvalidationManager] = None


def get_invalidation_manager() -> CacheInvalidationManager:
    """獲取全局失效管理器"""
    global _global_invalidation_manager
    if _global_invalidation_manager is None:
        _global_invalidation_manager = CacheInvalidationManager()
    return _global_invalidation_manager


# 便捷函數
async def should_evict_cache(
    entries: List[CacheEntry],
    strategy: InvalidationStrategy = InvalidationStrategy.LRU
) -> List[str]:
    """判斷需要驅逐的緩存鍵"""
    manager = get_invalidation_manager()
    return await manager.should_evict(entries, strategy)


def invalidate_cache_key(key: str, strategy: InvalidationStrategy = InvalidationStrategy.MANUAL):
    """手動失效緩存鍵"""
    manager = get_invalidation_manager()
    manager.invalidate_key(key, strategy)


def invalidate_cache_pattern(pattern: str, entries: List[CacheEntry]):
    """基於模式失效緩存"""
    manager = get_invalidation_manager()
    return manager.invalidate_pattern(pattern, entries)


def add_cache_dependency(key: str, depends_on: str):
    """添加緩存依賴"""
    manager = get_invalidation_manager()
    manager.add_dependency(key, depends_on)


async def emit_cache_event(event_type: str, **kwargs):
    """發射緩存事件"""
    manager = get_invalidation_manager()
    await manager.emit_event(event_type, **kwargs)
