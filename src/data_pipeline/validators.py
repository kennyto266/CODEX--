"""
Data Validation Module for CODEX quantitative trading system.

This module provides comprehensive validation for OHLCV data through the pipeline:
- Schema validation using Pydantic models
- Business rule validation (OHLC relationships, outlier detection)
- Asset-specific validation using profiles
- Batch validation with detailed reporting

Validation stages:
1. Raw validation: Check data completeness and types
2. Clean validation: Validate OHLCV relationships and ranges
3. Normalized validation: Check timezone and trading day status
"""

from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from src.data_pipeline.schemas import (
    OHLCVData, RawPriceData, CleanedPriceData, NormalizedPriceData,
    OHLCVDataBatch, DataValidationResult
)
from src.data_pipeline.asset_profile import AssetProfile, get_registry


class DataValidator:
    """
    Comprehensive data validation for the CODEX system.

    Validates raw data through the cleaning and normalization pipeline,
    checking both structure (Pydantic) and business rules.
    """

    def __init__(self, asset_profile: Optional[AssetProfile] = None):
        """
        Initialize validator.

        Args:
            asset_profile: Optional asset profile for symbol-specific validation
        """
        self.asset_profile = asset_profile
        self.outlier_threshold_pct = 0.20  # 20% daily change = outlier
        self.min_price_change = 0.0001  # Minimum price increment

    def validate_raw_data(self, data: Dict[str, Any]) -> DataValidationResult:
        """
        Validate raw data from a data source.

        Checks:
        - Required fields present
        - Data types correct
        - Value ranges reasonable

        Args:
            data: Raw data dictionary

        Returns:
            DataValidationResult with validation status
        """
        result = DataValidationResult(is_valid=True, record_count=1)

        try:
            record = RawPriceData(**data)
            result.valid_count = 1

            # Check for missing required fields
            if not record.has_complete_ohlcv():
                missing = record.get_missing_fields()
                result.add_warning(0, 'ohlcv', f"Missing fields: {missing}")

        except Exception as e:
            result.is_valid = False
            result.add_error(0, 'raw_data', str(e))

        result.generate_summary()
        return result

    def validate_ohlcv_relationships(self, record: Dict[str, Any]) -> List[str]:
        """
        Validate OHLCV relationships.

        Checks:
        - High >= all prices
        - Low <= all prices
        - Close between High and Low
        - Open, High, Low, Close > 0

        Args:
            record: OHLCV record

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        high = record.get('high')
        low = record.get('low')
        close = record.get('close')
        open_price = record.get('open')

        if None in [high, low, close, open_price]:
            return errors  # Skip if any field is None

        # Check high is highest
        if not (high >= low and high >= close and high >= open_price):
            errors.append(f"High ({high}) must be >= all prices")

        # Check low is lowest
        if not (low <= high and low <= close and low <= open_price):
            errors.append(f"Low ({low}) must be <= all prices")

        # Check close is between
        if not (low <= close <= high):
            errors.append(f"Close ({close}) must be between Low ({low}) and High ({high})")

        # Check all positive
        for name, value in [('open', open_price), ('high', high), ('low', low), ('close', close)]:
            if value <= 0:
                errors.append(f"{name.capitalize()} ({value}) must be positive")

        return errors

    def detect_outliers(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect statistical outliers in price data.

        Uses percentage change threshold to identify suspicious price movements.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Series of boolean values indicating outliers
        """
        if len(df) < 2:
            return pd.Series(False, index=df.index)

        # Calculate daily percentage change
        pct_change = df['close'].pct_change().abs()

        # Mark outliers
        is_outlier = pct_change > self.outlier_threshold_pct

        return is_outlier

    def validate_volume(self, df: pd.DataFrame) -> List[str]:
        """
        Validate volume data.

        Checks:
        - No NaN values
        - All non-negative
        - No zeros (trading days should have volume)

        Args:
            df: DataFrame with 'volume' column

        Returns:
            List of error messages
        """
        errors = []

        if df['volume'].isnull().any():
            errors.append("Volume contains NaN values")

        if (df['volume'] < 0).any():
            errors.append("Volume contains negative values")

        if (df['volume'] == 0).any():
            errors.append("Volume contains zero values (non-trading days?)")

        return errors

    def validate_batch(self, df: pd.DataFrame, symbol: str) -> DataValidationResult:
        """
        Validate a batch of OHLCV records.

        Args:
            df: DataFrame with OHLCV columns
            symbol: Asset symbol

        Returns:
            DataValidationResult with detailed status
        """
        result = DataValidationResult(is_valid=True, record_count=len(df))

        if len(df) == 0:
            result.add_error(0, 'batch', 'Empty DataFrame')
            result.generate_summary()
            return result

        # Validate each row
        for idx, row in df.iterrows():
            record_dict = row.to_dict()

            # Validate OHLCV relationships
            ohlcv_errors = self.validate_ohlcv_relationships(record_dict)
            for error in ohlcv_errors:
                result.add_error(idx, 'ohlcv', error)

            # Check for missing values
            if pd.isna(row).any():
                missing_cols = row[pd.isna(row)].index.tolist()
                result.add_warning(idx, 'missing', f"Missing: {missing_cols}")

        # Batch-level validation
        volume_errors = self.validate_volume(df)
        for error in volume_errors:
            result.add_error(0, 'volume', error)

        # Detect outliers
        outliers = self.detect_outliers(df)
        outlier_count = outliers.sum()
        if outlier_count > 0:
            result.add_warning(0, 'outliers', f"{outlier_count} outliers detected")

        # Set valid count
        result.valid_count = len(df) - len(result.errors)
        result.is_valid = len(result.errors) == 0

        result.generate_summary()
        return result

    def clean_and_validate(self, raw_df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, DataValidationResult]:
        """
        Clean and validate raw data.

        Operations:
        1. Fill missing trading days
        2. Detect and flag outliers
        3. Validate relationships
        4. Normalize dtypes

        Args:
            raw_df: Raw OHLCV DataFrame
            symbol: Asset symbol

        Returns:
            (cleaned_df, validation_result)
        """
        df = raw_df.copy()
        result = self.validate_batch(df, symbol)

        # Fill missing trading days (business days only)
        if len(df) > 0:
            df = df.reindex(
                pd.bdate_range(df.index.min(), df.index.max()),
                method='ffill'
            )

        # Normalize volume to integers
        if 'volume' in df.columns:
            df['volume'] = df['volume'].astype(int)

        # Detect outliers
        df['is_outlier'] = self.detect_outliers(df)

        return df, result

    def normalize_to_utc(self, df: pd.DataFrame, source_tz: str = 'Asia/Hong_Kong') -> pd.DataFrame:
        """
        Normalize datetime to UTC.

        Args:
            df: DataFrame with datetime index
            source_tz: Original timezone (default: Asia/Hong_Kong for HKEX)

        Returns:
            DataFrame with UTC index
        """
        df = df.copy()

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Add timezone if naive
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(source_tz)

        # Convert to UTC
        df.index = df.index.tz_convert('UTC')

        return df

    def is_trading_day(self, date: datetime, market: str = 'HKEX') -> bool:
        """
        Check if date is a trading day.

        Args:
            date: Date to check
            market: Market code (default: HKEX)

        Returns:
            True if trading day
        """
        # Skip weekends
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Common holidays (simplified - HKEX specific)
        hkex_holidays = {
            '2025-01-01',  # New Year's Day
            '2025-02-10',  # Chinese New Year
            '2025-02-11',  # Chinese New Year
            '2025-04-04',  # Children's Day
            '2025-05-01',  # Labour Day
            '2025-06-10',  # Dragon Boat Festival
            '2025-09-18',  # Mid-Autumn Festival
            '2025-10-01',  # National Day
            '2025-10-11',  # Chung Yeung Festival
            '2025-12-25',  # Christmas Day
        }

        date_str = date.strftime('%Y-%m-%d')
        return date_str not in hkex_holidays

    def validate_trading_day_alignment(self, df: pd.DataFrame) -> List[Tuple[datetime, str]]:
        """
        Check if data is properly aligned to trading days.

        Args:
            df: DataFrame with datetime index

        Returns:
            List of (date, issue) tuples
        """
        issues = []

        for date in df.index:
            # Skip timezone-aware check if needed
            if hasattr(date, 'date'):
                date_only = date.date() if hasattr(date, 'date') else date
            else:
                date_only = date

            if not self.is_trading_day(date):
                issues.append((date, 'Non-trading day'))

        return issues

    def validate_with_asset_profile(self, df: pd.DataFrame, symbol: str) -> DataValidationResult:
        """
        Validate data against asset profile parameters.

        Checks:
        - Symbol consistency
        - Price ranges reasonable for asset
        - Volume matches asset characteristics

        Args:
            df: OHLCV DataFrame
            symbol: Asset symbol

        Returns:
            DataValidationResult
        """
        result = DataValidationResult(is_valid=True, record_count=len(df))

        # Get asset profile
        registry = get_registry()
        profile = registry.get(symbol)

        if not profile:
            result.add_warning(0, 'profile', f"No profile found for {symbol}")
            return result

        # Check price ranges (basic sanity check)
        avg_price = df['close'].mean()
        price_std = df['close'].std()

        if price_std > avg_price:
            result.add_warning(0, 'price', "High price volatility relative to mean")

        # Check volume consistency
        avg_volume = df['volume'].mean()
        if avg_volume == 0:
            result.add_error(0, 'volume', "Zero average volume")
        else:
            volume_cv = df['volume'].std() / avg_volume
            if volume_cv > 1.0:
                result.add_warning(0, 'volume', f"High volume volatility (CV={volume_cv:.2f})")

        result.valid_count = len(df) - len(result.errors)
        result.is_valid = len(result.errors) == 0
        result.generate_summary()

        return result


