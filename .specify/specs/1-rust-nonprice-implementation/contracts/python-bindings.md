# Python Bindings API Contracts

**Version**: 1.0.0
**Date**: 2025-11-10
**Target**: `python-nonprice` PyO3 module
**Module Name**: `rust_nonprice`

## Overview

This document defines the Python API for the Rust non-price data processing system via PyO3 bindings. The Python API provides a convenient interface to the high-performance Rust core while maintaining Pythonic ergonomics.

---

## Installation

```bash
# From source
cd rust-nonprice/python
maturin develop --release

# Or install wheel
pip install rust-nonprice
```

---

## Core Classes

### 1. NonPriceIndicator

Python wrapper for NonPriceIndicator struct.

```python
from rust_nonprice import NonPriceIndicator
from datetime import date

class NonPriceIndicator:
    """Represents raw economic data point (HIBOR, visitor count, etc.)"""

    def __init__(self, symbol: str, date: date, value: float, source: str = ""):
        """Initialize non-price indicator

        Args:
            symbol: Data identifier (e.g., "HIBOR_Overnight_%")
            date: Observation date
            value: Numeric value
            source: Data source (e.g., "HKMA")
        """
        self.symbol = symbol
        self.date = date
        self.value = value
        self.source = source
        self.quality = "GOOD"  # Automatically set after validation

    @classmethod
    def from_csv(cls, file_path: str) -> List['NonPriceIndicator']:
        """Load indicators from CSV file

        Args:
            file_path: Path to CSV file with columns: symbol,date,value,source

        Returns:
            List of NonPriceIndicator objects

        Raises:
            DataLoadError: If file not found or format invalid
        """
        ...

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'value': self.value,
            'source': self.source,
            'quality': self.quality
        }
```

**Example**:
```python
from rust_nonprice import NonPriceIndicator
from datetime import date

# Create indicator
hibor = NonPriceIndicator(
    symbol="HIBOR_Overnight_%",
    date=date(2023, 6, 15),
    value=4.25,
    source="HKMA"
)

# Load from CSV
indicators = NonPriceIndicator.from_csv("hibor_data.csv")
```

---

### 2. TechnicalIndicator

```python
from rust_nonprice import TechnicalIndicator, IndicatorType

class TechnicalIndicator:
    """Calculated technical indicator (Z-Score, RSI, SMA)"""

    def __init__(self):
        self.base_symbol: str
        self.date: date
        self.indicator_type: IndicatorType
        self.value: Optional[float]
        self.window_size: int
        self.is_valid: bool

    @staticmethod
    def calculate_zscore(
        data: List[NonPriceIndicator],
        window_size: int = 20
    ) -> List['TechnicalIndicator']:
        """Calculate Z-Score for all data points

        Args:
            data: Non-price indicator data
            window_size: Rolling window size (default 20)

        Returns:
            List of Z-Score indicators

        Raises:
            InsufficientData: If data length < window_size
        """
        ...

    @staticmethod
    def calculate_rsi(
        data: List[NonPriceIndicator],
        window_size: int = 14
    ) -> List['TechnicalIndicator']:
        """Calculate RSI (Relative Strength Index)

        Args:
            data: Non-price indicator data
            window_size: RSI period (default 14)

        Returns:
            List of RSI indicators
        """
        ...

    @staticmethod
    def calculate_sma(
        data: List[NonPriceIndicator],
        window_size: int
    ) -> List['TechnicalIndicator']:
        """Calculate Simple Moving Average

        Args:
            data: Non-price indicator data
            window_size: Moving average period

        Returns:
            List of SMA indicators
        """
        ...

    @staticmethod
    def calculate_all(
        data: List[NonPriceIndicator]
    ) -> List['TechnicalIndicator']:
        """Calculate all technical indicators (Z-Score, RSI, SMA)

        Args:
            data: Non-price indicator data

        Returns:
            List of all calculated indicators
        """
        ...
```

**Example**:
```python
from rust_nonprice import TechnicalIndicator

# Calculate all indicators
indicators = TechnicalIndicator.calculate_all(hibor_data)

# Filter by type
zscores = [i for i in indicators if i.indicator_type == IndicatorType.ZSCORE]
```

---

### 3. TradingSignal

```python
from rust_nonprice import TradingSignal, SignalAction

class TradingSignal:
    """Generated trading signal (BUY/SELL/HOLD)"""

    def __init__(self):
        self.symbol: str
        self.date: date
        self.action: SignalAction
        self.confidence: float
        self.source_indicators: List[str]
        self.reasoning: str

    @staticmethod
    def generate(
        indicators: List[TechnicalIndicator],
        parameters: 'ParameterSet'
    ) -> List['TradingSignal']:
        """Generate trading signals from technical indicators

        Args:
            indicators: Calculated technical indicators
            parameters: Trading parameters (thresholds)

        Returns:
            List of trading signals (BUY/SELL/HOLD)
        """
        ...
```

