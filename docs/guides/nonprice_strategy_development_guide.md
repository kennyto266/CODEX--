# 🎯 非价格数据策略开发指南
# Non-Price Data Strategy Development Guide

**目标**: 基于政府数据（HIBOR、访客数、交通等）开发量化交易策略
**参数优化**: 步长0-300，测试所有组合

---

## 📊 支持的非价格指标

### 1. HIBOR利率 (HKMA数据)
```
字段名: HIBOR_Overnight_%
数据类型: float
单位: %
频率: 每日
策略类型: 银行股
阈值范围: 0.0% - 10.0%
```

### 2. 访客入境统计 (旅游局数据)
```
字段名: Visitor_Count
数据类型: int
单位: 人
频率: 每月
策略类型: 零售股
阈值范围: 50,000 - 500,000
```

### 3. 交通速度 (运输署数据)
```
字段名: Traffic_Speed_kmh
数据类型: float
单位: km/h
频率: 每日
策略类型: 运输股
阈值范围: 0 - 100
```

### 4. 空气质量指数 (环保署数据)
```
字段名: AQHI 或 avg_aqhi
数据类型: float
单位: 指数 (0-10+)
频率: 每日
策略类型: 医疗健康股
阈值范围: 0 - 20
```

---

## 🚀 快速开始

### 1. 运行默认策略
```bash
# 运行所有默认非价格数据策略
python nonprice_strategy_backtest.py --strategy all

# 运行单个策略
python nonprice_strategy_backtest.py --strategy hibor
python nonprice_strategy_backtest.py --strategy visitor
python nonprice_strategy_backtest.py --strategy traffic
python nonprice_strategy_backtest.py --strategy aqhi
python nonprice_strategy_backtest.py --strategy composite
```

### 2. 参数优化 (0-300组合)
```bash
# HIBOR策略参数优化 (3.0%-8.0% 买入, 1.0%-5.0% 卖出)
python nonprice_strategy_backtest.py --strategy optimize --optimize-type hibor --workers 8

# 访客策略参数优化 (150,000-300,000 买入, 100,000-250,000 卖出)
python nonprice_strategy_backtest.py --strategy optimize --optimize-type visitor --workers 8

# 优化所有策略
python nonprice_strategy_backtest.py --strategy optimize --optimize-type all --workers 8
```

### 3. 自定义股票和时间范围
```bash
# 测试港交所 (0388.HK)
python nonprice_strategy_backtest.py --symbol 0388 --strategy all

# 测试建设银行 (0939.HK)
python nonprice_strategy_backtest.py --symbol 0939 --strategy all

# 自定义时间范围
python nonprice_strategy_backtest.py --symbol 0700 --start 2023-01-01 --end 2024-12-31 --strategy all
```

---

## 📈 策略详细说明

### HIBOR银行股策略

**策略逻辑**:
```
买入条件: HIBOR > 5.0% (利率上升，银行股受益)
卖出条件: HIBOR < 3.0% (利率下降，银行股受压)
其他情况: 持有
```

**参数优化范围**:
```
买入阈值: 3.0%, 3.5%, 4.0%, 4.5%, 5.0%, 5.5%, 6.0%, 6.5%, 7.0%, 7.5%, 8.0% (11个值)
卖出阈值: 1.0%, 1.5%, 2.0%, 2.5%, 3.0%, 3.5%, 4.0%, 4.5%, 5.0% (9个值)
总组合数: 11 × 9 = 99个组合
```

**使用示例**:
```python
from nonprice_strategy_backtest import NonPriceDataBacktest

backtest = NonPriceDataBacktest('0700', '2022-01-01', '2025-01-01')
backtest.load_integrated_data()

# 运行HIBOR策略
result = backtest.run_hibor_strategy(buy_threshold=5.0, sell_threshold=3.0)

# 参数优化
results = backtest.optimize_hibor_parameters(max_workers=8)

# 获取最佳5个参数组合
best = backtest.get_best_strategies(results, top_n=5)
print("最佳HIBOR策略参数:")
for i, r in enumerate(best, 1):
    print(f"{i}. 买入阈值: {r['buy_threshold']:.1f}%, "
          f"卖出阈值: {r['sell_threshold']:.1f}%, "
          f"夏普比率: {r['sharpe_ratio']:.3f}")
```

### 访客零售股策略

**策略逻辑**:
```
买入条件: 访客 > 220,000 (旅游复苏，零售股受益)
卖出条件: 访客 < 200,000 (旅游疲软，零售股受压)
其他情况: 持有
```

