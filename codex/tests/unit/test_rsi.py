"""
Unit tests for RSI calculation module.
"""

import pytest
import pandas as pd
import numpy as np
from src.indicators.rsi import (
    calculate_rsi,
    calculate_rsi_multiple_windows,
    get_rsi_warmup_period,
    _calculate_rsi_pandas
)


@pytest.mark.unit
class TestRSICalculation:
    """Test suite for RSI calculation."""

    def test_rsi_basic_calculation(self):
        """Test basic RSI calculation with known values."""
        # Create simple price series with known pattern
        # Prices: 100, 105, 110, 105, 100, 95, 100, 105
        prices = pd.Series([100, 105, 110, 105, 100, 95, 100, 105])

        rsi = calculate_rsi(prices, window=14)

        # Check basic properties
        assert len(rsi) == len(prices)
        # RSI should be in range [0, 100]
        assert rsi.dropna().min() >= 0
        assert rsi.dropna().max() <= 100

    def test_rsi_all_gains_returns_100(self):
        """Test that RSI returns 100 when all price changes are gains."""
        # Steadily increasing prices
        prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])

        rsi = calculate_rsi(prices, window=5)

        # After warmup period, RSI should approach 100
        assert rsi.iloc[-1] > 95  # Should be very high

    def test_rsi_all_losses_returns_0(self):
        """Test that RSI returns 0 when all price changes are losses."""
        # Steadily decreasing prices
        prices = pd.Series([110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100])

        rsi = calculate_rsi(prices, window=5)

        # After warmup period, RSI should approach 0
        assert rsi.iloc[-1] < 5  # Should be very low

    def test_rsi_alternating_returns_50(self):
        """Test that RSI returns ~50 when gains and losses are balanced."""
        # Alternating up and down by same amount
        prices = pd.Series([100, 101, 100, 101, 100, 101, 100, 101, 100, 101] * 3)

        rsi = calculate_rsi(prices, window=5)

        # RSI should be around 50 (balanced gains/losses)
        rsi_mean = rsi.dropna().mean()
        assert 40 < rsi_mean < 60

    def test_rsi_invalid_window_raises_error(self):
        """Test that invalid window sizes raise ValueError."""
        prices = pd.Series([100, 101, 102, 103, 104])

        with pytest.raises(ValueError, match="window must be positive"):
            calculate_rsi(prices, window=0)

        with pytest.raises(ValueError, match="window must be positive"):
            calculate_rsi(prices, window=-5)

    def test_rsi_empty_series_raises_error(self):
        """Test that empty price series raises ValueError."""
        prices = pd.Series([])

        with pytest.raises(ValueError, match="cannot be empty"):
            calculate_rsi(prices, window=14)

    def test_rsi_insufficient_data_returns_nan(self):
        """Test that insufficient data returns NaN values."""
        prices = pd.Series([100, 101, 102])  # Only 3 values

        rsi = calculate_rsi(prices, window=14)  # Need 14+ for RSI(14)

        # All values should be NaN
        assert rsi.isna().all()

    def test_rsi_boundary_condition_30(self):
        """Test RSI values near buy threshold (30)."""
        # Create prices that should yield RSI around 30
        prices = pd.Series([100] + [99] * 10 + [100] * 5)

        rsi = calculate_rsi(prices, window=5)

        # Check that RSI can produce values near 30
        assert any((25 < val < 35) for val in rsi.dropna())

    def test_rsi_boundary_condition_70(self):
        """Test RSI values near sell threshold (70)."""
        # Create prices that should yield RSI around 70
        prices = pd.Series([100] + [101] * 10 + [100] * 5)

        rsi = calculate_rsi(prices, window=5)

        # Check that RSI can produce values near 70
        assert any((65 < val < 75) for val in rsi.dropna())

    def test_rsi_window_1(self):
        """Test RSI with window=1 (edge case)."""
        prices = pd.Series([100, 105, 103, 108, 102])

        rsi = calculate_rsi(prices, window=1)

        # Window=1 means each day's RSI depends only on that day's change
        # Up days should have RSI=100, down days RSI=0
        changes = prices.diff()
        for i in range(1, len(rsi)):
            if not pd.isna(rsi.iloc[i]):
                if changes.iloc[i] > 0:
                    assert rsi.iloc[i] > 90  # Should be high
                elif changes.iloc[i] < 0:
                    assert rsi.iloc[i] < 10  # Should be low

    def test_calculate_rsi_multiple_windows(self):
        """Test pre-computing RSI for multiple windows."""
        prices = pd.Series(range(100, 200))  # 100 prices

        rsi_cache = calculate_rsi_multiple_windows(prices, 10, 30, 5)

        # Should have windows: 10, 15, 20, 25, 30
        assert len(rsi_cache) == 5
        assert 10 in rsi_cache
        assert 15 in rsi_cache
        assert 30 in rsi_cache

        # Each RSI series should have same length as input
        for window, rsi in rsi_cache.items():
            assert len(rsi) == len(prices)

    def test_get_rsi_warmup_period(self):
        """Test warmup period calculation."""
        warmup_14 = get_rsi_warmup_period(14)
        warmup_50 = get_rsi_warmup_period(50)
        warmup_200 = get_rsi_warmup_period(200)

        # Warmup should increase with window
        assert warmup_50 > warmup_14
        assert warmup_200 > warmup_50

        # Warmup should be at least window + 100
        assert warmup_14 >= 114
        assert warmup_50 >= 150

    def test_rsi_pandas_implementation(self):
        """Test the fallback pandas RSI implementation."""
        prices = pd.Series([100, 105, 110, 108, 112, 115, 113, 118, 120, 117])

        rsi = _calculate_rsi_pandas(prices, window=5)

        # Basic sanity checks
        assert len(rsi) == len(prices)
        assert rsi.dropna().min() >= 0
        assert rsi.dropna().max() <= 100

    def test_rsi_handles_nan_input(self):
        """Test that RSI handles NaN values in input gracefully."""
        prices = pd.Series([100, 105, np.nan, 108, 110, 112, 115])

        rsi = calculate_rsi(prices, window=5)

        # Should return a series (may have NaN values)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(prices)
