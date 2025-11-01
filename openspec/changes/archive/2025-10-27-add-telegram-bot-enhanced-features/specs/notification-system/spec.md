## ADDED Requirements

### Requirement: System MUST set price alerts
用戶可以使用 `/alert` 命令設置價格警報，監控特定股票的價格變化。

#### Scenario: 設置價格上漲警報
- **WHEN** 用戶執行 `/alert 0700.HK above 400.0`
- **THEN** 系統創建警報：當0700.HK價格高於400.0時通知用戶

#### Scenario: 設置價格下跌警報
- **WHEN** 用戶執行 `/alert 0700.HK below 300.0`
- **THEN** 系統創建警報：當0700.HK價格低於300.0時通知用戶

#### Scenario: 設置百分比變化警報
- **WHEN** 用戶執行 `/alert 0700.HK change +5%`
- **THEN** 系統創建警報：當0700.HK漲幅超過5%時通知用戶

### Requirement: System MUST view alert list
用戶可以查看所有設置的價格警報。

#### Scenario: 查看警報列表
- **WHEN** 用戶執行 `/alert list`
- **THEN** 系統顯示所有警報，包括：
  - 股票代碼
  - 警報條件
  - 創建時間
  - 狀態（啟用/禁用）

#### Scenario: 空警報列表
- **WHEN** 用戶執行 `/alert list` 但沒有設置任何警報
- **THEN** 系統顯示提示信息，建議用戶設置警報

### Requirement: System MUST delete alerts
用戶可以刪除不需要的價格警報。

#### Scenario: 刪除指定警報
- **WHEN** 用戶執行 `/alert delete <警報ID>`
- **THEN** 系統刪除指定的警報

#### Scenario: 刪除所有警報
- **WHEN** 用戶執行 `/alert clear`
- **THEN** 系統刪除用戶的所有警報並確認

### Requirement: System MUST monitor price changes
系統必須定期檢查所有啟用的警報，監控價格變化。

#### Scenario: 定期檢查價格
- **WHEN** 系統每分鐘執行一次檢查
- **THEN** 系統獲取所有監控股票的當前價格

#### Scenario: 觸發警報條件
- **WHEN** 股票價格滿足警報條件
- **THEN** 系統立即向用戶發送通知消息

### Requirement: System MUST format alert notifications
警報通知必須清晰、易讀，包含關鍵信息。

#### Scenario: 價格上漲通知
- **WHEN** 觸發上漲警報時
- **THEN** 系統發送包含以下內容的通知：
  - 📈 表情符號
  - 股票代碼和名稱
  - 當前價格
  - 警報閾值
  - 漲幅百分比

#### Scenario: 價格下跌通知
- **WHEN** 觸發下跌警報時
- **THEN** 系統發送包含以下內容的通知：
  - 📉 表情符號
  - 股票代碼和名稱
  - 當前價格
  - 警報閾值
  - 跌幅百分比

### Requirement: System MUST persist alerts
警報數據必須持久化存儲，以便Bot重啟後不丟失。

#### Scenario: 保存警報到文件
- **WHEN** 用戶創建或修改警報時
- **THEN** 系統將警報數據保存到文件或數據庫

#### Scenario: 恢復警報
- **WHEN** Bot啟動時
- **THEN** 系統從持久化存儲中恢復所有警報

### Requirement: System MUST manage alert status
用戶可以啟用或禁用警報。

#### Scenario: 禁用警報
- **WHEN** 用戶執行 `/alert disable <警報ID>`
- **THEN** 系統將警報標記為禁用狀態，暫停監控

#### Scenario: 啟用警報
- **WHEN** 用戶執行 `/alert enable <警報ID>`
- **THEN** 系統將警報標記為啟用狀態，恢復監控

### Requirement: System MUST limit alert frequency
為了避免過度通知，系統實施警報頻率限制。

#### Scenario: 相同警報冷卻期
- **WHEN** 同一警報在30分鐘內多次觸發
- **THEN** 系統只發送一次通知，後續通知被暫停

#### Scenario: 恢復通知
- **WHEN** 警報條件不再滿足後重新滿足
- **THEN** 系統恢復正常通知機制

### Requirement: System MUST handle errors
警報系統必須妥善處理各種錯誤情況。

#### Scenario: 股票代碼無效
- **WHEN** 用戶為不存在的股票設置警報
- **THEN** 系統返回錯誤消息，提示股票代碼無效

#### Scenario: API調用失敗
- **WHEN** 獲取股價失敗時
- **THEN** 系統記錄錯誤並在下次循環時重試，不中斷其他警報的監控