**参数优化范围**:
```
买入阈值: 150,000 到 300,000 (步长5,000) = 31个值
卖出阈值: 100,000 到 250,000 (步长5,000) = 31个值
总组合数: 31 × 31 = 961个组合
```

**使用示例**:
```python
# 运行访客策略
result = backtest.run_visitor_strategy(buy_threshold=220000, sell_threshold=200000)

# 参数优化
results = backtest.optimize_visitor_parameters(max_workers=8)

# 查看最佳结果
best = backtest.get_best_strategies(results, top_n=10)
```

### 交通运输股策略

**策略逻辑**:
```
卖出条件: 交通速度 < 50 km/h (经济活动放缓，运输股受压)
其他情况: 持有
```

**参数优化范围**:
```
卖出阈值: 30, 35, 40, 45, 50, 55, 60, 65, 70 (9个值)
总组合数: 9个 (单参数策略)
```

### AQHI健康股策略

**策略逻辑**:
```
买入条件: AQHI > 10 (空气质量差，健康意识增强，医疗股受益)
其他情况: 持有
```

### 多因子综合策略

**策略逻辑**:
```
1. 标准化所有指标到0-1范围
2. 计算加权综合分数
3. 综合分数 > 0.7: 买入
4. 综合分数 < 0.3: 卖出
5. 其他情况: 持有
```

**默认权重**:
```python
weights = {
    'hibor': 0.25,      # HIBOR权重
    'visitor': 0.25,    # 访客权重
    'traffic': 0.25,    # 交通权重
    'aqhi': 0.25        # AQHI权重
}
```

---

## 🔧 高级功能

### 1. 自定义权重综合策略
```python
# 自定义权重：HIBOR权重更高
custom_weights = {
    'hibor': 0.4,       # 40%
    'visitor': 0.3,     # 30%
    'traffic': 0.2,     # 20%
    'aqhi': 0.1         # 10%
}

result = backtest.run_composite_strategy(weights=custom_weights)
```

### 2. 保存和加载优化结果
```python
# 保存优化结果
results = backtest.optimize_hibor_parameters(max_workers=8)
output_file = backtest.save_optimization_results(results, "hibor_best_params.json")

# 加载优化结果
import json
with open("hibor_best_params.json", 'r') as f:
    loaded_results = json.load(f)

best = loaded_results[0]
print(f"最佳参数: 买入{best['buy_threshold']:.1f}%, 卖出{best['sell_threshold']:.1f}%")
```

### 3. 批量测试多个股票
```python
symbols = ['0700', '0388', '0939', '1398', '3988']  # 腾讯、港交所、建行、工行、中行
results = {}

for symbol in symbols:
    backtest = NonPriceDataBacktest(symbol, '2022-01-01', '2025-01-01')
    backtest.load_integrated_data()
    results[symbol] = backtest.run_hibor_strategy()

# 比较结果
for symbol, result in results.items():
    print(f"{symbol}: 年化收益 {result['annual_return_pct']:.2f}%, "
          f"夏普比率 {result['sharpe_ratio']:.2f}")
```

---

## 📊 性能指标说明

### 回测结果指标
```
total_return_pct: 总收益率 (%)
annual_return_pct: 年化收益率 (%)
volatility_pct: 年化波动率 (%)
sharpe_ratio: 夏普比率
max_drawdown_pct: 最大回撤 (%)
total_trades: 总交易次数
signal_distribution: 信号分布 (BUY/SELL/HOLD天数)
```

### 优化结果指标
```
buy_threshold: 买入阈值
sell_threshold: 卖出阈值
total_return_pct: 总收益
annual_return_pct: 年化收益
sharpe_ratio: 夏普比率
max_drawdown_pct: 最大回撤
total_trades: 交易次数
```

---

## 🎯 策略评估标准

### 优秀策略标准
```
✅ 夏普比率 > 1.0
✅ 最大回撤 < 15%
✅ 年化收益 > 8%
✅ 交易次数 > 5 (避免过拟合)
✅ 总收益 > 基准收益
```

### 可接受策略标准
```
✅ 夏普比率 > 0.5
✅ 最大回撤 < 20%
✅ 年化收益 > 5%
```

### 避免的策略
```
❌ 夏普比率 < 0
❌ 最大回撤 > 30%
❌ 交易次数 = 1 (可能是过拟合)
❌ 只在牛市有效 (回撤期间)
```

---

## 🔍 常见问题

### Q1: 数据加载失败
**问题**: `集成数据文件不存在`
**解决**: 先运行数据集成
```bash
python integrate_stock_gov_data.py --symbol 0700 --capital 100000
```

