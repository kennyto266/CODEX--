# 🚀 完整量化交易系统 - 股票通用化说明

## 项目状态: ✅ 完全通用化

本系统已经**完全通用化**，支持分析**任何港股代码**。无需修改代码，只需输入不同的股票代码即可进行分析、回测和策略优化。

---

## 核心特性

### 1. 完全参数化设计
- ✅ 所有 API 端点使用 `{symbol}` 参数接受任何股票代码
- ✅ Web UI 支持实时输入任何股票代码
- ✅ 无需修改源代码即可切换股票

### 2. 支持多种使用方式

```
┌─────────────────────────────────┐
│   Web UI 界面                    │
│ http://localhost:8001           │
│ (最简单，推荐新手)              │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   RESTful API 接口              │
│ /api/analysis/{symbol}          │
│ /api/strategy-optimization/{s}  │
│ (用于集成，推荐开发者)          │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   命令行工具                     │
│ python analyze_stock_cli.py 0700│
│ (便捷快速，推荐高级用户)        │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Python 脚本                    │
│ batch_stock_analysis.py         │
│ (批量处理，推荐批量分析)        │
└─────────────────────────────────┘
```

---

## 快速开始

### 方式 1: Web UI (最简单)

```bash
# 1. 启动系统
python complete_project_system.py

# 2. 打开浏览器
http://localhost:8001

# 3. 输入股票代码（如 0700.HK）并点击分析
```

**支持的操作:**
- 📊 技术分析 - 查看技术指标
- 🔄 策略回测 - 评估策略性能
- 🚀 策略优化 - 找出最佳参数
- ⚠️ 风险评估 - 评估风险等级
- 😊 市场情绪 - 分析市场情绪

---

### 方式 2: 命令行工具 (推荐)

```bash
# 基础分析
python analyze_stock_cli.py 0700.HK

# 策略优化（所有策略）
python analyze_stock_cli.py 0700.HK --optimize

# 优化特定策略（ma, rsi, macd, bb）
python analyze_stock_cli.py 0700.HK --optimize --strategy macd

# 批量分析多个股票
python analyze_stock_cli.py 0700.HK 2800.HK 0939.HK

# 自定义超时时间
python analyze_stock_cli.py 0700.HK --timeout 120
```

**输出示例:**
```
✅ 服务器已连接

📊 正在分析 0700.HK...

======================================================================
📈 0700.HK 分析报告
======================================================================

📍 基本信息:
   当前价格: ¥608.00
   数据点数: 865
   分析耗时: 0.05s

📊 技术指标:
   SMA(20): 648.55
   RSI(14): 33.59
   MACD: 0.91
   ...

💰 回测结果:
   总收益率: 27.74%
   Sharpe 比率: 0.669
   ...
```

---

### 方式 3: 批量分析脚本

```bash
python batch_stock_analysis.py
```

**功能:**
- 分析多个股票
- 生成汇总报告
- 导出详细报告到文件
- 自动比较不同股票的表现

---

### 方式 4: API 集成

```python
import requests

# 分析单个股票
response = requests.get("http://localhost:8001/api/analysis/0700.HK")
data = response.json()

# 优化策略
response = requests.get(
    "http://localhost:8001/api/strategy-optimization/0700.HK",
    params={"strategy_type": "macd"}
)
data = response.json()
```

---

## API 端点

### 1. 技术分析

```
GET /api/analysis/{symbol}
```

**参数:**
- `symbol`: 股票代码（如 0700.HK）

**返回值:**
```json
{
  "success": true,
  "data": {
    "symbol": "0700.HK",
    "current_price": 608.0,
    "indicators": {
      "sma_20": 648.55,
      "rsi": 33.59,
      "macd": 0.91,
      ...
    },
    "backtest": {...},
    "risk": {...},
    "sentiment": {...}
  }
}
```

### 2. 策略优化

```
GET /api/strategy-optimization/{symbol}?strategy_type={type}
```

**参数:**
- `symbol`: 股票代码
- `strategy_type`: 策略类型 (all, ma, rsi, macd, bb)

