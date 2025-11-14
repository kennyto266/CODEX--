"""
垃圾回收优化模块 - 内存优化
实现引用计数、弱引用、及时释放和循环检测等高级功能
"""

import gc
import sys
import logging
import weakref
import threading
import time
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import tracemalloc
import cProfile
import pstats
import io
import inspect

logger = logging.getLogger("hk_quant.performance.gc")

@dataclass
class GCConfig:
    """垃圾回收配置"""
    auto_gc_enabled: bool = True
    gc_threshold: Tuple[int, int, int] = (700, 10, 10)  # 降低阈值，更频繁回收
    track_memory: bool = True
    profile_gc: bool = False
    cycle_detection: bool = True
    weak_ref_cleanup: bool = True

@dataclass
class GCStats:
    """垃圾回收统计"""
    collections_gen0: int = 0
    collections_gen1: int = 0
    collections_gen2: int = 0
    total_collected: int = 0
    cycle_detections: int = 0
    weak_refs_cleaned: int = 0
    memory_freed_mb: float = 0.0
    gc_time_ms: float = 0.0
    last_gc_time: float = 0.0

class ReferenceTracker:
    """引用追踪器"""

    def __init__(self):
        self._refs: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._ref_counts: Dict[int, int] = defaultdict(int)
        self._ref_lock = threading.Lock()

    def track_object(self, obj: Any, ref_type: str = "unknown") -> int:
        """追踪对象引用"""
        with self._ref_lock:
            obj_id = id(obj)
            self._refs[obj] = {
                "ref_type": ref_type,
                "created_at": time.time(),
                "ref_count": 0
            }
            self._ref_counts[obj_id] += 1
            return self._ref_counts[obj_id]

    def untrack_object(self, obj: Any) -> bool:
        """取消追踪对象"""
        with self._ref_lock:
            obj_id = id(obj)
            if obj_id in self._ref_counts:
                self._ref_counts[obj_id] -= 1
                if self._ref_counts[obj_id] <= 0:
                    del self._ref_counts[obj_id]
                    if obj in self._refs:
                        del self._refs[obj]
                    return True
            return False

    def get_ref_count(self, obj: Any) -> int:
        """获取引用计数"""
        with self._ref_lock:
            return self._ref_counts.get(id(obj), 0)

    def get_tracked_objects(self) -> List[Tuple[Any, Dict]]:
        """获取所有追踪的对象"""
        with self._ref_lock:
            return list(self._refs.items())

    def detect_reference_cycles(self) -> List[List[Any]]:
        """检测引用循环"""
        # 简化的循环检测
        cycles = []
        visited = set()

        for obj in self._refs.keys():
            if id(obj) not in visited:
                cycle = self._dfs_cycle(obj, visited, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def _dfs_cycle(self, obj: Any, visited: Set[int], path: List[Any]) -> Optional[List[Any]]:
        """深度优先搜索循环"""
        obj_id = id(obj)

        if obj_id in visited:
            # 找到循环
            cycle_start = None
            for i, item in enumerate(path):
                if id(item) == obj_id:
                    cycle_start = i
                    break

            if cycle_start is not None:
                return path[cycle_start:]

            return None

        visited.add(obj_id)
        current_path = path + [obj]

        # 检查对象的属性
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(obj, attr_name)
                    if hasattr(attr_value, '__iter__') and not isinstance(attr_value, (str, bytes)):
                        for item in attr_value:
                            if hasattr(item, '__dict__'):
                                cycle = self._dfs_cycle(item, visited, current_path)
                                if cycle:
                                    return cycle
                except:
                    pass

        return None


class WeakRefManager:
    """弱引用管理器"""

    def __init__(self):
        self._weak_refs: Dict[str, weakref.ref] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._cleanup_count = 0

    def create_weak_ref(self, obj: Any, name: str, callback: Optional[Callable] = None) -> bool:
        """创建弱引用"""
        try:
            ref = weakref.ref(obj)

            if callback:
                def weak_callback(ref):
                    self._cleanup_count += 1
                    if name in self._callbacks:
                        try:
                            self._callbacks[name](obj)
                        except Exception as e:
                            logger.error(f"弱引用回调错误: {e}")

                ref2 = weakref.ref(obj, weak_callback)
                self._weak_refs[name] = ref2
            else:
                self._weak_refs[name] = ref

            if callback:
                self._callbacks[name] = callback

            return True
        except Exception as e:
            logger.error(f"创建弱引用失败: {e}")
            return False

    def get_weak_ref(self, name: str) -> Optional[Any]:
        """获取弱引用对象"""
        if name in self._weak_refs:
            ref = self._weak_refs[name]
            obj = ref()
            if obj is None:
                # 对象已被回收，清理弱引用
                del self._weak_refs[name]
                if name in self._callbacks:
                    del self._callbacks[name]
            return obj
        return None

    def cleanup_dead_refs(self) -> int:
        """清理已死的弱引用"""
        dead_refs = []
        for name, ref in self._weak_refs.items():
            if ref() is None:
                dead_refs.append(name)

        for name in dead_refs:
            del self._weak_refs[name]
            if name in self._callbacks:
                del self._callbacks[name]

        self._cleanup_count += len(dead_refs)
        return len(dead_refs)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        alive_refs = sum(1 for ref in self._weak_refs.values() if ref() is not None)
        dead_refs = len(self._weak_refs) - alive_refs

        return {
            "total_refs": len(self._weak_refs),
            "alive_refs": alive_refs,
            "dead_refs": dead_refs,
            "total_cleanups": self._cleanup_count
        }


class ObjectPool:
    """对象池 - 减少对象创建和销毁"""

    def __init__(self, factory: Callable, max_size: int = 100, reset_func: Optional[Callable] = None):
        self.factory = factory
        self.max_size = max_size
        self.reset_func = reset_func
        self._pool: List[Any] = []
        self._lock = threading.Lock()
        self._stats = {
            "created": 0,
            "reused": 0,
            "returned": 0,
            "evicted": 0
        }

    def acquire(self) -> Any:
        """获取对象"""
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                self._stats["reused"] += 1
            else:
                obj = self.factory()
                self._stats["created"] += 1

            return obj

    def release(self, obj: Any) -> bool:
        """归还对象"""
        if self.reset_func:
            try:
                self.reset_func(obj)
            except Exception as e:
                logger.error(f"对象重置失败: {e}")
                return False

        with self._lock:
            if len(self._pool) < self.max_size:
                self._pool.append(obj)
                self._stats["returned"] += 1
                return True
            else:
                self._stats["evicted"] += 1
                return False

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        with self._lock:
            return {
                **self._stats,
                "pool_size": len(self._pool)
            }

    def clear(self):
        """清空对象池"""
        with self._lock:
            self._pool.clear()


class MemoryProfiler:
    """内存性能分析器"""

    def __init__(self):
        self._snapshots = []
        self._profilers: Dict[str, cProfile.Profile] = {}

    def start_memory_tracking(self):
        """开始内存跟踪"""
        tracemalloc.start()

    def stop_memory_tracking(self) -> Optional[tracemalloc.Snapshot]:
        """停止内存跟踪并返回快照"""
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            return snapshot
        return None

    def get_memory_stats(self) -> Optional[Dict[str, Any]]:
        """获取内存统计"""
        if not tracemalloc.is_tracing():
            return None

        current, peak = tracemalloc.get_traced_memory()
        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024
        }

    def take_snapshot(self, name: str) -> bool:
        """保存内存快照"""
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self._snapshots.append((name, time.time(), snapshot))
            return True
        return False

    def compare_snapshots(self, name1: str, name2: str) -> Optional[List]:
        """比较两个快照"""
        snap1 = None
        snap2 = None

        for n, t, s in self._snapshots:
            if n == name1:
                snap1 = s
            elif n == name2:
                snap2 = s

        if snap1 and snap2:
            return snap2.compare_to(snap1, 'lineno')
        return None

    def start_profiler(self, name: str):
        """启动性能分析器"""
        if name not in self._profilers:
            self._profilers[name] = cProfile.Profile()
        self._profilers[name].enable()

    def stop_profiler(self, name: str) -> Optional[pstats.Stats]:
        """停止性能分析器并返回统计"""
        if name in self._profilers:
            self._profilers[name].disable()
            stats = pstats.Stats(self._profilers[name])
            return stats
        return None


