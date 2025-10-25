# Refactor Core Architecture to Eliminate Duplication

## Why

The CODEX quantitative trading system has grown organically with significant functional duplication:
- Data cleaning logic scattered across adapters, pipeline, and agents
- Indicator calculations duplicated in multiple places with inconsistent results
- Performance metrics calculated separately in agents, backtest engine, and dashboard
- No clear responsibility boundaries between modules
- Difficult to add new features without modifying multiple files

This change restructures the system into three clear layers (Data Management, Performance Calculation, Visualization) with well-defined boundaries, eliminating duplication and improving maintainability.

## What

The proposal consists of three comprehensive specifications:

1. **Data Management Layer** (`specs/data-management/spec.md`)
   - Unified data source interface for all data providers
   - Standardized data validation and quality scoring
   - Temporal alignment handling
   - Asset profile management
   - Database persistence with ORM

2. **Performance Calculation Layer** (`specs/performance-calculation/spec.md`)
   - Variable management system for indicators and derived values
   - Parameter management for strategy optimization
   - Error detection and anomaly handling
   - Result normalization and aggregation
   - Core backtest engine
   - Trading logic framework

3. **Visualization Tools Layer** (`specs/visualization-tools/spec.md`)
   - Unified chart generation service
   - Interactive analytics dashboard
   - Report generation framework
   - Real-time performance monitoring
   - Data export and integration
   - Performance attribution analysis

## How

The refactoring is planned as a 6-week implementation with 5 phases:

1. **Phase 1 (Weeks 1-2)**: Infrastructure setup - create directory structure and base interfaces
2. **Phase 2 (Weeks 2-3)**: Data Management layer - implement unified data source interface and consolidation
3. **Phase 3 (Weeks 3-4)**: Performance Calculation layer - variable/parameter management and core engine
4. **Phase 4 (Weeks 4-5)**: Visualization layer - refactor dashboard and chart generation
5. **Phase 5 (Weeks 5-6)**: Cleanup and testing - remove duplicate code and run integration tests

See `proposal.md` for complete proposal and `tasks.md` for detailed implementation tasks (45 tasks, ~500 engineer-hours total).

## Documents

- **proposal.md** - Complete change proposal with timeline, risks, and success criteria
- **design.md** - Architectural design explaining the three-layer structure
- **tasks.md** - Detailed task list for all 5 implementation phases
- **specs/data-management/spec.md** - Data Management layer requirements
- **specs/performance-calculation/spec.md** - Performance Calculation layer requirements
- **specs/visualization-tools/spec.md** - Visualization Tools layer requirements

## Next Steps

1. Review the proposal and specifications
2. Discuss with team for feedback
3. Approve scope and timeline
4. Begin Phase 1 implementation
