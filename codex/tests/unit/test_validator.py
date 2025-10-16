"""
Unit tests for data validator module.
"""

import pytest
import pandas as pd
import numpy as np
from src.data.validator import validate_data, get_data_summary


@pytest.mark.unit
class TestDataValidator:
    """Test suite for data validation."""

    def test_valid_data_passes(self):
        """Test that valid data passes all checks."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05']),
            'open': [320.0, 324.8, 327.0],
            'high': [325.6, 328.0, 330.2],
            'low': [318.4, 322.6, 325.8],
            'close': [324.2, 327.4, 329.6],
            'volume': [15234000, 18921000, 21045000]
        })

        is_valid, messages = validate_data(df, strict=True)

        assert is_valid
        # May have warnings about missing trading days, but no errors

    def test_missing_columns_fails(self):
        """Test that missing required columns cause validation failure."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [325.6],
            'low': [318.4],
            # Missing 'close' column
            'volume': [15234000]
        })

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_data(df, strict=True)

    def test_non_chronological_dates_fails(self):
        """Test that non-chronological dates fail validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-05', '2023-01-03', '2023-01-04']),  # Out of order
            'open': [327.0, 320.0, 324.8],
            'high': [330.2, 325.6, 328.0],
            'low': [325.8, 318.4, 322.6],
            'close': [329.6, 324.2, 327.4],
            'volume': [21045000, 15234000, 18921000]
        })

        with pytest.raises(ValueError, match="not in chronological ascending order"):
            validate_data(df, strict=True)

    def test_duplicate_dates_fails(self):
        """Test that duplicate dates fail validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03', '2023-01-03', '2023-01-04']),  # Duplicate
            'open': [320.0, 320.5, 324.8],
            'high': [325.6, 326.0, 328.0],
            'low': [318.4, 319.0, 322.6],
            'close': [324.2, 324.5, 327.4],
            'volume': [15234000, 15000000, 18921000]
        })

        with pytest.raises(ValueError, match="duplicate dates"):
            validate_data(df, strict=True)

    def test_ohlc_violation_high_too_low(self):
        """Test that OHLC violation (high < close) fails validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [323.0],  # High is less than close
            'low': [318.4],
            'close': [325.0],  # Close is higher than high (invalid!)
            'volume': [15234000]
        })

        with pytest.raises(ValueError, match="OHLC violation.*high"):
            validate_data(df, strict=True)

    def test_ohlc_violation_low_too_high(self):
        """Test that OHLC violation (low > close) fails validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [325.6],
            'low': [323.0],  # Low is higher than open (invalid!)
            'close': [324.2],
            'volume': [15234000]
        })

        with pytest.raises(ValueError, match="OHLC violation.*low"):
            validate_data(df, strict=True)

    def test_negative_prices_fail(self):
        """Test that negative prices fail validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [325.6],
            'low': [-318.4],  # Negative price
            'close': [324.2],
            'volume': [15234000]
        })

        with pytest.raises(ValueError, match="Invalid.*prices"):
            validate_data(df, strict=True)

    def test_zero_prices_fail(self):
        """Test that zero prices fail validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [325.6],
            'low': [318.4],
            'close': [0.0],  # Zero price
            'volume': [15234000]
        })

        with pytest.raises(ValueError, match="Invalid close prices"):
            validate_data(df, strict=True)

    def test_negative_volume_fails(self):
        """Test that negative volume fails validation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03']),
            'open': [320.0],
            'high': [325.6],
            'low': [318.4],
            'close': [324.2],
            'volume': [-15234000]  # Negative volume
        })

        with pytest.raises(ValueError, match="Invalid volume"):
            validate_data(df, strict=True)

    def test_missing_trading_days_warning(self):
        """Test that missing trading days generate warnings (not errors)."""
        # Skip 2023-01-04 (a weekday)
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03', '2023-01-05', '2023-01-06']),
            'open': [320.0, 327.0, 330.0],
            'high': [325.6, 330.2, 333.0],
            'low': [318.4, 325.8, 328.0],
            'close': [324.2, 329.6, 331.5],
            'volume': [15234000, 21045000, 19000000]
        })

        is_valid, messages = validate_data(df, strict=False)

        # Should still be valid (warnings only)
        assert is_valid
        # Check that there's a message about missing trading days
        assert any('missing trading days' in msg.lower() for msg in messages)

    def test_get_data_summary(self):
        """Test data summary generation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05']),
            'open': [320.0, 324.8, 327.0],
            'high': [325.6, 328.0, 330.2],
            'low': [318.4, 322.6, 325.8],
            'close': [324.2, 327.4, 329.6],
            'volume': [15234000, 18921000, 21045000]
        })

        summary = get_data_summary(df)

        assert summary['num_days'] == 3
        assert summary['start_date'] == pd.to_datetime('2023-01-03')
        assert summary['end_date'] == pd.to_datetime('2023-01-05')
        assert summary['price_range']['min'] == 318.4
        assert summary['price_range']['max'] == 330.2
        assert summary['avg_volume'] == pytest.approx(18400000, rel=1e-2)