class AdvancedGarbageCollector:
    """高级垃圾回收器"""

    def __init__(self, config: Optional[GCConfig] = None):
        self.config = config or GCConfig()
        self.stats = GCStats()
        self.ref_tracker = ReferenceTracker()
        self.weak_ref_manager = WeakRefManager()
        self.profiler = MemoryProfiler()

        # 对象池
        self._pools: Dict[str, ObjectPool] = {}

        # 线程安全
        self._lock = threading.RLock()

        # 自动垃圾回收线程
        self._gc_thread = None
        self._gc_running = False

        # 初始化
        self._init_gc()
        self._start_auto_gc()

        logger.info("高级垃圾回收器初始化完成")

    def _init_gc(self):
        """初始化垃圾回收"""
        # 启用自动垃圾回收
        gc.enable()

        # 设置阈值
        if self.config.auto_gc_enabled:
            gc.set_threshold(*self.config.gc_threshold)
            logger.info(f"设置GC阈值: {self.config.gc_threshold}")

        # 启动内存跟踪
        if self.config.track_memory:
            self.profiler.start_memory_tracking()

    def _start_auto_gc(self):
        """启动自动垃圾回收线程"""
        if self.config.auto_gc_enabled:
            self._gc_running = True
            self._gc_thread = threading.Thread(target=self._auto_gc_loop, daemon=True)
            self._gc_thread.start()
            logger.info("自动垃圾回收线程已启动")

    def _auto_gc_loop(self):
        """自动垃圾回收循环"""
        while self._gc_running:
            try:
                time.sleep(10)  # 每10秒检查一次

                # 获取当前内存
                if self.config.track_memory:
                    memory_stats = self.profiler.get_memory_stats()
                    if memory_stats:
                        current_mb = memory_stats["current_mb"]
                        peak_mb = memory_stats["peak_mb"]

                        # 如果内存使用超过阈值，执行垃圾回收
                        if current_mb > self.config.gc_threshold[0]:
                            self.force_collection(reason="auto")

                        # 保存内存峰值快照
                        if peak_mb > 1024:  # 1GB
                            self.profiler.take_snapshot(f"peak_{int(peak_mb)}MB")

            except Exception as e:
                logger.error(f"自动GC循环错误: {e}")

    def force_collection(self, generation: int = -1, reason: str = "manual") -> Dict[str, Any]:
        """强制垃圾回收"""
        start_time = time.time()
        collected_before = gc.get_count()

        # 执行垃圾回收
        if generation == -1:
            collected = gc.collect()
        else:
            collected = gc.collect(generation)

        collected_after = gc.get_count()
        gc_time = (time.time() - start_time) * 1000

        # 更新统计
        for i in range(3):
            self.stats.collections_gen0 += collected_after[i] - collected_before[i]

        self.stats.total_collected += collected
        self.stats.gc_time_ms += gc_time
        self.stats.last_gc_time = gc_time

        # 清理弱引用
        if self.config.weak_ref_cleanup:
            cleaned = self.weak_ref_manager.cleanup_dead_refs()
            self.stats.weak_refs_cleaned += cleaned

        # 清理对象池
        for pool in self._pools.values():
            pool.clear()

        logger.info(f"垃圾回收完成 (原因: {reason}): 收集 {collected} 对象, 耗时 {gc_time:.2f}ms")

        return {
            "collected": collected,
            "time_ms": gc_time,
            "reason": reason
        }

    def detect_cycles(self) -> List[List[Any]]:
        """检测引用循环"""
        if not self.config.cycle_detection:
            return []

        cycles = self.ref_tracker.detect_reference_cycles()
        self.stats.cycle_detections += len(cycles)

        if cycles:
            logger.warning(f"检测到 {len(cycles)} 个引用循环")
            for i, cycle in enumerate(cycles):
                logger.debug(f"循环 {i+1}: {[str(obj)[:50] for obj in cycle]}")

        return cycles

    def create_object_pool(self, name: str, factory: Callable, max_size: int = 100,
                          reset_func: Optional[Callable] = None) -> ObjectPool:
        """创建对象池"""
        with self._lock:
            pool = ObjectPool(factory, max_size, reset_func)
            self._pools[name] = pool
            return pool

    def track_object(self, obj: Any, ref_type: str = "unknown") -> int:
        """追踪对象引用"""
        return self.ref_tracker.track_object(obj, ref_type)

    def create_weak_ref(self, obj: Any, name: str, callback: Optional[Callable] = None) -> bool:
        """创建弱引用"""
        return self.weak_ref_manager.create_weak_ref(obj, name, callback)

    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        memory_stats = self.profiler.get_memory_stats()
        gc_counts = gc.get_count()

        return {
            "memory": memory_stats,
            "gc_counts": {
                "gen0": gc_counts[0],
                "gen1": gc_counts[1],
                "gen2": gc_counts[2]
            },
            "gc_threshold": gc.get_threshold(),
            "stats": {
                "collections_gen0": self.stats.collections_gen0,
                "collections_gen1": self.stats.collections_gen1,
                "collections_gen2": self.stats.collections_gen2,
                "total_collected": self.stats.total_collected,
                "cycle_detections": self.stats.cycle_detections,
                "weak_refs_cleaned": self.stats.weak_refs_cleaned,
                "gc_time_ms": self.stats.gc_time_ms,
                "last_gc_time": self.stats.last_gc_time
            }
        }

    def get_ref_stats(self) -> Dict[str, Any]:
        """获取引用统计"""
        tracked = self.ref_tracker.get_tracked_objects()
        ref_types = defaultdict(int)
        for obj, info in tracked:
            ref_types[info["ref_type"]] += 1

        return {
            "total_tracked": len(tracked),
            "ref_types": dict(ref_types),
            "weak_ref_stats": self.weak_ref_manager.get_stats(),
            "pool_stats": {name: pool.get_stats() for name, pool in self._pools.items()}
        }

    def shutdown(self):
        """关闭垃圾回收器"""
        logger.info("关闭垃圾回收器")

        # 停止自动GC线程
        self._gc_running = False
        if self._gc_thread:
            self._gc_thread.join(timeout=5)

        # 强制最终垃圾回收
        self.force_collection(reason="shutdown")

        # 清理对象池
        for pool in self._pools.values():
            pool.clear()

        # 停止内存跟踪
        if self.config.track_memory:
            snapshot = self.profiler.stop_memory_tracking()
            if snapshot:
                logger.info(f"最终内存状态: {snapshot.statistics('filename')[:5]}")

        logger.info("垃圾回收器已关闭")


