"""
Data Cleaning Engine for CODEX quantitative trading system.

This module provides comprehensive data cleaning and quality enhancement:
- Handle missing data (forward fill, interpolation)
- Normalize outliers (clipping, smoothing)
- Quality scoring (0-1 range)
- Data augmentation (technical indicators)

Cleaning pipeline stages:
1. Missing data handling
2. Outlier detection and normalization
3. Quality scoring
4. Data augmentation (optional)
"""

from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from enum import Enum

from src.data_pipeline.schemas import CleanedPriceData, RawPriceData
from src.data_pipeline.validators import DataValidator


class MissingDataStrategy(Enum):
    """Strategy for handling missing data."""
    FORWARD_FILL = "forward_fill"  # Use previous value
    INTERPOLATE = "interpolate"    # Linear interpolation
    BACKWARD_FILL = "backward_fill"  # Use next value
    DROP = "drop"                  # Remove rows with missing data


class OutlierNormalizationStrategy(Enum):
    """Strategy for normalizing outliers."""
    CLIP = "clip"                  # Clip to std bounds
    SMOOTH = "smooth"              # Moving average smoothing
    FLAG = "flag"                  # Flag but don't modify
    REMOVE = "remove"              # Remove outlier rows


class QualityScorer:
    """Calculate data quality score (0-1 range)."""

    def __init__(self):
        """Initialize quality scorer."""
        self.weights = {
            'completeness': 0.30,    # All fields present
            'ohlc_logic': 0.20,      # OHLC relationships valid
            'volume': 0.15,          # Volume reasonable
            'outliers': 0.20,        # No outliers detected
            'consistency': 0.15      # Consistent with trends
        }

    def score_completeness(self, record: pd.Series) -> float:
        """Score data completeness (no NaN values)."""
        if record.isnull().any():
            null_count = record.isnull().sum()
            return max(0, 1.0 - (null_count / len(record)))
        return 1.0

    def score_ohlc_logic(self, record: pd.Series) -> float:
        """Score OHLC relationship validity."""
        try:
            high = record.get('high')
            low = record.get('low')
            close = record.get('close')
            open_price = record.get('open')

            if None in [high, low, close, open_price]:
                return 0.5  # Incomplete

            # Check all relationships
            checks = [
                high >= low,
                high >= close,
                high >= open_price,
                low <= close,
                low <= open_price
            ]

            if all(checks):
                return 1.0
            else:
                return 0.0  # Invalid relationships
        except Exception:
            return 0.5

    def score_volume(self, record: pd.Series) -> float:
        """Score volume reasonableness."""
        try:
            volume = record.get('volume')
            if pd.isna(volume) or volume is None:
                return 0.5

            if volume < 0:
                return 0.0  # Negative volume is invalid

            if volume == 0:
                return 0.3  # Zero volume is suspicious (non-trading)

            return 1.0  # Positive volume is good
        except Exception:
            return 0.5

    def score_outliers(self, pct_change: float, threshold: float = 0.20) -> float:
        """Score based on outlier magnitude."""
        if abs(pct_change) <= threshold:
            return 1.0
        elif abs(pct_change) <= threshold * 2:
            return 0.7
        elif abs(pct_change) <= threshold * 3:
            return 0.4
        else:
            return 0.0

    def score_consistency(self, df: pd.DataFrame, idx: int) -> float:
        """Score consistency with surrounding data."""
        if idx == 0 or idx >= len(df) - 1:
            return 1.0  # Edge cases are consistent by definition

        try:
            prev_close = df.iloc[idx - 1]['close']
            curr_close = df.iloc[idx]['close']
            next_open = df.iloc[idx + 1]['open']

            # Check if current price relates to neighbors
            if pd.isna(prev_close) or pd.isna(curr_close) or pd.isna(next_open):
                return 0.5

            # Price should be reasonably related to neighbors
            max_change = 0.20  # 20% max daily change
            if (abs((curr_close - prev_close) / prev_close) <= max_change and
                abs((next_open - curr_close) / curr_close) <= max_change):
                return 1.0
            else:
                return 0.3
        except Exception:
            return 0.5

    def calculate_quality_score(self, df: pd.DataFrame, idx: int) -> float:
        """Calculate overall quality score for a record."""
        record = df.iloc[idx]

        # Calculate component scores
        completeness = self.score_completeness(record)
        ohlc_logic = self.score_ohlc_logic(record)
        volume = self.score_volume(record)

        # Calculate price change for outlier scoring
        if idx > 0:
            prev_close = df.iloc[idx - 1].get('close')
            curr_close = record.get('close')
            if not pd.isna(prev_close) and not pd.isna(curr_close):
                pct_change = (curr_close - prev_close) / prev_close
                outliers = self.score_outliers(pct_change)
            else:
                outliers = 0.5
        else:
            outliers = 1.0

        consistency = self.score_consistency(df, idx)

        # Weighted average
        quality_score = (
            self.weights['completeness'] * completeness +
            self.weights['ohlc_logic'] * ohlc_logic +
            self.weights['volume'] * volume +
            self.weights['outliers'] * outliers +
            self.weights['consistency'] * consistency
        )

        return max(0.0, min(1.0, quality_score))


