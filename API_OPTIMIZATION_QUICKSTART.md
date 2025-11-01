# API優化快速開始指南

## 🚀 立即開始實施

### 第1步: 環境準備
```bash
# 1. 安裝依賴
pip install redis slowapi prometheus-client

# 2. 設置環境變量
cp .env.example .env
# 編輯.env文件，添加:
REDIS_URL=redis://localhost:6379/0
ENABLE_CACHE=true
ENABLE_RATE_LIMIT=true
```

### 第2步: 創建基礎設施文件
```bash
# 創建目錄結構
mkdir -p src/dashboard/{cache,repositories,dataloaders,middleware}

# 創建緩存管理器
touch src/dashboard/cache/__init__.py
touch src/dashboard/cache/cache_manager.py

# 創建Repository基類
touch src/dashboard/repositories/__init__.py
touch src/dashboard/repositories/base_repository.py

# 創建統一API管理器
touch src/dashboard/unified_api_manager.py
```

### 第3步: 第一個優化 - 添加緩存

#### 步驟1: 創建緩存管理器 (30分鐘)
```python
# src/dashboard/cache/cache_manager.py
import redis
import json
import hashlib
from typing import Any, Optional, Callable

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 300  # 5分鐘

    def generate_key(self, prefix: str, **params) -> str:
        """生成緩存鍵"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存"""
        value = self.redis_client.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """設置緩存"""
        ttl = ttl or self.default_ttl
        self.redis_client.setex(key, ttl, json.dumps(value))

    def cache_result(self, ttl: int = 300, key_prefix: str = ""):
        """緩存裝飾器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                cache_key = self.generate_key(key_prefix, func=func.__name__, args=args, kwargs=kwargs)
                cached = await self.get(cache_key)

                if cached:
                    return cached

                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator

cache_manager = CacheManager()
```

#### 步驟2: 修改第一個API端點 (15分鐘)
```python
# 修改 src/dashboard/api_agents.py

from ..cache.cache_manager import cache_manager

@router.get("/list")
@cache_manager.cache_result(ttl=60, key_prefix="agents")
async def list_agents():
    """獲取Agent列表 - 帶緩存"""
    try:
        agents_list = []
        for agent_id, agent_data in agents_store.items():
            # 這裡已經使用了緩存
            agents_list.append({...})
        return agents_list
    except Exception as e:
        logger.error(f"獲取Agent列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 第4步: 測試緩存效果 (10分鐘)
```python
# 測試腳本 test_cache.py
import asyncio
from src.dashboard.cache.cache_manager import cache_manager

async def test():
    # 第一次調用 - 會查詢數據庫
    result1 = await cache_manager.get("agents:list:test")
    print(f"第一次查詢: {result1 is None}")

    # 設置緩存
    await cache_manager.set("agents:list:test", {"id": 1, "name": "test"})

    # 第二次調用 - 從緩存獲取
    result2 = await cache_manager.get("agents:list:test")
    print(f"第二次查詢: {result2 is not None}")
    print(f"緩存數據: {result2}")

asyncio.run(test())
```

### 第5步: 添加分頁支持 (30分鐘)
```python
# 修改任意列表API端點
@router.get("/list")
async def list_agents(
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(50, ge=1, le=100, description="每頁數量")
):
    """獲取Agent列表 - 帶分頁"""
    try:
        # 獲取所有數據
        all_agents = list(agents_store.values())

        # 計算分頁
        start = (page - 1) * size
        end = start + size
        paginated_agents = all_agents[start:end]

        # 返回分頁結果
        return {
            "items": paginated_agents,
            "total": len(all_agents),
            "page": page,
            "size": size,
            "pages": (len(all_agents) + size - 1) // size
        }
    except Exception as e:
        logger.error(f"獲取Agent列表失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔧 常用代碼片段

### 片段1: 緩存裝飾器
```python
from functools import wraps

def cached(ttl=300, key_prefix=""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成緩存鍵
            key = f"{key_prefix}:{func.__name__}"
            # 檢查緩存
            cached_result = await cache_manager.get(key)
            if cached_result:
                return cached_result
            # 執行函數
            result = await func(*args, **kwargs)
            # 設置緩存
            await cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator
```

### 片段2: Repository基類
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self):
        self.cache = cache_manager

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def list(
        self,
        page: int = 1,
        size: int = 50,
        filters: Optional[Dict] = None
    ) -> List[T]:
        pass

    @abstractmethod
    async def create(self, data: Dict) -> T:
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict) -> T:
        pass