**返回值:**
```json
{
  "success": true,
  "data": {
    "best_strategies": [...],
    "total_strategies": 150,
    "best_sharpe_ratio": 1.066
  }
}
```

### 3. 健康检查

```
GET /api/health
```

---

## 支持的股票代码

| 代码 | 公司 | 说明 |
|------|------|------|
| 0700.HK | 腾讯控股 | 科技行业龙头 |
| 2800.HK | 宝马集团 | 汽车行业 |
| 0939.HK | 中国建设银行 | 金融行业 |
| 0001.HK | 长和 | 综合类公司 |
| 0005.HK | 汇丰控股 | 金融服务 |

**所有港股代码都支持！格式: 股票代码.HK**

---

## 分析功能详解

### 1. 技术分析 (Technical Analysis)

系统计算以下技术指标:

| 指标 | 周期 | 说明 |
|------|------|------|
| SMA | 20, 50 | 简单移动平均线 |
| EMA | 20 | 指数移动平均线 |
| RSI | 14 | 相对强弱指数 |
| MACD | 12,26,9 | 移动平均线收敛/发散 |
| 布林带 | 20, 2σ | 波动率指标 |
| ATR | 14 | 平均真实波幅 |

### 2. 策略回测 (Backtesting)

使用 SMA 交叉策略回测，计算:
- 总收益率
- 年化收益率
- Sharpe 比率
- 最大回撤
- 交易次数
- 最终投资组合价值

### 3. 策略优化 (Strategy Optimization)

支持四种策略的参数优化:

#### MA 交叉策略
```
参数: 短周期 (3-50), 长周期 (10-100)
示例: MA(5,20), MA(10,50), MA(20,200)
总组合数: ~2000+ 种
```

#### RSI 策略
```
参数: 超卖阈值 (10-40), 超买阈值 (50-80)
示例: RSI(20,80), RSI(30,70), RSI(25,75)
总组合数: ~900+ 种
```

#### MACD 策略
```
参数: 快周期 (8-16), 慢周期 (20-30), 信号周期 (7-11)
示例: MACD(12,26,9), MACD(10,22,7), MACD(8,24,5)
总组合数: 150 种
```

#### 布林带策略
```
参数: 周期 (15-30), 标准差倍数 (1-3)
示例: BB(20,2), BB(25,2), BB(27,1.5)
总组合数: 24 种
```

### 4. 风险评估 (Risk Assessment)

评估以下风险指标:
- **风险等级**: LOW / MEDIUM / HIGH
- **风险评分**: 0-100
- **波动率**: 年化波动率
- **VaR (95%)**: 95% 置信度下的最大损失
- **投资建议**: 基于风险的建议

### 5. 市场情绪 (Sentiment Analysis)

分析以下情绪指标:
- **情绪分数**: -100 到 +100
- **情绪等级**: Bullish / Neutral / Bearish
- **趋势强度**: 价格相对于移动平均线的偏离度
- **上涨/下跌天数**: 最近交易日统计

---

## 性能指标

| 操作 | 平均时间 | CPU占用 |
|------|---------|--------|
| 单个股票分析 | 2-5 秒 | 低 |
| MA 策略优化 | 5-15 秒 | 中 |
| RSI 策略优化 | 5-15 秒 | 中 |
| MACD 策略优化 | 10-20 秒 | 高 |
| 布林带策略优化 | 5-10 秒 | 中 |
| 全部策略优化 | 30-60 秒 | 很高 |

---

## 使用示例

### 示例 1: 快速分析单个股票

```bash
python analyze_stock_cli.py 0700.HK
```

### 示例 2: 找到最佳 MACD 参数

```bash
python analyze_stock_cli.py 0700.HK --optimize --strategy macd
```

输出:
```
最佳 MACD 策略:
策略名称: MACD(10,22,7)
Sharpe 比率: 1.066
年化收益率: 18.48%
最大回撤: -14.71%
```

### 示例 3: 批量分析多个股票

