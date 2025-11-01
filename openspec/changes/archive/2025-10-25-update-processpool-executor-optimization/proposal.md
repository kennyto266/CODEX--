## Why

The parameter optimization engine for 11 trading strategies (MA, RSI, MACD, Bollinger Bands, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR) was using ThreadPoolExecutor limited to 8 workers, which couldn't fully utilize modern multi-core CPUs (32-core 9950X3D available). Switching to ProcessPoolExecutor enables true parallelization by bypassing Python's Global Interpreter Lock (GIL), reducing optimization time by 4x from ~120 seconds to ~30-38 seconds for 1105+ parameter combinations.

## What Changes

- Replace ThreadPoolExecutor with ProcessPoolExecutor across all 10 `_optimize_xxx_parameters()` methods (RSI, MACD, Bollinger Bands, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR)
- Increase default `max_workers` from 8 to 32 to fully utilize available CPU cores
- Normalize context manager variable naming from `pool` to `executor` for consistency
- Add Unicode error handling for Windows console output (cp950 encoding)
- Achieve 4x performance improvement: ~30-38 seconds for full 11-strategy optimization on 9950X3D CPU

## Impact

- **Affected specs**: strategy-backtest (Parallel optimization performance requirement)
- **Affected code**: `enhanced_strategy_backtest.py` lines 758-956 (all `_optimize_xxx_parameters` methods)
- **Performance gain**: 120 seconds → 30-38 seconds (4x improvement)
- **Backward compatibility**: No breaking changes; parameter interface remains identical
- **Testing**: Validated with 0700.HK and 0939.HK stocks; 1105 parameter combinations tested successfully
- **Output**: `strategy_backtest_report.txt` with top 10 strategies ranked by Sharpe ratio
