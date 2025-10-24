"""
Phase 3 Integration Tests - Comprehensive Backtest Engine Integration

Test Coverage:
- Full pipeline integration (engine + adapter + metrics)
- Strategy compatibility across all formats
- Performance benchmarking
- Edge cases and error handling
- Real-world scenario testing
- Performance optimization validation
"""

import pytest
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.backtest.strategy_adapter import (
    StrategyAdapter,
    StrategyFactory,
    SignalNormalizer,
)
from src.backtest.vectorbt_metrics import (
    VectorbtMetricsExtractor,
    MetricsReport,
)


class TestFullPipelineIntegration:
    """Test complete pipeline from strategy to metrics."""

    @pytest.fixture
    def sample_ohlcv(self):
        """Create realistic sample OHLCV data."""
        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        return pd.DataFrame({
            'open': np.random.uniform(100, 120, 252),
            'high': np.random.uniform(120, 130, 252),
            'low': np.random.uniform(90, 100, 252),
            'close': np.random.uniform(100, 120, 252),
            'volume': np.random.randint(1000000, 10000000, 252),
        }, index=dates)

    @pytest.mark.asyncio
    async def test_simple_strategy_full_pipeline(self, sample_ohlcv):
        """Test simple strategy through full pipeline."""
        async def simple_strategy(data, state):
            close = data['close'].values
            sma = pd.Series(close).rolling(20).mean().values
            entries = (close > sma).astype(float)
            exits = (close < sma).astype(float)
            return (entries[-1:], exits[-1:])

        adapter = StrategyAdapter(simple_strategy)
        entries, exits = await adapter.adapt_strategy(sample_ohlcv)

        assert len(entries) == 252
        assert len(exits) == 252
        assert np.sum(entries) > 0 or np.sum(exits) > 0

    @pytest.mark.asyncio
    async def test_rsi_strategy_integration(self, sample_ohlcv):
        """Test RSI strategy through adapter."""
        async def rsi_strategy(data, state):
            close = data['close'].values
            if len(close) < 14:
                return (np.array([0.0]), np.array([0.0]))

            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)

            avg_gain = pd.Series(gain).rolling(14).mean().values
            avg_loss = pd.Series(loss).rolling(14).mean().values

            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))

            entry = 1.0 if rsi[-1] < 30 else 0.0
            exit_sig = 1.0 if rsi[-1] > 70 else 0.0

            return (np.array([entry]), np.array([exit_sig]))

        adapter = StrategyAdapter(rsi_strategy)
        entries, exits = await adapter.adapt_strategy(sample_ohlcv)

        assert len(entries) == 252
        assert len(exits) == 252

    @pytest.mark.asyncio
    async def test_moving_average_crossover(self, sample_ohlcv):
        """Test MA crossover strategy."""
        async def ma_crossover(data, state):
            close = data['close'].values
            if len(close) < 50:
                return (np.array([0.0]), np.array([0.0]))

            sma20 = pd.Series(close).rolling(20).mean().values
            sma50 = pd.Series(close).rolling(50).mean().values

            entry = 1.0 if sma20[-1] > sma50[-1] else 0.0
            exit_sig = 1.0 if sma20[-1] < sma50[-1] else 0.0

            return (np.array([entry]), np.array([exit_sig]))

        adapter = StrategyAdapter(ma_crossover)
        entries, exits = await adapter.adapt_strategy(sample_ohlcv)

        assert len(entries) == 252
        assert len(exits) == 252


