# Multi-Source Data Integration Guide

**Version**: 1.0
**Date**: November 10, 2025
**Status**: Phase 9 - Polish & Cross-Cutting Concerns

## Overview

This document describes the multi-source non-price data integration system that combines 5 distinct Hong Kong government data sources into a unified quantitative trading framework. The system converts alternative data (visitor arrivals, property prices, GDP, retail sales, and trade data) into 60 technical indicators (12 per source) for enhanced trading signal generation.

## System Architecture

### Data Sources (5 Primary Sources)

#### 1. Immigration/Visitor Data (User Story 1)
- **Source**: data.gov.hk (CKAN API)
- **Indicators**: visitor_total, visitor_mainland, visitor_growth
- **Adapter**: `src/data_adapters/visitor_adapter.py`
- **Output**: 12 technical indicators

#### 2. Real Estate Data (User Story 2)
- **Source**: RVD (rvd.gov.hk) + Land Registry (landreg.gov.hk)
- **Indicators**: price_index, transactions, volume, rental_price
- **Adapter**: `src/data_adapters/property_adapter.py`
- **Output**: 12 technical indicators

#### 3. GDP Data (User Story 3)
- **Source**: C&SD (censtatd.gov.hk) via Web Tables API
- **Indicators**: gdp_nominal, gdp_growth, sector_contributions
- **Adapter**: `src/data_adapters/gdp_adapter.py`
- **Output**: 12 technical indicators

#### 4. Retail Sales Data (User Story 4)
- **Source**: C&SD (censtatd.gov.hk) via Web Tables API
- **Indicators**: total_sales, category_breakdown, yoy_growth
- **Adapter**: `src/data_adapters/retail_adapter.py`
- **Output**: 12 technical indicators

#### 5. Trade Data (User Story 5)
- **Source**: C&SD (censtatd.gov.hk) via Web Tables API
- **Indicators**: exports, imports, trade_balance, partner_breakdown
- **Adapter**: `src/data_adapters/trade_adapter.py`
- **Output**: 12 technical indicators

### Additional Data Sources

#### 6. HIBOR Data (Support)
- **Source**: HKMA (hkma.gov.hk)
- **Indicators**: hibor_overnight, 1m, 3m, 6m, 12m
- **Adapter**: `src/data_adapters/hkma_hibor.py`
- **Purpose**: Rate-sensitive indicator for monetary policy impacts

## Technical Indicators (60 Total Conversions)

Each data source generates 12 standardized technical indicators:

### Core Indicators (All Sources)
1. **Simple Moving Average (SMA)** - 20, 50, 200-day periods
2. **Exponential Moving Average (EMA)** - 12, 26-day periods
3. **Relative Strength Index (RSI)** - 14-day period
4. **MACD (Moving Average Convergence Divergence)** - 12/26/9 configuration
5. **Bollinger Bands** - 20-day SMA with 2 standard deviations
6. **Stochastic Oscillator** - %K and %D lines (14, 3, 3)
7. **Williams %R** - 14-day period
8. **Commodity Channel Index (CCI)** - 20-day period
9. **Average True Range (ATR)** - 14-day period
10. **Money Flow Index (MFI)** - 14-day period
11. **On-Balance Volume (OBV)** - Volume-price trend
12. **Ichimoku Cloud** - Tenkan-sen, Kijun-sen, Senkou Span A/B

### Indicator Calculation Framework

```python
def calculate_all_indicators(data, source_type):
    """Calculate 12 technical indicators for a data source"""
    indicators = {}

    # Core trend indicators
    indicators['sma_20'] = calculate_sma(data, 20)
    indicators['sma_50'] = calculate_sma(data, 50)
    indicators['ema_12'] = calculate_ema(data, 12)
    indicators['ema_26'] = calculate_ema(data, 26)

    # Momentum indicators
    indicators['rsi'] = calculate_rsi(data, 14)
    indicators['macd'], indicators['macd_signal'] = calculate_macd(data)
    indicators['stoch_k'], indicators['stoch_d'] = calculate_stochastic(data)
    indicators['williams_r'] = calculate_williams_r(data, 14)
    indicators['cci'] = calculate_cci(data, 20)

    # Volatility indicators
    indicators['bollinger_upper'], indicators['bollinger_lower'] = calculate_bollinger(data)
    indicators['atr'] = calculate_atr(data, 14)

    # Volume indicators
    indicators['obv'] = calculate_obv(data)

    return indicators
```

