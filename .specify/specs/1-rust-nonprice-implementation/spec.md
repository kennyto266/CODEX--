# Feature Specification: Rust Non-Price Data Technical Indicators System

**Feature Branch**: `[1-rust-nonprice-implementation]`
**Created**: 2025-11-10
**Status**: Draft
**Input**: User description: "Implement non-price data to technical indicators conversion system in Rust with trading signal generation, parameter optimization, and backtesting capabilities including Sharpe ratio calculation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Non-Price Data Processing Engine (Priority: P1)

As a quantitative analyst, I need to convert non-price economic data (HIBOR rates, visitor counts, traffic speed, GDP growth, CPI, unemployment rate) into actionable technical indicators so that I can generate trading signals based on macroeconomic factors.

**Why this priority**: This is the core functionality that enables the entire system to work. Without data processing and technical indicator calculation, no trading signals can be generated.

**Independent Test**: Can be tested independently by processing a sample dataset of 1000+ data points and verifying that all technical indicators (Z-Score, RSI, SMA) are calculated correctly with mathematical precision.

**Acceptance Scenarios**:

1. **Given** a dataset containing HIBOR overnight rates from 2022-2025, **When** the system processes the data, **Then** it should generate Z-Score values using 20-day rolling windows, RSI values using 14-day periods, and SMA fast/slow lines using 10-day and 30-day periods respectively.
2. **Given** multiple non-price indicators (visitor count, traffic speed, GDP, CPI, unemployment), **When** processed, **Then** each indicator should have all three technical indicators calculated independently without data leakage.
3. **Given** incomplete or missing data points, **When** the system encounters them, **Then** it should handle them gracefully using forward-fill or interpolation methods and log the issue.

---

### User Story 2 - Trading Signal Generation (Priority: P1)

As a trader, I need automated trading signals (BUY/SELL/HOLD) generated from technical indicators of non-price data so that I can make informed trading decisions based on macroeconomic trends.

**Why this priority**: Signal generation is the primary value delivery mechanism. Users need clear, actionable signals to execute trades.

**Independent Test**: Can be tested independently by applying signal generation logic to a dataset with known indicator values and verifying that signals are generated according to the configured thresholds (e.g., Z-Score buy threshold of -0.5, sell threshold of 0.5).

**Acceptance Scenarios**:

1. **Given** Z-Score value of -0.6 for HIBOR, **When** signal generation runs, **Then** it should generate a BUY signal.
2. **Given** RSI value of 80 for visitor count, **When** signal generation runs, **Then** it should generate a SELL signal (assuming overbought threshold is 75).
3. **Given** SMA fast line crossing above SMA slow line, **When** signal generation runs, **Then** it should generate a BUY signal for golden cross scenario.
4. **Given** conflicting signals from multiple indicators, **When** signal generation runs, **Then** it should use the configured logic (e.g., majority vote, OR/AND conditions) to determine the final signal.

---

### User Story 3 - Parameter Optimization System (Priority: P2)

As a quantitative researcher, I need to optimize trading parameters across thousands of combinations (2,160 combinations per indicator) to find the best-performing threshold values so that I can maximize strategy performance metrics like Sharpe ratio.

**Why this priority**: Parameter optimization is critical for strategy performance but can be implemented after basic signal generation. It helps users discover optimal thresholds for their specific market conditions.

**Independent Test**: Can be tested independently by running parameter optimization on a historical dataset and verifying that the system explores all parameter combinations within the defined ranges without errors, and returns the best combination based on Sharpe ratio.

**Acceptance Scenarios**:

1. **Given** parameter ranges (Z-Score buy: -2.0 to 0.0, sell: 0.5 to 2.0, RSI buy: 25-35, RSI sell: 65-75, SMA fast: 5-15, SMA slow: 20-40), **When** optimization runs, **Then** it should test all 2,160 combinations.
2. **Given** 6 different non-price indicators, **When** optimization completes, **Then** it should identify the best-performing indicator and its optimal parameters.
3. **Given** multi-core CPU environment, **When** optimization runs, **Then** it should utilize parallel processing to reduce computation time by at least 50%.

