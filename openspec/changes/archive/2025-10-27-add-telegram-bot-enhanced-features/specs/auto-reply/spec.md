## ADDED Requirements

### Requirement: System MUST detect auto tags
Bot必須能夠檢測到有人標記用戶名稱@penguin8n，並自動回復。

#### Scenario: 檢測到@penguin8n標籤
- **WHEN** 用戶在群組或頻道中發送包含@penguin8n的消息
- **THEN** Bot檢測到該標籤並觸發自動回復流程

#### Scenario: 私聊中的自動回復
- **WHEN** 用戶在私聊中提到penguin8n（無@符號）
- **THEN** Bot檢測到該用戶名並自動回復

#### Scenario: 忽略其他用戶名
- **WHEN** 用戶標記其他用戶名（如@otheruser）時
- **THEN** Bot不觸發自動回復功能

### Requirement: System MUST send AI agent reply
當檢測到標籤時，Bot必須自動回復AI代理消息。

#### Scenario: 發送AI代理回覆
- **WHEN** 檢測到@penguin8n標籤時
- **THEN** Bot自動發送以下消息：
  - "🤖 您好！我是AI代理助手。"
  - "penguin8n 目前不在，我將代為轉達您的消息。"
  - "請告訴我您需要什麼幫助？"

#### Scenario: 使用表情符號
- **WHEN** 發送自動回覆時
- **THEN** Bot使用適當的AI相關表情符號：
  - 🤖 機器人
  - 💬 聊天氣泡
  - ✉️ 信封
  - ⏰ 時鐘

### Requirement: System MUST check username whitelist
自動回復功能支持配置用戶名白名單。

#### Scenario: 默認白名單
- **WHEN** 系統啟動時
- **THEN** 默認白名單包含：penguin8n

#### Scenario: 自定義白名單
- **WHEN** 配置環境變量 TG_AUTO_REPLY_USERS 時
- **THEN** 系統使用配置的自定義白名單

### Requirement: System MUST understand context intelligently
Bot可以根據消息上下文提供更相關的回復。

#### Scenario: 理解問題類型
- **WHEN** 用戶標記@penguin8n並提出問題時
- **THEN** Bot分析問題類型並提供相應的自動回復：
  - 技術問題 → "AI代理：技術問題已記錄，我會轉達。"
  - 交易問題 → "AI代理：交易相關問題已記錄。"
  - 一般詢問 → "AI代理：一般詢問已記錄。"

#### Scenario: 提取關鍵信息
- **WHEN** 自動回復時
- **THEN** Bot嘗試提取消息中的關鍵信息並包含在回覆中

### Requirement: System MUST enforce frequency limits
為防止垃圾信息，系統實施自動回復頻率限制。

#### Scenario: 同一用戶冷卻期
- **WHEN** 同一用戶在5分鐘內多次標記@penguin8n時
- **THEN** Bot只回復第一次，後續標記被忽略

#### Scenario: 群組頻率限制
- **WHEN** 同一群組中5分鐘內有多人標記@penguin8n時
- **THEN** Bot只回復第一次標記

### Requirement: System MUST handle special groups
系統可以根據群組類型調整自動回復行為。

#### Scenario: 私人群組
- **WHEN** 在私人群組中檢測到標籤時
- **THEN** Bot正常執行自動回復

#### Scenario: 公開頻道
- **WHEN** 在公開頻道中檢測到標籤時
- **THEN** Bot自動回復並標記為公開回復

#### Scenario: 忽略的群組
- **WHEN** 在配置為忽略的群組中檢測到標籤時
- **THEN** Bot不執行自動回復

### Requirement: System MUST provide contact information
自動回復中可以包含聯繫方式或替代溝通渠道。

#### Scenario: 提供聯繫方式
- **WHEN** 發送自動回覆時
- **THEN** Bot可以包含以下信息：
  - "您也可以通過以下方式聯繫："
  - "📧 郵箱：..."
  - "📱 Telegram：..."
  - "🌐 網站：..."

#### Scenario: 智能回覆模板
- **WHEN** 根據消息內容選擇回覆模板時
- **THEN** Bot使用以下模板之一：
  - 一般詢問模板
  - 緊急事務模板
  - 技術支持模板
  - 商務合作模板

### Requirement: System MUST handle errors
自動回復功能必須妥善處理各種錯誤情況。

#### Scenario: 消息發送失敗
- **WHEN** 自動回復消息發送失敗時
- **THEN** Bot記錄錯誤並嘗試重新發送（最多3次）

#### Scenario: 無效用戶名
- **WHEN** 檢測到無效的用戶名格式時
- **THEN** Bot忽略該消息並記錄日誌

#### Scenario: 權限不足
- **WHEN** Bot沒有權限在群組中回復時
- **THEN** Bot記錄錯誤但不中斷正常運行

### Requirement: System MUST learn and optimize
Bot可以學習用戶的回復偏好並優化自動回復。

#### Scenario: 記錄回復統計
- **WHEN** 執行自動回復時
- **THEN** Bot記錄以下統計信息：
  - 回復次數
  - 用戶反饋
  - 群組活動度

#### Scenario: 優化回覆內容
- **WHEN** 累積足夠的數據時
- **THEN** Bot可以調整自動回覆內容以提高用戶滿意度

### Requirement: System MUST control enable/disable
用戶可以控制自動回復功能的開啟和關閉。

#### Scenario: 禁用自動回復
- **WHEN** 用戶執行 `/autoreply off` 命令時
- **THEN** Bot停止自動回復功能

#### Scenario: 啟用自動回復
- **WHEN** 用戶執行 `/autoreply on` 命令時
- **THEN** Bot恢復自動回復功能

#### Scenario: 查詢狀態
- **WHEN** 用戶執行 `/autoreply status` 命令時
- **THEN** Bot返回自動回復功能的當前狀態（啟用/禁用）
