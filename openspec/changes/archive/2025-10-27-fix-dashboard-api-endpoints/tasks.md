# Dashboard API Endpoints Fix - Tasks

**Change ID**: fix-dashboard-api-endpoints
**Total Tasks**: 13
**Estimated Duration**: 13 hours

---

## Phase 1: 設計與規範 (2 hours)

### Task 1.1: 驗證當前 API 規範
- **Objective**: 確認 HTML 期望的 API 端點和響應格式
- **Actions**:
  - [x] 解析 index.html 中的 JavaScript API 調用
  - [x] 記錄所有期望的端點
  - [x] 定義期望的 JSON 響應格式
- **Validation**: 創建 API 需求文檔
- **Time**: 1 hour
- **Status**: COMPLETED

### Task 1.2: 建立 API 規範文檔
- **Objective**: 創建完整的 OpenSpec API 規範
- **Actions**:
  - [ ] 創建 `specs/api-endpoints/spec.md`
  - [ ] 定義每個端點的需求
  - [ ] 添加場景案例 (Scenario)
  - [ ] 驗證規範
- **Validation**: `openspec validate fix-dashboard-api-endpoints`
- **Time**: 1 hour
- **Status**: PENDING

---

## Phase 2: 實現 API 層 (4 hours)

### Task 2.1: 修復啟動流程
- **Objective**: 解決 asyncio 事件循環衝突
- **Actions**:
  - [ ] 重寫 `run_dashboard.py` main() 函數
  - [ ] 使用 uvicorn.Server 低階 API
  - [ ] 移除 asyncio.run() 調用
  - [ ] 添加 try/except 錯誤處理
- **Files Modified**: `run_dashboard.py`
- **Validation**:
  - [ ] 腳本可成功啟動
  - [ ] 無 RuntimeError
  - [ ] 服務監聽 8001 端口
- **Tests**:
  - [ ] `test_dashboard_startup.py`
- **Time**: 1.5 hours
- **Dependencies**: Task 1.1
- **Status**: PENDING

### Task 2.2: 實現健康檢查 API
- **Objective**: 實現 GET /api/health 和 GET /health 端點
- **Actions**:
  - [ ] 添加 @app.get('/api/health') 路由
  - [ ] 添加 @app.get('/health') 別名
  - [ ] 實現系統狀態檢查邏輯
  - [ ] 添加適當的日誌
- **Files Modified**: `run_dashboard.py` 或新建 `api_handlers.py`
- **Validation**:
  - [ ] curl http://localhost:8001/api/health 返回 200
  - [ ] JSON 響應包含 status, service, timestamp
- **Tests**:
  - [ ] `test_health_endpoint.py`
- **Time**: 1 hour
- **Dependencies**: Task 2.1
- **Status**: PENDING

### Task 2.3: 實現投資組合 API
- **Objective**: 實現 GET /api/trading/portfolio 端點
- **Actions**:
  - [ ] 添加 @app.get('/api/trading/portfolio') 路由
  - [ ] 實現 Mock 投資組合數據
  - [ ] 返回期望的 JSON 結構
  - [ ] 添加錯誤處理
- **Files Modified**: `run_dashboard.py` 或 `api_handlers.py`
- **Validation**:
  - [ ] GET /api/trading/portfolio 返回 200
  - [ ] 包含所有必要字段
- **Tests**:
  - [ ] `test_portfolio_endpoint.py`
- **Time**: 0.75 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING

### Task 2.4: 實現性能 API
- **Objective**: 實現 GET /api/trading/performance 端點
- **Actions**:
  - [ ] 添加 @app.get('/api/trading/performance') 路由
  - [ ] 實現性能指標計算或 Mock 數據
  - [ ] 返回 Sharpe, MaxDD, 收益率等指標
  - [ ] 添加時間戳
- **Files Modified**: `run_dashboard.py` 或 `api_handlers.py`
- **Validation**:
  - [ ] GET /api/trading/performance 返回 200
  - [ ] 包含完整的性能指標
- **Tests**:
  - [ ] `test_performance_endpoint.py`
- **Time**: 0.75 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING

### Task 2.5: 實現系統狀態 API
- **Objective**: 實現 GET /api/system/status 端點
- **Actions**:
  - [ ] 添加 @app.get('/api/system/status') 路由
  - [ ] 實現系統狀態檢查
  - [ ] 返回正確的狀態值
  - [ ] 包含資源使用信息
