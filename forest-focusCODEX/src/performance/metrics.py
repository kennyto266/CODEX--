"""
Performance metrics calculation module.

Calculates Sharpe ratio, returns, drawdown, and other portfolio metrics.
"""

import logging
from dataclasses import dataclass
from typing import List

import pandas as pd
import numpy as np

from src.strategy.backtest_engine import Trade

logger = logging.getLogger("rsi_backtest.performance.metrics")


@dataclass
class PerformanceMetrics:
    """Container for calculated performance metrics."""
    rsi_window: int
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    num_winning_trades: int = 0
    num_losing_trades: int = 0
    avg_trade_return: float = 0.0


def calculate_returns(equity_curve: pd.Series) -> pd.Series:
    """
    Calculate daily returns from equity curve.

    Args:
        equity_curve: Series of portfolio values over time

    Returns:
        Series of daily returns (percentage change)
    """
    returns = equity_curve.pct_change().dropna()
    return returns


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    trading_days: int = 252
) -> float:
    """
    Calculate annualized Sharpe ratio.

    Formula:
        Sharpe = (Annualized Return - Risk Free Rate) / Annualized Volatility

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate (default: 2%)
        trading_days: Trading days per year (default: 252)

    Returns:
        Sharpe ratio (float)
    """
    if len(returns) == 0:
        logger.warning("No returns data, Sharpe ratio undefined")
        return 0.0

    # Annualize returns and volatility
    mean_return = returns.mean()
    std_return = returns.std()

    if std_return == 0 or np.isnan(std_return):
        logger.warning("Zero volatility, Sharpe ratio undefined")
        return 0.0

    annualized_return = mean_return * trading_days
    annualized_volatility = std_return * np.sqrt(trading_days)

    # Calculate Sharpe ratio
    sharpe = (annualized_return - risk_free_rate) / annualized_volatility

    return sharpe


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown (peak-to-trough decline).

    Args:
        equity_curve: Series of portfolio values

    Returns:
        Maximum drawdown as negative fraction (e.g., -0.15 = -15%)
    """
    if len(equity_curve) == 0:
        return 0.0

    # Calculate running maximum
    running_max = equity_curve.cummax()

    # Calculate drawdown at each point
    drawdown = (equity_curve - running_max) / running_max

    # Maximum drawdown is the minimum value (most negative)
    max_dd = drawdown.min()

    return max_dd if not np.isnan(max_dd) else 0.0


def calculate_win_rate(trades: List[Trade]) -> tuple:
    """
    Calculate win rate from trade history.

    A trade is considered winning if sell price > buy price (after costs).

    Args:
        trades: List of Trade objects

    Returns:
        Tuple of (win_rate, num_winning, num_losing)
    """
    if not trades:
        return 0.0, 0, 0

    # Match buy and sell trades
    buy_trades = [t for t in trades if t.action == 'BUY']
    sell_trades = [t for t in trades if t.action == 'SELL']

    # Can only evaluate completed round trips
    num_pairs = min(len(buy_trades), len(sell_trades))

    if num_pairs == 0:
        return 0.0, 0, 0

    winning = 0
    losing = 0

    for i in range(num_pairs):
        buy_trade = buy_trades[i]
        sell_trade = sell_trades[i]

        # Calculate P&L
        buy_cost = buy_trade.net_amount
        sell_proceeds = sell_trade.net_amount

        if sell_proceeds > buy_cost:
            winning += 1
        else:
            losing += 1

    win_rate = winning / num_pairs if num_pairs > 0 else 0.0

    return win_rate, winning, losing


def calculate_performance_metrics(
    rsi_window: int,
    equity_curve: pd.Series,
    trades: List[Trade],
    initial_capital: float,
    risk_free_rate: float = 0.02,
    trading_days: int = 252
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics for a backtest.

    Args:
        rsi_window: RSI window parameter used
        equity_curve: Portfolio value over time
        trades: List of executed trades
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate
        trading_days: Trading days per year

    Returns:
        PerformanceMetrics object
    """
    # Calculate returns
    daily_returns = calculate_returns(equity_curve)

    # Total return
    final_equity = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital
    total_return = (final_equity - initial_capital) / initial_capital

    # Annualized return and volatility
    if len(daily_returns) > 0:
        annualized_return = daily_returns.mean() * trading_days
        annualized_volatility = daily_returns.std() * np.sqrt(trading_days)
    else:
        annualized_return = 0.0
        annualized_volatility = 0.0

    # Sharpe ratio
    sharpe = calculate_sharpe_ratio(daily_returns, risk_free_rate, trading_days)

    # Maximum drawdown
    max_dd = calculate_max_drawdown(equity_curve)

    # Win rate
    win_rate, num_winning, num_losing = calculate_win_rate(trades)

    # Average trade return
    if num_winning + num_losing > 0:
        # Simple approximation: total return / number of round trips
        avg_trade_return = total_return / (num_winning + num_losing)
    else:
        avg_trade_return = 0.0

    metrics = PerformanceMetrics(
        rsi_window=rsi_window,
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        win_rate=win_rate,
        num_trades=len(trades),
        num_winning_trades=num_winning,
        num_losing_trades=num_losing,
        avg_trade_return=avg_trade_return
    )

    logger.debug(
        f"Metrics calculated for RSI({rsi_window}): "
        f"Sharpe={sharpe:.4f}, Return={total_return*100:.2f}%, "
        f"MaxDD={max_dd*100:.2f}%"
    )

    return metrics


def calculate_buy_and_hold_metrics(
    data: pd.DataFrame,
    initial_capital: float,
    risk_free_rate: float = 0.02,
    trading_days: int = 252
) -> PerformanceMetrics:
    """
    Calculate performance metrics for buy-and-hold strategy (baseline).

    Args:
        data: Price data DataFrame
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate
        trading_days: Trading days per year

    Returns:
        PerformanceMetrics for buy-and-hold
    """
    if len(data) == 0:
        return PerformanceMetrics(
            rsi_window=0,
            total_return=0.0,
            annualized_return=0.0,
            annualized_volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            num_trades=0
        )

    # Buy at first price, sell at last price
    first_price = data['close'].iloc[0]
    last_price = data['close'].iloc[-1]

    # Calculate number of shares
    shares = int(initial_capital / first_price)
    final_equity = shares * last_price

    # Create equity curve (just scaled close prices)
    equity_curve = (data['close'] / first_price) * initial_capital
    equity_curve = pd.Series(equity_curve.values, index=data['date'])

    # Calculate returns
    daily_returns = calculate_returns(equity_curve)

    # Total return
    total_return = (final_equity - initial_capital) / initial_capital

    # Annualized metrics
    if len(daily_returns) > 0:
        annualized_return = daily_returns.mean() * trading_days
        annualized_volatility = daily_returns.std() * np.sqrt(trading_days)
        sharpe = calculate_sharpe_ratio(daily_returns, risk_free_rate, trading_days)
    else:
        annualized_return = 0.0
        annualized_volatility = 0.0
        sharpe = 0.0

    # Maximum drawdown
    max_dd = calculate_max_drawdown(equity_curve)

    return PerformanceMetrics(
        rsi_window=0,  # N/A for buy-and-hold
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        win_rate=1.0 if total_return > 0 else 0.0,  # Single "trade"
        num_trades=2  # 1 buy, 1 sell
    )
