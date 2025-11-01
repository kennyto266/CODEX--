"""
Data processors package.

Provides data processing implementations for the Data Management Layer:
- BasicDataProcessor: Fundamental processing operations
- TemporalAligner: Time series alignment
- AssetProfiler: Asset profile enrichment
- MissingDataHandler: Handle missing values
- FeatureEngineer: Create derived features
- DataAggregator: Resample to different frequencies
- MultiValidator: Multi-criteria validation

Usage:
    from src.data_pipeline.processors import (
        BasicDataProcessor,
        TemporalAligner,
        AssetProfiler,
        MissingDataHandler,
        FeatureEngineer,
        DataAggregator,
        MultiValidator,
    )

    processor = BasicDataProcessor()
    processed_data = processor.process(cleaned_data)
"""

from .basic_processor import (
    BasicDataProcessor,
    TemporalAligner,
    AssetProfiler,
)

from .advanced_processors import (
    MissingDataHandler,
    FeatureEngineer,
    DataAggregator,
    MultiValidator,
)

__all__ = [
    # Basic processors
    'BasicDataProcessor',
    'TemporalAligner',
    'AssetProfiler',
    # Advanced processors
    'MissingDataHandler',
    'FeatureEngineer',
    'DataAggregator',
    'MultiValidator',
]
