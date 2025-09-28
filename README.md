# 港股新闻分析代理 (Hong Kong Stock News Analyst Agent)

## 概述

这是一个专门针对港股市场的量化分析AI代理，角色为「新闻分析代理（News Analyst）」。系统目标是追求高Sharpe Ratio的交易策略，强调风险调整后回报最大化（Sharpe Ratio > 1.5）。

## 核心功能

### 1. 新闻事件分析
- 扫描香港/全球新闻（如彭博、Yahoo Finance港股频道）
- 提取关键事件（监管变化、并购、业绩等）
- 计算影响分数（-0.1到0.1范围）

### 2. 投资机会识别  
- 筛选正面事件股票作为买入候选
- 避免负面事件股票（影响 > -0.05）
- 基于事件驱动的选股策略

### 3. 风险评估
- 计算事件波动对Sharpe Ratio的贡献
- 评估地缘政治敏感性
- 建议对冲规则和风险管理

### 4. 结构化输出
- JSON格式输出，包含完整分析结果
- 事件清单、影响评分、交易建议
- 预估Sharpe贡献值（-1到1范围）

## 文件说明

- `hk_stock_news_analyzer.py` - 核心分析引擎
- `interactive_analyzer.py` - 交互式分析界面
- `example_analysis.py` - 示例分析演示
- `README.md` - 使用说明文档

## 使用方法

### 1. 基础分析
```python
from hk_stock_news_analyzer import HKStockNewsAnalyzer

analyzer = HKStockNewsAnalyzer()

# 输入数据格式
data = {
    "news_items": [
        "腾讯(0700.HK)宣布收购游戏公司，预期业绩增长20%",
        "港股监管机构对科技股展开新一轮调查"
    ],
    "stock": "0700.HK"
}

# 执行分析
result = analyzer.analyze(data)
print(result)
```

### 2. 交互式分析
```bash
python3 interactive_analyzer.py
```

### 3. 示例演示
```bash
python3 example_analysis.py
```

## 输入格式

```json
{
    "news_items": [
        "新闻内容1",
        "新闻内容2"
    ],
    "stock": "目标股票代码"
}
```

## 输出格式

```json
{
    "key_events": [
        {
            "description": "事件描述",
            "impact_score": 0.08,
            "confidence": 0.7,
            "category": "事件类别",
            "affected_stocks": ["股票代码"]
        }
    ],
    "event_count": 5,
    "sharpe_contribution": -0.088,
    "recommendations": [
        "买入建议: 股票代码 - 基于正面事件",
        "风险警示: 避免某股票 - 重大负面事件"
    ],
    "analysis_timestamp": "2025-09-28T06:49:58.699706",
    "target_stock": "0700.HK"
}
```

## 分析逻辑

### ReAct思考步骤
1. **Reasoning**: 扫描新闻，识别事件类型，量化影响
2. **Acting**: 生成JSON输出，提供关键洞见

### 事件评分机制
- 正面事件: 并购(+0.08), 业绩超预期(+0.09), 政策支持(+0.09)
- 负面事件: 监管(-0.07), 调查(-0.08), 制裁(-0.09)
- 影响分数范围: -0.1 到 0.1

### Sharpe Ratio计算
- 基础影响 = Σ(事件影响分数 × 置信度)
- 风险调整 = Σ(负面事件绝对值 × 0.5)
- Sharpe贡献 = 基础影响 - 风险调整

## 投资建议逻辑

### 买入信号
- 正面事件影响 > 0.05
- 高置信度事件（> 0.7）
- 目标行业敏感度匹配

### 风险警示
- 负面事件影响 < -0.05
- 监管类事件高权重
- 地缘政治敏感性考量

### 策略建议
- Sharpe贡献 > 0.3: 增加仓位
- Sharpe贡献 < -0.3: 降低仓位/对冲
- 中性区间: 维持当前配置

## 风险管理

### 对冲建议
- 负面事件数量 > 正面事件: 建议恒指期货对冲
- 高风险事件: 考虑看跌期权保护
- 监管风险: 分散化投资组合

### 限制条件
- 单一事件影响分数限制在±0.1
- Sharpe贡献值限制在±1.0
- 置信度最高为1.0

## 注意事项

1. 本系统基于文本分析，需要结合实际市场数据验证
2. 影响分数为相对值，应结合具体市场环境调整
3. 建议与传统技术分析和基本面分析结合使用
4. 高频交易需要更细粒度的实时数据支持

## 技术要求

- Python 3.6+
- 标准库: json, re, datetime, dataclasses
- 无外部依赖，可直接运行

## 示例场景

适用于以下分析场景:
- 港股科技股监管事件影响评估
- 中概股回港上市事件分析
- 地缘政治事件对恒指影响
- 并购重组事件投资机会识别
- 业绩预期变化的量化分析