## Integration Architecture

### MultiSourceBacktestEngine

The `MultiSourceBacktestEngine` extends the base backtest framework to handle multiple data sources simultaneously:

```python
class MultiSourceBacktestEngine:
    """Unified engine for multi-source data backtesting"""

    def __init__(self):
        self.adapters = {
            'visitor': VisitorAdapter(),
            'property': PropertyAdapter(),
            'gdp': GDPAdapter(),
            'retail': RetailAdapter(),
            'trade': TradeAdapter()
        }
        self.indicators = {}
        self.performance_metrics = {}

    async def fetch_all_data(self, start_date, end_date):
        """Fetch data from all 5 sources in parallel"""
        tasks = []
        for source, adapter in self.adapters.items():
            task = adapter.fetch_data(start_date, end_date)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return dict(zip(self.adapters.keys(), results))

    async def calculate_all_indicators(self, data_dict):
        """Calculate indicators for all sources in parallel"""
        tasks = []
        for source, data in data_dict.items():
            task = self.calculate_indicators_for_source(source, data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return dict(zip(data_dict.keys(), results))
```

### Data Flow

```
┌─────────────────────┐
│  Data Sources (5)   │
│  - Visitor          │
│  - Property         │
│  - GDP              │
│  - Retail           │
│  - Trade            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Data Adapters      │
│  (Parallel Fetch)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Data Normalization │
│  & Validation       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Technical Indicators│
│  (60 conversions)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Backtest Engine    │
│  - Parameter Opt    │
│  - Signal Gen       │
│  - Performance      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Results & Reports  │
│  - Sharpe Ratio     │
│  - Max Drawdown     │
│  - Multi-Source     │
│    Comparison       │
└─────────────────────┘
```

## Performance Optimization

### Parallel Processing

All data fetching and indicator calculations are parallelized:

```python
# Parallel data fetching
async def fetch_all_data_parallel():
    tasks = [
        fetch_visitor_data(),
        fetch_property_data(),
        fetch_gdp_data(),
        fetch_retail_data(),
        fetch_trade_data()
    ]
    return await asyncio.gather(*tasks)

# Parallel indicator calculation
async def calculate_all_indicators_parallel(data):
    tasks = [
        calculate_indicators('visitor', data['visitor']),
        calculate_indicators('property', data['property']),
        calculate_indicators('gdp', data['gdp']),
        calculate_indicators('retail', data['retail']),
        calculate_indicators('trade', data['trade'])
    ]
    return await asyncio.gather(*tasks)
```

### Caching Strategy

LRU caching reduces redundant API calls:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_cached_data(source, start_date, end_date):
    """Cache API responses to reduce network calls"""
    return adapter.fetch_data(source, start_date, end_date)