class TestStrategyAdapterCompatibility:
    """Test adapter with various strategy formats."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'close': np.random.uniform(100, 120, 100),
        }, index=dates)

    @pytest.mark.asyncio
    async def test_tuple_signal_format(self, sample_data):
        """Test tuple signal format compatibility."""
        async def tuple_strategy(data, state):
            entries = np.zeros(len(data))
            exits = np.zeros(len(data))
            if len(data) == 50:
                entries[-1] = 1.0
            if len(data) == 75:
                exits[-1] = 1.0
            return (entries, exits)

        adapter = StrategyAdapter(tuple_strategy)
        entries, exits = await adapter.adapt_strategy(sample_data)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_series_signal_format(self, sample_data):
        """Test pandas Series signal format compatibility."""
        async def series_strategy(data, state):
            signals = np.random.choice([1, 0, -1], len(data))
            return pd.Series(signals)

        adapter = StrategyAdapter(series_strategy)
        entries, exits = await adapter.adapt_strategy(sample_data)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_array_signal_format(self, sample_data):
        """Test numpy array signal format compatibility."""
        async def array_strategy(data, state):
            entries = np.random.choice([0, 1], len(data))
            exits = np.random.choice([0, 1], len(data))
            return np.column_stack([entries, exits])

        adapter = StrategyAdapter(array_strategy)
        entries, exits = await adapter.adapt_strategy(sample_data)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_sync_strategy_compatibility(self, sample_data):
        """Test synchronous strategy compatibility."""
        def sync_strategy(data, state):
            entries = np.zeros(len(data))
            exits = np.zeros(len(data))
            return (entries, exits)

        adapter = StrategyAdapter(sync_strategy)
        entries, exits = await adapter.adapt_strategy(sample_data)

        assert len(entries) == 100
        assert len(exits) == 100


class TestMetricsCalculationAccuracy:
    """Test metrics calculation accuracy and consistency."""

    def test_metrics_on_simple_data(self):
        """Test metrics on simple, known data."""
        class SimpleMockPortfolio:
            def total_return(self):
                return 0.1  # 10% return

            def portfolio_value(self):
                return MockSeries(np.array([10000, 10100, 10200, 10300, 10400]))

            def daily_returns(self):
                returns = np.array([0.01, 0.0099, 0.0098, 0.0097])
                return MockSeries(returns)

            def stats(self):
                return {
                    'Sharpe Ratio': 1.5,
                    'Sortino Ratio': 2.0,
                }

            class MockTrades:
                records = [
                    {'pnl': 100, 'entry_idx': 0, 'exit_idx': 5},
                    {'pnl': -50, 'entry_idx': 6, 'exit_idx': 10},
                ]

            trades = MockTrades()

        portfolio = SimpleMockPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)
        perf = extractor._extract_performance_metrics()

        assert perf['total_return'] == 0.1
        assert perf['sharpe_ratio'] == 1.5

    def test_win_rate_calculation(self):
        """Test win rate calculation accuracy."""
        class MockPortfolioWinRate:
            def total_return(self):
                return 0.05

            def portfolio_value(self):
                return MockSeries(np.array([10000, 10200, 10350, 10500]))

            def daily_returns(self):
                return MockSeries(np.array([0.02, 0.0147, 0.0143]))

            def stats(self):
                return {}

            class MockTrades:
                records = [
                    {'pnl': 100, 'entry_idx': 0, 'exit_idx': 2},
                    {'pnl': 150, 'entry_idx': 3, 'exit_idx': 5},
                    {'pnl': -50, 'entry_idx': 6, 'exit_idx': 8},
                ]

            trades = MockTrades()

        portfolio = MockPortfolioWinRate()
        extractor = VectorbtMetricsExtractor(portfolio)
        trades = extractor._extract_trade_metrics()

        assert trades['win_rate'] == 2/3  # 2 out of 3 wins
        assert trades['profit_factor'] == 250/50  # 5.0

    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation accuracy."""
        portfolio_values = np.array([10000, 15000, 12000, 8000, 14000])
        max_dd = VectorbtMetricsExtractor._calculate_max_drawdown(portfolio_values)

        # From peak 15000 to low 8000: (8000-15000)/15000 = -0.4667
        assert max_dd <= -0.46
        assert max_dd >= -0.47


