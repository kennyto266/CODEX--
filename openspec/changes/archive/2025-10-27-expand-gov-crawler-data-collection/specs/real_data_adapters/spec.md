# Real Data Adapters Specification

## Overview

Define a comprehensive set of adapters for collecting real alternative data from 9 distinct Hong Kong data sources to replace simulated data in the quantitative trading system.

## ADDED Requirements

### Requirement: HiborAdapter - HKMA HIBOR Data Collection

Implement adapter for Hong Kong Monetary Authority Interbank Offered Rates.

#### Scenario: Fetching Daily HIBOR Rates
- **Given**: Need to collect HIBOR rates for 5 different maturities
- **When**: `HiborAdapter.fetch_data()` is called
- **Then**: System retrieves overnight, 1M, 3M, 6M, and 12M rates from HKMA API
- **And**: Data is normalized to standard format with timestamps

#### Scenario: Handling API Rate Limits
- **Given**: HKMA API has request rate restrictions
- **When**: Multiple requests are made in short succession
- **Then**: Adapter implements exponential backoff and respects rate limits
- **And**: Failed requests are retried up to 3 times before failing

#### Scenario: Data Validation
- **Given**: HIBOR rate data received from API
- **When**: `validate_data_quality()` is called
- **Then**: System checks for missing values, anomalous rates, and format consistency
- **And**: Invalid data points are flagged and logged

### Requirement: PropertyAdapter - Real Estate Market Data

Implement adapter for Hong Kong property market data from Land Registry and property agencies.

#### Scenario: Collecting Property Transaction Data
- **Given**: Need monthly property market statistics
- **When**: `PropertyAdapter.fetch_data()` executes
- **Then**: System collects average transaction prices, rental yields, transaction volumes
- **And**: Data is aggregated and normalized by district and property type

#### Scenario: Processing Multiple Property Data Sources
- **Given**: Data available from Land Registry, RICS, and private agencies
- **When**: Adapter attempts to fetch from primary source
- **Then**: If primary fails, adapter attempts secondary sources
- **And**: Data from multiple sources is reconciled and validated

#### Scenario: Historical Data Retrieval
- **Given**: Request for 5-year historical property data
- **When**: `fetch_historical_data(start_date, end_date)` is called
- **Then**: Adapter retrieves all available historical records
- **And**: Missing periods are flagged and documented

### Requirement: RetailAdapter - Retail Sales Statistics

Implement adapter for Census and Statistics Department retail sales data.

#### Scenario: Monthly Retail Sales Collection
- **Given**: Need to track retail performance across categories
- **When**: `RetailAdapter.fetch_data()` runs
- **Then**: System collects total sales, clothing, supermarket, restaurants, electronics data
- **And**: Year-over-year growth calculations are performed

#### Scenario: Category-Level Data Processing
- **Given**: Retail data segmented by product category
- **When**: Data is processed for analysis
- **Then**: Each category is separately validated and normalized
- **And**: Category-specific trends are identified and flagged

### Requirement: EconomicAdapter - GDP and Economic Indicators

Implement adapter for comprehensive economic data from C&SD.

#### Scenario: Quarterly GDP Data Collection
- **Given**: Need nominal GDP and sector breakdown data
- **When**: `EconomicAdapter.fetch_gdp_data()` executes
- **Then**: System retrieves primary, secondary, and tertiary sector contributions
- **And**: Growth rates are calculated and validated

#### Scenario: Economic Indicator Validation
- **Given**: Multiple economic indicators (GDP, CPI, unemployment)
- **When**: Data validation is performed
- **Then**: Cross-validation between indicators ensures consistency
- **And**: Anomalies are flagged for manual review

### Requirement: VisitorAdapter - Tourism and Visitor Data

Implement adapter for visitor arrival statistics from Tourism Board and Immigration.

#### Scenario: Daily Visitor Count Tracking
- **Given**: Need to track visitor arrivals for tourism impact analysis
- **When**: `VisitorAdapter.fetch_data()` runs
- **Then**: System collects total arrivals, mainland China visitors, and growth rates
- **And**: Data is segmented by arrival type and nationality

#### Scenario: Multi-Source Data Reconciliation
- **Given**: Data available from Tourism Board and Immigration Department
- **When**: Both sources are queried
- **Then**: Data is cross-referenced for accuracy
- **And**: Discrepancies are resolved using authoritative source priority

### Requirement: TradeAdapter - Trade Statistics

Implement adapter for import/export data from C&SD.

#### Scenario: Monthly Trade Balance Calculation
- **Given**: Need to track Hong Kong's trade performance
- **When**: `TradeAdapter.fetch_trade_data()` executes
- **Then**: System collects export values, import values, and calculates trade balance
- **And**: Major trading partner breakdowns are included

