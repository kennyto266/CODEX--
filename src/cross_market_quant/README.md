# 跨市场量化交易系统

基于OpenSpec规范文档实现的完整跨市场量化交易系统，集成了FX、商品、债券和港股数据，实现跨市场套利策略。

## 🎯 核心特性

### 1. 多市场数据适配器
- **FX适配器** (FXAdapter): 支持USD/CNH、EUR/USD等汇率数据
- **商品适配器** (CommodityAdapter): 支持黄金、石油等大宗商品数据
- **债券适配器** (BondAdapter): 支持美国国债收益率数据
- **HKEX适配器** (HKEXAdapter): 支持港交所股票数据

### 2. 累积回报过滤器（阿程策略12核心）
- 计算多天累积回报率（默认4天窗口）
- 使用±0.4%阈值过滤交易信号
- 支持动态阈值调整（基于市场波动率）
- 减少噪音交易，提高信号质量

### 3. 跨市场策略框架
- **USD/CNH → HSI策略**: 使用汇率预测港股走势
- **商品-股票策略**: 使用商品价格预测相关股票
- **策略组合**: 多策略动态权重组合

### 4. 增强回测引擎
- 14天固定持仓期管理
- 多资产组合支持
- 完整性能分析（夏普比率、最大回撤、胜率等）

### 5. 性能指标计算
- **信号统计**: 触发率、胜率分析
- **收益归因**: Brinson归因分析
- **风险调整收益**: 夏普、索提诺、卡玛比率

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│            跨市场量化交易系统                            │
├─────────────────────────────────────────────────────────┤
│  数据层: 多市场数据适配器                              │
│  ├── FXAdapter (USD/CNH, EUR/USD)                      │
│  ├── CommodityAdapter (Gold, Oil)                      │
│  ├── BondAdapter (US 10Y)                              │
│  └── HKEXAdapter (0700.HK, 0388.HK)                    │
├─────────────────────────────────────────────────────────┤
│  策略层: 累积回报过滤器 + 跨市场策略                    │
│  ├── CumulativeReturnFilter (4天窗口, ±0.4%阈值)       │
│  ├── FXHsiStrategy (USD/CNH → HSI)                     │
│  ├── CommodityStockStrategy (商品 → 股票)              │
│  └── StrategyPortfolio (策略组合)                      │
├─────────────────────────────────────────────────────────┤
│  回测层: 增强回测引擎                                  │
│  ├── 14天固定持仓期                                    │
│  ├── 多资产组合支持                                    │
│  └── 交易成本模型                                      │
├─────────────────────────────────────────────────────────┤
│  指标层: 性能指标计算                                  │
│  ├── SignalStatistics (信号统计)                        │
│  ├── ReturnAttribution (收益归因)                      │
│  └── RiskAdjustedReturns (风险调整收益)                │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装依赖

```bash
cd src/cross_market_quant
pip install -r requirements.txt
```

### 运行演示

```bash
# 运行完整系统演示
python demo_cross_market_system.py

# 运行测试套件
python test_cross_market_system.py
```

### 基本使用

```python
import asyncio
from cross_market_quant.strategies.fx_hsi_strategy import FXHsiStrategy

async def main():
    # 创建策略
    strategy = FXHsiStrategy(
        fx_symbol='USD_CNH',
        hsi_symbol='0700.HK',
        window=4,
        threshold=0.005,  # 0.5%阈值
        holding_period=14
    )

    # 生成信号
    signals = await strategy.generate_signals('2024-01-01', '2024-12-31')
    print(signals)

    # 运行回测
    backtest = await strategy.backtest('2024-01-01', '2024-12-31')
    print(backtest['performance'])

asyncio.run(main())
```

## 📈 策略逻辑

### USD/CNH → HSI策略（阿程策略12）

**核心假设**: USD/CNH汇率变动可以预测HSI走势

**信号生成逻辑**:
- USD/CNH 4天累积回报 ≥ 0.5% → HSI卖出信号
- USD/CNH 4天累积回报 ≤ -0.5% → HSI买入信号

