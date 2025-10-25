# Tasks: Vectorbt-Based Architecture Implementation

**Change ID**: `vectorbt-architecture-redesign`

---

## Phase 1: Foundation & Infrastructure (Weeks 1-2)

### Task 1.1: Install and Verify Vectorbt
**Status**: Pending
**Owner**: Platform Engineer
**Estimate**: 2 hours

**Work**:
1. Install vectorbt: `pip install vectorbt`
2. Verify installation: `python -c "import vectorbt as vbt; print(vbt.__version__)"`
3. Run vectorbt examples from documentation
4. Test performance on sample 5-year dataset (0700.HK)
5. Document any platform-specific issues

**Acceptance Criteria**:
- ✅ vectorbt successfully imported and functional
- ✅ Example backtest runs in < 1 second
- ✅ Performance baseline established
- ✅ Documentation updated in README

**Dependencies**: None

**Parallelizable**: Yes (can run with Task 1.2)

---

### Task 1.2: Design and Create Data Schema Definitions
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 4 hours

**Work**:
1. Create `src/data_pipeline/schemas/` directory
2. Define data models using Pydantic:
   - `OHLCVData` - Standard OHLCV format
   - `RawPriceData` - Raw data from sources
   - `CleanedPriceData` - After cleaning
   - `NormalizedPriceData` - After datetime normalization
3. Add validation rules to each schema
4. Create serialization/deserialization methods
5. Write documentation for each schema

**Files to Create**:
- `src/data_pipeline/schemas/ohlcv.py`
- `src/data_pipeline/schemas/__init__.py`

**Acceptance Criteria**:
- ✅ All schemas defined with Pydantic
- ✅ Validation rules enforced
- ✅ JSON serialization works
- ✅ Unit tests for schema validation pass

**Dependencies**: None

**Parallelizable**: Yes (can run with Task 1.1)

---

### Task 1.3: Implement Asset Profile System
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 3 hours

**Work**:
1. Create `src/data_pipeline/asset_profile.py`
2. Implement `AssetProfile` dataclass with all required fields
3. Create `AssetProfileRegistry` for managing profiles
4. Load profiles from CSV/JSON: `data/asset_profiles.json`
5. Implement profile lookup by symbol
6. Add validation for profile data

**File to Create**:
- `src/data_pipeline/asset_profile.py`

**Sample Profile JSON**:
```json
{
  "0700.HK": {
    "name": "Tencent Holdings",
    "market": "HKEX",
    "currency": "HKD",
    "multiplier": 1.0,
    "min_lot_size": 100,
    "commission_pct": 0.001,
    "slippage_bps": 5
  }
}
```

**Acceptance Criteria**:
- ✅ AssetProfile loads from file
- ✅ Registry retrieves profiles by symbol
- ✅ Commission and slippage calculated correctly
- ✅ Unit tests pass

**Dependencies**: Task 1.2 (schemas)

**Parallelizable**: Partially (depends on schemas)

---

### Task 1.4: Write Data Validation Module
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 3 hours

**Work**:
1. Create `src/data_pipeline/validators.py`
2. Implement validation rules:
   - Required columns (OHLCV)
   - Data type checks (numeric, positive)
   - Price logic (High ≥ Close ≥ Low)
   - Volume checks (positive integers)
   - DateTime checks (monotonic increase)
3. Create custom exceptions for validation failures
4. Add logging for validation errors
5. Write comprehensive unit tests

**Files to Create**:
- `src/data_pipeline/validators.py`

**Sample Validator**:
```python
class OHLCVValidator:
    @staticmethod
    def validate_price_logic(df: pd.DataFrame) -> List[int]:
        """Return indices of invalid rows"""
        invalid_rows = []
        invalid_rows.extend(df[df['High'] < df['Low']].index)
        invalid_rows.extend(df[df['Close'] > df['High']].index)
        invalid_rows.extend(df[df['Close'] < df['Low']].index)
        return invalid_rows
```

**Acceptance Criteria**:
- ✅ All validation rules implemented
- ✅ Custom exceptions raise with helpful messages
- ✅ 100% unit test coverage for validators
- ✅ Documentation with examples

**Dependencies**: Task 1.2 (schemas)

**Parallelizable**: Yes

---

## Phase 2: Data Pipeline (Weeks 2-3)

### Task 2.1: Build Data Cleaning Layer
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 4 hours

**Work**:
1. Create `src/data_pipeline/cleaners.py`
2. Implement `DataCleaner` class with methods:
   - `fill_missing_dates()` - Handle weekends/holidays
   - `detect_outliers()` - Flag suspicious data
   - `interpolate_volumes()` - Handle zero volumes
   - `round_prices()` - Ensure consistent decimal places
