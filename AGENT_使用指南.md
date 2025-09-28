# 🤖 港股量化交易 AI Agent 系统 - 完整使用指南

## 🎯 快速开始

### 方式1: 一键启动脚本 ⭐⭐⭐ (推荐)

```bash
python3 start_agents.py
```

这个脚本提供了交互式菜单，包含所有启动选项。

### 方式2: 直接运行演示 ⭐⭐ (最简单)

```bash
python3 demo.py
```

无需任何配置，立即体验7个AI Agent的功能。

### 方式3: Web仪表板 ⭐ (功能最全)

```bash
# 安装依赖
pip3 install fastapi uvicorn

# 启动Web界面
python3 simple_web_dashboard_fixed.py
```

然后访问: http://localhost:8000

## 📊 Agent系统架构

### 7个专业AI Agent

1. **📊 量化分析师** (`quantitative_analyst`)
   - **功能**: 技术分析和策略研究
   - **策略**: 技术分析策略
   - **特点**: 基于技术指标的交易决策

2. **💹 量化交易员** (`quantitative_trader`)
   - **功能**: 执行交易决策
   - **策略**: 动量策略
   - **特点**: 高频交易执行

3. **📈 投资组合经理** (`portfolio_manager`)
   - **功能**: 资产配置优化
   - **策略**: 风险平价策略
   - **特点**: 动态资产配置

4. **⚠️ 风险分析师** (`risk_analyst`)
   - **功能**: 风险控制和监控
   - **策略**: 对冲策略
   - **特点**: 实时风险监控

5. **🔬 数据科学家** (`data_scientist`)
   - **功能**: 数据分析和建模
   - **策略**: 机器学习策略
   - **特点**: AI驱动的预测模型

6. **🔧 量化工程师** (`quantitative_engineer`)
   - **功能**: 系统维护和优化
   - **策略**: 系统优化策略
   - **特点**: 性能监控和优化

7. **📚 研究分析师** (`research_analyst`)
   - **功能**: 市场研究和预测
   - **策略**: 研究驱动策略
   - **特点**: 基本面分析

### Agent通信系统

- **消息协议**: 标准化的ProtocolMessage格式
- **路由机制**: 智能消息路由和广播
- **优先级**: LOW → NORMAL → HIGH → URGENT → CRITICAL
- **可靠性**: 自动重试和错误处理

## 🚀 运行模式详解

### 1. 演示模式 (Demo Mode)

**特点**:
- ✅ 无需任何配置
- ✅ 展示所有Agent功能
- ✅ 模拟交易活动
- ✅ 绩效分析报告

**运行命令**:
```bash
python3 demo.py
```

**输出示例**:
```
╔══════════════════════════════════════════════════════════════╗
║        🚀 港股量化交易 AI Agent 系统演示                      ║
║        7个专业AI Agent + 实时监控仪表板                      ║
╚══════════════════════════════════════════════════════════════╝

📊 系统概览
总Agent数量: 7
运行中Agent: 7
平均夏普比率: 1.92
平均收益率: 12.86%
系统状态: 🟢 正常
```

### 2. Web仪表板模式 (Web Dashboard)

**特点**:
- ✅ 现代化Web界面
- ✅ 实时Agent监控
- ✅ 远程控制功能
- ✅ 性能指标展示

**启动步骤**:
```bash
# 1. 安装依赖
pip3 install fastapi uvicorn

# 2. 启动Web服务器
python3 simple_web_dashboard_fixed.py
```

**访问地址**:
- 主仪表板: http://localhost:8000
- API状态: http://localhost:8000/api/status
- Agent详情: http://localhost:8000/agent/{agent_id}

**界面功能**:
- 📊 实时Agent状态监控
- 🎛️ Agent启动/停止控制
- 📈 绩效指标展示
- 🔄 自动刷新数据

### 3. 完整系统模式 (Full System)

**特点**:
- ✅ 所有功能完整运行
- ✅ 需要Redis服务
- ✅ 生产环境就绪
- ✅ 真实数据集成

**启动步骤**:
```bash
# 1. 启动Redis服务
docker run -d -p 6379:6379 redis:latest

# 2. 启动完整系统
python3 start_dashboard.py dashboard
```

## 🔧 配置和自定义

### Agent配置

每个Agent都有详细的配置选项：

```python
# RealAgentConfig 示例
config = RealAgentConfig(
    agent_id="quantitative_analyst_001",
    agent_type="quantitative_analyst",
    name="量化分析师",
    data_sources=["yahoo_finance", "alpha_vantage"],
    update_frequency=60,  # 秒
    lookback_period=252,  # 天
    signal_threshold=0.6,
    confidence_threshold=0.7,
    max_position_size=0.1,
    stop_loss_threshold=0.05,
    take_profit_threshold=0.1
)
```

