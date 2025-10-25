# Specification: Per-Task Execution Timing

## Purpose

Measure and report the actual CPU and wall-clock time required to execute each strategy parameter combination, enabling verification that computation is genuine and not cached.

## ADDED Requirements

### Requirement: Per-Task Timing Measurement

The system SHALL measure execution time for each strategy parameter combination independently.

#### Scenario: Capture timing for individual task
- **WHEN** a strategy parameter combination is executed
- **THEN** measure:
  - `wall_time_ms`: Wall-clock time elapsed (time.time() delta) in milliseconds
  - `cpu_time_ms`: CPU time used (time.process_time() delta) in milliseconds
  - `cpu_efficiency`: Ratio of CPU time to wall time as percentage
    - Formula: `cpu_time_ms / wall_time_ms * 100`
    - Expected: 80-100% (high CPU efficiency, no I/O wait)

#### Scenario: Timing data structure
- **WHEN** task completes and returns result
- **THEN** attach timing metadata to result:
  ```python
  result['_timing'] = {
    'task_id': str,                # Unique task identifier
    'task_index': int,             # Sequential task index (0 to total-1)
    'wall_time_ms': float,         # Wall-clock time in ms
    'cpu_time_ms': float,          # CPU time in ms
    'cpu_efficiency': float,       # Percentage 0-100
  }
  ```

#### Scenario: Timing measurement accuracy
- **WHEN** timing is recorded
- **THEN** ensure:
  - Timing measurements are exclusive to strategy execution only
  - Exclude task scheduling/queue overhead
  - Exclude result serialization/deserialization
  - Granularity: millisecond precision
  - Overhead: < 2ms per measurement

### Requirement: Task Identification and Indexing

The system SHALL assign unique identifiers to each strategy parameter combination task.

#### Scenario: Generate task IDs
- **WHEN** parameter combinations are enumerated
- **THEN** assign to each combination:
  - Unique `task_id` (string or UUID)
  - Sequential `task_index` (0 to total-1)
  - Strategy name and parameters for traceability

#### Scenario: Task ID structure
- **WHEN** task is identified
- **THEN** include in result:
  - task_id links results back to original parameters
  - task_index enables progress tracking
  - Example: task_id = "MA_3_10_001", task_index = 47

### Requirement: Progress Tracking and Logging

The system SHALL emit progress logs showing task completion rate and timing statistics.

#### Scenario: Log progress every 100 tasks
- **WHEN** tasks are completed during optimization
- **THEN** every 100+ task completions, log at INFO level:
  ```
  ✅ Progress: 100/2297 tasks (4%)
  ✅ Progress: 200/2297 tasks (9%)
  ...
  ✅ Progress: 2297/2297 tasks (100%)
  ```

#### Scenario: Log average task timing
- **WHEN** progress milestone is reached
- **THEN** include in log message:
  - Number of completed tasks
  - Percentage complete
  - Average wall-clock time per task (ms)
  - Average CPU efficiency (%)

#### Scenario: Example progress log output
```
✅ Progress: 500/2297 tasks (22%)
   Avg time: 28.5ms/task, CPU efficiency: 92.3%
   Estimated remaining: 45 seconds
```

### Requirement: Timing Summary Report

The system SHALL generate summary statistics of task execution times after optimization completes.

#### Scenario: Generate timing summary
- **WHEN** all optimization tasks complete
- **THEN** calculate and report:
  ```python
  timing_summary = {
    'total_tasks': int,            # Number of completed tasks
    'min_wall_time_ms': float,     # Fastest single task
    'max_wall_time_ms': float,     # Slowest single task
    'avg_wall_time_ms': float,     # Average wall-clock time
    'min_cpu_time_ms': float,      # Minimum CPU time
    'max_cpu_time_ms': float,      # Maximum CPU time
    'avg_cpu_time_ms': float,      # Average CPU time
    'avg_cpu_efficiency': float,   # Mean CPU efficiency %
    'total_wall_seconds': float,   # Sum of all wall times
    'total_cpu_seconds': float,    # Sum of all CPU times
  }
  ```

#### Scenario: Log timing summary
- **WHEN** optimization completes
- **THEN** log at INFO level:
  ```
  ⏱️ Timing Summary:
     - Tasks completed: 2,297
     - Avg time per task: 28.3ms
     - Range: 15ms - 102ms
     - CPU efficiency: 91.2%
     - Total wall time: 65.2 seconds
  ```

