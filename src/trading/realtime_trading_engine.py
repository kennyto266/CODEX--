"""
Real-time Trading Engine - Live Market Integration

Manages real-time signal generation, order execution, and position management
for live trading operations.

Features:
    - Real-time market data streaming
    - Signal generation from multiple strategies
    - Order execution gateway
    - Position and portfolio tracking
    - Trade logging and audit trail
    - Risk monitoring integration

Architecture:
    MarketDataFeed
        ↓
    RealtimeTradingEngine
        ├─→ Signal Generation (strategies)
        ├─→ Risk Validation
        ├─→ Order Execution (OrderGateway)
        └─→ Position Management
            ↓
        PerformanceMonitoring
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger("hk_quant_system.trading.realtime")


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PositionStatus(str, Enum):
    """Position status enumeration"""
    OPENING = "OPENING"
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


@dataclass
class Order:
    """Order representation"""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    commission: float = 0.0

    def is_filled(self) -> bool:
        """Check if order is fully filled"""
        return self.status == OrderStatus.FILLED or \
               abs(self.filled_quantity - self.quantity) < 1e-6


@dataclass
class Position:
    """Position representation"""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    def update_market_price(self, price: float) -> None:
        """Update position with current market price"""
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity
        if self.entry_price > 0:
            self.unrealized_pnl_pct = self.unrealized_pnl / (self.entry_price * self.quantity)

    def get_duration(self) -> timedelta:
        """Get position duration"""
        return datetime.now() - self.entry_time


@dataclass
class LiveSignal:
    """Real-time trading signal"""
    symbol: str
    timestamp: datetime
    direction: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float
    reason: str
    source: str = "PRICE_AND_ALT_DATA"
    alt_data_inputs: Dict[str, float] = field(default_factory=dict)


class PositionManager:
    """Manages open positions"""

    def __init__(self):
        """Initialize position manager"""
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.logger = logging.getLogger("hk_quant_system.trading.position_manager")

    def add_position(self, symbol: str, quantity: float, entry_price: float) -> Position:
        """Add a new position"""
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(),
            current_price=entry_price
        )
        self.positions[symbol] = position
        self.logger.info(f"Added position: {symbol} x{quantity} @ {entry_price:.2f}")
        return position

    def update_position(self, symbol: str, market_price: float) -> None:
        """Update position with current market price"""
        if symbol in self.positions:
            self.positions[symbol].update_market_price(market_price)

    def close_position(self, symbol: str, exit_price: float) -> Optional[Position]:
        """Close a position"""
        if symbol not in self.positions:
            self.logger.warning(f"Position not found: {symbol}")
            return None

        position = self.positions.pop(symbol)
        position.status = PositionStatus.CLOSED
        position.unrealized_pnl = (exit_price - position.entry_price) * position.quantity

        self.closed_positions.append(position)

        self.logger.info(
            f"Closed position: {symbol} PnL={position.unrealized_pnl:.2f} "
            f"({position.unrealized_pnl_pct*100:.2f}%)"
        )
        return position

    def get_portfolio_value(self, cash: float) -> float:
        """Calculate total portfolio value"""
        position_value = sum(p.current_price * p.quantity for p in self.positions.values())
        return cash + position_value

    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_position_heat(self) -> float:
        """Calculate portfolio heat (exposure)"""
        return sum(abs(p.quantity * p.current_price) for p in self.positions.values())

    def get_positions_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        return {
            'open_positions': len(self.positions),
            'total_exposure': self.get_position_heat(),
            'unrealized_pnl': self.get_total_unrealized_pnl(),
            'positions': {symbol: asdict(pos) for symbol, pos in self.positions.items()}
        }


class OrderGateway:
    """Gateway for order execution"""

    def __init__(self):
        """Initialize order gateway"""
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        self.executions: List[Order] = []
        self.logger = logging.getLogger("hk_quant_system.trading.order_gateway")

    async def send_order(self, order: Order) -> str:
        """Send order to market"""
        self.order_counter += 1
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter}"
        order.order_id = order_id
        order.status = OrderStatus.SUBMITTED

        self.orders[order_id] = order
        self.logger.info(
            f"Order submitted: {order_id} {order.side} {order.quantity} {order.symbol} @ {order.price:.2f}"
        )

        # Simulate order execution (in real system, would connect to broker API)
        await self._simulate_execution(order_id)

        return order_id

    async def _simulate_execution(self, order_id: str) -> None:
        """Simulate order execution"""
        order = self.orders[order_id]

        # Simulate execution delay
        await asyncio.sleep(0.1)

        # Simulate partial fills
        filled = int(order.quantity * 0.8)  # 80% filled initially
        order.filled_quantity = filled
        order.average_fill_price = order.price * 0.999  # Slight slippage
        order.status = OrderStatus.PARTIAL

        # Complete remaining
        await asyncio.sleep(0.1)
        order.filled_quantity = order.quantity
        order.average_fill_price = order.price
        order.status = OrderStatus.FILLED

        self.executions.append(order)
        self.logger.info(f"Order filled: {order_id} @ {order.average_fill_price:.2f}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False

        order.status = OrderStatus.CANCELLED
        self.logger.info(f"Order cancelled: {order_id}")
        return True

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get order status"""
        return self.orders.get(order_id, {}).status if order_id in self.orders else None

    def get_executions(self) -> List[Order]:
        """Get all executions"""
        return self.executions.copy()


