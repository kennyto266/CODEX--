# Quickstart Guide: 0700.HK RSI Backtest Optimizer

**Feature**: 001-rsi-backtest-optimizer
**Date**: 2025-10-16
**Purpose**: Get analysts up and running with the RSI backtest optimizer in under 10 minutes

## What You'll Build

An RSI-based backtest optimizer that:
1. Tests 300 RSI window configurations (1-300 days)
2. Finds the optimal parameter maximizing Sharpe ratio
3. Generates performance charts and comprehensive reports
4. Completes analysis in under 5 minutes

## Prerequisites

**Hardware**: Modern laptop/desktop (8GB+ RAM recommended, faster with multi-core CPU)

**Software**:
- Python 3.8 or later
- Git (for cloning repository)
- Text editor or IDE

**Knowledge**:
- Basic Python programming
- Familiarity with command line
- Understanding of RSI indicator (optional but helpful)

## Quick Start (5 Steps)

### Step 1: Setup Environment (2 minutes)

```bash
# Clone the repository (or navigate to project directory)
cd /path/to/codex

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: TA-Lib installation may require additional steps on some systems. See [TA-Lib Installation](#ta-lib-installation) section below if you encounter issues.

### Step 2: Prepare Data (1 minute)

Create a CSV file with 0700.HK price data:

```csv
date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
2023-01-05,327.00,330.20,325.80,329.60,21045000
```

Save as `data/0700_HK.csv`

**Quick Test**: Use the provided sample data:
```bash
# Sample data is included in the repository
ls data/0700_HK.csv  # Should exist
```

### Step 3: Run Basic Backtest (5 seconds)

```bash
python rsi_backtest_optimizer.py
```

**What happens**:
- Loads data from `data/0700_HK.csv`
- Tests RSI windows 1-300
- Uses standard thresholds (buy<30, sell>70)
- Applies Hong Kong trading costs
- Generates charts and reports

**Expected output**:
```
Loading data from data/0700_HK.csv... Done (756 days)
Pre-computing RSI indicators... Done (300 series)
Running backtest optimization...
[============================================] 300/300 (100%)
Optimization complete!

Optimal RSI window: 42 (Sharpe=1.2667)
Results saved to: results/
```

### Step 4: Review Results (2 minutes)

Open the summary report:
```bash
# On Windows:
type results\summary_report.txt

# On Linux/Mac:
cat results/summary_report.txt
```

View the charts:
- `results/charts/equity_curve.png` - Strategy vs buy-and-hold
- `results/charts/rsi_sharpe_relationship.png` - Parameter sensitivity

### Step 5: Explore Different Configurations (Optional)

Try custom parameters:

```bash
# Test only RSI windows 10-50 (faster)
python rsi_backtest_optimizer.py --start-window 10 --end-window 50

# More aggressive thresholds
python rsi_backtest_optimizer.py --buy-threshold 20 --sell-threshold 80

# Zero trading costs (theoretical maximum)
python rsi_backtest_optimizer.py --commission 0 --stamp-duty 0
```

## Understanding the Results

### Key Metrics Explained

**Sharpe Ratio**: Risk-adjusted return metric
- \> 2.0: Excellent
- 1.0-2.0: Good
- 0.5-1.0: Acceptable
- < 0.5: Poor

**Total Return**: Overall percentage gain/loss
- Example: 0.4123 = 41.23% gain

**Max Drawdown**: Worst peak-to-trough decline
- Example: -0.0945 = -9.45% max loss from peak
- Lower (less negative) is better

**Win Rate**: Percentage of profitable trades
- Example: 0.67 = 67% of trades were winners

### Reading the Summary Report

```
Optimal Result:
- Best RSI Window: 42          ← Use this parameter for trading
- Sharpe Ratio: 1.2667         ← Risk-adjusted performance
- Total Return: 41.23%         ← Overall profit
- Max Drawdown: -9.45%         ← Worst decline
- Number of Trades: 14         ← Trading frequency
```

### Interpreting the Charts

**Equity Curve** (`equity_curve.png`):
- Blue line = RSI strategy performance
- Orange line = Buy-and-hold baseline
- Higher is better
- Smooth curves indicate consistent returns

**Parameter Sensitivity** (`rsi_sharpe_relationship.png`):
- Each dot = one RSI window test
- Red line = optimal window
- Cluster of good performance suggests robust parameter range
- Sparse high Sharpe values may indicate overfitting

## Common Tasks

### Compare Multiple Stocks

```bash
# Analyze different stocks
python rsi_backtest_optimizer.py --data data/0001_HK.csv --output-dir results_0001
python rsi_backtest_optimizer.py --data data/0700_HK.csv --output-dir results_0700

# Compare optimal windows
grep "Optimal RSI window" results_*/summary_report.txt
```

### Quick Parameter Exploration

```bash
# Fast test with fewer windows
python rsi_backtest_optimizer.py \
  --start-window 10 \
  --end-window 50 \
  --step 5 \
  --no-charts

# Output: Tests windows 10, 15, 20, ..., 50 (9 backtests, ~30 seconds)
```

### Sensitivity Analysis (Threshold Tuning)

```bash
# Test different buy/sell thresholds
for buy_thresh in 20 30 40; do
  python rsi_backtest_optimizer.py \
    --buy-threshold $buy_thresh \
    --output-dir results_buy${buy_thresh}
done

