"""
Unified Risk Calculation Engine

Comprehensive risk management and calculation system.
Consolidates risk calculations from multiple modules into unified interface.

Features:
- Position-level risk metrics
- Portfolio-level risk metrics
- Value at Risk (VaR) calculations
- Stress testing and scenario analysis
- Risk limits monitoring
- Hedging recommendations

Used by: Portfolio manager, risk monitor, execution engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger("hk_quant_system.risk_calculator")


@dataclass
class Position:
    """Represents a trading position."""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    position_type: str  # 'LONG' or 'SHORT'

    @property
    def market_value(self) -> float:
        """Current market value."""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        if self.position_type == 'LONG':
            return self.quantity * (self.current_price - self.entry_price)
        else:
            return self.quantity * (self.entry_price - self.current_price)

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage."""
        return self.unrealized_pnl / (self.quantity * self.entry_price)


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics."""
    total_value: float
    total_margin_used: float
    available_margin: float
    margin_ratio: float  # used / available

    # Risk metrics
    portfolio_var_95: float  # 95% VaR
    portfolio_cvar_95: float  # Conditional VaR
    portfolio_var_99: float  # 99% VaR

    # Concentration risk
    largest_position_pct: float
    concentration_index: float  # Herfindahl

    # Correlation risk
    portfolio_beta: float
    portfolio_correlation_with_market: float

    # Liquidity risk
    illiquid_positions_pct: float

    def is_risk_acceptable(
        self,
        max_var: float = 0.05,  # 5% max VaR
        max_concentration: float = 0.3,  # 30% max concentration
        max_margin_ratio: float = 0.5,  # 50% max margin usage
    ) -> Tuple[bool, List[str]]:
        """Check if portfolio risk is within acceptable limits."""
        warnings = []

        if self.portfolio_var_95 > max_var:
            warnings.append(f"VaR {self.portfolio_var_95:.2%} exceeds limit {max_var:.2%}")

        if self.largest_position_pct > max_concentration:
            warnings.append(
                f"Concentration {self.largest_position_pct:.2%} exceeds limit {max_concentration:.2%}"
            )

        if self.margin_ratio > max_margin_ratio:
            warnings.append(
                f"Margin ratio {self.margin_ratio:.2%} exceeds limit {max_margin_ratio:.2%}"
            )

        return len(warnings) == 0, warnings


class UnifiedRiskCalculator:
    """
    Unified risk calculation engine.

    Provides comprehensive risk metrics for positions and portfolios.

    Example:
        >>> calculator = UnifiedRiskCalculator()
        >>> positions = [Position("0700.HK", 1000, 100, 102, "LONG")]
        >>> portfolio_risk = calculator.calculate_portfolio_risk(positions)
        >>> var_95 = calculator.calculate_var(returns, confidence=0.95)
    """

    def __init__(self, risk_free_rate: float = 0.03, lookback_days: int = 252):
        """
        Initialize risk calculator.

        Args:
            risk_free_rate: Annual risk-free rate
            lookback_days: Days for risk calculations
        """
        self.risk_free_rate = risk_free_rate
        self.lookback_days = lookback_days

    def calculate_position_risk(self, position: Position) -> Dict[str, float]:
        """
        Calculate risk metrics for a single position.

        Args:
            position: Position object

        Returns:
            Dictionary with risk metrics
        """
        return {
            'symbol': position.symbol,
            'market_value': position.market_value,
            'unrealized_pnl': position.unrealized_pnl,
            'unrealized_pnl_pct': position.unrealized_pnl_pct,
            'position_type': position.position_type,
        }

    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
        method: str = "historical",
    ) -> float:
        """
        Calculate Value at Risk.

        Args:
            returns: Return series
            confidence: Confidence level (0-1)
            method: 'historical' or 'parametric'

        Returns:
            VaR value (negative for losses)
        """
        if method == "historical":
            return returns.quantile(1 - confidence)

        elif method == "parametric":
            # Assume normal distribution
            mean = returns.mean()
            std = returns.std()
            z_score = np.percentile(np.random.normal(0, 1, 10000), (1 - confidence) * 100)
            return mean + z_score * std

        else:
            raise ValueError(f"Unknown VaR method: {method}")

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        Args:
            returns: Return series
            confidence: Confidence level

        Returns:
            CVaR value
        """
        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()

    def calculate_portfolio_risk(
        self,
        positions: List[Position],
        historical_prices: Optional[pd.DataFrame] = None,
    ) -> PortfolioRisk:
        """
        Calculate portfolio-level risk metrics.

        Args:
            positions: List of Position objects
            historical_prices: Historical price data for correlation

        Returns:
            PortfolioRisk object
        """
        if not positions:
            return PortfolioRisk(
                total_value=0,
                total_margin_used=0,
                available_margin=0,
                margin_ratio=0,
                portfolio_var_95=0,
                portfolio_cvar_95=0,
                portfolio_var_99=0,
                largest_position_pct=0,
                concentration_index=0,
                portfolio_beta=0,
                portfolio_correlation_with_market=0,
                illiquid_positions_pct=0,
            )

        # Calculate total value
        total_value = sum(pos.market_value for pos in positions)

        # Calculate position weights
        weights = np.array([
            pos.market_value / total_value for pos in positions
        ])

        # Concentration risk (Herfindahl index)
        concentration_index = np.sum(weights ** 2)
        largest_position_pct = np.max(weights)

        # Portfolio returns (if historical data available)
        if historical_prices is not None:
            portfolio_returns = self._calculate_portfolio_returns(
                positions,
                historical_prices,
                weights,
            )

            var_95 = self.calculate_var(portfolio_returns, 0.95)
            cvar_95 = self.calculate_cvar(portfolio_returns, 0.95)
            var_99 = self.calculate_var(portfolio_returns, 0.99)

            # Portfolio beta
            beta = self._calculate_portfolio_beta(portfolio_returns, weights)

        else:
            var_95 = 0
            cvar_95 = 0
            var_99 = 0
            beta = 0

        # Margin calculations (simplified)
        total_margin_used = sum(
            abs(pos.market_value * 0.5) if pos.position_type == 'LONG'
            else pos.market_value * 0.5
            for pos in positions
        )
        available_margin = total_value * 2  # 2x leverage
        margin_ratio = total_margin_used / available_margin if available_margin > 0 else 0

        return PortfolioRisk(
            total_value=total_value,
            total_margin_used=total_margin_used,
            available_margin=available_margin,
            margin_ratio=margin_ratio,
            portfolio_var_95=var_95,
            portfolio_cvar_95=cvar_95,
            portfolio_var_99=var_99,
            largest_position_pct=largest_position_pct,
            concentration_index=concentration_index,
            portfolio_beta=beta,
            portfolio_correlation_with_market=0,  # Would calculate with market data
            illiquid_positions_pct=0,  # Would track illiquid positions
        )

    def calculate_hedge_ratio(
        self,
        position_size: float,
        instrument_beta: float,
        hedge_instrument_beta: float,
    ) -> float:
        """
        Calculate hedge ratio for a position.

        Args:
            position_size: Size of position to hedge
            instrument_beta: Beta of position
            hedge_instrument_beta: Beta of hedge instrument

        Returns:
            Hedge ratio (units of hedge instrument)
        """
        if hedge_instrument_beta == 0:
            return 0

        return (position_size * instrument_beta) / hedge_instrument_beta

    def stress_test(
        self,
        positions: List[Position],
        stress_scenarios: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Run stress testing on portfolio.

        Args:
            positions: List of positions
            stress_scenarios: Dict of {symbol: price_change_pct}

        Returns:
            Portfolio P&L under each scenario
        """
        results = {}

        for scenario_name, changes in stress_scenarios.items():
            pnl = 0

            for pos in positions:
                if pos.symbol in changes:
                    # Calculate P&L under this scenario
                    price_change = changes[pos.symbol]
                    new_price = pos.current_price * (1 + price_change)

                    if pos.position_type == 'LONG':
                        scenario_pnl = pos.quantity * (new_price - pos.current_price)
                    else:
                        scenario_pnl = pos.quantity * (pos.current_price - new_price)

                    pnl += scenario_pnl

            results[scenario_name] = pnl

        return results

    def get_risk_metrics_summary(
        self,
        positions: List[Position],
        historical_prices: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive risk metrics summary."""
        portfolio_risk = self.calculate_portfolio_risk(positions, historical_prices)

        return {
            'total_value': portfolio_risk.total_value,
            'var_95': portfolio_risk.portfolio_var_95,
            'cvar_95': portfolio_risk.portfolio_cvar_95,
            'var_99': portfolio_risk.portfolio_var_99,
            'concentration': portfolio_risk.concentration_index,
            'largest_position': portfolio_risk.largest_position_pct,
            'margin_ratio': portfolio_risk.margin_ratio,
            'beta': portfolio_risk.portfolio_beta,
        }

    def _calculate_portfolio_returns(
        self,
        positions: List[Position],
        historical_prices: pd.DataFrame,
        weights: np.ndarray,
    ) -> pd.Series:
        """Calculate portfolio returns from positions."""
        portfolio_ret = pd.Series(0, index=historical_prices.index)

        for i, pos in enumerate(positions):
            if pos.symbol in historical_prices.columns:
                symbol_returns = historical_prices[pos.symbol].pct_change()
                portfolio_ret += weights[i] * symbol_returns

        return portfolio_ret.dropna()

    def _calculate_portfolio_beta(
        self,
        portfolio_returns: pd.Series,
        weights: np.ndarray,
    ) -> float:
        """Calculate portfolio beta."""
        if len(portfolio_returns) < 2:
            return 0

        # Simplified: assume uniform market returns
        market_returns = portfolio_returns.mean() * np.ones_like(portfolio_returns)

        # Calculate covariance
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        if market_variance == 0:
            return 0

        return covariance / market_variance
