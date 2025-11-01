"""
並行處理監控

提供：
- 實時性能監控
- 指標收集
- 告警機制
- 性能分析
"""

import asyncio
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from src.core.logging import get_logger

logger = get_logger("parallel_monitor")


@dataclass
class TaskMetric:
    """任務指標"""
    task_id: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, completed, failed, cancelled
    worker_id: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class SystemMetric:
    """系統指標"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    throughput: float  # tasks/sec


class ParallelTaskMonitor:
    """並行任務監控器"""

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.logger = get_logger("parallel_monitor")

        # 任務指標
        self._task_metrics: Dict[str, TaskMetric] = {}
        self._task_history: deque = deque(maxlen=max_history)

        # 系統指標
        self._system_metrics: deque = deque(maxlen=max_history)

        # 性能統計
        self._performance_stats: Dict[str, Any] = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "peak_memory_usage": 0.0,
            "peak_cpu_usage": 0.0
        }

        # 告警
        self._alerts: List[Dict] = []
        self._alert_handlers: List[Callable] = []

        # 監控閾值
        self._thresholds = {
            "max_execution_time": 300,  # 5分鐘
            "max_memory_usage": 1024,  # 1GB
            "max_cpu_usage": 90,  # 90%
            "failure_rate": 0.1,  # 10%
            "max_queue_size": 1000
        }

    def start_task(self, task_id: str, worker_id: Optional[str] = None) -> TaskMetric:
        """開始監控任務"""
        metric = TaskMetric(
            task_id=task_id,
            start_time=time.time(),
            worker_id=worker_id
        )

        self._task_metrics[task_id] = metric
        self._performance_stats["total_tasks"] += 1

        self.logger.debug(f"Started monitoring task: {task_id}")
        return metric

    def complete_task(
        self,
        task_id: str,
        status: str = "completed",
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None
    ) -> Optional[TaskMetric]:
        """完成任務監控"""
        metric = self._task_metrics.pop(task_id, None)
        if not metric:
            return None

        metric.end_time = time.time()
        metric.status = status
        metric.execution_time = metric.end_time - metric.start_time
        metric.memory_usage = memory_usage
        metric.cpu_usage = cpu_usage

        # 更新統計
        self._performance_stats["total_execution_time"] += metric.execution_time
        self._performance_stats["completed_tasks"] += 1
        self._performance_stats["average_execution_time"] = (
            self._performance_stats["total_execution_time"] /
            max(self._performance_stats["completed_tasks"], 1)
        )

        # 記錄歷史
        self._task_history.append(metric)

        # 檢查告警
        self._check_alerts(metric)

        self.logger.debug(f"Completed monitoring task: {task_id} ({status})")
        return metric

    def fail_task(self, task_id: str, error: Optional[str] = None) -> Optional[TaskMetric]:
        """標記任務失敗"""
        metric = self._task_metrics.pop(task_id, None)
        if not metric:
            return None

        metric.end_time = time.time()
        metric.status = "failed"
        metric.execution_time = metric.end_time - metric.start_time

        # 更新統計
        self._performance_stats["failed_tasks"] += 1
        self._performance_stats["total_execution_time"] += metric.execution_time

        # 記錄歷史
        self._task_history.append(metric)

        # 檢查告警
        self._check_alerts(metric)

        self.logger.warning(f"Task failed: {task_id} - {error}")
        return metric

    async def collect_system_metrics(self) -> SystemMetric:
        """收集系統指標"""
        import psutil

        current_time = time.time()

        # 收集任務統計
        active_tasks = len(self._task_metrics)
        completed_tasks = self._performance_stats["completed_tasks"]
        failed_tasks = self._performance_stats["failed_tasks"]

        # 計算吞吐量（每分鐘完成任務數）
        recent_completed = sum(
            1 for m in self._task_history
            if m.end_time and current_time - m.end_time < 60
        )
        throughput = recent_completed / 60  # tasks/min

        metric = SystemMetric(
            timestamp=current_time,
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            memory_available=psutil.virtual_memory().available,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            throughput=throughput
        )

        # 保存歷史
        self._system_metrics.append(metric)

        # 更新性能統計
        if metric.memory_percent > self._performance_stats["peak_memory_usage"]:
            self._performance_stats["peak_memory_usage"] = metric.memory_percent
        if metric.cpu_percent > self._performance_stats["peak_cpu_usage"]:
            self._performance_stats["peak_cpu_usage"] = metric.cpu_percent

        return metric

    def _check_alerts(self, metric: TaskMetric):
        """檢查告警條件"""
        # 執行時間告警
        if metric.execution_time and metric.execution_time > self._thresholds["max_execution_time"]:
            self._create_alert(
                "SLOW_TASK",
                "WARNING",
                f"Task {metric.task_id} took too long: {metric.execution_time:.2f}s",
                {"task_id": metric.task_id, "execution_time": metric.execution_time}
            )

        # 失敗率告警
        if metric.status == "failed":
            failure_rate = (
                self._performance_stats["failed_tasks"] /
                max(self._performance_stats["total_tasks"], 1)
            )
            if failure_rate > self._thresholds["failure_rate"]:
                self._create_alert(
                    "HIGH_FAILURE_RATE",
                    "WARNING",
                    f"Task failure rate is high: {failure_rate:.2%}",
                    {"failure_rate": failure_rate}
                )

    def _create_alert(self, alert_type: str, severity: str, message: str, data: Dict):
        """創建告警"""
        alert = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": time.time(),
            "data": data
        }

        self._alerts.append(alert)

        # 觸發告警處理器
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")

    def register_alert_handler(self, handler: Callable):
        """註冊告警處理器"""
        self._alert_handlers.append(handler)

    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """獲取性能摘要"""
        cutoff_time = time.time() - (minutes * 60)

        # 篩選最近的任務
        recent_tasks = [
            m for m in self._task_history
            if m.end_time and m.end_time >= cutoff_time
        ]

        if not recent_tasks:
            return {
                "period_minutes": minutes,
                "total_tasks": 0,
                "average_execution_time": 0,
                "throughput": 0,
                "error_rate": 0
            }

        # 計算統計
        execution_times = [m.execution_time for m in recent_tasks if m.execution_time]
        completed = [m for m in recent_tasks if m.status == "completed"]
        failed = [m for m in recent_tasks if m.status == "failed"]

        return {
            "period_minutes": minutes,
            "total_tasks": len(recent_tasks),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "error_rate": len(failed) / len(recent_tasks) if recent_tasks else 0,
            "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "min_execution_time": min(execution_times) if execution_times else 0,
            "max_execution_time": max(execution_times) if execution_times else 0,
            "throughput": len(completed) / minutes,  # tasks/min
            "peak_memory_usage": max([m.memory_usage for m in recent_tasks if m.memory_usage], default=0),
            "peak_cpu_usage": max([m.cpu_usage for m in recent_tasks if m.cpu_usage], default=0)
        }

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """獲取活躍任務"""
        return [
            {
                "task_id": metric.task_id,
                "start_time": metric.start_time,
                "duration": time.time() - metric.start_time,
                "worker_id": metric.worker_id
            }
            for metric in self._task_metrics.values()
        ]

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """獲取最近告警"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            alert for alert in self._alerts
            if alert["timestamp"] > cutoff_time
        ]

    def get_system_trend(self, minutes: int = 60) -> Dict[str, Any]:
        """獲取系統趨勢"""
        cutoff_time = time.time() - (minutes * 60)

        recent_metrics = [
            m for m in self._system_metrics
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        return {
            "cpu_trend": {
                "min": min(m.cpu_percent for m in recent_metrics),
                "max": max(m.cpu_percent for m in recent_metrics),
                "avg": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            },
            "memory_trend": {
                "min": min(m.memory_percent for m in recent_metrics),
                "max": max(m.memory_percent for m in recent_metrics),
                "avg": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            },
            "throughput_trend": {
                "min": min(m.throughput for m in recent_metrics),
                "max": max(m.throughput for m in recent_metrics),
                "avg": sum(m.throughput for m in recent_metrics) / len(recent_metrics)
            },
            "active_tasks_trend": {
                "min": min(m.active_tasks for m in recent_metrics),
                "max": max(m.active_tasks for m in recent_metrics),
                "avg": sum(m.active_tasks for m in recent_metrics) / len(recent_metrics)
            }
        }

    def reset_stats(self):
        """重置統計"""
        self._performance_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "peak_memory_usage": 0.0,
            "peak_cpu_usage": 0.0
        }
        self._task_metrics.clear()
        self._task_history.clear()
        self._system_metrics.clear()
        self._alerts.clear()

    def set_thresholds(self, thresholds: Dict[str, float]):
        """設置告警閾值"""
        self._thresholds.update(thresholds)


