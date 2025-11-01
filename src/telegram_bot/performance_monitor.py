#!/usr/bin/env python3
"""
性能監控模組
追蹤系統運行指標，提供實時性能數據
"""

import time
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading
import json

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指標收集器"""

    def __init__(self):
        self.response_times = defaultdict(list)
        self.api_calls = defaultdict(list)
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        self.errors = defaultdict(int)
        self.command_counts = defaultdict(int)
        self.start_time = time.time()

    def track_response_time(self, command: str, start_time: float):
        """追蹤命令響應時間"""
        elapsed = time.time() - start_time
        self.response_times[command].append({
            "time": elapsed,
            "timestamp": datetime.now().isoformat()
        })

        # 只保留最近1000條記錄
        if len(self.response_times[command]) > 1000:
            self.response_times[command] = self.response_times[command][-1000:]

    def track_api_call(self, endpoint: str, success: bool, response_time: float):
        """追蹤API調用"""
        self.api_calls[endpoint].append({
            "success": success,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        })

        if len(self.api_calls[endpoint]) > 1000:
            self.api_calls[endpoint] = self.api_calls[endpoint][-1000:]

    def track_cache_operation(self, cache_type: str, hit: bool):
        """追蹤緩存操作"""
        if hit:
            self.cache_hits[cache_type] += 1
        else:
            self.cache_misses[cache_type] += 1

    def track_error(self, error_type: str):
        """追蹤錯誤"""
        self.errors[error_type] += 1

    def track_command(self, command: str):
        """追蹤命令執行"""
        self.command_counts[command] += 1

    def get_response_time_stats(self, command: str) -> Dict:
        """獲取響應時間統計"""
        times = self.response_times.get(command, [])
        if not times:
            return {}

        elapsed_times = [t["time"] for t in times]

        return {
            "count": len(elapsed_times),
            "avg": sum(elapsed_times) / len(elapsed_times),
            "min": min(elapsed_times),
            "max": max(elapsed_times),
            "p95": self._percentile(elapsed_times, 0.95),
            "p99": self._percentile(elapsed_times, 0.99)
        }

    def get_api_stats(self, endpoint: str) -> Dict:
        """獲取API統計"""
        calls = self.api_calls.get(endpoint, [])
        if not calls:
            return {}

        total = len(calls)
        successful = sum(1 for c in calls if c["success"])
        response_times = [c["response_time"] for c in calls]

        return {
            "total": total,
            "success": successful,
            "failures": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times)
        }

    def get_cache_stats(self, cache_type: str) -> Dict:
        """獲取緩存統計"""
        hits = self.cache_hits.get(cache_type, 0)
        misses = self.cache_misses.get(cache_type, 0)
        total = hits + misses

        if total > 0:
            hit_rate = hits / total * 100
        else:
            hit_rate = 0

        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total": total
        }

    def get_error_stats(self) -> Dict:
        """獲取錯誤統計"""
        return dict(self.errors)

    def get_command_stats(self) -> Dict:
        """獲取命令統計"""
        return dict(self.command_counts)

    def get_uptime(self) -> Dict:
        """獲取運行時間"""
        uptime_seconds = time.time() - self.start_time
        uptime = str(timedelta(seconds=uptime_seconds))

        return {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_readable": uptime
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not data:
            return 0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def generate_report(self) -> Dict:
        """生成完整性能報告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "commands": {},
            "apis": {},
            "cache": {},
            "errors": self.get_error_stats(),
            "overall_stats": {}
        }

        # 命令統計
        for command in set(self.response_times.keys()) | set(self.command_counts.keys()):
            cmd_stats = self.get_response_time_stats(command)
            cmd_stats["total_calls"] = self.command_counts.get(command, 0)
            report["commands"][command] = cmd_stats

        # API統計
        for endpoint in self.api_calls.keys():
            report["apis"][endpoint] = self.get_api_stats(endpoint)

        # 緩存統計
        all_cache_types = set(self.cache_hits.keys()) | set(self.cache_misses.keys())
        for cache_type in all_cache_types:
            report["cache"][cache_type] = self.get_cache_stats(cache_type)

        # 整體統計
        all_response_times = []
        for times in self.response_times.values():
            all_response_times.extend([t["time"] for t in times])

        if all_response_times:
            report["overall_stats"] = {
                "avg_response_time": sum(all_response_times) / len(all_response_times),
                "total_commands": sum(self.command_counts.values()),
                "total_api_calls": sum(len(calls) for calls in self.api_calls.values()),
                "total_errors": sum(self.errors.values())
            }

        return report


