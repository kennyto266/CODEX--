"""Unit tests for backtest engine."""

import pytest
import pandas as pd

from src.strategy.backtest_engine import BacktestEngine, PositionStatus


@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05']),
        'open': [100.0, 102.0, 101.0],
        'high': [101.0, 103.0, 102.0],
        'low': [99.0, 101.0, 100.0],
        'close': [100.0, 102.0, 101.0],
        'volume': [1000000, 1100000, 1050000]
    })


@pytest.fixture
def sample_signals():
    """Create sample signals."""
    return pd.Series(['BUY', 'HOLD', 'SELL'])


@pytest.mark.unit
def test_backtest_engine_initialization(sample_data, sample_signals):
    """Test engine initialization."""
    engine = BacktestEngine(
        data=sample_data,
        signals=sample_signals,
        initial_capital=100000.0
    )

    assert engine.initial_capital == 100000.0
    assert engine.position.cash == 100000.0
    assert engine.position.status == PositionStatus.OUT_MARKET


@pytest.mark.unit
def test_execute_buy(sample_data, sample_signals):
    """Test buy order execution."""
    engine = BacktestEngine(sample_data, sample_signals, initial_capital=100000.0)

    date = sample_data['date'].iloc[0]
    price = 100.0

    success = engine.execute_buy(date, price)

    assert success is True
    assert engine.position.status == PositionStatus.IN_MARKET
    assert engine.position.shares > 0
    assert engine.position.cash < 100000.0
    assert len(engine.trades) == 1


@pytest.mark.unit
def test_execute_sell(sample_data, sample_signals):
    """Test sell order execution."""
    engine = BacktestEngine(sample_data, sample_signals, initial_capital=100000.0)

    # First buy
    engine.execute_buy(sample_data['date'].iloc[0], 100.0)

    # Then sell
    success = engine.execute_sell(sample_data['date'].iloc[1], 102.0)

    assert success is True
    assert engine.position.status == PositionStatus.OUT_MARKET
    assert engine.position.shares == 0
    assert len(engine.trades) == 2


@pytest.mark.unit
def test_run_backtest(sample_data, sample_signals):
    """Test complete backtest run."""
    engine = BacktestEngine(sample_data, sample_signals, initial_capital=100000.0)

    trades, equity_curve = engine.run()

    assert isinstance(trades, list)
    assert isinstance(equity_curve, pd.Series)
    assert len(equity_curve) == len(sample_data)
