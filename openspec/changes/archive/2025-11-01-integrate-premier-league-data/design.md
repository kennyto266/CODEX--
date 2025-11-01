# 設計文檔：英超聯賽官網數據源整合

## 架構設計

### 系統架構概覽

```
Telegram Bot
    │
    ├── Command Handler (/score, /schedule)
    │   │
    │   └── FootballScraper (統一接口)
    │       │
    │       ├── PremierLeagueAdapter (英超官網 - 優先)
    │       ├── RealSportsDataFetcher (ESPN API - 備用)
    │       └── MockDataGenerator (模擬數據 - 最後)
    │
    └── Data Processor
            │
            ├── Timezone Converter (GMT → HKT)
            ├── Team Name Mapper (EN → ZH)
            └── Status Formatter
```

### 核心組件設計

#### 1. PremierLeagueAdapter

**職責**: 專門負責從英超官網獲取數據

```python
class PremierLeagueAdapter:
    """英超聯賽官網數據適配器"""

    def __init__(self):
        self.base_url = "https://www.premierleague.com/en/matches"
        self.chrome_mcp = None
        self.cache = {}  # 5分鐘緩存

    async def fetch_scores(self) -> List[Dict]:
        """獲取英超比分數據"""

    async def fetch_schedule(self, days: int = 7) -> List[Dict]:
        """獲取英超賽程"""

    def _parse_match_data(self, raw_data: str) -> List[Dict]:
        """解析網頁數據"""

    def _convert_timezone(self, gmt_time: str) -> str:
        """GMT轉換為HKT"""
```

**關鍵特性**:
- 使用 Chrome MCP 進行動態內容爬取
- 實施 5 分鐘緩存機制
- 支持參數化查詢（賽季、週數、月份）
- 實現請求限流（每分鐘 20 次）

#### 2. 數據流設計

```
用戶請求 → FootballScraper.fetch_scores()
                    │
                    ├── 檢查緩存
                    │   ├── 有 → 返回緩存數據
                    │   └── 無 → 繼續
                    │
                    ├── 嘗試 PremierLeagueAdapter
                    │   ├── 成功 → 解析並緩存 → 返回
                    │   └── 失敗 → 記錄日誌
                    │
                    ├── 嘗試 RealSportsDataFetcher (ESPN)
                    │   ├── 成功 → 解析並緩存 → 返回
                    │   └── 失敗 → 記錄日誌
                    │
                    └── 最後回退到 MockDataGenerator
                        └── 返回模擬數據
```

## 數據模型設計

### 1. Match 數據結構

```python
@dataclass
class PremierLeagueMatch:
    # 基本信息
    match_id: str
    home_team: str
    away_team: str
    home_score: int = 0
    away_score: int = 0

    # 狀態信息
    status: MatchStatus  # scheduled, live, halftime, finished
    minute: Optional[int] = None  # 比賽進行分鐘
    added_time: Optional[int] = None  # 補時分鐘

    # 時間信息
    start_time_gmt: str  # 原GMT時間
    start_time_hkt: str  # 轉換後HKT時間
    date: str

    # 比賽信息
    competition: str = "英超"
    venue: Optional[str] = None
    matchweek: Optional[int] = None

    # 元數據
    last_update: datetime
    data_source: str = "premierleague.com"

    @property
    def is_live(self) -> bool:
        return self.status == MatchStatus.LIVE

    @property
    def display_time(self) -> str:
        """返回顯示用時間"""
        if self.status == MatchStatus.LIVE:
            if self.added_time:
                return f"{self.minute}'+{self.added_time}"
            return f"{self.minute}'"
        return self.start_time_hkt
```

### 2. 球隊名稱映射表

```python
TEAM_NAME_MAPPING = {
    # 2024-25 英超球隊
    "Arsenal": "阿仙奴",
    "Aston Villa": "阿士東維拉",
    "Brighton & Hove Albion": "白禮頓",
    "Burnley": "般尼",
    "Chelsea": "車路士",
    "Crystal Palace": "水晶宮",
    "Everton": "愛華頓",
    "Fulham": "富咸",
    "Liverpool": "利物浦",
    "Luton Town": "盧頓",
    "Manchester City": "曼城",
    "Manchester United": "曼聯",
    "Newcastle United": "紐卡素",
    "Norwich City": "諾域治",
    "Nottingham Forest": "諾定咸森林",
    "Sheffield United": "錫菲聯",
    "Tottenham Hotspur": "熱刺",
    "West Ham United": "韋斯咸",
    "Wolverhampton Wanderers": "狼隊",
    # 其他常用球隊
    "Brentford": "賓福特",
    "Leicester City": "李斯特城",
    "Leeds United": "列斯聯",
    "Southampton": "修咸頓",
    "West Bromwich Albion": "西布朗",
    "Watford": "屈福特",
    "Bournemouth": "般尼茅夫",
    "Huddersfield Town": "哈特斯菲爾德",
}
```

