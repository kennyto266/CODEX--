# CLI Tool API Contracts

**Version**: 1.0.0
**Date**: 2025-11-10
**Binary Name**: `rust-nonprice`
**Target**: Standalone executable

## Overview

This document defines the command-line interface for the Rust non-price data processing system. The CLI provides convenient commands for all major operations without requiring Python.

---

## Installation

```bash
# Build from source
cd rust-nonprice
cargo build --release

# Or install via cargo
cargo install --path .

# Run
rust-nonprice --help
```

---

## Commands

### 1. `rust-nonprice --version`

Display version information.

**Output**:
```
rust-nonprice 1.0.0
Rust version: 1.75.0
Built: 2025-11-10T10:30:00Z
```

---

### 2. `rust-nonprice --help`

Display help information.

**Output**:
```
Rust Non-Price Data Technical Indicators System

USAGE:
    rust-nonprice [SUBCOMMAND]

FLAGS:
    -h, --help       Print help information
    -V, --version    Print version information

SUBCOMMANDS:
    indicators       Calculate technical indicators
    signals          Generate trading signals
    optimize         Optimize parameters
    backtest         Run backtest
    report           Generate reports
    validate         Validate data

For more information about a subcommand, use:
    rust-nonprice <SUBCOMMAND> --help
```

---

## Data Validation

### `rust-nonprice validate <INPUT>`

Validate input data for completeness and integrity.

**Usage**:
```bash
rust-nonprice validate <INPUT> [OPTIONS]
```

**Arguments**:
- `INPUT`: Path to CSV/Parquet file with non-price data

**Options**:
- `--format <FORMAT>`: Input format (csv, parquet) [default: auto-detect]
- `--output <OUTPUT>`: Path to write validation report (JSON)
- `--fix`: Attempt to fix common issues (missing values, outliers)
- `--verbose`: Show detailed validation results

**Example**:
```bash
# Validate HIBOR data
rust-nonprice validate hibor_data.csv --output validation_report.json

# Validate and auto-fix
rust-nonprice validate visitor_data.csv --fix --verbose
```

**Exit Codes**:
- `0`: All checks passed
- `1`: Validation failed
- `2`: File not found or unreadable

**Output Example**:
```json
{
  "total_records": 1000,
  "valid_records": 995,
  "invalid_records": 5,
  "issues": [
    {
      "row": 42,
      "field": "value",
      "issue": "missing",
      "severity": "error"
    },
    {
      "row": 87,
      "field": "date",
      "issue": "invalid_format",
      "severity": "error"
    }
  ],
  "data_quality_score": 0.995
}
```

---

## Technical Indicator Calculation

### `rust-nonprice indicators <INPUT>`

Calculate technical indicators from non-price data.

**Usage**:
```bash
rust-nonprice indicators <INPUT> [OPTIONS]
```

**Arguments**:
- `INPUT`: Path to input CSV/Parquet file

**Options**:
- `--output <OUTPUT>`: Path to write results (CSV/Parquet) [default: indicators_output.csv]
- `--format <FORMAT>`: Output format (csv, parquet) [default: same as input]
- `--indicator <INDICATOR>`: Specific indicator to calculate (zscore, rsi, sma, all) [default: all]
- `--window <WINDOW>`: Rolling window size (default: 20 for Z-Score, 14 for RSI)
- `--sma-fast <N>`: SMA fast period [default: 10]
- `--sma-slow <N>`: SMA slow period [default: 30]
- `--parallel`: Use parallel processing for large datasets
- `--jobs <N>`: Number of parallel jobs [default: CPU cores]

**Examples**:
```bash
# Calculate all indicators
rust-nonprice indicators hibor_data.csv --output indicators.csv

# Calculate only Z-Score
rust-nonprice indicators hibor_data.csv --indicator zscore --window 30

# Calculate with custom SMA periods
rust-nonprice indicators visitor_data.csv --sma-fast 5 --sma-slow 20

# Use parallel processing
rust-nonprice indicators gdp_data.csv --parallel --jobs 8
```

**Output Columns**:
- `symbol`: Original data symbol
- `date`: Observation date
- `zscore`: Z-Score value (or null)
- `rsi`: RSI value (or null)
- `sma_fast`: Fast SMA (or null)
- `sma_slow`: Slow SMA (or null)

---

## Signal Generation

### `rust-nonprice signals <INDICATORS> <OUTPUT>`

Generate trading signals from technical indicators.

