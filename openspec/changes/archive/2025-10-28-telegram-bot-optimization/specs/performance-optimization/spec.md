# 性能優化規格說明

**規格ID**: performance-optimization-v1
**版本**: 1.0.0
**最後更新**: 2025-10-28

## 📋 規格概述

本規格說明定義了Telegram Bot整體性能優化的具體要求，包括響應時間優化、緩存機制、並發處理和監控體系的實施。

## 🎯 改進目標

### 主要目標
1. 將平均響應時間從2.5秒降至1.2秒 (縮短52%)
2. 提升系統並發處理能力至100+用戶
3. 實施分級緩存機制，命中率 > 70%
4. 建立完整的性能監控體系

### 成功標準
- 平均響應時間 < 1.5秒 (目標1.2秒)
- 95%分位響應時間 < 3秒
- 系統並發處理 > 100用戶
- 緩存命中率 > 70%
- 服務可用性 > 99.5%

## ✅ 修改需求

### MODIFIED Requirements

#### PO-001: 實施統一緩存管理
**描述**: The system MUST The system SHALL 創建 `cache_manager.py`，統一管理所有服務的緩存

**文件位置**: `src/telegram_bot/cache_manager.py`

**核心類**:
```python
class UnifiedCacheManager:
    """統一緩存管理器"""

    def __init__(self):
        self.memory_cache = {}
        self.cache_config = self._load_config()
        self._setup_cleanup_task()

    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存數據"""
        pass

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """設置緩存數據"""
        pass

    async def delete(self, key: str) -> None:
        """刪除緩存數據"""
        pass

    async def clear_pattern(self, pattern: str) -> None:
        """按模式清理緩存"""
        pass
```

**緩存配置**:
```python
CACHE_CONFIG = {
    "stock_data": {
        "ttl": 300,        # 5分鐘
        "max_size": 100,   # 最多100條
        "description": "股票技術分析數據"
    },
    "weather_data": {
        "ttl": 900,        # 15分鐘
        "max_size": 50,
        "description": "天氣數據"
    },
    "sports_scores": {
        "ttl": 60,         # 1分鐘
        "max_size": 200,
        "description": "體育比分"
    },
    "mark6_data": {
        "ttl": 3600,       # 1小時
        "max_size": 10,
        "description": "六合彩數據"
    },
    "portfolio_data": {
        "ttl": 600,        # 10分鐘
        "max_size": 100,
        "description": "投資組合數據"
    },
    "heatmap_data": {
        "ttl": 1800,       # 30分鐘
        "max_size": 20,
        "description": "熱力圖數據"
    }
}
```

**LRU緩存實現**:
```python
class LRUCache:
    """LRU緩存實現"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_count = defaultdict(int)

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None

        # LRU: 移動到末尾
        value = self.cache.pop(key)
        self.cache[key] = value
        self.access_count[key] += 1

        return value

    def set(self, key: str, value: Any) -> None:
        if key in self.cache:
            # 更新現有key
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # 移除最少使用的key
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]

        self.cache[key] = value
        self.access_count[key] = 1
```

**驗收條件**:
- [ ] 緩存命中率 > 70%
- [ ] 緩存自動過期機制正常
- [ ] LRU策略正確實現
- [ ] 內存使用 < 200MB

#### PO-002: 優化命令響應格式
**描述**: The system MUST The system SHALL 簡化所有命令的回應格式，移除冗餘信息

**優化策略**:

1. **保留核心信息**:
   - 股票: 價格、變化、技術指標
   - 天氣: 溫度、濕度、天氣、警告
   - 比分: 比分、時間、狀態
   - 投資組合: 總值、盈虧、持倉

2. **移除冗餘信息**:
   - 詳細的技術參數
   - 重複的描述文字
   - 過多的表情符號
   - 歷史數據（除非必要）

**格式規範**:
```python
RESPONSE_FORMAT_GUIDELINES = {
    "max_length": 800,          # 最大長度
    "max_lines": 15,            # 最大行數
    "emoji_limit": 5,           # 表情符號限制
    "required_fields": [],      # 必含字段
    "optional_fields": [],      # 可選字段
}
```

**驗收條件**:
- [ ] 所有命令回應 < 800字符
- [ ] 保留核心信息完整性
- [ ] 移除冗餘內容
- [ ] 用戶體驗提升

#### PO-003: 實施異步並發處理
**描述**: The system MUST The system SHALL 使用異步編程優化多個API調用

