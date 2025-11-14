# Implementation Tasks: Rust Non-Price Data Technical Indicators System

**Feature**: Rust Non-Price Data Technical Indicators System
**Spec Reference**: [spec.md](spec.md)
**Plan Reference**: [plan.md](plan.md)
**Data Model**: [data-model.md](data-model.md)
**Total Tasks**: 127
**Priority**: P1 (US1, US2, US4) and P2 (US3)

## Project Overview

Build a high-performance Rust system for converting non-price economic data (HIBOR rates, visitor counts, traffic speed, GDP, CPI, unemployment) into technical indicators (Z-Score, RSI, SMA), generating trading signals, and performing backtesting with Sharpe ratio optimization. Delivered as standalone executable with PyO3 Python bindings.

## Phase 1: Setup & Project Initialization

**Goal**: Create project structure and initialize development environment

- [ ] T001 Create Rust workspace structure at rust-nonprice/ with Cargo.toml
- [ ] T002 Configure workspace dependencies: polars, rayon, pyo3, tokio, serde, thiserror
- [ ] T003 [P] Create directory structure: src/{core,data,strategy,backtest,utils}, python/, examples/, tests/, benches/, docs/
- [ ] T004 Create base lib.rs with module declarations per plan.md
- [ ] T005 Configure .cargo/config.toml for cross-platform builds
- [ ] T006 Set up CI/CD configuration: .github/workflows/ci.yml with cargo test, clippy, tarpaulin
- [ ] T007 Create basic .gitignore for Rust project (target/, Cargo.lock, python/target/)
- [ ] T008 Create development documentation: README.md, CONTRIBUTING.md
- [ ] T009 Set up pre-commit hooks: rustfmt, clippy, commitlint
- [ ] T010 Initialize test framework: tests/unit/, tests/integration/, tests/performance/

## Phase 2: Foundational Infrastructure

**Goal**: Implement core data structures, error handling, and foundational components that all user stories depend on

- [ ] T011 [P] Implement error types in src/core/error.rs: BacktestError enum with 8 variants per API contract
- [ ] T012 [P] Create core data structures in src/core/data.rs: NonPriceIndicator, TechnicalIndicator, TradingSignal, ParameterSet, BacktestResult, Trade structs
- [ ] T013 [P] Define enums in src/core/data.rs: IndicatorType, SignalAction, DataQuality, OptimizationMetric
- [ ] T014 [P] Implement OHLCV structure for stock price data in src/core/data.rs
- [ ] T015 [P] Create configuration structs: OptimizationConfig, BacktestConfig, PositionSizing in src/core/backtest.rs
- [ ] T016 [P] Implement Result<T, E> error handling pattern throughout (no unwrap/panic)
- [ ] T017 [P] Create structured JSON logging in src/utils/logging.rs with serde_json
- [ ] T018 [P] Implement mathematical utilities in src/utils/math.rs: statistical functions, annualization
- [ ] T019 [P] Create validation trait and implementations in src/core/validators.rs
- [ ] T020 Write unit tests for error handling (T011-T016): tests/unit/test_error_handling.rs
- [ ] T021 Write unit tests for core data structures (T012-T015): tests/unit/test_core_data.rs
- [ ] T022 Run cargo clippy --all-targets --all-features -- -D warnings (verify no warnings)
- [ ] T023 Run cargo test --lib (verify all unit tests pass)
- [ ] T024 Document core modules in docs/architecture/core.md

## Phase 3: User Story 1 - Non-Price Data Processing Engine (P1)

**Goal**: Convert non-price economic data into technical indicators (Z-Score, RSI, SMA)

**Independent Test Criteria**: Process 1000+ data points and verify all three technical indicators calculated with mathematical precision

