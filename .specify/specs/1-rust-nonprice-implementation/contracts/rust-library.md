# Rust Library API Contracts

**Version**: 1.0.0
**Date**: 2025-11-10
**Target**: `rust-nonprice` crate

## Overview

This document defines the public API for the Rust non-price data processing library. All APIs use Result<T, E> for error handling (no unwrap/expect in production code).

---

## Core API

### 1. Data Loading

```rust
/// Load non-price indicators from CSV file
pub fn load_nonprice_csv(
    path: &Path,
) -> Result<Vec<NonPriceIndicator>, BacktestError>

/// Load non-price indicators from Parquet file
pub fn load_nonprice_parquet(
    path: &Path,
) -> Result<Vec<NonPriceIndicator>, BacktestError>

/// Load stock price data for backtesting
pub fn load_stock_prices(
    path: &Path,
    symbol: &str,
) -> Result<Vec<OHLCV>, BacktestError>

/// Validate loaded data integrity
pub fn validate_data(
    data: &[NonPriceIndicator],
) -> Result<DataValidationReport, BacktestError>
```

**Errors**:
- `BacktestError::DataLoadError`: File not found, format error
- `BacktestError::ValidationError`: Data integrity check failed

**Example**:
```rust
use rust_nonprice::load_nonprice_csv;

let indicators = load_nonprice_csv(Path::new("hibor_data.csv"))?;
let validation = validate_data(&indicators)?;
println!("Loaded {} indicators, {} invalid", validation.valid_count, validation.invalid_count);
```

---

### 2. Technical Indicator Calculation

```rust
/// Calculate all technical indicators for a dataset
pub fn calculate_all_indicators(
    data: &[NonPriceIndicator],
) -> Result<Vec<TechnicalIndicator>, BacktestError>

/// Calculate Z-Score for given window size
pub fn calculate_zscore(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError>

/// Calculate RSI with Wilder's smoothing
pub fn calculate_rsi(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError>

/// Calculate Simple Moving Average
pub fn calculate_sma(
    data: &[NonPriceIndicator],
    window_size: usize,
) -> Result<Vec<TechnicalIndicator>, BacktestError>
```

**Errors**:
- `BacktestError::InsufficientData`: Not enough data for window
- `BacktestError::CalculationOverflow`: Numeric overflow in calculation

**Example**:
```rust
use rust_nonprice::{calculate_all_indicators, IndicatorType};

let indicators = calculate_all_indicators(&hibor_data)?;
let zscore_only: Vec<_> = indicators
    .iter()
    .filter(|i| i.indicator_type == IndicatorType::ZSCORE)
    .collect();
```

---

### 3. Signal Generation

```rust
/// Generate trading signals from technical indicators
pub fn generate_signals(
    indicators: &[TechnicalIndicator],
    parameters: &ParameterSet,
) -> Result<Vec<TradingSignal>, BacktestError>

/// Generate signals for multiple indicators (combined)
pub fn generate_combined_signals(
    indicators: &[TechnicalIndicator],
    parameter_sets: &[ParameterSet],
    combination_strategy: CombinationStrategy,
) -> Result<Vec<TradingSignal>, BacktestError>
```

**CombinationStrategy Enum**:
```rust
pub enum CombinationStrategy {
    MAJORITY_VOTE,    // Use signal from majority of indicators
    CONSENSUS,        // All indicators must agree
    WEIGHTED,         // Weighted by confidence
    BEST_PERFORMER,   // Use signal from historically best indicator
}
```

**Example**:
```rust
use rust_nonprice::{generate_signals, ParameterSet};

let params = ParameterSet {
    zscore_buy: -0.5,
    zscore_sell: 0.5,
    // ... other parameters
};

let signals = generate_signals(&indicators, &params)?;
```

---

### 4. Parameter Optimization

```rust
/// Optimize parameters for a single indicator (2,160 combinations)
pub fn optimize_parameters(
    indicators: &[TechnicalIndicator],
    stock_data: &[OHLCV],
    optimization_config: &OptimizationConfig,
) -> Result<OptimizationResult, BacktestError>

/// Optimize parameters for all 6 indicators
pub fn optimize_all_indicators(
    all_indicators: &[Vec<TechnicalIndicator>],
    stock_data: &[OHLCV],
    optimization_config: &OptimizationConfig,
) -> Result<MultiIndicatorOptimizationResult, BacktestError>
```

**OptimizationConfig**:
```rust
pub struct OptimizationConfig {
    pub max_combinations: Option<usize>,     // None = all 2,160
    pub max_workers: usize,                  // Parallel workers
    pub timeout: Option<Duration>,           // Max runtime
    pub min_trades: usize,                   // Filter small samples
    pub primary_metric: OptimizationMetric,  // Sharpe, Return, etc.
}
```

**OptimizationResult**:
```rust
pub struct OptimizationResult {
    pub best_parameters: ParameterSet,
    pub best_sharpe: f64,
    pub best_return: f64,
    pub best_drawdown: f64,
    pub all_results: Vec<ScoredParameterSet>,
    pub total_combinations: usize,
    pub execution_time_ms: u64,
}
```

