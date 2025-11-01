# 📚 Dashboard API - 快速参考指南

## 🚀 快速启动

### 启动仪表板

```bash
# 启动仪表板服务
python run_dashboard.py

# 后台运行
nohup python run_dashboard.py > dashboard.log 2>&1 &

# 检查日志
tail -f dashboard.log
```

### 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 主界面 | http://localhost:8001 | 仪表板主页 |
| API 文档 | http://localhost:8001/docs | Swagger UI |
| 健康检查 | http://localhost:8001/api/health | 系统健康状态 |
| ReDoc | http://localhost:8001/redoc | 替代 API 文档 |

---

## 📡 REST API 端点

### 1. 健康检查

```http
GET /api/health
GET /health
```

**响应示例**:
```json
{
  "status": "ok",
  "service": "dashboard",
  "timestamp": "2025-10-28T21:25:00",
  "version": "1.0.0"
}
```

### 2. 投资组合数据

```http
GET /api/trading/portfolio
```

**响应示例**:
```json
{
  "initial_capital": 1000000.0,
  "portfolio_value": 1050000.0,
  "active_positions": 3,
  "total_return": 50000.0,
  "total_return_pct": 5.0,
  "currency": "USD",
  "last_update": "2025-10-28T21:25:00",
  "positions": [
    {
      "symbol": "0700.HK",
      "quantity": 100,
      "entry_price": 350.0,
      "current_price": 365.0,
      "pnl": 1500.0,
      "pnl_pct": 4.3
    }
  ]
}
```

### 3. 性能指标

```http
GET /api/trading/performance
```

**响应示例**:
```json
{
  "total_return_pct": 5.0,
  "annualized_return": 15.2,
  "volatility": 12.5,
  "sharpe_ratio": 1.2,
  "sortino_ratio": 1.8,
  "max_drawdown": -8.3,
  "win_rate": 0.65,
  "profit_factor": 1.45,
  "total_trades": 125,
  "winning_trades": 82,
  "losing_trades": 43,
  "average_win": 150.0,
  "average_loss": 95.0,
  "last_update": "2025-10-28T21:25:00"
}
```

### 4. 系统状态

```http
GET /api/system/status
```

**响应示例**:
```json
{
  "status": "operational",
  "agents": {
    "total": 7,
    "active": 7,
    "inactive": 0
  },
  "uptime_seconds": 3600,
  "uptime_formatted": "1h 0m",
  "resources": {
    "memory_usage_mb": 256,
    "memory_available_mb": 8192,
    "cpu_usage_pct": 15.5,
    "disk_usage_pct": 45.2
  },
  "performance": {
    "active_trades": 3,
    "pending_orders": 2,
    "last_trade_timestamp": "2025-10-28T08:25:30Z"
  },
  "last_update": "2025-10-28T21:25:00"
}
```

### 5. 系统刷新

```http
POST /api/system/refresh
Content-Type: application/json

{
  "hard_refresh": false
}
```

**响应示例**:
```json
{
  "status": "success",
  "refresh_type": "soft",
  "timestamp": "2025-10-28T21:25:00",
  "affected_systems": [
    "portfolio",
    "performance",
    "agent_status"
  ]
}
```

### 6. 股票数据 (HKEX)

```http
GET /api/stock/data?symbol=0700.HK&duration=365
```

**参数**:
- `symbol` (必需): 股票代码，如 0700.HK
- `duration` (可选): 时间范围（天数），默认 365

**响应示例**:
```json
{
  "symbol": "0700.HK",
  "name": "Tencent (騰訊)",
  "last_price": 325.50,
  "change": 2.50,
  "change_percent": 0.77,
  "high": 328.00,
  "low": 321.00,
  "volume": 45230000,
  "market_cap": "3.2T",
  "timestamp": "2025-10-28T21:25:00",
  "data_source": "Real-time HKEX API"
}
```

**错误响应 (503 Service Unavailable)**:
```json
{
  "error": "DATA_SOURCE_ERROR",
  "message": "無法從 HKEX 數據源獲取 0700.HK 的數據",
  "symbol": "0700.HK",
  "timestamp": "2025-10-28T21:25:00",
  "data_source": "HKEX API",
  "error_details": "Connection timeout",
  "note": "請檢查 HKEX 數據源連接或稍後重試"
}
```