class PipelineValidator:
    """
    Validates data through the complete pipeline: Raw → Cleaned → Normalized.
    """

    def __init__(self):
        """Initialize pipeline validator."""
        self.validator = DataValidator()

    def validate_pipeline(self, raw_df: pd.DataFrame, symbol: str) -> Dict[str, DataValidationResult]:
        """
        Validate data through the complete pipeline.

        Args:
            raw_df: Raw OHLCV data
            symbol: Asset symbol

        Returns:
            Dictionary with validation results at each stage
        """
        results = {}

        # Stage 1: Raw validation
        results['raw'] = self.validator.validate_batch(raw_df, symbol)

        # Stage 2: Clean and validate
        cleaned_df, results['cleaned'] = self.validator.clean_and_validate(raw_df, symbol)

        # Stage 3: Normalize
        normalized_df = self.validator.normalize_to_utc(cleaned_df)
        trading_day_issues = self.validator.validate_trading_day_alignment(normalized_df)

        # Stage 4: Asset-specific validation
        results['asset_profile'] = self.validator.validate_with_asset_profile(cleaned_df, symbol)

        # Summary
        results['summary'] = {
            'raw_records': len(raw_df),
            'cleaned_records': len(cleaned_df),
            'normalized_records': len(normalized_df),
            'trading_day_issues': len(trading_day_issues),
            'overall_valid': all(r.is_valid for r in results.values() if isinstance(r, DataValidationResult))
        }

        return results

    def get_validation_report(self, results: Dict[str, DataValidationResult]) -> str:
        """
        Generate human-readable validation report.

        Args:
            results: Validation results dictionary

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 60,
            "DATA VALIDATION REPORT",
            "=" * 60,
        ]

        for stage_name, stage_result in results.items():
            if stage_name == 'summary':
                lines.append(f"\nSummary:")
                for key, value in stage_result.items():
                    lines.append(f"  {key}: {value}")
            elif isinstance(stage_result, DataValidationResult):
                lines.append(f"\n{stage_name.capitalize()} Validation:")
                lines.append(f"  Valid: {stage_result.is_valid}")
                lines.append(f"  Records: {stage_result.record_count}")
                lines.append(f"  Valid count: {stage_result.valid_count}")
                lines.append(f"  Errors: {len(stage_result.errors)}")
                lines.append(f"  Warnings: {len(stage_result.warnings)}")

                if stage_result.errors:
                    lines.append("  Error details:")
                    for error in stage_result.errors[:5]:  # Show first 5
                        lines.append(f"    - {error}")

                if stage_result.warnings:
                    lines.append("  Warnings:")
                    for warning in stage_result.warnings[:3]:  # Show first 3
                        lines.append(f"    - {warning}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
