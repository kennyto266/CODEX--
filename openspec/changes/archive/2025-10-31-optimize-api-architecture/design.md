# API架構優化 - 技術設計方案

## 1. 統一API管理器 (UnifiedAPIManager)

### 設計目標
將分散的6個API路由器整合成統一的、可管理的架構。

### 架構設計
```python
class UnifiedAPIManager:
    """統一API管理器 - 管理所有API路由和中間件"""

    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.middleware: List[Callable] = []
        self.error_handlers: Dict[int, Callable] = {}
        self.before_request_handlers: List[Callable] = []

    def register_router(self, name: str, router: APIRouter):
        """註冊API路由器"""
        self.routers[name] = router

    def add_middleware(self, middleware: Callable):
        """添加中間件"""
        self.middleware.append(middleware)

    def apply_to_app(self, app: FastAPI):
        """將所有路由和中間件應用到FastAPI應用"""
```

### 優勢
- **集中管理**: 所有API端點在一處管理
- **一致性**: 統一的錯誤處理、日誌記錄、認證
- **可擴展性**: 易於添加新API模塊
- **可觀測性**: 統一的監控和度量

## 2. 緩存層架構

### 多級緩存設計
```
┌─────────────────────────────────────┐
│           Client Request            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        L1: In-Memory Cache          │
│      (LRU, TTL: 60s)                │
│   - 熱點數據 (Agent狀態)             │
└──────────────┬──────────────────────┘
               │ Miss
               ▼
┌─────────────────────────────────────┐
│        L2: Redis Cache              │
│      (TTL: 300s)                    │
│   - 會話數據                        │
│   - 計算結果                        │
└──────────────┬──────────────────────┘
               │ Miss
               ▼
┌─────────────────────────────────────┐
│        L3: Database                 │
│      (持久化存儲)                    │
│   - 歷史數據                        │
│   - 配置數據                        │
└─────────────────────────────────────┘
```

### 緩存鍵策略
```python
# 緩存鍵格式
CACHE_KEYS = {
    'agents': 'agents:list:{filters_hash}',
    'agent_detail': 'agent:detail:{agent_id}',
    'strategies': 'strategies:list:{filters_hash}',
    'backtest_results': 'backtest:results:{user_id}:{limit}',
    'portfolio_risk': 'risk:portfolio:{portfolio_id}:{timestamp_date}',
}

def generate_cache_key(prefix: str, **params) -> str:
    """生成緩存鍵"""
    params_str = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"{prefix}:{params_hash}"
```

### 緩存裝飾器
```python
def cache_result(ttl: int = 300, key_prefix: str = ""):
    """緩存結果裝飾器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash_args(args, kwargs)}"
            cached_result = await cache_manager.get(cache_key)

            if cached_result:
                return cached_result

            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

## 3. Repository模式

### Repository基類設計
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Repository基類 - 抽象數據訪問層"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.table_name = ""
        self.model_class = None

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[T]:
        pass

    @abstractmethod
    async def create(self, data: Dict) -> T:
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict) -> T:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
```

### 具體Repository示例
```python
class AgentRepository(BaseRepository[Agent]):
    """Agent數據訪問層"""

    def __init__(self, cache_manager: CacheManager):
        super().__init__(cache_manager)
        self.table_name = "agents"
        self.default_ttl = 60  # Agent狀態緩存60秒

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        cache_key = f"agent:detail:{agent_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            return Agent(**cached)

        # 從數據庫查詢
        agent_data = await self._fetch_from_db(agent_id)
        if agent_data:
            await self.cache.set(cache_key, agent_data, self.default_ttl)
            return Agent(**agent_data)

        return None

    async def list(
        self,
        filters: Optional[Dict] = None,
        sort_by: str = "last_activity",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Agent]:
        # 使用緩存
        cache_key = f"agents:list:{self._hash_filters(filters)}:{sort_by}:{sort_order}:{limit}:{offset}"
        cached = await self.cache.get(cache_key)

        if cached:
            return [Agent(**data) for data in cached]

        # 從數據庫查詢
        agents_data = await self._fetch_list_from_db(filters, sort_by, sort_order, limit, offset)

        # 緩存結果
        await self.cache.set(cache_key, agents_data, self.default_ttl)

        return [Agent(**data) for data in agents_data]
```

## 4. DataLoader模式 (數據預取)

### 問題場景
```python
# N+1查詢問題
agents = await agent_repo.list()  # 查詢1次
for agent in agents:
    # 每次循環都查詢 - N次查詢
    agent.performance = await performance_repo.get_by_agent_id(agent.id)
```

