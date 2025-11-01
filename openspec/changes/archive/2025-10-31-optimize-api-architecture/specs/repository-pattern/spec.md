# Repository模式規範

## ADDED Requirements

### Requirement 1: Repository基類
**描述**: 創建泛型Repository基類定義標準數據訪問接口

#### Scenario: 基本CRUD操作
- **Given**: 繼承BaseRepository的具體Repository
- **When**: 調用get_by_id, list, create, update, delete
- **Then**: 應該執行對應的數據庫操作

#### Scenario: 泛型類型安全
- **Given**: 定義Repository[T]
- **When**: 指定具體類型Agent
- **Then**: 應該確保返回類型為Agent

#### Scenario: 抽象方法實現
- **Given**: 抽象基類方法
- **When**: 具體類實現
- **Then**: 必須實現所有抽象方法

#### Scenario: 自動處理數據轉換
- **Given**: 數據庫結果
- **When**: Repository返回
- **Then**: 應該自動轉換為Pydantic模型

### Requirement 2: 分頁支持
**描述**: 所有列表查詢應該支持分頁

#### Scenario: 分頁查詢
- **Given**: 大量數據記錄
- **When**: 調用list(page=1, size=50)
- **Then**: 應該只返回50條記錄

#### Scenario: 頁碼驗證
- **Given**: 分頁參數
- **When**: page=0或負數
- **Then**: 應該拋出ValidationError

#### Scenario: 分頁大小限制
- **Given**: 分頁大小參數
- **When**: size=1000
- **Then**: 應該限制為最大值（如100）

#### Scenario: 總數統計
- **Given**: 分頁查詢
- **When**: 需要總記錄數
- **Then**: 應該返回總數用於前端分頁

#### Scenario: 空結果處理
- **Given**: 無數據情況
- **When**: 執行分頁查詢
- **Then**: 應該返回空列表和總數0

### Requirement 3: 排序支持
**描述**: 支持多種排序方式

#### Scenario: 單字段排序
- **Given**: 數據列表
- **When**: 指定sort_by="created_at"和sort_order="desc"
- **Then**: 應該按創建時間降序排列

#### Scenario: 排序順序驗證
- **Given**: 排序參數
- **When**: sort_order="invalid"
- **Then**: 應該拋出ValidationError

#### Scenario: 多字段排序
- **Given**: 複雜排序需求
- **When**: 支持多字段排序
- **Then**: 應該按優先級依次排序

#### Scenario: 默認排序
- **Given**: 未指定排序參數
- **When**: 執行查詢
- **Then**: 應該使用合理的默認排序

### Requirement 4: 過濾器支持
**描述**: 支持多種條件過濾

#### Scenario: 簡單過濾器
- **Given**: 過濾器字典{"status": "active"}
- **When**: 執行過濾查詢
- **Then**: 應該只返回狀態為active的記錄

#### Scenario: 範圍過濾器
- **Given**: 範圍條件{"price": {"gte": 100, "lte": 200}}
- **When**: 執行查詢
- **Then**: 應該返回價格在100-200之間的記錄

#### Scenario: 模糊搜索
- **Given**: 搜索條件{"name": "agent"}
- **When**: 執行模糊搜索
- **Then**: 應該返回名稱包含"agent"的記錄

#### Scenario: 多條件AND
- **Given**: 多個過濾條件
- **When**: 執行查詢
- **Then**: 應該滿足所有條件（AND邏輯）

#### Scenario: 多條件OR
- **Given**: OR條件組
- **When**: 執行查詢
- **Then**: 應該滿足任一條件（OR邏輯）

### Requirement 5: 聚合查詢支持
**描述**: 支持count, sum, avg等聚合操作

#### Scenario: 計數查詢
- **Given**: 過濾條件
- **When**: 調用count方法
- **Then**: 應該返回匹配的記錄數

#### Scenario: 求和查詢
- **Given**: 數值字段
- **When**: 調用sum方法
- **Then**: 應該返回字段總和

#### Scenario: 平均值查詢
- **Given**: 數值字段
- **When**: 調用avg方法
- **Then**: 應該返回字段平均值

#### Scenario: 最大最小值
- **Given**: 數值字段
- **When**: 調用max/min方法
- **Then**: 應該返回最大/最小值

### Requirement 6: 事務支持
**描述**: 支持數據庫事務操作

#### Scenario: 單一事務
- **Given**: 多個數據庫操作
- **When**: 包裝在事務中
- **Then**: 要麼全部成功，要麼全部回滾

#### Scenario: 嵌套事務
- **Given**: 嵌套的Repository調用
- **When**: 外層事務
- **Then**: 內層操作應該參與外層事務

#### Scenario: 並發控制
- **Given**: 並發事務
- **When**: 修改相同數據
- **Then**: 應該使用鎖機制避免衝突

### Requirement 7: 批量操作
**描述**: 支持批量插入、更新、刪除

#### Scenario: 批量插入
- **Given**: 多條記錄
- **When**: 調用batch_insert
- **Then**: 應該一次提交所有記錄

#### Scenario: 批量更新
- **Given**: 更新條件和數據
- **When**: 調用batch_update
- **Then**: 應該更新所有匹配的記錄

#### Scenario: 批量刪除
- **Given**: 刪除條件
- **When**: 調用batch_delete
- **Then**: 應該刪除所有匹配的記錄

#### Scenario: 批量操作性能
- **Given**: 1000條記錄
- **When**: 批量插入
- **Then**: 應該比逐個插入快5倍以上

## MODIFIED Requirements

### Requirement 8: 現有API使用Repository
**描述**: 重構所有API端點使用Repository模式

#### Scenario: Agent API使用Repository
- **Given**: Agent API端點
- **When**: 重構為使用AgentRepository
- **Then**: 功能應該保持不變但代碼更簡潔

#### Scenario: 策略API使用Repository
- **Given**: 策略API端點
- **When**: 重構為使用StrategyRepository
- **Then**: 應該支持分頁和排序

#### Scenario: 交易API使用Repository
- **Given**: 交易API端點
- **When**: 重構為使用TradingRepository
- **Then**: 應該支持復雜查詢

#### Scenario: 風險API使用Repository
- **Given**: 風險API端點
- **When**: 重構為使用RiskRepository
- **Then**: 應該支持聚合查詢

### Requirement 9: 緩存整合
**描述**: Repository與緩存層深度整合

#### Scenario: 自動緩存
- **Given**: Repository查詢
- **When**: 獲取數據
- **Then**: 應該自動緩存結果

#### Scenario: 緩存失效
- **Given**: Repository更新
- **When**: 數據變更
- **Then**: 應該自動失效相關緩存

#### Scenario: 讀寫策略
- **Given**: Repository操作
- **When**: 查詢或更新
- **Then**: 應該遵循適當的緩存策略

## REMOVED Requirements

### Requirement 10: 清理直接數據庫訪問
**描述**: 移除API端點中的直接SQL查詢

#### Scenario: 移除字符串拼接SQL
- **Given**: 使用字符串拼接的SQL
- **When**: 重構為Repository
- **Then**: 應該使用ORM查詢

#### Scenario: 移除重複查詢代碼
- **Given**: 多個端點中的重複查詢
- **When**: 提取到Repository
- **Then**: 應該移除重複代碼

#### Scenario: 移除硬編碼查詢
- **Given**: 硬編碼的查詢邏輯
- **When**: 使用Repository
- **Then**: 應該使用配置化的查詢
