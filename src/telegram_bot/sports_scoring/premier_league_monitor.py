#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英超聯賽官網數據源性能監控器
實時監控系統性能指標並生成報告
"""

import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    timestamp: datetime
    response_time: float
    success: bool
    data_source: str
    cache_hit: bool = False
    error_message: str = ""


@dataclass
class SystemMetrics:
    """系統整體指標"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    uptime_start: datetime = field(default_factory=datetime.now)
    last_request_time: datetime = None
    data_source_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class PremierLeagueMonitor:
    """英超聯賽官網數據源性能監控器"""

    def __init__(self, max_history: int = 1000):
        """
        初始化監控器

        Args:
            max_history: 歷史記錄最大數量
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.system_metrics = SystemMetrics()
        self.alerts = []

        logger.info("初始化性能監控器")

    def record_request(
        self,
        response_time: float,
        success: bool,
        data_source: str,
        cache_hit: bool = False,
        error_message: str = ""
    ):
        """
        記錄請求性能指標

        Args:
            response_time: 響應時間 (秒)
            success: 是否成功
            data_source: 數據源名稱
            cache_hit: 是否命中緩存
            error_message: 錯誤信息
        """
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            response_time=response_time,
            success=success,
            data_source=data_source,
            cache_hit=cache_hit,
            error_message=error_message
        )

        # 添加到歷史記錄
        self.metrics_history.append(metric)

        # 更新系統指標
        self._update_system_metrics(metric)

    def _update_system_metrics(self, metric: PerformanceMetrics):
        """更新系統整體指標"""
        self.system_metrics.total_requests += 1
        self.system_metrics.last_request_time = metric.timestamp

        if metric.success:
            self.system_metrics.successful_requests += 1
        else:
            self.system_metrics.failed_requests += 1

        if metric.cache_hit:
            self.system_metrics.cache_hits += 1
        else:
            self.system_metrics.cache_misses += 1

        # 更新響應時間統計
        if metric.success:
            self.system_metrics.min_response_time = min(
                self.system_metrics.min_response_time,
                metric.response_time
            )
            self.system_metrics.max_response_time = max(
                self.system_metrics.max_response_time,
                metric.response_time
            )

            # 計算平均響應時間
            total_time = (
                self.system_metrics.average_response_time *
                (self.system_metrics.successful_requests - 1) +
                metric.response_time
            )
            self.system_metrics.average_response_time = (
                total_time / self.system_metrics.successful_requests
            )

        # 記錄數據源使用情況
        self.system_metrics.data_source_usage[metric.data_source] += 1

    def get_system_metrics(self) -> Dict[str, Any]:
        """獲取系統整體指標"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.system_metrics.uptime_start).total_seconds(),
            "total_requests": self.system_metrics.total_requests,
            "successful_requests": self.system_metrics.successful_requests,
            "failed_requests": self.system_metrics.failed_requests,
            "success_rate": (
                self.system_metrics.successful_requests / self.system_metrics.total_requests
                if self.system_metrics.total_requests > 0 else 0
            ),
            "cache_hits": self.system_metrics.cache_hits,
            "cache_misses": self.system_metrics.cache_misses,
            "cache_hit_rate": (
                self.system_metrics.cache_hits / (
                    self.system_metrics.cache_hits + self.system_metrics.cache_misses
                ) if (self.system_metrics.cache_hits + self.system_metrics.cache_misses) > 0 else 0
            ),
            "average_response_time_ms": self.system_metrics.average_response_time * 1000,
            "min_response_time_ms": (
                self.system_metrics.min_response_time * 1000
                if self.system_metrics.min_response_time != float('inf') else 0
            ),
            "max_response_time_ms": self.system_metrics.max_response_time * 1000,
            "data_source_usage": dict(self.system_metrics.data_source_usage),
        }

        return metrics

    def get_recent_metrics(self, count: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的指標記錄"""
        recent = list(self.metrics_history)[-count:]
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "response_time_ms": m.response_time * 1000,
                "success": m.success,
                "data_source": m.data_source,
                "cache_hit": m.cache_hit,
                "error_message": m.error_message,
            }
            for m in recent
        ]

    def check_alerts(self) -> List[Dict[str, Any]]:
        """檢查是否需要觸發告警"""
        alerts = []
        metrics = self.get_system_metrics()

        # 成功率告警
        if metrics["success_rate"] < 0.90:
            alerts.append({
                "type": "warning",
                "message": f"成功率過低: {metrics['success_rate']:.2%}",
                "value": metrics["success_rate"],
                "threshold": 0.90,
                "timestamp": datetime.now().isoformat()
            })

        # 響應時間告警
        if metrics["average_response_time_ms"] > 3000:
            alerts.append({
                "type": "warning",
                "message": f"平均響應時間過長: {metrics['average_response_time_ms']:.0f}ms",
                "value": metrics["average_response_time_ms"],
                "threshold": 3000,
                "timestamp": datetime.now().isoformat()
            })

        # 緩存命中率告警
        if metrics["cache_hit_rate"] < 0.50:
            alerts.append({
                "type": "info",
                "message": f"緩存命中率較低: {metrics['cache_hit_rate']:.2%}",
                "value": metrics["cache_hit_rate"],
                "threshold": 0.50,
                "timestamp": datetime.now().isoformat()
            })

        # 連續錯誤告警
        recent_failures = [
            m for m in list(self.metrics_history)[-10:]
            if not m.success
        ]
        if len(recent_failures) >= 5:
            alerts.append({
                "type": "critical",
                "message": f"連續 {len(recent_failures)} 次請求失敗",
                "value": len(recent_failures),
                "threshold": 5,
                "timestamp": datetime.now().isoformat()
            })

        return alerts

    def generate_performance_report(self) -> str:
        """生成性能報告"""
        metrics = self.get_system_metrics()
        uptime = metrics["uptime_seconds"]

        # 計算小時、分鐘
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        report = f"""
============================================================
英超聯賽官網數據源 - 性能監控報告
============================================================
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 整體指標
------------------------------------------------------------
運行時間: {hours}小時 {minutes}分鐘
總請求數: {metrics['total_requests']:,}
成功請求: {metrics['successful_requests']:,}
失敗請求: {metrics['failed_requests']:,}
成功率: {metrics['success_rate']:.2%}

⏱️ 性能指標
------------------------------------------------------------
平均響應時間: {metrics['average_response_time_ms']:.0f}ms
最快響應時間: {metrics['min_response_time_ms']:.0f}ms
最慢響應時間: {metrics['max_response_time_ms']:.0f}ms

💾 緩存指標
------------------------------------------------------------
緩存命中: {metrics['cache_hits']:,}
緩存未命中: {metrics['cache_misses']:,}
緩存命中率: {metrics['cache_hit_rate']:.2%}

📈 數據源使用情況
------------------------------------------------------------"""
        for source, count in metrics['data_source_usage'].items():
            percentage = (count / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0
            report += f"\n{source:20} {count:5,} 次 ({percentage:5.1f}%)"

        # 告警信息
        alerts = self.check_alerts()
        if alerts:
            report += "\n\n⚠️ 告警信息"
            report += "\n------------------------------------------------------------"
            for alert in alerts:
                icon = "🔴" if alert["type"] == "critical" else "⚠️"
                report += f"\n{icon} {alert['message']}"

        report += "\n\n============================================================\n"

        return report

    def reset_metrics(self):
        """重置所有指標"""
        self.metrics_history.clear()
        self.system_metrics = SystemMetrics()
        logger.info("重置性能指標")


# 全局監控器實例
monitor = PremierLeagueMonitor()


def get_monitor() -> PremierLeagueMonitor:
    """獲取全局監控器實例"""
    return monitor


# 性能測量裝飾器
def measure_performance(data_source: str):
    """性能測量裝飾器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_message = ""

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_message = str(e)
                raise
            finally:
                elapsed = time.time() - start_time
                monitor.record_request(
                    response_time=elapsed,
                    success=success,
                    data_source=data_source,
                    error_message=error_message
                )

        return wrapper
    return decorator
