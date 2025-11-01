"""
Calculation Layer Integration Tests

Tests the unified backtest engine, strategy executor, and related components.

Run with: pytest tests/test_calculation_layer.py -v -m calculation_layer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import (
    UnifiedBacktestEngine,
    BacktestConfig,
    StrategyExecutor,
    StrategyFactory,
)
from src.core.base_strategy import Signal, SignalType
from tests.fixtures import mock_ohlcv_data


class TestUnifiedBacktestEngine:
    """Test unified backtest engine."""

    @pytest.mark.calculation_layer
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = UnifiedBacktestEngine(mode="vectorized")
        assert engine.mode == "vectorized"
        assert engine.get_engine_name() == "unified_backtest_vectorized"

    @pytest.mark.calculation_layer
    def test_simple_buy_hold_strategy(self):
        """Test simple buy-and-hold strategy."""
        engine = UnifiedBacktestEngine(mode="vectorized")

        # Generate mock data
        data = mock_ohlcv_data("0700.HK", num_days=100)

        # Generate simple buy signal at start
        signals = pd.DataFrame({
            'Signal': [1] + [0] * 99
        }, index=data.index)

        config = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=100000.0,
        )

        result = engine.run(config, signals, data)

        assert 'equity_curve' in result
        assert 'trades' in result
        assert 'metrics' in result
        assert len(result['trades']) > 0

    @pytest.mark.calculation_layer
    def test_backtest_metrics_calculation(self):
        """Test metrics calculation."""
        engine = UnifiedBacktestEngine(mode="vectorized")

        data = mock_ohlcv_data("0700.HK", num_days=100)
        signals = pd.DataFrame({
            'Signal': np.random.choice([1, -1, 0], size=len(data), p=[0.2, 0.2, 0.6])
        }, index=data.index)

        config = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        result = engine.run(config, signals, data)
        metrics = result['metrics']

        # Verify metric properties
        assert -1 <= metrics.total_return <= 10  # Reasonable return range
        assert metrics.volatility >= 0
        assert metrics.max_drawdown <= 0
        assert metrics.sharpe_ratio is not None
        assert 0 <= metrics.win_rate <= 1

    @pytest.mark.calculation_layer
    def test_different_engine_modes(self):
        """Test different backtest engine modes."""
        data = mock_ohlcv_data("0700.HK", num_days=100)
        signals = pd.DataFrame({
            'Signal': [1] + [0] * 99
        }, index=data.index)

        config = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        for mode in ["vectorized", "traditional", "real_data", "alt_data"]:
            engine = UnifiedBacktestEngine(mode=mode)
            result = engine.run(config, signals, data)

            assert result is not None
            assert 'metrics' in result
            assert result['mode'] == mode

    @pytest.mark.calculation_layer
    def test_transaction_costs(self):
        """Test transaction cost impact."""
        data = mock_ohlcv_data("0700.HK", num_days=100)
        signals = pd.DataFrame({
            'Signal': [1] + [0] * 99
        }, index=data.index)

        # Run with no costs
        engine = UnifiedBacktestEngine()
        config_no_cost = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
            transaction_cost=0.0,
        )
        result_no_cost = engine.run(config_no_cost, signals, data)

        # Run with costs
        config_with_cost = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
            transaction_cost=0.001,  # 0.1%
        )
        result_with_cost = engine.run(config_with_cost, signals, data)

        # With costs should have lower return
        assert (result_with_cost['final_value'] <=
                result_no_cost['final_value'])


class TestStrategyExecutor:
    """Test strategy executor."""

    @pytest.mark.calculation_layer
    def test_executor_initialization(self):
        """Test executor initialization."""
        executor = StrategyExecutor(mode="backtest")
        assert executor.mode == "backtest"
        assert len(executor.strategies) == 0

    @pytest.mark.calculation_layer
    def test_strategy_registration(self):
        """Test registering strategies."""
        executor = StrategyExecutor()

        # Create mock strategy
        from tests.fixtures import MockStrategy

        strategy1 = MockStrategy(name="Strategy1")
        strategy2 = MockStrategy(name="Strategy2")

        executor.register_strategy("strat1", strategy1)
        executor.register_strategy("strat2", strategy2)

        assert len(executor.strategies) == 2
        assert "strat1" in executor.strategies
        assert "strat2" in executor.strategies

    @pytest.mark.calculation_layer
    def test_signal_generation(self):
        """Test signal generation from strategies."""
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        strategy = MockStrategy(name="TestStrategy")
        executor.register_strategy("test", strategy)

        data = mock_ohlcv_data("0700.HK", num_days=100)
        executor.initialize(data)

        signals = executor.generate_signals(data.iloc[-5:])

        assert signals is not None
        assert len(signals) > 0

    @pytest.mark.calculation_layer
    def test_signal_aggregation_voting(self):
        """Test voting aggregation method."""
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        # Create strategies that vote
        executor.register_strategy("bullish1", MockStrategy())
        executor.register_strategy("bullish2", MockStrategy())
        executor.register_strategy("bearish1", MockStrategy())

        data = mock_ohlcv_data("0700.HK", num_days=10)
        executor.initialize(data)

        # Manually create signals for testing
        signals = [
            Signal(symbol="0700.HK", timestamp=data.index[0], signal_type=SignalType.BUY,
                   confidence=0.8, reason="Test", price=100.0),
            Signal(symbol="0700.HK", timestamp=data.index[0], signal_type=SignalType.BUY,
                   confidence=0.7, reason="Test", price=100.0),
            Signal(symbol="0700.HK", timestamp=data.index[0], signal_type=SignalType.SELL,
                   confidence=0.6, reason="Test", price=100.0),
        ]

        aggregated = executor._aggregate_by_voting(signals)

        # Should vote BUY (2 vs 1)
        assert aggregated[0].signal_type == SignalType.BUY

    @pytest.mark.calculation_layer
    def test_signal_aggregation_weighted(self):
        """Test weighted aggregation method."""
        executor = StrategyExecutor()

        signals = [
            Signal(symbol="0700.HK", timestamp=datetime.now(), signal_type=SignalType.BUY,
                   confidence=0.9, reason="Test", price=100.0),
            Signal(symbol="0700.HK", timestamp=datetime.now(), signal_type=SignalType.SELL,
                   confidence=0.3, reason="Test", price=100.0),
        ]

        aggregated = executor._aggregate_by_weighted(signals)

        # Should vote BUY (0.9 vs 0.3)
        assert aggregated[0].signal_type == SignalType.BUY

    @pytest.mark.calculation_layer
    def test_signal_aggregation_consensus(self):
        """Test consensus aggregation method."""
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        # Register 5 strategies
        for i in range(5):
            executor.register_strategy(f"strat{i}", MockStrategy())

        signals = [
            Signal(symbol="0700.HK", timestamp=datetime.now(), signal_type=SignalType.BUY,
                   confidence=0.8, reason="Test", price=100.0)
            for _ in range(4)  # 4 out of 5 agree
        ] + [
            Signal(symbol="0700.HK", timestamp=datetime.now(), signal_type=SignalType.SELL,
                   confidence=0.6, reason="Test", price=100.0)
        ]

        aggregated = executor._aggregate_by_consensus(signals)

        # Should get BUY signal (4/5 = 80%)
        assert len(aggregated) > 0
        assert aggregated[0].signal_type == SignalType.BUY

    @pytest.mark.calculation_layer
    def test_strategy_performance_tracking(self):
        """Test strategy performance tracking."""
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        executor.register_strategy("strat1", MockStrategy())

        data = mock_ohlcv_data("0700.HK", num_days=100)
        executor.initialize(data)

        # Generate signals multiple times
        for i in range(5):
            executor.generate_signals(data.iloc[i:i+10])

        performance = executor.get_strategy_performance()

        assert "strat1" in performance
        assert performance["strat1"]["signals_generated"] > 0

    @pytest.mark.calculation_layer
    def test_signal_history_retrieval(self):
        """Test signal history retrieval."""
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        executor.register_strategy("strat1", MockStrategy())

        data = mock_ohlcv_data("0700.HK", num_days=100)
        executor.initialize(data)

        executor.generate_signals(data.iloc[-10:])

        history = executor.get_signal_history(symbol="0700.HK")
        assert len(history) > 0

        # Get summary
        summary = executor.get_summary()
        assert summary["strategies_registered"] == 1
        assert summary["total_signals"] > 0


class TestStrategyFactory:
    """Test strategy factory."""

    @pytest.mark.calculation_layer
    def test_factory_registration(self):
        """Test factory registration."""
        from tests.fixtures import MockStrategy

        # Register a mock strategy
        StrategyFactory.register("mock_strategy", MockStrategy)

        # Create instance
        strategy = StrategyFactory.create("mock_strategy")
        assert strategy is not None

    @pytest.mark.calculation_layer
    def test_factory_list_available(self):
        """Test listing available strategies."""
        StrategyFactory.register("test_strategy", type("TestStrat", (), {}))

        available = StrategyFactory.list_available()
        assert "test_strategy" in available


class TestEndToEndCalculationLayer:
    """End-to-end calculation layer tests."""

    @pytest.mark.calculation_layer
    def test_full_calculation_pipeline(self):
        """Test complete calculation layer workflow."""
        # Initialize components
        engine = UnifiedBacktestEngine(mode="vectorized")
        executor = StrategyExecutor()

        from tests.fixtures import MockStrategy

        executor.register_strategy("strategy1", MockStrategy())
        executor.register_strategy("strategy2", MockStrategy())

        # Get data
        data = mock_ohlcv_data("0700.HK", num_days=100)

        # Initialize strategies
        executor.initialize(data)

        # Generate signals
        signals_df = pd.DataFrame({
            'Signal': np.random.choice([1, -1, 0], size=len(data), p=[0.3, 0.2, 0.5])
        }, index=data.index)

        # Run backtest
        config = BacktestConfig(
            symbol="0700.HK",
            start_date=data.index[0],
            end_date=data.index[-1],
            engine="vectorized",
        )

        result = engine.run(config, signals_df, data)

        # Verify results
        assert "metrics" in result
        assert result["final_value"] > 0
        assert result["metrics"].total_return is not None

        # Check executor performance
        perf = executor.get_strategy_performance()
        assert len(perf) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "calculation_layer"])
