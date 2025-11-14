"""
Bottleneck Detection System (T060n)
Identifies performance bottlenecks in the quantitative trading platform
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any, Optional
import logging
import math
import statistics


@dataclass
class Bottleneck:
    type: str
    severity: str
    component: str
    description: str
    affected_operations: List[str]
    impact_score: float
    recommendations: List[str]
    detected_at: datetime
    estimated_cost_ms: float


class MetricsRegistry:
    def get_metric_series(self, metric_name: str, time_range: Tuple[datetime, datetime]) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    def get_latest_value(self, metric_name: str) -> float:
        raise NotImplementedError


class BottleneckDetector:
    def __init__(self, metrics_registry: MetricsRegistry):
        self.metrics_registry = metrics_registry
        self.logger = logging.getLogger("hk_quant_system.observability.bottleneck_detector")
        self.thresholds = {
            "cpu_usage_percent": 80.0,
            "memory_usage_mb": 1024.0,
            "backtest_latency_p95_ms": 100.0,
            "optimization_latency_p95_ms": 15000.0,
            "error_rate_percent": 5.0,
            "concurrent_backtests": 32
        }
    
    def analyze_performance(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        bottlenecks = []
        bottlenecks.extend(self._detect_cpu_bottlenecks(time_range))
        bottlenecks.extend(self._detect_memory_bottlenecks(time_range))
        bottlenecks.extend(self._detect_latency_bottlenecks(time_range))
        bottlenecks.extend(self._detect_throughput_bottlenecks(time_range))
        bottlenecks.extend(self._detect_error_bottlenecks(time_range))
        return sorted(bottlenecks, key=lambda x: x.impact_score, reverse=True)
    
    def _detect_cpu_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        bottlenecks = []
        cpu_metrics = self.metrics_registry.get_metric_series("cpu_usage_percent", time_range)
        if not cpu_metrics:
            return bottlenecks
        return bottlenecks
    
    def _detect_memory_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        return []
    
    def _detect_latency_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        return []
    
    def _detect_throughput_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        bottlenecks = []
        active_backtests = self.metrics_registry.get_latest_value("active_backtests")
        if active_backtests > self.thresholds["concurrent_backtests"]:
            bottleneck = Bottleneck(
                type="throughput",
                severity="medium",
                component="backtest_engine",
                description=f"Concurrent backtests ({active_backtests}) exceed recommended limit",
                affected_operations=["backtest_queue"],
                impact_score=min(100.0, (active_backtests / 32.0) * 60.0),
                recommendations=["Scale horizontally"],
                detected_at=datetime.utcnow(),
                estimated_cost_ms=active_backtests * 5
            )
            bottlenecks.append(bottleneck)
        return bottlenecks
    
    def _detect_error_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> List[Bottleneck]:
        return []
