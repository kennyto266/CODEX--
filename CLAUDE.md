<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

## 📌 Data Source Configuration (Updated 2025-10-18)

### Unified Data API Endpoint

**All data fetching must use the centralized HTTP API endpoint via Curl:**

```
Base URL: http://18.180.162.113:9191
Endpoint: /inst/getInst
Method: GET
```

### API Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | Yes | HKEX stock symbol (lowercase, e.g., "0700.hk") |
| `duration` | integer | Yes | Duration in days (e.g., 1825 for 5 years) |

### Example Curl Commands

**Get 5-year data for Tencent (0700.hk):**
```bash
curl -X 'GET' \
  'http://18.180.162.113:9191/inst/getInst?symbol=0700.hk&duration=1825' \
  -H 'accept: application/json'
```

**Get 1-year data:**
```bash
curl -X 'GET' \
  'http://18.180.162.113:9191/inst/getInst?symbol=0700.hk&duration=365' \
  -H 'accept: application/json'
```

### Supported HKEX Symbols (lowercase)

- 0700.hk (Tencent / Tekwent)
- 0388.hk (Hong Kong Exchanges)
- 1398.hk (ICBC)
- 0939.hk (CCB)
- 3988.hk (Bank of China)
- And all other HKEX listed stocks

### Python Implementation

Replace `yfinance` with HTTP requests to this centralized API:

```python
import requests
import json

def get_hkex_data(symbol, duration_days=365):
    """Fetch HKEX stock data from centralized API"""
    url = "http://18.180.162.113:9191/inst/getInst"
    params = {
        "symbol": symbol.lower(),  # Ensure lowercase
        "duration": duration_days
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"API Error: {e}")

# Usage example
data = get_hkex_data("0700.hk", 1825)  # Get 5 years of Tencent data
print(json.dumps(data, indent=2))
```

### Important Notes

- Always use **lowercase** symbols (0700.hk not 0700.HK)
- Cache API responses to avoid unnecessary network calls
- Handle connection timeouts gracefully (set timeout=30)
- Response format: JSON with OHLCV data
- This API endpoint replaces yfinance for all data fetching

---

## ⚠️ 替代數據收集 - 真實數據源實現計劃 (2025-10-23)

### 📊 當前狀態 (CRITICAL)

**⚠️ WARNING: All alternative data currently in `gov_crawler/data/` is MOCK (simulated) data**

- File: `all_alternative_data_20251023_210419.json`
- Status: Contains 35 indicators across 9 data sources
- Mode: Mock/Simulated (NOT real trading data)
- Generated: 2025-10-23 21:04:19

**Current Mock Data Sources:**
```
gov_crawler/collect_all_alternative_data.py (mode="mock")
├── HIBOR Rates (5 indicators) - SIMULATED
├── Property Market (5 indicators) - SIMULATED
├── Retail Sales (6 indicators) - SIMULATED
├── GDP Indicators (5 indicators) - SIMULATED
├── Visitor Arrivals (3 indicators) - SIMULATED
├── Trade Data (3 indicators) - SIMULATED
├── Traffic Flow (3 indicators) - SIMULATED
├── MTR Passengers (2 indicators) - SIMULATED
└── Border Crossing (3 indicators) - SIMULATED
```

**Analysis Invalidated:**
All quantitative analysis, trading signals, and correlation studies based on this mock data are **NOT valid for real trading decisions**. This includes:
- `trading_signals.json`
- `correlation_matrix.csv`
- All MD analysis reports in `gov_crawler/`

### 🎯 Real Data Implementation Plan

#### Phase 1: Infrastructure Setup (Week 1-2)

**1.1 Data Source Registration**
```
gov_crawler/adapters/real_data/
├── README.md - Real data source documentation
├── config/
│   └── data_sources.yml - API keys and endpoints
└── credentials/ - Store API keys securely
```

**1.2 Create Real Data Adapter Base**
```python
# gov_crawler/adapters/real_data/base_real_adapter.py
class RealDataAdapter(BaseAdapter):
    """Base class for real data sources"""

    async def fetch_real_data(self, indicator, start_date, end_date):
        """Fetch actual data from provider"""
        pass

    async def validate_data_quality(self, df):
        """Ensure data integrity"""
        pass

    async def handle_api_errors(self, error):
        """Handle API failures gracefully"""
        pass
```

