# Dashboard REST API Endpoints - Specification

**Spec ID**: api-endpoints
**Change ID**: fix-dashboard-api-endpoints
**Version**: 1.0
**Status**: PROPOSED
**Created**: 2025-10-26

## Overview

本規範定義儀表板應實現的所有 REST API 端點，確保前端 JavaScript 可成功調用這些 API 獲取數據。

---

## ADDED Requirements

### Requirement 1: GET /api/health - 系統健康檢查

**描述**: 檢查系統整體健康狀態

#### Specification:
```
Method: GET
Endpoint: /api/health
Alternative: GET /health
Authentication: Not required
Rate Limit: None
```

#### Request Parameters:
無

#### Response Format (200 OK):
```json
{
  "status": "ok",
  "service": "dashboard",
  "timestamp": "2025-10-26T08:30:45Z",
  "version": "1.0.0"
}
```

#### Response Format (503 Service Unavailable):
```json
{
  "status": "error",
  "error_code": "SERVICE_DEGRADED",
  "message": "System is in degraded state",
  "timestamp": "2025-10-26T08:30:45Z"
}
```

#### Status Codes:
- `200 OK`: 系統正常
- `503 Service Unavailable`: 系統降級

#### Scenario: 系統啟動後調用健康檢查

```
Given: 儀表板服務已啟動
When: 客戶端調用 GET /api/health
Then: 返回 200 OK
And: 響應包含 status="ok"
And: 響應包含有效的 timestamp
```

#### Scenario: 系統故障時調用健康檢查

```
Given: 系統因某個原因進入降級狀態
When: 客戶端調用 GET /api/health
Then: 返回 503 Service Unavailable
And: 響應包含 error_code
And: 響應包含錯誤信息
```

---

### Requirement 2: GET /api/trading/portfolio - 投資組合數據

**描述**: 獲取當前投資組合的狀態和統計信息

#### Specification:
```
Method: GET
Endpoint: /api/trading/portfolio
Authentication: Not required
Caching: 可緩存 30 秒
```

#### Request Parameters:
無

#### Response Format (200 OK):
```json
{
  "initial_capital": 1000000.0,
  "portfolio_value": 1050000.0,
  "active_positions": 3,
  "total_return": 50000.0,
  "total_return_pct": 5.0,
  "currency": "USD",
  "last_update": "2025-10-26T08:30:45Z",
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

#### Field Descriptions:
| 字段 | 類型 | 說明 |
|------|------|------|
| initial_capital | float | 初始資本 |
| portfolio_value | float | 當前投資組合總值 |
| active_positions | int | 活躍倉位數量 |
| total_return | float | 總收益（絕對值） |
| total_return_pct | float | 總收益率（百分比） |
| currency | string | 貨幣單位 |
| last_update | string | 最後更新時間 (ISO 8601) |
| positions | array | 倉位清單 |

#### Status Codes:
- `200 OK`: 成功獲取投資組合數據
- `500 Internal Server Error`: 無法檢索投資組合數據

#### Scenario: 獲取投資組合數據

```
Given: 投資組合已初始化
When: 客戶端調用 GET /api/trading/portfolio
Then: 返回 200 OK
And: 響應包含 portfolio_value > 0
And: 響應包含 initial_capital
And: 響應包含 last_update 時間戳
```

#### Scenario: 無活躍倉位

```
Given: 投資組合已初始化但無倉位
When: 客戶端調用 GET /api/trading/portfolio
Then: 返回 200 OK
And: active_positions = 0
And: positions = []
```

---

### Requirement 3: GET /api/trading/performance - 性能指標

**描述**: 獲取策略和投資組合的性能指標

#### Specification:
```
Method: GET
Endpoint: /api/trading/performance
Authentication: Not required
Caching: 可緩存 60 秒
```

#### Request Parameters:
無

#### Response Format (200 OK):
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
  "last_update": "2025-10-26T08:30:45Z"
}
```

#### Field Descriptions:
| 字段 | 類型 | 說明 |
|------|------|------|
| total_return_pct | float | 總收益率 (%) |
| annualized_return | float | 年化收益率 (%) |
| volatility | float | 年化波動率 (%) |
| sharpe_ratio | float | 夏普比率 |
| sortino_ratio | float | 索提諾比率 |
| max_drawdown | float | 最大回撤 (%) |
| win_rate | float | 勝率 (0-1) |
| profit_factor | float | 利潤因子 |
| total_trades | int | 總交易次數 |
| winning_trades | int | 勝利交易次數 |
| losing_trades | int | 虧損交易次數 |
| average_win | float | 平均贏利 |
| average_loss | float | 平均虧損 |
| last_update | string | 最後更新時間 |