**重要说明**:
- 此端点专门连接 HKEX 数据源
- **不会回退到 Mock 数据**
- 如果数据源不可用，将返回明确的错误信息
- HKEX 和 gov_crawler 是独立的数据项目

### 7. gov_crawler 政府数据

```http
GET /api/gov/data?indicator=hibor_overnight&start_date=2024-01-01&end_date=2025-10-28
```

**参数**:
- `indicator` (必需): 指标类型，如 "hibor_overnight"
- `start_date` (可选): 开始日期 (YYYY-MM-DD)，默认 "2024-01-01"
- `end_date` (可选): 结束日期 (YYYY-MM-DD)，默认 "2025-10-28"

**响应示例**:
```json
{
  "indicator": "hibor_overnight",
  "data": {
    "value": 3.85,
    "date": "2025-10-28",
    "source": "HKMA"
  },
  "source": "gov_crawler",
  "timestamp": "2025-10-28T21:25:00",
  "start_date": "2024-01-01",
  "end_date": "2025-10-28",
  "note": "數據來自 gov_crawler 政府數據收集系統"
}
```

### 8. gov_crawler 指标列表

```http
GET /api/gov/indicators
```

**响应示例**:
```json
{
  "total_indicators": 35,
  "indicators": [
    "hibor_overnight",
    "hibor_1m",
    "property_price",
    "gdp",
    ...
  ],
  "data_source": "gov_crawler",
  "last_update": "2025-10-28T21:25:00",
  "note": "數據來自 gov_crawler 政府數據收集系統"
}
```

### 9. gov_crawler 系统状态

```http
GET /api/gov/status
```

**响应示例**:
```json
{
  "project": "gov_crawler",
  "status": "operational",
  "data_source": "gov_crawler",
  "timestamp": "2025-10-28T21:25:00",
  "checks": {
    "project_directory": "✅ 存在",
    "data_file": "✅ 存在"
  },
  "project_found": true,
  "data_file_size": "125.67 KB",
  "data_file_mtime": "2025-10-23T21:04:19",
  "data_available": true,
  "total_indicators": 35
}
```

**数据源区分**:
- **HKEX 数据源**: `/api/stock/data` (股票数据)
- **gov_crawler 数据源**: `/api/gov/data` (政府数据)

---

## 🔌 WebSocket 端点

