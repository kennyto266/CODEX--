"""
Real-time Performance Monitoring System

Monitors and reports on live trading performance metrics.

Features:
    - Real-time P&L calculation
    - Performance attribution
    - Signal effectiveness tracking
    - System health monitoring
    - Metrics aggregation and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger("hk_quant_system.monitoring.performance")


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: datetime
    metric_name: str
    metric_value: float
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health status"""
    timestamp: datetime
    data_feed_status: str  # 'ACTIVE', 'STALLED', 'ERROR'
    execution_latency_ms: float
    order_fill_rate: float  # 0-1
    signal_generation_rate: float  # signals per minute
    system_cpu_usage: float  # 0-100
    system_memory_usage: float  # 0-100


class RealtimePerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor

        Args:
            window_size: Number of recent metrics to keep
        """
        self.window_size = window_size
        self.metrics: List[PerformanceMetric] = []
        self.system_health_history: List[SystemHealth] = []

        self.trades_executed = 0
        self.signals_generated = 0
        self.daily_trades = []
        self.hourly_returns: Dict[int, float] = {}

        self.logger = logging.getLogger("hk_quant_system.monitoring.performance")

    def record_metric(self,
                     metric_name: str,
                     metric_value: float,
                     symbol: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value,
            symbol=symbol,
            metadata=metadata or {}
        )

        self.metrics.append(metric)

        # Maintain window size
        if len(self.metrics) > self.window_size:
            self.metrics.pop(0)

    def record_trade(self, symbol: str, pnl: float, duration_seconds: float) -> None:
        """Record a completed trade"""
        self.trades_executed += 1
        self.daily_trades.append({
            'symbol': symbol,
            'pnl': pnl,
            'duration': duration_seconds,
            'timestamp': datetime.now()
        })

        self.record_metric(
            'TRADE_PNL',
            pnl,
            symbol=symbol,
            metadata={'duration_seconds': duration_seconds}
        )

    def record_signal(self, symbol: str, signal_type: str, confidence: float) -> None:
        """Record a generated signal"""
        self.signals_generated += 1

        self.record_metric(
            'SIGNAL_GENERATED',
            confidence,
            symbol=symbol,
            metadata={'signal_type': signal_type}
        )

    def record_system_health(self, health: SystemHealth) -> None:
        """Record system health status"""
        self.system_health_history.append(health)

        # Maintain history
        if len(self.system_health_history) > self.window_size:
            self.system_health_history.pop(0)

    def get_realized_sharpe(self) -> float:
        """Calculate realized Sharpe ratio from trades"""
        if not self.daily_trades:
            return 0.0

        pnls = [t['pnl'] for t in self.daily_trades]
        daily_returns = np.array(pnls)

        if len(daily_returns) < 2:
            return 0.0

        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)

        if std_return == 0:
            return 0.0

        # Annualize if trades are intraday
        sharpe = (mean_return / std_return) * np.sqrt(252)

        return float(sharpe)

    def get_win_rate(self) -> float:
        """Get win rate from executed trades"""
        if not self.daily_trades:
            return 0.0

        wins = sum(1 for t in self.daily_trades if t['pnl'] > 0)
        return wins / len(self.daily_trades) if self.daily_trades else 0.0

    def get_avg_trade_duration(self) -> float:
        """Get average trade duration in seconds"""
        if not self.daily_trades:
            return 0.0

        durations = [t['duration'] for t in self.daily_trades]
        return float(np.mean(durations))

    def get_signal_effectiveness(self) -> float:
        """Get signal effectiveness (trades won / signals generated)"""
        if self.signals_generated == 0:
            return 0.0

        wins = sum(1 for t in self.daily_trades if t['pnl'] > 0)
        return wins / self.signals_generated

    def get_hourly_return(self, hour: Optional[int] = None) -> float:
        """Get return for a specific hour"""
        if hour is None:
            hour = datetime.now().hour

        return self.hourly_returns.get(hour, 0.0)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        daily_pnl = sum(t['pnl'] for t in self.daily_trades)
        avg_pnl = daily_pnl / len(self.daily_trades) if self.daily_trades else 0.0

        daily_trades = [t for t in self.daily_trades
                       if t['timestamp'].date() == datetime.now().date()]

        return {
            'timestamp': datetime.now().isoformat(),
            'trades_executed': self.trades_executed,
            'signals_generated': self.signals_generated,
            'daily_trades': len(daily_trades),
            'daily_pnl': daily_pnl,
            'avg_trade_pnl': avg_pnl,
            'win_rate': self.get_win_rate(),
            'realized_sharpe': self.get_realized_sharpe(),
            'signal_effectiveness': self.get_signal_effectiveness(),
            'avg_trade_duration': self.get_avg_trade_duration(),
            'avg_trade_duration_display': f"{self.get_avg_trade_duration():.0f}s",
        }

    def get_latest_metrics(self, metric_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest metrics"""
        metrics = self.metrics

        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]

        # Return latest entries
        latest = metrics[-limit:] if len(metrics) > limit else metrics

        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'metric_name': m.metric_name,
                'metric_value': m.metric_value,
                'symbol': m.symbol
            } for m in latest
        ]

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get current system health summary"""
        if not self.system_health_history:
            return {
                'status': 'UNKNOWN',
                'message': 'No health data available'
            }

        latest_health = self.system_health_history[-1]

        return {
            'timestamp': latest_health.timestamp.isoformat(),
            'data_feed_status': latest_health.data_feed_status,
            'execution_latency_ms': latest_health.execution_latency_ms,
            'order_fill_rate': f"{latest_health.order_fill_rate*100:.1f}%",
            'signal_generation_rate': f"{latest_health.signal_generation_rate:.1f}/min",
            'cpu_usage': f"{latest_health.system_cpu_usage:.1f}%",
            'memory_usage': f"{latest_health.system_memory_usage:.1f}%",
        }

    def get_hourly_metrics(self) -> Dict[int, Dict[str, Any]]:
        """Get metrics aggregated by hour"""
        hourly_data: Dict[int, List[Dict]] = {}

        for trade in self.daily_trades:
            hour = trade['timestamp'].hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(trade)

        result = {}
        for hour, trades in hourly_data.items():
            pnls = [t['pnl'] for t in trades]
            result[hour] = {
                'trades': len(trades),
                'pnl': sum(pnls),
                'avg_pnl': np.mean(pnls),
                'win_rate': sum(1 for p in pnls if p > 0) / len(pnls) if pnls else 0.0
            }

        return result

    def reset_daily_metrics(self) -> None:
        """Reset daily metrics"""
        self.daily_trades = []
        self.hourly_returns = {}

        self.logger.info("Daily metrics reset")


class MetricsAggregator:
    """Aggregates metrics from multiple sources"""

    def __init__(self):
        """Initialize metrics aggregator"""
        self.performance_monitor = RealtimePerformanceMonitor()
        self.metrics_cache: Dict[str, Any] = {}
        self.last_update = datetime.now()

    def update_metrics(self, portfolio_data: Dict[str, Any]) -> None:
        """Update aggregated metrics from portfolio data"""
        self.metrics_cache = {
            'portfolio_value': portfolio_data.get('portfolio_value', 0),
            'total_pnl': portfolio_data.get('total_pnl', 0),
            'total_pnl_pct': portfolio_data.get('total_pnl_pct', 0),
            'unrealized_pnl': portfolio_data.get('unrealized_pnl', 0),
            'open_positions': portfolio_data.get('open_positions', 0),
            'position_heat': portfolio_data.get('position_heat', 0),
        }

        self.last_update = datetime.now()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        perf_summary = self.performance_monitor.get_performance_summary()
        health_summary = self.performance_monitor.get_system_health_summary()

        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio': self.metrics_cache,
            'performance': perf_summary,
            'system_health': health_summary,
            'metrics_updated_at': self.last_update.isoformat(),
        }


__all__ = [
    'RealtimePerformanceMonitor',
    'MetricsAggregator',
    'PerformanceMetric',
    'SystemHealth',
]