- **Files Modified**: `run_dashboard.py` 或 `api_handlers.py`
- **Validation**:
  - [ ] GET /api/system/status 返回 200
  - [ ] status 字段值為 "operational"
- **Tests**:
  - [ ] `test_system_status_endpoint.py`
- **Time**: 0.75 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING

### Task 2.6: 實現系統刷新 API (Optional)
- **Objective**: 實現 POST /api/system/refresh 端點
- **Actions**:
  - [ ] 添加 @app.post('/api/system/refresh') 路由
  - [ ] 實現重新加載邏輯
  - [ ] 返回刷新狀態
- **Files Modified**: `run_dashboard.py` 或 `api_handlers.py`
- **Validation**:
  - [ ] POST /api/system/refresh 返回 200
- **Tests**:
  - [ ] `test_refresh_endpoint.py`
- **Time**: 0.75 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING
- **Priority**: MEDIUM

---

## Phase 3: Favicon 和靜態資源 (1 hour)

### Task 3.1: 添加 Favicon
- **Objective**: 移除 404 favicon 錯誤
- **Actions**:
  - [ ] 生成或準備 favicon.ico
  - [ ] 將其放在靜態資源目錄
  - [ ] 配置 FastAPI 靜態文件服務
  - [ ] 或使用 Base64 embedded favicon
- **Files Modified**: `run_dashboard.py`
- **Validation**:
  - [ ] curl http://localhost:8001/favicon.ico 返回 200
  - [ ] 或 HTML 不再請求 favicon
- **Time**: 0.5 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING

### Task 3.2: 配置靜態文件服務
- **Objective**: 為 CSS、JS、圖片等配置靜態文件服務
- **Actions**:
  - [ ] 創建 static/ 目錄
  - [ ] 配置 StaticFiles 中間件
  - [ ] 驗證靜態資源加載
- **Files Modified**: `run_dashboard.py`
- **Validation**:
  - [ ] 所有靜態資源可訪問
- **Time**: 0.5 hours
- **Dependencies**: Task 2.1
- **Status**: PENDING

---

## Phase 4: 集成與測試 (3 hours)

### Task 4.1: 編寫單元測試
- **Objective**: 為所有 API 端點編寫單元測試
- **Actions**:
  - [ ] 創建 `tests/test_dashboard_api.py`
  - [ ] 編寫每個端點的測試用例
  - [ ] 驗證 HTTP 狀態碼
  - [ ] 驗證 JSON 響應格式
  - [ ] 驗證錯誤處理
- **Files**: `tests/test_dashboard_api.py` (新建)
- **Coverage Target**: >= 80%
- **Validation**:
  - [ ] `pytest tests/test_dashboard_api.py -v`
  - [ ] 所有測試通過
- **Time**: 1.5 hours
- **Dependencies**: Task 2.1-2.6
- **Status**: PENDING

### Task 4.2: 整合測試 (端到端)
- **Objective**: 從前端視角測試完整的工作流
- **Actions**:
  - [ ] 啟動儀表板服務
  - [ ] 用瀏覽器訪問 http://localhost:8001
  - [ ] 驗證頁面無 404 錯誤
  - [ ] 驗證數據正常顯示
  - [ ] 檢查系統狀態顯示
- **Files**: `INTEGRATION_TEST_REPORT.md` (新建)
- **Validation**:
  - [ ] 所有 HTTP 請求返回 200
  - [ ] 頁面無刷新迴圈
  - [ ] 控制台無 JavaScript 錯誤
- **Time**: 1 hour
- **Dependencies**: Task 2.1-4.1
- **Status**: PENDING

### Task 4.3: 性能和負載測試
- **Objective**: 驗證 API 性能
- **Actions**:
  - [ ] 測試 API 響應時間
  - [ ] 驗證內存使用
  - [ ] 檢查並發性能
  - [ ] 記錄性能指標
- **Files**: `PERFORMANCE_TEST_REPORT.md` (新建)
- **Performance Target**:
  - [ ] API 響應時間 < 100ms
  - [ ] 內存使用 < 500MB
- **Time**: 0.5 hours
- **Dependencies**: Task 4.1
- **Status**: PENDING

---

