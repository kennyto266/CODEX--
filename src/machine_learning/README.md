# 机器学习预测系统

## 概述

机器学习预测系统是一个完整的股票价格预测框架，集成了多种先进的机器学习算法，包括LSTM深度学习、随机森林和XGBoost。系统提供统一的API接口，支持特征工程、模型训练、预测生成和回测验证。

## 核心功能

### 1. 多种机器学习模型

#### LSTM神经网络
- **特点**: 深度学习模型，适合时间序列预测
- **优势**: 能够捕捉长期依赖关系
- **应用**: 股价序列预测、多步预测

#### 随机森林 (Random Forest)
- **特点**: 基于决策树的集成学习算法
- **优势**: 训练速度快，泛化能力强，提供特征重要性
- **应用**: 分类和回归预测

#### XGBoost
- **特点**: 梯度提升决策树算法
- **优势**: 高精度，快速训练，支持特征重要性分析
- **应用**: 结构化数据预测

### 2. 智能特征工程

自动生成100+技术指标特征：

#### 价格特征
- 价格变化率、高低价差、开盘收盘价差
- 相对于昨日收盘价的缺口
- 收盘价在高低价范围内的位置

#### 成交量特征
- 成交量变化率、移动平均
- 价格-成交量关系指标
- 成交量趋势分析

#### 技术指标
- **移动平均**: SMA, EMA (5, 10, 20, 50日)
- **相对强弱**: RSI (7, 14日)
- **MACD**: MACD线、信号线、柱状图
- **布林带**: 上下轨、宽度、位置
- **KDJ指标**: K、D、J值
- **CCI指标**: 商品通道指数
- **ADX指标**: 平均方向指数
- **ATR指标**: 真实波动范围
- **威廉指标**: %R

#### 波动率特征
- 历史波动率 (5, 10, 20日)
- 波动率比率
- 价格偏离度

#### 动量特征
- 价格动量 (5, 10, 20日)
- 成交量动量
- 相对强弱

#### 价格形态特征
- K线形态 (十字星、锤头线、流星线)
- 影线比例
- 趋势特征

#### 时间特征
- 星期几、月份、一年中第几天
- 是否月初/月末、是否周一/周五

#### 滞后特征
- 1-10日的价格和指标滞后
- 技术指标的滞后特征

#### 滚动窗口特征
- 滚动均值、标准差、偏度、峰度
- 价格-成交量相关性

### 3. 完整的预测流程

```python
from ml_prediction_system import MLPredictionSystem

# 1. 初始化系统
ml_system = MLPredictionSystem(models=['rf', 'xgboost'])

# 2. 训练模型
train_results = ml_system.train_all_models(
    data=stock_data,
    target_type='next_return',  # 'next_return', 'direction', 'price_change'
    periods=1
)

# 3. 生成预测
predictions = ml_system.predict(recent_data)

# 4. 生成交易信号
signal = ml_system.generate_signals(data, threshold=0.02)

# 5. 回测验证
backtest_results = ml_system.backtest_strategy(
    data=full_data,
    start_date='2023-01-01',
    end_date='2023-12-31'
)
```

### 4. 交易信号生成

根据预测结果自动生成交易信号：

- **BUY**: 预测收益率 > 阈值 (默认2%)
- **SELL**: 预测收益率 < -阈值
- **HOLD**: 预测收益率在[-阈值, 阈值]范围内

### 5. 策略回测

完整的回测框架：

- 逐日模拟交易
- 计算收益率、夏普比率、最大回撤
- 记录交易历史
- 生成权益曲线

## 安装依赖

```bash
# 核心依赖
pip install pandas numpy scikit-learn

# 深度学习
pip install tensorflow

# XGBoost
pip install xgboost

# 技术分析
pip install TA-Lib

# 可视化 (可选)
pip install matplotlib seaborn
```

## 快速开始

### 基本示例

