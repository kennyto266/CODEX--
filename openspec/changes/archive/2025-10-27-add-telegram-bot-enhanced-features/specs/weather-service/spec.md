## ADDED Requirements

### Requirement: System MUST query Hong Kong weather
用戶可以使用 `/weather` 命令查詢香港的天氣信息。

#### Scenario: 查詢香港天氣
- **WHEN** 用戶執行 `/weather` 命令
- **THEN** 系統返回香港天文台的最新天氣數據，包括：
  - 當前溫度
  - 濕度
  - 風速和風向
  - 天氣狀況（晴/多雲/雨等）
  - 紫外線指數
  - 警報信息（如有）

#### Scenario: 查詢指定地區天氣
- **WHEN** 用戶執行 `/weather <地區名>`
- **THEN** 系統返回指定香港地區的天氣信息（如：香港島、九龍、新界）

### Requirement: System MUST use HKO data source
系統必須從香港天文台獲取準確的天氣數據。

#### Scenario: 訪問天文台API
- **WHEN** 獲取天氣數據時
- **THEN** 系統從香港天文台官方API或網站獲取數據

#### Scenario: 備用數據源
- **WHEN** 天文台API不可用時
- **THEN** 系統使用備用數據源（如openweathermap等）

### Requirement: System MUST format weather data
獲取的天氣數據必須以易讀的格式顯示。

#### Scenario: 格式化天氣信息
- **WHEN** 顯示天氣數據時
- **THEN** 系統使用以下格式：
  - 🌤️ 表情符號表示天氣狀況
  - 地區名稱（加粗）
  - 溫度（攝氏度）
  - 濕度百分比
  - 風速和風向
  - 紫外線指數
  - 警告信息（如適用）

#### Scenario: 溫度單位轉換
- **WHEN** 顯示溫度時
- **THEN** 系統同時顯示攝氏度和華氏度

### Requirement: System MUST send weather icons
系統可以發送天氣圖標或簡圖來直觀顯示天氣。

#### Scenario: 發送天氣圖標
- **WHEN** 獲取天氣數據後
- **THEN** 系統根據天氣狀況發送相應的emoji或圖標

#### Scenario: 生成天氣圖
- **WHEN** 需要更詳細的天氣信息時
- **THEN** 系統生成包含以下內容的天氣圖：
  - 溫度曲線
  - 降雨概率
  - 未來24小時預報

### Requirement: System MUST send weather alerts
系統會主動提醒用戶重要的天氣警報。

#### Scenario: 天氣警報檢查
- **WHEN** 查詢天氣時
- **THEN** 系統檢查是否有以下警報：
  - 颱風警報
  - 暴雨警報
  - 酷熱天氣警告
  - 雷暴警告

#### Scenario: 警報顯示
- **WHEN** 檢測到天氣警報時
- **THEN** 系統使用紅色標記並加粗顯示警報信息

### Requirement: System MUST support multiple regions
系統支持查詢香港不同地區的天氣。

#### Scenario: 支持的地區
- **WHEN** 用戶查詢地區天氣時
- **THEN** 系統支持以下地區：
  - 香港島
  - 九龍
  - 新界
  - 離島
  - 具體地區（如：沙田、荃灣、港島東等）

#### Scenario: 地區名稱模糊匹配
- **WHEN** 用戶輸入的地區名稱不完全匹配時
- **THEN** 系統進行模糊匹配並返回最相似的地區天氣

### Requirement: System MUST query historical weather
系統可以查詢歷史天氣數據。

#### Scenario: 查詢昨日天氣
- **WHEN** 用戶執行 `/weather yesterday`
- **THEN** 系統返回昨日的天氣摘要

#### Scenario: 查詢一週天氣
- **WHEN** 用戶執行 `/weather weekly`
- **THEN** 系統返回未來一週的天氣預報

### Requirement: System MUST handle errors
天氣服務必須妥善處理各種錯誤情況。

#### Scenario: 數據源不可用
- **WHEN** 天氣數據源不可用時
- **THEN** 系統返回錯誤消息並建議用戶稍後重試

#### Scenario: 地區名稱無效
- **WHEN** 用戶輸入不存在的地區名稱時
- **THEN** 系統返回錯誤消息並提供可用地區列表

#### Scenario: 數據過期
- **WHEN** 天氣數據過期時（如超過1小時）
- **THEN** 系統標記數據為"可能不準確"並提示用戶

### Requirement: System MUST implement caching
為提高響應速度，系統實施天氣數據緩存。

#### Scenario: 緩存天氣數據
- **WHEN** 成功獲取天氣數據後
- **THEN** 系統緩存數據30分鐘

#### Scenario: 使用緩存數據
- **WHEN** 30分鐘內再次查詢相同地區天氣時
- **THEN** 系統直接返回緩存的數據

### Requirement: System MUST optimize performance
天氣服務必須優化性能以提供快速響應。

#### Scenario: 異步數據獲取
- **WHEN** 獲取天氣數據時
- **THEN** 系統異步執行，避免阻塞主線程

#### Scenario: 批量查詢支持
- **WHEN** 同時有多個用戶查詢天氣時
- **THEN** 系統批量獲取數據以提高效率
