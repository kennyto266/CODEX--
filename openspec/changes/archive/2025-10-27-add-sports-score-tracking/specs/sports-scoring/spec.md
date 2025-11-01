# 體育比分核心功能規格

## 概述

本規格定義了 Telegram Bot 體育比分追蹤功能的核心架構和通用功能，支持多種運動類型的實時比分查詢。

## ADDED Requirements

### Requirement: System MUST implement base sports scoring framework
系統必須實現基礎的體育比分框架，為不同運動類型提供統一的數據結構和處理邏輯。

#### Scenario: 初始化體育比分系統
- **WHEN** Bot 啟動並載入體育比分模組
- **THEN** 系統初始化以下組件：
  - 創建 Chrome MCP 連接池
  - 初始化緩存管理器
  - 載入配置參數
  - 準備數據處理管道

#### Scenario: 註冊運動類型
- **WHEN** 系統啟動時
- **THEN** 自動註冊以下運動類型：
  - NBA (籃球)
  - Soccer (足球)
  - 每個運動類型關聯對應的爬蟲模組

#### Scenario: 統一數據格式
- **WHEN** 不同運動類型的數據進入處理管道時
- **THEN** 系統將數據轉換為統一的格式：
  - 比賽時間
  - 主隊/客隊名稱
  - 比分
  - 比賽狀態 (未開始/進行中/已結束)
  - 聯賽/盃賽信息

### Requirement: System MUST provide command routing
系統必須提供命令路由功能，將用戶命令正確路由到對應的運動類型處理器。

#### Scenario: 路由 `/score` 命令
- **WHEN** 用戶執行 `/score` 命令
- **THEN** 系統檢查參數並路由：
  - 無參數 → 返回所有運動類型比分
  - `nba` → 路由到 NBA 處理器
  - `soccer` → 路由到足球處理器
  - 無效參數 → 返回錯誤信息和可用選項

#### Scenario: 路由 `/schedule` 命令
- **WHEN** 用戶執行 `/schedule` 命令
- **THEN** 系統檢查參數並路由：
  - 無參數 → 返回所有運動類型賽程
  - 指定運動類型 → 路由到對應處理器
  - 指定日期 → 查詢特定日期賽程

#### Scenario: 處理無效命令
- **WHEN** 用戶執行不支持的命令
- **THEN** 系統返回：
  - 錯誤消息說明命令不支持
  - 可用命令列表
  - 幫助信息鏈接

### Requirement: System MUST implement Chrome MCP integration
系統必須使用 Chrome MCP 進行網頁爬取，支持動態內容加載。

#### Scenario: 建立 Chrome MCP 連接
- **WHEN** 首次需要爬取數據時
- **THEN** 系統執行以下操作：
  - 檢查 Chrome MCP 服務是否運行
  - 建立 WebSocket 連接
  - 驗證連接狀態
  - 返回連接結果

#### Scenario: 執行爬蟲任務
- **WHEN** 需要爬取網頁數據時
- **THEN** 系統執行以下步驟：
  - 分配 Chrome MCP 連接
  - 導航到目標 URL
  - 等待頁面完全加載
  - 提取所需數據
  - 釋放連接資源

#### Scenario: 處理爬蟲失敗
- **WHEN** 爬蟲操作失敗時
- **THEN** 系統執行以下操作：
  - 記錄錯誤詳情
  - 嘗試重試 (最多 3 次)
  - 如果全部失敗，返回友好錯誤消息
  - 通知管理員 (如果配置)

### Requirement: System MUST implement data caching
系統必須實現多層緩存機制，提高響應速度並減少對目標網站的請求。

#### Scenario: 緩存比分數據
- **WHEN** 成功獲取比分數據後
- **THEN** 系統執行：
  - 將數據存儲到內存緩存 (TTL: 2 分鐘)
  - 生成數據指紋 (hash)
  - 記錄緩存時間戳
  - 標記數據來源

#### Scenario: 從緩存返回數據
- **WHEN** 收到比分查詢請求時
- **THEN** 系統執行：
  - 檢查緩存是否存在
  - 驗證緩存是否過期
  - 如果有效，返回緩存數據
  - 如果過期，重新爬取並更新緩存

#### Scenario: 緩存失效策略
- **WHEN** 數據超過 TTL 時間時
- **THEN** 系統執行：
  - 標記緩存為過期
  - 為進行中的比賽創建短期緩存 (30 秒)
  - 為已結束的比賽保持較長時間緩存 (10 分鐘)

