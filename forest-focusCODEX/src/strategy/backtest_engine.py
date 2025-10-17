"""
Backtest engine for RSI trading strategy.

Implements event-driven backtest with position tracking and trade execution.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger("rsi_backtest.strategy.backtest_engine")


class PositionStatus(Enum):
    """Position status enum."""
    OUT_MARKET = "OUT_MARKET"  # Holding cash
    IN_MARKET = "IN_MARKET"    # Holding stock


@dataclass
class Trade:
    """Record of a single trade transaction."""
    trade_id: int
    date: pd.Timestamp
    action: str  # 'BUY' or 'SELL'
    price: float
    shares: int
    gross_amount: float
    commission: float = 0.0
    stamp_duty: float = 0.0
    total_cost: float = 0.0
    net_amount: float = 0.0


@dataclass
class Position:
    """Current position state."""
    status: PositionStatus = PositionStatus.OUT_MARKET
    entry_date: pd.Timestamp = None
    entry_price: float = 0.0
    shares: int = 0
    cash: float = 100000.0  # Initial capital
    equity: float = 100000.0


class BacktestEngine:
    """
    Event-driven backtest engine for RSI strategy.

    Features:
    - Event-driven architecture (no look-ahead bias)
    - Position tracking (IN_MARKET/OUT_MARKET)
    - Trade execution with cost model
    - Daily equity calculation
    """

    def __init__(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        initial_capital: float = 100000.0,
        commission: float = 0.0,
        stamp_duty: float = 0.0
    ):
        """
        Initialize backtest engine.

        Args:
            data: DataFrame with date, open, high, low, close, volume
            signals: Series of trading signals ('BUY', 'SELL', 'HOLD')
            initial_capital: Starting portfolio value in HKD
            commission: Commission rate (e.g., 0.001 = 0.1%)
            stamp_duty: Stamp duty rate on sells (e.g., 0.001 = 0.1%)
        """
        self.data = data.copy()
        self.signals = signals
        self.initial_capital = initial_capital
        self.commission_rate = commission
        self.stamp_duty_rate = stamp_duty

        # State tracking
        self.position = Position(cash=initial_capital, equity=initial_capital)
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.dates: List[pd.Timestamp] = []

        # Trade ID counter
        self._next_trade_id = 1

        logger.info(
            f"Backtest engine initialized: "
            f"capital={initial_capital}, commission={commission*100:.1f}%, "
            f"stamp_duty={stamp_duty*100:.1f}%"
        )

    def calculate_trade_cost(self, gross_amount: float, action: str) -> Tuple[float, float, float]:
        """
        Calculate trading costs.

        Args:
            gross_amount: Trade amount before costs
            action: 'BUY' or 'SELL'

        Returns:
            Tuple of (commission, stamp_duty, total_cost)
        """
        commission = gross_amount * self.commission_rate

        if action == 'SELL':
            stamp_duty = gross_amount * self.stamp_duty_rate
        else:
            stamp_duty = 0.0

        total_cost = commission + stamp_duty
        return commission, stamp_duty, total_cost

    def execute_buy(self, date: pd.Timestamp, price: float) -> bool:
        """
        Execute BUY order.

        Args:
            date: Transaction date
            price: Buy price

        Returns:
            True if trade executed, False otherwise
        """
        if self.position.status == PositionStatus.IN_MARKET:
            # Already holding stock, cannot buy again
            return False

        # Calculate how many shares we can afford
        available_cash = self.position.cash
        commission, stamp_duty, total_cost = self.calculate_trade_cost(available_cash, 'BUY')

        # shares * price + cost = available_cash
        # shares = (available_cash - cost) / price
        # But cost depends on shares, so iterate or approximate
        shares = int((available_cash) / (price * (1 + self.commission_rate)))

        if shares <= 0:
            logger.warning(f"Insufficient cash to buy on {date.date()}")
            return False

        gross_amount = shares * price
        commission, stamp_duty, total_cost = self.calculate_trade_cost(gross_amount, 'BUY')
        net_amount = gross_amount + total_cost

        if net_amount > available_cash:
            # Reduce shares by 1 to ensure we can afford it
            shares -= 1
            gross_amount = shares * price
            commission, stamp_duty, total_cost = self.calculate_trade_cost(gross_amount, 'BUY')
            net_amount = gross_amount + total_cost

        # Execute trade
        self.position.cash -= net_amount
        self.position.shares = shares
        self.position.entry_date = date
        self.position.entry_price = price
        self.position.status = PositionStatus.IN_MARKET

        # Record trade
        trade = Trade(
            trade_id=self._next_trade_id,
            date=date,
            action='BUY',
            price=price,
            shares=shares,
            gross_amount=gross_amount,
            commission=commission,
            stamp_duty=stamp_duty,
            total_cost=total_cost,
            net_amount=net_amount
        )
        self.trades.append(trade)
        self._next_trade_id += 1

        logger.debug(
            f"BUY executed: {shares} shares @ {price:.2f} on {date.date()} "
            f"(cost={total_cost:.2f}, cash remaining={self.position.cash:.2f})"
        )

        return True

    def execute_sell(self, date: pd.Timestamp, price: float) -> bool:
        """
        Execute SELL order.

        Args:
            date: Transaction date
            price: Sell price

        Returns:
            True if trade executed, False otherwise
        """
        if self.position.status == PositionStatus.OUT_MARKET:
            # No position to sell
            return False

        shares = self.position.shares
        gross_amount = shares * price
        commission, stamp_duty, total_cost = self.calculate_trade_cost(gross_amount, 'SELL')
        net_amount = gross_amount - total_cost

        # Execute trade
        self.position.cash += net_amount
        self.position.shares = 0
        self.position.entry_date = None
        self.position.entry_price = 0.0
        self.position.status = PositionStatus.OUT_MARKET

        # Record trade
        trade = Trade(
            trade_id=self._next_trade_id,
            date=date,
            action='SELL',
            price=price,
            shares=shares,
            gross_amount=gross_amount,
            commission=commission,
            stamp_duty=stamp_duty,
            total_cost=total_cost,
            net_amount=net_amount
        )
        self.trades.append(trade)
        self._next_trade_id += 1

        logger.debug(
            f"SELL executed: {shares} shares @ {price:.2f} on {date.date()} "
            f"(cost={total_cost:.2f}, cash now={self.position.cash:.2f})"
        )

        return True

    def update_equity(self, current_price: float) -> float:
        """
        Calculate current portfolio equity.

        Args:
            current_price: Current stock price

        Returns:
            Total portfolio value (cash + stock value)
        """
        stock_value = self.position.shares * current_price
        self.position.equity = self.position.cash + stock_value
        return self.position.equity

    def run(self) -> Tuple[List[Trade], pd.Series]:
        """
        Run the backtest simulation.

        Returns:
            Tuple of (trades, equity_curve)
        """
        logger.info(f"Starting backtest with {len(self.data)} days of data...")

        for i in range(len(self.data)):
            date = self.data['date'].iloc[i]
            close_price = self.data['close'].iloc[i]
            signal = self.signals.iloc[i]

            # Execute trades based on signal
            if signal == 'BUY':
                self.execute_buy(date, close_price)
            elif signal == 'SELL':
                self.execute_sell(date, close_price)

            # Update equity (mark-to-market)
            equity = self.update_equity(close_price)
            self.equity_curve.append(equity)
            self.dates.append(date)

        # Create equity curve series
        equity_series = pd.Series(self.equity_curve, index=self.dates, name='equity')

        logger.info(
            f"Backtest complete: {len(self.trades)} trades executed, "
            f"final equity={self.position.equity:.2f}"
        )

        return self.trades, equity_series

    def get_summary(self) -> dict:
        """
        Get backtest summary statistics.

        Returns:
            Dictionary of summary metrics
        """
        buy_trades = [t for t in self.trades if t.action == 'BUY']
        sell_trades = [t for t in self.trades if t.action == 'SELL']

        return {
            'initial_capital': self.initial_capital,
            'final_equity': self.position.equity,
            'total_return': (self.position.equity - self.initial_capital) / self.initial_capital,
            'num_trades': len(self.trades),
            'num_buy': len(buy_trades),
            'num_sell': len(sell_trades),
            'total_commission': sum(t.commission for t in self.trades),
            'total_stamp_duty': sum(t.stamp_duty for t in self.trades),
            'total_costs': sum(t.total_cost for t in self.trades)
        }
