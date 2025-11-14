# Rust Engine Python Wrapper

A high-performance Python wrapper for the Rust backtest engine, providing seamless integration between Python and Rust with automatic fallback to pure Python when needed.

## Overview

The Rust Engine Python Wrapper provides:

- **High Performance**: Leverages Rust's speed for computation-intensive backtesting
- **Seamless Fallback**: Automatically falls back to pure Python if Rust module is unavailable
- **Type Safety**: Full type hints and comprehensive validation
- **Async Support**: Asynchronous operations for concurrent backtests
- **Caching**: Intelligent caching for repeated computations
- **Easy Integration**: Clean, Pythonic API that feels natural

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Application                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              RustEngine (Python Wrapper)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ┌──────────────┐        ┌────────────────────────┐  │  │
│  │  │ Rust Module  │        │ Python Fallback        │  │  │
│  │  │ (PyO3)       │        │ (Pure Python)          │  │  │
│  │  └──────────────┘        └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Rust Backtest Engine (Native)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Market Data │ Backtest Logic │ Metrics Calculation  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **Rust Toolchain**
   ```bash
   # Install Rust (https://rustup.rs/)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   ```

2. **Python Dependencies**
   ```bash
   pip install pandas numpy
   ```

### Build the Rust Module

```bash
# Navigate to rust-core directory
cd rust-core

# Build with Python bindings (release mode for performance)
cargo build --release --features python

# Or build in debug mode for development
cargo build --features python
```

The compiled module will be in `rust-core/target/release/libquant_core.so` (or `.dll` on Windows, `.dylib` on macOS).

### Install the Python Package

```bash
# Create symlink or copy the built module to your Python path
# Or install via pip if you have a setup.py
```

## Quick Start

### Basic Usage

```python
from src.backtest.rust_engine import (
    RustEngine,
    generate_sample_data,
)

# Create engine (auto-detects Rust availability)
engine = RustEngine(use_rust=True)

# Generate sample data
data = generate_sample_data("0700.HK", days=100, start_price=100.0)

# Run backtest
result = engine.run_sma_backtest(
    data=data,
    fast_period=10,
    slow_period=30,
    initial_capital=100000.0
)

# Display results
print(f"Total Return: {result.total_return:.2%}")
print(f"Win Rate: {result.win_rate:.2f}%")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

### Using Real Data

```python
import pandas as pd
from src.backtest.rust_engine import RustEngine

# Load data from CSV, API, etc.
df = pd.read_csv("market_data.csv")

# Ensure required columns exist
required_columns = ["date", "open", "high", "low", "close", "volume"]
assert all(col in df.columns for col in required_columns)

# Create engine and run backtest
engine = RustEngine(use_rust=True)
result = engine.run_sma_backtest(df, fast_period=20, slow_period=50)

print(f"Result: {result.to_dict()}")
```

## API Reference

### Core Classes

#### `MarketData`

Container for market data with validation.

```python
@dataclass
class MarketData:
    symbol: str
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]
```

**Methods:**
- `from_pandas(df: pd.DataFrame) -> MarketData`: Create from DataFrame
- `to_pandas() -> pd.DataFrame`: Convert to DataFrame

**Validation:**
- All arrays must have the same length
- Low ≤ Open, Close ≤ High
- Low ≤ High (always true)

#### `BacktestResult`

Results from backtest execution.

```python
@dataclass
class BacktestResult:
    total_return: float
    annualized_return: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    execution_time_ms: int
    trades: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[float]] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    volatility: Optional[float] = None
```

#### `RustEngine`

Main engine class.

**Constructor:**
```python
engine = RustEngine(use_rust=True)
```

**Methods:**
- `run_sma_backtest(data, fast_period, slow_period, initial_capital, commission_rate) -> BacktestResult`
- `run_sma_backtest_async(...) -> BacktestResult` (async version)
- `run_multiple_backtests(...) -> List[BacktestResult]`
- `validate_data(data) -> bool`
- `is_rust_available() -> bool`
- `get_engine_info() -> Dict[str, Any]`

### Factory Functions

#### `create_engine`

```python
from src.backtest.rust_engine import create_engine

# Create standard engine
engine = create_engine(use_rust=True)

