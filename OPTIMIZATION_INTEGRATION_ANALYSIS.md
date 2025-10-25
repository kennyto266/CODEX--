# CODEX 策略优化框架 - 现状分析与集成计划

## 执行摘要

项目中**已经存在完整的策略优化框架**，分布在两处：
1. **src/strategy_management/strategy_optimizer.py** (904行) - 抽象层，支持7种算法
2. **hk-stock-quant-system/unified_strategy_optimizer.py** (854行) - 生产级别实现，包含多进程

**关键缺失**: 两个框架都**缺乏与数据库的集成**和**API暴露**，这才是真正需要做的工作。

---

## 第1部分：现有优化框架详解

### 1.1 src/strategy_management/strategy_optimizer.py

**特点**: 高度抽象，支持多种算法

**关键类**:
```python
class StrategyOptimizer:
    # 支持的算法：
    - _grid_search()
    - _random_search()
    - _bayesian_optimization()
    - _genetic_algorithm()
    - _particle_swarm()
    - _simulated_annealing()
    - _machine_learning_optimization()

    # 关键方法：
    async def optimize_strategy(instance, parameter_space, algorithm, max_iterations)
```

**问题**:
- 没有具体的参数评估实现（`_evaluate_parameters()` 是抽象的）
- 无法直接用于真实策略优化
- 需要与实际回测引擎集成

### 1.2 hk-stock-quant-system/unified_strategy_optimizer.py

**特点**: 生产级别，实现完整、经过验证

**关键功能**:
```python
class UnifiedStrategyOptimizer:
    # 核心方法：
    def optimize() -> Dict  # 完整的优化流程
    def _evaluate_params() -> Dict  # 单参数组合评估
    def grid_search() -> Dict  # 网格搜索（带交叉验证）
    def evaluate_strategy() -> Dict  # 完整的性能指标计算

    # 性能指标包括：
    - sharpe_ratio, sortino_ratio
    - annual_return, max_drawdown
    - win_rate, profit_loss_ratio
    - avg_holding_period, trade_count
```

**优势**:
- 多进程支持（默认8核或自动检测）
- 完整的性能指标计算
- 交叉验证（5折）
- 内存管理（批处理、垃圾回收）
- 经过实际交易验证

---

## 第2部分：真实需要做的工作

### 必做项（核心功能）

#### 1. **数据库持久化** ⭐ 高优先级
```
当前状态: 无优化结果表
需要创建:
  - optimization_runs 表
    - id, symbol, strategy_name, created_at
    - metric, total_combinations, status
    - best_parameters (JSON), best_metrics (JSON)

  - optimization_results 表
    - id, run_id, rank
    - parameter_hash, parameters (JSON), metrics (JSON)
    - Indexes: (run_id, rank), (symbol, strategy_name)
```

#### 2. **API 端点** ⭐ 高优先级
```
需要在 src/dashboard/api_routes.py 中添加：

POST /api/optimize/{symbol}/{strategy}
  请求: metric='sharpe_ratio', preset='default'
  响应: task_id, status, created_at

GET /api/optimize/{task_id}/status
  响应: 进度百分比, 预计剩余时间

GET /api/optimize/{symbol}/{strategy}/results
  请求: limit=10, metric='sharpe_ratio'
  响应: 排序的参数组合 + 指标

GET /api/optimize/{symbol}/{strategy}/sensitivity
  响应: 参数敏感性分析数据

GET /api/optimize/history
  请求: symbol, strategy, date_range
  响应: 历史优化运行列表
```

#### 3. **背景任务管理** ⭐ 中高优先级
```
当前状态: 无异步优化支持
需要: 集成 Celery 或 APScheduler
  - 长时间运行的优化不阻塞API
  - WebSocket推送实时进度
  - 可以取消正在运行的优化
```

#### 4. **与真实回测引擎的集成** ⭐ 中高优先级
```
当前状态: unified_strategy_optimizer 使用模拟的 strategy.evaluate()
需要: 连接到 EnhancedBacktestEngine
  - 使用真实的回测计算
  - 包含交易成本
  - 实时返回性能指标
```

### 可选项（增强功能）

#### 5. **高级算法** (scikit-optimize集成)
- 贝叶斯优化改进版（使用 skopt.gp_minimize）
- Hyperband 算法
- BOHB (Bayesian Optimization and HyperBand)

#### 6. **仪表板UI组件**
- 参数网格可视化表格
- 敏感性分析图表
- 优化历史对比

#### 7. **分布式计算** (Ray集成)
- 多机器优化
- 云就绪基础设施

---

## 第3部分：集成路线图

### 阶段1: 核心集成（第1-2周）
```
目标: 建立完整的优化→数据库→API流程

1.1 创建数据库表
    - 创建 OptimizationRun 和 OptimizationResult SQLAlchemy 模型
    - 创建 Alembic 迁移

1.2 创建 OptimizationRepository
    - save_run(run) / save_result(result)
    - get_run(run_id) with results
    - query_runs(filters)

1.3 集成 UnifiedStrategyOptimizer 到 CODEX
    - 复制 unified_strategy_optimizer.py 到 src/optimization/
    - 创建适配器使用 EnhancedBacktestEngine
    - 实现参数验证

1.4 创建 OptimizationService 层
    - start_optimization(symbol, strategy, metric)
    - get_results(task_id, filters)
    - apply_parameters(symbol, strategy, params)

时间: 40-60 小时
```

### 阶段2: API和后台任务（第3周）
```
目标: 完整的REST API和异步支持

2.1 API 端点
    - POST /api/optimize/{symbol}/{strategy}
    - GET /api/optimize/{task_id}/status
    - GET /api/optimize/{symbol}/{strategy}/results

2.2 后台任务
    - 集成 Celery 或 APScheduler
    - 实现优化任务队列
    - 添加进度回调

时间: 20-30 小时
```