### 连接 WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/system');
```

### WebSocket 端点列表

| 端点 | 用途 | 事件 |
|------|------|------|
| `/ws/portfolio` | 投资组合实时更新 | 头寸更新、净值变化 |
| `/ws/orders` | 订单实时推送 | 订单状态、成交通知 |
| `/ws/risk` | 风险告警推送 | 新告警、风险指标 |
| `/ws/system` | 系统监控数据 | CPU/内存、Agent 状态 |

### WebSocket 消息格式

**订阅请求**:
```json
{
  "action": "subscribe",
  "topic": "system_status"
}
```

**心跳**:
```json
{
  "action": "ping"
}
```

**取消订阅**:
```json
{
  "action": "unsubscribe",
  "topic": "system_status"
}
```

---

## 💻 代码示例

### JavaScript / 前端

#### 获取投资组合数据

```javascript
async function fetchPortfolio() {
    try {
        const response = await fetch('/api/trading/portfolio');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        console.log('投资组合价值:', data.portfolio_value);
        console.log('活跃仓位:', data.active_positions);
        console.log('总收益:', data.total_return_pct + '%');
        return data;
    } catch (error) {
        console.error('获取投资组合失败:', error);
    }
}
```

#### 获取系统状态

```javascript
async function fetchSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        console.log('系统状态:', data.status);
        console.log('Agent 状态:', `${data.agents.active}/${data.agents.total}`);
        console.log('运行时间:', data.uptime_formatted);
        return data;
    } catch (error) {
        console.error('获取系统状态失败:', error);
    }
}
```

#### 刷新系统

```javascript
async function refreshSystem(hardRefresh = false) {
    try {
        const response = await fetch('/api/system/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({hard_refresh: hardRefresh})
        });
        const data = await response.json();
        console.log('刷新结果:', data.status);
        console.log('刷新类型:', data.refresh_type);
        return data;
    } catch (error) {
        console.error('刷新系统失败:', error);
    }
}
```

#### 获取 gov_crawler 系统状态

```javascript
async function fetchGovCrawlerStatus() {
    try {
        const response = await fetch('/api/gov/status');
        const data = await response.json();
        console.log('gov_crawler 状态:', data.status);
        console.log('可用指标数:', data.total_indicators);
        console.log('项目存在:', data.project_found);
        return data;
    } catch (error) {
        console.error('获取 gov_crawler 状态失败:', error);
    }
}
```

#### 获取 gov_crawler 指标列表

```javascript
async function fetchGovIndicators() {
    try {
        const response = await fetch('/api/gov/indicators');
        const data = await response.json();
        console.log('可用指标:', data.indicators);
        console.log('指标总数:', data.total_indicators);
        return data.indicators;
    } catch (error) {
        console.error('获取指标列表失败:', error);
    }
}
```

#### 获取 gov_crawler 数据

```javascript
async function fetchGovData(indicator = 'hibor_overnight') {
    try {
        const response = await fetch(`/api/gov/data?indicator=${indicator}`);
        if (response.ok) {
            const data = await response.json();
            console.log(`${indicator} 数据:`, data);
            return data;
        } else {
            console.error(`获取 ${indicator} 数据失败:`, response.status);
            const error = await response.json();
            console.error('错误信息:', error.detail);
        }
    } catch (error) {
        console.error('获取 gov 数据失败:', error);
    }
}
```

#### WebSocket 连接示例

```javascript
// 连接到系统状态 WebSocket
const ws = new WebSocket('ws://localhost:8001/ws/system');

