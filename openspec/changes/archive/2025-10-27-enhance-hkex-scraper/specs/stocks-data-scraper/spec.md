# HKEX 股票数据爬虫规范

## 规范信息

**规范名称:** HKEX 股票数据爬虫

**版本:** 1.0.0

**创建日期:** 2025-10-27

**变更 ID:** enhance-hkex-scraper

---

## 概述

本规范定义 HKEX 主板和创业板股票数据的爬取功能，包括股票列表、实时报价、历史数据、基本信息等。

---

## ADDED Requirements

### 1. 股票列表管理

#### 需求: 提取股票列表

**描述:** 系统必须能够提取 HKEX 所有股票列表

**支持市场:**
- 主板股票 (Main Board)
- 创业板股票 (GEM)
- 主板第二上市 (Secondary Listing)

**数据字段:**
- 股票代码 (stock_code)
- 股票名称 (stock_name)
- 上市日期 (listing_date)
- 市场 (market)
- 行业分类 (sector)
- 子行业 (sub_sector)
- 市值 (market_cap)
- 状态 (status)

**验收标准:**
- [ ] 股票列表提取完整率 100%
- [ ] 支持至少 2000 只股票
- [ ] 行业分类准确率 > 95%
- [ ] 提取时间 < 30 秒

**场景:**

```python
# 场景 1: 获取所有股票列表
stocks = await scraper.get_stock_list()
# 返回: DataFrame with 2000+ rows

# 场景 2: 获取主板股票
main_board = await scraper.get_stock_list(market="main")
# 返回: DataFrame with main board stocks only

# 场景 3: 按行业筛选
tech_stocks = await scraper.get_stock_list(sector="Technology")
```

---

### 2. 实时报价数据

#### 需求: 实时股价提取

**描述:** 系统必须能够获取股票实时报价

**数据字段:**
- 股票代码 (stock_code)
- 现价 (current_price)
- 涨跌额 (change_amount)
- 涨跌率 (change_percent)
- 开盘价 (open_price)
- 最高价 (high_price)
- 最低价 (low_price)
- 昨收价 (prev_close)
- 成交量 (volume)
- 成交额 (turnover)

**验收标准:**
- [ ] 实时数据延迟 < 3 秒
- [ ] 数据准确率 > 99.5%
- [ ] 支持同时查询 500 只股票
- [ ] 并发查询响应时间 < 5 秒

**场景:**

```python
# 场景 1: 获取单只股票报价
quote = await scraper.get_realtime_quote("0700.HK")

# 场景 2: 批量获取报价
quotes = await scraper.get_batch_quotes(["0700.HK", "0388.HK", "1398.HK"])

# 场景 3: 获取活跃股票列表
active_stocks = await scraper.get_active_stocks(min_volume=1000000)
```

---

### 3. 股票基本信息

#### 需求: 提取公司基本信息

**描述:** 系统必须能够提取股票的基本公司信息

**数据字段:**
- 公司名称 (company_name)
- 公司名称英文 (company_name_en)
- 注册地 (incorporation_place)
- 行业 (industry)
- 主营业务 (business_scope)
- 上市日期 (listing_date)
- 发行价格 (issue_price)
- 总股本 (total_shares)
- 流通股本 (public_shares)
- 董事 (directors)
- 网址 (website)

**验收标准:**
- [ ] 基本信息完整率 > 90%
- [ ] 行业分类准确率 > 95%
- [ ] 网站可访问性检查
- [ ] 数据更新及时性检查

**场景:**

```python
# 场景 1: 获取公司基本信息
info = await scraper.get_company_info("0700.HK")

# 场景 2: 批量获取公司信息
infos = await scraper.get_batch_company_info(["0700.HK", "0388.HK"])

# 场景 3: 按行业获取公司列表
companies = await scraper.get_companies_by_industry("Technology")
```

---

### 4. 历史价格数据

#### 需求: 获取历史价格数据

**描述:** 系统必须能够获取股票历史价格数据

**数据字段:**
- 日期 (date)
- 开盘价 (open)
- 最高价 (high)
- 最低价 (low)
- 收盘价 (close)
- 成交量 (volume)
- 成交额 (turnover)
- 调整收盘价 (adj_close)

**验收标准:**
- [ ] 历史数据回溯 > 10 年
- [ ] 日数据提取时间 < 10 秒
- [ ] 分钟数据提取时间 < 30 秒
- [ ] 数据完整性检查通过率 > 98%

**场景:**

```python
# 场景 1: 获取日线数据
daily_data = await scraper.get_historical_data(
    stock_code="0700.HK",
    start_date=date(2020, 1, 1),
    end_date=date(2025, 10, 27),
    granularity="daily"
)

# 场景 2: 获取分钟数据
minute_data = await scraper.get_historical_data(
    stock_code="0700.HK",
    date=date(2025, 10, 27),
    granularity="1min"
)

# 场景 3: 获取调整后价格
adj_data = await scraper.get_adjusted_data(
    stock_code="0700.HK",
    start_date=date(2020, 1, 1),
    end_date=date(2025, 10, 27)
)
```

---

### 5. 分红配股信息

#### 需求: 提取分红配股数据

**描述:** 系统必须能够提取股票分红配股信息

**数据字段:**
- 公告日期 (announcement_date)
- 除权日期 (ex_date)
- 派息日 (payment_date)
- 分红类型 (dividend_type)
- 每股分红 (dividend_per_share)
- 配股比例 (rights_ratio)
- 配股价格 (rights_price)
- 红股 (bonus_shares)

**验收标准:**
- [ ] 分红数据完整率 > 95%
- [ ] 支持历史分红查询 > 10 年
- [ ] 分红收益率计算准确
- [ ] 除权除息日准确

