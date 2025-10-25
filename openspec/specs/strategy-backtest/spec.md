# strategy-backtest Specification

## Purpose
TBD - created by archiving change add-advanced-technical-indicators. Update Purpose after archive.
## Requirements
### Requirement: KDJ/Stochastic Indicator Strategy
The backtest engine SHALL support KDJ (Stochastic) indicator-based trading strategy with configurable K-period, D-period, overbought, and oversold thresholds.

#### Scenario: KDJ buy signal when oversold
- **WHEN** K value crosses below oversold threshold (e.g., 20) and then crosses above it
- **THEN** generate a buy signal
- **AND** track the position for performance calculation

#### Scenario: KDJ sell signal when overbought
- **WHEN** K value crosses above overbought threshold (e.g., 80) and then crosses below it
- **THEN** generate a sell signal
- **AND** close the position if holding

#### Scenario: KDJ parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='kdj' or 'all'
- **THEN** test K/D periods from 5-30 with step size 5
- **AND** test overbought/oversold thresholds from 20-80 with step size 5
- **AND** return results sorted by Sharpe ratio

### Requirement: CCI Commodity Channel Index Strategy
The backtest engine SHALL support CCI (Commodity Channel Index) indicator-based trading strategy with configurable period and overbought/oversold thresholds ranging from -300 to +300.

#### Scenario: CCI buy signal on oversold condition
- **WHEN** CCI value crosses below oversold threshold (e.g., -100) and then rises above it
- **THEN** generate a buy signal indicating potential upward reversal

#### Scenario: CCI sell signal on overbought condition
- **WHEN** CCI value crosses above overbought threshold (e.g., +100) and then falls below it
- **THEN** generate a sell signal indicating potential downward reversal

#### Scenario: CCI parameter optimization with wide range
- **WHEN** user runs parameter optimization with strategy_type='cci' or 'all'
- **THEN** test periods from 10-30 with step size 5
- **AND** test thresholds from -300 to +300 with step size 25
- **AND** evaluate approximately 100-200 parameter combinations

### Requirement: ADX Average Directional Index Strategy
The backtest engine SHALL support ADX (Average Directional Index) indicator-based trading strategy using ADX threshold combined with +DI and -DI for trend strength confirmation.

#### Scenario: ADX trending buy signal
- **WHEN** ADX value exceeds threshold (e.g., 25) indicating strong trend
- **AND** +DI crosses above -DI
- **THEN** generate a buy signal for upward trending market

#### Scenario: ADX trending sell signal
- **WHEN** ADX value exceeds threshold indicating strong trend
- **AND** -DI crosses above +DI
- **THEN** generate a sell signal for downward trending market

#### Scenario: ADX parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='adx' or 'all'
- **THEN** test ADX periods from 10-30 with step size 5
- **AND** test ADX thresholds from 15-50 with step size 5

### Requirement: ATR Average True Range Strategy
The backtest engine SHALL support ATR (Average True Range) indicator-based trading strategy using volatility-adjusted stop-loss and position sizing.

#### Scenario: ATR volatility breakout entry
- **WHEN** price moves beyond a multiple of ATR (e.g., 2x ATR) from recent high/low
- **THEN** generate a breakout signal in the direction of movement

#### Scenario: ATR parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='atr' or 'all'
- **THEN** test ATR periods from 10-30 with step size 5
- **AND** test ATR multipliers from 0.5-5.0 with step size 0.5

#### Scenario: ATR stop-loss calculation
- **WHEN** a position is opened
- **THEN** calculate stop-loss distance as ATR multiplied by configured factor
- **AND** exit position if price reaches stop-loss level

### Requirement: OBV On-Balance Volume Strategy
The backtest engine SHALL support OBV (On-Balance Volume) indicator-based trading strategy using volume-confirmed price trends.

#### Scenario: OBV bullish divergence buy signal
- **WHEN** price makes a lower low but OBV makes a higher low
- **THEN** generate a buy signal indicating potential reversal

#### Scenario: OBV trend confirmation
- **WHEN** OBV trend (using moving average) aligns with price trend
- **THEN** generate a buy signal if both are upward trending
- **OR** generate a sell signal if both are downward trending

