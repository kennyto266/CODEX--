# 港交所数据获取 - 简单版指南

## 🎯 简介

这是一个**简化版**的港交所数据获取工具，基于您现有的 `hkex爬蟲/` 系统，提供简单、统一的数据接口。

---

## ✨ 核心功能

### 1. **市场统计数据** 📈
- 每日成交股份、成交股数
- 上升股数、下跌股数、涨跌不变
- 恒指和国企指数成交数据

### 2. **十大成交股票** 🏆
- 按成交股数排名的十大股票
- 按成交金额排名的十大股票
- 包含股票代码、名称、成交数据

### 3. **个股价格数据** 💰
- 基于统一API (`18.180.162.113:9191`)
- 获取港股个股价（开高低收量）
- 最近30天历史数据

### 4. **数据导出** 💾
- 自动导出为JSON格式
- 统一的数据结构
- 方便后续处理

---

## 🚀 快速开始

### 步骤1: 运行简单数据获取

```bash
python simple_hkex_data_fetcher.py
```

### 步骤2: 查看输出结果

```
============================================================
📊 港交所数据获取器 - 简单版
============================================================

📋 数据摘要:
{
  "market_data": {
    "exists": true,
    "file": "hkex爬蟲/data/hkex_all_market_data.csv",
    "records": 45,
    "date_range": "2025-09-02 ~ 2025-10-31"
  },
  ...
}

📈 市场统计数据:
{
  "status": "success",
  "message": "获取市场统计成功",
  "data": {
    "Date": "2025-10-31",
    "Shares_Traded": 1500000000,
    "Advanced_Stocks": 45,
    "Declined_Stocks": 52,
    ...
  }
}
```

### 步骤3: 获取的数据文件

运行后会生成：
- `data/hkex_simple_data.json` - 所有数据的JSON文件

---

## 📝 编程接口使用

### 1. 初始化

```python
from simple_hkex_data_fetcher import SimpleHKEXDataFetcher

fetcher = SimpleHKEXDataFetcher()
```

### 2. 获取市场统计

```python
# 获取最新市场统计
market = fetcher.get_market_statistics()

# 获取指定日期的市场统计
market = fetcher.get_market_statistics("2025-10-31")

print(market['data'])
```

### 3. 获取十大成交股票

```python
# 按成交股数获取
top_shares = fetcher.get_top_stocks(by="shares")

# 按成交金额获取
top_turnover = fetcher.get_top_stocks(by="turnover")

# 获取指定日期的十大成交
top_date = fetcher.get_top_stocks(date="2025-10-31")

print(top_shares['data'])
```

### 4. 获取个股价格

```python
# 获取腾讯股价
tencent = fetcher.get_stock_price("0700.hk")

# 获取港交所股价
hkex = fetcher.get_stock_price("0388.hk")

print(tencent['data'])
```

### 5. 导出数据

```python
# 导出为JSON
all_data = {
    "market": fetcher.get_market_statistics(),
    "top_stocks": fetcher.get_top_stocks(),
    "stock": fetcher.get_stock_price("0700.hk")
}

fetcher.export_to_json(all_data, "my_hkex_data.json")
```

---

## 📊 数据结构

### 市场统计数据

```json
{
  "Date": "2025-10-31",
  "Shares_Traded": 1500000000,
  "Advanced_Stocks": 45,
  "Declined_Stocks": 52,
  "Unchanged_Stocks": 23
}
```

### 十大成交股票

```json
[
  {
    "Date": "2025-10-31",
    "Rank": 1,
    "Code": "0700",
    "Ticker": "00700",
    "Product": "股票",
    "Name_CHI": "腾讯控股",
    "Currency": "HKD",
    "Shares_Traded": 15000000,
    "Turnover_HKD": 5250000000,
    "High": 350.0,
    "Low": 345.0
  }
]
```

### 个股价格数据

```json
{
  "symbol": "0700.hk",
  "dates": ["2025-10-01", "2025-10-02", ...],
  "close_prices": [348.5, 350.0, ...],
  "volumes": [1200000, 1100000, ...]
}
```

---

## 🔧 依赖要求

确保已安装：

```bash
pip install pandas requests
```

---

## 📁 文件结构

```
项目根目录/
├── hkex爬蟲/                    # 现有爬虫系统
│   ├── src/                     # 爬虫源码
│   └── data/                    # 爬取的数据
│       ├── hkex_all_market_data.csv    # 市场统计
│       └── top_stocks/                 # 十大成交股票
│           ├── top_stocks_by_shares_all.csv
│           └── top_stocks_by_turnover_all.csv
├── simple_hkex_data_fetcher.py  # 简单数据获取器 ⭐
├── data/                        # 输出目录
│   └── hkex_simple_data.json    # 导出的JSON数据
└── SIMPLE_HKEX_DATA_GUIDE.md    # 本指南
```

