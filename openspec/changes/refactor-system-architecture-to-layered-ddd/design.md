# 架構重構技術設計文檔

## 背景

本設計文檔詳細闡述了將 codex-- 項目從當前的 "多功能集成" 架構重構為 "分層架構 + DDD + 事件驅動" 的技術決策。

## 設計目標與非目標

### 目標 (Goals)
1. **降低複雜性**: 通過分層架構將複雜系統分解為可管理的模塊
2. **提升可維護性**: 清晰的業務邊界和職責分離
3. **增強可測試性**: 依賴倒置和接口隔離
4. **提高性能**: 異步處理、多級緩存、並行計算
5. **改進可觀測性**: 完整的日誌、指標、追蹤系統

### 非目標 (Non-Goals)
- 1. 不改變現有業務邏輯 (僅重構架構)
- 2. 不修改數據庫模式 (保持兼容性)
- 3. 不重新設計 UI/UX (保持界面不變)
- 4. 不引入新的編程語言 (繼續使用 Python)
- 5. 不改變部署方式 (保持容器化)

## 架構決策

### 1. 分層架構選擇

**決策**: 採用經典的四層架構

**原因**:
- Python 生態系統成熟支持
- 與現有 FastAPI 框架自然契合
- 團隊熟悉層次化思維
- 避免過度工程 (微服務)

**替代方案考慮**:
- ❌ 六邊形架構 (Hexagonal): 過度複雜，收益不足以抵銷成本
- ❌ 洋蔥架構 (Onion): 與分層架構類似，但學習曲線更陡
- ✅ **分層架構**: 平衡了簡單性和功能性

**層次定義**:

```python
# 依賴方向 (從上到下)
Interface Layer      → Application Layer
        ↓                    ↓
Application Layer    → Domain Layer
        ↓                    ↓
Domain Layer         → Infrastructure Layer
```

**關鍵原則**:
- 每層只能依賴下層，不能跨層依賴
- 領域層是核心，不依賴其他層
- 接口層只依賴應用層，不直接訪問基礎設施

### 2. 領域驅動設計 (DDD)

**決策**: 實施核心 DDD 概念 (不使用完整 Framwork)

**原因**:
- 需要清晰的業務邊界 (現有系統缺乏)
- 需要統一的領域語言 (Ubiquitous Language)
- 現有系統業務邏輯分散，需要聚合

**DDD 元素實施**:

```python
# 領域實體 (Entity)
class Order:
    """訂單實體 - 擁有身份標識和業務規則"""
    def __init__(self, order_id: OrderId, ...):
        self._id = order_id
        self._status = OrderStatus.PENDING

    def execute(self) -> None:
        """業務邏輯: 執行訂單"""
        if self._status != OrderStatus.PENDING:
            raise BusinessRuleViolation("訂單已執行")
        self._status = OrderStatus.EXECUTED

# 領域服務 (Domain Service)
class OrderService:
    """訂單服務 - 跨聚合的業務邏輯"""
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    def cancel_expired_orders(self) -> List[Order]:
        """取消過期訂單"""
        expired = self._order_repo.find_expired()
        for order in expired:
            order.cancel()
        return expired

# 倉儲 (Repository)
class OrderRepository(ABC):
    """訂單倉儲 - 抽象數據訪問"""
    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Order:
        pass

    @abstractmethod
    async def save(self, order: Order) -> None:
        pass
```

**聚合設計**:
```
Order Aggregate (訂單聚合):
    ├── Order (根實體)
    ├── OrderLine[]
    └── Execution[]

Portfolio Aggregate (投資組合聚合):
    ├── Portfolio (根實體)
    ├── Position[]
    └── Transaction[]
```

**領域事件**:
```python
@dataclass
class DomainEvent:
    """領域事件 - 表示業務事實"""
    event_id: EventId
    aggregate_id: AggregateId
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime

class OrderExecuted(DomainEvent):
    """訂單已執行事件"""
    event_type = "Order.Executed"
```

### 3. 事件驅動架構

**決策**: 實施輕量級事件總線 (不引入 Kafka)

**原因**:
- 現有系統規模不需要企業級消息隊列
- 簡化系統複雜度
- 快速實施和調試

