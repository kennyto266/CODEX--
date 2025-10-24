"""
Tests for Strategy Adapter Layer

Test Coverage:
- Signal format normalization
- Async strategy adaptation
- Legacy strategy support
- Multiple signal format handling
- Error handling and validation
- Strategy factory
"""

import pytest
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime

from src.backtest.strategy_adapter import (
    SignalNormalizer,
    StrategyAdapter,
    LegacyStrategyWrapper,
    StrategyFactory,
    get_strategy_factory,
    register_strategy,
    register_legacy_strategy,
    SignalFormat
)


class TestSignalNormalizer:
    """Test signal normalization."""

    def test_normalize_tuple_format(self):
        """Test normalizing tuple (entries, exits) format."""
        entries = [1, 0, 1, 0, 0]
        exits = [0, 1, 0, 1, 0]

        norm_entries, norm_exits = SignalNormalizer.normalize((entries, exits))

        assert len(norm_entries) == 5
        assert len(norm_exits) == 5
        assert np.array_equal(norm_entries, np.array([1, 0, 1, 0, 0], dtype=float))

    def test_normalize_series_format(self):
        """Test normalizing pandas Series format (buy/sell)."""
        signals = pd.Series([1, 0, -1, 0, 1, -1, 0])  # 1=buy, -1=sell, 0=hold

        entries, exits = SignalNormalizer.normalize(signals)

        assert len(entries) == 7
        assert len(exits) == 7
        assert entries[0] == 1.0  # Buy signal
        assert exits[2] == 1.0    # Sell signal

    def test_normalize_numpy_array_2d(self):
        """Test normalizing 2D numpy array."""
        signals = np.array([
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1]
        ], dtype=float)

        entries, exits = SignalNormalizer.normalize(signals)

        assert len(entries) == 4
        assert len(exits) == 4
        assert entries[0] == 1.0
        assert exits[1] == 1.0

    def test_normalize_dict_format(self):
        """Test normalizing dictionary format."""
        signals = {
            'entries': [1, 0, 1, 0],
            'exits': [0, 1, 0, 1]
        }

        entries, exits = SignalNormalizer.normalize(signals)

        assert len(entries) == 4
        assert len(exits) == 4

    def test_normalize_position_to_signals(self):
        """Test converting continuous positions to entry/exit."""
        positions = np.array([0, 1, 1, 0, -1, -1, 0])  # Long, flat, short, flat

        entries, exits = SignalNormalizer._position_to_signals(positions)

        assert entries[1] == 1.0  # Entry at position 1
        assert exits[3] == 1.0    # Exit at position 3
        assert entries[4] == 1.0  # Entry short at position 4
        assert exits[6] == 1.0    # Exit short at position 6

    def test_validate_signals(self):
        """Test signal validation."""
        entries = np.array([1, 0, 1, 0], dtype=float)
        exits = np.array([0, 1, 0, 1], dtype=float)

        # Should not raise
        assert SignalNormalizer.validate_signals(entries, exits) is True

    def test_validate_signals_length_mismatch(self):
        """Test validation with length mismatch."""
        entries = np.array([1, 0, 1], dtype=float)
        exits = np.array([0, 1, 0, 1], dtype=float)

        with pytest.raises(ValueError):
            SignalNormalizer.validate_signals(entries, exits)

    def test_validate_signals_min_length(self):
        """Test validation with minimum length requirement."""
        entries = np.array([1, 0, 1], dtype=float)
        exits = np.array([0, 1, 0], dtype=float)

        with pytest.raises(ValueError):
            SignalNormalizer.validate_signals(entries, exits, min_length=10)


