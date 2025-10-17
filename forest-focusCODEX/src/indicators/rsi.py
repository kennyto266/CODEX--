"""
RSI (Relative Strength Index) calculation module.

Wraps TA-Lib's RSI function with additional handling for edge cases.
"""

import logging
from typing import Union

import numpy as np
import pandas as pd

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logging.warning(
        "TA-Lib not available. RSI calculation will use fallback implementation. "
        "For production use, install TA-Lib for better performance."
    )

logger = logging.getLogger("rsi_backtest.indicators.rsi")


def calculate_rsi_talib(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate RSI using TA-Lib (Wilder's smoothing method).

    Args:
        prices: Close prices series
        window: RSI lookback period (typically 14)

    Returns:
        RSI values series (0-100), with NaN for initial warmup period
    """
    if not TALIB_AVAILABLE:
        raise ImportError(
            "TA-Lib is required but not installed. "
            "Please install TA-Lib to use this function."
        )

    rsi_values = talib.RSI(prices.values, timeperiod=window)
    return pd.Series(rsi_values, index=prices.index, name=f'RSI_{window}')


def calculate_rsi_fallback(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculate RSI using pure pandas (fallback when TA-Lib unavailable).

    Uses Wilder's exponential smoothing method:
    RS = Average Gain / Average Loss
    RSI = 100 - (100 / (1 + RS))

    Args:
        prices: Close prices series
        window: RSI lookback period

    Returns:
        RSI values series (0-100), with NaN for initial warmup period
    """
    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Calculate exponential moving averages (Wilder's smoothing)
    # Wilder's EMA uses adjust=False and alpha=1/window
    avg_gain = gain.ewm(span=window, adjust=False).mean()
    avg_loss = loss.ewm(span=window, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Handle edge case: all gains (loss = 0) → RSI = 100
    rsi = rsi.fillna(100.0)

    return pd.Series(rsi.values, index=prices.index, name=f'RSI_{window}')


def calculate_rsi(
    prices: Union[pd.Series, np.ndarray],
    window: int,
    use_talib: bool = True
) -> pd.Series:
    """
    Calculate RSI indicator values.

    Args:
        prices: Close prices (pandas Series or numpy array)
        window: RSI lookback period (1-500)
        use_talib: If True, use TA-Lib (faster). If False, use pandas fallback.

    Returns:
        RSI values series (0-100)

    Raises:
        ValueError: If window is invalid or insufficient data
    """
    if window < 1 or window > 500:
        raise ValueError(f"RSI window must be between 1 and 500, got {window}")

    # Convert to pandas Series if needed
    if isinstance(prices, np.ndarray):
        prices = pd.Series(prices)
    elif not isinstance(prices, pd.Series):
        raise TypeError(
            f"prices must be pandas Series or numpy array, got {type(prices)}"
        )

    if len(prices) < window:
        logger.warning(
            f"Insufficient data for RSI({window}): "
            f"need at least {window} bars, got {len(prices)}"
        )

    # Use TA-Lib if available and requested
    if use_talib and TALIB_AVAILABLE:
        return calculate_rsi_talib(prices, window)
    else:
        return calculate_rsi_fallback(prices, window)


def precompute_rsi_series(
    prices: pd.Series,
    windows: range
) -> dict:
    """
    Pre-compute RSI values for multiple windows (optimization for parameter sweep).

    Args:
        prices: Close prices series
        windows: Range of RSI windows to calculate (e.g., range(1, 301))

    Returns:
        Dictionary mapping window -> RSI series
    """
    logger.info(f"Pre-computing RSI for {len(list(windows))} windows...")

    rsi_cache = {}
    for window in windows:
        rsi_cache[window] = calculate_rsi(prices, window)

    logger.info(f"Pre-computation complete: {len(rsi_cache)} RSI series cached")
    return rsi_cache
