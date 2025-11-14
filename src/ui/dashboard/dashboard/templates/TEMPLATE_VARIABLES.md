# 报告模板变量说明

## 概述

本文档详细说明了报告模板系统中使用的所有 Jinja2 变量。这些变量用于动态生成报告内容，支持模板的灵活性和可定制性。

---

## 通用变量

所有模板都支持的通用变量：

| 变量名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `title` | string | 否 | 报告标题 | "性能分析报告" |
| `symbol` | string | 否 | 股票代码 | "0700.HK" |
| `period` | string | 否 | 分析期间 | "2023-01-01 至 2023-12-31" |
| `timestamp` | string | 否 | 生成时间 | "2025-11-09 10:00:00" |
| `now()` | function | - | 当前时间函数 | - |

---

## T460: Performance.html (性能分析模板)

### 核心指标变量

```python
# 收益率指标
total_return: float        # 总收益率 (%)
annual_return: float       # 年化收益率 (%)
monthly_returns: list      # 月度收益明细列表

# 风险指标
sharpe_ratio: float        # 夏普比率
sortino_ratio: float       # 索提诺比率
calmar_ratio: float        # 卡玛比率
information_ratio: float   # 信息比率
treynor_ratio: float       # 特雷诺比率
max_drawdown: float        # 最大回撤 (%)
volatility: float          # 波动率 (%)
win_rate: float            # 胜率 (%)
win_count: int             # 胜出交易数
loss_count: int            # 失败交易数
```

### 图表数据变量

```python
# 性能曲线数据
performance_data: dict = {
    "dates": list,         # 日期列表
    "portfolio": list,     # 投资组合收益率
    "benchmark": list      # 基准收益率
}

# 收益归因数据
attribution_data: dict = {
    "labels": list,        # 归因标签
    "values": list         # 归因值
}
```

### 月度收益数据格式

```python
monthly_returns = [
    {
        "date": "2023-01",     # 月份
        "return": 5.2,         # 月度收益率
        "cumulative": 5.2,     # 累计收益率
        "benchmark": 3.5,      # 基准收益率
        "alpha": 1.7           # 超额收益
    },
    # ... 更多月份
]
```

---

## T461: Risk.html (风险评估模板)

### 风险概览变量

```python
# 风险等级
overall_risk_level: string     # "low" | "medium" | "high"

# VaR 指标
var_90: float             # VaR 90%
var_95: float             # VaR 95%
var_99: float             # VaR 99%
cvar_95: float            # CVaR 95%

# 风险指标
beta: float               # Beta 系数
downside_deviation: float # 下行标准差
sharpe_ratio: float       # 夏普比率
sortino_ratio: float      # 索提诺比率
```

### 图表数据变量

```python
# VaR 分布数据
var_data: dict = {
    "returns": list,       # 日收益率列表
    "var_95": float,       # VaR 95% 值
    "max_y": int           # Y轴最大值
}

# 回撤数据
drawdown_data: dict = {
    "dates": list,         # 日期列表
    "values": list         # 回撤值列表
}

# 压力测试数据
stress_data: dict = {
    "scenarios": list,     # 压力场景列表
    "impact": list         # 影响值列表
}
```

### 风险事件数据格式

```python
risk_events = [
    {
        "date": "2023-03-15",      # 事件日期
        "description": "市场调整",   # 事件描述
        "severity": "high",         # 严重程度
        "loss": -8.5                # 损失百分比
    },
    # ... 更多事件
]
```

---

## T462: Comparison.html (策略对比模板)

### 策略数据变量

```python
strategies: list          # 策略列表（至少1个）
```

### 单个策略数据格式

```python
strategy = {
    "name": "KDJ策略",          # 策略名称
    "type": "技术分析",           # 策略类型
    "rank": 1,                   # 排名
    "total_return": 25.6,        # 总收益率
    "annual_return": 15.3,       # 年化收益率
    "volatility": 12.4,          # 波动率
    "sharpe_ratio": 1.8,         # 夏普比率
    "sortino_ratio": 2.1,        # 索提诺比率
    "calmar_ratio": 1.5,         # 卡玛比率
    "information_ratio": 0.8,    # 信息比率
    "max_drawdown": -10.2,       # 最大回撤
    "win_rate": 65.5,            # 胜率
    "trade_count": 156,          # 交易次数
    "rating": 5,                 # 评级 (1-5星)
    "pros": [                    # 优势列表
        "高夏普比率",
        "回撤控制良好"
    ],
    "cons": [                    # 劣势列表
        "交易频率较高",
        "对市场环境敏感"
    ],
    "recommendation": "适合稳健型投资者"  # 建议
}
```

### 图表数据变量

```python
# 性能对比数据
performance_comparison: dict = {
    "dates": list,               # 日期列表
    "strategies": [              # 策略列表
        {
            "name": "策略1",
            "returns": list      # 收益率列表
        },
        # ... 更多策略
    ]
}

# 风险-收益散点图数据
risk_return_data: dict = {
    "strategies": [              # 策略列表
        {
            "name": "策略名",
            "risk": 12.5,        # 风险 (波动率)
            "return": 15.3,      # 收益 (年化)
            "rank": 1            # 排名
        },
        # ... 更多策略
    ]
}

# 相关性矩阵数据
correlation_data: dict = {
    "strategies": list,          # 策略名称列表
    "matrix": list               # 相关性矩阵 (NxN)
}
```

---

## T463: Executive Summary (执行摘要模板)

### 概述信息

```python
report_title: string        # 报告标题
date_range: string          # 日期范围
executive_summary: string   # 执行摘要文本
report_id: string           # 报告ID
```

