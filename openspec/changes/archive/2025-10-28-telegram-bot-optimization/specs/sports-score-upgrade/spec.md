# 體育比分系統升級規格說明

**規格ID**: sports-score-upgrade-v1
**版本**: 1.0.0
**最後更新**: 2025-10-28

## 📋 規格概述

本規格說明定義了將體育比分系統升級為使用足智彩官方數據的具體要求，提升數據準確性和實時性，並與現有NBA/足球系統無縫整合。

## 🎯 改進目標

### 主要目標
1. 接入足智彩官方數據源 (https://bet.hkjc.com/ch/football/home)
2. 提升數據準確率至90%以上
3. 保持與現有系統的向下兼容
4. 優化回應速度和用戶體驗

### 成功標準
- 數據準確率 > 90% (原70%)
- 回應時間 < 2秒
- 99% 服務可用性
- 用戶滿意度 > 8/10

## ✅ 修改需求

### MODIFIED Requirements

#### SSU-001: 創建足智彩數據適配器
**描述**: The system MUST The system SHALL 創建 `joker_sports_adapter.py`，作為足智彩官方數據源的適配器

**文件位置**: `src/telegram_bot/sports_scoring/joker_sports_adapter.py`

**核心類**:
```python
class JokerSportsAdapter:
    """足智彩體育數據適配器"""

    async def fetch_live_scores(self, sport_type: str) -> List[Dict]:
        """獲取實時比分"""
        pass

    async def fetch_upcoming_matches(self, sport_type: str) -> List[Dict]:
        """獲取 upcoming 比賽"""
        pass

    async def fetch_league_table(self, league: str) -> List[Dict]:
        """獲取聯賽積分榜"""
        pass
```

**支持的運動類型**:
- **足球**: 英超、西甲、意甲、德甲、法甲等
- **籃球**: NBA、CBA等
- **其他**: 網球、排球等

**數據格式**:
```python
MatchInfo = {
    "match_id": str,              # 比賽ID
    "league": str,                # 聯賽名稱
    "home_team": str,             # 主隊
    "away_team": str,             # 客隊
    "home_score": Optional[int],  # 主隊得分
    "away_score": Optional[int],  # 客隊得分
    "status": str,                # 比賽狀態 (未開始/進行中/已結束)
    "match_time": str,            # 比賽時間
    "venue": str,                 # 比賽場地
    "data_source": "joker",       # 數據來源標記
}
```

**驗收條件**:
- [ ] 成功抓取足智彩網站數據
- [ ] 正確解析多項運動數據
- [ ] 數據格式與現有系統兼容
- [ ] 錯誤處理機制完善

**Scenario: 獲取足球比分**
```
用戶輸入: /score soccer
系統回應:
⚽ 足球比分

🏴󠁧󠁢󠁥󠁮󠁧󠁿 英超 (2025-10-28)

🔥 進行中:
曼聯 2-1 利物浦 (75')
阿森納 1-0 曼城 (82')

📅 今日賽事:
切爾西 vs 熱刺 19:30
📊 數據源: 足智彩
```

#### SSU-002: 升級現有爬蟲系統
**描述**: The system MUST The system SHALL 修改 `nba_scraper.py` 和 `football_scraper.py`，整合足智彩數據

**文件位置**:
- `src/telegram_bot/sports_scoring/nba_scraper.py`
- `src/telegram_bot/sports_scoring/football_scraper.py`

**修改策略**:
```python
class FootballScraper:
    def __init__(self):
        self.primary_adapter = JokerSportsAdapter()  # 足智彩
        self.fallback_adapter = LegacyFootballAdapter()  # 舊系統

    async def fetch_scores(self):
        """優先使用足智彩，失敗時使用舊系統"""
        try:
            data = await self.primary_adapter.fetch_live_scores("soccer")
            if data:
                return self._tag_data_source(data, "足智彩")
        except Exception as e:
            logger.warning(f"足智彩數據獲取失敗: {e}")

        # 回退到舊系統
        data = await self.fallback_adapter.fetch_scores()
        return self._tag_data_source(data, "舊系統")
```

**驗收條件**:
- [ ] 優先使用足智彩數據
- [ ] 自動回退機制正常
- [ ] 數據來源標記清晰
- [ ] 現有功能不受影響

**Scenario: 足智彩數據失效，自動回退**
```
用戶輸入: /score nba
系統回應: "⚠️ 足智彩數據暫時不可用，使用備用數據源"
系統回應: [NBA比分數據]
📊 數據源: 備用源
```

#### SSU-003: 升級數據處理器
**描述**: The system MUST The system SHALL 修改 `data_processor.py`，支持足智彩數據格式和標記

**文件位置**: `src/telegram_bot/sports_scoring/data_processor.py`

**新增功能**:
```python
class EnhancedDataProcessor:
    """增強數據處理器"""

    def format_score_with_source(self, games: List[Dict]):
        """格式化比分並標記數據來源"""
        formatted = []
        for game in games:
            text = self._format_game(game)
            source = game.get("data_source", "未知")
            formatted.append(f"{text}\n📊 數據源: {source}")

        return "\n\n".join(formatted)

    def merge_joker_data(self, joker_data: List[Dict], legacy_data: List[Dict]):
        """合併足智彩和舊系統數據"""
        # 優先使用足智彩數據
        # 不足部分用舊系統補充
        # 去除重複
        pass
```

**驗收條件**:
- [ ] 正確標記數據來源
- [ ] 數據合併邏輯正確
- [ ] 回應格式保持一致
- [ ] 性能未下降

#### SSU-004: 實施智能快取
**描述**: The system MUST The system SHALL 為體育比分數據實施分級快取機制

**快取策略**:
```python
SPORTS_CACHE_CONFIG = {
    "live_scores": {
        "ttl": 60,    # 實時比分：60秒
        "description": "比賽進行中，快速更新"
    },
    "upcoming_matches": {
        "ttl": 300,   # 即將開始：5分鐘
        "description": "未來24小時內的比賽"
    },
    "league_table": {
        "ttl": 1800,  # 積分榜：30分鐘
        "description": "聯賽積分榜變化較慢"
    },
    "final_results": {
        "ttl": 86400, # 已結束：24小時
        "description": "已結束的比賽"
    }
}
```

**實現方式**:
```python
class SportsCacheManager:
    _cache = {}

    async def get_cached_data(self, key: str, ttl: int):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < ttl:
                return data
        return None

    async def set_cached_data(self, key: str, data, ttl: int):
        self._cache[key] = (data, time.time())
```

**驗收條件**:
- [ ] 快取機制正常工作
- [ ] TTL設置合理
- [ ] 命中率 > 70%
- [ ] 內存使用 < 100MB

#### SSU-005: 優化回應格式
**描述**: The system MUST The system SHALL 簡化比分回應格式，突出重要信息

**舊格式**:
```
🏆 足球比分

🆚 曼聯 vs 利物浦
📅 日期: 2025-10-28 19:30
🏟️ 球場: 老特拉福德
👥 裁判: Michael Oliver
⏱️ 狀態: 進行中 (75')
⚽ 比分: 曼聯 2-1 利物浦
📊 控球率: 曼聯 52% vs 利物浦 48%
🥅 射門: 曼聯 8 vs 利物浦 6
... (過多冗餘信息)
```

**新格式**:
```
⚽ 足球比分

🔥 進行中:
曼聯 2-1 利物浦 (75')
阿森納 1-0 曼城 (82')

📅 今日賽事:
切爾西 vs 熱刺 19:30
🔚 已結束:
皇馬 3-2 巴薩 90+3'

📊 數據源: 足智彩
⏰ 更新: 2分鐘前
```

**驗收條件**:
- [ ] 回應長度 < 800字符 (原 > 1500字符)
- [ ] 突出核心信息
- [ ] 移除冗餘數據
- [ ] 用戶體驗提升

#### SSU-006: 添加數據質量監控
**描述**: The system MUST The system SHALL 實施數據質量監控系統，追蹤準確率

**監控指標**:
```python
DATA_QUALITY_METRICS = {
    "source_accuracy": {
        "joker": 0.92,      # 足智彩準確率 92%
        "legacy": 0.68,     # 舊系統 68%
    },
    "update_frequency": {
        "live": "每60秒",   # 實時比分更新頻率
        "scheduled": "每5分鐘"  # 賽程更新頻率
    },
    "error_rate": {
        "network": 0.02,    # 網絡錯誤率 2%
        "parsing": 0.01,    # 解析錯誤率 1%
        "timeout": 0.03     # 超時錯誤率 3%
    }
}
```

**實現**:
```python
class DataQualityMonitor:
    def __init__(self):
        self.metrics = defaultdict(int)
        self.total_requests = 0

    def record_success(self, source: str):
        self.metrics[f"{source}_success"] += 1
        self.total_requests += 1

    def record_error(self, source: str, error_type: str):
        self.metrics[f"{source}_{error_type}"] += 1

    def get_accuracy_report(self):
        total = self.metrics["total"]
        success = self.metrics["success"]
        return success / total if total > 0 else 0
```

**驗收條件**:
- [ ] 準確率統計正常
- [ ] 錯誤率追踪完整
- [ ] 報告生成正確
- [ ] 日誌記錄完整

## 🔍 測試需求

### 單元測試

#### T-SSU-001: 測試足智彩數據抓取
```python
@pytest.mark.asyncio
async def test_joker_data_fetching():
    """測試足智彩數據抓取"""
    adapter = JokerSportsAdapter()

    data = await adapter.fetch_live_scores("soccer")

    assert len(data) > 0
    for match in data:
        assert "home_team" in match
        assert "away_team" in match
        assert match["data_source"] == "joker"
```

#### T-SSU-002: 測試數據合併
```python
@pytest.mark.asyncio
async def test_data_merging():
    """測試足智彩和舊系統數據合併"""
    processor = EnhancedDataProcessor()

    joker_data = [
        {"match_id": "001", "home_team": "A", "away_team": "B"}
    ]
    legacy_data = [
        {"match_id": "002", "home_team": "C", "away_team": "D"}
    ]

    merged = processor.merge_joker_data(joker_data, legacy_data)

    assert len(merged) == 2
    assert any(m["match_id"] == "001" for m in merged)
    assert any(m["match_id"] == "002" for m in merged)
```

#### T-SSU-003: 測試快取機制
```python
@pytest.mark.asyncio
async def test_cache_mechanism():
    """測試快取機制"""
    cache = SportsCacheManager()

    # 設置數據
    await cache.set_cached_data("test", {"score": "2-1"}, 60)

    # 獲取數據（未過期）
    data = await cache.get_cached_data("test", 60)
    assert data["score"] == "2-1"

    # 等待過期
    await asyncio.sleep(1)
    data = await cache.get_cached_data("test", 60)
    assert data is None
```

#### T-SSU-004: 測試回退機制
```python
@pytest.mark.asyncio
async def test_fallback_mechanism():
    """測試數據源回退機制"""
    scraper = FootballScraper()
    scraper.primary_adapter.fetch_live_scores = Mock(side_effect=Exception("Error"))
    scraper.fallback_adapter.fetch_scores = Mock(return_value=[{"test": "data"}])

    data = await scraper.fetch_scores()

    assert data is not None
    assert data[0]["data_source"] == "舊系統"
```

### 集成測試

#### T-SSU-005: 端到端測試
```python
@pytest.mark.asyncio
async def test_sports_e2e():
    """測試完整比分系統"""
    bot = TestBot("test_token")

    response = await bot.send_command("/score soccer")

    assert response.status_code == 200
    assert "足球比分" in response.text
    assert "數據源" in response.text
    assert response.text_length < 800
```

#### T-SSU-006: 性能測試
```python
@pytest.mark.asyncio
async def test_performance():
    """測試響應性能"""
    start_time = time.time()

    scraper = FootballScraper()
    await scraper.fetch_scores()

    elapsed = time.time() - start_time
    assert elapsed < 2.0
```

### 準確性測試

#### T-SSU-007: 數據準確率驗證
```python
@pytest.mark.asyncio
async def test_data_accuracy():
    """測試數據準確率"""
    adapter = JokerSportsAdapter()
    data = await adapter.fetch_live_scores("soccer")

    # 與官方網站對比
    for match in data:
        official_data = await fetch_official_data(match["match_id"])
        assert match["home_score"] == official_data["home_score"]
        assert match["away_score"] == official_data["away_score"]
```

**準確率目標**: 90% 以上

## 📊 性能需求

### 性能指標
- **響應時間**: < 2秒 (90%分位)
- **數據準確率**: > 90%
- **服務可用性**: 99%
- **快取命中率**: > 70%
- **錯誤率**: < 3%

### 監控指標
```python
SPORTS_METRICS = {
    "avg_response_time": "平均響應時間",
    "cache_hit_rate": "快取命中率",
    "data_accuracy": "數據準確率",
    "api_success_rate": "API成功率",
    "user_satisfaction": "用戶滿意度",
    "error_count": "錯誤次數統計",
}
```

## 🔄 向下兼容

### 兼容策略
1. **保持現有命令**: `/score`, `/schedule`, `/favorite` 不變
2. **數據格式兼容**: 足智彩數據自動轉換為現有格式
3. **回應格式優化**: 保持一致性，僅簡化內容
4. **回退機制**: 足智彩失效時自動使用舊系統

### 遷移策略
1. **第一週**: 足智彩作為備用數據源
2. **第二週**: 設為主要數據源
3. **第三週**: 完全切換，移除舊系統

## 📝 實施檢查清單

- [ ] SSU-001: 創建joker_sports_adapter.py
- [ ] SSU-002: 升級現有爬蟲系統
- [ ] SSU-003: 升級數據處理器
- [ ] SSU-004: 實施智能快取
- [ ] SSU-005: 優化回應格式
- [ ] SSU-006: 添加數據質量監控
- [ ] T-SSU-001: 單元測試 - 數據抓取
- [ ] T-SSU-002: 單元測試 - 數據合併
- [ ] T-SSU-003: 單元測試 - 快取機制
- [ ] T-SSU-004: 單元測試 - 回退機制
- [ ] T-SSU-005: 集成測試
- [ ] T-SSU-006: 性能測試
- [ ] T-SSU-007: 準確性測試
- [ ] 文檔更新
- [ ] 部署檢查

---

**規格作者**: Claude Code
**審核狀態**: 待審核
**優先級**: 高
**估計工期**: 7天
**依賴**: command-simplification, mark6-integration