### 阶段3: UI和高级功能（第4-5周）
```
目标: 完整的用户界面和高级特性

3.1 仪表板组件
    - React 参数表格组件
    - 敏感性分析图表

3.2 高级算法
    - 贝叶斯优化改进
    - Hyperband 支持

时间: 30-40 小时
```

### 总投入: 90-130 小时（3-4周全职）

---

## 第4部分：不需要重新创建的东西

❌ **不要做这些**:
1. ~~创建新的 BaseOptimizer 抽象类~~ - 已经有了（虽然不完美）
2. ~~实现 Grid Search~~ - 已经完全实现
3. ~~实现 Genetic Algorithm~~ - 已经完全实现
4. ~~参数验证逻辑~~ - 已经有了
5. ~~多进程框架~~ - 已经有了
6. ~~性能指标计算~~ - 已经完全实现

✅ **只需要做这些**:
1. 数据库表 + Repository 层
2. API 端点
3. 后台任务集成
4. 真实回测引擎集成
5. UI 组件（可选）

---

## 第5部分：具体行动步骤

### 步骤1: 准备 (2 小时)
```bash
# 1. 复制生产级优化器到 CODEX
cp hk-stock-quant-system/unified_strategy_optimizer.py \
   src/optimization/production_optimizer.py

# 2. 查看 EnhancedBacktestEngine 的接口
grep -n "def run_backtest\|def evaluate" \
   src/backtest/enhanced_backtest_engine.py

# 3. 检查 SQLAlchemy 模型位置
ls -la src/models/
```

### 步骤2: 创建数据库层 (8 小时)
```python
# src/models/optimization.py
class OptimizationRun(Base):
    __tablename__ = 'optimization_runs'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    metric = Column(String(50))  # 'sharpe_ratio', 'return' 等
    best_parameters = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

class OptimizationResult(Base):
    __tablename__ = 'optimization_results'
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('optimization_runs.id'))
    rank = Column(Integer)
    parameters = Column(Text)  # JSON
    metrics = Column(Text)  # JSON
```

### 步骤3: 创建 Repository 和 Service (10 小时)
```python
# src/repository/optimization_repository.py
class OptimizationRepository:
    def save_run(self, run: OptimizationRun)
    def save_result(self, result: OptimizationResult)
    def get_run(self, run_id: int)
    def query_runs(self, symbol, strategy, limit=10)

# src/dashboard/optimization_service.py
class OptimizationService:
    def start_optimization(self, symbol, strategy, metric)
    def get_results(self, run_id, filters)
    def apply_parameters(self, symbol, strategy, params)
```

### 步骤4: 创建 API 端点 (6 小时)
```python
# src/dashboard/api_routes.py - 新增
@app.post("/api/optimize/{symbol}/{strategy}")
async def start_optimization(symbol: str, strategy: str, body: OptimizeRequest):
    service = OptimizationService()
    run_id = await service.start_optimization(symbol, strategy, body.metric)
    return {"task_id": run_id, "status": "started"}

@app.get("/api/optimize/{symbol}/{strategy}/results")
async def get_results(symbol: str, strategy: str, limit: int = 10):
    service = OptimizationService()
    results = await service.get_results(symbol, strategy, limit)
    return results
```

### 步骤5: 后台任务集成 (4 小时)
```python
# src/tasks/optimization_tasks.py
from celery import shared_task

@shared_task
def optimize_strategy_task(symbol, strategy, metric):
    optimizer = UnifiedStrategyOptimizer(symbol)
    results = optimizer.optimize()
    save_to_database(results)
    return results
```

---

## 第6部分：验证清单

### 完成后应该能做：
- [ ] 通过 API 启动策略优化（POST /api/optimize/0700.hk/rsi）
- [ ] 查看优化进度（GET /api/optimize/{task_id}/status）
- [ ] 获取优化结果排序列表（GET /api/optimize/0700.hk/rsi/results）
- [ ] 获取敏感性分析数据（GET /api/optimize/0700.hk/rsi/sensitivity）
- [ ] 查看历史优化运行（GET /api/optimize/history）
- [ ] 应用最优参数（POST /api/optimize/{run_id}/apply）
- [ ] 在仪表板中查看优化历史

### 性能目标：
- ✅ 100个参数组合 < 30秒（multiprocessing）
- ✅ 敏感性分析 < 2分钟
- ✅ API 响应 < 500ms
- ✅ 内存使用 < 500MB

---

## 第7部分：关键文件映射

| 需求 | 对应文件 | 状态 |
|-----|--------|------|
| 参数网格生成 | `hk-stock-quant-system/unified_strategy_optimizer.py:60` | ✅ 已有 |
| 多进程执行 | `hk-stock-quant-system/unified_strategy_optimizer.py:154` | ✅ 已有 |
| 性能指标计算 | `hk-stock-quant-system/unified_strategy_optimizer.py:218` | ✅ 已有 |
| 数据库模型 | `src/models/optimization.py` | ❌ 需要创建 |
| API 端点 | `src/dashboard/api_routes.py` | ❌ 需要添加 |
| 后台任务 | `src/tasks/optimization_tasks.py` | ❌ 需要创建 |
| 服务层 | `src/dashboard/optimization_service.py` | ❌ 需要创建 |

---

## 建议

与其创建新的 BaseOptimizer 抽象，不如：

1. **直接使用** `UnifiedStrategyOptimizer` - 已经经过验证
2. **包装它** 在 Service 层进行数据库集成
3. **通过 API** 暴露功能
4. **逐步迁移** src/strategy_management/strategy_optimizer.py 使用相同的数据库/API

这样做会快得多，风险更低。
