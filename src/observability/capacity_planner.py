"""
Capacity Planning System (T060o)
Plans capacity and scaling for quantitative trading platform
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
import math
from .bottleneck_detector import MetricsRegistry


@dataclass
class ResourceModel:
    current_capacity: float
    projected_demand: float
    scaling_factor: float
    cost_per_unit: float


@dataclass
class ScalingRecommendation:
    resource_type: str
    current_value: float
    recommended_value: float
    action: str
    priority: str
    estimated_cost_per_month: float
    description: str


@dataclass
class CapacityPlan:
    current_usage: Dict[str, float]
    projected_requirements: Dict[str, float]
    scaling_recommendations: List[ScalingRecommendation]
    cost_estimate_usd: float
    recommended_actions: List[str]
    analysis_date: datetime
    projection_date: datetime


class CapacityPlanner:
    def __init__(self, metrics_registry: MetricsRegistry):
        self.metrics_registry = metrics_registry
        self.logger = logging.getLogger("hk_quant_system.observability.capacity_planner")
        self.resource_models: Dict[str, ResourceModel] = {}
    
    def analyze_capacity_requirements(
        self,
        projected_users: int,
        projected_backtests_per_day: int,
        time_horizon_days: int = 30
    ) -> CapacityPlan:
        cpu_requirements = self._calculate_cpu_requirements(projected_backtests_per_day, time_horizon_days)
        memory_requirements = self._calculate_memory_requirements(projected_backtests_per_day, time_horizon_days)
        storage_requirements = self._calculate_storage_requirements(projected_backtests_per_day, time_horizon_days)
        network_requirements = self._calculate_network_requirements(projected_users, projected_backtests_per_day)
        
        scaling_recommendations = self._generate_scaling_recommendations(
            cpu_requirements, memory_requirements, storage_requirements, network_requirements
        )
        
        return CapacityPlan(
            current_usage=self._get_current_usage(),
            projected_requirements={
                "cpu_cores": cpu_requirements,
                "memory_gb": memory_requirements,
                "storage_gb": storage_requirements,
                "network_gbps": network_requirements
            },
            scaling_recommendations=scaling_recommendations,
            cost_estimate_usd=self._estimate_monthly_cost(cpu_requirements, memory_requirements, storage_requirements),
            recommended_actions=[r.description for r in scaling_recommendations],
            analysis_date=datetime.utcnow(),
            projection_date=datetime.utcnow() + timedelta(days=time_horizon_days)
        )
    
    def _calculate_cpu_requirements(self, backtests_per_day: int, days: int) -> int:
        base_ms_per_backtest = 50.0
        safety_factor = 2.0
        overhead_factor = 1.5
        total_backtests = backtests_per_day * days
        total_ms = total_backtests * base_ms_per_backtest * safety_factor * overhead_factor
        cpu_time_available = 8 * 24 * 3600 * 1000
        required_cores = math.ceil(total_ms / cpu_time_available * 8)
        return max(8, required_cores)
    
    def _calculate_memory_requirements(self, backtests_per_day: int, days: int) -> float:
        base_mb_per_backtest = 10.0
        safety_factor = 3.0
        overhead_gb = 2.0
        total_mb = backtests_per_day * days * base_mb_per_backtest * safety_factor
        total_gb = (total_mb / 1024.0) + overhead_gb
        return round(total_gb, 1)
    
    def _calculate_storage_requirements(self, backtests_per_day: int, days: int) -> float:
        base_mb_per_backtest = 5.0
        safety_factor = 2.0
        overhead_gb = 50.0
        total_mb = backtests_per_day * days * base_mb_per_backtest * safety_factor
        total_gb = (total_mb / 1024.0) + overhead_gb
        return round(total_gb, 1)
    
    def _calculate_network_requirements(self, users: int, backtests_per_day: int) -> float:
        base_gbps = 1.0
        user_factor = users / 100.0
        backtest_factor = backtests_per_day / 1000.0
        return round(base_gbps + user_factor + backtest_factor, 1)
    
    def _generate_scaling_recommendations(self, cpu_cores: int, memory_gb: float, storage_gb: float, network_gbps: float) -> List[ScalingRecommendation]:
        recommendations = []
        current_cpu = self._get_current_cpu_cores()
        if cpu_cores > current_cpu:
            recommendations.append(ScalingRecommendation(
                resource_type="cpu",
                current_value=current_cpu,
                recommended_value=cpu_cores,
                action="scale_up",
                priority="high" if cpu_cores > current_cpu * 2 else "medium",
                estimated_cost_per_month=500.0,
                description=f"Scale CPU from {current_cpu} to {cpu_cores} cores"
            ))
        return recommendations
    
    def _estimate_monthly_cost(self, cpu_cores: int, memory_gb: float, storage_gb: float) -> float:
        cpu_cost = cpu_cores * 50.0
        memory_cost = memory_gb * 5.0
        storage_cost = storage_gb * 0.1
        return round(cpu_cost + memory_cost + storage_cost, 2)
    
    def _get_current_usage(self) -> Dict[str, float]:
        return {
            "cpu_cores": self._get_current_cpu_cores(),
            "memory_gb": self._get_current_memory_gb(),
            "storage_gb": 100.0,
            "network_gbps": 1.0
        }
    
    def _get_current_cpu_cores(self) -> int:
        return 8
    
    def _get_current_memory_gb(self) -> float:
        return 16.0