- [ ] T025 [P] [US1] Implement data loader in src/data/loader.rs: load_nonprice_csv() and load_nonprice_parquet()
- [ ] T026 [P] [US1] Implement stock price loader in src/data/loader.rs: load_stock_prices() for backtesting
- [ ] T027 [P] [US1] Create data validator in src/data/validator.rs: validate_data() with integrity checks
- [ ] T028 [P] [US1] Implement data quality assessment and missing data handling in src/data/validator.rs
- [ ] T029 [P] [US1] Implement Z-Score calculation in src/data/processor.rs: calculate_zscore() with 20-day rolling window
- [ ] T030 [P] [US1] Implement RSI calculation in src/data/processor.rs: calculate_rsi() with Wilder's 14-day method
- [ ] T031 [P] [US1] Implement SMA calculation in src/data/processor.rs: calculate_sma() for fast (10-day) and slow (30-day)
- [ ] T032 [P] [US1] Create calculate_all_indicators() wrapper in src/data/processor.rs for batch processing
- [ ] T033 [P] [US1] Implement Polars integration for vectorized operations in src/data/processor.rs
- [ ] T034 [P] [US1] Handle edge cases: insufficient data windows, division by zero, NaN propagation
- [ ] T035 [P] [US1] Create data fixtures for testing: hibor_data.csv, visitor_data.csv, gdp_data.csv
- [ ] T036 [US1] Write integration tests: tests/integration/test_data_loading.rs (T025-T028)
- [ ] T037 [US1] Write unit tests: tests/unit/test_indicator_calculations.rs (T029-T033)
- [ ] T038 [US1] Write performance tests: tests/performance/test_indicator_performance.rs (SC-001: <30s for 1000+ points)
- [ ] T039 [US1] Verify mathematical accuracy: Z-Score, RSI, SMA calculations match known formulas
- [ ] T040 [US1] Create example: examples/basic_usage.rs demonstrating data processing pipeline
- [ ] T041 [US1] Run cargo test --test integration (verify T036 passes)
- [ ] T042 [US1] Run cargo bench --bench indicator_calculation (verify performance target)
- [ ] T043 [US1] Document data model and processing in docs/user-guide/data-processing.md
- [ ] T044 [US1] Test with real HK economic data: HIBOR, visitor counts, GDP (if available)

## Phase 4: User Story 2 - Trading Signal Generation (P1)

**Goal**: Generate BUY/SELL/HOLD signals from technical indicators using configurable thresholds

**Independent Test Criteria**: Apply signal generation to known indicator values and verify signals match configured thresholds

- [ ] T045 [P] [US2] Define Strategy trait in src/strategy/traits.rs for extensibility
- [ ] T046 [P] [US2] Implement signal generation logic in src/strategy/signals.rs: generate_signals()
- [ ] T047 [P] [US2] Implement signal threshold evaluation: Z-Score, RSI, SMA crossing logic
- [ ] T048 [P] [US2] Create signal confidence calculation based on indicator agreement
- [ ] T049 [P] [US2] Implement multi-indicator combination in src/strategy/combiner.rs: CombinationStrategy enum
- [ ] T050 [P] [US2] Support majority vote, consensus, and weighted combination strategies
- [ ] T051 [P] [US2] Generate human-readable signal reasoning in TradingSignal struct
- [ ] T052 [P] [US2] Create parameter validation: ensure zscore_buy < 0, zscore_sell > 0, etc.
- [ ] T053 [P] [US2] Implement signal filtering: skip weekends/holidays, invalid dates
- [ ] T054 [P] [US2] Create signal aggregation for multiple non-price indicators
- [ ] T055 [US2] Write unit tests: tests/unit/test_signal_generation.rs (T046-T051)
- [ ] T056 [US2] Write unit tests: tests/unit/test_signal_combination.rs (T049-T050)
- [ ] T057 [US2] Write integration tests: tests/integration/test_signals_with_indicators.rs
- [ ] T058 [US2] Test signal generation with edge cases: conflicting signals, boundary values
- [ ] T059 [US2] Verify signal accuracy: Z-Score -0.6 → BUY, RSI 80 → SELL, etc.
- [ ] T060 [US2] Create example: examples/signal_generation.rs
- [ ] T061 [US2] Run cargo test --test integration (verify T057 passes)
- [ ] T062 [US2] Document signal generation in docs/user-guide/signal-generation.md
- [ ] T063 [US2] Performance test: generate signals for 6 indicators × 1000 data points < 5s

