# 港股量化交易 AI Agent 系统使用指南

## 📋 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [运行模式](#运行模式)
4. [Agent仪表板使用](#agent仪表板使用)
5. [API接口使用](#api接口使用)
6. [开发模式](#开发模式)
7. [故障排除](#故障排除)

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.9+
- Redis 6+
- PostgreSQL 12+ (可选，用于数据持久化)

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 如果使用开发模式，安装额外依赖
pip install pytest black flake8 mypy
```

### 3. 配置环境变量

```bash
# 复制环境配置文件
cp env.example .env

# 编辑配置文件（至少需要配置Redis）
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your_password
```

### 4. 启动Redis服务

```bash
# 如果使用Docker
docker run -d -p 6379:6379 redis:latest

# 或者本地安装Redis
# Windows: 下载Redis for Windows
# Linux/Mac: sudo apt-get install redis-server / brew install redis
```

## 🎯 运行模式

### 模式1: 快速演示模式

最简单的运行方式，使用内存模拟，无需外部依赖：

```bash
python simple_demo.py
```

这将启动一个简化的演示，展示7个AI Agent的基本交互。

### 模式2: 完整系统模式

运行完整的系统，包括所有Agent和仪表板：

```bash
python -m src.main
```

### 模式3: 仪表板专用模式

只启动Agent监控仪表板：

```bash
python -c "
import asyncio
from src.dashboard.dashboard_ui import DashboardUI
from src.dashboard.api_routes import DashboardAPI
from src.core import SystemConfig
from unittest.mock import Mock

async def start_dashboard():
    # 创建模拟的coordinator和message_queue
    coordinator = Mock()
    message_queue = Mock()
    
    # 创建API和UI
    api = DashboardAPI(coordinator, message_queue)
    await api.initialize()
    
    ui = DashboardUI(api)
    await ui.start()

asyncio.run(start_dashboard())
"
```

## 📊 Agent仪表板使用

### 访问仪表板

启动系统后，在浏览器中访问：
- **主仪表板**: http://localhost:8000/
- **绩效分析**: http://localhost:8000/performance
- **系统状态**: http://localhost:8000/system

### 仪表板功能

#### 1. Agent状态监控
- 实时查看7个AI Agent的运行状态
- 监控CPU、内存使用情况
- 查看消息处理数量和错误计数

#### 2. 策略信息展示
- 查看每个Agent采用的交易策略
- 策略参数配置
- 策略版本和风险等级

#### 3. 绩效指标监控
- **夏普比率**: 风险调整后的收益指标
- **总收益率**: 累计收益表现
- **最大回撤**: 最大损失幅度
- **胜率**: 盈利交易占比
- **波动率**: 收益的稳定性

#### 4. Agent控制操作
- **启动**: 启动停止的Agent
- **停止**: 停止运行的Agent
- **重启**: 重启Agent服务
- **暂停/恢复**: 临时暂停Agent执行

#### 5. 实时数据更新
- WebSocket实时推送数据
- 自动刷新Agent状态
- 实时告警通知

## 🔌 API接口使用

### 基础API端点

```bash
# 健康检查
curl http://localhost:8000/api/dashboard/health

# 获取系统状态
curl http://localhost:8000/api/dashboard/status

# 获取所有Agent数据
curl http://localhost:8000/api/dashboard/agents

# 获取特定Agent数据
curl http://localhost:8000/api/dashboard/agents/quant_analyst_001
```

### Agent控制API

```bash
# 启动Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/start

# 停止Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/stop

# 重启Agent
curl -X POST http://localhost:8000/api/dashboard/agents/quant_analyst_001/control/restart
```

### 策略信息API

```bash
# 获取所有策略
curl http://localhost:8000/api/dashboard/strategies

# 获取Agent策略
curl http://localhost:8000/api/dashboard/agents/quant_analyst_001/strategy
```

### 绩效数据API

```bash
# 获取所有绩效数据
curl http://localhost:8000/api/dashboard/performance

# 获取Agent绩效
curl http://localhost:8000/api/dashboard/agents/quant_analyst_001/performance
```

## 💻 开发模式

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/dashboard/

# 运行集成测试
pytest tests/integration/

# 生成测试覆盖率报告
pytest --cov=src --cov-report=html
```

### 代码质量检查

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 开发调试

```bash
# 启用调试模式
export DEBUG=true
python -m src.main

# 查看详细日志
export LOG_LEVEL=DEBUG
python -m src.main
```

## 🔧 故障排除

### 常见问题

#### 1. Redis连接失败

```
错误: Redis connection failed
解决: 确保Redis服务正在运行，检查连接配置
```

```bash
# 检查Redis状态
redis-cli ping
# 应该返回 PONG

# 检查端口是否被占用
netstat -an | grep 6379
```

#### 2. 依赖包安装失败

```
错误: Package installation failed
解决: 更新pip或使用虚拟环境
```

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 端口被占用

```
错误: Port 8000 already in use
解决: 更改端口或停止占用端口的进程
```

```bash
# 查找占用端口的进程
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 更改端口
export PORT=8001
python -m src.main
```

#### 4. Agent启动失败

```
错误: Agent initialization failed
解决: 检查日志文件，确认依赖服务正常
```

```bash
# 查看日志
tail -f logs/system.log

# 检查Agent状态
curl http://localhost:8000/api/dashboard/status
```

### 性能优化

#### 1. 内存使用优化

```bash
# 启用内存监控
export ENABLE_MEMORY_MONITOR=true

# 调整缓存大小
export CACHE_SIZE=1000
```

#### 2. 响应时间优化

```bash
# 启用响应压缩
export ENABLE_COMPRESSION=true

# 调整连接池大小
export CONNECTION_POOL_SIZE=100
```

### 日志分析

```bash
# 查看系统日志
tail -f logs/system.log

# 查看Agent日志
tail -f logs/agents/*.log

# 查看错误日志
grep ERROR logs/system.log
```

## 📈 监控和维护

### 系统监控

```bash
# 查看系统状态
curl http://localhost:8000/api/dashboard/status | jq

# 查看性能指标
curl http://localhost:8000/api/dashboard/performance | jq

# 查看告警信息
curl http://localhost:8000/api/dashboard/alerts | jq
```

### 定期维护

```bash
# 清理日志文件（每周）
find logs/ -name "*.log" -mtime +7 -delete

# 清理缓存（每日）
curl -X DELETE http://localhost:8000/api/dashboard/alerts

# 重启系统（每月）
systemctl restart hk-quant-system  # 如果使用systemd
```

## 📚 进阶使用

### 自定义Agent策略

```python
# 创建自定义策略
from src.models.agent_dashboard import StrategyInfo, StrategyType

custom_strategy = StrategyInfo(
    strategy_id="custom_001",
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
# 添加自定义组件
from src.dashboard.components import AgentCardComponent

custom_component = AgentCardComponent()
# 自定义配置和样式
```

### 集成外部数据源

```python
# 集成外部API
from src.core.data_sources import ExternalDataSource

data_source = ExternalDataSource(
    api_key="your_api_key",
    base_url="https://api.example.com"
)
```

## 🆘 获取帮助

如果遇到问题，可以：

1. **查看文档**: 阅读 `docs/` 目录下的详细文档
2. **检查日志**: 查看 `logs/` 目录下的日志文件
3. **运行测试**: 使用 `pytest` 验证系统状态
4. **查看API文档**: 访问 http://localhost:8000/docs 查看API文档

## 📞 技术支持

- **项目文档**: 查看 `docs/` 目录
- **API参考**: 查看 `docs/api_reference.md`
- **用户指南**: 查看 `docs/user_guide.md`
- **开发指南**: 查看 `docs/developer_guide.md`

---

**祝您使用愉快！** 🎉