### Requirement: System MUST validate scraped data
系統必須驗證爬取的數據，確保數據完整性和準確性。

#### Scenario: 驗證比分數據
- **WHEN** 接收到原始比分數據時
- **THEN** 系統檢查：
  - 比賽時間格式是否正確
  - 球隊名稱是否存在且非空
  - 比分格式是否正確 (數字)
  - 比賽狀態是否有效

#### Scenario: 處理無效數據
- **WHEN** 數據驗證失敗時
- **THEN** 系統執行：
  - 記錄無效數據和原因
  - 嘗試從備用數據源獲取
  - 如果仍無法獲取，返回部分數據並標記
  - 向管理員發送告警 (可選)

#### Scenario: 數據完整性檢查
- **WHEN** 處理多場比賽數據時
- **THEN** 系統檢查：
  - 沒有重複的比賽記錄
  - 所有必需字段都已填充
  - 時間戳是合理的 (不超過當前時間)
  - 比分變化是連續的 (如果有歷史數據)

### Requirement: System MUST format output messages
系統必須將比分數據格式化成用戶友好的 Telegram 消息。

#### Scenario: 格式化 NBA 比分消息
- **WHEN** 格式化 NBA 比分時
- **THEN** 系統使用以下格式：
  - 標題: "🏀 NBA 今日比分 (YYYY-MM-DD)"
  - 已結束: "✅ 已結束\n🏆 球隊A XX - XX 球隊B\n📊 勝率: X.X% vs X.X%"
  - 進行中: "🔴 進行中\n⚡ 球隊A vs 球隊B (第X節)\n💯 比分: XX - XX\n⏱️ 剩餘: X:XX"

#### Scenario: 格式化足球比分消息
- **WHEN** 格式化足球比分時
- **THEN** 系統使用以下格式：
  - 標題: "⚽ 足球比分 (YYYY-MM-DD)"
  - 已結束: "✅ 已結束\n🥅 球隊A XX - XX 球隊B\n📅 HH:MM | 現場: 球場名稱"
  - 進行中: "🔴 進行中\n⚡ 球隊A vs 球隊B (下半場)\n💯 比分: XX - XX\n⏱️ 剩餘: XX:XX"

#### Scenario: 添加快速操作按鈕
- **WHEN** 發送比分消息時
- **THEN** 系統可以添加以下按鈕：
  - "🔄 刷新" - 重新獲取最新比分
  - "📅 賽程" - 查看賽程
  - "⭐ 收藏" - 收藏球隊
  - 運動類型切換按鈕

### Requirement: System MUST handle concurrent requests
系統必須處理並發請求，確保在高負載情況下穩定運行。

#### Scenario: 處理多個同時請求
- **WHEN** 多個用戶同時查詢比分時
- **THEN** 系統執行：
  - 為每個請求創建獨立任務
  - 使用連接池管理 Chrome MCP 連接
  - 如果連接池滿，進入等待隊列
  - 返回相應的結果

#### Scenario: 請求限制
- **WHEN** 用戶在短時間內發送多個請求時
- **THEN** 系統執行：
  - 記錄請求時間戳
  - 如果 30 秒內超過 10 次請求
  - 返回 "請求過於頻繁，請稍後再試"
  - 記錄濫用行為到日誌

#### Scenario: 資源清理
- **WHEN** 任務完成或超時時
- **THEN** 系統執行：
  - 釋放所有 Chrome MCP 連接
  - 清理臨時數據
  - 關閉無用的瀏覽器標籤頁
  - 釋放內存資源

### Requirement: System MUST implement error handling
系統必須實現完善的錯誤處理機制，提供清晰的錯誤信息和恢復策略。

#### Scenario: 網絡連接失敗
- **WHEN** 無法連接到目標網站時
- **THEN** 系統執行：
  - 記錄錯誤詳情 (URL、錯誤類型、時間)
  - 嘗試備用數據源
  - 如果都失敗，返回 "暫時無法獲取數據，請稍後重試"
  - 建議用戶稍後再試

#### Scenario: Chrome MCP 不可用
- **WHEN** Chrome MCP 服務不可用時
- **THEN** 系統執行：
  - 檢查服務狀態
  - 嘗試重新連接
  - 如果多次失敗，返回錯誤消息
  - 建議檢查 Chrome MCP 配置