**Example**:
```python
from rust_nonprice import TradingSignal, ParameterSet

# Create parameters
params = ParameterSet(
    zscore_buy=-0.5,
    zscore_sell=0.5,
    rsi_buy=25.0,
    rsi_sell=65.0,
    sma_fast=10,
    sma_slow=30
)

# Generate signals
signals = TradingSignal.generate(indicators, params)

# Filter buy signals
buy_signals = [s for s in signals if s.action == SignalAction.BUY]
```

---

### 4. ParameterSet

```python
from rust_nonprice import ParameterSet

class ParameterSet:
    """Collection of trading parameters for signal generation"""

    def __init__(
        self,
        zscore_buy: float,
        zscore_sell: float,
        rsi_buy: float,
        rsi_sell: float,
        sma_fast: int,
        sma_slow: int
    ):
        """Initialize parameter set

        Args:
            zscore_buy: Z-Score buy threshold (< 0)
            zscore_sell: Z-Score sell threshold (> 0)
            rsi_buy: RSI buy threshold (< rsi_sell)
            rsi_sell: RSI sell threshold (> rsi_buy)
            sma_fast: SMA fast period (< sma_slow)
            sma_slow: SMA slow period (> sma_fast)

        Raises:
            ValueError: If parameters invalid
        """
        self.zscore_buy = zscore_buy
        self.zscore_sell = zscore_sell
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow

    @classmethod
    def default(cls) -> 'ParameterSet':
        """Get default parameter set"""
        return cls(
            zscore_buy=-0.5,
            zscore_sell=0.5,
            rsi_buy=25.0,
            rsi_sell=65.0,
            sma_fast=10,
            sma_slow=30
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'zscore_buy': self.zscore_buy,
            'zscore_sell': self.zscore_sell,
            'rsi_buy': self.rsi_buy,
            'rsi_sell': self.rsi_sell,
            'sma_fast': self.sma_fast,
            'sma_slow': self.sma_slow
        }
```

---

### 5. BacktestEngine

```python
from rust_nonprice import BacktestEngine, BacktestConfig

class BacktestResult:
    """Backtest results with performance metrics"""

    def __init__(self):
        self.symbol: str
        self.start_date: date
        self.end_date: date
        self.initial_capital: float
        self.final_value: float
        self.total_return_pct: float
        self.annual_return_pct: float
        self.sharpe_ratio: float
        self.max_drawdown_pct: float
        self.win_rate_pct: float
        self.total_trades: int
        self.execution_time_ms: int

    def summary(self) -> str:
        """Get human-readable summary"""
        return f"""
Backtest Results for {self.symbol}:
Period: {self.start_date} to {self.end_date}
Initial Capital: ${self.initial_capital:,.2f}
Final Value: ${self.final_value:,.2f}
Total Return: {self.total_return_pct:.2f}%
Annual Return: {self.annual_return_pct:.2f}%
Sharpe Ratio: {self.sharpe_ratio:.2f}
Max Drawdown: {self.max_drawdown_pct:.2f}%
Win Rate: {self.win_rate_pct:.1f}%
Total Trades: {self.total_trades}
        """.strip()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        ...

class BacktestConfig:
    """Backtest configuration"""

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.0005,
        risk_free_rate: float = 0.02
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.risk_free_rate = risk_free_rate

class BacktestEngine:
    """Main backtest engine"""

    @staticmethod
    def run(
        signals: List[TradingSignal],
        stock_data: List['OHLCV'],
        config: Optional[BacktestConfig] = None
    ) -> BacktestResult:
        """Run backtest with given signals and stock data

        Args:
            signals: Generated trading signals
            stock_data: Historical stock price data (OHLCV)
            config: Backtest configuration (uses defaults if None)

        Returns:
            BacktestResult with performance metrics
        """
        ...
```

**Example**:
```python
from rust_nonprice import BacktestEngine, BacktestConfig

# Configure backtest
config = BacktestConfig(
    initial_capital=100_000.0,
    commission_rate=0.001,
    slippage=0.0005
)

# Run backtest
result = BacktestEngine.run(signals, stock_data, config)

# Print results
print(result.summary())

# Access metrics
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
```

---

### 6. ParameterOptimizer