#### Scenario: OBV parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='obv' or 'all'
- **THEN** test OBV trend periods from 10-100 with step size 10

### Requirement: Ichimoku Cloud Strategy
The backtest engine SHALL support Ichimoku Cloud indicator-based trading strategy with configurable conversion line, base line, and span parameters.

#### Scenario: Ichimoku bullish signal
- **WHEN** conversion line (Tenkan-sen) crosses above base line (Kijun-sen)
- **AND** price is above the cloud (Senkou Span A and B)
- **THEN** generate a strong buy signal

#### Scenario: Ichimoku bearish signal
- **WHEN** conversion line crosses below base line
- **AND** price is below the cloud
- **THEN** generate a strong sell signal

#### Scenario: Ichimoku parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='ichimoku' or 'all'
- **THEN** test conversion line periods from 5-15 with step size 5
- **AND** test base line periods from 20-40 with step size 5
- **AND** test span B periods from 40-60 with step size 5

#### Scenario: Ichimoku cloud thickness analysis
- **WHEN** calculating signal strength
- **THEN** consider the distance between Senkou Span A and Senkou Span B
- **AND** weight signals higher when cloud is thicker (stronger support/resistance)

### Requirement: Parabolic SAR Strategy
The backtest engine SHALL support Parabolic SAR (Stop and Reverse) indicator-based trading strategy with configurable acceleration factor.

#### Scenario: Parabolic SAR bullish reversal
- **WHEN** SAR dots switch from above price to below price
- **THEN** generate a buy signal for trend reversal

#### Scenario: Parabolic SAR bearish reversal
- **WHEN** SAR dots switch from below price to above price
- **THEN** generate a sell signal for trend reversal

#### Scenario: Parabolic SAR parameter optimization
- **WHEN** user runs parameter optimization with strategy_type='parabolic_sar' or 'all'
- **THEN** test acceleration factors from 0.01-0.2 with step size 0.01
- **AND** test maximum acceleration from 0.1-0.5 with step size 0.05

### Requirement: Extended Parameter Optimization Support
The backtest engine's `optimize_parameters()` method SHALL accept strategy_type values for all 11 supported strategies including the 7 new advanced indicators.

#### Scenario: Optimize all strategies including new indicators
- **WHEN** user calls `optimize_parameters(strategy_type='all')`
- **THEN** execute parameter optimization for all 11 strategies: MA, RSI, MACD, Bollinger Bands, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR
- **AND** return combined results sorted by Sharpe ratio

#### Scenario: Optimize specific new indicator
- **WHEN** user calls `optimize_parameters(strategy_type='kdj')` or any other new indicator type
- **THEN** execute parameter optimization only for the specified indicator
- **AND** use appropriate parameter ranges and step sizes for that indicator

#### Scenario: Parallel optimization performance
- **WHEN** running optimization with multiple parameter combinations
- **THEN** utilize ThreadPoolExecutor with max_workers based on CPU count
- **AND** complete optimization without blocking the main thread
- **AND** log progress as parameter combinations are tested

### Requirement: Technical Indicator Calculation Extension
The `calculate_technical_indicators()` method SHALL compute all necessary values for the 7 new indicators including intermediate calculations needed for strategy logic.

#### Scenario: Calculate all indicators in one pass
- **WHEN** user calls `calculate_technical_indicators(df)`
- **THEN** return DataFrame with columns for all 11+ indicators including: MA series, RSI, MACD, Bollinger Bands, K/D values, CCI, ADX/+DI/-DI, ATR, OBV, Ichimoku components, Parabolic SAR
- **AND** handle missing data appropriately without raising errors

#### Scenario: Indicator calculation with insufficient data
- **WHEN** DataFrame has fewer rows than required for indicator calculation (e.g., < 60 for Ichimoku)
- **THEN** fill missing values with NaN for that indicator
- **AND** strategy methods SHALL skip that indicator or return None

#### Scenario: Vectorized calculation performance
- **WHEN** calculating indicators for large datasets (> 1000 rows)
- **THEN** use Pandas vectorized operations instead of loops
- **AND** complete calculation in reasonable time (< 5 seconds for 3 years of daily data)

