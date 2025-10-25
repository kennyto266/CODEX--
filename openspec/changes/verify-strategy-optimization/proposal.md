# Proposal: Verify Strategy Optimization CPU Usage and Data Authenticity

## Problem Statement

Users report that strategy parameter optimization results (~2,297 parameter combinations) complete in approximately 30 seconds, raising concerns about whether:

1. CPU cores are actually being utilized for computation
2. DataFrame data is properly copied (not shared/cached)
3. Technical indicator calculations are genuinely executed
4. Results represent authentic backtest computations vs. placeholder values

Currently, the system lacks:
- **CPU monitoring**: No visibility into which cores are active, CPU utilization %, or process threading
- **Per-task timing**: No measurement of how long each parameter combination takes to compute
- **Data validation**: No verification that results differ across parameter sets
- **Diagnostic output**: No logging of worker process status, memory usage, or computation progress

## Solution Overview

Implement a **Strategy Optimization Verification System** with four key components:

1. **CPU Monitoring**: Track CPU usage, thread count, memory, and worker process status during optimization
2. **Task Timing Diagnostics**: Measure and log per-task execution times to verify computation occurs
3. **Result Validation**: Verify result diversity and authenticity across parameter combinations
4. **Enhanced Logging**: Provide detailed diagnostic output showing exactly which cores are active

## Change Scope

This proposal spans three capabilities:
1. **Capability A**: CPU monitoring and diagnostic logging
2. **Capability B**: Per-task execution timing and progress tracking
3. **Capability C**: Result validation and authenticity verification

## Related Systems

- **Backtest Engine** (`src/backtest/enhanced_backtest_engine.py`): Uses multiprocessing
- **Strategy Functions** (`complete_project_system.py`, lines 2058-2327): Performs calculations
- **Performance Metrics** (`calculate_strategy_performance()`, lines 2329-2369): Computes Sharpe ratio
- **API Endpoint** (`/api/strategy-optimization/{symbol}`, lines 2371-2417): Exposes optimization

## Success Criteria

- ✅ CPU monitoring logs show actual worker processes and CPU cores in use
- ✅ Per-task timing logs show each task takes 20-50ms (for 1000-5000 row datasets)
- ✅ Result validation confirms result diversity > 80% unique values
- ✅ Total optimization time remains < 60 seconds for all 2,297 parameter combinations
- ✅ Documentation clearly explains why optimization is fast (lightweight data + high parallelism)

## Implementation Sequence

1. **Phase 1**: Add CPU monitoring infrastructure
2. **Phase 2**: Add per-task timing and progress tracking
3. **Phase 3**: Add result validation and authenticity checks
4. **Phase 4**: Integration testing and documentation

---

**Next**: Review `design.md` for architectural decisions and `tasks.md` for work breakdown.
