# Dashboard API Endpoints Fix - Design Document

**Change ID**: fix-dashboard-api-endpoints
**Last Updated**: 2025-10-26

## 架構設計

### 問題分析

#### 問題 1: asyncio 事件循環衝突

**當前代碼** (run_dashboard.py):
```python
async def main():
    dashboard_ui = DashboardUI(...)
    await dashboard_ui.start()

    uvicorn.run(app, ...)  # ❌ 在 async 上下文中調用

if __name__ == "__main__":
    asyncio.run(main())  # ❌ 試圖創建新事件循環
```

**問題**:
- `asyncio.run()` 試圖創建一個新事件循環
- `uvicorn.run()` 也會創建事件循環
- 兩者衝突導致崩潰

**解決方案**:
使用 `uvicorn.Server` 的低階 API，在已有事件循環中運行

```python
import asyncio
import uvicorn

async def main():
    app = create_app()

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

---

#### 問題 2: 缺失的 API 端點

**HTML 期望的端點** (從 index.html 的 JavaScript):
```javascript
fetch('/api/health')
fetch('/api/trading/portfolio')
fetch('/api/trading/performance')
fetch('/health')
```

**當前實現**:
```python
@app.get('/')                    # ✅ 實現
@app.get('/api/health')          # ❌ 缺失
@app.get('/api/trading/portfolio') # ❌ 缺失
@app.get('/api/trading/performance') # ❌ 缺失
```

**解決方案**:
實現所有必要的 API 端點，返回 Mock 數據或真實數據

---

#### 問題 3: 系統狀態顯示不正確

**當前**:
- HTML 中硬編碼 `DEGRADED` 狀態
- 或無法從 API 獲取正確狀態

**解決方案**:
實現 `/api/health` 端點，返回正確的系統狀態

---

### 解決方案設計

#### 層次架構

```
┌─────────────────────────────────────────┐
│         HTML + JavaScript               │
│      (src/dashboard/templates/)         │
└──────────────┬──────────────────────────┘
               │ HTTP Requests
               ▼
┌─────────────────────────────────────────┐
│      FastAPI Application                │
│   (run_dashboard.py / app.py)          │
├─────────────────────────────────────────┤
│  Route Layer (API Endpoints)            │
│  - GET /                                │
│  - GET /api/health                      │
│  - GET /api/trading/portfolio           │
│  - GET /api/trading/performance         │
│  - POST /api/system/refresh             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Data Service Layer                   │
│  - DashboardAPI                         │
│  - PerformanceService                   │
│  - AgentDataService                     │
└─────────────────────────────────────────┘
```

#### API 端點設計

##### 1. 健康檢查端點

```
GET /api/health
GET /health (別名)

Response 200:
{
    "status": "ok",
    "service": "dashboard",
    "timestamp": "2025-10-26T08:00:00Z",
    "version": "1.0.0"
}
```

##### 2. 投資組合端點

```
GET /api/trading/portfolio

Response 200:
{
    "initial_capital": 1000000.0,
    "portfolio_value": 1000000.0,
    "active_positions": 0,
    "total_return": 0.0,
    "currency": "USD",
    "last_update": "2025-10-26T08:00:00Z"
}
```

##### 3. 性能端點

```
GET /api/trading/performance

Response 200:
{
    "total_return_pct": 0.0,
    "annualized_return": 0.0,
    "sharpe_ratio": 0.0,
    "max_drawdown": 0.0,
    "win_rate": 0.0,
    "total_trades": 0,
    "last_update": "2025-10-26T08:00:00Z"
}
```

##### 4. 系統狀態端點

```
GET /api/system/status

Response 200:
{
    "status": "operational",  # operational, degraded, offline
    "agents_count": 7,
    "active_agents": 7,
    "uptime_seconds": 3600,
    "memory_usage_mb": 256,
    "cpu_usage_pct": 25.5,
    "last_update": "2025-10-26T08:00:00Z"
}
```

---

### 實現方案

#### Phase 1: 修復啟動流程

**文件**: `run_dashboard.py` (重寫)

```python
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

def create_app():
    """Create and configure FastAPI application"""
    app = FastAPI(title="CODEX Trading Dashboard")

    # Routes
    @app.get('/', response_class=HTMLResponse)
    async def root():
        with open('src/dashboard/templates/index.html', 'r') as f:
            return f.read()

    @app.get('/api/health')
    async def health():
        return {
            "status": "ok",
            "service": "dashboard",
            "timestamp": datetime.now().isoformat()
        }

    # ... 其他端點

    return app

async def main():
    app = create_app()

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Phase 2: 實現 API 層

為每個端點創建處理器，可初期使用 Mock 數據

**文件**: `src/dashboard/api_handlers.py` (新建)

```python
from datetime import datetime
from typing import Dict, Any

class DashboardAPIHandlers:
    """API endpoint handlers for dashboard"""

    @staticmethod
    async def get_health() -> Dict[str, Any]:
        """System health check"""
        return {
            "status": "ok",
            "service": "dashboard",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    @staticmethod
    async def get_portfolio() -> Dict[str, Any]:
        """Get portfolio data"""
        return {
            "initial_capital": 1000000.0,
            "portfolio_value": 1000000.0,
            "active_positions": 0,
            "total_return": 0.0,
            "currency": "USD",
            "last_update": datetime.now().isoformat()
        }

    # ... 其他處理器
```

#### Phase 3: 集成現有服務

將已有的 `DashboardAPI`、`PerformanceService` 等集成到新的啟動流程中

---

### 相依關係

```
run_dashboard.py
  ├─ src/dashboard/templates/index.html
  ├─ src/dashboard/api_handlers.py (新建)
  ├─ src/dashboard/api_routes.py (已有)
  ├─ src/dashboard/dashboard_ui.py (已有)
  └─ FastAPI + uvicorn
```

---

### 測試策略

#### 單元測試
- 測試每個 API 端點
- 驗證響應格式和狀態碼
- 檢查 Mock 數據的完整性

#### 集成測試
- 從前端 JavaScript 角度模擬 API 調用
- 驗證頁面是否正常顯示數據
- 測試頁面刷新流程

#### 性能測試
- 響應時間 < 100ms
- 內存使用穩定
- 無內存洩漏

---

### 向後相容性

所有修改都是**添加性**的，不會破壞現有功能：
- 新增 API 端點
- 修復啟動流程
- 保留所有既有的 DashboardAPI 類

---

### 監控和日誌

添加詳細的日誌記錄：

```python
logger.info(f"啟動儀表板服務... (端口 {port})")
logger.info(f"API 端點已註冊: {len(routes)} 條路由")
logger.debug(f"API 調用: {method} {path}")
logger.error(f"API 錯誤: {path} - {error}")
```

---

### 預期成果

修復完成後：
- ✅ 頁面無 404 錯誤
- ✅ 所有 API 端點可訪問
- ✅ 系統狀態正確顯示
- ✅ 儀表板數據正常顯示
- ✅ 無持續刷新迴圈

