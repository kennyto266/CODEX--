# CLI Interface Contract: 0700.HK RSI Backtest Optimizer

**Feature**: 001-rsi-backtest-optimizer
**Date**: 2025-10-16
**Purpose**: Define command-line interface contract for the RSI backtest optimizer

## Overview

This document specifies the command-line interface for the RSI backtest optimizer. The tool is designed as a single-command application with configurable parameters, following Unix philosophy: do one thing well, text-based I/O, composable with other tools.

## Command Syntax

```bash
python rsi_backtest_optimizer.py [OPTIONS]
```

## Options

### Required Options

None - all options have sensible defaults.

### Optional Parameters

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--data` | path | `data/0700_HK.csv` | Path to input CSV file containing OHLCV data |
| `--start-window` | int | `1` | Starting RSI window for parameter sweep (min: 1) |
| `--end-window` | int | `300` | Ending RSI window for parameter sweep (max: 500) |
| `--step` | int | `1` | Step size for window sweep |
| `--buy-threshold` | float | `30.0` | RSI level below which to generate BUY signal |
| `--sell-threshold` | float | `70.0` | RSI level above which to generate SELL signal |
| `--commission` | float | `0.001` | Commission rate (0.001 = 0.1%) |
| `--stamp-duty` | float | `0.001` | Stamp duty rate on sells (0.001 = 0.1%) |
| `--risk-free-rate` | float | `0.02` | Annual risk-free rate for Sharpe calculation (0.02 = 2%) |
| `--initial-capital` | float | `100000.0` | Starting portfolio value in HKD |
| `--output-dir` | path | `results` | Directory for output files |
| `--no-charts` | flag | False | Skip chart generation (faster for testing) |
| `--parallel-workers` | int | `16` | Number of parallel processes (0 = auto-detect cores) |
| `--log-level` | str | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `--verbose` | flag | False | Enable verbose output (progress bars, detailed logs) |
| `--version` | flag | N/A | Display version and exit |
| `--help` | flag | N/A | Display help message and exit |

## Usage Examples

### Example 1: Basic Usage (All Defaults)

```bash
python rsi_backtest_optimizer.py
```

**Behavior**:
- Loads `data/0700_HK.csv`
- Tests RSI windows 1-300 (step=1)
- Uses thresholds 30/70
- Applies Hong Kong costs (0.1% commission, 0.1% stamp duty)
- Generates all charts
- Outputs to `results/` directory

### Example 2: Custom RSI Window Range

```bash
python rsi_backtest_optimizer.py --start-window 5 --end-window 50 --step 5
```

**Behavior**:
- Tests only windows: 5, 10, 15, 20, 25, 30, 35, 40, 45, 50
- Faster execution (10 backtests instead of 300)
- Useful for quick exploration

### Example 3: Different Thresholds

```bash
python rsi_backtest_optimizer.py --buy-threshold 20 --sell-threshold 80
```

**Behavior**:
- More conservative strategy (buy at RSI<20, sell at RSI>80)
- Fewer trades, potentially different optimal window

### Example 4: Frictionless Backtest (No Costs)

```bash
python rsi_backtest_optimizer.py --commission 0 --stamp-duty 0
```

**Behavior**:
- Zero trading costs
- Useful for comparing with realistic cost scenario

### Example 5: Quick Test Mode

```bash
python rsi_backtest_optimizer.py \
  --start-window 10 \
  --end-window 30 \
  --step 2 \
  --no-charts \
  --log-level WARNING
```

**Behavior**:
- Reduced window range (10, 12, 14, ..., 30)
- No chart generation
- Minimal logging
- Fastest execution for development/testing

### Example 6: Custom Data File

```bash
python rsi_backtest_optimizer.py --data /path/to/my_data.csv --output-dir /path/to/results
```

**Behavior**:
- Load data from custom path
- Save results to custom directory

## Input Format

### CSV File Structure

**Required columns** (case-insensitive, order-agnostic):
- `date`: Date in YYYY-MM-DD format (e.g., "2023-01-03")
- `open`: Opening price (float, must be > 0)
- `high`: Highest price (float, must be >= all other prices)
- `low`: Lowest price (float, must be <= all other prices)
- `close`: Closing price (float, must be > 0)
- `volume`: Trading volume (int, must be >= 0)

**Example**:
```csv
date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
2023-01-05,327.00,330.20,325.80,329.60,21045000
```

**Optional columns** (ignored if present):
- `symbol`, `adjusted_close`, `dividends`, etc.

**Validation**:
- Missing required columns → ERROR, exit code 1
- Invalid date format → ERROR, exit code 1
- Non-monotonic dates → ERROR, exit code 1
- OHLC violations (e.g., high < low) → ERROR, exit code 1

## Output Files

All outputs are saved to `--output-dir` (default: `results/`):

### 1. optimization_results.csv

Complete results for all tested RSI windows.

**Columns**:
- `rsi_window`: RSI configuration (int)
- `total_return`: Total return ratio (float)
- `annualized_return`: Annualized return (float)
- `annualized_volatility`: Annualized volatility (float)
- `sharpe_ratio`: Sharpe ratio (float)
- `max_drawdown`: Maximum drawdown (float, negative)
- `win_rate`: Win rate ratio (float, 0-1)
- `num_trades`: Number of trades (int)

**Example**:
```csv
rsi_window,total_return,annualized_return,annualized_volatility,sharpe_ratio,max_drawdown,win_rate,num_trades
14,0.2345,0.1823,0.2100,0.7729,-0.1234,0.58,24
21,0.3012,0.2201,0.2050,0.9761,-0.1089,0.62,18
42,0.4123,0.2987,0.2200,1.2667,-0.0945,0.67,14
```

### 2. top_10_windows.csv

Best 10 configurations sorted by Sharpe ratio (descending).

**Format**: Same as optimization_results.csv, limited to top 10 rows.

### 3. summary_report.txt

Human-readable summary report.

**Content**:
```
========================================
RSI Backtest Optimization Report
========================================
Date: 2025-10-16 14:35:22
Stock: 0700.HK
Data Period: 2021-01-04 to 2023-12-29 (756 days)