**並發策略**:
```python
class AsyncRequestManager:
    """異步請求管理器"""

    async def fetch_multiple_data(self, requests: List[Dict]):
        """並行獲取多個數據源"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for req in requests:
                task = self._fetch_single_data(session, req)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._process_results(results)

    async def _fetch_single_data(self, session, request):
        """獲取單個數據源"""
        try:
            async with session.get(
                request["url"],
                timeout=request.get("timeout", 5)
            ) as response:
                return await response.json()
        except Exception as e:
            return {"error": str(e), "source": request["name"]}
```

**應用場景**:
```python
# 優化前: 串行獲取
data1 = await get_stock_data("0700.HK")  # 2秒
data2 = await get_weather_data()          # 1.5秒
data3 = await get_sports_scores()         # 1秒
# 總計: 4.5秒

# 優化後: 並行獲取
data1, data2, data3 = await asyncio.gather(
    get_stock_data("0700.HK"),
    get_weather_data(),
    get_sports_scores()
)
# 總計: 2秒 (最慢的時間)
```

**驗收條件**:
- [ ] 並發請求正確處理
- [ ] 錯誤隔離機制正常
- [ ] 響應時間減少 > 50%
- [ ] 資源使用合理

#### PO-004: 優化數據庫查詢
**描述**: The system MUST The system SHALL 優化投資組合和警報管理器的數據庫操作

**優化策略**:

1. **連接池**:
```python
class DatabasePool:
    """數據庫連接池"""

    def __init__(self, pool_size: int = 10):
        self.pool_size = pool_size
        self.pool = None

    async def init_pool(self):
        """初始化連接池"""
        self.pool = await aiosqlite.connect(
            "bot_data.db",
            check_same_thread=False
        )

    async def execute_query(self, query: str, params: tuple = None):
        """執行查詢"""
        async with self.pool.execute(query, params or ()) as cursor:
            return await cursor.fetchall()
```

2. **查詢優化**:
```python
# 優化前: N+1查詢問題
for user_id in user_ids:
    portfolio = await get_portfolio(user_id)  # N次查詢

# 優化後: 批量查詢
portfolios = await batch_get_portfolios(user_ids)  # 1次查詢
```

3. **索引優化**:
```sql
-- 為常用查詢字段添加索引
CREATE INDEX idx_portfolio_user_id ON portfolio(user_id);
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_active ON alerts(active, timestamp);
```

**驗收條件**:
- [ ] 數據庫查詢時間減少 > 60%
- [ ] 連接池正常工作
- [ ] 索引生效
- [ ] 查詢錯誤率 < 0.1%

#### PO-005: 實施性能監控
**描述**: The system MUST The system SHALL 創建性能監控模組，追蹤系統運行指標

**核心類**:
```python
class PerformanceMonitor:
    """性能監控器"""

    def __init__(self):
        self.metrics = defaultdict(list)
        self.alerts = []

    async def track_response_time(self, command: str, start_time: float):
        """追蹤命令響應時間"""
        elapsed = time.time() - start_time
        self.metrics[f"{command}_response_time"].append(elapsed)

    async def track_api_call(self, endpoint: str, success: bool, response_time: float):
        """追蹤API調用"""
        self.metrics[f"{endpoint}_api_call"].append({
            "success": success,
            "response_time": response_time,
            "timestamp": time.time()
        })

    async def track_cache_hit(self, cache_key: str):
        """追蹤緩存命中"""
        self.metrics["cache_hit"].append({
            "key": cache_key,
            "timestamp": time.time()
        })

    def get_performance_report(self) -> Dict:
        """生成性能報告"""
        return {
            "avg_response_time": self._calculate_avg_response_time(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "api_success_rate": self._calculate_api_success_rate(),
            "top_slow_commands": self._get_top_slow_commands(),
            "error_rate": self._calculate_error_rate(),
        }
```

**監控指標**:
```python
MONITORING_METRICS = {
    "response_times": {
        "description": "命令響應時間",
        "collection": "histogram",
        "unit": "seconds",
        "targets": {
            "avg": "< 1.5",
            "p95": "< 3.0",
            "p99": "< 5.0"
        }
    },
    "cache_performance": {
        "description": "緩存命中率",
        "collection": "percentage",
        "targets": {
            "hit_rate": "> 70%"
        }
    },
    "api_performance": {
        "description": "API成功率",
        "collection": "percentage",
        "targets": {
            "success_rate": "> 95%"
        }
    },
    "error_rates": {
        "description": "錯誤率",
        "collection": "percentage",
        "targets": {
            "error_rate": "< 2%"
        }
    }
}
```

