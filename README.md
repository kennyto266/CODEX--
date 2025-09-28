# 港股AI代理系统

基于 `hk_complete_system.py` 重构的完整港股量化分析系统，实现从股票数据获取到7个真实AI代理分析再到Dashboard输出的完整工作流。

## 🚀 系统特性

- **📊 实时数据获取**: 从API获取港股实时数据
- **🤖 7个专业AI代理**: 基本面、技术、情绪、新闻、研究辩论、交易、风险管理
- **🌐 实时Dashboard**: Web界面展示分析结果
- **⚡ 并行处理**: 7个代理同时运行，提高效率
- **🔧 易于配置**: 支持环境变量和配置文件

## 📋 系统架构

```
股票数据获取 → 7个AI代理分析 → Dashboard展示
     ↓              ↓              ↓
  StockData    AgentManager    WebServer
  Provider      (7 Agents)     (HTML/JS)
```

## 🛠️ 安装和配置

### 环境要求

- Python 3.10+
- Windows 10/11
- 网络连接

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

设置环境变量：

```bash
set CURSOR_API_KEY=your_cursor_api_key_here
```

或在 `config/settings.py` 中直接修改：

```python
CURSOR_API_KEY = "your_cursor_api_key_here"
```

## 🚀 快速开始

### 运行完整系统

```bash
python main.py
```

系统将：
1. 获取0700.HK股票数据
2. 启动7个AI代理进行分析
3. 启动Dashboard服务器
4. 在浏览器中打开 http://localhost:8080

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定模块测试
python -m pytest tests/test_data.py
python -m pytest tests/test_agents.py
python -m pytest tests/test_dashboard.py
python -m pytest tests/test_integration.py
```

## 📁 项目结构

```
hk-ai-agents-system/
├── main.py                    # 主入口文件
├── config/
│   └── settings.py           # 系统配置
├── src/
│   ├── data/                 # 数据模块
│   │   ├── stock_data.py     # 股票数据获取
│   │   └── data_formatter.py # 数据格式化
│   ├── agents/               # AI代理模块
│   │   ├── base_agent.py     # 代理基类
│   │   ├── agent_manager.py  # 代理管理器
│   │   ├── fundamental_agent.py    # 基本面分析代理
│   │   ├── technical_agent.py      # 技术分析代理
│   │   ├── sentiment_agent.py      # 情绪分析代理
│   │   ├── news_agent.py           # 新闻分析代理
│   │   ├── research_agent.py       # 研究辩论代理
│   │   ├── trader_agent.py         # 交易代理
│   │   └── risk_manager_agent.py   # 风险管理代理
│   └── dashboard/            # Dashboard模块
│       ├── web_server.py     # Web服务器
│       └── html_generator.py # HTML生成器
├── tests/                    # 测试文件
├── docs/                     # 文档
└── requirements.txt          # 依赖管理
```

## 🤖 AI代理说明

### 1. 基本面分析代理 📊
- 分析PE、PB、ROE等财务指标
- 评估公司价值和成长性
- 提供投资建议

### 2. 技术分析代理 📈
- 分析技术指标和图表形态
- 识别支撑位和阻力位
- 提供买卖信号

### 3. 情绪分析代理 😊
- 分析市场情绪和投资者心理
- 评估资金流向
- 预测情绪变化

### 4. 新闻分析代理 📰
- 分析新闻事件对股价的影响
- 评估市场反应
- 识别新闻驱动的机会

### 5. 研究辩论代理 🔬
- 多角度研究和辩论分析
- 看多/看空观点对比
- 综合投资结论

### 6. 交易代理 💼
- 提供具体交易策略
- 设定入场和出场时机
- 风险控制建议

### 7. 风险管理代理 ⚠️
- 全面风险评估
- 风险控制建议
- 预警机制

## 🌐 Dashboard功能

- **实时状态**: 显示所有代理运行状态
- **分析结果**: 展示每个代理的分析内容
- **自动刷新**: 30秒自动更新数据
- **响应式设计**: 支持移动端访问
- **美观界面**: 现代化UI设计

## ⚙️ 配置选项

在 `config/settings.py` 中可以配置：

```python
# API配置
CURSOR_API_KEY = "your_api_key"
STOCK_API_BASE_URL = "http://18.180.162.113:9191"

# Dashboard配置
DASHBOARD_PORT = 8080
DASHBOARD_HOST = "localhost"

# 代理配置
AGENT_TIMEOUT = 30
AGENT_RETRY_COUNT = 3

# 日志配置
LOG_LEVEL = "INFO"
```

## 🔧 开发指南

### 添加新代理

1. 继承 `BaseAgent` 类
2. 实现 `name`、`icon` 和 `generate_prompt` 方法
3. 在 `AgentManager` 中注册新代理

### 自定义Dashboard

修改 `src/dashboard/html_generator.py` 中的HTML和CSS

### 扩展数据源

修改 `src/data/stock_data.py` 中的API调用逻辑

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `CURSOR_API_KEY` 环境变量
   - 确认API密钥有效

2. **网络连接问题**
   - 检查网络连接
   - 确认API端点可访问

3. **代理启动失败**
   - 检查Cursor API状态
   - 查看日志错误信息

4. **Dashboard无法访问**
   - 检查端口是否被占用
   - 确认防火墙设置

### 日志查看

系统日志会显示在控制台，包括：
- 数据获取状态
- 代理启动和运行状态
- Dashboard服务状态
- 错误信息

## 📈 性能优化

- 使用异步处理提高并发性能
- 实现数据缓存减少API调用
- 优化HTML生成提高响应速度
- 添加错误重试机制

## 🔒 安全考虑

- API密钥安全存储
- 本地访问限制
- 输入数据验证
- 错误信息过滤

## 📝 更新日志

### v1.0.0 (2024-09-28)
- 初始版本发布
- 实现7个AI代理
- 完成Dashboard界面
- 添加完整测试覆盖

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 📞 支持

如有问题，请查看：
- 项目文档
- 测试用例
- 日志输出

---

**港股AI代理系统** - 让AI为你的投资决策提供专业分析 🚀