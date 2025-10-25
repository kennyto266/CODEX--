# 股票通用化使用指南

## 项目现状：已完全通用化 ✅

完整量化交易系统已经完全支持任何股票代码，您可以输入任何港股代码进行分析、回测和优化。

---

## 使用方式

### 1. Web UI 界面 (最简单)

#### 访问系统
```
http://localhost:8001
```

#### 使用步骤：
1. 在搜索框中输入股票代码（例如：0700.HK, 2800.HK, 0939.HK 等）
2. 点击"🔍 分析股票"按钮
3. 系统会自动进行以下分析：
   - 技术分析（SMA、RSI、MACD、布林带等）
   - 策略回测
   - 风险评估
   - 市场情绪分析

#### 策略优化
1. 切换到"策略优化"标签
2. 输入股票代码
3. 选择策略类型：
   - 全部策略
   - 移动平均交叉（MA）
   - RSI策略
   - MACD策略
   - 布林带策略
4. 点击"🔍 开始优化"开始参数优化

---

### 2. API 接口 (用于集成)

#### 技术分析 API
```bash
# 分析任何股票
curl "http://localhost:8001/api/analysis/{symbol}"

# 示例
curl "http://localhost:8001/api/analysis/0700.HK"
curl "http://localhost:8001/api/analysis/2800.HK"
curl "http://localhost:8001/api/analysis/0939.HK"
```

**返回数据包括：**
- 价格数据
- 技术指标（SMA、RSI、MACD、布林带、ATR）
- 回测结果
- 风险评估
- 市场情绪

#### 策略优化 API
```bash
# 对任何股票进行策略参数优化
curl "http://localhost:8001/api/strategy-optimization/{symbol}?strategy_type={type}"

# 示例
curl "http://localhost:8001/api/strategy-optimization/0700.HK?strategy_type=all"
curl "http://localhost:8001/api/strategy-optimization/2800.HK?strategy_type=macd"
curl "http://localhost:8001/api/strategy-optimization/0939.HK?strategy_type=bb"
```

**策略类型参数：**
- `all` - 全部策略
- `ma` - 移动平均交叉
- `rsi` - RSI策略
- `macd` - MACD策略
- `bb` - 布林带策略

#### 健康检查 API
```bash
curl "http://localhost:8001/api/health"
```

---

### 3. 支持的港股代码示例

| 股票代码 | 公司名称 | 说明 |
|---------|--------|------|
| 0700.HK | 腾讯控股 | 科技行业龙头 |
| 2800.HK | 宝马集团 | 汽车行业 |
| 0939.HK | CCB | 金融行业 |
| 0001.HK | 长和 | 综合类公司 |
| 0005.HK | 汇丰控股 | 金融服务 |

**所有港股代码都支持，格式为：股票代码.HK**

---

## 核心功能详解

### 1. 技术分析（通用于所有股票）
- **移动平均线** (SMA): SMA(20), SMA(50)
- **指数平滑平均** (EMA): EMA(20)
- **相对强弱指数** (RSI): RSI(14)
- **MACD**: MACD(12,26,9)
- **布林带**: BB(20,2)
- **平均真实波幅** (ATR): ATR(14)

### 2. 策略回测（支持自定义参数）

#### MA交叉策略
```
参数范围：短周期 3-50，长周期 10-100
例如：MA(5,20), MA(10,50), MA(20,200)
```

#### RSI策略
```
参数范围：超卖阈值 10-40，超买阈值 50-80
例如：RSI(20,80), RSI(30,70), RSI(25,75)
```

#### MACD策略
```
参数范围：快线周期 8-16, 慢线周期 20-30, 信号周期 7-11
例如：MACD(12,26,9), MACD(10,22,7), MACD(8,24,5)
```

#### 布林带策略
```
参数范围：周期 15-30，标准差倍数 1-3
例如：BB(20,2), BB(25,2), BB(27,1.5)
```

### 3. 性能指标（计算每个策略）
- **总收益率**: 累计收益百分比
- **年化收益率**: 年均回报率
- **波动率**: 收益波动程度
- **Sharpe比率**: 风险调整后收益（推荐指标）
- **最大回撤**: 从高峰到低谷的最大跌幅
- **胜率**: 盈利交易占比
- **交易次数**: 总交易笔数

### 4. 风险评估（自动评估）
- **风险等级**: LOW/MEDIUM/HIGH
- **风险评分**: 0-100
- **波动率**: 价格波动程度
- **VaR (95%)**: 95%置信度下的最大损失
- **投资建议**: 基于风险等级的建议

### 5. 市场情绪分析（实时分析）
- **情绪分数**: -100 到 +100
- **情绪等级**: Bullish/Neutral/Bearish
- **趋势强度**: 价格相对于移动平均线的偏离度
- **上涨/下跌天数**: 最近交易日的涨跌统计

---

## 高级用法

### Python 脚本集成

