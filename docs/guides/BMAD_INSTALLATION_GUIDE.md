# BMAD-METHOD 安裝成功指南

## ✅ 已完成安裝

BMAD-METHOD 已成功安裝到您的項目中！

### 📁 安裝的文件結構

```
your-project/
├── bmad/                          # BMAD 核心目錄
│   ├── core/                      # 核心框架
│   │   ├── agents/                # 代理配置
│   │   │   └── bmad-web-orchestrator.agent.xml
│   │   ├── tasks/                 # 任務模板
│   │   └── workflows/             # 工作流模板
│   ├── bmm/                       # BMad Method (敏捷 AI 開發)
│   │   ├── tasks/                 # 項目管理任務
│   │   └── workflows/             # 開發工作流
│   ├── bmb/                       # BMad Builder (自定義解決方案)
│   │   ├── workflows/             # 工作流創建
│   │   └── agents/                # 代理配置
│   ├── cis/                       # Creative Intelligence Suite
│   ├── docs/                      # 文檔
│   └── _cfg/                      # 您的自定義配置
├── .claude/                       # Claude 集成配置
│   └── commands/bmad/             # Claude 命令
├── BMAD-METHOD/                   # 源代碼（可選，可刪除）
└── bmad_install_summary.md        # 本文件
```

## 🚀 如何使用 BMAD

### 1. 啟動工作流

在 Claude 中使用以下斜杠命令來啟動 BMAD 工作流：

```
/workflow-init
```

這將初始化工作流系統並幫助您選擇起始點。

### 2. 主要模塊功能

#### 📋 BMM (BMad Method) - 敏捷 AI 開發
- **四階段方法**：
  1. Analysis - 頭腦風暴、研究、簡報
  2. Planning - 規模自適應 PRD/GDD
  3. Solutioning - 架構和技術規範
  4. Implementation - 故事、開發、審查

- **專門代理**：PM、Analyst、Architect、Scrum Master、Developer、Game Designer/Developer/Architect、UX、Test Architect

#### 🔨 BMB (BMad Builder) - 創建自定義解決方案
- **Agent Creation** - 自定義角色和行為
- **Workflow Design** - 結構化多步驟流程
- **Module Development** - 完整領域解決方案

#### 🎨 CIS (Creative Intelligence Suite) - 創新與創造力
- **5 個互動工作流** - 頭腦風暴、設計思維、問題解決、創新策略、故事講述
- **150+ 創意技術** - 經過驗證的框架和方法論
- **5 個專門代理** - 獨特的角色和促進風格

## 📚 可用的 Claude 斜杠命令

在 Claude 中，您可以使用以下命令：

1. **`/workflow-init`** - 初始化工作流系統
2. **`/bmad:analyze`** - 啟動分析階段
3. **`/bmad:plan`** - 啟動規劃階段
4. **`/bmad:solution`** - 啟動解決方案階段
5. **`/bmad:implement`** - 啟動實施階段
6. **`/bmad:create-agent`** - 創建新代理
7. **`/bmad:create-workflow`** - 創建新工作流
8. **`/bmad:brainstorm`** - 啟動創意思維會議

## 🎯 使用示例

### 示例 1：啟動新項目

```
/workflow-init
```

### 示例 2：創建自定義代理

```
/bmad:create-agent
```

## 🔧 配置和自定義

### 修改代理

您可以通過編輯以下文件來自定義代理：

```
bmad/_cfg/agents/
```

這些自定義將在更新中保留。

### 多語言支持

BMAD 支持獨立的多語言設置：
- 溝通語言
- 輸出語言

配置位於：`bmad/_cfg/`

## 📖 進一步閱讀

- [完整文檔](./bmad/docs/)
- [BMM 模塊](./bmad/bmm/README.md)
- [BMB 模塊](./bmad/bmb/README.md)
- [CIS 模塊](./bmad/cis/README.md)
- [BMAD-METHOD 官方 README](./BMAD-METHOD/README.md)

## 💡 提示

1. **首次使用**：運行 `/workflow-init` 開始
2. **項目類型**：BMAD 會根據項目類型（Web、移動、嵌入式、遊戲）調整文檔
3. **規模自適應**：從快速修復（Level 0）到企業級項目（Level 4）
4. **持續更新**：您的自定義配置在所有更新中都會保留

## 🆘 故障排除

### 常見問題

**Q: `/workflow-init` 命令不工作？**
A: 確保 BMAD 已正確安裝（檢查 bmad/ 目錄是否存在）

**Q: 找不到代理？**
A: 運行：`node BMAD-METHOD/tools/cli/bmad-cli.js build --all --force`

**Q: 如何更新 BMAD？**
A: 運行：`npx bmad-method@alpha update`

### 獲取幫助

- 完整的安裝日誌：查看安裝過程
- CLI 工具：`node BMAD-METHOD/tools/cli/bmad-cli.js --help`
- 狀態檢查：`node BMAD-METHOD/tools/cli/bmad-cli.js status`

## ✅ 安裝完成檢查清單

- [x] Node.js v20+ 安裝 ✓
- [x] BMAD-METHOD 依賴安裝 ✓
- [x] 核心模塊複製 ✓
- [x] 代理文件編譯 ✓
- [x] .claude 配置 ✓
- [x] 文檔生成 ✓

---

**🎉 恭喜！BMAD-METHOD 已成功安裝並可以使用！**

開始使用：在 Claude 中輸入 `/workflow-init`