```

### Performance Targets

- **Data Fetching**: < 30 seconds for all 5 sources
- **Indicator Calculation**: < 15 seconds for 60 indicators
- **Parameter Optimization**: < 10 minutes for 2000+ combinations
- **Memory Usage**: < 4GB for full dataset

## Configuration

### Data Source Configuration

```json
{
  "visitor": {
    "source": "data.gov.hk",
    "api_endpoint": "https://data.gov.hk/api/3/action/datastore_search",
    "update_frequency": "daily",
    "timeout": 30
  },
  "property": {
    "source": "rvd.gov.hk",
    "api_endpoint": "https://www.rvd.gov.hk/sc.property_market_statistics.html",
    "update_frequency": "monthly",
    "timeout": 30
  },
  "gdp": {
    "source": "censtatd.gov.hk",
    "api_endpoint": "https://www.censtatd.gov.hk/api/web_table.html",
    "update_frequency": "quarterly",
    "timeout": 30
  },
  "retail": {
    "source": "censtatd.gov.hk",
    "api_endpoint": "https://www.censtatd.gov.hk/api/web_table.html",
    "update_frequency": "monthly",
    "timeout": 30
  },
  "trade": {
    "source": "censtatd.gov.hk",
    "api_endpoint": "https://www.censtatd.gov.hk/api/web_table.html",
    "update_frequency": "monthly",
    "timeout": 30
  }
}
```

### Technical Indicator Parameters

```json
{
  "indicators": {
    "sma_periods": [20, 50, 200],
    "ema_periods": [12, 26],
    "rsi_period": 14,
    "macd_config": {"fast": 12, "slow": 26, "signal": 9},
    "bollinger_config": {"period": 20, "std_dev": 2},
    "stochastic_config": {"k": 14, "d": 3, "smooth": 3},
    "williams_r_period": 14,
    "cci_period": 20,
    "atr_period": 14
  },
  "trading_signals": {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "bollinger_squeeze_threshold": 0.02,
    "macd_crossover_threshold": 0.0
  }
}
```

## Testing Strategy

### Test Coverage

- **Unit Tests**: Each adapter independently tested
- **Integration Tests**: Multi-source data flow tested
- **Performance Tests**: <30 second target validated
- **Contract Tests**: Data format compliance verified
- **Mock Detection**: Simulated data identified

### Test Files Structure

```
tests/
├── unit/
│   ├── test_visitor_adapter.py
│   ├── test_property_adapter.py
│   ├── test_gdp_adapter.py
│   ├── test_retail_adapter.py
│   └── test_trade_adapter.py
├── integration/
│   └── test_multi_source.py
├── contract/
│   ├── test_visitor_data.py
│   ├── test_property_data.py
│   ├── test_gdp_data.py
│   ├── test_retail_data.py
│   └── test_trade_data.py
└── performance/
    └── test_data_fetching.py
```

## Security Considerations

### Input Validation

All data sources validated for authenticity:

```python
def validate_data_source(data, source):
    """Validate data source authenticity"""
    # Check for government domain
    assert data.domain in GOVERNMENT_DOMAINS[source]

    # Detect mock data
    assert not is_mock_data(data)

    # Validate data structure
    validate_schema(data, SCHEMAS[source])

    # Check data freshness
    assert data.age < MAX_DATA_AGE[source]
```

### API Rate Limiting

```python
from asyncio import Semaphore

# Limit concurrent API calls
API_SEMAPHORE = Semaphore(5)

async def fetch_with_rate_limit(adapter, *args, **kwargs):
    async with API_SEMAPHORE:
        return await adapter.fetch_data(*args, **kwargs)
```

### Error Handling

```python
class GovernmentDataError(Exception):
    """Raised when government data is unavailable"""
    pass

class MockDataError(Exception):
    """Raised when mock data is detected"""
    pass

class APILimitError(Exception):
    """Raised when API rate limit is exceeded"""
    pass
```

## Usage Examples

### Basic Multi-Source Backtest

```python
from src.integration.multi_source_backtest import MultiSourceBacktestEngine

# Initialize engine
engine = MultiSourceBacktestEngine()

# Fetch all data
data = await engine.fetch_all_data('2020-01-01', '2023-12-31')

# Calculate indicators
indicators = await engine.calculate_all_indicators(data)

# Run backtest
results = await engine.run_backtest(
    data=data,
    indicators=indicators,
    start_date='2020-01-01',
    end_date='2023-12-31'
)

# Display results
print(f"Sharpe Ratio: {results.sharpe_ratio}")
print(f"Max Drawdown: {results.max_drawdown}")
print(f"Total Return: {results.total_return}%")
```

### Individual Source Analysis

```python
# Analyze single source
visitor_adapter = VisitorAdapter()
visitor_data = await visitor_adapter.fetch_data('2020-01-01', '2023-12-31')
visitor_indicators = calculate_all_indicators(visitor_data, 'visitor')

# Generate signals
signals = generate_trading_signals(visitor_indicators)
print(f"Buy signals: {signals.buy_count}")
print(f"Sell signals: {signals.sell_count}")
```

### Parameter Optimization

```python
# Optimize parameters for all sources
optimization_results = await engine.optimize_parameters(
    data=data,
    param_grid={
        'visitor': {'rsi_oversold': [20, 30], 'rsi_overbought': [70, 80]},
        'property': {'sma_period': [20, 50], 'atr_multiplier': [2.0, 2.5]},
        'gdp': {'cci_threshold': [100, 150]},
        'retail': {'macd_threshold': [0.0, 0.1]},
        'trade': {'bollinger_position': ['upper', 'lower']}
    },
    max_workers=8
)