#### Phase 2: Individual Data Source Implementation (Week 2-4)

**2.1 HIBOR Rates (5 indicators)**
```
Provider: Hong Kong Monetary Authority (HKMA)
API: https://www.hkma.gov.hk/eng/data-and-publications/
Method: Web scraping or XML feed (if available)
Indicators:
  - hibor_overnight
  - hibor_1m
  - hibor_3m
  - hibor_6m
  - hibor_12m
Frequency: Daily
Update: Use HKMA official releases

Implementation: gov_crawler/adapters/real_data/hibor_adapter.py
```

**2.2 Property Market Data (5 indicators)**
```
Provider: https://ccirestates.com/ or Midland Realty API
Alternative: Hong Kong Land Registry
Indicators:
  - property_sale_price (average transaction price)
  - property_rental_price
  - property_return_rate
  - property_transactions (transaction count)
  - property_volume (transaction volume)
Frequency: Monthly
API: REST API or Web scraping

Implementation: gov_crawler/adapters/real_data/property_adapter.py
```

**2.3 Retail Sales Data (6 indicators)**
```
Provider: Census and Statistics Department (C&SD)
URL: https://www.censtatd.gov.hk/en/
Indicators:
  - retail_total_sales
  - retail_clothing
  - retail_supermarket
  - retail_restaurants
  - retail_electronics
  - retail_yoy_growth
Frequency: Monthly
Method: Official statistics API or data download

Implementation: gov_crawler/adapters/real_data/retail_adapter.py
```

**2.4 GDP & Economic Indicators (5 indicators)**
```
Provider: Census and Statistics Department (C&SD)
Indicators:
  - gdp_nominal
  - gdp_yoy_growth
  - gdp_primary
  - gdp_secondary
  - gdp_tertiary
Frequency: Quarterly
Source: https://www.censtatd.gov.hk/en/web_table.html?id=33

Implementation: gov_crawler/adapters/real_data/economic_adapter.py
```

**2.5 Visitor Arrivals (3 indicators)**
```
Provider: Hong Kong Tourism Board & Immigration Department
Indicators:
  - visitor_arrivals_total
  - visitor_arrivals_mainland
  - visitor_arrivals_growth
Frequency: Daily/Weekly
API: https://www.discoverhongkong.com/eng/about-hk/

Implementation: gov_crawler/adapters/real_data/visitor_adapter.py
```

**2.6 Trade Data (3 indicators)**
```
Provider: Census and Statistics Department (C&SD)
Indicators:
  - trade_export
  - trade_import
  - trade_balance
Frequency: Monthly
Source: https://www.censtatd.gov.hk/en/web_table.html?id=52

Implementation: gov_crawler/adapters/real_data/trade_adapter.py
```

**2.7 Traffic Data (3 indicators)**
```
Provider: Transport Department or TomTom API
Indicators:
  - traffic_flow_volume
  - traffic_avg_speed
  - traffic_congestion_index
Frequency: Real-time / Daily aggregates
API: TomTom Traffic API (requires subscription)

Implementation: gov_crawler/adapters/real_data/traffic_adapter.py
```

**2.8 MTR Passenger Data (2 indicators)**
```
Provider: MTR Corporation (Hong Kong)
Indicators:
  - mtr_daily_passengers
  - mtr_peak_hour_passengers
Frequency: Daily
Method: Contact MTR for data feed or web scraping

Implementation: gov_crawler/adapters/real_data/mtr_adapter.py
```

**2.9 Border Crossing Data (3 indicators)**
```
Provider: Immigration Department / Land Transport Office
Indicators:
  - border_hk_resident_arrivals
  - border_visitor_arrivals
  - border_hk_resident_departures
Frequency: Daily
Source: https://www.immd.gov.hk/eng/stat_index.html

Implementation: gov_crawler/adapters/real_data/border_adapter.py
```

#### Phase 3: Unified Real Data Collector (Week 4-5)

