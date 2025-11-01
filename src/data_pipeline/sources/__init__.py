"""
Data sources interface and implementations.

This module provides unified interfaces for all data sources in the Data Management Layer.
Includes implementations for HTTP APIs, files, and HKEX data.

Usage:
    from src.data_pipeline.sources import (
        IDataSource,
        HttpApiDataSource,
        HKEXDataSource,
        FileDataSource,
    )
"""

from .base_source import (
    IDataSource,
    IDataCleaner,
    IProcessor,
    ValidationResult,
    DataMetadata,
)

from .http_api_source import (
    HttpApiDataSource,
    CentralizedHKEXHttpSource,
)

from .file_source import (
    FileDataSource,
    CSVDataSource,
    ExcelDataSource,
)

from .hkex_unified_source import HKEXDataSource

__all__ = [
    # Interfaces
    'IDataSource',
    'IDataCleaner',
    'IProcessor',
    'ValidationResult',
    'DataMetadata',
    # HTTP API implementations
    'HttpApiDataSource',
    'CentralizedHKEXHttpSource',
    # File implementations
    'FileDataSource',
    'CSVDataSource',
    'ExcelDataSource',
    # HKEX unified
    'HKEXDataSource',
]