class TestStrategyAdapter:
    """Test strategy adaptation."""

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'open': np.random.uniform(100, 120, 100),
            'high': np.random.uniform(120, 130, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 120, 100),
            'volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        async def dummy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        adapter = StrategyAdapter(dummy_strategy)

        assert adapter.strategy_func is not None
        assert adapter.is_async is True

    def test_adapter_sync_strategy(self):
        """Test adapter with sync strategy."""
        def sync_strategy(data, state):
            return (np.ones(len(data)), np.zeros(len(data)))

        adapter = StrategyAdapter(sync_strategy)
        assert adapter.is_async is False

    @pytest.mark.asyncio
    async def test_adapt_simple_strategy(self, sample_ohlcv):
        """Test adapting a simple async strategy."""
        async def simple_strategy(data, state):
            # Buy on day 10, sell on day 20
            entries = np.zeros(len(data))
            exits = np.zeros(len(data))
            if len(data) >= 10:
                entries[-1] = 1.0
            if len(data) >= 20:
                exits[-1] = 1.0
            return entries, exits

        adapter = StrategyAdapter(simple_strategy)
        entries, exits = await adapter.adapt_strategy(sample_ohlcv)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_adapt_series_signal_strategy(self, sample_ohlcv):
        """Test adapting strategy that returns Series signals."""
        async def series_strategy(data, state):
            close = data['close'].values
            sma20 = pd.Series(close).rolling(20).mean().values
            signals = np.where(close > sma20, 1, np.where(close < sma20, -1, 0))
            return pd.Series(signals)

        adapter = StrategyAdapter(series_strategy)
        entries, exits = await adapter.adapt_strategy(sample_ohlcv)

        assert len(entries) == 100
        assert len(exits) == 100
        assert np.sum(entries) > 0 or np.sum(exits) > 0

    @pytest.mark.asyncio
    async def test_adapt_with_state(self, sample_ohlcv):
        """Test strategy adaptation with state management."""
        async def stateful_strategy(data, state):
            # Track position in state
            if len(data) == 10:
                state['entered'] = True
                entries = np.zeros(len(data))
                entries[-1] = 1.0
                return (entries, np.zeros(len(data)))
            elif len(data) == 20 and state.get('entered'):
                exits = np.zeros(len(data))
                exits[-1] = 1.0
                state['entered'] = False
                return (np.zeros(len(data)), exits)
            return (np.zeros(len(data)), np.zeros(len(data)))

        adapter = StrategyAdapter(stateful_strategy)
        initial_state = {'entered': False}
        entries, exits = await adapter.adapt_strategy(sample_ohlcv, initial_state)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_adapt_empty_data(self):
        """Test adapter with empty data."""
        async def dummy_strategy(data, state):
            return (np.array([]), np.array([]))

        adapter = StrategyAdapter(dummy_strategy)

        with pytest.raises(ValueError):
            await adapter.adapt_strategy(pd.DataFrame())


class TestLegacyStrategyWrapper:
    """Test legacy strategy wrapping."""

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'open': np.full(100, 100.0),
            'high': np.full(100, 110.0),
            'low': np.full(100, 90.0),
            'close': np.full(100, 100.0),
            'volume': np.full(100, 1000000),
        }, index=dates)

    def test_wrapper_initialization(self):
        """Test wrapper initialization."""
        async def legacy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        wrapper = LegacyStrategyWrapper(legacy_strategy, params={'threshold': 0.5})

        assert wrapper.legacy_strategy is not None
        assert wrapper.params['threshold'] == 0.5

    @pytest.mark.asyncio
    async def test_wrapper_generate_signals(self, sample_ohlcv):
        """Test generating signals from wrapped strategy."""
        async def legacy_strategy(data, state):
            # Strategy receives incrementally growing data
            # Only return signal at end of current bar
            if len(data) == 10:
                return (np.array([1.0]), np.array([0.0]))
            elif len(data) == 20:
                return (np.array([0.0]), np.array([1.0]))
            else:
                return (np.array([0.0]), np.array([0.0]))

        wrapper = LegacyStrategyWrapper(legacy_strategy)
        entries, exits = await wrapper.generate_signals(sample_ohlcv)

        assert len(entries) == 100
        assert len(exits) == 100

    @pytest.mark.asyncio
    async def test_wrapper_with_custom_params(self, sample_ohlcv):
        """Test wrapper with custom parameters."""
        async def parameterized_strategy(data, state):
            # Strategy behavior depends on parameters
            entries = np.zeros(len(data))
            exits = np.zeros(len(data))
            return (entries, exits)

        wrapper = LegacyStrategyWrapper(parameterized_strategy, params={'rsi_period': 14})

        custom_params = {'rsi_period': 21}
        entries, exits = await wrapper.generate_signals_with_params(sample_ohlcv, custom_params)

        assert len(entries) == 100