## 爬蟲設計

### 1. Chrome MCP 爬蟲流程

```
啟動 Chrome MCP
    │
    ├── 導航到英超官網
    │   └── URL: https://www.premierleague.com/en/matches
    │
    ├── 等待頁面加載
    │   ├── 等待 DOM 元素加載
    │   └── 等待 AJAX 請求完成
    │
    ├── 執行數據提取
    │   ├── 定位比分容器
    │   ├── 提取比賽信息
    │   └── 滾動頁面（如需要）
    │
    ├── 解析數據
    │   ├── 提取球隊名稱
    │   ├── 提取比分
    │   ├── 提取比賽狀態
    │   └── 提取時間信息
    │
    └── 關閉連接
```

### 2. 數據提取策略

**使用 CSS 選擇器**:

```python
SELECTORS = {
    'matches': 'div[data-match-status]',  # 所有比賽
    'home_team': 'span[data-testid="home-team"]',  # 主隊
    'away_team': 'span[data-testid="away-team"]',  # 客隊
    'home_score': 'span[data-testid="home-score"]',  # 主隊比分
    'away_score': 'span[data-testid="away-score"]',  # 客隊比分
    'status': 'span[data-testid="match-status"]',  # 比賽狀態
    'minute': 'span[data-testid="match-minute"]',  # 比賽分鐘
    'venue': 'span[data-testid="match-venue"]',  # 球場
    'date': 'span[data-testid="match-date"]',  # 比賽日期
}
```

### 3. 反爬蟲策略

- **請求間隔**: 每個請求間隔 1-2 秒
- **User-Agent 輪換**: 使用多種瀏覽器 UA
- **會話保持**: 保持 Cookie 狀態
- **錯誤處理**: 自動重試和切換代理
- **請求限流**: 每分鐘最多 20 次請求

## 緩存設計

### 1. 多層緩存架構

```
L1: 內存緩存 (5分鐘)
    │
    ├── 數據存儲: Dict[str, Any]
    ├── 鍵格式: "pl_scores_YYYY-MM-DD"
    └── 策略: 最近最少使用 (LRU)
    │
    ├── L2: 文件緩存 (30分鐘)
    │   ├── 存儲位置: /tmp/premierleague/
    │   ├── 文件格式: JSON
    │   └── 策略: 先入先出 (FIFO)
    │
    └── L3: Redis 緩存 (可選，1小時)
        ├── 鍵格式: "pl:scores:{date}"
        └── 策略: TTL 過期
```

### 2. 緩存更新策略

- **自動更新**: 緩存過期後自動刷新
- **手動更新**: 支持強制刷新
- **增量更新**: 只更新變化的數據
- **預加載**: 比賽開始前預加載數據

## 錯誤處理設計

### 1. 錯誤分類

```python
class DataSourceError(Exception):
    """數據源錯誤基類"""

class PremierLeagueSiteError(DataSourceError):
    """英超官網錯誤"""
    pass

class NetworkTimeoutError(DataSourceError):
    """網絡超時錯誤"""
    pass

class ParseError(DataSourceError):
    """數據解析錯誤"""
    pass

class RateLimitError(DataSourceError):
    """請求限流錯誤"""
    pass
```

### 2. 錯誤恢復策略

```
錯誤檢測
    │
    ├── 檢查錯誤類型
    │   ├── 網站不可用 → 切換到ESPN
    │   ├── 解析失敗 → 記錄日誌，嘗試其他源
    │   ├── 限流 → 等待重試
    │   └── 超時 → 重新請求
    │
    ├── 實施恢復動作
    │   ├── 記錄錯誤日誌
    │   ├── 切換數據源
    │   └── 更新監控指標
    │
    └── 通知用戶
        └── "數據獲取中，請稍後重試"
```

### 3. 日誌設計

```python
# 使用結構化日誌
logger.info(
    "Fetching Premier League data",
    extra={
        'source': 'premierleague.com',
        'action': 'fetch_scores',
        'matchweek': 10,
        'season': 2025,
        'response_time_ms': 1250,
        'cache_hit': False,
    }
)

logger.error(
    "Failed to fetch data",
    extra={
        'error_type': 'timeout',
        'url': 'https://www.premierleague.com/en/matches',
        'retry_count': 2,
    },
    exc_info=True
)
```

