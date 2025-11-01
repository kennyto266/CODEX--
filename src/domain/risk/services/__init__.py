"""
Risk Domain Services
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math

from ..entities import (
    RiskMetric, RiskMetricId, RiskMetricType, RiskLimit, RiskLimitId,
    RiskLimitType, RiskAssessment, RiskLevel, RiskExposure
)
from ...repositories import Repository


class RiskService:
    """Domain service for risk management operations"""

    def __init__(
        self,
        metric_repository: Repository[RiskMetric],
        limit_repository: Repository[RiskLimit],
        assessment_repository: Repository[RiskAssessment]
    ):
        self._metric_repository = metric_repository
        self._limit_repository = limit_repository
        self._assessment_repository = assessment_repository

    # ===== Risk Metric Operations =====

    async def calculate_var(self, returns: List[float], confidence_level: float = 0.95, time_horizon: int = 1) -> float:
        """
        Calculate Value at Risk (VaR)
        Uses historical simulation method
        """
        if not returns:
            return 0.0

        # Sort returns (ascending order)
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = -sorted_returns[index] * math.sqrt(time_horizon)

        return var

    async def calculate_volatility(self, returns: List[float], annualize: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns)
        """
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)

        volatility = math.sqrt(variance)

        if annualize:
            # Assume daily returns, multiply by sqrt(252)
            volatility *= math.sqrt(252)

        return volatility

    async def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        """
        if not returns:
            return 0.0

        volatility = await self.calculate_volatility(returns, annualize=False)
        if volatility == 0:
            return 0.0

        mean_return = sum(returns) / len(returns)
        excess_return = mean_return - (risk_free_rate / 252)  # Daily risk-free rate

        sharpe_ratio = excess_return / volatility * math.sqrt(252)
        return sharpe_ratio

    async def create_risk_metric(
        self,
        metric_type: RiskMetricType,
        value: float,
        confidence_level: Optional[float] = None,
        time_horizon: Optional[int] = None,
        portfolio_id: Optional[str] = None,
        asset_symbol: Optional[str] = None
    ) -> RiskMetric:
        """Create a new risk metric"""
        metric_id = RiskMetricId.create()
        metric = RiskMetric(
            metric_id=metric_id,
            metric_type=metric_type,
            value=value,
            confidence_level=confidence_level,
            time_horizon=time_horizon,
            portfolio_id=UUID(portfolio_id) if portfolio_id else None,
            asset_symbol=asset_symbol
        )

        await self._metric_repository.save(metric)
        return metric

    async def get_latest_metrics(self, portfolio_id: Optional[str] = None) -> List[RiskMetric]:
        """Get latest risk metrics"""
        all_metrics = await self._metric_repository.find_all()

        if portfolio_id:
            portfolio_uuid = UUID(portfolio_id)
            all_metrics = [m for m in all_metrics if m.portfolio_id == portfolio_uuid]

        # Group by metric type and get latest
        latest_metrics = {}
        for metric in all_metrics:
            key = (metric.metric_type, metric.portfolio_id, metric.asset_symbol)
            if key not in latest_metrics or metric.calculation_date > latest_metrics[key].calculation_date:
                latest_metrics[key] = metric

        return list(latest_metrics.values())

    # ===== Risk Limit Operations =====

    async def create_risk_limit(
        self,
        name: str,
        limit_type: RiskLimitType,
        threshold_value: float,
        metric_type: Optional[RiskMetricType] = None,
        portfolio_id: Optional[str] = None,
        asset_symbol: Optional[str] = None
    ) -> RiskLimit:
        """Create a new risk limit"""
        limit_id = RiskLimitId.create()
        limit = RiskLimit(
            limit_id=limit_id,
            name=name,
            limit_type=limit_type,
            threshold_value=threshold_value,
            metric_type=metric_type,
            portfolio_id=UUID(portfolio_id) if portfolio_id else None,
            asset_symbol=asset_symbol
        )

        await self._limit_repository.save(limit)
        return limit

    async def check_limits(self, portfolio_id: str) -> Dict[str, Any]:
        """Check all limits for a portfolio"""
        portfolio_uuid = UUID(portfolio_id)
        all_limits = await self._limit_repository.find_all()

        # Get limits for this portfolio
        portfolio_limits = [l for l in all_limits if l.portfolio_id == portfolio_uuid]

        # Get latest metrics
        latest_metrics = await self.get_latest_metrics(portfolio_id)

        violations = []
        passed_limits = []

        for limit in portfolio_limits:
            # Find corresponding metric
            metric = None
            for m in latest_metrics:
                if m.portfolio_id == portfolio_uuid and m.metric_type == limit.metric_type:
                    metric = m
                    break

            if metric:
                is_violated = limit.check_limit(metric.value)
                limit_dict = {
                    "limit": limit.to_dict(),
                    "metric": metric.to_dict(),
                    "violated": is_violated
                }

                if is_violated:
                    violations.append(limit_dict)
                else:
                    passed_limits.append(limit_dict)

        return {
            "portfolio_id": portfolio_id,
            "total_limits": len(portfolio_limits),
            "violations": violations,
            "passed_limits": passed_limits,
            "violation_count": len(violations),
            "check_timestamp": datetime.now().isoformat()
        }

    # ===== Risk Assessment Operations =====

    async def create_risk_assessment(self, portfolio_id: str) -> RiskAssessment:
        """Create a comprehensive risk assessment"""
        assessment_id = UUID(portfolio_id)  # Use portfolio ID as assessment ID for simplicity
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            portfolio_id=UUID(portfolio_id)
        )

        # Get latest metrics
        metrics = await self.get_latest_metrics(portfolio_id)
        for metric in metrics:
            assessment.add_metric(metric)

        # Create risk exposures (simplified)
        assessment.add_exposure(RiskExposure("equity", 70.0, 80.0))
        assessment.add_exposure(RiskExposure("bond", 20.0, 30.0))
        assessment.add_exposure(RiskExposure("cash", 10.0, 10.0))

        # Calculate overall risk level
        assessment.calculate_overall_risk_level()

        # Generate recommendations
        assessment.generate_recommendations()

        await self._assessment_repository.save(assessment)
        return assessment

    async def get_risk_assessment(self, portfolio_id: str) -> Optional[RiskAssessment]:
        """Get latest risk assessment for a portfolio"""
        all_assessments = await self._assessment_repository.find_all()
        assessment_id = UUID(portfolio_id)

        for assessment in all_assessments:
            if assessment.id == assessment_id:
                return assessment

        return None

    async def get_risk_dashboard_data(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive risk dashboard data"""
        # Get or create assessment
        assessment = await self.get_risk_assessment(portfolio_id)
        if not assessment:
            assessment = await self.create_risk_assessment(portfolio_id)

        # Get limit violations
        limit_check = await self.check_limits(portfolio_id)

        # Get latest metrics
        latest_metrics = await self.get_latest_metrics(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "overall_risk_level": assessment.overall_risk_level.value,
            "metrics": [m.to_dict() for m in latest_metrics],
            "exposures": [e.to_dict() for e in assessment.exposures],
            "recommendations": assessment.recommendations,
            "limit_violations": limit_check["violations"],
            "last_updated": datetime.now().isoformat(),
        }


from uuid import UUID