class AlertManager:
    """警報管理器"""

    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.alert_thresholds = {
            "response_time": 3.0,      # 3秒
            "error_rate": 0.05,        # 5%
            "cache_hit_rate": 0.50,     # 50%
            "api_failure_rate": 0.10   # 10%
        }
        self.alerts = deque(maxlen=100)
        self.lock = threading.Lock()

    def check_alerts(self) -> List[Dict]:
        """檢查警報條件"""
        alerts = []

        # 檢查響應時間
        for command, stats in self.metrics.get_response_time_stats("").items():
            if stats.get("avg", 0) > self.alert_thresholds["response_time"]:
                alerts.append({
                    "type": "high_response_time",
                    "command": command,
                    "value": stats["avg"],
                    "threshold": self.alert_thresholds["response_time"],
                    "timestamp": datetime.now().isoformat()
                })

        # 檢查錯誤率
        error_stats = self.metrics.get_error_stats()
        total_commands = sum(self.metrics.command_counts.values())
        if total_commands > 0:
            error_rate = sum(error_stats.values()) / total_commands
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "high_error_rate",
                    "value": error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                    "timestamp": datetime.now().isoformat()
                })

        # 記錄警報
        with self.lock:
            self.alerts.extend(alerts)

        return alerts

    def add_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """手動添加警報"""
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }

        with self.lock:
            self.alerts.append(alert)

        logger.warning(f"警報 [{severity}]: {message}")

    def get_recent_alerts(self, count: int = 10) -> List[Dict]:
        """獲取最近的警報"""
        with self.lock:
            return list(self.alerts)[-count:]


class PerformanceMonitor:
    """性能監控器主類"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.alert_manager = AlertManager(self.metrics)
        self._start_monitoring()

    def _start_monitoring(self):
        """啟動監控任務"""
        def monitoring_loop():
            while True:
                try:
                    time.sleep(60)  # 每分鐘檢查一次
                    alerts = self.alert_manager.check_alerts()
                    if alerts:
                        logger.warning(f"檢測到 {len(alerts)} 個性能警報")
                except Exception as e:
                    logger.error(f"監控任務失敗: {e}")

        # 啟動監控線程
        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.start()
        logger.info("性能監控已啟動")

    def track_command(self, command: str, start_time: float):
        """追蹤命令執行"""
        self.metrics.track_command(command)
        self.metrics.track_response_time(command, start_time)

    def track_api_call(self, endpoint: str, success: bool, start_time: float):
        """追蹤API調用"""
        elapsed = time.time() - start_time
        self.metrics.track_api_call(endpoint, success, elapsed)

    def track_cache_operation(self, cache_type: str, hit: bool):
        """追蹤緩存操作"""
        self.metrics.track_cache_operation(cache_type, hit)

    def track_error(self, error_type: str):
        """追蹤錯誤"""
        self.metrics.track_error(error_type)
        self.alert_manager.add_alert("error", f"檢測到錯誤: {error_type}", "error")

    def get_report(self) -> Dict:
        """獲取性能報告"""
        return self.metrics.generate_report()

    def get_alerts(self, count: int = 10) -> List[Dict]:
        """獲取警報"""
        return self.alert_manager.get_recent_alerts(count)

    def save_report(self, filepath: str):
        """保存性能報告到文件"""
        try:
            report = self.get_report()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"性能報告已保存到: {filepath}")
        except Exception as e:
            logger.error(f"保存性能報告失敗: {e}")


# 創建全局實例
performance_monitor = PerformanceMonitor()
