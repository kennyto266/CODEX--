# Proposal: HKEX Real Data Web Scraper

**ID**: `hkex-realdata-scraper`
**Status**: DRAFT
**Created**: 2025-10-18
**Author**: Claude Code
**Priority**: HIGH

---

## Problem Statement

Current implementation relies on:
1. **Mock data** from pytest fixtures (synthetic data)
2. **Third-party libraries** (yfinance) for real data

**Issues**:
- Mock data doesn't represent real market conditions
- External library dependency creates maintenance burden
- No direct control over data source
- Hidden API changes can break functionality

**Requirement**:
- Implement **real data web scraper** for HKEX stocks
- Use **direct HTTP/Curl** instead of external libraries
- Ensure **data authenticity** and **reliability**
- Avoid all mock/synthetic data

---

## Scope

### In Scope
- ✅ Web scraper for HKEX real-time data
- ✅ Support for major HKEX stocks (40+ stocks)
- ✅ Historical data collection (OHLCV)
- ✅ Real-time price updates
- ✅ Robust error handling and retry logic
- ✅ Data validation and quality checks
- ✅ Local data persistence/caching
- ✅ Replace all mock data with real data

### Out of Scope
- X Alternative data sources (social media sentiment, etc.)
- X Real-time streaming (WebSocket)
- X Advanced data preprocessing (ML features)

---

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────┐
│          Real Data Web Scraper System               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Data Source Discovery                          │
│     └─ HKEX official website analysis              │
│     └─ Alternative financial data providers        │
│                                                     │
│  2. Web Scraper Engine                             │
│     └─ Requests/BeautifulSoup for static pages     │
│     └─ Selenium for JavaScript-rendered pages      │
│     └─ Async support for parallel fetching         │
│                                                     │
│  3. Data Parser & Validator                        │
│     └─ Parse OHLCV data from HTML/JSON             │
│     └─ Validate data quality & accuracy            │
│     └─ Handle missing/corrupt data                 │
│                                                     │
│  4. Local Storage & Caching                        │
│     └─ SQLite database for historical data         │
│     └─ CSV export capability                       │
│     └─ Automatic cleanup of old data               │
│                                                     │
│  5. Backtest Integration                           │
│     └─ Replace mock fixtures with real data        │
│     └─ Real backtest execution                     │
│     └─ Verify strategy performance on real data    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **HKEX Data Discovery** (New)
- Analyze HKEX official website
- Identify available data sources
- Document data access points
- Handle authentication if needed

#### 2. **Web Scraper** (New)
- `src/scrapers/hkex_web_scraper.py`
- Support multiple data sources
- Async parallel scraping
- Automatic retry with backoff

#### 3. **Data Persistence** (New)
- `src/database/hkex_datastore.py`
- SQLite for historical data
- Incremental updates
- Data versioning

#### 4. **Real Data Fixtures** (Modified)
- `tests/conftest_real_data.py`
- Remove synthetic data generation
- Load from actual database
- Ensure data freshness

#### 5. **Backtest Engine** (Modified)
- Use only real data
- Remove mock data option
- Validate against real market conditions

---

## Requirements

### Functional Requirements

#### FR-001: Scrape Historical Data
- System shall collect 5+ years of historical HKEX data
- Support OHLCV (Open, High, Low, Close, Volume)
- Accuracy: ±0.01% price deviation
- Complete trading data (no gaps for trading days)

#### FR-002: Real-Time Data Updates
- System shall update stock prices daily after market close
- Support 40+ major HKEX stocks
- Update latency: < 5 minutes after source update

#### FR-003: Data Validation
- Validate price logic: High ≥ Low, Close ≤ High, Close ≥ Low
- Detect outliers and anomalies
- Flag suspicious data for review

#### FR-004: Local Persistence
- Store data in local database
- Support incremental updates
- Enable offline backtesting

#### FR-005: Backtest Integration
- Replace all mock data with real data
- Run backtests only on real historical data
- Track data source & collection date

### Non-Functional Requirements

#### NFR-001: Performance
- Scrape 5 years of data in < 60 seconds
- Update daily data in < 30 seconds
- Database queries < 1 second

#### NFR-002: Reliability
- 99% uptime for data collection
- Automatic retry on failures
- Data backup & recovery

#### NFR-003: Maintainability
- Clear separation of scraper/parser/storage
- Comprehensive logging
- Easy to add new data sources

---

## Implementation Plan

### Phase 1: Data Source Analysis (Week 1)
- [ ] Analyze HKEX official website
- [ ] Identify data sources
- [ ] Document API endpoints or scraping points
- [ ] Assess data availability and accuracy

### Phase 2: Web Scraper Development (Week 2)
- [ ] Implement base scraper class
- [ ] Develop HKEX-specific scraper
- [ ] Add retry and error handling
- [ ] Support async parallel requests

### Phase 3: Data Storage (Week 2-3)
- [ ] Design SQLite schema
- [ ] Implement data persistence layer
- [ ] Add incremental update logic
- [ ] Support data exports

### Phase 4: Testing & Validation (Week 3)
- [ ] Collect real historical data
- [ ] Validate data accuracy
- [ ] Compare with known sources
- [ ] Unit tests for all components

### Phase 5: Integration (Week 4)
- [ ] Replace mock data fixtures
- [ ] Update backtest engine
- [ ] Run backtests with real data
- [ ] Performance benchmarking

---

## Success Criteria

- ✅ 5+ years of real HKEX data collected
- ✅ 40+ stocks covered
- ✅ Data accuracy ± 0.01%
- ✅ Zero mock data in backtests
- ✅ All tests pass with real data
- ✅ < 60 seconds for full historical fetch
- ✅ Documentation complete
- ✅ Zero dependency on external data libs

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| HKEX website structure changes | Medium | Monitor & adapt scraper regex |
| Rate limiting | Low | Implement delays & retries |
| Data inconsistencies | High | Strict validation & QA |
| Network failures | Medium | Robust error handling & cache |
| Performance degradation | Medium | Async & parallel processing |

---

## Open Questions

1. **Data Source**: Which HKEX data source should we prioritize?
   - Official HKEX website?
   - Third-party data providers?
   - Real-time feeds?

2. **Frequency**: How often should data be updated?
   - Daily after market close?
   - Real-time during trading hours?
   - Weekly?

3. **Storage**: Local SQLite or cloud database?
   - Storage size limit?
   - Retention period?

4. **Scope**: All HKEX stocks or just major ones?
   - 40 stocks (Hang Seng index)?
   - 100+ stocks?
   - All listed stocks?

---

## Next Steps

1. Review and approve this proposal
2. Gather team feedback on data source preferences
3. Create detailed design document
4. Begin Phase 1 (Data Source Analysis)

---

**Status**: Ready for Review
**Approval Required**: YES

