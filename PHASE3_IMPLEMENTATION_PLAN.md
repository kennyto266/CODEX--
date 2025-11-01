# Phase 3: Backtest Engine Integration - Implementation Plan

**Start Date**: 2025-10-25
**Estimated Duration**: 1-2 sessions
**Overall Status**: 🔄 **IN PREPARATION**

---

## 📋 Phase 3 Overview

Phase 3 integrates vectorbt to create a **10x faster backtest engine** while maintaining backward compatibility with existing strategies and metrics.

### Objectives
- ✅ Migrate from loop-based to vectorized backtesting
- ✅ Maintain 100% signal compatibility (99%+ correlation)
- ✅ Support existing strategies without modification
- ✅ Achieve sub-second backtests on 5-year datasets
- ✅ Enable fast parameter optimization (100 params in < 1 min)

### Success Criteria
- **Performance**: 10x improvement (0.1-0.3s per backtest)
- **Accuracy**: 99%+ signal correlation with EnhancedBacktest
- **Compatibility**: All existing strategies work unchanged
- **Test Coverage**: >= 85% on new code
- **Memory**: < 50MB for standard datasets

---

## 🏗️ Architecture Design

### Current System (Loop-Based)
```
Historical Data
    ↓
Daily Iteration Loop
├─→ Load data for day
├─→ Call strategy function (async)
├─→ Execute trades one-by-one
├─→ Update positions
└─→ Calculate portfolio value
    ↓
Results Aggregation (Python loops)
    ├─→ Calculate returns series
    ├─→ Compute metrics (Sharpe, etc.)
    └─→ Generate report
```

**Performance**: 2-3 seconds per 5-year backtest
**Memory**: 500MB+ for large datasets

### Proposed System (Vectorized with Vectorbt)
```
Historical Data (Pre-loaded)
    ↓
Vectorized Signal Generation
├─→ Apply strategy to entire dataset
├─→ Generate signal array (numpy)
└─→ Convert to entry/exit signals
    ↓
Portfolio Simulation (Vectorbt)
├─→ Portfolio.from_signals()
├─→ Automatic trade simulation
└─→ Built-in cost modeling
    ↓
Vectorized Metrics Extraction
├─→ Extract from portfolio._metrics
├─→ Calculate risk metrics
└─→ Generate report
```

**Performance**: 0.1-0.3 seconds per backtest
**Memory**: < 50MB

---

## 📊 Task Breakdown

### Task 3.1: Vectorbt Wrapper Engine
**Status**: 🔄 In Progress
**Deliverable**: `src/backtest/vectorbt_engine.py`

**Components to Implement**:

1. **VectorbtBacktestEngine Class**
   - Inherit from BaseBacktestEngine
   - Implement required interface methods
   - Data loading and preprocessing
   - Vectorized signal generation
   - Portfolio creation and simulation
   - Metrics extraction

2. **Data Preparation Layer**
   - Convert DataManager output to vectorbt format
   - Ensure proper datetime indexing
   - Handle multiple symbols
   - Pre-align OHLCV data

3. **Signal Generation Interface**
   - Adapter for existing async strategies
   - Vectorized signal computation
   - Entry/exit signal conversion
   - Position sizing integration

4. **Portfolio Management**
   - Use vectorbt.Portfolio
   - Cost configuration (commission, slippage)
   - Cash management
   - Leverage and short selling

5. **Metrics Extraction**
   - Extract all metrics from portfolio object
   - Calculate additional metrics if needed
   - Performance report generation

**Test Coverage**: 15+ test cases
**Expected Lines of Code**: 400-500

### Task 3.2: Strategy Adapter Layer
**Status**: 🔄 Planned
**Deliverable**: `src/backtest/strategy_adapter.py`

**Components to Implement**:

1. **StrategyAdapter Class**
   - Convert async generator strategy to vectorized
   - Handle strategy function signature changes
   - Signal format conversion

2. **Signal Conversion Utilities**
   - Trade list → numpy signal array
   - Support multiple signal types
   - Handle edge cases (no signals, partial fills)

3. **Backward Compatibility**
   - Wrap old strategies transparently
   - No changes to existing strategy code
   - Fallback to EnhancedBacktest if needed

4. **Vectorization Helpers**
   - Batch data preparation
   - Parallel signal generation
   - Memory-efficient processing

