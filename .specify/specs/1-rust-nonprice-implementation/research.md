# Research Findings: Rust Non-Price Data Technical Indicators System

**Date**: 2025-11-10
**Feature**: Rust implementation of non-price data to technical indicators conversion system
**Source**: `/specs/1-rust-nonprice-implementation/spec.md`

## Executive Summary

Research confirms feasibility of building high-performance Rust system for non-price data analysis with clear technical decisions made. All constitutional gates pass. Key findings: Polars is optimal for data processing, Rayon provides excellent parallelization, and PyO3 is mature for Python integration.

---

## Technical Decision: Data Processing Library

**Decision**: Use **Polars** as primary data processing library
**Rationale**:
- Excellent performance (Rust-native, zero-copy operations)
- Built-in CSV/Parquet support with automatic schema inference
- Vectorized operations for technical indicators (20-50x faster than Python)
- Memory efficient (lazy evaluation, streaming processing for large files)
- Natural integration with ndarray for mathematical operations
- Supports both batch and streaming modes

**Alternatives Considered**:
- **ndarray**: Too low-level, would require manual implementation of CSV parsing, schema validation
- **Apache Arrow**: Excellent for data interchange but lacks built-in technical indicator functions
- **csv + manual parsing**: Too slow, no type safety, would need months of development

**References**:
- Polars: https://pola.rs/ - Benchmarks show 2-5x faster than Pandas
- Performance study: https://github.com/pola-rs/polars-bench

---

## Technical Decision: Parallel Processing Framework

**Decision**: Use **Rayon** for parallel parameter optimization
**Rationale**:
- Effortless parallelism (just change `.iter()` to `.par_iter()`)
- Work-stealing scheduler optimizes CPU utilization
- Perfect for-embarrassingly parallel parameter optimization (2,160 combinations)
- Zero-cost abstraction (no runtime overhead vs manual threads)
- Integrates seamlessly with iterator chains

**Alternatives Considered**:
- **Tokio**: Overkill for CPU-bound tasks, designed for async I/O
- **std::thread**: Too low-level, manual workload distribution
- **crossbeam**: More flexible but Rayon simpler for parallel iterators

**Implementation Pattern**:
```rust
use rayon::prelude::*;

let results: Vec<_> = parameter_combinations
    .par_iter()
    .map(|params| backtest_with_params(data, params))
    .collect();
```

---

## Technical Decision: Python Binding Strategy

**Decision**: Use **PyO3** with **Maturin** for building Python bindings
**Rationale**:
- Mature, stable library (PyO3 0.20+)
- Automatic conversion between Rust and Python data types
- Zero-copy for numeric arrays (numpy ndarray integration)
- Supports both sync and async Python functions
- Excellent documentation and community support
- Can distribute as pip-installable wheel or direct .so/.pyd file

**Alternatives Considered**:
- **Cython**: Would require rewriting in Cython, lose Rust safety benefits
- **Rust DLL + ctypes**: Too low-level, manual ABI management, poor error handling
- **JSON/CSV interprocess**: Simple but slow, serialization overhead, complex orchestration

**Integration Architecture**:
```
Python Code → PyO3 Bindings → Rust Core → Polars/numpy arrays
    ↓              ↓              ↓            ↓
User Workflow ← Easy Integration ← High Performance ← Vectorized Math
```

---

## Technical Decision: Technical Indicator Calculations

**Decision**: Implement custom technical indicators using vectorized operations
**Rationale**:
- Tailored to our specific use case (non-price data)
- Maximum performance and memory efficiency
- Can optimize for float64 precision in financial calculations
- Self-contained (no external dependencies for core calculations)
- Full control over edge case handling

**Implementation Strategy**:
- **Z-Score**: Rolling mean and stddev over configurable window
- **RSI**: Wilder's smoothing method (14-period standard)
- **SMA**: Simple moving average with configurable fast/slow periods
- All using Polars expressions for vectorization

**Edge Cases Addressed**:
- Rolling windows with insufficient data (return null/NaN)
- Division by zero in RSI calculations (handle gracefully)
- NaN propagation in Z-Score (standard statistical approach)
- Missing data interpolation strategies

---

## Technical Decision: Backtest Engine Architecture

**Decision**: Event-driven backtest engine with position tracking
**Rationale**:
- Industry standard for quantitative finance
- Clear separation between signal generation and execution
- Easy to add transaction costs, slippage, position sizing
- Enables detailed trade-by-trade analysis
- Natural fit for calculating performance metrics

