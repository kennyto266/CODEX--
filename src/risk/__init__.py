"""
风险管理系统

提供完整的风险管理框架，包括：
- 动态仓位管理 (position_sizing)
- VaR计算系统 (var)
- 压力测试框架 (stress_test)
- 风险平价策略 (parity_strategy)
- 回撤控制机制 (drawdown_control)
"""

from .position_sizing import (
    SizingMethod,
    PositionSizingRequest,
    PositionSizingResult,
    RiskParityWeights,
    VolatilitySizingParams,
    PositionSizingEngine
)

from .var import (
    VaRMethod,
    VaRResult,
    PortfolioVaRResult,
    StressTestScenario,
    VaRCalculator
)

from .stress_test import (
    StressTestType,
    HistoricalStressEvent,
    MarketShockScenario,
    VolatilityShock,
    LiquidityStress,
    StressTestResult,
    StressTestReport,
    StressTestEngine
)

from .parity_strategy import (
    RiskParityMethod,
    RiskBudget,
    RiskParityConfig,
    AssetRiskMetrics,
    RiskParityResult,
    RebalanceAction,
    RiskParityEngine
)

from .drawdown_control import (
    DrawdownSeverity,
    DrawdownThreshold,
    StopLossConfig,
    PositionReductionRule,
    DrawdownWarning,
    DrawdownControlResult,
    RiskRecoveryPlan,
    DrawdownControlEngine
)

__all__ = [
    # Position Sizing
    'SizingMethod',
    'PositionSizingRequest',
    'PositionSizingResult',
    'RiskParityWeights',
    'VolatilitySizingParams',
    'PositionSizingEngine',

    # VaR
    'VaRMethod',
    'VaRResult',
    'PortfolioVaRResult',
    'StressTestScenario',
    'VaRCalculator',

    # Stress Test
    'StressTestType',
    'HistoricalStressEvent',
    'MarketShockScenario',
    'VolatilityShock',
    'LiquidityStress',
    'StressTestResult',
    'StressTestReport',
    'StressTestEngine',

    # Risk Parity
    'RiskParityMethod',
    'RiskBudget',
    'RiskParityConfig',
    'AssetRiskMetrics',
    'RiskParityResult',
    'RebalanceAction',
    'RiskParityEngine',

    # Drawdown Control
    'DrawdownSeverity',
    'DrawdownThreshold',
    'StopLossConfig',
    'PositionReductionRule',
    'DrawdownWarning',
    'DrawdownControlResult',
    'RiskRecoveryPlan',
    'DrawdownControlEngine'
]
