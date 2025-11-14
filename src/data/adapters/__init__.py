"""
Data Adapters Package
====================

数据适配器包

提供统一的数据接口，支持多种数据源：
- Yahoo Finance
- Alpha Vantage
- HTTP API
- 自定义数据源
"""

from .base import (
    BaseAdapter,
    AdapterConfig,
    OHLCV,
    DataValidationResult,
    DataQuality,
    DataSourceType,
    AdapterStatus,
    PerformanceMetrics
)

from .yahoo import YahooFinanceAdapter
from .alpha_vantage import AlphaVantageAdapter

__all__ = [
    'BaseAdapter',
    'AdapterConfig',
    'OHLCV',
    'DataValidationResult',
    'DataQuality',
    'DataSourceType',
    'AdapterStatus',
    'PerformanceMetrics',
    'YahooFinanceAdapter',
    'AlphaVantageAdapter',
]
