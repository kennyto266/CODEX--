# Proposal: Vectorbt-Based Architecture Redesign

**Change ID**: `vectorbt-architecture-redesign`

**Status**: Draft

**Version**: 1.0

**Created**: 2025-10-24

---

## Summary

Redesign the CODEX quantitative trading system to use **vectorbt** as the core backtesting engine while implementing a layered data architecture that explicitly separates:

1. **Data Source Layer** - Raw data acquisition from multiple providers
2. **Database Layer** - Persistent storage with standardized schemas
3. **Data Cleaning Layer** - Validation, normalization, datetime formatting
4. **Asset Profile Layer** - Static metadata about traded instruments
5. **Data Management Layer** - Query, caching, and data access patterns
6. **Core Backtest Engine** (vectorbt) - Vectorized performance computation
7. **Variables Management** - State, calculations, and intermediate results
8. **Trade Logic** - Signal generation and order execution rules
9. **Parameter Management** - Strategy configuration and optimization

---

## Motivation

### Current Limitations
- **Performance Bottleneck**: Current backtest engine uses Pandas iterative operations, not vectorized computations
- **Scalability Issues**: Cannot efficiently handle large parameter grids or long historical periods
- **Architectural Ambiguity**: Data pipeline is not explicitly layered; responsibilities are mixed
- **Optimization Inefficiency**: Parameter tuning requires repeated full backtests

### Vectorbt Advantages
- **Vectorized Operations**: 100-1000x faster than loop-based backtesting
- **Memory Efficient**: Processes terabytes of data in memory
- **Built-in Optimization**: Automatic portfolio metrics computation
- **Mature Ecosystem**: Production-ready, widely adopted in quant finance
- **Performance Metrics**: Native support for Sharpe, Sortino, Calmar, etc.

### Architecture Benefits
- **Clear Separation of Concerns**: Each layer has defined responsibilities
- **Testability**: Each layer can be tested independently
- **Extensibility**: Easy to swap data sources or add new analysis layers
- **Data Traceability**: Explicit transformation pipeline from raw to processed data

---

## Scope

### In Scope
✅ Replace current backtest engine with vectorbt
✅ Implement 9-layer data architecture
✅ Refactor data adapters to conform to new schema
✅ Create standardized data cleaning pipeline
✅ Implement asset profile metadata system
✅ Build parameter management system for strategy optimization
✅ Create data management interfaces (caching, querying)
✅ Migrate existing strategies to vectorbt
✅ Add comprehensive unit and integration tests

### Out of Scope
❌ Replace FastAPI dashboard (reuse existing)
❌ Modify agent system architecture
❌ Implement real-time trading execution
❌ Change database backend (SQLAlchemy remains)

---

## Key Design Decisions

### 1. Vectorbt Integration Pattern
- **Approach**: Wrapper layer on top of vectorbt for CODEX-specific needs
- **File**: `src/backtest/vectorbt_engine.py`
- **Interface**: Keep existing `IBacktestEngine` compatible

### 2. Data Flow
```
Data Source → Database → Cleaning → Asset Profile → Data Management
                                                           ↓
                                    Parameter Mgmt ← Variables ← Core Engine
                                           ↓
                                    Trade Logic → Results
```

### 3. DateTime Standardization
- **Standard**: UTC timezone, pandas DatetimeIndex
- **Format**: ISO 8601 for serialization
- **Frequency**: Market hours aware (non-trading days excluded)

### 4. Asset Profile Schema
```python
{
    "symbol": "0700.HK",
    "name": "Tencent",
    "market": "HKEX",
    "currency": "HKD",
    "multiplier": 1,
    "commission": 0.001,  # 0.1%
    "slippage": 0.0005,   # 0.05%
    "min_order_size": 1
}
```

---

## Dependencies & Sequencing

### Phase 1: Foundation (Weeks 1-2)
1. Install and verify vectorbt
2. Create data schema definitions
3. Implement asset profile system
4. Write data validation module

### Phase 2: Data Pipeline (Weeks 2-3)
5. Build data cleaning layer
6. Implement data management (caching/queries)
7. Create asset profile loader
8. Migrate existing data adapters

### Phase 3: Backtest Engine (Weeks 3-4)
9. Implement vectorbt wrapper
10. Migrate strategies to vectorbt format
11. Create performance metrics module
12. Build parameter optimization layer

### Phase 4: Testing & Validation (Week 4-5)
13. Write comprehensive tests
14. Validate against historical results
15. Performance benchmark
16. Documentation

---

## Success Criteria

- ✅ All strategies produce identical signals in vectorbt vs. old engine
- ✅ Backtest speed: 10x improvement on 5-year data
- ✅ Memory usage: < 1GB for standard dataset
- ✅ Parameter optimization: 100-parameter grid in < 1 minute
- ✅ Test coverage: ≥ 85%
- ✅ All existing functionality preserved

---

## References

- vectorbt Documentation: https://vectorbt.dev/
- CODEX Architecture: `openspec/project.md`
- Current Backtest: `src/backtest/enhanced_backtest_engine.py`
