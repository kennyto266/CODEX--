"""
Risk Domain Entities
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP
from ...entities import DomainEntity


class RiskMetricType(Enum):
    """Risk metric type enumeration"""
    VALUE_AT_RISK = "value_at_risk"
    EXPECTED_SHORTFALL = "expected_shortfall"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    BETA = "beta"
    ALPHA = "alpha"
    CORRELATION = "correlation"
    TRACKING_ERROR = "tracking_error"


class RiskLimitType(Enum):
    """Risk limit type enumeration"""
    ABSOLUTE = "absolute"  # Absolute value limit
    PERCENTAGE = "percentage"  # Percentage of portfolio
    VAR_LIMIT = "var_limit"  # VaR limit
    VOLATILITY_LIMIT = "volatility_limit"  # Volatility limit
    CONCENTRATION_LIMIT = "concentration_limit"  # Concentration limit


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetricId:
    """Value object for risk metric ID"""
    value: UUID

    @staticmethod
    def create() -> RiskMetricId:
        return RiskMetricId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class RiskLimitId:
    """Value object for risk limit ID"""
    value: UUID

    @staticmethod
    def create() -> RiskLimitId:
        return RiskLimitId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


class RiskMetric(DomainEntity):
    """
    Risk metric entity
    Represents a calculated risk metric
    """

    def __init__(
        self,
        metric_id: RiskMetricId,
        metric_type: RiskMetricType,
        value: float,
        confidence_level: Optional[float] = None,
        time_horizon: Optional[int] = None,  # in days
        portfolio_id: Optional[UUID] = None,
        asset_symbol: Optional[str] = None,
        calculation_date: Optional[datetime] = None
    ):
        from datetime import datetime
        super().__init__(id=metric_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._metric_type = metric_type
        self._value = value
        self._confidence_level = confidence_level
        self._time_horizon = time_horizon
        self._portfolio_id = portfolio_id
        self._asset_symbol = asset_symbol
        self._calculation_date = calculation_date or datetime.now()

    @property
    def metric_type(self) -> RiskMetricType:
        """Get metric type"""
        return self._metric_type

    @property
    def value(self) -> float:
        """Get metric value"""
        return self._value

    @property
    def confidence_level(self) -> Optional[float]:
        """Get confidence level"""
        return self._confidence_level

    @property
    def time_horizon(self) -> Optional[int]:
        """Get time horizon in days"""
        return self._time_horizon

    @property
    def portfolio_id(self) -> Optional[UUID]:
        """Get portfolio ID"""
        return self._portfolio_id

    @property
    def asset_symbol(self) -> Optional[str]:
        """Get asset symbol"""
        return self._asset_symbol

    @property
    def calculation_date(self) -> datetime:
        """Get calculation date"""
        return self._calculation_date

    @property
    def is_stale(self) -> bool:
        """Check if metric is stale (older than 1 day)"""
        return datetime.now() - self._calculation_date > timedelta(days=1)

    def get_risk_level(self) -> RiskLevel:
        """Determine risk level based on metric value and type"""
        if self._metric_type == RiskMetricType.VALUE_AT_RISK:
            # VaR as percentage of portfolio
            if self._value > 0.1:  # > 10%
                return RiskLevel.CRITICAL
            elif self._value > 0.05:  # > 5%
                return RiskLevel.HIGH
            elif self._value > 0.02:  # > 2%
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        elif self._metric_type == RiskMetricType.VOLATILITY:
            # Annualized volatility
            if self._value > 0.3:  # > 30%
                return RiskLevel.CRITICAL
            elif self._value > 0.2:  # > 20%
                return RiskLevel.HIGH
            elif self._value > 0.1:  # > 10%
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        elif self._metric_type == RiskMetricType.SHARPE_RATIO:
            # Sharpe ratio (higher is better)
            if self._value < 0:
                return RiskLevel.CRITICAL
            elif self._value < 0.5:
                return RiskLevel.HIGH
            elif self._value < 1.0:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        elif self._metric_type == RiskMetricType.MAX_DRAWDOWN:
            # Max drawdown
            if self._value > 0.3:  # > 30%
                return RiskLevel.CRITICAL
            elif self._value > 0.2:  # > 20%
                return RiskLevel.HIGH
            elif self._value > 0.1:  # > 10%
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        else:
            # Default classification
            return RiskLevel.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "metric_type": self._metric_type.value,
            "value": self._value,
            "confidence_level": self._confidence_level,
            "time_horizon": self._time_horizon,
            "portfolio_id": str(self._portfolio_id) if self._portfolio_id else None,
            "asset_symbol": self._asset_symbol,
            "calculation_date": self._calculation_date.isoformat(),
            "risk_level": self.get_risk_level().value,
            "is_stale": self.is_stale,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RiskLimit(DomainEntity):
    """
    Risk limit entity
    Represents a risk limit or threshold
    """

    def __init__(
        self,
        limit_id: RiskLimitId,
        name: str,
        limit_type: RiskLimitType,
        threshold_value: float,
        metric_type: Optional[RiskMetricType] = None,
        portfolio_id: Optional[UUID] = None,
        asset_symbol: Optional[str] = None,
        is_active: bool = True
    ):
        from datetime import datetime
        super().__init__(id=limit_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._name = name
        self._limit_type = limit_type
        self._threshold_value = threshold_value
        self._metric_type = metric_type
        self._portfolio_id = portfolio_id
        self._asset_symbol = asset_symbol
        self._is_active = is_active
        self._violation_count = 0
        self._last_violation_date: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Get limit name"""
        return self._name

    @property
    def limit_type(self) -> RiskLimitType:
        """Get limit type"""
        return self._limit_type

    @property
    def threshold_value(self) -> float:
        """Get threshold value"""
        return self._threshold_value

    @property
    def metric_type(self) -> Optional[RiskMetricType]:
        """Get metric type"""
        return self._metric_type

    @property
    def portfolio_id(self) -> Optional[UUID]:
        """Get portfolio ID"""
        return self._portfolio_id

    @property
    def asset_symbol(self) -> Optional[str]:
        """Get asset symbol"""
        return self._asset_symbol

    @property
    def is_active(self) -> bool:
        """Get active status"""
        return self._is_active

    @property
    def violation_count(self) -> int:
        """Get violation count"""
        return self._violation_count

    @property
    def last_violation_date(self) -> Optional[datetime]:
        """Get last violation date"""
        return self._last_violation_date

    def check_limit(self, metric_value: float) -> bool:
        """
        Check if limit is violated
        Returns True if limit is violated, False otherwise
        """
        if not self._is_active:
            return False

        is_violated = False

        if self._limit_type == RiskLimitType.ABSOLUTE:
            # Absolute value limit (e.g., max VaR = 100,000)
            is_violated = metric_value > self._threshold_value

        elif self._limit_type == RiskLimitType.PERCENTAGE:
            # Percentage limit (e.g., max VaR = 5% of portfolio)
            is_violated = metric_value > self._threshold_value

        elif self._limit_type == RiskLimitType.VAR_LIMIT:
            # VaR limit (same as absolute/percentage but semantic)
            is_violated = metric_value > self._threshold_value

        elif self._limit_type == RiskLimitType.VOLATILITY_LIMIT:
            # Volatility limit
            is_violated = metric_value > self._threshold_value

        elif self._limit_type == RiskLimitType.CONCENTRATION_LIMIT:
            # Concentration limit (e.g., max 10% in single asset)
            is_violated = metric_value > self._threshold_value

        if is_violated:
            self._violation_count += 1
            self._last_violation_date = datetime.now()
            self._mark_updated()

        return is_violated

    def activate(self) -> None:
        """Activate the limit"""
        self._is_active = True
        self._mark_updated()

    def deactivate(self) -> None:
        """Deactivate the limit"""
        self._is_active = False
        self._mark_updated()

    def update_threshold(self, new_threshold: float) -> None:
        """Update threshold value"""
        self._threshold_value = new_threshold
        self._mark_updated()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self._name,
            "limit_type": self._limit_type.value,
            "threshold_value": self._threshold_value,
            "metric_type": self._metric_type.value if self._metric_type else None,
            "portfolio_id": str(self._portfolio_id) if self._portfolio_id else None,
            "asset_symbol": self._asset_symbol,
            "is_active": self._is_active,
            "violation_count": self._violation_count,
            "last_violation_date": self._last_violation_date.isoformat() if self._last_violation_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class RiskExposure:
    """
    Value object representing risk exposure
    """
    category: str
    value: float
    limit: Optional[float] = None

    @property
    def utilization(self) -> float:
        """Calculate utilization percentage"""
        if self.limit is None or self.limit == 0:
            return 0.0
        return (self.value / self.limit) * 100

    @property
    def is_within_limit(self) -> bool:
        """Check if exposure is within limit"""
        if self.limit is None:
            return True
        return self.value <= self.limit

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "category": self.category,
            "value": self.value,
            "limit": self.limit,
            "utilization": self.utilization,
            "within_limit": self.is_within_limit
        }


