"""
Vectorized Metrics Module - Comprehensive Performance Analysis for Backtests

Provides deep performance analysis including:
- Portfolio metrics (return, volatility, drawdown)
- Risk metrics (VaR, CVaR, Sortino, Calmar)
- Trade analytics (win rate, profit factor, consecutive wins)
- Equity curve analysis (max drawdown, underwater plot metrics)
- Risk-adjusted returns
- Drawdown analysis

Architecture:
    Portfolio (from vectorbt) ↓
    ↙         ↓           ↘
Performance  Risk      Trade
 Metrics    Metrics   Analytics
    ↓         ↓           ↓
    └─────────┴───────────┘
           ↓
    MetricsReport
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict

logger = logging.getLogger("hk_quant_system.backtest.vectorbt_metrics")


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics."""
    total_return: float  # Total return %
    annualized_return: float  # Annualized return %
    volatility: float  # Annualized volatility
    sharpe_ratio: float  # Risk-adjusted return
    sortino_ratio: float  # Downside risk-adjusted return
    calmar_ratio: float  # Return / Max Drawdown
    max_drawdown: float  # Maximum drawdown %
    cumulative_return: float  # Cumulative return
    average_return: float  # Average period return


@dataclass
class RiskMetrics:
    """Risk analysis metrics."""
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional VaR (95%)
    var_99: float  # Value at Risk (99%)
    cvar_99: float  # Conditional VaR (99%)
    skewness: float  # Return skewness
    kurtosis: float  # Return kurtosis
    daily_std: float  # Daily volatility
    downside_deviation: float  # Downside volatility


