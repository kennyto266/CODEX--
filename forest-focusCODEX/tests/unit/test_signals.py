"""Unit tests for signal generation module."""

import pytest
import pandas as pd
import numpy as np

from src.strategy.signals import (
    generate_rsi_signals,
    SignalType,
    get_signal_at_date,
    count_signal_transitions
)


@pytest.fixture
def sample_rsi():
    """Create sample RSI series for testing."""
    return pd.Series([50, 25, 20, 35, 65, 75, 80, 50, 30, 70], name='RSI_14')


@pytest.mark.unit
def test_generate_rsi_signals_basic(sample_rsi):
    """Test basic signal generation."""
    signals = generate_rsi_signals(sample_rsi, buy_threshold=30, sell_threshold=70)

    assert len(signals) == len(sample_rsi)
    assert signals[0] == 'HOLD'  # RSI=50
    assert signals[1] == 'BUY'   # RSI=25
    assert signals[2] == 'BUY'   # RSI=20
    assert signals[5] == 'SELL'  # RSI=75
    assert signals[6] == 'SELL'  # RSI=80


@pytest.mark.unit
def test_generate_rsi_signals_boundary():
    """Test signal generation at exact thresholds."""
    rsi = pd.Series([30, 70])
    signals = generate_rsi_signals(rsi, buy_threshold=30, sell_threshold=70)

    # At exact thresholds, should be HOLD
    assert signals[0] == 'HOLD'
    assert signals[1] == 'HOLD'


@pytest.mark.unit
def test_generate_rsi_signals_nan_handling():
    """Test that NaN RSI values produce HOLD signals."""
    rsi = pd.Series([50, np.nan, 25, np.nan, 75])
    signals = generate_rsi_signals(rsi)

    assert signals[1] == 'HOLD'  # NaN -> HOLD
    assert signals[3] == 'HOLD'  # NaN -> HOLD
    assert signals[2] == 'BUY'   # Valid RSI < 30
    assert signals[4] == 'SELL'  # Valid RSI > 70


@pytest.mark.unit
def test_generate_rsi_signals_invalid_thresholds():
    """Test validation of threshold parameters."""
    rsi = pd.Series([50, 60, 70])

    # buy_threshold >= sell_threshold
    with pytest.raises(ValueError, match="must be <"):
        generate_rsi_signals(rsi, buy_threshold=70, sell_threshold=30)

    # Thresholds out of range
    with pytest.raises(ValueError, match="must be in range"):
        generate_rsi_signals(rsi, buy_threshold=-10, sell_threshold=70)


@pytest.mark.unit
def test_count_signal_transitions(sample_rsi):
    """Test signal transition counting."""
    signals = generate_rsi_signals(sample_rsi)
    counts = count_signal_transitions(signals)

    assert counts['total_signals'] == len(sample_rsi)
    assert counts['buy_signals'] > 0
    assert counts['sell_signals'] > 0
    assert counts['hold_signals'] > 0