### KPI 指标

```python
# 资产指标
aum: float                  # 资产管理规模
aum_change: float           # 资产规模变化 (%)

# 收益指标
cumulative_return: float    # 累计收益率
annual_return: float        # 年化收益率
benchmark_return: float     # 基准收益率

# 风险指标
max_drawdown: float         # 最大回撤
sharpe_ratio: float         # 夏普比率
win_rate: float             # 胜率
win_count: int              # 胜出交易数
loss_count: int             # 失败交易数
```

### 主要发现数据格式

```python
key_findings = [
    {
        "type": "positive",           # 类型: positive | negative | neutral
        "icon": "check-circle",       # 图标名称
        "title": "发现标题",
        "description": "详细描述",
        "impact": "影响说明"           # 可选
    },
    # ... 更多发现
]
```

### 投资建议数据格式

```python
recommendations = [
    {
        "title": "建议标题",
        "description": "建议描述",
        "priority": "high",            # 优先级: high | medium | low
        "timeframe": "1-3个月"
    },
    # ... 更多建议
]
```

### 风险数据格式

```python
risks = [
    {
        "title": "风险标题",
        "description": "风险描述"
    },
    # ... 更多风险
]
```

### 行动计划数据格式

```python
action_items = [
    {
        "task": "任务描述",
        "owner": "负责人",
        "deadline": "截止日期",
        "priority": "high",        # 优先级: high | medium | low
        "completed": False         # 是否完成
    },
    # ... 更多任务
]
```

### 图表数据变量

```python
# 性能数据
performance_data: dict = {
    "dates": list,              # 日期列表
    "portfolio": list,          # 投资组合数据
    "benchmark": list           # 基准数据
}

# 风险数据
risk_data: dict = {
    "score": 65                 # 风险评分 (0-100)
}
```

---

## T464: Technical Appendix (技术附录模板)

技术附录模板主要使用静态内容，不需要动态变量。但支持以下可选变量：

```python
timestamp: string             # 生成时间
```

---

## 使用示例

### Python 代码示例

```python
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# 准备数据
data = {
    'title': '性能分析报告',
    'symbol': '0700.HK',
    'period': '2023-01-01 至 2023-12-31',
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_return': 25.6,
    'annual_return': 12.8,
    'sharpe_ratio': 1.85,
    'max_drawdown': -8.2,
    'volatility': 14.3,
    'win_rate': 62.5,
    'performance_data': {
        'dates': ['2023-01', '2023-02', ...],
        'portfolio': [0, 1.2, 2.5, ...],
        'benchmark': [0, 0.8, 1.1, ...]
    }
}

# 渲染模板
env = Environment(loader=FileSystemLoader('templates/'))
template = env.get_template('performance.html')
html = template.render(**data)

# 保存或返回
with open('report.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

### JavaScript 数据示例

```javascript
// 性能数据
const performanceData = {
    dates: ['2023-01', '2023-02', '2023-03', '2023-04', '2023-05'],
    portfolio: [0, 1.2, 2.5, 3.8, 4.5],
    benchmark: [0, 0.8, 1.1, 2.2, 2.8]
};

// 策略对比数据
const strategies = [
    {
        name: 'KDJ策略',
        type: '技术分析',
        rank: 1,
        total_return: 25.6,
        sharpe_ratio: 1.85,
        max_drawdown: -8.2,
        win_rate: 62.5,
        trade_count: 156,
        rating: 5,
        pros: ['高夏普比率', '回撤控制良好'],
        cons: ['交易频率较高'],
        recommendation: '适合稳健型投资者'
    }
    // ... 更多策略
];
```

---

## 数据验证

### 数值范围

- **收益率**: 可为负数，通常在 -100% 到 1000% 之间
- **比率** (夏普、索提诺等): 可为负数，通常在 -5 到 10 之间
- **胜率**: 0 到 100
- **回撤**: 0 到 -100 (负值)
- **风险评分**: 0 到 100

### 数据类型检查

```python
def validate_data(data):
    """验证数据格式"""
    required_types = {
        'total_return': (int, float),
        'sharpe_ratio': (int, float),
        'strategies': list
    }

    for key, expected_type in required_types.items():
        if key in data and not isinstance(data[key], expected_type):
            raise TypeError(f"{key} 必须是 {expected_type} 类型")
```

---

## 最佳实践

1. **始终提供必填变量**: 确保所有模板使用的变量都已定义
2. **使用适当的数值格式**: 百分比保留2位小数，比率保留2位小数
3. **处理空值**: 对可选变量提供默认值或空列表
4. **数据验证**: 在渲染前验证数据格式和范围
5. **性能优化**: 大数据集考虑分页或虚拟化
6. **本地化**: 支持多语言和不同地区格式
7. **打印优化**: 考虑使用 `@media print` 样式
8. **响应式设计**: 确保在不同屏幕尺寸下正常显示

---

## 常见错误

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| `UndefinedError` | 变量未定义 | 检查所有必填变量 |
| `TypeError` | 数据类型错误 | 验证变量类型 |
| `KeyError` | 字典键不存在 | 使用 `get()` 方法或提供默认值 |
| `NaN` 值 | 计算错误 | 检查计算逻辑，处理除零情况 |
| 图表不显示 | 数据格式错误 | 确保数组长度一致 |

---

## 更新日志

- **v1.0** (2025-11-09): 初始版本，支持所有5个模板
- 后续版本将根据需求添加更多变量和功能

---

## 联系支持

如有疑问或需要添加新变量，请联系开发团队。
