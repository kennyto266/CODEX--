# Specification: CPU Monitoring and Diagnostic Reporting

## Purpose

Enable visibility into CPU resource utilization during strategy parameter optimization by instrumenting the multiprocess execution pipeline with process-level monitoring and diagnostic reporting.

## ADDED Requirements

### Requirement: CPU Utilization Baseline Capture

The system SHALL record baseline CPU and process metrics before strategy optimization begins.

#### Scenario: Capture baseline metrics at optimization start
- **WHEN** `/api/strategy-optimization/{symbol}` endpoint is invoked
- **AND** before any optimization tasks are submitted to the process pool
- **THEN** capture and log:
  - Process CPU usage percentage (at invocation time)
  - Number of active threads in main process
  - Memory usage in MB
  - Number of child processes (should be 0 at start)
  - System timestamp
- **AND** store baseline metrics for later comparison

#### Scenario: Accessible baseline data structure
- **WHEN** baseline metrics are captured
- **THEN** return data structure with fields:
  ```python
  {
    'timestamp': float,            # UNIX timestamp
    'cpu_percent': float,          # 0-100%
    'num_threads': int,            # Active threads
    'memory_mb': float,            # Memory in MB
    'num_children': int,           # Child processes
  }
  ```

### Requirement: CPU Utilization Real-Time Monitoring

The system SHALL collect CPU metrics during strategy optimization execution.

#### Scenario: Capture snapshots during optimization
- **WHEN** strategy optimization is in progress
- **THEN** every 500+ tasks processed:
  - Capture current process-level CPU metrics
  - Capture metrics for each child worker process:
    - Child process ID (PID)
    - Child CPU usage percentage
    - Child memory usage MB
  - Log snapshot with task completion count

#### Scenario: Track worker process lifecycle
- **WHEN** child processes are spawned by ProcessPoolExecutor
- **THEN** monitoring SHALL detect and track:
  - Number of active child processes (up to max_workers)
  - CPU percent per child process
  - Memory usage per child process
  - Verify children processes are actually consuming CPU

### Requirement: CPU Utilization Report Generation

The system SHALL generate comprehensive CPU monitoring report after optimization completes.

#### Scenario: Generate final CPU utilization report
- **WHEN** strategy optimization completes
- **THEN** generate report comparing baseline vs final state:
  ```python
  {
    'baseline': {
      'timestamp': float,
      'cpu_percent': float,
      'num_threads': int,
      'memory_mb': float,
      'num_children': int,
    },
    'final': {
      'timestamp': float,
      'cpu_percent': float,
      'num_threads': int,
      'memory_mb': float,
      'num_children': int,
      'child_processes': [
        {
          'pid': int,
          'cpu_percent': float,
          'memory_mb': float,
        },
        ...
      ]
    },
    'cpu_change': float,           # final - baseline
    'memory_change': float,        # final - baseline in MB
    'active_children': int,        # Number of children in final state
    'peak_cpu_percent': float,     # Maximum CPU during optimization (if tracked)
  }
  ```

#### Scenario: CPU monitoring report accuracy
- **WHEN** CPU monitoring report is generated
- **THEN** verify:
  - All numeric fields are non-negative
  - CPU percent ranges 0-100%
  - Timestamp is valid UNIX time
  - Child process count >= 0
  - active_children <= MAX_WORKERS (190)

### Requirement: CPU Monitoring Logging

The system SHALL emit detailed log messages for CPU monitoring activities.

#### Scenario: Log baseline capture
- **WHEN** baseline metrics are captured
- **THEN** log at INFO level:
  ```
  📊 CPU Monitoring Started
  Baseline: CPU=12.5%, Threads=8, Memory=245.3MB, Children=0
  ```

#### Scenario: Log CPU utilization during optimization
- **WHEN** monitoring snapshot is captured during optimization
- **THEN** log at DEBUG level (periodically):
  ```
  CPU Snapshot: CPU=85.2%, Threads=198, Memory=892.5MB, Children=187
  Active Workers: [PID1:75%, PID2:68%, ...]
  ```

