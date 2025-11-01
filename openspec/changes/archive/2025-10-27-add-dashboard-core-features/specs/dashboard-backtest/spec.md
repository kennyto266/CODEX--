# Specification: Dashboard Backtest Interface

**Capability ID**: `dashboard-backtest-interface`
**Status**: PROPOSED
**Priority**: CRITICAL
**API Endpoints**: 5
**Frontend Components**: 4

---

## Capability Overview

Enables users to configure, execute, and analyze strategy backtests directly from the dashboard without command-line access.

---

## ADDED Requirements

### Requirement: Backtest Execution via Web Interface

The system SHALL allow users to submit a backtest job with strategy, parameters, and date range via the dashboard

#### Scenario: User runs backtest for MA strategy
```
Given: User on Dashboard → Backtest tab
When: User selects strategy "MA (Moving Average)"
  And: Sets date range "2023-01-01" to "2024-01-01"
  And: Sets initial capital "$100,000"
  And: Clicks "Run Backtest"
Then: Backend creates backtest job
  And: Returns backtest_id with status "QUEUED"
  And: Frontend polls status endpoint every 2 seconds
  And: Status changes to "RUNNING" then "COMPLETED"
  And: Results display automatically with equity curve and metrics
```

#### API Specification
```
POST /api/backtest/run
Content-Type: application/json

{
  "strategy": "ma",
  "parameters": {
    "fast_period": 10,
    "slow_period": 30,
    "signal_period": 9
  },
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000,
  "commission": 0.001
}

Response (202 Accepted):
{
  "backtest_id": "bt-20251026-001",
  "status": "QUEUED",
  "started_at": "2025-10-26T10:00:00Z",
  "estimated_completion": "2025-10-26T10:05:00Z"
}
```

### Requirement: Backtest Status Polling

The system SHALL allow the frontend to poll backtest status and receive progress updates

#### Scenario: User monitors backtest progress
```
Given: Backtest job submitted with ID "bt-20251026-001"
When: Frontend polls GET /api/backtest/status/bt-20251026-001
Then: Returns current status: "RUNNING", progress 45%, ETA 3 minutes
  And: Frontend updates progress bar
  And: User sees real-time progress without page refresh
```

#### API Specification
```
GET /api/backtest/status/{backtest_id}

Response (200 OK):
{
  "backtest_id": "bt-20251026-001",
  "status": "RUNNING",
  "progress_percent": 45,
  "trades_processed": 450,
  "total_trades": 1000,
  "elapsed_time": "2m 30s",
  "estimated_remaining": "3m 0s"
}
```

### Requirement: Backtest Results Display

The system SHALL fetch and display complete backtest results with visualizations

#### Scenario: User views backtest results
```
Given: Backtest completed successfully
When: Frontend fetches /api/backtest/results/bt-20251026-001
Then: Returns complete results with:
  - Equity curve (daily values)
  - Performance metrics (Sharpe, Sortino, Max Drawdown, etc.)
  - Trade list (entry, exit, PnL for each trade)
  - Monthly returns heatmap
  - Drawdown chart
```

#### API Specification
```
GET /api/backtest/results/{backtest_id}

Response (200 OK):
{
  "backtest_id": "bt-20251026-001",
  "strategy": "ma",
  "status": "COMPLETED",
  "metrics": {
    "total_return_pct": 23.5,
    "annual_return_pct": 19.2,
    "sharpe_ratio": 1.8,
    "sortino_ratio": 2.1,
    "max_drawdown_pct": 8.5,
    "win_rate": 0.58,
    "profit_factor": 1.9,
    "total_trades": 45,
    "winning_trades": 26,
    "losing_trades": 19
  },
  "equity_curve": [
    {"date": "2023-01-01", "value": 100000},
    {"date": "2023-01-02", "value": 101500},
    ...
  ],
  "trades": [
    {
      "entry_date": "2023-01-15",
      "entry_price": 325.50,
      "exit_date": "2023-01-20",
      "exit_price": 328.75,
      "shares": 100,
      "pnl": 325,
      "pnl_pct": 1.0
    },
    ...
  ]
}
```

### Requirement: Backtest History & Management

The system SHALL allow users to view, compare, and manage past backtests

#### Scenario: User compares two backtest results
```
Given: User has run 5 backtests in the past week
When: User views /dashboard/backtest/history
Then: Displays table with:
  - Backtest ID, strategy, date range, Sharpe ratio, max drawdown
  - "View Details" button for each
  - "Compare" checkbox to select multiple backtests
When: User selects 2 backtests and clicks "Compare"
Then: Shows side-by-side metrics and overlaid equity curves
```

#### API Specification
```
GET /api/backtest/list
  ?strategy=ma&limit=10&offset=0&sort_by=created_at

Response (200 OK):
{
  "total": 5,
  "backtests": [
    {
      "backtest_id": "bt-20251026-001",
      "strategy": "ma",
      "created_at": "2025-10-26T10:00:00Z",
      "start_date": "2023-01-01",
      "end_date": "2024-01-01",
      "initial_capital": 100000,
      "final_value": 123500,
      "total_return_pct": 23.5,
      "sharpe_ratio": 1.8,
      "max_drawdown_pct": 8.5
    },
    ...
  ]
}
```

