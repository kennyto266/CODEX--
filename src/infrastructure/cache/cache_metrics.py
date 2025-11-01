"""
緩存監控和指標收集

提供：
- 實時性能指標
- 緩存命中率統計
- 緩存大小監控
- 性能趨勢分析
- 告警機制
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from threading import Lock

from src.core.logging import get_logger

logger = get_logger("cache_metrics")


@dataclass
class CacheMetricsSnapshot:
    """緩存指標快照"""
    timestamp: float
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    cache_size: int = 0
    memory_usage_bytes: int = 0
    hit_ratio: float = 0.0
    average_latency_ms: float = 0.0
    throughput_ops_per_sec: float = 0.0


@dataclass
class CacheAlert:
    """緩存告警"""
    alert_id: str
    alert_type: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    timestamp: float
    threshold: Optional[float] = None
    current_value: Optional[float] = None


class CacheMetricsCollector:
    """緩存指標收集器"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.logger = get_logger("cache_metrics_collector")

        # 計數器
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._evictions = 0
        self._errors = 0

        # 時延統計
        self._latencies = deque(maxlen=max_history)
        self._lock = Lock()

        # 歷史數據
        self._history: List[CacheMetricsSnapshot] = []

        # 告警
        self._alerts: List[CacheAlert] = []
        self._alert_handlers: List[Callable[[CacheAlert], None]] = []

        # 告警閾值
        self._thresholds = {
            "hit_ratio_min": 0.8,  # 命中率最低80%
            "latency_max_ms": 100,  # 時延最大100ms
            "eviction_rate_max": 0.1,  # 驅逐率最大10%
            "error_rate_max": 0.05,  # 錯誤率最大5%
        }

    def record_hit(self, latency_ms: float = 0.0):
        """記錄緩存命中"""
        with self._lock:
            self._hits += 1
            if latency_ms > 0:
                self._latencies.append(latency_ms)

    def record_miss(self, latency_ms: float = 0.0):
        """記錄緩存未命中"""
        with self._lock:
            self._misses += 1
            if latency_ms > 0:
                self._latencies.append(latency_ms)

    def record_set(self, latency_ms: float = 0.0):
        """記錄緩存設置"""
        with self._lock:
            self._sets += 1
            if latency_ms > 0:
                self._latencies.append(latency_ms)

    def record_delete(self, latency_ms: float = 0.0):
        """記錄緩存刪除"""
        with self._lock:
            self._deletes += 1
            if latency_ms > 0:
                self._latencies.append(latency_ms)

    def record_eviction(self, latency_ms: float = 0.0):
        """記錄緩存驅逐"""
        with self._lock:
            self._evictions += 1
            if latency_ms > 0:
                self._latencies.append(latency_ms)

    def record_error(self):
        """記錄錯誤"""
        with self._lock:
            self._errors += 1

    def get_current_metrics(self, cache_size: int = 0, memory_usage: int = 0) -> CacheMetricsSnapshot:
        """獲取當前指標"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = self._hits / max(total_requests, 1)
            error_rate = self._errors / max(total_requests, 1)

            # 計算平均時延
            avg_latency = sum(self._latencies) / max(len(self._latencies), 1)

            # 計算吞吐量 (請求/秒)
            throughput = 0.0
            if len(self._history) >= 2:
                time_diff = self._history[-1].timestamp - self._history[0].timestamp
                if time_diff > 0:
                    throughput = total_requests / time_diff

            metrics = CacheMetricsSnapshot(
                timestamp=time.time(),
                hits=self._hits,
                misses=self._misses,
                sets=self._sets,
                deletes=self._deletes,
                evictions=self._evictions,
                cache_size=cache_size,
                memory_usage_bytes=memory_usage,
                hit_ratio=hit_ratio,
                average_latency_ms=avg_latency,
                throughput_ops_per_sec=throughput
            )

            return metrics

    def take_snapshot(self, cache_size: int = 0, memory_usage: int = 0) -> CacheMetricsSnapshot:
        """拍攝指標快照"""
        snapshot = self.get_current_metrics(cache_size, memory_usage)

        # 添加到歷史
        self._history.append(snapshot)
        if len(self._history) > self.max_history:
            self._history.pop(0)

        # 檢查告警
        self._check_alerts(snapshot)

        return snapshot

    def _check_alerts(self, metrics: CacheMetricsSnapshot):
        """檢查告警條件"""
        # 命中率告警
        if metrics.hit_ratio < self._thresholds["hit_ratio_min"]:
            self._create_alert(
                "HIT_RATIO_LOW",
                "WARNING",
                f"Cache hit ratio low: {metrics.hit_ratio:.2%}",
                metrics.hit_ratio,
                self._thresholds["hit_ratio_min"]
            )

        # 時延告警
        if metrics.average_latency_ms > self._thresholds["latency_max_ms"]:
            self._create_alert(
                "LATENCY_HIGH",
                "WARNING",
                f"Cache latency high: {metrics.average_latency_ms:.2f}ms",
                metrics.average_latency_ms,
                self._thresholds["latency_max_ms"]
            )

        # 錯誤率告警
        error_rate = self._errors / max(metrics.hits + metrics.misses, 1)
        if error_rate > self._thresholds["error_rate_max"]:
            self._create_alert(
                "ERROR_RATE_HIGH",
                "ERROR",
                f"Cache error rate high: {error_rate:.2%}",
                error_rate,
                self._thresholds["error_rate_max"]
            )

        # 驅逐率告警
        eviction_rate = self._evictions / max(metrics.sets + self._hits + self._misses, 1)
        if eviction_rate > self._thresholds["eviction_rate_max"]:
            self._create_alert(
                "EVICTION_RATE_HIGH",
                "WARNING",
                f"Cache eviction rate high: {eviction_rate:.2%}",
                eviction_rate,
                self._thresholds["eviction_rate_max"]
            )

    def _create_alert(self, alert_type: str, severity: str, message: str,
                     current_value: float, threshold: float):
        """創建告警"""
        import uuid
        alert = CacheAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            threshold=threshold,
            current_value=current_value
        )

        self._alerts.append(alert)
        self.logger.warning(f"Cache alert: {message}")

        # 觸發告警處理器
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")

    def register_alert_handler(self, handler: Callable[[CacheAlert], None]):
        """註冊告警處理器"""
        self._alert_handlers.append(handler)

    def get_recent_alerts(self, hours: int = 24) -> List[CacheAlert]:
        """獲取最近的告警"""
        cutoff = time.time() - (hours * 3600)
        return [a for a in self._alerts if a.timestamp > cutoff]

    def get_history(self, hours: int = 1) -> List[CacheMetricsSnapshot]:
        """獲取歷史指標"""
        cutoff = time.time() - (hours * 3600)
        return [m for m in self._history if m.timestamp > cutoff]

    def get_trend_analysis(self, hours: int = 1) -> Dict[str, Any]:
        """獲取趨勢分析"""
        history = self.get_history(hours)
        if not history:
            return {}

        # 計算趨勢
        hit_ratios = [m.hit_ratio for m in history]
        latencies = [m.average_latency_ms for m in history]
        throughputs = [m.throughput_ops_per_sec for m in history]

        def calculate_trend(values: List[float]) -> str:
            if len(values) < 2:
                return "stable"
            first, last = values[0], values[-1]
            diff = last - first
            if abs(diff) < 0.01:  # 變化小於1%
                return "stable"
            return "increasing" if diff > 0 else "decreasing"

        return {
            "period_hours": hours,
            "samples": len(history),
            "hit_ratio_trend": calculate_trend(hit_ratios),
            "hit_ratio_avg": sum(hit_ratios) / len(hit_ratios),
            "hit_ratio_min": min(hit_ratios),
            "hit_ratio_max": max(hit_ratios),
            "latency_trend": calculate_trend(latencies),
            "latency_avg": sum(latencies) / len(latencies),
            "latency_min": min(latencies),
            "latency_max": max(latencies),
            "throughput_trend": calculate_trend(throughputs),
            "throughput_avg": sum(throughputs) / len(throughputs),
            "throughput_max": max(throughputs),
        }

    def reset(self):
        """重置計數器"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._sets = 0
            self._deletes = 0
            self._evictions = 0
            self._errors = 0
            self._latencies.clear()
            self._history.clear()

    def set_thresholds(self, thresholds: Dict[str, float]):
        """設置告警閾值"""
        self._thresholds.update(thresholds)


