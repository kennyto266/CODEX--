"""Strategy management and optimization system for Hong Kong quantitative trading.

This package provides comprehensive strategy lifecycle management, automated
optimization, and performance evaluation capabilities for the AI Agent trading system.
"""

from .strategy_manager import (
    StrategyManager,
    StrategyConfig,
    StrategyStatus,
    StrategyType,
    OptimizationMethod
)
from .strategy_optimizer import (
    StrategyOptimizer,
    OptimizationResult,
    ParameterSpace,
    OptimizationAlgorithm,
    FitnessFunction
)
from .strategy_evaluator import (
    StrategyEvaluator,
    EvaluationMetrics,
    PerformanceComparison,
    RiskMetrics,
    DrawdownAnalysis
)
from .strategy_deployer import (
    StrategyDeployer,
    DeploymentConfig,
    DeploymentStatus,
    RollbackStrategy
)
from .strategy_monitor import (
    StrategyMonitor,
    MonitoringConfig,
    PerformanceAlert,
    StrategyHealth
)

__all__ = [
    # Strategy management
    'StrategyManager',
    'StrategyConfig',
    'StrategyStatus',
    'StrategyType',
    'OptimizationMethod',
    
    # Strategy optimization
    'StrategyOptimizer',
    'OptimizationResult',
    'ParameterSpace',
    'OptimizationAlgorithm',
    'FitnessFunction',
    
    # Strategy evaluation
    'StrategyEvaluator',
    'EvaluationMetrics',
    'PerformanceComparison',
    'RiskMetrics',
    'DrawdownAnalysis',
    
    # Strategy deployment
    'StrategyDeployer',
    'DeploymentConfig',
    'DeploymentStatus',
    'RollbackStrategy',
    
    # Strategy monitoring
    'StrategyMonitor',
    'MonitoringConfig',
    'PerformanceAlert',
    'StrategyHealth'
]