## Phase 5: User Story 3 - Parameter Optimization System (P2)

**Goal**: Optimize parameters across 2,160 combinations to maximize Sharpe ratio

**Independent Test Criteria**: Run optimization on historical data, verify all 2,160 combinations explored, return best parameters

- [ ] T064 [P] [US3] Implement parameter grid generation in src/strategy/optimizer.rs: 4×4×3×3×3×5 combinations
- [ ] T065 [P] [US3] Create parallel optimization engine using Rayon in src/utils/parallel.rs
- [ ] T066 [P] [US3] Implement work-stealing scheduler for optimal CPU utilization
- [ ] T067 [P] [US3] Create OptimizationConfig with max_workers, timeout, min_trades settings
- [ ] T068 [P] [US3] Implement optimization progress tracking with structured logging
- [ ] T069 [P] [US3] Create OptimizationResult struct with best parameters and all scores
- [ ] T070 [P] [US3] Implement timeout handling: return best result so far if timeout exceeded
- [ ] T071 [P] [US3] Create result filtering: exclude combinations with < min_trades
- [ ] T072 [P] [US3] Implement early termination: stop if Sharpe ratio ceiling reached
- [ ] T073 [P] [US3] Support multi-indicator optimization: optimize_all_indicators()
- [ ] T074 [P] [US3] Implement deterministic execution: configurable seed for reproducibility
- [ ] T075 [US3] Write unit tests: tests/unit/test_parameter_grid.rs (T064)
- [ ] T076 [US3] Write integration tests: tests/integration/test_optimization.rs (T065-T073)
- [ ] T077 [US3] Write performance tests: tests/performance/test_optimization_performance.rs (SC-002: <15min for 2,160 combos)
- [ ] T078 [US3] Test parallel scaling: verify 8 workers = ~4x speedup vs 2 workers
- [ ] T079 [US3] Test timeout handling: set 10s timeout, verify graceful termination
- [ ] T080 [US3] Test with 6 different non-price indicators
- [ ] T081 [US3] Create example: examples/parameter_optimization.rs
- [ ] T082 [US3] Run cargo bench --bench optimization (verify performance target)
- [ ] T083 [US3] Document optimization in docs/user-guide/optimization.md
- [ ] T084 [US3] Verify memory usage: <8GB for 100MB dataset (SC-008 compliance)

## Phase 6: User Story 4 - Backtesting and Performance Evaluation (P1)

**Goal**: Apply signals to stock price data and calculate performance metrics (Sharpe, max drawdown, win rate)

**Independent Test Criteria**: Run backtests on historical data, verify all performance metrics match manual calculations

- [ ] T085 [P] [US4] Implement backtest engine in src/backtest/engine.rs: run_backtest()
- [ ] T086 [P] [US4] Create event-driven architecture: signal → position change → trade execution
- [ ] T087 [P] [US4] Implement position tracking: cash, shares, unrealized P&L
- [ ] T088 [P] [US4] Create trade execution logic with commission and slippage
- [ ] T089 [P] [US4] Implement equity curve calculation: portfolio value over time
- [ ] T090 [P] [US4] Calculate performance metrics in src/backtest/metrics.rs: Sharpe ratio, total return, annual return
- [ ] T091 [P] [US4] Calculate max drawdown, win rate, total trades, winning/losing trades
- [ ] T092 [P] [US4] Implement trade-by-trade tracking: entry/exit prices, hold days, P&L
- [ ] T093 [P] [US4] Support transaction costs: commission rate, slippage per spec
- [ ] T094 [P] [US4] Implement risk-free rate for Sharpe calculation (2% default)
- [ ] T095 [P] [US4] Create comprehensive backtest result with all metrics and trade history
- [ ] T096 [P] [US4] Validate backtest accuracy: verify calculations match manual math
- [ ] T097 [US4] Write unit tests: tests/unit/test_backtest_engine.rs (T085-T089)
- [ ] T098 [US4] Write unit tests: tests/unit/test_performance_metrics.rs (T090-T091)
- [ ] T099 [US4] Write integration tests: tests/integration/test_full_backtest.rs
- [ ] T100 [US4] Test with 3-year historical data: 0700.HK or similar
- [ ] T101 [US4] Verify Sharpe ratio accuracy: match manual calculation within 0.01 (SC-003)
- [ ] T102 [US4] Test portfolio tracking: $100k initial capital, verify final value
- [ ] T103 [US4] Run performance test: 3-year backtest < 60s (SC-003)
- [ ] T104 [US4] Create example: examples/backtest_simulation.rs
- [ ] T105 [US4] Run cargo test --test integration (verify T099 passes)
- [ ] T106 [US4] Run cargo bench --bench backtest (verify performance target)
- [ ] T107 [US4] Document backtesting in docs/user-guide/backtesting.md

