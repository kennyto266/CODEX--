# AI Agent 量化交易系统 - 多智能体协作平台

一个基于多智能体协作的量化交易系统，集成了数据适配器、回测引擎、实时监控和Telegram机器人等功能模块。

## 系统架构

### 核心组件

1. **多智能体系统** - 7个专业AI Agent协作处理量化交易
2. **数据适配器** - 支持多种数据源（HTTP API、原始数据等）
3. **回测引擎** - 集成Sharpe比率和最大回撤计算
4. **实时监控** - WebSocket实时数据推送和性能监控
5. **Telegram集成** - 通过机器人接收交易信号和系统状态
6. **Web仪表板** - 可视化界面展示系统状态和交易决策

### 核心特性

- **模块化设计**: 可插拔的组件架构
- **实时通信**: WebSocket + HTTP API双重通信机制
- **风险管理**: 集成Sharpe比率和最大回撤计算
- **多数据源**: 支持HTTP API和原始数据适配器
- **用户友好**: 提供Web界面和Telegram机器人交互

## 快速开始

### 环境要求

- Python 3.10+ (推荐3.10或3.11)
- Windows 10/11 (当前版本针对Windows优化)
- PowerShell 5.1+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd CODEX-寫量化團隊
```

2. **创建虚拟环境**
```bash
python -m venv .venv310
.venv310\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
cp env.example .env
# 编辑 .env 文件，配置API密钥和数据库连接
```

5. **启动系统**
```bash
# 方式1: 完整系统模式
python run_full_dashboard.py

# 方式2: 简单仪表板
python simple_web_dashboard.py

# 方式3: 使用脚本启动
.\scripts\start_server.ps1
```

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 设置代码格式化
pre-commit install

# 运行测试
pytest tests/
```

## 项目结构

```
CODEX-寫量化團隊/
├── src/
│   ├── agents/         # AI Agent实现
│   ├── backtest/       # 回测引擎
│   ├── core/           # 核心模块
│   ├── dashboard/      # Web仪表板
│   ├── data_adapters/  # 数据适配器
│   ├── integration/    # 系统集成
│   ├── monitoring/     # 监控模块
│   ├── strategy_management/ # 策略管理
│   ├── telegram/       # Telegram机器人
│   └── utils/          # 工具函数
├── scripts/            # 启动脚本
├── tests/              # 测试文件
├── docs/               # 文档
├── config/             # 配置文件
├── examples/           # 示例代码
└── requirements.txt    # 依赖包
```

## 配置说明

系统支持通过环境变量进行配置，主要配置项包括：

- **API配置**: `API_HOST`, `API_PORT`
- **Telegram配置**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **数据源配置**: `DATA_SOURCE_URL`, `DATA_API_KEY`
- **回测配置**: `RISK_FREE_RATE`, `MAX_POSITION_SIZE`

详细配置请参考 `env.example` 文件。

## 主要功能

### 1. 多智能体协作
- 7个专业AI Agent协同工作
- 实时消息传递和状态同步
- 智能决策和风险控制

### 2. 数据适配器
- HTTP API数据源适配
- 原始数据文件处理
- 实时数据流处理

### 3. 回测引擎 (enhanced_strategy_backtest.py)
支持 **11种技术指标策略** 的多维参数优化
- **基础指标 (4种)**: MA, RSI, MACD, Bollinger Bands
- **高级指标 (7种)**: KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR
- **Sharpe比率计算** - 自动优化排序
- **最大回撤分析** - 风险评估
- **多线程优化** - 1000+ 参数组合并行测试
- **策略性能评估** - 年化收益率、波动率、胜率等

#### 快速使用示例
```python
from enhanced_strategy_backtest import EnhancedStrategyBacktest

# 初始化
backtest = EnhancedStrategyBacktest('0700.HK', '2020-01-01', '2023-01-01')
backtest.load_data()

# 优化单个指标 (KDJ) - 约5分钟
kdj_results = backtest.optimize_parameters(strategy_type='kdj')

# 优化所有指标 - 约30-60分钟
all_results = backtest.optimize_parameters(strategy_type='all', max_workers=8)

# 获取最佳策略
best = backtest.get_best_strategies(top_n=10)
```

详细说明请参考 `CLAUDE.md` 中的"高级技术指标策略"部分

### 4. Web仪表板
- 实时系统状态监控
- 交易信号可视化
- 性能指标展示

### 5. Telegram集成
- 交易信号推送
- 系统状态通知
- 远程控制命令

## 监控和日志

- **日志系统**: 基于Python logging模块，支持文件和控制台输出
- **性能监控**: 集成Prometheus和Grafana
- **错误追踪**: 集成Sentry错误监控

## 测试

```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行性能测试
pytest tests/performance/

# 生成测试覆盖率报告
pytest --cov=src tests/
```

## 文档

- [API文档](docs/api_reference.md)
- [用户指南](docs/user_guide.md)
- [开发指南](docs/developer_guide.md)

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: 港股量化交易团队
- 邮箱: contact@hk-quant-team.com
- 项目链接: [https://github.com/hk-quant-team/hk-quant-ai-agents](https://github.com/hk-quant-team/hk-quant-ai-agents)