**日誌格式**:
```python
LOG_FORMAT = (
    "%(asctime)s %(levelname)s "
    "[%(name)s] "
    "cmd=%(command)s "
    "time=%(response_time).3fs "
    "status=%(status)s "
    "cache=%(cache_hit)s "
    "%(message)s"
)
```

**驗收條件**:
- [ ] 監控指標正確收集
- [ ] 性能報告生成正常
- [ ] 警報機制工作
- [ ] 日誌格式標準化

#### PO-006: 優化內存使用
**描述**: The system MUST The system SHALL 優化內存使用，防止內存洩漏

**優化策略**:

1. **對象池**:
```python
class ObjectPool:
    """對象池，減少GC壓力"""

    def __init__(self, factory, max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self.pool = []

    async def acquire(self):
        """獲取對象"""
        if self.pool:
            return self.pool.pop()
        return self.factory()

    async def release(self, obj):
        """釋放對象"""
        if len(self.pool) < self.max_size:
            self._reset(obj)
            self.pool.append(obj)

    def _reset(self, obj):
        """重置對象狀態"""
        # 清理對象
        pass
```

2. **弱引用**:
```python
import weakref

class CacheWithWeakRef:
    """使用弱引用的緩存"""

    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value
```

3. **定期清理**:
```python
class MemoryManager:
    """內存管理器"""

    def __init__(self):
        self.cleanup_interval = 3600  # 每小時清理
        self._start_cleanup_task()

    async def _start_cleanup_task(self):
        """啟動定期清理任務"""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            await self._cleanup_unused_cache()
            await self._compact_memory()
```

**驗收條件**:
- [ ] 內存使用穩定
- [ ] 無明顯洩漏
- [ ] 定期清理正常
- [ ] GC壓力降低

#### PO-007: 實施連接池優化
**描述**: The system MUST The system SHALL 優化HTTP連接池，減少連接建立開銷

**連接池配置**:
```python
HTTP_POOL_CONFIG = {
    "conn_pool_size": 100,      # 連接池大小
    "conn_pool_lifetime": 300,  # 連接生存時間(秒)
    "keep_alive": True,         # 啟用keep-alive
    "timeout": {
        "connect": 5,            # 連接超時
        "read": 10,              # 讀取超時
        "total": 30              # 總超時
    },
    "retry": {
        "max_retries": 3,        # 最大重試次數
        "backoff_factor": 0.5,   # 退避因子
        "retry_on_status": [500, 502, 503, 504]
    }
}
```

**實現**:
```python
class OptimizedHttpClient:
    """優化的HTTP客戶端"""

    def __init__(self):
        self.session = None

    async def init_session(self):
        """初始化HTTP會話"""
        connector = aiohttp.TCPConnector(
            limit=HTTP_POOL_CONFIG["conn_pool_size"],
            keepalive_timeout=HTTP_POOL_CONFIG["conn_pool_lifetime"],
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(
            connect=HTTP_POOL_CONFIG["timeout"]["connect"],
            sock_read=HTTP_POOL_CONFIG["timeout"]["read"],
            total=HTTP_POOL_CONFIG["timeout"]["total"]
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

    async def request(self, method, url, **kwargs):
        """發送請求（帶重試）"""
        for attempt in range(HTTP_POOL_CONFIG["retry"]["max_retries"]):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status in HTTP_POOL_CONFIG["retry"]["retry_on_status"]:
                        await asyncio.sleep(
                            HTTP_POOL_CONFIG["retry"]["backoff_factor"] * (2 ** attempt)
                        )
                        continue
                    return await response.json()
            except Exception as e:
                if attempt == HTTP_POOL_CONFIG["retry"]["max_retries"] - 1:
                    raise
                await asyncio.sleep(0.1)
```

**驗收條件**:
- [ ] 連接複用率 > 80%
- [ ] 請求成功率 > 95%
- [ ] 超時處理正常
- [ ] 重試機制有效

## 🔍 測試需求

### 性能測試

#### T-PO-001: 響應時間測試
```python
@pytest.mark.asyncio
async def test_response_time():
    """測試命令響應時間"""
    bot = TestBot("test_token")
    commands = ["start", "help", "analyze 0700.HK", "weather", "score"]

    for cmd in commands:
        start_time = time.time()
        response = await bot.send_command(cmd)
        elapsed = time.time() - start_time

        assert elapsed < 1.5, f"{cmd} 響應時間過長: {elapsed:.3f}s"
```