3. Create logging for cleaning operations
4. Handle edge cases (first/last bar, gaps)
5. Write integration tests with real data

**Acceptance Criteria**:
- ✅ Missing dates filled correctly
- ✅ Outliers detected and logged
- ✅ No NaN values after cleaning
- ✅ Integration tests pass

**Dependencies**: Task 1.4 (validators)

**Parallelizable**: No (depends on validators)

---

### Task 2.2: Implement DateTime Normalization Layer
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 3 hours

**Work**:
1. Create `src/data_pipeline/datetime_handler.py`
2. Implement `DateTimeNormalizer`:
   - Convert Hong Kong time to UTC
   - Remove non-trading hours
   - Check trading day calendar
   - Ensure UTC timezone consistency
3. Create HKEX holiday calendar
4. Add timezone-aware operations
5. Write tests for different timezones

**File to Create**:
- `src/data_pipeline/datetime_handler.py`

**Acceptance Criteria**:
- ✅ All times converted to UTC
- ✅ Non-trading hours removed
- ✅ Holiday calendar up-to-date
- ✅ Timezone tests pass

**Dependencies**: None (independent)

**Parallelizable**: Yes

---

### Task 2.3: Create Database Layer (SQLAlchemy Models)
**Status**: Pending
**Owner**: Backend Engineer
**Estimate**: 4 hours

**Work**:
1. Create `src/data_pipeline/database.py`
2. Define SQLAlchemy models:
   - `PriceData` - OHLCV records
   - `DataVersionLog` - Audit trail
   - `AssetMetadata` - Asset info
3. Create database migrations
4. Implement CRUD operations
5. Add query optimization (indexes, constraints)
6. Write tests with SQLite in-memory DB

**Models**:
```python
class PriceData(Base):
    __tablename__ = "price_data"
    id: int = Column(Integer, primary_key=True)
    symbol: str = Column(String(10), index=True)
    date: datetime = Column(DateTime, index=True)
    open: float = Column(Float)
    high: float = Column(Float)
    low: float = Column(Float)
    close: float = Column(Float)
    volume: int = Column(Integer)
    source: str = Column(String(50))
    fetched_at: datetime = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('symbol', 'date', 'source'),
        Index('symbol_date', 'symbol', 'date')
    )
```

**Acceptance Criteria**:
- ✅ Models created and validated
- ✅ Migrations run successfully
- ✅ CRUD operations tested
- ✅ Query performance acceptable

**Dependencies**: Task 1.2 (schemas)

**Parallelizable**: No (depends on schemas)

---

### Task 2.4: Implement Data Management Layer
**Status**: Pending
**Owner**: Data Engineer
**Estimate**: 5 hours

**Work**:
1. Create `src/data_pipeline/data_manager.py`
2. Implement `DataManager` class:
   - LRU caching for frequently accessed data
   - Unified query interface
   - Automatic cache invalidation
   - Performance metrics
3. Integrate with database layer
4. Add caching strategy
5. Write integration tests
6. Benchmark cache effectiveness

**Key Methods**:
```python
class DataManager:
    def get_ohlcv(self, symbol, start, end, freq='1d'):
        """Get OHLCV data with caching"""
        pass

    def add_indicator(self, df, name, func):
        """Compute and cache indicator"""
        pass
```

**Acceptance Criteria**:
- ✅ LRU cache working
- ✅ Cache hit rate > 80% in tests
- ✅ Query performance benchmarked
- ✅ Integration tests pass

**Dependencies**: Task 2.3 (database)

**Parallelizable**: No

---

## Phase 3: Backtest Engine (Weeks 3-4)

### Task 3.1: Implement Vectorbt Wrapper Engine
**Status**: Pending
**Owner**: Quant Engineer
**Estimate**: 6 hours

**Work**:
1. Create `src/backtest/vectorbt_engine.py`
2. Implement `VectorbtBacktestEngine` class
3. Implement core methods:
   - `run()` - Execute backtest
   - `compute_metrics()` - Calculate performance stats
   - `get_trades()` - Extract trade details
4. Integration with AssetProfile (commissions, slippage)
5. Result serialization
6. Comprehensive unit tests

**Core Method**:
```python
def run(self, data: pd.DataFrame, signals: pd.Series, initial_cash: float) -> BacktestResult:
    close = data['Close'].values
    entries = signals == 1
    exits = signals == -1

    pf = vbt.Portfolio.from_signals(
        close, entries, exits,
        init_cash=initial_cash,
        fees=self.profile.commission_pct,
        freq='D'
    )

    return BacktestResult(
        total_return=pf.total_return(),
        sharpe_ratio=pf.sharpe_ratio(),
        # ... more metrics
    )
```