```python
from batch_stock_analysis import BatchAnalyzer

analyzer = BatchAnalyzer()
stocks = ["0700.HK", "2800.HK", "0939.HK"]
results = analyzer.analyze_stocks(stocks)
analyzer.generate_summary_report()
analyzer.generate_detailed_report(save_to_file=True)
```

### 示例 4: Python 集成

```python
import requests

# 分析 0700.HK
response = requests.get("http://localhost:8001/api/analysis/0700.HK")
data = response.json()

if data['success']:
    indicators = data['data']['indicators']
    risk = data['data']['risk']

    print(f"RSI: {indicators['rsi']:.2f}")
    print(f"风险等级: {risk['risk_level']}")
    print(f"建议: {risk['recommendation']}")
```

---

## 常见问题

### Q: 系统支持哪些股票？
A: 支持所有港股代码，格式为 `股票代码.HK`（如 0700.HK, 2800.HK）

### Q: 如何添加新的股票数据源？
A: 修改 `complete_project_system.py` 中的 `get_stock_data()` 函数，替换数据源 URL 即可。

### Q: Sharpe 比率多高才是好策略？
A:
- Sharpe > 1.0: 优秀策略
- Sharpe 0.5-1.0: 可接受策略
- Sharpe < 0.5: 不推荐策略

### Q: 最大回撤多少是可以接受的？
A:
- 最大回撤 > -10%: 优秀
- 最大回撤 -10% ~ -20%: 可接受
- 最大回撤 < -20%: 需要谨慎

### Q: 如何在生产环境使用？
A: 使用 `secure_complete_system.py`，它包含 CORS、输入验证等安全功能。

### Q: 支持实时数据吗？
A: 当前支持历史数据分析。可修改数据适配器以支持实时数据。

---

## 架构设计

```
┌─────────────────────────────────┐
│ 通用输入层                       │
│ (任何股票代码)                  │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 路由层                           │
│ API: /api/analysis/{symbol}      │
│ Web: 输入框                      │
│ CLI: 命令行参数                  │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 数据获取层 (参数化)              │
│ get_stock_data(symbol)           │
│ 支持任何股票代码                │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 分析引擎 (通用计算)              │
│ - 技术分析                      │
│ - 回测                          │
│ - 风险评估                      │
│ - 情绪分析                      │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 优化引擎 (参数搜索)              │
│ 测试不同参数组合                │
│ 返回最优结果                    │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ 输出层                           │
│ JSON / HTML / 文件              │
│ (支持任何格式)                  │
└─────────────────────────────────┘
```

---

## 部署选项

### 本地开发
```bash
python complete_project_system.py
```

### Docker 部署
```bash
docker-compose up -d
```

### 生产环境 (推荐)
```bash
python secure_complete_system.py
# 在 Nginx/Apache 后面运行
# 配置 HTTPS
# 启用日志轮转
```

---

## 扩展指南

### 添加新的数据源

```python
# 在 get_stock_data() 中修改
def get_stock_data(symbol: str, duration: int = 1825):
    # 修改 API URL
    url = 'http://你的-api-地址/数据'
    # ...
```

### 添加新的策略

```python
# 在 run_strategy_optimization_single_thread() 中添加
if strategy_type in ['all', 'your_strategy']:
    for param in range(...):
        result = your_strategy_function(df, param)
        if result:
            results.append(result)
```

### 添加新的技术指标

```python
# 在 calculate_technical_indicators() 中添加
indicators['your_indicator'] = calculate_indicator(df)
```

---

## 总结

✅ **项目完全通用化，支持：**

- 任何港股代码输入
- 多种使用方式（Web UI, API, CLI, Python）
- 所有功能都参数化
- 易于扩展和集成
- 生产就绪

**立即开始使用：**
```bash
python complete_project_system.py
# 访问 http://localhost:8001
```

---

## 联系支持

- 📚 文档: 查看 `STOCK_GENERALIZATION_GUIDE.md`
- 🛠️ 工具: `analyze_stock_cli.py`, `batch_stock_analysis.py`
- 🔧 源代码: `complete_project_system.py`

**享受量化交易分析！**
