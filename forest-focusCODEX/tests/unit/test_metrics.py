"""Unit tests for performance metrics module."""

import pytest
import pandas as pd
import numpy as np

from src.performance.metrics import (
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate
)
from src.strategy.backtest_engine import Trade


@pytest.fixture
def sample_equity_curve():
    """Create sample equity curve."""
    return pd.Series([100000, 101000, 102000, 101500, 103000, 104000])


@pytest.mark.unit
def test_calculate_returns(sample_equity_curve):
    """Test returns calculation."""
    returns = calculate_returns(sample_equity_curve)

    assert len(returns) == len(sample_equity_curve) - 1
    assert isinstance(returns, pd.Series)


@pytest.mark.unit
def test_calculate_sharpe_ratio():
    """Test Sharpe ratio calculation."""
    # Positive returns
    returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.005])
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

    assert isinstance(sharpe, float)
    assert not np.isnan(sharpe)


@pytest.mark.unit
def test_calculate_sharpe_ratio_zero_volatility():
    """Test Sharpe with zero volatility."""
    returns = pd.Series([0.0, 0.0, 0.0])
    sharpe = calculate_sharpe_ratio(returns)

    assert sharpe == 0.0


@pytest.mark.unit
def test_calculate_max_drawdown(sample_equity_curve):
    """Test maximum drawdown calculation."""
    max_dd = calculate_max_drawdown(sample_equity_curve)

    assert isinstance(max_dd, float)
    assert max_dd <= 0  # Drawdown is negative


@pytest.mark.unit
def test_calculate_max_drawdown_no_drawdown():
    """Test drawdown with monotonically increasing equity."""
    equity = pd.Series([100, 110, 120, 130])
    max_dd = calculate_max_drawdown(equity)

    assert max_dd == 0.0


@pytest.mark.unit
def test_calculate_win_rate():
    """Test win rate calculation."""
    trades = [
        Trade(1, pd.Timestamp('2023-01-01'), 'BUY', 100.0, 100, 10000, 10, 0, 10, 10010),
        Trade(2, pd.Timestamp('2023-01-02'), 'SELL', 105.0, 100, 10500, 10.5, 10.5, 21, 10479),
        Trade(3, pd.Timestamp('2023-01-03'), 'BUY', 105.0, 100, 10500, 10.5, 0, 10.5, 10510.5),
        Trade(4, pd.Timestamp('2023-01-04'), 'SELL', 100.0, 100, 10000, 10, 10, 20, 9980)
    ]

    win_rate, winning, losing = calculate_win_rate(trades)

    assert 0 <= win_rate <= 1
    assert winning + losing == 2  # 2 round trips


@pytest.mark.unit
def test_calculate_win_rate_empty():
    """Test win rate with no trades."""
    win_rate, winning, losing = calculate_win_rate([])

    assert win_rate == 0.0
    assert winning == 0
    assert losing == 0
