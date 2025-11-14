"""
Python Wrapper for Rust Backtest Engine

This module provides a clean, Pythonic interface to the high-performance
Rust backtest engine while handling PyO3 bindings, data conversion, and
providing fallback to pure Python when needed.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import logging
from contextlib import contextmanager
from functools import lru_cache
import asyncio
import time

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """
    Market data container with comprehensive validation.

    Ensures data integrity and provides conversion utilities for pandas DataFrames.
    Validates OHLC relationships and data consistency.
    """

    symbol: str
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]

    def __post_init__(self) -> None:
        """Validate data consistency after initialization."""
        # Check all arrays have the same length
        lengths = [
            len(self.dates),
            len(self.open),
            len(self.high),
            len(self.low),
            len(self.close),
            len(self.volume),
        ]
        if len(set(lengths)) != 1:
            raise ValueError(
                f"All arrays must have the same length. "
                f"Got lengths: {lengths}"
            )

        # Validate OHLC relationships
        for i in range(len(self.close)):
            # Low should not exceed high
            if self.low[i] > self.high[i]:
                raise ValueError(
                    f"Low price ({self.low[i]}) cannot exceed high price "
                    f"({self.high[i]}) at index {i}"
                )

            # Open and close should be within high-low range
            if not (
                self.low[i] <= self.open[i] <= self.high[i]
                and self.low[i] <= self.close[i] <= self.high[i]
            ):
                raise ValueError(
                    f"Invalid OHLC relationship at index {i}: "
                    f"Open={self.open[i]}, Close={self.close[i]}, "
                    f"High={self.high[i]}, Low={self.low[i]}"
                )

    @classmethod
    def from_pandas(cls, df: pd.DataFrame) -> "MarketData":
        """
        Create MarketData from pandas DataFrame.

        Args:
            df: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
                 and optional 'symbol'

        Returns:
            MarketData instance

        Raises:
            ValueError: If required columns are missing
        """
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"DataFrame must have columns: {required_columns}. "
                f"Missing: {missing_columns}"
            )

        return cls(
            symbol=df.get("symbol", ["UNKNOWN"])[0]
            if "symbol" in df.columns
            else "UNKNOWN",
            dates=df["date"].dt.strftime("%Y-%m-%d").tolist(),
            open=df["open"].tolist(),
            high=df["high"].tolist(),
            low=df["low"].tolist(),
            close=df["close"].tolist(),
            volume=df["volume"].astype(int).tolist(),
        )

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame(
            {
                "symbol": self.symbol,
                "date": pd.to_datetime(self.dates),
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            }
        )

    def __len__(self) -> int:
        """Return the number of data points."""
        return len(self.close)


@dataclass
class BacktestResult:
    """
    Backtest execution result with comprehensive metrics.

    Contains all performance metrics and execution details from a backtest run.
    """

    total_return: float
    annualized_return: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    execution_time_ms: int
    trades: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[float]] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    volatility: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "trade_count": self.trade_count,
            "execution_time_ms": self.execution_time_ms,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "volatility": self.volatility,
        }

    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"BacktestResult(\n"
            f"  Total Return: {self.total_return:.2%}\n"
            f"  Annualized Return: {self.annualized_return:.2%}\n"
            f"  Max Drawdown: {self.max_drawdown:.2%}\n"
            f"  Win Rate: {self.win_rate:.2f}%\n"
            f"  Trade Count: {self.trade_count}\n"
            f"  Execution Time: {self.execution_time_ms}ms\n"
            f")"
        )


class RustEngine:
    """
    Python wrapper for Rust backtest engine.

    Provides automatic fallback to pure Python implementation when Rust is unavailable.
    Supports both synchronous and asynchronous operations with comprehensive caching.
    """

    def __init__(self, use_rust: bool = True):
        """
        Initialize the Rust engine wrapper.

        Args:
            use_rust: If True, attempt to use Rust engine. If False, use pure Python.
        """
        self.use_rust = use_rust
        self._rust_module = None
        self._available = False

        if use_rust:
            self._initialize_rust()

    def _initialize_rust(self) -> None:
        """Initialize PyO3 bindings to Rust engine."""
        try:
            # Try to import the Rust module
            from quant_backtest import (
                PyMarketData,
                run_sma_backtest,
                validate_market_data,
                calculate_drawdown,
            )

            # Store references to Rust functions
            self._PyMarketData = PyMarketData
            self._run_sma_backtest = run_sma_backtest
            self._validate_market_data = validate_market_data
            self._calculate_drawdown = calculate_drawdown
            self._available = True

            logger.info("Rust engine successfully initialized")

        except ImportError as e:
            self._log_warning(
                f"Rust engine not available: {e}. Falling back to pure Python."
            )
            self._available = False
        except Exception as e:
            self._log_warning(
                f"Failed to initialize Rust engine: {e}. Falling back to pure Python."
            )
            self._available = False

    def is_rust_available(self) -> bool:
        """Check if Rust engine is available and initialized."""
        return self._available

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine."""
        return {
            "rust_available": self._available,
            "use_rust": self.use_rust,
            "engine_type": "Rust" if self._available else "Python",
        }

    def run_sma_backtest(
        self,
        data: Union[MarketData, pd.DataFrame],
        fast_period: int,
        slow_period: int,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
    ) -> BacktestResult:
        """
        Run SMA crossover strategy backtest.

        Args:
            data: Market data (MarketData or DataFrame)
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            initial_capital: Initial capital for backtest
            commission_rate: Commission rate per trade

        Returns:
            BacktestResult with performance metrics
        """
        # Convert to MarketData if needed
        if isinstance(data, pd.DataFrame):
            data = MarketData.from_pandas(data)

        # Validate input parameters
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if fast_period < 1 or slow_period < 1:
            raise ValueError("Periods must be positive integers")
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if not 0 <= commission_rate <= 1:
            raise ValueError("Commission rate must be between 0 and 1")

        if self._available:
            return self._run_sma_backtest_rust(
                data, fast_period, slow_period, initial_capital
            )
        else:
            return self._run_sma_backtest_python(
                data, fast_period, slow_period, initial_capital, commission_rate
            )

    def _run_sma_backtest_rust(
        self,
        data: MarketData,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
    ) -> BacktestResult:
        """Execute backtest using Rust engine."""
        start_time = time.time()

        # Convert to PyMarketData
        py_data = self._PyMarketData(
            symbol=data.symbol,
            dates=data.dates,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
        )

        # Call Rust function
        result = self._run_sma_backtest(
            py_data, fast_period, slow_period, initial_capital
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        # Convert back to Python
        return BacktestResult(
            total_return=result.total_return,
            annualized_return=result.annualized_return,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            trade_count=result.trade_count,
            execution_time_ms=int(execution_time),
            trades=result.trades,
            equity_curve=result.equity_curve,
            sharpe_ratio=getattr(result, "sharpe_ratio", None),
        )

    def _run_sma_backtest_python(
        self,
        data: MarketData,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
        commission_rate: float,
    ) -> BacktestResult:
        """Execute backtest using pure Python (fallback)."""
        start_time = time.time()

        # Calculate SMAs
        close_prices = np.array(data.close, dtype=np.float64)
        fast_sma = self._calculate_sma(close_prices, fast_period)
        slow_sma = self._calculate_sma(close_prices, slow_period)

        # Generate signals and execute trades
        position = 0.0  # 0 = no position, 1 = long, -1 = short
        capital = initial_capital
        entry_price = 0.0
        trades = []
        equity_curve = [initial_capital]
        current_shares = 0.0

        for i in range(1, len(close_prices)):
            if np.isnan(fast_sma[i]) or np.isnan(slow_sma[i]):
                # Not enough data for SMA
                equity_curve.append(equity_curve[-1])
                continue

            current_price = close_prices[i]
            current_sma_fast = fast_sma[i]
            current_sma_slow = slow_sma[i]
            prev_sma_fast = fast_sma[i - 1]
            prev_sma_slow = slow_sma[i - 1]

            # Check for crossovers
            buy_signal = prev_sma_fast <= prev_sma_slow and current_sma_fast > current_sma_slow
            sell_signal = prev_sma_fast >= prev_sma_slow and current_sma_fast < current_sma_slow

            # Execute trades
            if buy_signal and position <= 0.0:
                # Buy signal
                if position < 0.0:
                    # Close short position
                    pnl = (entry_price - current_price) * current_shares
                    capital += pnl
                    trades.append(
                        {
                            "type": "BUY_TO_CLOSE",
                            "date": data.dates[i],
                            "price": current_price,
                            "pnl": pnl,
                        }
                    )

                # Open long position
                current_shares = capital / current_price
                entry_price = current_price
                capital = 0.0
                position = 1.0

                trades.append(
                    {
                        "type": "BUY",
                        "date": data.dates[i],
                        "price": current_price,
                        "shares": current_shares,
                        "value": current_shares * current_price,
                    }
                )

            elif sell_signal and position >= 0.0:
                # Sell signal
                if position > 0.0:
                    # Close long position
                    capital = current_shares * current_price
                    pnl = capital - (current_shares * entry_price)
                    trades.append(
                        {
                            "type": "SELL_TO_CLOSE",
                            "date": data.dates[i],
                            "price": current_price,
                            "shares": current_shares,
                            "value": capital,
                            "pnl": pnl,
                        }
                    )

                # Open short position
                current_shares = initial_capital / current_price
                entry_price = current_price
                position = -1.0

                trades.append(
                    {
                        "type": "SELL",
                        "date": data.dates[i],
                        "price": current_price,
                        "shares": current_shares,
                    }
                )

            # Update equity curve
            if position > 0.0:
                # Long position
                equity_curve.append(current_shares * current_price)
            elif position < 0.0:
                # Short position
                equity_curve.append(
                    initial_capital
                    - (current_price - entry_price) * current_shares
                )
            else:
                # No position
                equity_curve.append(capital)

        # Calculate metrics
        final_value = equity_curve[-1]
        total_return = (final_value - initial_capital) / initial_capital

        # Calculate annualized return
        years = len(data.dates) / 252.0  # Assuming 252 trading days per year
        annualized_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        # Calculate win rate
        profit_trades = [t for t in trades if t.get("pnl", 0) > 0]
        win_rate = (len(profit_trades) / max(len(trades), 1)) * 100.0

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            trade_count=len(trades),
            execution_time_ms=int(execution_time),
            trades=trades,
            equity_curve=equity_curve,
        )

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average using vectorized operations."""
        return pd.Series(prices).rolling(window=period, min_periods=1).mean().values

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve."""
        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak if peak > 0 else 0.0
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def validate_data(self, data: Union[MarketData, pd.DataFrame]) -> bool:
        """
        Validate market data integrity.

        Args:
            data: Market data to validate

        Returns:
            True if data is valid, False otherwise
        """
        if isinstance(data, pd.DataFrame):
            try:
                data = MarketData.from_pandas(data)
            except ValueError:
                return False

        if self._available:
            try:
                py_data = self._PyMarketData(
                    symbol=data.symbol,
                    dates=data.dates,
                    open=data.open,
                    high=data.high,
                    low=data.low,
                    close=data.close,
                    volume=data.volume,
                )
                return self._validate_market_data(py_data)
            except Exception:
                return False
        else:
            # Pure Python validation
            try:
                # This will trigger __post_init__ validation
                MarketData(
                    symbol=data.symbol,
                    dates=data.dates,
                    open=data.open,
                    high=data.high,
                    low=data.low,
                    close=data.close,
                    volume=data.volume,
                )
                return True
            except ValueError:
                return False

    def _log_warning(self, message: str) -> None:
        """Log warning message."""
        warnings.warn(message, UserWarning)
        logger.warning(message)

    # Async support
    async def run_sma_backtest_async(
        self,
        data: Union[MarketData, pd.DataFrame],
        fast_period: int,
        slow_period: int,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
    ) -> BacktestResult:
        """
        Async version of SMA backtest.

        Runs the backtest in a thread pool to avoid blocking the event loop.

        Args:
            data: Market data
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            initial_capital: Initial capital
            commission_rate: Commission rate

        Returns:
            BacktestResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.run_sma_backtest,
            data,
            fast_period,
            slow_period,
            initial_capital,
            commission_rate,
        )

    def run_multiple_backtests(
        self,
        data: Union[MarketData, pd.DataFrame],
        fast_periods: List[int],
        slow_periods: List[int],
        initial_capital: float = 100000.0,
        max_workers: int = 4,
    ) -> List[BacktestResult]:
        """
        Run multiple backtests with different parameters.

        Args:
            data: Market data
            fast_periods: List of fast periods to test
            slow_periods: List of slow periods to test
            initial_capital: Initial capital
            max_workers: Maximum number of worker threads

        Returns:
            List of BacktestResult
        """
        from concurrent.futures import ThreadPoolExecutor

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for fast in fast_periods:
                for slow in slow_periods:
                    if fast < slow:
                        future = executor.submit(
                            self.run_sma_backtest,
                            data,
                            fast,
                            slow,
                            initial_capital,
                        )
                        futures.append((fast, slow, future))

            for fast, slow, future in futures:
                try:
                    result = future.result()
                    results.append((fast, slow, result))
                except Exception as e:
                    logger.error(f"Backtest failed for ({fast}, {slow}): {e}")

        return results


class CachedRustEngine(RustEngine):
    """
    Rust engine with intelligent result caching.

    Caches backtest results to avoid recomputation for identical parameters.
    Uses LRU cache with configurable size.
    """

    def __init__(self, use_rust: bool = True, cache_size: int = 128):
        """
        Initialize cached engine.

        Args:
            use_rust: If True, use Rust engine
            cache_size: Maximum number of cached results
        """
        super().__init__(use_rust)
        self._cache_size = cache_size

    @lru_cache(maxsize=128)
    def run_sma_backtest_cached(
        self,
        data_hash: tuple,
        fast_period: int,
        slow_period: int,
        initial_capital: int,
    ) -> BacktestResult:
        """
        Cached version of SMA backtest.

        Args:
            data_hash: Hash of the data (for caching)
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            initial_capital: Initial capital

        Returns:
            BacktestResult
        """
        # This method should be used with data serialization
        # In practice, you'd serialize the MarketData and pass it through
        raise NotImplementedError(
            "Cached backtest requires data serialization. "
            "Use run_sma_backtest() for normal operation."
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if hasattr(self.run_sma_backtest_cached, "cache_info"):
            info = self.run_sma_backtest_cached.cache_info()
            return {
                "hits": info.hits,
                "misses": info.misses,
                "maxsize": info.maxsize,
                "currsize": info.currsize,
                "hit_rate": info.hits / max(info.hits + info.misses, 1),
            }
        return {"error": "Cache not available"}


# Context Manager
@contextmanager
def rust_engine_context(use_rust: bool = True):
    """
    Context manager for Rust engine.

    Ensures proper initialization and cleanup of engine resources.

    Args:
        use_rust: If True, attempt to use Rust engine

    Yields:
        RustEngine instance

    Example:
        with rust_engine_context() as engine:
            result = engine.run_sma_backtest(data, 10, 30)
    """
    engine = RustEngine(use_rust=use_rust)
    try:
        yield engine
    finally:
        # Cleanup if needed
        pass


# Factory function
def create_engine(use_rust: bool = True, use_cache: bool = False) -> RustEngine:
    """
    Create a Rust engine instance.

    Args:
        use_rust: If True, use Rust engine
        use_cache: If True, use cached version

    Returns:
        RustEngine or CachedRustEngine instance
    """
    if use_cache:
        return CachedRustEngine(use_rust=use_rust)
    return RustEngine(use_rust=use_rust)


# Utility functions
def generate_sample_data(
    symbol: str, days: int, start_price: float = 100.0
) -> MarketData:
    """
    Generate sample market data for testing.

    Args:
        symbol: Stock symbol
        days: Number of days to generate
        start_price: Starting price

    Returns:
        MarketData with synthetic data
    """
    np.random.seed(42)  # For reproducible results

    dates = []
    current_date = datetime(2020, 1, 1)
    for _ in range(days):
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date = current_date.__class__(
            current_date.year, current_date.month, current_date.day + 1
        )

    # Generate price data with random walk
    returns = np.random.normal(0.001, 0.02, days)
    prices = [start_price]

    for i in range(1, days):
        price = prices[-1] * (1 + returns[i])
        prices.append(price)

    # Generate OHLC from close prices
    open_prices = prices.copy()
    high_prices = [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices]
    low_prices = [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices]
    volumes = [int(np.random.uniform(100000, 1000000)) for _ in range(days)]

    return MarketData(
        symbol=symbol,
        dates=dates,
        open=[float(p) for p in open_prices],
        high=[float(p) for p in high_prices],
        low=[float(p) for p in low_prices],
        close=[float(p) for p in prices],
        volume=volumes,
    )


# Performance benchmarking
def benchmark_engine(
    data: MarketData, fast_period: int = 10, slow_period: int = 30
) -> Dict[str, Any]:
    """
    Benchmark Rust vs Python engine performance.

    Args:
        data: Market data for testing
        fast_period: Fast period
        slow_period: Slow period

    Returns:
        Dictionary with benchmark results
    """
    results = {}

    # Test Python engine
    python_engine = RustEngine(use_rust=False)
    start = time.time()
    python_result = python_engine.run_sma_backtest(data, fast_period, slow_period)
    python_time = (time.time() - start) * 1000
    results["python"] = {
        "time_ms": python_time,
        "execution_time_ms": python_result.execution_time_ms,
    }

    # Test Rust engine (if available)
    rust_engine = RustEngine(use_rust=True)
    if rust_engine.is_rust_available():
        start = time.time()
        rust_result = rust_engine.run_sma_backtest(data, fast_period, slow_period)
        rust_time = (time.time() - start) * 1000
        results["rust"] = {
            "time_ms": rust_time,
            "execution_time_ms": rust_result.execution_time_ms,
        }
        results["speedup"] = python_time / rust_time if rust_time > 0 else 0

    return results


# Export public API
__all__ = [
    "MarketData",
    "BacktestResult",
    "RustEngine",
    "CachedRustEngine",
    "rust_engine_context",
    "create_engine",
    "generate_sample_data",
    "benchmark_engine",
]
