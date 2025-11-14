"""
q«æÔ!D - Shared Entities Module

!D+†ûq-è!Jq«„æÔ^‹ŒxÚ!‹
- SystemConfig: ûqMn^
- SystemConstants: ûq8Ïš©
- æ(åwýx
"""

# e8ÃMn^
from .system_config import SystemConfig, SystemConstants, setup_logging
from .system_config import get_project_root, get_config_path, get_logs_path

# eVeøÜæÔ
from .strategy_template import StrategyTemplate, PerformanceMetrics

# e*øÜæÔ
from .optimization_result import (
    OptimizationResult,
    OptimizationMetrics,
    DateRange
)

# e@MnæÔ
from .layout_config import (
    LayoutConfig,
    LayoutData,
    WidgetConfig,
    GridConfig,
    ThemeConfig
)

# ú@	lq¥ã
__all__ = [
    # ûqMn
    "SystemConfig",
    "SystemConstants",
    "setup_logging",
    "get_project_root",
    "get_config_path",
    "get_logs_path",

    # Ve!
    "StrategyTemplate",
    "PerformanceMetrics",

    # *Pœ
    "OptimizationResult",
    "OptimizationMetrics",
    "DateRange",

    # @Mn
    "LayoutConfig",
    "LayoutData",
    "WidgetConfig",
    "GridConfig",
    "ThemeConfig"
]

# H,áo
__version__ = "1.0.0"
__author__ = "/¡Ï¤AI Agentûq"