class RiskAssessment(DomainEntity):
    """
    Risk assessment entity
    Represents a comprehensive risk assessment
    """

    def __init__(
        self,
        assessment_id: UUID,
        portfolio_id: UUID,
        assessment_date: Optional[datetime] = None
    ):
        from datetime import datetime
        super().__init__(id=assessment_id, created_at=datetime.now(), updated_at=datetime.now())

        self._portfolio_id = portfolio_id
        self._assessment_date = assessment_date or datetime.now()
        self._metrics: Dict[RiskMetricType, RiskMetric] = {}
        self._exposures: List[RiskExposure] = []
        self._overall_risk_level: RiskLevel = RiskLevel.MEDIUM
        self._recommendations: List[str] = []

    @property
    def portfolio_id(self) -> UUID:
        """Get portfolio ID"""
        return self._portfolio_id

    @property
    def assessment_date(self) -> datetime:
        """Get assessment date"""
        return self._assessment_date

    @property
    def metrics(self) -> List[RiskMetric]:
        """Get all risk metrics"""
        return list(self._metrics.values())

    @property
    def exposures(self) -> List[RiskExposure]:
        """Get all risk exposures"""
        return self._exposures

    @property
    def overall_risk_level(self) -> RiskLevel:
        """Get overall risk level"""
        return self._overall_risk_level

    @property
    def recommendations(self) -> List[str]:
        """Get recommendations"""
        return self._recommendations

    def add_metric(self, metric: RiskMetric) -> None:
        """Add a risk metric"""
        self._metrics[metric.metric_type] = metric
        self._mark_updated()

    def get_metric(self, metric_type: RiskMetricType) -> Optional[RiskMetric]:
        """Get metric by type"""
        return self._metrics.get(metric_type)

    def add_exposure(self, exposure: RiskExposure) -> None:
        """Add a risk exposure"""
        self._exposures.append(exposure)
        self._mark_updated()

    def calculate_overall_risk_level(self) -> RiskLevel:
        """Calculate overall risk level based on all metrics and exposures"""
        risk_levels = []

        # Add risk levels from metrics
        for metric in self._metrics.values():
            risk_levels.append(metric.get_risk_level())

        # Add risk levels from exposures
        for exposure in self._exposures:
            utilization = exposure.utilization
            if utilization > 90:
                risk_levels.append(RiskLevel.CRITICAL)
            elif utilization > 75:
                risk_levels.append(RiskLevel.HIGH)
            elif utilization > 50:
                risk_levels.append(RiskLevel.MEDIUM)
            else:
                risk_levels.append(RiskLevel.LOW)

        # Overall risk level is the highest (worst) of all components
        risk_priority = {
            RiskLevel.CRITICAL: 4,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1
        }

        max_priority = max(risk_priority[level] for level in risk_levels) if risk_levels else 2

        self._overall_risk_level = next(
            level for level, priority in risk_priority.items()
            if priority == max_priority
        )

        self._mark_updated()
        return self._overall_risk_level

    def generate_recommendations(self) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []

        # Check metrics
        for metric_type, metric in self._metrics.items():
            risk_level = metric.get_risk_level()

            if risk_level == RiskLevel.CRITICAL:
                if metric_type == RiskMetricType.VALUE_AT_RISK:
                    recommendations.append("URGENT: VaR exceeds critical threshold. Reduce position sizes immediately.")
                elif metric_type == RiskMetricType.VOLATILITY:
                    recommendations.append("URGENT: Portfolio volatility is too high. Diversify holdings.")
                elif metric_type == RiskMetricType.MAX_DRAWDOWN:
                    recommendations.append("URGENT: Maximum drawdown is unacceptable. Implement stop-losses.")

            elif risk_level == RiskLevel.HIGH:
                if metric_type == RiskMetricType.SHARPE_RATIO:
                    recommendations.append("Sharpe ratio is low. Review risk-adjusted returns.")
                elif metric_type == RiskMetricType.BETA:
                    recommendations.append("High beta indicates market sensitivity. Consider hedging.")

        # Check exposures
        for exposure in self._exposures:
            if not exposure.is_within_limit:
                recommendations.append(f"Concentration risk: {exposure.category} exposure at {exposure.utilization:.1f}% of limit.")

        # Check for stale metrics
        stale_metrics = [m for m in self._metrics.values() if m.is_stale]
        if stale_metrics:
            recommendations.append("Some risk metrics are stale. Recalculate using latest data.")

        self._recommendations = recommendations
        self._mark_updated()
        return recommendations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "portfolio_id": str(self._portfolio_id),
            "assessment_date": self._assessment_date.isoformat(),
            "overall_risk_level": self._overall_risk_level.value,
            "metrics": [metric.to_dict() for metric in self._metrics.values()],
            "exposures": [exposure.to_dict() for exposure in self._exposures],
            "recommendations": self._recommendations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
