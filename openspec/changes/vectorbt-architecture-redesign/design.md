# Design Document: Vectorbt-Based Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE LAYER                          │
│  (Yahoo Finance, HKEX API, Alpha Vantage, HTTP API, CSV)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      DATABASE LAYER                             │
│  (SQLAlchemy ORM, Persistent Storage, Versioning)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              DATA CLEANING LAYER                                │
│  (Validation, Outlier Detection, Missing Data Handling)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│          DATETIME NORMALIZATION LAYER                           │
│  (UTC Conversion, Trading Hours, Holiday Handling)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              ASSET PROFILE LAYER                                │
│  (Metadata: Commission, Slippage, Multiplier, etc.)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              DATA MANAGEMENT LAYER                              │
│  (Caching, Query Interface, Data Access Patterns)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼──────────┐          ┌────────▼─────┐
    │  VARIABLES    │          │   PARAMETER  │
    │  MANAGEMENT   │          │ MANAGEMENT   │
    │  (State,      │          │ (Config,     │
    │   Calcs)      │          │  Grids)      │
    └────┬──────────┘          └────────┬─────┘
         │                              │
    ┌────▼──────────────────────────────▼──────┐
    │   CORE BACKTEST ENGINE (Vectorbt)        │
    │  (Vectorized Portfolio Computation)      │
    └────┬─────────────────────────────────────┘
         │
    ┌────▼──────────────────┐
    │   TRADE LOGIC         │
    │   (Signals → Orders)  │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │   RESULTS & METRICS   │
    │   (Performance Stats) │
    └───────────────────────┘
