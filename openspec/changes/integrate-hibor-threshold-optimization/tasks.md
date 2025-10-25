# Implementation Tasks: HIBOR Threshold Optimization Integration

## Phase 1: Core Optimization Engine (2-3 days)

### 1.1 Create Base Optimizer Framework
- [ ] Create `src/optimization/__init__.py`
- [ ] Create `src/optimization/base_optimizer.py` with abstract class
  - [ ] Define abstract methods: `_generate_param_grid()`, `evaluate_params()`
  - [ ] Implement concrete methods: `grid_search()`, `sensitivity_analysis()`, `get_best_params()`
  - [ ] Add logging and progress tracking
  - [ ] Implement result ranking and filtering
- [ ] Create `src/optimization/optimization_utils.py` with shared utilities
  - [ ] Metric calculation functions (Sharpe, returns, max_drawdown, etc.)
  - [ ] Parameter hashing for caching
  - [ ] Result validation functions
- [ ] Write unit tests in `tests/test_base_optimizer.py`
  - [ ] Test parameter grid generation
  - [ ] Test sensitivity analysis
  - [ ] Test result ranking
- [ ] **Acceptance Criteria**: Base optimizer can be instantiated and inherited; 80% test coverage

### 1.2 Implement HIBOR Optimizer
- [ ] Create `src/optimization/hibor_optimizer.py`
  - [ ] Inherit from `BaseOptimizer`
  - [ ] Port parameter ranges from `hibor_threshold_optimization.py`
  - [ ] Implement `_generate_param_grid()` for HIBOR thresholds
  - [ ] Implement `evaluate_params()` to run HIBOR strategy
  - [ ] Support multi-metric optimization (Sharpe, returns, win_rate, profit_factor)
- [ ] Create `src/optimization/hibor_strategy.py` (adapted from `hibor_6m_prediction_strategy.py`)
  - [ ] Minimal version with signal generation and backtesting
  - [ ] Remove plotting/visualization code
  - [ ] Add configuration validation
- [ ] Write unit tests in `tests/test_hibor_optimizer.py`
  - [ ] Test parameter validation
  - [ ] Test grid search with small dataset
  - [ ] Test metric calculations
- [ ] **Acceptance Criteria**: HIBOR optimizer produces same results as standalone system within 5% margin

### 1.3 Implement RSI and MACD Optimizers
- [ ] Create `src/optimization/rsi_optimizer.py`
  - [ ] Parameter ranges: period [5-300, step 5], overbought [50-90, step 10], oversold [10-50, step 10]
  - [ ] Implement RSI calculation and signal generation
- [ ] Create `src/optimization/macd_optimizer.py`
  - [ ] Parameter ranges: fast [5-20], slow [15-40], signal [5-15]
  - [ ] Implement MACD calculation and signal generation
- [ ] Create `tests/test_rsi_optimizer.py` and `tests/test_macd_optimizer.py`
  - [ ] Basic functionality tests
  - [ ] Parameter range validation
- [ ] **Acceptance Criteria**: Each optimizer completes 50 parameter combos in < 30 seconds

### 1.4 Create Optimizer Registry
- [ ] Create `src/optimization/registry.py`
  - [ ] Define `OPTIMIZER_REGISTRY` dictionary
  - [ ] Implement `get_optimizer(strategy_name)` factory function
  - [ ] Implement `register_optimizer(name, class)` for extensibility
- [ ] Write tests in `tests/test_optimizer_registry.py`
- [ ] **Acceptance Criteria**: Registry can instantiate all optimizers; extensible for user-defined strategies

---

## Phase 2: API Integration (2-3 days)

### 2.1 Create API Routes
- [ ] Create `src/dashboard/optimization_routes.py`
  - [ ] `POST /api/optimize/{symbol}/{strategy}` - Start optimization
    - [ ] Validate symbol and strategy exist
    - [ ] Queue optimization task
    - [ ] Return task ID and status endpoint
  - [ ] `GET /api/optimize/{symbol}/{strategy}/results` - Get optimization results
    - [ ] Query top N results (default: 10, max: 100)
    - [ ] Filter by metric threshold
    - [ ] Support sorting by any metric
  - [ ] `GET /api/optimize/{symbol}/{strategy}/sensitivity` - Get sensitivity analysis
    - [ ] Return sensitivity data for visualization
  - [ ] `GET /api/optimize/runs` - List optimization runs
    - [ ] Filter by symbol, strategy, date range
    - [ ] Pagination support
  - [ ] `POST /api/optimize/{run_id}/apply` - Apply optimization result
    - [ ] Update active strategy parameters
- [ ] Integrate into `src/dashboard/api_routes.py`
- [ ] Write integration tests in `tests/test_optimization_api.py`
  - [ ] Test all endpoints with valid/invalid inputs
  - [ ] Test error handling
  - [ ] Test result persistence