# 全局垃圾回收器实例
_global_gc: Optional[AdvancedGarbageCollector] = None
_gc_lock = threading.Lock()

def get_global_gc() -> AdvancedGarbageCollector:
    """获取全局垃圾回收器实例"""
    global _global_gc
    with _gc_lock:
        if _global_gc is None:
            _global_gc = AdvancedGarbageCollector()
        return _global_gc


# 使用示例
def example_usage():
    """使用示例"""
    print("=" * 60)
    print("🗑️ 高级垃圾回收优化测试")
    print("=" * 60)

    # 创建配置
    config = GCConfig(
        auto_gc_enabled=True,
        gc_threshold=(100, 10, 10),  # 更敏感的阈值
        track_memory=True,
        cycle_detection=True
    )

    # 创建垃圾回收器
    gc_manager = AdvancedGarbageCollector(config)

    # 创建对象池
    def create_array():
        return np.zeros(1000000, dtype=np.float64)

    pool = gc_manager.create_object_pool("arrays", create_array, max_size=10)

    print("\n=== 对象池测试 ===")
    # 获取和归还对象
    for i in range(15):
        obj = pool.acquire()
        pool.release(obj)
    print(f"对象池统计: {pool.get_stats()}")

    print("\n=== 引用追踪测试 ===")
    # 追踪对象
    test_obj = {"data": list(range(1000))}
    ref_count = gc_manager.track_object(test_obj, "test_object")
    print(f"对象引用计数: {ref_count}")

    # 创建弱引用
    gc_manager.create_weak_ref(test_obj, "test_weak", lambda x: print(f"对象 {x} 被回收"))

    print("\n=== 内存信息 ===")
    memory_info = gc_manager.get_memory_info()
    print(f"当前内存: {memory_info['memory']}")
    print(f"GC计数: {memory_info['gc_counts']}")

    print("\n=== 强制垃圾回收 ===")
    result = gc_manager.force_collection(reason="test")
    print(f"垃圾回收结果: {result}")

    print("\n=== 引用统计 ===")
    ref_stats = gc_manager.get_ref_stats()
    print(f"引用统计: {ref_stats}")

    # 关闭
    gc_manager.shutdown()


if __name__ == "__main__":
    example_usage()