#### Scenario: Log final CPU monitoring report
- **WHEN** optimization completes and report is generated
- **THEN** log at INFO level:
  ```
  ✅ CPU Monitoring Complete
  Baseline → Final: CPU 12.5% → 45.3% (+32.8%)
  Memory: 245.3MB → 892.5MB (+647.2MB)
  Peak Workers: 187/190 active
  ```

### Requirement: CPU Monitoring Integration with Optimization Pipeline

The system SHALL integrate CPU monitoring seamlessly into `run_strategy_optimization()` function.

#### Scenario: Transparent monitoring integration
- **WHEN** `run_strategy_optimization(data, strategy_type)` is called
- **THEN** CPU monitoring SHALL:
  - Not require additional parameters
  - Not modify existing result structure
  - Not introduce breaking changes to API
  - Execute transparently without user action

#### Scenario: CPU monitoring overhead
- **WHEN** CPU monitoring is active
- **THEN** impose < 5% overhead on total optimization time:
  - Each baseline/snapshot capture: < 50ms
  - Per-task overhead: < 2ms
  - Report generation: < 100ms
  - Example: 30-second optimization becomes 31-32 seconds

### Requirement: CPU Monitoring Data Persistence

The system SHALL make CPU monitoring data available in API responses.

#### Scenario: Include CPU monitoring in optimization response
- **WHEN** `/api/strategy-optimization/{symbol}` returns results
- **THEN** include `diagnostics.cpu_monitoring` object:
  ```json
  {
    "success": true,
    "data": { ... strategy results ... },
    "diagnostics": {
      "cpu_monitoring": { ... cpu report ... },
      "execution_time_seconds": 31.5,
      "strategies_per_second": 72.8
    },
    "timestamp": "2025-10-18T12:34:56.789Z"
  }
  ```

#### Scenario: Backwards compatible response
- **WHEN** clients consume optimization API response
- **THEN** existing clients SHALL continue to work:
  - All new fields are in `diagnostics` section
  - No changes to `data` structure
  - `success` field unchanged
  - Optional `diagnostics` can be ignored by older clients

### Requirement: psutil Process Monitoring

The system SHALL use psutil library to collect process-level metrics.

#### Scenario: Dependency requirement
- **WHEN** CPU monitoring is enabled
- **THEN** require `psutil` package:
  - MUST be in requirements.txt
  - Version: >= 5.9.0 (supports cpu_percent with interval)
  - Cross-platform support: Windows, Linux, macOS

#### Scenario: Handle monitoring errors gracefully
- **WHEN** psutil call fails (permission denied, process terminated)
- **THEN**:
  - Log warning with error details
  - Continue optimization without monitoring
  - Return partial diagnostics (only successful metrics)
  - Do NOT crash or interrupt optimization

---

## Related Specifications

- **Task Timing**: Per-task execution time measurement (spec/task-timing/)
- **Result Validation**: Result authenticity and diversity checks (spec/result-validation/)
- **Strategy Optimization**: Base optimization pipeline (openspec/specs/strategy-backtest/)

## Implementation Notes

- CPU monitoring uses `psutil.Process(os.getpid())`
- Child processes created by `ProcessPoolExecutor` automatically tracked
- CPU percent calculation: `process.cpu_percent(interval=0.1)` (non-blocking)
- Memory in MB: `process.memory_info().rss / 1024 / 1024`
- Child process iteration: `process.children(recursive=False)`

## Success Criteria

- ✅ Baseline metrics captured at optimization start
- ✅ CPU monitoring integrated without breaking changes
- ✅ Final report generated after optimization
- ✅ All metrics logged with appropriate detail level
- ✅ CPU monitoring overhead < 5%
- ✅ Graceful error handling for permission/availability issues
- ✅ All metrics exported in API response