---

### User Story 4 - Backtesting and Performance Evaluation (Priority: P1)

As an investment manager, I need comprehensive backtesting that applies trading signals to actual stock price movements to evaluate strategy performance using metrics like Sharpe ratio, maximum drawdown, and win rate so that I can validate the strategy before live trading.

**Why this priority**: Backtesting is essential for validating that signals derived from non-price data can actually generate profits in the stock market. It's a critical validation step before any live trading.

**Independent Test**: Can be tested independently by running backtests on historical data and verifying that all performance metrics are calculated correctly and match expected results from manual calculations.

**Acceptance Scenarios**:

1. **Given** 3-year historical stock price data and trading signals, **When** backtest completes, **Then** it should calculate Sharpe ratio, maximum drawdown, total return, annual return, and win rate.
2. **Given** buy signal on day 1 and sell signal on day 10, **When** backtest processes, **Then** it should calculate the correct profit/loss based on actual stock price movements.
3. **Given** initial capital of $100,000, **When** backtest runs, **Then** it should track portfolio value throughout the entire period and report final value.
4. **Given** multiple indicators with different signals, **When** backtest evaluates, **Then** it should use the final combined signal to determine position changes.

---

### Edge Cases

- **Data Quality Issues**: How does the system handle missing data points, outliers, or inconsistent data formats?
- **Market Conditions**: How does the system perform during market crashes, extreme volatility, or prolonged bull/bear markets?
- **Memory Constraints**: What happens when processing datasets larger than available system memory?
- **Calculation Errors**: How does the system handle division by zero in RSI calculations or negative values in Z-Score normalization?
- **Performance Degradation**: What happens if optimization takes longer than expected (timeout scenarios)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support processing 6 types of non-price indicators: HIBOR rates (5 maturities), visitor counts, traffic speed, GDP growth, CPI inflation, and unemployment rate.
- **FR-002**: System MUST calculate three technical indicators for each non-price indicator: Z-Score (20-day rolling), RSI (14-day), and SMA (fast: 10-day, slow: 30-day).
- **FR-003**: System MUST generate three types of trading signals: BUY, SELL, HOLD based on configurable threshold parameters.
- **FR-004**: System MUST support parameter optimization across 2,160 combinations per indicator (Z-Score buy/sell: 4×4, RSI buy/sell: 3×3, SMA fast/slow: 3×5).
- **FR-005**: System MUST perform backtesting using actual stock price data to calculate performance metrics.
- **FR-006**: System MUST calculate and report key performance metrics: Sharpe ratio, total return, annual return, maximum drawdown, win rate, and final portfolio value.
- **FR-007**: System MUST support parallel processing for parameter optimization to improve performance.
- **FR-008**: System MUST generate detailed reports in both Markdown and JSON formats with optimization results.
- **FR-009**: System MUST handle edge cases gracefully including missing data, calculation errors, and performance timeouts.
- **FR-010**: System MUST provide clear error messages and logging for debugging and monitoring.

### Key Entities

