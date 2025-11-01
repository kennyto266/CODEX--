"""
Macro Hedge Strategy

Implements portfolio hedging decisions based on macroeconomic indicators.
Dynamically adjusts hedge ratios and selects appropriate hedge instruments
based on macro alert levels and market stress indicators.

Features:
    - Dynamic hedge ratio calculation
    - Macro alert level assessment
    - Hedge instrument selection
    - Correlation-based hedge effectiveness
    - Portfolio stress scenario analysis

Usage:
    strategy = MacroHedgeStrategy(hedge_ratio=0.2)

    hedge_signal = strategy.generate_hedge_signal(
        macro_indicator=4.5,           # HIBOR rate
        alert_threshold=4.0,
        base_position_size=100
    )

    instrument = strategy.select_hedge_instrument(
        correlation=0.65,
        macro_alert_level='HIGH'
    )
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np


class MacroAlertLevel(str, Enum):
    """Macroeconomic alert level classification"""
    GREEN = "green"            # Normal conditions (< 1 std from mean)
    YELLOW = "yellow"          # Elevated conditions (1-2 std from mean)
    ORANGE = "orange"          # High stress (2-3 std from mean)
    RED = "red"                # Extreme stress (> 3 std from mean)


class HedgeInstrument(str, Enum):
    """Types of hedge instruments available"""
    PUT_OPTIONS = "put_options"           # Downside protection, limited upside
    SHORT_EQUITY = "short_equity"         # Direct hedge, full protection
    FIXED_INCOME = "fixed_income"         # Stable hedge, low correlation
    COMMODITIES = "commodities"           # Inflation hedge, diversification
    VOLATILITY = "volatility"             # VIX/tail risk hedge
    CURRENCY = "currency"                 # Currency hedge for FX exposure
    NONE = "none"                         # No hedge needed


class HedgePosition(BaseModel):
    """Hedge position specification"""
    instrument: HedgeInstrument = Field(..., description="Type of hedge instrument")
    hedge_ratio: float = Field(..., description="Fraction of portfolio to hedge (0-1)")
    size: float = Field(..., description="Notional size of hedge position")
    cost: float = Field(..., description="Cost of hedge (in bps)")
    expected_correlation: float = Field(..., description="Expected correlation to portfolio")
    expected_protection: float = Field(..., description="Expected downside protection (0-1)")
    expected_effectiveness: float = Field(..., description="Hedge effectiveness (0-1)")
    duration_days: int = Field(..., description="Hedge duration in days")
    reasoning: str = Field(..., description="Explanation of hedge choice")


class MacroHedgeSignal(BaseModel):
    """Macro hedge trading signal"""
    alert_level: MacroAlertLevel = Field(..., description="Current macro alert level")
    hedge_required: bool = Field(..., description="Whether hedging is needed")
    recommended_hedge_ratio: float = Field(..., description="Recommended hedge ratio (0-1)")
    current_macro_value: float = Field(..., description="Current macro indicator value")
    mean_macro_value: float = Field(..., description="Mean macro indicator value")
    std_macro_value: float = Field(..., description="Std dev of macro indicator")
    alert_threshold: float = Field(..., description="Alert threshold value")
    recommended_instruments: List[HedgeInstrument] = Field(..., description="Recommended hedge instruments")
    hedge_position: Optional[HedgePosition] = Field(None, description="Detailed hedge position")
    confidence: float = Field(..., description="Signal confidence (0-1)")
    reasoning: str = Field(..., description="Human-readable explanation")


class PortfolioStressScenario(BaseModel):
    """Portfolio stress test scenario"""
    scenario_name: str = Field(..., description="Name of stress scenario")
    macro_shock: Dict[str, float] = Field(..., description="Macro variable shocks")
    portfolio_impact: float = Field(..., description="Expected portfolio impact (%)")
    hedge_protection: float = Field(..., description="Protection from hedge (%)")
    net_impact: float = Field(..., description="Net impact after hedging (%)")
    probability: float = Field(..., description="Scenario probability (0-1)")


class MacroHedgeStrategy:
    """
    Macro Hedge Strategy

    Implements dynamic portfolio hedging based on macroeconomic indicators.
    Assesses macro risk, determines appropriate hedge ratios, and selects
    optimal hedge instruments based on current market conditions.
    """

    def __init__(
        self,
        hedge_ratio: float = 0.2,
        max_hedge_ratio: float = 0.5,
        alert_threshold_multiplier: float = 2.0,
        min_cost_bps: float = 5,
        max_cost_bps: float = 50
    ):
        """
        Initialize Macro Hedge Strategy

        Args:
            hedge_ratio: Base hedge ratio when macro alert is yellow (0-1)
            max_hedge_ratio: Maximum allowed hedge ratio
            alert_threshold_multiplier: Std dev threshold for alerts
            min_cost_bps: Minimum hedge cost in basis points
            max_cost_bps: Maximum acceptable hedge cost
        """
        assert 0 <= hedge_ratio <= 1, "Hedge ratio must be 0-1"
        assert 0 <= max_hedge_ratio <= 1, "Max hedge ratio must be 0-1"
        assert hedge_ratio <= max_hedge_ratio, "Hedge ratio must be <= max"

        self.hedge_ratio = hedge_ratio
        self.max_hedge_ratio = max_hedge_ratio
        self.alert_threshold_multiplier = alert_threshold_multiplier
        self.min_cost_bps = min_cost_bps
        self.max_cost_bps = max_cost_bps

        self.logger = logging.getLogger("hk_quant_system.macro_hedge_strategy")
        self.logger.info(f"Initialized MacroHedgeStrategy with hedge_ratio={hedge_ratio}")

        # Macro indicator thresholds and characteristics
        self.indicator_characteristics = {
            'HIBOR': {
                'alert_high': 4.5,      # High interest rate alert
                'critical_high': 5.0,   # Critical level
                'interpretation': 'Higher rates = tighter liquidity',
                'portfolio_impact': -0.5  # Negative for stock portfolio
            },
            'HSCEI_VOLATILITY': {
                'alert_high': 30,       # High volatility alert
                'critical_high': 40,    # Critical level
                'interpretation': 'Higher vol = more risk',
                'portfolio_impact': -0.3
            },
            'CREDIT_SPREAD': {
                'alert_high': 150,      # 150 bps
                'critical_high': 200,   # 200 bps
                'interpretation': 'Wider spreads = credit stress',
                'portfolio_impact': -0.4
            },
            'FORWARD_PBV': {
                'alert_high': 0.85,     # Forward valuations < 0.85x historical
                'critical_high': 0.80,
                'interpretation': 'Low valuations = undervalued or distressed',
                'portfolio_impact': -0.2
            }
        }

        # Hedge instrument characteristics
        self.hedge_instruments_profile = {
            HedgeInstrument.PUT_OPTIONS: {
                'cost_bps': 25,
                'protection': 0.85,
                'correlation': -0.3,
                'time_decay': 0.7,
                'effectiveness_vs_alert': {
                    MacroAlertLevel.GREEN: 0.0,
                    MacroAlertLevel.YELLOW: 0.5,
                    MacroAlertLevel.ORANGE: 0.8,
                    MacroAlertLevel.RED: 0.9
                }
            },
            HedgeInstrument.SHORT_EQUITY: {
                'cost_bps': 30,
                'protection': 1.0,
                'correlation': -0.9,
                'time_decay': 0.0,
                'effectiveness_vs_alert': {
                    MacroAlertLevel.GREEN: 0.0,
                    MacroAlertLevel.YELLOW: 0.3,
                    MacroAlertLevel.ORANGE: 0.7,
                    MacroAlertLevel.RED: 1.0
                }
            },
            HedgeInstrument.FIXED_INCOME: {
                'cost_bps': 10,
                'protection': 0.4,
                'correlation': 0.2,
                'time_decay': 0.0,
                'effectiveness_vs_alert': {
                    MacroAlertLevel.GREEN: 0.0,
                    MacroAlertLevel.YELLOW: 0.6,
                    MacroAlertLevel.ORANGE: 0.7,
                    MacroAlertLevel.RED: 0.5
                }
            },
            HedgeInstrument.COMMODITIES: {
                'cost_bps': 15,
                'protection': 0.3,
                'correlation': -0.1,
                'time_decay': 0.2,
                'effectiveness_vs_alert': {
                    MacroAlertLevel.GREEN: 0.0,
                    MacroAlertLevel.YELLOW: 0.4,
                    MacroAlertLevel.ORANGE: 0.5,
                    MacroAlertLevel.RED: 0.6
                }
            },
            HedgeInstrument.VOLATILITY: {
                'cost_bps': 35,
                'protection': 0.6,
                'correlation': -0.5,
                'time_decay': 0.9,
                'effectiveness_vs_alert': {
                    MacroAlertLevel.GREEN: 0.1,
                    MacroAlertLevel.YELLOW: 0.4,
                    MacroAlertLevel.ORANGE: 0.9,
                    MacroAlertLevel.RED: 1.0
                }
            }
        }

    def generate_hedge_signal(
        self,
        macro_indicator: float,
        mean_macro_value: float,
        std_macro_value: float,
        alert_threshold: float,
        base_position_size: float = 100,
        current_hedge_ratio: float = 0.0,
        portfolio_beta: float = 1.0,
        indicator_name: str = "HIBOR"
    ) -> Optional[MacroHedgeSignal]:
        """
        Generate macro-based hedge signal

        Args:
            macro_indicator: Current macro indicator value
            mean_macro_value: Historical mean
            std_macro_value: Historical std dev
            alert_threshold: Alert level threshold
            base_position_size: Base portfolio size
            current_hedge_ratio: Current hedge ratio (for adjustment)
            portfolio_beta: Portfolio beta for scaling
            indicator_name: Name of macro indicator

        Returns:
            MacroHedgeSignal with recommended hedge action
        """
        try:
            if std_macro_value <= 0:
                return None

            # Determine alert level
            alert_level = self._assess_alert_level(
                macro_indicator, alert_threshold, mean_macro_value, std_macro_value
            )

            # Determine if hedging is needed
            hedge_required = alert_level in [MacroAlertLevel.ORANGE, MacroAlertLevel.RED]

            # Calculate recommended hedge ratio
            recommended_hedge_ratio = self._calculate_hedge_ratio(
                alert_level, current_hedge_ratio
            )

            # Select hedge instruments
            recommended_instruments = self._recommend_hedge_instruments(
                alert_level, macro_indicator, std_macro_value
            )

            # Create detailed hedge position if needed
            hedge_position = None
            if hedge_required and recommended_instruments:
                primary_instrument = recommended_instruments[0]
                hedge_position = self._create_hedge_position(
                    primary_instrument,
                    recommended_hedge_ratio,
                    base_position_size,
                    alert_level,
                    portfolio_beta
                )

            # Calculate confidence
            deviation_std = abs(macro_indicator - mean_macro_value) / std_macro_value
            confidence = min(deviation_std / 2, 1.0)  # Confidence increases with deviation

            # Generate reasoning
            reasoning = self._generate_hedge_reasoning(
                alert_level, macro_indicator, alert_threshold,
                recommended_hedge_ratio, recommended_instruments,
                indicator_name
            )

            return MacroHedgeSignal(
                alert_level=alert_level,
                hedge_required=hedge_required,
                recommended_hedge_ratio=recommended_hedge_ratio,
                current_macro_value=macro_indicator,
                mean_macro_value=mean_macro_value,
                std_macro_value=std_macro_value,
                alert_threshold=alert_threshold,
                recommended_instruments=recommended_instruments,
                hedge_position=hedge_position,
                confidence=np.clip(confidence, 0.0, 1.0),
                reasoning=reasoning
            )

        except Exception as e:
            self.logger.error(f"Error generating hedge signal: {e}")
            return None

    def run_stress_test(
        self,
        macro_scenarios: List[Dict[str, float]],
        portfolio_sensitivity: Dict[str, float],
        current_hedge_ratio: float = 0.0
    ) -> List[PortfolioStressScenario]:
        """
        Run portfolio stress tests against macro scenarios

        Args:
            macro_scenarios: List of macro shock scenarios
            portfolio_sensitivity: Portfolio sensitivity to macro factors
            current_hedge_ratio: Current hedge ratio

        Returns:
            List of stress test results
        """
        try:
            results = []

            for scenario in macro_scenarios:
                scenario_name = scenario.get('name', 'Unnamed Scenario')
                shocks = {k: v for k, v in scenario.items() if k != 'name'}

                # Calculate portfolio impact from macro shocks
                portfolio_impact = sum(
                    shocks.get(factor, 0) * sensitivity
                    for factor, sensitivity in portfolio_sensitivity.items()
                )

                # Calculate hedge protection (rough estimate)
                hedge_protection = current_hedge_ratio * 0.8 * abs(portfolio_impact)

                # Net impact after hedging
                net_impact = portfolio_impact - hedge_protection

                # Scenario probability (higher impact = lower probability, roughly)
                probability = 1.0 / (1.0 + abs(portfolio_impact) / 5)

                results.append(
                    PortfolioStressScenario(
                        scenario_name=scenario_name,
                        macro_shock=shocks,
                        portfolio_impact=portfolio_impact,
                        hedge_protection=hedge_protection,
                        net_impact=net_impact,
                        probability=np.clip(probability, 0.01, 0.99)
                    )
                )

            return results

        except Exception as e:
            self.logger.error(f"Error running stress test: {e}")
            return []

    def _assess_alert_level(
        self,
        value: float,
        threshold: float,
        mean: float,
        std: float
    ) -> MacroAlertLevel:
        """Determine macro alert level from indicator value"""
        if value <= threshold:
            return MacroAlertLevel.GREEN

        std_above_threshold = (value - threshold) / std if std > 0 else 0

        if std_above_threshold < 1:
            return MacroAlertLevel.YELLOW
        elif std_above_threshold < 2:
            return MacroAlertLevel.ORANGE
        else:
            return MacroAlertLevel.RED

    def _calculate_hedge_ratio(
        self,
        alert_level: MacroAlertLevel,
        current_ratio: float
    ) -> float:
        """Calculate recommended hedge ratio based on alert level"""
        alert_to_ratio = {
            MacroAlertLevel.GREEN: 0.0,
            MacroAlertLevel.YELLOW: self.hedge_ratio * 0.5,
            MacroAlertLevel.ORANGE: self.hedge_ratio,
            MacroAlertLevel.RED: self.max_hedge_ratio
        }

        recommended = alert_to_ratio.get(alert_level, 0.0)

        # Smooth transition (don't change too dramatically)
        adjustment = (recommended - current_ratio) * 0.3
        final_ratio = current_ratio + adjustment

        return float(np.clip(final_ratio, 0.0, self.max_hedge_ratio))

    def _recommend_hedge_instruments(
        self,
        alert_level: MacroAlertLevel,
        macro_value: float,
        std_value: float
    ) -> List[HedgeInstrument]:
        """Recommend hedge instruments for given alert level"""
        if alert_level == MacroAlertLevel.GREEN:
            return [HedgeInstrument.NONE]

        recommendations = []

        # Score each instrument by effectiveness at this alert level
        scores = {}
        for instrument, profile in self.hedge_instruments_profile.items():
            effectiveness = profile['effectiveness_vs_alert'].get(alert_level, 0.5)
            cost_penalty = profile['cost_bps'] / self.max_cost_bps
            score = effectiveness - cost_penalty * 0.3

            scores[instrument] = score

        # Return top 3 most effective instruments
        sorted_instruments = sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        )

        return [instrument for instrument, _ in sorted_instruments[:3]]

    def _create_hedge_position(
        self,
        instrument: HedgeInstrument,
        hedge_ratio: float,
        base_size: float,
        alert_level: MacroAlertLevel,
        portfolio_beta: float
    ) -> HedgePosition:
        """Create detailed hedge position specification"""
        profile = self.hedge_instruments_profile.get(
            instrument, self.hedge_instruments_profile[HedgeInstrument.FIXED_INCOME]
        )

        hedge_size = base_size * hedge_ratio * portfolio_beta
        effectiveness = profile['effectiveness_vs_alert'].get(alert_level, 0.5)

        duration = {
            MacroAlertLevel.YELLOW: 30,
            MacroAlertLevel.ORANGE: 60,
            MacroAlertLevel.RED: 90
        }.get(alert_level, 30)

        return HedgePosition(
            instrument=instrument,
            hedge_ratio=hedge_ratio,
            size=hedge_size,
            cost=profile['cost_bps'],
            expected_correlation=profile['correlation'],
            expected_protection=profile['protection'],
            expected_effectiveness=effectiveness,
            duration_days=duration,
            reasoning=f"Hedge with {instrument.value} at {hedge_ratio:.1%} ratio for {alert_level.value} conditions"
        )

    @staticmethod
    def _generate_hedge_reasoning(
        alert_level: MacroAlertLevel,
        macro_value: float,
        threshold: float,
        hedge_ratio: float,
        instruments: List[HedgeInstrument],
        indicator_name: str
    ) -> str:
        """Generate human-readable hedge reasoning"""
        reason = f"{indicator_name} at {macro_value:.2f} ({alert_level.value.upper()} alert level). "

        if alert_level == MacroAlertLevel.GREEN:
            reason += "Market conditions normal. No hedging needed."
        elif alert_level == MacroAlertLevel.YELLOW:
            reason += (
                f"Elevated macro risk detected. "
                f"Recommend {hedge_ratio:.1%} hedge ratio using {instruments[0].value if instruments else 'no'}."
            )
        elif alert_level == MacroAlertLevel.ORANGE:
            reason += (
                f"High macro stress. Recommend {hedge_ratio:.1%} hedge ratio. "
                f"Consider {instruments[0].value}."
            )
        else:  # RED
            reason += (
                f"Extreme macro stress (above {threshold:.2f}). "
                f"URGENT: Increase hedge to {hedge_ratio:.1%}. Recommended: {instruments[0].value}."
            )

        return reason


__all__ = [
    'MacroHedgeStrategy',
    'MacroHedgeSignal',
    'HedgePosition',
    'PortfolioStressScenario',
    'MacroAlertLevel',
    'HedgeInstrument'
]
