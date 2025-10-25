# Implementation Tasks: Core Architecture Refactoring

## Phase 1: Infrastructure Setup (Weeks 1-2)

### 1.1 Directory Structure and Base Classes

**Task 1.1.1**: Create new directory structure
- [ ] Create `src/data_pipeline/sources/` directory with `__init__.py`
- [ ] Create `src/data_pipeline/cleaners/` directory with `__init__.py`
- [ ] Create `src/data_pipeline/processors/` directory with `__init__.py`
- [ ] Create `src/core/` directory with `__init__.py`
- [ ] Create `src/analysis/` directory (already exists, validate content)
- [ ] Create `src/visualization/` directory with `__init__.py`
- [ ] Create `src/database/` directory with `__init__.py`

**Verification**: All directories exist with proper `__init__.py` files
**Time**: 1-2 hours

---

**Task 1.1.2**: Define base interfaces for data sources
- [ ] Create `src/data_pipeline/sources/base_source.py`
- [ ] Define `IDataSource` interface with methods:
  - `fetch_raw(symbol, start_date, end_date)` → Dict
  - `validate(data)` → ValidationResult
  - `get_metadata()` → Dict
- [ ] Add docstrings explaining expected behavior
- [ ] Create `IDataCleaner` interface with:
  - `clean(data)` → pd.DataFrame
  - `get_quality_score()` → float
- [ ] Create `IProcessor` interface with:
  - `process(data)` → ProcessedData

**Verification**: Interfaces are abstract, cannot be instantiated, type hints complete
**Time**: 2-3 hours
**Tests**: Test that interfaces cannot be instantiated directly

---

**Task 1.1.3**: Define base interfaces for calculations
- [ ] Create `src/core/base_strategy.py` with `IStrategy` interface
- [ ] Create `src/analysis/base_analyzer.py` with `IAnalyzer` interface
- [ ] Create `src/visualization/base_chart.py` with `IChartBuilder` interface
- [ ] All interfaces include:
  - Clear method signatures
  - Comprehensive docstrings
  - Type hints
  - Example usage

**Verification**: All interfaces documented with examples, type hints complete
**Time**: 2-3 hours
**Tests**: Unit tests for interface structure

---

### 1.2 Testing Infrastructure

**Task 1.2.1**: Update pytest configuration
- [ ] Review current `pytest.ini`
- [ ] Add markers for new test categories:
  - `@pytest.mark.data_layer`
  - `@pytest.mark.calculation_layer`
  - `@pytest.mark.visualization_layer`
- [ ] Update coverage thresholds if needed
- [ ] Ensure 80%+ coverage requirement maintained

**Verification**: `pytest --co` shows new markers, tests can be run with `-m` filter
**Time**: 1 hour

---

**Task 1.2.2**: Create test fixtures and mocks
- [ ] Create `tests/fixtures/mock_data.py` with:
  - Mock OHLCV data generators
  - Mock asset profiles
  - Mock strategy results
- [ ] Create `tests/fixtures/mock_adapters.py` with:
  - Mock data source implementations
  - Mock calculator implementations
  - Mock analyzer implementations
- [ ] Ensure fixtures can be used across all layers

**Verification**: All fixtures import without errors, provide expected data structure
**Time**: 2-3 hours
**Tests**: Validate fixture output format and consistency

---

## Phase 2: Data Management Layer (Weeks 2-3)

### 2.1 Data Source Interface Implementation

**Task 2.1.1**: Create unified data source factory
- [ ] Create `src/data_pipeline/sources/factory.py`
- [ ] Implement `DataSourceFactory` class with:
  - `register(source_type, source_class)`
  - `create(source_type, config) → IDataSource`
  - `list_available_sources() → List[str]`
- [ ] Register all existing adapters in the factory
- [ ] Update configuration to use factory

**Verification**: All data sources registered, factory creates correct types
**Time**: 2-3 hours
**Tests**: Unit tests for factory registration and creation

---

**Task 2.1.2**: Refactor HTTP API adapter to new interface
- [ ] Create `src/data_pipeline/sources/http_api_source.py`
- [ ] Implement `IDataSource` interface
- [ ] Migrate code from `src/data_adapters/http_api_adapter.py`
- [ ] Ensure backward compatibility (no breaking changes to callers)
- [ ] Add comprehensive docstrings
- [ ] Validate with existing tests

