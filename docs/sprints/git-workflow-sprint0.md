# Git 工作流程配置文檔
## Sprint 0 - US-002 Task 2.3

### 目錄
1. [Git Flow 工作流程](#git-flow-工作流程)
2. [分支管理](#分支管理)
3. [提交規範](#提交規範)
4. [Pull Request 流程](#pull-request-流程)
5. [分支保護規則](#分支保護規則)
6. [工具配置](#工具配置)

---

## Git Flow 工作流程

### 核心分支
```
main                    # 生產分支 - 穩定版本
├── develop             # 開發分支 - 集成所有功能
    ├── feature/*       # 功能分支 - 開發新功能
    ├── bugfix/*        # 修復分支 - 修復Bug
    ├── hotfix/*        # 緊急修復分支 - 生產環境緊急修復
    └── release/*       # 發布分支 - 準備發布版本
```

### 分支命名規範

#### 功能分支 (Feature)
```
feature/US-XXX-功能描述
feature/US-002-5層架構重構
feature/US-003-HKMA數據適配器
feature/US-004-宏觀指標服務
```

#### 修復分支 (Bugfix)
```
bugfix/BUG-XXX-問題描述
bugfix/BUG-001-修復InfluxDB配置錯誤
```

#### 緊急修復分支 (Hotfix)
```
hotfix/HOTFIX-XXX-緊急修復描述
hotfix/HOTFIX-001-生產環境數據庫連接失敗
```

#### 發布分支 (Release)
```
release/vX.Y.Z
release/v1.0.0
```

---

## 分支管理

### 1. 創建功能分支

```bash
# 從 develop 創建新功能分支
git checkout develop
git pull origin develop
git checkout -b feature/US-XXX-功能描述

# 推送分支到遠程
git push -u origin feature/US-XXX-功能描述
```

### 2. 同步更新

```bash
# 定期同步 develop 分支
git checkout develop
git pull origin develop
git checkout feature/US-XXX-功能描述
git rebase develop

# 如果有衝突
git add .
git rebase --continue
# 解決衝突後繼續...
git push origin feature/US-XXX-功能描述 --force
```

### 3. 完成功能分支

```bash
# 合併到 develop
git checkout develop
git pull origin develop
git merge --no-ff feature/US-XXX-功能描述
git push origin develop

# 刪除本地分支
git branch -d feature/US-XXX-功能描述

# 刪除遠程分支
git push origin --delete feature/US-XXX-功能描述
```

---

## 提交規範

### Conventional Commits 標準

#### 格式
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### 類型 (Type)
- **feat**: 新功能 (US-XXX)
- **fix**: 修復Bug
- **docs**: 文檔更新
- **style**: 代碼格式 (不影響代碼運行的變動)
- **refactor**: 重構 (既不是新功能，也不是修復Bug的代碼變動)
- **perf**: 性能優化
- **test**: 添加測試
- **chore**: 建構過程或輔助工具的變動
- **build**: 構建系統或依賴變動
- **ci**: CI配置文件和腳本的變動

#### 示例

```bash
# 新功能
git commit -m "feat(US-002): implement 5-layer architecture interfaces"

# 修復Bug
git commit -m "fix(US-001): resolve InfluxDB volume mount error"

# 文檔更新
git commit -m "docs: update Sprint 0 requirements documentation"

# 重構
git commit -m "refactor(data-adapter): simplify HKMA adapter interface"

# 測試
git commit -m "test: add unit tests for repository pattern"

# 多個變更
git commit -m "feat(US-003): add HKMA data adapter

- Implement IHKMAAdapter interface
- Add HIBOR rate fetching methods
- Integrate with docker-compose InfluxDB
- Add validation for time-series data

Closes #123"
```

#### 工作流

```bash
# 1. 編輯代碼
vim src/core/interfaces/repository.py

# 2. 檢查變更
git status
git diff

# 3. 添加到暫存區
git add src/core/interfaces/repository.py

# 4. 提交 (使用互動式提交)
git commit

# 或直接提交
git commit -m "feat(US-002): add IRepository interface with CRUD operations"
```

---

## Pull Request 流程

### 1. 創建 PR

```bash
# 完成功能開發後，創建 Pull Request
# 在 GitHub/GitLab 界面操作，或使用 CLI

# gh CLI (GitHub)
gh pr create \
  --title "feat(US-002): Implement 5-layer architecture" \
  --body "## 描述
實現5層架構重構，包括核心接口定義

## 變更清單
- 添加 IRepository 接口
- 添加 IDataAdapter 接口
- 添加 IMacroIndicatorService 接口
- 添加 IStrategyService 接口
- 添加 IRiskService 接口

## 測試
- [ ] 單元測試通過
- [ ] 代碼覆蓋率 > 80%
- [ ] 所有 linting 檢查通過

## 檢查清單
- [ ] 代碼遵循 PEP 8 規範
- [ ] 添加了適當的 docstring
- [ ] 所有新接口已測試
- [ ] 與 develop 分支無衝突
" \
  --base develop \
  --head feature/US-002-5層架構
```

### 2. PR 描述模板

```markdown
## 📋 變更摘要
簡要描述本次 PR 的主要變更

## 🎯 相關 Story
- US-XXX: Story標題

## ✨ 新增功能
- 列出新增功能
- 使用項目符號

## 🐛 修復問題
- 列出修復的Bug
- 引用 Issue 編號

## 📚 文檔更新
- 列出文檔變更
- 更新配置文件

## 🧪 測試
- [ ] 單元測試: xxx
- [ ] 集成測試: xxx
- [ ] 端到端測試: xxx

## 📊 性能影響
- 描述性能變更（如有）

## 🔄 向後兼容性
- [ ] 向後兼容
- [ ] 需要遷移

## 🔍 代碼覆蓋率
- 當前覆蓋率: XX%
- 新增覆蓋率: XX%

## 📝 檢查清單
- [ ] 代碼遵循規範 (black, isort, flake8)
- [ ] 所有測試通過
- [ ] 添加了必要的 docstring
- [ ] 更新了相關文檔
- [ ] 與 develop 分支同步
```

### 3. PR 審查清單

#### 審查者檢查項目

```markdown
## 代碼質量
- [ ] 代碼清晰易懂
- [ ] 遵循單一職責原則
- [ ] 適當的抽象層次
- [ ] 避免重複代碼

## 功能正確性
- [ ] 代碼實現符合需求
- [ ] 邊界情況處理
- [ ] 錯誤處理完善
- [ ] 性能可接受

## 測試覆蓋
- [ ] 添加了適當測試
- [ ] 測試覆蓋率 > 80%
- [ ] 測試名稱清晰
- [ ] 覆蓋關鍵邏輯

## 文檔
- [ ] 添加/更新了 docstring
- [ ] 複雜邏輯有註釋
- [ ] API 文檔完整
- [ ] 變更日誌更新

## 安全性
- [ ] 無安全漏洞
- [ ] 敏感信息處理正確
- [ ] 輸入驗證完善
- [ ] 無硬編碼密鑰

## 架構
- [ ] 遵循5層架構
- [ ] 接口定義合理
- [ ] 依賴關係正確
- [ ] 模塊耦合度低
```

### 4. PR 合併流程

```bash
# 方法1: Merge (保留分支歷史)
git checkout develop
git merge --no-ff feature/US-XXX-功能描述
git push origin develop

# 方法2: Squash and Merge (推薦，保持 develop 整潔)
# 在 GitHub/GitLab 界面操作

# 方法3: Rebase (線性歷史)
git checkout develop
git rebase feature/US-XXX-功能描述
git push --force origin develop
```

---

## 分支保護規則

### main 分支保護
```
保護規則:
- 需要Pull Request審查
- 至少1人審查通過
- 禁止直接推送
- 需要狀態檢查通過
- 要求分支為最新版本
- 必須使用 Squash Merge
```

### develop 分支保護
```
保護規則:
- 需要Pull Request審查
- 至少1人審查通過
- 禁止直接推送
- 需要狀態檢查通過
- 要求分支為最新版本
```

### 設置步驟 (GitHub)

1. **進入 Settings > Branches**
2. **添加保護規則**
   - Branch name pattern: `main`
   - ✅ Require a pull request before merging
   - ✅ Dismiss stale PR approvals when new commits are pushed
   - ✅ Require review from Code Owners
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

3. **設置狀態檢查**
   - CI/CD 檢查
   - 代碼覆蓋率檢查
   - Linting 檢查
   - 測試套件

### 設置步驟 (GitLab)

1. **進入 Settings > Repository**
2. **Protected Branches**
   - Branch: `main`
   - Allowed to merge: Maintainers
   - Allowed to push: No one
   - Allowed to force push: No one

3. **Protected Tags**
   - Tag: `v*`
   - Allowed to create: Maintainers

---

## 工具配置

### 1. 安裝 Git Hooks

```bash
# 安裝 pre-commit
pip install pre-commit

# 配置 .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# 安裝 hooks
pre-commit install
```

### 2. 提交信息驗證

```bash
# 安裝 commitlint
npm install -g @commitlint/cli @commitlint/config-conventional

# 配置 commitlint.config.js
cat > commitlint.config.js << 'EOF'
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'chore', 'build', 'ci']
    ],
    'subject-case': [0]
  }
}
EOF

# 配置 commit-msg hook
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/sh
npx --no-install commitlint --edit $1
EOF
chmod +x .git/hooks/commit-msg
```

### 3. 自動生成變更日誌

```bash
# 安裝 conventional-changelog-cli
npm install -g conventional-changelog-cli

# 配置 CHANGELOG.md 生成
cat > package.json << 'EOF'
{
  "scripts": {
    "changelog": "conventional-changelog -p conventionalcommits -i CHANGELOG.md -s",
    "release": "npm run changelog && git add CHANGELOG.md"
  }
}
EOF

# 生成變更日誌
npm run changelog
```

---

## 快速參考

### 常用命令

```bash
# 創建功能分支
git checkout -b feature/US-XXX-描述 develop

# 檢查狀態
git status
git diff

# 提交代碼
git add .
git commit -m "feat(US-XXX): 描述"

# 推送分支
git push -u origin feature/US-XXX-描述

# 更新分支
git fetch origin
git rebase origin/develop

# 合併到 develop
git checkout develop
git merge --no-ff feature/US-XXX-描述
git push origin develop

# 刪除分支
git branch -d feature/US-XXX-描述
git push origin --delete feature/US-XXX-描述

# 修訂提交
git commit --amend
git push --force-with-lease origin feature/US-XXX-描述
```

### Git Flow 完整流程

```bash
# 1. 開始新功能
git flow feature start US-XXX-描述

# 2. 開發和提交
git add .
git commit -m "feat(US-XXX): 描述"
git push origin feature/US-XXX-描述

# 3. 完成功能
git flow feature finish US-XXX-描述

# 4. 創建 release
git flow release start v1.0.0
# 完成發布準備
git flow release finish v1.0.0

# 5. 緊急修復
git flow hotfix start HOTFIX-XXX
git flow hotfix finish HOTFIX-XXX
```

---

## 審查指南

### PR 審查者職責

1. **及時審查**: 24小時內完成審查
2. **建設性反饋**: 提供具體改進建議
3. **技術準確性**: 驗證代碼邏輯正確性
4. **代碼質量**: 確保符合項目標準
5. **文檔完整性**: 檢查文檔更新

### 審查步驟

1. **閱讀描述**: 了解 PR 目的和範圍
2. **檢查分支**: 確保基於正確分支
3. **驗證測試**: 確保所有測試通過
4. **代碼審查**: 逐行檢查關鍵邏輯
5. **運行測試**: 本地驗證（如需要）
6. **給出反饋**: 使用 GitHub 評論功能
7. **批准合併**: 確認無問題後批准

### 審查評論示例

```markdown
✅ **好的評論**:
"這個接口設計很好，建議將異常處理改為自定義異常類型"

❌ **避免的評論**:
"這個代碼不行，重寫"
```

---

## 故障排除

### 合併衝突

```bash
# 同步最新代碼
git fetch origin
git checkout develop
git pull origin develop

# 切換到功能分支
git checkout feature/US-XXX-描述
git rebase develop

# 解決衝突
git add .
git rebase --continue

# 繼續或跳過
git rebase --skip  # 如果當前提交已被合併

# 推送到遠程
git push --force-with-lease origin feature/US-XXX-描述
```

### 撤銷操作

```bash
# 撤銷最後一次提交（保留更改）
git reset --soft HEAD~1

# 撤銷最後一次提交（丟棄更改）
git reset --hard HEAD~1

# 撤銷已推送的提交
git revert HEAD
git push origin feature/US-XXX-描述

# 清理本地分支
git remote prune origin
```

### 保護規則問題

```bash
# 如果無法推送（分支保護）
git push origin feature/US-XXX-描述  # 會失敗，需要PR

# 如果需要緊急修復
# 1. 聯繫有權限的開發者
# 2. 或使用 hotfix 分支
git flow hotfix start emergency-fix
```

---

## 總結

本工作流程確保：

✅ 代碼質量高
✅ 歷史記錄清晰
✅ 協作效率高
✅ 錯誤風險低
✅ 可追溯性強

遵循此流程，所有開發者都能高效協作，確保代碼庫穩定和可維護性。

---

**文檔版本**: 1.0.0
**更新日期**: 2025-11-05
**維護者**: Sprint 0 團隊
