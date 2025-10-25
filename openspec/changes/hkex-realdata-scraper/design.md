# Design: HKEX Real Data Web Scraper

**ID**: `hkex-realdata-scraper`
**Document Type**: DESIGN
**Created**: 2025-10-18

---

## Architecture Overview

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                      HKEX Data System                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Data Source Layer                                │   │
│  │    • HKEX Official Website                          │   │
│  │    • Alternative Financial Data Providers           │   │
│  │    • Real-time Data APIs                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 2. Web Scraper Engine                               │   │
│  │    • HTTP/HTTPS requests (requests library)         │   │
│  │    • HTML parsing (BeautifulSoup)                   │   │
│  │    • JavaScript rendering (Selenium) - optional     │   │
│  │    • Async support (asyncio)                        │   │
│  │    • Rate limiting & retry logic                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 3. Data Parser & Validator                          │   │
│  │    • Extract OHLCV from HTML/JSON                   │   │
│  │    • Validate data types & ranges                   │   │
│  │    • Check price logic consistency                  │   │
│  │    • Handle missing/corrupt records                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 4. Data Storage Layer                               │   │
│  │    • SQLite database (historical)                   │   │
│  │    • CSV exports                                    │   │
│  │    • Incremental updates                            │   │
│  │    • Data versioning                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 5. Integration Layer                                │   │
│  │    • Backtest Engine Integration                    │   │
│  │    • Pytest Real Data Fixtures                      │   │
│  │    • Real-time Monitoring                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐
│   Raw Data   │
│  (HTML/JSON) │
└──────┬───────┘
       ↓
┌────────────────────┐
│   Web Scraper      │
│ (Download & Parse) │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│  Data Validator    │
│ (Quality Checks)   │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Data Transformer   │
│ (Normalize Format) │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│  SQLite Database   │
│ (Historical Data)  │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Backtest Engine    │
│ (Use Real Data)    │
└────────────────────┘
```

---

## Detailed Design

### 1. Web Scraper Engine

**File**: `src/scrapers/hkex_web_scraper.py`

```python
class HKEXWebScraper:
    """
    Web scraper for HKEX real-time and historical data
    Uses direct HTTP requests instead of external libraries
    """

    # Configuration
    API_ENDPOINTS = {
        'hkex_official': 'https://www.hkex.com.hk/...',
        'alternative_source_1': 'https://...',
        'alternative_source_2': 'https://...',
    }

    # Methods
    async def scrape_historical_data(symbol, years=5)
    async def scrape_daily_data(symbol)
    async def scrape_realtime_data(symbols: List[str])
    def parse_html(html_content, parser_config)
    def parse_json(json_content, parser_config)
    def validate_data_record(record) -> bool
```

### 2. Data Storage Layer

**File**: `src/database/hkex_datastore.py`

```python
class HKEXDataStore:
    """
    Local SQLite database for HKEX historical data
    """

    # Schema
    CREATE TABLE IF NOT EXISTS hkex_data (
        id INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL,
        date DATE NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        source TEXT,
        scraped_at DATETIME,
        UNIQUE(symbol, date)
    );

    # Methods
    async def insert_data(symbol, date, ohlcv)
    async def get_data_range(symbol, start_date, end_date)
    async def update_daily_data(symbol)
    def export_to_csv(symbol, filename)
```

### 3. Data Parser & Validator

**File**: `src/scrapers/data_validator.py`

```python
class DataValidator:
    """
    Validates scraped data for quality and consistency
    """

    def validate_price_logic(open, high, low, close) -> bool
        # High >= max(Open, Close)
        # Low <= min(Open, Close)
        # All prices > 0

    def validate_volume(volume) -> bool
        # Volume >= 0
        # No extreme outliers

    def detect_anomalies(data_series) -> List[Anomaly]
        # Detect suspicious price movements
        # Flag duplicate records
        # Identify gaps in dates

    def check_data_completeness(symbol, date_range) -> float
        # Percentage of trading days with data
```

### 4. Real Data Fixtures

**File**: `tests/conftest_real_data_live.py`

```python
@pytest.fixture
async def real_hkex_tencent_live():
    """
    Live Tencent data from database
    NOT synthetic/mock data
    """
    datastore = HKEXDataStore()
    df = await datastore.get_data_range(
        "0700.hk",
        date.today() - timedelta(days=365),
        date.today()
    )
    return df

@pytest.fixture
async def real_hkex_portfolio_live():
    """
    Portfolio of 5 major HKEX stocks
    All real historical data
    """
    datastore = HKEXDataStore()
    symbols = ["0700.hk", "0388.hk", "1398.hk", "0939.hk", "3988.hk"]
    portfolio = {}
    for symbol in symbols:
        portfolio[symbol] = await datastore.get_data_range(symbol, ...)
    return portfolio
```

### 5. Data Quality Assurance

```python
class DataQualityChecker:
    """
    Ensures scraped data meets quality standards
    """

    def check_accuracy(symbol) -> QualityReport
        # Compare with multiple sources
        # Calculate deviation percentage
        # Flag discrepancies

    def check_completeness(symbol, date_range) -> ComplenessReport
        # Verify all trading days have data
        # Check for missing records
        # Validate date continuity

    def check_consistency(symbol) -> ConsistencyReport
        # Verify price logic (High >= Close, etc.)
        # Check volume reasonableness
        # Detect outliers
