"""
Basic Data Processor Implementation

This module provides fundamental data processing operations.
Implements the IProcessor interface.

Used by: Data pipeline for preparing cleaned data for analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

from src.data_pipeline.sources.base_source import IProcessor

logger = logging.getLogger("hk_quant_system.basic_processor")


class BasicDataProcessor(IProcessor):
    """
    Basic data processor for OHLCV data.

    Performs:
    - Data normalization (min-max, z-score)
    - Return calculations
    - Technical indicators preparation
    - Data alignment

    Example:
        >>> processor = BasicDataProcessor()
        >>> cleaned_data = pd.DataFrame({...})
        >>> processed = processor.process(cleaned_data)
        >>> info = processor.get_processing_info()
    """

    def __init__(
        self,
        normalize_prices: bool = True,
        normalize_volume: bool = True,
        calculate_returns: bool = True,
    ):
        """
        Initialize processor.

        Args:
            normalize_prices: Normalize price columns (default: True)
            normalize_volume: Normalize volume (default: True)
            calculate_returns: Calculate returns (default: True)
        """
        self.normalize_prices = normalize_prices
        self.normalize_volume = normalize_volume
        self.calculate_returns = calculate_returns

        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process cleaned data.

        Args:
            data: Cleaned OHLCV DataFrame

        Returns:
            Processed DataFrame with additional columns
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        if data.empty:
            logger.warning("Input DataFrame is empty")
            return data

        df = data.copy()
        self.processing_info = {
            'initial_rows': len(df),
            'operations': [],
        }

        # Ensure proper index
        if 'Date' in df.columns and df.index.name != 'Date':
            df.set_index('Date', inplace=True)

        # Step 1: Calculate returns
        if self.calculate_returns:
            df = self._calculate_returns(df)

        # Step 2: Normalize prices
        if self.normalize_prices:
            df = self._normalize_prices(df)

        # Step 3: Normalize volume
        if self.normalize_volume:
            df = self._normalize_volume(df)

        # Step 4: Forward fill NaN values from calculations
        df = self._forward_fill(df)

        self.processing_info['final_rows'] = len(df)
        self.processing_info['columns'] = list(df.columns)
        self.processing_info['temporal_aligned'] = True
        self.processing_info['normalized'] = (
            self.normalize_prices or self.normalize_volume
        )

        logger.info(
            f"Processed {self.processing_info['initial_rows']} rows "
            f"→ {self.processing_info['final_rows']} rows "
            f"(operations: {len(self.processing_info['operations'])})"
        )

        return df

    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns."""
        if 'Close' not in df.columns:
            return df

        # Daily return
        df['Daily_Return'] = df['Close'].pct_change()

        # Log return
        df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))

        # Intraday return (Close/Open - 1)
        df['Intraday_Return'] = (df['Close'] - df['Open']) / df['Open']

        self.processing_info['operations'].append('calculated_returns')

        return df

    def _normalize_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize price columns."""
        price_cols = ['Open', 'High', 'Low', 'Close']
        available_cols = [c for c in price_cols if c in df.columns]

        for col in available_cols:
            # Min-max normalization (0-1 scale)
            min_val = df[col].min()
            max_val = df[col].max()

            if max_val > min_val:
                df[f'{col}_Normalized'] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[f'{col}_Normalized'] = 0.5

        self.processing_info['operations'].append('normalized_prices')

        return df

    def _normalize_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize volume."""
        if 'Volume' not in df.columns:
            return df

        # Min-max normalization
        min_vol = df['Volume'].min()
        max_vol = df['Volume'].max()

        if max_vol > min_vol:
            df['Volume_Normalized'] = (df['Volume'] - min_vol) / (max_vol - min_vol)
        else:
            df['Volume_Normalized'] = 0.5

        # Z-score normalization for comparison
        vol_mean = df['Volume'].mean()
        vol_std = df['Volume'].std()

        if vol_std > 0:
            df['Volume_ZScore'] = (df['Volume'] - vol_mean) / vol_std
        else:
            df['Volume_ZScore'] = 0

        self.processing_info['operations'].append('normalized_volume')

        return df

    def _forward_fill(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward fill NaN values from calculations."""
        # Only for calculated columns, not original data
        calculated_cols = [
            c for c in df.columns if c.endswith('_Return') or c.endswith('_Normalized')
        ]

        for col in calculated_cols:
            df[col] = df[col].fillna(method='ffill')

        # Replace first NaN (from pct_change) with 0
        for col in calculated_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        return df

    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get processing information.

        Returns:
            Dictionary with:
                - initial_rows: Initial number of rows
                - final_rows: Final number of rows
                - operations: List of operations applied
                - temporal_aligned: Whether data is temporally aligned
                - normalized: Whether data was normalized
                - columns: Final column list
        """
        return self.processing_info.copy()


class TemporalAligner(IProcessor):
    """
    Align data to specific time frequency.

    Handles data with different timestamps and frequencies
    (e.g., different trading calendars, missing trading days).
    """

    def __init__(self, frequency: str = 'D', fill_method: str = 'forward'):
        """
        Initialize temporal aligner.

        Args:
            frequency: Target frequency ('D' for daily, 'H' for hourly, etc.)
            fill_method: How to fill gaps ('forward', 'interpolate', 'drop')
        """
        self.frequency = frequency
        self.fill_method = fill_method
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Align data to target frequency.

        Args:
            data: DataFrame with DatetimeIndex

        Returns:
            Temporally aligned DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        if data.empty:
            return data

        df = data.copy()
        self.processing_info = {
            'initial_rows': len(df),
            'operations': [],
        }

        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'Date' in df.columns:
                df.set_index('Date', inplace=True)
            else:
                logger.warning("No datetime index found")
                return df

        # Find frequency
        inferred_freq = pd.infer_freq(df.index)
        self.processing_info['inferred_frequency'] = str(inferred_freq)

        # Create complete date range
        start_date = df.index.min()
        end_date = df.index.max()
        complete_dates = pd.date_range(start=start_date, end=end_date, freq=self.frequency)

        # Reindex
        df = df.reindex(complete_dates)

        # Fill gaps
        if self.fill_method == 'forward':
            df = df.fillna(method='ffill')
            self.processing_info['operations'].append('forward_fill')
        elif self.fill_method == 'interpolate':
            df = df.interpolate(method='linear')
            self.processing_info['operations'].append('linear_interpolate')
        elif self.fill_method == 'drop':
            df = df.dropna()
            self.processing_info['operations'].append('drop_na')

        self.processing_info['final_rows'] = len(df)
        self.processing_info['temporal_aligned'] = True

        return df

    def get_processing_info(self) -> Dict[str, Any]:
        """Get temporal alignment information."""
        return self.processing_info.copy()


class AssetProfiler(IProcessor):
    """
    Add asset profile information to data.

    Enriches price data with company/asset information.
    """

    def __init__(self, asset_info: Dict[str, Any] = None):
        """
        Initialize asset profiler.

        Args:
            asset_info: Optional dictionary with asset metadata
        """
        self.asset_info = asset_info or {}
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add asset profile columns.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with asset profile columns
        """
        df = data.copy()
        self.processing_info = {'operations': []}

        # Add asset profile columns
        if self.asset_info:
            for key, value in self.asset_info.items():
                df[f'asset_{key}'] = value
                self.processing_info['operations'].append(f'added_{key}')

        self.processing_info['asset_columns'] = [
            c for c in df.columns if c.startswith('asset_')
        ]

        return df

    def get_processing_info(self) -> Dict[str, Any]:
        """Get profiling information."""
        return self.processing_info.copy()