### DataLoader解決方案
```python
class DataLoader:
    """數據預取器 - 解決N+1查詢問題"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_loads: Dict[str, List[Callable]] = {}
        self.results_cache: Dict[str, Any] = {}

    async def load(self, key: str, loader_func: Callable) -> Any:
        """加載單個數據（使用批處理）"""
        if key in self.results_cache:
            return self.results_cache[key]

        if key not in self.pending_loads:
            self.pending_loads[key] = []

        future = asyncio.Future()
        self.pending_loads[key].append(future)

        # 如果達到批次大小，立即執行
        if len(self.pending_loads[key]) >= self.batch_size:
            await self._execute_batch(key, loader_func)

        return await future

    async def _execute_batch(self, key: str, loader_func: Callable):
        """執行批次加載"""
        batch = self.pending_loads.pop(key)
        keys = [f.key for f in batch]

        # 批量加載
        results = await loader_func(keys)

        # 分發結果
        for future, result in zip(batch, results):
            self.results_cache[future.key] = result
            future.set_result(result)

class AgentPerformanceLoader:
    """Agent性能數據預取器"""

    def __init__(self, performance_repo: PerformanceRepository):
        self.loader = DataLoader()
        self.performance_repo = performance_repo

    async def get_performance(self, agent_id: str):
        """獲取單個Agent性能（使用批處理）"""
        return await self.loader.load(
            agent_id,
            self.performance_repo.get_by_agent_ids
        )

# 使用示例
async def get_agents_with_performance():
    agents = await agent_repo.list()
    performance_loader = AgentPerformanceLoader(performance_repo)

    # 並行加載所有Agent的性能數據（只需1次數據庫查詢）
    tasks = [performance_loader.get_performance(a.id) for a in agents]
    performances = await asyncio.gather(*tasks)

    for agent, perf in zip(agents, performances):
        agent.performance = perf
```

## 5. 中間件架構

### 中間件鏈
```
請求 → 認證中間件 → 速率限制 → 日誌 → 緩存檢查 → 業務邏輯
                ↓
響應 ← 錯誤處理 ← 日誌 ← 緩存設置 ← 業務邏輯
```

### 認證中間件
```python
async def auth_middleware(request: Request, call_next):
    """API密鑰認證中間件"""
    api_key = request.headers.get("X-API-Key")

    # 公開端點豁免
    public_paths = ["/health", "/docs", "/openapi.json"]
    if request.url.path in public_paths:
        return await call_next(request)

    if not api_key:
        raise HTTPException(401, "缺少API密鑰")

    if not await validate_api_key(api_key):
        raise HTTPException(403, "無效的API密鑰")

    request.state.api_key = api_key
    request.state.user = await get_user_from_api_key(api_key)

    response = await call_next(request)
    return response
```

### 速率限制中間件
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")  # 每分鐘100次請求
async def rate_limit_middleware(request: Request, call_next):
    response = await call_next(request)
    return response
