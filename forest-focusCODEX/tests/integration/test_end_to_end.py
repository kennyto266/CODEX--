"""
Integration tests for end-to-end backtest workflow.

Tests the complete data pipeline from loading to optimization.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.data.loader import load_csv
from src.data.validator import validate_data
from src.indicators.rsi import calculate_rsi
from src.strategy.signals import generate_rsi_signals
from src.strategy.backtest_engine import BacktestEngine
from src.performance.metrics import calculate_performance_metrics
from src.performance.optimizer import RSIOptimizer


@pytest.fixture
def sample_data_path():
    """Path to sample data file."""
    return "data/0700_HK_sample.csv"


@pytest.mark.integration
def test_full_workflow_single_window(sample_data_path):
    """Test complete workflow for a single RSI window."""
    # 1. Load data
    data = load_csv(sample_data_path)
    assert len(data) > 0

    # 2. Validate data
    is_valid, warnings = validate_data(data)
    assert is_valid is True

    # 3. Calculate RSI
    rsi = calculate_rsi(data['close'], window=14)
    assert len(rsi) == len(data)

    # 4. Generate signals
    signals = generate_rsi_signals(rsi)
    assert len(signals) == len(data)

    # 5. Run backtest
    engine = BacktestEngine(
        data=data,
        signals=signals,
        initial_capital=100000.0,
        commission=0.001,
        stamp_duty=0.001
    )

    trades, equity_curve = engine.run()

    # 6. Calculate metrics
    metrics = calculate_performance_metrics(
        rsi_window=14,
        equity_curve=equity_curve,
        trades=trades,
        initial_capital=100000.0
    )

    # Verify metrics are reasonable
    assert isinstance(metrics.sharpe_ratio, float)
    assert isinstance(metrics.total_return, float)
    assert isinstance(metrics.max_drawdown, float)


@pytest.mark.integration
@pytest.mark.slow
def test_optimizer_end_to_end(sample_data_path, tmp_path):
    """Test complete optimization workflow."""
    output_dir = tmp_path / "test_results"

    optimizer = RSIOptimizer(
        data_path=sample_data_path,
        start_window=10,
        end_window=20,
        step=5,
        buy_threshold=30.0,
        sell_threshold=70.0,
        initial_capital=100000.0,
        commission=0.001,
        stamp_duty=0.001,
        parallel_workers=2
    )

    # Run optimization
    optimal = optimizer.run(output_dir=str(output_dir))

    # Verify optimal result
    assert optimal is not None
    assert optimal.rsi_window in [10, 15, 20]
    assert isinstance(optimal.sharpe_ratio, float)

    # Verify output files
    assert (output_dir / "optimization_results.csv").exists()
    assert (output_dir / "top_10_windows.csv").exists()
    assert (output_dir / "summary_report.txt").exists()

    # Verify CSV content
    results_df = pd.read_csv(output_dir / "optimization_results.csv")
    assert len(results_df) == 3  # 3 windows tested (10, 15, 20)
    assert 'rsi_window' in results_df.columns
    assert 'sharpe_ratio' in results_df.columns


@pytest.mark.integration
def test_data_pipeline_validation(sample_data_path):
    """Test that data pipeline handles validation correctly."""
    # Load and validate in one flow
    data = load_csv(sample_data_path)
    is_valid, warnings = validate_data(data, strict=True)

    assert is_valid is True
    # May have warnings about missing dates (weekends), but should pass


@pytest.mark.integration
def test_signal_to_trade_execution(sample_data_path):
    """Test that signals are correctly executed as trades."""
    data = load_csv(sample_data_path)
    rsi = calculate_rsi(data['close'], window=14)

    # Generate signals
    signals = generate_rsi_signals(rsi, buy_threshold=30, sell_threshold=70)

    # Count expected signal changes
    signal_changes = (signals != signals.shift(1)).sum()

    # Run backtest
    engine = BacktestEngine(data, signals, initial_capital=100000.0)
    trades, _ = engine.run()

    # Trades should correlate with signal changes
    # (though not exactly equal, as some signals may not execute)
    assert len(trades) <= signal_changes
