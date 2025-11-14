"""
Backtest Tracing Spans (T060l)

This module provides specialized tracing spans for backtest execution workflows.
It tracks the complete lifecycle of backtest operations including data loading,
strategy execution, trade simulation, and metrics calculation.

Key Components:
- BacktestSpans: Factory for creating backtest trace spans
- BacktestExecutionSpan: Context manager for full backtest execution
- DataLoadingContext: Context manager for data loading operations
- StrategyContext: Context manager for strategy execution

Author: Claude Code
Version: 1.0.0
"""

from typing import Dict, Any, Optional, Generator
from contextlib import contextmanager
from src.observability.trace_context import TraceContext, TraceManager


class BacktestSpans:
    """
    Factory for creating backtest-related trace spans.

    This class provides methods to create and manage spans for different
    phases of backtest execution, ensuring proper parent-child relationships
    and consistent metadata tracking.
    """

    def __init__(self, trace_manager: TraceManager):
        """
        Initialize BacktestSpans with a trace manager.

        Args:
            trace_manager: TraceManager instance for span creation
        """
        self.trace_manager = trace_manager

    def trace_backtest_execution(
        self,
        user_id: str,
        symbol: str,
        strategy_type: str,
        start_date: str,
        end_date: str
    ) -> 'BacktestExecutionSpan':
        """
        Create a context manager for full backtest execution trace.

        This is the top-level span that encompasses the entire backtest
        workflow. It serves as the parent for all sub-operations.

        Args:
            user_id: ID of user who initiated the backtest
            symbol: Stock symbol being tested (e.g., "0700.HK")
            strategy_type: Type of trading strategy (e.g., "kdj", "rsi")
            start_date: Start date for backtest period
            end_date: End date for backtest period

        Returns:
            BacktestExecutionSpan context manager
        """
        return BacktestExecutionSpan(
            trace_manager=self.trace_manager,
            user_id=user_id,
            symbol=symbol,
            strategy_type=strategy_type,
            start_date=start_date,
            end_date=end_date
        )

    def trace_data_loading(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> 'DataLoadingContext':
        """
        Create a context manager for data loading trace.

        This span tracks the process of loading historical market data
        for the backtest period.

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataLoadingContext context manager
        """
        span = self.trace_manager.start_span(
            operation_name="backtest.data_loading",
            tags={
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        return DataLoadingContext(self.trace_manager, span)

    def trace_strategy_execution(
        self,
        strategy_type: str,
        parameters: Dict[str, Any]
    ) -> 'StrategyContext':
        """
        Create a context manager for strategy execution trace.

        This span tracks the generation of trading signals using the
        specified strategy and parameters.

        Args:
            strategy_type: Type of strategy (kdj, rsi, macd, etc.)
            parameters: Strategy parameters (e.g., k_period=9, d_period=3)

        Returns:
            StrategyContext context manager
        """
        span = self.trace_manager.start_span(
            operation_name="backtest.strategy_execution",
            tags={
                "strategy_type": strategy_type,
                **{
                    f"param.{k}": v
                    for k, v in parameters.items()
                }
            }
        )

        return StrategyContext(self.trace_manager, span)

    def trace_trade_simulation(
        self,
        initial_capital: float,
        commission_rate: float
    ) -> TraceContext:
        """
        Create a span for trade simulation and P&L calculation.

        This span tracks the simulation of trades based on generated signals,
        including position tracking, P&L calculation, and transaction costs.

        Args:
            initial_capital: Initial capital for backtest
            commission_rate: Commission rate per trade (e.g., 0.001 for 0.1%)

        Returns:
            TraceContext for trade simulation
        """
        return self.trace_manager.start_span(
            operation_name="backtest.trade_simulation",
            tags={
                "initial_capital": initial_capital,
                "commission_rate": commission_rate
            }
        )

    def trace_metrics_calculation(
        self,
        trade_count: int
    ) -> TraceContext:
        """
        Create a span for performance metrics calculation.

        This span tracks the calculation of performance metrics such as
        Sharpe ratio, max drawdown, win rate, etc.

        Args:
            trade_count: Number of trades executed

        Returns:
            TraceContext for metrics calculation
        """
        return self.trace_manager.start_span(
            operation_name="backtest.metrics_calculation",
            tags={
                "trade_count": trade_count
            }
        )


class BacktestExecutionSpan:
    """
    Context manager for backtest execution trace lifecycle.

    This class manages the complete backtest execution trace, including
    setup, execution, and cleanup. It provides methods to create child
    spans for each phase of the backtest.

    Example:
        with backtest_spans.trace_backtest_execution(
            user_id="user123",
            symbol="0700.HK",
            strategy_type="kdj",
            start_date="2020-01-01",
            end_date="2023-01-01"
        ) as execution:
            # Load data
            with execution.trace_data_loading(1000) as data_ctx:
                data_ctx.add_data_source("AlphaVantage", 1250.5)

            # Execute strategy
            with execution.trace_strategy_execution(150) as strategy_ctx:
                # Strategy execution code
                pass
    """

    def __init__(
        self,
        trace_manager: TraceManager,
        user_id: str,
        symbol: str,
        strategy_type: str,
        start_date: str,
        end_date: str
    ):
        """
        Initialize backtest execution span.

        Args:
            trace_manager: TraceManager instance
            user_id: User who initiated the backtest
            symbol: Stock symbol
            strategy_type: Trading strategy type
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.trace_manager = trace_manager
        self.user_id = user_id
        self.symbol = symbol
        self.strategy_type = strategy_type
        self.start_date = start_date
        self.end_date = end_date

        # Child spans
        self.main_span: Optional[TraceContext] = None
        self.data_span: Optional[TraceContext] = None
        self.strategy_span: Optional[TraceContext] = None
        self.simulation_span: Optional[TraceContext] = None
        self.metrics_span: Optional[TraceContext] = None

    def __enter__(self) -> 'BacktestExecutionSpan':
        """
        Enter backtest execution context.

        Creates the main backtest execution span and sets it as current.

        Returns:
            Self for context manager
        """
        self.main_span = self.trace_manager.start_span(
            operation_name="backtest.execution",
            user_id=self.user_id,
            tags={
                "symbol": self.symbol,
                "strategy_type": self.strategy_type,
                "start_date": self.start_date,
                "end_date": self.end_date
            }
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit backtest execution context.

        Finishes the main backtest span and logs the result.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if exc_type is not None:
            # An error occurred
            self.main_span.add_log("backtest_error", {
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val),
                "symbol": self.symbol,
                "strategy_type": self.strategy_type
            })
            self.main_span.finish(status="ERROR", error=exc_val)
        else:
            # Success
            self.main_span.add_log("backtest_completed", {
                "symbol": self.symbol,
                "strategy_type": self.strategy_type,
                "start_date": self.start_date,
                "end_date": self.end_date
            })
            self.main_span.finish(status="OK")

    def trace_data_loading(
        self,
        data_points: int
    ) -> 'DataLoadingContext':
        """
        Start a data loading span as a child of the main backtest span.

        Args:
            data_points: Number of data points loaded

        Returns:
            DataLoadingContext for data loading operations
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.data_span = self.trace_manager.start_span(
            operation_name="backtest.data_loading",
            tags={
                "data_points": data_points,
                "parent_symbol": self.symbol
            }
        )

        return DataLoadingContext(self.trace_manager, self.data_span)

    def trace_strategy_execution(
        self,
        signal_count: int
    ) -> 'StrategyContext':
        """
        Start a strategy execution span as a child of the main backtest span.

        Args:
            signal_count: Number of trading signals generated

        Returns:
            StrategyContext for strategy operations
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.strategy_span = self.trace_manager.start_span(
            operation_name="backtest.strategy_execution",
            tags={
                "signal_count": signal_count,
                "parent_strategy": self.strategy_type
            }
        )

        return StrategyContext(self.trace_manager, self.strategy_span)

    def trace_trade_simulation(
        self,
        initial_capital: float,
        commission_rate: float
    ) -> TraceContext:
        """
        Start a trade simulation span as a child of the main backtest span.

        Args:
            initial_capital: Initial capital for backtest
            commission_rate: Commission rate per trade

        Returns:
            TraceContext for trade simulation
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.simulation_span = self.trace_manager.start_span(
            operation_name="backtest.trade_simulation",
            tags={
                "initial_capital": initial_capital,
                "commission_rate": commission_rate,
                "parent_symbol": self.symbol
            }
        )

        return self.simulation_span

    def trace_metrics_calculation(
        self,
        trade_count: int
    ) -> TraceContext:
        """
        Start a metrics calculation span as a child of the main backtest span.

        Args:
            trade_count: Number of trades executed

        Returns:
            TraceContext for metrics calculation
        """
        if self.main_span is None:
            raise RuntimeError("Must enter context before creating child spans")

        self.metrics_span = self.trace_manager.start_span(
            operation_name="backtest.metrics_calculation",
            tags={
                "trade_count": trade_count,
                "parent_strategy": self.strategy_type
            }
        )

        return self.metrics_span


class DataLoadingContext:
    """
    Context manager for data loading span lifecycle.

    This class manages a span that tracks the process of loading historical
    market data for backtesting. It ensures proper cleanup and error handling.
    """

    def __init__(self, trace_manager: TraceManager, span: TraceContext):
        """
        Initialize data loading context.

        Args:
            trace_manager: TraceManager instance
            span: The span to manage
        """
        self.trace_manager = trace_manager
        self.span = span

    def __enter__(self) -> 'DataLoadingContext':
        """Enter data loading context"""
        self.span.add_log("data_loading_started", {
            "operation": "data_loading",
            "timestamp": self.span.start_time
        })
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit data loading context.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if exc_type is not None:
            self.span.add_log("error", {
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val),
                "operation": "data_loading"
            })
            self.span.finish(status="ERROR", error=exc_val)
        else:
            self.span.add_log("data_loaded", {
                "status": "success",
                "operation": "data_loading"
            })
            self.span.finish(status="OK")

    def add_data_source(self, source: str, fetch_time_ms: float):
        """
        Log data source and fetch time.

        Args:
            source: Data source name (e.g., "AlphaVantage", "Yahoo Finance")
            fetch_time_ms: Time taken to fetch data in milliseconds
        """
        self.span.add_tag("data_source", source)
        self.span.add_tag("fetch_time_ms", fetch_time_ms)
        self.span.add_log("data_source_logged", {
            "source": source,
            "fetch_time_ms": fetch_time_ms
        })

    def add_data_quality_metrics(
        self,
        total_records: int,
        missing_values: int,
        data_freshness_hours: int
    ):
        """
        Log data quality metrics.

        Args:
            total_records: Total number of records loaded
            missing_values: Number of missing values detected
            data_freshness_hours: How old the data is in hours
        """
        self.span.add_tag("total_records", total_records)
        self.span.add_tag("missing_values", missing_values)
        self.span.add_tag("data_freshness_hours", data_freshness_hours)

        self.span.add_log("data_quality_assessed", {
            "total_records": total_records,
            "missing_values": missing_values,
            "data_freshness_hours": data_freshness_hours,
            "completeness": (total_records - missing_values) / total_records if total_records > 0 else 0
        })


class StrategyContext:
    """
    Context manager for strategy execution span lifecycle.

    This class manages a span that tracks the execution of a trading strategy
    and the generation of trading signals.
    """

    def __init__(self, trace_manager: TraceManager, span: TraceContext):
        """
        Initialize strategy context.

        Args:
            trace_manager: TraceManager instance
            span: The span to manage
        """
        self.trace_manager = trace_manager
        self.span = span

    def __enter__(self) -> 'StrategyContext':
        """Enter strategy context"""
        self.span.add_log("strategy_started", {
            "operation": "strategy_execution",
            "timestamp": self.span.start_time
        })
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit strategy context.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if exc_type is not None:
            self.span.add_log("error", {
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_val),
                "operation": "strategy_execution"
            })
            self.span.finish(status="ERROR", error=exc_val)
        else:
            self.span.add_log("strategy_completed", {
                "status": "success",
                "operation": "strategy_execution"
            })
            self.span.finish(status="OK")

    def log_signal_generated(self, signal_type: str, signal_strength: float):
        """
        Log a trading signal that was generated.

        Args:
            signal_type: Type of signal (e.g., "BUY", "SELL", "HOLD")
            signal_strength: Strength of the signal (0-1)
        """
        self.span.add_log("signal_generated", {
            "signal_type": signal_type,
            "signal_strength": signal_strength
        })

    def add_strategy_metrics(
        self,
        signal_count: int,
        buy_signals: int,
        sell_signals: int,
        hold_signals: int
    ):
        """
        Add strategy execution metrics.

        Args:
            signal_count: Total number of signals generated
            buy_signals: Number of buy signals
            sell_signals: Number of sell signals
            hold_signals: Number of hold signals
        """
        self.span.add_tag("signal_count", signal_count)
        self.span.add_tag("buy_signals", buy_signals)
        self.span.add_tag("sell_signals", sell_signals)
        self.span.add_tag("hold_signals", hold_signals)

        self.span.add_log("strategy_metrics", {
            "total_signals": signal_count,
            "buy_count": buy_signals,
            "sell_count": sell_signals,
            "hold_count": hold_signals,
            "buy_ratio": buy_signals / signal_count if signal_count > 0 else 0,
            "sell_ratio": sell_signals / signal_count if signal_count > 0 else 0
        })


# Export public API
__all__ = [
    'BacktestSpans',
    'BacktestExecutionSpan',
    'DataLoadingContext',
    'StrategyContext'
]
