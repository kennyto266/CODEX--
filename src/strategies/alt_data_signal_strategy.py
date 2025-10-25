"""
Alternative Data Signal Strategy

Combines price-based and alternative data signals for enhanced trading decisions.
Implements configurable signal weights, confidence scoring, and adaptive position sizing.

Features:
    - Weighted signal combination
    - Confidence scoring based on correlation strength
    - Adaptive position sizing
    - Signal strength calculation
    - Multi-indicator support

Usage:
    strategy = AltDataSignalStrategy(price_weight=0.6, alt_weight=0.4)

    signal = strategy.generate_signal(
        price_signal=1.0,           # Buy signal
        alt_signal=0.8,             # Positive alt data
        correlation=0.65,           # Price-alt correlation
        base_position_size=100
    )
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import numpy as np


class SignalStrength(str, Enum):
    """Signal strength classification"""
    VERY_STRONG = "very_strong"      # > 0.8
    STRONG = "strong"                 # 0.6-0.8
    MODERATE = "moderate"             # 0.4-0.6
    WEAK = "weak"                     # 0.2-0.4
    VERY_WEAK = "very_weak"          # 0-0.2


class SignalDirection(str, Enum):
    """Trading signal direction"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ConfidenceFactors(BaseModel):
    """Factors affecting signal confidence"""
    price_signal_strength: float = Field(..., description="Price signal strength (0-1)")
    alt_signal_strength: float = Field(..., description="Alt data signal strength (0-1)")
    correlation_strength: float = Field(..., description="Correlation strength (0-1)")
    signal_alignment: float = Field(..., description="Signal alignment factor (0-1)")
    volatility_factor: float = Field(default=1.0, description="Volatility adjustment factor")


class PositionSizeRecommendation(BaseModel):
    """Position sizing recommendation"""
    base_size: float = Field(..., description="Base position size")
    confidence_adjusted_size: float = Field(..., description="Size adjusted by confidence")
    risk_adjusted_size: float = Field(..., description="Size adjusted for risk")
    final_size: float = Field(..., description="Final recommended position size")
    max_size: float = Field(..., description="Maximum allowed position size")
    min_size: float = Field(..., description="Minimum allowed position size")


class AltDataSignal(BaseModel):
    """Combined alternative data signal"""
    symbol: str = Field(..., description="Trading symbol")
    direction: SignalDirection = Field(..., description="Signal direction (buy/sell/hold)")
    strength: float = Field(..., description="Overall signal strength (0-1)")
    classification: SignalStrength = Field(..., description="Signal strength classification")
    confidence: float = Field(..., description="Signal confidence (0-1)")
    price_signal: float = Field(..., description="Price signal component (-1 to 1)")
    alt_signal: float = Field(..., description="Alt data signal component (-1 to 1)")
    correlation: float = Field(..., description="Price-alt correlation at signal time")
    recommended_size: float = Field(..., description="Recommended position size")
    current_price: Optional[float] = Field(None, description="Current price at signal time")
    stop_loss: Optional[float] = Field(None, description="Suggested stop loss price")
    take_profit: Optional[float] = Field(None, description="Suggested take profit price")
    reasoning: str = Field(..., description="Human-readable explanation")