class TestStrategyFactory:
    """Test strategy factory."""

    def test_factory_initialization(self):
        """Test factory initialization."""
        factory = StrategyFactory()

        assert len(factory.strategies) == 0
        assert len(factory.adapters) == 0

    def test_register_strategy(self):
        """Test registering a strategy."""
        factory = StrategyFactory()

        def dummy_strategy(data):
            return (np.zeros(len(data)), np.zeros(len(data)))

        factory.register_strategy("test_strategy", dummy_strategy)

        assert "test_strategy" in factory.list_strategies()

    def test_register_legacy_strategy(self):
        """Test registering a legacy async strategy."""
        factory = StrategyFactory()

        async def legacy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        factory.register_legacy_strategy("legacy_strategy", legacy_strategy)

        assert "legacy_strategy" in factory.list_strategies()
        assert factory.get_adapter("legacy_strategy") is not None

    def test_get_strategy(self):
        """Test retrieving registered strategy."""
        factory = StrategyFactory()

        def dummy_strategy(data):
            return (np.zeros(len(data)), np.zeros(len(data)))

        factory.register_strategy("test", dummy_strategy)
        retrieved = factory.get_strategy("test")

        assert retrieved is dummy_strategy

    def test_get_nonexistent_strategy(self):
        """Test retrieving non-existent strategy."""
        factory = StrategyFactory()
        retrieved = factory.get_strategy("nonexistent")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_factory_generate_signals(self):
        """Test generating signals from factory."""
        factory = StrategyFactory()

        async def test_strategy(data, state):
            # Return signal for current bar (single element)
            if len(data) == 10:
                return (np.array([1.0]), np.array([0.0]))
            elif len(data) == 20:
                return (np.array([0.0]), np.array([1.0]))
            else:
                return (np.array([0.0]), np.array([0.0]))

        factory.register_legacy_strategy("test_strategy", test_strategy)

        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        ohlcv = pd.DataFrame({
            'close': np.full(50, 100.0),
        }, index=dates)

        entries, exits = await factory.generate_signals("test_strategy", ohlcv)

        assert len(entries) == 50
        assert len(exits) == 50


class TestGlobalFactory:
    """Test global strategy factory."""

    def test_get_global_factory(self):
        """Test getting global factory instance."""
        factory = get_strategy_factory()

        assert factory is not None
        assert isinstance(factory, StrategyFactory)

    def test_register_with_global_factory(self):
        """Test registering with global factory."""
        async def global_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        register_legacy_strategy("global_test", global_strategy)

        factory = get_strategy_factory()
        assert "global_test" in factory.list_strategies()

    def test_register_multiple_strategies(self):
        """Test registering multiple strategies."""
        async def strategy1(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        async def strategy2(data, state):
            return (np.ones(len(data)), np.zeros(len(data)))

        register_legacy_strategy("strategy1", strategy1)
        register_legacy_strategy("strategy2", strategy2)

        factory = get_strategy_factory()
        strategies = factory.list_strategies()

        assert "strategy1" in strategies
        assert "strategy2" in strategies


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_adapter_with_real_strategy(self):
        """Test adapter with realistic strategy."""
        # Simulated RSI-based strategy
        async def rsi_strategy(data, state):
            close = data['close'].values
            if len(close) < 14:
                return (np.zeros(len(close)), np.zeros(len(close)))

            # Calculate RSI
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)

            avg_gain = pd.Series(gain).rolling(14).mean().values
            avg_loss = pd.Series(loss).rolling(14).mean().values

            rs = avg_gain / (avg_loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))

            # Generate signals
            entries = (rsi[-len(rsi):] < 30).astype(float)
            exits = (rsi[-len(rsi):] > 70).astype(float)

            return (entries, exits)

        adapter = StrategyAdapter(rsi_strategy)

        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        ohlcv = pd.DataFrame({
            'open': np.random.uniform(100, 120, 100),
            'high': np.random.uniform(120, 130, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 120, 100),
            'volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)

        entries, exits = await adapter.adapt_strategy(ohlcv)

        assert len(entries) == 100
        assert len(exits) == 100
        assert np.sum(entries) >= 0
        assert np.sum(exits) >= 0

    @pytest.mark.asyncio
    async def test_multiple_format_compatibility(self):
        """Test adapter with different signal formats."""
        formats_to_test = []

        # Tuple format
        async def tuple_strategy(data, state):
            return (
                np.random.choice([0, 1], len(data)),
                np.random.choice([0, 1], len(data))
            )
        formats_to_test.append(("tuple", tuple_strategy))

        # Series format
        async def series_strategy(data, state):
            return pd.Series(np.random.choice([0, 1, -1], len(data)))
        formats_to_test.append(("series", series_strategy))

        # Array format
        async def array_strategy(data, state):
            return np.random.choice([0, 1], (len(data), 2))
        formats_to_test.append(("array", array_strategy))

        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        ohlcv = pd.DataFrame({
            'close': np.full(50, 100.0),
        }, index=dates)

        for format_name, strategy in formats_to_test:
            adapter = StrategyAdapter(strategy)
            entries, exits = await adapter.adapt_strategy(ohlcv)

            assert len(entries) == 50
            assert len(exits) == 50
            print(f"✓ {format_name} format test passed")
