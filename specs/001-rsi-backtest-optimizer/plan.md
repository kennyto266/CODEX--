# Implementation Plan: 0700.HK RSI Backtest Optimizer

**Branch**: `001-rsi-backtest-optimizer` | **Date**: 2025-10-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rsi-backtest-optimizer/spec.md`

## Summary

Build an RSI-based backtest optimizer for 0700.HK (Tencent Holdings) stock that systematically tests RSI window parameters from 1-300 days to identify the optimal configuration maximizing risk-adjusted returns (Sharpe ratio). The system will implement realistic trading costs (Hong Kong market: 0.1% commission + 0.1% stamp duty on sells), ensure zero look-ahead bias, and generate comprehensive visualizations comparing strategy performance against buy-and-hold baseline.

Primary requirement: Enable quantitative analysts to make data-driven decisions on RSI parameter selection with full transparency into cost impact and performance characteristics.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**:
- Pandas 1.3+ (data processing and time series manipulation)
- NumPy 1.20+ (numerical calculations)
- TA-Lib 0.4+ (RSI indicator calculation)
- Matplotlib 3.3+ (chart generation)

**Storage**: CSV file input (OHLCV data), file system output (results, charts, logs)
**Testing**: pytest 6.0+ with pytest-cov for coverage reporting
**Target Platform**: Cross-platform (Windows/Linux/macOS), optimized for AMD Ryzen 9 9950X3D (16-core, 32-thread, 128GB RAM)
**Project Type**: single (standalone Python application)

**Performance Goals**:
- Complete 300 RSI window backtests in under 5 minutes on target hardware
- Support datasets with 2-10 years of daily data (~500-2500 trading days)
- Memory efficient: process full dataset in <2GB RAM footprint
- Vectorized operations throughout (no explicit Python loops for calculations)

**Constraints**:
- Zero look-ahead bias (strict temporal data access)
- Deterministic results (same input always produces same output)
- Hong Kong market rules (0.1% commission, 0.1% stamp duty on sells only)
- Daily frequency only (no intraday support)

**Scale/Scope**:
- Single stock analysis (0700.HK focus, extensible to other symbols)
- 300 parameter configurations tested
- Support 500-2500 data points per backtest
- Generate 2 charts + comprehensive metrics per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on project principles from CLAUDE.md:

### I. Modular Architecture ✅
- **Requirement**: System MUST be implemented in modular Python code with clear separation of concerns (FR-014)
- **Compliance**: Design will separate: data loading, RSI calculation, backtest engine, performance metrics, visualization
- **Rationale**: Enables replacing RSI with other indicators (SC-009) without touching core backtest logic

### II. Data Integrity ✅
- **Requirement**: Input data validation required - check missing dates, null values, chronological order (FR-002)
- **Compliance**: Data loader module will validate completeness before processing
- **Rationale**: Prevents garbage-in-garbage-out scenarios, ensures RSI calculations are meaningful

### III. Zero Look-Ahead Bias (NON-NEGOTIABLE) ✅
- **Requirement**: RSI calculation and signal generation must not use future data (FR-005)
- **Compliance**: Signals generated at day T will only use data from days 1 to T-1
- **Rationale**: Industry-standard requirement for valid backtesting; violation would invalidate all results

### IV. Comprehensive Testing ✅
- **Requirement**: Test-driven development with 80% coverage minimum (pytest.ini requirement)
- **Compliance**: Unit tests for each module, integration tests for end-to-end workflows
- **Rationale**: Financial calculations must be verified correct; edge cases (no trades, insufficient data) need explicit handling

### V. Observability & Logging ✅
- **Requirement**: Comprehensive logging of all major operations (FR-012)
- **Compliance**: Python logging module with INFO/WARNING/ERROR levels, timestamped operations
- **Rationale**: Enables troubleshooting and audit trail for regulatory/research purposes

**GATE STATUS**: ✅ PASS - All principles addressed in design

## Project Structure

### Documentation (this feature)

```
specs/001-rsi-backtest-optimizer/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli_interface.md # Command-line interface specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
codex/
├── rsi_backtest_optimizer.py   # Main entry point CLI
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py           # CSV data loading
│   │   └── validator.py        # Data validation rules
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── rsi.py              # RSI calculation (TA-Lib wrapper)
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── signals.py          # Signal generation (RSI<30 buy, RSI>70 sell)
│   │   └── backtest_engine.py  # Core backtest loop with cost model
│   ├── performance/
│   │   ├── __init__.py
│   │   ├── metrics.py          # Sharpe, returns, drawdown, etc.
│   │   └── optimizer.py        # Parameter sweep coordinator
│   └── visualization/
│       ├── __init__.py
│       ├── equity_curve.py     # Cumulative returns chart
│       └── parameter_chart.py  # RSI window vs Sharpe scatter plot
├── tests/
│   ├── contract/
│   │   └── test_cli.py         # CLI interface contract tests
│   ├── integration/
│   │   ├── test_end_to_end.py  # Full backtest workflow
│   │   └── test_cost_model.py  # Trading cost integration
│   └── unit/
│       ├── test_loader.py
│       ├── test_validator.py
│       ├── test_rsi.py
│       ├── test_signals.py
│       ├── test_backtest_engine.py
│       ├── test_metrics.py
│       └── test_visualizations.py
├── data/                       # Input data directory
│   └── 0700_HK.csv             # Sample/actual price data
├── results/                    # Output directory
│   ├── optimization_results.csv
│   ├── top_10_windows.csv
│   ├── charts/
│   │   ├── equity_curve.png
│   │   └── rsi_sharpe_relationship.png
│   └── logs/
│       └── backtest_YYYYMMDD_HHMMSS.log
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Test configuration
└── README.md                   # Project documentation
```

**Structure Decision**: Single project structure selected because this is a standalone analysis tool with no separate frontend/backend or mobile components. All functionality is encapsulated in a command-line application with file-based I/O.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No violations identified - all principles satisfied by design.