## Phase 7: Report Generation & API Integration

**Goal**: Generate Markdown/JSON reports and expose public API functions

- [ ] T108 [P] Implement report generation in src/backtest/report.rs: generate_markdown_report()
- [ ] T109 [P] Implement JSON report generation: generate_json_report()
- [ ] T110 [P] Create comprehensive report bundle with charts (if gnuplot available)
- [ ] T111 [P] Expose public API functions in src/lib.rs per contracts/rust-library.md
- [ ] T112 [P] Create CLI tool in src/cli.rs with 6 subcommands: validate, indicators, signals, optimize, backtest, report
- [ ] T113 [P] Implement CLI argument parsing: clap for command-line interface
- [ ] T114 [P] Create Python bindings in python/lib.rs using PyO3
- [ ] T115 [P] Expose 7 Python classes: NonPriceIndicator, TechnicalIndicator, TradingSignal, ParameterSet, BacktestEngine, ParameterOptimizer, ReportGenerator
- [ ] T116 [P] Implement Python type conversions: Rust ↔ Python data types
- [ ] T117 [P] Create PyO3 module initialization: rust_nonprice Python package
- [ ] T118 [P] Build Python wheel using maturin: pip install support
- [ ] T119 [P] Test CLI tool: rust-nonprice validate, indicators, signals, optimize, backtest, report
- [ ] T120 [P] Test Python integration: import rust_nonprice, run basic workflow
- [ ] T121 Write integration tests: tests/integration/test_cli_tool.rs
- [ ] T122 Write integration tests: tests/integration/test_python_bindings.rs
- [ ] T123 Create report examples: examples/sample_report.md, examples/sample_report.json
- [ ] T124 Test complete workflow: data → indicators → signals → optimization → backtest → report
- [ ] T125 Document public API in docs/api/rust-library.md
- [ ] T126 Document CLI usage in docs/user-guide/cli.md
- [ ] T127 Document Python integration in docs/user-guide/python-integration.md

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Finalize documentation, optimization, and compliance with all success criteria

- [ ] T128 [P] Optimize performance: profile with Criterion, optimize hot paths
- [ ] T129 [P] Implement memory optimizations: pre-allocate Vecs, use with_capacity()
- [ ] T130 [P] Add comprehensive error messages: provide context for all BacktestError variants
- [ ] T131 [P] Create configuration file support: YAML/JSON for parameters
- [ ] T132 [P] Implement batch processing mode: process multiple indicators in one run
- [ ] T133 [P] Add data caching: LRU cache for frequently accessed data
- [ ] T134 Run full test suite: cargo test --all-targets --all-features
- [ ] T135 Run clippy: cargo clippy --all-targets --all-features -- -D warnings
- [ ] T136 Run coverage: cargo tarpaulin --out xml --output-dir coverage/
- [ ] T137 Verify all success criteria: SC-001 through SC-008
- [ ] T138 Create user quickstart guide: docs/quickstart.md
- [ ] T139 Create troubleshooting guide: docs/troubleshooting.md
- [ ] T140 Update main README.md with feature description and usage
- [ ] T141 Run end-to-end test: complete pipeline with real data
- [ ] T142 Performance audit: verify <30s single indicator, <15min optimization, <60s backtest
- [ ] T143 Memory audit: verify <8GB usage for 100MB dataset
- [ ] T144 Create deployment scripts: build-release.sh, install.sh
- [ ] T145 Final documentation review: all docs complete and accurate

