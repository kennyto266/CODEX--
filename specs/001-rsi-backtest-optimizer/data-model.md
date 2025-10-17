# Data Model: 0700.HK RSI Backtest Optimizer

**Feature**: 001-rsi-backtest-optimizer
**Date**: 2025-10-16
**Purpose**: Define all data structures and their relationships for the RSI backtest system

## Overview

This document specifies the data model for the RSI backtest optimizer, covering input data structures, intermediate calculations, backtest state, and output formats. All entities are designed for in-memory processing with file-system persistence.

## Core Entities

### 1. PriceData

**Purpose**: Represents daily OHLCV price records for 0700.HK stock.

**Fields**:
- `date`: datetime64 - Trading date (YYYY-MM-DD format)
- `open`: float64 - Opening price in HKD
- `high`: float64 - Highest price during the day in HKD
- `low`: float64 - Lowest price during the day in HKD
- `close`: float64 - Closing price in HKD
- `volume`: int64 - Number of shares traded

**Validation Rules**:
- `date` must be unique (no duplicate dates)
- `date` must be in chronological ascending order
- `high >= max(open, close, low)` (high is truly the highest)
- `low <= min(open, close, high)` (low is truly the lowest)
- `close > 0` and `open > 0` (no zero or negative prices)
- `volume >= 0` (volume can be zero but not negative)

**Relationships**:
- Input to RSI Indicator calculation
- Used by BacktestEngine for price lookups

**Storage Format**: CSV file with header row
```csv
date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
```

**In-Memory Representation**: pandas DataFrame

---

### 2. RSIIndicator

**Purpose**: Stores calculated RSI values for each day and RSI window configuration.

**Fields**:
- `date`: datetime64 - Trading date
- `rsi`: float64 - RSI value (range: 0.0 to 100.0)
- `window`: int - RSI calculation window in days (1-300)

**Validation Rules**:
- `rsi` must be in range [0, 100] or NaN (for insufficient data)
- `window` must be in range [1, 300]
- First `window` + warmup (typically 100) values will be NaN