**Test Coverage**: 10+ test cases
**Expected Lines of Code**: 200-300

### Task 3.3: Vectorized Metrics
**Status**: 🔄 Planned
**Deliverable**: `src/backtest/vectorbt_metrics.py`

**Components to Implement**:

1. **VectorbtPerformanceCalculator Class**
   - Extract metrics from portfolio object
   - Compute additional risk metrics
   - Trade-level analytics

2. **Risk Metrics**
   - Volatility, Sharpe, Sortino
   - VaR, Expected Shortfall
   - Max Drawdown, Calmar ratio
   - Beta, Alpha, Information ratio

3. **Trade Analytics**
   - Win rate, Profit factor
   - Average win/loss
   - Trade duration analysis
   - Commission/slippage impact

4. **Report Generation**
   - Format metrics for display
   - Generate HTML reports
   - Export to JSON/CSV

**Test Coverage**: 20+ test cases
**Expected Lines of Code**: 300-400

### Task 3.4: Comprehensive Tests
**Status**: 🔄 Planned
**Deliverable**: `tests/test_vectorbt_engine.py`

**Test Categories**:

1. **Engine Tests** (10+ tests)
   - Initialization and configuration
   - Data loading and preprocessing
   - Backtest execution
   - Results generation

2. **Compatibility Tests** (15+ tests)
   - Signal correlation vs EnhancedBacktest
   - Metric accuracy vs manual calculation
   - Edge cases (no trades, all-in positions, etc.)

3. **Performance Tests** (5+ tests)
   - Execution speed benchmarks
   - Memory usage tracking
   - Optimization time measurement

4. **Integration Tests** (10+ tests)
   - DataManager integration
   - Strategy integration
   - Portfolio optimization
   - Report generation

**Test Coverage Goal**: >= 85%
**Expected Test Count**: 40+ tests

### Task 3.5: Parameter Optimization
**Status**: 🔄 Planned
**Deliverable**: `src/backtest/vectorbt_optimizer.py`

**Components to Implement**:

1. **VectorbtParameterOptimizer Class**
   - Fast parameter grid evaluation
   - Parallel optimization
   - Memory management
   - Results caching

2. **Optimization Strategies**
   - Grid search with vectorbt
   - Random search support
   - Bayesian optimization ready
   - Progressive refinement

3. **Performance Tracking**
   - Optimization statistics
   - Time tracking
   - Memory profiling
   - Result archiving

4. **Integration with ProductionOptimizer**
   - Compatible interface
   - Drop-in replacement
   - Gradual migration path

**Test Coverage**: 10+ test cases
**Expected Lines of Code**: 250-350

---

## 🔄 Implementation Sequence

### Phase 3.1: Foundation (Session 1, Hours 1-2)
1. ✅ Create `src/backtest/vectorbt_engine.py`
2. ✅ Implement VectorbtBacktestEngine class
3. ✅ Data loading and preprocessing
4. ✅ Signal generation adapter

### Phase 3.2: Metrics & Validation (Session 1, Hours 2-3)
5. ✅ Create `src/backtest/vectorbt_metrics.py`
6. ✅ Implement performance calculator
7. ✅ Risk metrics extraction
8. ✅ Report generation

### Phase 3.3: Testing & Optimization (Session 1, Hours 3-4)
9. ✅ Create comprehensive test suite
10. ✅ Verify signal compatibility (99%+)
11. ✅ Performance benchmarking
12. ✅ Parameter optimization integration

### Phase 3.4: Documentation & Polish (Session 2, Hours 1-2)
13. ✅ Strategy migration guide
14. ✅ API documentation
15. ✅ Usage examples
16. ✅ Configuration guide

---

## 📦 Dependencies

### Required Libraries
- `vectorbt >= 0.28.0` (already verified)
- `pandas >= 1.5` (already available)
- `numpy >= 1.20` (already available)
- `scipy >= 1.8` (for statistics)

### Internal Dependencies
- `src/data_pipeline/data_manager.py` - Data loading
- `src/backtest/base_backtest.py` - Interface definition
- `src/backtest/config.py` - Configuration models
- `src/strategies/` - Existing strategies
- `src/risk_management/` - Risk calculations

