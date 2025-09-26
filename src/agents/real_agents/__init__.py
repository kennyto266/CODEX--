"""Real AI Agents module for Hong Kong quantitative trading system.

This module provides real data-driven AI agents that replace the simulated agents
with actual market data analysis, machine learning models, and intelligent decision making.
"""

from .base_real_agent import BaseRealAgent, RealAgentConfig, RealAgentStatus
from .real_data_analyzer import RealDataAnalyzer, AnalysisResult, SignalStrength
from .ml_integration import MLModelManager, ModelType, ModelPerformance
from .real_quantitative_analyst import RealQuantitativeAnalyst, QuantitativeAnalysisResult
from .real_quantitative_trader import (
    RealQuantitativeTrader, 
    TradingSignal, 
    Order, 
    Position, 
    TradingStrategy, 
    TradingPerformance,
    OrderType,
    OrderSide,
    OrderStatus
)
from .real_portfolio_manager import (
    RealPortfolioManager,
    Asset,
    Portfolio,
    RiskBudget,
    RebalanceDecision,
    AssetClass,
    OptimizationMethod,
    RebalanceTrigger
)
from .real_risk_analyst import (
    RealRiskAnalyst,
    RiskMetric,
    RiskAlert,
    StressTestScenario,
    VaRAnalysis,
    RiskLevel,
    RiskType,
    AlertLevel
)
from .real_data_scientist import (
    RealDataScientist,
    Feature,
    MLModel,
    AnomalyDetection,
    FeatureEngineering,
    ModelStatus,
    FeatureType,
    AnomalyType
)
from .real_quantitative_engineer import (
    RealQuantitativeEngineer,
    PerformanceMetric,
    SystemAlert,
    SystemComponent,
    OptimizationRecommendation,
    SystemStatus,
    AlertSeverity,
    ComponentType
)
from .real_research_analyst import (
    RealResearchAnalyst,
    ResearchHypothesis,
    Factor,
    StrategyResearch,
    LiteratureReview,
    ResearchType,
    HypothesisStatus,
    FactorType
)

__all__ = [
    # Base classes
    'BaseRealAgent',
    'RealAgentConfig', 
    'RealAgentStatus',
    
    # Data analysis
    'RealDataAnalyzer',
    'AnalysisResult',
    'SignalStrength',
    
    # Machine learning
    'MLModelManager',
    'ModelType',
    'ModelPerformance',
    
    # Real agents
    'RealQuantitativeAnalyst',
    'QuantitativeAnalysisResult',
    'RealQuantitativeTrader',
    'TradingSignal',
    'Order',
    'Position',
    'TradingStrategy',
    'TradingPerformance',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'RealPortfolioManager',
    'Asset',
    'Portfolio',
    'RiskBudget',
    'RebalanceDecision',
    'AssetClass',
    'OptimizationMethod',
    'RebalanceTrigger',
    'RealRiskAnalyst',
    'RiskMetric',
    'RiskAlert',
    'StressTestScenario',
    'VaRAnalysis',
    'RiskLevel',
    'RiskType',
    'AlertLevel',
    'RealDataScientist',
    'Feature',
    'MLModel',
    'AnomalyDetection',
    'FeatureEngineering',
    'ModelStatus',
    'FeatureType',
    'AnomalyType',
    'RealQuantitativeEngineer',
    'PerformanceMetric',
    'SystemAlert',
    'SystemComponent',
    'OptimizationRecommendation',
    'SystemStatus',
    'AlertSeverity',
    'ComponentType',
    'RealResearchAnalyst',
    'ResearchHypothesis',
    'Factor',
    'StrategyResearch',
    'LiteratureReview',
    'ResearchType',
    'HypothesisStatus',
    'FactorType',
]