class CleaningEngine:
    """
    Comprehensive data cleaning engine.

    Handles:
    - Missing data filling
    - Outlier normalization
    - Quality scoring
    - Data validation
    """

    def __init__(self,
                 missing_strategy: MissingDataStrategy = MissingDataStrategy.FORWARD_FILL,
                 outlier_strategy: OutlierNormalizationStrategy = OutlierNormalizationStrategy.FLAG,
                 outlier_threshold_pct: float = 0.20):
        """
        Initialize cleaning engine.

        Args:
            missing_strategy: How to handle missing data
            outlier_strategy: How to handle outliers
            outlier_threshold_pct: Threshold for outlier detection (default: 20%)
        """
        self.missing_strategy = missing_strategy
        self.outlier_strategy = outlier_strategy
        self.outlier_threshold_pct = outlier_threshold_pct
        self.quality_scorer = QualityScorer()
        self.validator = DataValidator()

    def handle_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing data according to strategy.

        Args:
            df: DataFrame with potential missing values

        Returns:
            DataFrame with missing data handled
        """
        df = df.copy()

        if self.missing_strategy == MissingDataStrategy.FORWARD_FILL:
            # Forward fill (use previous value)
            df = df.fillna(method='ffill')
            # Backward fill for first values
            df = df.fillna(method='bfill')

        elif self.missing_strategy == MissingDataStrategy.BACKWARD_FILL:
            # Backward fill (use next value)
            df = df.fillna(method='bfill')
            # Forward fill for last values
            df = df.fillna(method='ffill')

        elif self.missing_strategy == MissingDataStrategy.INTERPOLATE:
            # Linear interpolation
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                df[col] = df[col].interpolate(method='linear')
            # Fill remaining with forward/backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')

        elif self.missing_strategy == MissingDataStrategy.DROP:
            # Remove rows with any missing values
            df = df.dropna()

        return df

    def normalize_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Normalize outliers according to strategy.

        Args:
            df: DataFrame with potential outliers

        Returns:
            (cleaned_df, is_outlier_series)
        """
        df = df.copy()
        is_outlier = pd.Series(False, index=df.index)

        # Detect outliers (percentage change > threshold)
        pct_change = df['close'].pct_change().abs()
        is_outlier = pct_change > self.outlier_threshold_pct

        if self.outlier_strategy == OutlierNormalizationStrategy.CLIP:
            # Clip prices to moving average bounds
            ma_20 = df['close'].rolling(window=20, min_periods=1).mean()
            std_20 = df['close'].rolling(window=20, min_periods=1).std()

            for idx in df[is_outlier].index:
                if idx in ma_20.index:
                    ma = ma_20[idx]
                    std = std_20[idx] if not pd.isna(std_20[idx]) else 0
                    # Clip to 2 standard deviations
                    df.loc[idx, 'close'] = np.clip(
                        df.loc[idx, 'close'],
                        ma - 2 * std,
                        ma + 2 * std
                    )

        elif self.outlier_strategy == OutlierNormalizationStrategy.SMOOTH:
            # Apply moving average smoothing
            outlier_mask = is_outlier
            outlier_positions = df[outlier_mask].index

            for date_idx in outlier_positions:
                # Get position in dataframe
                pos = df.index.get_loc(date_idx)
                if pos > 0 and pos < len(df) - 1:
                    # Smooth with neighbors
                    prev_close = df.iloc[pos - 1]['close']
                    curr_close = df.iloc[pos]['close']
                    next_close = df.iloc[pos + 1]['close']

                    df.loc[date_idx, 'close'] = (prev_close + curr_close + next_close) / 3

        elif self.outlier_strategy == OutlierNormalizationStrategy.FLAG:
            # Just flag outliers, don't modify data
            pass

        elif self.outlier_strategy == OutlierNormalizationStrategy.REMOVE:
            # Remove outlier rows
            df = df[~is_outlier]

        return df, is_outlier

    def calculate_quality_scores(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate quality scores for all records.

        Args:
            df: Input DataFrame

        Returns:
            Series of quality scores (0-1)
        """
        quality_scores = pd.Series(index=df.index, dtype=float)

        for idx in range(len(df)):
            quality_scores.iloc[idx] = self.quality_scorer.calculate_quality_score(df, idx)

        return quality_scores

    def clean_data(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Perform complete data cleaning.

        Args:
            df: Raw input DataFrame
            symbol: Asset symbol for reporting

        Returns:
            (cleaned_df, cleaning_report)
        """
        original_count = len(df)
        cleaning_report = {
            'symbol': symbol,
            'original_records': original_count,
            'steps': []
        }

        # Step 1: Handle missing data
        df_cleaned = self.handle_missing_data(df)
        missing_step = {
            'step': 'missing_data_handling',
            'strategy': self.missing_strategy.value,
            'records_after': len(df_cleaned),
            'records_dropped': original_count - len(df_cleaned)
        }
        cleaning_report['steps'].append(missing_step)

        # Step 2: Normalize outliers
        df_cleaned, is_outlier = self.normalize_outliers(df_cleaned)
        outlier_step = {
            'step': 'outlier_normalization',
            'strategy': self.outlier_strategy.value,
            'outliers_detected': is_outlier.sum(),
            'records_after': len(df_cleaned)
        }
        cleaning_report['steps'].append(outlier_step)

        # Step 3: Calculate quality scores
        quality_scores = self.calculate_quality_scores(df_cleaned)
        df_cleaned['quality_score'] = quality_scores
        df_cleaned['is_outlier'] = is_outlier

        quality_step = {
            'step': 'quality_scoring',
            'mean_quality': float(quality_scores.mean()),
            'min_quality': float(quality_scores.min()),
            'max_quality': float(quality_scores.max()),
            'high_quality_records': int((quality_scores >= 0.8).sum())
        }
        cleaning_report['steps'].append(quality_step)

        # Final report
        cleaning_report['final_records'] = len(df_cleaned)
        cleaning_report['records_removed'] = original_count - len(df_cleaned)
        cleaning_report['mean_quality_score'] = float(quality_scores.mean())

        return df_cleaned, cleaning_report

    def enhance_with_indicators(self, df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        """
        Enhance cleaned data with technical indicators.

        Args:
            df: Cleaned DataFrame
            indicators: List of indicators to add ('sma', 'ema', 'rsi', 'bb')

        Returns:
            DataFrame with indicator columns added
        """
        df = df.copy()

        for indicator in indicators:
            if indicator == 'sma':
                # Simple Moving Average (20-day)
                df['sma_20'] = df['close'].rolling(window=20).mean()

            elif indicator == 'ema':
                # Exponential Moving Average (12-day)
                df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()

            elif indicator == 'rsi':
                # Relative Strength Index (14-day)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi_14'] = 100 - (100 / (1 + rs))

            elif indicator == 'bb':
                # Bollinger Bands (20-day, 2 std)
                sma = df['close'].rolling(window=20).mean()
                std = df['close'].rolling(window=20).std()
                df['bb_upper'] = sma + (std * 2)
                df['bb_lower'] = sma - (std * 2)

        return df


class PipelineCleaner:
    """Orchestrates complete cleaning pipeline."""

    def __init__(self):
        """Initialize pipeline cleaner."""
        self.cleaning_engine = CleaningEngine()
        self.validator = DataValidator()

    def execute_cleaning_pipeline(self,
                                 raw_df: pd.DataFrame,
                                 symbol: str,
                                 enhance_indicators: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute complete cleaning and validation pipeline.

        Args:
            raw_df: Raw input data
            symbol: Asset symbol
            enhance_indicators: Whether to add technical indicators

        Returns:
            (cleaned_df, pipeline_report)
        """
        pipeline_report = {
            'symbol': symbol,
            'stages': {}
        }

        # Stage 1: Initial validation
        validation_result = self.validator.validate_batch(raw_df, symbol)
        pipeline_report['stages']['validation'] = {
            'is_valid': validation_result.is_valid,
            'errors': len(validation_result.errors),
            'warnings': len(validation_result.warnings),
            'valid_records': validation_result.valid_count
        }

        # Stage 2: Data cleaning
        cleaned_df, cleaning_report = self.cleaning_engine.clean_data(raw_df, symbol)
        pipeline_report['stages']['cleaning'] = cleaning_report

        # Stage 3: Post-cleaning validation
        post_validation = self.validator.validate_batch(cleaned_df, symbol)
        pipeline_report['stages']['post_validation'] = {
            'is_valid': post_validation.is_valid,
            'errors': len(post_validation.errors),
            'warnings': len(post_validation.warnings)
        }

        # Stage 4: Quality enhancement
        if enhance_indicators:
            cleaned_df = self.cleaning_engine.enhance_with_indicators(
                cleaned_df,
                ['sma', 'ema', 'rsi', 'bb']
            )
            pipeline_report['stages']['enhancement'] = {
                'indicators_added': ['sma_20', 'ema_12', 'rsi_14', 'bb_upper', 'bb_lower']
            }

        pipeline_report['final_status'] = 'success' if post_validation.is_valid else 'success_with_warnings'
        pipeline_report['output_records'] = len(cleaned_df)

        return cleaned_df, pipeline_report