**场景:**

```python
# 场景 1: 获取分红历史
dividends = await scraper.get_dividend_history("0700.HK")

# 场景 2: 获取即将除权股票
ex_right_stocks = await scraper.get_ex_right_stocks(
    ex_date=date(2025, 11, 1)
)

# 场景 3: 计算分红收益率
yield_rate = await scraper.calculate_dividend_yield("0700.HK")
```

---

### 6. 财务数据

#### 需求: 提取财务指标

**描述:** 系统必须能够提取股票关键财务指标

**数据字段:**
- 报告期 (report_date)
- 总资产 (total_assets)
- 净资产 (net_assets)
- 营业收入 (revenue)
- 净利润 (net_profit)
- 每股收益 (eps)
- 每股净资产 (book_value)
- 资产负债率 (debt_ratio)
- 净资产收益率 (roe)

**验收标准:**
- [ ] 财务数据完整率 > 90%
- [ ] 数据准确性验证
- [ ] 季度/年度数据支持
- [ ] 数据一致性检查

**场景:**

```python
# 场景 1: 获取财务摘要
financials = await scraper.get_financial_summary("0700.HK")

# 场景 2: 获取多年财务数据
multi_year = await scraper.get_multi_year_financials(
    stock_code="0700.HK",
    years=5
)

# 场景 3: 计算财务比率
ratios = await scraper.calculate_financial_ratios(
    stock_code="0700.HK"
)
```

---

### 7. 批量处理与优化

#### 需求: 批量数据查询

**描述:** 系统必须支持高效的批量数据查询

**实现要求:**
- 并发查询优化
- 查询结果缓存
- 分页查询支持
- 查询限流保护
- 进度跟踪

**验收标准:**
- [ ] 批量查询 1000 只股票 < 60 秒
- [ ] 缓存命中率 > 80%
- [ ] 查询限流正常
- [ ] 错误隔离 100%

**场景:**

```python
# 场景 1: 批量查询报价
quotes = await scraper.batch_query_quotes(
    stock_codes=all_stocks,
    max_concurrency=20
)

# 场景 2: 分页查询历史数据
page_data = await scraper.paginated_query(
    query_type="historical",
    stock_code="0700.HK",
    page_size=1000,
    page=1
)

# 场景 3: 查询进度跟踪
progress = await scraper.get_batch_progress(task_id="123")
```

---

### 8. 数据质量保证

#### 需求: 数据验证与清洗

**描述:** 系统必须对提取的数据进行验证和清洗

**验证规则:**
- 价格数据合理性
- 成交量非负性
- 日期连续性
- 股票代码格式
- 数据完整性

**验收标准:**
- [ ] 数据验证准确率 > 99%
- [ ] 异常值识别率 > 95%
- [ ] 数据清洗正确率 100%
- [ ] 质量报告完整

**场景:**

```python
# 场景 1: 验证单只股票数据
quality = await scraper.validate_stock_data("0700.HK")

# 场景 2: 批量数据验证
batch_quality = await scraper.batch_validate_data(
    stock_codes=stock_list
)

# 场景 3: 数据质量报告
quality_report = await scraper.generate_quality_report(
    period="monthly"
)
```

---

## 数据格式规范

### 股票数据 JSON 格式

```json
{
  "stock_code": "0700.HK",
  "quote": {
    "current_price": 350.0,
    "change": 5.0,
    "change_percent": 1.45,
    "open": 348.0,
    "high": 352.0,
    "low": 347.0,
    "prev_close": 345.0,
    "volume": 25000000,
    "turnover": 8750000000.0
  },
  "company_info": {
    "name": "腾讯控股",
    "name_en": "Tencent Holdings",
    "sector": "Technology",
    "listing_date": "2004-06-16"
  },
  "timestamp": "2025-10-27T16:10:00"
}
```

---

## API 接口

### RESTful 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/stocks/list` | 获取股票列表 |
| GET | `/api/stocks/quote/{code}` | 获取实时报价 |
| GET | `/api/stocks/historical/{code}` | 获取历史数据 |
| GET | `/api/stocks/info/{code}` | 获取公司信息 |
| GET | `/api/stocks/dividend/{code}` | 获取分红信息 |
| GET | `/api/stocks/financial/{code}` | 获取财务数据 |
| POST | `/api/stocks/batch/quote` | 批量获取报价 |
| POST | `/api/stocks/batch/historical` | 批量获取历史数据 |

---

## 性能要求

### 查询性能
- 单只股票查询: < 500ms
- 批量查询 100 只: < 10 秒
- 批量查询 1000 只: < 60 秒
- 历史数据查询: < 2 秒

### 并发性能
- 并发查询数: 50
- 最大查询速率: 100 QPS
- 缓存并发读取: 500 QPS
- 数据库并发连接: 20

---

## 错误处理

### 错误类型
- 股票代码不存在
- 数据获取超时
- 网络连接错误
- 数据格式错误
- 频率限制触发

### 恢复策略
- 自动重试 (最多 3 次)
- 降级到缓存数据
- 延迟重试机制
- 错误聚合报告

---

## 测试要求

### 测试覆盖率
- 单元测试 > 90%
- 集成测试 > 85%
- API 测试 100%
- 性能测试通过

### 测试场景
- 正常查询流程
- 批量查询场景
- 异常数据处理
- 并发查询压力
- 数据一致性

---

## 文档要求

- API 参考文档
- 数据字段说明
- 使用示例代码
- 错误处理指南
- 性能调优建议

---

## 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| 1.0.0 | 2025-10-27 | 初始版本 | Claude Code |

---

## 批准状态

- [ ] 技术架构师审批
- [ ] 开发负责人审批
- [ ] 最终批准
