# CODEX 量化交易系统 - API文档

## 目录

1. [API概述](#1-api概述)
2. [API访问](#2-api访问)
3. [认证授权](#3-认证授权)
4. [API端点](#4-api端点)
5. [数据模型](#5-数据模型)
6. [错误处理](#6-错误处理)
7. [代码示例](#7-代码示例)
8. [SDK使用](#8-sdk使用)

---

## 1. API概述

### 1.1 基本信息

**API基础URL**:
```
开发环境: http://localhost:8000
生产环境: https://your-domain.com
```

**API版本**: v1.0.0

**支持格式**:
- 请求: JSON
- 响应: JSON

**协议**: HTTP/HTTPS

### 1.2 API特性

- ✅ **RESTful设计** - 遵循REST架构原则
- ✅ **异步支持** - 所有端点支持异步操作
- ✅ **自动文档** - 基于OpenAPI/Swagger自动生成
- ✅ **类型安全** - 使用Pydantic进行数据验证
- ✅ **错误处理** - 统一的错误响应格式
- ✅ **限流保护** - 支持API调用频率限制

### 1.3 响应格式

**成功响应**:
```json
{
    "success": true,
    "data": {
        // 实际数据
    },
    "message": "操作成功",
    "timestamp": "2025-10-31T15:00:00Z"
}
```

**错误响应**:
```json
{
    "success": false,
    "error": {
        "code": "INVALID_SYMBOL",
        "message": "股票代码格式不正确",
        "details": {
            "field": "symbol",
            "value": "INVALID"
        }
    },
    "timestamp": "2025-10-31T15:00:00Z"
}
```

---

## 2. API访问

### 2.1 交互式文档

系统提供两套自动生成的交互式文档：

**Swagger UI** (推荐):
```
http://localhost:8000/docs
```

**ReDoc**:
```
http://localhost:8000/redoc
```

### 2.2 OpenAPI规范

完整的OpenAPI 3.0规范可通过以下方式获取：

**JSON格式**:
```
http://localhost:8000/openapi.json
```

**YAML格式**:
```
http://localhost:8000/openapi.yaml
```

### 2.3 基础URL配置

**Python**:
```python
import requests

BASE_URL = "http://localhost:8000"

# GET请求示例
response = requests.get(f"{BASE_URL}/api/agents/list")
data = response.json()
```

**JavaScript**:
```javascript
const BASE_URL = "http://localhost:8000";

// GET请求示例
fetch(`${BASE_URL}/api/agents/list`)
    .then(response => response.json())
    .then(data => console.log(data));
```

**cURL**:
```bash
# GET请求示例
curl -X GET "http://localhost:8000/api/agents/list" \
     -H "accept: application/json"

# POST请求示例
curl -X POST "http://localhost:8000/api/trading/order" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "0700.HK",
       "order_type": "BUY",
       "quantity": 1000,
       "price": 350.0
     }'
```

---

## 3. 认证授权

### 3.1 认证方式

目前系统使用模拟认证，实际部署时需要配置API密钥。

**请求头格式**:
```
Authorization: Bearer <token>
```

### 3.2 获取访问令牌

```python
# 登录获取令牌
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    json={
        "username": "admin",
        "password": "your_password"
    }
)

token = response.json()["access_token"]

# 使用令牌请求
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8000/api/agents/list",
    headers=headers
)
```

---

## 4. API端点

### 4.1 系统信息

#### 4.1.1 健康检查

```http
GET /health
```

**描述**: 检查系统健康状态

**响应示例**:
```json
{
    "status": "healthy",
    "timestamp": "2025-10-31T15:00:00Z",
    "version": "1.0.0",
    "services": {
        "database": "ok",
        "redis": "ok",
        "futu_api": "ok"
    }
}
```

#### 4.1.2 系统状态

```http
GET /api/dashboard/status
```

**描述**: 获取系统整体状态

**响应示例**:
```json
{
    "success": true,
    "data": {
        "system_status": "running",
        "uptime": "24h 15m",
        "active_agents": 7,
        "total_agents": 7,
        "cpu_usage": 35.2,
        "memory_usage": 68.5
    }
}
```

### 4.2 Agent管理

#### 4.2.1 获取Agent列表

```http
GET /api/agents/list
```

**描述**: 获取所有AI Agent的状态信息

**响应示例**:
```json
{
    "success": true,
    "data": [
        {
            "id": "coordinator",
            "name": "Coordinator Agent",
            "icon": "🎯",
            "description": "Coordinates all agent workflows and messages",
            "status": "running",
            "healthy": true,
            "messages": 2845,
            "uptime": "24h 15m",
            "cpu_usage": 15,
            "memory_usage": 234
        },
        {
            "id": "data_scientist",
            "name": "Data Scientist Agent",
            "icon": "📊",
            "description": "Data analysis and anomaly detection",
            "status": "running",
            "healthy": true,
            "messages": 1923,
            "uptime": "24h 15m",
            "cpu_usage": 22,
            "memory_usage": 445
        }
    ]
}
```

#### 4.2.2 启动Agent

```http
POST /api/agents/{agent_id}/start
```

**路径参数**:
- `agent_id` (string): Agent唯一标识符

**响应示例**:
```json
{
    "success": true,
    "message": "Agent started successfully"
}
```

#### 4.2.3 停止Agent

```http
POST /api/agents/{agent_id}/stop
```

**路径参数**:
- `agent_id` (string): Agent唯一标识符

**响应示例**:
```json
{
    "success": true,
    "message": "Agent stopped successfully"
}
```

#### 4.2.4 重启Agent

```http
POST /api/agents/{agent_id}/restart
```

**路径参数**:
- `agent_id` (string): Agent唯一标识符

#### 4.2.5 获取Agent日志

```http
GET /api/agents/{agent_id}/logs
```

**查询参数**:
- `lines` (integer, 可选): 返回日志行数，默认100
- `level` (string, 可选): 日志级别 (INFO/WARNING/ERROR)

**响应示例**:
```json
{
    "success": true,
    "data": {
        "agent_id": "coordinator",
        "logs": [
            {
                "timestamp": "2025-10-31T15:00:00Z",
                "level": "INFO",
                "message": "Agent initialized"
            }
        ]
    }
}
```

### 4.3 交易相关

#### 4.3.1 获取持仓列表

```http
GET /api/trading/positions
```

**描述**: 获取当前所有持仓

**响应示例**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "symbol": "0700.HK",
                "name": "腾讯控股",
                "quantity": 1000,
                "avg_price": 350.0,
                "current_price": 360.0,
                "market_value": 360000.0,
                "unrealized_pnl": 10000.0,
                "realized_pnl": 0.0,
                "pnl_percentage": 2.86,
                "currency": "HKD",
                "exchange": "HKEX"
            }
        ],
        "total_value": 360000.0,
        "total_pnl": 10000.0
    }
}
```

#### 4.3.2 下单交易

```http
POST /api/trading/order
```

**请求体**:
```json
{
    "symbol": "0700.HK",
    "order_type": "BUY",
    "quantity": 1000,
    "price": 350.0,
    "order_style": "NORMAL",
    "validity": "DAY"
}
```

**参数说明**:
- `symbol` (string, 必需): 股票代码
- `order_type` (string, 必需): 交易类型 (BUY/SELL)
- `quantity` (integer, 必需): 交易数量
- `price` (float, 可选): 价格 (市价单时可选)
- `order_style` (string, 可选): 订单样式 (NORMAL/OCOCO/OTOCO)
- `validity` (string, 可选): 有效期 (DAY/GTC)

**响应示例**:
```json
{
    "success": true,
    "data": {
        "order_id": "ORDER_20251031_001",
        "symbol": "0700.HK",
        "side": "BUY",
        "quantity": 1000,
        "price": 350.0,
        "status": "SUBMITTED",
        "timestamp": "2025-10-31T15:00:00Z"
    }
}
```

#### 4.3.3 获取订单列表

```http
GET /api/trading/orders
```

**查询参数**:
- `status` (string, 可选): 订单状态 (PENDING/SUBMITTED/FILLED/CANCELLED)
- `symbol` (string, 可选): 股票代码过滤
- `limit` (integer, 可选): 返回数量限制，默认100

**响应示例**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "order_id": "ORDER_20251031_001",
                "symbol": "0700.HK",
                "side": "BUY",
                "quantity": 1000,
                "filled_quantity": 0,
                "price": 350.0,
                "avg_price": 0.0,
                "status": "SUBMITTED",
                "timestamp": "2025-10-31T15:00:00Z"
            }
        ],
        "total": 1
    }
}
```

#### 4.3.4 获取交易历史

```http
GET /api/trading/trades
```

**查询参数**:
- `start_date` (string, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (string, 可选): 结束日期 (YYYY-MM-DD)
- `symbol` (string, 可选): 股票代码过滤

**响应示例**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "trade_id": "TRADE_20251031_001",
                "order_id": "ORDER_20251031_001",
                "symbol": "0700.HK",
                "side": "BUY",
                "quantity": 500,
                "price": 350.0,
                "trade_value": 175000.0,
                "commission": 17.5,
                "currency": "HKD",
                "exchange": "HKEX",
                "timestamp": "2025-10-31T15:05:00Z"
            }
        ]
    }
}
```

#### 4.3.5 取消订单

```http
DELETE /api/trading/orders/{order_id}
```

**路径参数**:
- `order_id` (string): 订单ID

#### 4.3.6 获取交易统计

```http
GET /api/trading/statistics
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total_trades": 25,
        "total_buy": 13,
        "total_sell": 12,
        "total_volume": 15000,
        "total_turnover": 5250000.0,
        "win_rate": 52.0,
        "profit_factor": 1.35,
        "sharpe_ratio": 0.85
    }
}
```

### 4.4 风险管理

#### 4.4.1 获取风险指标

```http
GET /api/risk/metrics
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "portfolio_value": 1000000.0,
        "volatility": 0.3071,
        "var_95": -0.0289,
        "var_99": -0.0385,
        "expected_shortfall_95": -0.0360,
        "expected_shortfall_99": -0.0432,
        "max_drawdown": 0.2551,
        "sharpe_ratio": 0.6611,
        "sortino_ratio": 1.2072,
        "calmar_ratio": 0.9136
    }
}
```

#### 4.4.2 获取组合风险

```http
GET /api/risk/portfolio
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total_exposure": 850000.0,
        "net_exposure": 650000.0,
        "position_count": 5,
        "top_positions": [
            {
                "symbol": "0700.HK",
                "exposure": 360000.0,
                "percentage": 36.0
            }
        ],
        "sector_allocation": {
            "Technology": 45.2,
            "Finance": 30.5,
            "Consumer": 24.3
        }
    }
}
```

### 4.5 回测相关

#### 4.5.1 运行回测

```http
POST /api/backtest/run
```

**请求体**:
```json
{
    "symbol": "0700.HK",
    "strategy": "kdj",
    "start_date": "2022-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 1000000,
    "parameters": {
        "k_period": 9,
        "d_period": 3,
        "oversold": 20,
        "overbought": 80
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "backtest_id": "BT_20251031_001",
        "symbol": "0700.HK",
        "strategy": "kdj",
        "period": "2022-01-01 to 2024-01-01",
        "results": {
            "total_return": 0.2047,
            "annualized_return": 0.2330,
            "volatility": 0.3071,
            "max_drawdown": -0.2551,
            "sharpe_ratio": 0.6611,
            "win_rate": 0.5317,
            "total_trades": 252,
            "final_value": 1204700.0
        }
    }
}
```

#### 4.5.2 获取回测历史

```http
GET /api/backtest/list
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "backtest_id": "BT_20251031_001",
                "symbol": "0700.HK",
                "strategy": "kdj",
                "start_date": "2022-01-01",
                "end_date": "2024-01-01",
                "total_return": 0.2047,
                "created_at": "2025-10-31T15:00:00Z"
            }
        ]
    }
}
```

### 4.6 策略相关

#### 4.6.1 获取可用策略

```http
GET /api/strategies
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "basic_strategies": [
            {
                "name": "ma",
                "display_name": "Moving Average",
                "category": "基础指标",
                "description": "移动平均策略",
                "parameters": [
                    {
                        "name": "fast_period",
                        "type": "integer",
                        "default": 12,
                        "min": 5,
                        "max": 50
                    }
                ]
            }
        ],
        "advanced_strategies": [
            {
                "name": "kdj",
                "display_name": "KDJ",
                "category": "高级指标",
                "description": "随机指标策略",
                "parameters": [
                    {
                        "name": "k_period",
                        "type": "integer",
                        "default": 9,
                        "min": 5,
                        "max": 30
                    }
                ]
            }
        ]
    }
}
```

### 4.7 任务管理

#### 4.7.1 获取任务列表

```http
GET /api/tasks
```

**响应示例**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "title": "优化交易算法",
            "description": "提升交易执行效率",
            "status": "进行中",
            "priority": "P0",
            "is_completed": false,
            "assignee": "量化分析师",
            "created_at": "2025-10-01T10:00:00Z",
            "updated_at": "2025-10-31T15:00:00Z"
        }
    ]
}
```