class AltDataSignalStrategy:
    """
    Alternative Data Signal Strategy

    Combines price-based and alternative data signals for more robust trading decisions.
    Uses configurable weights, correlation-based confidence scoring, and adaptive position sizing.
    """

    def __init__(
        self,
        price_weight: float = 0.6,
        alt_weight: float = 0.4,
        min_confidence: float = 0.3,
        max_position_size: float = 1000,
        use_correlation_weighting: bool = True,
        volatility_adjustment: bool = True
    ):
        """
        Initialize Alternative Data Signal Strategy

        Args:
            price_weight: Weight for price signals (0-1)
            alt_weight: Weight for alternative data signals (0-1)
            min_confidence: Minimum confidence to generate signal
            max_position_size: Maximum allowed position size
            use_correlation_weighting: Whether to adjust weights by correlation
            volatility_adjustment: Whether to adjust sizes for volatility
        """
        assert 0 <= price_weight <= 1, "price_weight must be between 0 and 1"
        assert 0 <= alt_weight <= 1, "alt_weight must be between 0 and 1"
        assert abs((price_weight + alt_weight) - 1.0) < 0.01, "Weights should sum to approximately 1"

        self.price_weight = price_weight
        self.alt_weight = alt_weight
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.use_correlation_weighting = use_correlation_weighting
        self.volatility_adjustment = volatility_adjustment

        self.logger = logging.getLogger("hk_quant_system.alt_data_strategy")
        self.logger.info(f"Initialized AltDataSignalStrategy with weights: price={price_weight}, alt={alt_weight}")

    def generate_signal(
        self,
        price_signal: float,
        alt_signal: float,
        correlation: float,
        current_price: Optional[float] = None,
        base_position_size: float = 100,
        symbol: str = "UNKNOWN",
        volatility: Optional[float] = None,
        historical_volatility: Optional[float] = None
    ) -> Optional[AltDataSignal]:
        """
        Generate combined alternative data signal

        Args:
            price_signal: Price-based signal (-1 to 1, negative=sell, 0=hold, positive=buy)
            alt_signal: Alternative data signal (-1 to 1)
            correlation: Correlation between price and alt data (0-1)
            current_price: Current price for stop loss/take profit calculation
            base_position_size: Base position size for this trade
            symbol: Trading symbol
            volatility: Current volatility (if None, not used)
            historical_volatility: Historical volatility reference

        Returns:
            AltDataSignal with combined recommendation, or None if confidence too low
        """
        try:
            # Calculate confidence factors
            confidence_factors = self._calculate_confidence_factors(
                price_signal,
                alt_signal,
                correlation
            )

            # Calculate weighted signal
            merged_signal = self._calculate_weighted_signal(
                price_signal,
                alt_signal,
                correlation
            )

            # Calculate final confidence
            final_confidence = self._calculate_confidence(confidence_factors)

            # Determine signal direction
            direction, strength = self._determine_signal_direction(merged_signal)

            # For very weak signals, return HOLD instead of None (always provide a signal)
            if final_confidence < self.min_confidence:
                if direction != SignalDirection.HOLD:
                    self.logger.debug(f"Signal confidence {final_confidence:.2%} below threshold {self.min_confidence:.2%}, converting to HOLD")
                    direction = SignalDirection.HOLD
                    strength = 0.05  # Very weak signal
                else:
                    self.logger.debug(f"Signal confidence {final_confidence:.2%} below threshold, keeping HOLD")

            # Calculate position size
            position_rec = self._calculate_position_size(
                base_position_size,
                final_confidence,
                volatility,
                historical_volatility
            )

            # Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_price_targets(
                current_price,
                direction,
                strength
            ) if current_price else (None, None)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                direction,
                strength,
                final_confidence,
                price_signal,
                alt_signal,
                correlation
            )

            # Create signal object
            signal = AltDataSignal(
                symbol=symbol,
                direction=direction,
                strength=strength,
                classification=self._classify_strength(strength),
                confidence=final_confidence,
                price_signal=price_signal,
                alt_signal=alt_signal,
                correlation=correlation,
                recommended_size=position_rec.final_size,
                current_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning
            )

            self.logger.info(f"Generated signal for {symbol}: {direction.value} (confidence={final_confidence:.2%})")
            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None

    def _calculate_confidence_factors(
        self,
        price_signal: float,
        alt_signal: float,
        correlation: float
    ) -> ConfidenceFactors:
        """Calculate individual confidence factors"""
        price_strength = abs(price_signal)
        alt_strength = abs(alt_signal)

        # Signal alignment: do they agree? (both positive or both negative)
        alignment = 1.0 if (price_signal * alt_signal >= 0) else 0.5
        if abs(price_signal) < 0.1 or abs(alt_signal) < 0.1:  # One signal is neutral
            alignment = 0.7

        # Correlation strength as confidence factor
        correlation_strength = max(0, correlation)  # 0 to 1

        return ConfidenceFactors(
            price_signal_strength=price_strength,
            alt_signal_strength=alt_strength,
            correlation_strength=correlation_strength,
            signal_alignment=alignment
        )

    def _calculate_weighted_signal(
        self,
        price_signal: float,
        alt_signal: float,
        correlation: float
    ) -> float:
        """Calculate weighted combined signal"""
        if self.use_correlation_weighting and correlation > 0.3:
            # Increase alternative data weight when signals are correlated
            adjusted_price_weight = self.price_weight * (1 - 0.1 * correlation)
            adjusted_alt_weight = self.alt_weight * (1 + 0.1 * correlation)

            # Normalize
            total = adjusted_price_weight + adjusted_alt_weight
            adjusted_price_weight /= total
            adjusted_alt_weight /= total
        else:
            adjusted_price_weight = self.price_weight
            adjusted_alt_weight = self.alt_weight

        merged = adjusted_price_weight * price_signal + adjusted_alt_weight * alt_signal
        return np.clip(merged, -1.0, 1.0)

    def _calculate_confidence(self, factors: ConfidenceFactors) -> float:
        """Calculate overall confidence score (0-1)"""
        # Average of all factors, weighted by importance
        avg_signal_strength = (factors.price_signal_strength + factors.alt_signal_strength) / 2
        alignment_boost = factors.signal_alignment * 0.1  # Max +0.1 boost

        confidence = (avg_signal_strength * 0.7 + factors.correlation_strength * 0.2) + alignment_boost
        return np.clip(confidence, 0.0, 1.0)

    def _determine_signal_direction(self, merged_signal: float) -> Tuple[SignalDirection, float]:
        """Determine signal direction and strength"""
        strength = abs(merged_signal)

        if strength < 0.2:
            return SignalDirection.HOLD, strength
        elif merged_signal > 0:
            return SignalDirection.BUY, strength
        else:
            return SignalDirection.SELL, strength

    @staticmethod
    def _classify_strength(strength: float) -> SignalStrength:
        """Classify signal strength"""
        if strength > 0.8:
            return SignalStrength.VERY_STRONG
        elif strength > 0.6:
            return SignalStrength.STRONG
        elif strength > 0.4:
            return SignalStrength.MODERATE
        elif strength > 0.2:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

    def _calculate_position_size(
        self,
        base_size: float,
        confidence: float,
        volatility: Optional[float] = None,
        historical_volatility: Optional[float] = None
    ) -> PositionSizeRecommendation:
        """Calculate recommended position size based on confidence and risk"""
        # Confidence adjustment (0.3 confidence = 30% of base, 0.8 confidence = 80% of base)
        confidence_adjusted = base_size * max(confidence, 0.1)

        # Risk adjustment based on volatility
        if self.volatility_adjustment and volatility and historical_volatility:
            volatility_ratio = volatility / historical_volatility if historical_volatility > 0 else 1.0
            volatility_factor = 1.0 / max(volatility_ratio, 0.5)  # Reduce size if vol is high
            risk_adjusted = confidence_adjusted * volatility_factor
        else:
            risk_adjusted = confidence_adjusted

        # Apply position limits
        final_size = np.clip(risk_adjusted, 0, self.max_position_size)
        min_size = max(1, base_size * 0.1)  # At least 10% of base

        return PositionSizeRecommendation(
            base_size=base_size,
            confidence_adjusted_size=confidence_adjusted,
            risk_adjusted_size=risk_adjusted,
            final_size=final_size,
            max_size=self.max_position_size,
            min_size=min_size
        )

    @staticmethod
    def _calculate_price_targets(
        current_price: float,
        direction: SignalDirection,
        strength: float
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate stop loss and take profit levels"""
        if direction == SignalDirection.HOLD:
            return None, None

        # Risk/reward ratios based on signal strength
        if strength > 0.7:
            risk_ratio = 0.03  # 3% risk
            reward_ratio = 0.09  # 9% reward (3:1 ratio)
        elif strength > 0.5:
            risk_ratio = 0.04  # 4% risk
            reward_ratio = 0.08  # 8% reward (2:1 ratio)
        else:
            risk_ratio = 0.05  # 5% risk
            reward_ratio = 0.10  # 10% reward (2:1 ratio)

        if direction == SignalDirection.BUY:
            stop_loss = current_price * (1 - risk_ratio)
            take_profit = current_price * (1 + reward_ratio)
        else:  # SELL
            stop_loss = current_price * (1 + risk_ratio)
            take_profit = current_price * (1 - reward_ratio)

        return stop_loss, take_profit

    def _generate_reasoning(
        self,
        direction: SignalDirection,
        strength: float,
        confidence: float,
        price_signal: float,
        alt_signal: float,
        correlation: float
    ) -> str:
        """Generate human-readable explanation for the signal"""
        direction_text = {
            SignalDirection.BUY: "Buy",
            SignalDirection.SELL: "Sell",
            SignalDirection.HOLD: "Hold"
        }[direction]

        strength_text = self._classify_strength(strength).value

        price_desc = "positive price signal" if price_signal > 0 else "negative price signal"
        alt_desc = "positive alternative data" if alt_signal > 0 else "negative alternative data"
        alignment = "agree" if price_signal * alt_signal >= 0 else "diverge"

        reasoning = (
            f"{direction_text} signal ({strength_text} strength, {confidence:.0%} confidence). "
            f"Price-based signal and alternative data {alignment}: {price_desc} and {alt_desc}. "
            f"Correlation: {correlation:.2f}."
        )

        return reasoning

    def update_weights(self, price_weight: float, alt_weight: float) -> None:
        """Update signal weights dynamically"""
        assert 0 <= price_weight <= 1
        assert 0 <= alt_weight <= 1
        assert abs((price_weight + alt_weight) - 1.0) < 0.01

        self.price_weight = price_weight
        self.alt_weight = alt_weight
        self.logger.info(f"Updated weights: price={price_weight}, alt={alt_weight}")

    def set_min_confidence(self, min_confidence: float) -> None:
        """Update minimum confidence threshold"""
        assert 0 <= min_confidence <= 1
        self.min_confidence = min_confidence
        self.logger.info(f"Updated minimum confidence threshold: {min_confidence:.0%}")


# Example usage and helper functions
async def example_alt_data_strategy(
    alt_data_current: Dict[str, float],
    current_positions: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Example alternative data strategy function for use with backtest engine

    Args:
        alt_data_current: Current alternative data values
        current_positions: Current position holdings

    Returns:
        List of trading signals
    """
    strategy = AltDataSignalStrategy(price_weight=0.6, alt_weight=0.4)
    signals = []

    # Example: Generate signals based on alt data
    if 'HIBOR' in alt_data_current:
        hibor_signal = 1.0 if alt_data_current['HIBOR'] < 4.0 else -1.0

        signal = strategy.generate_signal(
            price_signal=0.5,           # Neutral price signal
            alt_signal=hibor_signal,
            correlation=0.65,
            base_position_size=100,
            symbol="0939.HK"
        )

        if signal:
            signals.append({
                'symbol': signal.symbol,
                'side': 'buy' if signal.direction == SignalDirection.BUY else 'sell',
                'quantity': signal.recommended_size,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning
            })

    return signals


__all__ = [
    'AltDataSignalStrategy',
    'AltDataSignal',
    'SignalStrength',
    'SignalDirection',
    'ConfidenceFactors',
    'PositionSizeRecommendation',
    'example_alt_data_strategy'
]
