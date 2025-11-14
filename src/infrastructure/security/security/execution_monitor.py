"""
代码执行监控器 - 实时监控代码执行过程
提供执行跟踪、资源监控、异常检测和执行日志功能
"""

import sys
import os
import time
import logging
import threading
import psutil
import subprocess
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import traceback

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEvent:
    """执行事件"""
    timestamp: float
    event_type: str  # START, PROGRESS, ERROR, END, RESOURCE_WARNING
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """资源使用情况"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_connections: int = 0
    open_files: int = 0
    thread_count: int = 0


class ExecutionTracker:
    """执行跟踪器"""

    def __init__(self, process_id: int):
        self.process_id = process_id
        self.process = None
        self.start_time = None
        self.events: List[ExecutionEvent] = []
        self.resource_snapshots: List[ResourceUsage] = []

        try:
            self.process = psutil.Process(process_id)
        except psutil.NoSuchProcess:
            logger.error(f"Process {process_id} not found")

    def track_event(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """记录执行事件"""
        event = ExecutionEvent(
            timestamp=time.time(),
            event_type=event_type,
            message=message,
            data=data or {}
        )
        self.events.append(event)
        logger.debug(f"[{event_type}] {message}")

    def get_resource_usage(self) -> Optional[ResourceUsage]:
        """获取当前资源使用情况"""
        if not self.process or not self.process.is_running():
            return None

        try:
            # 获取CPU和内存使用率
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = self.process.memory_percent()

            # 获取磁盘I/O
            try:
                disk_io = self.process.io_counters()
                disk_read = disk_io.read_bytes if disk_io else 0
                disk_write = disk_io.write_bytes if disk_io else 0
            except (psutil.AccessDenied, AttributeError):
                disk_read = disk_write = 0

            # 获取网络连接数
            network_connections = len(self.process.connections())

            # 获取打开文件数
            open_files = len(self.process.open_files())

            # 获取线程数
            thread_count = self.process.num_threads()

            return ResourceUsage(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read=disk_read,
                disk_io_write=disk_write,
                network_connections=network_connections,
                open_files=open_files,
                thread_count=thread_count
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Failed to get resource usage: {e}")
            return None

    def snapshot_resource_usage(self):
        """快照当前资源使用"""
        usage = self.get_resource_usage()
        if usage:
            self.resource_snapshots.append(usage)

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.start_time:
            return {}

        end_time = time.time()
        duration = end_time - self.start_time

        # 分析事件
        event_counts = {}
        for event in self.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        # 分析资源使用
        if not self.resource_snapshots:
            resource_stats = {}
        else:
            cpu_values = [s.cpu_percent for s in self.resource_snapshots]
            memory_values = [s.memory_mb for s in self.resource_snapshots]

            resource_stats = {
                'max_cpu': max(cpu_values) if cpu_values else 0,
                'avg_cpu': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max_memory_mb': max(memory_values) if memory_values else 0,
                'avg_memory_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
                'total_snapshots': len(self.resource_snapshots)
            }

        return {
            'process_id': self.process_id,
            'duration_seconds': duration,
            'start_time': self.start_time,
            'end_time': end_time,
            'event_counts': event_counts,
            'resource_stats': resource_stats,
            'total_events': len(self.events),
            'total_resource_snapshots': len(self.resource_snapshots)
        }


class RealTimeMonitor:
    """实时监控器"""

    def __init__(self, poll_interval: float = 0.5):
        self.poll_interval = poll_interval
        self.trackers: Dict[int, ExecutionTracker] = {}
        self.monitoring = False
        self.monitor_thread = None
        self.alert_callbacks: List[Callable] = []
        self.thresholds = {
            'max_cpu_percent': 80.0,
            'max_memory_mb': 512.0,
            'max_network_connections': 10,
            'max_open_files': 50
        }

    def add_tracker(self, tracker: ExecutionTracker):
        """添加跟踪器"""
        self.trackers[tracker.process_id] = tracker

    def remove_tracker(self, process_id: int):
        """移除跟踪器"""
        if process_id in self.trackers:
            del self.trackers[process_id]

    def add_alert_callback(self, callback: Callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                for process_id, tracker in list(self.trackers.items()):
                    # 检查进程是否还存在
                    if not tracker.process or not tracker.process.is_running():
                        tracker.track_event("END", f"Process {process_id} terminated")
                        self.remove_tracker(process_id)
                        continue

                    # 快照资源使用
                    tracker.snapshot_resource_usage()
                    current_usage = tracker.get_resource_usage()

                    if current_usage:
                        # 检查阈值
                        self._check_thresholds(tracker, current_usage)

                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1)

    def _check_thresholds(self, tracker: ExecutionTracker, usage: ResourceUsage):
        """检查资源阈值"""
        for threshold_name, threshold_value in self.thresholds.items():
            if threshold_name == 'max_cpu_percent' and usage.cpu_percent > threshold_value:
                self._trigger_alert(tracker, 'RESOURCE_WARNING', f"CPU usage exceeded {usage.cpu_percent}%", {
                    'threshold': threshold_value,
                    'current': usage.cpu_percent
                })

            elif threshold_name == 'max_memory_mb' and usage.memory_mb > threshold_value:
                self._trigger_alert(tracker, 'RESOURCE_WARNING', f"Memory usage exceeded {usage.memory_mb}MB", {
                    'threshold': threshold_value,
                    'current': usage.memory_mb
                })

            elif threshold_name == 'max_network_connections' and usage.network_connections > threshold_value:
                self._trigger_alert(tracker, 'RESOURCE_WARNING', f"Network connections exceeded {usage.network_connections}", {
                    'threshold': threshold_value,
                    'current': usage.network_connections
                })

            elif threshold_name == 'max_open_files' and usage.open_files > threshold_value:
                self._trigger_alert(tracker, 'RESOURCE_WARNING', f"Open files exceeded {usage.open_files}", {
                    'threshold': threshold_value,
                    'current': usage.open_files
                })

    def _trigger_alert(self, tracker: ExecutionTracker, event_type: str, message: str, data: Dict[str, Any]):
        """触发告警"""
        tracker.track_event(event_type, message, data)
        for callback in self.alert_callbacks:
            try:
                callback(tracker, event_type, message, data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def start(self):
        """启动监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Real-time monitor started")

    def stop(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Real-time monitor stopped")

    def get_all_trackers_summary(self) -> List[Dict[str, Any]]:
        """获取所有跟踪器的摘要"""
        return [tracker.get_execution_summary() for tracker in self.trackers.values()]


class ExecutionLogger:
    """执行日志记录器"""

    def __init__(self, log_dir: str = "logs/execution"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_logs: Dict[str, List[ExecutionEvent]] = {}

    def start_session(self, session_id: str):
        """开始会话"""
        self.session_logs[session_id] = []
        logger.info(f"Execution session {session_id} started")

    def log_event(self, session_id: str, event: ExecutionEvent):
        """记录事件"""
        if session_id not in self.session_logs:
            self.session_logs[session_id] = []

        self.session_logs[session_id].append(event)

    def end_session(self, session_id: str, summary: Dict[str, Any]):
        """结束会话"""
        if session_id in self.session_logs:
            # 保存到文件
            log_file = self.log_dir / f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            log_data = {
                'session_id': session_id,
                'start_time': summary.get('start_time'),
                'end_time': summary.get('end_time'),
                'events': [
                    {
                        'timestamp': e.timestamp,
                        'event_type': e.event_type,
                        'message': e.message,
                        'data': e.data
                    }
                    for e in self.session_logs[session_id]
                ],
                'summary': summary
            }

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Session {session_id} logged to {log_file}")

            # 清理内存中的日志
            del self.session_logs[session_id]

    def get_session_events(self, session_id: str) -> List[ExecutionEvent]:
        """获取会话事件"""
        return self.session_logs.get(session_id, [])


class ExecutionMonitor:
    """代码执行监控主类"""

    def __init__(self, monitor_interval: float = 0.5, log_dir: str = "logs/execution"):
        self.real_time_monitor = RealTimeMonitor(monitor_interval)
        self.execution_logger = ExecutionLogger(log_dir)
        self.active_sessions: Dict[str, ExecutionTracker] = {}

        # 添加默认告警回调
        self.real_time_monitor.add_alert_callback(self._default_alert_handler)

    def _default_alert_handler(self, tracker: ExecutionTracker, event_type: str, message: str, data: Dict[str, Any]):
        """默认告警处理器"""
        logger.warning(f"[ALERT] {message}")
        print(f"\n⚠️  ALERT: {message}\n", file=sys.stderr)

    def start_monitoring(self):
        """启动监控"""
        self.real_time_monitor.start()

    def stop_monitoring(self):
        """停止监控"""
        self.real_time_monitor.stop()

    def start_execution_tracking(self, process_id: int, session_id: str) -> ExecutionTracker:
        """开始执行跟踪"""
        tracker = ExecutionTracker(process_id)
        tracker.start_time = time.time()
        tracker.track_event("START", f"Process {process_id} started")

        self.active_sessions[session_id] = tracker
        self.real_time_monitor.add_tracker(tracker)
        self.execution_logger.start_session(session_id)

        return tracker

    def stop_execution_tracking(self, session_id: str) -> Dict[str, Any]:
        """停止执行跟踪"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        tracker = self.active_sessions[session_id]
        tracker.track_event("END", f"Process {tracker.process_id} ended")
        self.real_time_monitor.remove_tracker(tracker.process_id)

        summary = tracker.get_execution_summary()
        self.execution_logger.end_session(session_id, summary)

        del self.active_sessions[session_id]

        return summary

    def get_active_sessions(self) -> List[str]:
        """获取活跃会话"""
        return list(self.active_sessions.keys())

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        tracker = self.active_sessions.get(session_id)
        if tracker:
            return tracker.get_execution_summary()
        return None

    def get_all_sessions_summary(self) -> List[Dict[str, Any]]:
        """获取所有会话摘要"""
        return self.real_time_monitor.get_all_trackers_summary()

    def export_session_log(self, session_id: str, output_file: str):
        """导出会话日志"""
        tracker = self.active_sessions.get(session_id)
        if not tracker:
            raise ValueError(f"Session {session_id} not found")

        log_data = {
            'session_id': session_id,
            'events': [
                {
                    'timestamp': e.timestamp,
                    'event_type': e.event_type,
                    'message': e.message,
                    'data': e.data
                }
                for e in tracker.events
            ],
            'summary': tracker.get_execution_summary()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Session {session_id} exported to {output_file}")

    def set_alert_thresholds(self, thresholds: Dict[str, float]):
        """设置告警阈值"""
        self.real_time_monitor.thresholds.update(thresholds)
        logger.info(f"Alert thresholds updated: {thresholds}")
