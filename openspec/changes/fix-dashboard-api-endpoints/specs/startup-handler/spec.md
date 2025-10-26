# Dashboard Startup Handler - Specification

**Spec ID**: startup-handler
**Change ID**: fix-dashboard-api-endpoints
**Version**: 1.0
**Status**: PROPOSED
**Created**: 2025-10-26

## Overview

本規範定義儀表板應用的啟動流程，特別是解決 asyncio 事件循環衝突問題。

---

## ADDED Requirements

### Requirement 1: 正確的 Event Loop 管理

**描述**: FastAPI 應用應在單一事件循環中正確啟動，無任何衝突

#### Specification:

啟動流程應遵循以下步驟：

```python
1. 創建 FastAPI 應用實例
2. 配置所有路由和中間件
3. 創建 uvicorn.Config 對象
4. 創建 uvicorn.Server 實例
5. 在 asyncio 事件循環中運行 server.serve()
```

#### Requirements:

- 不能使用 `asyncio.run(uvicorn.run())` 的組合（會導致雙重事件循環創建）
- 必須使用 `uvicorn.Server` 的低階 API
- 必須支持 Ctrl+C 優雅關閉
- 必須正確清理資源

#### Scenario: 正常啟動流程

```
Given: 系統未運行
When: 執行 python run_dashboard.py
Then: 應無任何 RuntimeError 異常
And: 日誌顯示 "Server running on http://0.0.0.0:8001"
And: 服務監聽 8001 端口
```

#### Scenario: 接收 SIGINT 信號

```
Given: 服務正在運行
When: 用戶按 Ctrl+C
Then: 應捕獲 KeyboardInterrupt
And: 日誌顯示清理消息
And: 進程優雅退出
```

#### Implementation Example:

