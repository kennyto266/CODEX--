"""
Resource monitoring utilities for execution tracking

Provides comprehensive monitoring of CPU, memory, network usage, and performance
metrics for scraping operations.
"""

import time
import psutil
import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .models import ResourceUsage, ExecutionMetrics
from .logging_config import StructuredLogger


@dataclass
class ResourceMonitor:
    """Resource monitoring state"""
    process: psutil.Process
    start_time: float = field(default_factory=time.time)
    peak_memory: int = 0
    network_start_bytes: Dict[str, int] = field(default_factory=dict)
    thread_count: int = 0
    file_handle_count: int = 0


class ResourceTracker:
    """Thread-safe resource tracker for concurrent operations"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.monitoring")
        self._monitors: Dict[str, ResourceMonitor] = {}
        self._lock = threading.Lock()

    def start_monitoring(self, execution_id: str) -> None:
        """Start monitoring a specific execution"""
        with self._lock:
            try:
                process = psutil.Process()
                network = psutil.net_io_counters()

                self._monitors[execution_id] = ResourceMonitor(
                    process=process,
                    network_start_bytes={
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv
                    }
                )
                self.logger.info(
                    f"Started resource monitoring for execution: {execution_id}",
                    execution_id=execution_id,
                    operation="start_monitoring"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to start monitoring: {str(e)}",
                    execution_id=execution_id,
                    operation="start_monitoring"
                )

    def stop_monitoring(self, execution_id: str) -> Optional[ResourceUsage]:
        """Stop monitoring and return resource usage"""
        with self._lock:
            monitor = self._monitors.get(execution_id)
            if not monitor:
                self.logger.warning(
                    f"No monitoring found for execution: {execution_id}",
                    execution_id=execution_id,
                    operation="stop_monitoring"
                )
                return None

            try:
                # Calculate resource usage
                end_time = time.time()
                duration = end_time - monitor.start_time

                # Memory metrics
                memory_info = monitor.process.memory_info()
                current_memory = memory_info.rss

                # CPU time
                cpu_times = monitor.process.cpu_times()
                cpu_time = sum(cpu_times)

                # Network usage
                network_end = psutil.net_io_counters()
                network_bytes_sent = network_end.bytes_sent - monitor.network_start_bytes['bytes_sent']
                network_bytes_received = network_end.bytes_recv - monitor.network_start_bytes['bytes_recv']

                # Thread and file handle counts
                thread_count = monitor.process.num_threads()

                try:
                    file_handle_count = monitor.process.num_handles()
                except (AttributeError, psutil.AccessDenied):
                    # num_handles not available on all platforms
                    file_handle_count = 0

                resource_usage = ResourceUsage(
                    cpu_time=cpu_time,
                    wall_time=duration,
                    memory_peak=monitor.peak_memory,
                    memory_average=current_memory,  # Using current as average for simplicity
                    disk_io=0,  # Would need more sophisticated tracking
                    network_bytes_sent=network_bytes_sent,
                    network_bytes_received=network_bytes_received,
                    network_requests=1,  # Simplified - would need request counting
                    subprocess_count=0,  # Would need subprocess tracking
                    file_handles=file_handle_count
                )

                self.logger.info(
                    f"Stopped resource monitoring for execution: {execution_id}",
                    execution_id=execution_id,
                    duration_ms=duration * 1000,
                    memory_mb=current_memory / 1024 / 1024,
                    cpu_time=cpu_time,
                    operation="stop_monitoring"
                )

                return resource_usage

            except Exception as e:
                self.logger.error(
                    f"Error stopping monitoring: {str(e)}",
                    execution_id=execution_id,
                    operation="stop_monitoring"
                )
                return None
            finally:
                # Clean up monitor
                del self._monitors[execution_id]

    def update_peak_memory(self, execution_id: str, current_memory: int) -> None:
        """Update peak memory usage for an execution"""
        with self._lock:
            monitor = self._monitors.get(execution_id)
            if monitor and current_memory > monitor.peak_memory:
                monitor.peak_memory = current_memory

    def get_current_usage(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current resource usage for an execution"""
        with self._lock:
            monitor = self._monitors.get(execution_id)
            if not monitor:
                return None

            try:
                memory_info = monitor.process.memory_info()
                cpu_percent = monitor.process.cpu_percent()

                network = psutil.net_io_counters()

                return {
                    "memory_current_mb": memory_info.rss / 1024 / 1024,
                    "memory_peak_mb": monitor.peak_memory / 1024 / 1024,
                    "cpu_percent": cpu_percent,
                    "network_bytes_sent": network.bytes_sent - monitor.network_start_bytes['bytes_sent'],
                    "network_bytes_received": network.bytes_recv - monitor.network_start_bytes['bytes_recv'],
                    "thread_count": monitor.process.num_threads(),
                    "duration_seconds": time.time() - monitor.start_time
                }
            except Exception as e:
                self.logger.error(
                    f"Error getting current usage: {str(e)}",
                    execution_id=execution_id,
                    operation="get_current_usage"
                )
                return None