## Phase 5: 文檔與驗收 (2 hours)

### Task 5.1: 更新測試文檔
- **Objective**: 記錄測試結果
- **Actions**:
  - [ ] 更新 DASHBOARD_TEST_REPORT.md
  - [ ] 記錄所有修復項
  - [ ] 驗收標準檢查清單
  - [ ] 對比修復前後
- **Files**: `DASHBOARD_TEST_REPORT.md` (更新)
- **Time**: 0.5 hours
- **Dependencies**: Task 4.1-4.3
- **Status**: PENDING

### Task 5.2: 更新代碼文檔
- **Objective**: 添加 docstrings 和評論
- **Actions**:
  - [ ] 為所有新增 API 端點添加 docstring
  - [ ] 添加內聯評論解釋複雜邏輯
  - [ ] 更新 CLAUDE.md 中的儀表板說明
- **Files**: `run_dashboard.py`, `CLAUDE.md`
- **Time**: 0.5 hours
- **Dependencies**: Task 2.1-4.3
- **Status**: PENDING

### Task 5.3: 創建 API 文檔
- **Objective**: 生成完整的 API 文檔
- **Actions**:
  - [ ] 創建 API_REFERENCE.md
  - [ ] 列出所有端點
  - [ ] 提供 curl 示例
  - [ ] 記錄常見問題
- **Files**: `API_REFERENCE.md` (新建)
- **Time**: 0.5 hours
- **Dependencies**: Task 2.1-2.6
- **Status**: PENDING

### Task 5.4: 最終驗收和合併
- **Objective**: 驗收並準備合併
- **Actions**:
  - [ ] 運行完整的 `openspec validate`
  - [ ] 檢查所有驗收標準
  - [ ] 準備 git commit
  - [ ] 創建 PR 用於審查
- **Validation**:
  - [ ] `openspec validate fix-dashboard-api-endpoints --strict` 通過
  - [ ] 所有驗收標準滿足
  - [ ] 代碼審查通過
- **Files**: Git commit, Pull Request
- **Time**: 0.5 hours
- **Dependencies**: Task 5.1-5.3
- **Status**: PENDING

---

## 依賴關係圖

```
Task 1.1 ─────────────────────────┐
          └─→ Task 1.2 (待後續)    │
                                  │
                                  ▼
Task 2.1 ────→ Task 2.2/2.3/2.4/2.5/2.6
                      │
                      ▼
Task 3.1/3.2 ───→ Task 4.1
                      │
                      ▼
Task 4.2 ────────→ Task 4.3
                      │
                      ▼
Task 5.1/5.2/5.3 ──→ Task 5.4
```

---

## 優先級和平行化

### 高優先級 (P0) - 必須完成
- Task 2.1: 修復啟動流程
- Task 2.2-2.5: 實現必要的 API 端點
- Task 4.1-4.2: 單元和整合測試

### 中優先級 (P1) - 應該完成
- Task 3.1-3.2: Favicon 和靜態資源
- Task 5.1-5.3: 文檔更新

### 低優先級 (P2) - 可選
- Task 2.6: 系統刷新 API (可選)
- Task 4.3: 性能測試 (可選)

### 可平行化的任務
- Task 2.2-2.5 可同時進行 (獨立的 API 端點)
- Task 4.2-4.3 可並行執行 (獨立測試)

---

## 定義完成 (DoD - Definition of Done)

每個 Task 完成後必須滿足：
- ✅ 代碼已編寫並通過本地測試
- ✅ 單元測試通過，覆蓋率 >= 80%
- ✅ 無 Python 語法或邏輯錯誤
- ✅ 添加了適當的日誌記錄
- ✅ 更新了相關文檔
- ✅ 代碼審查通過
- ✅ 集成測試通過

---

## 驗收標準 (Definition of Acceptance)

全部 Task 完成後整個修復應滿足：
- ✅ 所有 API 端點返回 HTTP 200
- ✅ 儀表板頁面無 404 錯誤
- ✅ 系統狀態顯示 "OPERATIONAL"
- ✅ 儀表板數據正常顯示
- ✅ 無持續頁面刷新迴圈
- ✅ 單元測試覆蓋率 >= 80%
- ✅ 集成測試全部通過
- ✅ 性能指標符合目標
- ✅ 完整的代碼和 API 文檔

