# Design: HIBOR Threshold Optimization Integration

## Architectural Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CODEX Main System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Parameter Optimization Framework              │  │
│  │  (src/optimization/base_optimizer.py)                 │  │
│  │                                                        │  │
│  │  - Grid search engine                                │  │
│  │  - Multiprocessing handler                           │  │
│  │  - Result ranking/filtering                          │  │
│  │  - Sensitivity analysis                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                  │
│                           │ (inheritance)                    │
│        ┌──────────────────┼──────────────────┐              │
│        │                  │                  │              │
│   ┌─────────┐        ┌──────────┐      ┌─────────┐         │
│   │  HIBOR  │        │   RSI    │      │  MACD   │         │
│   │Optimizer│        │Optimizer │      │Optimizer│         │
│   └────┬────┘        └────┬─────┘      └────┬────┘         │
│        │                  │                  │              │
│        └──────────────────┼──────────────────┘              │
│                           │                                 │
│                    ┌──────▼────────┐                        │
│                    │   FastAPI     │                        │
│                    │   Routes      │                        │
│                    │  (/api/opt/)  │                        │
│                    └──────┬────────┘                        │
│                           │                                 │
│                    ┌──────▼────────┐                        │
│                    │   Dashboard   │                        │
│                    │    UI         │                        │
│                    │  (React/JS)   │                        │
│                    └───────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Design Decisions

### 1. Base Optimizer Pattern

**Decision**: Create abstract `BaseOptimizer` class with standard interface.

**Rationale**:
- Enables code reuse across all strategy optimizers
- Allows strategies to implement custom logic while maintaining consistency
- Simplifies API routing (single endpoint handles all strategies)

**Implementation**:
```python
# src/optimization/base_optimizer.py
class BaseOptimizer(ABC):
    @abstractmethod
    def _generate_param_grid(self) -> List[Dict]: ...

    @abstractmethod
    def evaluate_params(self, params: Dict) -> Dict: ...

    def grid_search(self, metric='sharpe_ratio') -> List[Dict]: ...

    def sensitivity_analysis(self) -> Dict: ...
```

### 2. Multiprocessing Strategy

**Decision**: Use `multiprocessing.Pool` with configurable worker count.

**Rationale**:
- HIBOR optimization already uses this successfully
- Better than threading for CPU-bound operations (GIL bypass)
- Better than async for backtest calculations
- Scales well with core count

**Configuration**:
- Default workers = min(8, cpu_count())
- Configurable via environment variable: `OPTIMIZER_MAX_WORKERS`

### 3. Result Storage

**Decision**: Store optimization results in database with denormalized key fields.

**Schema**:
```
optimization_runs
├── id (PK)
├── strategy_name
├── symbol
├── created_at
├── metric
├── total_combinations
├── top_result (JSON)

optimization_results
├── id (PK)
├── run_id (FK)
├── param_hash (unique per param combo)
├── parameters (JSON)
├── metrics (JSON)
├── rank
```

**Rationale**:
- Query by strategy/symbol quickly
- Track optimization history
- Enable result comparison
- param_hash allows deduplication

### 4. API Design

**Decision**: RESTful endpoints with strategy name as path parameter.

**Endpoints**:
- `POST /api/optimize/{symbol}/{strategy}` - Start optimization
- `GET /api/optimize/{symbol}/{strategy}/results` - Get top results
- `GET /api/optimize/{symbol}/{strategy}/sensitivity` - Get sensitivity analysis
- `GET /api/optimize/runs` - List all optimization runs
- `POST /api/optimize/{run_id}/save` - Save specific result as active strategy

**Rationale**:
- Clear resource hierarchy
- Separates read/write concerns
- Allows long-running operations (background task queue)

### 5. Dashboard Integration

**Decision**: Add optimization panel to existing dashboard with three views.

