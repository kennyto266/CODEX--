# 港股量化分析AI代理团队 - Prompt模板集成

## 🎯 项目概述

本项目成功将您提供的7个港股量化分析AI代理prompt模板集成到现有的量化交易系统中。每个代理都专门针对港股市场优化，追求高Sharpe Ratio (>1.5)的交易策略，使用ReAct风格的结构化prompt。

## 🏗️ 系统架构

```
港股量化分析AI代理团队
├── Prompt模板系统 (hk_prompt_templates.py)
│   ├── 7个专业代理模板
│   ├── JSON格式标准化
│   └── 响应解析和验证
├── Prompt执行引擎 (hk_prompt_engine.py)
│   ├── 多LLM提供商支持
│   ├── 异步执行和错误处理
│   └── 执行统计和监控
├── 代理实现 (hk_prompt_agents.py)
│   ├── 7个专业代理类
│   ├── 消息队列集成
│   └── 数据适配器支持
└── 配置和文档
    ├── 配置文件
    ├── 使用指南
    └── 测试脚本
```

## 🤖 7个专业代理

### 1. 基本面分析代理 (Fundamental Analyst)
- **功能**: 分析PE比率、ROE、盈利成长率
- **输出**: 低估股票清单、平均PE、Sharpe贡献值
- **特点**: 专注恒生指数成分股，考虑地缘政治因素

### 2. 情绪分析代理 (Sentiment Analyst)
- **功能**: 量化社交媒体情绪分数
- **输出**: 情绪分数、平均情绪、情绪建议
- **特点**: 分析X、Weibo等平台，考虑情绪传染效应

### 3. 新闻分析代理 (News Analyst)
- **功能**: 提取关键事件，计算影响分数
- **输出**: 关键事件、事件数量、事件建议
- **特点**: 扫描彭博、Yahoo Finance等新闻源

### 4. 技术分析代理 (Technical Analyst)
- **功能**: 计算MA、RSI、MACD等技术指标
- **输出**: 交易信号、平均RSI、技术建议
- **特点**: 专注港股K线图和高流动性股票

### 5. 研究辩论代理 (Research Debate)
- **功能**: 整合各代理分析，平衡乐观/悲观观点
- **输出**: 乐观分数、悲观分数、平衡分数
- **特点**: 模拟Bullish/Bearish辩论，生成平衡观点

### 6. 交易执行代理 (Trader)
- **功能**: 基于分析结果生成交易订单
- **输出**: 交易订单、预期回报、执行建议
- **特点**: 考虑港股交易成本和T+0结算

### 7. 风险管理代理 (Risk Manager)
- **功能**: 计算VaR、Sharpe比率，控制风险暴露
- **输出**: VaR值、Sharpe比率、风险限额
- **特点**: 监测恒生指数曝险，进行压力测试

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install openai anthropic aiohttp pandas numpy
```

### 2. 配置LLM
```python
from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider

llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    api_key="your-openai-api-key",
    model="gpt-4",
    max_tokens=2000,
    temperature=0.1
)

prompt_engine = HKPromptEngine(llm_config)
```

### 3. 创建代理
```python
from src.agents.hk_prompt_agents import HKPromptAgentFactory
from src.agents.hk_prompt_templates import AgentType

# 创建所有代理
agents = HKPromptAgentFactory.create_all_agents(
    message_queue, system_config, prompt_engine
)

# 初始化代理
for agent in agents.values():
    await agent.initialize()
```

### 4. 执行分析
```python
# 准备市场数据
market_data = [{
    "symbol": "0700.HK",
    "timestamp": "2024-01-01T09:30:00",
    "open": 100.0, "high": 102.0, "low": 98.0, "close": 101.0, "volume": 1000000
}]

# 执行代理管道
results = await prompt_engine.execute_agent_pipeline(
    {"market_data": market_data}
)

# 处理结果
for agent_type, result in results.items():
    if result.success:
        print(f"{agent_type.value}: {result.explanation}")
        print(f"数据: {result.parsed_data}")
```

## 📁 文件结构

```
src/agents/
├── hk_prompt_templates.py      # Prompt模板系统
├── hk_prompt_engine.py         # Prompt执行引擎
├── hk_prompt_agents.py         # 代理实现
└── ...

config/
└── hk_prompt_agents_config.json  # 配置文件

docs/
└── hk_prompt_agents_guide.md     # 详细使用指南

examples/
└── hk_prompt_agents_demo.py      # 演示示例