**Acceptance Criteria**:
- ✅ Vectorbt integration complete
- ✅ All metrics computed
- ✅ Performance > 10x faster than old engine
- ✅ Results match expected values

**Dependencies**: Task 1.3 (asset profiles), Task 1.1 (vectorbt installed)

**Parallelizable**: No

---

### Task 3.2: Implement Variables Management
**Status**: Pending
**Owner**: Quant Engineer
**Estimate**: 3 hours

**Work**:
1. Create `src/backtest/variable_manager.py`
2. Implement `VariableManager` class
3. Track state during backtest:
   - Current position
   - Entry/exit prices
   - Unrealized P&L
   - Trade count
4. Store intermediate calculations
5. Write unit tests

**Usage**:
```python
vars = VariableManager()
vars.update_state('position', 100)
vars.add_calculation('rsi', 45.2)
```

**Acceptance Criteria**:
- ✅ State tracking accurate
- ✅ Calculations stored correctly
- ✅ Unit tests pass

**Dependencies**: None

**Parallelizable**: Yes

---

### Task 3.3: Implement Parameter Management Layer
**Status**: Pending
**Owner**: Quant Engineer
**Estimate**: 4 hours

**Work**:
1. Create `src/backtest/parameter_manager.py`
2. Implement `ParameterGrid` for parameter combinations
3. Support for different optimization algorithms:
   - Grid Search
   - Random Search
   - Bayesian Optimization
4. Parameter validation
5. Result tracking and storage
6. Unit tests

**Example**:
```python
grid = ParameterGrid(
    rsi_period=[10, 14, 20],
    rsi_upper=[60, 70, 80],
    rsi_lower=[20, 30, 40]
)
for params in grid:
    result = backtest(params)
```

**Acceptance Criteria**:
- ✅ Parameter combinations generated correctly
- ✅ Grid size calculated accurately
- ✅ Results tracked and stored
- ✅ Integration tests pass

**Dependencies**: Task 3.1 (backtest engine)

**Parallelizable**: No

---

### Task 3.4: Migrate Existing Strategies to Vectorbt
**Status**: Pending
**Owner**: Quant Engineer
**Estimate**: 5 hours

**Work**:
1. Update `src/strategies/__init__.py` to use vectorbt
2. Migrate three strategies:
   - RSI Strategy
   - MACD Strategy
   - Bollinger Bands Strategy
3. Ensure signal generation matches old implementation
4. Add vectorbt-specific optimizations
5. Write regression tests

**Expected Change**:
```python
# Old
def generate_signals(self, data):
    rsi = self._calculate_rsi(data['Close'])
    signals = pd.Series(0, index=data.index)
    signals[rsi < self.oversold] = 1
    return signals

# New (leverages vectorbt's built-in TA)
def generate_signals(self, data):
    rsi = vbt.ta.rsi(data['Close'].values, self.period)
    signals = pd.Series(0, index=data.index)
    signals[rsi < self.oversold] = 1
    return signals
```

**Acceptance Criteria**:
- ✅ All three strategies migrated
- ✅ Signals match 99%+ (allowing small numerical differences)
- ✅ Performance improved
- ✅ Regression tests pass

**Dependencies**: Task 3.1 (vectorbt engine)

**Parallelizable**: No

---

## Phase 4: Testing & Validation (Week 4-5)

### Task 4.1: Write Unit Tests for All Layers
**Status**: Pending
**Owner**: QA Engineer
**Estimate**: 8 hours

**Work**:
1. Create `tests/test_data_pipeline.py`:
   - Test cleaners
   - Test validators
   - Test datetime handler
   - Test asset profiles
2. Create `tests/test_data_manager.py`:
   - Test caching
   - Test queries
   - Test performance
3. Create `tests/test_vectorbt_engine.py`:
   - Test metric computation
   - Test signal handling
4. Create `tests/test_parameter_manager.py`:
   - Test grid generation
   - Test result tracking

**Coverage Target**: ≥ 85%

**Acceptance Criteria**:
- ✅ All tests pass
- ✅ Coverage ≥ 85%
- ✅ Edge cases covered
- ✅ No flaky tests

**Dependencies**: All implementation tasks

**Parallelizable**: Partially (can start once code exists)

---

### Task 4.2: Integration Tests - Full Data Flow
**Status**: Pending
**Owner**: QA Engineer
**Estimate**: 6 hours