#### Scenario: 數據解析錯誤
- **WHEN** 網頁結構變更導致數據解析失敗時
- **THEN** 系統執行：
  - 記錄當前網頁結構
  - 嘗試多種解析策略
  - 如果都失敗，返回部分數據或錯誤
  - 通知開發者更新爬蟲規則

### Requirement: System MUST log activities
系統必須記錄所有重要活動，支持監控和故障排除。

#### Scenario: 記錄用戶請求
- **WHEN** 用戶執行命令時
- **THEN** 系統記錄：
  - 用戶 ID 和用戶名
  - 命令和參數
  - 執行時間
  - 響應時間
  - 結果 (成功/失敗)

#### Scenario: 記錄爬蟲操作
- **WHEN** 執行爬蟲操作時
- **THEN** 系統記錄：
  - 目標 URL
  - 爬取時間
  - 數據大小
  - 成功/失敗狀態
  - 錯誤信息 (如果有)

#### Scenario: 記錄性能指標
- **WHEN** 完成請求處理時
- **THEN** 系統記錄：
  - 總響應時間
  - 網頁加載時間
  - 數據解析時間
  - 緩存命中率
  - 內存使用量

### Requirement: System MUST support configuration
系統必須支持靈活的配置，允許自定義行為。

#### Scenario: 配置文件加載
- **WHEN** 系統啟動時
- **THEN** 系統從以下位置加載配置：
  - 環境變量
  - `.env` 文件
  - `config.json` 文件 (可選)
  - 默認配置

#### Scenario: 可配置的參數
- **WHEN** 配置生效時
- **THEN** 系統支持以下配置項：
  - 緩存 TTL (比分、賽程)
  - 最大重試次數
  - 請求超時時間
  - 連接池大小
  - 用戶白名單
  - 日誌級別

#### Scenario: 熱更新配置
- **WHEN** 配置文件變更時
- **THEN** 系統執行：
  - 檢測配置文件變更
  - 重新加載配置
  - 應用到新請求
  - 記錄配置更新

### Requirement: System MUST ensure data freshness
系統必須確保數據的時效性，特別是對於正在進行的比賽。

#### Scenario: 實時比分更新
- **WHEN** 用戶查詢進行中的比賽時
- **THEN** 系統執行：
  - 檢查最後更新時間
  - 如果超過 30 秒，重新爬取
  - 如果比賽即將結束 (最後 5 分鐘)，每 15 秒更新一次
  - 返回帶有 "🔄" 標記的更新比分

#### Scenario: 比賽狀態自動檢測
- **WHEN** 系統定期檢查比分時
- **THEN** 系統自動檢測：
  - 比赛是否剛剛開始/結束
  - 比分是否發生變化
  - 比賽階段是否變更 (如 NBA 的節次)
  - 自動更新緩存

#### Scenario: 比賽結束處理
- **WHEN** 檢測到比賽結束時
- **THEN** 系統執行：
  - 將比賽標記為 "已結束"
  - 延長緩存時間到 10 分鐘
  - 移除從實時更新列表
  - 生成比賽摘要 (可選)

## 數據模型

### SportsMatch
```python
@dataclass
class SportsMatch:
    match_id: str
    sport_type: str  # 'nba', 'soccer'
    league: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str  # 'scheduled', 'live', 'finished'
    start_time: datetime
    update_time: datetime
    quarter: Optional[str] = None  # NBA 節次
    venue: Optional[str] = None
    attendance: Optional[int] = None
```

### CacheEntry
```python
@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    source: str
    valid_until: datetime
```

## 性能要求

- **響應時間**: 首次查詢 < 5 秒，緩存查詢 < 1 秒
- **並發處理**: 支持至少 10 個並發請求
- **緩存命中率**: > 70%
- **成功率**: > 95% (網絡正常情況下)
- **內存使用**: < 100MB

## 監控指標

1. 爬蟲成功率
2. 平均響應時間
3. 緩存命中率
4. 並發請求數
5. 錯誤率
6. 數據準確性
7. 資源使用率 (CPU/內存)

## 相關規格

- `specs/nba-scoring` - NBA 特定實現
- `specs/football-scoring` - 足球特定實現
- `specs/sports-schedule` - 賽程查詢功能
- `specs/telegram-bot` - Telegram Bot 集成
- `specs/web-scraping` - 網頁爬取基礎