## Implementation Strategy

### MVP Scope (User Story 1 Only)
Focus on T001-T044 first: basic data processing and technical indicator calculation. This provides immediate value and validates the core concept.

### Incremental Delivery
After US1 MVP, proceed in priority order:
1. **US1 (P1)**: Data processing and indicators (T025-T044)
2. **US2 (P1)**: Signal generation (T045-T063)
3. **US4 (P1)**: Backtesting (T085-T107)
4. **US3 (P2)**: Parameter optimization (T064-T084)
5. **Integration**: Reports, CLI, Python bindings (T108-T127)

### Parallel Execution Opportunities
Tasks marked with [P] can be executed in parallel since they operate on different files:
- Core data structures (T011-T015) can be developed simultaneously
- Data loader and validator (T025-T028) can be developed in parallel
- Each technical indicator (T029-T031) can be implemented independently
- Signal generation components (T045-T054) can be parallelized
- Optimization engine (T064-T074) can be developed alongside backtest engine
- Report generation and API exposure (T108-T117) can run in parallel

## User Story Dependencies

```
Phase 2 (Foundational) → US1 → US2 → US4 → US3
         ↓                 ↓      ↓      ↓      ↓
    All Stories      Data Proc  Signals  Backtest  Optimize
```

**Dependency Graph**:
- US1 depends on: Phase 2 (error handling, core data)
- US2 depends on: US1 (indicators), Phase 2
- US3 depends on: US1 (indicators), US4 (backtest for scoring)
- US4 depends on: US2 (signals), Phase 2

**Parallel Development**:
- US1 and US2 can be developed in parallel after Phase 2
- US3 can start after US1 is complete (use mock backtest initially)
- Full integration requires all stories complete

## Success Criteria Validation

- **SC-001**: Single indicator <30s - Test T038, T082
- **SC-002**: Optimization 2,160 combos <15min - Test T077, T082
- **SC-003**: Backtest <60s for 3-year data - Test T103, T106
- **SC-004**: Sharpe >0.5 for best indicator - Test in US3 integration
- **SC-005**: Final return >5% over 3 years - Test in US4 integration
- **SC-006**: Max drawdown <60% - Test in US4 integration
- **SC-007**: >95% uptime during optimization - Test T078
- **SC-008**: <0.1% error rate for clean data - Test T027, T037

## Testing Requirements

### Coverage Targets
- **Unit tests**: ≥80% overall, ≥95% for core algorithms
- **Integration tests**: All user story workflows
- **Performance tests**: All success criteria benchmarks
- **Property tests**: Randomized testing for edge cases

### Test Execution
```bash
# Run all tests
cargo test --all-targets --all-features

# Run with coverage
cargo tarpaulin --out xml --output-dir coverage/

# Run performance benchmarks
cargo bench

# Run specific test suites
cargo test --test integration
cargo test --test performance
```

## Resource Estimates

- **Development Time**: 4-6 weeks (full implementation)
- **US1 MVP**: 1-1.5 weeks (Phase 2 + US1)
- **Memory Usage**: <8GB for 100MB dataset
- **CPU Usage**: Multi-core optimization (Rayon)
- **Storage**: ~50MB for compiled binary

## Risk Mitigation

1. **PyO3 Learning Curve**: Start with simple functions, reference PyO3 guide
2. **Performance Targets**: Profile early, optimize hot paths, use Polars vectorization
3. **Data Quality Issues**: Robust validation, interpolation methods, clear error messages
4. **Mathematical Accuracy**: Test against known formulas, use property-based testing

---

**Status**: Ready for Phase 2 (Implementation)
**Next Step**: Execute tasks in priority order, starting with Phase 1 Setup
**Completion Criteria**: All tests passing, all success criteria met, documentation complete
