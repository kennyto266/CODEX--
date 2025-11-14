"""
Technical Indicators Module

Implements 5 advanced technical indicators:
1. Ichimoku - Ichimoku Cloud
2. Keltner - Keltner Channel
3. CMO - Chande Momentum Oscillator
4. VROC - Volume Rate of Change
5. Advanced Variants (Williams %R, Stochastic RSI, Optimized ADX, ATR Bands, Improved OBV)
"""

from .ichimoku import (
    IchimokuIndicator,
    calculate_ichimoku
)

from .keltner import (
    KeltnerIndicator,
    calculate_keltner
)

from .cmo import (
    CMOIndicator,
    calculate_cmo
)

from .vroc import (
    VROCIndicator,
    calculate_vroc
)

from .advanced_indicators import (
    WilliamsRIndicator,
    StochasticRSIIndicator,
    OptimizedADXIndicator,
    ATRBandsIndicator,
    ImprovedOBVIndicator,
    calculate_williams_r,
    calculate_stochastic_rsi,
    calculate_optimized_adx,
    calculate_atr_bands,
    calculate_improved_obv
)

__all__ = [
    # Ichimoku
    'IchimokuIndicator',
    'calculate_ichimoku',

    # Keltner
    'KeltnerIndicator',
    'calculate_keltner',

    # CMO
    'CMOIndicator',
    'calculate_cmo',

    # VROC
    'VROCIndicator',
    'calculate_vroc',

    # Advanced Indicators
    'WilliamsRIndicator',
    'StochasticRSIIndicator',
    'OptimizedADXIndicator',
    'ATRBandsIndicator',
    'ImprovedOBVIndicator',
    'calculate_williams_r',
    'calculate_stochastic_rsi',
    'calculate_optimized_adx',
    'calculate_atr_bands',
    'calculate_improved_obv',
]
