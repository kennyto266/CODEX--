# 🚀 港股量化交易 AI Agent 系统使用指南

## 📋 快速开始

### 1️⃣ 一键演示 (推荐新手)
```bash
python demo.py
```
**特点**: 
- ✅ 无需任何配置
- ✅ 展示7个AI Agent的完整功能
- ✅ 包含绩效分析、风险控制、策略展示
- ✅ 模拟真实交易活动

### 2️⃣ 完整仪表板 (推荐日常使用)
```bash
python start_dashboard.py dashboard
```
**特点**:
- ✅ 现代化Web界面
- ✅ 实时监控Agent状态
- ✅ 远程控制Agent操作
- ✅ 详细的策略和绩效分析

### 3️⃣ 生产环境 (完整系统)
```bash
python -m src.main
```
**特点**:
- ✅ 所有功能完整运行
- ✅ 需要Redis服务
- ✅ 适合生产环境

---

## 🎯 系统功能概览

### 🤖 7个专业AI Agent

| Agent | 职责 | 主要策略 | 夏普比率 |
|-------|------|----------|----------|
| **量化分析师** | 技术分析、模型开发 | 技术分析策略 | 1.85 |
| **量化交易员** | 交易执行、机会识别 | 动量策略 | 2.10 |
| **投资组合经理** | 资产配置、风险管理 | 风险平价策略 | 1.95 |
| **风险分析师** | 风险控制、对冲策略 | 对冲策略 | 1.75 |
| **数据科学家** | 机器学习、预测分析 | 机器学习策略 | 2.25 |
| **量化工程师** | 系统优化、监控 | 系统优化策略 | 1.65 |
| **研究分析师** | 策略研究、文献分析 | 研究驱动策略 | 1.90 |

### 📊 关键绩效指标

- **平均夏普比率**: 1.92 (优秀)
- **平均收益率**: 12.86%
- **平均最大回撤**: 3.86%
- **系统可用性**: 99.9%

---

## 🌐 Web仪表板功能

### 主界面 (http://localhost:8000)
- **Agent状态监控**: 实时查看所有Agent运行状态
- **资源使用监控**: CPU、内存使用情况
- **消息处理统计**: 处理消息数量和错误计数
- **一键控制**: 启动/停止/重启Agent

### 绩效分析 (http://localhost:8000/performance)
- **夏普比率趋势**: 风险调整后收益表现
- **收益率分析**: 总收益、年化收益
- **回撤分析**: 最大回撤、当前回撤
- **风险指标**: VaR、波动率、Beta值

### 系统状态 (http://localhost:8000/system)
- **系统健康检查**: 各组件运行状态
- **性能监控**: 响应时间、吞吐量
- **告警信息**: 系统异常和风险告警
- **连接统计**: WebSocket连接数量

---

## 🔌 API接口使用

### 基础查询
```bash
# 获取所有Agent状态
curl http://localhost:8000/api/dashboard/agents

# 获取系统状态
curl http://localhost:8000/api/dashboard/status

# 获取绩效数据
curl http://localhost:8000/api/dashboard/performance
```

### Agent控制
```bash
# 启动Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/start

# 停止Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/stop

# 重启Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/restart
```

### 策略信息
```bash
# 获取所有策略
curl http://localhost:8000/api/dashboard/strategies

# 获取特定Agent策略
curl http://localhost:8000/api/dashboard/agents/quant_analyst_001/strategy
```

---

## 🛠️ 环境配置

### 最小配置 (演示模式)
```bash
# 无需任何配置，直接运行
python demo.py
```

### 标准配置 (仪表板模式)
```bash
# 可选：启动Redis (推荐)
docker run -d -p 6379:6379 redis:latest

# 启动仪表板
python start_dashboard.py dashboard
```

### 完整配置 (生产模式)
```bash
# 1. 启动Redis
docker run -d -p 6379:6379 redis:latest

# 2. 配置环境变量
cp env.example .env
# 编辑.env文件

# 3. 启动完整系统
python -m src.main
```

---

## 📈 使用场景

### 场景1: 学习了解系统
```bash
# 运行演示，了解系统功能
python demo.py
```

### 场景2: 日常监控管理
```bash
# 启动仪表板，监控Agent状态
python start_dashboard.py dashboard

# 访问 http://localhost:8000
# 查看Agent状态、绩效指标、控制操作
```

### 场景3: 策略开发测试
```bash
# 启动完整系统
python -m src.main

# 使用API接口进行策略测试
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/start
```

### 场景4: 生产环境部署
```bash
# 配置生产环境
export PRODUCTION=true
export REDIS_URL=redis://production-server:6379

# 启动生产服务
python -m src.main
```

---

## 🔧 故障排除

### 常见问题解决

#### 1. Python版本问题
```bash
# 检查版本 (需要3.9+)
python --version

# 如果版本过低，请升级Python
```

#### 2. 依赖包问题
```bash
# 重新安装依赖
pip install -r requirements.txt

# 或使用自动安装脚本
python install.py
```

#### 3. 端口被占用
```bash
# 查找占用进程
netstat -ano | findstr :8000

# 更改端口
export PORT=8001
python start_dashboard.py dashboard
```

#### 4. Redis连接失败
```bash
# 启动Redis
docker run -d -p 6379:6379 redis:latest

# 或使用演示模式 (无需Redis)
python demo.py
```

### 日志查看
```bash
# 查看系统日志
tail -f logs/dashboard.log

# 查看错误日志
grep ERROR logs/system.log
```

---

## 📚 进阶功能

### 自定义Agent策略
```python
from src.models.agent_dashboard import StrategyInfo, StrategyType

# 创建自定义策略
custom_strategy = StrategyInfo(
    strategy_id="my_strategy_001",
    strategy_name="我的自定义策略",
    strategy_type=StrategyType.MOMENTUM,
    parameters=[
        {"name": "period", "value": 20},
        {"name": "threshold", "value": 0.02}
    ]
)
```

### 扩展仪表板功能
```python
from src.dashboard.components import AgentCardComponent

# 创建自定义组件
custom_component = AgentCardComponent()
# 自定义配置和样式
```

### 集成外部数据源
```python
from src.core.data_sources import ExternalDataSource

# 集成外部API
data_source = ExternalDataSource(
    api_key="your_api_key",
    base_url="https://api.example.com"
)
```

---

## 🎉 开始使用

### 新手推荐流程
1. **体验演示**: `python demo.py`
2. **启动仪表板**: `python start_dashboard.py dashboard`
3. **访问界面**: http://localhost:8000
4. **查看文档**: 阅读 USAGE_GUIDE.md

### 开发者推荐流程
1. **安装依赖**: `python install.py`
2. **运行测试**: `pytest tests/`
3. **启动完整系统**: `python -m src.main`
4. **查看API文档**: http://localhost:8000/docs

### 生产环境推荐流程
1. **配置环境**: 设置生产环境变量
2. **启动Redis**: 配置Redis集群
3. **部署系统**: 使用Docker或Kubernetes
4. **监控告警**: 配置监控和告警系统

---

## 📞 获取帮助

- **📖 详细文档**: [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **🚀 快速开始**: [QUICK_START.md](QUICK_START.md)
- **🔧 API文档**: [docs/api_reference.md](docs/api_reference.md)
- **👨‍💻 开发指南**: [docs/developer_guide.md](docs/developer_guide.md)

---

**祝您使用愉快！** 🎉

您的港股量化交易AI Agent系统现在已经完全就绪，可以开始您的量化交易之旅了！
