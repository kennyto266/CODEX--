# 港股量化交易 AI Agent 系统

一个专门针对港股市场的量化交易系统，由7个专业的AI Agent组成，旨在追求高Sharpe比率的交易策略。

## 系统架构

### 7个专业AI Agent

1. **量化分析师 Agent** - 开发数学模型、评估风险、制定交易策略
2. **量化交易员 Agent** - 识别交易机会、执行买卖订单、优化策略
3. **投资组合经理 Agent** - 构建投资组合、管理资产配置、监控绩效
4. **风险分析师 Agent** - 计算风险指标、设计对冲策略、压力测试
5. **数据科学家 Agent** - 机器学习预测、数据挖掘、异常检测
6. **量化工程师 Agent** - 系统监控、性能优化、自动部署
7. **研究分析师 Agent** - 量化研究、策略开发、学术文献分析

### 核心特性

- **微服务架构**: 7个独立的AI Agent组件
- **事件驱动**: Agent间通过消息队列异步通信
- **实时响应**: 毫秒级交易信号检测和执行
- **风险管理**: 全面的风险控制和监控体系
- **高可用性**: 99.9%的系统可用性保证

## 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker (可选)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd hk-quant-ai-agents
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库、Redis等连接信息
```

4. **初始化数据库**
```bash
# 创建数据库迁移
alembic upgrade head
```

5. **启动系统**
```bash
python -m src.main
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
hk-quant-ai-agents/
├── src/
│   ├── core/           # 核心模块
│   ├── agents/         # AI Agent实现
│   ├── models/         # 数据模型
│   ├── services/       # 业务服务
│   └── utils/          # 工具函数
├── tests/              # 测试文件
├── docs/               # 文档
├── .spec-workflow/     # 规范工作流程文档
└── requirements.txt    # 依赖包
```

## 配置说明

系统支持通过环境变量进行配置，主要配置项包括：

- **数据库配置**: `DATABASE_URL`
- **Redis配置**: `REDIS_HOST`, `REDIS_PORT`
- **交易配置**: `TRADING_ENABLED`, `MAX_POSITION_SIZE`
- **风险控制**: `RISK_LIMIT`, `MAX_DAILY_LOSS`

详细配置请参考 `env.example` 文件。

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
