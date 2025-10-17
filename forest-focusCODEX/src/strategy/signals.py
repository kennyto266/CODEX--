"""
Trading signal generation module.

Generates BUY/SELL/HOLD signals based on RSI indicator thresholds.
"""

import logging
from enum import Enum
from typing import Union

import pandas as pd
import numpy as np

logger = logging.getLogger("rsi_backtest.strategy.signals")


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


def generate_rsi_signals(
    rsi: pd.Series,
    buy_threshold: float = 30.0,
    sell_threshold: float = 70.0
) -> pd.Series:
    """
    Generate trading signals based on RSI thresholds.

    Signal Rules:
    - BUY when RSI < buy_threshold (oversold)
    - SELL when RSI > sell_threshold (overbought)
    - HOLD otherwise

    Args:
        rsi: RSI indicator series (0-100)
        buy_threshold: RSI level below which to generate BUY signal (default: 30)
        sell_threshold: RSI level above which to generate SELL signal (default: 70)

    Returns:
        Series of signal strings ('BUY', 'SELL', 'HOLD')

    Raises:
        ValueError: If thresholds are invalid
    """
    if buy_threshold >= sell_threshold:
        raise ValueError(
            f"buy_threshold ({buy_threshold}) must be < sell_threshold ({sell_threshold})"
        )

    if buy_threshold < 0 or sell_threshold > 100:
        raise ValueError("Thresholds must be in range [0, 100]")

    # Initialize all signals as HOLD
    signals = pd.Series(SignalType.HOLD.value, index=rsi.index, name='signal')

    # Generate BUY signals (RSI < threshold, indicating oversold)
    signals[rsi < buy_threshold] = SignalType.BUY.value

    # Generate SELL signals (RSI > threshold, indicating overbought)
    signals[rsi > sell_threshold] = SignalType.SELL.value

    # Handle NaN RSI values (insufficient data) → HOLD
    signals[rsi.isna()] = SignalType.HOLD.value

    return signals


def get_signal_at_date(
    signals: pd.Series,
    date: Union[pd.Timestamp, str, int]
) -> str:
    """
    Get trading signal for a specific date (with look-ahead bias protection).

    Args:
        signals: Signal series
        date: Date or index to query

    Returns:
        Signal string ('BUY', 'SELL', or 'HOLD')
    """
    try:
        if isinstance(date, int):
            # Index-based access
            return signals.iloc[date]
        else:
            # Date-based access
            return signals.loc[date]
    except (KeyError, IndexError):
        logger.warning(f"No signal found for date {date}, returning HOLD")
        return SignalType.HOLD.value


def count_signal_transitions(signals: pd.Series) -> dict:
    """
    Count signal transitions (for analysis purposes).

    Args:
        signals: Signal series

    Returns:
        Dictionary with transition counts
    """
    transitions = {
        'total_signals': len(signals),
        'buy_signals': (signals == SignalType.BUY.value).sum(),
        'sell_signals': (signals == SignalType.SELL.value).sum(),
        'hold_signals': (signals == SignalType.HOLD.value).sum()
    }

    # Count actual transitions (signal changes)
    signal_changes = (signals != signals.shift(1)).sum() - 1  # Subtract 1 for first row
    transitions['signal_changes'] = max(0, signal_changes)

    return transitions