**Core Components**:
1. **MarketData**: OHLCV data structure with validation
2. **Signal**: BUY/SELL/HOLD with confidence and source indicator
3. **Position**: Current portfolio state (cash, shares, unrealized P&L)
4. **Trade**: Executed transaction with entry/exit prices and timestamps
5. **Portfolio**: Position tracker with equity curve calculation

**Performance Considerations**:
- Pre-allocate vectors for equity curve
- Use integer indices instead of datetime lookups
- Batch process signal application
- Inline performance metric calculations

---

## Technical Decision: Parameter Optimization Strategy

**Decision**: Exhaustive grid search with parallelization
**Rationale**:
- 2,160 combinations is computationally feasible with parallelization
- Guaranteed to find global optimum within search space
- Simple to implement and reason about
- Provides complete sensitivity analysis
- Can be extended to genetic algorithms or Bayesian optimization later

**Search Space** (per indicator):
- Z-Score buy threshold: [-2.0, -1.5, -1.0, -0.5] (4 values)
- Z-Score sell threshold: [0.5, 1.0, 1.5, 2.0] (4 values)
- RSI buy threshold: [25, 30, 35] (3 values)
- RSI sell threshold: [65, 70, 75] (3 values)
- SMA fast period: [5, 10, 15] (3 values)
- SMA slow period: [20, 25, 30, 35, 40] (5 values)
- **Total**: 4×4×3×3×3×5 = **2,160 combinations**

**Optimization Metrics**:
- Primary: Sharpe ratio (risk-adjusted return)
- Secondary: Max drawdown, total return, win rate
- Filtering: Minimum trade count (avoid overfitting to small sample)

---

## Technical Decision: Performance Optimization Techniques

**Memory Management**:
- Pre-allocate Vec<T> with `.with_capacity()`
- Use stack-allocated arrays for small fixed-size data
- Reuse buffers in loops (avoid allocations)
- Use `&[T]` slices instead of `Vec<T>` where possible

**Computation Optimization**:
- Vectorized operations (Polars expressions)
- Avoid branching in hot paths (use predicates)
- Cache rolling window calculations
- Parallelize independent calculations (Rayon)

**I/O Optimization**:
- Use Parquet for storage (5-10x smaller than CSV)
- Memory-mapped files for large datasets
- Lazy loading with Polars lazy API
- Batch processing to avoid loading entire dataset

**Target Performance** (from spec SC-001 to SC-008):
- Single indicator: <30s (1000+ data points)
- Full optimization: <15min (13,000+ combinations across 6 indicators)
- Backtest: <60s (3-year data, 1000+ trades)
- Memory: <8GB (100MB dataset)

---

## Technical Decision: Error Handling Strategy

**Decision**: Comprehensive Result<T, E> with typed errors
**Rationale**:
- No unwrap()/expect() in production code (constitution requirement)
- Fail-fast on data quality issues
- Graceful degradation where possible
- Clear error messages for debugging

**Error Types**:
```rust
#[derive(Debug)]
pub enum BacktestError {
    InsufficientData { needed: usize, have: usize },
    InvalidPrice { price: f64, date: NaiveDate },
    CalculationOverflow { operation: String, value: f64 },
    OptimizationTimeout { elapsed: Duration },
    DataLoadError { source: String, error: String },
    ValidationError { field: String, reason: String },
}
```

**Propagation Strategy**:
- Errors bubble up through Result chains
- Log all errors with context (timestamp, operation, data point)
- Return meaningful errors to Python via PyO3
- Never panic in production (always return Result)

---

## Technical Decision: Structured Logging Implementation

**Decision**: JSON-structured logging with serde_json
**Rationale**:
- Machine-readable for log analysis
- Easy to parse and search
- Integrates with monitoring systems (ELK, Datadog)
- Tracks every decision for audit trail

**Log Format Example**:
```json
{
  "timestamp": "2025-11-10T10:30:00Z",
  "level": "INFO",
  "event": "PARAMETER_OPTIMIZATION",
  "indicator": "HIBOR_Overnight_%",
  "combination": 1,
  "total_combinations": 2160,
  "progress": 0.046,
  "elapsed_ms": 1250,
  "best_sharpe": 0.72,
  "thread_id": 7
}
```

**Log Events**:
- DATA_LOADED: Data loading completion
- INDICATOR_CALCULATED: Technical indicator computed
- SIGNAL_GENERATED: Trading signal created
- OPTIMIZATION_STARTED/ENDED: Parameter search lifecycle
- TRADE_EXECUTED: Buy/sell transaction
- BACKTEST_COMPLETED: Full backtest finish
- ERROR: Any error conditions

