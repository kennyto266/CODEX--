# WebSocket实时更新系统 - Phase 4 实现指南

## 概述

本指南描述了港股量化交易系统Phase 4中实现的WebSocket实时更新系统。该系统提供了实时数据推送、进度跟踪、图表更新和通知功能。

## 实现的任务

### T083 - WebSocket服务器 ✅
- **文件**: `src/api/websocket.py`
- **功能**:
  - FastAPI WebSocket端点 (`/api/v1/websocket/ws`)
  - 连接管理和池化
  - 消息广播和路由
  - 错误处理和自动重连
  - 心跳检测

### T084 - 回测进度更新 ✅
- **文件**: `src/api/websocket/progress_tracker.py`
- **功能**:
  - 实时回测进度跟踪
  - 任务状态管理 (pending, running, completed, failed)
  - 步骤级别进度更新
  - 客户端订阅机制
  - 自动重连支持

### T085 - 实时图表更新 ✅
- **文件**: `src/api/websocket/chart_updates.py`
- **功能**:
  - 实时价格数据推送
  - 技术指标数据更新
  - 批量数据更新
  - 高效传输机制
  - 性能优化

### T086 - 通知系统 ✅
- **文件**: `src/api/websocket/notifications.py`
- **功能**:
  - 操作完成通知
  - 消息推送中心
  - 通知历史记录
  - 用户偏好设置
  - 自动清理机制

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     客户端 (前端)                              │
└────────────────────┬────────────────────────────────────────┘
                     │ WebSocket (ws://host/api/v1/websocket/ws)
                     │
┌────────────────────▼────────────────────────────────────────┐
│              WebSocket服务器                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ConnectionManager                                     │  │
│  │  - 连接池管理                                           │  │
│  │  - 订阅管理                                             │  │
│  │  - 消息广播                                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌────────────┬────────────┬─────────────┬──────────────┐  │
│  │ 进度跟踪器 │ 图表数据   │  通知中心   │  后台任务     │  │
│  │  管理器    │  管理器    │             │  管理        │  │
│  └────────────┴────────────┴─────────────┴──────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    业务逻辑层                                │
│  - 回测引擎                                                    │
│  - 策略优化                                                    │
│  - 数据适配器                                                  │
│  - 通知服务                                                    │
└─────────────────────────────────────────────────────────────┘
```

## API 端点

### WebSocket端点

#### 主连接端点
```
WebSocket: ws://localhost:8001/api/v1/websocket/ws
```

#### HTTP管理端点
```
GET  /api/v1/websocket/status          # 获取连接状态
POST /api/v1/websocket/broadcast       # 广播消息
```

## WebSocket协议

### 客户端 → 服务器消息

#### 1. 建立连接
```json
{
  "type": "ping"
}
```

**响应**:
```json
{
  "type": "pong",
  "timestamp": "2025-11-09T12:00:00Z"
}
```

#### 2. 订阅频道
```json
{
  "type": "subscribe",
  "channel": "backtest_progress"
}
```

**频道列表**:
- `backtest_progress` - 回测进度更新
- `chart_updates` - 图表数据更新
- `notifications` - 系统通知
- `system_status` - 系统状态
- `market_data` - 市场数据

**响应**:
```json
{
  "type": "subscription_confirmed",
  "channel": "backtest_progress",
  "timestamp": "2025-11-09T12:00:00Z"
}
```

#### 3. 取消订阅
```json
{
  "type": "unsubscribe",
  "channel": "backtest_progress"
}
```

#### 4. 订阅图表数据
```json
{
  "type": "subscribe_chart",
  "symbol": "0700.HK"
}
```

#### 5. 请求回测进度
```json
{
  "type": "request_backtest_progress",
  "task_id": "backtest_001"
}
```

#### 6. 获取通知
```json
{
  "type": "get_notifications",
  "limit": 50
}
```

### 服务器 → 客户端消息

#### 1. 回测进度更新
```json
{
  "type": "backtest_progress_update",
  "task_id": "backtest_001",
  "data": {
    "task_id": "backtest_001",
    "status": "running",
    "progress": 45.5,
    "current_step": "策略执行",
    "current_step_index": 4,
    "total_steps": 10,
    "message": "正在执行KDJ策略...",
    "estimated_time_remaining": 120.5,
    "elapsed_time": 30.2,
    "data": {
      "symbol": "0700.HK",
      "strategy": "kdj"
    }
  },
  "timestamp": "2025-11-09T12:00:00Z"
}
```

#### 2. 图表数据更新
```json
{
  "type": "chart_update",
  "symbol": "0700.HK",
  "update_type": "add",
  "data_points": [
    {
      "timestamp": 1731144000.0,
      "data_type": "ohlcv",
      "value": 355.0,
      "additional_data": {
        "field": "close"
      }
    },
    {
      "timestamp": 1731144000.0,
      "data_type": "indicator_KDJ_K",
      "value": 65.5,
      "additional_data": {
        "D": 60.0,
        "J": 75.0
      }
    }
  ],
  "metadata": {
    "data_types": ["ohlcv", "indicator_KDJ_K"],
    "batch_size": 2
  },
  "timestamp": "2025-11-09T12:00:00Z"
}
```

#### 3. 通知消息
```json
{
  "type": "notification",
  "notification": {
    "id": "notif_1731144000000_1",
    "type": "backtest_completed",
    "title": "回测完成",
    "message": "回测任务 backtest_001 已完成",
    "priority": "HIGH",
    "timestamp": "2025-11-09T12:00:00Z",
    "metadata": {
      "task_id": "backtest_001",
      "result_summary": {
        "total_return": 15.67,
        "sharpe_ratio": 1.23,
        "trades_count": 48
      }
    },
    "action_url": "/backtest/result/backtest_001",
    "action_text": "查看结果"
  },
  "timestamp": "2025-11-09T12:00:00Z"
}
```

#### 4. 系统状态更新
```json
{
  "type": "system_status_update",
  "status": {
    "active_connections": 5,
    "cpu_usage": 45.2,
    "memory_usage": 1024.5,
    "active_backtests": 2
  },
  "timestamp": "2025-11-09T12:00:00Z"
}
```

## 使用示例

### Python客户端示例

```python
import asyncio
import websockets
import json

async def main():
    uri = "ws://localhost:8001/api/v1/websocket/ws"

    async with websockets.connect(uri) as websocket:
        # 1. 订阅回测进度
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "backtest_progress"
        }))

        # 2. 订阅通知
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "notifications"
        }))

        # 3. 订阅图表数据
        await websocket.send(json.dumps({
            "type": "subscribe_chart",
            "symbol": "0700.HK"
        }))

        # 4. 接收消息
        async for message in websocket:
            data = json.loads(message)
            print(f"收到: {data['type']}")

            # 处理不同类型的消息
            if data['type'] == 'backtest_progress_update':
                print(f"进度: {data['data']['progress']}%")

            elif data['type'] == 'chart_update':
                print(f"图表数据: {data['symbol']}")

            elif data['type'] == 'notification':
                print(f"通知: {data['notification']['title']}")