```

### 片段3: 統一響應格式
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict

class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

    @classmethod
    def success(cls, data: Any):
        return cls(success=True, data=data)

    @classmethod
    def error(cls, error: str):
        return cls(success=False, error=error)
```

### 片段4: 分頁響應
```python
def paginated_response(items: List[Any], total: int, page: int, size: int):
    pages = (total + size - 1) // size
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }
```

### 片段5: 速率限制
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/agents")
@limiter.limit("100/minute")
async def get_agents(request: Request):
    return await agent_repo.list()
```

### 片段6: 認證中間件
```python
async def auth_middleware(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")

    # 公開端點豁免
    public_paths = ["/health", "/docs"]
    if request.url.path in public_paths:
        return await call_next(request)

    if not api_key:
        raise HTTPException(401, "缺少API密鑰")

    if not await validate_api_key(api_key):
        raise HTTPException(403, "無效的API密鑰")

    request.state.user = await get_user_from_key(api_key)
    return await call_next(request)
```

---

## ⚡ 快速實施檢查清單

### 基礎設施 (第1天)
- [ ] 安裝Redis
- [ ] 創建CacheManager類
- [ ] 測試Redis連接
- [ ] 創建統一響應格式

### 緩存應用 (第2天)
- [ ] 為Top 5 API端點添加緩存
- [ ] 測試緩存命中率
- [ ] 驗證TTL過期
- [ ] 監控性能提升

### 分頁功能 (第3天)
- [ ] 為所有列表端點添加分頁
- [ ] 測試分頁邊界情況
- [ ] 驗證總數計算
- [ ] 更新前端分頁組件

### Repository模式 (第4-5天)
- [ ] 創建BaseRepository類
- [ ] 實現AgentRepository
- [ ] 重構Agent API使用Repository
- [ ] 實現其他Repository

### DataLoader (第6天)
- [ ] 創建DataLoader基類
- [ ] 實現Agent性能Loader
- [ ] 應用到API端點
- [ ] 驗證查詢減少

### 安全與監控 (第7天)
- [ ] 實現API認證
- [ ] 添加速率限制
- [ ] 配置Prometheus指標
- [ ] 添加健康檢查

---

## 📈 性能測試腳本

```python
# performance_test.py
import asyncio
import time
import aiohttp
import statistics

async def test_api_performance(url: str, num_requests: int = 100):
    """測試API性能"""
    async with aiohttp.ClientSession() as session:
        times = []

        for _ in range(num_requests):
            start = time.time()
            async with session.get(url) as response:
                await response.json()
            end = time.time()
            times.append(end - start)

        avg_time = statistics.mean(times) * 1000  # ms
        p95_time = sorted(times)[int(len(times) * 0.95)] * 1000
        min_time = min(times) * 1000
        max_time = max(times) * 1000

        print(f"\n=== API性能測試: {url} ===")
        print(f"請求數: {num_requests}")
        print(f"平均響應時間: {avg_time:.2f}ms")
        print(f"P95響應時間: {p95_time:.2f}ms")
        print(f"最快響應: {min_time:.2f}ms")
        print(f"最慢響應: {max_time:.2f}ms")
        print(f"吞吐量: {num_requests / sum(times):.2f} QPS")

asyncio.run(test_api_performance("http://localhost:8001/api/agents"))
```

---

## 🔍 故障排除

### 問題1: 緩存未生效
**檢查清單**:
- [ ] Redis服務是否運行
- [ ] 緩存鍵是否正確生成
- [ ] TTL設置是否合理
- [ ] 緩存裝飾器是否正確應用

### 問題2: 分頁結果錯誤
**檢查清單**:
- [ ] 總數計算是否正確
- [ ] start/end索引是否正確
- [ ] 邊界條件測試
- [ ] 空結果集處理

### 問題3: 性能沒有提升
**檢查清單**:
- [ ] 緩存命中率是否達到80%
- [ ] 數據庫查詢是否減少
- [ ] 是否有阻塞操作
- [ ] 監控指標是否正常

---

## 📞 獲得幫助

如果遇到問題:
1. 檢查日誌文件: `quant_system.log`
2. 監控Redis狀態: `redis-cli ping`
3. 檢查API指標: `/metrics` 端點
4. 查看詳細錯誤: 設置 `LOG_LEVEL=DEBUG`

---

**開始時間**: ⏰ 現在
**預計完成**: 📅 7天 (每天2-3小時)
**第一個可見成果**: 📦 第1天結束 - 緩存生效
