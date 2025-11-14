"""
策略特征标记模块
标记策略的特殊属性和行为特征

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from core.data import OHLCV, Signal, IndicatorConfig
except ImportError:
    try:
        from ..core.data import OHLCV, Signal, IndicatorConfig
    except ImportError:
        # 简化的实现
        class OHLCV:
            pass
        class Signal:
            pass
        class IndicatorConfig:
            pass


@dataclass
class StrategyTraits:
    """策略特征配置类"""
    name: str = "未命名策略"
    timeframe: str = "1D"
    风险水平: str = "中等"
    适用市场: List[str] = None
    requires_indicators: List[str] = None

    # 新增特征
    多资产管理: bool = False
    风险控制: bool = False
    动态再平衡: bool = False
    多策略融合: bool = False
    投票机制: bool = False
    自适应: bool = False
    机器学习: bool = False
    在线学习: bool = False
    特征工程: bool = False
    可视化构建: bool = False
    参数调优: bool = False
    代码生成: bool = False
    多时间框架分析: bool = False
    信号过滤: bool = False
    market_regime适应性: bool = False

    def __post_init__(self):
        if self.适用市场 is None:
            self.适用市场 = ['港股', 'A股', '美股']
        if self.requires_indicators is None:
            self.requires_indicators = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'timeframe': self.timeframe,
            'risk_level': self.风险水平,
            'markets': self.适用市场,
            'required_indicators': self.requires_indicators,
            'features': {
                'multi_asset': self.多资产管理,
                'risk_control': self.风险控制,
                'dynamic_rebalance': self.动态再平衡,
                'strategy_fusion': self.多策略融合,
                'voting_mechanism': self.投票机制,
                'adaptive': self.自适应,
                'machine_learning': self.机器学习,
                'online_learning': self.在线学习,
                'feature_engineering': self.特征工程,
                'visual_builder': self.可视化构建,
                'parameter_tuning': self.参数调优,
                'code_generation': self.代码生成,
                'multi_timeframe': self.多时间框架分析,
                'signal_filtering': self.信号过滤,
                'market_regime_adaptive': self.market_regime适应性
            }
        }


__all__ = ['StrategyTraits', 'OHLCV', 'Signal', 'IndicatorConfig']
