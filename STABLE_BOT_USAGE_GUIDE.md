# Telegram Bot 穩定版使用指南

## ✅ 當前狀態

**Bot 名稱**: @penguinai_bot
**版本**: `telegram_bot_stable.py` (穩定版)
**狀態**: ✅ 正在運行
**進程狀態**: ✅ 正常運行 (檢測衝突但繼續)
**API 狀態**: ✅ 響應正常

## 🚀 核心功能

### 可用命令

| 命令 | 功能 | 狀態 |
|------|------|------|
| `/start` | 啟動 Bot 並顯示功能列表 | ✅ |
| `/help` | 顯示所有可用命令 | ✅ |
| `/status` | 顯示系統狀態和模塊狀態 | ✅ |
| `/score` | 查看所有體育比分 | ✅ |
| `/score nba` | 查看 NBA 比分 | ✅ |
| `/score soccer` | 查看足球比分 | ✅ |
| `/schedule` | 查看未來賽程 | ✅ |
| `/portfolio` | 投資組合管理 | ✅ |
| `/weather` | 天氣查詢 | ✅ |
| `/weather <地區>` | 指定地區天氣 | ✅ |
| `/mark6` | 彩票開獎查詢 | ✅ |

### 已啟用模塊

- ✅ **體育比分系統** - 支援 NBA、足球等
- ✅ **投資組合管理** - 投資組合查看和管理
- ✅ **警報系統** - 價格警報管理
- ✅ **天氣服務** - 香港天文台數據
- ✅ **彩票服務** - 香港 Mark Six
- ✅ **熱力圖服務** - 港股熱力圖

### 特殊功能

- ✅ **智能降級** - 模塊導入失敗不影響其他功能
- ✅ **衝突處理** - 檢測到衝突時記錄日誌但繼續運行
- ✅ **持續重試** - 自動重試機制（最多 10 次）
- ✅ **優雅錯誤處理** - 不會因錯誤自動停止

## 📊 監控指令

### 檢查運行狀態

```bash
# 查看實時日誌
tail -f bot_stable.log

# 檢查進程
ps aux | grep telegram_bot_stable

# 測試 API
curl -s "https://api.telegram.org/bot7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI/getMe"
```

### 查看模塊狀態

```bash
# 查看最近 50 行日誌
tail -50 bot_stable.log

# 查看啟動時的模塊狀態
grep -E "(Enabled|OK|导入失败)" bot_stable.log | tail -20

# 查看衝突日誌
grep "Conflict" bot_stable.log | tail -10
```

### 清理日誌

```bash
# 備份並清理日誌
cp bot_stable.log bot_stable.log.backup
echo "" > bot_stable.log
```

## 🧪 測試 Bot

### 在 Telegram 中測試

1. **搜索 Bot**: `@penguinai_bot`
2. **發送測試命令**:
   - `/start` - 啟動並查看功能列表
   - `/status` - 查看系統狀態
   - `/score nba` - 查看 NBA 比分
   - `/weather` - 查看天氣
   - `/mark6` - 查看彩票信息

### 自動化測試

```bash
# 模擬發送 /start 命令 (需要 Bot Token)
curl -X POST "https://api.telegram.org/bot7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI/sendMessage" \
  -d chat_id=<YOUR_CHAT_ID> \
  -d text="/start"

# 獲取待處理的更新
curl -s "https://api.telegram.org/bot7180490983:AAFbkKnDPC1MHAaOGzQA1fOs9FBwSGGonzI/getUpdates"
```

## 🔧 維護和重啟

### 如果需要重啟 Bot

```bash
# 終止現有進程 (Windows)
taskkill /F /IM python.exe

# 重新啟動
nohup python telegram_bot_stable.py > STABLE_BOT.log 2>&1 &

# 驗證重啟
tail -f STABLE_BOT.log
```

### 解決衝突問題

穩定版 Bot 會檢測到衝突但繼續運行。如果遇到問題：

1. **檢查日誌**:
   ```bash
   grep "Conflict" bot_stable.log | tail -5
   ```

2. **等待 Telegram 釋放連接** (通常 60-90 秒)
   ```bash
   echo "等待 2 分鐘..."
   sleep 120
   echo "重試連接"
   ```

3. **重新啟動**:
   ```bash
   taskkill /F /IM python.exe
   sleep 10
   nohup python telegram_bot_stable.py > STABLE_BOT.log 2>&1 &
   ```

## 📋 功能示例

### 用戶交互示例

**用戶發送**: `/start`
**Bot 回覆**:
```
Hello [Name]! [OK]

Bot is running with complete features:

• Sports scores (/score, /schedule)
• Portfolio management (/portfolio)
• Weather query (/weather)
• Lottery info (/mark6)

Send /help for all commands
```

**用戶發送**: `/score nba`
**Bot 回覆**:
```
NBA Scores:

• Lakers 102 : 99 Warriors
• Nets 115 : 118 Celtics
```

**用戶發送**: `/status`
**Bot 回覆**:
```
Bot Status:

Quant system: OFF
Sports system: OK
Portfolio: OK
Alert: OK
Weather: OK
Lottery: OK
Heatmap: OK

Uptime: 2025-11-01 07:23:30
```

## ⚠️ 注意事項

### 衝突處理機制

穩定版 Bot 使用**智能衝突處理**：
- 檢測到多實例運行時，記錄日誌但**繼續運行**
- 不會自動停止（與完整版不同）
- 會定期重試連接

### 模塊導入

如果某個模塊導入失敗：
- 該功能會被禁用
- 其他功能繼續正常運行
- `/status` 命令會顯示哪些模塊啟用/禁用

### 性能監控

建議定期監控：
1. **日誌大小**: `ls -lh bot_stable.log`
2. **進程狀態**: `ps aux | grep telegram_bot_stable`
3. **API 響應**: `curl -s "https://api.telegram.org/bot.../getMe"`

## 🎯 最佳實踐

1. **定期備份日誌**: 避免日誌文件過大
2. **監控衝突次數**: 過多衝突可能影響性能
3. **定期測試命令**: 確保所有功能正常
4. **保持更新**: 定期檢查模塊狀態

## 🆘 故障排除

### Bot 無響應

```bash
# 檢查進程
ps aux | grep telegram_bot_stable

# 檢查日誌
tail -20 bot_stable.log

# 重新啟動
python telegram_bot_stable.py
```

### API 錯誤

```bash
# 測試 API
curl -s "https://api.telegram.org/bot.../getMe"

# 檢查 webhook 狀態
curl -s "https://api.telegram.org/bot.../getWebhookInfo"
```

### 模塊導入失敗

檢查 `/status` 命令輸出，看哪些模塊未啟用：
- 如果是依賴問題，需要安裝相應的 Python 模塊
- 如果是路徑問題，檢查 `sys.path` 設置

## 📞 技術支持

如需幫助：
1. 查看日誌: `tail -100 bot_stable.log`
2. 檢查模塊狀態: `/status`
3. 重啟 Bot: `python telegram_bot_stable.py`

---

**最後更新**: 2025-11-01 07:23:30
**狀態**: ✅ 穩定版 Bot 運行正常
**版本**: telegram_bot_stable.py
