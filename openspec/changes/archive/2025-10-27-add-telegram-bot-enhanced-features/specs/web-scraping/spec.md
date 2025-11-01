## ADDED Requirements

### Requirement: System MUST scrape TFT rankings
用戶可以使用 `/tft` 命令爬取TFT Academy網站的排行榜信息。

#### Scenario: 爬取TFT排行榜
- **WHEN** 用戶執行 `/tft` 命令
- **THEN** 系統爬取 https://tftacademy.com/tierlist/comps 並返回：
  - 當前強勢陣容列表
  - 陣容評級（S/A/B/C等）
  - 陣容關鍵英雄
  - 推薦裝備

#### Scenario: 爬取成功
- **WHEN** 網站可訪問且數據正常時
- **THEN** 系統成功獲取數據並格式化顯示

#### Scenario: 網站無法訪問
- **WHEN** 目標網站無法訪問或超時
- **THEN** 系統返回錯誤消息，提示網站不可用

### Requirement: System MUST integrate Chrome MCP
系統必須使用Chrome MCP Server進行網頁爬取。

#### Scenario: 初始化Chrome MCP
- **WHEN** 系統首次使用爬蟲功能時
- **THEN** 系統啟動Chrome MCP連接

#### Scenario: 執行爬蟲操作
- **WHEN** 需要爬取網頁時
- **THEN** 系統通過Chrome MCP控制瀏覽器並執行以下操作：
  - 打開目標網址
  - 等待頁面加載
  - 提取所需數據
  - 關閉瀏覽器

### Requirement: System MUST parse and format data
爬取的數據必須經過解析和格式化。

#### Scenario: 解析陣容數據
- **WHEN** 獲取網頁內容後
- **THEN** 系統解析以下信息：
  - 陣容名稱
  - 評級等級
  - 英雄列表
  - 裝備推薦
  - 勝率（如有）

#### Scenario: 格式化顯示
- **WHEN** 顯示爬取結果時
- **THEN** 系統使用以下格式：
  - 🎮 遊戲表情符號
  - 陣容名稱（加粗）
  - 評級（使用emoji：⭐️）
  - 英雄列表（每行一個）
  - 推薦裝備（如果有）

### Requirement: System MUST process images
系統可以獲取並發送網頁截圖。

#### Scenario: 截取網頁截圖
- **WHEN** 用戶執行 `/tft screenshot`
- **THEN** 系統截取目標網頁的截圖並發送給用戶

#### Scenario: 選擇性截圖
- **WHEN** 用戶指定截圖區域時
- **THEN** 系統只截取指定的網頁區域

### Requirement: System MUST handle errors和重試
爬蟲功能必須具備完善的錯誤處理機制。

#### Scenario: 頁面加載超時
- **WHEN** 頁面加載超時（45秒）時
- **THEN** 系統記錄錯誤並返回超時提示

#### Scenario: 數據提取失敗
- **WHEN** 網頁結構變更導致數據提取失敗時
- **THEN** 系統返回錯誤消息並提示可能需要更新爬蟲邏輯

#### Scenario: 自動重試
- **WHEN** 爬取失敗時
- **THEN** 系統自動重試最多3次，每次間隔5秒

### Requirement: System MUST implement caching
為提高效率，系統實施數據緩存。

#### Scenario: 緩存爬取結果
- **WHEN** 成功爬取數據後
- **THEN** 系統將結果緩存30分鐘

#### Scenario: 使用緩存數據
- **WHEN** 30分鐘內再次請求相同數據時
- **THEN** 系統直接返回緩存的數據，不重新爬取

### Requirement: System MUST validate data
爬取的數據必須經過驗證以確保準確性。

#### Scenario: 驗證數據完整性
- **WHEN** 解析爬取的數據時
- **THEN** 系統檢查必要字段是否存在：
  - 陣容名稱
  - 評級
  - 至少一個英雄

#### Scenario: 標記可疑數據
- **WHEN** 數據不完整或格式異常時
- **THEN** 系統在結果中標記數據可能不準確

### Requirement: System MUST optimize performance
爬蟲功能必須優化性能以提供快速響應。

#### Scenario: 異步執行
- **WHEN** 用戶執行爬蟲命令時
- **THEN** 系統異步執行爬取操作，避免阻塞主線程

#### Scenario: 資源管理
- **WHEN** 爬取完成或失敗時
- **THEN** 系統立即釋放Chrome MCP資源

### Requirement: System MUST check user permissions
爬蟲功能可能需要特定權限。

#### Scenario: 白名單檢查
- **WHEN** 用戶嘗試使用爬蟲功能時
- **THEN** 系統檢查用戶是否在白名單中（如果已配置）

#### Scenario: 記錄使用日誌
- **WHEN** 用戶使用爬蟲功能時
- **THEN** 系統記錄使用日誌，包括用戶ID、時間和操作
