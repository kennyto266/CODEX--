"""
RSI (Relative Strength Index) calculation module.

This module wraps TA-Lib's RSI function and provides utilities
for calculating RSI across multiple window sizes.
"""

import pandas as pd
import numpy as np
import logging

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logging.warning("TA-Lib not installed. RSI calculation will use fallback implementation.")

logger = logging.getLogger("rsi_backtest.indicators.rsi")


def calculate_rsi(close_prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index) for given window size.

    Uses TA-Lib implementation if available, otherwise falls back to
    pandas-based calculation using Wilder's smoothing method.

    Args:
        close_prices: Series of closing prices
        window: RSI lookback window (number of periods)

    Returns:
        Series of RSI values (0-100), with NaN for insufficient data

    Raises:
        ValueError: If window is not positive or close_prices is empty
    """
    if window <= 0:
        raise ValueError(f"RSI window must be positive, got {window}")

    if len(close_prices) == 0:
        raise ValueError("close_prices cannot be empty")

    if len(close_prices) < window + 1:
        logger.warning(f"Insufficient data for RSI({window}): need {window + 1}, got {len(close_prices)}")
        return pd.Series([np.nan] * len(close_prices), index=close_prices.index)

    # Use TA-Lib if available
    if TALIB_AVAILABLE:
        try:
            rsi_values = talib.RSI(close_prices.values, timeperiod=window)
            return pd.Series(rsi_values, index=close_prices.index)
        except Exception as e:
            logger.warning(f"TA-Lib RSI calculation failed: {e}. Using fallback.")

    # Fallback: Pandas implementation with Wilder's smoothing
    return _calculate_rsi_pandas(close_prices, window)


def _calculate_rsi_pandas(close_prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate RSI using pandas (Wilder's smoothing method).

    This is a fallback implementation when TA-Lib is not available.

    Formula:
        1. Calculate price changes (delta)
        2. Separate gains and losses
        3. Apply exponential smoothing with span=window
        4. RS = avg_gain / avg_loss
        5. RSI = 100 - (100 / (1 + RS))

    Args:
        close_prices: Series of closing prices
        window: RSI lookback window

    Returns:
        Series of RSI values (0-100)
    """
    # Calculate price changes
    delta = close_prices.diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Wilder's smoothing (exponential moving average)
    # Use adjust=False for Wilder's method
    avg_gain = gain.ewm(span=window, adjust=False).mean()
    avg_loss = loss.ewm(span=window, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss

    # Handle division by zero (avg_loss = 0 means all gains, RSI = 100)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # When avg_loss is 0, RS is inf, and RSI should be 100
    rsi = rsi.fillna(100.0)

    return rsi


def calculate_rsi_multiple_windows(close_prices: pd.Series,
                                   window_start: int = 1,
                                   window_end: int = 300,
                                   window_step: int = 1) -> dict:
    """
    Calculate RSI for multiple window sizes.

    This pre-computes RSI values for a range of windows, which is
    more efficient than calculating on-demand during backtest.

    Args:
        close_prices: Series of closing prices
        window_start: Starting RSI window (inclusive)
        window_end: Ending RSI window (inclusive)
        window_step: Step size between windows

    Returns:
        Dictionary mapping window -> RSI Series

    Example:
        >>> rsi_cache = calculate_rsi_multiple_windows(prices, 10, 50, 5)
        >>> rsi_cache[14]  # Get RSI(14)
    """
    logger.info(f"Pre-computing RSI for windows {window_start} to {window_end} (step={window_step})")

    rsi_cache = {}
    windows = range(window_start, window_end + 1, window_step)

    for window in windows:
        rsi_cache[window] = calculate_rsi(close_prices, window)

    logger.info(f"✓ Pre-computed {len(rsi_cache)} RSI series")

    return rsi_cache


def get_rsi_warmup_period(window: int) -> int:
    """
    Get recommended warmup period for RSI calculation.

    TA-Lib uses exponential smoothing which requires a warmup period
    for the moving averages to stabilize.

    Args:
        window: RSI window size

    Returns:
        Number of periods needed before RSI becomes stable
    """
    # Wilder's RSI uses EMA with span=window
    # Rule of thumb: 2-3x window for EMA stability
    return window + max(100, window * 2)
