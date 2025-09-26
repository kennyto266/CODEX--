"""Real-time monitoring and alerting system for Hong Kong quantitative trading.

This package provides comprehensive monitoring, alerting, and system health
management for the AI Agent trading system.
"""

from .real_time_monitor import (
    RealTimeMonitor,
    SystemMetrics,
    AlertLevel,
    AlertType,
    MonitoringConfig
)
from .alert_manager import (
    AlertManager,
    AlertRule,
    AlertAction,
    NotificationChannel,
    AlertStatus
)
from .health_checker import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
    SystemHealth
)
from .performance_tracker import (
    PerformanceTracker,
    PerformanceMetrics,
    MetricType,
    PerformanceAlert
)
from .anomaly_detector import (
    AnomalyDetector,
    AnomalyType,
    AnomalyAlert,
    DetectionMethod
)

__all__ = [
    # Real-time monitoring
    'RealTimeMonitor',
    'SystemMetrics',
    'AlertLevel',
    'AlertType',
    'MonitoringConfig',
    
    # Alert management
    'AlertManager',
    'AlertRule',
    'AlertAction',
    'NotificationChannel',
    'AlertStatus',
    
    # Health checking
    'HealthChecker',
    'HealthStatus',
    'ComponentHealth',
    'SystemHealth',
    
    # Performance tracking
    'PerformanceTracker',
    'PerformanceMetrics',
    'MetricType',
    'PerformanceAlert',
    
    # Anomaly detection
    'AnomalyDetector',
    'AnomalyType',
    'AnomalyAlert',
    'DetectionMethod'
]