- **Non-Price Indicator**: Represents economic/macro data points (HIBOR, visitor count, etc.) with timestamp, value, and metadata
- **Technical Indicator**: Calculated values (Z-Score, RSI, SMA) derived from non-price indicators with period and configuration
- **Trading Signal**: Generated decision (BUY/SELL/HOLD) based on technical indicator thresholds with confidence level
- **Parameter Set**: Collection of threshold values for signal generation (Z-Score buy/sell, RSI buy/sell, SMA fast/slow)
- **Backtest Result**: Performance metrics and trade history from applying signals to stock price data
- **Optimization Result**: Best-performing parameter combination and all tested combinations with performance scores

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System processes datasets of 1,000+ data points in under 30 seconds for single indicator
- **SC-002**: Parameter optimization completes 2,160 combinations in under 15 minutes on 8-core CPU
- **SC-003**: Backtesting generates accurate Sharpe ratio calculations matching manual calculations within 0.01 precision
- **SC-004**: System identifies optimal parameters achieving Sharpe ratio above 0.5 for at least one indicator
- **SC-005**: Final portfolio value shows positive return (>5%) over 3-year backtest period for best strategy
- **SC-006**: Maximum drawdown stays below 60% for the best-performing parameter combination
- **SC-007**: System maintains >95% uptime during intensive optimization tasks
- **SC-008**: Error rate for data processing stays below 0.1% for clean datasets

### Assumptions

- Input data is provided in CSV or Parquet format with date and value columns
- Stock price data for backtesting is available with Open, High, Low, Close, Volume columns
- Target stock for backtesting is Tencent (0700.HK) or similar Hong Kong stock
- System has access to multi-core CPU for parallel optimization
- Users have basic understanding of quantitative trading concepts
- Historical data spans at least 2-3 years for meaningful backtesting

### Constraints

- Must support datasets up to 100MB in size
- Optimization timeout set to 2 hours maximum
- Memory usage should not exceed 8GB during operation
- Must be compatible with existing Python ecosystem for data input/output
- Results should be reproducible given the same input data and parameters
- System processes data in batch mode only (no real-time streaming)
- Delivery as standalone executable binary (no runtime dependencies)
- Provides Python bindings via PyO3 for integration with existing workflows

### Dependencies

- Historical non-price economic data for Hong Kong (HIBOR, visitor statistics, etc.)
- Historical stock price data for backtesting
- Statistical/mathematical libraries for indicator calculations
- Parallel processing capabilities for optimization
- Report generation libraries for Markdown/JSON output
- PyO3 library for Python bindings (providing Python interface to Rust core)

## Non-Functional Requirements

### Performance

- System MUST complete single indicator processing in under 30 seconds
- System MUST complete full optimization (6 indicators × 2,160 combinations) in under 30 minutes
- Backtesting for 3-year period MUST complete in under 60 seconds

### Reliability

- System MUST handle missing data gracefully without crashing
- System MUST provide meaningful error messages for all failure scenarios
- System MUST maintain calculation accuracy with <0.01% error rate for mathematical operations

### Usability

- System MUST provide clear documentation for parameter configuration
- System MUST generate human-readable reports in Markdown format
- System MUST support batch processing of multiple indicators

### Scalability

- System MUST support adding new non-price indicators without code changes
- System MUST support extending parameter optimization ranges
- System MUST handle datasets up to 1M data points

## Clarifications

### Session 2025-11-10

- **Q: Real-time data processing or batch only?** → **A: Batch processing only**
- **Q: Deployment format preference?** → **A: Standalone executable**
- **Q: Integration with Python ecosystem?** → **B: Python bindings (PyO3)**

## Assumptions

- Non-price data sources will be provided in standardized CSV or Parquet format
- Stock price data for backtesting will use adjusted close prices to account for splits and dividends
- Benchmark risk-free rate for Sharpe ratio calculation will be 2% (Hong Kong savings rate)
- Trading costs (commission, slippage) will be set to 0.1% per transaction
- Position sizing will be fixed (100% allocation when signal is BUY/SELL, 0% when HOLD)

## Risks and Mitigations

- **Risk**: Poor performance of non-price indicators in stock prediction
  - **Mitigation**: Test multiple indicators and focus on best performers, provide clear performance metrics

- **Risk**: Overfitting of optimized parameters to historical data
  - **Mitigation**: Provide out-of-sample testing capabilities and clear warnings about overfitting risks

- **Risk**: Data quality issues affecting calculations
  - **Mitigation**: Implement robust data validation and error handling throughout the pipeline