```python
import pandas as pd
from ml_prediction_system import MLPredictionSystem

# 1. 准备数据 (数据格式: timestamp, open, high, low, close, volume)
data = pd.read_csv('stock_data.csv')

# 2. 初始化ML系统
ml_system = MLPredictionSystem(models=['rf', 'xgboost'])

# 3. 训练模型
results = ml_system.train_all_models(
    data,
    target_type='next_return',
    periods=1
)

# 4. 生成预测
predictions = ml_system.predict(data[-30:])

# 5. 生成交易信号
signal = ml_system.generate_signals(data[-60:], threshold=0.02)
print(f"交易信号: {signal['signal']}")
print(f"置信度: {signal['confidence']:.2%}")

# 6. 保存模型
ml_system.save_models('./models/')
```

### 高级功能

#### 使用LSTM进行多步预测

```python
from models.lstm_model import LSTMModel

# 初始化LSTM
lstm_model = LSTMModel(
    sequence_length=60,
    lstm_units=[50, 50],
    learning_rate=0.001
)

# 准备序列数据
features = lstm_model.prepare_features(data)
X, y = prepare_sequences(features, target, sequence_length=60)

# 训练
train_results = lstm_model.train(X, y)

# 多步预测
predictions = lstm_model.predict_sequence(features, steps=5)
```

#### 特征重要性分析

```python
# 获取特征重要性
importance = ml_system.models['rf'].get_feature_importance()

# 显示前10个重要特征
top_features = list(importance.items())[:10]
for feature, score in top_features:
    print(f"{feature}: {score:.4f}")

# 绘制特征重要性图
ml_system.models['rf'].plot_feature_importance(top_n=20, save_path='importance.png')
```

#### 自定义特征工程

```python
from feature_engineering import FeatureEngine

# 创建特征工程器
feature_engine = FeatureEngine()

# 自定义特征配置
feature_engine.feature_config = {
    'price_features': True,
    'volume_features': True,
    'technical_indicators': True,
    'volatility_features': True,
    'momentum_features': True,
    'price_pattern_features': False,  # 禁用某些特征
    'time_features': True,
    'lag_features': True,
    'rolling_features': True
}

# 生成特征
features = feature_engine.create_all_features(data)

# 创建自定义目标
target = feature_engine.create_target(
    data,
    target_type='direction',
    threshold=0.01
)
```

## API参考

### MLPredictionSystem

主类，提供统一的ML预测接口。

#### 初始化

```python
MLPredictionSystem(models=['rf', 'xgboost'])
```

**参数**:
- `models`: 要使用的模型列表，可选值: 'lstm', 'rf', 'xgboost'

#### 方法

##### train_all_models()
训练所有模型。

```python
train_all_modelse(
    data: pd.DataFrame,
    target_type: str = 'next_return',
    periods: int = 1,
    test_size: float = 0.2
) -> Dict[str, Any]
```

**参数**:
- `data`: 股票数据 (必须包含 timestamp, open, high, low, close, volume)
- `target_type`: 目标类型 ('next_return', 'direction', 'price_change')
- `periods`: 预测周期
- `test_size`: 测试集比例

**返回**: 训练结果字典

##### predict()
生成预测。

```python
predict(
    data: pd.DataFrame,
    model_name: Optional[str] = None,
    ensemble_method: str = 'average'
) -> Dict[str, np.ndarray]
```

**参数**:
- `data`: 股票数据
- `model_name`: 指定模型名称 (None表示所有模型)
- `ensemble_method`: 集成方法 ('average', 'weighted')

**返回**: 预测结果字典

##### generate_signals()
生成交易信号。

```python
generate_signals(
    data: pd.DataFrame,
    threshold: float = 0.02,
    model_name: Optional[str] = None
) -> Dict[str, Any]
```

**参数**:
- `data`: 股票数据
- `threshold`: 信号阈值
- `model_name`: 指定模型

**返回**: 交易信号字典 (signal, confidence, prediction)

##### backtest_strategy()
回测策略。

```python
backtest_strategy(
    data: pd.DataFrame,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000
) -> Dict[str, Any]
```

**参数**:
- `data`: 股票数据
- `start_date`: 开始日期
- `end_date`: 结束日期
- `initial_capital`: 初始资金

**返回**: 回测结果字典

### BaseMLModel

所有模型的基类。

#### 方法

##### train()
训练模型。

##### predict()
生成预测。

##### predict_proba()
生成概率预测 (仅分类模型)。

