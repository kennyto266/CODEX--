# Design: Alternative Data Framework

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Alternative Data Layer                      │
├─────────────────────────────────────────────────────────────────┤
│
│  ┌──────────────────────────────────────────────────────────┐
│  │           Data Collection Layer                         │
│  ├──────────────────────────────────────────────────────────┤
│  │ • AlternativeDataAdapter (base)                         │
│  │ • HKEXDataCollector (futures, options, market data)     │
│  │ • GovDataCollector (interbank rates, visitor arrivals)  │
│  │ • KaggleDataCollector (curated datasets)                │
│  └──────────────────────────────────────────────────────────┘
│                           ↓
│  ┌──────────────────────────────────────────────────────────┐
│  │           Data Pipeline Layer                           │
│  ├──────────────────────────────────────────────────────────┤
│  │ • DataCleaner (missing values, outliers)                │
│  │ • TemporalAligner (align to trading days)               │
│  │ • DataNormalizer (standardization, scaling)             │
│  │ • QualityScorer (completeness metrics)                  │
│  └──────────────────────────────────────────────────────────┘
│                           ↓
│  ┌──────────────────────────────────────────────────────────┐
│  │        Integration & Analysis Layer                     │
│  ├──────────────────────────────────────────────────────────┤
│  │ • CorrelationAnalyzer (Sharpe, correlation coeff.)      │
│  │ • AlternativeDataService (unified access)              │
│  │ • BacktestEngine extension (alt data signals)           │
│  │ • Dashboard visualization                               │
│  └──────────────────────────────────────────────────────────┘
│                           ↓
│  ┌──────────────────────────────────────────────────────────┐
│  │              Usage in Strategies                        │
│  ├──────────────────────────────────────────────────────────┤
│  │ • AltDataSignalStrategy (multi-signal with alt data)    │
│  │ • CorrelationStrategy (act on high correlation pairs)   │
│  │ • MacroHedgeStrategy (hedge using macro indicators)     │
│  └──────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Alternative Data Adapter Framework

**Base Class: AlternativeDataAdapter**
```python
class AlternativeDataAdapter(BaseAdapter):
    """Alternative data adapter extending base adapter interface."""

    async def fetch_data(
        self,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """Fetch alternative data indicator"""

    async def get_realtime_data(self, indicator_code: str) -> dict:
        """Get latest indicator value"""

    async def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate alternative data quality"""

    async def get_metadata(self, indicator_code: str) -> dict:
        """Get indicator metadata (frequency, units, etc.)"""
```

**Concrete Implementations:**

#### HKEXDataCollector
- **Data Sources**:
  - Futures contract volume (HSI, HHI, MHI)
  - Options open interest and implied volatility
  - Market turnover and activity indices
  - Hang Seng Index composition changes
- **Collection Method**: Web scraping + RSS feeds
- **Update Frequency**: Daily (after market close)
- **Key Indicators**:
  - `hkex_futures_volume`: Total futures volume
  - `hkex_implied_volatility`: Put/call IV
  - `hkex_market_breadth`: Advancing vs declining stocks

#### GovDataCollector
- **Data Sources**:
  - Hong Kong Interbank Offered Rate (HIBOR) - data.gov.hk
  - Visitor arrivals by country - Tourism Board
  - Trade data (imports/exports) - Census Bureau
  - Currency rate movements - Central Bank
- **Collection Method**: API calls + web scraping
- **Update Frequency**: Daily/Weekly
- **Key Indicators**:
  - `hibor_overnight`: Overnight rate
  - `visitor_arrivals`: Monthly arrivals
  - `trade_balance`: Import/export ratio

#### KaggleDataCollector
- **Data Sources**: Pre-downloaded HK economy datasets
- **Key Datasets**:
  - HK real estate prices
  - Manufacturing PMI
  - CRB commodities index
  - Technology sector data
- **Collection Method**: CSV loading + caching
- **Update Frequency**: Weekly/Monthly

### 2. Data Pipeline Layer

**DataCleaner**
```python
class DataCleaner:
    """Handle missing data, outliers, and anomalies."""

    def handle_missing_values(df, method='interpolate'):
        """Linear interpolation for time series gaps"""

    def detect_outliers(df, threshold=3.0):
        """Identify statistical outliers (z-score)"""

    def remove_outliers(df, method='clip'):
        """Remove or cap outliers"""
```

**TemporalAligner**
```python
class TemporalAligner:
    """Align alternative data to trading calendar."""

    def align_to_trading_days(alt_data_df, price_data_df):
        """Resample alt data to trading days
        - Forward fill for lower frequency data
        - Interpolate for intra-day data
        - Drop non-trading dates
        """

    def forward_fill_data(df, max_periods=5):
        """Forward fill with max period limit"""

    def create_lagged_features(df, lags=[1, 5, 21]):
        """Generate lagged indicators for momentum"""
```

**DataNormalizer**
```python
class DataNormalizer:
    """Standardize and scale indicators."""

    def normalize_z_score(df):
        """Z-score normalization: (x - mean) / std"""

    def normalize_min_max(df):
        """Min-max scaling: (x - min) / (max - min)"""

    def normalize_log_returns(df):
        """Log returns: ln(t / t-1)"""
```