**Example**:
```rust
use rust_nonprice::{optimize_parameters, OptimizationConfig, OptimizationMetric};

let config = OptimizationConfig {
    max_combinations: None,        // Test all 2,160
    max_workers: 8,
    timeout: Some(Duration::from_secs(3600)),
    min_trades: 10,
    primary_metric: OptimizationMetric::SHARPE_RATIO,
};

let result = optimize_parameters(&hibor_indicators, &stock_data, &config)?;
println!("Best Sharpe: {:.2}", result.best_sharpe);
```

---

### 5. Backtesting

```rust
/// Run single backtest with given parameters
pub fn run_backtest(
    signals: &[TradingSignal],
    stock_data: &[OHLCV],
    backtest_config: &BacktestConfig,
) -> Result<BacktestResult, BacktestError>

/// Run comprehensive backtest with multiple metrics
pub fn run_comprehensive_backtest(
    signals: &[TradingSignal],
    stock_data: &[OHLCV],
    backtest_config: &BacktestConfig,
) -> Result<ComprehensiveBacktestResult, BacktestError>
```

**BacktestConfig**:
```rust
pub struct BacktestConfig {
    pub initial_capital: f64,
    pub commission_rate: f64,      // 0.001 = 0.1%
    pub slippage: f64,            // 0.0005 = 0.05%
    pub risk_free_rate: f64,      // 0.02 = 2%
    pub position_sizing: PositionSizing, // Fixed, Kelly, etc.
    pub allow_short_selling: bool,
}
```

**Example**:
```rust
use rust_nonprice::{run_backtest, BacktestConfig};

let config = BacktestConfig {
    initial_capital: 100_000.0,
    commission_rate: 0.001,
    slippage: 0.0005,
    risk_free_rate: 0.02,
    position_sizing: PositionSizing::FIXED { size: 1.0 },
    allow_short_selling: false,
};

let result = run_backtest(&signals, &stock_data, &config)?;
println!("Sharpe Ratio: {:.2}", result.sharpe_ratio);
```

---

### 6. Report Generation

```rust
/// Generate Markdown report
pub fn generate_markdown_report(
    result: &BacktestResult,
    output_path: &Path,
) -> Result<(), BacktestError>

/// Generate JSON report
pub fn generate_json_report(
    result: &BacktestResult,
    output_path: &Path,
) -> Result<(), BacktestError>

/// Generate comprehensive report (Markdown + JSON + charts)
pub fn generate_comprehensive_report(
    result: &BacktestResult,
    output_dir: &Path,
) -> Result<ReportBundle, BacktestError>
```

**Example**:
```rust
use rust_nonprice::generate_markdown_report;

generate_markdown_report(&backtest_result, Path::new("report.md"))?;
```

---

### 7. Utility Functions

```rust
/// Get performance metrics from equity curve
pub fn calculate_metrics(
    equity_curve: &[(NaiveDate, f64)],
    initial_capital: f64,
) -> Result<PerformanceMetrics, BacktestError>

/// Convert daily returns to annualized metrics
pub fn annualize_metrics(
    daily_return: f64,
    volatility: f64,
    trading_days: usize,
) -> AnnualizedMetrics

/// Detect and handle missing data
pub fn interpolate_missing(
    data: &mut [NonPriceIndicator],
    method: InterpolationMethod,
) -> Result<(), BacktestError>
```

---

## Error Types

```rust
#[derive(Debug, thiserror::Error)]
pub enum BacktestError {
    #[error("Insufficient data: needed {needed}, have {have}")]
    InsufficientData { needed: usize, have: usize },

    #[error("Invalid price: {price} on {date}")]
    InvalidPrice { price: f64, date: NaiveDate },

    #[error("Calculation overflow in {operation}: {value}")]
    CalculationOverflow { operation: String, value: f64 },

    #[error("Optimization timeout after {elapsed:?}")]
    OptimizationTimeout { elapsed: Duration },

    #[error("Data load error from {source}: {error}")]
    DataLoadError { source: String, error: String },

    #[error("Validation error for {field}: {reason}")]
    ValidationError { field: String, reason: String },

    #[error("IO error: {message}")]
    IoError { message: String },

    #[error("JSON serialization error: {message}")]
    JsonError { message: String },
}
```

---

## Module Structure

```rust
// src/lib.rs
pub mod core {
    pub mod data;
    pub mod backtest;
    pub mod error;
}

pub mod data {
    pub mod loader;
    pub mod validator;
    pub mod processor;
}

pub mod strategy {
    pub mod traits;
    pub mod signals;
    pub mod optimizer;
    pub mod combiner;
}

pub mod backtest {
    pub mod engine;
    pub mod metrics;
    pub mod report;
}

pub mod utils {
    pub mod math;
    pub mod parallel;
    pub mod logging;
}
```

---

**Rust Library API Completed**: 2025-11-10
**Status**: ✅ Complete - Ready for implementation
