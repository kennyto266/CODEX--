"""
Data validator module for RSI Backtest Optimizer.

Validates OHLCV data integrity: schema, chronology, OHLC relationships, missing dates.
"""

import logging
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger("rsi_backtest.data.validator")


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that DataFrame has required columns with correct types.

    Args:
        df: DataFrame to validate

    Raises:
        ValidationError: If schema validation fails
    """
    required_columns = {'date', 'open', 'high', 'low', 'close', 'volume'}

    if not all(col in df.columns for col in required_columns):
        missing = required_columns - set(df.columns)
        raise ValidationError(f"Missing required columns: {missing}")

    # Check date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        raise ValidationError("Column 'date' must be datetime type")

    # Check numeric columns
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValidationError(f"Column '{col}' must be numeric type")


def validate_chronological(df: pd.DataFrame) -> None:
    """
    Validate that dates are in chronological ascending order.

    Args:
        df: DataFrame to validate

    Raises:
        ValidationError: If dates are not monotonic increasing
    """
    if not df['date'].is_monotonic_increasing:
        raise ValidationError("Dates must be in chronological ascending order")

    # Check for duplicate dates
    duplicates = df['date'].duplicated().sum()
    if duplicates > 0:
        raise ValidationError(f"Found {duplicates} duplicate dates")


def validate_ohlc_relationships(df: pd.DataFrame) -> None:
    """
    Validate OHLC price relationships (high >= others, low <= others, etc.).

    Args:
        df: DataFrame to validate

    Raises:
        ValidationError: If OHLC relationships are violated
    """
    # High must be >= all other prices
    high_violations = (
        (df['high'] < df['open']) |
        (df['high'] < df['close']) |
        (df['high'] < df['low'])
    ).sum()

    if high_violations > 0:
        raise ValidationError(
            f"High price violation: {high_violations} rows where high < other prices"
        )

    # Low must be <= all other prices
    low_violations = (
        (df['low'] > df['open']) |
        (df['low'] > df['close']) |
        (df['low'] > df['high'])
    ).sum()

    if low_violations > 0:
        raise ValidationError(
            f"Low price violation: {low_violations} rows where low > other prices"
        )

    # No negative or zero prices
    price_cols = ['open', 'high', 'low', 'close']
    for col in price_cols:
        non_positive = (df[col] <= 0).sum()
        if non_positive > 0:
            raise ValidationError(
                f"Price validation failed: {non_positive} rows with {col} <= 0"
            )

    # Volume must be non-negative
    negative_volume = (df['volume'] < 0).sum()
    if negative_volume > 0:
        raise ValidationError(
            f"Volume validation failed: {negative_volume} rows with negative volume"
        )


def detect_missing_dates(df: pd.DataFrame) -> List[pd.Timestamp]:
    """
    Detect missing trading days (business days) in the date range.

    Args:
        df: DataFrame with date column

    Returns:
        List of missing business day dates
    """
    if len(df) == 0:
        return []

    date_range = pd.date_range(
        start=df['date'].min(),
        end=df['date'].max(),
        freq='B'  # Business days (Mon-Fri)
    )

    existing_dates = set(df['date'])
    missing_dates = [d for d in date_range if d not in existing_dates]

    if missing_dates:
        logger.warning(
            f"{len(missing_dates)} missing trading days detected "
            f"(first: {missing_dates[0].date()}, last: {missing_dates[-1].date()})"
        )

    return missing_dates


def validate_data(df: pd.DataFrame, strict: bool = True) -> Tuple[bool, List[str]]:
    """
    Perform complete data validation.

    Args:
        df: DataFrame to validate
        strict: If True, raise ValidationError on failures. If False, return warnings.

    Returns:
        Tuple of (is_valid, warnings)

    Raises:
        ValidationError: If validation fails and strict=True
    """
    warnings = []

    try:
        # Schema validation
        validate_schema(df)

        # Chronological validation
        validate_chronological(df)

        # OHLC relationships
        validate_ohlc_relationships(df)

        # Missing dates (warning only, not fatal)
        missing_dates = detect_missing_dates(df)
        if missing_dates:
            warnings.append(
                f"{len(missing_dates)} missing trading days detected"
            )

        # Check for NaN values
        nan_counts = df[['open', 'high', 'low', 'close', 'volume']].isnull().sum()
        if nan_counts.sum() > 0:
            warnings.append(f"NaN values detected: {nan_counts.to_dict()}")

        logger.info("Data validation passed")
        return True, warnings

    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        if strict:
            raise
        return False, [str(e)]
