"""
Basic Data Cleaner Implementation

This module provides fundamental data cleaning operations for OHLCV data.
Implements the IDataCleaner interface.

Used by: Data pipeline for cleaning raw market data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging

from src.data_pipeline.sources.base_source import IDataCleaner

logger = logging.getLogger("hk_quant_system.basic_cleaner")


class BasicDataCleaner(IDataCleaner):
    """
    Basic data cleaner for OHLCV data.

    Performs:
    - Removal of NaN/null values
    - Data type conversion
    - Price consistency validation
    - Volume normalization

    Example:
        >>> cleaner = BasicDataCleaner()
        >>> raw_data = pd.DataFrame({...})
        >>> cleaned = cleaner.clean(raw_data)
        >>> score = cleaner.get_quality_score()
    """

    def __init__(
        self,
        remove_nulls: bool = True,
        remove_duplicates: bool = True,
        validate_prices: bool = True,
        min_volume: int = 0,
    ):
        """
        Initialize basic cleaner.

        Args:
            remove_nulls: Remove rows with null values (default: True)
            remove_duplicates: Remove duplicate rows (default: True)
            validate_prices: Validate High >= Low, etc. (default: True)
            min_volume: Minimum volume threshold (default: 0)
        """
        self.remove_nulls = remove_nulls
        self.remove_duplicates = remove_duplicates
        self.validate_prices = validate_prices
        self.min_volume = min_volume

        self.last_quality_score = 1.0
        self.operations_applied = []
        self.removed_rows = 0

    def clean(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean raw data.

        Args:
            raw_data: Raw OHLCV DataFrame

        Returns:
            Cleaned DataFrame with standardized columns
        """
        if not isinstance(raw_data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        if raw_data.empty:
            logger.warning("Input DataFrame is empty")
            return raw_data

        df = raw_data.copy()
        initial_rows = len(df)
        self.operations_applied = []

        # Step 1: Standardize column names
        df = self._standardize_columns(df)

        # Step 2: Convert data types
        df = self._convert_data_types(df)

        # Step 3: Handle null values
        if self.remove_nulls:
            df = self._remove_nulls(df)

        # Step 4: Remove duplicates
        if self.remove_duplicates:
            df = self._remove_duplicates(df)

        # Step 5: Validate price consistency
        if self.validate_prices:
            df = self._validate_prices(df)

        # Step 6: Filter by volume
        if self.min_volume > 0:
            df = self._filter_by_volume(df)

        # Step 7: Sort by date
        if 'Date' in df.columns:
            df = df.sort_values('Date')
            self.operations_applied.append('sorted_by_date')

        # Calculate quality score
        self.removed_rows = initial_rows - len(df)
        self._calculate_quality_score(initial_rows)

        logger.info(
            f"Cleaned {initial_rows} rows → {len(df)} rows "
            f"(removed {self.removed_rows}, quality: {self.last_quality_score:.2%})"
        )

        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to OHLCV format."""
        column_mapping = {
            'open': 'Open',
            'Open': 'Open',
            'high': 'High',
            'High': 'High',
            'low': 'Low',
            'Low': 'Low',
            'close': 'Close',
            'Close': 'Close',
            'volume': 'Volume',
            'Volume': 'Volume',
            'date': 'Date',
            'Date': 'Date',
            'datetime': 'Date',
            'Datetime': 'Date',
            'timestamp': 'Date',
            'Timestamp': 'Date',
        }

        df = df.rename(columns=column_mapping)
        self.operations_applied.append('standardized_columns')

        return df

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert data types to appropriate formats."""
        # Convert date columns
        if 'Date' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['Date'])
                if df.index.name != 'Date':
                    df = df.set_index('Date')
            except Exception as e:
                logger.warning(f"Could not convert Date column: {e}")

        # Convert OHLC to float
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Could not convert {col} to numeric: {e}")

        # Convert Volume to int
        if 'Volume' in df.columns:
            try:
                df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').astype('Int64')
            except Exception as e:
                logger.warning(f"Could not convert Volume: {e}")

        self.operations_applied.append('converted_data_types')

        return df

    def _remove_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows with null values."""
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        cols_to_check = [c for c in required_cols if c in df.columns]

        null_count_before = df[cols_to_check].isnull().sum().sum()

        if null_count_before > 0:
            df = df.dropna(subset=cols_to_check)
            logger.info(f"Removed {null_count_before} null values")
            self.operations_applied.append('removed_nulls')

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows."""
        dup_count = df.duplicated().sum()

        if dup_count > 0:
            df = df.drop_duplicates()
            logger.info(f"Removed {dup_count} duplicate rows")
            self.operations_applied.append('removed_duplicates')

        return df

    def _validate_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate price consistency and remove invalid rows."""
        if not all(c in df.columns for c in ['High', 'Low', 'Open', 'Close']):
            return df

        invalid_rows = []

        # High should be >= all prices
        invalid = df['High'] < df['Low']
        invalid_rows.extend(df[invalid].index.tolist())

        invalid = df['High'] < df['Open']
        invalid_rows.extend(df[invalid].index.tolist())

        invalid = df['High'] < df['Close']
        invalid_rows.extend(df[invalid].index.tolist())

        # Low should be <= all prices
        invalid = df['Low'] > df['Open']
        invalid_rows.extend(df[invalid].index.tolist())

        invalid = df['Low'] > df['Close']
        invalid_rows.extend(df[invalid].index.tolist())

        # Remove invalid rows
        invalid_rows = list(set(invalid_rows))
        if invalid_rows:
            logger.warning(f"Removing {len(invalid_rows)} rows with invalid price data")
            df = df.drop(invalid_rows)
            self.operations_applied.append('validated_prices')

        return df

    def _filter_by_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter rows by minimum volume threshold."""
        if 'Volume' not in df.columns:
            return df

        before = len(df)
        df = df[df['Volume'] >= self.min_volume]
        after = len(df)

        if after < before:
            logger.info(f"Filtered {before - after} rows below volume threshold")
            self.operations_applied.append(f'filtered_by_volume_>={self.min_volume}')

        return df

    def _calculate_quality_score(self, initial_rows: int) -> None:
        """Calculate data quality score."""
        if initial_rows == 0:
            self.last_quality_score = 0.0
            return

        # Quality is based on:
        # 1. Data retention (more rows = better, but some removal is expected)
        # 2. Number of cleaning operations (more operations = more issues)

        retention_ratio = max(0, (initial_rows - self.removed_rows) / initial_rows)

        # Operations penalty (each major operation reduces quality)
        operation_penalty = min(0.2, len(self.operations_applied) * 0.02)

        self.last_quality_score = max(0.5, retention_ratio - operation_penalty)

    def get_quality_score(self) -> float:
        """
        Get data quality score.

        Returns:
            Quality score between 0 and 1
        """
        return self.last_quality_score

    @property
    def cleaning_operations_applied(self) -> List[str]:
        """Get list of cleaning operations applied."""
        return self.operations_applied.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cleaning statistics.

        Returns:
            Dictionary with:
                - rows_removed: Number of rows removed
                - quality_score: Data quality score
                - operations: List of operations applied
        """
        return {
            'rows_removed': self.removed_rows,
            'quality_score': self.last_quality_score,
            'operations': self.operations_applied,
        }


class OutlierDetector(IDataCleaner):
    """
    Detect and handle outliers in OHLCV data.

    Uses statistical methods (z-score, IQR) to identify and remove outliers.
    """

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        use_iqr: bool = True,
        iqr_multiplier: float = 1.5,
        remove_outliers: bool = False,
    ):
        """
        Initialize outlier detector.

        Args:
            z_score_threshold: Z-score threshold for outliers (default: 3.0)
            use_iqr: Use IQR method as well (default: True)
            iqr_multiplier: IQR multiplier (default: 1.5)
            remove_outliers: Remove outliers or just flag them (default: False)
        """
        self.z_score_threshold = z_score_threshold
        self.use_iqr = use_iqr
        self.iqr_multiplier = iqr_multiplier
        self.remove_outliers = remove_outliers

        self.last_quality_score = 1.0
        self.operations_applied = []
        self.outliers_detected = 0

    def clean(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and handle outliers.

        Args:
            raw_data: Raw OHLCV DataFrame

        Returns:
            DataFrame with outliers removed or flagged
        """
        df = raw_data.copy()
        self.operations_applied = []
        self.outliers_detected = 0

        # Detect outliers in price columns
        for col in ['Open', 'High', 'Low', 'Close']:
            if col not in df.columns:
                continue

            # Z-score method
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            z_outliers = z_scores > self.z_score_threshold

            # IQR method
            if self.use_iqr:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.iqr_multiplier * IQR
                upper_bound = Q3 + self.iqr_multiplier * IQR
                iqr_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)

                outliers = z_outliers | iqr_outliers
            else:
                outliers = z_outliers

            self.outliers_detected += outliers.sum()

            if self.remove_outliers and outliers.sum() > 0:
                logger.warning(f"Removing {outliers.sum()} outliers in {col}")
                df = df[~outliers]
                self.operations_applied.append(f'removed_outliers_{col}')

        self.last_quality_score = 0.9 - (self.outliers_detected * 0.01)

        return df

    def get_quality_score(self) -> float:
        """Get quality score."""
        return max(0, self.last_quality_score)

    @property
    def cleaning_operations_applied(self) -> List[str]:
        """Get applied operations."""
        return self.operations_applied.copy()
