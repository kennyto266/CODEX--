"""
Unit tests for data validator module.
"""

import pytest
import pandas as pd
import numpy as np

from src.data.validator import (
    validate_schema,
    validate_chronological,
    validate_ohlc_relationships,
    detect_missing_dates,
    validate_data,
    ValidationError
)


@pytest.fixture
def valid_dataframe():
    """Create a valid OHLCV DataFrame."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05']),
        'open': [320.0, 324.8, 327.0],
        'high': [325.6, 328.0, 330.2],
        'low': [318.4, 322.6, 325.8],
        'close': [324.2, 327.4, 329.6],
        'volume': [15234000, 18921000, 21045000]
    })


@pytest.mark.unit
def test_validate_schema_success(valid_dataframe):
    """Test schema validation with valid data."""
    # Should not raise any exception
    validate_schema(valid_dataframe)


@pytest.mark.unit
def test_validate_schema_missing_columns():
    """Test schema validation with missing columns."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03']),
        'open': [320.0],
        'high': [325.6]
    })

    with pytest.raises(ValidationError, match="Missing required columns"):
        validate_schema(df)


@pytest.mark.unit
def test_validate_schema_wrong_date_type():
    """Test schema validation with non-datetime date column."""
    df = pd.DataFrame({
        'date': ['2023-01-03', '2023-01-04'],
        'open': [320.0, 324.8],
        'high': [325.6, 328.0],
        'low': [318.4, 322.6],
        'close': [324.2, 327.4],
        'volume': [15234000, 18921000]
    })

    with pytest.raises(ValidationError, match="date.*datetime"):
        validate_schema(df)


@pytest.mark.unit
def test_validate_chronological_success(valid_dataframe):
    """Test chronological validation with properly ordered dates."""
    validate_chronological(valid_dataframe)


@pytest.mark.unit
def test_validate_chronological_out_of_order():
    """Test chronological validation with out-of-order dates."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-05', '2023-01-03', '2023-01-04']),
        'open': [327.0, 320.0, 324.8],
        'high': [330.2, 325.6, 328.0],
        'low': [325.8, 318.4, 322.6],
        'close': [329.6, 324.2, 327.4],
        'volume': [21045000, 15234000, 18921000]
    })

    with pytest.raises(ValidationError, match="chronological"):
        validate_chronological(df)


@pytest.mark.unit
def test_validate_chronological_duplicates():
    """Test chronological validation with duplicate dates."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03', '2023-01-03', '2023-01-04']),
        'open': [320.0, 320.0, 324.8],
        'high': [325.6, 325.6, 328.0],
        'low': [318.4, 318.4, 322.6],
        'close': [324.2, 324.2, 327.4],
        'volume': [15234000, 15234000, 18921000]
    })

    with pytest.raises(ValidationError, match="duplicate"):
        validate_chronological(df)


@pytest.mark.unit
def test_validate_ohlc_relationships_success(valid_dataframe):
    """Test OHLC validation with valid relationships."""
    validate_ohlc_relationships(valid_dataframe)


@pytest.mark.unit
def test_validate_ohlc_high_violation():
    """Test OHLC validation when high < other prices."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03']),
        'open': [320.0],
        'high': [315.0],  # High is lower than open!
        'low': [310.0],
        'close': [318.0],
        'volume': [15234000]
    })

    with pytest.raises(ValidationError, match="High price violation"):
        validate_ohlc_relationships(df)


@pytest.mark.unit
def test_validate_ohlc_low_violation():
    """Test OHLC validation when low > other prices."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03']),
        'open': [320.0],
        'high': [325.0],
        'low': [322.0],  # Low is higher than open!
        'close': [318.0],
        'volume': [15234000]
    })

    with pytest.raises(ValidationError, match="Low price violation"):
        validate_ohlc_relationships(df)


@pytest.mark.unit
def test_validate_ohlc_negative_price():
    """Test OHLC validation with negative prices."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03']),
        'open': [320.0],
        'high': [325.0],
        'low': [310.0],
        'close': [-318.0],  # Negative price!
        'volume': [15234000]
    })

    with pytest.raises(ValidationError, match="Price validation"):
        validate_ohlc_relationships(df)


@pytest.mark.unit
def test_validate_ohlc_negative_volume():
    """Test OHLC validation with negative volume."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03']),
        'open': [320.0],
        'high': [325.0],
        'low': [310.0],
        'close': [318.0],
        'volume': [-15234000]  # Negative volume!
    })

    with pytest.raises(ValidationError, match="Volume validation"):
        validate_ohlc_relationships(df)


@pytest.mark.unit
def test_detect_missing_dates():
    """Test missing date detection."""
    # Create data with a gap (skip 2023-01-04, which is a business day)
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03', '2023-01-05', '2023-01-06'])
    })

    missing = detect_missing_dates(df)

    # Should detect 2023-01-04 as missing
    assert len(missing) > 0
    assert pd.Timestamp('2023-01-04') in missing


@pytest.mark.unit
def test_detect_missing_dates_empty():
    """Test missing date detection with empty DataFrame."""
    df = pd.DataFrame({'date': pd.to_datetime([])})

    missing = detect_missing_dates(df)
    assert len(missing) == 0


@pytest.mark.unit
def test_validate_data_success(valid_dataframe):
    """Test complete validation with valid data."""
    is_valid, warnings = validate_data(valid_dataframe)

    assert is_valid is True
    # May have warnings about missing dates (weekends), but should be valid


@pytest.mark.unit
def test_validate_data_failure_strict():
    """Test complete validation failure in strict mode."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-05', '2023-01-03']),  # Out of order!
        'open': [327.0, 320.0],
        'high': [330.2, 325.6],
        'low': [325.8, 318.4],
        'close': [329.6, 324.2],
        'volume': [21045000, 15234000]
    })

    with pytest.raises(ValidationError):
        validate_data(df, strict=True)


@pytest.mark.unit
def test_validate_data_failure_non_strict():
    """Test complete validation failure in non-strict mode."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-05', '2023-01-03']),  # Out of order!
        'open': [327.0, 320.0],
        'high': [330.2, 325.6],
        'low': [325.8, 318.4],
        'close': [329.6, 324.2],
        'volume': [21045000, 15234000]
    })

    is_valid, warnings = validate_data(df, strict=False)

    assert is_valid is False
    assert len(warnings) > 0