### Requirement: Parameter Optimization UI

The system SHALL allow users to configure parameter optimization directly in the dashboard

#### Scenario: User optimizes MA fast period
```
Given: User on Backtest panel, MA strategy selected
When: User clicks "Optimize Parameters"
Then: Shows parameter optimization form:
  - fast_period: range 5-50, step 5
  - slow_period: range 20-100, step 10
  - signal_period: range 5-15, step 1
When: User selects ranges and clicks "Start Optimization"
Then: Backend runs 1000+ combinations
  And: Frontend displays optimization progress
  And: Results show best parameters with associated Sharpe ratio
```

#### API Specification
```
POST /api/backtest/optimize

{
  "strategy": "ma",
  "base_parameters": {
    "fast_period": [5, 50, 5],      # [min, max, step]
    "slow_period": [20, 100, 10],
    "signal_period": [5, 15, 1]
  },
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "optimize_for": "sharpe_ratio",  # or "total_return", "win_rate"
  "max_workers": 8
}

Response (202 Accepted):
{
  "optimization_id": "opt-20251026-001",
  "status": "QUEUED",
  "total_combinations": 1200
}
```

---

## Capability Dependencies

**Requires**:
- `enhanced_backtest_engine.py` (backend backtest execution)
- `strategy_performance.py` (performance metrics calculation)
- Database table: `backtest_configs` (store configurations)
- Database table: `backtest_results` (store results)

**Extends**:
- Strategy backtest spec (core backtest functionality)

**No breaking changes** to existing APIs.

---

## Frontend Components

### BacktestPanel (Parent Container)
- Tabs: Configuration, Results, History, Optimization
- State: selectedStrategy, backtestId, results, isRunning

### BacktestForm
- Strategy selector dropdown
- Date range picker
- Capital input (default 100000)
- Commission input (default 0.1%)
- "Run Backtest" button with spinner

### BacktestResults
- Equity curve chart (Chart.js line chart)
- Metrics cards (Sharpe, Sortino, Max Drawdown, etc.)
- Trade table (paginated, sortable)
- Monthly returns heatmap

### BacktestComparison
- Strategy comparison picker
- Side-by-side metrics table
- Overlaid equity curves
- Performance metric comparison

---

## Database Schema

```sql
CREATE TABLE backtest_configs (
  id VARCHAR(50) PRIMARY KEY,
  strategy VARCHAR(50) NOT NULL,
  parameters JSON NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  initial_capital DECIMAL(15, 2) NOT NULL,
  commission DECIMAL(5, 4),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(100),
  status ENUM('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED'),
  INDEX idx_strategy (strategy),
  INDEX idx_created_at (created_at)
);

CREATE TABLE backtest_results (
  id VARCHAR(50) PRIMARY KEY,
  config_id VARCHAR(50) NOT NULL,
  total_return_pct DECIMAL(10, 4),
  annual_return_pct DECIMAL(10, 4),
  sharpe_ratio DECIMAL(10, 4),
  sortino_ratio DECIMAL(10, 4),
  max_drawdown_pct DECIMAL(10, 4),
  win_rate DECIMAL(5, 4),
  profit_factor DECIMAL(10, 4),
  total_trades INT,
  winning_trades INT,
  losing_trades INT,
  equity_curve JSON,      -- array of {date, value}
  trades JSON,            -- array of trade objects
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (config_id) REFERENCES backtest_configs(id),
  INDEX idx_config (config_id)
);
```

---

## Performance Requirements

| Metric | Target | Rationale |
|--------|--------|-----------|
| Backtest execution (1 year) | < 30 seconds | User waits for results |
| API response time | < 100ms | Frontend polling |
| Results display time | < 2 seconds | Chart rendering |
| History list load | < 500ms | Database query |

---

## Error Handling

**Scenario: Invalid parameter range**
```
When: User submits start_date > end_date
Then: Return 400 Bad Request
{
  "error": "Invalid date range",
  "message": "start_date must be before end_date",
  "field": "date_range"
}
```

**Scenario: Backtest timeout**
```
When: Backtest runs > 5 minutes
Then: Return 408 Request Timeout
{
  "error": "Backtest timeout",
  "backtest_id": "bt-20251026-001",
  "message": "Backtest exceeded 5 minute limit. Try with shorter date range."
}
```

---

## Testing Strategy

### Unit Tests
- [ ] Parameter validation (valid/invalid ranges)
- [ ] Metrics calculation (equity curve, Sharpe ratio)
- [ ] Trade identification (entry/exit signals)

### Integration Tests
- [ ] Full backtest workflow (submit → poll → fetch results)
- [ ] Result persistence (save to database)
- [ ] History retrieval (query multiple backtests)

### E2E Tests
- [ ] User runs backtest end-to-end in browser
- [ ] Results display correctly in charts
- [ ] Comparison feature works with 2+ backtests

### Performance Tests
- [ ] Large backtest (5+ years data): < 60 seconds
- [ ] Large result set (1000+ trades): < 2 second display
- [ ] Concurrent backtests: 10 simultaneous jobs

---

**Specification Status**: DRAFT
**Ready for Implementation**: NO (pending approval)
**Last Updated**: 2025-10-26
