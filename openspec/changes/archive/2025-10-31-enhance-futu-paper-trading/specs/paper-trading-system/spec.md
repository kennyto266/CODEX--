# 模拟交易系统技术规格

## ADDED Requirements

### 1. FutuPaperTradingController

#### 1.1 基础功能
**Requirement**: 系统 SHALL 实现独立的模拟交易控制器，负责管理整个模拟交易流程

**Components**:
- 交易状态管理
- 信号处理和验证
- 订单执行协调
- 实时监控

**Methods**:
```python
class FutuPaperTradingController:
    async def initialize() -> bool
    async def start_trading() -> None
    async def stop_trading() -> None
    async def execute_signal(signal: TradeSignal) -> bool
    async def get_status() -> Dict[str, Any]
```

**Scenarios**:
- **Scenario 1.1**: 初始化控制器
  - Given: 系统启动
  - When: 调用 `initialize()`
  - Then: 连接到富途 DEMO 环境，验证凭证，建立连接

- **Scenario 1.2**: 执行交易信号
  - Given: 控制器已初始化，收到交易信号
  - When: 调用 `execute_signal(signal)`
  - Then: 验证信号 → 检查风险 → 下单 → 监控执行 → 返回结果

- **Scenario 1.3**: 停止交易
  - Given: 控制器正在运行
  - When: 调用 `stop_trading()`
  - Then: 取消所有待执行订单，关闭连接，释放资源

#### 1.2 配置管理
**Requirement**: 系统 SHALL 支持灵活的配置管理，包括初始资金、风险参数等

**Configuration Options**:
- `initial_balance`: 初始虚拟资金 (默认: 1,000,000 HKD)
- `max_position_size`: 单笔最大仓位 (默认: 100,000 HKD)
- `max_daily_trades`: 每日最大交易次数 (默认: 100)
- `trading_enabled`: 是否启用交易 (默认: True)

**Scenarios**:
- **Scenario 1.4**: 自定义初始资金
  - Given: 控制器配置了 `initial_balance=500000`
  - When: 初始化系统
  - Then: 虚拟账户余额为 500,000 HKD

### 2. PaperTradingEngine

#### 2.1 订单管理
**Requirement**: 系统 SHALL 提供完整的订单生命周期管理，包括创建、跟踪、取消和成交

**Features**:
- 订单创建和验证
- 实时状态跟踪
- 订单匹配和成交
- 异常处理

**Methods**:
```python
class PaperTradingEngine:
    async def create_order(order: Order) -> str
    async def cancel_order(order_id: str) -> bool
    async def get_order_status(order_id: str) -> OrderStatus
    async def get_all_orders() -> List[Order]
```

**Scenarios**:
- **Scenario 2.1**: 创建限价买单
  - Given: 账户余额充足，市场开盘
  - When: 创建 00700.HK 限价买单，价格 350 HKD，数量 1000
  - Then: 订单状态为 PENDING，等待价格匹配

- **Scenario 2.2**: 限价单成交
  - Given: 存在限价买单，价格 350 HKD
  - When: 市场价格达到 350 HKD
  - Then: 订单自动成交，状态变为 FILLED，扣除资金，增加持仓

- **Scenario 2.3**: 取消订单
  - Given: 存在待执行订单
  - When: 调用 `cancel_order(order_id)`
  - Then: 订单状态变为 CANCELLED，释放冻结资金

#### 2.2 仓位管理
**Requirement**: 系统 SHALL 实时跟踪持仓信息，计算市值和盈亏

**Features**:
- 持仓信息存储
- 实时市值计算
- 未实现盈亏计算
- 持仓集中度监控

**Methods**:
```python
class PaperTradingEngine:
    async def get_positions() -> List[Position]
    async def update_position(symbol: str, quantity: Decimal, price: Decimal)
    async def get_portfolio_value() -> Decimal
    async def get_unrealized_pnl() -> Decimal
```

