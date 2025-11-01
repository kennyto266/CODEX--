# 跨市场量化交易系统设计文档

## 架构设计原则

### 1. 模块化设计
每个能力模块独立开发、测试和部署，降低耦合度，提高可维护性。

### 2. 向后兼容
新功能不破坏现有API和数据结构，确保平滑升级。

### 3. 异步优先
使用 `async/await` 处理I/O密集型操作，提高系统吞吐量。

### 4. 向量化计算
使用Pandas/NumPy进行批量计算，避免Python循环。

## 详细架构

### 数据层设计

```
src/data_adapters/
├── __init__.py
├── base_adapter.py              # 现有基类
├── fx_adapter.py                # 新增：汇率数据适配器
├── commodity_adapter.py         # 新增：商品数据适配器
├── bond_adapter.py              # 新增：债券数据适配器
├── multi_market_service.py      # 新增：多市场数据服务
└── correlation_calculator.py    # 新增：相关性计算模块
```

**关键设计点**:
- 所有适配器继承自 `BaseAdapter`
- 统一的数据格式标准：pandas.DataFrame with datetime index
- 自动缓存机制减少API调用
- 支持多种数据源（Yahoo Finance, Alpha Vantage, FRED等）

### 策略层设计

```
src/strategies/
├── __init__.py
├── base_strategy.py             # 现有基类
├── cross_market_strategy.py     # 新增：跨市场策略基类
├── cumulative_filter.py         # 新增：累积回报过滤器
├── fx_hsi_strategy.py           # 新增：USD/CNH → HSI策略
├── commodity_stock_strategy.py  # 新增：商品 → 股票策略
└── bond_equity_strategy.py      # 新增：债券 → 股票策略
```

**关键设计点**:
- 策略组合机制：支持多策略并行运行
- 动态权重调整：根据历史绩效调整策略权重
- 信号阈值优化：基于市场波动率动态调整阈值

### 回测层设计

```
src/backtest/
├── enhanced_backtest_engine.py  # 扩展现有引擎
├── position_manager.py          # 新增：持仓期管理
├── transaction_cost_model.py    # 增强：交易成本模型
├── multi_asset_portfolio.py     # 新增：多资产组合
└── market_impact_simulator.py   # 新增：市场冲击模拟
```

**关键设计点**:
- 固定持仓期管理：支持阿程策略的14天持仓
- 滑点模型：基于市场深度模拟交易滑点
- 市场冲击：模拟大额交易对价格的影响

### 绩效层设计

```
src/performance/
├── metrics_calculator.py        # 增强：绩效指标计算
├── attribution_analysis.py      # 新增：收益归因分析
├── signal_statistics.py         # 新增：信号统计
└── risk_adjusted_returns.py     # 新增：风险调整收益
```

**关键设计点**:
- 因子归因：Brinson模型分析跨市场收益来源
- 信号质量评估：计算信号的预测能力和失效概率
- 风险调整：支持夏普、索提诺、卡尔玛等指标

## 数据流设计

```
┌──────────────┐
│ 数据获取层    │
│ (Adapters)  │
└──────┬───────┘
       │
       ↓
┌──────────────┐    ┌──────────────┐
│ 数据处理层    │    │ 相关性计算   │
│ (清洗/转换)  │───→│ (Correlation)│
└──────┬───────┘    └──────────────┘
       │
       ↓
┌──────────────┐
│ 累积回报过滤  │
│ (Cumulative) │
└──────┬───────┘
       │
       ↓
┌──────────────┐    ┌──────────────┐
│ 策略执行层    │    │ 信号生成     │
│ (Strategies) │───→│ (Signals)   │
└──────┬───────┘    └──────────────┘
       │
       ↓
┌──────────────┐    ┌──────────────┐
│ 回测执行层    │    │ 持仓管理     │
│ (Backtest)   │───→│ (Positions) │
└──────┬───────┘    └──────────────┘
       │
       ↓
┌──────────────┐
│ 绩效评估层    │
│ (Performance)│
└──────────────┘
```

## 核心算法

### 1. 累积回报计算
```python
def calculate_cumulative_return(prices: pd.Series, window: int = 4) -> pd.Series:
    """
    计算累积回报

    Formula: (Price[t] / Price[t-window]) - 1

    Args:
        prices: 价格序列
        window: 累积窗口（天）

    Returns:
        累积回报序列
    """
    return (prices / prices.shift(window - 1)) - 1
```

### 2. 信号过滤
```python
def filter_signals(cumulative_returns: pd.Series,
                   threshold: float = 0.004,
                   signal_type: str = 'both') -> pd.Series:
    """
    基于累积回报过滤信号

    Args:
        cumulative_returns: 累积回报
        threshold: 阈值（默认±0.4%）
        signal_type: 'long', 'short', 'both'

    Returns:
        信号序列 (1: 做多, -1: 做空, 0: 无信号)
    """
    if signal_type in ['long', 'both']:
        long_signals = (cumulative_returns < -threshold).astype(int)
    else:
        long_signals = pd.Series(0, index=cumulative_returns.index)

    if signal_type in ['short', 'both']:
        short_signals = -(cumulative_returns > threshold).astype(int)
    else:
        short_signals = pd.Series(0, index=cumulative_returns.index)

    return long_signals + short_signals
```