**Verification**: Old tests still pass, new interface tests pass
**Time**: 3-4 hours
**Tests**: Update existing HTTP adapter tests to use new interface

---

**Task 2.1.3**: Refactor file source adapter
- [ ] Create `src/data_pipeline/sources/file_source.py`
- [ ] Implement `IDataSource` interface for file-based data
- [ ] Migrate code from `src/data_adapters/raw_data_adapter.py`
- [ ] Support multiple file formats (CSV, JSON, Excel)
- [ ] Add validation and error handling

**Verification**: Can read files, validates structure, returns standardized format
**Time**: 2-3 hours
**Tests**: Tests for different file formats and error cases

---

**Task 2.1.4**: Refactor market data source adapter
- [ ] Create `src/data_pipeline/sources/market_data_source.py`
- [ ] Consolidate Yahoo Finance, Alpha Vantage adapters
- [ ] Implement `IDataSource` interface
- [ ] Support multiple market data providers with fallback
- [ ] Handle real-time vs. historical data

**Verification**: Can fetch from multiple providers, handles fallback
**Time**: 3-4 hours
**Tests**: Tests for multiple providers and fallback scenarios

---

### 2.2 Data Cleaning and Validation

**Task 2.2.1**: Consolidate data cleaning logic
- [ ] Create `src/data_pipeline/cleaners/data_cleaner.py`
- [ ] Implement `IDataCleaner` interface
- [ ] Consolidate logic from:
  - `src/data_adapters/` cleaning code
  - `src/data_pipeline/data_cleaner.py`
  - `src/data_pipeline/cleaners.py`
- [ ] Implement methods for:
  - Missing data handling
  - Duplicate removal
  - Type conversion
  - Format standardization

**Verification**: All legacy cleaning code removed or migrated
**Time**: 3-4 hours
**Tests**: Tests for all cleaning scenarios with real data

---

**Task 2.2.2**: Implement outlier detection
- [ ] Create `src/data_pipeline/cleaners/outlier_detector.py`
- [ ] Implement `IOutlierDetector` interface with:
  - Z-score based detection
  - IQR based detection
  - Isolation forest detection
  - Context-aware detection (compare to peers)
- [ ] Return outlier scores and recommendations

**Verification**: Detects known anomalies in test data
**Time**: 3-4 hours
**Tests**: Tests with synthetic anomalies, real market data anomalies

---

**Task 2.2.3**: Create data quality scoring system
- [ ] Create `src/data_pipeline/cleaners/quality_scorer.py`
- [ ] Implement scoring across:
  - Completeness (% non-null values)
  - Accuracy (validation checks passed)
  - Freshness (how recent is the data)
  - Consistency (values within expected ranges)
- [ ] Return quality score (0-100) for each dataset
- [ ] Attach score to all fetched data

**Verification**: Quality scores assigned to all datasets, scores reasonable
**Time**: 2-3 hours
**Tests**: Tests for different data quality scenarios

---

### 2.3 Temporal Alignment

**Task 2.3.1**: Create temporal aligner
- [ ] Create `src/data_pipeline/processors/temporal_aligner.py`
- [ ] Implement `IProcessor` interface with:
  - Timezone conversion and standardization
  - Market hours alignment (handle pre/post-market)
  - Holiday calendar integration
  - Data point mapping to correct trading day
- [ ] Support HKEX trading calendar specifically
- [ ] Handle data gaps during holidays

**Verification**: Correctly aligns data across timezones and holidays
**Time**: 4-5 hours
**Tests**: Tests for HKEX calendar, timezone conversion, edge cases

---

**Task 2.3.2**: Implement trading calendar management
- [ ] Create `src/data_pipeline/processors/calendar_manager.py`
- [ ] Define HKEX trading calendar:
  - Regular trading days
  - Holiday dates
  - Trading hours
  - Special trading hours (short days)
- [ ] Support multiple calendars (Hong Kong, mainland China, US)
- [ ] Update calendar data periodically

**Verification**: Calendar accurate for HKEX, supports other markets
**Time**: 2-3 hours
**Tests**: Tests for historical dates, upcoming holidays, edge cases

