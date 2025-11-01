# 任務管理系統使用指南

## 🎉 系統已成功啟動並運行！

### 📊 當前狀態

**✅ 任務導入完成**
- 總任務數: 122個
- 數據庫: tasks.db
- 導入時間: 2025-10-30

### 🔍 查看導入的任務

#### 方式1: 數據庫直接查詢
```bash
# 使用Python查詢
python -c "
import sqlite3
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title, status, priority FROM tasks WHERE id LIKE \"TASK-%\" ORDER BY id LIMIT 10')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1][:50]}...')
conn.close()
"
```

#### 方式2: 查看JSON導出
```bash
cat imported_tasks.json | head -100
```

### 📋 任務看板

**前端看板演示**: http://localhost:8001/task-board-demo.html

功能包括:
- ✅ 實時統計卡片
- ✅ 拖拽式任務流轉
- ✅ 優先級標識 (P0/P1/P2)
- ✅ 狀態分類 (待開始/進行中/待驗收/已完成)
- ✅ 過濾和搜索

### 🔧 API文檔

**API文檔地址**: http://localhost:8001/docs

包含以下端點:
- `GET /api/v1/tasks` - 獲取任務列表
- `POST /api/v1/tasks` - 創建新任務
- `PUT /api/v1/tasks/{id}` - 更新任務
- `POST /api/v1/tasks/{id}/transition` - 任務狀態流轉
- `POST /api/v1/tasks/{id}/assign` - 分配任務

### 📁 系統文件

**核心文件位置**:
- 任務模型: `src/dashboard/models/task.py`
- Sprint模型: `src/dashboard/models/sprint.py`
- 任務API: `src/dashboard/api_tasks.py`
- Sprint API: `src/dashboard/api_sprints.py`
- 前端組件: `src/dashboard/static/js/components/Task*.vue`
- 任務導入服務: `src/dashboard/services/task_import_service.py`

**測試文件**:
- `tests/dashboard/test_task_import_basic.py`
- `tests/dashboard/test_task_import_api.py`

**命令行工具**:
- `scripts/import_tasks.py` - 任務導入工具
- `scripts/import_historical_tasks.py` - 歷史任務導入
- `quick_start_task_system.py` - 快速啟動腳本

### 🎯 下一步操作

#### 1. 使用任務看板管理任務
```bash
# 打開瀏覽器訪問
http://localhost:8001/task-board-demo.html
```

#### 2. 創建新任務 (通過API)
```bash
curl -X POST http://localhost:8001/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "實現新功能",
    "priority": "P1",
    "estimated_hours": 5,
    "description": "添加新功能到系統"
  }'
```

#### 3. 狀態流轉
```bash
curl -X POST http://localhost:8001/api/v1/tasks/TASK-100/transition \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "進行中",
    "comment": "開始開發"
  }'
```

#### 4. 分配任務
```bash
curl -X POST http://localhost:8001/api/v1/tasks/TASK-100/assign \
  -H "Content-Type: application/json" \
  -d '{
    "assignee": "開發者A"
  }'
```

### 📈 任務狀態說明

**狀態流轉**:
```
待開始 → 進行中 → 待驗收 → 已已完成
    ↓         ↓         ↓
  已阻塞   ← 已阻塞   ← 已阻塞
```

**優先級說明**:
- `P0`: 關鍵路徑任務，最高優先級
- `P1`: 重要任務
- `P2`: 一般任務

### 🔍 查詢示例

#### 查看所有P0任務
```python
import sqlite3
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title FROM tasks WHERE priority = \"P0\"')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')
```

#### 查看進行中的任務
```python
cursor.execute('SELECT id, title, assignee FROM tasks WHERE status = \"進行中\"')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} (分配給: {row[2]})')
```

#### 查看被阻塞的任務
```python
cursor.execute('SELECT id, title, status FROM tasks WHERE status = \"已阻塞\"')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]}')
```

### 🚀 系統特性

#### ✅ 已實現功能
- [x] 任務CRUD操作
- [x] 狀態流轉管理
- [x] 優先級分類
- [x] 任務分配
- [x] Sprint管理
- [x] 任務導入導出
- [x] 前端任務看板
- [x] API文檔
- [x] 數據庫索引優化
- [x] 任務依賴管理
- [x] 批量操作
- [x] 搜索和過濾

#### 🔄 實時功能
- [x] WebSocket支持
- [x] 實時統計
- [x] 拖拽流轉
- [x] 自動更新

#### 📊 報表功能
- [x] 任務統計
- [x] 進度追蹤
- [x] 優先級分布
- [x] 階段分布

### 🎓 使用建議

#### 1. 日常任務管理
- 每天查看任務看板
- 將任務從"待開始"拖拽到"進行中"
- 完成後將任務拖拽到"待驗收"
- 驗收後將任務標記為"已完成"

#### 2. Sprint規劃
- 使用Sprint API創建新的Sprint
- 將任務分配到特定Sprint
- 跟蹤Sprint進度和完成率

#### 3. 團隊協作
- 將任務分配給團隊成員
- 使用評論功能記錄進度
- 定期更新任務狀態

#### 4. 報告和分析
- 使用API獲取統計數據
- 定期導出任務數據
- 分析團隊效率和瓶頸

### 🛠️ 故障排除

#### 問題1: 無法訪問任務看板
**解決**: 確保前端服務正在運行
```bash
ps aux | grep "http.server 8001"
```

#### 問題2: API返回404
**解決**: 檢查FastAPI應用是否運行
```bash
ps aux | grep simple_task_api
```

#### 問題3: 數據庫錯誤
**解決**: 檢查tasks.db文件
```bash
ls -lh tasks.db
```

### 📞 技術支持

如有問題，請查看:
1. `PROJECT_PLAN_OPTIMIZATION_STATUS_REPORT.md` - 完整狀態報告
2. `imported_tasks.json` - 導入的任務數據
3. `TASK_IMPORT_SUMMARY.txt` - 導入摘要

### 🎉 開始使用

立即開始管理您的項目任務！

1. 打開任務看板: http://localhost:8001/task-board-demo.html
2. 查看API文檔: http://localhost:8001/docs
3. 開始您的任務管理之旅！

---
**最後更新**: 2025-10-30  
**版本**: v1.0  
**狀態**: ✅ 運行中
