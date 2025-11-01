# 任務數據導入使用指南

## 📋 概述

任務數據導入功能可以將Markdown格式的任務清單批量導入到任務管理系統中。目前支持從項目計劃優化任務清單（109個任務）進行導入。

## 🚀 快速開始

### 方法1: 使用命令行工具

#### 1. 分析任務清單
```bash
# 分析文件質量
python scripts/import_tasks.py analyze openspec/changes/optimize-project-plan/tasks.md
```

輸出示例：
```
============================================================
📊 任務清單分析
============================================================

文件: openspec/changes/optimize-project-plan/tasks.md
總行數: 344
任務數量: 109

優先級分布:
  P0: 45 個 (41.3%)
  P1: 41 個 (37.6%)
  P2: 23 個 (21.1%)

工時統計:
  最小: 2 小時
  最大: 12 小時
  平均: 3.5 小時
  總計: 180 小時

✅ 未發現質量問題

📈 質量評分: 95.0/100
  優秀 ✅

============================================================
```

#### 2. 導入任務（演練模式）
```bash
# 演練模式（預覽，不實際導入）
python scripts/import_tasks.py import openspec/changes/optimize-project-plan/tasks.md
```

#### 3. 實際導入
```bash
# 執行實際導入
python scripts/import_tasks.py import openspec/changes/optimize-project-plan/tasks.md --no-dry-run
```

### 方法2: 使用API端點

#### 1. 分析任務清單
```bash
curl -X POST http://localhost:8001/api/v1/import/tasks/analyze \
  -H "Content-Type: application/json" \
  -d '{"file_path": "openspec/changes/optimize-project-plan/tasks.md"}'
```

#### 2. 開始導入
```bash
curl -X POST http://localhost:8001/api/v1/import/tasks/start \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "openspec/changes/optimize-project-plan/tasks.md",
    "create_sprint": true
  }'
```

#### 3. 檢查導入狀態
```bash
# 替換import_id為實際返回的ID
curl http://localhost:8001/api/v1/import/tasks/status/import_20251029_143000
```

#### 4. 查看導入報告
```bash
curl http://localhost:8001/api/v1/import/tasks/report/import_20251029_143000
```

### 方法3: 上傳文件導入

```bash
curl -X POST http://localhost:8001/api/v1/import/tasks/upload \
  -F "file=@tasks.md" \
  -F "create_sprint=true"
```

## 📊 分析功能

### 分析內容
- **任務數量統計**: 總任務數、按優先級分布
- **工時分析**: 最小/最大/平均/總計工時
- **質量問題檢測**: 無優先級、無時間估算、過長任務等
- **質量評分**: 0-100分綜合評分

### 質量問題類型
1. 無優先級任務
2. 無時間估算
3. 長時間任務（>20小時）
4. 超短任務（<1小時）
5. 重複任務標題

### 評分標準
- **90-100分**: 優秀 ✅
- **60-89分**: 良好 ⚠️
- **<60分**: 需改進 ❌

## 🔄 導入流程

### 步驟1: 文件解析
- 讀取Markdown文件
- 提取階段和小節信息
- 解析任務行
- 提取優先級、時間、文件路徑

### 步驟2: 數據驗證
- 檢查任務標題
- 驗證優先級（P0/P1/P2）
- 檢查時間估算
- 去除重複任務

### 步驟3: Sprint創建
- 為每個階段創建對應Sprint
- 分配Sprint ID（SPRINT-1, SPRINT-2, ...）
- 設置Sprint基本信息

### 步驟4: 任務創建
- 分配任務ID（TASK-100, TASK-101, ...）
- 生成描述（包含階段信息）
- 設置默認狀態為「待開始」
- 分配到對應Sprint

### 步驟5: 生成報告
- 導入摘要統計
- 按優先級/階段分布
- 錯誤和警告
- 任務ID列表

## 📈 導入統計

### 109個任務分布
- **P0任務**: 45個 (41.3%)
- **P1任務**: 41個 (37.6%)
- **P2任務**: 23個 (21.1%)
- **總工時**: 180小時
- **建議Sprint數**: 3個

### 按階段分布
- **階段1**: 數據模型設計 + 任務管理API + 前端界面 + 自動化工作流 (3天)
- **階段2**: 工作流標準化 (2天)
- **階段3**: 項目結構整理 (2天)
- **階段4**: 指標和監控 (1天)
- **階段5**: Sprint試運行 (2週)

## 🎯 導入規則

### 任務ID分配
- 起始編號: TASK-100
- 格式: TASK-XXX（3位數字）
- 順序: 按階段和文件中的順序

