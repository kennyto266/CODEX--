# 命令簡化規格說明

**規格ID**: command-simplification-v1
**版本**: 1.0.0
**最後更新**: 2025-10-28

## 📋 規格概述

本規格說明定義了Telegram Bot命令簡化的具體要求，旨在移除使用率低、價值有限的命令，並重新組織幫助文檔以提升用戶體驗。

## 🎯 改進目標

### 主要目標
1. 將命令數量從22個減少至18個
2. 移除用戶反饋為"無用"的命令
3. 重新組織幫助文檔結構
4. 簡化命令描述文字

### 成功標準
- 命令數量減少18%
- 幫助文檔長度減少40%
- 用戶查找命令時間減少50%
- 新用戶上手時間 < 5分鐘

## ADDED/MODIFIED/REMOVED Requirements

### REMOVED Requirements

#### R-CMD-001: 移除 `/id` 命令
**描述**: The system MUST The system SHALL 完全移除 `/id` 命令及其所有相關功能

**移除內容**:
- `id_cmd()` 函數 (`src/telegram_bot/telegram_quant_bot.py:1370`)
- `/id` 命令處理器 (`build_app()` 函數中)
- 命令註冊 (`BotCommand("id", ...)`)

**驗收條件**:
- [ ] `/id` 命令不再出現在命令列表中
- [ ] `/id` 命令執行返回"未知指令"
- [ ] help文檔中不再包含此命令

**Scenario: 用戶嘗試使用已移除的 /id 命令**
```
用戶輸入: /id
系統回應: 未知指令。使用 /help 查看可用指令。
```

#### R-CMD-002: 移除 `/echo` 命令
**描述**: The system MUST The system SHALL 移除 `/echo` 命令，保留echo_message自動回聲功能

**移除內容**:
- `echo_cmd()` 函數 (`src/telegram_bot/telegram_quant_bot.py:997`)
- `/echo` 命令處理器
- `/echo` 命令註冊

**保留內容**:
- `echo_message()` - 私聊自動回聲功能
- `/echo` 命令處理器之外的文本處理

**驗收條件**:
- [ ] `/echo` 命令執行返回"未知指令"
- [ ] 私聊中發送文字仍會自動回聲
- [ ] help文檔中不再包含此命令

**Scenario: 用戶使用已移除的 /echo 命令**
```
用戶輸入: /echo hello world
系統回應: 未知指令。使用 /help 查看可用指令。
```

**Scenario: 私聊中文字自動回聲**
```
用戶輸入: hello world
系統回應: hello world
```

#### R-CMD-003: 移除 `/history` 命令
**描述**: The system MUST The system SHALL 完全移除 `/history` 命令

**移除內容**:
- `history_cmd()` 函數 (`src/telegram_bot/telegram_quant_bot.py:1071`)
- `/history` 命令處理器
- `/history` 命令註冊
- 最近消息記錄功能（可選）

**驗收條件**:
- [ ] `/history` 命令不再出現在命令列表中
- [ ] `/history` 命令執行返回"未知指令"
- [ ] help文檔中不再包含此命令

**Scenario: 用戶嘗試查看歷史**
```
用戶輸入: /history 10
系統回應: 未知指令。使用 /help 查看可用指令。
```

### MODIFIED Requirements

#### M-CMD-004: 重構幫助文檔
**描述**: The system MUST The system SHALL 重新設計 `build_help_text()` 函數，精簡內容並重新分類

**修改位置**: `src/telegram_bot/telegram_quant_bot.py:321`

**新結構**:
```
🤖 量化交易系統Bot - 幫助

📊 功能分類：
1. 量化交易 (/analyze, /optimize, /risk, /sentiment)
2. 投資管理 (/portfolio, /alert, /heatmap)
3. 體育比分 (/score, /schedule, /favorite)
4. 生活服務 (/weather, /mark6)
5. AI助手 (/ai)
6. 系統功能 (/start, /help, /status)

💡 常用示例：
/analyze 0700.HK
/score nba
/weather
/mark6

查看詳細說明請使用 /help <功能名稱>
```

**驗收條件**:
- [ ] 幫助文檔長度 < 250 行 (原410行)
- [ ] 命令按功能分類清晰
- [ ] 每個分類的命令數量合理 (1-6個)
- [ ] 提供常用示例

**Scenario: 用戶查看幫助**
```
用戶輸入: /help
系統回應: 結構化的幫助文檔，包含6大功能分類
```

**Scenario: 用戶查看特定功能幫助**
```
用戶輸入: /help sports
系統回應: 體育比分功能詳細說明
```