### 3. 固定持仓期管理
```python
class FixedHoldingPeriodManager:
    """
    固定持仓期管理器

    类似阿程策略的14天持仓机制
    """

    def __init__(self, holding_period: int = 14):
        self.holding_period = holding_period
        self.positions = {}  # {symbol: {'entry_date': datetime, 'signal': int}}

    def update_positions(self, signals: pd.Series, prices: pd.Series) -> pd.Series:
        """
        更新持仓状态

        Args:
            signals: 信号序列
            prices: 价格序列

        Returns:
            实际持仓序列
        """
        # 实现持仓期管理逻辑
        pass
```

### 4. 跨市场相关性计算
```python
def calculate_rolling_correlation(asset1: pd.Series,
                                 asset2: pd.Series,
                                 window: int = 60) -> pd.Series:
    """
    计算滚动相关性

    Args:
        asset1: 资产1价格
        asset2: 资产2价格
        window: 滚动窗口

    Returns:
        滚动相关系数
    """
    returns1 = asset1.pct_change()
    returns2 = asset2.pct_change()

    return returns1.rolling(window).corr(returns2)
```

## 配置设计

```yaml
# config/cross_market_config.yaml

cross_market:
  data_sources:
    fx:
      - name: "USD_CNH"
        source: "yahoo_finance"
        symbol: "USDCNY=X"
        enabled: true

    commodity:
      - name: "GOLD"
        source: "yahoo_finance"
        symbol: "GC=F"
        enabled: true
      - name: "OIL"
        source: "yahoo_finance"
        symbol: "CL=F"
        enabled: true

    bond:
      - name: "US_10Y"
        source: "fred"
        symbol: "DGS10"
        enabled: true

  strategies:
    fx_hsi:
      enabled: true
      window: 4
      threshold: 0.004
      holding_period: 14
      transaction_cost: 0.0002

    commodity_stock:
      enabled: true
      window: 5
      threshold: 0.005
      holding_period: 21

  backtest:
    initial_capital: 1000000
    commission_rate: 0.0002
    slippage: 0.0005
    market_impact: true

  performance:
    risk_free_rate: 0.02
    benchmark: "HSI"
    attribution_periods: [30, 60, 90]
```

## 性能优化

### 1. 缓存策略
- LRU缓存：API调用结果缓存1小时
- 内存映射：大数据文件使用mmap减少内存占用
- 增量计算：仅计算新增数据的相关性

### 2. 并行处理
- 多进程：跨市场数据获取并行执行
- 异步I/O：数据API调用使用aiohttp
- 向量化：所有计算使用Pandas/NumPy向量化

### 3. 数据压缩
- Parquet格式：列式存储压缩比高
- 分区存储：按年份分区减少I/O
- 索引优化：使用datetime索引快速查询

## 监控与告警

### 1. 数据质量监控
- 数据延迟监控：数据更新时间超过阈值告警
- 数据完整性检查：缺失值占比超过阈值告警
- 异常值检测：价格跳变超过3σ告警

### 2. 策略绩效监控
- 信号频率监控：信号触发频率异常告警
- 胜率监控：胜率低于历史均值2σ告警
- 回撤监控：回撤超过阈值告警

### 3. 系统性能监控
- API延迟监控：数据获取延迟超过阈值告警
- 内存使用监控：内存使用率超过80%告警
- CPU使用监控：CPU使用率超过90%告警

## 测试策略

### 单元测试
- 数据适配器：测试各种数据源的数据获取
- 策略逻辑：测试信号生成和过滤逻辑
- 绩效计算：测试各种绩效指标计算

### 集成测试
- 端到端测试：从数据获取到绩效报告的全流程
- 策略组合测试：多策略并行运行测试
- 回测验证：与历史回测结果对比验证

### 压力测试
- 大数据量测试：测试5年日频数据处理性能
- 高频信号测试：测试信号密集情况下的性能
- 并发测试：测试多用户同时使用系统的性能

## 部署策略

### 阶段1：基础数据层
- 部署多市场数据适配器
- 集成跨市场相关性计算
- **验证标准**: 能够获取USD/CNH和HSI数据，计算相关性

### 阶段2：策略层
- 部署累积回报过滤器
- 实现基础跨市场策略
- **验证标准**: 能运行类似阿程策略的策略

### 阶段3：回测层
- 增强回测引擎
- 添加固定持仓期管理
- **验证标准**: 支持14天持仓期的完整回测

### 阶段4：绩效层
- 完善绩效评估指标
- 添加收益归因分析
- **验证标准**: 生成完整的跨市场绩效报告

## 风险缓解

### 技术风险
- **数据源稳定性**: 实现多数据源备援，自动切换
- **计算性能**: 使用增量计算和并行处理优化性能
- **内存使用**: 实现数据分片和懒加载

### 业务风险
- **策略失效**: 实现策略绩效实时监控，自动停用失效策略
- **回测过拟合**: 使用时间序列交叉验证，避免look-ahead bias
- **市场异常**: 实现熔断机制，极端市场情况下自动暂停交易

---
