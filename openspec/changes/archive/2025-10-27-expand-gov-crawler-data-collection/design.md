# Design Document: Gov Crawler Data Collection Expansion

## Architecture Overview

This document outlines the technical design decisions for expanding the gov_crawler system to collect real alternative data from 9 distinct Hong Kong data sources.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Explorer (Chrome MCP)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Site A      │  │  Site B      │  │  Site C      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Discovery & Analysis Engine                 │
│  • API Detection    • Format Analysis   • Quality Scoring│
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                Real Data Adapters Layer                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │ HIBOR  │ │Property│ │ Retail │ │ GDP    │ │ Visitor│ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │ Trade  │ │Traffic │ │  MTR   │ │ Border │           │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Data Quality Assurance Layer                │
│  • Validation   • Anomaly Detection   • Quality Scoring │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│            Unified Data Collection System                │
│  • Parallel Processing  • Error Handling  • Caching     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│            Quant Trading System Integration              │
│  • Data API    • Signal Generation   • Backtesting      │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Chrome MCP Integration for Web Exploration

**Decision**: Use Chrome DevTools MCP for automated web exploration

**Rationale**:
- **Pros**: Real browser automation, JavaScript rendering support, accurate DOM analysis
- **Cons**: Higher resource consumption, slower than HTTP-only approaches
- **Why this approach**: Many Hong Kong government sites use JavaScript for data loading. Chrome MCP ensures we capture all dynamically loaded content.

**Alternative Considered**: HTTP-only exploration with requests/BeautifulSoup
- **Rejected because**: Would miss AJAX-loaded data, less accurate for complex sites

**Implementation**:
```python
class WebExplorer:
    def __init__(self):
        self.browser = ChromeMCPBrowser()

    async def explore_site(self, url: str):
        # Use Chrome MCP to navigate and analyze
        page = await self.browser.new_page()
        await page.goto(url)
        # Full page analysis including dynamic content
```

### 2. Adapter Pattern with Async Support

**Decision**: Extend existing BaseAdapter pattern with async capabilities

**Rationale**:
- **Pros**: Consistent interface, easy testing, familiar for team
- **Cons**: Need to manage async complexity
- **Why this approach**: Maintains consistency with existing codebase while adding real-time capabilities

**Design**:
```python
class RealDataAdapter(BaseAdapter):
    async def fetch_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Async data fetching with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return await self._fetch_with_retry(start_date, end_date)
            except TransientError as e:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        raise DataCollectionError("Max retries exceeded")
```

### 3. Parallel Data Collection

**Decision**: Run all 9 adapters concurrently for faster data collection

**Rationale**:
- **Pros**: Reduces total collection time from ~135 seconds (15 sec/adapter) to ~30 seconds
- **Cons**: Higher memory usage, potential rate limit issues
- **Why this approach**: Speed is critical for daily updates, modern systems can handle concurrent requests

**Implementation**:
```python
async def collect_all_data():
    tasks = [
        hibor_adapter.fetch_data(...),
        property_adapter.fetch_data(...),
        # ... 7 more adapters
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Mitigation for Rate Limits**:
- Implement per-adapter rate limiting
- Stagger requests for APIs from same domain
- Use semaphore to limit concurrent requests to 3-5

### 4. Configuration Management Strategy

**Decision**: YAML configuration + Environment Variables

**Rationale**:
- **Pros**: Human-readable config, environment-specific values, security for API keys
- **Cons**: Two places to manage config
- **Why this approach**: Standard practice in Python, separates code from config

**Config Structure**:
```yaml
# config.yaml
crawler:
  timeout: 30
  max_retries: 3

datasets:
  hibor:
    enabled: true
    update_interval: 86400
    api_endpoint: "${HIBOR_API_ENDPOINT}"
    api_key_env: "HIBOR_API_KEY"
```

**API Keys**: Loaded exclusively from environment variables
```python
api_key = os.getenv(config['api_key_env'])
if not api_key:
    raise ConfigurationError(f"API key not found: {config['api_key_env']}")