- [ ] **Acceptance Criteria**: All endpoints functional; 80% test coverage; API docs auto-generated

### 2.2 Create Optimization Service Layer
- [ ] Create `src/dashboard/optimization_service.py`
  - [ ] `OptimizationService` class managing optimizer lifecycle
  - [ ] `start_optimization(symbol, strategy, params)` method
  - [ ] `get_results(symbol, strategy, filters)` method
  - [ ] `save_result_to_db(result)` method
  - [ ] `load_result_from_db(run_id)` method
- [ ] Write unit tests in `tests/test_optimization_service.py`
- [ ] **Acceptance Criteria**: Service handles all CRUD operations cleanly

### 2.3 Background Task Queue Setup
- [ ] Choose task queue: Celery (existing in CODEX) or APScheduler
- [ ] Create `src/tasks/optimization_tasks.py`
  - [ ] `optimize_strategy_task(symbol, strategy, **kwargs)` - Long-running task
  - [ ] Implement progress callback
  - [ ] Implement error handling and retry logic
- [ ] Write tests in `tests/test_optimization_tasks.py`
- [ ] **Acceptance Criteria**: Long optimizations don't block API; progress queryable

---

## Phase 3: Database Persistence (1-2 days)

### 3.1 Create ORM Models
- [ ] Create `src/models/optimization.py`
  - [ ] `OptimizationRun` model
    - Fields: id, strategy_name, symbol, created_at, metric, total_combinations, status
    - Relationship to OptimizationResult (1-to-many)
  - [ ] `OptimizationResult` model
    - Fields: id, run_id, param_hash, parameters (JSON), metrics (JSON), rank
    - Indexes: (run_id, rank), (param_hash) for dedup
- [ ] Create Alembic migration in `src/models/migrations/`
- [ ] Write tests in `tests/test_optimization_models.py`
- [ ] **Acceptance Criteria**: Models properly defined; migrations apply cleanly

### 3.2 Database Repository Layer
- [ ] Create `src/repository/optimization_repository.py`
  - [ ] `save_run(run: OptimizationRun)`
  - [ ] `save_result(result: OptimizationResult)`
  - [ ] `get_run(run_id)` with all results
  - [ ] `get_latest_run(symbol, strategy)`
  - [ ] `query_runs(filters)` - by symbol, strategy, date range
- [ ] Write repository tests in `tests/test_optimization_repository.py`
- [ ] **Acceptance Criteria**: All repository methods working; no N+1 queries

### 3.3 Caching Layer (Redis)
- [ ] Create `src/cache/optimization_cache.py`
  - [ ] Cache key format: `opt:{symbol}:{strategy}:{param_hash}`
  - [ ] TTL: 7 days
  - [ ] Invalidation on parameter change
- [ ] Integrate caching into `OptimizationService`
- [ ] Write tests in `tests/test_optimization_cache.py`
- [ ] **Acceptance Criteria**: Cache improves lookup speed by 10x

---

## Phase 4: Dashboard UI Components (2-3 days)

### 4.1 Create Parameter Grid Component
- [ ] Create `frontend/components/ParameterGrid.tsx`
  - [ ] Display all tested parameter combinations in table
  - [ ] Sortable by any metric column
  - [ ] Filterable by metric value ranges
  - [ ] Pagination for large result sets
  - [ ] "Apply" button to use selected parameters
- [ ] Write component tests in `frontend/__tests__/ParameterGrid.test.tsx`
- [ ] **Acceptance Criteria**: Table renders 1000+ rows efficiently; sorting works

### 4.2 Create Sensitivity Analysis Component
- [ ] Create `frontend/components/SensitivityCharts.tsx`
  - [ ] Three separate charts for three main parameters
  - [ ] Line plots showing metric vs parameter value
  - [ ] Highlight best parameter value
  - [ ] Interactive tooltips
- [ ] Write component tests
- [ ] **Acceptance Criteria**: Charts render correctly; no performance issues

### 4.3 Create Optimization Control Panel
- [ ] Create `frontend/pages/Optimization.tsx`
  - [ ] Strategy selector (dropdown)
  - [ ] Symbol selector (dropdown/search)
  - [ ] Metric selector for optimization
  - [ ] "Start Optimization" button
  - [ ] Progress indicator (% complete)
  - [ ] Estimated time remaining
  - [ ] "View Results" tab with Parameter Grid
  - [ ] "Sensitivity" tab with charts
  - [ ] "Compare" tab for side-by-side view
- [ ] Create `frontend/services/optimizationApi.ts` for API calls
- [ ] Write integration tests
- [ ] **Acceptance Criteria**: Full UI workflow functional; responsive design

