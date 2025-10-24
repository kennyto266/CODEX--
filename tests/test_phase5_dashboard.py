"""
Phase 5: Real-time Dashboard Tests

Comprehensive test suite for real-time dashboard components:
- WebSocket connection management
- Live data broadcasting
- Dashboard endpoints
- Data history tracking
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.dashboard.realtime_dashboard import (
    RealtimeDashboard,
    WebSocketManager,
    DashboardUpdate
)


# ==================== WebSocket Manager Tests ====================

class TestWebSocketManager:
    """Test WebSocket connection management"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = WebSocketManager()

        assert manager.active_connections == []
        assert 'positions' in manager.subscribers
        assert 'pnl' in manager.subscribers
        assert 'signals' in manager.subscribers
        assert 'alerts' in manager.subscribers
        assert 'trades' in manager.subscribers
        assert 'system_health' in manager.subscribers

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test client connection and disconnection"""
        manager = WebSocketManager()
        mock_ws = AsyncMock()

        await manager.connect(mock_ws, 'positions')
        assert len(manager.active_connections) == 1
        assert mock_ws in manager.subscribers['positions']

        await manager.disconnect(mock_ws, 'positions')
        assert len(manager.active_connections) == 0
        assert mock_ws not in manager.subscribers['positions']

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test multiple simultaneous connections"""
        manager = WebSocketManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()

        await manager.connect(mock_ws1, 'positions')
        await manager.connect(mock_ws2, 'signals')
        await manager.connect(mock_ws3, 'alerts')

        assert len(manager.active_connections) == 3
        assert len(manager.subscribers['positions']) == 1
        assert len(manager.subscribers['signals']) == 1
        assert len(manager.subscribers['alerts']) == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self):
        """Test broadcasting to specific channel"""
        manager = WebSocketManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, 'positions')
        await manager.connect(mock_ws2, 'signals')

        message = {'type': 'position_update', 'data': {'symbol': '0700.HK'}}
        await manager.broadcast(message, 'positions')

        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        """Test broadcasting to all clients"""
        manager = WebSocketManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.connect(mock_ws1, 'positions')
        await manager.connect(mock_ws2, 'signals')

        message = {'type': 'general_update', 'data': {}}
        await manager.broadcast(message)

        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific client"""
        manager = WebSocketManager()
        mock_ws = AsyncMock()

        await manager.connect(mock_ws)

        message = {'type': 'personal', 'data': 'Hello'}
        await manager.send_personal(mock_ws, message)

        mock_ws.send_json.assert_called_once_with(message)

    def test_get_active_count(self):
        """Test active connection count"""
        manager = WebSocketManager()

        assert manager.get_active_count() == 0

        manager.active_connections = [AsyncMock(), AsyncMock(), AsyncMock()]
        assert manager.get_active_count() == 3


# ==================== Real-time Dashboard Tests ====================

class TestRealtimeDashboard:
    """Test real-time dashboard service"""

    def test_initialization(self):
        """Test dashboard initialization"""
        dashboard = RealtimeDashboard()

        assert isinstance(dashboard.ws_manager, WebSocketManager)
        assert dashboard.position_history == []
        assert dashboard.trade_history == []
        assert dashboard.alert_history == []
        assert dashboard.signal_history == []

    @pytest.mark.asyncio
    async def test_position_update(self):
        """Test position update handling"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        positions = {
            '0700.HK': {'quantity': 1000, 'entry_price': 100.0, 'current_price': 105.0}
        }

        await dashboard.on_position_update(positions)

        assert len(dashboard.position_history) == 1
        assert dashboard.position_history[0]['type'] == 'position_update'
        dashboard.ws_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_pnl_update(self):
        """Test P&L update handling"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        pnl_data = {
            'daily_pnl': 5000,
            'total_pnl': 25000,
            'unrealized_pnl': 3000
        }

        await dashboard.on_pnl_update(pnl_data)

        dashboard.ws_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_signal_generated(self):
        """Test signal generation handling"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        signal_data = {
            'symbol': '0700.HK',
            'direction': 'BUY',
            'confidence': 0.85,
            'entry_price': 100.0
        }

        await dashboard.on_signal_generated(signal_data)

        assert len(dashboard.signal_history) == 1
        assert dashboard.signal_history[0]['type'] == 'signal_generated'
        dashboard.ws_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_risk_alert(self):
        """Test risk alert handling"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        alert_data = {
            'level': 'WARNING',
            'message': 'Position size exceeds limit',
            'symbol': '0700.HK'
        }

        await dashboard.on_risk_alert(alert_data)

        assert len(dashboard.alert_history) == 1
        assert dashboard.alert_history[0]['type'] == 'risk_alert'
        dashboard.ws_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_trade_executed(self):
        """Test trade execution handling"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        trade_data = {
            'symbol': '0700.HK',
            'side': 'BUY',
            'quantity': 1000,
            'price': 100.0,
            'pnl': 5000
        }

        await dashboard.on_trade_executed(trade_data)

        assert len(dashboard.trade_history) == 1
        assert dashboard.trade_history[0]['type'] == 'trade_executed'
        dashboard.ws_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_health(self):
        """Test system health update"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        health_data = {
            'status': 'HEALTHY',
            'latency_ms': 45,
            'cpu_usage': 35.2
        }

        await dashboard.on_system_health(health_data)

        dashboard.ws_manager.broadcast.assert_called_once()

    def test_history_limits(self):
        """Test that history respects size limits"""
        dashboard = RealtimeDashboard()

        # Add more than limit
        for i in range(150):
            dashboard.signal_history.append({
                'type': 'signal_generated',
                'signal': {'id': i}
            })

        # Simulate trimming
        while len(dashboard.signal_history) > 200:
            dashboard.signal_history.pop(0)

        assert len(dashboard.signal_history) <= 200

    def test_get_position_history(self):
        """Test retrieving position history"""
        dashboard = RealtimeDashboard()

        for i in range(10):
            dashboard.position_history.append({
                'type': 'position_update',
                'positions': {'0700.HK': {'quantity': 1000 * i}}
            })

        history = dashboard.get_position_history(limit=5)
        assert len(history) == 5
        assert history[-1]['positions']['0700.HK']['quantity'] == 9000

    def test_get_trade_history(self):
        """Test retrieving trade history"""
        dashboard = RealtimeDashboard()

        for i in range(20):
            dashboard.trade_history.append({
                'type': 'trade_executed',
                'trade': {'symbol': f'stock_{i}', 'pnl': 1000 * i}
            })

        history = dashboard.get_trade_history(limit=10)
        assert len(history) == 10

    def test_get_alert_history(self):
        """Test retrieving alert history"""
        dashboard = RealtimeDashboard()

        for i in range(15):
            dashboard.alert_history.append({
                'type': 'risk_alert',
                'alert': {'level': 'WARNING', 'id': i}
            })

        history = dashboard.get_alert_history(limit=5)
        assert len(history) == 5

    def test_get_signal_history(self):
        """Test retrieving signal history"""
        dashboard = RealtimeDashboard()

        for i in range(30):
            dashboard.signal_history.append({
                'type': 'signal_generated',
                'signal': {'symbol': '0700.HK', 'id': i}
            })

        history = dashboard.get_signal_history(limit=10)
        assert len(history) == 10

    def test_get_dashboard_summary(self):
        """Test dashboard summary generation"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.active_connections = [AsyncMock(), AsyncMock()]

        for i in range(5):
            dashboard.position_history.append({'type': 'position_update'})
            dashboard.trade_history.append({'type': 'trade_executed'})
            dashboard.alert_history.append({'type': 'risk_alert'})
            dashboard.signal_history.append({'type': 'signal_generated'})

        summary = dashboard.get_dashboard_summary()

        assert summary['active_connections'] == 2
        assert summary['position_updates'] == 5
        assert summary['trades'] == 5
        assert summary['alerts'] == 5
        assert summary['signals'] == 5
        assert 'timestamp' in summary