class CacheMetricsMonitor:
    """緩存指標監控器"""

    def __init__(self, collector: CacheMetricsCollector, monitor_interval: int = 60):
        self.collector = collector
        self.monitor_interval = monitor_interval
        self.logger = get_logger("cache_metrics_monitor")
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """啟動監控"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        self.logger.info(f"Started cache metrics monitoring (interval: {self.monitor_interval}s)")

    async def stop(self):
        """停止監控"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped cache metrics monitoring")

    async def _monitor_loop(self):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(self.monitor_interval)
                if not self._running:
                    break

                # 拍攝快照
                snapshot = self.collector.take_snapshot()

                # 記錄日誌
                self.logger.info(
                    f"Cache metrics - Hits: {snapshot.hits}, "
                    f"Misses: {snapshot.misses}, "
                    f"Hit Ratio: {snapshot.hit_ratio:.2%}, "
                    f"Latency: {snapshot.average_latency_ms:.2f}ms"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")


# 多級緩存指標聚合器
class MultiLevelCacheMetrics:
    """多級緩存指標聚合器"""

    def __init__(self):
        self.logger = get_logger("multi_level_cache_metrics")
        self._collectors: Dict[str, CacheMetricsCollector] = {
            "l1": CacheMetricsCollector(),
            "l2": CacheMetricsCollector(),
            "l3": CacheMetricsCollector()
        }
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

    def get_collector(self, level: str) -> CacheMetricsCollector:
        """獲取指定級別的收集器"""
        return self._collectors.get(level.lower())

    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """獲取聚合指標"""
        # 聚合所有級別的指標
        total_hits = sum(c._hits for c in self._collectors.values())
        total_misses = sum(c._misses for c in self._collectors.values())
        total_sets = sum(c._sets for c in self._collectors.values())

        total_requests = total_hits + total_misses
        aggregate_hit_ratio = total_hits / max(total_requests, 1)

        # 各級別命中率
        hit_ratios = {}
        for level, collector in self._collectors.items():
            level_requests = collector._hits + collector._misses
            hit_ratios[f"{level}_hit_ratio"] = (
                collector._hits / max(level_requests, 1) if level_requests > 0 else 0
            )

        return {
            "aggregate": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_sets": total_sets,
                "total_requests": total_requests,
                "hit_ratio": aggregate_hit_ratio,
            },
            "by_level": hit_ratios
        }

    def start_monitoring(self, interval: int = 60):
        """啟動監控"""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        self.logger.info("Started multi-level cache monitoring")

    async def stop_monitoring(self):
        """停止監控"""
        if not self._running:
            return

        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped multi-level cache monitoring")

    async def _monitor_loop(self, interval: int):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break

                # 獲取聚合指標
                metrics = self.get_aggregate_metrics()

                # 記錄日誌
                agg = metrics["aggregate"]
                self.logger.info(
                    f"Multi-level cache aggregate - "
                    f"Hits: {agg['total_hits']}, "
                    f"Misses: {agg['total_misses']}, "
                    f"Hit Ratio: {agg['hit_ratio']:.2%}"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Multi-level monitoring error: {e}")


# 全局指標收集器
_global_metrics_collector: Optional[CacheMetricsCollector] = None


def get_metrics_collector() -> CacheMetricsCollector:
    """獲取全局指標收集器"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = CacheMetricsCollector()
    return _global_metrics_collector


def get_multi_level_metrics() -> MultiLevelCacheMetrics:
    """獲取多級緩存指標聚合器"""
    return MultiLevelCacheMetrics()


# 便捷函數
def record_cache_hit(latency_ms: float = 0.0):
    """記錄緩存命中"""
    get_metrics_collector().record_hit(latency_ms)


def record_cache_miss(latency_ms: float = 0.0):
    """記錄緩存未命中"""
    get_metrics_collector().record_miss(latency_ms)


def record_cache_set(latency_ms: float = 0.0):
    """記錄緩存設置"""
    get_metrics_collector().record_set(latency_ms)


def record_cache_eviction(latency_ms: float = 0.0):
    """記錄緩存驅逐"""
    get_metrics_collector().record_eviction(latency_ms)


def get_cache_metrics_summary() -> Dict[str, Any]:
    """獲取緩存指標摘要"""
    collector = get_metrics_collector()
    metrics = collector.get_current_metrics()
    trend = collector.get_trend_analysis(hours=1)

    return {
        "current": {
            "hits": metrics.hits,
            "misses": metrics.misses,
            "hit_ratio": metrics.hit_ratio,
            "average_latency_ms": metrics.average_latency_ms,
            "throughput_ops_per_sec": metrics.throughput_ops_per_sec
        },
        "trend": trend
    }