ws.onopen = function() {
    console.log('WebSocket 已连接');
    // 订阅系统状态
    ws.send(JSON.stringify({
        action: 'subscribe',
        topic: 'system_status'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
    // 处理实时更新
    if (data.type === 'agent_status') {
        updateAgentStatus(data.agents);
    }
};

ws.onerror = function(error) {
    console.error('WebSocket 错误:', error);
};

ws.onclose = function() {
    console.log('WebSocket 已断开');
};
```

---

### Python / 后端

#### 使用 httpx (推荐)

```python
import asyncio
import httpx
from typing import Dict, Any

class DashboardClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url

    async def get_health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()

    async def get_portfolio(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/trading/portfolio")
            response.raise_for_status()
            return response.json()

    async def get_system_status(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/system/status")
            response.raise_for_status()
            return response.json()

    async def refresh_system(self, hard_refresh: bool = False) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/system/refresh",
                json={"hard_refresh": hard_refresh}
            )
            response.raise_for_status()
            return response.json()

# 使用示例
async def main():
    client = DashboardClient()

    # 获取系统状态
    health = await client.get_health()
    print(f"系统状态: {health['status']}")

    # 获取投资组合
    portfolio = await client.get_portfolio()
    print(f"投资组合价值: ${portfolio['portfolio_value']:,.2f}")

    # 刷新系统
    result = await client.refresh_system(hard_refresh=False)
    print(f"刷新结果: {result['status']}")

asyncio.run(main())
```

#### 使用 requests (同步版本)

```python
import requests
from typing import Dict, Any

class DashboardClientSync:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url

    def get_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

    def get_portfolio(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/api/trading/portfolio")
        response.raise_for_status()
        return response.json()

# 使用示例
client = DashboardClientSync()
health = client.get_health()
print(f"系统状态: {health['status']}")
```

---

### curl 命令

#### 健康检查

```bash
curl -X GET http://localhost:8001/api/health \
  -H "Accept: application/json"
```

#### 获取投资组合

```bash
curl -X GET http://localhost:8001/api/trading/portfolio \
  -H "Accept: application/json"
```

#### 刷新系统

```bash
curl -X POST http://localhost:8001/api/system/refresh \
  -H "Content-Type: application/json" \
  -d '{"hard_refresh": true}'
```

#### 获取股票数据

```bash
curl -X GET "http://localhost:8001/api/stock/data?symbol=0700.HK&duration=365" \
  -H "Accept: application/json"
```

#### 获取 gov_crawler 系统状态

```bash
curl -X GET http://localhost:8001/api/gov/status \
  -H "Accept: application/json"
```

#### 获取 gov_crawler 指标列表

```bash
curl -X GET http://localhost:8001/api/gov/indicators \
  -H "Accept: application/json"
```

#### 获取 gov_crawler 数据

```bash
curl -X GET "http://localhost:8001/api/gov/data?indicator=hibor_overnight" \
  -H "Accept: application/json"
```

---

## 🧪 测试 API

### 运行自动化测试

```bash
# 安装测试依赖
pip install httpx websockets

# 运行测试脚本
python test_dashboard_api.py
```

### 手动测试

```bash
# 测试所有端点
curl -s http://localhost:8001/api/health | jq .
curl -s http://localhost:8001/api/trading/portfolio | jq .
curl -s http://localhost:8001/api/trading/performance | jq .
curl -s http://localhost:8001/api/system/status | jq .

# 测试系统刷新
curl -X POST http://localhost:8001/api/system/refresh \
  -H "Content-Type: application/json" \
  -d '{"hard_refresh": false}' | jq .

# 测试 gov_crawler 端点
curl -s http://localhost:8001/api/gov/status | jq .
curl -s http://localhost:8001/api/gov/indicators | jq .
curl -s "http://localhost:8001/api/gov/data?indicator=hibor_overnight" | jq .
```

---

## ⚠️ 错误处理

### 常见错误码

| 状态码 | 说明 | 解决方法 |
|--------|------|----------|
| 200 | 成功 | - |
| 404 | 端点不存在 | 检查 URL 是否正确 |
| 500 | 服务器内部错误 | 查看服务器日志 |
| 503 | 服务不可用 | 服务可能正在启动 |

### 错误响应格式

```json
{
  "error": "错误描述",
  "status_code": 500,
  "timestamp": "2025-10-28T21:25:00"
}
```

### 重试机制

```python
import asyncio
import httpx

async def fetch_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

---

## 📊 性能监控

### API 响应时间

```python
import time
import httpx

async def measure_response_time(url: str):
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    elapsed = time.time() - start_time
    print(f"响应时间: {elapsed:.3f}s")
    return elapsed
```

### 监控 WebSocket 连接数

```javascript
// 获取 WebSocket 状态
fetch('http://localhost:8001/ws/status')
  .then(response => response.json())
  .then(data => {
    console.log('活跃连接数:', data.active_connections);
  });
```

---

## 🔐 安全注意事项

### 生产环境建议

1. **启用 HTTPS**
   ```python
   # 使用 TLS 证书
   uvicorn.run(
       app,
       host="0.0.0.0",
       port=8443,
       ssl_keyfile="key.pem",
       ssl_certfile="cert.pem"
   )
   ```

2. **添加认证**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   async def verify_token(token: str = Depends(security)):
       # 验证 JWT token
       if not validate_token(token.credentials):
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="无效的认证凭据"
           )
       return token
   ```

3. **限制请求率**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

   @app.get("/api/health")
   @limiter.limit("10/minute")
   async def health(request: Request):
       return {"status": "ok"}
   ```

4. **CORS 配置**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # 指定域名
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["Authorization", "Content-Type"],
   )
   ```

---

## 📞 支持与反馈

### 获取帮助

- **API 文档**: http://localhost:8001/docs
- **日志文件**: 查看 `dashboard.log`
- **测试脚本**: `python test_dashboard_api.py`

### 报告问题

如遇到问题，请提供：
1. 错误信息
2. 请求 URL
3. 响应内容
4. 服务器日志

---

## 📝 更新日志

### v1.0.0 (2025-10-28)
- ✅ 实现 5 个核心 API 端点
- ✅ 添加 WebSocket 实时推送
- ✅ 配置静态文件服务
- ✅ 集成真实股票数据 API
- ✅ 修复 asyncio 事件循环冲突
- ✅ 添加完整的错误处理和日志

---

**最后更新**: 2025-10-28 21:25:00
**API 版本**: 1.0.0
**状态**: ✅ 稳定版本