---

## Technical Decision: Testing Strategy

**Unit Testing** (≥80% coverage, core ≥95%):
- Technical indicator calculations (test against known formulas)
- Signal generation logic (edge cases, boundary conditions)
- Data validation (invalid prices, missing values, OHLCV consistency)
- Performance metrics calculation (Sharpe, drawdown - verify formulas)
- Error handling (all error paths tested)

**Integration Testing**:
- End-to-end pipeline (data → indicators → signals → backtest)
- Python binding integration (test via pytest)
- Parallel optimization (verify no race conditions)
- Report generation (Markdown and JSON output)

**Performance Testing**:
- Benchmark each component (indicator calculation, backtest, optimization)
- Verify performance targets (SC-001 to SC-008)
- Memory profiling (ensure no leaks)
- Load testing (100MB dataset)

**Fixtures**:
- Pre-generated datasets (CSV and Parquet)
- Mock stock price data for backtesting
- Known-good parameter sets for regression testing
- Python integration test scripts

---

## Research Gaps Resolved

| Topic | Research Conducted | Decision Made |
|-------|-------------------|---------------|
| Data Processing | ✅ Polars vs ndarray vs Arrow | Polars selected |
| Parallelization | ✅ Rayon vs Tokio vs std::thread | Rayon selected |
| Python Integration | ✅ PyO3 vs Cython vs DLL | PyO3 selected |
| Indicator Algorithms | ✅ Financial math best practices | Custom vectorized |
| Backtest Architecture | ✅ Event-driven vs bar-replay | Event-driven selected |
| Optimization | ✅ Grid search vs genetic vs Bayesian | Grid search (2,160 combos) |
| Error Handling | ✅ Rust error handling patterns | Result<T, E> with typed errors |
| Logging | ✅ Structured logging for finance | JSON with serde_json |
| Testing | ✅ Rust testing best practices | Unit+Integration+Performance |

---

## Risk Analysis

**High Risk**:
- ⚠️ **PyO3 Learning Curve**: Team unfamiliar with PyO3
  - **Mitigation**: Extensive examples provided, start with simple functions
  - **Mitigation**: Use PyO3 guide and examples as reference
  - **Timeline Impact**: +1 week for binding development

- ⚠️ **Performance Targets**: Aggressive performance goals (30s for 1000+ data points)
  - **Mitigation**: Profile early, optimize hot paths
  - **Mitigation**: Use Polars vectorization extensively
  - **Timeline Impact**: May need performance optimization phase

**Medium Risk**:
- ⚠️ **Data Quality**: Real-world data may have more issues than test data
  - **Mitigation**: Robust validation and error handling
  - **Mitigation**: Support multiple interpolation strategies
  - **Contingency**: Provide data cleaning tools

**Low Risk**:
- ✅ **Rust Tooling**: Stable, well-documented, excellent compiler
- ✅ **Constitution Compliance**: All gates pass, clear guidelines
- ✅ **Algorithm Complexity**: Standard financial calculations, well-documented

---

## Next Steps (Phase 1)

1. **Data Model Design** (data-model.md):
   - Define NonPriceIndicator, TechnicalIndicator, Signal, BacktestResult structs
   - Specify validation rules and state transitions
   - Create relationship diagrams

2. **API Contracts** (contracts/):
   - Define Rust library API (functions, traits, types)
   - Define PyO3 Python interface
   - Create CLI command structure

3. **Quickstart Guide** (quickstart.md):
   - Installation instructions
   - Basic usage example
   - Python integration example

---

## References

1. **Technical Indicators**:
   - Technical Analysis of the Financial Markets - Murphy
   - Z-Score: https://en.wikipedia.org/wiki/Standard_score
   - RSI: https://en.wikipedia.org/wiki/Relative_strength_index

2. **Performance**:
   - Polars Documentation: https://pola-rs.github.io/polars-book/
   - Rayon Documentation: https://docs.rs/rayon/

3. **Rust Best Practices**:
   - Rust Book: https://doc.rust-lang.org/book/
   - Error Handling: https://doc.rust-lang.org/book/ch09-00-error-handling.html

4. **PyO3**:
   - PyO3 Guide: https://pyo3.rs/
   - Python Integration: https://pyo3.rs/main/python-from-rust

---

**Research Completed**: 2025-11-10
**Status**: ✅ All unknowns resolved, ready for Phase 1 (Design)
