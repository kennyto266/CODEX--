"""Unit tests for visualization modules."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from src.visualization.equity_curve import plot_equity_curve
from src.visualization.parameter_chart import plot_parameter_sensitivity
from src.performance.metrics import PerformanceMetrics


@pytest.fixture
def sample_equity_curves():
    """Create sample equity curves."""
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    strategy = pd.Series(
        [100000 + i * 500 + (i % 5) * 200 for i in range(50)],
        index=dates
    )
    baseline = pd.Series(
        [100000 + i * 400 for i in range(50)],
        index=dates
    )
    return strategy, baseline


@pytest.fixture
def sample_metrics():
    """Create sample performance metrics."""
    return [
        PerformanceMetrics(
            rsi_window=i,
            total_return=0.1 + i * 0.01,
            annualized_return=0.12,
            annualized_volatility=0.2,
            sharpe_ratio=0.5 + i * 0.05,
            max_drawdown=-0.1,
            win_rate=0.6,
            num_trades=10
        )
        for i in range(10, 21)
    ]


@pytest.mark.unit
def test_plot_equity_curve(sample_equity_curves, tmp_path):
    """Test equity curve plot generation."""
    strategy, baseline = sample_equity_curves

    output_file = tmp_path / "test_equity.png"

    result_path = plot_equity_curve(
        strategy_equity=strategy,
        baseline_equity=baseline,
        output_path=str(output_file)
    )

    assert Path(result_path).exists()
    assert Path(result_path).suffix == '.png'


@pytest.mark.unit
def test_plot_parameter_sensitivity(sample_metrics, tmp_path):
    """Test parameter sensitivity plot generation."""
    output_file = tmp_path / "test_param.png"

    result_path = plot_parameter_sensitivity(
        results=sample_metrics,
        optimal_window=15,
        output_path=str(output_file)
    )

    assert Path(result_path).exists()
    assert Path(result_path).suffix == '.png'


@pytest.mark.unit
def test_plot_equity_curve_auto_path(sample_equity_curves, tmp_path, monkeypatch):
    """Test equity curve plot with auto-generated path."""
    strategy, baseline = sample_equity_curves

    # Temporarily change to tmp directory
    monkeypatch.chdir(tmp_path)

    result_path = plot_equity_curve(
        strategy_equity=strategy,
        baseline_equity=baseline
    )

    # Should create default path
    assert 'equity_curve.png' in result_path