**Scenarios**:
- **Scenario 2.4**: 更新持仓
  - Given: 持有 00700.HK 1000股，成本价 350 HKD
  - When: 以 360 HKD 价格再买入 500股
  - Then: 持仓更新为 1500股，成本价调整为 353.33 HKD

- **Scenario 2.5**: 计算组合价值
  - Given: 多个持仓
  - When: 调用 `get_portfolio_value()`
  - Then: 返回所有持仓市值总和加上现金余额

### 3. 风险控制

#### 3.1 交易前检查
**Requirement**: 系统 SHALL 在执行交易前进行全面的风险检查

**Checks**:
- 资金充足性检查
- 仓位限制检查
- 单日交易次数检查
- 集中度风险检查

**Methods**:
```python
async def validate_trade(order: Order) -> Tuple[bool, str]:
    """验证交易是否符合风险要求"""
    pass
```

**Scenarios**:
- **Scenario 3.1**: 资金不足
  - Given: 账户余额 50,000 HKD
  - When: 尝试下单 100,000 HKD
  - Then: 交易被拒绝，返回"资金不足"错误

- **Scenario 3.2**: 超过单日交易次数
  - Given: 当日已交易 100 次
  - When: 尝试第 101 次交易
  - Then: 交易被拒绝，返回"超过日交易次数限制"

#### 3.2 紧急停止机制
**Requirement**: 系统 SHALL 支持紧急停止所有交易活动

**Features**:
- 一键停止所有交易
- 取消所有待执行订单
- 锁定交易功能

**Methods**:
```python
async def emergency_stop() -> bool:
    """紧急停止所有交易"""
    pass

async def unlock_trading() -> bool:
    """解锁交易功能"""
    pass
```

**Scenarios**:
- **Scenario 3.3**: 紧急停止
  - Given: 系统正常运行，有待执行订单
  - When: 调用 `emergency_stop()`
  - Then: 所有订单被取消，交易功能被锁定，需要手动解锁

### 4. 实时监控

#### 4.1 交易性能指标
**Requirement**: 系统 SHALL 计算和展示交易性能指标

**Metrics**:
- 总收益率
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率

**Methods**:
```python
async def get_performance_metrics() -> Dict[str, float]:
    """获取性能指标"""
    pass
```

**Scenarios**:
- **Scenario 4.1**: 计算收益率
  - Given: 初始资金 1,000,000，当前总资产 1,100,000
  - When: 调用 `get_performance_metrics()`
  - Then: 返回总收益率 10%

#### 4.2 实时数据推送
**Requirement**: 系统 SHALL 通过 WebSocket 实时推送交易状态更新

**Events**:
- 订单状态变更
- 成交确认
- 持仓变更
- 账户余额更新

**Scenarios**:
- **Scenario 4.2**: 订单成交推送
  - Given: 客户端订阅订单事件
  - When: 订单成交
  - Then: 客户端收到 WebSocket 消息，包含订单详情

### 5. API 接口

#### 5.1 RESTful API
**Requirement**: 系统 SHALL 提供完整的 RESTful API 接口

**Endpoints**:
- `GET /api/paper-trading/status` - 获取交易状态
- `POST /api/paper-trading/orders` - 创建订单
- `GET /api/paper-trading/orders` - 获取订单列表
- `DELETE /api/paper-trading/orders/{id}` - 取消订单
- `GET /api/paper-trading/positions` - 获取持仓
- `GET /api/paper-trading/account` - 获取账户信息
- `GET /api/paper-trading/performance` - 获取性能指标

**Scenarios**:
- **Scenario 5.1**: 通过 API 下单
  - Given: 客户端发送 POST 请求到 `/api/paper-trading/orders`
  - When: 请求包含订单信息 (symbol, side, quantity, price)
  - Then: 订单被创建，返回订单 ID

#### 5.2 配置接口
**Requirement**: 系统 SHALL 支持动态修改交易配置