**Work**:
1. Create `tests/test_integration.py`
2. Test full pipeline:
   - Data fetch → Clean → Normalize → Backtest
3. Use real 1-year dataset for 0700.HK
4. Verify results against known-good baseline
5. Test error handling and recovery

**Test Cases**:
- Normal flow (happy path)
- Missing data scenarios
- Outlier detection
- Weekend/holiday handling
- Multiple assets

**Acceptance Criteria**:
- ✅ All integration tests pass
- ✅ Results match baseline ±1%
- ✅ Error cases handled gracefully
- ✅ Performance within targets

**Dependencies**: All implementation tasks

**Parallelizable**: No

---

### Task 4.3: Performance Benchmarking & Validation
**Status**: Pending
**Owner**: Performance Engineer
**Estimate**: 4 hours

**Work**:
1. Benchmark against old engine:
   - Single backtest speed
   - Parameter grid speed
   - Memory usage
2. Create performance report
3. Validate 10x+ improvement
4. Identify bottlenecks
5. Document optimization opportunities

**Benchmarks to Compare**:
- 5-year daily backtest: Target < 0.3s (from 2-3s)
- 100-parameter grid: Target < 60s (from 5-10 min)
- Memory (1000 days): Target < 50MB (from 500MB)

**Acceptance Criteria**:
- ✅ Vectorbt version 10x faster
- ✅ Memory usage 10x smaller
- ✅ Detailed benchmark report
- ✅ No performance regressions

**Dependencies**: Task 4.2 (integration tests)

**Parallelizable**: No

---

### Task 4.4: Migration Validation & Documentation
**Status**: Pending
**Owner**: Tech Lead
**Estimate**: 4 hours

**Work**:
1. Verify old and new engines produce same signals
2. Run 100-strategy backtests on both engines
3. Compare results (Sharpe, drawdown, etc.)
4. Document migration guide
5. Create troubleshooting guide
6. Update CLAUDE.md and README

**Documentation Files**:
- `VECTORBT_MIGRATION_GUIDE.md`
- `ARCHITECTURE.md` (updated)

**Acceptance Criteria**:
- ✅ Signal correlation > 99%
- ✅ Metric differences < 1%
- ✅ Migration guide complete
- ✅ All docs updated

**Dependencies**: Task 4.3 (benchmarking)

**Parallelizable**: No

---

## Task Dependencies Graph

```
1.1 (Vectorbt)          1.2 (Schemas)           1.3 (Asset Profile)
    ↓                        ↓                           ↓
    └────────┬────────────────┘                         │
             ↓                                           │
         1.4 (Validators)     1.2 ←─────────────────────┘
             ↓
         2.1 (Cleaners)
             ↓
         2.3 (Database)
             ↓
         2.4 (Data Manager)

1.1, 2.2 (DateTime Handler) - Independent
         ↓
     3.1 (Vectorbt Engine) ← 1.3
         ↓
     3.2, 3.3, 3.4 (Strategies, Parameters, Variables)
         ↓
    4.1, 4.2 (Tests) ← All above
         ↓
    4.3 (Benchmarking)
         ↓
    4.4 (Validation)
```

---

## Timeline Summary

| Phase | Duration | Start | End | Key Deliverables |
|-------|----------|-------|-----|------------------|
| 1 | 2 weeks | Week 1 | Week 2 | Vectorbt installed, schemas defined, validation working |
| 2 | 1 week | Week 2 | Week 3 | Data pipeline complete, database migrated |
| 3 | 1 week | Week 3 | Week 4 | Vectorbt engine, strategies migrated |
| 4 | 1 week | Week 4 | Week 5 | Tests passing, performance validated |
| **Total** | **5 weeks** | | | **Production-ready vectorbt system** |

---

## Success Metrics

✅ **Functional**: All tests pass, no broken functionality
✅ **Performant**: 10x+ improvement on key benchmarks
✅ **Maintainable**: Clear layered architecture, comprehensive documentation
✅ **Validated**: Signal correlation > 99% with old system
✅ **Tested**: ≥ 85% code coverage

---

## Rollback Plan

If critical issues discovered:
1. Keep old backtest engine in parallel
2. Add feature flag to switch engines
3. Gradually migrate to new system
4. Maintain data compatibility layer

```python
# Feature flag
USE_VECTORBT = os.getenv('USE_VECTORBT', 'false').lower() == 'true'

if USE_VECTORBT:
    engine = VectorbtBacktestEngine()
else:
    engine = EnhancedBacktestEngine()
```