**Calculation Formula** (Wilder's smoothing):
```
1. Calculate price changes: delta = close[t] - close[t-1]
2. Separate gains and losses:
   gain[t] = delta[t] if delta[t] > 0 else 0
   loss[t] = -delta[t] if delta[t] < 0 else 0
3. Apply exponential smoothing with span=window:
   avg_gain = EMA(gain, span=window)
   avg_loss = EMA(loss, span=window)
4. Calculate RS and RSI:
   RS = avg_gain / avg_loss
   RSI = 100 - (100 / (1 + RS))
```

**Relationships**:
- Derived from PriceData
- Input to TradingSignal generation

**Storage Format**: Not persisted (calculated on-the-fly, cached in memory)

**In-Memory Representation**: pandas Series (one per window) or DataFrame with MultiIndex(date, window)

---

### 3. TradingSignal

**Purpose**: Discrete trading actions generated from RSI thresholds.

**Fields**:
- `date`: datetime64 - Signal generation date
- `action`: enum - One of: 'BUY', 'SELL', 'HOLD'
- `rsi_value`: float64 - RSI value that triggered the signal
- `window`: int - RSI window configuration used

**Generation Rules**:
- `action = 'BUY'` when `rsi_value < 30`
- `action = 'SELL'` when `rsi_value > 70`
- `action = 'HOLD'` when `30 <= rsi_value <= 70`

**Boundary Conditions**:
- `rsi_value == 30` → 'HOLD' (not 'BUY')
- `rsi_value == 70` → 'HOLD' (not 'SELL')

**Validation Rules**:
- Signal at date T must only use RSI values up to and including date T (no look-ahead)
- If RSI is NaN, signal is 'HOLD'

**Relationships**:
- Derived from RSIIndicator
- Input to BacktestEngine for trade execution

**Storage Format**: Not persisted (generated during backtest)

**In-Memory Representation**: pandas Series or list of signal tuples

---

### 4. Position

**Purpose**: Tracks current holdings state in the backtest simulation.

**Fields**:
- `status`: enum - 'IN_MARKET' (holding stock) or 'OUT_MARKET' (holding cash)
- `entry_date`: datetime64 - Date when current position was opened (null if OUT_MARKET)
- `entry_price`: float64 - Price at which stock was purchased (null if OUT_MARKET)
- `shares`: int - Number of shares held (0 if OUT_MARKET)
- `cash`: float64 - Cash balance in HKD
- `equity`: float64 - Total portfolio value (cash + shares * current_price)

**State Transitions**:
```
OUT_MARKET --[BUY signal]--> IN_MARKET
  - Deduct cash for purchase + commission
  - Set entry_date, entry_price, shares

IN_MARKET --[SELL signal]--> OUT_MARKET
  - Add cash from sale - commission - stamp_duty
  - Clear entry_date, entry_price, shares to default

IN_MARKET --[HOLD signal]--> IN_MARKET (no change)
OUT_MARKET --[HOLD signal]--> OUT_MARKET (no change)
```

**Validation Rules**:
- `cash >= 0` (no negative cash balance / no leverage)
- `shares >= 0` (no short selling)
- `equity = cash + shares * current_price` must always hold
- When `status = 'OUT_MARKET'`, `shares = 0`
- When `status = 'IN_MARKET'`, `shares > 0`

**Relationships**:
- Updated by BacktestEngine based on TradingSignals
- Generates Trade records when position changes

**Storage Format**: Not persisted (transient state during backtest)

**In-Memory Representation**: Python class instance or dict

---

### 5. Trade

**Purpose**: Records individual buy/sell transactions during backtest.

**Fields**:
- `trade_id`: int - Unique identifier (sequential)
- `date`: datetime64 - Execution date
- `action`: enum - 'BUY' or 'SELL'
- `price`: float64 - Execution price in HKD
- `shares`: int - Number of shares transacted
- `gross_amount`: float64 - `price * shares`
- `commission`: float64 - Commission paid (0.1% of gross_amount)
- `stamp_duty`: float64 - Stamp duty paid (0.1% of gross_amount for SELL, 0 for BUY)
- `total_cost`: float64 - `commission + stamp_duty`
- `net_amount`: float64 - `gross_amount - total_cost` (for SELL) or `gross_amount + total_cost` (for BUY)

**Cost Calculation**:
```python
# BUY example: Purchase HK$100,000 of stock
gross_amount = 100000
commission = gross_amount * 0.001 = 100
stamp_duty = 0  # No stamp duty on buys
total_cost = 100
net_amount = 100000 + 100 = 100100  # Cash outflow

# SELL example: Sell HK$110,000 of stock
gross_amount = 110000
commission = gross_amount * 0.001 = 110
stamp_duty = gross_amount * 0.001 = 110
total_cost = 220
net_amount = 110000 - 220 = 109780  # Cash inflow
```

**Validation Rules**:
- `trade_id` is unique and sequential
- `action` is either 'BUY' or 'SELL' (not 'HOLD')
- `shares > 0` (cannot trade zero shares)
- `price > 0` (no zero-price trades)
- `stamp_duty > 0` only if `action = 'SELL'`

**Relationships**:
- Generated by BacktestEngine when Position state changes
- Aggregated into PerformanceMetrics for analysis

**Storage Format**: CSV output for audit trail
```csv
trade_id,date,action,price,shares,gross_amount,commission,stamp_duty,total_cost,net_amount
1,2023-01-05,BUY,324.20,308,99853.60,99.85,0.00,99.85,99953.45
2,2023-02-10,SELL,342.80,308,105582.40,105.58,105.58,211.16,105371.24
```

**In-Memory Representation**: List of Trade objects or pandas DataFrame

---

### 6. PerformanceMetrics

**Purpose**: Calculated statistics for each RSI window backtest.

**Fields**:
- `rsi_window`: int - RSI configuration tested (1-300)
- `total_return`: float64 - Overall return: (final_equity - initial_equity) / initial_equity
- `annualized_return`: float64 - Mean daily return × 252
- `annualized_volatility`: float64 - Std daily return × √252
- `sharpe_ratio`: float64 - (annual_return - 0.02) / annual_volatility
- `max_drawdown`: float64 - Maximum peak-to-trough decline in equity
- `win_rate`: float64 - Percentage of profitable trades
- `num_trades`: int - Total number of trades (buy + sell)
- `cumulative_returns`: pandas.Series - Daily equity curve

**Calculation Formulas**:
```python
# Total return
initial_equity = 100000  # Starting capital
final_equity = position.equity  # Ending portfolio value
total_return = (final_equity - initial_equity) / initial_equity

# Annualized return and volatility
daily_returns = equity_series.pct_change().dropna()
annualized_return = daily_returns.mean() * 252
annualized_volatility = daily_returns.std() * np.sqrt(252)

# Sharpe ratio
risk_free_rate = 0.02  # 2% annual
excess_returns = daily_returns - (risk_free_rate / 252)
sharpe_ratio = (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))

# Max drawdown
cumulative = (1 + daily_returns).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min()

# Win rate
profitable_trades = trades[(trades['action'] == 'SELL') & (trades['net_amount'] > trades['entry_cost'])]
win_rate = len(profitable_trades) / len(trades[trades['action'] == 'SELL'])
```

**Validation Rules**:
- `sharpe_ratio` is finite (not inf or NaN) unless num_trades = 0
- `max_drawdown <= 0` (drawdown is negative by convention)
- `win_rate` in range [0, 1]
- `num_trades >= 0` and even (every BUY has corresponding SELL in complete backtest)

**Relationships**:
- Derived from Trade records and Position history
- Aggregated into OptimizationReport

**Storage Format**: CSV output with one row per RSI window
```csv
rsi_window,total_return,annualized_return,annualized_volatility,sharpe_ratio,max_drawdown,win_rate,num_trades
14,0.2345,0.1823,0.2100,0.7729,-0.1234,0.58,24
21,0.3012,0.2201,0.2050,0.9761,-0.1089,0.62,18
```

**In-Memory Representation**: pandas DataFrame (one row per window)

---

### 7. BacktestResult

**Purpose**: Complete output for a single RSI window test.

**Fields**:
- `rsi_window`: int - Configuration tested
- `trades`: List[Trade] - All executed trades
- `position_history`: pandas.DataFrame - Daily position snapshots
- `metrics`: PerformanceMetrics - Aggregated statistics
- `equity_curve`: pandas.Series - Daily equity values

**Validation Rules**:
- All trades must be chronologically ordered
- Position history dates must match price data dates
- Metrics must be consistent with trades and equity curve

**Relationships**:
- Contains Trade, Position history, and PerformanceMetrics
- 300 BacktestResults (one per window) are aggregated into OptimizationReport

**Storage Format**: Not persisted as single entity (components saved separately)

**In-Memory Representation**: Python dataclass or dict

---

### 8. OptimizationReport

**Purpose**: Final summary identifying optimal RSI window and top performers.

**Fields**:
- `optimal_window`: int - RSI window with highest Sharpe ratio
- `optimal_sharpe`: float64 - Sharpe ratio of optimal window
- `top_10_windows`: pandas.DataFrame - Best 10 configurations ranked by Sharpe
- `all_results`: pandas.DataFrame - PerformanceMetrics for all 300 windows
- `best_equity_curve`: pandas.Series - Equity curve of optimal window
- `baseline_equity_curve`: pandas.Series - Buy-and-hold performance
- `chart_paths`: dict - File paths to generated visualizations

**Validation Rules**:
- `optimal_window` must be in range [1, 300]
- `top_10_windows` must have exactly 10 rows (or fewer if some windows had no trades)
- `all_results` must have 300 rows

**Relationships**:
- Aggregates all 300 BacktestResults
- Used to generate final charts and summary report

**Storage Format**: Multiple outputs
- `optimization_results.csv`: all_results DataFrame
- `top_10_windows.csv`: top_10_windows DataFrame
- `summary_report.txt`: Human-readable summary

**In-Memory Representation**: Python class or dict

---

## Entity Relationships Diagram

```
PriceData (CSV input)
    ↓
RSIIndicator (calculated, one per window)
    ↓
TradingSignal (generated from RSI thresholds)
    ↓
BacktestEngine (processes signals)
    ↓
Position (current state) + Trade (transactions)
    ↓
PerformanceMetrics (calculated from trades/equity)
    ↓
BacktestResult (per-window output)
    ↓
OptimizationReport (aggregated findings)
```

## Data Flow

1. **Load** PriceData from CSV
2. **Validate** PriceData (schema, chronology, sanity checks)
3. **Calculate** 300 RSIIndicator series (one per window 1-300)
4. For each window:
   a. **Generate** TradingSignals from RSI thresholds
   b. **Execute** backtest: iterate through dates, update Position, record Trades
   c. **Calculate** PerformanceMetrics from trades and equity curve
   d. **Store** BacktestResult
5. **Aggregate** all 300 BacktestResults into OptimizationReport
6. **Identify** optimal_window (highest Sharpe ratio)
7. **Generate** visualizations (equity curve, parameter sensitivity chart)
8. **Save** results to files

## Storage Organization

```
data/
  └── 0700_HK.csv             # Input: PriceData

results/
  ├── optimization_results.csv # All 300 PerformanceMetrics
  ├── top_10_windows.csv       # Best 10 configurations
  ├── summary_report.txt       # Human-readable summary
  ├── trades/
  │   ├── window_014_trades.csv # Trade log for RSI(14)
  │   ├── window_021_trades.csv # Trade log for RSI(21)
  │   └── ...                   # One file per window
  ├── charts/
  │   ├── equity_curve.png     # Optimal vs buy-hold
  │   └── rsi_sharpe_relationship.png
  └── logs/
      └── backtest_20251016_143210.log
```

## Summary

This data model provides:
- Clear entity definitions with validation rules
- Explicit state transitions (Position changes)
- Comprehensive calculation formulas (RSI, Sharpe, drawdown)
- Structured output formats for analysis and audit
- Temporal consistency (no look-ahead bias by design)

All entities are designed for in-memory processing with file-system persistence, optimized for the 300-window parameter sweep workflow.