#### T-PO-002: 緩存命中率測試
```python
@pytest.mark.asyncio
async def test_cache_hit_rate():
    """測試緩存命中率"""
    cache = UnifiedCacheManager()

    # 第一次請求（緩存未命中）
    await cache.set("test_key", "test_value", 300)
    data = await cache.get("test_key")
    assert data == "test_value"

    # 第二次請求（緩存命中）
    data = await cache.get("test_key")
    assert data == "test_value"

    # 驗證命中統計
    report = cache.get_performance_report()
    assert report["cache_hit_rate"] > 70
```

#### T-PO-003: 並發性能測試
```python
@pytest.mark.asyncio
async def test_concurrent_performance():
    """測試並發性能"""
    async def simulate_user():
        bot = TestBot("test_token")
        await bot.send_command("/weather")
        await bot.send_command("/score soccer")

    # 100個並發用戶
    tasks = [simulate_user() for _ in range(100)]
    start_time = time.time()
    await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    # 100個用戶總時間 < 30秒
    assert elapsed < 30
```

#### T-PO-004: 內存使用測試
```python
def test_memory_usage():
    """測試內存使用"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # 執行100次命令
    for _ in range(100):
        asyncio.run(bot.send_command("/weather"))

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # 內存增長 < 100MB
    assert memory_increase < 100 * 1024 * 1024
```

### 負載測試

#### T-PO-005: 壓力測試
```python
@pytest.mark.asyncio
async def test_load_testing():
    """24小時壓力測試"""
    bot = TestBot("test_token")
    commands = [
        "/analyze 0700.HK",
        "/weather",
        "/score soccer",
        "/portfolio",
        "/mark6"
    ]

    start_time = time.time()
    end_time = start_time + 86400  # 24小時

    error_count = 0
    request_count = 0

    while time.time() < end_time:
        for cmd in commands:
            try:
                response = await bot.send_command(cmd)
                if response.status_code != 200:
                    error_count += 1
                request_count += 1
            except Exception:
                error_count += 1
                request_count += 1

            await asyncio.sleep(1)  # 每秒1次請求

    error_rate = error_count / request_count
    assert error_rate < 0.02  # 錯誤率 < 2%
```

## 📊 性能基準

### 性能目標對比

| 指標 | 優化前 | 優化後 | 改進幅度 |
|------|--------|--------|----------|
| 平均響應時間 | 2.5秒 | 1.2秒 | -52% |
| 95分位響應時間 | 5.0秒 | 3.0秒 | -40% |
| 緩存命中率 | 0% | 75% | +75% |
| 並發用戶數 | 20 | 100 | +400% |
| 內存使用 | 300MB | 200MB | -33% |
| CPU使用率 | 80% | 50% | -38% |
| 服務可用性 | 97% | 99.5% | +2.5% |
| 錯誤率 | 5% | 1.5% | -70% |

### 監控儀表板

```python
DASHBOARD_CONFIG = {
    "metrics": [
        "response_time",
        "cache_hit_rate",
        "api_success_rate",
        "error_rate",
        "active_users",
        "memory_usage",
        "cpu_usage"
    ],
    "refresh_interval": 5,  # 5秒刷新
    "alert_thresholds": {
        "response_time": 3.0,
        "error_rate": 0.02,
        "cpu_usage": 0.80,
        "memory_usage": 0.90
    }
}
```

## 🔄 持續優化

### 自動優化
1. **動態調整緩存TTL**: 根據訪問頻率自動調整
2. **預測性加載**: 預測用戶請求，提前加載數據
3. **智能降級**: 高負載時自動關閉非核心功能

### 週期性維護
- **每日**: 檢查性能報告
- **每週**: 分析慢查詢和優化機會
- **每月**: 調優緩存策略和索引

## 📝 實施檢查清單

- [ ] PO-001: 實施統一緩存管理
- [ ] PO-002: 優化命令響應格式
- [ ] PO-003: 實施異步並發處理
- [ ] PO-004: 優化數據庫查詢
- [ ] PO-005: 實施性能監控
- [ ] PO-006: 優化內存使用
- [ ] PO-007: 實施連接池優化
- [ ] T-PO-001: 性能測試 - 響應時間
- [ ] T-PO-002: 性能測試 - 緩存命中率
- [ ] T-PO-003: 性能測試 - 並發性能
- [ ] T-PO-004: 性能測試 - 內存使用
- [ ] T-PO-005: 壓力測試
- [ ] 監控儀表板部署
- [ ] 性能基準驗證
- [ ] 文檔更新

---

**規格作者**: Claude Code
**審核狀態**: 待審核
**優先級**: 高
**估計工期**: 10天
**依賴**: 所有其他capabilities (最後實施)
