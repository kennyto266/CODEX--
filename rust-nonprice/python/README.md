# Rust-NonPrice Python Bindings

Python bindings for the high-performance Rust non-price data technical indicators system.

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd rust-nonprice/python

# Build and install
maturin build --release
pip install target/wheels/*.whl
```

### Requirements

- Python 3.8+
- Rust 1.70+
- maturin

Install maturin:
```bash
pip install maturin
```

## Quick Start

```python
import rust_nonprice

# Create a non-price indicator
hibor = rust_nonprice.PyNonPriceIndicator(
    symbol="HIBOR_1M",
    date="2025-01-01",
    value=3.45,
    source="HKMA"
)

# Create a parameter set
params = rust_nonprice.PyParameterSet(
    indicator_name="HIBOR_ZSCORE",
    zscore_buy=-0.5,
    zscore_sell=0.5,
    rsi_buy=25.0,
    rsi_sell=65.0,
    sma_fast=10,
    sma_slow=30
)

# Create a backtest engine
engine = rust_nonprice.PyBacktestEngine(
    initial_capital=1000000.0,
    commission=0.001
)
```

## API Reference

### Classes

#### PyNonPriceIndicator
Represents raw economic data points.

**Constructor:**
```python
PyNonPriceIndicator(symbol: str, date: str, value: float, source: str)
```

**Properties:**
- `symbol`: The indicator symbol
- `date`: Date in YYYY-MM-DD format
- `value`: Data value
- `source`: Data source

#### PyTechnicalIndicator
Represents calculated technical indicators.

**Constructor:**
```python
PyTechnicalIndicator(symbol: str, date: str, indicator_type: str, window_size: int, value: float)
```

**Properties:**
- `symbol`: Associated stock symbol
- `date`: Date in YYYY-MM-DD format
- `indicator_type`: Type (ZSCORE, RSI, SMA_FAST, SMA_SLOW)
- `value`: Indicator value
- `window_size`: Calculation window

#### PyTradingSignal
Represents generated trading signals.

**Constructor:**
```python
PyTradingSignal(symbol: str, date: str, action: str, strength: float)
```

**Properties:**
- `symbol`: Stock symbol
- `date`: Date in YYYY-MM-DD format
- `action`: Action (BUY, SELL, HOLD)
- `strength`: Signal strength (0.0-1.0)
- `confidence`: Signal confidence (0.0-1.0)

#### PyParameterSet
Configuration parameters for signal generation.

**Constructor:**
```python
PyParameterSet(
    indicator_name: str,
    zscore_buy: float,
    zscore_sell: float,
    rsi_buy: float,
    rsi_sell: float,
    sma_fast: int,
    sma_slow: int
)
```

**Properties:**
- `id`: Unique parameter set ID
- `indicator_name`: Associated indicator name
- `zscore_buy`: Z-Score buy threshold
- `zscore_sell`: Z-Score sell threshold
- `rsi_buy`: RSI buy threshold
- `rsi_sell`: RSI sell threshold
- `sma_fast`: Fast SMA period
- `sma_slow`: Slow SMA period

#### PyBacktestEngine
Runs backtests on trading signals.

**Constructor:**
```python
PyBacktestEngine(initial_capital: float, commission: float)
```

**Methods:**
- `run_backtest(signals: List[PyTradingSignal], stock_data: List[str]) -> str`

#### PyParameterOptimizer
Optimizes trading parameters.

**Constructor:**
```python
PyParameterOptimizer(metric: str, max_iterations: int)
```

**Methods:**
- `optimize(data: List[PyNonPriceIndicator]) -> PyParameterSet`

**Optimization Metrics:**
- `SHARPE`: Sharpe ratio (default)
- `RETURN`: Total return
- `DRAWDOWN`: Maximum drawdown

#### PyReportGenerator
Generates reports in various formats.

**Constructor:**
```python
PyReportGenerator()
```

**Methods:**
- `generate_markdown(result: str, output_path: str) -> str`
- `generate_json(result: str, output_path: str) -> str`

## Examples

See `examples/python_demo.py` for a complete demonstration of all classes and methods.

## Development

### Building from Source

```bash
# Build bindings
maturin build --release

# Run tests
maturin test

# Develop in editable mode
maturin develop --extras
```

### Code Structure

```
python/
├── src/
│   └── lib.rs          # PyO3 bindings
├── Cargo.toml          # Python package config
└── README.md           # This file
```

## License

MIT License - see LICENSE file for details.