```

### 5. Data Quality Assurance Approach

**Decision**: Multi-layered validation with automated scoring

**Rationale**:
- **Pros**: Catches errors early, provides measurable quality metrics
- **Cons**: Additional processing overhead (~2-5 seconds per adapter)
- **Why this approach**: Data quality is critical for trading decisions

**Validation Layers**:
1. **Schema Validation**: Check data types and required fields
2. **Range Validation**: Detect outliers and impossible values
3. **Temporal Validation**: Ensure date ranges are valid and complete
4. **Cross-Validation**: Compare with historical patterns
5. **Source Validation**: Verify data matches source expectations

**Quality Scoring**:
```python
@dataclass
class QualityReport:
    completeness: float  # 0-1 (no missing values)
    accuracy: float      # 0-1 (validated against rules)
    timeliness: float    # 0-1 (data is current)
    consistency: float   # 0-1 (format and values consistent)
    overall: float       # Weighted average

    def is_acceptable(self) -> bool:
        return self.overall >= 0.8  # 80% threshold
```

### 6. Error Handling Strategy

**Decision**: Granular error classification with graceful degradation

**Rationale**:
- **Pros**: Some data is better than none, can recover from transient failures
- **Cons**: Complex error handling logic
- **Why this approach**: Quant system can function with partial data

**Error Categories**:

```python
class DataCollectionError(Exception):
    """Base exception for all data collection errors"""

class TransientError(DataCollectionError):
    """Temporary errors (network timeouts, API limits) - retryable"""

class PermanentError(DataCollectionError):
    """Permanent errors (invalid API key, wrong endpoint) - not retryable"""

class DataQualityError(DataCollectionError):
    """Data quality below threshold - retry collection if possible"""
```

**Handling Strategy**:
- **Transient**: Retry with exponential backoff (max 3 attempts)
- **Permanent**: Log error, mark adapter as failed, continue with others
- **Partial Data**: Accept and flag incomplete datasets
- **All Failed**: Raise alert, use cached data if available

### 7. Storage and Caching Strategy

**Decision**: Layered storage (raw/processed/metadata) with intelligent caching

**Rationale**:
- **Pros**: Preserves raw data, allows reprocessing, tracks data lineage
- **Cons**: More disk space usage (~10-15% overhead)
- **Why this approach**: Supports debugging, analysis, and data lineage tracking

**Storage Structure**:
```
data/
├── raw/                    # Original data from sources
│   ├── hibor_20251027.json
│   └── hibor_20251027_metadata.json
├── processed/              # Cleaned and normalized data
│   ├── hibor_20251027.csv
│   └── hibor_20251027_summary.json
└── cache/                  # Frequently accessed processed data
    └── hibor_latest.csv
```

**Caching Strategy**:
- **Raw Data**: Cache for 90 days (allows reprocessing)
- **Processed Data**: Cache for 30 days (recent data most valuable)
- **Cache Invalidation**: On data source update or quality degradation
- **Cache Size Limit**: 1GB total, LRU eviction

### 8. Integration with Quant Trading System

**Decision**: REST API + Direct Database Integration

**Rationale**:
- **Pros**: Loose coupling, can scale independently
- **Cons**: Additional latency (~50-100ms) for API calls
- **Why this approach**: Clean separation of concerns, quant system doesn't need to know about crawler internals

**API Design**:
```python
@app.get("/api/v1/alternative-data/{symbol}")
async def get_alternative_data(symbol: str, date: str = None):
    """Get alternative data for trading analysis"""
    data = await data_service.get_data(symbol, date)
    return {"status": "success", "data": data}

@app.get("/api/v1/data-quality/{source}")
async def get_data_quality(source: str):
    """Get data quality report for a source"""
    report = await quality_service.get_report(source)
    return report
```

**Database Integration**:
```python
# Direct integration for high-frequency access
class QuantDataAdapter:
    def get_data_direct(self, symbol: str) -> pd.DataFrame:
        """Direct DB access for quant system - faster than API"""
        return db.query("""
            SELECT date, indicator, value
            FROM alternative_data
            WHERE symbol = %s AND date >= %s
        """, (symbol, start_date))