# Compare results
ls -d results_buy*/
```

### Export for Further Analysis

```bash
# Results are in CSV format, ready for Excel/Python/R
python -c "import pandas as pd; df = pd.read_csv('results/optimization_results.csv'); print(df.describe())"

# Or open in Excel
start results\optimization_results.csv  # Windows
open results/optimization_results.csv   # Mac
```

## Troubleshooting

### Problem: "Missing required column 'close'"

**Solution**: Check CSV file format. Required columns: `date`, `open`, `high`, `low`, `close`, `volume`

```bash
# Verify CSV header
head -1 data/0700_HK.csv
# Should output: date,open,high,low,close,volume
```

### Problem: "OHLC validation failed: high < low"

**Solution**: Data quality issue. Check for corrupted rows:

```python
import pandas as pd
df = pd.read_csv('data/0700_HK.csv')
invalid = df[df['high'] < df['low']]
print(invalid)  # Shows problematic rows
```

Fix corrupted rows or remove them before re-running.

### Problem: Slow execution (>10 minutes)

**Possible causes**:
1. **Large dataset**: More than 3000 days of data
   - **Solution**: Use `--start-window 5 --end-window 100` to reduce tests

2. **Insufficient CPU cores**
   - **Solution**: Check `--parallel-workers` (default: 16)
   - Reduce if you have fewer cores: `--parallel-workers 4`

3. **TA-Lib not installed correctly**
   - **Solution**: Reinstall TA-Lib (see installation section)

### Problem: Charts not generated

**Check**:
```bash
ls results/charts/
# Should list: equity_curve.png, rsi_sharpe_relationship.png
```

**Solution**: Ensure matplotlib is installed correctly:
```bash
pip install --upgrade matplotlib
python -c "import matplotlib.pyplot as plt; print('OK')"
```

### Problem: "Permission denied" writing to results/

**Solution**: Check directory permissions:
```bash
# Create results directory manually
mkdir -p results/charts results/logs

# Or specify different output directory
python rsi_backtest_optimizer.py --output-dir /path/to/writable/dir
```

## TA-Lib Installation

TA-Lib requires special installation on some platforms:

### Windows

1. Download pre-built wheel from [TA-Lib releases](https://github.com/cgohlke/talib-build/releases)
2. Choose file matching your Python version (e.g., `TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl` for Python 3.10)
3. Install:
   ```bash
   pip install TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl
   ```

### Linux (Ubuntu/Debian)

```bash
# Install TA-Lib C library
sudo apt-get update
sudo apt-get install ta-lib

# Install Python wrapper
pip install TA-Lib
```

### macOS

```bash
# Install via Homebrew
brew install ta-lib

# Install Python wrapper
pip install TA-Lib
```

### Verification

```python
python -c "import talib; print('TA-Lib version:', talib.__version__)"
# Expected output: TA-Lib version: 0.4.24 (or similar)
```

## Next Steps

### Validate Results

Run the test suite to ensure everything works:
```bash
pytest tests/contract/test_cli.py -v
```

### Customize Strategy

Modify RSI thresholds or add features:
1. Edit `src/strategy/signals.py` for signal logic
2. Edit `src/backtest/engine.py` for position management
3. Re-run backtest to see impact

### Integrate with Workflow

Add to automated analysis pipeline:
```bash
#!/bin/bash
# daily_analysis.sh

# Download latest data
python scripts/download_data.py --symbol 0700.HK

# Run backtest
python rsi_backtest_optimizer.py --data data/0700_HK.csv

# Email report
python scripts/email_report.py results/summary_report.txt
```

### Explore Advanced Features

- **Multi-stock comparison**: Analyze multiple symbols
- **Walk-forward optimization**: Split data into train/test periods
- **Monte Carlo simulation**: Test strategy robustness
- **Risk-adjusted position sizing**: Kelly criterion, fixed fractional

(These features are out-of-scope for MVP but can be added later)

## Project Structure (Quick Reference)

```
codex/
├── rsi_backtest_optimizer.py  # Main entry point (run this)
├── src/
│   ├── data/                  # Data loading & validation
│   ├── indicators/            # RSI calculation
│   ├── strategy/              # Signal generation & backtest
│   ├── performance/           # Metrics & optimization
│   └── visualization/         # Chart generation
├── tests/                     # Test suite
├── data/                      # Input CSV files
├── results/                   # Output directory
│   ├── optimization_results.csv
│   ├── top_10_windows.csv
│   ├── summary_report.txt
│   ├── charts/
│   └── logs/
├── requirements.txt           # Python dependencies
└── README.md                  # Full documentation
```

## Summary

You've learned how to:
1. ✅ Install and setup the RSI backtest optimizer
2. ✅ Run a basic 300-window parameter sweep
3. ✅ Interpret Sharpe ratios and performance metrics
4. ✅ Generate and review charts
5. ✅ Troubleshoot common issues

**Time invested**: ~10 minutes
**Output**: Optimal RSI parameter for 0700.HK with full performance analysis

**Next**: Review full documentation in `README.md` for advanced usage patterns and development guidelines.

## Getting Help

- **Documentation**: See `README.md` for comprehensive guide
- **Specification**: See `specs/001-rsi-backtest-optimizer/spec.md` for requirements
- **Technical Design**: See `specs/001-rsi-backtest-optimizer/data-model.md` and `research.md`
- **CLI Reference**: See `specs/001-rsi-backtest-optimizer/contracts/cli_interface.md`
- **Issues**: Report bugs or request features via project issue tracker

Happy backtesting!
