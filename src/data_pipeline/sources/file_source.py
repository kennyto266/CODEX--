"""
File-Based Data Source Implementation

This module provides a data source for reading OHLCV data from local files
(CSV, Excel, JSON). It implements the IDataSource interface.

Used by: Data pipeline for loading historical data from local storage
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

from .base_source import (
    IDataSource,
    ValidationResult,
    DataMetadata,
)

logger = logging.getLogger("hk_quant_system.file_source")


class FileDataSource(IDataSource):
    """File-based data source for reading OHLCV data from local files."""

    def __init__(self, data_directory: str = "data/raw"):
        """
        Initialize file-based data source.

        Args:
            data_directory: Root directory for data files (default: 'data/raw')

        Example:
            >>> source = FileDataSource("data/raw")
            >>> data = source.fetch_raw("0700.HK", "2023-01-01", "2024-01-01")
        """
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.last_metadata: Optional[DataMetadata] = None
        self._supported_formats = ['.csv', '.xlsx', '.json']

    def fetch_raw(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch data from local file.

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            start_date: Start date for filtering
            end_date: End date for filtering
            **kwargs: Additional parameters (e.g., file_path)

        Returns:
            Dictionary containing:
                - data: DataFrame or list of records
                - symbol: Stock symbol
                - start_date: Start date
                - end_date: End date
                - source: 'file'
                - file_path: Path to source file
                - raw_format: File format used

        Raises:
            FileNotFoundError: If file not found
            ValueError: If unsupported file format
        """
        # Get file path from kwargs or construct from symbol
        file_path = kwargs.get('file_path')

        if file_path is None:
            # Try to find file matching symbol
            file_path = self._find_file_for_symbol(symbol)

        if file_path is None:
            raise FileNotFoundError(
                f"No data file found for symbol {symbol} in {self.data_directory}"
            )

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load based on file format
        file_suffix = file_path.suffix.lower()

        if file_suffix == '.csv':
            df = pd.read_csv(file_path)
            raw_format = 'csv'
        elif file_suffix == '.xlsx':
            df = pd.read_excel(file_path)
            raw_format = 'xlsx'
        elif file_suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            raw_format = 'json'
        else:
            raise ValueError(
                f"Unsupported file format: {file_suffix}. "
                f"Supported formats: {self._supported_formats}"
            )

        # Filter by date range
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        logger.info(f"Loaded {len(df)} records from {file_path}")

        return {
            'data': df,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'source': 'file',
            'file_path': str(file_path),
            'raw_format': raw_format,
        }

    def validate(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate data from file.

        Args:
            raw_data: Raw data dictionary from fetch_raw()

        Returns:
            ValidationResult with quality assessment
        """
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            data = raw_data.get('data')

            # Check if data exists
            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                errors.append("No data loaded from file")
                quality_score = 0.0
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    quality_score=quality_score,
                )

            # Convert to DataFrame if needed
            if isinstance(data, pd.DataFrame):
                df = data
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                errors.append("Unsupported data format")
                quality_score = 0.0

            # Check required OHLCV columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [c for c in required_cols if c not in df.columns]

            if missing_cols:
                # Try with lowercase
                lowercase_missing = []
                for col in missing_cols:
                    if col.lower() in df.columns:
                        df = df.rename(columns={col.lower(): col})
                    else:
                        lowercase_missing.append(col)

                if lowercase_missing:
                    warnings.append(f"Missing columns: {lowercase_missing}")
                    quality_score *= 0.7

            # Check for null values
            null_count = df[required_cols].isnull().sum().sum()
            if null_count > 0:
                warnings.append(f"Found {null_count} null values in OHLCV data")
                quality_score *= 0.8

            # Check data consistency (High >= Low, etc.)
            if 'High' in df.columns and 'Low' in df.columns:
                inconsistent = (df['High'] < df['Low']).sum()
                if inconsistent > 0:
                    warnings.append(
                        f"Found {inconsistent} records where High < Low"
                    )
                    quality_score *= 0.7

            # Check minimum records
            if len(df) < 5:
                warnings.append(f"Only {len(df)} records in file (minimum 5 recommended)")
                quality_score *= 0.6

            # File source quality is generally lower than API
            quality_score *= 0.85

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            quality_score = 0.0

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0, min(1, quality_score)),
        )

    def get_metadata(self) -> DataMetadata:
        """
        Get metadata about the data source.

        Returns:
            DataMetadata with source information
        """
        if self.last_metadata is None:
            self.last_metadata = DataMetadata(
                symbol='unknown',
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now(),
                record_count=0,
                source_name='file',
                last_updated=datetime.now(),
                data_frequency='daily',
                has_missing_data=False,
            )

        return self.last_metadata

    @property
    def source_name(self) -> str:
        """Return source name."""
        return f"file ({self.data_directory})"

    def _find_file_for_symbol(self, symbol: str) -> Optional[Path]:
        """
        Find data file for a given symbol.

        Searches for files matching pattern: symbol.* or symbol_*.* in data directory

        Args:
            symbol: Stock symbol to search for

        Returns:
            Path to file if found, None otherwise
        """
        # Normalize symbol for filename
        clean_symbol = symbol.replace('.', '_').replace('-', '_').upper()

        for file_path in self.data_directory.glob('*'):
            if file_path.is_file():
                # Check if filename contains symbol
                filename = file_path.stem.upper()

                if symbol.upper() in filename or clean_symbol in filename:
                    return file_path

        return None

    def list_available_symbols(self) -> List[str]:
        """
        List all available symbols with data files.

        Returns:
            List of symbol strings found in data directory
        """
        symbols = []

        for file_path in self.data_directory.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self._supported_formats:
                # Extract symbol from filename
                symbol = file_path.stem
                symbols.append(symbol)

        return sorted(list(set(symbols)))


class CSVDataSource(FileDataSource):
    """Specialized file source for CSV files."""

    def __init__(self, csv_directory: str = "data/raw"):
        """Initialize CSV data source."""
        super().__init__(csv_directory)
        self._supported_formats = ['.csv']

    @property
    def source_name(self) -> str:
        """Return source name."""
        return f"csv ({self.data_directory})"


class ExcelDataSource(FileDataSource):
    """Specialized file source for Excel files."""

    def __init__(self, excel_directory: str = "data/raw"):
        """Initialize Excel data source."""
        super().__init__(excel_directory)
        self._supported_formats = ['.xlsx', '.xls']

    @property
    def source_name(self) -> str:
        """Return source name."""
        return f"excel ({self.data_directory})"
