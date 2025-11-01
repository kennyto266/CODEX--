## Why

當前的Telegram Bot功能已相當完善（14個命令），但用戶希望增加更多實用功能，特別是：
1. 投資組合管理功能，讓用戶能查看和管理自己的投資組合
2. 進階分析工具（熱力圖、可視化）
3. 智能通知系統（價格警報）
4. AI交互功能（直接調用Claude Code）
5. Web爬蟲功能（TFT排行榜）
6. 生活服務功能（香港天氣）
7. 自動回復功能（AI代理模式）

這些功能將極大提升Bot的實用性和用戶體驗。

## What Changes

### 新增的命令功能 (7個)
- `/portfolio` - 投資組合查看和管理
- `/heatmap` - 股票熱力圖分析
- `/alert` - 設置價格警報
- `/ai` - AI CLI命令（調用Claude Code，限制100字回應）
- `/tft` - 爬取TFT排行榜（使用Chrome MCP）
- `/weather` - 香港天氣查詢（對接香港天文台）
- 自動回復 - 檢測@penguin8n並自動回覆AI代理消息

### 增強現有功能
- 改進消息處理邏輯，支持引用回復和標籤檢測
- 增強錯誤處理和日誌記錄
- 添加新命令到/help文本和BotCommand列表

### 新增依賴
- Chrome MCP Server（用於網頁爬蟲）
- 香港天文台API或爬蟲

## Impact

### 受影響的規格
- `specs/telegram-bot` - 核心Bot功能擴展
- `specs/portfolio-management` - 新增投資組合管理
- `specs/analysis-features` - 新增分析工具
- `specs/notification-system` - 新增通知系統
- `specs/ai-cli` - 新增AI CLI
- `specs/web-scraping` - 新增網頁爬蟲
- `specs/weather-service` - 新增天氣服務
- `specs/auto-reply` - 新增自動回復

### 受影響的代碼
- `src/telegram_bot/telegram_quant_bot.py` - 主要Bot實現
- `src/telegram_bot/` - 新增模組文件
- `requirements.txt` - 新增依賴
- 配置文件更新

### 風險評估
- **低風險**: 新功能採用可選依賴，不影響現有功能
- **中風險**: Chrome MCP需要額外配置，可能增加系統複雜度
- **低風險**: 自動回復可能誤觸發，需要精確的用戶名檢測

### 向後兼容性
- 所有現有功能保持不變
- 新功能為增量添加
- 現有配置文件無需修改（除非使用新功能）
