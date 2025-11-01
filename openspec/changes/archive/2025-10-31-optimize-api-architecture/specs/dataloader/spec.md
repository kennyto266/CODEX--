# DataLoader數據預取規範

## ADDED Requirements

### Requirement 1: DataLoader基類
**描述**: 創建批量數據加載器解決N+1查詢問題

#### Scenario: 基本批量加載
- **Given**: 需要加載多個ID的數據
- **When**: 使用DataLoader批量加載
- **Then**: 應該用一次查詢獲取所有數據

#### Scenario: 緩存結果
- **Given**: 已經加載過的數據
- **When**: 再次請求相同ID
- **Then**: 應該返回緩存結果不重新查詢

#### Scenario: 批次大小控制
- **Given**: 1000個ID需要加載
- **When**: 批次大小設置為100
- **Then**: 應該分10批次執行查詢

#### Scenario: 並發加載
- **Given**: 多個同時的加載請求
- **When**: DataLoader處理
- **Then**: 應該合併為單批次查詢

#### Scenario: 延遲加載
- **Given**: 請求單個數據
- **When**: 等待事件循環完成
- **Then**: 應該聚合同批次其他請求一起執行

### Requirement 2: 自動批處理
**描述**: 自動聚合多個單獨請求為批次

#### Scenario: 請求聚合
- **Given**: 3個並發的加載請求
- **When**: 事件循環tick
- **Then**: 應該聚合為單次批量查詢

#### Scenario: 微任務優化
- **Given**: 大量小請求
- **When**: 使用微任務
- **Then**: 應該在next tick統一執行

#### Scenario: 防止過度聚合
- **Given**: 實時性能要求
- **When**: 加載延遲超過閾值
- **Then**: 應該立即執行當前批次

### Requirement 3: 可配置加載函數
**描述**: 支持自定義批量加載邏輯

#### Scenario: 自定義加載器
- **Given**: 特殊數據加載需求
- **When**: 註冊加載函數
- **Then**: 應該使用自定義邏輯加載

#### Scenario: 錯誤處理
- **Given**: 加載函數拋出異常
- **When**: DataLoader處理
- **Then**: 應該將錯誤傳遞給所有請求者

#### Scenario: 部分失敗
- **Given**: 批次中部分數據不存在
- **When**: 加載完成
- **Then**: 應該返回有效數據和錯誤信息

### Requirement 4: 級聯加載
**描述**: 支持關聯數據的級聯加載

#### Scenario: 主從關係加載
- **Given**: 主數據和關聯從數據
- **When**: 使用級聯加載器
- **Then**: 應該先加載主數據，再加載關聯數據

#### Scenario: 多級關聯
- **Given**: 三層關聯關係
- **When**: 使用級聯加載
- **Then**: 應該逐層加載並緩存

#### Scenario: 加載深度控制
- **Given**: 複雜關聯圖
- **When**: 設置加載深度限制
- **Then**: 應該只加載指定深度的關聯

### Requirement 5: 緩存策略
**描述**: 提供靈活的緩存策略

#### Scenario: LRU緩存
- **Given**: 緩存大小限制
- **When**: 達到容量限制
- **Then**: 應該移除最少使用的數據

#### Scenario: TTL過期
- **Given**: 設置緩存過期時間
- **When**: 數據過期
- **Then**: 應該重新加載數據

#### Scenario: 手動失效
- **Given**: 數據更新
- **When**: 手動失效緩存
- **Then**: 應該從緩存中移除指定數據

#### Scenario: 緩存鍵自定義
- **Given**: 複雜加載邏輯
- **When**: 生成緩存鍵
- **Then**: 應該支持自定義鍵生成函數

### Requirement 6: 監控和度量
**描述**: 監控DataLoader性能

#### Scenario: 查詢次數統計
- **Given**: 加載操作
- **When**: 記錄統計
- **Then**: 應該統計減少的查詢次數

#### Scenario: 性能指標
- **Given**: 加載請求
- **When**: 完成加載
- **Then**: 應該記錄加載時間和數據量

#### Scenario: 命中率
- **Given**: 緩存請求
- **When**: 計算命中率
- **Then**: 應該暴露緩存命中率指標

#### Scenario: 調試支持
- **Given**: 開發模式
- **When**: 啟用調試
- **Then**: 應該記錄詳細加載信息

## MODIFIED Requirements

### Requirement 7: API端點整合DataLoader
**描述**: 將DataLoader整合到API端點

#### Scenario: Agent API使用DataLoader
- **Given**: Agent列表API
- **When**: 整合AgentPerformanceLoader
- **Then**: 應該批量加載所有Agent性能數據

#### Scenario: 策略API使用DataLoader
- **Given**: 策略列表API
- **When**: 整合StrategyMetricsLoader
- **Then**: 應該一次查詢獲取所有策略指標

#### Scenario: 交易API使用DataLoader
- **Given**: 交易記錄API
- **When**: 整合PositionLoader
- **Then**: 應該批量加載所有頭寸數據

#### Scenario: 風險API使用DataLoader
- **Given**: 風險指標API
- **When**: 整合RiskMetricsLoader
- **Then**: 應該預取相關風險數據

### Requirement 8: Repository整合DataLoader
**描述**: Repository自動使用DataLoader

#### Scenario: Repository自動加載關聯
- **Given**: Repository查詢主數據
- **When**: 啟用自動加載
- **Then**: 應該自動加載關聯數據

#### Scenario: 延遲加載配置
- **Given**: 關聯數據加載策略
- **When**: 配置延遲加載
- **Then**: 只在訪問時加載關聯數據

#### Scenario: 預加載配置
- **Given**: 關聯數據加載策略
- **When**: 配置預加載
- **Then**: 查詢主數據時自動加載關聯

## REMOVED Requirements

### Requirement 9: 清理N+1查詢
**描述**: 移除所有N+1查詢模式

#### Scenario: 循環查詢移除
- **Given**: for循環中的查詢
- **When**: 重構為DataLoader
- **Then**: 應該用批量查詢替換

#### Scenario: 重複查詢移除
- **Given**: 多次查詢相同數據
- **When**: 使用緩存
- **Then**: 應該只查詢一次

#### Scenario: 隱式查詢移除
- **Given**: 屬性訪問觸發查詢
- **When**: 使用DataLoader
- **Then**: 應該明確定義加載策略