### 優先級映射
- `[P0]` → P0 (關鍵路徑)
- `[P1]` → P1 (重要)
- `[P2]` → P2 (一般)

### Sprint映射
- 階段1 → SPRINT-1
- 階段2 → SPRINT-2
- 階段3 → SPRINT-3
- 階段4 → SPRINT-4
- 階段5 → SPRINT-5

### 默認值
- 狀態: 待開始
- 被分配者: 無
- 報告者: 系統導入
- 故事點: 根據工時自動計算

## 📝 任務清單格式

### Markdown格式示例
```markdown
## 階段1: 任務管理系統建設

### 1.1 數據模型設計 (4小時)
- [ ] 創建 `src/dashboard/models/task.py` 任務數據模型 [P0]
- [ ] 創建 `src/dashboard/models/sprint.py` Sprint數據模型 [P0]
- [ ] 創建 `src/dashboard/models/task_status.py` 狀態枚舉 [P0]
- [ ] 定義數據庫遷移腳本 [P1]

### 1.2 任務管理API開發 (8小時)
- [ ] 實現 `/api/tasks` GET端點 (獲取任務列表) [P0]
- [ ] 實現 `/api/tasks` POST端點 (創建任務) [P0]
```

### 格式說明
- **階段標題**: `## 階段X: 標題`
- **小節標題**: `### X.X 標題 (時間)`
- **任務行**: `- [ ] 任務描述 [優先級] (時間)`
- **文件引用**: `路徑`（反引號包圍）

## 🔧 進階使用

### 只創建Sprint不導入任務
```bash
python scripts/import_tasks.py import tasks.md --create-sprint --dry-run
```

### 驗證已導入任務
```bash
# API方式
curl http://localhost:8001/api/v1/import/tasks/validate

# 命令行（待實現）
python scripts/import_tasks.py validate
```

### 回滾導入
```bash
# 刪除指定任務
curl -X POST http://localhost:8001/api/v1/import/tasks/rollback \
  -H "Content-Type: application/json" \
  -d '{"task_ids": ["TASK-100", "TASK-101"]}'
```

### 批量導入多個文件
```bash
# 使用shell腳本
for file in tasks_*.md; do
  echo "正在導入: $file"
  python scripts/import_tasks.py import "$file" --no-dry-run
done
```

## 📊 查看導入結果

### 在任務看板中查看
1. 訪問: http://localhost:8001/tasks
2. 查看任務列表
3. 按Sprint篩選

### 獲取導入報告
```bash
# API方式
curl http://localhost:8001/api/v1/import/tasks/report/{import_id}

# 報告文件
cat import_report_*.md
```

### 驗證數據完整性
```bash
# 統計任務
curl http://localhost:8001/api/v1/tasks/metrics

# 驗證任務
curl http://localhost:8001/api/v1/import/tasks/validate
```

## ⚠️ 注意事項

### 導入前
1. ✅ 備份現有任務數據
2. ✅ 確保文件路徑正確
3. ✅ 檢查文件格式
4. ✅ 運行質量分析

### 導入中
1. ⏳ 導入過程可能需要幾分鐘
2. ⏳ 請勿中斷導入過程
3. ⏳ 觀察日誌輸出

### 導入後
1. 🔍 檢查導入報告
2. 🔍 驗證任務數據
3. 🔍 分配任務給團隊
4. 🔍 啟動Sprint

## 🆘 常見問題

### Q: 文件不存在錯誤
**A**: 檢查文件路徑是否正確
```bash
# 檢查文件是否存在
ls -la openspec/changes/optimize-project-plan/tasks.md
```

### Q: 導入失敗
**A**: 檢查日誌和錯誤信息
```bash
# 查看錯誤
tail -f quant_system.log | grep import
```

### Q: 任務重複
**A**: 系統會檢查重複，但建議先備份
```bash
# 檢查重複任務
curl http://localhost:8001/api/v1/import/tasks/validate
```

### Q: 質量分數低
**A**: 優化任務描述
- 添加優先級標籤 [P0/P1/P2]
- 添加時間估算 (X小時)
- 拆分長時間任務
- 避免重複標題

## 📞 技術支持

如需幫助：
1. 查看導入報告
2. 檢查日誌文件
3. 參考本文檔
4. 聯繫開發團隊

## 🔗 相關鏈接

- 任務看板: `/tasks`
- 導入API文檔: `/docs#/import`
- 項目計劃: `openspec/changes/optimize-project-plan/`
- 導入腳本: `scripts/import_tasks.py`