---

### 2.4 Asset Profile Management

**Task 2.4.1**: Create asset profile system
- [ ] Create `src/data_pipeline/processors/asset_profiler.py`
- [ ] Define `AssetProfile` data class with:
  - Basic info (symbol, name, listing date)
  - Classification (sector, industry, sub-industry)
  - Trading info (trading hours, currency, exchange)
  - Special flags (Southbound Connect, suspended, etc.)
- [ ] Load HKEX stock profiles from data source
- [ ] Support querying profiles by criteria

**Verification**: Profiles exist for major HKEX stocks, queries work
**Time**: 3-4 hours
**Tests**: Tests for profile access and filtering

---

**Task 2.4.2**: Create asset filtering system
- [ ] Create `src/data_pipeline/processors/asset_filter.py`
- [ ] Implement filtering by:
  - Sector, industry, sub-industry
  - Trading volume criteria
  - Listing date range
  - Market cap range
  - Special flags (Southbound eligible, etc.)
- [ ] Support complex queries (AND, OR combinations)

**Verification**: Can filter stocks by various criteria, returns correct results
**Time**: 2-3 hours
**Tests**: Tests for various filter combinations

---

### 2.5 Database Integration

**Task 2.5.1**: Create ORM models
- [ ] Create `src/database/models.py` with SQLAlchemy models for:
  - `MarketData` (OHLCV data)
  - `Indicators` (technical indicators)
  - `Features` (feature engineering results)
  - `StrategyResults` (backtest results)
  - `AssetProfile` (asset metadata)
  - `ParameterSet` (optimization results)
- [ ] Define relationships and indexes
- [ ] Add data validation at model level

**Verification**: Models can be created and queried, relationships work
**Time**: 4-5 hours
**Tests**: Tests for ORM operations, relationships, queries

---

**Task 2.5.2**: Create database operations abstraction
- [ ] Create `src/database/operations.py` with:
  - `insert_market_data()`
  - `get_market_data()`
  - `update_data()`
  - `delete_old_data()`
  - Batch operations
  - Transaction management
- [ ] Implement connection pooling and optimization
- [ ] Error handling and retry logic

**Verification**: All CRUD operations work, performance acceptable
**Time**: 3-4 hours
**Tests**: Tests for CRUD operations, concurrent access, transactions

---

**Task 2.5.3**: Create data query interfaces
- [ ] Create `src/database/queries.py` with:
  - `get_historical_data(symbol, start, end)`
  - `get_latest_data(symbol)`
  - `get_data_range(symbols, period)`
  - `query_indicators(symbol, indicator, period)`
- [ ] Support efficient querying
- [ ] Return typed results (pandas DataFrame or pydantic models)

**Verification**: Queries return correct data, performance good
**Time**: 2-3 hours
**Tests**: Tests for various query patterns, performance benchmarks

---

## Phase 3: Performance Calculation Layer (Weeks 3-4)

### 3.1 Variable Management System

**Task 3.1.1**: Create variable manager base
- [ ] Create `src/core/variable_manager.py`
- [ ] Implement `VariableManager` class with:
  - `register_variable(name, calculation_func, dependencies)`
  - `get_variable(name)` → value
  - `set_parameter(param_name, value)`
  - `compute_all_variables()`
  - Dependency tracking and topological sort
- [ ] Support lazy evaluation and caching
- [ ] Handle circular dependency detection

**Verification**: Variables computed in correct order, circular deps detected
**Time**: 4-5 hours
**Tests**: Tests for dependency resolution, caching, circular dependencies

---

**Task 3.1.2**: Implement technical indicator variables
- [ ] Create `src/core/indicator_variables.py`
- [ ] Implement common indicators as variables:
  - Moving averages (SMA, EMA, WMA)
  - Momentum indicators (RSI, MACD, ROC)
  - Volatility indicators (Bollinger Bands, ATR)
  - Volume indicators (OBV, VWAP)
- [ ] Each indicator available through variable manager
- [ ] Support multiple timeframes

**Verification**: All indicators computed correctly, match TA-Lib results
**Time**: 5-6 hours
**Tests**: Tests comparing with TA-Lib reference, different timeframes

