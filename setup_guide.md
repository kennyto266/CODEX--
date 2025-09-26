# 港股量化交易 AI Agent 系统 - 使用指南

## 🚀 快速开始

### 1. 环境准备

#### 系统要求
- Python 3.8+
- Redis 6.0+
- 8GB+ RAM (推荐)
- 多核CPU (推荐4核+)

#### 安装Redis

**Windows:**
```bash
# 下载并安装Redis for Windows
# 或使用WSL安装Linux版本
wsl --install
# 然后在WSL中安装Redis
sudo apt update
sudo apt install redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. 安装系统

```bash
# 1. 进入项目目录
cd "C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 3. 配置系统

```bash
# 复制配置文件
copy env.example .env

# 编辑配置文件 (可选)
notepad .env
```

### 4. 启动Redis

```bash
# 启动Redis服务器
redis-server

# 验证Redis运行
redis-cli ping
# 应该返回: PONG
```

## 🎮 使用方式

### 方式1: 快速演示 (推荐新手)

```bash
# 运行快速启动脚本
python quick_start.py
```

这个脚本会：
- 自动初始化所有7个AI Agent
- 演示完整的交易工作流程
- 展示系统各项功能
- 提供交互式命令界面

### 方式2: 编程使用

```python
import asyncio
from src.core.message_queue import MessageQueue
from src.agents.coordinator import AgentCoordinator

async def main():
    # 1. 初始化消息队列
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 2. 创建协调器
    coordinator = AgentCoordinator(message_queue)
    await coordinator.initialize()
    
    # 3. 启动系统
    await coordinator.start_all_agents()
    
    print("系统已启动！")
    
    # 4. 发送市场数据
    from src.models.base import MarketData
    from src.core.message_queue import Message
    from datetime import datetime
    
    market_data = MarketData(
        symbol="2800.HK",
        timestamp=datetime.now(),
        open_price=25.50,
        high_price=25.80,
        low_price=25.40,
        close_price=25.70,
        volume=1000000,
        vwap=25.60
    )
    
    message = Message(
        sender_id="market_data_source",
        receiver_id="data_scientist_001",
        message_type="MARKET_DATA",
        payload=market_data.dict(),
        timestamp=datetime.now(),
        priority="NORMAL"
    )
    
    await message_queue.publish_message(message)
    print("市场数据已发送！")

if __name__ == "__main__":
    asyncio.run(main())
```

### 方式3: 测试系统

```bash
# 运行集成测试
python -m pytest tests/integration/test_agent_integration.py -v

# 运行性能测试
python -m pytest tests/performance/benchmark_tests.py -v

# 运行所有测试
python -m pytest tests/ -v
```

## 📊 系统监控

### Web界面监控

```bash
# 启动监控仪表板 (如果有Web界面)
python -m src.agents.quantitative_engineer.monitoring_dashboard
```

### 命令行监控

```python
# 获取系统状态
async def check_system_status():
    coordinator = AgentCoordinator(message_queue)
    statuses = await coordinator.get_all_agent_statuses()
    
    for agent_id, status in statuses.items():
        print(f"Agent {agent_id}: {status['status']}")
```

## 🔧 常见问题解决

### 1. Redis连接失败

**错误**: `ConnectionError: Redis connection failed`

**解决方案**:
```bash
# 检查Redis是否运行
redis-cli ping

# 如果Redis未运行，启动它
redis-server

# 检查配置文件中的Redis设置
```

### 2. 依赖包安装失败

**错误**: `ModuleNotFoundError`

**解决方案**:
```bash
# 确保在虚拟环境中
pip list

# 重新安装依赖
pip install -r requirements.txt --upgrade

# 如果仍有问题，逐个安装
pip install redis pydantic asyncio fastapi
```

### 3. Agent启动失败

**错误**: `Agent initialization failed`

**解决方案**:
```bash
# 检查日志
tail -f logs/system.log

# 检查Agent配置
python -c "
from src.agents.base_agent import AgentConfig
config = AgentConfig(agent_id='test', agent_type='TestAgent')
print(config)
"
```

### 4. 内存不足

**错误**: `MemoryError`

**解决方案**:
```python
# 调整系统配置
from src.core import SystemConfig

config = SystemConfig(
    max_agents=10,  # 减少Agent数量
    max_connections=50  # 减少连接数
)
```

## 📚 详细文档

### 用户指南
- [完整用户指南](docs/user_guide.md) - 详细的系统使用说明
- [API参考文档](docs/api_reference.md) - 完整的API文档

### 系统架构
- [需求文档](.spec-workflow/specs/hk-quant-ai-agents/requirements.md)
- [设计文档](.spec-workflow/specs/hk-quant-ai-agents/design.md)
- [任务文档](.spec-workflow/specs/hk-quant-ai-agents/tasks.md)

## 🎯 使用示例

### 示例1: 发送交易信号

```python
from src.models.base import TradingSignal
from src.core.message_queue import Message

# 创建交易信号
signal = TradingSignal(
    symbol="2800.HK",
    signal_type="BUY",
    strength=0.8,
    price=25.70,
    timestamp=datetime.now(),
    confidence=0.85,
    reasoning="动量指标显示买入信号"
)

# 发送给量化交易员
message = Message(
    sender_id="quant_analyst_001",
    receiver_id="quant_trader_001",
    message_type="TRADING_SIGNAL",
    payload=signal.dict(),
    timestamp=datetime.now(),
    priority="HIGH"
)

await message_queue.publish_message(message)
```

### 示例2: 启动研究项目

```python
# 发送研究请求
research_message = Message(
    sender_id="user",
    receiver_id="research_analyst_001",
    message_type="CONTROL",
    payload={
        "command": "start_research",
        "parameters": {
            "research_type": "strategy_hypothesis",
            "focus_area": "momentum_strategies"
        }
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)

await message_queue.publish_message(research_message)
```

### 示例3: 系统监控

```python
# 收集系统指标
metrics_message = Message(
    sender_id="system",
    receiver_id="quant_engineer_001",
    message_type="CONTROL",
    payload={
        "command": "collect_metrics",
        "parameters": {}
    },
    timestamp=datetime.now(),
    priority="NORMAL"
)

await message_queue.publish_message(metrics_message)
```

## 🚀 高级用法

### 自定义Agent

```python
from src.agents.base_agent import BaseAgent, AgentConfig

class CustomAgent(BaseAgent):
    def __init__(self, config: AgentConfig, message_queue: MessageQueue):
        super().__init__(config, message_queue)
    
    async def process_message(self, message: Message) -> bool:
        # 自定义消息处理逻辑
        if message.message_type == "CUSTOM_MESSAGE":
            # 处理自定义消息
            pass
        return True

# 使用自定义Agent
config = AgentConfig(
    agent_id="custom_agent_001",
    agent_type="CustomAgent"
)
custom_agent = CustomAgent(config, message_queue)
await custom_agent.initialize()
```

### 批量处理消息

```python
async def batch_process_messages(messages: List[Message]):
    tasks = []
    for message in messages:
        task = asyncio.create_task(message_queue.publish_message(message))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 错误处理和重试

```python
async def send_message_with_retry(message: Message, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            await message_queue.publish_message(message)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)  # 指数退避
    return False
```

## 🎉 开始使用

现在您已经了解了如何使用系统，让我们开始吧！

1. **新手用户**: 运行 `python quick_start.py` 开始快速演示
2. **开发者**: 查看 [API参考文档](docs/api_reference.md) 进行开发
3. **系统管理员**: 查看 [用户指南](docs/user_guide.md) 了解运维

**祝您使用愉快！** 🚀
