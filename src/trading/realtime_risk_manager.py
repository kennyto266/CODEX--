"""
Real-time Risk Management System

Monitors and controls risk in live trading operations.

Features:
    - Position size limits enforcement
    - Dynamic stop-loss calculation
    - Portfolio heat monitoring
    - Risk-adjusted position sizing
    - Automated risk alerts
    - Correlation-based risk assessment
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger("hk_quant_system.trading.risk_manager")


class AlertLevel(str, Enum):
    """Risk alert level"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AlertAction(str, Enum):
    """Risk alert action"""
    REDUCE_POSITION = "REDUCE_POSITION"
    CLOSE_POSITION = "CLOSE_POSITION"
    INCREASE_MONITORING = "INCREASE_MONITORING"
    NO_ACTION = "NO_ACTION"


@dataclass
class RiskAlert:
    """Risk alert"""
    level: AlertLevel
    message: str
    timestamp: datetime
    symbol: Optional[str] = None
    action: AlertAction = AlertAction.NO_ACTION
    severity_score: float = 0.5


class RealtimeRiskManager:
    """Real-time risk management system"""

    def __init__(self,
                 max_position_size: float = 100000.0,
                 max_portfolio_heat: float = 500000.0,
                 max_daily_loss: float = 50000.0,
                 max_drawdown: float = -0.20):
        """
        Initialize risk manager

        Args:
            max_position_size: Maximum size per position
            max_portfolio_heat: Maximum total portfolio exposure
            max_daily_loss: Maximum loss per day
            max_drawdown: Maximum drawdown tolerance
        """
        self.max_position_size = max_position_size
        self.max_portfolio_heat = max_portfolio_heat
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown

        self.alerts: List[RiskAlert] = []
        self.daily_pnl = 0.0
        self.peak_portfolio_value = 0.0
        self.current_portfolio_value = 0.0

        self.logger = logging.getLogger("hk_quant_system.trading.risk_manager")

    def check_position_limits(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Check if position respects limits

        Args:
            symbol: Symbol
            quantity: Position quantity
            price: Entry price

        Returns:
            True if within limits, False otherwise
        """
        position_value = quantity * price

        if position_value > self.max_position_size:
            self._create_alert(
                AlertLevel.WARNING,
                f"Position size {position_value:.2f} exceeds limit {self.max_position_size:.2f}",
                symbol,
                AlertAction.REDUCE_POSITION
            )
            return False

        return True

    def check_portfolio_heat(self, current_heat: float) -> bool:
        """Check if portfolio heat is within limits"""
        if current_heat > self.max_portfolio_heat:
            self._create_alert(
                AlertLevel.CRITICAL,
                f"Portfolio heat {current_heat:.2f} exceeds limit {self.max_portfolio_heat:.2f}",
                None,
                AlertAction.REDUCE_POSITION
            )
            return False

        return True

    def check_daily_loss(self, daily_pnl: float) -> bool:
        """Check if daily loss exceeds limit"""
        if daily_pnl < -self.max_daily_loss:
            self._create_alert(
                AlertLevel.CRITICAL,
                f"Daily loss {daily_pnl:.2f} exceeds limit {self.max_daily_loss:.2f}",
                None,
                AlertAction.CLOSE_POSITION
            )
            return False

        return True

    def check_drawdown(self, current_value: float, peak_value: float) -> bool:
        """Check if drawdown exceeds limit"""
        if peak_value > 0:
            drawdown = (current_value - peak_value) / peak_value
            if drawdown < self.max_drawdown:
                self._create_alert(
                    AlertLevel.CRITICAL,
                    f"Drawdown {drawdown:.2%} exceeds limit {self.max_drawdown:.2%}",
                    None,
                    AlertAction.CLOSE_POSITION
                )
                return False

        return True

    def calculate_dynamic_stoploss(self,
                                   entry_price: float,
                                   volatility: float,
                                   atr: Optional[float] = None) -> float:
        """
        Calculate dynamic stop-loss based on volatility

        Args:
            entry_price: Entry price
            volatility: Recent volatility (annualized)
            atr: Average True Range (optional)

        Returns:
            Stop-loss price
        """
        if atr:
            # Use ATR for stop-loss
            stoploss = entry_price - (2.0 * atr)
        else:
            # Use volatility for stop-loss
            daily_vol = volatility / np.sqrt(252)
            stoploss = entry_price * (1 - 2 * daily_vol)

        return stoploss

    def calculate_position_size(self,
                               signal_confidence: float,
                               portfolio_value: float,
                               volatility: float,
                               max_risk_per_trade: float = 0.02) -> float:
        """
        Calculate position size based on risk and confidence

        Args:
            signal_confidence: Signal confidence (0-1)
            portfolio_value: Current portfolio value
            volatility: Expected volatility
            max_risk_per_trade: Maximum risk per trade (% of portfolio)

        Returns:
            Position size
        """
        # Base position size on confidence
        confidence_multiplier = 0.5 + (signal_confidence * 0.5)  # 0.5x to 1.0x

        # Adjust for volatility (lower vol = larger position)
        vol_multiplier = 1.0 / (1.0 + volatility)

        # Risk-based position sizing
        risk_amount = portfolio_value * max_risk_per_trade
        position_size = risk_amount * confidence_multiplier * vol_multiplier

        # Cap at max position size
        return min(position_size, self.max_position_size)

    def assess_correlation_risk(self, correlations: Dict[str, float]) -> float:
        """
        Assess portfolio risk based on position correlations

        Args:
            correlations: Dictionary of symbol pair correlations

        Returns:
            Risk score (0-1)
        """
        if not correlations:
            return 0.0

        # High correlations increase portfolio risk
        avg_correlation = np.mean(list(correlations.values()))

        # Convert correlation to risk score
        risk_score = max(0, min(1, avg_correlation))

        return risk_score

    def calculate_portfolio_heat(self, positions: Dict[str, Any]) -> float:
        """Calculate total portfolio exposure"""
        total_heat = 0.0

        for symbol, position in positions.items():
            if isinstance(position, dict):
                exposure = position.get('quantity', 0) * position.get('current_price', 0)
            else:
                exposure = position.quantity * position.current_price

            total_heat += abs(exposure)

        return total_heat

    def _create_alert(self,
                     level: AlertLevel,
                     message: str,
                     symbol: Optional[str] = None,
                     action: AlertAction = AlertAction.NO_ACTION) -> RiskAlert:
        """Create and log risk alert"""
        alert = RiskAlert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            severity_score=self._calculate_severity(level)
        )

        self.alerts.append(alert)

        log_method = getattr(self.logger, level.value.lower())
        log_method(f"Risk Alert [{alert.level}]: {message}")

        return alert

    @staticmethod
    def _calculate_severity(level: AlertLevel) -> float:
        """Calculate severity score based on alert level"""
        level_map = {
            AlertLevel.CRITICAL: 1.0,
            AlertLevel.WARNING: 0.5,
            AlertLevel.INFO: 0.2
        }
        return level_map.get(level, 0.0)

    def get_active_alerts(self) -> List[RiskAlert]:
        """Get recent active alerts"""
        return [alert for alert in self.alerts if alert.level != AlertLevel.INFO]

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk management summary"""
        return {
            'total_alerts': len(self.alerts),
            'active_alerts': len(self.get_active_alerts()),
            'max_position_size': self.max_position_size,
            'max_portfolio_heat': self.max_portfolio_heat,
            'max_daily_loss': self.max_daily_loss,
            'max_drawdown': self.max_drawdown,
            'recent_alerts': [
                {
                    'level': a.level.value,
                    'message': a.message,
                    'timestamp': a.timestamp.isoformat(),
                    'symbol': a.symbol
                } for a in self.alerts[-5:]  # Last 5 alerts
            ]
        }


class PositionRiskCalculator:
    """Calculate risk metrics for individual positions"""

    @staticmethod
    def calculate_position_var(entry_price: float,
                               quantity: float,
                               volatility: float,
                               confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk for a position

        Args:
            entry_price: Entry price
            quantity: Position quantity
            volatility: Annualized volatility
            confidence_level: Confidence level (default 95%)

        Returns:
            VaR in dollars
        """
        # Z-score for confidence level
        z_scores = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
        z = z_scores.get(confidence_level, 1.645)

        daily_vol = volatility / np.sqrt(252)
        var = entry_price * quantity * daily_vol * z

        return var

    @staticmethod
    def calculate_sharpe_contribution(position_return: float,
                                     position_volatility: float,
                                     portfolio_sharpe: float) -> float:
        """
        Calculate position's contribution to portfolio Sharpe ratio

        Args:
            position_return: Position return (%)
            position_volatility: Position volatility
            portfolio_sharpe: Portfolio Sharpe ratio

        Returns:
            Sharpe contribution
        """
        if position_volatility == 0:
            return 0.0

        position_sharpe = position_return / position_volatility
        contribution = (position_sharpe - portfolio_sharpe) / 10  # Normalized

        return max(-1, min(1, contribution))  # Bound to [-1, 1]


__all__ = [
    'RealtimeRiskManager',
    'PositionRiskCalculator',
    'RiskAlert',
    'AlertLevel',
    'AlertAction',
]
