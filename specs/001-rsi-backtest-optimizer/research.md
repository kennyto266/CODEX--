# Research: 0700.HK RSI Backtest Optimizer

**Feature**: 001-rsi-backtest-optimizer
**Date**: 2025-10-16
**Purpose**: Document technology choices, best practices, and design decisions for RSI backtest implementation

## Overview

This document consolidates research findings that inform the implementation of the RSI backtest optimizer for 0700.HK stock. Key decisions cover RSI calculation methodology, backtest engine design patterns, performance optimization for 300-parameter sweep, and Hong Kong market cost modeling.

## 1. RSI Calculation Implementation

### Decision
Use TA-Lib's RSI function (`talib.RSI()`) for indicator calculation with Wilder's smoothing method (standard implementation).

### Rationale
- **Industry Standard**: TA-Lib is the de facto standard for technical analysis in quantitative finance
- **Correctness**: Implements Wilder's exponential moving average smoothing correctly (not simple SMA)
- **Performance**: C-based implementation significantly faster than pure Python
- **Tested**: Battle-tested library used in production systems worldwide

### Alternatives Considered
1. **pandas_ta library**:
   - Pure Python, easier to install (no compilation)
   - **Rejected**: Slower for 300 iterations, less widely used, potential correctness concerns

2. **Manual implementation** (NumPy/Pandas):
   ```python
   # Wilder's RSI formula
   delta = df['close'].diff()
   gain = (delta.where(delta > 0, 0)).ewm(span=window, adjust=False).mean()
   loss = (-delta.where(delta < 0, 0)).ewm(span=window, adjust=False).mean()
   rs = gain / loss
   rsi = 100 - (100 / (1 + rs))
   ```
   - **Rejected**: Reinventing the wheel, higher risk of implementation bugs, no performance advantage

### Implementation Notes
- Minimum data requirement: RSI window + 100 warmup bars recommended (TA-Lib uses exponential smoothing)
- First RSI value appears at index `window + warmup`, earlier values are NaN
- For window=1, RSI is essentially always 100 (single-bar gain) or 0 (single-bar loss) - mathematically valid but strategically meaningless

## 2. Backtest Engine Architecture

### Decision
Implement event-driven backtest loop with explicit state management (position tracking, cash, equity).

### Rationale
- **Look-ahead bias prevention**: Event-driven design naturally enforces temporal data access
- **Clarity**: Explicit state makes debugging and verification straightforward
- **Flexibility**: Easy to add features like stop-loss, position sizing later
- **Standard pattern**: Used by professional backtest libraries (Zipline, Backtrader)

### Alternatives Considered
1. **Vectorized backtest** (all signals generated upfront, then apply returns):
   ```python
   signals = generate_all_signals(data, rsi_window)
   strategy_returns = signals.shift(1) * data['returns']
   ```
   - **Rejected for primary implementation**: Harder to add complex trading logic, cost modeling is less intuitive
   - **Accepted for performance validation**: We can compare event-driven vs vectorized results to verify correctness

2. **Backtrader/Zipline integration**:
   - Full-featured backtest frameworks
   - **Rejected**: Overkill for simple RSI strategy, adds heavy dependencies, harder to customize cost model

### Design Pattern
```python
class BacktestEngine:
    def __init__(self, data, rsi_window, commission=0.001, stamp_duty=0.001):
        self.data = data
        self.rsi = calculate_rsi(data, rsi_window)
        self.position = 0  # 0=cash, 1=stock
        self.cash = 100000  # Initial capital
        self.shares = 0
        self.trades = []

    def run(self):
        for i in range(len(self.data)):
            signal = self.generate_signal(i)  # Only uses data[:i+1]
            if signal != self.position:
                self.execute_trade(i, signal)
        return self.calculate_performance()
```

## 3. Trading Cost Model (Hong Kong Market)

### Decision
Apply 0.1% commission on both buy and sell, plus 0.1% stamp duty on sell only.

### Rationale
- **Hong Kong market standard**: Matches typical online broker fees
- **Conservative estimate**: Actual costs may vary (0.05%-0.25% commission) but 0.1% is reasonable middle ground
- **Stamp duty asymmetry**: Hong Kong government charges stamp duty on sells only (not buys)