class PerformanceMonitor:
    """Performance monitoring and benchmarking utilities"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.performance")
        self._metrics: Dict[str, Any] = {}

    def start_timer(self, operation_id: str, execution_id: str = None) -> str:
        """Start timing an operation"""
        timer_id = f"{operation_id}_{execution_id}" if execution_id else operation_id
        self._metrics[timer_id] = {
            "start_time": time.time(),
            "execution_id": execution_id,
            "operation": operation_id
        }

        self.logger.debug(
            f"Started timer for operation: {operation_id}",
            timer_id=timer_id,
            execution_id=execution_id,
            operation="start_timer"
        )

        return timer_id

    def end_timer(self, timer_id: str) -> float:
        """End timing an operation and return duration"""
        if timer_id not in self._metrics:
            self.logger.warning(
                f"Timer not found: {timer_id}",
                operation="end_timer"
            )
            return 0.0

        start_time = self._metrics[timer_id]["start_time"]
        duration = time.time() - start_time

        self._metrics[timer_id]["duration"] = duration
        self._metrics[timer_id]["end_time"] = time.time()

        self.logger.debug(
            f"Ended timer for operation: {self._metrics[timer_id]['operation']}",
            timer_id=timer_id,
            duration_ms=duration * 1000,
            operation="end_timer"
        )

        return duration

    def record_metric(self, name: str, value: Any, execution_id: str = None) -> None:
        """Record a custom metric"""
        metric_key = f"{name}_{execution_id}" if execution_id else name

        self._metrics[metric_key] = {
            "value": value,
            "timestamp": time.time(),
            "execution_id": execution_id,
            "metric_name": name
        }

        self.logger.debug(
            f"Recorded metric: {name} = {value}",
            metric_key=metric_key,
            execution_id=execution_id,
            operation="record_metric"
        )

    def get_metrics_summary(self, execution_id: str = None) -> Dict[str, Any]:
        """Get summary of recorded metrics"""
        if execution_id:
            # Filter metrics by execution_id
            filtered_metrics = {
                k: v for k, v in self._metrics.items()
                if v.get("execution_id") == execution_id
            }
        else:
            filtered_metrics = self._metrics.copy()

        # Calculate summary statistics
        durations = [v.get("duration", 0) for v in filtered_metrics.values() if "duration" in v]
        custom_metrics = {
            k: v for k, v in filtered_metrics.items()
            if "duration" not in v and "metric_name" in v
        }

        summary = {
            "execution_id": execution_id,
            "total_operations": len([m for m in filtered_metrics.values() if "operation" in m]),
            "total_duration": sum(durations),
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "custom_metrics": custom_metrics
        }

        return summary

    def clear_metrics(self, execution_id: str = None) -> None:
        """Clear recorded metrics"""
        if execution_id:
            # Clear metrics for specific execution
            keys_to_remove = [
                k for k, v in self._metrics.items()
                if v.get("execution_id") == execution_id
            ]
            for key in keys_to_remove:
                del self._metrics[key]
        else:
            # Clear all metrics
            self._metrics.clear()

        self.logger.debug(
            f"Cleared metrics for execution_id: {execution_id}",
            execution_id=execution_id,
            operation="clear_metrics"
        )


# Global instances
resource_tracker = ResourceTracker()
performance_monitor = PerformanceMonitor()


def get_resource_tracker() -> ResourceTracker:
    """Get global resource tracker instance"""
    return resource_tracker


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return performance_monitor


# Context managers for easy resource monitoring
class ResourceMonitoringContext:
    """Context manager for resource monitoring"""

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.tracker = get_resource_tracker()

    def __enter__(self):
        self.tracker.start_monitoring(self.execution_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None


class PerformanceTimerContext:
    """Context manager for performance timing"""

    def __init__(self, operation_id: str, execution_id: str = None):
        self.operation_id = operation_id
        self.execution_id = execution_id
        self.monitor = get_performance_monitor()
        self.timer_id = None
        self.duration = None

    def __enter__(self):
        self.timer_id = self.monitor.start_timer(self.operation_id, self.execution_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = self.monitor.end_timer(self.timer_id)
        return None


def track_resources(execution_id: str) -> ResourceMonitoringContext:
    """Create a resource monitoring context manager"""
    return ResourceMonitoringContext(execution_id)


def time_operation(operation_id: str, execution_id: str = None) -> PerformanceTimerContext:
    """Create a performance timing context manager"""
    return PerformanceTimerContext(operation_id, execution_id)