### Q2: 缺少非价格指标
**问题**: `缺少必需的非价格指标`
**解决**: 确保集成数据包含以下列
```
HIBOR_Overnight_%
Visitor_Count
Traffic_Speed_kmh
Close
```

### Q3: 参数优化速度慢
**问题**: 参数优化耗时过长
**解决**: 增加并行工作线程
```bash
python nonprice_strategy_backtest.py --strategy optimize --optimize-type hibor --workers 8
```

### Q4: 结果不一致
**问题**: 不同时间范围结果差异大
**解决**: 检查数据质量，确保足够的历史数据
```python
# 检查数据完整性
print(f"数据条数: {len(self.data)}")
print(f"缺失值: {self.data.isnull().sum().sum()}")
print(f"日期范围: {self.data['Date'].min()} 到 {self.data['Date'].max()}")
```

---

## 🚀 进阶开发

### 1. 添加新的非价格指标
```python
def run_custom_strategy(self, custom_threshold: float, initial_capital: float = 100000.0):
    """自定义非价格指标策略"""
    df = self.data.copy()
    df = df.sort_values('Date').reset_index(drop=True)

    # 假设添加新指标: GDP_Growth_%
    df['Signal'] = 'HOLD'
    df.loc[df['GDP_Growth_%'] > custom_threshold, 'Signal'] = 'BUY'
    df.loc[df['GDP_Growth_%'] < -custom_threshold, 'Signal'] = 'SELL'

    result = self._backtest(df, '自定义GDP策略', initial_capital)
    return result
```

### 2. 实现机器学习策略
```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

def run_ml_strategy(self):
    """基于机器学习的非价格数据策略"""
    df = self.data.copy()

    # 准备特征 (非价格指标)
    features = ['HIBOR_Overnight_%', 'Visitor_Count', 'Traffic_Speed_kmh', 'GDP_Growth_%']
    X = df[features].fillna(0)
    y = df['Close'].pct_change().shift(-1)  # 未来收益率

    # 训练模型
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X_train, y_train)

    # 预测并生成信号
    predictions = model.predict(X_test)
    df.loc[X_test.index, 'Signal'] = np.where(predictions > 0, 'BUY', 'SELL')

    result = self._backtest(df, '机器学习策略', initial_capital)
    return result
```

### 3. 实现止损策略
```python
def run_stop_loss_strategy(self, stop_loss_pct: float = 0.05):
    """带止损的非价格数据策略"""
    df = self.data.copy()

    # 生成基础信号
    df['Signal'] = 'HOLD'
    df.loc[df['HIBOR_Overnight_%'] > 5.0, 'Signal'] = 'BUY'

    # 添加止损逻辑
    df['Stop_Loss'] = False
    df['Portfolio_Value'] = 0.0
    position = 0
    entry_price = 0

    for i, row in df.iterrows():
        if row['Signal'] == 'BUY' and position == 0:
            position = 1
            entry_price = row['Close']

        # 检查止损
        if position > 0:
            current_return = (row['Close'] - entry_price) / entry_price
            if current_return < -stop_loss_pct:
                df.loc[i, 'Stop_Loss'] = True
                position = 0

    result = self._backtest(df, f'HIBOR+止损{stop_loss_pct*100}%策略', initial_capital)
    return result
```

---

## 📞 快速命令参考

```bash
# 1. 快速运行所有策略
python nonprice_strategy_backtest.py --strategy all

# 2. HIBOR策略参数优化
python nonprice_strategy_backtest.py --strategy optimize --optimize-type hibor --workers 8

# 3. 访客策略参数优化
python nonprice_strategy_backtest.py --strategy optimize --optimize-type visitor --workers 8

# 4. 测试其他股票
python nonprice_strategy_backtest.py --symbol 0388 --strategy hibor

# 5. 自定义时间范围
python nonprice_strategy_backtest.py --symbol 0700 --start 2023-01-01 --end 2024-12-31 --strategy all

# 6. 输出结果到文件
python nonprice_strategy_backtest.py --strategy optimize --optimize-type hibor --output hibor_results.json
```

---

## ✅ 下一步行动

### 立即执行
1. **运行默认策略** - 了解系统性能
2. **参数优化** - 找到最佳参数组合
3. **多股票测试** - 验证策略稳健性

### 短期开发
1. **机器学习策略** - 随机森林/LSTM
2. **止损策略** - 风险控制
3. **多因子优化** - 更复杂的权重组合

### 长期目标
1. **实时交易系统** - 接入券商API
2. **另类数据** - 新闻、卫星图像
3. **高频交易** - 分钟级数据

---

**🚀 开始开发非价格数据策略！**

运行命令: `python nonprice_strategy_backtest.py --strategy all`