---

**Task 3.1.3**: Implement derived value variables
- [ ] Create `src/core/derived_variables.py`
- [ ] Implement derived values:
  - Price returns (simple, log returns)
  - Volatility (rolling std, exponential weighted)
  - Correlations
  - Z-scores
  - Ranking
- [ ] Support cross-sectional and time-series calculations

**Verification**: Calculations match statistical references
**Time**: 3-4 hours
**Tests**: Tests against pandas reference implementations

---

### 3.2 Parameter Management System

**Task 3.2.1**: Create parameter manager
- [ ] Create `src/core/parameter_manager.py`
- [ ] Implement `ParameterManager` class with:
  - `define_parameter(name, type, range, default)`
  - `register_parameter_set(name, values, metadata)`
  - `get_best_parameter_sets(metric, top_n)`
  - `load_parameter_set(set_id)`
  - `save_optimization_result(params, metrics)`
- [ ] Store parameter sets with metadata (date, asset, period, performance)
- [ ] Support parameter validation

**Verification**: Can save/load parameter sets, queries work
**Time**: 3-4 hours
**Tests**: Tests for CRUD operations, queries, validation

---

**Task 3.2.2**: Create parameter history and versioning
- [ ] Extend parameter manager with:
  - Parameter set versioning
  - Historical tracking of parameter changes
  - A/B testing framework (old vs. new parameters)
  - Performance comparison across versions
- [ ] Store all optimization runs for analysis

**Verification**: Can compare parameter sets across time, A/B test works
**Time**: 2-3 hours
**Tests**: Tests for versioning, comparison, A/B testing

---

### 3.3 Error Detection and Analysis

**Task 3.3.1**: Create error detector
- [ ] Create `src/analysis/error_detector.py`
- [ ] Implement `ErrorDetector` class with:
  - Statistical anomaly detection (z-score, IQR)
  - Isolation forest for complex anomalies
  - Contextual detection (compare to peers, market)
  - Confidence scoring
- [ ] Detect:
  - Trading errors (unusual frequency, size)
  - Data errors (price jumps, missing data)
  - Market anomalies (extreme movements)

**Verification**: Detects known anomalies, low false positive rate
**Time**: 4-5 hours
**Tests**: Tests with synthetic anomalies, real market anomalies

---

**Task 3.3.2**: Create anomaly analysis and logging
- [ ] Extend error detector with:
  - Anomaly logging and alerting
  - Root cause analysis
  - Anomaly history and patterns
  - Recommendations for handling
- [ ] Integrate with monitoring system

**Verification**: Anomalies logged correctly, alerts triggered
**Time**: 2-3 hours
**Tests**: Tests for logging, alerting, analysis accuracy

---

### 3.4 Result Normalization and Aggregation

**Task 3.4.1**: Create result normalizer
- [ ] Create `src/analysis/normalizer.py`
- [ ] Implement normalization methods:
  - Min-max scaling (0-1 range)
  - Z-score normalization
  - Percentile ranking
  - Robust scaling (using median/IQR)
- [ ] Handle edge cases (zero range, all same value)
- [ ] Support different normalization for different metric types

**Verification**: Normalization formulas correct, edge cases handled
**Time**: 2-3 hours
**Tests**: Tests with various data distributions, edge cases

---

**Task 3.4.2**: Create result aggregator
- [ ] Create `src/analysis/aggregator.py`
- [ ] Implement aggregation strategies:
  - Simple averaging
  - Weighted averaging
  - Robust aggregation (remove outliers)
  - Hierarchical aggregation (by sector, strategy, etc.)
- [ ] Support partial results and missing data
- [ ] Calculate aggregation confidence/uncertainty

**Verification**: Aggregations mathematically correct, handles partial data
**Time**: 3-4 hours
**Tests**: Tests for different aggregation methods, partial data

---

### 3.5 Core Backtest Engine

**Task 3.5.1**: Create refactored backtest engine
- [ ] Create `src/backtest/core_backtest_engine.py`
- [ ] Rewrite using new architecture:
  - Use Data Management layer for data
  - Use Variable Manager for indicators
  - Use Parameter Manager for parameters
  - Use Signal Generator for trading signals
