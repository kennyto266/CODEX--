"""
Phase 5: Real-time Trading Integration Tests

Comprehensive test suite for real-time trading components:
- RealtimeTradingEngine
- PositionManager
- OrderGateway
- RealtimeRiskManager
- RealtimePerformanceMonitor
"""

import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.trading.realtime_trading_engine import (
    RealtimeTradingEngine, PositionManager, OrderGateway,
    Order, Position, LiveSignal, OrderSide, OrderStatus
)
from src.trading.realtime_risk_manager import (
    RealtimeRiskManager, PositionRiskCalculator,
    AlertLevel, RiskAlert
)
from src.monitoring.realtime_performance_monitor import (
    RealtimePerformanceMonitor, MetricsAggregator, SystemHealth
)


# ==================== Position Manager Tests ====================

class TestPositionManager:
    """Test position management"""

    def test_add_position(self):
        """Test adding a position"""
        manager = PositionManager()
        position = manager.add_position('0700.HK', 1000, 100.0)

        assert position.symbol == '0700.HK'
        assert position.quantity == 1000
        assert position.entry_price == 100.0
        assert '0700.HK' in manager.positions

    def test_update_position(self):
        """Test updating position price"""
        manager = PositionManager()
        manager.add_position('0700.HK', 1000, 100.0)
        manager.update_position('0700.HK', 105.0)

        position = manager.positions['0700.HK']
        assert position.current_price == 105.0
        assert position.unrealized_pnl == 5000.0  # (105-100)*1000

    def test_close_position(self):
        """Test closing a position"""
        manager = PositionManager()
        manager.add_position('0700.HK', 1000, 100.0)
        closed = manager.close_position('0700.HK', 105.0)

        assert closed.unrealized_pnl == 5000.0
        assert '0700.HK' not in manager.positions
        assert len(manager.closed_positions) == 1

    def test_portfolio_value(self):
        """Test portfolio value calculation"""
        manager = PositionManager()
        manager.add_position('0700.HK', 1000, 100.0)
        manager.update_position('0700.HK', 105.0)

        value = manager.get_portfolio_value(cash=50000)
        assert value == 50000 + 105000  # cash + position value

    def test_position_heat(self):
        """Test portfolio heat calculation"""
        manager = PositionManager()
        manager.add_position('0700.HK', 1000, 100.0)
        manager.add_position('0388.HK', 500, 200.0)
        manager.update_position('0700.HK', 100.0)
        manager.update_position('0388.HK', 200.0)

        heat = manager.get_position_heat()
        assert heat == 100000 + 100000  # sum of position exposures


# ==================== Order Gateway Tests ====================

