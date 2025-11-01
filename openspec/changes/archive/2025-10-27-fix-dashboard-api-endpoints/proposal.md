# Dashboard API Endpoints Fix - Proposal

**Change ID**: fix-dashboard-api-endpoints
**Status**: PROPOSED
**Created**: 2025-10-26
**Author**: Claude Code AI

## Executive Summary

Dashboard 儀表板無法正常運作，因為 API 端點未正確實現。經過全面測試，發現 5 個關鍵和高優先級問題：

1. **Critical**: API 端點缺失 (404 errors)
2. **High**: asyncio 事件循環衝突導致啟動失敗
3. **High**: 系統狀態顯示不正確 ("DEGRADED" 而非 "OPERATIONAL")
4. **High**: 頁面自動刷新迴圈
5. **Low**: Favicon 缺失

## Why

儀表板是 CODEX 系統的關鍵組件，用於實時監控 7 個 AI Agent、查看投資組合狀態和交易性能。當前實現無法正常運作，限制了系統的可用性和可觀測性。

**業務影響**:
- 用戶無法監控系統狀態
- 無法查看實時性能指標
- 無法進行故障診斷
- 影響交易系統的信任度

**技術影響**:
- API 設計與前端期望不匹配
- asyncio 事件循環衝突導致啟動失敗
- 缺失標準化的 API 規範

---

## Problem Statement

### 當前狀態
- ✅ 頁面 HTML 可加載
- ❌ API 端點返回 404 (portfolio, performance, health)
- ❌ 無法顯示性能數據
- ❌ 系統狀態無法獲取
- ❌ 頁面陷入刷新迴圈

### 根本原因
1. `run_dashboard.py` 啟動腳本只實現了 2 個端點，缺失所有其他必要的 API
2. asyncio.run() 與 uvicorn.run() 的事件循環衝突
3. HTML 頁面期望完整的 API，但後端未提供

### 影響範圍
- 🔴 P0: 無法訪問儀表板功能
- 🔴 P0: 無法監控 Agent 狀態
- 🔴 P0: 無法查看性能指標

## Proposed Solution

### 1. 修復 API 端點 (Spec: api-endpoints)
實現以下必要的 API 端點：
- `GET /api/health` - 系統健康檢查
- `GET /api/trading/portfolio` - 投資組合數據
- `GET /api/trading/performance` - 性能指標
- `POST /api/system/refresh` - 刷新系統狀態
- 其他儀表板所需端點

### 2. 修復啟動流程 (Spec: startup-handler)
解決 asyncio 事件循環衝突：
- 改用 `uvicorn.Config()` + `uvicorn.Server()` 的低階 API
- 或使用 `asyncio.run(uvicorn.run(...))` 的替代方案
- 正確初始化 FastAPI 應用

### 3. 完整儀表板集成
- 集成 DashboardAPI 類
- 連接所有數據服務
- 實現實時 WebSocket 推送

## Impact Assessment

### 正面影響
- ✅ 儀表板可完全運作
- ✅ 用戶可監控系統狀態
- ✅ 性能數據實時顯示
- ✅ Agent 狀態可視化

### 負面影響
- ⚠️ 需要正確的數據服務實現
- ⚠️ 可能需要調整 API 響應格式

## Risk Assessment

| 風險 | 等級 | 緩解方案 |
|------|------|---------|
| API 格式不匹配 | Medium | 驗證 HTML 期望的 API 響應格式 |
| 性能問題 | Low | 使用 LRU 緩存減少 API 調用 |
| 相容性問題 | Low | 充分的單元測試 |

## Scope & Deliverables

### In Scope ✅
- 實現所有必要的 REST API 端點
- 修復 asyncio 事件循環問題
- 實現 Mock 數據服務用於測試
- 添加完整的 API 文檔
- 編寫單元和集成測試

### Out of Scope ❌
- WebSocket 實時推送的完整實現 (已有，需驗證)
- Agent 系統的完整集成 (相依於其他組件)
- 生產環境優化 (安全性、認證等)

## Success Criteria

- ✅ 所有 API 端點返回 HTTP 200
- ✅ 頁面不再出現 404 錯誤
- ✅ 系統狀態顯示 "OPERATIONAL"
- ✅ 儀表板數據正常顯示
- ✅ 無持續的頁面刷新迴圈
- ✅ 單元測試覆蓋率 >= 80%
- ✅ 集成測試通過

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1. 設計與規範 | 2 小時 | Spec docs |
| 2. 實現 API 層 | 4 小時 | 所有端點實現 |
| 3. 修復啟動流程 | 2 小時 | 運行腳本修復 |
| 4. 集成與測試 | 3 小時 | 測試與驗證 |
| 5. 文檔與驗收 | 2 小時 | 最終報告 |
| **總計** | **13 小時** | 完全修復 |

## Dependencies

- [ ] `openspec/specs/dashboard-api/spec.md` - 完整 API 規範 (待創建)
- [x] `openspec/project.md` - 項目上下文 (已有)
- [x] `DASHBOARD_TEST_REPORT.md` - 測試報告 (已創建)

## Next Steps

1. 進行 OpenSpec 設計審查
2. 創建詳細的規範文檔
3. 提交任務清單供批准
4. 開始實現

---

**Approval Status**: ⏳ PENDING REVIEW

