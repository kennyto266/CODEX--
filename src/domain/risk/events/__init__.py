"""
Risk Domain Events
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from ...entities import DomainEvent
from ..entities import RiskMetric, RiskLevel


class RiskMetricCalculatedEvent(DomainEvent):
    """Event fired when a risk metric is calculated"""

    def __init__(self, metric: RiskMetric):
        super().__init__()
        self.event_type = "Risk.MetricCalculated"
        self.event_data = {
            "metric_id": str(metric.id),
            "metric_type": metric.metric_type.value,
            "value": metric.value,
            "confidence_level": metric.confidence_level,
            "risk_level": metric.get_risk_level().value,
            "portfolio_id": str(metric.portfolio_id) if metric.portfolio_id else None,
            "asset_symbol": metric.asset_symbol,
            "timestamp": datetime.now().isoformat()
        }


class RiskLimitViolationEvent(DomainEvent):
    """Event fired when a risk limit is violated"""

    def __init__(self, limit_name: str, metric_value: float, threshold: float, severity: str):
        super().__init__()
        self.event_type = "Risk.LimitViolation"
        self.event_data = {
            "limit_name": limit_name,
            "metric_value": metric_value,
            "threshold": threshold,
            "severity": severity,
            "breach_amount": metric_value - threshold,
            "timestamp": datetime.now().isoformat()
        }


class PortfolioRiskAssessmentEvent(DomainEvent):
    """Event fired when a portfolio risk assessment is completed"""

    def __init__(self, portfolio_id: UUID, overall_risk_level: RiskLevel, violation_count: int):
        super().__init__()
        self.event_type = "Risk.AssessmentCompleted"
        self.event_data = {
            "portfolio_id": str(portfolio_id),
            "overall_risk_level": overall_risk_level.value,
            "violation_count": violation_count,
            "timestamp": datetime.now().isoformat()
        }


class RiskAlertEvent(DomainEvent):
    """Event fired when a risk alert is triggered"""

    def __init__(self, alert_type: str, message: str, severity: str, portfolio_id: Optional[UUID] = None):
        super().__init__()
        self.event_type = "Risk.Alert"
        self.event_data = {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "portfolio_id": str(portfolio_id) if portfolio_id else None,
            "timestamp": datetime.now().isoformat()
        }
