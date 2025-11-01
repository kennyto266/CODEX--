# 📡 CODEX Trading Dashboard - API 文档

## 📋 目录

1. [概述](#概述)
2. [认证](#认证)
3. [基础信息](#基础信息)
4. [智能体API](#智能体api)
5. [交易API](#交易api)
6. [风险API](#风险api)
7. [回测API](#回测api)
8. [监控API](#监控api)
9. [WebSocket API](#websocket-api)
10. [错误代码](#错误代码)
11. [SDK和示例](#sdk和示例)

---

## 概述

CODEX Trading Dashboard 提供RESTful API和WebSocket接口，用于量化交易系统的数据交互和实时监控。

### API特性

- ✅ RESTful设计风格
- ✅ JSON数据格式
- ✅ WebSocket实时通信
- ✅ 统一的错误处理
- ✅ 性能优化 (缓存、防抖)
- ✅ 完整的文档生成

### 基础URL

```
开发环境: http://localhost:8001
生产环境: https://api.codex-trading.com

所有API请求都应使用HTTPS (生产环境)
```

### 内容类型

```
Content-Type: application/json
Accept: application/json
```

---

## 认证

目前API采用无认证模式，后续版本将支持API Key认证。

```http
# 示例请求头
GET /api/agents/list HTTP/1.1
Host: localhost:8001
Accept: application/json

# 未来版本认证
GET /api/agents/list HTTP/1.1
Host: localhost:8001
Authorization: Bearer YOUR_API_KEY
Accept: application/json
```

---

## 基础信息

### 健康检查

检查服务健康状态

```http
GET /api/health
```

**响应示例** (200):
```json
{
  "status": "healthy",
  "timestamp": 1703688000.123,
  "uptime": 3600,
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 42.8,
    "disk_percent": 23.5
  },
  "version": "1.0.0"
}
```

**字段说明**:
- `status`: 服务状态 (healthy | warning | unhealthy)
- `timestamp`: Unix时间戳
- `uptime`: 运行时间 (秒)
- `system`: 系统资源使用率

### 系统信息

获取系统详细信息

```http
GET /api/system/info
```

**响应示例** (200):
```json
{
  "platform": "Linux",
  "python_version": "3.10.12",
  "app_version": "1.0.0",
  "components": {
    "vue": "3.4.0",
    "fastapi": "0.104.1",
    "uvicorn": "0.24.0"
  },
  "features": [
    "multi_agent",
    "backtest_engine",
    "risk_management",
    "real_time_monitoring"
  ]
}
```

---

## 智能体API

### 获取智能体列表

```http
GET /api/agents/list
```

**响应示例** (200):
```json
[
  {
    "id": 1,
    "name": "Coordinator",
    "type": "Orchestrator",
    "status": "running",
    "cpu_usage": 15.2,
    "memory_usage": 256.5,
    "uptime": 7200,
    "tasks_completed": 1245,
    "success_rate": 99.2,
    "last_heartbeat": 1703687940
  },
  {
    "id": 2,
    "name": "Data Scientist",
    "type": "Data Analysis",
    "status": "running",
    "cpu_usage": 22.8,
    "memory_usage": 512.3,
    "uptime": 6800,
    "tasks_completed": 856,
    "success_rate": 97.8,
    "last_heartbeat": 1703687935
  }
]
```

**字段说明**:
- `id`: 智能体唯一ID
- `name`: 智能体名称
- `type`: 智能体类型
- `status`: 状态 (running | idle | stopped | error)
- `cpu_usage`: CPU使用率 (%)
- `memory_usage`: 内存使用 (MB)
- `uptime`: 运行时间 (秒)
- `tasks_completed`: 已完成任务数
- `success_rate`: 成功率 (%)
- `last_heartbeat`: 最后心跳时间 (Unix时间戳)

### 启动智能体

```http
POST /api/agents/{agent_id}/start
```

**路径参数**:
- `agent_id`: 智能体ID (整数)

**响应示例** (200):
```json
{
  "success": true,
  "message": "Agent started successfully",
  "agent_id": 1,
  "timestamp": 1703688000
}
```

### 停止智能体

```http
POST /api/agents/{agent_id}/stop
```

**路径参数**:
- `agent_id`: 智能体ID (整数)

**响应示例** (200):
```json
{
  "success": true,
  "message": "Agent stopped successfully",
  "agent_id": 1,
  "timestamp": 1703688000
}
```

### 重启智能体

```http
POST /api/agents/{agent_id}/restart
```

**响应示例** (200):
```json
{
  "success": true,
  "message": "Agent restarted successfully",
  "agent_id": 1,
  "timestamp": 1703688000
}
```

### 获取智能体日志

```http
GET /api/agents/{agent_id}/logs?limit=100&level=INFO
```

**查询参数**:
- `limit`: 返回日志条数 (默认100, 最大1000)
- `level`: 日志级别 (DEBUG | INFO | WARNING | ERROR)
- `since`: 起始时间戳 (可选)

**响应示例** (200):
```json
[
  {
    "timestamp": 1703687950,
    "level": "INFO",
    "message": "Agent initialized successfully",
    "component": "Coordinator"
  },
  {
    "timestamp": 1703687945,
    "level": "WARNING",
    "message": "High memory usage detected",
    "component": "Data Scientist"
  }
]
```

### 批量操作智能体

```http
POST /api/agents/batch_action
```

**请求体**:
```json
{
  "action": "start",
  "agent_ids": [1, 2, 3]
}
```

**支持的action**:
- `start`: 启动
- `stop`: 停止
- `restart`: 重启

**响应示例** (200):
```json
{
  "success": true,
  "results": [
    {
      "agent_id": 1,
      "success": true,
      "message": "Agent started"
    },
    {
      "agent_id": 2,
      "success": false,
      "error": "Agent already running"
    }
  ]
}
```

---

## 交易API

### 获取投资组合

```http
GET /api/trading/portfolio
```

**响应示例** (200):
```json
{
  "positions": [
    {
      "symbol": "0700.HK",
      "name": "Tencent Holdings",
      "shares": 1000,
      "avg_cost": 320.50,
      "current_price": 318.25,
      "market_value": 318250,
      "unrealized_pnl": -2250,
      "unrealized_pnl_percent": -0.70,
      "weight": 35.2
    },
    {
      "symbol": "0388.HK",
      "name": "HKEX",
      "shares": 500,
      "avg_cost": 380.00,
      "current_price": 385.75,
      "market_value": 192875,
      "unrealized_pnl": 2875,
      "unrealized_pnl_percent": 1.51,
      "weight": 21.3
    }
  ],
  "cash_balance": 392875.50,
  "total_value": 903875.50,
  "total_pnl": 625.00,
  "total_pnl_percent": 0.07
}
```

**字段说明**:
- `positions`: 持仓列表
- `cash_balance`: 现金余额
- `total_value`: 总资产价值
- `total_pnl`: 总盈亏
- `total_pnl_percent`: 总盈亏百分比

### 获取订单列表

```http
GET /api/trading/orders?limit=50&status=pending
```

**查询参数**:
- `limit`: 返回条数 (默认50, 最大200)
- `status`: 订单状态 (all | pending | filled | cancelled)
- `symbol`: 股票代码 (可选)

**响应示例** (200):
```json
{
  "orders": [
    {
      "id": 1001,
      "symbol": "0700.HK",
      "side": "BUY",
      "quantity": 100,
      "price": 318.50,
      "status": "filled",
      "filled_quantity": 100,
      "filled_price": 318.50,
      "timestamp": 1703687500
    },
    {
      "id": 1002,
      "symbol": "0388.HK",
      "side": "SELL",
      "quantity": 200,
      "price": 385.00,
      "status": "pending",
      "filled_quantity": 0,
      "timestamp": 1703687950
    }
  ]
}
```

**字段说明**:
- `side`: 交易方向 (BUY | SELL)
- `status`: 订单状态
- `filled_quantity`: 已成交数量
- `filled_price`: 成交均价

### 下单

```http
POST /api/trading/orders
```

**请求体**:
```json
{
  "symbol": "0700.HK",
  "side": "BUY",
  "quantity": 100,
  "price": 318.50,
  "order_type": "LIMIT"
}
```

**字段说明**:
- `symbol`: 股票代码 (必需)
- `side`: 交易方向 (必需)
- `quantity`: 数量 (必需)
- `price`: 价格 (必需, LIMIT订单)
- `order_type`: 订单类型 (MARKET | LIMIT)

**响应示例** (201):
```json
{
  "success": true,
  "order": {
    "id": 1003,
    "symbol": "0700.HK",
    "side": "BUY",
    "quantity": 100,
    "price": 318.50,
    "status": "pending",
    "timestamp": 1703688000
  },
  "message": "Order placed successfully"
}
```

### 撤单

```http
DELETE /api/trading/orders/{order_id}
```

**路径参数**:
- `order_id`: 订单ID

**响应示例** (200):
```json
{
  "success": true,
  "order_id": 1002,
  "message": "Order cancelled successfully"
}
```

### 获取交易历史

```http
GET /api/trading/history?start_date=2025-01-01&end_date=2025-12-31
```

**查询参数**:
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `symbol`: 股票代码 (可选)

**响应示例** (200):
```json
{
  "trades": [
    {
      "id": 5001,
      "symbol": "0700.HK",
      "side": "BUY",
      "quantity": 100,
      "price": 318.50,
      "timestamp": 1703687500,
      "pnl": -225.00,
      "commission": 10.00
    },
    {
      "id": 5002,
      "symbol": "0388.HK",
      "side": "SELL",
      "quantity": 200,
      "price": 385.75,
      "timestamp": 1703687400,
      "pnl": 350.00,
      "commission": 15.00
    }
  ]
}
```

### 获取实时行情

```http
GET /api/trading/quote?symbol=0700.HK
```

**查询参数**:
- `symbol`: 股票代码

**响应示例** (200):
```json
{
  "symbol": "0700.HK",
  "name": "Tencent Holdings",
  "price": 318.25,
  "change": -2.25,
  "change_percent": -0.70,
  "volume": 12500000,
  "high": 320.50,
  "low": 317.80,
  "open": 319.00,
  "prev_close": 320.50,
  "timestamp": 1703688000
}
```

---

## 风险API

### 获取风险指标

```http
GET /api/risk/metrics
```

**响应示例** (200):
```json
{
  "portfolio_var": 125000.00,
  "portfolio_var_change": -2.5,
  "portfolio_beta": 1.12,
  "sharpe_ratio": 1.85,
  "max_drawdown": 12.35,
  "volatility": 18.6,
  "correlation_matrix": [
    [1.00, 0.75, 0.68],
    [0.75, 1.00, 0.82],
    [0.68, 0.82, 1.00]
  ],
  "top_holdings": [
    {
      "symbol": "0700.HK",
      "weight": 35.5,
      "risk_contribution": 28.2
    },
    {
      "symbol": "0388.HK",
      "weight": 28.3,
      "risk_contribution": 24.1
    }
  ]
}
```

### 获取VaR分析

```http
GET /api/risk/var?confidence_level=0.95&horizon_days=1
```

**查询参数**:
- `confidence_level`: 置信水平 (0.90 | 0.95 | 0.99, 默认0.95)
- `horizon_days`: 持有期间 (天数, 默认1)

**响应示例** (200):
```json
{
  "historical_var": 125000,
  "parametric_var": 118500,
  "monte_carlo_var": 122800,
  "confidence_level": 0.95,
  "horizon_days": 1,
  "timestamp": 1703688000,
  "scenarios": [
    {
      "scenario": "Market Crash",
      "var": 285000,
      "probability": 0.05
    },
    {
      "scenario": "Normal Volatility",
      "var": 125000,
      "probability": 0.90
    },
    {
      "scenario": "Low Volatility",
      "var": 75000,
      "probability": 0.05
    }
  ]
}
```

### 获取风险告警

```http
GET /api/risk/alerts?status=active
```

**查询参数**:
- `status`: 告警状态 (all | active | resolved)
- `severity`: 严重级别 (all | critical | warning | info)

**响应示例** (200):
```json
{
  "alerts": [
    {
      "id": 2001,
      "severity": "high",
      "category": "risk",
      "title": "VaR Exceeded Threshold",
      "message": "Portfolio VaR exceeded $100,000 limit",
      "status": "active",
      "timestamp": 1703687900,
      "threshold": 100000,
      "current_value": 125000
    },
    {
      "id": 2002,
      "severity": "medium",
      "category": "concentration",
      "title": "Position Concentration High",
      "message": "0700.HK position exceeds 30%",
      "status": "active",
      "timestamp": 1703687850,
      "threshold": 30,
      "current_value": 35.5
    }
  ]
}
```

### 压力测试

```http
POST /api/risk/stress_test
```

**请求体**:
```json
{
  "scenarios": [
    {
      "name": "Market Crash",
      "shock": -0.20,
      "volatility_multiplier": 2.0
    },
    {
      "name": "Interest Rate Hike",
      "shock": 0.02,
      "sector": "financial"
    }
  ]
}
```

**响应示例** (200):
```json
{
  "results": [
    {
      "scenario": "Market Crash",
      "portfolio_impact": -185000,
      "portfolio_impact_percent": -20.5,
      "new_var": 385000,
      "days_to_recovery": 45
    },
    {
      "scenario": "Interest Rate Hike",
      "portfolio_impact": -25000,
      "portfolio_impact_percent": -2.8,
      "new_var": 145000,
      "days_to_recovery": 5
    }
  ]
}
```

---

## 回测API

### 启动回测

```http
POST /api/backtest/start
```

**请求体**:
```json
{
  "strategy": "kdj",
  "symbol": "0700.HK",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 1000000,
  "parameters": {
    "k_period": 9,
    "d_period": 3,
    "oversold": 20,
    "overbought": 80
  }
}
```

**响应示例** (202):
```json
{
  "success": true,
  "backtest_id": "BT_2025_0001",
  "status": "running",
  "message": "Backtest started",
  "timestamp": 1703688000
}
```

### 获取回测状态

```http
GET /api/backtest/status/{backtest_id}
```

**响应示例** (200):
```json
{
  "backtest_id": "BT_2025_0001",
  "status": "completed",
  "progress": 100,
  "start_time": 1703688000,
  "end_time": 1703688100,
  "duration": 100
}
```

**状态说明**:
- `pending`: 等待中
- `running`: 运行中
- `completed`: 已完成
- `failed`: 失败
- `cancelled`: 已取消

### 获取回测结果

```http
GET /api/backtest/results/{backtest_id}
```

**响应示例** (200):
```json
{
  "backtest_id": "BT_2025_0001",
  "strategy": "kdj",
  "symbol": "0700.HK",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "metrics": {
    "total_return": 25.67,
    "annualized_return": 8.12,
    "volatility": 18.5,
    "sharpe_ratio": 1.45,
    "max_drawdown": 15.23,
    "win_rate": 62.5,
    "total_trades": 127,
    "profit_factor": 1.85
  },
  "equity_curve": [
    {"date": "2023-01-01", "value": 1000000},
    {"date": "2023-01-02", "value": 1001500},
    ...
  ],
  "trades": [
    {
      "date": "2023-01-15",
      "symbol": "0700.HK",
      "side": "BUY",
      "price": 318.50,
      "quantity": 100,
      "pnl": 1250.00
    },
    ...
  ]
}
```

### 获取回测列表

```http
GET /api/backtest/list?limit=20&offset=0
```

**查询参数**:
- `limit`: 返回条数 (默认20)
- `offset`: 偏移量 (分页)

**响应示例** (200):
```json
{
  "total": 45,
  "backtests": [
    {
      "backtest_id": "BT_2025_0001",
      "strategy": "kdj",
      "symbol": "0700.HK",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "status": "completed",
      "total_return": 25.67,
      "created_at": 1703688000
    },
    ...
  ]
}
```

### 优化策略参数

```http
POST /api/backtest/optimize
```

**请求体**:
```json
{
  "strategy": "kdj",
  "symbol": "0700.HK",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "parameters": {
    "k_period": {"min": 5, "max": 30, "step": 5},
    "d_period": {"min": 3, "max": 5, "step": 1},
    "oversold": {"min": 20, "max": 40, "step": 5},
    "overbought": {"min": 60, "max": 80, "step": 5}
  },
  "objective": "sharpe_ratio",
  "max_workers": 4
}
```

**响应示例** (202):
```json
{
  "success": true,
  "optimization_id": "OPT_2025_0001",
  "status": "running",
  "total_combinations": 400,
  "completed_combinations": 0,
  "timestamp": 1703688000
}
```

### 获取优化结果

```http
GET /api/backtest/optimization/{optimization_id}
```

**响应示例** (200):
```json
{
  "optimization_id": "OPT_2025_0001",
  "status": "completed",
  "best_parameters": {
    "k_period": 9,
    "d_period": 3,
    "oversold": 20,
    "overbought": 80
  },
  "best_metrics": {
    "total_return": 28.45,
    "sharpe_ratio": 1.62,
    "max_drawdown": 14.2
  },
  "results": [
    {
      "parameters": {"k_period": 9, "d_period": 3, "oversold": 20, "overbought": 80},
      "metrics": {"total_return": 28.45, "sharpe_ratio": 1.62}
    },
    ...
  ]
}
```

---

## 监控API

### 性能监控

```http
POST /api/monitoring/performance
```

**请求体**:
```json
{
  "loadTime": 1520,
  "domContentLoaded": 850,
  "firstPaint": 620,
  "timestamp": 1703688000
}
```

**响应示例** (200):
```json
{
  "success": true,
  "recorded": true
}
```

### 错误报告

```http
POST /api/monitoring/errors
```

**请求体**:
```json
{
  "message": "Component render error",
  "stack": "Error: ...",
  "component": "AgentPanel",
  "info": "error in mounted hook",
  "timestamp": 1703688000
}
```

**响应示例** (200):
```json
{
  "success": true,
  "error_id": "ERR_2025_0001"
}
```

### 获取系统指标

```http
GET /api/monitoring/metrics
```

**响应示例** (200):
```json
{
  "cpu": {
    "usage": 15.2,
    "load_average": [0.5, 0.6, 0.8]
  },
  "memory": {
    "total": 8589934592,
    "used": 3672095232,
    "available": 4917839360,
    "percent": 42.8
  },
  "disk": {
    "total": 107374182400,
    "used": 25769803776,
    "free": 81604378624,
    "percent": 23.5
  },
  "network": {
    "bytes_sent": 1048576,
    "bytes_recv": 2097152,
    "packets_sent": 1024,
    "packets_recv": 2048
  },
  "timestamp": 1703688000
}
```

---

## WebSocket API

### 建立连接

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

// 连接事件
ws.onopen = () => {
    console.log('✅ WebSocket connected');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Message:', data);
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = () => {
    console.log('🔌 WebSocket disconnected');
};
```

### 订阅消息

```javascript
// 订阅智能体状态更新
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'agents'
}));

// 订阅市场数据
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'market_data',
    symbol: '0700.HK'
}));

// 订阅交易信号
ws.send(JSON.stringify({
    action: 'subscribe',
    channel: 'trading_signals'
}));
```

### 取消订阅

```javascript
ws.send(JSON.stringify({
    action: 'unsubscribe',
    channel: 'agents'
}));
```

### 智能体状态更新

```json
{
  "type": "agent_update",
  "channel": "agents",
  "data": {
    "agent_id": 1,
    "name": "Coordinator",
    "status": "running",
    "cpu_usage": 15.2,
    "memory_usage": 256.5,
    "timestamp": 1703688000
  }
}
```

### 市场数据更新

```json
{
  "type": "market_update",
  "channel": "market_data",
  "symbol": "0700.HK",
  "data": {
    "price": 318.25,
    "change": -2.25,
    "volume": 12500000,
    "timestamp": 1703688000
  }
}
```

### 交易信号

```json
{
  "type": "trading_signal",
  "channel": "trading_signals",
  "data": {
    "signal_id": "SIG_2025_0001",
    "symbol": "0700.HK",
    "action": "BUY",
    "strength": 0.85,
    "timestamp": 1703688000
  }
}
```

### 风险告警

```json
{
  "type": "risk_alert",
  "channel": "risk_alerts",
  "data": {
    "alert_id": 2001,
    "severity": "high",
    "message": "VaR exceeded threshold",
    "timestamp": 1703688000
  }
}
```

---

## 错误代码

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求错误 |
| 401 | 未认证 |
| 403 | 禁止访问 |
| 404 | 资源未找到 |
| 429 | 请求频率过高 |
| 500 | 服务器内部错误 |

### 业务错误代码

```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Invalid stock symbol",
    "details": {
      "symbol": "INVALID",
      "expected_format": "XXXX.HK"
    }
  }
}
```

**常见错误代码**:
- `INVALID_SYMBOL`: 股票代码无效
- `INSUFFICIENT_CASH`: 现金余额不足
- `POSITION_NOT_FOUND`: 持仓不存在
- `ORDER_NOT_FOUND`: 订单不存在
- `STRATEGY_NOT_FOUND`: 策略不存在
- `BACKTEST_NOT_FOUND`: 回测任务不存在
- `AGENT_NOT_FOUND`: 智能体不存在
- `RATE_LIMIT_EXCEEDED`: 超出频率限制

---

## SDK和示例

### Python SDK

```python
import requests

class CodexAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_agents(self):
        response = requests.get(f"{self.base_url}/api/agents/list")
        return response.json()

    def start_agent(self, agent_id):
        response = requests.post(f"{self.base_url}/api/agents/{agent_id}/start")
        return response.json()

    def get_portfolio(self):
        response = requests.get(f"{self.base_url}/api/trading/portfolio")
        return response.json()

    def place_order(self, order_data):
        response = requests.post(
            f"{self.base_url}/api/trading/orders",
            json=order_data
        )
        return response.json()

# 使用示例
api = CodexAPI("http://localhost:8001")

# 获取智能体列表
agents = api.get_agents()
print(f"Active agents: {len([a for a in agents if a['status'] == 'running'])}")

# 启动智能体
result = api.start_agent(1)
print(result['message'])

# 获取投资组合
portfolio = api.get_portfolio()
print(f"Total value: ${portfolio['total_value']:,.2f}")
```

### JavaScript SDK

```javascript
class CodexAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async getAgents() {
        const response = await fetch(`${this.baseUrl}/api/agents/list`);
        return response.json();
    }

    async startAgent(agentId) {
        const response = await fetch(`${this.baseUrl}/api/agents/${agentId}/start`, {
            method: 'POST'
        });
        return response.json();
    }

    async getPortfolio() {
        const response = await fetch(`${this.baseUrl}/api/trading/portfolio`);
        return response.json();
    }

    async placeOrder(orderData) {
        const response = await fetch(`${this.baseUrl}/api/trading/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        return response.json();
    }

    connectWebSocket() {
        return new WebSocket(`ws://${this.baseUrl}/ws`);
    }
}

// 使用示例
const api = new CodexAPI('localhost:8001');

// 获取智能体列表
api.getAgents().then(agents => {
    console.log(`Active agents: ${agents.filter(a => a.status === 'running').length}`);
});

// 下单
api.placeOrder({
    symbol: '0700.HK',
    side: 'BUY',
    quantity: 100,
    price: 318.50,
    order_type: 'LIMIT'
}).then(result => {
    console.log(`Order placed: ${result.order.id}`);
});

// WebSocket连接
const ws = api.connectWebSocket();
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

### cURL示例

```bash
# 获取智能体列表
curl -X GET http://localhost:8001/api/agents/list

# 启动智能体
curl -X POST http://localhost:8001/api/agents/1/start

# 获取投资组合
curl -X GET http://localhost:8001/api/trading/portfolio

# 下单
curl -X POST http://localhost:8001/api/trading/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "0700.HK",
    "side": "BUY",
    "quantity": 100,
    "price": 318.50,
    "order_type": "LIMIT"
  }'

# 启动回测
curl -X POST http://localhost:8001/api/backtest/start \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "kdj",
    "symbol": "0700.HK",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000
  }'

# 健康检查
curl -X GET http://localhost:8001/api/health
```

### WebSocket测试

```javascript
// 使用wscat测试
npm install -g wscat
wscat -c ws://localhost:8001/ws

// 发送订阅消息
{"action":"subscribe","channel":"agents"}
```

---

## 速率限制

为了保证系统稳定性，API有速率限制：

- **普通API**: 每分钟60次请求
- **交易API**: 每分钟30次请求
- **回测API**: 每分钟10次请求
- **WebSocket**: 每秒10条消息

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

---

## 版本控制

API使用URL版本控制：

```
http://localhost:8001/api/v1/agents/list
http://localhost:8001/api/v1/trading/portfolio
```

当前版本: `v1`

---

## 反馈和支持

如果您在使用API时遇到问题：

1. **查看文档**: 阅读完整的API文档
2. **检查示例**: 参考SDK和cURL示例
3. **查看日志**: 检查服务器日志获取详细错误
4. **创建Issue**: 在GitHub提交问题报告
5. **联系支持**: 发送邮件到 support@codex-trading.com

---

**感谢使用 CODEX Trading Dashboard API！**

---

*最后更新: 2025-10-27*
*API版本: v1.0.0*
*OpenAPI规范: http://localhost:8001/docs*