#### Scenario: Timing statistics validation
- **WHEN** timing summary is calculated
- **THEN** verify:
  - min_wall_time <= avg_wall_time <= max_wall_time
  - All times are positive (> 0)
  - cpu_efficiency between 0-100%
  - Total wall time >= sum of individual tasks / num_workers

### Requirement: Per-Strategy Timing Analysis

The system SHALL aggregate timing data by strategy type for comparative analysis.

#### Scenario: Calculate timing by strategy
- **WHEN** optimization includes multiple strategy types
- **THEN** group results and calculate per-strategy statistics:
  ```python
  strategy_timing = {
    'MA': {
      'count': 1104,
      'avg_time_ms': 22.1,
      'total_time_s': 24.4,
    },
    'RSI': {
      'count': 961,
      'avg_time_ms': 25.3,
      'total_time_s': 24.3,
    },
    ...
  }
  ```

#### Scenario: Identify expensive strategies
- **WHEN** strategy timing analysis is complete
- **THEN** log which strategies have:
  - Highest average time per task
  - Most total computation time
  - Lowest CPU efficiency

#### Scenario: Example per-strategy analysis log
```
📊 Timing by Strategy:
   MA:       1104 tasks, avg 22.1ms (eff: 93%), total: 24.4s
   RSI:       961 tasks, avg 25.3ms (eff: 91%), total: 24.3s
   MACD:      150 tasks, avg 31.2ms (eff: 87%), total:  4.7s
   KDJ:         8 tasks, avg 18.4ms (eff: 95%), total:  0.1s
   Parabolic:   1 tasks, avg 45.2ms (eff: 98%), total:  0.0s
```

### Requirement: Timing Data Export

The system SHALL make per-task timing data accessible for analysis.

#### Scenario: Export timing data in results
- **WHEN** optimization completes
- **THEN** include in response:
  - Per-task `_timing` metadata in each result
  - Summary statistics in `diagnostics.timing_summary`
  - Per-strategy breakdown in `diagnostics.timing_by_strategy`

#### Scenario: Timing data persistence
- **WHEN** results are stored or exported
- **THEN** preserve timing data:
  - Do NOT strip `_timing` fields during serialization
  - Include timing in CSV/JSON exports
  - Enable post-analysis of performance trends

### Requirement: Timing Anomaly Detection

The system SHALL detect and log tasks with unusual execution times.

#### Scenario: Flag slow tasks
- **WHEN** task execution time exceeds 2x average
- **THEN** log at WARNING level:
  ```
  ⚠️ Slow task detected:
     Task: RSI_25_65_087
     Time: 156.3ms (avg: 25.3ms, 6.2x slower)
     Sharpe: 0.87
  ```

#### Scenario: Flag fast tasks
- **WHEN** task execution time is less than 0.5x average
- **THEN** log at DEBUG level (for investigation):
  ```
  🚀 Fast task completed:
     Task: KDJ_14_001
     Time: 4.2ms (avg: 18.4ms, 4.4x faster)
  ```

#### Scenario: Anomaly investigation
- **WHEN** anomaly is detected
- **THEN** do NOT:
  - Stop optimization
  - Skip result collection
  - Mark result as invalid
- **BUT** do log for manual investigation

### Requirement: Timing Integration with Progress Tracking

The system SHALL use timing data to estimate remaining computation time.

#### Scenario: Estimate remaining time
- **WHEN** progress milestone (every 100 tasks) is reached
- **THEN** calculate:
  - Average time per task so far
  - Remaining tasks
  - Estimated completion time
  - Example: `Estimated remaining: 45s`

#### Scenario: Time estimates in logs
- **WHEN** progress is logged
- **THEN** include estimate:
  ```
  ✅ Progress: 500/2297 (22%)
     Avg: 28.5ms/task
     ETA: 44 seconds remaining
  ```

---

## Related Specifications

- **CPU Monitoring**: System-level CPU utilization (spec/cpu-monitoring/)
- **Result Validation**: Result authenticity checks (spec/result-validation/)

## Implementation Notes

- Use `time.time()` for wall-clock time (includes all delays)
- Use `time.process_time()` for CPU time (excludes I/O, sleep)
- CPU efficiency = CPU time / Wall time * 100%
- Timing measurement overhead: 2-5ms per task
- Expected per-task times: 15-50ms for typical strategies with 1000-5000 rows

## Success Criteria

- ✅ Each task includes timing metadata
- ✅ Progress logged every 100 tasks with timing stats
- ✅ Timing summary generated after optimization
- ✅ Per-strategy timing analysis available
- ✅ Anomalies detected and logged
- ✅ Timing estimates accurate within 10%
- ✅ Timing data preserved in results export