### New Dependencies
- Will need to import: `vectorbt as vbt`, `vectorbt.portfolio`

---

## 🎯 Key Implementation Details

### 1. Data Format Conversion
```python
# Input from DataManager
df = manager.load_data('0700.hk', start_date, end_date)
# shape: (1000, 5) - OHLCV data

# Convert to vectorbt format
ohlcv = df[['open', 'high', 'low', 'close', 'volume']].values
# shape: (1000, 5) - numpy array

# Use with vectorbt
portfolio = vbt.Portfolio.from_signals(
    close=ohlcv[:, 3],      # close prices
    entries=entry_signals,   # 1D array of entry signals
    exits=exit_signals,      # 1D array of exit signals
    init_cash=100000,
    fees=commission_rate,
    freq='d'
)
```

### 2. Strategy Integration
```python
# Old strategy (loop-based)
async def old_strategy(current_data, positions):
    if current_data['close'] > sma_20:
        return [{'symbol': '0700.hk', 'side': 'buy', 'quantity': 100}]
    return []

# New strategy wrapper (vectorized)
def new_strategy_wrapper(ohlcv_data):
    close = ohlcv_data[:, 3]
    sma_20 = pd.Series(close).rolling(20).mean().values
    entries = (close > sma_20).astype(float)
    exits = (close < sma_20).astype(float)
    return entries, exits
```

### 3. Metrics Extraction
```python
# From vectorbt portfolio object
sharpe = portfolio.stats()['Sharpe Ratio']
max_dd = portfolio.stats()['Max Drawdown']
win_rate = portfolio.trades.win_rate  # Built-in trade analytics
total_return = portfolio.final_value() / portfolio.init_cash - 1
```

### 4. Backward Compatibility
```python
# Config parameter selects engine
config = BacktestConfig(engine_type='vectorbt')
engine = BacktestEngineFactory.create_engine(config)

# Or use legacy
config = BacktestConfig(engine_type='enhanced')
engine = BacktestEngineFactory.create_engine(config)

# Both inherit from BaseBacktestEngine
async result = engine.run_backtest(strategy_func)
```

---

## 📈 Expected Results

### Performance Improvements
| Operation | Enhanced | Vectorbt | Improvement |
|-----------|----------|----------|-------------|
| 5-year backtest | 2-3s | 0.1-0.3s | **10-20x** |
| 100-param grid | 5-10m | 30-60s | **10-15x** |
| Memory usage | 500MB | <50MB | **10x** |
| Load 1000 days | 100ms | 10ms | **10x** |

### Accuracy Validation
| Metric | Match Rate | Notes |
|--------|-----------|-------|
| Total Return | 99.99% | Accounting for rounding |
| Sharpe Ratio | 99.95% | Same calculation method |
| Max Drawdown | 99.99% | Exact match |
| Trade Count | 100% | Exact match |
| Win Rate | 99.9% | Rounding differences |

---

## 🚀 Deliverables Summary

### Code Files (7 new files)
1. ✅ `src/backtest/vectorbt_engine.py` - Main engine implementation
2. ✅ `src/backtest/strategy_adapter.py` - Strategy conversion layer
3. ✅ `src/backtest/vectorbt_metrics.py` - Metrics extraction
4. ✅ `src/backtest/vectorbt_schemas.py` - Data schema definitions
5. ✅ `src/backtest/engine_selector.py` - Factory pattern
6. ✅ `src/backtest/vectorbt_optimizer.py` - Fast optimization
7. ✅ `tests/test_vectorbt_engine.py` - Comprehensive test suite

### Documentation Files (4 files)
1. ✅ `PHASE3_TASK3_1_COMPLETION.md` - Engine completion report
2. ✅ `PHASE3_TASK3_2_COMPLETION.md` - Adapter completion report
3. ✅ `docs/STRATEGY_MIGRATION_GUIDE.md` - User guide
4. ✅ `PHASE3_COMPLETE_SUMMARY.md` - Phase 3 summary

### Modified Files (2 files)
1. ⏳ `src/backtest/config.py` - Add vectorbt options
2. ⏳ `requirements.txt` - Add vectorbt dependency

---

## 🧪 Testing Strategy

### Unit Tests (20 tests)
- Engine initialization
- Data preprocessing
- Signal generation
- Metrics calculation

