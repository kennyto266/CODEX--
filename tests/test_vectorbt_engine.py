"""
Tests for Vectorbt Backtest Engine

Test Coverage:
- Engine initialization and configuration
- Data loading and preprocessing
- Signal generation (vectorized)
- Portfolio simulation
- Metrics extraction
- Trade recording
- Performance benchmarks
- Backward compatibility
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timezone
from pathlib import Path
import tempfile

from src.backtest.vectorbt_engine import VectorbtBacktestEngine, VECTORBT_AVAILABLE
from src.backtest.base_backtest import BacktestConfig, BacktestStatus
from src.data_pipeline.data_manager import DataManager


@pytest.mark.skipif(not VECTORBT_AVAILABLE, reason="vectorbt not installed")
class TestVectorbtEngineInitialization:
    """Test engine initialization."""

    def test_engine_creation(self):
        """Test creating engine instance."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            assert engine.config == config
            assert engine.status == BacktestStatus.PENDING
            assert len(engine.ohlcv_data) == 0

            manager.close()

    def test_engine_initialization_without_data(self):
        """Test initialization without loading data."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            assert engine.config.strategy_name == "TestStrategy"
            assert engine.config.initial_capital == 100000

            manager.close()


@pytest.mark.skipif(not VECTORBT_AVAILABLE, reason="vectorbt not installed")
class TestVectorbtSignalGeneration:
    """Test signal generation."""

    def test_signal_array_conversion(self):
        """Test converting signals to entry/exit arrays."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            # Mock OHLCV data
            dates = pd.date_range('2024-01-01', periods=100, freq='D')
            ohlcv = pd.DataFrame({
                'open': np.random.uniform(100, 120, 100),
                'high': np.random.uniform(120, 130, 100),
                'low': np.random.uniform(90, 100, 100),
                'close': np.random.uniform(100, 120, 100),
                'volume': np.random.randint(1000000, 10000000, 100),
            }, index=dates)

            engine.ohlcv_data['0700.hk'] = ohlcv
            engine.close_prices['0700.hk'] = ohlcv['close'].values

            # Test signal generation
            async def simple_strategy(data):
                entries = np.zeros(len(data), dtype=float)
                exits = np.zeros(len(data), dtype=float)
                # Buy on day 10, sell on day 20
                entries[10] = 1.0
                exits[20] = 1.0
                return entries, exits

            # Run signal generation
            import asyncio
            entries, exits = asyncio.run(engine._generate_signals_vectorized(simple_strategy))

            assert len(entries) == 100
            assert len(exits) == 100
            assert np.sum(entries) == 1.0
            assert np.sum(exits) == 1.0

            manager.close()

    def test_signal_from_series(self):
        """Test signal conversion from pandas Series."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            # Mock OHLCV data
            dates = pd.date_range('2024-01-01', periods=100, freq='D')
            ohlcv = pd.DataFrame({
                'open': np.random.uniform(100, 120, 100),
                'high': np.random.uniform(120, 130, 100),
                'low': np.random.uniform(90, 100, 100),
                'close': np.random.uniform(100, 120, 100),
                'volume': np.random.randint(1000000, 10000000, 100),
            }, index=dates)

            engine.ohlcv_data['0700.hk'] = ohlcv
            engine.close_prices['0700.hk'] = ohlcv['close'].values

            # Strategy returning Series
            async def series_strategy(data):
                signals = pd.Series(0, index=range(len(data)))
                signals.iloc[10] = 1  # Buy signal
                signals.iloc[20] = -1  # Sell signal
                return signals

            import asyncio
            entries, exits = asyncio.run(engine._generate_signals_vectorized(series_strategy))

            assert len(entries) == 100
            assert len(exits) == 100
            assert entries[10] == 1.0
            assert exits[20] == 1.0

            manager.close()


@pytest.mark.skipif(not VECTORBT_AVAILABLE, reason="vectorbt not installed")
class TestVectorbtMetrics:
    """Test metrics extraction."""

    def test_metrics_extraction(self):
        """Test extracting metrics from portfolio."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            # Mock closing prices and signals
            np.random.seed(42)
            close_prices = np.random.uniform(100, 120, 252)  # 1 year of trading

            # Simple buy and hold strategy
            entries = np.zeros(252)
            exits = np.zeros(252)
            entries[0] = 1.0  # Buy on first day

            # Create portfolio
            import vectorbt as vbt
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=entries,
                exits=exits,
                init_cash=config.initial_capital,
                fees=0.001,
                freq='d'
            )

            engine.portfolio = portfolio
            import asyncio
            asyncio.run(engine._extract_metrics())

            assert 'total_return' in engine.metrics
            assert 'sharpe_ratio' in engine.metrics
            assert 'max_drawdown' in engine.metrics
            assert len(engine.portfolio_values) == 252
            assert isinstance(engine.metrics['total_return'], float)

            manager.close()

    def test_trade_record_extraction(self):
        """Test extracting trade records."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)
            engine = VectorbtBacktestEngine(config, data_manager=manager)

            # Mock data with dates
            dates = pd.date_range('2024-01-01', periods=252, freq='D')
            close_prices = np.random.uniform(100, 120, 252)

            # Create some trades
            entries = np.zeros(252)
            exits = np.zeros(252)
            entries[10] = 1.0
            exits[30] = 1.0

            import vectorbt as vbt
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=entries,
                exits=exits,
                init_cash=config.initial_capital,
                fees=0.001,
                freq='d'
            )

            engine.portfolio = portfolio
            engine.ohlcv_data['0700.hk'] = pd.DataFrame({'close': close_prices}, index=dates)

            engine._extract_trades()

            assert len(engine.trade_records) > 0
            for trade in engine.trade_records:
                assert 'symbol' in trade
                assert 'entry_price' in trade
                assert 'pnl' in trade

            manager.close()


@pytest.mark.skipif(not VECTORBT_AVAILABLE, reason="vectorbt not installed")
class TestVectorbtBacktest:
    """Test complete backtest execution."""

    def test_backtest_run(self):
        """Test running a complete backtest."""
        config = BacktestConfig(
            strategy_name="SimpleMomentum",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)

            # Prepare test data
            dates = pd.date_range('2024-01-01', periods=252, freq='D')
            test_data = pd.DataFrame({
                'open': np.random.uniform(100, 120, 252),
                'high': np.random.uniform(120, 130, 252),
                'low': np.random.uniform(90, 100, 252),
                'close': np.random.uniform(100, 120, 252),
                'volume': np.random.randint(1000000, 10000000, 252),
            }, index=dates)

            manager.save_data('0700.hk', test_data)

            engine = VectorbtBacktestEngine(config, data_manager=manager)

            import asyncio

            # Initialize
            success = asyncio.run(engine.initialize())
            assert success
            assert len(engine.ohlcv_data) > 0

            # Define simple strategy
            async def momentum_strategy(data):
                close = data['close'].values
                # Simple momentum: buy if close increases
                momentum = np.diff(close, prepend=close[0])
                entries = (momentum > 0).astype(float)
                exits = (momentum < 0).astype(float)
                entries = np.roll(entries, 1)  # Shift to avoid look-ahead
                return entries, exits

            # Run backtest
            result = asyncio.run(engine.run_backtest(momentum_strategy))

            assert result.strategy_name == "SimpleMomentum"
            assert result.initial_capital == 100000
            assert result.final_capital > 0
            assert len(result.portfolio_values) > 0
            assert result.sharpe_ratio is not None or isinstance(result.sharpe_ratio, (int, float))

            manager.close()

    def test_backtest_result_format(self):
        """Test backtest result format."""
        config = BacktestConfig(
            strategy_name="TestStrategy",
            symbols=["0700.hk"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)

            # Prepare test data
            dates = pd.date_range('2024-01-01', periods=100, freq='D')
            test_data = pd.DataFrame({
                'open': np.full(100, 100.0),
                'high': np.full(100, 110.0),
                'low': np.full(100, 90.0),
                'close': np.full(100, 100.0),
                'volume': np.full(100, 1000000),
            }, index=dates)

            manager.save_data('0700.hk', test_data)

            engine = VectorbtBacktestEngine(config, data_manager=manager)

            import asyncio

            asyncio.run(engine.initialize())

            async def no_trade_strategy(data):
                return np.zeros(len(data)), np.zeros(len(data))

            result = asyncio.run(engine.run_backtest(no_trade_strategy))

            assert result.strategy_name == "TestStrategy"
            assert result.start_date == date(2024, 1, 1)
            assert result.end_date == date(2024, 12, 31)
            assert result.initial_capital == 100000
            assert result.total_return == pytest.approx(0.0, abs=0.01)
            assert isinstance(result.metrics, dict)
            assert isinstance(result.trades, list)
            assert isinstance(result.portfolio_values, list)

            manager.close()


@pytest.mark.skipif(not VECTORBT_AVAILABLE, reason="vectorbt not installed")
class TestVectorbtPerformance:
    """Test performance characteristics."""

    def test_execution_speed(self):
        """Test backtest execution speed."""
        config = BacktestConfig(
            strategy_name="Speed Test",
            symbols=["0700.hk"],
            start_date=date(2020, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)

            # Create large dataset (5 years)
            dates = pd.date_range('2020-01-01', periods=1260, freq='D')  # ~5 years
            np.random.seed(42)
            test_data = pd.DataFrame({
                'open': np.random.uniform(100, 120, 1260),
                'high': np.random.uniform(120, 130, 1260),
                'low': np.random.uniform(90, 100, 1260),
                'close': np.random.uniform(100, 120, 1260),
                'volume': np.random.randint(1000000, 10000000, 1260),
            }, index=dates)

            manager.save_data('0700.hk', test_data)

            engine = VectorbtBacktestEngine(config, data_manager=manager)

            import asyncio
            import time

            asyncio.run(engine.initialize())

            async def simple_strategy(data):
                close = data['close'].values
                sma20 = pd.Series(close).rolling(20).mean().values
                entries = (close > sma20).astype(float)
                exits = (close < sma20).astype(float)
                entries = np.roll(entries, 1)
                return entries, exits

            # Time the backtest
            start = time.time()
            result = asyncio.run(engine.run_backtest(simple_strategy))
            elapsed = time.time() - start

            assert elapsed < 1.0  # Should complete in < 1 second
            assert result.total_return is not None
            assert result.sharpe_ratio is not None

            manager.close()

    def test_memory_efficiency(self):
        """Test memory efficiency with large dataset."""
        config = BacktestConfig(
            strategy_name="Memory Test",
            symbols=["0700.hk"],
            start_date=date(2020, 1, 1),
            end_date=date(2024, 12, 31),
            initial_capital=100000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_url = f'sqlite:///{tmpdir}/test.db'
            manager = DataManager(database_url=db_url, enable_pipeline=False)

            # Create dataset
            dates = pd.date_range('2020-01-01', periods=1260, freq='D')
            np.random.seed(42)
            test_data = pd.DataFrame({
                'open': np.random.uniform(100, 120, 1260),
                'high': np.random.uniform(120, 130, 1260),
                'low': np.random.uniform(90, 100, 1260),
                'close': np.random.uniform(100, 120, 1260),
                'volume': np.random.randint(1000000, 10000000, 1260),
            }, index=dates)

            manager.save_data('0700.hk', test_data)

            engine = VectorbtBacktestEngine(config, data_manager=manager)

            import asyncio
            import sys

            asyncio.run(engine.initialize())

            # Check memory usage
            portfolio_values_size = sys.getsizeof(engine.portfolio_values)
            ohlcv_data_size = sum(sys.getsizeof(df) for df in engine.ohlcv_data.values())

            # Should be memory efficient
            assert ohlcv_data_size < 100_000_000  # < 100MB for 5 years

            manager.close()