```

### 日誌中間件
```python
async def logging_middleware(request: Request, call_next):
    """結構化日誌中間件"""
    start_time = time.time()

    # 記錄請求
    logger.info(
        "API Request",
        extra={
            "type": "api_request",
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "api_key": request.state.get("api_key", "anonymous"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 記錄響應
        logger.info(
            "API Response",
            extra={
                "type": "api_response",
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "API Error",
            extra={
                "type": "api_error",
                "error": str(e),
                "process_time": process_time,
            },
            exc_info=True
        )
        raise
```

## 6. 統一響應格式

### 響應模型
```python
class APIResponse(BaseModel):
    """統一API響應格式"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def success(cls, data: Any = None, meta: Optional[Dict] = None):
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def error(cls, error: str, status_code: int = 400):
        return cls(success=False, error=error)

class PaginatedResponse(BaseModel):
    """分頁響應格式"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class APIResponseWithMeta(BaseModel):
    """帶元數據的響應"""
    success: bool
    data: Any
    meta: Dict[str, Any]
    links: Dict[str, str]  # 分頁鏈接
```

### 響應工具函數
```python
def create_success_response(data: Any, meta: Optional[Dict] = None):
    """創建成功響應"""
    return APIResponse.success(data, meta)

def create_error_response(error: str, status_code: int = 400):
    """創建錯誤響應"""
    return JSONResponse(
        status_code=status_code,
        content=APIResponse.error(error).dict()
    )

def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    base_url: str
):
    """創建分頁響應"""
    pages = (total + size - 1) // size

    meta = {
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
    }

    links = {
        "self": f"{base_url}?page={page}&size={size}",
        "next": f"{base_url}?page={page + 1}&size={size}" if page < pages else None,
        "prev": f"{base_url}?page={page - 1}&size={size}" if page > 1 else None,
        "first": f"{base_url}?page=1&size={size}",
        "last": f"{base_url}?page={pages}&size={size}"
    }

    return APIResponseWithMeta(
        success=True,
        data=items,
        meta=meta,
        links=links
    )
```

## 7. API端點優化示例

### 優化前
```python
@router.get("/agents")
async def get_agents():
    # 每次請求都查詢數據庫
    agents_data = []
    for agent_id, agent_info in agents_store.items():
        # 額外查詢性能和日誌
        performance = await get_agent_performance(agent_id)
        logs = await get_agent_logs(agent_id, limit=10)

        agents_data.append({
            "id": agent_id,
            "info": agent_info,
            "performance": performance,
            "recent_logs": logs
        })

    return {"agents": agents_data}
```

### 優化後
```python
@router.get("/agents")
@cache_result(ttl=60, key_prefix="agents")
async def get_agents(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    sort_by: str = Query("last_activity"),
    fields: Optional[str] = Query(None)  # 字段過濾
):
    # 使用Repository模式
    filters = {"status": status} if status else None
    agents = await agent_repo.list(
        filters=filters,
        sort_by=sort_by,
        page=page,
        size=size
    )

    # 使用DataLoader預取性能數據
    performance_loader = AgentPerformanceLoader(performance_repo)
    tasks = [performance_loader.get_performance(a.id) for a in agents]
    performances = await asyncio.gather(*tasks)

    # 組裝響應數據
    response_data = []
    for agent, perf in zip(agents, performances):
        data = {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "last_activity": agent.last_activity,
            "performance": perf
        }
        response_data.append(data)

    # 字段過濾
    if fields:
        requested_fields = fields.split(",")
        response_data = [
            {k: v for k, v in item.items() if k in requested_fields}
            for item in response_data
        ]

    # 分頁
    total = await agent_repo.count(filters)
    return create_paginated_response(response_data, total, page, size, "/api/agents")
```

## 8. 配置管理

### 配置結構
```python
# config/api_config.py
class APIConfig:
    """API配置"""

    # 緩存配置
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_AGENTS: int = 60
    CACHE_TTL_STRATEGIES: int = 300
    CACHE_TTL_RISK: int = 120

    # 速率限制
    RATE_LIMIT_DEFAULT: str = "1000/hour"
    RATE_LIMIT_AUTH: str = "100/minute"

    # 分頁
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # 性能
    DATALOADER_BATCH_SIZE: int = 100
    API_TIMEOUT: int = 30

# 使用
config = APIConfig()
```

## 9. 監控和度量

### 性能指標
```python
from prometheus_client import Counter, Histogram, Gauge

# 定義指標
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'api_active_connections',
    'Number of active API connections'
)

# 中間件中使用
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    active_connections.inc()

    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        return response
    finally:
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        active_connections.dec()
```

## 10. 測試策略

### 單元測試
```python
# tests/test_cache_manager.py
import pytest

@pytest.mark.asyncio
async def test_cache_get_or_set():
    cache = CacheManager()
    await cache.set("test_key", "test_value", 60)
    result = await cache.get("test_key")
    assert result == "test_value"

@pytest.mark.asyncio
async def test_cache_expiration():
    cache = CacheManager()
    await cache.set("test_key", "test_value", 1)
    await asyncio.sleep(1.1)
    result = await cache.get("test_key")
    assert result is None
```

### 集成測試
```python
# tests/test_api_agents.py
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_get_agents_with_cache():
    client = TestClient(app)

    # 第一次請求
    response1 = client.get("/api/agents?page=1&size=10")
    assert response1.status_code == 200

    # 第二次請求（應該使用緩存）
    response2 = client.get("/api/agents?page=1&size=10")
    assert response2.status_code == 200

    # 響應應該相同
    assert response1.json() == response2.json()
```

## 11. 遷移策略

### 向後兼容
```python
# 保留舊端點作為別名
@router.get("/agents", deprecated=True)
async def get_agents_legacy():
    """舊版API端點（已棄用）"""
    return await get_agents()

# 在OpenAPI文檔中標記為棄用
@router.get("/agents", deprecated=True, tags=["Agents"])
async def get_agents():
    return await get_agents()
```

### 功能開關
```python
# config/features.py
class FeatureFlags:
    USE_NEW_API = os.getenv("USE_NEW_API", "false").lower() == "true"
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    ENABLE_DATALOADER = os.getenv("ENABLE_DATALOADER", "true").lower() == "true"

# 在API中使用
if FeatureFlags.USE_NEW_API:
    router = create_new_api_router()
else:
    router = create_old_api_router()
```

這個設計方案提供了完整的技術實施細節，確保API優化工作能夠順利進行並達到預期效果。