- [ ] Maintain all existing functionality
- [ ] Improve documentation and clarity

**Verification**: Backtests produce same results as legacy engine
**Time**: 6-8 hours
**Tests**: Tests comparing legacy vs. new engine results

---

**Task 3.5.2**: Add parallel backtesting support
- [ ] Extend backtest engine with:
  - Multi-process execution for parameter grid search
  - Result aggregation across processes
  - Progress tracking
  - Resource management (CPU, memory)
- [ ] Support batch backtesting

**Verification**: Parallel execution faster than sequential, results consistent
**Time**: 4-5 hours
**Tests**: Tests for parallel execution, result consistency

---

### 3.6 Trading Logic Framework

**Task 3.6.1**: Create signal generator
- [ ] Create `src/core/signal_generator.py`
- [ ] Implement `ISignalGenerator` interface with:
  - `generate_signals(variables) → List[Signal]`
  - Support for BUY, SELL, HOLD actions
  - Confidence scores for signals
  - Signal rationale/reasoning
- [ ] Support multiple signal types

**Verification**: Signals generated correctly, confidence scores reasonable
**Time**: 2-3 hours
**Tests**: Tests for signal generation, confidence scoring

---

**Task 3.6.2**: Create execution engine
- [ ] Create `src/core/execution_engine.py`
- [ ] Implement `ExecutionEngine` with:
  - Order placement simulation
  - Position tracking
  - Commission and slippage modeling
  - Order fill simulation (partial fills)
  - Trade tracking and analytics
- [ ] Realistic execution modeling

**Verification**: Executions simulated realistically, tracking accurate
**Time**: 4-5 hours
**Tests**: Tests for order execution, slippage, position tracking

---

## Phase 4: Visualization Tools Layer (Weeks 4-5)

### 4.1 Chart Generation Service

**Task 4.1.1**: Create unified chart service
- [ ] Create `src/visualization/chart_service.py`
- [ ] Implement `ChartService` with methods for:
  - Line charts (price, equity curve)
  - Bar charts (returns, sectors)
  - Scatter plots (risk-return)
  - Heatmaps (correlation, sector performance)
  - Candlestick charts (OHLCV)
- [ ] Support customizable styling
- [ ] Export to PNG, SVG, PDF, HTML

**Verification**: All chart types work, exports valid files
**Time**: 5-6 hours
**Tests**: Tests for chart generation, export formats

---

**Task 4.1.2**: Create interactive visualization
- [ ] Enhance chart service with:
  - Interactive features (hover, zoom, pan)
  - Drill-down capability
  - Filtering and selection
  - Real-time updates
  - Responsive design

**Verification**: Charts interactive, responsive to user input
**Time**: 4-5 hours
**Tests**: Tests for interactive features

---

### 4.2 Dashboard Refactoring

**Task 4.2.1**: Update dashboard routes
- [ ] Refactor `src/dashboard/api_routes.py` to:
  - Call calculation layer APIs instead of direct calculations
  - Simplify route handlers
  - Improve error handling
- [ ] Remove calculation logic from routes
- [ ] Update all endpoints

**Verification**: All routes functional, same results as before
**Time**: 4-5 hours
**Tests**: Update all endpoint tests to use new structure

---

**Task 4.2.2**: Create dashboard widget system
- [ ] Create `src/dashboard/widgets.py`
- [ ] Implement reusable widgets:
  - Portfolio overview
  - Strategy performance
  - Trade history
  - Risk dashboard
  - Alert panel
- [ ] Support customization and layout

**Verification**: Widgets render correctly, can be arranged
**Time**: 3-4 hours
**Tests**: Tests for widget rendering and data display

---

### 4.3 Report Generation

**Task 4.3.1**: Create report builder
- [ ] Create `src/visualization/report_builder.py`
- [ ] Implement `ReportBuilder` with:
  - Report template system
  - Section builders (executive summary, details, charts)
  - Export to PDF, Excel, HTML
  - Scheduling and distribution
- [ ] Support multiple report types

**Verification**: Reports generated correctly, exports valid
**Time**: 5-6 hours
**Tests**: Tests for report generation, different templates

---

### 4.4 Real-time Monitoring

