"""
Test fixtures and mock implementations for Phase 2 testing.

This package provides:
1. Mock data generators (OHLCV, asset profiles, results, metrics)
2. Mock implementations of all Phase 2 interfaces
3. Convenient factory functions for creating mocks

Usage:
    from tests.fixtures import mock_ohlcv_data, create_mock_strategy

    # Generate mock data
    data = mock_ohlcv_data("0700.HK", num_days=100)

    # Create mock objects
    strategy = create_mock_strategy()
"""

# Export mock data generators
from .mock_data import (
    MockOHLCVGenerator,
    MockAssetProfileGenerator,
    MockStrategyResultsGenerator,
    MockPerformanceMetricsGenerator,
    mock_ohlcv_data,
    mock_asset_profile,
    mock_strategy_results,
    mock_performance_metrics,
)

# Export mock implementations
from .mock_adapters import (
    MockDataSource,
    MockDataCleaner,
    MockProcessor,
    MockStrategy,
    MockVariableManager,
    MockChartBuilder,
    MockAnalyzer,
    create_mock_data_source,
    create_mock_data_cleaner,
    create_mock_processor,
    create_mock_strategy,
    create_mock_variable_manager,
    create_mock_chart_builder,
    create_mock_analyzer,
)

__all__ = [
    # Generators
    'MockOHLCVGenerator',
    'MockAssetProfileGenerator',
    'MockStrategyResultsGenerator',
    'MockPerformanceMetricsGenerator',
    'mock_ohlcv_data',
    'mock_asset_profile',
    'mock_strategy_results',
    'mock_performance_metrics',
    # Mock implementations
    'MockDataSource',
    'MockDataCleaner',
    'MockProcessor',
    'MockStrategy',
    'MockVariableManager',
    'MockChartBuilder',
    'MockAnalyzer',
    # Factory functions
    'create_mock_data_source',
    'create_mock_data_cleaner',
    'create_mock_processor',
    'create_mock_strategy',
    'create_mock_variable_manager',
    'create_mock_chart_builder',
    'create_mock_analyzer',
]