##### get_feature_importance()
获取特征重要性。

##### save_model()
保存模型。

##### load_model()
加载模型。

### FeatureEngine

特征工程类。

#### 方法

##### create_all_features()
创建所有特征。

##### create_target()
创建目标变量。

##### select_features()
特征选择。

## 性能指标

### 模型评估指标

#### 回归任务
- **MSE**: 均方误差
- **MAE**: 平均绝对误差
- **RMSE**: 均方根误差

#### 分类任务
- **Accuracy**: 准确率
- **Precision**: 精确率
- **Recall**: 召回率
- **F1-Score**: F1分数

### 回测指标
- **总收益率**: (最终价值 - 初始资金) / 初始资金
- **年化波动率**: 日收益率标准差 * sqrt(252)
- **夏普比率**: 年化超额收益 / 年化波动率
- **最大回撤**: (峰值 - 谷值) / 峰值
- **胜率**: 盈利交易 / 总交易

## 最佳实践

### 1. 数据质量

- 确保数据完整 (无缺失值)
- 数据量至少100天 (LSTM需要更多)
- 使用真实市场数据而非模拟数据

### 2. 模型选择

- **小数据集** (< 1000天): 随机森林
- **中等数据集** (1000-5000天): XGBoost
- **大数据集** (> 5000天): LSTM
- **特征重要性分析**: 随机森林或XGBoost
- **序列预测**: LSTM

### 3. 参数调优

```python
# XGBoost调优
model = XGBoostModel(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8
)

# LSTM调优
model = LSTMModel(
    sequence_length=60,
    lstm_units=[100, 50],
    dropout_rate=0.3,
    learning_rate=0.0005
)
```

### 4. 特征工程优化

- 移除高度相关的特征
- 使用特征选择方法
- 根据目标调整特征配置

### 5. 风险控制

- 设置合理的信号阈值
- 实施止损策略
- 分散投资

## 示例代码

### 完整示例: 腾讯股价预测

```python
import pandas as pd
from ml_prediction_system import MLPredictionSystem

# 1. 获取腾讯股票数据
data = fetch_stock_data('0700.HK', days=1000)  # 返回 DataFrame

# 2. 初始化系统
ml_system = MLPredictionSystem(models=['rf', 'xgboost'])

# 3. 训练模型
train_results = ml_system.train_all_models(
    data,
    target_type='next_return',
    periods=1
)

# 4. 评估模型
for model_name, result in train_results.items():
    if 'test_rmse' in result:
        print(f"{model_name} RMSE: {result['test_rmse']:.6f}")

# 5. 预测
predictions = ml_system.predict(data[-60:])

# 6. 生成信号
signal = ml_system.generate_signals(data[-60:], threshold=0.02)

# 7. 回测
backtest_results = ml_system.backtest_strategy(
    data=data,
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_capital=100000
)

# 8. 显示结果
print(f"交易信号: {signal['signal']}")
print(f"总收益率: {backtest_results['total_return']:.2%}")
print(f"夏普比率: {backtest_results['sharpe_ratio']:.2f}")

# 9. 保存模型
ml_system.save_models('./models/tencent/')
```

## 故障排除

### 常见错误

#### 1. "数据验证失败"

**原因**: 数据包含缺失值或异常值
**解决**:
```python
data = data.dropna()  # 移除空值
# 或
data = data.fillna(method='ffill')  # 前向填充
```

#### 2. "模型尚未训练"

**原因**: 调用预测前未训练模型
**解决**: 先调用 `train_all_models()`

#### 3. LSTM内存不足

**原因**: 数据量过大或序列长度过长
**解决**:
```python
# 减少序列长度
model = LSTMModel(sequence_length=30)

# 减少数据量
data = data[-1000:]  # 只用最近1000天

# 减少批次大小
model = LSTMModel(batch_size=16)
```

#### 4. 特征维度不匹配

**原因**: 预测时特征与训练时不一致
**解决**: 确保 `predict()` 和 `train()` 使用相同的特征

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0 (2025-10-30)
- 初始版本
- 支持LSTM、随机森林、XGBoost
- 完整的特征工程系统
- 交易信号生成
- 策略回测框架