### 4.4 Integrate into Existing Dashboard
- [ ] Add "Optimization" menu item to navigation
- [ ] Integrate new components into main dashboard layout
- [ ] Update dashboard routing
- [ ] Write E2E tests for full workflow
- [ ] **Acceptance Criteria**: New UI seamlessly integrated; no regression in existing features

---

## Phase 5: Testing and Validation (1-2 days)

### 5.1 Comprehensive Integration Tests
- [ ] Create `tests/test_optimization_integration.py`
  - [ ] Full workflow: optimize → save → retrieve → apply
  - [ ] Multi-strategy optimization
  - [ ] Large dataset performance test (1000+ rows)
  - [ ] Parallel optimization of multiple symbols
- [ ] **Acceptance Criteria**: All integration tests pass; no data corruption

### 5.2 Performance Benchmarking
- [ ] Create `tests/test_optimization_performance.py`
  - [ ] Benchmark: 100 combinations → < 30 seconds
  - [ ] Benchmark: Sensitivity analysis → < 2 minutes
  - [ ] Benchmark: API response → < 500ms
  - [ ] Memory usage monitoring (< 500MB)
- [ ] Generate performance report
- [ ] **Acceptance Criteria**: All performance targets met

### 5.3 Migration from Standalone System
- [ ] Deprecate `/hk-stock-quant-system/hibor_threshold_optimization.py`
- [ ] Create migration script to import existing results (if any)
- [ ] Update README with new API usage
- [ ] Create migration guide for users
- [ ] Archive old system code
- [ ] **Acceptance Criteria**: Zero data loss; backward compatibility where possible

---

## Phase 6: Documentation (1 day)

### 6.1 API Documentation
- [ ] Ensure OpenAPI/Swagger docs auto-generated from FastAPI
- [ ] Add example requests/responses for all endpoints
- [ ] Document parameter ranges for each strategy
- [ ] Document metrics available for optimization
- [ ] **Acceptance Criteria**: API docs complete and auto-generated

### 6.2 User Guide
- [ ] Create `docs/optimization-guide.md`
  - [ ] How to optimize HIBOR strategy
  - [ ] How to optimize RSI strategy
  - [ ] Interpreting results
  - [ ] Using sensitivity analysis
  - [ ] Applying optimized parameters
- [ ] Create `docs/extension-guide.md` for adding custom strategies
- [ ] **Acceptance Criteria**: Guides cover all use cases with examples

### 6.3 Developer Documentation
- [ ] Create `docs/optimization-architecture.md`
  - [ ] System design overview
  - [ ] Adding a new optimizer
  - [ ] Understanding result caching
  - [ ] Performance tuning
- [ ] Generate code documentation (Sphinx)
- [ ] **Acceptance Criteria**: Developers can extend system independently

---

## Phase 7: Deployment and Cleanup (1 day)

### 7.1 Final Integration
- [ ] Run full test suite: `pytest -v --cov=. --cov-report=term`
- [ ] Verify 80% minimum test coverage
- [ ] Run linting: `pylint src/optimization`, `black src/optimization`
- [ ] Update requirements.txt if new dependencies added
- [ ] **Acceptance Criteria**: No linting errors; tests pass; coverage ≥ 80%

### 7.2 Environment Setup
- [ ] Document new environment variables (if any)
- [ ] Update `.env.example`
- [ ] Update Docker setup if needed
- [ ] Test deployment on clean environment
- [ ] **Acceptance Criteria**: System runs on fresh install

### 7.3 Final Archive
- [ ] Archive change to `openspec/changes/archive/`
- [ ] Update relevant specs in `openspec/specs/`
- [ ] Create commit with all changes
- [ ] Update CHANGELOG.md with new feature
- [ ] **Acceptance Criteria**: All artifacts properly archived; ready for production

---

## Dependencies and Sequencing

```
Phase 1 (Core Engine)
  ├─ 1.1 Base Framework ──┐
  ├─ 1.2 HIBOR ───────────┼─→ Phase 2 (API) ───┐
  ├─ 1.3 RSI, MACD ──────┤                     ├─→ Phase 5 (Testing)
  └─ 1.4 Registry ───────┘                     │
                                                │
                      Phase 3 (Database) ──────┘
                         ├─ 3.1 Models
                         ├─ 3.2 Repository
                         └─ 3.3 Cache
                                 │
                      Phase 4 (UI) ────────────┘
                                 │
                      Phase 6 (Docs)
                                 │
                      Phase 7 (Deploy)
```

**Parallelizable Work**:
- Phases 1.1 and 1.2 can proceed in parallel with UI design
- Database migrations (3.1) can be prepared while API (2.1) is being built
- Documentation can be drafted early and refined throughout

---

## Success Metrics

By end of implementation:
- [ ] All 70+ tasks completed
- [ ] Test coverage ≥ 80%
- [ ] 5+ integration tests pass
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Backward compatibility maintained
- [ ] User can optimize and apply parameters via API + UI
