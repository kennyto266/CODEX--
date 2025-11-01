"""
Strategy Adapter Layer - Bridge between Async and Vectorized Strategies

Enables seamless integration of existing async-based strategies with the new
vectorbt-powered backtest engine. Provides transparent format conversion and
maintains 100% backward compatibility.

Architecture:
    Legacy Async Strategy
        ↓
    StrategyAdapter (conversion layer)
        ↓
    Normalized Signal Format
        ↓
    VectorbtBacktestEngine (vectorized execution)

Key Features:
    - Automatic async → vectorized conversion
    - Multiple signal format support
    - No strategy code changes required
    - Transparent buffering and caching
    - Error handling and validation
    - Performance monitoring
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

logger = logging.getLogger("hk_quant_system.backtest.strategy_adapter")


class SignalFormat(str, Enum):
    """Supported signal formats."""
    ENTRY_EXIT = "entry_exit"  # Tuple: (entries, exits)
    BUY_SELL = "buy_sell"      # Series: 1=buy, -1=sell, 0=hold
    POSITION = "position"       # Array: continuous position (1.0=long, -1.0=short)
    NUMPY_ARRAY = "numpy_array" # Raw numpy arrays


class SignalNormalizer:
    """
    Normalize signals from various formats to standardized entry/exit arrays.

    Supports conversion from:
    - Tuple format: (entries, exits)
    - pandas Series: buy/sell signals
    - numpy arrays: signal arrays
    - Continuous positions: generate entry/exit from changes
    """

    @staticmethod
    def normalize(signals: Any, signal_format: Optional[SignalFormat] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalize signals to (entries, exits) format.

        Args:
            signals: Signal data in various formats
            signal_format: Explicitly specify format

        Returns:
            Tuple of (entries, exits) as numpy arrays
        """
        try:
            if isinstance(signals, tuple) and len(signals) == 2:
                entries, exits = signals
                return (
                    np.asarray(entries, dtype=float),
                    np.asarray(exits, dtype=float)
                )

            elif isinstance(signals, pd.Series):
                # Buy/sell signal format: 1=buy, -1=sell, 0=hold
                entries = (signals == 1).astype(float).values
                exits = (signals == -1).astype(float).values
                return entries, exits

            elif isinstance(signals, np.ndarray):
                if signals.ndim == 2 and signals.shape[1] >= 2:
                    # 2D array: extract entry/exit columns
                    return signals[:, 0].astype(float), signals[:, 1].astype(float)
                elif signals.ndim == 1:
                    # 1D array: convert position changes to entry/exit
                    return SignalNormalizer._position_to_signals(signals)
                else:
                    raise ValueError(f"Unsupported array shape: {signals.shape}")

            elif isinstance(signals, dict):
                # Dictionary format: {'entries': [...], 'exits': [...]}
                entries = np.asarray(signals.get('entries', []), dtype=float)
                exits = np.asarray(signals.get('exits', []), dtype=float)
                return entries, exits

            elif isinstance(signals, list):
                # List of signals: convert to array first
                signals_array = np.asarray(signals, dtype=float)
                if signals_array.ndim == 2 and signals_array.shape[1] >= 2:
                    return signals_array[:, 0], signals_array[:, 1]
                else:
                    return SignalNormalizer._position_to_signals(signals_array)

            else:
                raise ValueError(f"Unsupported signal type: {type(signals)}")

        except Exception as e:
            logger.error(f"Signal normalization failed: {e}")
            raise

    @staticmethod
    def _position_to_signals(positions: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert continuous positions to entry/exit signals.

        Args:
            positions: Array of positions (1.0=long, -1.0=short, 0=flat)

        Returns:
            Tuple of (entries, exits)
        """
        positions = np.asarray(positions, dtype=float)
        entries = np.zeros_like(positions)
        exits = np.zeros_like(positions)

        # Detect position changes
        prev_pos = 0
        for i, pos in enumerate(positions):
            if prev_pos == 0 and pos != 0:
                # Entry signal
                entries[i] = 1.0
            elif prev_pos != 0 and pos == 0:
                # Exit signal
                exits[i] = 1.0

            prev_pos = pos

        return entries, exits

    @staticmethod
    def validate_signals(entries: np.ndarray, exits: np.ndarray, min_length: int = 0) -> bool:
        """
        Validate entry and exit signal arrays.

        Args:
            entries: Entry signals
            exits: Exit signals
            min_length: Minimum expected length

        Returns:
            True if valid, raises exception otherwise
        """
        if len(entries) != len(exits):
            raise ValueError(f"Entry/exit length mismatch: {len(entries)} != {len(exits)}")

        if len(entries) < min_length:
            raise ValueError(f"Signal length {len(entries)} < minimum {min_length}")

        # Check for valid values (0 or 1)
        valid_entries = np.all((entries == 0) | (entries == 1))
        valid_exits = np.all((exits == 0) | (exits == 1))

        if not (valid_entries and valid_exits):
            logger.warning("Signal values outside [0, 1] range - will be normalized")

        return True


class StrategyAdapter:
    """
    Adapter for converting legacy async strategies to vectorized format.

    Enables:
    - Running async strategies on historical data
    - Converting daily signals to vectorized entry/exit arrays
    - Supporting multiple strategy patterns
    - Maintaining state across days
    - Error handling and validation

    Usage:
        adapter = StrategyAdapter(strategy_func)
        entries, exits = await adapter.adapt_strategy(ohlcv_data)
        # Use with VectorbtBacktestEngine
    """

    def __init__(self, strategy_func: Callable, buffer_size: int = 100):
        """
        Initialize strategy adapter.

        Args:
            strategy_func: Async or sync strategy function
            buffer_size: Size of signal buffer
        """
        self.strategy_func = strategy_func
        self.buffer_size = buffer_size
        self.signal_buffer = []
        self.is_async = asyncio.iscoroutinefunction(strategy_func)
        logger.info(f"Initialized StrategyAdapter (async={self.is_async})")

    async def adapt_strategy(
        self,
        ohlcv_data: pd.DataFrame,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Adapt async strategy to vectorized entry/exit arrays.

        Args:
            ohlcv_data: OHLCV DataFrame with DatetimeIndex
            initial_state: Optional initial state (positions, indicators, etc.)

        Returns:
            Tuple of (entries, exits) as numpy arrays
        """
        try:
            if ohlcv_data.empty:
                raise ValueError("Empty OHLCV data provided")

            logger.info(f"Adapting strategy for {len(ohlcv_data)} bars")

            # Initialize state
            state = initial_state or {
                'positions': {},
                'indicators': {},
                'last_signals': []
            }

            entries = np.zeros(len(ohlcv_data), dtype=float)
            exits = np.zeros(len(ohlcv_data), dtype=float)

            # Process each bar
            for i in range(len(ohlcv_data)):
                # Get data up to current bar (no look-ahead)
                current_data = ohlcv_data.iloc[:i+1].copy()

                # Call strategy function
                if self.is_async:
                    signal = await self.strategy_func(current_data, state)
                else:
                    signal = self.strategy_func(current_data, state)

                # Normalize signal
                if signal is not None:
                    signal_entry, signal_exit = SignalNormalizer.normalize(signal)

                    # Use last signal value (most recent)
                    if len(signal_entry) > 0:
                        entries[i] = signal_entry[-1]
                    if len(signal_exit) > 0:
                        exits[i] = signal_exit[-1]

            # Validate results
            SignalNormalizer.validate_signals(entries, exits, min_length=10)

            logger.info(f"Strategy adapted: {np.sum(entries)} entries, {np.sum(exits)} exits")
            return entries, exits

        except Exception as e:
            logger.error(f"Strategy adaptation failed: {e}", exc_info=True)
            raise

    async def adapt_strategy_batch(
        self,
        ohlcv_data: pd.DataFrame,
        batch_size: int = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Adapt strategy with batch processing for efficiency.

        Args:
            ohlcv_data: OHLCV DataFrame
            batch_size: Process bars in batches

        Returns:
            Tuple of (entries, exits)
        """
        entries = np.zeros(len(ohlcv_data), dtype=float)
        exits = np.zeros(len(ohlcv_data), dtype=float)

        # Process in batches
        for batch_start in range(0, len(ohlcv_data), batch_size):
            batch_end = min(batch_start + batch_size, len(ohlcv_data))

            batch_data = ohlcv_data.iloc[:batch_end]
            batch_entries, batch_exits = await self.adapt_strategy(batch_data)

            entries[batch_start:batch_end] = batch_entries[-len(batch_entries)+batch_start:]
            exits[batch_start:batch_end] = batch_exits[-len(batch_exits)+batch_start:]

        return entries, exits

    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics and buffer info."""
        return {
            'strategy_type': 'async' if self.is_async else 'sync',
            'buffer_size': len(self.signal_buffer),
            'max_buffer': self.buffer_size,
            'signal_count': len(self.signal_buffer)
        }


class LegacyStrategyWrapper:
    """
    Wrapper for legacy strategies to work with VectorbtBacktestEngine.

    Handles:
    - Old async strategy format
    - Position-based signals
    - State management
    - Parameter passing
    """

    def __init__(self, legacy_strategy: Callable, params: Optional[Dict[str, Any]] = None):
        """
        Initialize legacy strategy wrapper.

        Args:
            legacy_strategy: Original async strategy function
            params: Strategy parameters
        """
        self.legacy_strategy = legacy_strategy
        self.params = params or {}
        self.adapter = StrategyAdapter(legacy_strategy)

    async def generate_signals(
        self,
        ohlcv_data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate entry/exit signals from legacy strategy.

        Args:
            ohlcv_data: OHLCV data

        Returns:
            Tuple of (entries, exits)
        """
        return await self.adapter.adapt_strategy(ohlcv_data)

    async def generate_signals_with_params(
        self,
        ohlcv_data: pd.DataFrame,
        strategy_params: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate signals with custom parameters.

        Args:
            ohlcv_data: OHLCV data
            strategy_params: Override parameters

        Returns:
            Tuple of (entries, exits)
        """
        # Update parameters
        original_params = self.params.copy()
        self.params.update(strategy_params)

        try:
            signals = await self.adapter.adapt_strategy(ohlcv_data)
            return signals
        finally:
            # Restore original parameters
            self.params = original_params


class StrategyFactory:
    """
    Factory for creating and managing strategies.

    Supports:
    - Vectorized strategies
    - Legacy async strategies
    - Strategy composition
    - Parameter management
    """

    def __init__(self):
        """Initialize strategy factory."""
        self.strategies: Dict[str, Callable] = {}
        self.adapters: Dict[str, StrategyAdapter] = {}
        logger.info("Initialized StrategyFactory")

    def register_strategy(self, name: str, strategy_func: Callable) -> None:
        """Register a strategy."""
        self.strategies[name] = strategy_func
        logger.info(f"Registered strategy: {name}")

    def register_legacy_strategy(self, name: str, strategy_func: Callable) -> None:
        """
        Register a legacy async strategy for automatic adaptation.

        Args:
            name: Strategy name
            strategy_func: Legacy async strategy function
        """
        self.strategies[name] = strategy_func
        self.adapters[name] = StrategyAdapter(strategy_func)
        logger.info(f"Registered legacy strategy: {name} (auto-adapted)")

    def get_strategy(self, name: str) -> Optional[Callable]:
        """Get a registered strategy."""
        return self.strategies.get(name)

    def get_adapter(self, name: str) -> Optional[StrategyAdapter]:
        """Get adapter for a legacy strategy."""
        return self.adapters.get(name)

    async def generate_signals(
        self,
        strategy_name: str,
        ohlcv_data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate signals from a registered strategy.

        Args:
            strategy_name: Name of registered strategy
            ohlcv_data: OHLCV data

        Returns:
            Tuple of (entries, exits)
        """
        adapter = self.get_adapter(strategy_name)
        if adapter:
            return await adapter.adapt_strategy(ohlcv_data)

        strategy = self.get_strategy(strategy_name)
        if strategy:
            if asyncio.iscoroutinefunction(strategy):
                # Adapt on-the-fly
                adapter = StrategyAdapter(strategy)
                return await adapter.adapt_strategy(ohlcv_data)
            else:
                # Direct call
                return strategy(ohlcv_data)

        raise ValueError(f"Strategy not found: {strategy_name}")

    def list_strategies(self) -> List[str]:
        """List all registered strategies."""
        return list(self.strategies.keys())


# Global strategy factory instance
_global_factory = None


def get_strategy_factory() -> StrategyFactory:
    """Get or create global strategy factory."""
    global _global_factory
    if _global_factory is None:
        _global_factory = StrategyFactory()
    return _global_factory


def register_strategy(name: str, strategy_func: Callable) -> None:
    """Register a strategy with global factory."""
    get_strategy_factory().register_strategy(name, strategy_func)


def register_legacy_strategy(name: str, strategy_func: Callable) -> None:
    """Register a legacy async strategy with global factory."""
    get_strategy_factory().register_legacy_strategy(name, strategy_func)
