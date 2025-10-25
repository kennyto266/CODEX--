"""
Advanced Data Processors

Provides advanced data processing operations for feature engineering,
data aggregation, and validation.

Used by: Data pipeline for complex data transformations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable, Optional
import logging

from src.data_pipeline.sources.base_source import IProcessor

logger = logging.getLogger("hk_quant_system.advanced_processors")


class MissingDataHandler(IProcessor):
    """
    Handle missing data in time series.

    Strategies:
    - Forward fill: Propagate last valid observation
    - Backward fill: Propagate next valid observation
    - Interpolation: Linear, polynomial, or spline
    - Drop: Remove rows with missing values
    """

    def __init__(
        self,
        strategy: str = "forward_fill",
        threshold: float = 0.3,
        limit: Optional[int] = None,
    ):
        """
        Initialize missing data handler.

        Args:
            strategy: Fill strategy ('forward_fill', 'backward_fill', 'interpolate', 'drop')
            threshold: Drop rows with >threshold % missing (0-1)
            limit: Maximum consecutive fills (None = unlimited)
        """
        self.strategy = strategy
        self.threshold = threshold
        self.limit = limit
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing data.

        Args:
            data: DataFrame with potential missing values

        Returns:
            DataFrame with missing values handled
        """
        df = data.copy()
        self.processing_info = {
            'initial_nulls': df.isnull().sum().sum(),
            'operations': [],
        }

        if df.empty:
            return df

        # Step 1: Drop rows exceeding threshold
        null_fraction = df.isnull().sum(axis=1) / len(df.columns)
        rows_to_drop = null_fraction > self.threshold

        if rows_to_drop.sum() > 0:
            logger.warning(f"Dropping {rows_to_drop.sum()} rows with >{self.threshold*100}% missing")
            df = df[~rows_to_drop]
            self.processing_info['operations'].append(
                f'dropped_{rows_to_drop.sum()}_high_missing_rows'
            )

        # Step 2: Apply fill strategy
        if self.strategy == "forward_fill":
            df = df.fillna(method='ffill', limit=self.limit)
            self.processing_info['operations'].append('forward_filled')

        elif self.strategy == "backward_fill":
            df = df.fillna(method='bfill', limit=self.limit)
            self.processing_info['operations'].append('backward_filled')

        elif self.strategy == "interpolate":
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = df[col].interpolate(method='linear', limit=self.limit)
            self.processing_info['operations'].append('interpolated')

        elif self.strategy == "drop":
            df = df.dropna()
            self.processing_info['operations'].append('dropped_na_rows')

        # Step 3: Forward/backward fill any remaining
        df = df.fillna(method='ffill').fillna(method='bfill')

        self.processing_info['final_nulls'] = df.isnull().sum().sum()
        self.processing_info['nulls_removed'] = (
            self.processing_info['initial_nulls'] - self.processing_info['final_nulls']
        )

        return df

    def get_processing_info(self) -> Dict[str, Any]:
        """Get processing information."""
        return self.processing_info.copy()


class FeatureEngineer(IProcessor):
    """
    Create derived features from OHLCV data.

    Features:
    - Technical indicators (SMA, RSI, MACD, Bollinger Bands)
    - Volatility measures
    - Volume-based indicators
    - Price action patterns
    """

    def __init__(
        self,
        features: List[str] = None,
        windows: Dict[str, int] = None,
    ):
        """
        Initialize feature engineer.

        Args:
            features: List of features to calculate
            windows: Dictionary of window sizes for indicators
        """
        if features is None:
            features = ['sma', 'rsi', 'macd', 'volatility']

        if windows is None:
            windows = {
                'short': 20,
                'medium': 50,
                'long': 200,
                'rsi': 14,
                'macd_fast': 12,
                'macd_slow': 26,
            }

        self.features = features
        self.windows = windows
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        self.processing_info = {'features_created': [], 'rows': len(df)}

        if 'Close' not in df.columns:
            logger.warning("Close price not found, skipping feature engineering")
            return df

        # SMA
        if 'sma' in self.features:
            for window in [self.windows['short'], self.windows['medium'], self.windows['long']]:
                df[f'SMA_{window}'] = df['Close'].rolling(window).mean()
                self.processing_info['features_created'].append(f'SMA_{window}')

        # Volatility
        if 'volatility' in self.features:
            df['Volatility_20'] = df['Close'].pct_change().rolling(20).std()
            self.processing_info['features_created'].append('Volatility_20')

        # RSI
        if 'rsi' in self.features:
            rsi_window = self.windows['rsi']
            df['RSI'] = self._calculate_rsi(df['Close'], rsi_window)
            self.processing_info['features_created'].append('RSI')

        # MACD
        if 'macd' in self.features:
            macd_fast = self.windows['macd_fast']
            macd_slow = self.windows['macd_slow']
            df['MACD'], df['MACD_Signal'] = self._calculate_macd(
                df['Close'], macd_fast, macd_slow
            )
            self.processing_info['features_created'].append('MACD')
            self.processing_info['features_created'].append('MACD_Signal')

        # Volume indicators
        if 'volume' in self.features and 'Volume' in df.columns:
            df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20']
            self.processing_info['features_created'].extend(['Volume_MA_20', 'Volume_Ratio'])

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
    ) -> tuple:
        """Calculate MACD and Signal line."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()

        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9).mean()

        return macd, signal

    def get_processing_info(self) -> Dict[str, Any]:
        """Get processing information."""
        return self.processing_info.copy()


class DataAggregator(IProcessor):
    """
    Aggregate data to different time frequencies.

    Converts daily data to weekly, monthly, or custom intervals.
    """

    def __init__(self, target_frequency: str = 'W'):
        """
        Initialize aggregator.

        Args:
            target_frequency: Target frequency ('D', 'W', 'M', 'Q', 'Y')
        """
        self.target_frequency = target_frequency
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate data to target frequency.

        Args:
            data: Daily OHLCV DataFrame

        Returns:
            Aggregated DataFrame
        """
        df = data.copy()
        self.processing_info = {
            'original_frequency': 'daily',
            'target_frequency': self.target_frequency,
            'original_rows': len(df),
        }

        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("Index is not DatetimeIndex, cannot aggregate")
            return df

        # OHLC aggregation
        agg_dict = {}

        if 'Open' in df.columns:
            agg_dict['Open'] = 'first'
        if 'High' in df.columns:
            agg_dict['High'] = 'max'
        if 'Low' in df.columns:
            agg_dict['Low'] = 'min'
        if 'Close' in df.columns:
            agg_dict['Close'] = 'last'
        if 'Volume' in df.columns:
            agg_dict['Volume'] = 'sum'

        # Aggregate
        df = df.resample(self.target_frequency).agg(agg_dict)

        # Remove rows with missing data
        df = df.dropna()

        self.processing_info['final_rows'] = len(df)
        self.processing_info['rows_removed'] = (
            self.processing_info['original_rows'] - self.processing_info['final_rows']
        )

        return df

    def get_processing_info(self) -> Dict[str, Any]:
        """Get processing information."""
        return self.processing_info.copy()