# 全局監控實例
_global_monitor: Optional[ParallelTaskMonitor] = None


def get_parallel_monitor() -> ParallelTaskMonitor:
    """獲取全局並行監控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ParallelTaskMonitor()
    return _global_monitor


# 便捷函數
def start_task_monitoring(task_id: str, worker_id: Optional[str] = None) -> TaskMetric:
    """開始任務監控"""
    return get_parallel_monitor().start_task(task_id, worker_id)


def complete_task_monitoring(
    task_id: str,
    status: str = "completed",
    memory_usage: Optional[float] = None,
    cpu_usage: Optional[float] = None
) -> Optional[TaskMetric]:
    """完成任務監控"""
    return get_parallel_monitor().complete_task(task_id, status, memory_usage, cpu_usage)


def fail_task_monitoring(task_id: str, error: Optional[str] = None) -> Optional[TaskMetric]:
    """標記任務失敗"""
    return get_parallel_monitor().fail_task(task_id, error)


async def collect_system_metrics() -> SystemMetric:
    """收集系統指標"""
    return await get_parallel_monitor().collect_system_metrics()


def get_monitor_summary(minutes: int = 60) -> Dict[str, Any]:
    """獲取監控摘要"""
    return get_parallel_monitor().get_performance_summary(minutes)