@dataclass
class TradeMetrics:
    """Trade-level metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    avg_trade_duration: float


@dataclass
class DrawdownMetrics:
    """Drawdown analysis metrics."""
    max_drawdown: float
    max_drawdown_duration: int
    current_drawdown: float
    drawdown_events: int
    recovery_time: float  # Average recovery time


class VectorbtMetricsExtractor:
    """
    Extract comprehensive metrics from vectorbt Portfolio objects.

    Usage:
        portfolio = vbt.Portfolio.from_signals(...)
        extractor = VectorbtMetricsExtractor(portfolio, risk_free_rate=0.02)
        metrics = extractor.extract_all()
    """

    def __init__(self, portfolio, risk_free_rate: float = 0.02, period: str = 'daily'):
        """
        Initialize metrics extractor.

        Args:
            portfolio: vectorbt.Portfolio object
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino (default 2%)
            period: Time period ('daily', 'monthly', 'yearly')
        """
        self.portfolio = portfolio
        self.risk_free_rate = risk_free_rate
        self.period = period
        self.stats = portfolio.stats() if hasattr(portfolio, 'stats') else {}

    def extract_all(self) -> Dict[str, Any]:
        """Extract all metrics categories."""
        return {
            'performance': self._extract_performance_metrics(),
            'risk': self._extract_risk_metrics(),
            'trades': self._extract_trade_metrics(),
            'drawdown': self._extract_drawdown_metrics(),
            'equity_curve': self._extract_equity_curve_metrics(),
        }

    def _extract_performance_metrics(self) -> Dict[str, float]:
        """Extract portfolio performance metrics."""
        try:
            # Get returns
            total_return = float(self.portfolio.total_return()) if hasattr(self.portfolio, 'total_return') else 0

            # Get portfolio values
            portfolio_values = self.portfolio.portfolio_value()
            if hasattr(portfolio_values, 'values'):
                portfolio_values = portfolio_values.values

            # Calculate returns
            if len(portfolio_values) > 1:
                daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]
            else:
                daily_returns = np.array([0.0])

            # Annualized metrics (assuming 252 trading days)
            volatility = float(np.std(daily_returns) * np.sqrt(252))
            annualized_return = float(((1 + total_return) ** (252 / len(portfolio_values)) - 1) if len(portfolio_values) > 1 else 0)
            average_return = float(np.mean(daily_returns))

            # Risk-adjusted returns
            excess_return = annualized_return - self.risk_free_rate
            sharpe_ratio = float(excess_return / volatility) if volatility > 0 else 0

            # Sortino ratio (downside only)
            downside_returns = np.minimum(daily_returns, 0)
            downside_std = float(np.std(downside_returns) * np.sqrt(252))
            sortino_ratio = float(excess_return / downside_std) if downside_std > 0 else 0

            # Get from stats if available
            if isinstance(self.stats, dict):
                sharpe_ratio = float(self.stats.get('Sharpe Ratio', sharpe_ratio))
                sortino_ratio = float(self.stats.get('Sortino Ratio', sortino_ratio))

            # Calmar ratio
            max_dd = self._calculate_max_drawdown(portfolio_values)
            calmar_ratio = float(annualized_return / abs(max_dd)) if max_dd != 0 else 0

            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'max_drawdown': max_dd,
                'cumulative_return': total_return,
                'average_return': average_return,
            }
        except Exception as e:
            logger.error(f"Performance metrics extraction failed: {e}")
            return {}

    def _extract_risk_metrics(self) -> Dict[str, float]:
        """Extract risk metrics from returns distribution."""
        try:
            # Get daily returns
            daily_returns = self._get_daily_returns()
            if daily_returns is None or len(daily_returns) == 0:
                return {}

            # Value at Risk (VaR)
            var_95 = float(np.percentile(daily_returns, 5))
            var_99 = float(np.percentile(daily_returns, 1))

            # Conditional VaR (Expected Shortfall)
            cvar_95 = float(daily_returns[daily_returns <= var_95].mean())
            cvar_99 = float(daily_returns[daily_returns <= var_99].mean())

            # Distribution metrics
            skewness = float(self._calculate_skewness(daily_returns))
            kurtosis = float(self._calculate_kurtosis(daily_returns))

            # Volatility
            daily_std = float(np.std(daily_returns))
            downside_std = float(np.std(np.minimum(daily_returns, 0)))

            return {
                'var_95': var_95,
                'cvar_95': cvar_95,
                'var_99': var_99,
                'cvar_99': cvar_99,
                'skewness': skewness,
                'kurtosis': kurtosis,
                'daily_std': daily_std,
                'downside_deviation': downside_std,
            }
        except Exception as e:
            logger.error(f"Risk metrics extraction failed: {e}")
            return {}

    def _extract_trade_metrics(self) -> Dict[str, Any]:
        """Extract trade-level metrics."""
        try:
            if not hasattr(self.portfolio, 'trades'):
                return {}

            trades = self.portfolio.trades
            if not hasattr(trades, 'records') or len(trades.records) == 0:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0,
                    'consecutive_wins': 0,
                    'consecutive_losses': 0,
                    'avg_trade_duration': 0.0,
                }

            # Extract PnL from records
            pnls = [float(record.get('pnl', 0)) for record in trades.records]
            durations = [int(record.get('exit_idx', 0) - record.get('entry_idx', 0))
                        for record in trades.records]

            winning = [p for p in pnls if p > 0]
            losing = [p for p in pnls if p < 0]

            total_trades = len(pnls)
            winning_trades = len(winning)
            losing_trades = len(losing)
            win_rate = float(winning_trades / total_trades) if total_trades > 0 else 0

            # Profit factor
            gross_profit = sum(winning) if winning else 0
            gross_loss = abs(sum(losing)) if losing else 0
            profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else (1.0 if gross_profit > 0 else 0.0)

            # Average trades
            avg_win = float(np.mean(winning)) if winning else 0
            avg_loss = float(np.mean(losing)) if losing else 0
            largest_win = float(max(winning)) if winning else 0
            largest_loss = float(min(losing)) if losing else 0

            # Consecutive wins/losses
            consecutive_wins = self._calculate_consecutive(pnls, True)
            consecutive_losses = self._calculate_consecutive(pnls, False)

            # Average duration
            avg_duration = float(np.mean(durations)) if durations else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': largest_win,
                'largest_loss': largest_loss,
                'consecutive_wins': consecutive_wins,
                'consecutive_losses': consecutive_losses,
                'avg_trade_duration': avg_duration,
            }
        except Exception as e:
            logger.error(f"Trade metrics extraction failed: {e}")
            return {}

    def _extract_drawdown_metrics(self) -> Dict[str, Any]:
        """Extract drawdown analysis metrics."""
        try:
            portfolio_values = self.portfolio.portfolio_value()
            if hasattr(portfolio_values, 'values'):
                portfolio_values = portfolio_values.values

            if len(portfolio_values) == 0:
                return {}

            # Calculate running maximum
            running_max = np.maximum.accumulate(portfolio_values)

            # Calculate drawdown
            drawdown = (portfolio_values - running_max) / running_max

            # Max drawdown
            max_dd = float(np.min(drawdown))

            # Drawdown duration
            max_dd_idx = np.argmin(drawdown)
            max_dd_duration = 0
            if max_dd_idx > 0:
                for i in range(max_dd_idx - 1, -1, -1):
                    if drawdown[i] == 0:
                        max_dd_duration = max_dd_idx - i
                        break

            # Current drawdown
            current_dd = float(drawdown[-1]) if len(drawdown) > 0 else 0

            # Count drawdown events (crossing from 0 to negative)
            dd_events = 0
            in_drawdown = False
            for dd in drawdown:
                if dd < 0 and not in_drawdown:
                    dd_events += 1
                    in_drawdown = True
                elif dd == 0:
                    in_drawdown = False

            # Average recovery time (estimate)
            recovery_times = []
            in_dd = False
            dd_start = 0
            for i, dd in enumerate(drawdown):
                if dd < 0 and not in_dd:
                    dd_start = i
                    in_dd = True
                elif dd == 0 and in_dd:
                    recovery_times.append(i - dd_start)
                    in_dd = False

            avg_recovery = float(np.mean(recovery_times)) if recovery_times else 0

            return {
                'max_drawdown': max_dd,
                'max_drawdown_duration': max_dd_duration,
                'current_drawdown': current_dd,
                'drawdown_events': dd_events,
                'recovery_time': avg_recovery,
            }
        except Exception as e:
            logger.error(f"Drawdown metrics extraction failed: {e}")
            return {}

    def _extract_equity_curve_metrics(self) -> Dict[str, Any]:
        """Extract equity curve analysis metrics."""
        try:
            portfolio_values = self.portfolio.portfolio_value()
            if hasattr(portfolio_values, 'values'):
                portfolio_values = portfolio_values.values

            if len(portfolio_values) < 2:
                return {}

            # Equity curve statistics
            daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

            return {
                'equity_curve_length': len(portfolio_values),
                'positive_days': int(np.sum(daily_returns > 0)),
                'negative_days': int(np.sum(daily_returns < 0)),
                'flat_days': int(np.sum(daily_returns == 0)),
                'positive_day_rate': float(np.sum(daily_returns > 0) / len(daily_returns)) if len(daily_returns) > 0 else 0,
                'best_day': float(np.max(daily_returns)),
                'worst_day': float(np.min(daily_returns)),
            }
        except Exception as e:
            logger.error(f"Equity curve metrics extraction failed: {e}")
            return {}

    # Helper methods
    def _get_daily_returns(self) -> Optional[np.ndarray]:
        """Get daily returns from portfolio."""
        try:
            if hasattr(self.portfolio, 'daily_returns'):
                returns = self.portfolio.daily_returns()
                if returns is not None and hasattr(returns, 'values'):
                    return returns.values

            # Alternative: calculate from portfolio values
            portfolio_values = self.portfolio.portfolio_value()
            if hasattr(portfolio_values, 'values'):
                portfolio_values = portfolio_values.values

            if len(portfolio_values) > 1:
                return np.diff(portfolio_values) / portfolio_values[:-1]

            return None
        except Exception as e:
            logger.error(f"Failed to get daily returns: {e}")
            return None

    @staticmethod
    def _calculate_max_drawdown(portfolio_values: np.ndarray) -> float:
        """Calculate maximum drawdown."""
        if len(portfolio_values) == 0:
            return 0.0

        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        return float(np.min(drawdown))

    @staticmethod
    def _calculate_skewness(returns: np.ndarray) -> float:
        """Calculate return skewness."""
        if len(returns) < 3:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0.0

        return float(np.mean(((returns - mean) / std) ** 3))

    @staticmethod
    def _calculate_kurtosis(returns: np.ndarray) -> float:
        """Calculate return kurtosis."""
        if len(returns) < 4:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0.0

        return float(np.mean(((returns - mean) / std) ** 4) - 3)

    @staticmethod
    def _calculate_consecutive(pnls: List[float], wins: bool) -> int:
        """Calculate maximum consecutive wins or losses."""
        if not pnls:
            return 0

        target = lambda p: p > 0 if wins else p < 0
        max_consecutive = 0
        current_consecutive = 0

        for pnl in pnls:
            if target(pnl):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive


class MetricsReport:
    """Generate comprehensive metrics reports."""

    def __init__(self, extractor: VectorbtMetricsExtractor):
        """Initialize report generator."""
        self.extractor = extractor
        self.metrics = extractor.extract_all()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        result = {}
        for category, metrics in self.metrics.items():
            if isinstance(metrics, dict):
                result[category] = metrics
            else:
                result[category] = asdict(metrics)
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to DataFrame for easy viewing."""
        flat_metrics = {}
        for category, metrics in self.metrics.items():
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    flat_metrics[f"{category}_{key}"] = value

        return pd.DataFrame([flat_metrics])

    def to_summary_text(self) -> str:
        """Generate human-readable summary."""
        lines = ["=" * 60]
        lines.append("BACKTEST METRICS REPORT")
        lines.append("=" * 60)

        # Performance
        perf = self.metrics.get('performance', {})
        if perf:
            lines.append("\n📊 PERFORMANCE METRICS:")
            lines.append(f"  Total Return:        {perf.get('total_return', 0):.2%}")
            lines.append(f"  Annualized Return:   {perf.get('annualized_return', 0):.2%}")
            lines.append(f"  Volatility:          {perf.get('volatility', 0):.2%}")
            lines.append(f"  Sharpe Ratio:        {perf.get('sharpe_ratio', 0):.2f}")
            lines.append(f"  Sortino Ratio:       {perf.get('sortino_ratio', 0):.2f}")
            lines.append(f"  Calmar Ratio:        {perf.get('calmar_ratio', 0):.2f}")
            lines.append(f"  Max Drawdown:        {perf.get('max_drawdown', 0):.2%}")

        # Risk
        risk = self.metrics.get('risk', {})
        if risk:
            lines.append("\n⚠️  RISK METRICS:")
            lines.append(f"  VaR (95%):           {risk.get('var_95', 0):.2%}")
            lines.append(f"  CVaR (95%):          {risk.get('cvar_95', 0):.2%}")
            lines.append(f"  VaR (99%):           {risk.get('var_99', 0):.2%}")
            lines.append(f"  CVaR (99%):          {risk.get('cvar_99', 0):.2%}")
            lines.append(f"  Skewness:            {risk.get('skewness', 0):.2f}")
            lines.append(f"  Kurtosis:            {risk.get('kurtosis', 0):.2f}")

        # Trades
        trades = self.metrics.get('trades', {})
        if trades:
            lines.append("\n💹 TRADE METRICS:")
            lines.append(f"  Total Trades:        {trades.get('total_trades', 0)}")
            lines.append(f"  Winning Trades:      {trades.get('winning_trades', 0)}")
            lines.append(f"  Losing Trades:       {trades.get('losing_trades', 0)}")
            lines.append(f"  Win Rate:            {trades.get('win_rate', 0):.2%}")
            lines.append(f"  Profit Factor:       {trades.get('profit_factor', 0):.2f}")
            lines.append(f"  Avg Win:             {trades.get('avg_win', 0):.2f}")
            lines.append(f"  Avg Loss:            {trades.get('avg_loss', 0):.2f}")
            lines.append(f"  Avg Trade Duration:  {trades.get('avg_trade_duration', 0):.1f} days")

        # Drawdown
        dd = self.metrics.get('drawdown', {})
        if dd:
            lines.append("\n📉 DRAWDOWN ANALYSIS:")
            lines.append(f"  Max Drawdown:        {dd.get('max_drawdown', 0):.2%}")
            lines.append(f"  Max DD Duration:     {dd.get('max_drawdown_duration', 0)} days")
            lines.append(f"  Current Drawdown:    {dd.get('current_drawdown', 0):.2%}")
            lines.append(f"  DD Events:           {dd.get('drawdown_events', 0)}")
            lines.append(f"  Avg Recovery Time:   {dd.get('recovery_time', 0):.1f} days")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
