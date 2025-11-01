## ADDED Requirements

### Requirement: System MUST generate stock heatmap
用戶可以使用 `/heatmap` 命令生成股票市場的熱力圖分析。

#### Scenario: 生成熱力圖
- **WHEN** 用戶執行 `/heatmap` 命令
- **THEN** 系統生成包含以下元素的熱力圖：
  - 不同顏色代表漲跌幅
  - 矩形大小代表市值
  - 顯示股票代碼和漲跌幅百分比

#### Scenario: 指定股票範圍
- **WHEN** 用戶執行 `/heatmap <股票代碼列表>`
- **THEN** 系統只生成指定股票的熱力圖

#### Scenario: 熱力圖顏色編碼
- **WHEN** 生成熱力圖時
- **THEN** 系統使用以下顏色編碼：
  - 紅色（深淺）= 漲幅（深紅=大漲，淺紅=小漲）
  - 綠色（深淺）= 跌幅（深綠=大跌，淺綠=小跌）
  - 黃色/橙色 = 平盤或微小變化

### Requirement: System MUST send heatmap
生成的熱力圖必須通過Telegram發送給用戶。

#### Scenario: 發送圖片
- **WHEN** 熱力圖生成完成
- **THEN** 系統將圖片發送到用戶的Telegram聊天窗口

#### Scenario: 圖片格式和大小
- **WHEN** 發送熱力圖時
- **THEN** 系統確保：
  - 圖片格式為PNG或JPEG
  - 圖片大小適合Telegram傳輸（<10MB）
  - 圖片解析度清晰可讀

### Requirement: System MUST integrate data sources
熱力圖需要集成多個數據源以生成準確的分析。

#### Scenario: 獲取股票列表
- **WHEN** 生成熱力圖時
- **THEN** 系統從以下來源獲取股票列表：
  - 用戶指定的股票代碼
  - 預定義的熱門港股列表（如恆生指數成分股）
  - 投資組合中的股票

#### Scenario: 獲取股價數據
- **WHEN** 獲取股票數據時
- **THEN** 系統使用統一的數據API獲取：
  - 當前價格
  - 開盤價
  - 昨日收盤價
  - 成交量
  - 市值

### Requirement: System MUST support heatmap interaction
熱力圖可以提供基本的交互功能。

#### Scenario: 點擊股票信息
- **WHEN** 用戶詢問特定股票的詳細信息
- **THEN** 系統顯示該股票的：
  - 當前價格
  - 漲跌幅
  - 成交量
  - 市值
  - 技術指標摘要

### Requirement: System MUST support custom heatmap parameters
用戶可以自定義熱力圖的顯示參數。

#### Scenario: 自定義時間範圍
- **WHEN** 用戶執行 `/heatmap --period 1d|1w|1m`
- **THEN** 系統生成基於指定時間範圍的熱力圖

#### Scenario: 自定義股票池
- **WHEN** 用戶執行 `/heatmap --top 50`
- **THEN** 系統生成市值前50名的股票熱力圖

### Requirement: System MUST optimize heatmap performance
熱力圖生成必須優化性能，避免長時間等待。

#### Scenario: 異步數據獲取
- **WHEN** 生成熱力圖時
- **THEN** 系統異步獲取所有股票數據，提高生成速度

#### Scenario: 緩存機制
- **WHEN** 短時間內多次生成熱力圖時
- **THEN** 系統緩存股價數據，避免重複API調用

### Requirement: System MUST handle errors
熱力圖生成過程中的錯誤必須妥善處理。

#### Scenario: 部分股票數據缺失
- **WHEN** 某些股票無法獲取數據
- **THEN** 系統使用占位符顯示這些股票，並在消息中說明

#### Scenario: 所有股票數據獲取失敗
- **WHEN** 無法獲取任何股票數據
- **THEN** 系統返回錯誤消息，並提示用戶稍後重試
