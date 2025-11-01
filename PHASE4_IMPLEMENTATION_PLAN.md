# Phase 4: Backtest Integration Implementation Plan

**Status**: Starting Phase 4
**Date**: 2025-10-18
**Target Completion**: Single Session

---

## Overview

Phase 4 extends the BacktestEngine to support alternative data signals, creating a comprehensive framework for testing trading strategies that combine price-based and alternative data indicators.

---

## Architecture

### Current BacktestEngine Flow
```
Data Loading
    ↓
Daily Loop (process_trading_day)
    ↓
Strategy Signal Generation
    ↓
Trade Execution
    ↓
Position Updates
    ↓
Portfolio Metrics
    ↓
Results
```

### Phase 4 Enhanced Flow
```
Data Loading (with alt data)
    ↓
Daily Loop (process_trading_day)
    ↓
Price Signals Generation
    ↓
Alternative Data Signals Generation ← NEW
    ↓
Signal Merging ← NEW
    ↓
Trade Execution (with signal tracking) ← EXTENDED
    ↓
Position Updates
    ↓
Portfolio Metrics (with signal attribution) ← EXTENDED
    ↓
Signal Validation ← NEW
    ↓
Results (with alt data comparison)
```

---

## Phase 4 Tasks

### 4.1 Extend BacktestEngine for Alternative Data

**File**: `src/backtest/enhanced_backtest_engine.py`

**Changes**:
1. Add `alternative_data` parameter to `run_backtest()`
2. Add signal merging logic in `_process_trading_day()`
3. Track signal sources in Trade records
4. Extend metrics to include signal attribution

**Key Methods**:
```python
async def run_backtest_with_alt_data(
    self,
    strategy_func,
    alt_data_signals: Dict[str, pd.Series]
) -> BacktestResult:
    """Run backtest with alternative data signals"""

async def _merge_signals(
    self,
    price_signal: Dict[str, Any],
    alt_signal: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Merge price and alternative data signals"""

def _track_signal_source(
    self,
    trade: Trade,
    source: str  # 'price', 'alt_data', 'combined'
) -> None:
    """Track which signal triggered the trade"""
```

---

### 4.2 Create AltDataSignalStrategy

**File**: `src/strategies/alt_data_signal_strategy.py` (NEW)

**Features**:
- Combines price signals with HIBOR/visitor arrivals/other indicators
- Configurable signal weights
- Confidence scoring based on correlation strength
- Position sizing based on signal confidence

**Key Class**:
```python
class AltDataSignalStrategy:
    def __init__(self, price_weight=0.6, alt_weight=0.4):
        """
        Args:
            price_weight: Weight for price-based signals (0-1)
            alt_weight: Weight for alternative data signals (0-1)
        """

    def generate_signal(
        self,
        price_signal: float,
        alt_signal: float,
        correlation: float,
        confidence: float
    ) -> Dict[str, Any]:
        """Generate combined signal with confidence"""

    def calculate_position_size(
        self,
        base_size: float,
        confidence: float
    ) -> float:
        """Adjust position size based on signal confidence"""
```

---

### 4.3 Create CorrelationStrategy

**File**: `src/strategies/correlation_strategy.py` (NEW)

**Features**:
- Detects correlation breakdowns (mean reversion signals)
- Generates signals when correlation deviates from norm
- Tracks correlation regime changes

**Key Class**:
```python
class CorrelationStrategy:
    def __init__(self, deviation_threshold=2.0):
        """
        Args:
            deviation_threshold: Std devs from mean correlation to trigger signal
        """

    def detect_correlation_breakdown(
        self,
        current_correlation: float,
        mean_correlation: float,
        std_correlation: float
    ) -> Optional[Dict[str, Any]]:
        """Generate signal on correlation deviation"""

    def detect_regime_change(
        self,
        rolling_correlation: pd.Series
    ) -> List[Dict[str, Any]]:
        """Identify correlation regime transitions"""
```

---

### 4.4 Create MacroHedgeStrategy

**File**: `src/strategies/macro_hedge_strategy.py` (NEW)

**Features**:
- Portfolio hedging based on macro indicators
- Dynamic position sizing on macro alerts
- Hedge instrument selection

**Key Class**:
```python
class MacroHedgeStrategy:
    def __init__(self, hedge_ratio=0.2):
        """
        Args:
            hedge_ratio: Fraction of portfolio to hedge (0-1)
        """

    def generate_hedge_signal(
        self,
        macro_indicator: float,
        threshold: float
    ) -> Dict[str, Any]:
        """Generate hedging signal when macro alert triggered"""

    def select_hedge_instrument(
        self,
        correlation: float
    ) -> str:
        """Select hedge instrument (put option, short, etc)"""
```

---

### 4.5 Extend Performance Metrics

**File**: `src/backtest/strategy_performance.py` (MODIFY)

