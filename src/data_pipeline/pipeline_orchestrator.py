"""
Data Pipeline Orchestrator

Coordinates the complete data pipeline workflow:
Data Source → Validation → Cleaning → Processing → Output

This orchestrator manages:
1. Data fetching from various sources
2. Data validation
3. Cleaning operations
4. Processing transformations
5. Output caching and delivery

Used by: All data pipeline consumers (backtest, analysis, monitoring)
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .sources import (
    IDataSource,
    FileDataSource,
    HKEXDataSource,
)
from .cleaners import BasicDataCleaner
from .processors import BasicDataProcessor

logger = logging.getLogger("hk_quant_system.pipeline_orchestrator")


class DataPipelineOrchestrator:
    """
    Orchestrates the complete data pipeline.

    Manages data flow from source through validation, cleaning, and processing.

    Example:
        >>> orchestrator = DataPipelineOrchestrator()
        >>> orchestrator.register_source("hkex", HKEXDataSource())
        >>> result = orchestrator.process(
        ...     source="hkex",
        ...     symbol="0700.hk",
        ...     start_date="2023-01-01",
        ...     end_date="2024-01-01"
        ... )
        >>> df = result['processed_data']
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.sources: Dict[str, IDataSource] = {}
        self.cleaner = BasicDataCleaner()
        self.processor = BasicDataProcessor()
        self.pipeline_history: List[Dict[str, Any]] = []

    def register_source(self, name: str, source: IDataSource) -> None:
        """
        Register a data source.

        Args:
            name: Source identifier (e.g., 'hkex', 'csv', 'api')
            source: IDataSource implementation
        """
        self.sources[name] = source
        logger.info(f"Registered data source: {name}")

    def process(
        self,
        source: str,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process data through full pipeline.

        Args:
            source: Source name (must be registered)
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            **kwargs: Additional source-specific parameters

        Returns:
            Dictionary containing:
                - raw_data: Original raw data
                - validation_result: Validation results
                - cleaned_data: Cleaned DataFrame
                - processed_data: Final processed DataFrame
                - pipeline_info: Metadata about processing
        """
        if source not in self.sources:
            raise ValueError(
                f"Unknown source: {source}. "
                f"Available: {list(self.sources.keys())}"
            )

        # Convert dates
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        pipeline_info = {
            'source': source,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'steps': [],
            'started_at': datetime.now().isoformat(),
        }

        try:
            # Step 1: Fetch raw data
            logger.info(f"Fetching {symbol} from {source}...")
            raw_data = self.sources[source].fetch_raw(
                symbol, start_dt, end_dt, **kwargs
            )
            pipeline_info['steps'].append('fetch')

            # Step 2: Validate
            logger.info("Validating data...")
            validation_result = self.sources[source].validate(raw_data)
            pipeline_info['validation_quality'] = validation_result.quality_score
            pipeline_info['validation_errors'] = len(validation_result.errors)
            pipeline_info['steps'].append('validate')

            # Step 3: Convert to DataFrame if needed
            if isinstance(raw_data.get('data'), pd.DataFrame):
                df = raw_data['data']
            else:
                logger.info("Converting to DataFrame...")
                df = self.sources[source].convert_to_dataframe(raw_data)

            # Step 4: Clean
            logger.info("Cleaning data...")
            cleaned_data = self.cleaner.clean(df)
            pipeline_info['clean_quality'] = self.cleaner.get_quality_score()
            pipeline_info['steps'].append('clean')

            # Step 5: Process
            logger.info("Processing data...")
            processed_data = self.processor.process(cleaned_data)
            pipeline_info['process_info'] = self.processor.get_processing_info()
            pipeline_info['steps'].append('process')

            # Step 6: Generate output
            pipeline_info['finished_at'] = datetime.now().isoformat()
            pipeline_info['success'] = True

            result = {
                'raw_data': raw_data,
                'validation_result': validation_result,
                'cleaned_data': cleaned_data,
                'processed_data': processed_data,
                'pipeline_info': pipeline_info,
            }

            # Store in history
            self.pipeline_history.append(pipeline_info)

            logger.info(
                f"Pipeline completed successfully for {symbol} "
                f"({len(processed_data)} rows)"
            )

            return result

        except Exception as e:
            pipeline_info['finished_at'] = datetime.now().isoformat()
            pipeline_info['success'] = False
            pipeline_info['error'] = str(e)

            logger.error(f"Pipeline failed for {symbol}: {e}")

            return {
                'error': str(e),
                'pipeline_info': pipeline_info,
            }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get pipeline execution history."""
        return self.pipeline_history.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        total = len(self.pipeline_history)
        successful = sum(1 for p in self.pipeline_history if p.get('success'))

        return {
            'total_runs': total,
            'successful_runs': successful,
            'failed_runs': total - successful,
            'success_rate': successful / total if total > 0 else 0,
            'sources': list(self.sources.keys()),
        }


def create_default_orchestrator() -> DataPipelineOrchestrator:
    """
    Create orchestrator with default sources.

    Returns:
        Configured DataPipelineOrchestrator

    Example:
        >>> orch = create_default_orchestrator()
        >>> result = orch.process('hkex', '0700.hk', '2023-01-01', '2024-01-01')
    """
    orch = DataPipelineOrchestrator()

    # Register default sources
    orch.register_source('hkex', HKEXDataSource())
    orch.register_source('file', FileDataSource('data/raw'))

    return orch