## 性能優化設計

### 1. 並發控制

```python
# 使用信號量限制並發請求
MAX_CONCURRENT_REQUESTS = 5
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def fetch_with_limit():
    async with request_semaphore:
        # 執行請求
        pass
```

### 2. 請求優化

- **連接池**: 重用 HTTP 連接
- **Keep-Alive**: 保持連接活躍
- **壓縮**: 啟用 gzip 壓縮
- **DNS 緩存**: 緩存 DNS 解析結果

### 3. 數據處理優化

- **懶加載**: 僅在需要時加載數據
- **批量處理**: 一次性處理多個比賽
- **向量化操作**: 使用 Pandas 進行批量數據處理
- **內存池**: 重用對象減少 GC 壓力

## 監控設計

### 1. 關鍵指標

```python
METRICS = {
    'request_count': '請求總數',
    'success_rate': '成功率',
    'average_response_time': '平均響應時間',
    'cache_hit_rate': '緩存命中率',
    'data_freshness': '數據新鮮度',
    'error_rate': '錯誤率',
    'concurrent_requests': '並發請求數',
}
```

### 2. 告警閾值

- **成功率 < 90%**: 警告
- **響應時間 > 5 秒**: 警告
- **緩存命中率 < 50%**: 警告
- **連續錯誤 > 10**: 嚴重告警

## 安全設計

### 1. 請求安全

- **速率限制**: 每 IP 每分鐘 20 次請求
- **IP 封鎖檢測**: 自動檢測和處理
- **HTTPS**: 所有請求使用 HTTPS
- **驗證**: 檢查 SSL 證書

### 2. 數據安全

- **輸入驗證**: 驗證所有輸入參數
- **SQL 注入防護**: 使用參數化查詢
- **XSS 防護**: 轉義所有輸出
- **數據脱敏**: 不存儲敏感信息

## 測試設計

### 1. 單元測試

```python
class TestPremierLeagueAdapter:
    """測試 PremierLeagueAdapter"""

    async def test_fetch_scores_success(self):
        """測試成功獲取比分"""

    async def test_fetch_scores_timeout(self):
        """測試請求超時"""

    async def test_parse_match_data(self):
        """測試數據解析"""

    def test_timezone_conversion(self):
        """測試時區轉換"""

    def test_team_name_mapping(self):
        """測試球隊名稱映射"""
```

### 2. 集成測試

```python
class TestFootballScraperIntegration:
    """測試足球爬蟲集成"""

    async def test_multi_source_fallback(self):
        """測試多數據源回退"""

    async def test_concurrent_requests(self):
        """測試並發請求"""

    async def test_cache_functionality(self):
        """測試緩存功能"""

    async def test_error_recovery(self):
        """測試錯誤恢復"""
```

### 3. 負載測試

- 100 並發用戶
- 持續 1 小時
- 監控響應時間和成功率

## 部署設計

### 1. 漸進式部署

```
Phase 1: 內部測試
    ├── 部署到測試環境
    ├── 5% 用戶流量
    └── 監控 24 小時

    ↓ 驗證成功

Phase 2: 部分生產
    ├── 部署到生產環境
    ├── 50% 用戶流量
    └── 監控 48 小時

    ↓ 驗證成功

Phase 3: 完全部署
    ├── 100% 用戶流量
    └── 持續監控
```

### 2. 回滾計劃

- **藍綠部署**: 保持兩個版本並行
- **快速回滾**: 1 分鐘內回滾
- **數據恢復**: 保證數據一致性
- **通知機制**: 及時通知相關人員

## 擴展設計

### 1. 水平擴展

- **微服務拆分**: 將適配器拆分為獨立服務
- **負載均衡**: 使用 Nginx 或 HAProxy
- **容器化**: Docker 部署
- **Kubernetes**: 自動擴縮容

### 2. 功能擴展

- 支持更多聯賽（西甲、意甲、德甲）
- 添加球員統計數據
- 支持歷史數據查詢
- 添加預測功能

## 總結

本設計文檔詳細說明了英超聯賽官網數據源整合的技術方案，包括架構設計、數據模型、爬蟲策略、緩存機制、錯誤處理、性能優化、監控、安全和測試等各個方面。該設計遵循模塊化、可擴展、可維護的原則，確保系統的穩定性和可靠性。
