"""
Data validation module for price data quality checks.

This module validates OHLCV data for schema correctness, chronological order,
OHLC relationships, and detects missing dates.
"""

import pandas as pd
import logging
import numpy as np

logger = logging.getLogger("rsi_backtest.data.validator")


def validate_data(df: pd.DataFrame, strict: bool = True) -> tuple[bool, list[str]]:
    """
    Validate OHLCV data for quality and correctness.

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume
        strict: If True, raise exceptions on validation failures

    Returns:
        Tuple of (is_valid, list of warnings/errors)

    Raises:
        ValueError: If validation fails and strict=True
    """
    warnings = []
    errors = []

    logger.info("Validating data...")

    # 1. Schema check
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        if strict:
            raise ValueError(errors[-1])

    # 2. Check for null values
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        msg = f"Found null values: {null_counts[null_counts > 0].to_dict()}"
        errors.append(msg)
        logger.error(msg)
        if strict:
            raise ValueError(msg)

    # 3. Chronological order check
    if not df['date'].is_monotonic_increasing:
        errors.append("Dates are not in chronological ascending order")
        logger.error(errors[-1])
        if strict:
            raise ValueError(errors[-1])

    # 4. Check for duplicate dates
    duplicates = df['date'].duplicated()
    if duplicates.any():
        dup_dates = df.loc[duplicates, 'date'].tolist()
        errors.append(f"Found duplicate dates: {dup_dates}")
        logger.error(errors[-1])
        if strict:
            raise ValueError(errors[-1])

    # 5. OHLC relationship validation
    # high >= max(open, close, low)
    invalid_high = df['high'] < df[['open', 'close', 'low']].max(axis=1)
    if invalid_high.any():
        invalid_dates = df.loc[invalid_high, 'date'].tolist()
        errors.append(f"OHLC violation: high < max(open, close, low) on dates: {invalid_dates[:5]}")
        logger.error(errors[-1])
        if strict:
            raise ValueError(errors[-1])

    # low <= min(open, close, high)
    invalid_low = df['low'] > df[['open', 'close', 'high']].min(axis=1)
    if invalid_low.any():
        invalid_dates = df.loc[invalid_low, 'date'].tolist()
        errors.append(f"OHLC violation: low > min(open, close, high) on dates: {invalid_dates[:5]}")
        logger.error(errors[-1])
        if strict:
            raise ValueError(errors[-1])

    # 6. Check for negative or zero prices
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        invalid_prices = (df[col] <= 0) | (df[col].isna())
        if invalid_prices.any():
            invalid_dates = df.loc[invalid_prices, 'date'].tolist()
            errors.append(f"Invalid {col} prices (<=0 or NaN) on dates: {invalid_dates[:5]}")
            logger.error(errors[-1])
            if strict:
                raise ValueError(errors[-1])

    # 7. Check for negative volume
    invalid_volume = (df['volume'] < 0) | (df['volume'].isna())
    if invalid_volume.any():
        invalid_dates = df.loc[invalid_volume, 'date'].tolist()
        errors.append(f"Invalid volume (<0 or NaN) on dates: {invalid_dates[:5]}")
        logger.error(errors[-1])
        if strict:
            raise ValueError(errors[-1])

    # 8. Missing dates detection (warnings only)
    date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='B')  # Business days
    missing_dates = set(date_range) - set(df['date'])

    if missing_dates:
        msg = f"Detected {len(missing_dates)} missing trading days (business days calendar)"
        warnings.append(msg)
        logger.warning(msg)

        # Show first few missing dates
        sorted_missing = sorted(list(missing_dates))[:5]
        logger.warning(f"  First missing dates: {[d.date() for d in sorted_missing]}")

    # Summary
    is_valid = len(errors) == 0

    if is_valid:
        logger.info("✓ Data validation passed")
    else:
        logger.error(f"✗ Data validation failed with {len(errors)} errors")

    return is_valid, warnings + errors


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Get summary statistics for the dataset.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Dictionary with summary statistics
    """
    return {
        'num_days': len(df),
        'start_date': df['date'].min(),
        'end_date': df['date'].max(),
        'price_range': {
            'min': df['low'].min(),
            'max': df['high'].max(),
        },
        'avg_volume': df['volume'].mean(),
        'total_volume': df['volume'].sum(),
    }