### Cost Calculation
```python
def calculate_trade_cost(gross_amount, action):
    commission = gross_amount * 0.001  # 0.1%
    if action == 'SELL':
        stamp_duty = gross_amount * 0.001  # 0.1% on sells only
        return commission + stamp_duty
    else:  # BUY
        return commission

# Example: Buy HK$100,000 worth of stock
buy_cost = 100000 * 0.001 = HK$100 commission
# Actual outlay: HK$100,100

# Example: Sell HK$110,000 worth of stock
sell_commission = 110000 * 0.001 = HK$110
sell_stamp_duty = 110000 * 0.001 = HK$110
total_sell_cost = HK$220
# Actual proceeds: HK$109,780
```

### Alternatives Considered
- **Zero costs**: Would overestimate returns, not realistic
- **Slippage modeling**: Market impact, bid-ask spread
  - **Rejected**: Daily close prices already represent executable prices for small positions; slippage modeling adds complexity without improving parameter optimization quality

## 4. Sharpe Ratio Calculation

### Decision
Use annualized Sharpe ratio with 252 trading days and 2% risk-free rate.

### Formula
```python
daily_returns = strategy_returns  # Already calculated
excess_returns = daily_returns - (0.02 / 252)  # Risk-free rate per day
sharpe_ratio = (excess_returns.mean() * 252) / (excess_returns.std() * sqrt(252))

# Equivalent to:
annual_return = daily_returns.mean() * 252
annual_vol = daily_returns.std() * sqrt(252)
sharpe_ratio = (annual_return - 0.02) / annual_vol
```

### Rationale
- **252 trading days**: Standard convention for Hong Kong/US markets (excludes weekends, holidays)
- **2% risk-free rate**: Approximate HKD deposit rate / short-term government bond yield
- **Annualized metric**: Makes Sharpe ratios comparable across different time periods

### Edge Cases
- **Zero volatility** (no trades): Return Sharpe = 0 or NaN, log warning
- **Negative volatility** (impossible): Indicates calculation bug, raise error
- **Insufficient data** (<30 trades): Sharpe ratio unreliable, flag in report

## 5. Performance Optimization Strategy

### Decision
Implement three-tier optimization approach:
1. **Vectorized RSI calculation** (TA-Lib)
2. **Pre-compute all RSI values** for all windows before backtest loop
3. **Parallel parameter sweep** using Python multiprocessing

### Rationale
- **TA-Lib vectorization**: C implementation ~10-100x faster than Python loops
- **Pre-computation**: Calculate 300 RSI series once, reuse in backtest loops
  - Avoids redundant calculations
  - Memory cost: 300 windows × 2500 days × 8 bytes = ~6MB (negligible)
- **Multiprocessing**: AMD Ryzen 9 9950X3D has 16 cores/32 threads
  - Linear speedup expected: 300 backtests / 16 cores = ~19 backtests per core
  - Target: <5 minutes total = ~16 seconds per backtest per core (easily achievable)

### Implementation Sketch
```python
# Phase 1: Pre-compute all RSI series (window = RSI lookback period)
rsi_cache = {}
for window in range(1, 301):
    # Note: timeperiod is TA-Lib's API parameter name for the window size
    rsi_cache[window] = talib.RSI(data['close'], timeperiod=window)

# Phase 2: Parallel backtest
from multiprocessing import Pool

def run_backtest_for_window(window):
    engine = BacktestEngine(data, rsi_cache[window], window)
    return engine.run()

with Pool(processes=16) as pool:
    results = pool.map(run_backtest_for_window, range(1, 301))
```

### Alternatives Considered
- **Single-threaded**: Would take ~16 × 5min = 80 min (unacceptable)
- **Numba JIT compilation**: Adds dependency, minimal benefit (bottleneck is I/O and TA-Lib, not Python loops)
- **Cython**: Compilation complexity not justified for this workload

## 6. Data Validation Strategy

### Decision
Implement multi-stage validation pipeline:
1. **Schema check**: Verify required columns (date, open, high, low, close, volume)
2. **Completeness check**: Detect missing dates using business day calendar
3. **Sanity check**: Flag anomalies (negative prices, zero volume, OHLC violations)
4. **Chronological order**: Ensure dates are sorted ascending

### Rationale
- **Fail fast**: Catch data issues before RSI calculation
- **Clear errors**: Provide actionable error messages (e.g., "Missing data on 2023-05-15")
- **Garbage-in-garbage-out prevention**: Bad data produces meaningless RSI values

