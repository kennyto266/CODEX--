# Change Proposal: Refactor Core Architecture to Eliminate Duplication

## Summary

The CODEX quantitative trading system has grown organically with overlapping functionality scattered across multiple modules (data adapters, pipeline, agents, backtest engine, dashboard). This proposal restructures the system into three clear layers with well-defined boundaries, eliminating duplication and improving maintainability:

1. **Data Management Layer**: Unified data source interface, validation, cleaning, and persistence
2. **Performance Calculation Layer**: Core trading logic, variable management, parameter optimization, error detection
3. **Visualization Tools Layer**: Dashboards, charts, reports consuming APIs from lower layers

## Problem Statement

### Current Issues

1. **Functional Duplication**
   - Data cleaning logic appears in `src/data_adapters/`, `src/data_pipeline/`, and individual agent implementations
   - Indicator calculations duplicated across agents, backtest engine, and strategies
   - Performance metrics calculated in multiple places with inconsistent results
   - Multiple implementations of the same algorithm (e.g., moving average, RSI)

2. **Unclear Responsibility Boundaries**
   - Not clear which module should handle data validation
   - Agents both consume and produce data in overlapping ways
   - Backtest engine reimplements data processing already done elsewhere
   - Dashboard has business logic that should be in calculation layer

3. **Difficult to Extend**
   - Adding a new data source requires understanding multiple adapter patterns
   - Adding a new indicator requires modifying multiple modules
   - Adding a new metric requires changes scattered across codebase
   - Creating a new strategy requires learning different frameworks from agents vs. backtest

4. **Testing Challenges**
   - Difficult to test individual components in isolation
   - Integration tests needed to verify calculations work end-to-end
   - High coupling makes mocking difficult
   - Test coverage gaps because unclear ownership of functionality

5. **Performance Bottlenecks**
   - Same data fetched multiple times from API
   - Same indicators calculated multiple times in different contexts
   - No single place to implement caching effectively
   - Parallel processing difficult due to scattered computation

## Proposed Solution

### Three-Layer Architecture

```
┌────────────────────────────────────────┐
│  Visualization Tools (Dashboard, Charts) │
│  - Interactive dashboards              │
│  - Report generation                   │
│  - Chart building                      │
└────────────────────────────────────────┘
              ↑ Consumes
         API Results
              │
┌────────────────────────────────────────┐
│  Performance Calculation (Core Engine)   │
│  - Trading logic & signals             │
│  - Variable management                 │
│  - Parameter optimization              │
│  - Error detection & aggregation       │
└────────────────────────────────────────┘
              ↑ Consumes
          Standardized Data
              │
┌────────────────────────────────────────┐
│  Data Management (Data Sources)         │
│  - Unified source interface            │
│  - Data validation & cleaning          │
│  - Temporal alignment                  │
│  - Database persistence                │
└────────────────────────────────────────┘
```

### Layer Responsibilities

**Data Management Layer** (Spec: `specs/data-management/spec.md`)
- All data fetching from external sources
- Data validation and quality scoring
- Data cleaning and outlier detection
- Temporal alignment (handling holidays, timezones)
- Asset profile management
- Database caching and persistence

**Performance Calculation Layer** (Spec: `specs/performance-calculation/spec.md`)
- Variable management system (indicators, derived values)
- Parameter management system (strategy parameters, optimization)
- Trading logic and signal generation
- Error detection (anomalies, execution errors)
- Result normalization and aggregation
- Core backtest engine
- All calculations for performance metrics

**Visualization Tools Layer** (Spec: `specs/visualization-tools/spec.md`)
- Dashboard API routes calling calculation layer
- Chart generation service
- Report generation framework
- Real-time performance monitoring
- Data export and integration
- Attribution analysis

### Key Benefits

1. **Reduced Duplication**
   - Single implementation of each calculation
   - Easier to fix bugs (one place to fix)
   - Easier to improve performance (one place to optimize)

2. **Clear Ownership**
   - Each module has single responsibility
   - New developers understand where to add features
   - Testing easier with clear boundaries

3. **Improved Extensibility**
   - Add new data source: implement `IDataSource` interface
   - Add new indicator: add to variable manager
   - Add new metric: add to performance calculator
   - Add new visualization: use calculation APIs

4. **Better Testing**
   - Unit test each layer independently
   - Mock lower layers when testing upper layers
   - Easier to achieve high coverage