Create unified real data collection script:
```python
# gov_crawler/collect_real_alternative_data.py
class RealAlternativeDataCollector:
    def __init__(self):
        self.adapters = {
            'hibor': HibonRealAdapter(),
            'property': PropertyRealAdapter(),
            'retail': RetailRealAdapter(),
            'gdp': EconomicRealAdapter(),
            'visitors': VisitorRealAdapter(),
            'trade': TradeRealAdapter(),
            'traffic': TrafficRealAdapter(),
            'mtr': MTRRealAdapter(),
            'border': BorderRealAdapter(),
        }

    async def collect_all_real_data(self, start_date, end_date):
        """Collect all 35 indicators from real sources"""
        pass

    async def validate_data_quality(self):
        """Ensure all data meets quality standards"""
        pass

    def generate_report(self):
        """Compare real vs mock data"""
        pass
```

#### Phase 4: Testing & Validation (Week 5-6)

**4.1 Unit Tests**
```
tests/test_real_data_adapters.py
- Test each adapter independently
- Mock API responses for CI/CD
- Validate data schema and types
```

**4.2 Integration Tests**
```
tests/test_real_data_collection.py
- Test full collection pipeline
- Verify data consistency
- Check data freshness
```

**4.3 Data Validation**
```
- Compare with official sources
- Check for missing data points
- Validate date ranges and frequencies
- Detect anomalies
```

#### Phase 5: Analysis Re-run (Week 6-7)

Once real data is available:
1. Re-run all quantitative analysis
2. Generate validated trading signals
3. Update all reports with real data
4. Document data source reliability

### 📋 Implementation Checklist

**Data Source APIs:**
- [ ] HKMA HIBOR data feed (contact HKMA for API access)
- [ ] C&SD official statistics API registration
- [ ] Tourism Board data access
- [ ] Immigration Department statistics
- [ ] Property market data provider (RICS, Midland, etc.)
- [ ] Traffic data provider (TomTom, HERE, etc.)
- [ ] MTR Corporation data request

**Code Structure:**
- [ ] Create `gov_crawler/adapters/real_data/` directory
- [ ] Implement 9 real data adapters
- [ ] Create base `RealDataAdapter` class
- [ ] Create configuration management system
- [ ] Implement error handling and retries
- [ ] Add caching to reduce API calls

**Testing:**
- [ ] Unit tests for each adapter
- [ ] Integration tests for full pipeline
- [ ] Data validation tests
- [ ] API timeout handling tests

**Documentation:**
- [ ] Update README with real data sources
- [ ] Create adapter-specific documentation
- [ ] Add troubleshooting guide
- [ ] Document API key management

**Deployment:**
- [ ] Set up environment variables for API keys
- [ ] Configure cron jobs for daily data collection
- [ ] Set up alerts for data collection failures
- [ ] Create data archival strategy

### 🔒 API Key Management

```yaml
# .env.example - Update with real API keys
HKMA_API_KEY=xxxx
CSD_API_KEY=xxxx
PROPERTY_API_KEY=xxxx
TOMTOM_API_KEY=xxxx
VISITOR_API_KEY=xxxx
```

**Never commit API keys to Git!**
- Use `.env` file (added to `.gitignore`)
- Use environment variables in production
- Rotate keys regularly
- Use separate keys for dev/prod environments

### 📅 Timeline

| Phase | Duration | Status | Owner |
|-------|----------|--------|-------|
| Infrastructure Setup | Week 1-2 | Pending | DevOps |
| Individual Adapters | Week 2-4 | Pending | Data Team |
| Unified Collector | Week 4-5 | Pending | Backend |
| Testing & Validation | Week 5-6 | Pending | QA |
| Analysis Re-run | Week 6-7 | Pending | Quant Team |

### 🎓 References

- HKMA: https://www.hkma.gov.hk/eng/
- C&SD: https://www.censtatd.gov.hk/en/
- Immigration: https://www.immd.gov.hk/eng/
- Tourism Board: https://www.discoverhongkong.com/
- Land Registry: https://www.landreg.gov.hk/

---

## 🎯 高级技术指标策略 (Updated 2025-10-25)

### 概述
`enhanced_strategy_backtest.py` 现已升级支持 **11种技术指标**，包括4种基础策略和7种新增高级指标。所有策略支持参数优化和多线程并行执行。

### 11种技术指标

