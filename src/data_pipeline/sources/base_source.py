"""
Base interfaces for data sources in the Data Management Layer.

This module defines the standard interfaces that all data sources must implement.
These interfaces ensure consistent behavior across different data source implementations
(HTTP API, files, market data feeds, etc.)

Author: Claude Code
Date: 2025-10-25
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: list = None
    warnings: list = None
    quality_score: float = 1.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class DataMetadata:
    """Metadata about fetched data."""
    symbol: str
    start_date: datetime
    end_date: datetime
    record_count: int
    source_name: str
    last_updated: datetime
    data_frequency: str  # 'daily', 'hourly', etc.
    has_missing_data: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'symbol': self.symbol,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'record_count': self.record_count,
            'source_name': self.source_name,
            'last_updated': self.last_updated.isoformat(),
            'data_frequency': self.data_frequency,
            'has_missing_data': self.has_missing_data,
        }


class IDataSource(ABC):
    """
    Interface for all data sources in the Data Management Layer.

    Every data source adapter (HTTP API, files, market feeds, etc.) must implement this interface
    to ensure consistent data fetching and validation behavior.

    Typical usage:
        source = HttpApiDataSource(url="http://api.example.com")
        raw_data = source.fetch_raw("0700.HK", start_date, end_date)
        validation = source.validate(raw_data)
        if validation.is_valid:
            metadata = source.get_metadata()
    """

    @abstractmethod
    def fetch_raw(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch raw data from the source.

        Args:
            symbol: Stock symbol (e.g., "0700.HK")
            start_date: Data start date (inclusive)
            end_date: Data end date (inclusive)
            **kwargs: Additional parameters specific to the data source

        Returns:
            Dictionary with raw data (typically contains 'data', 'metadata' keys)

        Raises:
            ConnectionError: If unable to connect to data source
            ValueError: If symbol or date range is invalid

        Example:
            >>> source = HttpApiDataSource()
            >>> data = source.fetch_raw("0700.HK", datetime(2023,1,1), datetime(2023,12,31))
            >>> df = pd.DataFrame(data['data'])
        """
        pass

    @abstractmethod
    def validate(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate the fetched data.

        Checks for:
        - Required columns (OHLCV)
        - Data type correctness
        - Date range consistency
        - Missing values
        - Logical consistency (e.g., High >= Low)

        Args:
            raw_data: Raw data dictionary returned by fetch_raw()

        Returns:
            ValidationResult with is_valid flag and any errors/warnings

        Example:
            >>> raw_data = source.fetch_raw(...)
            >>> result = source.validate(raw_data)
            >>> print(f"Valid: {result.is_valid}, Quality: {result.quality_score}")
        """
        pass

    @abstractmethod
    def get_metadata(self) -> DataMetadata:
        """
        Get metadata about the last fetched data.

        Returns:
            DataMetadata object with source information

        Example:
            >>> metadata = source.get_metadata()
            >>> print(f"Records: {metadata.record_count}, Updated: {metadata.last_updated}")
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Source identifier (e.g., 'http_api', 'yahoo_finance')."""
        pass


class IDataCleaner(ABC):
    """
    Interface for data cleaning implementations.

    Data cleaners are responsible for transforming raw data into clean, standardized format.
    They handle outlier removal, missing data, format normalization, etc.
    """

    @abstractmethod
    def clean(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the raw data.

        Args:
            raw_data: Raw DataFrame with OHLCV columns

        Returns:
            Cleaned DataFrame

        Example:
            >>> raw_df = pd.DataFrame(raw_data)
            >>> clean_df = cleaner.clean(raw_df)
        """
        pass

    @abstractmethod
    def get_quality_score(self) -> float:
        """
        Get the quality score of the last cleaned data (0-1 scale).

        Returns:
            Quality score (1.0 = perfect data, 0.0 = very poor)
        """
        pass

    @property
    @abstractmethod
    def cleaning_operations_applied(self) -> list:
        """List of cleaning operations that were applied."""
        pass


class IProcessor(ABC):
    """
    Interface for data processing implementations.

    Processors handle temporal alignment, normalization, and other transformations
    needed to prepare data for analysis.
    """

    @abstractmethod
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process the cleaned data.

        Args:
            data: Cleaned DataFrame

        Returns:
            Processed DataFrame ready for analysis

        Example:
            >>> processed_df = processor.process(clean_df)
        """
        pass

    @abstractmethod
    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about processing applied."""
        pass


# Type aliases for common patterns
DataSourceFactory = type[IDataSource]
CleanerFactory = type[IDataCleaner]
ProcessorFactory = type[IProcessor]