# Get best parameters
best_params = optimization_results.get_best_parameters()
print(f"Best parameters: {best_params}")
```

## Monitoring & Alerting

### Data Quality Monitoring

```python
class DataQualityMonitor:
    """Monitor data quality across all sources"""

    def __init__(self):
        self.thresholds = {
            'data_freshness': 7,  # days
            'missing_data_ratio': 0.1,  # 10%
            'anomaly_threshold': 3.0  # standard deviations
        }

    async def check_all_sources(self):
        """Check data quality for all sources"""
        results = {}
        for source in self.sources:
            quality = await self.check_source_quality(source)
            results[source] = quality

            if quality.score < self.thresholds['min_score']:
                await self.send_alert(source, quality)

        return results
```

### Performance Monitoring

```python
class PerformanceMonitor:
    """Monitor system performance"""

    async def benchmark_data_fetching(self):
        """Benchmark data fetching performance"""
        start_time = time.time()
        data = await engine.fetch_all_data('2023-01-01', '2023-12-31')
        duration = time.time() - start_time

        assert duration < 30, f"Data fetching too slow: {duration}s"
        return duration
```

## Troubleshooting

### Common Issues

1. **Mock Data Detection**
   - Check data source domain
   - Verify timestamp authenticity
   - Cross-reference with official statistics

2. **API Rate Limiting**
   - Implement exponential backoff
   - Use cached data when available
   - Monitor rate limit headers

3. **Data Format Changes**
   - Validate schema before processing
   - Implement version detection
   - Maintain backward compatibility

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose data inspection
engine = MultiSourceBacktestEngine(debug=True)

# Inspect raw data
raw_data = await engine.fetch_all_data_debug()
print(json.dumps(raw_data, indent=2, default=str))
```

## API Reference

### MultiSourceBacktestEngine

#### Methods

- `fetch_all_data(start_date, end_date)` - Fetch data from all sources
- `calculate_all_indicators(data_dict)` - Calculate indicators for all sources
- `run_backtest(config)` - Execute backtest with all sources
- `optimize_parameters(param_grid)` - Optimize trading parameters
- `generate_report()` - Generate comprehensive performance report

### Data Adapters

#### BaseAdapter Interface

```python
class BaseAdapter(ABC):
    @abstractmethod
    async def fetch_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from source"""

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate data authenticity"""

    @abstractmethod
    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize data format"""
```

## Deployment

### Production Checklist

- [ ] All 5 data sources tested and validated
- [ ] Technical indicators calculated correctly (60 total)
- [ ] Performance targets met (<30s data fetch, <10min optimization)
- [ ] Test coverage ≥80%
- [ ] Security hardening implemented
- [ ] Monitoring and alerting configured
- [ ] Documentation complete
- [ ] Error handling robust
- [ ] Rate limiting configured
- [ ] Caching strategy implemented

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATA_GOV_HK_API_KEY=your_key
export RVD_API_KEY=your_key
export CSD_API_KEY=your_key

# Run tests
pytest tests/ -v --cov=src/

# Start system
python complete_project_system.py
```

## Future Enhancements

### Planned Features

1. **Additional Data Sources**
   - MTR passenger data
   - Border crossing statistics
   - Traffic flow data
   - Energy consumption data

2. **Advanced Indicators**
   - Custom technical indicators
   - Machine learning-based signals
   - Sentiment analysis integration
   - Alternative data fusion

3. **Performance Improvements**
   - Real-time data streaming
   - Edge computing support
   - Distributed processing
   - GPU acceleration

## Conclusion

The multi-source data integration system provides a robust framework for combining Hong Kong government data sources into actionable trading signals. With 60 technical indicator conversions across 5 data sources, the system offers comprehensive market insight through alternative data analysis.

For questions or support, please refer to the troubleshooting section or contact the development team.

---

**Last Updated**: November 10, 2025
**Version**: 1.0
**Status**: Production Ready
