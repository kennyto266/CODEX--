# Git自動化工作流使用指南

## 📋 概述

Git自動化工作流實現了以下功能：
- Git提交自動關聯任務
- 根據提交信息自動更新任務狀態
- 任務依賴檢查和阻塞檢測
- 僵屍任務檢測和告警
- 自動生成進度報告

## 🚀 快速開始

### 1. 設置Git Hook

在項目根目錄執行：
```bash
python scripts/setup_git_hooks.py
```

這會自動設置：
- `pre-commit`: 檢查提交格式
- `commit-msg`: 處理提交信息並更新任務

### 2. 查看任務看板

訪問：`http://localhost:8001/tasks`

### 3. 提交代碼

按照規範格式提交代碼，任務會自動更新。

## 📝 提交格式規範

### 基本格式
```
<type>: <task_id> <description>
```

### 類型（Type）
- `feat`: 新功能
- `fix`: Bug修復
- `docs`: 文檔更新
- `style`: 代碼格式
- `refactor`: 重構
- `test`: 測試
- `chore`: 雜項
- `perf`: 性能優化

### 示例

#### 1. 開始任務
```bash
git commit -m "feat: TASK-001 實現用戶認證功能
- 添加登錄頁面
- 集成JWT驗證
WIP"
```
結果：任務狀態更新為「進行中」

#### 2. 進度更新
```bash
git commit -m "progress: TASK-001 實現登錄驗證邏輯
- 驗證用戶名密碼
- 生成JWT token"
```
結果：添加進度註記

#### 3. 完成任務
```bash
git commit -m "feat: TASK-001 完成用戶認證功能
- 前端登錄表單
- 後端驗證邏輯
- JWT token生成
Closes TASK-001"
```
結果：任務狀態更新為「已完成」

#### 4. 修復問題
```bash
git commit -m "fix: TASK-002 修復登錄頁面bug
- 修復密碼驗證錯誤
- 優化錯誤提示"
Close TASK-002"
```
結果：任務標記為已完成

#### 5. 文檔任務
```bash
git commit -m "docs: TASK-003 更新API文檔
- 添加認證接口說明
- 更新示例代碼"
Close TASK-003"
```
結果：文檔任務自動完成

## 🔧 自動化規則

### 規則1: 關閉任務
**觸發**: 提交信息包含 `close`, `fix`, `resolve`, `complete`
**操作**: 自動將任務標記為「已完成」

### 規則2: 開始任務
**觸發**: 提交信息包含 `start`, `begin`, `init`, `work on`
**操作**: 自動將任務狀態改為「進行中」

### 規則3: 進度更新
**觸發**: 提交信息包含 `wip`, `progress`, `update`
**操作**: 添加進度註記

### 規則4: 文檔任務
**觸發**: 提交類型為 `docs`
**操作**: 自動完成文檔任務

### 規則5: 測試任務
**觸發**: 提交類型為 `test`
**操作**: 自動完成測試任務

### 規則6: 自動分配
**觸發**: 任何提交
**操作**: 自動分配給提交者

## 🔍 任務檢查

### 檢查類型

#### 1. 依賴檢查
- 檢查任務依賴是否已滿足
- 自動標記阻塞任務

#### 2. 僵屍任務檢測
- 3天未更新的任務
- 自動發送提醒

#### 3. 循環依賴檢測
- 檢測任務間是否存在循環依賴
- 生成告警

#### 4. WIP限制檢查
- 每人同時超過3個任務
- 提醒重新分配

### 運行檢查
```bash
# 運行所有檢查
curl -X POST http://localhost:8001/api/v1/automation/check/run

# 指定Sprint檢查
curl -X POST http://localhost:8001/api/v1/automation/check/run \
  -H "Content-Type: application/json" \
  -d '{"sprint_id": "SPRINT-2025-10", "auto_fix": true}'

# 獲取檢查報告
curl http://localhost:8001/api/v1/automation/check/report
```

## 🔄 Webhook集成

### GitHub Webhook
1. 進入GitHub倉庫設置
2. 添加Webhook URL: `http://your-server.com/api/v1/automation/webhook/git`
3. 選擇事件：`push`, `pull_request`, `issues`
4. 保存設置

### GitLab Webhook
1. 進入GitLab項目設置
2. 添加Webhook URL: `http://your-server.com/api/v1/automation/webhook/git`
3. 勾選觸發事件
4. 保存設置

## 📊 API端點

### 提交處理
```bash
POST /api/v1/automation/commit/process
{
  "repo_path": "/path/to/repo",
  "commit": {
    "hash": "abc123...",
    "message": "feat: TASK-001 your message",
    "author": "developer@example.com",
    "branch": "main",
    "files": ["src/auth/login.js"],
    "timestamp": "2025-10-29T10:00:00Z"
  }
}
```

### Webhook接收
```bash
POST /api/v1/automation/webhook/git
# 自動處理GitHub/GitLab推送
```

### 任務檢查
```bash
POST /api/v1/automation/check/run
{
  "sprint_id": "SPRINT-2025-10",
  "auto_fix": true
}
```

### 規則管理
```bash
# 獲取所有規則
GET /api/v1/automation/rules

# 啟用規則
PUT /api/v1/automation/rules/{rule_name}/toggle?enabled=true

# 獲取統計
GET /api/v1/automation/stats
```

## 📈 自動化統計

查看自動化工作流效果：
```bash
curl http://localhost:8001/api/v1/automation/stats
```

返回數據包含：
- 總任務數
- 自動化更新次數
- 被阻塞任務數
- 完成率
- 規則統計

## 🎯 最佳實踐

### 1. 提交信息
- 始终包含任務ID：`TASK-001`
- 使用標準格式：`type: TASK-001 message`
- 關閉任務時使用關鍵字：`Closes TASK-001`

### 2. 任務分解
- 每個任務盡量小（1-2天）
- 明確的交付物
- 清晰的驗收標準

### 3. 依賴管理
- 避免循環依賴
- 及時更新依賴任務狀態
- 主動檢查阻塞任務

### 4. 定期檢查
- 每日運行任務檢查
- 週檢查Sprint健康度
- 月度自動化效果報告

## ⚠️ 常見問題

### Q: 提交後任務沒有更新？
A: 檢查：
1. 是否正確安裝Git Hook
2. 提交格式是否正確
3. 檢查日誌：`tail -f /var/log/git-automation.log`

### Q: 如何手動觸發檢查？
A:
```bash
curl -X POST http://localhost:8001/api/v1/automation/check/run
```

### Q: 如何禁用某個規則？
A:
```bash
curl -X PUT http://localhost:8001/api/v1/automation/rules/{rule_name}/toggle?enabled=false
```

### Q: Webhook不工作？
A: 檢查：
1. URL是否正確
2. 服務是否運行
3. 防火牆設置
4. GitHub/GitLab配置

## 🔧 配置

### 修改自動化規則
編輯文件：`src/dashboard/services/automation_config.py`
- 添加新規則
- 修改觸發條件
- 調整操作

### 自定義檢查邏輯
編輯文件：`src/dashboard/services/task_checker_service.py`
- 添加新的檢查類型
- 實現自動修復
- 調整告警規則

## 📞 技術支持

如有問題，請：
1. 查看日誌文件
2. 檢查API響應
3. 參考本文檔
4. 聯繫開發團隊

## 🔗 相關鏈接

- 任務看板: `/tasks`
- API文檔: `/docs`
- 檢查報告: `/api/v1/automation/check/report`
- 規則列表: `/api/v1/automation/rules`
