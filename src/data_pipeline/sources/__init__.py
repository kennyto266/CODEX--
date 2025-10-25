"""
Data sources interface and implementations.

This module provides unified interfaces for all data sources in the Data Management Layer.
"""

from .base_source import (
    IDataSource,
    IDataCleaner,
    IProcessor,
    ValidationResult,
    DataMetadata,
)

__all__ = [
    'IDataSource',
    'IDataCleaner',
    'IProcessor',
    'ValidationResult',
    'DataMetadata',
]
