## MODIFIED Requirements

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

#### Scenario: Parallel optimization performance with ProcessPoolExecutor
- **WHEN** running optimization with multiple parameter combinations (1105+ combinations for all 11 strategies)
- **THEN** utilize ProcessPoolExecutor with max_workers=32 to bypass Python GIL for true parallelization
- **AND** complete full optimization in ~30-38 seconds on 9950X3D CPU (4x improvement from 120 seconds with ThreadPoolExecutor)
- **AND** log progress as parameter combinations are tested
- **AND** support configurable max_workers parameter to adapt to available CPU cores

#### Scenario: Parallel optimization with custom worker count
- **WHEN** user calls `optimize_parameters(max_workers=8)` with custom worker count
- **THEN** respect the provided max_workers parameter
- **AND** use ProcessPoolExecutor with specified worker count
- **AND** complete optimization with specified parallelization level