test_hk_prompt_integration.py     # 集成测试
```

## 🔧 配置说明

### LLM提供商支持
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Claude**: Claude-3-Opus, Claude-3-Sonnet
- **Grok**: Grok-beta
- **本地模型**: 支持自定义API端点

### 代理配置
```json
{
  "analysis_symbols": ["0700.HK", "0005.HK", "0941.HK"],
  "lookback_days": 30,
  "analysis_interval_minutes": 5
}
```

### 风险管理
```json
{
  "max_drawdown_percent": 10.0,
  "target_sharpe_ratio": 1.5,
  "var_confidence_level": 0.95
}
```

## 🧪 测试和验证

### 运行集成测试
```bash
python test_hk_prompt_integration.py
```

### 运行演示示例
```bash
python examples/hk_prompt_agents_demo.py
```

### 测试覆盖
- ✅ Prompt模板加载和生成
- ✅ LLM引擎初始化和配置
- ✅ 代理创建和初始化
- ✅ 数据准备和格式化
- ✅ JSON解析和验证
- ✅ 消息队列集成
- ✅ 错误处理和恢复

## 📊 性能特性

### 执行模式
- **顺序执行**: 按依赖关系顺序执行代理
- **并行执行**: 同时执行多个独立代理
- **管道模式**: 支持复杂的代理协作流程

### 监控指标
- 执行次数和成功率
- 平均执行时间
- 错误统计和重试次数
- 资源使用情况

### 错误处理
- 自动重试机制
- 优雅降级
- 详细错误日志
- 性能告警

## 🔍 使用示例

### 基本分析流程
```python
# 1. 初始化系统
prompt_engine = HKPromptEngine(llm_config)
agents = HKPromptAgentFactory.create_all_agents(message_queue, system_config, prompt_engine)

# 2. 准备数据
market_data = get_hk_market_data()

# 3. 执行分析
results = await prompt_engine.execute_agent_pipeline({"market_data": market_data})

# 4. 处理结果
for agent_type, result in results.items():
    if result.success:
        process_analysis_result(agent_type, result.parsed_data)
```

### 高级用法
```python
# 并行执行特定代理
parallel_agents = [AgentType.FUNDAMENTAL_ANALYST, AgentType.TECHNICAL_ANALYST]
results = await prompt_engine.execute_parallel_agents(input_data, parallel_agents)

# 自定义prompt
custom_prompt = "你是一位专业的港股分析师..."
result = await prompt_engine.execute_prompt(AgentType.FUNDAMENTAL_ANALYST, input_data, custom_prompt)
```

## 🛠️ 扩展开发

### 添加新代理
1. 在`AgentType`枚举中添加新类型
2. 在`HKPromptTemplates`中添加prompt模板
3. 创建代理实现类
4. 在工厂类中注册

### 自定义prompt模板
```python
custom_template = PromptTemplate(
    agent_type=AgentType.CUSTOM,
    role="自定义代理",
    objective="自定义目标",
    tasks=["任务1", "任务2"],
    input_format="自定义输入格式",
    output_format="自定义输出格式",
    reasoning_steps="自定义推理步骤",
    example_output={"key": "value"},
    explanation="自定义解释"
)
```

## 📈 集成优势

### 1. 完全兼容现有系统
- 基于现有代理架构扩展
- 保持消息队列和协议兼容
- 无缝集成到现有工作流

### 2. 高度可配置
- 支持多种LLM提供商
- 灵活的代理配置选项
- 可自定义prompt模板

### 3. 生产就绪
- 完整的错误处理机制
- 详细的监控和日志
- 性能优化和资源管理

### 4. 易于维护
- 清晰的代码结构
- 完整的文档和示例
- 全面的测试覆盖

## 🎉 总结

本项目成功将您提供的7个港股量化分析AI代理prompt模板完整集成到现有系统中，实现了：

- ✅ **完整的prompt模板系统** - 支持所有7个专业代理
- ✅ **多LLM提供商支持** - OpenAI、Claude、Grok等
- ✅ **异步执行引擎** - 高性能、可扩展
- ✅ **标准化JSON输出** - 易于解析和集成
- ✅ **完整的错误处理** - 生产环境就绪
- ✅ **详细的文档和示例** - 易于使用和维护

现在您可以直接使用这些代理进行港股量化分析，所有代理都遵循您提供的prompt模板规范，专门针对港股市场优化，追求高Sharpe Ratio的交易策略。

## 📞 支持

如有问题或需要帮助，请：
1. 查看详细文档：`docs/hk_prompt_agents_guide.md`
2. 运行测试脚本：`python test_hk_prompt_integration.py`
3. 查看演示示例：`examples/hk_prompt_agents_demo.py`
4. 检查配置文件：`config/hk_prompt_agents_config.json`

祝您使用愉快！🚀