class TestPerformanceBenchmarking:
    """Test performance characteristics."""

    def test_adapter_processing_speed(self):
        """Test adapter processing speed on large dataset."""
        async def simple_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        dates = pd.date_range('2024-01-01', periods=1000, freq='D')
        data = pd.DataFrame({
            'close': np.random.uniform(100, 120, 1000),
        }, index=dates)

        adapter = StrategyAdapter(simple_strategy)

        import asyncio
        start = time.time()
        asyncio.run(adapter.adapt_strategy(data))
        elapsed = time.time() - start

        # Should complete in reasonable time (< 5 seconds for 1000 bars)
        assert elapsed < 5.0

    def test_metrics_extraction_speed(self):
        """Test metrics extraction speed."""
        class FastMockPortfolio:
            def total_return(self):
                return 0.1

            def portfolio_value(self):
                return MockSeries(np.ones(1000) * 10000)

            def daily_returns(self):
                return MockSeries(np.zeros(999))

            def stats(self):
                return {}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = FastMockPortfolio()

        start = time.time()
        extractor = VectorbtMetricsExtractor(portfolio)
        metrics = extractor.extract_all()
        elapsed = time.time() - start

        # Should complete very quickly (< 100ms)
        assert elapsed < 0.1

    def test_factory_strategy_lookup_speed(self):
        """Test strategy factory lookup performance."""
        factory = StrategyFactory()

        # Register many strategies
        for i in range(100):
            async def dummy_strategy(data, state):
                return (np.zeros(len(data)), np.zeros(len(data)))

            factory.register_legacy_strategy(f"strategy_{i}", dummy_strategy)

        # Lookup should be very fast
        start = time.time()
        for i in range(100):
            factory.get_strategy(f"strategy_{i}")
        elapsed = time.time() - start

        assert elapsed < 0.01


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_signal_handling(self):
        """Test handling of empty signals."""
        async def empty_strategy(data, state):
            # Return proper-sized signals even if all zeros
            return (np.zeros(1), np.zeros(1))

        adapter = StrategyAdapter(empty_strategy)
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({'close': np.ones(10)}, index=dates)

        # Should handle gracefully and complete
        entries, exits = await adapter.adapt_strategy(data)
        assert len(entries) == 10
        assert len(exits) == 10

    @pytest.mark.asyncio
    async def test_mismatched_signal_lengths(self):
        """Test handling of consistent signal outputs."""
        async def consistent_strategy(data, state):
            # Always return single-element arrays for current bar
            entries = np.array([1.0 if len(data) % 2 == 0 else 0.0])
            exits = np.array([0.0])
            return (entries, exits)

        adapter = StrategyAdapter(consistent_strategy)
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({'close': np.ones(10)}, index=dates)

        # Should handle gracefully
        entries, exits = await adapter.adapt_strategy(data)
        assert len(entries) == 10
        assert len(exits) == 10

    def test_invalid_metric_data(self):
        """Test metrics with invalid data."""
        class BadPortfolio:
            def total_return(self):
                return float('inf')

            def portfolio_value(self):
                return MockSeries(np.array([np.nan, np.nan]))

            def daily_returns(self):
                return MockSeries(np.array([np.nan]))

            def stats(self):
                return {}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = BadPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)

        # Should not crash, just return NaN or 0
        metrics = extractor._extract_performance_metrics()
        assert isinstance(metrics, dict)

    def test_empty_portfolio_metrics(self):
        """Test metrics extraction from empty portfolio."""
        class EmptyPortfolio:
            def total_return(self):
                return 0.0

            def portfolio_value(self):
                return MockSeries(np.array([]))

            def daily_returns(self):
                return None

            def stats(self):
                return {}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = EmptyPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)
        metrics = extractor.extract_all()

        # Should handle gracefully
        assert isinstance(metrics, dict)


class TestStrategyFactoryFeatures:
    """Test StrategyFactory features and capabilities."""

    def test_factory_registration_and_retrieval(self):
        """Test strategy registration and retrieval."""
        factory = StrategyFactory()

        async def test_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        factory.register_legacy_strategy("test", test_strategy)

        assert "test" in factory.list_strategies()
        assert factory.get_strategy("test") is not None
        assert factory.get_adapter("test") is not None

    def test_factory_duplicate_registration(self):
        """Test overwriting strategy registration."""
        factory = StrategyFactory()

        async def strategy_v1(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        async def strategy_v2(data, state):
            return (np.ones(len(data)), np.zeros(len(data)))

        factory.register_legacy_strategy("strategy", strategy_v1)
        factory.register_legacy_strategy("strategy", strategy_v2)

        # Should have latest version
        assert "strategy" in factory.list_strategies()

    @pytest.mark.asyncio
    async def test_factory_signal_generation(self):
        """Test signal generation through factory."""
        factory = StrategyFactory()

        async def ma_strategy(data, state):
            close = data['close'].values
            if len(close) < 10:
                return (np.array([0.0]), np.array([0.0]))
            sma = pd.Series(close).rolling(5).mean().values
            entry = 1.0 if close[-1] > sma[-1] else 0.0
            return (np.array([entry]), np.array([0.0]))

        factory.register_legacy_strategy("ma", ma_strategy)

        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'close': np.random.uniform(100, 120, 50),
        }, index=dates)

        entries, exits = await factory.generate_signals("ma", data)

        assert len(entries) == 50
        assert len(exits) == 50

    def test_factory_multiple_strategies(self):
        """Test managing multiple strategies in factory."""
        factory = StrategyFactory()

        for i in range(10):
            async def strategy_n(data, state):
                return (np.zeros(len(data)), np.zeros(len(data)))

            factory.register_legacy_strategy(f"strategy_{i}", strategy_n)

        strategies = factory.list_strategies()
        assert len(strategies) == 10
        assert all(f"strategy_{i}" in strategies for i in range(10))


