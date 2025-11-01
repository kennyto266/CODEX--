"""
Tests for Vectorized Metrics Module

Test Coverage:
- Performance metrics extraction
- Risk metrics calculation
- Trade metrics analysis
- Drawdown analysis
- Equity curve metrics
- Reports generation
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.backtest.vectorbt_metrics import (
    VectorbtMetricsExtractor,
    MetricsReport,
    PerformanceMetrics,
    RiskMetrics,
    TradeMetrics,
)


class MockPortfolio:
    """Mock vectorbt Portfolio for testing."""

    def __init__(self, portfolio_values, trades_data=None):
        """Initialize mock portfolio."""
        self.portfolio_values_data = portfolio_values
        self.trades_data = trades_data or []
        self.trades = MockTrades(trades_data) if trades_data else None
        self.stats_data = {
            'Sharpe Ratio': 1.5,
            'Sortino Ratio': 2.0,
            'Profit Factor': 2.5,
        }

    def total_return(self):
        """Calculate total return."""
        if len(self.portfolio_values_data) < 2:
            return 0.0
        return float(self.portfolio_values_data[-1] / self.portfolio_values_data[0] - 1)

    def portfolio_value(self):
        """Return portfolio values."""
        return MockSeries(self.portfolio_values_data)

    def daily_returns(self):
        """Calculate daily returns."""
        if len(self.portfolio_values_data) < 2:
            return None
        returns = np.diff(self.portfolio_values_data) / self.portfolio_values_data[:-1]
        return MockSeries(returns)

    def stats(self):
        """Return stats dictionary."""
        return self.stats_data


class MockTrades:
    """Mock trades object."""

    def __init__(self, records):
        """Initialize mock trades."""
        self.records = records

    def count(self):
        """Return trade count."""
        return len(self.records)

    def win_rate(self):
        """Calculate win rate."""
        if not self.records:
            return 0.0
        winners = sum(1 for r in self.records if r.get('pnl', 0) > 0)
        return float(winners / len(self.records))


class MockSeries:
    """Mock pandas Series."""

    def __init__(self, values):
        """Initialize mock series."""
        self.values = np.array(values)

    def mean(self):
        """Calculate mean."""
        return np.mean(self.values)


class TestPerformanceMetricsExtraction:
    """Test performance metrics extraction."""

    def test_extract_positive_return(self):
        """Test extracting metrics for profitable backtest."""
        portfolio_values = np.array([10000, 11000, 12100, 13310, 14641])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert 'total_return' in metrics
        assert 'annualized_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'sortino_ratio' in metrics
        assert metrics['total_return'] > 0  # Profitable

    def test_extract_negative_return(self):
        """Test extracting metrics for losing backtest."""
        portfolio_values = np.array([10000, 9500, 9000, 8500, 8000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert metrics['total_return'] < 0  # Losing trade

    def test_extract_zero_volatility(self):
        """Test handling zero volatility (flat returns)."""
        portfolio_values = np.array([10000, 10000, 10000, 10000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert metrics['volatility'] == 0.0
        # Sharpe ratio will come from stats dict if available, or 0 if calculated
        assert metrics['sharpe_ratio'] >= 0.0  # Should be non-negative

    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        portfolio_values = np.array([10000, 15000, 12000, 8000, 14000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert metrics['max_drawdown'] < 0  # Should be negative
        assert metrics['max_drawdown'] <= -0.4  # Should be around -46.67%

    def test_calmar_ratio_calculation(self):
        """Test Calmar ratio (return / max drawdown)."""
        portfolio_values = np.array([10000, 12000, 11000, 13000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert 'calmar_ratio' in metrics
        assert metrics['calmar_ratio'] > 0  # Positive return and DD exists


class TestRiskMetricsExtraction:
    """Test risk metrics extraction."""

    def test_extract_var_metrics(self):
        """Test Value at Risk calculation."""
        portfolio_values = np.array([10000, 11000, 9500, 10200, 10800, 9900])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_risk_metrics()

        assert 'var_95' in metrics
        assert 'var_99' in metrics
        # VaR is calculated as percentile values; both should exist
        assert isinstance(metrics['var_95'], float)
        assert isinstance(metrics['var_99'], float)

    def test_extract_cvar_metrics(self):
        """Test Conditional VaR (Expected Shortfall)."""
        portfolio_values = np.array([10000, 11000, 9500, 10200, 10800, 9900])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_risk_metrics()

        assert 'cvar_95' in metrics
        assert 'cvar_99' in metrics
        # CVaR should be more extreme than VaR
        assert metrics['cvar_95'] <= metrics['var_95']

    def test_extract_skewness_kurtosis(self):
        """Test skewness and kurtosis calculation."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800, 11500, 11100])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_risk_metrics()

        assert 'skewness' in metrics
        assert 'kurtosis' in metrics
        # These should be floats
        assert isinstance(metrics['skewness'], float)
        assert isinstance(metrics['kurtosis'], float)

    def test_downside_deviation(self):
        """Test downside deviation (Sortino denominator)."""
        portfolio_values = np.array([10000, 11000, 10500, 10900, 10200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_risk_metrics()

        assert 'downside_deviation' in metrics
        assert metrics['downside_deviation'] >= 0


class TestTradeMetricsExtraction:
    """Test trade-level metrics extraction."""

    def test_extract_trade_statistics(self):
        """Test extracting trade count and win rate."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': -50, 'entry_idx': 6, 'exit_idx': 10},
            {'pnl': 75, 'entry_idx': 11, 'exit_idx': 15},
        ]
        portfolio = MockPortfolio(np.ones(20), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        assert metrics['total_trades'] == 3
        assert metrics['winning_trades'] == 2
        assert metrics['losing_trades'] == 1
        assert metrics['win_rate'] == 2/3

    def test_profit_factor_calculation(self):
        """Test profit factor (gross profit / gross loss)."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': 200, 'entry_idx': 6, 'exit_idx': 10},
            {'pnl': -50, 'entry_idx': 11, 'exit_idx': 15},
        ]
        portfolio = MockPortfolio(np.ones(20), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        # Gross profit: 100 + 200 = 300
        # Gross loss: 50
        # Profit factor: 300 / 50 = 6.0
        assert metrics['profit_factor'] == 6.0

    def test_average_win_loss(self):
        """Test average win and loss calculation."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': 150, 'entry_idx': 6, 'exit_idx': 10},
            {'pnl': -50, 'entry_idx': 11, 'exit_idx': 15},
            {'pnl': -30, 'entry_idx': 16, 'exit_idx': 20},
        ]
        portfolio = MockPortfolio(np.ones(25), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        # Average win: (100 + 150) / 2 = 125
        # Average loss: (-50 - 30) / 2 = -40
        assert metrics['avg_win'] == 125.0
        assert metrics['avg_loss'] == -40.0

    def test_largest_win_loss(self):
        """Test tracking largest win and loss."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': 500, 'entry_idx': 6, 'exit_idx': 10},  # Largest win
            {'pnl': -200, 'entry_idx': 11, 'exit_idx': 15},  # Largest loss
            {'pnl': -50, 'entry_idx': 16, 'exit_idx': 20},
        ]
        portfolio = MockPortfolio(np.ones(25), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        assert metrics['largest_win'] == 500.0
        assert metrics['largest_loss'] == -200.0

    def test_consecutive_wins_losses(self):
        """Test consecutive wins and losses tracking."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},    # Win
            {'pnl': 50, 'entry_idx': 6, 'exit_idx': 10},     # Win
            {'pnl': 75, 'entry_idx': 11, 'exit_idx': 15},    # Win (3 consecutive)
            {'pnl': -50, 'entry_idx': 16, 'exit_idx': 20},   # Loss
            {'pnl': -30, 'entry_idx': 21, 'exit_idx': 25},   # Loss (2 consecutive)
        ]
        portfolio = MockPortfolio(np.ones(30), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        assert metrics['consecutive_wins'] == 3
        assert metrics['consecutive_losses'] == 2

    def test_average_trade_duration(self):
        """Test average trade duration calculation."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},    # 5 days
            {'pnl': 50, 'entry_idx': 6, 'exit_idx': 15},    # 9 days
            {'pnl': 75, 'entry_idx': 16, 'exit_idx': 26},   # 10 days
        ]
        portfolio = MockPortfolio(np.ones(30), trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        # Average: (5 + 9 + 10) / 3 = 8 days
        assert metrics['avg_trade_duration'] == 8.0

    def test_no_trades(self):
        """Test handling portfolio with no trades."""
        portfolio = MockPortfolio(np.ones(10), [])
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0
        assert metrics['profit_factor'] == 0.0


class TestDrawdownAnalysis:
    """Test drawdown analysis metrics."""

    def test_max_drawdown_detection(self):
        """Test maximum drawdown detection."""
        portfolio_values = np.array([10000, 15000, 12000, 8000, 14000, 13000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_drawdown_metrics()

        assert 'max_drawdown' in metrics
        # Max DD from peak of 15000 to low of 8000
        assert metrics['max_drawdown'] <= -0.46  # Should be around -46.67%

    def test_current_drawdown_tracking(self):
        """Test current drawdown from recent peak."""
        portfolio_values = np.array([10000, 15000, 12000, 14000, 13000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_drawdown_metrics()

        assert 'current_drawdown' in metrics
        # Current from peak of 15000 to final 13000
        assert metrics['current_drawdown'] <= -0.13  # Around -13.33%

    def test_drawdown_duration(self):
        """Test drawdown duration tracking."""
        portfolio_values = np.array([10000, 15000, 14000, 13000, 12000, 11000, 16000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_drawdown_metrics()

        assert 'max_drawdown_duration' in metrics
        assert metrics['max_drawdown_duration'] > 0

    def test_drawdown_event_counting(self):
        """Test counting distinct drawdown events."""
        # Series that has recovery and new entry: peak -> loss -> recovery -> peak -> loss
        portfolio_values = np.array([10000, 15000, 12000, 15000, 14000, 16000, 14000])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_drawdown_metrics()

        assert 'drawdown_events' in metrics


class TestEquityCurveMetrics:
    """Test equity curve analysis."""

    def test_positive_negative_days(self):
        """Test counting positive and negative trading days."""
        # Returns: +10%, -5%, +8%, -2%, +15%
        portfolio_values = np.array([10000, 11000, 10450, 11286, 11060, 12719])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_equity_curve_metrics()

        assert metrics['positive_days'] == 3  # +10%, +8%, +15%
        assert metrics['negative_days'] == 2  # -5%, -2%

    def test_positive_day_rate(self):
        """Test percentage of profitable days."""
        portfolio_values = np.array([10000, 11000, 10450, 11286, 11060, 12719])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_equity_curve_metrics()

        assert 0 <= metrics['positive_day_rate'] <= 1
        assert metrics['positive_day_rate'] == 3/5  # 60% positive days

    def test_best_worst_day(self):
        """Test best and worst day returns."""
        # Returns: +10%, -5%, +8%, -2%, +15%
        portfolio_values = np.array([10000, 11000, 10450, 11286, 11060, 12719])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_equity_curve_metrics()

        assert metrics['best_day'] > 0.14  # +15% is best
        assert metrics['worst_day'] < -0.04  # -5% is worst


class TestMetricsReportGeneration:
    """Test metrics report generation."""

    def test_extract_all_metrics(self):
        """Test extracting all metric categories."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        all_metrics = extractor.extract_all()

        assert 'performance' in all_metrics
        assert 'risk' in all_metrics
        assert 'trades' in all_metrics
        assert 'drawdown' in all_metrics
        assert 'equity_curve' in all_metrics

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        result_dict = report.to_dict()

        assert isinstance(result_dict, dict)
        assert 'performance' in result_dict

    def test_report_to_dataframe(self):
        """Test converting report to DataFrame."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        df = report.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1  # Single row

    def test_report_summary_text(self):
        """Test generating text summary report."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        summary = report.to_summary_text()

        assert isinstance(summary, str)
        assert "BACKTEST METRICS REPORT" in summary
        assert "PERFORMANCE METRICS" in summary
        assert "RISK METRICS" in summary


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_day_portfolio(self):
        """Test handling portfolio with only one day."""
        portfolio = MockPortfolio(np.array([10000]))
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        # Should not crash
        assert isinstance(metrics, dict)

    def test_empty_portfolio(self):
        """Test handling empty portfolio."""
        portfolio = MockPortfolio(np.array([]))
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_equity_curve_metrics()

        # Should return empty dict or handle gracefully
        assert isinstance(metrics, dict)

    def test_nan_values(self):
        """Test handling NaN values in data."""
        portfolio_values = np.array([10000, 11000, np.nan, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        # Should not crash on NaN
        metrics = extractor._extract_performance_metrics()
        assert isinstance(metrics, dict)

    def test_portfolio_without_trades(self):
        """Test portfolio with no trades attribute."""
        portfolio = MockPortfolio(np.ones(10))
        portfolio.trades = None
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_trade_metrics()

        assert metrics['total_trades'] == 0

    def test_zero_risk_free_rate(self):
        """Test with zero risk-free rate."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio, risk_free_rate=0.0)

        metrics = extractor._extract_performance_metrics()

        assert 'sharpe_ratio' in metrics

    def test_high_risk_free_rate(self):
        """Test with high risk-free rate."""
        portfolio_values = np.array([10000, 11000, 10500, 11200, 10800])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio, risk_free_rate=0.50)

        metrics = extractor._extract_performance_metrics()

        assert 'sharpe_ratio' in metrics


class TestMetricsCalculationAccuracy:
    """Test accuracy of metric calculations."""

    def test_total_return_accuracy(self):
        """Test total return calculation accuracy."""
        portfolio_values = np.array([10000, 12000])  # 20% return
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        assert abs(metrics['total_return'] - 0.2) < 0.001

    def test_volatility_calculation(self):
        """Test volatility is properly annualized."""
        # Create consistent returns
        portfolio_values = np.array([10000] + [10000 * 1.01 ** i for i in range(1, 100)])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        # Should have positive volatility
        assert metrics['volatility'] > 0

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio is properly calculated."""
        portfolio_values = np.array([10000, 10100, 10200, 10150, 10250, 10350])
        portfolio = MockPortfolio(portfolio_values)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor._extract_performance_metrics()

        # Should be positive (strategy is beating risk-free rate)
        assert metrics['sharpe_ratio'] > 0


class TestMultipleScenarios:
    """Test multiple realistic trading scenarios."""

    def test_winning_strategy(self):
        """Test metrics for consistently winning strategy."""
        trades_data = [
            {'pnl': 200, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': 150, 'entry_idx': 6, 'exit_idx': 10},
            {'pnl': 180, 'entry_idx': 11, 'exit_idx': 15},
        ]
        portfolio_values = np.linspace(10000, 12000, 20)
        portfolio = MockPortfolio(portfolio_values, trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor.extract_all()

        assert metrics['trades']['win_rate'] == 1.0
        assert metrics['performance']['total_return'] > 0

    def test_losing_strategy(self):
        """Test metrics for consistently losing strategy."""
        trades_data = [
            {'pnl': -200, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': -150, 'entry_idx': 6, 'exit_idx': 10},
            {'pnl': -180, 'entry_idx': 11, 'exit_idx': 15},
        ]
        portfolio_values = np.linspace(10000, 8000, 20)
        portfolio = MockPortfolio(portfolio_values, trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor.extract_all()

        assert metrics['trades']['win_rate'] == 0.0
        assert metrics['performance']['total_return'] < 0

    def test_breakeven_strategy(self):
        """Test metrics for breakeven strategy."""
        trades_data = [
            {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
            {'pnl': -100, 'entry_idx': 6, 'exit_idx': 10},
        ]
        portfolio_values = np.array([10000] * 15)
        portfolio = MockPortfolio(portfolio_values, trades_data)
        extractor = VectorbtMetricsExtractor(portfolio)

        metrics = extractor.extract_all()

        assert abs(metrics['performance']['total_return']) < 0.001
        assert metrics['trades']['win_rate'] == 0.5
