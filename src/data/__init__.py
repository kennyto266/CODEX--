"""
Data module - Phase 8: Enhanced Features
=========================================

Provides comprehensive data processing capabilities including:
- Storage, validation, and integrity checking
- Fundamental data integration (T194)
- Options data support (T195)
- Futures contracts management (T196)
- Multi-source data fusion (T197)
- Real-time data streaming (T198)
- Data quality and validation (T350-T354)

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

# Existing modules
from .storage import DataStorage, save_ohlcv_data, load_ohlcv_data
from .validator import DataValidator, validate_trading_data, quick_validate
from .integrity import IntegrityChecker, verify_file_integrity, quick_check_data_integrity

# Phase 8: Enhanced Features - T194-T198
# T194: Fundamental Data
from .fundamental import (
    FundamentalDataIntegrator,
    FinancialStatement,
    FinancialStatementType,
    ValuationMetrics,
    IndustryClassification,
    AnalystEstimate,
    AnalystRating,
    ESGScore,
    ESGRating,
    get_fundamental_data,
    calculate_financial_health_score
)

# T195: Options Data
from .options_data import (
    OptionsDataManager,
    OptionContract,
    OptionType,
    OptionStyle,
    OptionChain,
    VolatilitySmile,
    VolatilitySurface,
    get_option_chain,
    calculate_implied_volatility
)

# T196: Futures Data
from .futures_data import (
    FuturesDataManager,
    FuturesContract,
    FuturesType,
    DeliveryType,
    ContractStatus,
    BasisAnalysis,
    RollStrategy,
    CostOfCarry,
    get_futures_contracts,
    calculate_futures_fair_value
)

# T197: Data Fusion
from .fusion import (
    DataFusionEngine,
    DataSource,
    DataSourcePriority,
    ConflictResolution,
    DataType,
    DataRecord,
    FusionResult,
    fuse_multi_source_data
)

# T198: Real-time Streaming
from .streaming import (
    RealtimeStreamManager,
    StreamEvent,
    StreamEventType,
    ConnectionStatus,
    DataBuffer,
    Subscription,
    StreamEventProcessor,
    create_price_alert,
    get_realtime_data
)

# T350-T354: Data Quality and Validation
from .validation_pipeline import (
    ValidationPipeline,
    ValidationStage,
    ValidationResult,
    create_validation_pipeline
)
from .anomaly_detector import (
    AnomalyDetector,
    create_anomaly_detector
)
from .cross_source_verification import (
    CrossSourceVerification,
    create_cross_source_verifier
)
from .freshness_checker import (
    FreshnessChecker,
    create_freshness_checker
)
from .quality_reporter import (
    QualityReporter,
    QualityReport,
    QualityScoreCalculator,
    ReportFormatter,
    TrendAnalyzer,
    generate_quality_report
)

__all__ = [
    # Existing
    'DataStorage',
    'save_ohlcv_data',
    'load_ohlcv_data',
    'DataValidator',
    'validate_trading_data',
    'quick_validate',
    'IntegrityChecker',
    'verify_file_integrity',
    'quick_check_data_integrity',

    # T194: Fundamental Data
    'FundamentalDataIntegrator',
    'FinancialStatement',
    'FinancialStatementType',
    'ValuationMetrics',
    'IndustryClassification',
    'AnalystEstimate',
    'AnalystRating',
    'ESGScore',
    'ESGRating',
    'get_fundamental_data',
    'calculate_financial_health_score',

    # T195: Options Data
    'OptionsDataManager',
    'OptionContract',
    'OptionType',
    'OptionStyle',
    'OptionChain',
    'VolatilitySmile',
    'VolatilitySurface',
    'get_option_chain',
    'calculate_implied_volatility',

    # T196: Futures Data
    'FuturesDataManager',
    'FuturesContract',
    'FuturesType',
    'DeliveryType',
    'ContractStatus',
    'BasisAnalysis',
    'RollStrategy',
    'CostOfCarry',
    'get_futures_contracts',
    'calculate_futures_fair_value',

    # T197: Data Fusion
    'DataFusionEngine',
    'DataSource',
    'DataSourcePriority',
    'ConflictResolution',
    'DataType',
    'DataRecord',
    'FusionResult',
    'fuse_multi_source_data',

    # T198: Real-time Streaming
    'RealtimeStreamManager',
    'StreamEvent',
    'StreamEventType',
    'ConnectionStatus',
    'DataBuffer',
    'Subscription',
    'StreamEventProcessor',
    'create_price_alert',
    'get_realtime_data',

    # T350-T354: Data Quality and Validation
    'ValidationPipeline',
    'ValidationStage',
    'ValidationResult',
    'create_validation_pipeline',
    'AnomalyDetector',
    'create_anomaly_detector',
    'CrossSourceVerification',
    'create_cross_source_verifier',
    'FreshnessChecker',
    'create_freshness_checker',
    'QualityReporter',
    'QualityReport',
    'QualityScoreCalculator',
    'ReportFormatter',
    'TrendAnalyzer',
    'generate_quality_report'
]

__version__ = "1.0.0"