### Implementation Notes
```python
def validate_data(df):
    # 1. Schema
    required = ['date', 'open', 'high', 'low', 'close', 'volume']
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # 2. Completeness
    df['date'] = pd.to_datetime(df['date'])
    date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='B')
    missing_dates = set(date_range) - set(df['date'])
    if missing_dates:
        logger.warning(f"Missing {len(missing_dates)} trading days")

    # 3. Sanity checks
    assert (df['high'] >= df['low']).all(), "High < Low violation"
    assert (df['high'] >= df['close']).all(), "High < Close violation"
    assert (df['low'] <= df['close']).all(), "Low > Close violation"
    assert (df['close'] > 0).all(), "Negative/zero prices detected"

    # 4. Chronological order
    if not df['date'].is_monotonic_increasing:
        raise ValueError("Dates not in ascending order")
```

### Alternatives Considered
- **Skip validation**: Faster but risks invalid results
- **Pandas-specific validation** (pandera library): Adds dependency, overkill for simple checks

## 7. Visualization Best Practices

### Decision
Use Matplotlib with seaborn style, generate publication-quality charts.

### Chart 1: Cumulative Returns (Equity Curve)
```python
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(12, 8))

ax.plot(dates, strategy_equity, label='RSI Strategy', linewidth=2)
ax.plot(dates, buy_hold_equity, label='Buy & Hold', linewidth=2, alpha=0.7)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Portfolio Value (HKD)', fontsize=12)
ax.set_title(f'0700.HK: RSI({optimal_window}) vs Buy-and-Hold', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig('charts/equity_curve.png', dpi=150)
```

### Chart 2: Parameter Sensitivity
```python
fig, ax = plt.subplots(figsize=(12, 8))

ax.scatter(rsi_windows, sharpe_ratios, alpha=0.6, s=50)
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=optimal_window, color='red', linestyle='--', label=f'Optimal: {optimal_window}')
ax.set_xlabel('RSI Window (days)', fontsize=12)
ax.set_ylabel('Sharpe Ratio', fontsize=12)
ax.set_title('Parameter Sensitivity: RSI Window vs Sharpe Ratio', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig('charts/rsi_sharpe_relationship.png', dpi=150)
```

### Rationale
- **Seaborn style**: Professional appearance, good defaults for color/font/grid
- **High DPI (150)**: Ensures charts are presentation-ready, readable in reports
- **Clear labels**: Axes, titles, legends fully annotated
- **Highlight optimal**: Red line shows best parameter, easy to spot

## 8. Logging Strategy

### Decision
Use Python's standard `logging` module with file and console handlers.

### Configuration
```python
import logging
from datetime import datetime

log_filename = f"logs/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger('rsi_backtest')
```

### Log Events
- **INFO**: Data loaded, validation passed, backtest started/completed, optimal window found
- **WARNING**: Missing dates, insufficient data for window, no trades executed
- **ERROR**: Data validation failed, calculation errors, file I/O errors

### Example Log
```
2025-10-16 14:32:10 | INFO     | rsi_backtest.data.loader | Loaded 1247 days of data for 0700.HK
2025-10-16 14:32:10 | WARNING  | rsi_backtest.data.validator | 5 missing trading days detected
2025-10-16 14:32:11 | INFO     | rsi_backtest.optimizer | Starting parameter sweep: RSI windows 1-300
2025-10-16 14:32:45 | INFO     | rsi_backtest.optimizer | Completed 100/300 windows
2025-10-16 14:33:19 | INFO     | rsi_backtest.optimizer | Completed 200/300 windows
2025-10-16 14:33:52 | INFO     | rsi_backtest.optimizer | Completed 300/300 windows
2025-10-16 14:33:53 | INFO     | rsi_backtest.optimizer | Optimal RSI window: 42 (Sharpe=1.87)
```

## Summary of Decisions

| Component | Decision | Key Benefit |
|-----------|----------|-------------|
| RSI Calculation | TA-Lib's RSI function | Industry standard, C performance |
| Backtest Engine | Event-driven with state management | Look-ahead bias prevention, clarity |
| Cost Model | 0.1% commission + 0.1% stamp (sells) | Hong Kong market realistic |
| Sharpe Ratio | Annualized, 252 days, 2% risk-free | Standard financial metric |
| Performance | Pre-compute RSI, multiprocessing | <5 min for 300 windows |
| Data Validation | Multi-stage pipeline | Fail fast, clear errors |
| Visualization | Matplotlib + seaborn, 150 DPI | Publication-quality |
| Logging | Python logging, file+console | Audit trail, troubleshooting |

All decisions prioritize correctness, performance, and maintainability while adhering to quantitative finance best practices.