# Create cached engine
cached_engine = create_engine(use_rust=True, use_cache=True)
```

#### `rust_engine_context`

Context manager for automatic cleanup.

```python
from src.backtest.rust_engine import rust_engine_context

with rust_engine_context(use_rust=True) as engine:
    result = engine.run_sma_backtest(data, 10, 30)
```

### Utility Functions

#### `generate_sample_data`

Generate synthetic data for testing.

```python
from src.backtest.rust_engine import generate_sample_data

data = generate_sample_data(
    symbol="TEST.HK",
    days=100,
    start_price=100.0
)
```

#### `benchmark_engine`

Compare performance between Rust and Python.

```python
from src.backtest.rust_engine import benchmark_engine

results = benchmark_engine(data, fast_period=10, slow_period=30)
print(f"Speedup: {results['speedup']:.2f}x")
```

## Advanced Usage

### Parallel Backtests

```python
from src.backtest.rust_engine import RustEngine, generate_sample_data

engine = RustEngine(use_rust=True)
data = generate_sample_data("TEST.HK", days=500)

# Define parameter grid
fast_periods = [5, 10, 15, 20, 25]
slow_periods = [30, 40, 50, 60, 70]

# Run parallel backtests
results = engine.run_multiple_backtests(
    data=data,
    fast_periods=fast_periods,
    slow_periods=slow_periods,
    max_workers=4
)

# Find best parameters
best = max(results, key=lambda x: x[2].total_return)
print(f"Best: Fast={best[0]}, Slow={best[1]}, Return={best[2].total_return:.2%}")
```

### Async Operations

```python
import asyncio
from src.backtest.rust_engine import RustEngine, generate_sample_data

async def run_multiple_async():
    engine = RustEngine(use_rust=True)
    data = generate_sample_data("TEST.HK", days=200)

    # Run multiple backtests concurrently
    tasks = [
        engine.run_sma_backtest_async(data, 5, 20),
        engine.run_sma_backtest_async(data, 10, 30),
        engine.run_sma_backtest_async(data, 15, 45),
    ]

    results = await asyncio.gather(*tasks)
    return results

# Run async backtests
results = asyncio.run(run_multiple_async())
```

### Caching

```python
from src.backtest.rust_engine import CachedRustEngine

# Create cached engine
engine = CachedRustEngine(use_rust=True, cache_size=128)

# Run backtest (results cached automatically)
result1 = engine.run_sma_backtest(data, 10, 30)

# Get cache statistics
stats = engine.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

### Data Validation

```python
from src.backtest.rust_engine import RustEngine

engine = RustEngine(use_rust=True)

# Validate MarketData
is_valid = engine.validate_data(market_data)

# Validate pandas DataFrame
is_valid = engine.validate_data(dataframe)

if not is_valid:
    print("Data validation failed!")
```

## Performance Tips

### 1. Use Rust When Available

```python
# The engine automatically uses Rust if available
engine = RustEngine(use_rust=True)

# You can check if Rust is being used
if engine.is_rust_available():
    print("Using high-performance Rust engine")
else:
    print("Using pure Python fallback")
```

### 2. Leverage Parallel Processing

```python
# For parameter optimization, use parallel backtests
results = engine.run_multiple_backtests(
    data=data,
    fast_periods=fast_periods,
    slow_periods=slow_periods,
    max_workers=8  # Use CPU count
)
```

### 3. Use Async for I/O-Bound Operations

```python
# When combining with I/O (database, API calls)
results = await engine.run_sma_backtest_async(data, 10, 30)
```

### 4. Cache Frequently Used Results

```python
# For repeated computations with same parameters
engine = CachedRustEngine(use_rust=True, cache_size=256)
```

### 5. Batch Operations

```python
# Group multiple backtests together
all_results = []
for symbol in symbols:
    data = load_data(symbol)
    result = engine.run_sma_backtest(data, 10, 30)
    all_results.append(result)
```

## Error Handling

The wrapper provides comprehensive error handling:

```python
from src.backtest.rust_engine import RustEngine, MarketData

engine = RustEngine(use_rust=True)

try:
    # Invalid parameters
    result = engine.run_sma_backtest(data, fast_period=30, slow_period=10)
except ValueError as e:
    print(f"Invalid parameters: {e}")

# Invalid data
try:
    invalid_data = MarketData(
        symbol="TEST",
        dates=["2020-01-01"],
        open=[100.0],
        high=[99.0],  # Invalid: high < low
        low=[100.0],
        close=[99.5],
        volume=[1000],
    )
except ValueError as e:
    print(f"Invalid data: {e}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_rust_engine.py -v

# Run with coverage
python -m pytest tests/test_rust_engine.py --cov=src.backtest.rust_engine --cov-report=html

# Run specific test categories
python -m pytest tests/test_rust_engine.py::TestMarketData -v
python -m pytest tests/test_rust_engine.py::TestRustEngine -v
python -m pytest tests/test_rust_engine.py::TestAsyncOperations -v
```

## Examples

See `examples/rust_engine_example.py` for comprehensive examples:

```bash
# Run all examples
python examples/rust_engine_example.py

# Or run individual examples
python -c "from examples.rust_engine_example import example_1_basic_usage; example_1_basic_usage()"
```

## Benchmarks

Expected performance improvements (Rust vs Python):

- **SMA Backtest (1000 days)**: 10-50x faster
- **Parameter Optimization (100 combinations)**: 20-100x faster
- **Parallel Backtests**: Scales linearly with CPU cores

Actual speedup depends on:
- Data size
- Parameter combinations
- System specifications
- Compilation optimization level

## Troubleshooting

### Rust Module Not Found

```python
# Check if Rust is available
engine = RustEngine(use_rust=True)
if not engine.is_rust_available():
    print("Rust module not available, using Python fallback")
```

### Build Errors

```bash
# Clean build
cd rust-core
cargo clean
cargo build --release --features python

# Check Rust version
rustc --version  # Should be 1.70+

# Check Python version
python --version  # Should be 3.8+
```

### Import Errors

```python
# Make sure the module is in Python path
import sys
sys.path.append('/path/to/rust-core/target/release')

# Try importing directly
try:
    from quant_backtest import run_sma_backtest
    print("Rust module imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
```

## Architecture Decisions

### Why PyO3?

- **Zero-Cost Abstraction**: No overhead compared to pure Rust
- **Native Performance**: Direct function calls between Python and Rust
- **Type Safety**: Strong typing in Rust with Python bindings
- **Parallel Processing**: Rayon for CPU-bound operations
- **Memory Safety**: Rust's memory guarantees

### Why Fallback to Python?

- **Development Flexibility**: No Rust required for development
- **Testing**: Easy to test logic in Python
- **Debugging**: Python is easier to debug
- **Gradual Migration**: Can migrate components incrementally

### Why Caching?

- **Repeated Computations**: Avoid re-running expensive backtests
- **Parameter Tuning**: Cache intermediate results during optimization
- **User Experience**: Faster response times
- **Resource Efficiency**: Reduce CPU usage

## Contributing

### Adding New Strategies

1. Implement strategy logic in Rust (`rust-core/src/backtest/`)
2. Add Python bindings in `rust-core/src/python_bindings.rs`
3. Add Python wrapper method in `src/backtest/rust_engine.py`
4. Add tests in `tests/test_rust_engine.py`
5. Update documentation

### Code Style

- **Rust**: Follow `rustfmt` standards
- **Python**: Follow PEP 8, use `black` formatter
- **Type Hints**: All Python code must have type hints
- **Documentation**: Docstrings for all public methods
- **Tests**: Minimum 90% test coverage

## License

MIT License - see LICENSE file for details.

## Changelog

### Version 0.1.0

- Initial release
- SMA backtest implementation
- Rust/Python dual-mode operation
- Async support
- Caching
- Comprehensive test suite
- Full documentation

## Support

For issues, questions, or contributions:

1. Check existing documentation
2. Review test examples
3. Create an issue with:
   - OS and Python version
   - Rust version
   - Error messages
   - Minimal reproduction case

## Roadmap

- [ ] Add more technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Support for multiple assets
- [ ] Portfolio-level backtesting
- [ ] Real-time data integration
- [ ] Web-based visualization
- [ ] Machine learning integration
- [ ] GPU acceleration (via Rust + CUDA/OpenCL)
