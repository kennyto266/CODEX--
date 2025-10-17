# RSI Backtest Optimizer

A Python-based RSI (Relative Strength Index) strategy backtest optimizer that systematically tests RSI window parameters to identify optimal configurations maximizing risk-adjusted returns.

## Features

- **Comprehensive Parameter Sweep**: Test RSI windows from 1-300 days
- **Performance Optimization**: Parallel execution using multiprocessing
- **Realistic Cost Model**: Hong Kong market trading costs (commission + stamp duty)
- **Rich Metrics**: Sharpe ratio, returns, drawdown, win rate, and more
- **Publication-Quality Charts**: Equity curves and parameter sensitivity plots
- **Zero Look-Ahead Bias**: Event-driven backtest engine ensures temporal correctness
- **Extensive Test Coverage**: 80%+ test coverage with unit, integration, and contract tests

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd forest-focusCODEX

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: TA-Lib installation may require additional steps. See [TA-Lib Installation](#ta-lib-installation) below.

### Basic Usage

```bash
# Run with sample data
python rsi_backtest_optimizer.py --data data/0700_HK_sample.csv

# Custom RSI window range
python rsi_backtest_optimizer.py \
  --start-window 10 \
  --end-window 50 \
  --step 5

# Adjust signal thresholds
python rsi_backtest_optimizer.py \
  --buy-threshold 20 \
  --sell-threshold 80
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--data` | `data/0700_HK.csv` | Path to input CSV file |
| `--start-window` | `1` | Starting RSI window |
| `--end-window` | `300` | Ending RSI window |
| `--step` | `1` | Step size for window sweep |
| `--buy-threshold` | `30.0` | RSI buy signal threshold |
| `--sell-threshold` | `70.0` | RSI sell signal threshold |
| `--commission` | `0.001` | Commission rate (0.1%) |
| `--stamp-duty` | `0.001` | Stamp duty on sells (0.1%) |
| `--initial-capital` | `100000.0` | Starting capital (HKD) |
| `--risk-free-rate` | `0.02` | Annual risk-free rate (2%) |
| `--output-dir` | `results` | Output directory |
| `--no-charts` | False | Skip chart generation |
| `--parallel-workers` | auto | Number of parallel processes |
| `--log-level` | `INFO` | Logging level |
| `--verbose` | False | Enable verbose output |

## Input Data Format

CSV file with required columns:
- `date`: Trading date (YYYY-MM-DD)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price
- `close`: Closing price
- `volume`: Trading volume

Example:
```csv
date,open,high,low,close,volume
2023-01-03,320.00,325.60,318.40,324.20,15234000
2023-01-04,324.80,328.00,322.60,327.40,18921000
```

## Output Files

All outputs are saved to the `--output-dir` (default: `results/`):

- `optimization_results.csv`: Complete results for all tested windows
- `top_10_windows.csv`: Best 10 configurations by Sharpe ratio
- `summary_report.txt`: Human-readable summary
- `charts/equity_curve.png`: Strategy vs buy-and-hold comparison
- `charts/rsi_sharpe_relationship.png`: Parameter sensitivity scatter plot
- `logs/backtest_YYYYMMDD_HHMMSS.log`: Detailed execution log

## Performance Metrics

- **Sharpe Ratio**: Risk-adjusted return (annualized)
- **Total Return**: Overall percentage gain/loss
- **Annualized Return**: Mean daily return × 252 days
- **Annualized Volatility**: Std of daily returns × √252
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Win Rate**: Percentage of profitable round-trip trades
- **Number of Trades**: Total buy + sell transactions

## Architecture

```
src/
├── data/              # Data loading and validation
│   ├── loader.py
│   └── validator.py
├── indicators/        # RSI calculation (TA-Lib wrapper)
│   └── rsi.py
├── strategy/          # Signal generation and backtest engine
│   ├── signals.py
│   └── backtest_engine.py
├── performance/       # Metrics and optimization
│   ├── metrics.py
│   └── optimizer.py
└── visualization/     # Chart generation
    ├── equity_curve.py
    └── parameter_chart.py
```

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/contract/ -v       # Contract tests

# Generate coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## TA-Lib Installation

### Windows

1. Download pre-built wheel from [TA-Lib releases](https://github.com/cgohlke/talib-build/releases)
2. Install: `pip install TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl`

### Linux

```bash
sudo apt-get update
sudo apt-get install ta-lib
pip install TA-Lib
```

### macOS

```bash
brew install ta-lib
pip install TA-Lib
```

## Examples

### Find Optimal RSI Parameter

```bash
python rsi_backtest_optimizer.py --data data/0700_HK_sample.csv
```

Output:
```
Optimal RSI Window: 42
Sharpe Ratio: 1.2667
Total Return: 41.23%
Max Drawdown: -9.45%
```

### Compare Different Thresholds

```bash
for threshold in 20 30 40; do
  python rsi_backtest_optimizer.py \
    --buy-threshold $threshold \
    --output-dir results_buy${threshold}
done
```

### Quick Test (No Charts)

```bash
python rsi_backtest_optimizer.py \
  --start-window 10 \
  --end-window 30 \
  --step 5 \
  --no-charts
```

## Troubleshooting

### "Missing required column 'close'"

Check CSV format. Required columns: `date`, `open`, `high`, `low`, `close`, `volume`

### "OHLC validation failed"

Data quality issue. Check for:
- `high < low` violations
- Negative prices
- Non-chronological dates

### Slow execution

Reduce window range or increase `--parallel-workers`

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Citation

If you use this software in your research, please cite:

```bibtex
@software{rsi_backtest_optimizer,
  title = {RSI Backtest Optimizer},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/rsi-backtest-optimizer}
}
```

## Contact

For questions or issues, please open an issue on GitHub.