**持仓管理**:
- 固定持仓期: 14天
- 信号触发后持仓14天
- 持仓期间忽略新信号

### 累积回报过滤器

**计算公式**:
```
Cumulative_Return(t) = (Price(t) - Price(t-window+1)) / Price(t-window+1)
```

**阈值过滤**:
- 基础阈值: ±0.4%
- 动态调整: 阈值 × (1 + 波动率 × 调整系数)

## 📊 性能指标

### 基础指标
- 总收益率
- 年化收益率
- 波动率
- 最大回撤

### 风险调整指标
- 夏普比率 (Sharpe Ratio)
- 索提诺比率 (Sortino Ratio)
- 卡玛比率 (Calmar Ratio)
- 信息比率 (Information Ratio)

### 信号指标
- 信号触发率
- 胜率
- 平均收益（信号时）

## 🧪 测试

系统包含完整的测试套件，验证所有核心功能：

```bash
python test_cross_market_system.py
```

测试覆盖:
- ✅ 累积回报计算（4天窗口）
- ✅ 信号阈值过滤（±0.4%）
- ✅ 信号统计计算
- ✅ 风险调整收益
- ✅ FX数据适配器
- ✅ HKEX数据适配器
- ✅ USD/CNH → HSI策略

## 📁 项目结构

```
src/cross_market_quant/
├── adapters/                    # 数据适配器
│   ├── __init__.py
│   ├── base_adapter.py         # 基础适配器
│   ├── fx_adapter.py          # FX适配器
│   ├── commodity_adapter.py   # 商品适配器
│   ├── bond_adapter.py        # 债券适配器
│   └── hkex_adapter.py        # HKEX适配器
├── strategies/                 # 策略模块
│   ├── __init__.py
│   ├── fx_hsi_strategy.py     # USD/CNH → HSI策略
│   ├── commodity_stock_strategy.py  # 商品-股票策略
│   └── strategy_portfolio.py  # 策略组合
├── metrics/                    # 性能指标
│   ├── __init__.py
│   ├── signal_statistics.py   # 信号统计
│   ├── return_attribution.py  # 收益归因
│   └── risk_adjusted_returns.py  # 风险调整收益
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── cumulative_filter.py   # 累积回报过滤器
│   └── volatility_calculator.py  # 波动率计算器
├── demo_cross_market_system.py  # 演示脚本
├── test_cross_market_system.py  # 测试脚本
└── README.md
```

## 🎯 OpenSpec规范符合性

本系统完全符合OpenSpec规范文档要求：

### ✅ 多市场数据适配器规范
- [x] FX数据适配器（USD/CNH, EUR/USD）
- [x] 商品数据适配器（Gold, Oil）
- [x] 债券数据适配器（US 10Y）

### ✅ 累积回报过滤器规范
- [x] 4天累积回报计算
- [x] ±0.4%阈值过滤
- [x] 动态阈值调整

### ✅ 跨市场策略框架规范
- [x] USD/CNH → HSI策略（阿程策略12）
- [x] 4天累积回报触发信号
- [x] 0.5%累积回报 → SELL信号

### ✅ 增强回测引擎规范
- [x] 14天固定持仓期
- [x] 多资产组合支持
- [x] 交易成本计算

### ✅ 性能指标规范
- [x] 信号统计（触发率、胜率）
- [x] 收益归因（Brinson分析）
- [x] 风险调整收益（Sharpe, Sortino, Calmar）

## 📝 开发日志

### 2025-10-30
- ✅ 实现多市场数据适配器（FX、商品、债券、HKEX）
- ✅ 实现累积回报过滤器（4天窗口，±0.4%阈值）
- ✅ 实现USD/CNH → HSI跨市场策略（阿程策略12）
- ✅ 实现策略组合功能
- ✅ 实现性能指标计算（信号统计、收益归因、风险调整收益）
- ✅ 创建演示脚本和测试套件

## 🤝 贡献

欢迎提交Issue和Pull Request来改进系统！

## 📄 许可证

本项目基于MIT许可证开源。

## 📧 联系

如有问题，请联系开发团队。
