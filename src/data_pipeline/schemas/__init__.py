"""
Data pipeline schemas for CODEX quantitative trading system.

This package defines Pydantic models for the data pipeline stages:
- OHLCVData: Standard OHLCV format
- RawPriceData: Raw data from sources
- CleanedPriceData: Validated and cleaned data
- NormalizedPriceData: UTC-normalized data ready for backtesting
"""

from .ohlcv import (
    OHLCVData,
    RawPriceData,
    CleanedPriceData,
    NormalizedPriceData,
    OHLCVDataBatch,
    DataValidationResult
)

__all__ = [
    'OHLCVData',
    'RawPriceData',
    'CleanedPriceData',
    'NormalizedPriceData',
    'OHLCVDataBatch',
    'DataValidationResult'
]

__version__ = '1.0.0'
