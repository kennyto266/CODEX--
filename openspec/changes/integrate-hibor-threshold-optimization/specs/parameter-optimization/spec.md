# Specification: Parameter Optimization Framework

## Overview

The Parameter Optimization Framework enables systematic testing of trading strategy parameters to find optimal configurations that maximize selected performance metrics.

## ADDED Requirements

### Requirement: Grid Search Engine

The system SHALL support exhaustive grid search over discrete parameter combinations with configurable ranges and step sizes.

#### Scenario: Basic Grid Search
Given:
- Strategy: HIBOR with parameters (threshold, holding_period, position_size)
- Parameter ranges: threshold [0.05%, 0.30%], period [1, 10], size [10%, 50%]
- Optimization metric: Sharpe ratio

When:
- User initiates grid search with 100+ combinations

Then:
- System tests all combinations in parallel
- Returns results sorted by Sharpe ratio (highest first)
- Execution completes in < 60 seconds
- Results include all metrics (Sharpe, return, drawdown, win rate)

#### Scenario: Custom Parameter Ranges
Given:
- RSI optimizer with configurable period, overbought, oversold levels

When:
- User specifies custom ranges: period [10-50], overbought [60-80], oversold [20-40]

Then:
- System generates parameter grid within specified ranges
- Grid respects step sizes (e.g., period step=5)
- All combinations are valid and testable

### Requirement: Multiprocessing Execution

The system SHALL utilize multiple CPU cores to accelerate parameter testing and reduce optimization time.

#### Scenario: Parallel Execution
Given:
- 100 parameter combinations to test
- 8-core CPU available

When:
- Grid search starts on 8-core system

Then:
- System spawns 8 worker processes
- Each worker processes parameter combinations independently
- Total execution time = linear time per combination × parallelization factor
- Workers complete approximately simultaneously
- No deadlocks or data corruption from parallel access

#### Scenario: Resource Constraints
Given:
- System with 4 CPU cores
- Memory limit of 500MB

When:
- Grid search starts with large parameter space (1000+ combinations)

Then:
- System respects max_workers constraint (< 4)
- Memory usage stays under 500MB
- System doesn't crash due to resource exhaustion
- Remaining combinations queued for processing

### Requirement: Metric-Based Optimization

The system SHALL support multiple performance metrics (Sharpe ratio, returns, drawdown, win rate, profit factor) for optimization and result ranking.

#### Scenario: Sharpe Ratio Optimization
Given:
- HIBOR strategy optimization
- Optimization metric: Sharpe ratio

When:
- Grid search completes

Then:
- Results ranked by Sharpe ratio (highest first)
- Each result includes calculated Sharpe ratio
- Top 10 results clearly identified

#### Scenario: Multi-Metric Results
Given:
- Completed optimization with 100 combinations tested

When:
- User retrieves results

Then:
- Each result includes:
  - Sharpe ratio
  - Annual return (%)
  - Maximum drawdown (%)
  - Win rate (%)
  - Profit factor
  - Number of trades
  - Parameter values

#### Scenario: Custom Metric Selection
Given:
- Multiple metrics available for optimization

When:
- User specifies optimization metric = "profit_factor"

Then:
- Results ranked by profit factor
- Results displayed with all metrics
- Best configuration per metric identified

### Requirement: Sensitivity Analysis

The system SHALL provide sensitivity analysis to determine how individual parameters affect performance metrics.

#### Scenario: Single Parameter Sensitivity
Given:
- Best parameters from grid search: threshold=0.15%, period=5, size=0.30
- Need to understand impact of threshold alone

When:
- User requests sensitivity analysis for threshold parameter

Then:
- System tests threshold range [0.05% to 0.35%] in steps
- Holds period=5, size=0.30 constant
- Returns Sharpe ratio for each threshold value
- Charts show parameter vs metric relationship

#### Scenario: Sensitivity Interpretation
Given:
- Sensitivity analysis results showing Sharpe vs threshold

When:
- User views sensitivity chart

Then:
- Chart clearly shows optimal threshold value
- Y-axis shows Sharpe ratio values
- X-axis shows threshold values
- Peak is highlighted
- Flat regions indicate parameter insensitivity

### Requirement: Result Persistence

The system SHALL persist optimization results in a database for future retrieval, comparison, and audit trails.

#### Scenario: Save Optimization Results
Given:
- Completed optimization with 100 combinations
- Best result has Sharpe=1.25, return=15%

When:
- System saves results to database

Then:
- OptimizationRun record created with:
  - strategy_name = "HIBOR"
  - symbol = "2800.HK"
  - created_at = current timestamp
  - metric = "sharpe_ratio"
  - total_combinations = 100
  - status = "completed"
- OptimizationResult records created for all 100 combinations
- Each result includes parameters and metrics

#### Scenario: Retrieve Past Results
Given:
- Multiple optimizations stored in database
- User wants results for HIBOR on 2800.HK from last week

When:
- User queries optimization history by symbol and strategy

Then:
- System returns:
  - List of past optimization runs
  - Date, metric, and best result for each
  - Ability to drill into full results

### Requirement: API Endpoints

The system SHALL expose parameter optimization capabilities through RESTful API endpoints for starting, monitoring, and retrieving optimization results.

#### Scenario: Start Optimization
Given:
- Client wants to optimize HIBOR for symbol 2800.HK

When:
- POST /api/optimize/2800.HK/hibor with body:
  ```json
  {
    "metric": "sharpe_ratio",
    "preset": "default"
  }
  ```

Then:
- HTTP 202 response with:
  ```json
  {
    "task_id": "opt_abc123",
    "status": "started",
    "created_at": "2025-10-24T10:30:00Z"
  }
  ```
- Optimization runs in background
- Client can poll for status

#### Scenario: Retrieve Results
Given:
- Completed optimization task

When:
- GET /api/optimize/2800.HK/hibor/results?limit=10

Then:
- HTTP 200 response with:
  ```json
  {
    "total": 120,
    "results": [
      {
        "rank": 1,
        "parameters": {"threshold": 0.15, "period": 5, "size": 0.30},
        "sharpe_ratio": 1.25,
        "annual_return": 0.15,
        ...
      }
    ]
  }
  ```

#### Scenario: Get Sensitivity Analysis
Given:
- Completed optimization

When:
- GET /api/optimize/2800.HK/hibor/sensitivity

Then:
- HTTP 200 response with sensitivity data for visualization:
  ```json
  {
    "threshold": {
      "values": [0.05, 0.10, 0.15, 0.20],
      "metrics": [0.95, 1.10, 1.25, 1.15]
    },
    "holding_period": {
      "values": [1, 3, 5, 7, 10],
      "metrics": [0.85, 1.05, 1.25, 1.15, 0.95]
    }
  }
  ```

## Cross-References

- Related to: Backtest Engine (src/backtest/) - used for strategy evaluation
- Related to: Strategy Modules (src/strategies/) - defines tradeable strategies
- Related to: FastAPI Routes (src/dashboard/api_routes.py) - exposes API
- Related to: Dashboard UI (frontend/) - visualizes results

## Implementation Notes

- Parameter optimization is CPU-intensive; multiprocessing is mandatory
- Results must be reproducible; parameter hashing enables caching
- Sensitivity analysis is computationally expensive; should be cached
- UI must support 1000+ result rows with filtering and sorting