class TestOrderGateway:
    """Test order execution"""

    @pytest.mark.asyncio
    async def test_send_order(self):
        """Test sending an order"""
        gateway = OrderGateway()
        order = Order(
            symbol='0700.HK',
            side=OrderSide.BUY,
            quantity=1000,
            price=100.0,
            timestamp=datetime.now()
        )

        order_id = await gateway.send_order(order)
        assert order_id is not None
        assert order_id in gateway.orders

    @pytest.mark.asyncio
    async def test_order_execution(self):
        """Test order execution simulation"""
        gateway = OrderGateway()
        order = Order(
            symbol='0700.HK',
            side=OrderSide.BUY,
            quantity=1000,
            price=100.0,
            timestamp=datetime.now()
        )

        order_id = await gateway.send_order(order)
        await asyncio.sleep(0.3)  # Wait for execution

        executed_order = gateway.orders[order_id]
        assert executed_order.status == OrderStatus.FILLED
        assert executed_order.filled_quantity == 1000

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Test order cancellation"""
        gateway = OrderGateway()
        order = Order(
            symbol='0700.HK',
            side=OrderSide.BUY,
            quantity=1000,
            price=100.0,
            timestamp=datetime.now()
        )

        order_id = await gateway.send_order(order)
        cancelled = await gateway.cancel_order(order_id)

        # Should fail to cancel filled order
        assert not cancelled or gateway.orders[order_id].status == OrderStatus.FILLED


# ==================== Real-time Trading Engine Tests ====================

class TestRealtimeTradingEngine:
    """Test real-time trading engine"""

    def test_initialization(self):
        """Test engine initialization"""
        engine = RealtimeTradingEngine(initial_capital=1000000)

        assert engine.initial_capital == 1000000
        assert engine.current_cash == 1000000
        assert not engine.is_trading

    @pytest.mark.asyncio
    async def test_start_stop_trading(self):
        """Test starting and stopping trading"""
        engine = RealtimeTradingEngine()

        await engine.start_trading()
        assert engine.is_trading

        await engine.stop_trading()
        assert not engine.is_trading

    @pytest.mark.asyncio
    async def test_process_buy_signal(self):
        """Test processing buy signal"""
        engine = RealtimeTradingEngine(initial_capital=1000000)
        await engine.start_trading()

        signal = LiveSignal(
            symbol='0700.HK',
            timestamp=datetime.now(),
            direction='BUY',
            confidence=0.85,
            entry_price=100.0,
            target_price=110.0,
            stop_loss=95.0,
            position_size=1000,
            reason="Price above MA with high confidence"
        )

        order_id = await engine.process_signal(signal)

        assert order_id is not None
        assert '0700.HK' in engine.position_manager.positions
        assert engine.current_cash < 1000000  # Capital reduced

    @pytest.mark.asyncio
    async def test_process_sell_signal(self):
        """Test processing sell signal"""
        engine = RealtimeTradingEngine(initial_capital=1000000)
        await engine.start_trading()

        # Add position first
        engine.position_manager.add_position('0700.HK', 1000, 100.0)
        engine.current_cash -= 100000

        # Process sell signal
        signal = LiveSignal(
            symbol='0700.HK',
            timestamp=datetime.now(),
            direction='SELL',
            confidence=0.85,
            entry_price=105.0,
            target_price=110.0,
            stop_loss=95.0,
            position_size=1000,
            reason="Price near target, take profit"
        )

        await engine.process_signal(signal)

        assert '0700.HK' not in engine.position_manager.positions
        assert engine.current_cash == 1000000 + 5000  # Profit from close

    def test_portfolio_summary(self):
        """Test portfolio summary"""
        engine = RealtimeTradingEngine(initial_capital=1000000)
        engine.position_manager.add_position('0700.HK', 1000, 100.0)
        engine.position_manager.update_position('0700.HK', 105.0)
        engine.current_cash = 900000

        summary = engine.get_portfolio_summary()

        assert summary['initial_capital'] == 1000000
        assert summary['current_cash'] == 900000
        assert summary['unrealized_pnl'] == 5000


# ==================== Risk Manager Tests ====================

class TestRealtimeRiskManager:
    """Test real-time risk management"""

    def test_initialization(self):
        """Test risk manager initialization"""
        manager = RealtimeRiskManager()

        assert manager.max_position_size == 100000.0
        assert manager.max_portfolio_heat == 500000.0

    def test_check_position_limits(self):
        """Test position limit checking"""
        manager = RealtimeRiskManager(max_position_size=100000)

        # Within limit
        assert manager.check_position_limits('0700.HK', 1000, 50.0)

        # Exceeds limit
        assert not manager.check_position_limits('0700.HK', 10000, 50.0)

    def test_dynamic_stoploss(self):
        """Test dynamic stop-loss calculation"""
        manager = RealtimeRiskManager()

        stoploss = manager.calculate_dynamic_stoploss(
            entry_price=100.0,
            volatility=0.20,
            atr=None
        )

        assert stoploss < 100.0  # Stop should be below entry

    def test_position_sizing(self):
        """Test position sizing calculation"""
        manager = RealtimeRiskManager()

        size = manager.calculate_position_size(
            signal_confidence=0.85,
            portfolio_value=1000000,
            volatility=0.20
        )

        assert size > 0
        assert size <= manager.max_position_size

    def test_correlation_risk(self):
        """Test correlation risk assessment"""
        manager = RealtimeRiskManager()

        correlations = {
            'pair_1': 0.8,
            'pair_2': 0.7,
            'pair_3': 0.6
        }

        risk = manager.assess_correlation_risk(correlations)

        assert 0 <= risk <= 1

    def test_risk_alert(self):
        """Test risk alert generation"""
        manager = RealtimeRiskManager(max_portfolio_heat=100000)

        # Should trigger alert
        assert not manager.check_portfolio_heat(150000)
        assert len(manager.get_active_alerts()) > 0


# ==================== Performance Monitor Tests ====================

class TestRealtimePerformanceMonitor:
    """Test performance monitoring"""

    def test_initialization(self):
        """Test monitor initialization"""
        monitor = RealtimePerformanceMonitor()

        assert monitor.trades_executed == 0
        assert monitor.signals_generated == 0

    def test_record_metric(self):
        """Test metric recording"""
        monitor = RealtimePerformanceMonitor()

        monitor.record_metric('TEST_METRIC', 100.0, symbol='0700.HK')

        assert len(monitor.metrics) == 1
        assert monitor.metrics[0].metric_value == 100.0

    def test_record_trade(self):
        """Test trade recording"""
        monitor = RealtimePerformanceMonitor()

        monitor.record_trade('0700.HK', pnl=1000.0, duration_seconds=3600)

        assert monitor.trades_executed == 1
        assert len(monitor.daily_trades) == 1

    def test_win_rate(self):
        """Test win rate calculation"""
        monitor = RealtimePerformanceMonitor()

        monitor.record_trade('0700.HK', pnl=1000.0, duration_seconds=3600)
        monitor.record_trade('0388.HK', pnl=-500.0, duration_seconds=1800)
        monitor.record_trade('1398.HK', pnl=1500.0, duration_seconds=5400)

        win_rate = monitor.get_win_rate()

        assert win_rate == 2/3  # 2 wins out of 3 trades

    def test_signal_effectiveness(self):
        """Test signal effectiveness calculation"""
        monitor = RealtimePerformanceMonitor()

        monitor.signals_generated = 3
        monitor.record_trade('0700.HK', pnl=1000.0, duration_seconds=3600)
        monitor.record_trade('0388.HK', pnl=500.0, duration_seconds=1800)

        effectiveness = monitor.get_signal_effectiveness()

        assert 0 <= effectiveness <= 1

    def test_performance_summary(self):
        """Test performance summary"""
        monitor = RealtimePerformanceMonitor()

        monitor.signals_generated = 10
        monitor.record_trade('0700.HK', pnl=1000.0, duration_seconds=3600)
        monitor.record_trade('0388.HK', pnl=500.0, duration_seconds=1800)

        summary = monitor.get_performance_summary()

        assert summary['trades_executed'] == 2
        assert summary['signals_generated'] == 10
        assert 'win_rate' in summary
        assert 'realized_sharpe' in summary


# ==================== Integration Tests ====================

class TestPhase5Integration:
    """Integration tests for Phase 5 components"""

    @pytest.mark.asyncio
    async def test_full_trading_cycle(self):
        """Test complete trading cycle"""
        engine = RealtimeTradingEngine(initial_capital=1000000)
        risk_manager = RealtimeRiskManager()
        monitor = RealtimePerformanceMonitor()

        await engine.start_trading()

        # Check risk before trading
        assert risk_manager.check_position_limits('0700.HK', 1000, 100.0)

        # Generate and process signal
        signal = LiveSignal(
            symbol='0700.HK',
            timestamp=datetime.now(),
            direction='BUY',
            confidence=0.85,
            entry_price=100.0,
            target_price=110.0,
            stop_loss=95.0,
            position_size=1000,
            reason="Strong momentum signal with alt-data confirmation"
        )

        order_id = await engine.process_signal(signal)
        assert order_id is not None

        # Record metrics
        monitor.record_signal('0700.HK', 'BUY', 0.85)
        monitor.record_trade('0700.HK', pnl=5000.0, duration_seconds=3600)

        # Verify state
        assert len(engine.position_manager.positions) > 0 or len(engine.position_manager.closed_positions) > 0
        assert monitor.signals_generated == 1
        assert monitor.trades_executed == 1

        await engine.stop_trading()

    @pytest.mark.asyncio
    async def test_multi_symbol_trading(self):
        """Test trading multiple symbols"""
        engine = RealtimeTradingEngine(initial_capital=5000000)
        await engine.start_trading()

        symbols = ['0700.HK', '0388.HK', '1398.HK']

        for symbol in symbols:
            signal = LiveSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                direction='BUY',
                confidence=0.75,
                entry_price=100.0,
                target_price=105.0,
                stop_loss=95.0,
                position_size=1000,
                reason="Multi-symbol portfolio diversification signal"
            )

            await engine.process_signal(signal)

        assert len(engine.position_manager.positions) >= len(symbols)

        await engine.stop_trading()