**Usage**:
```bash
rust-nonprice signals <INDICATORS> <OUTPUT> [OPTIONS]
```

**Arguments**:
- `INDICATORS`: Path to indicators file (from `indicators` command)
- `OUTPUT`: Path to write signals (CSV/JSON)

**Options**:
- `--zscore-buy <FLOAT>`: Z-Score buy threshold [default: -0.5]
- `--zscore-sell <FLOAT>`: Z-Score sell threshold [default: 0.5]
- `--rsi-buy <FLOAT>`: RSI buy threshold [default: 25.0]
- `--rsi-sell <FLOAT>`: RSI sell threshold [default: 65.0]
- `--sma-fast <N>`: SMA fast period [default: 10]
- `--sma-slow <N>`: SMA slow period [default: 30]
- `--strategy <STRATEGY>`: Signal combination strategy (majority, consensus, weighted) [default: majority]
- `--params-file <FILE>`: Load parameters from JSON file

**Examples**:
```bash
# Generate signals with default parameters
rust-nonprice signals indicators.csv signals.json

# Use custom thresholds
rust-nonprice signals indicators.csv signals.csv --zscore-buy -1.0 --rsi-sell 70

# Load parameters from file
rust-nonprice signals indicators.csv signals.json --params-file optimal_params.json
```

**Output Columns**:
- `date`: Signal date
- `action`: BUY, SELL, or HOLD
- `confidence`: Confidence score (0.0-1.0)
- `zscore_signal`: Signal from Z-Score
- `rsi_signal`: Signal from RSI
- `sma_signal`: Signal from SMA
- `combined_signal`: Final combined signal

---

## Parameter Optimization

### `rust-nonprice optimize <INDICATORS> <STOCK_DATA> <OUTPUT>`

Optimize parameters across 2,160 combinations.

**Usage**:
```bash
rust-nonprice optimize <INDICATORS> <STOCK_DATA> <OUTPUT> [OPTIONS]
```

**Arguments**:
- `INDICATORS`: Path to indicators file
- `STOCK_DATA`: Path to stock price CSV (OHLCV format)
- `OUTPUT`: Path to write optimization results (JSON)

**Options**:
- `--workers <N>`: Number of parallel workers [default: 8]
- `--timeout <SECONDS>`: Maximum optimization time in seconds [default: 3600]
- `--min-trades <N>`: Minimum trades for valid result [default: 10]
- `--metric <METRIC>`: Optimization metric (sharpe, return, drawdown) [default: sharpe]
- `--zscore-range <MIN:MAX>`: Z-Score search range [default: -2.0:2.0]
- `--zscore-step <FLOAT>`: Z-Score step size [default: 0.5]
- `--rsi-range <MIN:MAX>`: RSI search range [default: 20:80]
- `--rsi-step <FLOAT>`: RSI step size [default: 5]
- `--sma-range <MIN:MAX>`: SMA period range [default: 5:40]
- `--sma-step <FLOAT>`: SMA step size [default: 5]

**Examples**:
```bash
# Basic optimization
rust-nonprice optimize hibor_indicators.csv 0700HK.csv results.json

# Parallel optimization with 16 workers
rust-nonprice optimize indicators.csv stock.csv results.json --workers 16

# Custom search ranges
rust-nonprice optimize indicators.csv stock.csv results.json \
    --zscore-range -3.0:3.0 --rsi-range 10:90

# Optimize for total return instead of Sharpe
rust-nonprice optimize indicators.csv stock.csv results.json --metric return
```

**Output Example**:
```json
{
  "best_parameters": {
    "zscore_buy": -0.5,
    "zscore_sell": 0.5,
    "rsi_buy": 25.0,
    "rsi_sell": 65.0,
    "sma_fast": 10,
    "sma_slow": 30
  },
  "best_sharpe": 0.72,
  "best_return": 18.5,
  "best_drawdown": -12.3,
  "total_combinations": 2160,
  "valid_combinations": 2100,
  "execution_time_seconds": 245,
  "all_results": [...]
}
```

**Progress Output**:
```
[00:00] Exploring parameter combinations... 0/2160 (0.0%)
[00:15] Exploring parameter combinations... 540/2160 (25.0%) Best Sharpe: 0.65
[00:30] Exploring parameter combinations... 1080/2160 (50.0%) Best Sharpe: 0.70
[00:45] Exploring parameter combinations... 1620/2160 (75.0%) Best Sharpe: 0.72
[01:00] Optimization complete! Best Sharpe: 0.72
```

