# OpenSpec Proposal: Add Dashboard Core Features

**Change ID**: `add-dashboard-core-features`
**Status**: PENDING APPROVAL
**Priority**: HIGH
**Scope**: Frontend + Backend
**Estimated Duration**: 4 weeks

---

## Why

The CODEX Trading Dashboard currently implements only ~5-10% of the system's capabilities. The backend has 40+ implemented modules with complete trading functionality (backtesting, strategy management, AI agents, risk monitoring, order execution), but users cannot access any of these through the UI—they are forced to use CLI tools. This proposal adds 8 comprehensive frontend features that expose existing backend functionality to users through a modern web interface.

---

## What Changes

This proposal adds 8 major interconnected dashboard features:

1. **Backtest System** - Strategy testing, parameter optimization, result visualization
2. **Agent Management** - Monitor and control 7 AI agents in real-time
3. **Risk Management** - Portfolio risk metrics, VaR, alerts, stress testing
4. **Strategy Management** - Browse strategies, compare performance, save configurations
5. **Trading Interface** - Place orders, manage positions, view trade history
6. **Performance Analytics** - Detailed performance metrics, equity curves, drawdown analysis
7. **Alternative Data Integration** - View HIBOR, property, GDP, retail data with correlations
8. **System Monitoring** - Real-time CPU/memory/disk metrics, health status, logs

**Key Implementation Details**:
- Frontend: Vue 3 + Tailwind CSS with Pinia state management
- Backend: REST + WebSocket hybrid API (30+ new endpoints)
- Real-time: Native WebSocket for portfolio updates, alerts, order fills
- Database: Minimal schema extension (5 new tables)
- No breaking changes to existing APIs (additive only)

---

## Impact

- **Affected specs**: 8 new dashboard capabilities
- **Affected code**: `src/dashboard/` (API routes, WebSocket), Vue 3 components, Pinia store
- **User impact**: Users gain access to full trading workflow from backtest → strategy selection → execution → monitoring
- **Risk level**: MEDIUM (new UI only, all backend systems already stable)
- **Timeline**: 4 weeks, 60 implementation tasks across 8 phases
- **Testing**: 80% code coverage requirement maintained

### Phase 1 (Week 1): Core Infrastructure
- Create API routes for backtest, agent, and risk modules
- Implement real-time WebSocket endpoints
- Set up frontend UI framework and navigation

### Phase 2 (Week 2-3): Feature Implementation
- Backtest interface + results visualization
- Agent management + status monitoring
- Risk dashboard + alert system
- Strategy configuration + comparison

### Phase 3 (Week 4): Advanced Features
- Trading interface (buy/sell orders)
- Performance analytics dashboard
- Alternative data integration
- System monitoring + performance metrics

---

## Technical Approach

### Backend (API Routes)
Create FastAPI endpoints for each feature:
```
POST   /api/backtest/run              - Start backtest
GET    /api/backtest/results/{id}     - Get results
POST   /api/agents/{id}/start         - Control agents
GET    /api/risk/portfolio            - Risk metrics
POST   /api/trading/order             - Place orders
GET    /api/strategies/list           - Available strategies
WS     /ws/portfolio                  - Real-time updates
```

### Frontend (React/Vue)
Create modular UI components:
```
/dashboard/components/
  ├── BacktestPanel.vue
  ├── AgentManager.vue
  ├── RiskDashboard.vue
  ├── StrategySelector.vue
  ├── TradingInterface.vue
  ├── PerformanceChart.vue
  ├── AlternativeDataViewer.vue
  └── SystemMonitor.vue
```

### Database Schema
Extend existing schema to store:
- Backtest configuration and results
- Strategy parameters and performance
- Trade history and filled orders
- System performance metrics

---

## Deliverables

### By End of Phase 1
- [ ] 8 new capability specs defined
- [ ] API route structure designed
- [ ] Frontend layout mockups approved
- [ ] Navigation system implemented

### By End of Phase 2
- [ ] Backtest system fully integrated
- [ ] Agent management UI operational
- [ ] Risk alerts configured and tested
- [ ] Strategy selection working

### By End of Phase 3
- [ ] Order execution tested with live data
- [ ] Performance analytics dashboard showing real metrics
- [ ] Alternative data sources integrated
- [ ] System monitoring with performance graphs

---

## Success Criteria

- [x] All 8 features have detailed specs
- [ ] Backend APIs fully implemented and tested
- [ ] Frontend components complete with responsive design
- [ ] End-to-end workflows functional (backtest → trade → monitor)
- [ ] 80% test coverage maintained
- [ ] No breaking changes to existing APIs
- [ ] Performance: Dashboard loads in < 3 seconds
- [ ] All WebSocket connections stable and real-time

---

## Dependencies

### Required Existing Systems
- `src/backtest/enhanced_backtest_engine.py` - Backtest execution
- `src/agents/` - Agent system (7 agents)
- `src/risk_management/` - Risk calculation modules
- `src/strategies.py` - Strategy definitions
- `run_dashboard.py` - Existing FastAPI server

### New Dependencies
- None required (uses existing libraries: FastAPI, pandas, numpy)

### Optional Enhancements
- Socket.io for WebSocket instead of native WebSocket
- Chart.js or Plotly for data visualization
- Redux/Pinia for state management

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| WebSocket scaling issues | MEDIUM | HIGH | Use connection pooling, test with 100+ concurrent users |
| Backtest results too large | MEDIUM | MEDIUM | Implement pagination, compress JSON responses |
| Agent communication delays | LOW | HIGH | Monitor message queue performance, add timeout handling |
| API rate limiting | LOW | MEDIUM | Implement caching, request batching |

---

## Not in Scope

- Mobile app (desktop-first)
- Authentication/authorization enhancements
- Database migrations (schema changes minimal)
- Trading with real money (simulated trading only)
- Machine learning model updates
- Email/SMS notifications

---

## Approval Checklist

- [ ] Product owner approval
- [ ] Architecture review
- [ ] Security review
- [ ] Test strategy approval
- [ ] Performance requirements agreed
- [ ] Timeline confirmed

---

## Implementation Plan

Refer to `tasks.md` for detailed task breakdown (50+ tasks).
Refer to `design.md` for architectural decisions and trade-offs.
Refer to `specs/*/spec.md` for detailed capability specifications.

---

**Prepared by**: Claude Code AI
**Date**: 2025-10-26
**Revision**: 1.0
