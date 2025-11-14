# Implementation Plan: Rust Non-Price Data Technical Indicators System

**Branch**: `[1-rust-nonprice-implementation]` | **Date**: 2025-11-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/1-rust-nonprice-implementation/spec.md`

## Summary

Build a high-performance Rust system for converting non-price economic data (HIBOR rates, visitor counts, traffic speed, GDP, CPI, unemployment) into technical indicators (Z-Score, RSI, SMA), generating trading signals, and performing backtesting with Sharpe ratio optimization. The system will be delivered as a standalone executable with PyO3 Python bindings for integration with existing workflows. Data processing is batch-only mode for historical analysis.

## Technical Context

**Language/Version**: Rust 1.75+ (with edition 2021)
**Primary Dependencies**: Polars (data processing), Rayon (parallel processing), PyO3 (Python bindings), tokio (async runtime), serde (serialization), serde_json (logging)
**Storage**: CSV/Parquet file-based (no database)
**Testing**: cargo test, cargo clippy, cargo tarpaulin (coverage), cargo bench (performance)
**Target Platform**: Linux/Windows/macOS (cross-platform executable)
**Project Type**: Single Rust library + CLI tool
**Performance Goals**: Single indicator processing < 30s, Full optimization (13,000+ combos) < 30min on 8-core, Backtesting < 60s for 3-year data
**Constraints**: Memory ≤ 8GB, Batch processing only (no real-time streaming), No unwrap()/panic in production code
**Scale/Scope**: Support 6 non-price indicators, 2,160 parameter combinations per indicator, 100MB dataset support

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Required Gates**:
- ✅ **Gate 1: Test Coverage** - Must achieve ≥80% test coverage (core algorithms ≥95%)
- ✅ **Gate 2: Performance** - Must use Rayon for parallel optimization, target <50ms per backtest
- ✅ **Gate 3: Security** - No unwrap()/expect() in production code, use Result<T, E> for error handling
- ✅ **Gate 4: Architecture** - Must follow layered architecture (data/strategy/backtest separated)
- ✅ **Gate 5: Monitoring** - Must implement structured JSON logging with traceable decisions
- ✅ **Gate 6: Data Accuracy** - Must validate data integrity, handle missing values gracefully
- ✅ **Gate 7: Extensibility** - Must use Strategy trait pattern for adding new indicators
- ✅ **Gate 8: Metrics** - Must calculate all required metrics (Sharpe, Max Drawdown, etc.)
- ✅ **Gate 9: Resource Management** - Must use Vec pre-allocation, batch processing for large datasets
- ✅ **Gate 10: Reproducibility** - Must support deterministic execution with configurable seed

## Project Structure

### Documentation (this feature)

```text
specs/1-rust-nonprice-implementation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
rust-nonprice/
├── Cargo.toml           # Workspace root
├── src/
│   ├── lib.rs          # Library entry point
│   ├── core/           # Core data structures and traits
│   │   ├── data.rs     # NonPriceIndicator, TechnicalIndicator, Signal types
│   │   ├── backtest.rs # Backtest trait and engine trait
│   │   └── error.rs    # Error types (BacktestError enum)
│   ├── data/           # Data layer
│   │   ├── loader.rs   # CSV/Parquet data loader
│   │   ├── validator.rs # Data validation (OHLCV logic, missing values)
│   │   └── processor.rs # Technical indicator calculations (Z-Score, RSI, SMA)
│   ├── strategy/       # Strategy layer
│   │   ├── traits.rs   # Strategy trait for extensibility
│   │   ├── signals.rs  # Signal generation logic
│   │   ├── optimizer.rs # Parameter optimization (2,160 combinations)
│   │   └── combiner.rs  # Multi-indicator signal combination
│   ├── backtest/       # Execution layer
│   │   ├── engine.rs   # Backtest engine implementation
│   │   ├── metrics.rs  # Performance metrics (Sharpe, Drawdown, etc.)
│   │   └── report.rs   # Markdown/JSON report generation
│   ├── utils/          # Utilities
│   │   ├── math.rs     # Statistical calculations
│   │   ├── parallel.rs # Rayon-based parallel processing
│   │   └── logging.rs  # Structured JSON logging
│   └── cli.rs          # CLI tool entry point
├── python/             # PyO3 Python bindings
│   ├── Cargo.toml      # Python binding crate
│   └── lib.rs          # PyO3 module definitions
├── examples/           # Example usage
│   ├── basic_usage.rs
│   ├── optimization.rs
│   └── python_demo.py
├── tests/              # Test suite
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── fixtures/
├── benches/            # Benchmark tests
│   ├── indicator_calculation.rs
│   ├── optimization.rs
│   └── backtest.rs
└── docs/               # Documentation
    ├── api/
    ├── user-guide/
    └── architecture/

**Structure Decision**: Rust workspace with single library crate, Python bindings crate, and CLI binary. Follows constitution-mandated layered architecture (data/strategy/backtest separation). PyO3 bindings provided for Python integration as specified in clarifications.
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None - all constitution gates pass | N/A | N/A |