class MultiValidator(IProcessor):
    """
    Validate data against multiple criteria.

    Checks:
    - Price ranges
    - Volume thresholds
    - Time series consistency
    - Data completeness
    """

    def __init__(
        self,
        checks: List[str] = None,
        strict_mode: bool = False,
    ):
        """
        Initialize validator.

        Args:
            checks: List of checks to perform
            strict_mode: Raise exception on validation failure
        """
        if checks is None:
            checks = ['prices', 'volume', 'dates', 'completeness']

        self.checks = checks
        self.strict_mode = strict_mode
        self.processing_info = {}

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data.

        Args:
            data: DataFrame to validate

        Returns:
            DataFrame (unchanged if valid)

        Raises:
            ValueError: If strict_mode=True and validation fails
        """
        df = data.copy()
        self.processing_info = {'checks_performed': [], 'issues': []}

        # Price checks
        if 'prices' in self.checks:
            issues = self._validate_prices(df)
            if issues:
                self.processing_info['issues'].extend(issues)
            self.processing_info['checks_performed'].append('prices')

        # Volume checks
        if 'volume' in self.checks:
            issues = self._validate_volume(df)
            if issues:
                self.processing_info['issues'].extend(issues)
            self.processing_info['checks_performed'].append('volume')

        # Date checks
        if 'dates' in self.checks:
            issues = self._validate_dates(df)
            if issues:
                self.processing_info['issues'].extend(issues)
            self.processing_info['checks_performed'].append('dates')

        # Completeness checks
        if 'completeness' in self.checks:
            issues = self._validate_completeness(df)
            if issues:
                self.processing_info['issues'].extend(issues)
            self.processing_info['checks_performed'].append('completeness')

        # Raise or log issues
        if self.processing_info['issues']:
            if self.strict_mode:
                raise ValueError(
                    f"Validation failed with {len(self.processing_info['issues'])} issues"
                )
            else:
                logger.warning(
                    f"Validation found {len(self.processing_info['issues'])} issues"
                )

        return df

    def _validate_prices(self, df: pd.DataFrame) -> List[str]:
        """Validate price data."""
        issues = []

        for col in ['Open', 'High', 'Low', 'Close']:
            if col not in df.columns:
                continue

            # Check for negative prices
            if (df[col] < 0).any():
                issues.append(f"{col}: negative prices found")

            # Check for extreme values
            if df[col].max() > 1e6:
                issues.append(f"{col}: extremely high value detected")

        # Check High >= Low
        if 'High' in df.columns and 'Low' in df.columns:
            if (df['High'] < df['Low']).any():
                issues.append("High < Low in some rows")

        return issues

    def _validate_volume(self, df: pd.DataFrame) -> List[str]:
        """Validate volume data."""
        issues = []

        if 'Volume' not in df.columns:
            return issues

        if (df['Volume'] < 0).any():
            issues.append("Negative volume found")

        if df['Volume'].sum() == 0:
            issues.append("Total volume is zero")

        return issues

    def _validate_dates(self, df: pd.DataFrame) -> List[str]:
        """Validate date index."""
        issues = []

        if not isinstance(df.index, pd.DatetimeIndex):
            issues.append("Index is not DatetimeIndex")
            return issues

        # Check for gaps
        expected_dates = pd.date_range(df.index.min(), df.index.max(), freq='D')
        missing = len(expected_dates) - len(df)

        if missing > 0:
            logger.debug(f"Date gaps detected: {missing} missing dates")

        return issues

    def _validate_completeness(self, df: pd.DataFrame) -> List[str]:
        """Validate data completeness."""
        issues = []

        # Check for required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [c for c in required if c not in df.columns]

        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for nulls
        null_count = df.isnull().sum().sum()
        if null_count > 0:
            logger.debug(f"Null values found: {null_count}")

        return issues

    def get_processing_info(self) -> Dict[str, Any]:
        """Get processing information."""
        return self.processing_info.copy()
