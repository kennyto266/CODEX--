# Proposal: Integrate HIBOR Threshold Optimization into CODEX Main System

## Why

The `hk-stock-quant-system` contains a proven, working parameter optimization system for HIBOR strategies that users have successfully executed. However, this powerful functionality is isolated in a separate subsystem, creating three critical problems:

1. **Fragmentation**: Users must manage separate optimization workflows and systems
2. **Limited Discoverability**: Optimization capabilities not exposed through main CODEX dashboard
3. **Code Duplication**: Similar parameter optimization patterns emerge for different strategies but are implemented independently

Integrating this capability into the main CODEX system enables:
- Unified parameter optimization for all strategies (not just HIBOR)
- Consistent API and dashboard experience
- Extensible architecture for adding new strategies
- Historical tracking and comparison of optimization decisions

## Problem Statement

The `hk-stock-quant-system` contains a powerful **HIBOR 6M Strategy Parameter Optimization** system that can:
- Test multiple HIBOR thresholds (0.05% - 0.30%)
- Optimize holding periods (1-10 days)
- Fine-tune position sizes (10% - 50%)
- Use grid search with parallel processing
- Support sensitivity analysis and multi-metric optimization

However, this functionality is currently isolated in a separate subsystem and not integrated into the main CODEX project. This creates:
- **Duplication**: Strategy parameter optimization logic exists in multiple places
- **Fragmentation**: Users must manage separate optimization flows for different strategies
- **Limited Discoverability**: Optimization capabilities not exposed through main system API

## Solution Overview

Integrate the production-grade parameter optimization system from `hk-stock-quant-system` into CODEX main system through:

1. **Optimization Engine Integration**: Adopt proven `UnifiedStrategyOptimizer` class (854 lines, production-tested)
2. **Database Persistence Layer**: Create SQLAlchemy models and repository for optimization results
3. **API Exposure**: Build FastAPI endpoints for optimization lifecycle management
4. **Service Layer**: Implement business logic for parameter optimization workflows
5. **Background Task Support**: Integrate async task queue for long-running optimizations
6. **Dashboard UI**: Add optimization visualization and management components

## Change Scope

This proposal spans six key capabilities:

1. **Capability A**: Optimization Engine Portability
   - Port `UnifiedStrategyOptimizer` to `src/optimization/`
   - Support RSI, MACD, Bollinger, HIBOR and custom strategies
   - Maintain proven multiprocessing architecture
   - Preserve cross-validation and performance metric calculation

2. **Capability B**: Database Persistence
   - Create `OptimizationRun` and `OptimizationResult` SQLAlchemy models
   - Index by symbol, strategy, and creation date for fast queries
   - Store parameter combinations (JSON) and all performance metrics
   - Enable historical comparison and audit trails

3. **Capability C**: API Integration
   - `POST /api/optimize/{symbol}/{strategy}` - Start optimization
   - `GET /api/optimize/{task_id}/status` - Real-time progress
   - `GET /api/optimize/{symbol}/{strategy}/results` - Query best combinations
   - `GET /api/optimize/{symbol}/{strategy}/sensitivity` - Parameter sensitivity
   - `GET /api/optimize/history` - Historical optimization runs

4. **Capability D**: Service Layer
   - `OptimizationService` class managing optimizer lifecycle
   - `OptimizationRepository` for database CRUD operations
   - Task scheduling and status tracking
   - Parameter validation and constraint checking

5. **Capability E**: Background Task Queue
   - Celery or APScheduler integration
   - Async parameter evaluation
   - WebSocket progress updates
   - Cancellation support

6. **Capability F**: Dashboard UI Components (Optional)
   - Parameter grid table with sorting/filtering
   - Sensitivity analysis charts
   - Optimization history timeline
   - Best parameters comparison widget

## Related Systems

- **Backtest Engine** (`src/backtest/`): Provides strategy evaluation
- **Strategy Modules** (`src/strategies/`): Define trading logic
- **FastAPI Routes** (`src/dashboard/api_routes.py`): Expose HTTP endpoints
- **Database Layer** (`src/models/`): Persist optimization results
- **Dashboard** (`src/dashboard/`): Web UI for parameter selection and result visualization

## Success Criteria

- ✅ Parameter optimization framework supports 5+ strategies with < 5% code duplication
- ✅ Grid search optimization completes in < 2 minutes for 100+ parameter combinations
- ✅ API endpoints fully functional with proper error handling
- ✅ Dashboard displays optimization results with interactive filtering
- ✅ Database schema properly normalizes optimization data
- ✅ Test coverage ≥ 80% for optimization modules
- ✅ Documentation includes usage examples for each strategy

## Impact Assessment

### Benefits
- **Consistency**: All strategies optimized through same framework
- **Discoverability**: Users find optimization features in main dashboard
- **Extensibility**: Easy to add new strategies or custom parameters
- **Automation**: Supports batch optimization of multiple stocks/strategies
- **Governance**: Historical tracking of all optimization decisions

### Risks
- **Complexity**: Generalization adds abstraction layers
- **Performance**: Parallel processing must handle resource constraints
- **Compatibility**: Must work with existing backtest engine

### Mitigation
- Incremental integration starting with HIBOR (proven working)
- Performance testing at each stage
- Comprehensive test suite for all components

## Implementation Sequence

1. **Phase 1**: Port optimization engine to CODEX (adapt UnifiedStrategyOptimizer)
2. **Phase 2**: Create database models and repository layer
3. **Phase 3**: Implement service layer for optimization workflows
4. **Phase 4**: Build REST API endpoints
5. **Phase 5**: Integrate background task queue
6. **Phase 6**: Implement dashboard UI (optional)
7. **Phase 7**: Documentation, testing, and production deployment

---

**Next**: Review `design.md` for architectural decisions and `tasks.md` for detailed work breakdown.