asyncio.run(main())
```

### JavaScript客户端示例

```javascript
const ws = new WebSocket('ws://localhost:8001/api/v1/websocket/ws');

ws.onopen = function() {
    console.log('WebSocket已连接');

    // 订阅频道
    ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'backtest_progress'
    }));

    ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'notifications'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'backtest_progress_update':
            console.log(`进度: ${data.data.progress}%`);
            break;

        case 'chart_update':
            console.log(`图表数据: ${data.symbol}`);
            break;

        case 'notification':
            console.log(`通知: ${data.notification.title}`);
            break;
    }
};

ws.onerror = function(error) {
    console.error('WebSocket错误:', error);
};

ws.onclose = function() {
    console.log('WebSocket已关闭');
};
```

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 连接建立 | < 100ms | 从连接到收到欢迎消息的时间 |
| 消息延迟 | < 50ms | 从发送到接收的延迟 |
| 并发连接 | 100+ | 最大并发WebSocket连接数 |
| 消息吞吐量 | 1000 msg/s | 每秒处理的消息数 |
| 内存使用 | < 100MB | WebSocket模块内存占用 |

## 性能优化

### 1. 连接池管理
- 限制最大连接数 (默认1000)
- 自动清理过期连接
- 连接复用机制

### 2. 消息队列
- 批量消息发送
- 消息压缩 (MessagePack支持)
- 优先级队列

### 3. 心跳检测
- 自动检测断线
- 自动重连机制
- Ping/Pong响应

### 4. 数据结构优化
- 使用deque存储数据点
- 限制数据历史数量
- 定期清理旧数据

## 错误处理

### 连接错误
- 自动重连 (最多5次)
- 指数退避策略
- 错误日志记录

### 消息错误
- JSON解析错误处理
- 无效消息过滤
- 消息确认机制

### 超时处理
- 30秒连接超时
- 5秒消息超时
- 90秒空闲超时

## 监控和调试

### 查看连接状态
```bash
curl http://localhost:8001/api/v1/websocket/status
```

### 广播测试消息
```bash
curl -X POST http://localhost:8001/api/v1/websocket/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "notifications",
    "message": {
      "type": "test",
      "title": "测试通知"
    }
  }'