**事件總線設計**:
```python
class EventBus:
    """事件總線 - 內存實現，後續可替換為 Redis/Kafka"""
    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = defaultdict(list)
        self._middlewares: List[Callable] = []

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        """訂閱事件"""
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent):
        """發布事件"""
        # 執行中間件
        for middleware in self._middlewares:
            await middleware(event)

        # 發送給所有處理器
        handlers = self._handlers[type(event)]
        for handler in handlers:
            await handler(event)
```

**事件處理器示例**:
```python
class TradeExecutionHandler:
    """交易執行處理器"""
    def __init__(self, portfolio_repo: PortfolioRepository):
        self._portfolio_repo = portfolio_repo

    async def handle(self, event: TradeExecuted):
        """處理交易執行事件"""
        # 更新投資組合
        portfolio = await self._portfolio_repo.find_by_id(event.portfolio_id)
        portfolio.apply_trade(event.trade)

        # 發布下一個事件
        await event_bus.publish(PortfolioUpdated(event.portfolio_id))
```

### 4. 依賴注入 (DI)

**決策**: 使用簡單的容器實現 (不引入 Spring 級別的 DI 框架)

**原因**:
- Python 生態沒有成熟的 DI 框架
- 避免過度工程
- 手動 DI 足以滿足需求

**DI 容器設計**:
```python
class DIContainer:
    """簡單的依賴注入容器"""
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type, implementation: Type, singleton: bool = True):
        """註冊服務"""
        self._services[interface] = (implementation, singleton)

    async def resolve(self, interface: Type) -> Any:
        """解析依賴"""
        if interface in self._singletons:
            return self._singletons[interface]

        if interface not in self._services:
            raise ValueError(f"Service not registered: {interface}")

        implementation, is_singleton = self._services[interface]
        instance = implementation()

        if is_singleton:
            self._singletons[interface] = instance

        return instance

# 使用示例
container = DIContainer()
container.register(OrderRepository, InMemoryOrderRepository, singleton=True)
container.register(OrderService, OrderService, singleton=False)

order_service = await container.resolve(OrderService)
```

### 5. 異步架構

**決策**: 全棧異步化 (async/await)

**原因**:
- I/O 密集型應用 (數據獲取、API 調用)
- Python 3.10+ 支持成熟的異步生態
- 顯著提升併發性能

**異步模式**:
```python
# 異步數據獲取
class MarketDataService:
    async def get_price(self, symbol: str) -> float:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/{symbol}")
            return response.json()["price"]

# 異步緩存
class Cache:
    async def get(self, key: str) -> Optional[Any]:
        return await self._redis.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self._redis.setex(key, ttl, json.dumps(value))
```

### 6. 緩存策略

**決策**: 三級緩存架構

**設計**:
```python
class CacheStrategy:
    """三級緩存策略"""

    @lru_cache(maxsize=1000)
    def get_l1(self, key: str) -> Any:
        """L1: 內存緩存 - 毫秒級"""
        return self._l2.get(key)

    async def get(self, key: str) -> Optional[Any]:
        # L1 緩存
        value = self.get_l1(key)
        if value is not None:
            return value

        # L2 緩存 (Redis)
        value = await self._l2.get(key)
        if value is not None:
            self._l1.set(key, value)
            return value

        # L3 緩存 (數據庫)
        value = await self._l3.get(key)
        if value is not None:
            await self._l2.set(key, value, ttl=300)
            self._l1.set(key, value)
            return value

        return None
```

### 7. 配置管理

**決策**: Pydantic-Settings + YAML

**配置層級**:
1. `config/base.yaml` - 基礎配置 (所有環境通用)
2. `config/development.yaml` - 開發環境覆蓋
3. `config/production.yaml` - 生產環境覆蓋
4. `config/local.yaml` - 本地覆蓋 (gitignore)

**實施**:
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """應用設置"""

    # 數據庫
    database_url: str = "sqlite:///./app.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # 日誌
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

## 數據模型設計

### 統一 ID 類型
```python
from typing import NewType
from uuid import UUID

OrderId = NewType('OrderId', UUID)
PortfolioId = NewType('PortfolioId', UUID)
TradeId = NewType('TradeId', UUID)
UserId = NewType('UserId', UUID)
```

