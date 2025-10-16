# Tasks: 0700.HK RSI Backtest Optimizer

**Input**: Design documents from `/specs/001-rsi-backtest-optimizer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as this is a financial calculations system requiring high correctness guarantees (80% coverage requirement from pytest.ini).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (codex/)
- Paths shown below use codex/ as repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/data/, src/indicators/, src/strategy/, src/performance/, src/visualization/, tests/contract/, tests/integration/, tests/unit/, data/, results/charts/, results/logs/)
- [X] T002 Initialize Python project with requirements.txt (pandas>=1.3, numpy>=1.20, TA-Lib>=0.4, matplotlib>=3.3, pytest>=6.0, pytest-cov)
- [X] T003 [P] Create pytest.ini configuration file with 80% coverage requirement and markers (unit, integration, contract)
- [X] T004 [P] Create .gitignore file (exclude results/, data/*.csv except sample, __pycache__/, *.pyc, venv/, .pytest_cache/)
- [X] T005 [P] Create all __init__.py files for src/ subdirectories (src/data/, src/indicators/, src/strategy/, src/performance/, src/visualization/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement data loader module in src/data/loader.py (load CSV, parse dates, return pandas DataFrame with OHLCV columns)
- [ ] T007 Implement data validator module in src/data/validator.py (schema check, chronological order, OHLC relationships, missing dates detection)
- [ ] T008 [P] Create unit test for data loader in tests/unit/test_loader.py (test CSV parsing, date conversion, column mapping)
- [ ] T009 [P] Create unit test for data validator in tests/unit/test_validator.py (test all validation rules, edge cases)
- [ ] T010 Implement RSI calculation wrapper in src/indicators/rsi.py (TA-Lib RSI wrapper, handle NaN values, return series per window)
- [ ] T011 [P] Create unit test for RSI calculation in tests/unit/test_rsi.py (verify against known RSI values, test boundary conditions)
- [ ] T012 Implement logging configuration utility in src/__init__.py (setup file+console handlers, timestamp format, INFO/WARNING/ERROR levels)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic RSI Strategy Backtest (Priority: P1) 🎯 MVP

**Goal**: Enable analyst to run 300-window RSI backtest and identify optimal parameter by Sharpe ratio

**Independent Test**: Run backtest with 2+ years of 0700.HK data, verify optimal RSI window identified, Sharpe ratios calculated for all 300 windows, execution completes <5 minutes

### Tests for User Story 1 ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for CLI interface in tests/contract/test_cli.py (test --help, --version, default run, parameter validation, exit codes)
- [ ] T014 [P] [US1] Integration test for end-to-end backtest workflow in tests/integration/test_end_to_end.py (load data → calculate RSI → run backtest → generate metrics → identify optimal)

### Implementation for User Story 1

- [ ] T015 [US1] Implement signal generation logic in src/strategy/signals.py (RSI<30 → BUY, RSI>70 → SELL, else HOLD, no look-ahead bias)
- [ ] T016 [P] [US1] Create unit test for signal generation in tests/unit/test_signals.py (test threshold logic, boundary conditions RSI=30/70, NaN handling)
- [ ] T017 [US1] Implement backtest engine core in src/strategy/backtest_engine.py (event-driven loop, position tracking, execute trades based on signals, NO costs yet)
- [ ] T018 [P] [US1] Create unit test for backtest engine in tests/unit/test_backtest_engine.py (test position state transitions, trade execution logic, equity calculation)
- [ ] T019 [US1] Implement Sharpe ratio calculation in src/performance/metrics.py (annualized with 252 days, 2% risk-free rate, handle zero volatility edge case)
- [ ] T020 [US1] Implement additional performance metrics in src/performance/metrics.py (total return, annualized return/volatility, max drawdown, win rate, num trades)
- [ ] T021 [P] [US1] Create unit test for metrics calculation in tests/unit/test_metrics.py (verify Sharpe formula, test edge cases like no trades, zero volatility)
- [ ] T022 [US1] Implement parameter sweep optimizer in src/performance/optimizer.py (pre-compute 300 RSI series, parallel backtest execution with multiprocessing, collect results)
- [ ] T023 [US1] Implement CLI entry point in rsi_backtest_optimizer.py (argparse for all CLI options, call optimizer, handle errors, log to file+console)
- [ ] T024 [US1] Implement results output in src/performance/optimizer.py (generate optimization_results.csv, top_10_windows.csv, summary_report.txt)
- [ ] T025 [US1] Add logging throughout execution flow (INFO for major steps, WARNING for missing data/insufficient data, ERROR for validation failures)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - analyst can identify optimal RSI window with complete performance metrics

---

## Phase 4: User Story 2 - Realistic Trading Cost Analysis (Priority: P2)

**Goal**: Add Hong Kong market trading costs (0.1% commission, 0.1% stamp duty on sells) to understand real-world profitability

**Independent Test**: Run same backtest with costs enabled/disabled, verify cost impact on returns (0.5-2% reduction), higher-frequency strategies penalized more

### Tests for User Story 2 ⚠️

- [ ] T026 [P] [US2] Integration test for cost model in tests/integration/test_cost_model.py (compare with/without costs, verify cost calculations, test high-frequency penalty)

### Implementation for User Story 2

- [ ] T027 [US2] Enhance backtest engine with cost model in src/strategy/backtest_engine.py (add commission parameter 0.1%, stamp duty 0.1% on sells only, apply to trade execution)
- [ ] T028 [P] [US2] Update unit test for backtest engine in tests/unit/test_backtest_engine.py (add cost calculation tests, verify commission+stamp duty applied correctly)
- [ ] T029 [US2] Add cost parameters to CLI in rsi_backtest_optimizer.py (--commission, --stamp-duty flags with defaults 0.001)
- [ ] T030 [US2] Update summary report generation to include cost comparison in src/performance/optimizer.py (show with-costs vs frictionless scenarios if applicable)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - analyst can toggle costs on/off to understand real-world impact

---

## Phase 5: User Story 3 - Visual Performance Analysis (Priority: P3)

**Goal**: Generate publication-quality charts for equity curve and parameter sensitivity analysis

**Independent Test**: Run completed backtest, verify two PNG charts generated (1200x800px, 150 DPI), charts are presentation-ready with proper labels/legends

### Tests for User Story 3 ⚠️

- [ ] T031 [P] [US3] Unit test for visualization modules in tests/unit/test_visualizations.py (test chart generation, file save, resolution/DPI verification, matplotlib figure creation)

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement equity curve chart in src/visualization/equity_curve.py (plot strategy vs buy-and-hold, seaborn style, 1200x800 @ 150 DPI, save to results/charts/)
- [ ] T033 [P] [US3] Implement parameter sensitivity chart in src/visualization/parameter_chart.py (scatter plot RSI window vs Sharpe, highlight optimal, save to results/charts/)
- [ ] T034 [US3] Integrate chart generation into optimizer workflow in src/performance/optimizer.py (call visualization modules after backtest completion, handle --no-charts flag)
- [ ] T035 [US3] Update CLI to support --no-charts flag in rsi_backtest_optimizer.py (skip visualization for faster testing)
- [ ] T036 [US3] Update summary report to include chart file paths in src/performance/optimizer.py (list generated charts in report output)

**Checkpoint**: All user stories should now be independently functional - complete system with numerical results + visual analysis

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Create comprehensive README.md documentation in codex/README.md (installation, usage, examples, troubleshooting)
- [ ] T038 [P] Create sample data file in data/0700_HK_sample.csv (2 years of realistic OHLCV data for testing)
- [ ] T039 [P] Add verbose mode support in rsi_backtest_optimizer.py (--verbose flag, detailed progress output, real-time updates)
- [ ] T040 [P] Enhance error messages throughout codebase (clear, actionable messages for common errors like missing columns, OHLC violations)
- [ ] T041 [P] Add input parameter validation to CLI in rsi_backtest_optimizer.py (start-window < end-window, thresholds valid, rates in 0-1 range)
- [ ] T042 Perform code cleanup and add docstrings (add module/class/function docstrings following Google style, remove debug prints)
- [ ] T043 Run full test suite and achieve 80% coverage (pytest --cov=src --cov-report=html, fix any failing tests, add tests for uncovered branches)
- [ ] T044 Validate quickstart.md instructions (follow quickstart guide step-by-step, verify all commands work, timing matches expectations)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - THIS IS THE MVP
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends backtest engine from US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses results from optimizer but independently testable

### Within Each User Story

- Tests (T013-T014, T026, T031) MUST be written and FAIL before implementation
- Core modules before integration (signals → backtest_engine → metrics → optimizer)
- Unit tests alongside implementation (write test, see it fail, implement, see it pass)
- CLI integration after core modules working
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T005)
- All Foundational tests can run in parallel (T008-T009, T011)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within US1: T013-T014 tests, T016 test, T018 test, T021 test can be written in parallel
- Within US3: T032-T033 chart implementations can run in parallel (different files)
- All Polish tasks (T037-T041) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for CLI interface in tests/contract/test_cli.py"
Task: "Integration test for end-to-end workflow in tests/integration/test_end_to_end.py"

# Launch unit tests in parallel once corresponding modules exist:
Task: "Unit test for signal generation in tests/unit/test_signals.py"
Task: "Unit test for backtest engine in tests/unit/test_backtest_engine.py"
Task: "Unit test for metrics calculation in tests/unit/test_metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Run: `python rsi_backtest_optimizer.py --data data/0700_HK_sample.csv`
   - Verify: Optimal RSI window identified, top 10 list generated, summary report created
   - Timing: Should complete in <5 minutes
5. Deploy/demo if ready (MVP complete - analyst can now optimize RSI parameters)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Core functionality works)
3. Add User Story 2 → Test independently → Deploy/Demo (Now with realistic costs)
4. Add User Story 3 → Test independently → Deploy/Demo (Now with visualizations)
5. Add Polish → Final release (Production-ready with docs and error handling)

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T012)
2. Once Foundational is done:
   - Developer A: User Story 1 (T013-T025)
   - Developer B: User Story 2 (T026-T030) - can start after A completes backtest engine
   - Developer C: User Story 3 (T031-T036) - can start after A completes optimizer
3. All converge on Polish phase (T037-T044)

Note: US2 and US3 have dependencies on US1 modules but can work in parallel if coordination is maintained.

---

## Task Count Summary

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (US1 - MVP)**: 13 tasks
- **Phase 4 (US2)**: 5 tasks
- **Phase 5 (US3)**: 6 tasks
- **Phase 6 (Polish)**: 8 tasks
- **TOTAL**: 44 tasks

### Parallel Opportunities

- Setup: 3 tasks can run in parallel (T003-T005)
- Foundational: 3 tasks can run in parallel (T008-T009, T011)
- US1: Up to 4 test tasks in parallel (T013-T014, T016, T018, T021)
- US3: 2 tasks can run in parallel (T032-T033)
- Polish: 5 tasks can run in parallel (T037-T041)

**Estimated parallel speedup**: With 2-3 developers, ~30-35% time reduction vs sequential execution.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD cycle: Red → Green → Refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

## Critical Success Factors

1. **Zero look-ahead bias** (FR-005): Every signal generation task MUST enforce temporal data access
2. **80% test coverage** (Constitution Check IV): Achieve this through US1-US3 test tasks
3. **<5 min execution** (SC-001): Verify after T022 (optimizer implementation)
4. **Modular design** (FR-014): Each module (data/, indicators/, strategy/, etc.) must be independently testable
5. **Comprehensive logging** (FR-012): Add logging calls throughout T023, T025

If these factors are not met at their respective checkpoints, STOP and resolve before proceeding.