```

### 运行测试
```bash
python test_websocket_phase4.py
```

## 部署注意事项

### 1. 端口配置
- 默认WebSocket端口: 8001
- 确保防火墙允许WebSocket连接
- 配置反向代理支持WebSocket

### 2. 负载均衡
- 使用粘性会话 (sticky session)
- 配置WebSocket超时
- 设置最大连接数

### 3. 资源限制
- 限制每个IP的连接数
- 设置内存使用上限
- 监控连接数趋势

## 故障排除

### 问题1: 连接被拒绝
**原因**: 服务器未启动或端口被占用
**解决**:
```bash
# 检查服务是否运行
netstat -tulpn | grep 8001

# 启动服务器
python -m src.api.server
```

### 问题2: 消息接收不到
**原因**: 未正确订阅频道
**解决**:
```javascript
// 确保先发送订阅消息
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'backtest_progress'
}));

// 等待订阅确认
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'subscription_confirmed') {
        console.log('订阅成功');
    }
};
```

### 问题3: 内存占用过高
**原因**: 大量数据点未清理
**解决**:
```python
# 调整数据点数量限制
chart_manager = ChartDataManager(max_data_points=5000)

# 定期清理
await chart_manager.remove_symbol('OLD_SYMBOL')
```

## 未来增强

### 1. 消息压缩
- 集成MessagePack
- GZIP压缩
- 减少带宽使用

### 2. 消息持久化
- Redis存储
- 消息历史
- 离线消息

### 3. 权限控制
- 用户认证
- 频道权限
- 消息过滤

### 4. 集群支持
- Redis Pub/Sub
- 消息路由
- 负载均衡

## 总结

Phase 4的WebSocket实时更新系统已成功实现，提供了完整的实时数据推送功能。系统具备高性能、高可靠性和可扩展性，能够满足港股量化交易系统的实时性要求。

**主要特性**:
- ✅ 实时连接管理
- ✅ 进度跟踪推送
- ✅ 图表数据更新
- ✅ 通知消息系统
- ✅ 性能监控
- ✅ 错误处理
- ✅ 自动重连
- ✅ 客户端示例

**测试覆盖**:
- ✅ 连接建立
- ✅ 消息收发
- ✅ 频道订阅
- ✅ 进度更新
- ✅ 图表推送
- ✅ 通知系统
- ✅ 错误处理
- ✅ 状态查询

系统已准备就绪，可用于生产环境部署。