class RealtimeTradingEngine:
    """Real-time trading engine"""

    def __init__(self, initial_capital: float = 1000000.0):
        """
        Initialize real-time trading engine

        Args:
            initial_capital: Starting capital in units
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.start_time = datetime.now()

        self.position_manager = PositionManager()
        self.order_gateway = OrderGateway()

        self.signals_generated: List[LiveSignal] = []
        self.daily_pnl: List[float] = []
        self.last_daily_pnl = 0.0

        self.logger = logging.getLogger("hk_quant_system.trading.realtime_engine")
        self.is_trading = False

    async def start_trading(self) -> None:
        """Start trading"""
        self.is_trading = True
        self.logger.info("Trading started")

    async def stop_trading(self) -> None:
        """Stop trading"""
        self.is_trading = False
        # Close all open positions
        await self.close_all_positions()
        self.logger.info("Trading stopped")

    async def process_signal(self, signal: LiveSignal) -> Optional[str]:
        """
        Process trading signal and execute orders

        Args:
            signal: Trading signal from strategy

        Returns:
            Order ID if executed, None otherwise
        """
        if not self.is_trading:
            return None

        self.signals_generated.append(signal)

        # Generate order from signal
        if signal.direction == "BUY":
            order = Order(
                symbol=signal.symbol,
                side=OrderSide.BUY,
                quantity=signal.position_size,
                price=signal.entry_price,
                timestamp=signal.timestamp
            )

            # Check if we have enough cash
            required_capital = signal.position_size * signal.entry_price
            if self.current_cash < required_capital:
                self.logger.warning(
                    f"Insufficient capital for {signal.symbol}: "
                    f"need {required_capital:.2f}, have {self.current_cash:.2f}"
                )
                return None

            # Execute order
            order_id = await self.order_gateway.send_order(order)
            self.current_cash -= required_capital

            # Add position
            self.position_manager.add_position(
                signal.symbol,
                signal.position_size,
                signal.entry_price
            )

            return order_id

        elif signal.direction == "SELL":
            # Close existing position
            if signal.symbol in self.position_manager.positions:
                position = self.position_manager.close_position(signal.symbol, signal.entry_price)
                if position:
                    self.current_cash += signal.position_size * signal.entry_price

            return None

        return None

    async def update_market_prices(self, prices: Dict[str, float]) -> None:
        """Update market prices for all positions"""
        for symbol, price in prices.items():
            self.position_manager.update_position(symbol, price)

    async def close_all_positions(self) -> None:
        """Close all open positions at current market price"""
        symbols = list(self.position_manager.positions.keys())

        for symbol in symbols:
            position = self.position_manager.positions[symbol]
            self.position_manager.close_position(symbol, position.current_price)
            self.current_cash += position.quantity * position.current_price

        self.logger.info(f"Closed {len(symbols)} positions")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        position_summary = self.position_manager.get_positions_summary()
        unrealized_pnl = self.position_manager.get_total_unrealized_pnl()

        portfolio_value = self.current_cash + (
            sum(p.current_price * p.quantity for p in self.position_manager.positions.values())
        )

        total_pnl = portfolio_value - self.initial_capital + sum(
            p.unrealized_pnl for p in self.position_manager.closed_positions
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'current_cash': self.current_cash,
            'portfolio_value': portfolio_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl / self.initial_capital if self.initial_capital > 0 else 0,
            'unrealized_pnl': unrealized_pnl,
            'position_heat': position_summary['total_exposure'],
            'open_positions': position_summary['open_positions'],
            'closed_positions': len(self.position_manager.closed_positions),
            'total_signals': len(self.signals_generated),
        }

    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate real-time performance metrics"""
        summary = self.get_portfolio_summary()

        # Calculate daily metrics
        closed_pnls = [p.unrealized_pnl for p in self.position_manager.closed_positions]

        if not closed_pnls:
            win_rate = 0.0
            profit_factor = 0.0
        else:
            wins = sum(1 for pnl in closed_pnls if pnl > 0)
            win_rate = wins / len(closed_pnls) if closed_pnls else 0.0

            total_wins = sum(pnl for pnl in closed_pnls if pnl > 0)
            total_losses = abs(sum(pnl for pnl in closed_pnls if pnl < 0))
            profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        return {
            'portfolio_value': summary['portfolio_value'],
            'total_pnl': summary['total_pnl'],
            'total_pnl_pct': summary['total_pnl_pct'],
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'trades_executed': len(self.position_manager.closed_positions),
            'signals_generated': summary['total_signals'],
        }


__all__ = [
    'RealtimeTradingEngine',
    'PositionManager',
    'OrderGateway',
    'Order',
    'Position',
    'LiveSignal',
    'OrderSide',
    'OrderStatus',
    'PositionStatus',
]
