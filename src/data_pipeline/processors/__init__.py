"""
Data processors package.

Provides data processing implementations for the Data Management Layer:
- BasicDataProcessor: Fundamental processing operations
- TemporalAligner: Time series alignment
- AssetProfiler: Asset profile enrichment

Usage:
    from src.data_pipeline.processors import (
        BasicDataProcessor,
        TemporalAligner,
        AssetProfiler,
    )

    processor = BasicDataProcessor()
    processed_data = processor.process(cleaned_data)
"""

from .basic_processor import (
    BasicDataProcessor,
    TemporalAligner,
    AssetProfiler,
)

__all__ = [
    'BasicDataProcessor',
    'TemporalAligner',
    'AssetProfiler',
]