**New Metrics**:
- Signal accuracy (% correct predictions)
- Signal contribution to Sharpe ratio
- Signal frequency and win rates
- Signal breakdown by type (price vs alt data)

**Key Methods**:
```python
def calculate_signal_accuracy(trades: List[Trade]) -> float:
    """Percentage of trades with positive PnL"""

def calculate_signal_attribution(
    trades: List[Trade],
    sharpe_overall: float
) -> Dict[str, float]:
    """Break down Sharpe contribution by signal type"""

def generate_signal_breakdown(trades: List[Trade]) -> Dict[str, Any]:
    """Stats on price vs alt data signal performance"""
```

---

### 4.6 Signal Validation Framework

**File**: `src/backtest/signal_validation.py` (NEW)

**Features**:
- Out-of-sample testing
- Signal stability analysis
- Overfitting detection
- Statistical significance validation

**Key Class**:
```python
class SignalValidator:
    def split_data(
        self,
        data: pd.DataFrame,
        train_ratio=0.7
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split into train/test sets"""

    def detect_overfitting(
        self,
        train_metrics: Dict,
        test_metrics: Dict
    ) -> bool:
        """Identify overfitting patterns"""

    def validate_statistical_significance(
        self,
        trades: List[Trade]
    ) -> Dict[str, float]:
        """Test if results are statistically significant"""
```

---

### 4.7 Dashboard Integration

**File**: `src/dashboard/api_routes.py` (MODIFY)

**New Endpoints**:
```python
@app.get("/api/backtest/{id}/alt-data-analysis")
async def get_alt_data_analysis(id: str):
    """Compare with/without alt data signals"""

@app.get("/api/backtest/{id}/signal-breakdown")
async def get_signal_breakdown(id: str):
    """Get signal attribution breakdown"""

@app.post("/api/backtest/{id}/validate-signals")
async def validate_signals(id: str):
    """Run signal validation tests"""
```

---

## Implementation Sequence

### Part 1: Core Engine (4.1)
1. ✅ Review BacktestEngine architecture
2. Add alt data parameter support
3. Implement signal merging logic
4. Track signal sources in trades
5. Test with sample data

### Part 2: Strategies (4.2-4.4)
1. Implement AltDataSignalStrategy
2. Implement CorrelationStrategy
3. Implement MacroHedgeStrategy
4. Create unit tests for each
5. Test backtest integration

### Part 3: Metrics & Validation (4.5-4.6)
1. Extend performance metrics calculation
2. Implement SignalValidator class
3. Add out-of-sample testing
4. Add overfitting detection
5. Test validation framework

### Part 4: Dashboard (4.7)
1. Create new API endpoints
2. Implement data aggregation
3. Add visualization support
4. Integration testing

---

## Data Structures

### SignalMergeResult
```python
class SignalMergeResult:
    price_signal: float          # -1 to +1
    alt_signal: float            # -1 to +1
    merged_signal: float         # Combined signal
    confidence: float            # 0 to 1
    signal_source: str           # 'price', 'alt_data', 'combined'
    strength: str                # 'STRONG', 'MODERATE', 'WEAK'
```

### SignalTradeMap
```python
class SignalTradeMap:
    trade_id: str
    signal_type: str             # 'price_only', 'alt_data_only', 'combined'
    price_signal_strength: float
    alt_signal_strength: float
    confidence: float
    correlation_at_trade: float
    pnl: float
    signal_accuracy: bool        # True if profitable
```

---

## Testing Strategy

### Unit Tests (each strategy)
- Signal generation correctness
- Confidence scoring validation
- Position sizing calculations
- Edge case handling

### Integration Tests
- Full backtest with alt data
- Signal merging in daily loop
- Portfolio metrics calculation
- Trade tracking

### Validation Tests
- Out-of-sample validation
- Overfitting detection
- Statistical significance

---

## Success Criteria

✅ BacktestEngine accepts alternative data signals
✅ Signals merge correctly with price signals
✅ Trade sources tracked accurately
✅ All 3 strategies generate valid signals
✅ Performance metrics include signal attribution
✅ Signal validation framework operational
✅ Dashboard shows alt data comparison
✅ All tests passing (target 90%+)
✅ No performance degradation

---

## Estimated Effort

- 4.1 Engine Extension: 3-4 hours
- 4.2 AltDataStrategy: 2-3 hours
- 4.3-4.4 Strategies: 2-3 hours
- 4.5 Metrics: 1-2 hours
- 4.6 Validation: 2-3 hours
- 4.7 Dashboard: 1-2 hours
- Testing & Integration: 2-3 hours
- **Total**: 15-20 hours

---

## Dependencies

- Phase 3 (Correlation Analysis) - ✅ Complete
- Phase 2 (Data Pipeline) - ✅ Complete
- BacktestEngine (existing) - ✅ Available
- DataService (existing) - ✅ Available

---

**Next**: Begin implementing 4.1 (BacktestEngine Extension)