---

## Backtesting

### `rust-nonprice backtest <SIGNALS> <STOCK_DATA>`

Run backtest with trading signals and stock data.

**Usage**:
```bash
rust-nonprice backtest <SIGNALS> <STOCK_DATA> [OPTIONS]
```

**Arguments**:
- `SIGNALS`: Path to signals file (from `signals` command)
- `STOCK_DATA`: Path to stock price CSV (OHLCV format)

**Options**:
- `--output <OUTPUT>`: Path to write backtest results (JSON/Markdown)
- `--format <FORMAT>`: Output format (json, markdown, both) [default: json]
- `--initial-capital <FLOAT>`: Starting capital [default: 100000.0]
- `--commission <FLOAT>`: Commission rate (0.001 = 0.1%) [default: 0.001]
- `--slippage <FLOAT>`: Slippage rate [default: 0.0005]
- `--risk-free <FLOAT>`: Risk-free rate [default: 0.02]

**Examples**:
```bash
# Basic backtest
rust-nonprice backtest signals.json 0700HK.csv --output backtest_results.json

# Generate Markdown report
rust-nonprice backtest signals.csv stock.csv --format markdown --output report.md

# Custom parameters
rust-nonprice backtest signals.csv stock.csv \
    --initial-capital 500000 \
    --commission 0.0005 \
    --output results.json
```

**Output Example** (JSON):
```json
{
  "symbol": "0700.HK",
  "period": {
    "start": "2022-01-01",
    "end": "2024-12-31"
  },
  "initial_capital": 100000.0,
  "final_value": 178045.36,
  "metrics": {
    "total_return_pct": 78.05,
    "annual_return_pct": 17.83,
    "sharpe_ratio": 0.70,
    "max_drawdown_pct": -51.25,
    "win_rate_pct": 51.27,
    "total_trades": 612,
    "avg_hold_days": 14.5
  },
  "trades": [...],
  "equity_curve": [...]
}
```

---

## Report Generation

### `rust-nonprice report <RESULTS>`

Generate comprehensive reports from backtest results.

**Usage**:
```bash
rust-nonprice report <RESULTS> [OPTIONS]
```

**Arguments**:
- `RESULTS`: Path to backtest results (JSON from `backtest` command)

**Options**:
- `--output <OUTPUT>`: Output directory for reports [default: ./reports/]
- `--format <FORMAT>`: Report format (markdown, html, pdf, all) [default: markdown]
- `--include-trades`: Include individual trade details
- `--include-charts`: Generate performance charts (requires gnuplot)

**Examples**:
```bash
# Generate Markdown report
rust-nonprice report backtest_results.json

# Generate all formats
rust-nonprice report backtest_results.json --format all --output ./reports/

# Include trade details
rust-nonprice report backtest_results.json --include-trades
```

**Generated Files**:
```
reports/
├── summary.md              # Executive summary
├── detailed_report.md      # Full report with metrics
├── trades.csv              # Individual trades
├── equity_curve.png        # Performance chart
├── drawdown.png            # Drawdown chart
└── metrics.json            # Machine-readable metrics
```

---

## Complete Workflow Example

```bash
# 1. Validate input data
rust-nonprice validate hibor_data.csv --fix

# 2. Calculate technical indicators
rust-nonprice indicators hibor_data.csv --output indicators.csv --parallel

# 3. Optimize parameters
rust-nonprice optimize indicators.csv 0700HK.csv results.json --workers 8

# 4. Generate signals with optimal parameters
rust-nonprice signals indicators.csv signals.json --params-file results.json

# 5. Run backtest
rust-nonprice backtest signals.json 0700HK.csv --output backtest.json --format both

# 6. Generate reports
rust-nonprice report backtest.json --format all --output ./final_report/
```

---

## Error Handling

**Common Error Codes**:
- `0`: Success
- `1`: Invalid arguments or input
- `2`: File not found or unreadable
- `3`: Data validation failed
- `4`: Optimization timeout
- `5`: Backtest error (insufficient data, etc.)

**Example Error Output**:
```
ERROR: Data validation failed
  File: hibor_data.csv
  Issues: 5 invalid records
  Run with --fix to attempt automatic repair
  See validation_report.json for details
```

**Debug Mode**:
```bash
# Enable debug logging
RUST_LOG=debug rust-nonprice optimize indicators.csv stock.csv results.json
```

---

**CLI API Completed**: 2025-11-10
**Status**: ✅ Complete - Ready for implementation