#### M-CMD-005: 精簡命令註冊列表
**描述**: The system MUST The system SHALL 更新 `post_init()` 函數中的命令註冊列表

**修改位置**: `src/telegram_bot/telegram_quant_bot.py:1628`

**新命令列表** (18個):
```
BotCommand("start", "問候與簡介")
BotCommand("help", "顯示幫助")
BotCommand("analyze", "股票技術分析")
BotCommand("optimize", "策略參數優化")
BotCommand("risk", "風險評估")
BotCommand("sentiment", "市場情緒分析")
BotCommand("portfolio", "投資組合管理")
BotCommand("alert", "價格警報管理")
BotCommand("heatmap", "股票熱力圖分析")
BotCommand("score", "體育比分")
BotCommand("schedule", "體育賽程")
BotCommand("favorite", "收藏球隊")
BotCommand("weather", "香港天氣")
BotCommand("mark6", "六合彩資訊")  [新]
BotCommand("ai", "AI問答助手")
BotCommand("summary", "總結消息(需API)")
BotCommand("cursor", "調用Cursor(需白名單)")
BotCommand("wsl", "WSL執行(需白名單)")
```

**驗收條件**:
- [ ] 命令總數為18個
- [ ] 每個命令的描述 < 15字
- [ ] 命令描述清晰準確

#### M-CMD-006: 移除自動回復標籤功能
**描述**: The system MUST The system SHALL 評估並決定是否保留 `@penguin8n` 自動回復功能

**當前實現**: `src/telegram_bot/telegram_quant_bot.py:1003`

**決策標準**:
- 使用率 < 5% - 移除
- 使用率 >= 5% - 保留但優化

**驗收條件**:
- [ ] 若保留：回應時間 < 1秒
- [ ] 若移除：清理相關代碼和幫助文檔

## 🔍 測試需求

### 單元測試

#### T-CMD-001: 測試命令移除
```python
def test_removed_commands():
    """測試已移除命令返回錯誤"""
    app = build_app(test_token)

    # 測試 /id 命令
    assert "id" not in app.commands

    # 測試 /echo 命令
    assert "echo" not in app.commands

    # 測試 /history 命令
    assert "history" not in app.commands
```

#### T-CMD-002: 測試幫助文檔
```python
def test_help_text_content():
    """測試幫助文檔內容正確"""
    help_text = build_help_text()

    # 檢查移除的命令不在幫助中
    assert "/id" not in help_text
    assert "/echo" not in help_text
    assert "/history" not in help_text

    # 檢查新分類存在
    assert "量化交易" in help_text
    assert "投資管理" in help_text
    assert "生活服務" in help_text
```

#### T-CMD-003: 測試命令統計
```python
def test_command_count():
    """測試命令總數"""
    app = build_app(test_token)
    assert len(app.commands) == 18
```

### 集成測試

#### T-CMD-004: 端到端測試
```python
async def test_all_commands_work():
    """測試所有18個命令可正常執行"""
    commands = ["start", "help", "analyze", ...]  # 18個命令

    for cmd in commands:
        response = await bot_test.send_command(cmd)
        assert response.status_code != 404
```

## 📊 性能需求

### 性能指標
- **幫助文檔加載時間**: < 500ms
- **命令解析時間**: < 100ms
- **幫助文檔大小**: < 10KB

### 監控指標
```python
COMMAND_METRICS = {
    "help_view_count": "幫助查看次數",
    "most_used_commands": "最常用命令TOP10",
    "unused_commands": "未使用命令列表",
    "command_error_rate": "命令錯誤率",
}
```

## 🔄 向下兼容

### 遷移策略
1. **通知期**: 提前1週通知用戶
2. **緩衝期**: 舊命令返回"已棄用"而非"未知"
3. **最終移除**: 緩衝期後完全移除

### 用戶遷移示例
```
第一週: /id → "⚠️ 此命令已棄用，請使用 /help 查看可用命令"
第二週: /id → "❌ 未知指令。使用 /help 查看可用指令。"
```

## 📝 實施檢查清單

- [ ] R-CMD-001: 移除 `/id` 命令
- [ ] R-CMD-002: 移除 `/echo` 命令
- [ ] R-CMD-003: 移除 `/history` 命令
- [ ] M-CMD-004: 重構幫助文檔
- [ ] M-CMD-005: 更新命令註冊列表
- [ ] M-CMD-006: 評估自動回復功能
- [ ] T-CMD-001: 單元測試
- [ ] T-CMD-002: 集成測試
- [ ] 性能測試
- [ ] 文檔更新
- [ ] 部署檢查

---

**規格作者**: Claude Code
**審核狀態**: 待審核
**優先級**: 高
**估計工期**: 3天