**QualityScorer**
```python
class QualityScorer:
    """Calculate data quality metrics."""

    def calculate_completeness(df, min_date, max_date):
        """% of expected data points present"""

    def calculate_staleness(df, expected_frequency):
        """How recent is the data"""

    def calculate_consistency(df, historical_patterns):
        """Compare variance vs expected range"""
```

### 3. Integration Layer

**CorrelationAnalyzer**
```python
class CorrelationAnalyzer:
    """Analyze correlation between alt data and returns."""

    def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
        """Sharpe = (return - rf) / std_dev"""

    def calculate_correlation_matrix(alt_data_df, returns_series):
        """Pearson correlation coefficients"""

    def calculate_rolling_correlation(alt_data, price_data, window=60):
        """Time-varying correlation analysis"""

    def identify_leading_indicators(alt_data, price_data, max_lag=20):
        """Lag correlation to find predictive signals"""

    def generate_correlation_report(symbol, alt_data_dict):
        """Summary statistics and visualizations"""
```

**AlternativeDataService**
```python
class AlternativeDataService:
    """Unified interface to all alternative data sources."""

    async def get_indicator(
        self,
        category: str,  # 'macro', 'market_structure', 'gov'
        indicator_code: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch from appropriate adapter"""

    async def get_multiple_indicators(self, indicators: List[str]):
        """Fetch multiple indicators efficiently"""

    async def get_aligned_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """Return price data + aligned alt data"""

    async def get_correlation_analysis(
        self,
        symbol: str,
        indicators: List[str]
    ) -> Dict:
        """Return Sharpe ratios, correlation coefficients"""
```

### 4. Backtesting Integration

**Enhanced BacktestEngine Changes**
```python
class EnhancedBacktestEngine:
    """Modified to accept alternative data signals."""

    def backtest_with_alt_data(
        self,
        symbol: str,
        strategy_class: Type,
        price_data: pd.DataFrame,
        alt_data: Dict[str, pd.DataFrame],  # NEW
        start_date: date,
        end_date: date,
        initial_capital: float
    ) -> BacktestResult:
        """Extended backtest with alternative data"""

    def calculate_metrics_with_alt_factors(
        self,
        returns: pd.Series,
        alt_data_signal_correlation: float
    ) -> PerformanceMetrics:
        """Include alt data correlation in Sharpe adjustment"""
```

**Strategy Signature Extension**
```python
class Strategy:
    """Base strategy class"""

    def generate_signals(
        self,
        price_data: pd.DataFrame,
        alt_data: Dict[str, pd.DataFrame] = None  # NEW
    ) -> pd.Series:
        """Generate trading signals, optionally using alt data"""

    def calculate_alt_data_score(
        self,
        alt_data: Dict[str, pd.DataFrame]
    ) -> float:
        """Weight alternative data contribution: 0 to 1"""
```

### 5. Dashboard Integration

**New Visualizations**
- Alternative Data Timeline: Charts showing macro indicators over time
- Correlation Heatmap: Alt data vs stock returns correlation matrix
- Sharpe Ratio Comparison: Strategy performance with/without alt data
- Signal Overlay: Price chart with alt data signals overlaid
- Data Quality Report: Completeness and freshness metrics

## Data Flow

```
1. Collection Phase:
   HKEXDataCollector → fetch_data() → raw HKEX futures data
   GovDataCollector → fetch_data() → raw government data
   KaggleDataCollector → fetch_data() → raw economy datasets

2. Pipeline Phase:
   raw data → DataCleaner → handle missing/outliers
             → TemporalAligner → align to trading days
             → DataNormalizer → standardize scales
             → QualityScorer → assess completeness
             → cleaned alt_data

3. Analysis Phase:
   price_data + alt_data → CorrelationAnalyzer
                         → Sharpe ratios
                         → Correlation matrix
                         → Leading indicators
                         → reports

4. Integration Phase:
   price_data + alt_data_signals → Strategy → trading signals
                                 → BacktestEngine → performance metrics

5. Visualization Phase:
   results → Dashboard → charts, heatmaps, reports
```

## Key Design Decisions

### 1. Why extend BaseAdapter?
- Maintains consistency with existing architecture
- Allows reuse of caching, retry, and config mechanisms
- Simplifies registration in DataService

### 2. Why separate pipeline components?
- Single Responsibility: Each component has one job
- Testability: Easy to unit test each transformation
- Configurability: Users can choose which steps to apply
- Reusability: Components can be used independently

### 3. Why temporal alignment is critical?
- Alt data has different frequencies (daily, weekly, monthly)
- Forward fill assumes data stays valid until next update
- Interpolation preserves continuity for correlation analysis
- Prevents look-ahead bias in backtesting

### 4. Why correlation analysis first before ML?
- Establishes interpretable baseline
- Identifies spurious vs genuine relationships
- Helps feature engineering decisions
- More transparent than black-box ML

## Dependencies

- **New**: requests (for web scraping), beautifulsoup4, HKEX API docs
- **Existing**: pandas, numpy, asyncio, pytest
- **Optional**: Kaggle API client for dataset downloads

## Testing Strategy

- Unit tests: Individual adapters, pipeline components
- Integration tests: Full pipeline from collection to analysis
- Mock tests: HKEX/Gov APIs with cached responses
- Backtesting validation: Compare with/without alt data
- Correlation sanity checks: Expected positive/negative relationships