5. **Performance Improvements**
   - Unified caching across all calculations
   - Opportunity for parallelization
   - Eliminate redundant computations
   - Profile bottlenecks at layer boundaries

## Scope and Constraints

### In Scope

- Restructure directory layout and establish new module organization
- Create unified interfaces for data sources, calculators, and visualizations
- Refactor existing code to use new architecture
- Migrate agents to consume calculation layer APIs
- Update all tests for new architecture

### Out of Scope

- Implementing new features (only restructuring existing functionality)
- Database migration (use new ORM models going forward)
- Changing trading strategies (existing strategies adapted to new framework)

### Constraints

- Maintain backward compatibility during transition (phased migration)
- Zero downtime for live trading systems (if any)
- All existing tests must pass (80% coverage requirement maintained)
- Documentation updated alongside code changes

## Success Criteria

1. **Code Organization**
   - [ ] No duplication of calculation logic across layers
   - [ ] Clear module boundaries enforced (imports go down, not across)
   - [ ] All business logic in appropriate layer

2. **Interface Standardization**
   - [ ] All data sources implement `IDataSource`
   - [ ] All strategies implement `IStrategy`
   - [ ] All indicators available through variable manager
   - [ ] All calculations go through calculation layer

3. **Testing**
   - [ ] 80%+ test coverage maintained
   - [ ] Each layer independently testable
   - [ ] Integration tests verify layer interactions
   - [ ] No flaky tests due to timing or ordering

4. **Performance**
   - [ ] No regression in backtesting speed
   - [ ] Faster live data updates (better caching)
   - [ ] Dashboard response time < 500ms for typical queries

5. **Developer Experience**
   - [ ] New feature implementation requires changes in only 1-2 places
   - [ ] Adding new data source takes < 2 hours
   - [ ] Adding new indicator takes < 1 hour
   - [ ] Documentation clear and examples available

## Migration Strategy

The refactoring will be done in phases with overlap to maintain system stability:

**Phase 1 (Week 1-2)**: Infrastructure Setup
- Create new directory structure
- Define interfaces and base classes
- Set up build/test infrastructure

**Phase 2 (Week 2-3)**: Data Management Layer
- Implement new data source interface
- Migrate existing adapters
- Set up unified database models

**Phase 3 (Week 3-4)**: Performance Calculation Layer
- Implement variable management
- Migrate existing strategies
- Implement parameter manager

**Phase 4 (Week 4-5)**: Visualization Layer
- Update dashboard routes
- Consolidate chart generation
- Create report generation framework

**Phase 5 (Week 5-6)**: Cleanup and Testing
- Remove old duplicate code
- Final integration testing
- Performance optimization

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Performance regression | Medium | High | Profile before/after, run benchmarks |
| Breaking changes to agents | High | Medium | Maintain backward compatibility wrapper |
| Migration complexity | Medium | High | Use feature flags for phased rollout |
| Testing gaps | Medium | Medium | Improve test coverage before refactoring |

## Timeline

- **Start Date**: [To be determined after review]
- **Phase 1**: Weeks 1-2
- **Phase 2**: Weeks 2-3
- **Phase 3**: Weeks 3-4
- **Phase 4**: Weeks 4-5
- **Phase 5**: Weeks 5-6
- **Total Duration**: 6 weeks
- **Effort**: ~500 engineer-hours (distributed across team)

## Resources

- **Tech Lead**: Architecture oversight, design decisions
- **Backend Engineers**: Refactoring implementation
- **QA Engineer**: Test updates and validation
- **Data Engineer**: Data layer and database design
- **DevOps**: CI/CD updates for new structure

## Related Specifications

- [Data Management Spec](specs/data-management/spec.md) - Detailed requirements for data layer
- [Performance Calculation Spec](specs/performance-calculation/spec.md) - Core engine details
- [Visualization Tools Spec](specs/visualization-tools/spec.md) - UI/reporting requirements

## Approval and Sign-Off

**Proposed by**: Claude Code (AI Assistant)
**Date**: 2025-10-25
**Status**: Awaiting review and approval

---

## Next Steps

1. Review this proposal for correctness and completeness
2. Discuss with team for feedback and concerns
3. Approve scope and timeline
4. Proceed with Phase 1 implementation (see `tasks.md`)