**Views**:
1. **Parameter Grid**: Interactive table showing all tested combinations
2. **Sensitivity Charts**: Line plots showing how each parameter affects metrics
3. **Comparison**: Side-by-side comparison of current vs best parameters

**Interaction**:
- Select metric to optimize (dropdown)
- Filter by metric threshold (slider)
- Export results (CSV/JSON)
- Apply selected params to active strategy

## Implementation Architecture

### Phase 1: Core Optimization Engine

```
src/optimization/
├── __init__.py
├── base_optimizer.py        # Abstract base class
├── optimization_utils.py    # Shared utilities
├── hibor_optimizer.py       # HIBOR implementation
├── rsi_optimizer.py         # RSI implementation
└── macd_optimizer.py        # MACD implementation
```

### Phase 2: API Integration

```
src/dashboard/
├── api_routes.py            # Add /api/optimize/* routes
├── optimization_service.py   # Service layer
└── models/optimization.py    # SQLAlchemy models
```

### Phase 3: Database

```
src/models/
├── optimization.py          # OptimizationRun, OptimizationResult
└── migrations/              # Alembic migrations
```

### Phase 4: Dashboard UI

```
frontend/
├── pages/
│   └── optimization.tsx      # Optimization page
├── components/
│   ├── ParameterGrid.tsx
│   ├── SensitivityCharts.tsx
│   └── ComparisonView.tsx
└── services/
    └── optimizationApi.ts
```

## Key Design Patterns

### Pattern 1: Strategy Factory

Enable adding new strategies without modifying core code:

```python
OPTIMIZER_REGISTRY = {
    'hibor': HIBOROptimizer,
    'rsi': RSIOptimizer,
    'macd': MACDOptimizer,
}

def get_optimizer(strategy_name: str) -> BaseOptimizer:
    return OPTIMIZER_REGISTRY[strategy_name]()
```

### Pattern 2: Async Task Queue

For long-running optimizations:

```python
@app.post("/api/optimize/{symbol}/{strategy}")
async def start_optimization(symbol: str, strategy: str):
    task = celery.send_task('optimize', (symbol, strategy))
    return {'task_id': task.id, 'status': 'queued'}
```

### Pattern 3: Caching Optimization Results

Avoid re-running same optimization:

```python
class OptimizationCache:
    def get_key(self, symbol, strategy, params_hash) -> str:
        return f"opt:{symbol}:{strategy}:{params_hash}"

    def get(self, key) -> Optional[Dict]:
        return redis.get(key)

    def set(self, key, value):
        redis.set(key, value, ex=86400*7)  # 7 days
```

## Testing Strategy

### Unit Tests
- Test each optimizer independently with synthetic data
- Verify parameter grid generation
- Validate metric calculations

### Integration Tests
- Test API endpoints with real backtest data
- Verify database persistence
- Test multiprocessing with actual strategy calculations

### Performance Tests
- Benchmark optimization speed for 100+ combinations
- Test scaling with core count
- Verify memory usage doesn't exceed limits

## Performance Targets

- **Grid Search (100 combinations)**: < 30 seconds
- **Sensitivity Analysis**: < 2 minutes
- **API Response (GET results)**: < 500ms
- **Memory Usage**: < 500MB per optimization

## Migration Path from Standalone System

1. Copy `hibor_6m_prediction_strategy.py` to new location
2. Create `HIBOROptimizer` wrapper inheriting from `BaseOptimizer`
3. Port parameter ranges to configuration
4. Add API endpoint forwarding to new implementation
5. Update dashboard to use new API
6. Archive old standalone system

## Open Questions / Future Work

1. Should support batch optimization of multiple symbols?
2. Should enable parameter ranges to be defined in UI instead of code?
3. Should support Monte Carlo or Bayesian optimization beyond grid search?
4. Should track who initiated each optimization for audit trail?
5. Should support A/B testing of different optimization strategies?

---

**Validation**: Run `openspec validate integrate-hibor-threshold-optimization --strict` to check this design.