Configuration:
- RSI Windows Tested: 1-300 (step=1)
- Buy Threshold: RSI < 30
- Sell Threshold: RSI > 70
- Commission: 0.1%
- Stamp Duty: 0.1% (on sells)
- Risk-Free Rate: 2.0%
- Initial Capital: HK$100,000

Optimal Result:
- Best RSI Window: 42
- Sharpe Ratio: 1.2667
- Total Return: 41.23%
- Annualized Return: 29.87%
- Annual Volatility: 22.00%
- Max Drawdown: -9.45%
- Win Rate: 67.0%
- Number of Trades: 14

Top 10 RSI Windows:
  Rank  Window  Sharpe   Return   Volatility  Drawdown  Trades
  1     42      1.2667   29.87%   22.00%      -9.45%    14
  2     38      1.1892   27.34%   21.50%      -10.23%   16
  3     35      1.1234   25.67%   20.80%      -11.02%   18
  ...

Buy-and-Hold Baseline:
- Total Return: 28.45%
- Sharpe Ratio: 0.8234
- Max Drawdown: -15.67%

Strategy vs Baseline:
- Outperformance: +12.78% total return
- Risk Reduction: 6.22% less max drawdown
- Sharpe Improvement: +0.4433

Chart Files:
- results/charts/equity_curve.png
- results/charts/rsi_sharpe_relationship.png

Log File: results/logs/backtest_20251016_143522.log
========================================
```

### 4. charts/equity_curve.png

Cumulative returns chart comparing optimal RSI strategy vs buy-and-hold.

**Resolution**: 1200×800 pixels, 150 DPI
**Format**: PNG
**Content**:
- X-axis: Date
- Y-axis: Portfolio value (HKD)
- Two lines: Strategy (blue), Buy-and-Hold (orange)
- Legend, grid, title

### 5. charts/rsi_sharpe_relationship.png

Parameter sensitivity scatter plot.

**Resolution**: 1200×800 pixels, 150 DPI
**Format**: PNG
**Content**:
- X-axis: RSI window (1-300)
- Y-axis: Sharpe ratio
- Scatter points for all tested windows
- Vertical red line at optimal window
- Legend, grid, title

### 6. logs/backtest_YYYYMMDD_HHMMSS.log

Detailed execution log.

**Format**: Timestamped log entries
**Example**:
```
2025-10-16 14:35:10 | INFO | rsi_backtest.data.loader | Loading data from data/0700_HK.csv
2025-10-16 14:35:10 | INFO | rsi_backtest.data.loader | Loaded 756 trading days (2021-01-04 to 2023-12-29)
2025-10-16 14:35:10 | WARNING | rsi_backtest.data.validator | 3 missing trading days detected
2025-10-16 14:35:11 | INFO | rsi_backtest.optimizer | Pre-computing 300 RSI series...
2025-10-16 14:35:14 | INFO | rsi_backtest.optimizer | Starting parallel backtest (16 workers)
2025-10-16 14:35:45 | INFO | rsi_backtest.optimizer | Completed 100/300 windows
2025-10-16 14:36:19 | INFO | rsi_backtest.optimizer | Completed 200/300 windows
2025-10-16 14:36:52 | INFO | rsi_backtest.optimizer | Completed 300/300 windows
2025-10-16 14:36:53 | INFO | rsi_backtest.optimizer | Optimal RSI window: 42 (Sharpe=1.2667)
2025-10-16 14:36:55 | INFO | rsi_backtest.visualizer | Generated charts/equity_curve.png
2025-10-16 14:36:56 | INFO | rsi_backtest.visualizer | Generated charts/rsi_sharpe_relationship.png
2025-10-16 14:36:56 | INFO | rsi_backtest.main | Backtest completed successfully
```

## Exit Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 0 | Success | Backtest completed, results saved |
| 1 | Input error | Missing required columns, invalid CSV format |
| 2 | Validation error | OHLC violations, non-chronological dates |
| 3 | Calculation error | RSI calculation failed, insufficient data |
| 4 | I/O error | Cannot read input file or write output files |
| 5 | Configuration error | Invalid parameter values (e.g., start-window > end-window) |

## Standard Output (stdout)

### Default Mode (--verbose not set)

Progress indicators only:
```
Loading data from data/0700_HK.csv... Done (756 days)
Pre-computing RSI indicators... Done (300 series)
Running backtest optimization...
[=====>                                      ] 100/300 (33%)
[==========>                                 ] 200/300 (67%)
[============================================] 300/300 (100%)
Optimization complete!