```python
from rust_nonprice import ParameterOptimizer, OptimizationConfig

class OptimizationResult:
    """Parameter optimization results"""

    def __init__(self):
        self.best_parameters: ParameterSet
        self.best_sharpe: float
        self.best_return: float
        self.best_drawdown: float
        self.total_combinations: int
        self.execution_time_ms: int
        self.all_results: List['ScoredParameterSet']

    def top_n(self, n: int) -> List['ScoredParameterSet']:
        """Get top N parameter sets by Sharpe ratio"""
        ...

class OptimizationConfig:
    """Optimization configuration"""

    def __init__(
        self,
        max_workers: int = 8,
        timeout_seconds: Optional[int] = None,
        min_trades: int = 10
    ):
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.min_trades = min_trades

class ParameterOptimizer:
    """Parameter optimization engine"""

    @staticmethod
    def optimize(
        indicators: List[TechnicalIndicator],
        stock_data: List['OHLCV'],
        config: Optional[OptimizationConfig] = None
    ) -> OptimizationResult:
        """Optimize parameters for single indicator (2,160 combinations)

        Args:
            indicators: Technical indicators for one non-price data source
            stock_data: Stock price data for backtesting
            config: Optimization configuration

        Returns:
            OptimizationResult with best parameters and all scores

        Raises:
            InsufficientData: If not enough data
            OptimizationTimeout: If exceeds timeout
        """
        ...

    @staticmethod
    def optimize_all(
        all_indicators: List[List[TechnicalIndicator]],
        stock_data: List['OHLCV'],
        config: Optional[OptimizationConfig] = None
    ) -> 'MultiIndicatorOptimizationResult':
        """Optimize parameters for all 6 indicators

        Args:
            all_indicators: Technical indicators for all 6 non-price data sources
            stock_data: Stock price data

        Returns:
            Results for each indicator
        """
        ...
```

**Example**:
```python
from rust_nonprice import ParameterOptimizer, OptimizationConfig

# Configure optimization
config = OptimizationConfig(
    max_workers=8,
    timeout_seconds=3600,  # 1 hour
    min_trades=10
)

# Run optimization
result = ParameterOptimizer.optimize(hibor_indicators, stock_data, config)

# Print best results
print(f"Best Sharpe Ratio: {result.best_sharpe:.2f}")
print(f"Best Parameters: {result.best_parameters.to_dict()}")
```

---

### 7. ReportGenerator

```python
from rust_nonprice import ReportGenerator

class ReportGenerator:
    """Generate reports in various formats"""

    @staticmethod
    def markdown(
        result: BacktestResult,
        output_path: str
    ) -> None:
        """Generate Markdown report

        Args:
            result: Backtest results
            output_path: Path to save report (.md file)
        """
        ...

    @staticmethod
    def json(
        result: BacktestResult,
        output_path: str
    ) -> None:
        """Generate JSON report

        Args:
            result: Backtest results
            output_path: Path to save report (.json file)
        """
        ...

    @staticmethod
    def comprehensive(
        result: BacktestResult,
        output_dir: str
    ) -> None:
        """Generate comprehensive report (Markdown + JSON + charts)

        Args:
            result: Backtest results
            output_dir: Directory to save all reports
        """
        ...
```

**Example**:
```python
from rust_nonprice import ReportGenerator

# Generate reports
ReportGenerator.markdown(result, "backtest_report.md")
ReportGenerator.json(result, "backtest_report.json")
ReportGenerator.comprehensive(result, "./reports/")
```

---

## High-Level API

```python
from rust_nonprice import (
    NonPriceIndicator,
    TechnicalIndicator,
    TradingSignal,
    ParameterOptimizer,
    BacktestEngine,
    ReportGenerator
)

# 1. Load data
indicators = NonPriceIndicator.from_csv("hibor_data.csv")
stock_data = load_stock_prices("0700HK.csv", "0700.HK")  # Custom function

# 2. Calculate technical indicators
tech_indicators = TechnicalIndicator.calculate_all(indicators)

# 3. Optimize parameters
config = OptimizationConfig(max_workers=8)
opt_result = ParameterOptimizer.optimize(tech_indicators, stock_data, config)

# 4. Generate signals with best parameters
signals = TradingSignal.generate(tech_indicators, opt_result.best_parameters)

# 5. Run backtest
backtest_result = BacktestEngine.run(signals, stock_data)

# 6. Generate report
ReportGenerator.comprehensive(backtest_result, "./results/")

# Print summary
print(backtest_result.summary())
```

---

## Error Handling

```python
from rust_nonprice import BacktestError

try:
    result = BacktestEngine.run(signals, stock_data)
except BacktestError as e:
    print(f"Backtest error: {e}")
    if isinstance(e, InsufficientData):
        print(f"Need {e.needed} data points, have {e.have}")
    elif isinstance(e, OptimizationTimeout):
        print("Optimization timed out")
```

**Error Types** (match Rust):
- `InsufficientData`
- `InvalidPrice`
- `CalculationOverflow`
- `OptimizationTimeout`
- `DataLoadError`
- `ValidationError`
- `IOError`

---

**Python Bindings API Completed**: 2025-11-10
**Status**: ✅ Complete - Ready for implementation