#### Status Codes:
- `200 OK`: 成功獲取性能指標
- `500 Internal Server Error`: 無法計算性能指標

#### Scenario: 獲取完整的性能指標

```
Given: 策略已執行至少 10 筆交易
When: 客戶端調用 GET /api/trading/performance
Then: 返回 200 OK
And: 響應包含 sharpe_ratio
And: 響應包含 max_drawdown
And: 響應包含 win_rate
```

#### Scenario: 無交易時的性能指標

```
Given: 投資組合初始化但無交易記錄
When: 客戶端調用 GET /api/trading/performance
Then: 返回 200 OK
And: total_return_pct = 0.0
And: total_trades = 0
```

---

### Requirement 4: GET /api/system/status - 系統狀態

**描述**: 獲取整體系統狀態和資源使用情況

#### Specification:
```
Method: GET
Endpoint: /api/system/status
Authentication: Not required
Caching: 可緩存 10 秒
```

#### Request Parameters:
無

#### Response Format (200 OK):
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
    "cpu_usage_pct": 25.5,
    "disk_usage_pct": 45.2
  },
  "performance": {
    "active_trades": 3,
    "pending_orders": 2,
    "last_trade_timestamp": "2025-10-26T08:25:30Z"
  },
  "last_update": "2025-10-26T08:30:45Z"
}
```

#### Status Values:
- `"operational"`: 系統正常運行
- `"degraded"`: 系統降級但功能部分可用
- `"offline"`: 系統離線

#### Status Codes:
- `200 OK`: 成功獲取系統狀態
- `503 Service Unavailable`: 系統離線

#### Scenario: 系統正常運行

```
Given: 所有 7 個 Agent 都在運行
When: 客戶端調用 GET /api/system/status
Then: 返回 200 OK
And: status = "operational"
And: agents.active = 7
And: uptime_seconds > 0
```

#### Scenario: 系統降級

```
Given: 部分 Agent 無法連接或故障
When: 客戶端調用 GET /api/system/status
Then: 返回 200 OK (或 503 Unavailable)
And: status = "degraded"
And: agents.inactive > 0
```

---

### Requirement 5: POST /api/system/refresh - 系統刷新

**描述**: 刷新系統狀態和所有緩存的數據

#### Specification:
```
Method: POST
Endpoint: /api/system/refresh
Authentication: Not required (可選)
Rate Limit: 每 5 秒一次
```

#### Request Body:
```json
{
  "hard_refresh": false
}
```

| 參數 | 類型 | 說明 |
|------|------|------|
| hard_refresh | boolean | 是否執行硬刷新（清除所有緩存） |

#### Response Format (200 OK):
```json
{
  "status": "success",
  "refresh_type": "soft",
  "timestamp": "2025-10-26T08:30:45Z",
  "affected_systems": [
    "portfolio",
    "performance",
    "agent_status"
  ]
}
```

#### Status Codes:
- `200 OK`: 刷新成功
- `429 Too Many Requests`: 刷新請求過於頻繁
- `500 Internal Server Error`: 刷新失敗

#### Scenario: 軟刷新

```
Given: 系統正在運行
When: 客戶端調用 POST /api/system/refresh { "hard_refresh": false }
Then: 返回 200 OK
And: 更新最近的數據
And: 保留長期緩存
```

---

## MODIFIED Requirements

### None
不修改現有的任何 API 端點。

---

## REMOVED Requirements

### None
不移除任何現有的 API 功能。

---

## Cross-References

相關規範：
- [startup-handler spec](../startup-handler/spec.md) - 應用啟動和事件循環管理
- [openspec/specs/strategy-backtest/spec.md](../../../../specs/strategy-backtest/spec.md) - 回測結果集成

---

## Validation Checklist

實現時應驗證：
- [ ] 所有端點返回正確的 HTTP 狀態碼
- [ ] 所有響應符合 JSON Schema
- [ ] 所有字段都有值（不存在 null）
- [ ] 時間戳都是 ISO 8601 格式
- [ ] 浮點數精度適當（2-4 位小數）
- [ ] 錯誤響應包含 error_code
- [ ] 支持 CORS (如果需要)
- [ ] 響應時間 < 100ms
- [ ] 所有端點都有日誌記錄

---

## Testing Requirements

- [ ] 單元測試: 每個端點至少 2 個場景
- [ ] 集成測試: 端到端工作流
- [ ] 性能測試: 響應時間驗證
- [ ] 錯誤處理測試: 異常情況
- [ ] 測試覆蓋率 >= 80%