**Task 4.4.1**: Create performance monitor service
- [ ] Create `src/visualization/performance_monitor.py`
- [ ] Implement monitoring for:
  - Strategy performance metrics
  - Data freshness
  - API response times
  - Error rates
  - System health
- [ ] Real-time updates via WebSocket
- [ ] Alert triggering

**Verification**: Monitors all metrics, alerts work
**Time**: 4-5 hours
**Tests**: Tests for monitoring, alerting

---

## Phase 5: Cleanup and Testing (Weeks 5-6)

### 5.1 Code Removal and Consolidation

**Task 5.1.1**: Remove duplicate code
- [ ] Identify all duplicate code across layers
- [ ] Remove:
  - Old adapter implementations (after verification)
  - Old calculation code
  - Old visualization code
- [ ] Update imports across codebase
- [ ] Verify no functionality lost

**Verification**: All duplicate code removed, system still works
**Time**: 4-5 hours
**Tests**: Run full test suite after each removal

---

**Task 5.1.2**: Consolidate configuration
- [ ] Create unified configuration system
- [ ] Move all settings to configuration files
- [ ] Support environment-specific configuration
- [ ] Remove hardcoded values from code

**Verification**: All configuration externalized, no hardcoded values
**Time**: 2-3 hours

---

### 5.2 Integration Testing

**Task 5.2.1**: Create end-to-end tests
- [ ] Create tests covering:
  - Data fetch → calculation → visualization pipeline
  - Strategy backtest end-to-end
  - Report generation end-to-end
  - Dashboard API end-to-end
- [ ] Use realistic data
- [ ] Verify all layers work together

**Verification**: E2E tests pass, realistic scenarios covered
**Time**: 5-6 hours
**Tests**: Create comprehensive E2E test suite

---

**Task 5.2.2**: Performance testing
- [ ] Benchmark critical paths:
  - Data fetching speed
  - Indicator calculation speed
  - Backtest speed
  - Dashboard query speed
- [ ] Compare with legacy implementation
- [ ] Identify and fix bottlenecks
- [ ] Document performance characteristics

**Verification**: Performance meets or exceeds legacy implementation
**Time**: 4-5 hours
**Tests**: Create performance test suite with benchmarks

---

### 5.3 Documentation

**Task 5.3.1**: Update architecture documentation
- [ ] Update CLAUDE.md with new architecture
- [ ] Document new interfaces and patterns
- [ ] Add migration guide for developers
- [ ] Create examples for common tasks

**Verification**: Documentation complete and accurate
**Time**: 3-4 hours

---

**Task 5.3.2**: Update API documentation
- [ ] Update API documentation
- [ ] Document new calculation layer APIs
- [ ] Document data management APIs
- [ ] Create API examples

**Verification**: API docs complete, examples work
**Time**: 2-3 hours

---

## Total Effort Summary

| Phase | Task Count | Estimated Hours | Days (assuming 8h/day) |
|-------|-----------|-----------------|----------------------|
| Phase 1 | 6 | 15-18 | 2-2.5 |
| Phase 2 | 15 | 48-58 | 6-7 |
| Phase 3 | 12 | 45-55 | 5.5-7 |
| Phase 4 | 6 | 25-30 | 3-4 |
| Phase 5 | 6 | 20-25 | 2.5-3 |
| **Total** | **45** | **153-186** | **19-23.5** |

**Team Allocation**: 2-3 engineers over 6 weeks = ~500 engineer-hours total

## Dependencies and Sequencing

- Phase 1 must complete before other phases
- Phase 2 can start immediately after Phase 1
- Phase 3 can start as Phase 2 completes (can overlap)
- Phase 4 can start as Phase 3 completes (can overlap)
- Phase 5 is cleanup and should happen after all other phases are mostly complete

## Risk Mitigation

- **Testing**: Each task includes comprehensive tests before moving to next phase
- **Feature flags**: Use feature flags to gradually migrate to new code paths
- **Rollback plan**: Keep legacy code accessible during transition period
- **Monitoring**: Extra monitoring during migration to catch issues quickly

## Sign-off

Tasks organized by phase and logical dependency. Each task includes:
- Clear acceptance criteria
- Time estimate
- Related tests
- Verification steps

Ready to begin implementation upon approval of proposal.