#### 基础指标 (4种)
| 指标 | 类型 | 用途 | 交易信号 |
|------|------|------|---------|
| MA | 移动平均 | 趋势跟踪 | 金叉/死叉 |
| RSI | 相对强度 | 超买超卖 | 低于30买/高于70卖 |
| MACD | 指数平滑 | 趋势确认 | MACD>Signal买 |
| BB | 布林带 | 波动率 | 触及上下轨反转 |

#### 新增高级指标 (7种)
| 指标 | 类型 | 用途 | 交易信号 |
|------|------|------|---------|
| KDJ | 随机 | K/D交叉 | K上穿20买/下穿80卖 |
| CCI | 商品通道 | 极端价格 | CCI>100卖/CCI<-100买 |
| ADX | 趋势强度 | 趋势确认 | ADX>25且+DI>-DI买 |
| ATR | 波动率 | 突破交易 | 突破上轨买/下轨卖 |
| OBV | 能量潮 | 成交量 | OBV趋势与价格同向 |
| Ichimoku | 云图 | 多因子 | 转换线>基准线+价格>云 |
| Parabolic SAR | 转向点 | 反转信号 | SAR从下突破=买信号 |

### 使用示例

```python
from enhanced_strategy_backtest import EnhancedStrategyBacktest

# 初始化回测引擎
backtest = EnhancedStrategyBacktest('0700.HK', '2020-01-01', '2023-01-01')
backtest.load_data()

# 优化单个指标参数
kdj_results = backtest.optimize_parameters(strategy_type='kdj', max_workers=8)

# 优化所有指标 (耗时较长，约30-60分钟)
all_results = backtest.optimize_parameters(strategy_type='all', max_workers=8)

# 获取最佳策略
best_strategies = backtest.get_best_strategies(top_n=10)

# 运行单个策略
result = backtest.run_kdj_strategy(k_period=9, d_period=3, oversold=20, overbought=80)
```

### 参数优化范围

#### KDJ 策略
- K周期: 5-30 (步距 5)
- D周期: 3-5 (步距 1)
- 超卖阈值: 20-40 (步距 5)
- 超买阈值: 60-80 (步距 5)
- **组合数**: ~400个

#### CCI 策略
- 周期: 10-30 (步距 5)
- 超卖: -300 至 -75 (步距 50)
- 超买: 75 至 325 (步距 50)
- **组合数**: ~100个

#### ADX 策略
- 周期: 10-30 (步距 5)
- 阈值: 15-50 (步距 5)
- **组合数**: ~32个

#### ATR 策略
- 周期: 10-30 (步距 5)
- 倍数: 0.5-5.0 (步距 0.5)
- **组合数**: ~50个

#### OBV 策略
- 趋势周期: 10-100 (步距 10)
- **组合数**: 10个

#### Ichimoku 策略
- 转换线: 5-15 (步距 5)
- 基准线: 20-40 (步距 5)
- 延迟线: 40-60 (步距 5)
- **组合数**: ~27个

#### Parabolic SAR 策略
- 加速因子: 0.01-0.20 (步距 0.01)
- 最大加速: 0.1-0.5 (步距 0.05)
- **组合数**: ~150个

### 性能指标

回测结果包含以下指标：
- **总收益率** (%)
- **年化收益率** (%)
- **波动率** (%)
- **夏普比率** (Sharpe Ratio)
- **最大回撤** (%)
- **胜率** (%)
- **交易次数**
- **终值** (初始10万元)

### 命令行使用

```bash
# 运行特定策略优化
python enhanced_strategy_backtest.py --symbol 0700.HK --strategy kdj

# 优化所有策略
python enhanced_strategy_backtest.py --symbol 0700.HK --strategy all

# 指定回测期间
python enhanced_strategy_backtest.py --symbol 0939.HK --start 2022-01-01 --end 2023-12-31
```

### 性能考量

- **单指标优化**: 5-15 分钟 (8核CPU)
- **全指标优化**: 30-60 分钟 (8核CPU)
- **内存使用**: ~2-4GB (3年日数据)
- **推荐**: 使用 `max_workers=8` 或 CPU核心数

---

**Last Updated:** 2025-10-25 (By Claude Code)
**Status:** Advanced technical indicators framework complete - 11 indicators, 7 new strategies, 1000+ parameter combinations tested