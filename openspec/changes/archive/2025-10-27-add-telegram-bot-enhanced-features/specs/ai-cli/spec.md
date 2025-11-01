## ADDED Requirements

### Requirement: System MUST provide AI CLI command
用戶可以使用 `/ai` 命令直接調用Claude Code API，並獲得限制在100字內的回答。

#### Scenario: 調用AI回答
- **WHEN** 用戶執行 `/ai 什麼是量化交易？`
- **THEN** 系統調用Claude Code API並返回100字內的簡潔回答

#### Scenario: 調用Claude Code
- **WHEN** 用戶執行 `/ai CLAUDE CODE 分析0700.HK的技術指標`
- **THEN** 系統調用Claude Code並返回分析結果（100字內）

#### Scenario: 處理空查詢
- **WHEN** 用戶執行 `/ai` 但沒有提供查詢內容
- **THEN** 系統返回使用說明，提示用戶輸入問題

### Requirement: System MUST enforce word count limit
AI回答必須嚴格限制在100字內。

#### Scenario: 截斷超長回答
- **WHEN** AI返回的回答超過100字
- **THEN** 系統自動截斷到100字並添加"..."表示省略

#### Scenario: 精確計算字數
- **WHEN** 計算字數時
- **THEN** 系統按中文字符計算，英文單詞按字母數計算

### Requirement: System MUST integrate AI API
系統必須能夠調用Claude Code API或其他AI服務。

#### Scenario: 配置API密鑰
- **WHEN** 系統啟動時
- **THEN** 系統從環境變量讀取AI_API_KEY

#### Scenario: 調用外部API
- **WHEN** 用戶提出AI查詢時
- **THEN** 系統向配置的AI服務發送請求

### Requirement: System MUST format responses
AI回答必須以清晰的格式呈現給用戶。

#### Scenario: 格式化回答
- **WHEN** 返回AI回答時
- **THEN** 系統使用以下格式：
  - 🤖 AI回答表情符號
  - 回答內容（100字內）
  - 字數統計標記

#### Scenario: 多輪對話支持
- **WHEN** 用戶連續提問時
- **THEN** 系統保持上下文，提供相關的回答

### Requirement: System MUST classify queries
系統能夠識別不同類型的查詢並採取相應行動。

#### Scenario: 識別Claude Code命令
- **WHEN** 用戶查詢包含 "CLAUDE CODE" 時
- **THEN** 系統將其標記為代碼分析類查詢

#### Scenario: 識別常規問題
- **WHEN** 用戶查詢不包含特殊關鍵字時
- **THEN** 系統將其作為常規知識問題處理

### Requirement: System MUST handle errors
AI CLI必須妥善處理各種錯誤情況。

#### Scenario: API密鑰缺失
- **WHEN** 系統沒有配置AI_API_KEY
- **THEN** 系統返回錯誤消息，提示用戶配置API密鑰

#### Scenario: API調用超時
- **WHEN** AI API調用超時時
- **THEN** 系統返回錯誤消息並建議用戶稍後重試

#### Scenario: API返回錯誤
- **WHEN** AI API返回錯誤響應時
- **THEN** 系統記錄錯誤並向用戶返回友好的錯誤消息

### Requirement: System MUST enforce rate limits
系統實施速率限制以防止API濫用。

#### Scenario: 限制查詢頻率
- **WHEN** 用戶在1分鐘內發送超過10個AI查詢
- **THEN** 系統返回速率限制提示，建議用戶稍後重試

#### Scenario: 重置計數器
- **WHEN** 1分鐘時間窗口結束時
- **THEN** 系統重置速率限制計數器

### Requirement: System MUST support context
系統可以處理多輪對話上下文。

#### Scenario: 保存對話歷史
- **WHEN** 用戶進行多輪AI對話時
- **THEN** 系統在會話中保存最近的對話歷史

#### Scenario: 使用上下文回答
- **WHEN** 用戶基於之前的問題繼續提問時
- **THEN** 系統結合上下文提供更準確的回答

### Requirement: System MUST support special commands
系統支持預定義的特殊AI命令。

#### Scenario: 執行代碼分析
- **WHEN** 用戶執行 `/ai code 分析 <股票代碼>`
- **THEN** 系統調用代碼分析功能並返回結果

#### Scenario: 生成交易策略
- **WHEN** 用戶執行 `/ai strategy <股票代碼>`
- **THEN** 系統生成簡化的交易策略建議（100字內）
