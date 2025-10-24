"""
Signal Attribution Metrics

Extends performance metrics to provide signal-level attribution analysis.
Measures contribution of different signal types (price-only, alt-data-only, combined)
to overall portfolio performance.

Features:
    - Signal accuracy calculation
    - Signal contribution to Sharpe ratio
    - Win rate by signal type
    - Signal frequency analysis
    - Signal effectiveness scoring

Usage:
    analyzer = SignalAttributionAnalyzer()

    accuracy = analyzer.calculate_signal_accuracy(trades)
    attribution = analyzer.calculate_signal_attribution(
        price_trades, alt_trades, combined_trades
    )
    breakdown = analyzer.generate_signal_breakdown(trades)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from decimal import Decimal


class SignalType(str, Enum):
    """Type of trading signal"""
    PRICE_ONLY = "price_only"
    ALT_DATA_ONLY = "alt_data_only"
    COMBINED = "combined"


@dataclass
class TradeRecord:
    """Trade record for analysis"""
    trade_id: str
    signal_type: SignalType
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    confidence: float
    symbol: str
    duration_days: int = 0

    @property
    def return_pct(self) -> float:
        """Calculate return percentage"""
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price * 100

    @property
    def profitable(self) -> bool:
        """Check if trade was profitable"""
        return self.pnl > 0


@dataclass
class SignalMetrics:
    """Metrics for a single signal type"""
    signal_type: SignalType
    trade_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    avg_return_pct: float = 0.0

    max_gain: float = 0.0
    max_loss: float = 0.0

    avg_winning_trade: float = 0.0
    avg_losing_trade: float = 0.0

    profit_factor: float = 0.0
    expectancy: float = 0.0

    avg_confidence: float = 0.0
    avg_duration_days: float = 0.0

    returns_std: float = 0.0
    sharpe_contribution: float = 0.0

    total_trades_pct: float = 0.0
    total_pnl_contribution_pct: float = 0.0


@dataclass
class SignalBreakdown:
    """Complete signal analysis breakdown"""
    total_trades: int = 0
    total_pnl: float = 0.0

    price_metrics: SignalMetrics = field(default_factory=lambda: SignalMetrics(SignalType.PRICE_ONLY))
    alt_data_metrics: SignalMetrics = field(default_factory=lambda: SignalMetrics(SignalType.ALT_DATA_ONLY))
    combined_metrics: SignalMetrics = field(default_factory=lambda: SignalMetrics(SignalType.COMBINED))

    correlation_with_overall: Dict[str, float] = field(default_factory=dict)
    best_performing_signal_type: Optional[SignalType] = None
    worst_performing_signal_type: Optional[SignalType] = None


@dataclass
class SignalContribution:
    """Contribution of signal type to overall performance"""
    signal_type: SignalType
    trades_count: int
    total_return_contribution: float
    sharpe_contribution: float
    volatility_contribution: float
    win_rate_contribution: float
    risk_adjusted_return: float
    effectiveness_score: float  # 0-1 score of how well this signal performed


class SignalAttributionAnalyzer:
    """
    Analyzer for signal-level attribution metrics

    Computes performance metrics segregated by signal source (price, alt data, combined)
    to understand which signals are most valuable for portfolio performance.
    """

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.signal_attribution")

    def calculate_signal_accuracy(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate accuracy metrics for trading signals

        Args:
            trades: List of trade records with pnl and confidence

        Returns:
            Dictionary with accuracy metrics
        """
        try:
            if not trades:
                return {
                    'overall_accuracy': 0.0,
                    'win_rate': 0.0,
                    'profitable_trades': 0,
                    'losing_trades': 0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0
                }

            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
            losing_trades = total_trades - winning_trades

            winning_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
            losing_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

            total_wins = sum(winning_pnls) if winning_pnls else 0.0
            total_losses = abs(sum(losing_pnls)) if losing_pnls else 0.0

            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            avg_win = total_wins / len(winning_pnls) if winning_pnls else 0.0
            avg_loss = total_losses / len(losing_pnls) if losing_pnls else 0.0

            profit_factor = total_wins / total_losses if total_losses > 0 else (1.0 if total_wins > 0 else 0.0)

            return {
                'overall_accuracy': win_rate,
                'win_rate': win_rate,
                'profitable_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_trades': total_trades,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'total_wins': total_wins,
                'total_losses': total_losses
            }

        except Exception as e:
            self.logger.error(f"Error calculating signal accuracy: {e}")
            return {}

    def calculate_signal_attribution(
        self,
        price_trades: List[Dict[str, Any]],
        alt_trades: List[Dict[str, Any]],
        combined_trades: List[Dict[str, Any]],
        overall_sharpe: float = 0.0
    ) -> Dict[str, SignalContribution]:
        """
        Calculate attribution of different signal types to overall performance

        Args:
            price_trades: Trades from price signals only
            alt_trades: Trades from alt data signals only
            combined_trades: Trades from combined signals
            overall_sharpe: Overall portfolio Sharpe ratio

        Returns:
            Dictionary of signal types to their contributions
        """
        try:
            contributions = {}

            # Calculate metrics for each signal type
            for signal_type, trades in [
                (SignalType.PRICE_ONLY, price_trades),
                (SignalType.ALT_DATA_ONLY, alt_trades),
                (SignalType.COMBINED, combined_trades)
            ]:
                if not trades:
                    continue

                # Calculate total pnl and returns
                total_pnl = sum(t.get('pnl', 0) for t in trades)
                total_quantity = sum(t.get('quantity', 0) for t in trades)

                # Win rate
                winning = sum(1 for t in trades if t.get('pnl', 0) > 0)
                win_rate = winning / len(trades) if trades else 0.0

                # Return statistics
                returns = [t.get('pnl', 0) / max(t.get('quantity', 1), 1) for t in trades]
                returns_std = np.std(returns) if returns else 0.0

                # Calculate Sharpe contribution
                returns_mean = np.mean(returns) if returns else 0.0
                signal_sharpe = returns_mean / returns_std * np.sqrt(252) if returns_std > 0 else 0.0

                # Calculate effectiveness score (0-1)
                effectiveness = self._calculate_effectiveness_score(
                    trades, overall_sharpe
                )

                # Total contribution
                all_trades_pnl = sum(t.get('pnl', 0) for t in price_trades + alt_trades + combined_trades)
                pnl_contribution = total_pnl / all_trades_pnl if all_trades_pnl > 0 else 0.0

                contributions[signal_type.value] = SignalContribution(
                    signal_type=signal_type,
                    trades_count=len(trades),
                    total_return_contribution=total_pnl,
                    sharpe_contribution=signal_sharpe,
                    volatility_contribution=returns_std,
                    win_rate_contribution=win_rate,
                    risk_adjusted_return=returns_mean / returns_std if returns_std > 0 else 0.0,
                    effectiveness_score=effectiveness
                )

            return contributions

        except Exception as e:
            self.logger.error(f"Error calculating signal attribution: {e}")
            return {}

    def generate_signal_breakdown(
        self,
        trades: List[Dict[str, Any]]
    ) -> SignalBreakdown:
        """
        Generate comprehensive signal breakdown

        Args:
            trades: List of all trades with signal_type field

        Returns:
            SignalBreakdown with detailed metrics
        """
        try:
            breakdown = SignalBreakdown()
            breakdown.total_trades = len(trades)
            breakdown.total_pnl = sum(t.get('pnl', 0) for t in trades)

            # Segregate trades by signal type
            price_trades = [t for t in trades if t.get('signal_type') == SignalType.PRICE_ONLY]
            alt_trades = [t for t in trades if t.get('signal_type') == SignalType.ALT_DATA_ONLY]
            combined_trades = [t for t in trades if t.get('signal_type') == SignalType.COMBINED]

            # Calculate metrics for each type
            breakdown.price_metrics = self._calculate_signal_metrics(
                price_trades, SignalType.PRICE_ONLY, breakdown.total_trades, breakdown.total_pnl
            )
            breakdown.alt_data_metrics = self._calculate_signal_metrics(
                alt_trades, SignalType.ALT_DATA_ONLY, breakdown.total_trades, breakdown.total_pnl
            )
            breakdown.combined_metrics = self._calculate_signal_metrics(
                combined_trades, SignalType.COMBINED, breakdown.total_trades, breakdown.total_pnl
            )

            # Determine best and worst performers
            all_metrics = [
                breakdown.price_metrics,
                breakdown.alt_data_metrics,
                breakdown.combined_metrics
            ]
            valid_metrics = [m for m in all_metrics if m.trade_count > 0]

            if valid_metrics:
                best = max(valid_metrics, key=lambda m: m.sharpe_contribution)
                worst = min(valid_metrics, key=lambda m: m.sharpe_contribution)
                breakdown.best_performing_signal_type = best.signal_type
                breakdown.worst_performing_signal_type = worst.signal_type

            # Calculate correlations with overall performance
            breakdown.correlation_with_overall = self._calculate_correlations(
                price_trades, alt_trades, combined_trades
            )

            return breakdown

        except Exception as e:
            self.logger.error(f"Error generating signal breakdown: {e}")
            return SignalBreakdown()

    def calculate_signal_efficiency(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate efficiency metrics for signals

        Args:
            trades: List of trades

        Returns:
            Dictionary of efficiency metrics
        """
        try:
            if not trades:
                return {}

            # Calculate win rate
            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            total = len(trades)
            win_rate = wins / total if total > 0 else 0.0

            # Calculate average trade duration
            durations = [t.get('duration_days', 1) for t in trades if t.get('duration_days')]
            avg_duration = np.mean(durations) if durations else 0.0

            # Calculate risk-adjusted returns
            returns = [t.get('pnl', 0) for t in trades]
            total_pnl = sum(returns)
            std_pnl = np.std(returns) if returns else 0.0

            rar = total_pnl / std_pnl if std_pnl > 0 else 0.0

            # Calculate hit frequency (trades per day)
            dates = set(t.get('entry_date') for t in trades if t.get('entry_date'))
            date_range = len(dates) if dates else 1
            hit_frequency = len(trades) / date_range

            return {
                'win_rate': win_rate,
                'avg_trade_duration': avg_duration,
                'risk_adjusted_return': rar,
                'hit_frequency': hit_frequency,
                'trades_per_day': hit_frequency,
                'avg_pnl_per_trade': total_pnl / total if total > 0 else 0.0
            }

        except Exception as e:
            self.logger.error(f"Error calculating signal efficiency: {e}")
            return {}

    def _calculate_signal_metrics(
        self,
        trades: List[Dict[str, Any]],
        signal_type: SignalType,
        total_trades: int,
        total_pnl: float
    ) -> SignalMetrics:
        """Calculate metrics for a specific signal type"""
        metrics = SignalMetrics(signal_type=signal_type)

        if not trades:
            return metrics

        metrics.trade_count = len(trades)
        metrics.winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        metrics.losing_trades = metrics.trade_count - metrics.winning_trades

        metrics.win_rate = metrics.winning_trades / metrics.trade_count if metrics.trade_count > 0 else 0.0

        pnls = [t.get('pnl', 0) for t in trades]
        metrics.total_pnl = sum(pnls)
        metrics.avg_pnl = metrics.total_pnl / metrics.trade_count if metrics.trade_count > 0 else 0.0

        returns_pct = [t.get('return_pct', 0) if 'return_pct' in t else 0.0 for t in trades]
        metrics.avg_return_pct = np.mean(returns_pct) if returns_pct else 0.0

        winning_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
        losing_pnls = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

        metrics.max_gain = max(winning_pnls) if winning_pnls else 0.0
        metrics.max_loss = min(losing_pnls) if losing_pnls else 0.0

        metrics.avg_winning_trade = np.mean(winning_pnls) if winning_pnls else 0.0
        metrics.avg_losing_trade = np.mean(losing_pnls) if losing_pnls else 0.0

        total_wins = sum(winning_pnls) if winning_pnls else 0.0
        total_losses = abs(sum(losing_pnls)) if losing_pnls else 0.0
        metrics.profit_factor = total_wins / total_losses if total_losses > 0 else (1.0 if total_wins > 0 else 0.0)

        metrics.expectancy = (metrics.win_rate * metrics.avg_winning_trade) - \
                            ((1 - metrics.win_rate) * abs(metrics.avg_losing_trade))

        metrics.avg_confidence = np.mean([t.get('confidence', 0.5) for t in trades]) if trades else 0.0

        durations = [t.get('duration_days', 1) for t in trades if t.get('duration_days')]
        metrics.avg_duration_days = np.mean(durations) if durations else 0.0

        metrics.returns_std = np.std(returns_pct) if returns_pct else 0.0

        metrics.total_trades_pct = metrics.trade_count / total_trades if total_trades > 0 else 0.0
        metrics.total_pnl_contribution_pct = metrics.total_pnl / total_pnl if total_pnl > 0 else 0.0

        # Sharpe contribution
        if metrics.returns_std > 0:
            metrics.sharpe_contribution = (metrics.avg_return_pct / metrics.returns_std) * np.sqrt(252)
        else:
            metrics.sharpe_contribution = 0.0

        return metrics

    @staticmethod
    def _calculate_effectiveness_score(
        trades: List[Dict[str, Any]],
        overall_sharpe: float
    ) -> float:
        """Calculate effectiveness score for signal type"""
        if not trades:
            return 0.0

        # Win rate component
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        win_rate = wins / len(trades)

        # Average confidence component
        avg_confidence = np.mean([t.get('confidence', 0.5) for t in trades])

        # Profitability component
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        max_pnl = max(t.get('pnl', 0) for t in trades) if trades else 1.0
        profitability = total_pnl / (max_pnl * len(trades)) if max_pnl > 0 else 0.0

        # Combined effectiveness (weighted average)
        effectiveness = (win_rate * 0.4 + avg_confidence * 0.35 + np.clip(profitability, 0, 1) * 0.25)

        return float(np.clip(effectiveness, 0.0, 1.0))

    @staticmethod
    def _calculate_correlations(
        price_trades: List[Dict],
        alt_trades: List[Dict],
        combined_trades: List[Dict]
    ) -> Dict[str, float]:
        """Calculate correlations between signal types"""
        correlations = {}

        # Calculate average returns for each type
        price_returns = np.array([t.get('pnl', 0) for t in price_trades])
        alt_returns = np.array([t.get('pnl', 0) for t in alt_trades])
        combined_returns = np.array([t.get('pnl', 0) for t in combined_trades])

        # Calculate correlations only if arrays have same length and sufficient data
        try:
            if len(price_returns) > 1 and len(alt_returns) > 1 and len(price_returns) == len(alt_returns):
                corr = np.corrcoef(price_returns, alt_returns)[0, 1]
                if not np.isnan(corr):
                    correlations['price_vs_alt'] = float(corr)

            if len(price_returns) > 1 and len(combined_returns) > 1 and len(price_returns) == len(combined_returns):
                corr = np.corrcoef(price_returns, combined_returns)[0, 1]
                if not np.isnan(corr):
                    correlations['price_vs_combined'] = float(corr)

            if len(alt_returns) > 1 and len(combined_returns) > 1 and len(alt_returns) == len(combined_returns):
                corr = np.corrcoef(alt_returns, combined_returns)[0, 1]
                if not np.isnan(corr):
                    correlations['alt_vs_combined'] = float(corr)
        except (ValueError, IndexError):
            # If correlation calculation fails, return empty dict
            pass

        return correlations


__all__ = [
    'SignalAttributionAnalyzer',
    'SignalMetrics',
    'SignalBreakdown',
    'SignalContribution',
    'SignalType',
    'TradeRecord'
]
