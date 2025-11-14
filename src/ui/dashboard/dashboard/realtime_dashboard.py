"""
Real-time Trading Dashboard

Provides WebSocket and HTTP endpoints for live trading data visualization.

Features:
    - WebSocket real-time position updates
    - Live P&L and portfolio tracking
    - Signal performance visualization
    - Risk metrics monitoring
    - Trade execution log
    - System health status
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import asdict, dataclass

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("hk_quant_system.dashboard.realtime")


@dataclass
class DashboardUpdate:
    """Real-time dashboard update"""
    timestamp: datetime
    update_type: str  # 'position', 'pnl', 'signal', 'alert', 'trade'
    data: Dict[str, Any]


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_connections: List[WebSocket] = []
        self.subscribers: Dict[str, Set[WebSocket]] = {
            'positions': set(),
            'pnl': set(),
            'signals': set(),
            'alerts': set(),
            'trades': set(),
            'system_health': set()
        }
        self.logger = logging.getLogger("hk_quant_system.dashboard.websocket")

    async def connect(self, websocket: WebSocket, channel: Optional[str] = None):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)

        if channel and channel in self.subscribers:
            self.subscribers[channel].add(websocket)

        self.logger.info(f"Client connected. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket, channel: Optional[str] = None):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if channel and channel in self.subscribers:
            self.subscribers[channel].discard(websocket)

        self.logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast message to all connected clients or to a specific channel"""
        if channel and channel in self.subscribers:
            target_connections = self.subscribers[channel]
        else:
            target_connections = self.active_connections

        disconnected = []
        for connection in target_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, channel)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            self.logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    def get_active_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