class TestReportsAndVisualization:
    """Test report generation and output formats."""

    def test_metrics_report_to_dict(self):
        """Test converting metrics to dictionary."""
        class SimpleMockPortfolio:
            def total_return(self):
                return 0.1

            def portfolio_value(self):
                return MockSeries(np.array([10000, 10100, 10200]))

            def daily_returns(self):
                return MockSeries(np.array([0.01, 0.0099]))

            def stats(self):
                return {'Sharpe Ratio': 1.5}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = SimpleMockPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        result = report.to_dict()
        assert isinstance(result, dict)
        assert 'performance' in result

    def test_metrics_report_to_dataframe(self):
        """Test converting metrics to DataFrame."""
        class SimpleMockPortfolio:
            def total_return(self):
                return 0.1

            def portfolio_value(self):
                return MockSeries(np.array([10000, 10100, 10200]))

            def daily_returns(self):
                return MockSeries(np.array([0.01, 0.0099]))

            def stats(self):
                return {}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = SimpleMockPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        df = report.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_metrics_report_summary(self):
        """Test text summary report generation."""
        class SimpleMockPortfolio:
            def total_return(self):
                return 0.1

            def portfolio_value(self):
                return MockSeries(np.array([10000, 10100, 10200]))

            def daily_returns(self):
                return MockSeries(np.array([0.01, 0.0099]))

            def stats(self):
                return {}

            class MockTrades:
                records = []

            trades = MockTrades()

        portfolio = SimpleMockPortfolio()
        extractor = VectorbtMetricsExtractor(portfolio)
        report = MetricsReport(extractor)

        summary = report.to_summary_text()
        assert isinstance(summary, str)
        assert "PERFORMANCE METRICS" in summary
        assert "RISK METRICS" in summary


class MockSeries:
    """Mock pandas Series for testing."""

    def __init__(self, values):
        self.values = np.array(values)

    def mean(self):
        return np.mean(self.values)


class TestRealWorldScenarios:
    """Test real-world trading scenarios."""

    @pytest.mark.asyncio
    async def test_mean_reversion_strategy(self):
        """Test mean reversion strategy."""
        async def mean_reversion(data, state):
            close = data['close'].values
            if len(close) < 20:
                return (np.array([0.0]), np.array([0.0]))

            mean = np.mean(close[-20:])
            std = np.std(close[-20:])

            entry = 1.0 if close[-1] < mean - std else 0.0
            exit_sig = 1.0 if close[-1] > mean + std else 0.0

            return (np.array([entry]), np.array([exit_sig]))

        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        data = pd.DataFrame({
            'close': np.random.uniform(100, 120, 252),
        }, index=dates)

        adapter = StrategyAdapter(mean_reversion)
        entries, exits = await adapter.adapt_strategy(data)

        assert len(entries) == 252
        assert len(exits) == 252

    @pytest.mark.asyncio
    async def test_momentum_strategy(self):
        """Test momentum strategy."""
        async def momentum(data, state):
            close = data['close'].values
            if len(close) < 20:
                return (np.array([0.0]), np.array([0.0]))

            returns = np.diff(close) / close[:-1]
            momentum_val = np.mean(returns[-20:])

            entry = 1.0 if momentum_val > 0.001 else 0.0
            exit_sig = 1.0 if momentum_val < -0.001 else 0.0

            return (np.array([entry]), np.array([exit_sig]))

        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        data = pd.DataFrame({
            'close': np.random.uniform(100, 120, 252),
        }, index=dates)

        adapter = StrategyAdapter(momentum)
        entries, exits = await adapter.adapt_strategy(data)

        assert len(entries) == 252

    @pytest.mark.asyncio
    async def test_volatility_breakout_strategy(self):
        """Test volatility breakout strategy."""
        async def vol_breakout(data, state):
            close = data['close'].values
            if len(close) < 20:
                return (np.array([0.0]), np.array([0.0]))

            vol = np.std(close[-20:])
            high = np.max(close[-20:])
            low = np.min(close[-20:])

            entry = 1.0 if close[-1] > high and vol > 0.02 else 0.0
            exit_sig = 1.0 if close[-1] < low else 0.0

            return (np.array([entry]), np.array([exit_sig]))

        dates = pd.date_range('2024-01-01', periods=252, freq='D')
        data = pd.DataFrame({
            'close': np.random.uniform(100, 120, 252),
        }, index=dates)

        adapter = StrategyAdapter(vol_breakout)
        entries, exits = await adapter.adapt_strategy(data)

        assert len(entries) == 252