---

## ⚙️ 高级用法

### 1. 批量获取多个股票价格

```python
symbols = ["0700.hk", "0388.hk", "1398.hk", "0939.hk"]

for symbol in symbols:
    data = fetcher.get_stock_price(symbol)
    print(f"{symbol}: {data['data']['close_prices'][-1]}")
```

### 2. 获取日期范围的数据

```python
from datetime import datetime, timedelta

# 获取过去7天的市场统计
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

dates = []
current = start_date
while current <= end_date:
    date_str = current.strftime("%Y-%m-%d")
    market = fetcher.get_market_statistics(date_str)
    if market['status'] == 'success':
        dates.append(market['data'])
    current += timedelta(days=1)

print(f"获取了 {len(dates)} 天的数据")
```

### 3. 自定义数据筛选

```python
# 获取十大成交股票中成交额超过1亿的
top_stocks = fetcher.get_top_stocks(by="turnover")
high_volume_stocks = [
    stock for stock in top_stocks['data']
    if stock['Turnover_HKD'] > 100000000
]

print(f"高成交额股票数量: {len(high_volume_stocks)}")
```

---

## 📈 使用示例

### 示例1: 简单的数据查看器

```python
from simple_hkex_data_fetcher import SimpleHKEXDataFetcher
import json

fetcher = SimpleHKEXDataFetcher()

# 获取今天的数据
today = datetime.now().strftime("%Y-%m-%d")

market = fetcher.get_market_statistics(today)
top = fetcher.get_top_stocks(date=today)

print(f"📅 日期: {today}")
print(f"📈 成交股份: {market['data']['Shares_Traded']:,}")
print(f"🏆 十大成交股数第一: {top['data'][0]['Name_CHI']}")
print(f"💰 成交金额: {top['data'][0]['Turnover_HKD']:,}")
```

### 示例2: 股票价格监控

```python
def monitor_stock(symbol):
    data = fetcher.get_stock_price(symbol)
    if data['status'] == 'success':
        prices = data['data']['close_prices']
        volumes = data['data']['volumes']

        # 计算涨跌幅
        if len(prices) >= 2:
            change = prices[-1] - prices[-2]
            change_pct = (change / prices[-2]) * 100

            print(f"\n{symbol} 最新价格:")
            print(f"  当前价格: {prices[-1]}")
            print(f"  涨跌额: {change:+.2f}")
            print(f"  涨跌幅: {change_pct:+.2f}%")
            print(f"  成交量: {volumes[-1]:,}")

# 监控多只股票
symbols = ["0700.hk", "0388.hk", "1398.hk"]
for symbol in symbols:
    monitor_stock(symbol)
```

---

## ❗ 常见问题

### Q1: 提示"数据不存在，请先运行爬虫"

**A1**: 需要先运行HKEX爬虫获取数据：

```bash
cd hkex爬蟲
npm install
npm run start:hkex        # 获取市场数据
npm run start:top-stocks  # 获取十大成交股票
```

### Q2: 股票价格获取失败

**A2**: 检查网络连接，统一API服务需要互联网访问：

```python
# 测试网络连接
import requests

try:
    response = requests.get('http://18.180.162.113:9191/inst/getInst?symbol=0700.hk&duration=1')
    print(f"API状态: {response.status_code}")
except Exception as e:
    print(f"网络错误: {e}")
```

### Q3: 数据格式错误

**A3**: 确保CSV文件格式正确，检查文件是否存在：

```python
import os

market_file = "hkex爬蟲/data/hkex_all_market_data.csv"
if os.path.exists(market_file):
    print("✅ 市场数据文件存在")
else:
    print("❌ 市场数据文件不存在，请运行爬虫")
```

---

## 🎯 下一步

### 1. 扩展数据类型
- 可以根据需要添加更多数据源
- 例如：ETF数据、期货数据、新股数据等

### 2. 数据分析
- 使用pandas进行数据分析
- 生成图表和报告

### 3. 定时更新
- 设置定时任务，每天自动获取最新数据
- 可以使用cron或Windows计划任务

### 4. 数据库存储
- 将数据存储到数据库（如SQLite、PostgreSQL）
- 方便历史数据查询和分析

---

## 📞 支持

如有问题，请检查：
1. 爬虫数据是否存在
2. 网络连接是否正常
3. Python包是否已安装

---

**总结**: 这个简单版工具提供了港交所核心数据的快速获取接口，适合日常数据查询和简单的分析需求。如需更复杂的功能，可以在此基础上扩展。

**版本**: v1.0.0
**更新**: 2025-11-01