### 环境变量配置

创建 `.env` 文件：

```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 数据源配置
YAHOO_FINANCE_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key

# 系统配置
LOG_LEVEL=INFO
MAX_CONCURRENT_AGENTS=10
HEARTBEAT_INTERVAL=30
```

## 📈 性能监控

### 关键指标

- **夏普比率**: 风险调整后收益
- **最大回撤**: 最大损失幅度
- **胜率**: 盈利交易比例
- **收益率**: 总收益百分比

### 实时监控

Web仪表板提供实时监控：
- Agent状态 (运行/停止/错误)
- 消息处理数量
- 错误计数
- 运行时间
- 交易统计

## 🛠️ 故障排除

### 常见问题

1. **端口8000被占用**
   ```bash
   # 解决方案: 使用其他端口
   uvicorn app:app --port 8001
   ```

2. **依赖安装失败**
   ```bash
   # 解决方案: 使用虚拟环境
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn
   ```

3. **Redis连接失败**
   ```bash
   # 解决方案: 启动Redis服务
   docker run -d -p 6379:6379 redis:latest
   ```

4. **Python版本过低**
   ```bash
   # 解决方案: 升级到Python 3.9+
   python3 --version
   ```

### 日志查看

```bash
# 查看系统日志
tail -f logs/system.log

# 查看Agent日志
tail -f logs/agents/*.log
```

## 🔄 API接口

### REST API端点

```bash
# 获取所有Agent状态
GET /api/agents

# 获取单个Agent状态
GET /api/agents/{agent_id}/status

# 启动Agent
POST /api/agents/{agent_id}/start

# 停止Agent
POST /api/agents/{agent_id}/stop

# 系统状态
GET /api/status
```

### API响应示例

```json
{
  "agents": [
    {
      "agent_id": "quantitative_analyst",
      "agent_type": "量化分析师",
      "status": "running",
      "messages_processed": 1250,
      "error_count": 2,
      "uptime_seconds": 3600,
      "performance_metrics": {
        "trades_count": 45,
        "profit_loss": 12500.50,
        "win_rate": 0.68,
        "sharpe_ratio": 1.85,
        "max_drawdown": 0.08
      }
    }
  ],
  "total_agents": 7,
  "running": 7,
  "stopped": 0
}
```

## 📚 进阶功能

### 自定义Agent

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def initialize(self):
        # 自定义初始化逻辑
        pass
    
    async def process_message(self, message):
        # 自定义消息处理
        pass
    
    async def cleanup(self):
        # 自定义清理逻辑
        pass
```

### 策略开发

```python
from src.strategy_management.strategy_manager import StrategyManager

# 创建自定义策略
strategy = StrategyManager()
strategy.create_strategy(
    name="自定义策略",
    description="基于自定义逻辑的交易策略",
    parameters={"threshold": 0.7}
)
```

### 数据适配器

```python
from src.data_adapters.base_adapter import BaseAdapter

class CustomDataAdapter(BaseAdapter):
    async def fetch_data(self, symbol, start_date, end_date):
        # 自定义数据获取逻辑
        pass
```

## 🎯 最佳实践

### 1. 开发环境设置

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8 mypy

# 运行测试
pytest tests/
```

### 2. 生产环境部署

```bash
# 使用Docker部署
docker-compose up -d

# 使用systemd服务
sudo systemctl start hk-quant-agents

# 监控服务状态
sudo systemctl status hk-quant-agents
```

### 3. 性能优化

- 使用异步处理提高并发性能
- 合理配置Agent数量避免资源竞争
- 定期清理日志文件
- 监控内存和CPU使用率

## 📞 支持和帮助

### 文档资源

- **快速开始**: `QUICK_START.md`
- **详细指南**: `USAGE_GUIDE.md`
- **API文档**: `docs/api_reference.md`
- **故障排除**: `TROUBLESHOOTING.md`

### 社区支持

- GitHub Issues: 报告问题和建议
- 文档Wiki: 详细使用说明
- 示例代码: `examples/` 目录

---

## 🎉 总结

您的港股量化交易AI Agent系统现在已经完全可用！通过以下三种方式启动：

1. **演示模式**: `python3 demo.py` - 快速体验
2. **Web仪表板**: `python3 simple_web_dashboard_fixed.py` - 完整功能
3. **一键启动**: `python3 start_agents.py` - 交互式菜单

系统包含7个专业AI Agent，提供完整的量化交易解决方案，从数据分析到风险控制，应有尽有！