### 實體關係圖

```
┌─────────────┐       ┌─────────────┐
│   Order     │       │  Portfolio  │
├─────────────┤       ├─────────────┤
│ - id        │       │ - id        │
│ - status    │       │ - name      │
│ - symbol    │◄──────┤ - owner_id  │
│ - quantity  │       │             │
│ - price     │       └─────────────┘
└─────────────┘                │
         │                     │
         │ has_many            │ has_many
         ▼                     ▼
┌─────────────┐       ┌─────────────┐
│ Execution   │       │  Position   │
├─────────────┤       ├─────────────┤
│ - id        │       │ - id        │
│ - order_id  │       │ - symbol    │
│ - timestamp │       │ - quantity  │
│ - price     │       │ - avg_price │
└─────────────┘       └─────────────┘
```

## 關鍵設計模式

### 1. Repository Pattern
**目的**: 隔離領域邏輯和數據訪問

```python
class OrderRepository(ABC):
    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        pass

    @abstractmethod
    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        pass

    @abstractmethod
    async def save(self, order: Order) -> None:
        pass

# 實現
class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: Dict[OrderId, Order] = {}

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order
```

### 2. Unit of Work Pattern
**目的**: 管理事務和一致性

```python
class UnitOfWork:
    """工作單元 - 管理事務"""
    def __init__(self):
        self._orders = InMemoryOrderRepository()
        self._portfolios = InMemoryPortfolioRepository()
        self._changes = []

    async def commit(self):
        """提交所有更改"""
        for change in self._changes:
            await change()
        self._changes.clear()

    async def rollback(self):
        """回滾所有更改"""
        self._changes.clear()
```

### 3. Factory Pattern
**目的**: 創建複雜對象

```python
class OrderFactory:
    """訂單工廠"""
    @staticmethod
    def create_limit_order(
        symbol: str,
        quantity: int,
        price: float,
        side: OrderSide
    ) -> Order:
        """創建限價單"""
        return Order(
            order_id=OrderId(uuid4()),
            symbol=symbol,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
            side=side
        )
```

## 錯誤處理策略

### 分層錯誤處理
```python
# 基礎設施層 - 技術錯誤
class DataAccessError(Exception):
    """數據訪問錯誤"""

# 領域層 - 業務錯誤
class BusinessRuleViolation(Exception):
    """業務規則違規"""
    def __init__(self, message: str, rule: str):
        super().__init__(message)
        self.rule = rule

# 應用層 - 應用錯誤
class ApplicationError(Exception):
    """應用錯誤"""

# 接口層 - 展示錯誤
@app.exception_handler(BusinessRuleViolation)
async def business_error_handler(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=400,
        content={"error": "Business Rule Violation", "message": str(exc)}
    )
```

## 性能考量

### 1. 數據庫優化
- 使用連接池 (asyncpg for PostgreSQL)
- 實施批量操作
- 避免 N+1 查詢 (使用 JOIN 或預取)
- 添加適當索引

### 2. 緩存策略
- L1: 內存緩存 (LRU, 1000 items)
- L2: Redis 緩存 (TTL: 5 分鐘)
- L3: 數據庫緩存 (持久化)
- 緩存失效: 事件驅動 + TTL

### 3. 異步併發
- 使用 `asyncio.gather()` 併發多個請求
- 實施連接池限制 (避免資源耗盡)
- 使用信號量控制併發度

### 4. 監控指標
```python
# 關鍵性能指標 (KPI)
METRICS = {
    "api_request_duration": Histogram("api_request_duration_seconds"),
    "api_request_count": Counter("api_requests_total"),
    "cache_hit_ratio": Gauge("cache_hit_ratio"),
    "database_query_duration": Histogram("db_query_duration_seconds"),
    "active_websocket_connections": Gauge("ws_connections_active"),
}
```

## 安全設計

### 1. 輸入驗證
```python
from pydantic import BaseModel, validator

class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    price: float

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[0-9]{4}\.HK$', v):
            raise ValueError('Invalid symbol format')
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0 or v > 1000000:
            raise ValueError('Quantity must be between 1 and 1,000,000')
        return v
```