```

## Performance Optimization Strategies

### 1. Async/Await Pattern
- All I/O operations are async
- Concurrent execution of independent operations
- Reduced blocking and context switching

### 2. Connection Pooling
- Reuse HTTP connections across requests
- Configurable pool size (default: 10)
- Automatic cleanup of stale connections

### 3. Data Compression
- Compress JSON data before storage (gzip)
- Reduces storage by ~60-70%
- Minimal CPU overhead for compression/decompression

### 4. Batch Processing
- Fetch multiple data points in single API calls where possible
- Reduces number of HTTP requests by ~40%
- Example: Fetch all HIBOR maturities in one request

### 5. Incremental Updates
- Only fetch data newer than last update
- Reduces API calls by ~80% for daily updates
- Requires tracking last update timestamp per source

## Security Considerations

### 1. API Key Management
- Keys stored in environment variables only
- Never log API keys (even in debug mode)
- Automatic key rotation support
- Separate keys for dev/staging/prod

### 2. Input Validation
- Validate all URLs before making requests
- Sanitize all parameters
- Prevent injection attacks
- Rate limiting to prevent abuse

### 3. Secure Communication
- All API calls over HTTPS/TLS 1.2+
- Certificate validation enabled
- Support for custom CA bundles
- Request signing where required

### 4. Audit Logging
- Log all API calls (without sensitive data)
- Track data quality changes
- Monitor for anomalous access patterns
- 90-day retention for logs

## Monitoring and Observability

### 1. Metrics Collection
```python
# Prometheus metrics
DATA_COLLECTION_SUCCESS = Counter('data_collection_success', 'Source')
DATA_COLLECTION_DURATION = Histogram('data_collection_duration_seconds', 'Source')
DATA_QUALITY_SCORE = Gauge('data_quality_score', 'Source')
API_RATE_LIMIT_HITS = Counter('api_rate_limit_hits', 'Source')
```

### 2. Health Checks
- Per-adapter health checks
- Overall system health endpoint
- Dependency health (database, cache)
- Automated alerting on failures

### 3. Dashboard
- Real-time data collection status
- Data quality trends over time
- API response times
- Error rates by source

## Deployment Considerations

### 1. Environment Separation
- **Dev**: Mock data mode for testing
- **Staging**: Limited real data sources
- **Prod**: All 9 sources active

### 2. Scalability
- Horizontal scaling via multiple worker processes
- Queue-based task distribution
- Stateless adapter design (no shared state)

### 3. Backward Compatibility
- Maintain existing mock data interface
- Graceful fallback to mock if real data fails
- Versioned API for breaking changes
- 6-month deprecation notice for changes

## Testing Strategy

### 1. Unit Tests
- Test each adapter independently
- Mock API responses for CI/CD
- Test error handling paths
- Test data validation logic
- Target: 90% code coverage

### 2. Integration Tests
- Test full data collection pipeline
- Test adapter-to-quant system integration
- Test with real API endpoints (rate-limited)
- Test concurrent execution

### 3. End-to-End Tests
- Full system test with test data
- Data quality validation test
- Performance benchmarking
- Failure recovery testing

## Migration Plan

### Phase 1: Infrastructure (Week 1)
1. Set up adapter framework
2. Implement configuration management
3. Basic error handling

### Phase 2: Adapters (Weeks 2-3)
1. Implement 3 adapters per week
2. Continuous integration testing
3. Quality validation implementation

### Phase 3: Integration (Week 4)
1. Unified collection system
2. Quant system integration
3. End-to-end testing

### Phase 4: Production (Week 5)
1. Deploy to staging
2. Monitor and optimize
3. Production rollout

## Risk Mitigation

### High-Risk Areas

1. **API Rate Limits**
   - Mitigation: Rate limiting, request queuing, multiple API keys
   - Monitoring: Track rate limit hits

2. **Data Quality Degradation**
   - Mitigation: Multi-layer validation, anomaly detection
   - Monitoring: Quality score thresholds

3. **External Dependencies**
   - Mitigation: Multiple data sources per indicator, graceful degradation
   - Monitoring: Dependency health checks

4. **Performance Issues**
   - Mitigation: Async processing, caching, connection pooling
   - Monitoring: Performance metrics dashboard

## Success Metrics

- **Data Collection Success Rate**: > 90%
- **Data Quality Score**: > 4.0/5.0
- **Collection Latency**: < 30 seconds (all 9 sources)
- **System Availability**: > 99% uptime
- **Test Coverage**: > 90%
- **Documentation Coverage**: 100% (all APIs and processes)