```

---

## Layer Specifications

### 1. Data Source Layer
**File**: `src/data_pipeline/sources/`

```python
class DataSourceBase(ABC):
    """Abstract base for all data sources"""

    async def fetch_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch OHLCV data with columns: Open, High, Low, Close, Volume"""
        pass
```

**Supported Sources**:
- HKEX HTTP API (primary)
- Yahoo Finance
- Alpha Vantage
- Local CSV/Parquet files
- Alternative data providers

**Output Schema**:
```
Date         Ticker    Open   High   Low    Close  Volume
2025-01-01   0700.HK   100.0  102.0  99.0  101.0  1000000
```

---

### 2. Database Layer
**File**: `src/data_pipeline/database.py`

**SQLAlchemy Models**:
```python
class PriceData(Base):
    """Persistent OHLCV storage"""
    __tablename__ = "price_data"

    id: int = Column(Integer, primary_key=True)
    symbol: str = Column(String(10), index=True)
    date: datetime = Column(DateTime, index=True)
    open: float = Column(Float)
    high: float = Column(Float)
    low: float = Column(Float)
    close: float = Column(Float)
    volume: int = Column(Integer)
    source: str = Column(String(50))  # "yahoo", "hkex", "csv"
    fetched_at: datetime = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('symbol', 'date', 'source'),
        Index('symbol_date', 'symbol', 'date')
    )
```

**Versioning**: Track data mutations
```python
class DataVersionLog(Base):
    timestamp: datetime
    symbol: str
    operation: str  # "insert", "update", "delete"
    old_value: dict
    new_value: dict
```

---

### 3. Data Cleaning Layer
**File**: `src/data_pipeline/cleaners.py`

```python
class DataCleaner:
    """Validates and cleans raw OHLCV data"""

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Check required columns exist"""
        required = {'Open', 'High', 'Low', 'Close', 'Volume'}
        return required.issubset(df.columns)

    def detect_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flag suspicious price movements (e.g., > 20% daily change)"""
        df['is_outlier'] = (
            df['Close'].pct_change().abs() > 0.20
        )
        return df

    def fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing trading days"""
        # Forward-fill or interpolate
        df = df.reindex(
            pd.date_range(df.index.min(), df.index.max(), freq='B')
        ).fillna(method='ffill')
        return df

    def normalize_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure volume is integer"""
        df['Volume'] = df['Volume'].astype(int)
        return df
```

**Validation Rules**:
- High ≥ Low
- High ≥ Close ≥ Low
- Close > 0
- Volume > 0
- No NaN in OHLCV

---

### 4. DateTime Normalization Layer
**File**: `src/data_pipeline/datetime_handler.py`

```python
class DateTimeNormalizer:
    """Standardize all datetime operations"""

    @staticmethod
    def to_utc(dt: datetime, tz: str = "Asia/Hong_Kong") -> datetime:
        """Convert Hong Kong time to UTC"""
        return pd.Timestamp(dt, tz=tz).tz_convert('UTC')

    @staticmethod
    def trading_hours_filter(df: pd.DataFrame) -> pd.DataFrame:
        """Remove non-trading hours data"""
        df['hour'] = df.index.hour
        return df[(df['hour'] >= 9) & (df['hour'] < 16)]

    @staticmethod
    def is_trading_day(date: datetime) -> bool:
        """Check if date is HKEX trading day"""
        # Weekday check: Mon-Fri
        if date.weekday() >= 5:
            return False
        # Holiday check
        hkex_holidays = ['2025-01-01', '2025-02-10']  # Example
        return str(date.date()) not in hkex_holidays
```

---

### 5. Asset Profile Layer
**File**: `src/data_pipeline/asset_profile.py`

```python
@dataclass
class AssetProfile:
    """Metadata for a traded asset"""

    symbol: str              # "0700.HK"
    name: str               # "Tencent Holdings"
    market: str             # "HKEX"
    currency: str           # "HKD"

    # Trading parameters
    multiplier: float = 1.0
    min_lot_size: int = 100
    max_position: float = inf

    # Costs
    commission_fixed: float = 0.0      # HKD per trade
    commission_pct: float = 0.001      # 0.1% of trade value
    slippage_bps: float = 5            # 5 basis points

    @property
    def total_cost_bps(self) -> float:
        """Total trading cost in basis points"""
        return (self.commission_pct * 10000) + self.slippage_bps
```

**Profile Registry**:
```python
class AssetProfileRegistry:
    _profiles = {
        '0700.HK': AssetProfile(...),
        '2800.HK': AssetProfile(...),
        '0388.HK': AssetProfile(...),
    }
```

---

### 6. Data Management Layer
**File**: `src/data_pipeline/data_manager.py`

```python
class DataManager:
    """Central interface for data access with caching"""

    def __init__(self, cache_size: int = 1000):
        self._cache = LRUCache(maxsize=cache_size)
        self._db = SQLAlchemyConnection()

    @lru_cache(maxsize=100)
    def get_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        frequency: str = '1d'
    ) -> pd.DataFrame:
        """Fetch data with automatic caching"""
        cache_key = f"{symbol}_{start}_{end}_{frequency}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        df = self._db.query(symbol, start, end)
        df = self._resample(df, frequency)

        self._cache[cache_key] = df
        return df

    def add_rolling_indicator(
        self,
        df: pd.DataFrame,
        name: str,
        func: Callable
    ) -> pd.DataFrame:
        """Compute and add rolling indicator"""
        df[name] = func(df)
        return df
```

---

### 7. Variables Management Layer
**File**: `src/backtest/variable_manager.py`

```python
class VariableManager:
    """Tracks state and intermediate calculations during backtest"""

    def __init__(self):
        self.state = {
            'cash': 0.0,
            'position': 0.0,
            'entry_price': 0.0,
            'entry_date': None,
            'trades_executed': []
        }
        self.calculations = {}

    def update_state(self, key: str, value: Any) -> None:
        """Update state variable"""
        self.state[key] = value

    def add_calculation(self, name: str, value: Any) -> None:
        """Store intermediate calculation for analysis"""
        if name not in self.calculations:
            self.calculations[name] = []
        self.calculations[name].append(value)
```

---

### 8. Parameter Management Layer
**File**: `src/backtest/parameter_manager.py`

```python
@dataclass
class ParameterGrid:
    """Defines parameter combinations for optimization"""

    rsi_period: list = field(default_factory=lambda: [10, 14, 20])
    rsi_upper: list = field(default_factory=lambda: [60, 70, 80])
    rsi_lower: list = field(default_factory=lambda: [20, 30, 40])

    def __iter__(self):
        """Yield parameter combinations"""
        for period in self.rsi_period:
            for upper in self.rsi_upper:
                for lower in self.rsi_lower:
                    yield {
                        'rsi_period': period,
                        'rsi_upper': upper,
                        'rsi_lower': lower
                    }

    @property
    def total_combinations(self) -> int:
        """Total combinations in grid"""
        return (
            len(self.rsi_period) *
            len(self.rsi_upper) *
            len(self.rsi_lower)
        )
```

---

### 9. Core Backtest Engine (Vectorbt)
**File**: `src/backtest/vectorbt_engine.py`

```python
import vectorbt as vbt

class VectorbtBacktestEngine:
    """Wrapper around vectorbt for CODEX compatibility"""

    def __init__(self, asset_profile: AssetProfile):
        self.profile = asset_profile
        self.portfolio = None

    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        initial_cash: float = 100000
    ) -> BacktestResult:
        """Run vectorized backtest"""

        # Prepare price data
        close = data['Close'].values

        # Convert signals to entries/exits
        entries = signals == 1
        exits = signals == -1

        # Create portfolio
        pf = vbt.Portfolio.from_signals(
            close,
            entries,
            exits,
            init_cash=initial_cash,
            fees=self.profile.commission_pct,
            freq='D'
        )

        # Compute metrics
        return BacktestResult(
            total_return=pf.total_return(),
            annual_return=pf.annualized_return(),
            sharpe_ratio=pf.sharpe_ratio(),
            sortino_ratio=pf.sortino_ratio(),
            max_drawdown=pf.max_drawdown(),
            win_rate=pf.trades.win_rate,
            trades=pf.trades
        )
```

**Vectorbt Features Used**:
- `Portfolio.from_signals()` - Fast signal-based backtesting
- `.sharpe_ratio()` - Risk-adjusted return
- `.max_drawdown()` - Peak-to-trough decline
- `.trades` - Trade execution details
- `.annual_return()` - Annualized performance

---

### 10. Trade Logic Layer
**File**: `src/backtest/trade_logic.py`

```python
class SignalGenerator(ABC):
    """Generates trading signals from data"""

    @abstractmethod
    def generate_signals(
        self,
        data: pd.DataFrame,
        variables: VariableManager
    ) -> pd.Series:
        """Returns pd.Series with values: 1 (buy), -1 (sell), 0 (hold)"""
        pass

class RSISignalGenerator(SignalGenerator):
    """RSI-based signal generation"""

    def __init__(self, period: int = 14, upper: float = 70, lower: float = 30):
        self.period = period
        self.upper = upper
        self.lower = lower

    def generate_signals(self, data, variables):
        rsi = vbt.ta.rsi(data['Close'].values, self.period)

        signals = pd.Series(0, index=data.index)
        signals[rsi < self.lower] = 1   # Buy
        signals[rsi > self.upper] = -1  # Sell

        return signals
```

---

## Data Flow Example

**Step 1: Fetch Raw Data**
```python
source = YahooFinanceSource()
raw_data = await source.fetch_ohlcv('0700.HK', '2020-01-01', '2025-10-24')
# → Raw OHLCV from Yahoo Finance
```

**Step 2: Store in Database**
```python
db_manager.store_price_data(raw_data, source='yahoo')
# → Persisted to PostgreSQL with metadata
```

**Step 3: Clean Data**
```python
cleaner = DataCleaner()
clean_data = cleaner.fill_missing(raw_data)
clean_data = cleaner.detect_outliers(clean_data)
# → Validated, outliers flagged
```

**Step 4: Normalize DateTime**
```python
norm = DateTimeNormalizer()
clean_data.index = clean_data.index.map(norm.to_utc)
clean_data = norm.trading_hours_filter(clean_data)
# → All times UTC, non-trading hours removed
```

**Step 5: Load Asset Profile**
```python
profile = AssetProfileRegistry.get('0700.HK')
# → Commission, slippage, limits loaded
```

**Step 6: Get from Data Manager**
```python
data = data_manager.get_ohlcv('0700.HK', start, end, '1d')
# → Cached, consistent interface
```

**Step 7: Run Backtest with Vectorbt**
```python
engine = VectorbtBacktestEngine(profile)
signals = rsi_strategy.generate_signals(data)
result = engine.run(data, signals)
# → Vectorized computation, < 1 second
```

---

## Migration Path from Current System

### Current Code → New Code

| Current | New | File |
|---------|-----|------|
| `yfinance.download()` | `DataSourceBase` | `sources/` |
| Manual DataFrame storage | SQLAlchemy ORM | `database.py` |
| Ad-hoc cleaning | `DataCleaner` | `cleaners.py` |
| Manual datetime handling | `DateTimeNormalizer` | `datetime_handler.py` |
| Hard-coded costs | `AssetProfile` | `asset_profile.py` |
| Direct queries | `DataManager` | `data_manager.py` |
| Loop-based backtest | `VectorbtBacktestEngine` | `vectorbt_engine.py` |
| Manual trade tracking | `VariableManager` | `variable_manager.py` |
| Fixed parameters | `ParameterGrid` | `parameter_manager.py` |

---

## Testing Strategy

### Unit Tests
- Each layer tested independently
- Mock dependencies
- Test file: `tests/test_data_pipeline.py`

### Integration Tests
- Full data flow: Source → Database → Backtest
- Compare against known-good results
- Test file: `tests/test_integration.py`

### Regression Tests
- Verify new engine produces same signals as old
- Benchmark performance improvements
- Test file: `tests/test_vectorbt_migration.py`

---

## Performance Targets

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Single backtest (5 years) | 2-3 sec | 0.2-0.3 sec | **10x faster** |
| Parameter grid (100 params) | 5-10 min | 30-60 sec | **5-10x faster** |
| Memory (1000-day dataset) | 500MB | 50MB | **10x smaller** |
| Parameter optimization latency | 2+ hours | < 5 minutes | **24x faster** |

---

## Dependencies

**New Requirements**:
```
vectorbt>=0.24.0
```

**Existing (retained)**:
```
pandas>=1.5.0
numpy>=1.23.0
sqlalchemy>=2.0.0
```