```

---

## Implementation Strategy

### Phase 1: Data Source Discovery
1. Analyze HKEX official website structure
2. Identify alternative data sources
3. Document HTML/API endpoints
4. Create scraper templates for each source

### Phase 2: Core Scraper
1. Implement base scraper class
2. Add HTTP session management
3. Implement retry logic with exponential backoff
4. Add async support for parallel requests
5. Rate limiting and respectful scraping

### Phase 3: Data Persistence
1. Design SQLite schema
2. Implement database connection pool
3. Add incremental update logic
4. Implement data versioning
5. CSV export functionality

### Phase 4: Data Validation
1. Implement price logic validators
2. Add anomaly detection
3. Compare with alternative sources
4. Create quality reporting

### Phase 5: Integration
1. Create real data fixtures
2. Remove all mock data
3. Update backtest engine
4. Validate backtests work correctly

---

## Key Decisions

### Decision 1: HTTP Library
- ✅ **Choice**: `requests` library
- **Reason**: Simpler than async alternatives for initial implementation
- **Alternative**: `aiohttp` for advanced async needs

### Decision 2: Storage
- ✅ **Choice**: SQLite (local database)
- **Reason**: No external dependencies, easy to version control
- **Alternative**: PostgreSQL (if scaling needed)

### Decision 3: Parsing
- ✅ **Choice**: BeautifulSoup for HTML, json library for JSON
- **Reason**: Robust and lightweight
- **Alternative**: Selenium (only if JavaScript rendering needed)

### Decision 4: Data Sources Priority
- ✅ **Primary**: HKEX official website
- ✅ **Secondary**: Alternative financial data providers
- ✅ **Tertiary**: Paid data services (if needed)

---

## Technology Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| HTTP Requests | `requests` | Simple, reliable, standard |
| HTML Parsing | `BeautifulSoup4` | Robust DOM parsing |
| Database | SQLite3 | No external service, local |
| Data Processing | `pandas` | DataFrame support for analysis |
| Async Support | `asyncio` | Python standard library |
| Testing | `pytest` | Already in use |
| Validation | `pydantic` | Type safety |

---

## Error Handling Strategy

```
┌─────────────────────┐
│  Network Error      │ → Retry with backoff
└─────────────────────┘

┌─────────────────────┐
│  Parsing Error      │ → Log & skip record, try alternative source
└─────────────────────┘

┌─────────────────────┐
│  Validation Error   │ → Flag for manual review, don't store
└─────────────────────┘

┌─────────────────────┐
│  Database Error     │ → Rollback transaction, alert operator
└─────────────────────┘

┌─────────────────────┐
│  Rate Limiting      │ → Backoff & retry later
└─────────────────────┘
```

---

## Performance Considerations

### Optimization 1: Parallel Scraping
- Fetch data for 40+ stocks in parallel
- Limit concurrency to 10 requests
- Expected time: ~30 seconds vs 2 minutes sequential

### Optimization 2: Incremental Updates
- Only fetch new trading days
- Cache historical data
- Only update daily after market close

### Optimization 3: Database Indexing
- Index on (symbol, date) for fast queries
- Index on source for data quality tracking

### Optimization 4: Caching
- Cache successful scrapes for 24 hours
- Reduce redundant requests

---

## Scalability

### Current Scope
- 40 major HKEX stocks
- 5 years of historical data
- Daily updates

### Future Enhancements
- All HKEX listed stocks (1000+)
- Minute-level data
- Real-time streaming
- Multiple markets (US, China, etc.)

---

## Monitoring & Maintenance

### Daily Tasks
- Verify data was updated after market close
- Check for parsing errors
- Validate against alternative sources
- Monitor scraper performance

### Weekly Tasks
- Review data quality reports
- Check for website structure changes
- Validate database integrity
- Update documentation

### Monthly Tasks
- Analyze scraping patterns
- Optimize performance
- Plan for new data sources
- Test disaster recovery

---

## Data Quality Metrics

**Target Metrics**:
- **Accuracy**: ± 0.01% price deviation
- **Completeness**: 99.9% of trading days
- **Consistency**: 100% price logic validation
- **Latency**: < 5 minutes after source update
- **Uptime**: 99.5% availability

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Website structure change | High | Medium | Monitor & adapt parsing logic |
| Rate limiting | Medium | Medium | Respectful scraping + delay |
| Data inconsistency | High | Low | Strict validation + verification |
| Network failures | Medium | Low | Retry + offline mode |
| Database corruption | High | Very Low | Regular backups + transactions |

---

## Testing Strategy

### Unit Tests
- Parser correctness
- Validator logic
- Data transformation

### Integration Tests
- End-to-end scraping
- Database operations
- Backtest with real data

### Performance Tests
- Scraping speed
- Query performance
- Memory usage

### Validation Tests
- Data accuracy (vs. alternative sources)
- Data completeness
- Consistency checks

---

## Rollback Plan

If real data integration breaks backtests:

1. **Immediate**: Keep backup copy of mock fixtures
2. **Verification**: Validate new real data against sources
3. **Analysis**: Compare results with yfinance data
4. **Rollback**: Use previous working version
5. **Root Cause**: Fix scraper/validator issues
6. **Retest**: Validate before re-deployment

---

**Design Status**: READY FOR IMPLEMENTATION
**Last Updated**: 2025-10-18