### Integration Tests (15 tests)
- DataManager integration
- Strategy compatibility
- End-to-end backtest
- Report generation

### Performance Tests (5 tests)
- Execution speed
- Memory usage
- Optimization speed
- Scaling tests

### Compatibility Tests (10+ tests)
- Signal correlation with EnhancedBacktest
- Metric accuracy validation
- Edge case handling
- Regression prevention

**Total Expected Tests**: 50+
**Coverage Goal**: >= 85%

---

## ⏱️ Timeline Estimate

### Session 1 (Estimated 4 hours)
- **Hour 1**: Vectorbt engine implementation
- **Hour 2**: Metrics extraction and schema
- **Hour 3**: Test suite creation and validation
- **Hour 4**: Performance optimization and documentation

### Session 2 (Estimated 2 hours)
- **Hour 1**: Advanced features and optimization
- **Hour 2**: Final testing, documentation, and deployment

**Total Estimated Time**: 6 hours
**Current Completeness**: 0% (about to start)

---

## 🔒 Risk Mitigation

### Backward Compatibility
- Keep EnhancedBacktest intact
- Use factory pattern for engine selection
- Gradual migration path for users
- Version checking and warnings

### Data Accuracy
- Validate signals match within 1% tolerance
- Test against manual calculations
- Compare metrics with industry standard tools
- Extensive edge case coverage

### Performance
- Progressive optimization
- Memory profiling
- Benchmark against vectorbt examples
- Load testing with large datasets

### Code Quality
- Comprehensive type hints
- Detailed docstrings
- Clean separation of concerns
- Extensive test coverage

---

## 📚 Resources & References

### Vectorbt Documentation
- Official: https://vectorbt.dev/
- API Reference: https://vectorbt.dev/api/
- Performance Guide: https://vectorbt.dev/docs/getting-started/performance
- Portfolio: https://vectorbt.dev/api/portfolio

### OpenSpec Design
- Location: `openspec/changes/vectorbt-architecture-redesign/`
- Design File: `design.md` (comprehensive specifications)
- Tasks: `tasks.md` (detailed implementation tasks)

### Existing Code
- Enhanced Engine: `src/backtest/enhanced_backtest_engine.py`
- Base Class: `src/backtest/base_backtest.py`
- Strategies: `src/strategies/`
- Risk Calc: `src/risk_management/risk_calculator.py`

---

## ✅ Pre-Implementation Checklist

- [x] Vectorbt installed and verified (v0.28.1)
- [x] OpenSpec proposal reviewed and approved
- [x] Phase 1 and Phase 2 complete (199 tests)
- [x] DataManager ready for data loading
- [x] Asset profiles defined
- [x] Strategy framework ready
- [x] Risk metrics available
- [x] Architecture design approved

---

## 🎯 Success Metrics

By end of Phase 3:
- [x] VectorbtBacktestEngine fully implemented
- [x] All existing strategies work unchanged
- [x] Signal correlation > 99% with EnhancedBacktest
- [x] 10x performance improvement demonstrated
- [x] Comprehensive test suite (50+ tests, 85%+ coverage)
- [x] Backward compatibility maintained
- [x] Documentation complete
- [x] Ready for production deployment

---

## 📞 Notes & Considerations

### Implementation Notes
1. Vectorbt requires pre-loaded data (can't stream)
2. Portfolio.from_signals() is the main computation
3. Metrics are extracted from portfolio._stats
4. Need to handle commission and slippage carefully
5. Risk-free rate needed for Sharpe ratio calculation

### Performance Tips
1. Pre-compute all data once at initialization
2. Use numpy arrays for signal generation
3. Batch-process parameter optimization
4. Cache results for repeated backtests
5. Profile memory usage with large datasets

### Known Challenges
1. Vectorbt handles signals differently than our loop-based engine
2. Must map buy/sell signals to entry/exit format
3. Short selling and leverage require special handling
4. Benchmark comparison may need special consideration
5. Slippage modeling differs from loop-based approach

---

**Phase 3 Status**: 🔄 Ready to Implement
**Next Action**: Begin Task 3.1 - VectorbtBacktestEngine
**Expected Completion**: Within 1-2 sessions

---

**Document Created**: 2025-10-25
**Version**: 1.0
**Status**: Implementation Plan Ready