### 2. 速率限制
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/orders")
@limiter.limit("10/minute")
async def create_order(request: Request, order: OrderRequest):
    # 實現訂單創建
    pass
```

### 3. 審計日誌
```python
class AuditLogger:
    """審計日誌記錄器"""

    async def log_trade(self, user_id: UserId, trade: Trade):
        logger.info(
            "Trade executed",
            extra={
                "user_id": str(user_id),
                "trade_id": str(trade.id),
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "price": trade.price,
                "timestamp": trade.timestamp.isoformat(),
                "audit": True  # 標記為審計事件
            }
        )
```

## 測試策略

### 測試金字塔
```
        /\
       /  \        E2E Tests (10%)
      /    \
     /------\
    /        \      Integration Tests (20%)
   /          \
  /------------\
 /              \    Unit Tests (70%)
/________________\
```

### 測試示例
```python
# 單元測試
class TestOrder:
    def test_execute_pending_order(self):
        order = OrderFactory.create_limit_order(
            "0700.HK", 100, 350.0, OrderSide.BUY
        )
        order.execute()
        assert order.status == OrderStatus.EXECUTED

    def test_cancel_already_executed_order_raises_error(self):
        order = OrderFactory.create_limit_order("0700.HK", 100, 350.0, OrderSide.BUY)
        order.execute()
        with pytest.raises(BusinessRuleViolation):
            order.cancel()

# 集成測試
class TestOrderService:
    @pytest.mark.asyncio
    async def test_cancel_expired_orders(self):
        service = OrderService(InMemoryOrderRepository())
        # 創建過期訂單
        expired_order = OrderFactory.create_limit_order("0700.HK", 100, 350.0, OrderSide.BUY)
        # ... 設置過期時間
        cancelled = await service.cancel_expired_orders()
        assert len(cancelled) == 1
        assert cancelled[0].status == OrderStatus.CANCELLED
```

## 遷移策略

### 階段性遷移
1. **Phase 1**: 建立新架構，同時運行舊系統 (平行運行)
2. **Phase 2**: 逐步將模塊遷移到新架構 (每次一個模塊)
3. **Phase 3**: 驗證穩定性，移除舊代碼

### 向後兼容性
- 保持現有 API 端點不變
- 數據格式保持兼容
- 配置遷移腳本支持
- 平滑的數據遷移

## 風險與緩解

### 識別的風險

| 風險 | 可能性 | 影響 | 緩解策略 |
|------|--------|------|----------|
| 性能下降 | 中 | 高 | 全面性能測試，基準測試 |
| 業務邏輯錯誤 | 低 | 高 | 完整測試覆蓋，業務驗證 |
| 遷移期間系統中斷 | 中 | 中 | 藍綠部署，快速回滾 |
| 團隊學習曲線 | 高 | 中 | 文檔，培訓，漸進式遷移 |
| 第三方依賴問題 | 低 | 中 | 鎖定版本，完整測試 |

### 緩解措施
- 完整的測試覆蓋 (單元、集成、E2E)
- 基準測試和性能監控
- 藍綠部署或金絲雀發布
- 詳細的回滾計劃
- 完整的審計日誌

## 實施建議

### 開發團隊結構
- **架構師**: 1 人 (負責整體設計和決策)
- **核心開發**: 2-3 人 (實施基礎設施和領域層)
- **業務開發**: 2-3 人 (實施業務邏輯)
- **測試工程師**: 1 人 (負責測試和質量保證)

### 開發節奏
- 每 2 週一個 Sprint
- 每週進度檢查和風險評估
- 每 Sprint 結束進行演示和反饋
- 持續集成和部署

### 工具鏈
- **版本控制**: Git + GitHub
- **CI/CD**: GitHub Actions
- **代碼質量**: Black, isort, mypy, flake8
- **測試**: pytest, coverage.py
- **文檔**: MkDocs, OpenAPI/Swagger
- **監控**: Prometheus, Grafana, ELK Stack

---

**設計版本**: 1.0.0
**最後更新**: 2025-10-31
**設計師**: Claude Code
**審核狀態**: 待審核
