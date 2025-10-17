"""
Unit tests for RSI calculation module.
"""

import pytest
import pandas as pd
import numpy as np

from src.indicators.rsi import (
    calculate_rsi,
    calculate_rsi_fallback,
    precompute_rsi_series,
    TALIB_AVAILABLE
)


@pytest.fixture
def sample_prices():
    """Create sample price series for testing."""
    # Create a simple price series with known pattern
    prices = pd.Series([
        100, 102, 101, 103, 105,  # Mostly gains
        104, 102, 101, 99, 98,    # Mostly losses
        100, 102, 104, 106, 108   # Strong gains
    ])
    return prices


@pytest.mark.unit
def test_calculate_rsi_fallback_basic(sample_prices):
    """Test basic RSI calculation with fallback method."""
    rsi = calculate_rsi_fallback(sample_prices, window=14)

    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(sample_prices)

    # RSI values should be between 0 and 100
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()


@pytest.mark.unit
def test_calculate_rsi_boundary_values():
    """Test RSI with known boundary conditions."""
    # All increasing prices → RSI should approach 100
    increasing_prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
    rsi = calculate_rsi_fallback(increasing_prices, window=5)

    # Last RSI value should be very high (close to 100)
    assert rsi.iloc[-1] > 80

    # All decreasing prices → RSI should approach 0
    decreasing_prices = pd.Series([109, 108, 107, 106, 105, 104, 103, 102, 101, 100])
    rsi = calculate_rsi_fallback(decreasing_prices, window=5)

    # Last RSI value should be very low (close to 0)
    assert rsi.iloc[-1] < 20


@pytest.mark.unit
def test_calculate_rsi_window_validation():
    """Test RSI window parameter validation."""
    prices = pd.Series([100, 101, 102, 103, 104])

    # Window too small
    with pytest.raises(ValueError, match="window must be between"):
        calculate_rsi(prices, window=0)

    # Window too large
    with pytest.raises(ValueError, match="window must be between"):
        calculate_rsi(prices, window=501)


@pytest.mark.unit
def test_calculate_rsi_insufficient_data(sample_prices):
    """Test RSI with insufficient data."""
    # Should still work but emit warning
    short_prices = sample_prices[:5]
    rsi = calculate_rsi(short_prices, window=14, use_talib=False)

    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(short_prices)


@pytest.mark.unit
def test_calculate_rsi_numpy_array():
    """Test that RSI works with numpy arrays."""
    prices = np.array([100, 101, 102, 103, 104, 105])
    rsi = calculate_rsi(prices, window=3, use_talib=False)

    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(prices)


@pytest.mark.unit
def test_calculate_rsi_invalid_input():
    """Test RSI with invalid input type."""
    with pytest.raises(TypeError):
        calculate_rsi([100, 101, 102], window=3)  # List not allowed


@pytest.mark.unit
@pytest.mark.skipif(not TALIB_AVAILABLE, reason="TA-Lib not installed")
def test_calculate_rsi_talib_vs_fallback(sample_prices):
    """Test that TA-Lib and fallback methods produce similar results."""
    window = 14

    rsi_talib = calculate_rsi(sample_prices, window=window, use_talib=True)
    rsi_fallback = calculate_rsi(sample_prices, window=window, use_talib=False)

    # Drop NaN values for comparison
    valid_indices = ~(rsi_talib.isna() | rsi_fallback.isna())

    if valid_indices.sum() > 0:
        # Results should be very similar (within 1 point due to rounding)
        diff = np.abs(rsi_talib[valid_indices] - rsi_fallback[valid_indices])
        assert (diff < 1.0).all(), "TA-Lib and fallback RSI differ significantly"


@pytest.mark.unit
def test_precompute_rsi_series(sample_prices):
    """Test pre-computation of multiple RSI series."""
    windows = range(5, 11)  # Windows 5-10

    rsi_cache = precompute_rsi_series(sample_prices, windows)

    assert isinstance(rsi_cache, dict)
    assert len(rsi_cache) == 6  # 6 windows

    for window in windows:
        assert window in rsi_cache
        assert isinstance(rsi_cache[window], pd.Series)
        assert len(rsi_cache[window]) == len(sample_prices)


@pytest.mark.unit
def test_rsi_series_naming(sample_prices):
    """Test that RSI series are properly named."""
    window = 14
    rsi = calculate_rsi_fallback(sample_prices, window=window)

    assert rsi.name == f'RSI_{window}'


@pytest.mark.unit
def test_rsi_edge_case_flat_prices():
    """Test RSI with flat (unchanged) prices."""
    flat_prices = pd.Series([100] * 20)
    rsi = calculate_rsi_fallback(flat_prices, window=14)

    # With no price changes, RSI should be undefined (NaN) or 50
    # After exponential smoothing converges, it becomes NaN/50
    valid_rsi = rsi.dropna()
    if len(valid_rsi) > 0:
        # If there are valid values, they should be near 50 or NaN is acceptable
        assert (valid_rsi >= 40).all() and (valid_rsi <= 60).all()


@pytest.mark.unit
def test_rsi_window_1():
    """Test RSI with window=1 (edge case)."""
    prices = pd.Series([100, 102, 101, 103, 99])
    rsi = calculate_rsi_fallback(prices, window=1)

    # Window=1 should give extreme values (0 or 100)
    valid_rsi = rsi.dropna()
    if len(valid_rsi) > 0:
        # With window=1, RSI is either 0 (loss) or 100 (gain)
        assert ((valid_rsi <= 1) | (valid_rsi >= 99)).all()