```python
import requests
import json

# 分析单个股票
symbol = "0700.HK"
response = requests.get(f"http://localhost:8001/api/analysis/{symbol}")
data = response.json()

if data['success']:
    indicators = data['data']['indicators']
    print(f"RSI: {indicators['rsi']:.2f}")
    print(f"MACD: {indicators['macd']:.2f}")
    print(f"Sharpe Ratio (Backtest): {data['data']['backtest']['sharpe_ratio']:.2f}")
```

### 批量分析多个股票

```python
stocks = ["0700.HK", "2800.HK", "0939.HK", "0001.HK"]

for stock in stocks:
    response = requests.get(f"http://localhost:8001/api/analysis/{stock}")
    data = response.json()
    if data['success']:
        risk = data['data']['risk']
        print(f"{stock}: 风险等级 {risk['risk_level']}, Sharpe {data['data']['backtest']['sharpe_ratio']}")
```

### 批量优化策略

```python
stocks = ["0700.HK", "2800.HK", "0939.HK"]
strategy_types = ["ma", "rsi", "macd", "bb"]

results = []
for stock in stocks:
    for strategy_type in strategy_types:
        response = requests.get(
            f"http://localhost:8001/api/strategy-optimization/{stock}",
            params={"strategy_type": strategy_type}
        )
        data = response.json()
        if data['success']:
            best = data['data']['best_strategies'][0]
            results.append({
                'stock': stock,
                'strategy': strategy_type,
                'best_sharpe': best['sharpe_ratio']
            })

# 输出最好的前10个策略
results_sorted = sorted(results, key=lambda x: x['best_sharpe'], reverse=True)
for i, r in enumerate(results_sorted[:10], 1):
    print(f"{i}. {r['stock']} - {r['strategy']}: Sharpe {r['best_sharpe']}")
```

---

## 常见问题

### Q: 系统支持哪些股票代码格式？
A: 支持港股代码格式，例如：0700.HK, 2800.HK, 0939.HK 等

### Q: 是否可以分析非港股？
A: 当前数据源主要支持港股。要添加其他市场，可修改 `get_stock_data()` 函数的数据源。

### Q: 如何选择最佳策略？
A: 优先选择 Sharpe 比率高（>1.0 为优秀）、最大回撤小（<-20% 为可接受）的策略。

### Q: API 响应时间？
A: 分析 API 通常 1-5 秒，优化 API 根据参数范围 10-60 秒。

### Q: 如何定制参数范围？
A: 修改 `run_strategy_optimization_single_thread()` 函数中的参数循环范围。

---

## 系统架构

```
┌─────────────────────────────────────┐
│      Web UI / API 请求              │
│  (输入任何港股代码，如 0700.HK)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   FastAPI 应用层                     │
│  /api/analysis/{symbol}             │
│  /api/strategy-optimization/{symbol}│
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   数据获取层 (通用化)                 │
│  get_stock_data(symbol)             │
│  支持任何股票代码                    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   核心分析引擎 (通用计算)             │
│  - 技术分析引擎                     │
│  - 回测引擎                         │
│  - 风险评估引擎                     │
│  - 情绪分析引擎                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   策略优化引擎 (并行计算)             │
│  - 参数搜索                         │
│  - 性能评估                         │
│  - 结果排序                         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   结果返回 (JSON 格式)               │
│  - 指标数据                         │
│  - 性能指标                         │
│  - 风险评分                         │
│  - 投资建议                         │
└─────────────────────────────────────┘
```

---

## 性能指标

| 操作 | 平均时间 | 最大股票数 |
|------|---------|----------|
| 单个股票分析 | 2-5 秒 | 无限制 |
| MA 策略优化 | 5-15 秒 | 无限制 |
| RSI 策略优化 | 5-15 秒 | 无限制 |
| MACD 策略优化 | 10-20 秒 | 无限制 |
| 布林带策略优化 | 5-10 秒 | 无限制 |
| 全部策略优化 | 30-60 秒 | 无限制 |

---

## 扩展说明

### 添加新的股票数据源

在 `get_stock_data()` 函数中修改数据 URL：

```python
def get_stock_data(symbol: str, duration: int = 1825):
    """获取股票数据 - 支持任何数据源"""
    # 修改这里以支持其他数据源
    url = 'http://your-data-api.com/getdata'
    params = {'symbol': symbol, 'duration': duration}
    # ...
```

### 添加新的交易策略

在 `run_strategy_optimization_single_thread()` 中添加新策略：

```python
if strategy_type in ['all', 'your_strategy']:
    for param1 in range(...):
        for param2 in range(...):
            result = your_strategy_function(df, param1, param2)
            if result:
                results.append(result)
```

---

## 总结

✅ **项目完全通用化**

- 支持任何港股代码输入
- API 接受 `{symbol}` 参数
- Web UI 支持实时输入不同股票
- 所有分析和优化功能都是参数化的
- 易于扩展支持其他股票市场

**立即开始使用：访问 http://localhost:8001**