**Endpoints**:
- `GET /api/paper-trading/config` - 获取配置
- `PUT /api/paper-trading/config` - 更新配置

**Scenarios**:
- **Scenario 5.3**: 修改交易限额
  - Given: 当前单笔交易限额 100,000 HKD
  - When: PUT 请求更新为 200,000 HKD
  - Then: 配置更新，后续交易使用新限额

### 6. 日志和审计

#### 6.1 交易日志
**Requirement**: 系统 SHALL 记录所有交易操作和系统事件

**Log Types**:
- 交易操作日志
- 系统事件日志
- 错误日志
- 性能日志

**Scenarios**:
- **Scenario 6.1**: 交易日志记录
  - Given: 执行了一笔交易
  - When: 交易完成
  - Then: 在日志中记录交易详情、时间戳、结果

#### 6.2 审计报告
**Requirement**: 系统 SHALL 生成交易审计报告

**Features**:
- 交易历史查询
- 盈亏分析
- 风险评估报告
- 导出功能

**Scenarios**:
- **Scenario 6.2**: 生成月度报告
  - Given: 系统运行一个月
  - When: 请求生成月度审计报告
  - Then: 返回包含所有交易、盈亏、风险的详细报告

## MODIFIED Requirements

### 1. FutuTradingAPI 增强

**Modification**: 系统 SHALL 在现有 `FutuTradingAPI` 基础上增强模拟交易功能

**Added Methods**:
```python
async def get_paper_trading_status() -> Dict[str, Any]
async def reset_paper_account(balance: Decimal = Decimal('1000000')) -> bool
async def get_trading_statistics() -> Dict[str, Any]
```

**Rationale**: 复用现有实现，降低开发成本，确保兼容性

**Backward Compatibility**: ✅ 完全兼容现有 API

### 2. 仪表板集成

**Modification**: 系统 SHALL 扩展现有仪表板添加模拟交易页面

**Added Views**:
- 模拟交易概览页
- 持仓管理页
- 交易历史页
- 性能分析页

**Integration**: 通过 WebSocket 实时更新数据

## REMOVED Requirements

无

## Dependencies

### 前置依赖
- ✅ `FutuTradingAPI` - 已实现 SIMULATE 环境
- ✅ `RealtimeExecutionEngine` - 现有执行引擎
- ✅ `SignalManager` - 现有信号管理
- ✅ WebSocket 支持 - 现有基础设施

### 被依赖组件
- 📋 `Dashboard` - 将添加模拟交易视图
- 📋 `API Routes` - 将添加新的端点
- 📋 `Monitoring` - 将扩展监控功能

## Error Handling

### 连接错误
- **Error**: 富途 API 连接失败
- **Handling**: 自动重试 (最多 3 次)，日志记录，告警通知

### 交易错误
- **Error**: 订单执行失败
- **Handling**: 取消订单，释放资金，记录错误，返回失败状态

### 数据错误
- **Error**: 市场数据异常
- **Handling**: 使用缓存数据，标记数据状态，告警通知

## Performance Requirements

- **订单响应时间**: < 1 秒
- **并发交易数**: 支持 10+ 并发订单
- **内存使用**: < 500MB
- **CPU 使用**: < 50% (正常负载)

## Security Requirements

- **环境隔离**: 仅使用 DEMO/SIMULATE 环境
- **凭证保护**: API 密钥加密存储
- **操作审计**: 所有操作记录日志
- **访问控制**: API 接口认证

## Testing Requirements

### 单元测试
- Controller 单元测试 (覆盖率 > 90%)
- Engine 单元测试 (覆盖率 > 90%)
- 风险控制单元测试 (覆盖率 > 90%)

### 集成测试
- API 集成测试
- WebSocket 集成测试
- 端到端测试

### 性能测试
- 并发交易测试
- 压力测试
- 稳定性测试