```python
import asyncio
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Dashboard")

async def main():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Cleanup code
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Requirement 2: 應用初始化

**描述**: FastAPI 應用應在啟動時正確初始化所有必要的元件

#### Specification:

應用初始化序列應包括：

```
1. 加載環境配置
2. 設置日誌
3. 創建 FastAPI 實例
4. 註冊路由
5. 配置中間件
6. 初始化數據服務 (可選)
7. 啟動 uvicorn 服務器
```

#### Requirements:

- 所有初始化步驟應有錯誤處理
- 應記錄初始化進度
- 應驗證必要的依賴
- 應檢查配置有效性

#### Scenario: 配置驗證失敗

```
Given: 必要的環境變量未設置
When: 執行 python run_dashboard.py
Then: 應記錄清晰的錯誤信息
And: 應包含修復建議
And: 進程應優雅退出 (exit code != 0)
```

#### Scenario: 端口被占用

```
Given: 端口 8001 已被其他服務占用
When: 執行 python run_dashboard.py
Then: 應捕獲 OSError
And: 應記錄 "Address already in use" 錯誤
And: 應建議使用 --port 參數
```

---

### Requirement 3: 日誌記錄和診斷

**描述**: 應用應提供清晰的日誌用於診斷和監控

#### Specification:

應記錄以下事件：

```
[INFO] 啟動儀表板服務
[INFO] FastAPI 應用已創建
[INFO] 已註冊 N 條路由
[INFO] 服務運行在 http://0.0.0.0:8001
[DEBUG] 初始化 DashboardAPI
[DEBUG] 初始化 PerformanceService
[INFO] 收到停止信號
[INFO] 開始清理資源
[INFO] 服務已關閉
```

#### Requirements:

- 日誌級別應正確設置 (INFO 級用於用戶, DEBUG 用於開發)
- 應包含時間戳
- 應包含模塊名稱
- 應支持日誌文件輸出 (可選)
- 敏感信息不應被記錄

#### Scenario: 調試模式日誌

```
Given: 日誌級別設為 DEBUG
When: 應用啟動
Then: 應顯示詳細的初始化日誌
And: 應顯示每個 API 調用的日誌
```

---

### Requirement 4: 優雅關閉

**描述**: 應用應支持優雅關閉，無任何懸掛連接或數據丟失

#### Specification:

優雅關閉流程應包括：

```
1. 捕獲 KeyboardInterrupt 或 SIGTERM
2. 記錄關閉信息
3. 停止接收新連接
4. 等待現有請求完成 (超時控制)
5. 清理資源 (數據庫連接、緩存等)
6. 退出進程
```

#### Requirements:

- 關閉超時應設為 30 秒
- 應記錄活動連接數
- 應正確關閉所有文件句柄
- 應清理臨時資源

#### Scenario: 优雅关闭

```
Given: 應用正在處理請求
When: 用戶按 Ctrl+C
Then: 應記錄 "Shutting down..."
And: 應等待當前請求完成
And: 應關閉所有連接
And: 進程應在 30 秒內退出
```

---

### Requirement 5: 啟動驗證

**描述**: 啟動後應驗證所有關鍵系統正常運作

#### Specification:

啟動後應檢查：

```
1. 所有 API 端點都已註冊
2. 監聽地址和端口正確
3. 可訪問健康檢查端點
4. 數據服務已初始化 (如適用)
5. 日誌系統正常運作
```

#### Requirements:

- 驗證應在啟動日誌中報告
- 任何驗證失敗應被記錄並警告
- 不應阻止啟動 (除非致命錯誤)

#### Scenario: 啟動驗證成功

```
Given: 應用已啟動
When: 檢查 GET /api/health
Then: 返回 200 OK
And: 所有驗證檢查通過
```

---

## MODIFIED Requirements

### None
不修改現有的任何啟動機制。

---

## REMOVED Requirements

### None
不移除任何現有的功能。

---

## Cross-References

相關規範：
- [api-endpoints spec](../api-endpoints/spec.md) - 應用提供的 API 端點
- [openspec/project.md](../../../../project.md) - 項目配置和約定

---

## Environment Configuration

啟動時應支持以下環境變量：

| 變量 | 類型 | 預設 | 說明 |
|------|------|------|------|
| DASHBOARD_HOST | string | 0.0.0.0 | 監聽地址 |
| DASHBOARD_PORT | int | 8001 | 監聽端口 |
| LOG_LEVEL | string | info | 日誌級別 |
| DEBUG | bool | False | 調試模式 |

---

## Error Handling Matrix

| 錯誤情況 | 處理方式 | 日誌級別 | Exit Code |
|---------|---------|---------|-----------|
| 缺失環境變量 | 顯示提示並退出 | ERROR | 1 |
| 端口被占用 | 顯示提示並退出 | ERROR | 1 |
| 配置文件錯誤 | 顯示提示並退出 | ERROR | 1 |
| 初始化失敗 | 記錄和退出 | ERROR | 1 |
| 數據服務連接失敗 | 警告並繼續 (如可選) | WARN | 0 |
| 優雅關閉超時 | 強制退出 | WARN | 1 |
| Ctrl+C 中斷 | 優雅關閉 | INFO | 0 |

---

## Performance Requirements

- 啟動時間: < 5 秒
- 首個 API 響應: < 100ms
- 內存佔用: < 300MB
- CPU 使用: < 10% (閒置時)

---

## Testing Requirements

啟動處理的測試應包括：

- [ ] 正常啟動流程
- [ ] 環境變量缺失情況
- [ ] 端口衝突情況
- [ ] Ctrl+C 優雅關閉
- [ ] 長連接處理
- [ ] 並發請求處理
- [ ] 資源清理驗證
- [ ] 日誌輸出驗證

---

## Validation Checklist

實現時應驗證：

- [ ] 無 RuntimeError 異常
- [ ] 正確的事件循環管理
- [ ] 日誌記錄完整
- [ ] 優雅關閉工作
- [ ] 所有路由都已註冊
- [ ] API 端點可訪問
- [ ] 性能指標符合要求
- [ ] 錯誤處理適當