#### 4.7.2 创建任务

```http
POST /api/tasks
```

**请求体**:
```json
{
    "title": "新功能开发",
    "description": "实现新功能模块",
    "status": "待开始",
    "priority": "P1",
    "assignee": "开发团队"
}
```

### 4.8 Sprint管理

#### 4.8.1 获取Sprint列表

```http
GET /api/sprints
```

**响应示例**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Sprint 1",
            "description": "第一阶段开发",
            "start_date": "2025-10-01",
            "end_date": "2025-10-15",
            "status": "已完成",
            "task_count": 10,
            "completed_task_count": 10
        }
    ]
}
```

---

## 5. 数据模型

### 5.1 通用响应模型

```python
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime
```

### 5.2 错误模型

```python
class APIError(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None
```

### 5.3 Agent模型

```python
class Agent(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    status: str
    healthy: bool
    messages: int
    uptime: str
    cpu_usage: float
    memory_usage: float
```

### 5.4 交易模型

```python
class Position(BaseModel):
    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    pnl_percentage: float
    currency: str
    exchange: str

class Order(BaseModel):
    order_id: str
    symbol: str
    side: str
    quantity: int
    filled_quantity: int
    price: float
    avg_price: float
    status: str
    timestamp: datetime
```

---

## 6. 错误处理

### 6.1 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 数据验证错误 |
| 429 | 请求频率过高 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 6.2 错误代码

| 错误代码 | 说明 |
|----------|------|
| INVALID_SYMBOL | 股票代码格式错误 |
| INSUFFICIENT_BALANCE | 余额不足 |
| INVALID_ORDER_TYPE | 订单类型错误 |
| MARKET_CLOSED | 市场已关闭 |
| RATE_LIMIT_EXCEEDED | 超出频率限制 |
| SERVICE_UNAVAILABLE | 服务不可用 |

### 6.3 错误示例

```json
{
    "success": false,
    "error": {
        "code": "INVALID_SYMBOL",
        "message": "股票代码格式不正确",
        "details": {
            "field": "symbol",
            "value": "INVALID",
            "expected": "如: 0700.HK"
        }
    },
    "timestamp": "2025-10-31T15:00:00Z"
}
```

---

## 7. 代码示例

### 7.1 Python示例

#### 获取Agent列表
```python
import requests

BASE_URL = "http://localhost:8000"

# 获取Agent列表
response = requests.get(f"{BASE_URL}/api/agents/list")
if response.status_code == 200:
    data = response.json()
    agents = data["data"]
    for agent in agents:
        print(f"Agent: {agent['name']} - Status: {agent['status']}")
else:
    print(f"Error: {response.status_code}")
```

#### 下单交易
```python
order_data = {
    "symbol": "0700.HK",
    "order_type": "BUY",
    "quantity": 1000,
    "price": 350.0
}

response = requests.post(
    f"{BASE_URL}/api/trading/order",
    json=order_data
)

if response.status_code == 200:
    result = response.json()
    print(f"Order submitted: {result['data']['order_id']}")
else:
    error = response.json()
    print(f"Error: {error['error']['message']}")
```

#### 运行回测
```python
backtest_data = {
    "symbol": "0700.HK",
    "strategy": "kdj",
    "start_date": "2022-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 1000000,
    "parameters": {
        "k_period": 9,
        "d_period": 3,
        "oversold": 20,
        "overbought": 80
    }
}

response = requests.post(
    f"{BASE_URL}/api/backtest/run",
    json=backtest_data
)

if response.status_code == 200:
    result = response.json()
    print(f"Total Return: {result['data']['results']['total_return']:.2%}")
```

### 7.2 JavaScript示例

#### 获取持仓
```javascript
async function getPositions() {
    try {
        const response = await fetch('http://localhost:8000/api/trading/positions');
        const data = await response.json();

        if (data.success) {
            data.data.items.forEach(position => {
                console.log(`${position.symbol}: ${position.quantity} shares`);
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

#### 获取风险指标
```javascript
async function getRiskMetrics() {
    const response = await fetch('http://localhost:8000/api/risk/metrics');
    const data = await response.json();

    if (data.success) {
        console.log('VaR (95%):', data.data.var_95);
        console.log('Max Drawdown:', data.data.max_drawdown);
        console.log('Sharpe Ratio:', data.data.sharpe_ratio);
    }
}
```

### 7.3 cURL示例

#### 健康检查
```bash
curl -X GET "http://localhost:8000/health" \
     -H "accept: application/json"
```

#### 获取Agent列表
```bash
curl -X GET "http://localhost:8000/api/agents/list" \
     -H "accept: application/json"
```

#### 下单交易
```bash
curl -X POST "http://localhost:8000/api/trading/order" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "0700.HK",
       "order_type": "BUY",
       "quantity": 1000,
       "price": 350.0
     }'
```

---

## 8. SDK使用

### 8.1 Python SDK示例

```python
# 安装SDK
pip install codex-sdk

# 使用SDK
from codex_sdk import CODEXClient

client = CODEXClient(
    base_url="http://localhost:8000",
    token="your_access_token"
)

# 获取Agent状态
agents = client.agents.list()
print(f"Active agents: {len([a for a in agents if a.status == 'running'])}")

# 下单交易
order = client.trading.place_order(
    symbol="0700.HK",
    side="BUY",
    quantity=1000,
    price=350.0
)
print(f"Order submitted: {order.order_id}")

# 运行回测
backtest = client.backtest.run(
    symbol="0700.HK",
    strategy="kdj",
    start_date="2022-01-01",
    end_date="2024-01-01"
)
print(f"Total return: {backtest.results.total_return:.2%}")
```

---

## 最佳实践

### 1. 错误处理

```python
try:
    response = requests.get(f"{BASE_URL}/api/trading/positions")
    response.raise_for_status()
    data = response.json()

    if data["success"]:
        # 处理成功响应
        positions = data["data"]["items"]
    else:
        # 处理业务错误
        print(f"Error: {data['error']['message']}")

except requests.exceptions.RequestException as e:
    # 处理网络错误
    print(f"Network error: {e}")
```

### 2. 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def api_call_with_retry(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### 3. 限流控制

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        now = datetime.now()
        self.requests = [
            req_time for req_time in self.requests
            if now - req_time < timedelta(seconds=self.time_window)
        ]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).seconds
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(now)

limiter = RateLimiter(max_requests=10, time_window=60)
limiter.wait_if_needed()
response = requests.get(f"{BASE_URL}/api/agents/list")
```

---

**API文档版本**: v1.0.0
**最后更新**: 2025-10-31
**文档维护**: CODEX开发团队

---

**快速链接**:
- 交互式文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
- OpenAPI规范: http://localhost:8000/openapi.json