#### Scenario: Trade Data Time Series Analysis
- **Given**: Historical trade data over multiple years
- **When**: Time series analysis is requested
- **Then**: Seasonal patterns and trends are identified
- **And**: Anomalous periods are flagged for investigation

### Requirement: TrafficAdapter - Traffic Flow Data

Implement adapter for traffic statistics from Transport Department or TomTom API.

#### Scenario: Real-Time Traffic Monitoring
- **Given**: Need traffic flow data for economic activity indicators
- **When**: `TrafficAdapter.fetch_traffic_data()` executes
- **Then**: System retrieves vehicle counts, average speeds, congestion indices
- **And**: Data is aggregated by highway and time period

#### Scenario: Traffic Data Fusion
- **Given**: Data from multiple traffic monitoring points
- **When**: TrafficAdapter processes the data
- **Then**: Data is averaged and weighted by monitoring station reliability
- **And**: City-wide traffic indices are calculated

### Requirement: MtrAdapter - MTR Passenger Statistics

Implement adapter for MTR Corporation passenger data.

#### Scenario: Daily Passenger Volume Tracking
- **Given**: Need MTR ridership as economic activity indicator
- **When**: `MtrAdapter.fetch_passenger_data()` executes
- **Then**: System collects total daily passengers and peak hour passengers
- **And**: Data is segmented by line and time period

#### Scenario: Seasonal Pattern Detection
- **Given**: MTR passenger data over multiple years
- **When**: Pattern analysis is performed
- **Then**: Seasonal variations (holiday effects, school terms) are identified
- **And**: Baseline expectations are established

### Requirement: BorderAdapter - Border Crossing Statistics

Implement adapter for Immigration Department border crossing data.

#### Scenario: Daily Border Flow Monitoring
- **Given**: Need to track cross-border traffic
- **When**: `BorderAdapter.fetch_border_data()` executes
- **Then**: System collects HK resident arrivals, visitor arrivals, HK resident departures
- **And**: Data is segregated by crossing point and direction

## MODIFIED Requirements

### Requirement: BaseAdapter Extension

Extend existing BaseAdapter to support real-time data collection with retry mechanisms.

#### Scenario: Async Data Fetching
- **Given**: Multiple adapters need to fetch data concurrently
- **When**: `fetch_data()` is called on any adapter
- **Then**: Method executes asynchronously to support parallel collection
- **And**: Caller can await multiple adapters simultaneously

#### Scenario: Enhanced Error Handling
- **Given**: Network errors, API timeouts, and data format issues
- **When**: Adapter encounters an error
- **Then**: Specific error types are logged with context
- **And**: Graceful degradation is implemented (partial data better than no data)

## REMOVED Requirements

### Requirement: Mock Data Generation

Remove mock data generation capabilities from base adapter framework.

#### Scenario: Disable Simulated Data
- **Given**: Adapter configured with mock mode
- **When**: System transitions to real data collection
- **Then**: Mock data generation is disabled
- **And**: All data collection attempts real sources only

## Technical Specifications

### Adapter Interface

```python
class RealDataAdapter(BaseAdapter):
    """Base class for all real data adapters"""

    async def fetch_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from real source"""
        pass

    async def validate_data_quality(self, df: pd.DataFrame) -> QualityReport:
        """Validate collected data quality"""
        pass

    async def handle_api_error(self, error: Exception) -> bool:
        """Handle and retry on API errors"""
        pass

    def get_update_frequency(self) -> str:
        """Return data update frequency (daily/weekly/monthly/quarterly)"""
        pass
```

### Data Quality Standards

1. **Completeness**: No missing values in critical fields
2. **Accuracy**: Validated against official sources
3. **Timeliness**: Data no older than defined frequency
4. **Consistency**: Standardized format across all adapters
5. **Traceability**: Full audit trail of data sources

### Error Handling Strategy

1. **Transient Errors**: Exponential backoff with jitter (max 3 retries)
2. **Permanent Errors**: Log error, skip source, continue with others
3. **Partial Data**: Accept and flag incomplete datasets
4. **API Limits**: Implement rate limiting and request queuing
5. **Data Format**: Graceful handling of unexpected formats

### Performance Requirements

- **Latency**: < 30 seconds per adapter for daily data
- **Throughput**: Support 9 adapters running concurrently
- **Reliability**: 99% success rate for routine data collection
- **Resource Usage**: < 500MB memory per adapter instance
- **Rate Limiting**: Respect all API rate limits (configurable)

### Security Requirements

- API keys loaded from environment variables only
- No credentials in code or config files
- All API communication over HTTPS
- Request signing where required by API
- Audit logging of all API calls
- Automatic key rotation support