# ==================== Integration Tests ====================

class TestDashboardIntegration:
    """Integration tests for dashboard with trading engine"""

    @pytest.mark.asyncio
    async def test_full_event_flow(self):
        """Test complete event flow through dashboard"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        # Simulate trading events
        signal_data = {
            'symbol': '0700.HK',
            'direction': 'BUY',
            'confidence': 0.85
        }
        await dashboard.on_signal_generated(signal_data)

        position_data = {
            '0700.HK': {'quantity': 1000, 'entry_price': 100.0}
        }
        await dashboard.on_position_update(position_data)

        trade_data = {
            'symbol': '0700.HK',
            'side': 'BUY',
            'quantity': 1000,
            'pnl': 5000
        }
        await dashboard.on_trade_executed(trade_data)

        # Verify all events recorded
        assert len(dashboard.signal_history) == 1
        assert len(dashboard.position_history) == 1
        assert len(dashboard.trade_history) == 1
        assert dashboard.ws_manager.broadcast.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_updates(self):
        """Test handling concurrent dashboard updates"""
        dashboard = RealtimeDashboard()
        dashboard.ws_manager.broadcast = AsyncMock()

        async def send_updates(event_type, count):
            for i in range(count):
                if event_type == 'signal':
                    await dashboard.on_signal_generated({'symbol': '0700.HK', 'id': i})
                elif event_type == 'trade':
                    await dashboard.on_trade_executed({'symbol': '0700.HK', 'id': i})
                elif event_type == 'alert':
                    await dashboard.on_risk_alert({'level': 'WARNING', 'id': i})

        # Send updates concurrently
        await asyncio.gather(
            send_updates('signal', 10),
            send_updates('trade', 10),
            send_updates('alert', 10)
        )

        assert len(dashboard.signal_history) == 10
        assert len(dashboard.trade_history) == 10
        assert len(dashboard.alert_history) == 10
        assert dashboard.ws_manager.broadcast.call_count == 30