Optimal RSI window: 42 (Sharpe=1.2667)
Results saved to: results/
```

### Verbose Mode (--verbose set)

Detailed real-time updates:
```
Loading data from data/0700_HK.csv...
  - Loaded 756 rows
  - Date range: 2021-01-04 to 2023-12-29
  - Validating schema... OK
  - Validating chronological order... OK
  - Validating OHLC relationships... OK
  - Warning: 3 missing trading days detected

Pre-computing RSI indicators...
  - Window 1/300... Done
  - Window 50/300... Done
  - Window 100/300... Done
  ...

Running backtest optimization (16 parallel workers)...
  - Worker 1: Testing windows 1-19
  - Worker 2: Testing windows 20-38
  ...
  - Completed 100/300 (33%) - Elapsed: 31s - ETA: 62s
  - Completed 200/300 (67%) - Elapsed: 64s - ETA: 32s
  - Completed 300/300 (100%) - Elapsed: 102s

Optimization complete!
  - Total execution time: 102.4 seconds
  - Optimal RSI window: 42
  - Optimal Sharpe ratio: 1.2667
  - Total return: 41.23%

Generating visualizations...
  - Created charts/equity_curve.png
  - Created charts/rsi_sharpe_relationship.png

Results summary:
  - All results: results/optimization_results.csv
  - Top 10: results/top_10_windows.csv
  - Report: results/summary_report.txt
  - Log: results/logs/backtest_20251016_143522.log
```

## Standard Error (stderr)

Error messages and warnings:
```
ERROR: Missing required column 'close' in data/0700_HK.csv
ERROR: OHLC validation failed: high < low on 2023-05-15
WARNING: 5 missing trading days detected (2023-01-02, 2023-05-01, ...)
WARNING: RSI window 280 skipped: insufficient data (756 days available, 300 required)
```

## Validation Rules

### Parameter Validation

- `--start-window` must be >= 1
- `--end-window` must be <= 500
- `--start-window` must be < `--end-window`
- `--step` must be >= 1
- `--buy-threshold` must be < `--sell-threshold`
- `--commission` and `--stamp-duty` must be >= 0 and <= 0.1 (10%)
- `--risk-free-rate` must be >= 0 and <= 1.0 (100%)
- `--initial-capital` must be > 0
- `--parallel-workers` must be >= 0 (0 = auto)
- `--log-level` must be one of: DEBUG, INFO, WARNING, ERROR

### Data Validation

- All required columns present
- Dates are valid and chronologically ordered
- OHLC relationships hold (high >= close >= low, etc.)
- No negative prices or volumes
- At least `max(window) + 100` data points available

## Performance Expectations

On AMD Ryzen 9 9950X3D (16 cores, 32 threads, 128GB RAM):
- 300 RSI windows (1-300, step=1)
- 756 trading days of data
- **Expected runtime**: <5 minutes

Approximate breakdown:
- Data loading: 1-2 seconds
- RSI pre-computation: 3-5 seconds
- Backtest execution: 4-4.5 minutes
- Chart generation: 1-2 seconds

## Composability

The CLI is designed to be composable with Unix tools:

### Example: Extract optimal window only
```bash
python rsi_backtest_optimizer.py | grep "Optimal RSI window" | awk '{print $4}'
# Output: 42
```

### Example: Compare multiple threshold configurations
```bash
for threshold in 20 30 40; do
  python rsi_backtest_optimizer.py \
    --buy-threshold $threshold \
    --output-dir results_${threshold} \
    --no-charts
done

# Compare optimal windows
grep "Optimal RSI window" results_*/summary_report.txt
```

### Example: JSON output for programmatic processing
(Future enhancement - not in MVP)
```bash
python rsi_backtest_optimizer.py --output-format json > results.json
```

## Contract Testing

CLI interface must pass these contract tests:

1. **Help flag test**: `python rsi_backtest_optimizer.py --help` exits 0, prints help
2. **Version flag test**: `python rsi_backtest_optimizer.py --version` exits 0, prints version
3. **Default run test**: `python rsi_backtest_optimizer.py` with valid data exits 0, generates all outputs
4. **Invalid data test**: Missing columns → exit 1, error message to stderr
5. **Invalid params test**: `--start-window 100 --end-window 50` → exit 5, error message
6. **Output files test**: All expected files created in output directory
7. **Determinism test**: Same input → same output (byte-identical CSV results)
8. **Performance test**: 300 windows, 756 days → complete in <5 minutes

These tests must be automated in `tests/contract/test_cli.py`.