class RealtimeDashboard:
    """Real-time trading dashboard service"""

    def __init__(self):
        """Initialize dashboard"""
        self.ws_manager = WebSocketManager()
        self.position_history: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.alert_history: List[Dict] = []
        self.signal_history: List[Dict] = []
        self.logger = logging.getLogger("hk_quant_system.dashboard.realtime")

    async def on_position_update(self, positions: Dict[str, Any]):
        """Handle position update"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'position_update',
            'positions': positions
        }
        self.position_history.append(update)

        # Keep last 100 updates
        if len(self.position_history) > 100:
            self.position_history.pop(0)

        await self.ws_manager.broadcast(update, 'positions')
        self.logger.debug(f"Position update broadcast to {self.ws_manager.get_active_count()} clients")

    async def on_pnl_update(self, pnl_data: Dict[str, Any]):
        """Handle P&L update"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'pnl_update',
            'pnl': pnl_data
        }
        await self.ws_manager.broadcast(update, 'pnl')
        self.logger.debug(f"P&L update broadcast to {self.ws_manager.get_active_count()} clients")

    async def on_signal_generated(self, signal_data: Dict[str, Any]):
        """Handle signal generation"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'signal_generated',
            'signal': signal_data
        }
        self.signal_history.append(update)

        # Keep last 200 signals
        if len(self.signal_history) > 200:
            self.signal_history.pop(0)

        await self.ws_manager.broadcast(update, 'signals')
        self.logger.info(f"Signal generated: {signal_data.get('symbol')} {signal_data.get('direction')}")

    async def on_risk_alert(self, alert_data: Dict[str, Any]):
        """Handle risk alert"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'risk_alert',
            'alert': alert_data
        }
        self.alert_history.append(update)

        # Keep last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history.pop(0)

        await self.ws_manager.broadcast(update, 'alerts')
        self.logger.warning(f"Risk alert: {alert_data.get('message')}")

    async def on_trade_executed(self, trade_data: Dict[str, Any]):
        """Handle trade execution"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'trade_executed',
            'trade': trade_data
        }
        self.trade_history.append(update)

        # Keep last 200 trades
        if len(self.trade_history) > 200:
            self.trade_history.pop(0)

        await self.ws_manager.broadcast(update, 'trades')
        self.logger.info(f"Trade executed: {trade_data.get('symbol')} {trade_data.get('side')} x{trade_data.get('quantity')}")

    async def on_system_health(self, health_data: Dict[str, Any]):
        """Handle system health update"""
        update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'system_health',
            'health': health_data
        }
        await self.ws_manager.broadcast(update, 'system_health')

    def get_position_history(self, limit: int = 50) -> List[Dict]:
        """Get recent position updates"""
        return self.position_history[-limit:]

    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        return self.trade_history[-limit:]

    def get_alert_history(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return self.alert_history[-limit:]

    def get_signal_history(self, limit: int = 50) -> List[Dict]:
        """Get recent signals"""
        return self.signal_history[-limit:]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_connections': self.ws_manager.get_active_count(),
            'position_updates': len(self.position_history),
            'trades': len(self.trade_history),
            'alerts': len(self.alert_history),
            'signals': len(self.signal_history)
        }


def create_realtime_dashboard_routes(dashboard: RealtimeDashboard) -> APIRouter:
    """Create FastAPI router with real-time dashboard endpoints"""
    router = APIRouter(prefix="/api/live", tags=["live-trading"])

    @router.websocket("/ws/portfolio")
    async def websocket_portfolio_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live portfolio updates"""
        await dashboard.ws_manager.connect(websocket, 'positions')
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                # Echo back or handle commands
                if data.startswith("PING"):
                    await dashboard.ws_manager.send_personal(websocket, {"type": "PONG"})
        except WebSocketDisconnect:
            await dashboard.ws_manager.disconnect(websocket, 'positions')

    @router.websocket("/ws/pnl")
    async def websocket_pnl_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live P&L updates"""
        await dashboard.ws_manager.connect(websocket, 'pnl')
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("PING"):
                    await dashboard.ws_manager.send_personal(websocket, {"type": "PONG"})
        except WebSocketDisconnect:
            await dashboard.ws_manager.disconnect(websocket, 'pnl')

    @router.websocket("/ws/signals")
    async def websocket_signals_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live signal updates"""
        await dashboard.ws_manager.connect(websocket, 'signals')
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("PING"):
                    await dashboard.ws_manager.send_personal(websocket, {"type": "PONG"})
        except WebSocketDisconnect:
            await dashboard.ws_manager.disconnect(websocket, 'signals')

    @router.websocket("/ws/alerts")
    async def websocket_alerts_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live alert updates"""
        await dashboard.ws_manager.connect(websocket, 'alerts')
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("PING"):
                    await dashboard.ws_manager.send_personal(websocket, {"type": "PONG"})
        except WebSocketDisconnect:
            await dashboard.ws_manager.disconnect(websocket, 'alerts')

    @router.websocket("/ws/trades")
    async def websocket_trades_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live trade updates"""
        await dashboard.ws_manager.connect(websocket, 'trades')
        try:
            while True:
                data = await websocket.receive_text()
                if data.startswith("PING"):
                    await dashboard.ws_manager.send_personal(websocket, {"type": "PONG"})
        except WebSocketDisconnect:
            await dashboard.ws_manager.disconnect(websocket, 'trades')

    @router.get("/positions")
    async def get_live_positions() -> Dict[str, Any]:
        """Get current live positions"""
        return {
            'timestamp': datetime.now().isoformat(),
            'positions_history': dashboard.get_position_history(limit=10)
        }

    @router.get("/pnl")
    async def get_live_pnl() -> Dict[str, Any]:
        """Get live P&L"""
        return {
            'timestamp': datetime.now().isoformat(),
            'message': 'P&L data available via WebSocket'
        }

    @router.get("/signals")
    async def get_live_signals() -> Dict[str, Any]:
        """Get recent signals"""
        return {
            'timestamp': datetime.now().isoformat(),
            'signals': dashboard.get_signal_history(limit=20),
            'total_signals': len(dashboard.signal_history)
        }

    @router.get("/alerts")
    async def get_live_alerts() -> Dict[str, Any]:
        """Get recent risk alerts"""
        return {
            'timestamp': datetime.now().isoformat(),
            'alerts': dashboard.get_alert_history(limit=10),
            'total_alerts': len(dashboard.alert_history)
        }

    @router.get("/trades")
    async def get_live_trades() -> Dict[str, Any]:
        """Get recent trades"""
        return {
            'timestamp': datetime.now().isoformat(),
            'trades': dashboard.get_trade_history(limit=20),
            'total_trades': len(dashboard.trade_history)
        }

    @router.get("/summary")
    async def get_dashboard_summary() -> Dict[str, Any]:
        """Get dashboard summary"""
        return dashboard.get_dashboard_summary()

    @router.get("/ws-connections")
    async def get_websocket_connections() -> Dict[str, int]:
        """Get current WebSocket connection count"""
        return {
            'active_connections': dashboard.ws_manager.get_active_count()
        }

    return router


__all__ = [
    'RealtimeDashboard',
    'WebSocketManager',
    'DashboardUpdate',
    'create_realtime_dashboard_routes'
]
