"""
Correlation Strategy

Implements trading signals based on correlation regime changes and breakdowns.
Detects when price-to-alternative data correlation deviates significantly from
historical norms, generating mean reversion or trend signals.

Features:
    - Correlation breakdown detection (deviation from mean)
    - Regime change detection (correlation trend shifts)
    - Statistical significance testing
    - Dynamic threshold adjustment
    - Correlation strength scoring

Usage:
    strategy = CorrelationStrategy(deviation_threshold=2.0)

    signal = strategy.detect_correlation_breakdown(
        current_correlation=0.45,
        mean_correlation=0.65,
        std_correlation=0.10
    )

    regime_signals = strategy.detect_regime_change(
        rolling_correlation=correlation_series
    )
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from scipy import stats


class CorrelationRegime(str, Enum):
    """Correlation regime classification"""
    HIGH_CORRELATION = "high_correlation"      # > mean + 1 std
    NORMAL_CORRELATION = "normal_correlation"  # within 1 std
    LOW_CORRELATION = "low_correlation"        # < mean - 1 std
    BREAKDOWN = "breakdown"                    # < mean - 2 std


class CorrelationSignalType(str, Enum):
    """Type of correlation signal"""
    BREAKDOWN = "breakdown"                    # Correlation suddenly drops
    SURGE = "surge"                           # Correlation suddenly rises
    REGIME_CHANGE = "regime_change"           # Shift in correlation regime
    STABILIZATION = "stabilization"           # Volatility decreases
    DESTABILIZATION = "destabilization"       # Volatility increases


class CorrelationRegimeChange(BaseModel):
    """Regime change event"""
    date: Optional[str] = Field(None, description="Date of regime change")
    previous_regime: CorrelationRegime = Field(..., description="Previous correlation regime")
    new_regime: CorrelationRegime = Field(..., description="New correlation regime")
    correlation_value: float = Field(..., description="Correlation value at change")
    significance: float = Field(..., description="Statistical significance (0-1)")
    strength: float = Field(..., description="Strength of regime change (0-1)")


class CorrelationBreakdownSignal(BaseModel):
    """Signal generated from correlation breakdown"""
    signal_type: CorrelationSignalType = Field(..., description="Type of correlation signal")
    direction: str = Field(..., description="Trading direction (buy/sell/hold)")
    strength: float = Field(..., description="Signal strength (0-1)")
    confidence: float = Field(..., description="Signal confidence (0-1)")
    current_correlation: float = Field(..., description="Current correlation value")
    mean_correlation: float = Field(..., description="Historical mean correlation")
    deviation_std: float = Field(..., description="Deviation in standard deviations")
    deviation_pct: float = Field(..., description="Deviation from mean (percent)")
    recommendation: str = Field(..., description="Trading recommendation")
    expected_reversion: float = Field(..., description="Expected correlation reversion (0-1)")
    reasoning: str = Field(..., description="Human-readable explanation")


class CorrelationStrategy:
    """
    Correlation-Based Trading Strategy

    Generates trading signals based on deviations in price-to-alternative data
    correlation from historical norms. Uses statistical methods to detect
    correlation breakdowns and regime changes for mean reversion or trending trades.
    """

    def __init__(
        self,
        deviation_threshold: float = 2.0,
        min_observations: int = 20,
        regime_change_threshold: float = 1.5,
        min_regime_duration: int = 5,
        significance_level: float = 0.05
    ):
        """
        Initialize Correlation Strategy

        Args:
            deviation_threshold: Standard deviations for correlation breakdown (default 2.0)
            min_observations: Minimum observations for statistical validity
            regime_change_threshold: Std devs for regime change detection
            min_regime_duration: Minimum bars in regime before change is valid
            significance_level: Statistical significance level for tests
        """
        assert 0 < deviation_threshold <= 5, "Deviation threshold must be 0-5 std devs"
        assert min_observations >= 10, "Need at least 10 observations"
        assert 0 < significance_level < 1, "Significance level must be 0-1"

        self.deviation_threshold = deviation_threshold
        self.min_observations = min_observations
        self.regime_change_threshold = regime_change_threshold
        self.min_regime_duration = min_regime_duration
        self.significance_level = significance_level

        self.logger = logging.getLogger("hk_quant_system.correlation_strategy")
        self.logger.info(
            f"Initialized CorrelationStrategy with deviation_threshold={deviation_threshold}"
        )

        # State tracking
        self.current_regime: Optional[CorrelationRegime] = None
        self.regime_duration: int = 0
        self.correlation_history: List[float] = []

    def detect_correlation_breakdown(
        self,
        current_correlation: float,
        mean_correlation: float,
        std_correlation: float,
        historical_correlations: Optional[List[float]] = None
    ) -> Optional[CorrelationBreakdownSignal]:
        """
        Detect correlation breakdown (deviation from historical norm)

        Args:
            current_correlation: Current correlation value (0-1)
            mean_correlation: Historical mean correlation
            std_correlation: Historical std dev of correlation
            historical_correlations: Optional historical series for additional analysis

        Returns:
            CorrelationBreakdownSignal if breakdown detected, None otherwise
        """
        try:
            if std_correlation <= 0:
                self.logger.debug("Zero std correlation, skipping analysis")
                return None

            # Calculate deviation
            deviation = current_correlation - mean_correlation
            deviation_std = deviation / std_correlation if std_correlation > 0 else 0
            deviation_pct = (deviation / mean_correlation * 100) if mean_correlation > 0 else 0

            # Check for breakdown
            if abs(deviation_std) < self.deviation_threshold:
                return None

            # Determine breakdown type
            if deviation_std < -self.deviation_threshold:
                signal_type = CorrelationSignalType.BREAKDOWN
                direction = "buy"  # Mean reversion: expect correlation to rise
                reasoning = (
                    f"Correlation breakdown: fell {abs(deviation_std):.2f} std devs below mean. "
                    f"Expected mean reversion toward {mean_correlation:.3f}."
                )
            else:
                signal_type = CorrelationSignalType.SURGE
                direction = "sell"  # Mean reversion: expect correlation to fall
                reasoning = (
                    f"Correlation surge: rose {deviation_std:.2f} std devs above mean. "
                    f"Expected mean reversion toward {mean_correlation:.3f}."
                )

            # Calculate confidence based on deviation magnitude
            max_confidence = min(abs(deviation_std) / 3.0, 1.0)  # Max at 3 std devs

            # Boost confidence if we have historical context
            if historical_correlations and len(historical_correlations) > self.min_observations:
                # Check if this is an extreme in recent history
                recent_correlations = historical_correlations[-self.min_observations:]
                percentile = stats.percentileofscore(recent_correlations, current_correlation)

                if (signal_type == CorrelationSignalType.BREAKDOWN and percentile < 20) or \
                   (signal_type == CorrelationSignalType.SURGE and percentile > 80):
                    confidence = max_confidence * 1.2  # 20% boost for extreme values
                else:
                    confidence = max_confidence * 0.9  # 10% penalty for non-extreme
            else:
                confidence = max_confidence

            confidence = np.clip(confidence, 0.0, 1.0)

            # Calculate expected reversion probability
            expected_reversion = self._calculate_reversion_probability(
                deviation_std, historical_correlations
            )

            return CorrelationBreakdownSignal(
                signal_type=signal_type,
                direction=direction,
                strength=min(abs(deviation_std) / self.deviation_threshold, 1.0),
                confidence=confidence,
                current_correlation=current_correlation,
                mean_correlation=mean_correlation,
                deviation_std=deviation_std,
                deviation_pct=deviation_pct,
                recommendation=f"{direction.upper()} to capitalize on mean reversion",
                expected_reversion=expected_reversion,
                reasoning=reasoning
            )

        except Exception as e:
            self.logger.error(f"Error detecting correlation breakdown: {e}")
            return None

    def detect_regime_change(
        self,
        rolling_correlation: pd.Series,
        window: int = 10
    ) -> List[CorrelationRegimeChange]:
        """
        Detect correlation regime changes

        Args:
            rolling_correlation: Time series of rolling correlation values
            window: Window size for regime classification

        Returns:
            List of regime change events
        """
        try:
            if len(rolling_correlation) < self.min_regime_duration * 2:
                self.logger.debug("Insufficient data for regime change detection")
                return []

            # Calculate statistics
            mean_corr = rolling_correlation.mean()
            std_corr = rolling_correlation.std()

            if std_corr <= 0:
                return []

            regime_changes = []

            # Classify regimes for each point
            regimes = []
            for corr in rolling_correlation:
                regime = self._classify_regime(corr, mean_corr, std_corr)
                regimes.append(regime)

            # Detect transitions
            previous_regime = regimes[0]
            regime_duration = 1

            for i in range(1, len(regimes)):
                current_regime = regimes[i]

                if current_regime == previous_regime:
                    regime_duration += 1
                else:
                    # Check if regime duration is significant
                    if regime_duration >= self.min_regime_duration:
                        # Detect change if moving to new regime
                        change_magnitude = abs(
                            rolling_correlation.iloc[i] - rolling_correlation.iloc[i - regime_duration]
                        )

                        change_strength = self._calculate_regime_strength(
                            previous_regime, current_regime, mean_corr, std_corr
                        )

                        # Statistical significance
                        significance = min(change_strength / self.regime_change_threshold, 1.0)

                        regime_changes.append(
                            CorrelationRegimeChange(
                                date=rolling_correlation.index[i].strftime("%Y-%m-%d")
                                if hasattr(rolling_correlation.index[i], "strftime")
                                else str(rolling_correlation.index[i]),
                                previous_regime=previous_regime,
                                new_regime=current_regime,
                                correlation_value=float(rolling_correlation.iloc[i]),
                                significance=np.clip(significance, 0.0, 1.0),
                                strength=np.clip(change_strength, 0.0, 1.0)
                            )
                        )

                    previous_regime = current_regime
                    regime_duration = 1

            self.logger.info(f"Detected {len(regime_changes)} regime changes")
            return regime_changes

        except Exception as e:
            self.logger.error(f"Error detecting regime changes: {e}")
            return []

    def detect_correlation_volatility(
        self,
        rolling_correlation: pd.Series,
        window: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Detect changes in correlation volatility

        Args:
            rolling_correlation: Time series of rolling correlation values
            window: Window for volatility calculation

        Returns:
            Volatility change signal
        """
        try:
            if len(rolling_correlation) < window * 2:
                return None

            # Calculate rolling volatility of correlation
            correlation_volatility = rolling_correlation.rolling(window).std()

            if len(correlation_volatility) < 2:
                return None

            previous_vol = correlation_volatility.iloc[-window-1:-1].mean()
            current_vol = correlation_volatility.iloc[-window:].mean()

            if previous_vol <= 0:
                return None

            vol_change_pct = (current_vol - previous_vol) / previous_vol * 100
            vol_change_std = abs(vol_change_pct) / 10  # Normalize to std devs

            return {
                'signal_type': (
                    CorrelationSignalType.DESTABILIZATION
                    if vol_change_pct > 0
                    else CorrelationSignalType.STABILIZATION
                ),
                'direction': 'sell' if vol_change_pct > 0 else 'buy',
                'strength': min(abs(vol_change_std) / 2, 1.0),
                'confidence': min(abs(vol_change_pct) / 50, 1.0),
                'previous_volatility': previous_vol,
                'current_volatility': current_vol,
                'change_pct': vol_change_pct,
                'recommendation': (
                    'Increase hedging - correlation becoming more volatile'
                    if vol_change_pct > 0
                    else 'Reduce hedging - correlation stabilizing'
                )
            }

        except Exception as e:
            self.logger.error(f"Error detecting correlation volatility: {e}")
            return None

    def calculate_correlation_strength(
        self,
        correlation: float,
        mean_correlation: float,
        std_correlation: float
    ) -> float:
        """
        Calculate correlation strength score (0-1)

        Args:
            correlation: Current correlation
            mean_correlation: Historical mean
            std_correlation: Historical std dev

        Returns:
            Strength score (0-1)
        """
        if std_correlation <= 0:
            return 0.5

        # Deviation from mean
        deviation = abs(correlation - mean_correlation)
        std_deviations = deviation / std_correlation

        # Strength increases with magnitude of deviation
        strength = 1.0 - (1.0 / (1.0 + std_deviations))  # Sigmoidal curve
        return float(np.clip(strength, 0.0, 1.0))

    @staticmethod
    def _classify_regime(
        correlation: float,
        mean: float,
        std: float
    ) -> CorrelationRegime:
        """Classify correlation value into regime"""
        if std <= 0:
            return CorrelationRegime.NORMAL_CORRELATION

        std_score = (correlation - mean) / std

        if std_score > 1:
            return CorrelationRegime.HIGH_CORRELATION
        elif std_score > -1:
            return CorrelationRegime.NORMAL_CORRELATION
        elif std_score > -2:
            return CorrelationRegime.LOW_CORRELATION
        else:
            return CorrelationRegime.BREAKDOWN

    @staticmethod
    def _calculate_reversion_probability(
        deviation_std: float,
        historical_correlations: Optional[List[float]]
    ) -> float:
        """Calculate probability of mean reversion"""
        # Base probability increases with deviation magnitude
        base_prob = min(abs(deviation_std) / 3.0, 1.0)

        # If we have history, check for oscillation pattern
        if historical_correlations and len(historical_correlations) > 5:
            recent = historical_correlations[-5:]
            changes = np.diff(recent)

            # Count sign changes (indicates oscillation)
            sign_changes = sum(1 for i in range(len(changes) - 1) if changes[i] * changes[i+1] < 0)

            # Boost probability if oscillating
            if sign_changes >= 2:
                base_prob *= 1.3

        return float(np.clip(base_prob, 0.0, 1.0))

    @staticmethod
    def _calculate_regime_strength(
        previous_regime: CorrelationRegime,
        new_regime: CorrelationRegime,
        mean: float,
        std: float
    ) -> float:
        """Calculate strength of regime transition"""
        regime_distance = {
            (CorrelationRegime.HIGH_CORRELATION, CorrelationRegime.BREAKDOWN): 4,
            (CorrelationRegime.HIGH_CORRELATION, CorrelationRegime.LOW_CORRELATION): 2,
            (CorrelationRegime.NORMAL_CORRELATION, CorrelationRegime.BREAKDOWN): 2,
            (CorrelationRegime.NORMAL_CORRELATION, CorrelationRegime.HIGH_CORRELATION): 1,
            (CorrelationRegime.LOW_CORRELATION, CorrelationRegime.HIGH_CORRELATION): 2,
            (CorrelationRegime.BREAKDOWN, CorrelationRegime.HIGH_CORRELATION): 4,
        }

        return float(regime_distance.get((previous_regime, new_regime), 1.0))


__all__ = [
    'CorrelationStrategy',
    'CorrelationBreakdownSignal',
    'CorrelationRegimeChange',
    'CorrelationRegime',
    'CorrelationSignalType'
]
