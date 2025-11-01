# Dashboard Core Features OpenSpec Proposal

## 📋 Proposal Overview

This OpenSpec proposal introduces **8 major dashboard features** that expose existing backend functionality to the web interface, transforming the dashboard from a basic status display to a comprehensive trading platform.

**Change ID**: `add-dashboard-core-features`
**Status**: PENDING APPROVAL
**Estimated Timeline**: 4 weeks
**Scope**: 60 implementation tasks, 8 new API modules, 30+ frontend components

---

## 📁 Proposal Structure

```
openspec/changes/add-dashboard-core-features/
├── proposal.md              # Executive summary & overview
├── design.md                # Architectural decisions & data flows
├── tasks.md                 # 60 implementation tasks with dependencies
├── README.md                # This file
└── specs/
    ├── dashboard-backtest/spec.md           # [DONE] Backtest interface
    ├── dashboard-agent-management/spec.md   # [TODO] Agent control
    ├── dashboard-risk-monitoring/spec.md    # [TODO] Risk dashboard
    ├── dashboard-strategy-management/spec.md # [TODO] Strategy management
    ├── dashboard-trading/spec.md            # [TODO] Order execution
    ├── dashboard-performance/spec.md        # [TODO] Analytics
    ├── dashboard-alternative-data/spec.md   # [TODO] Alt data viewer
    └── dashboard-monitoring/spec.md         # [TODO] System monitor
```

---

## 🎯 Features at a Glance

| Feature | Backend Status | Frontend Status | API Endpoints | Priority |
|---------|--|--|--|--|
| **Backtest System** | ✅ Complete | ❌ Missing | 5 | 🔴 HIGH |
| **Agent Management** | ✅ Complete | ❌ Missing | 4 | 🔴 HIGH |
| **Risk Monitoring** | ✅ Complete | ❌ Missing | 5 | 🔴 HIGH |
| **Strategy Management** | ✅ Complete | ❌ Missing | 4 | 🟠 MEDIUM |
| **Trading Interface** | ✅ Complete | ❌ Missing | 5 | 🟠 MEDIUM |
| **Performance Analytics** | ✅ Complete | ❌ Missing | 4 | 🟠 MEDIUM |
| **Alternative Data** | ✅ Complete | ❌ Missing | 2 | 🟡 LOW |
| **System Monitoring** | ✅ Complete | ❌ Missing | 3 | 🟡 LOW |

---

## 🔗 Specifications Summary

### 1️⃣ Backtest Interface (DETAILED SPEC ✅)

Users can configure, execute, and analyze strategy backtests from the dashboard.

**API Endpoints**:
- `POST /api/backtest/run` - Submit backtest job
- `GET /api/backtest/status/{id}` - Poll progress
- `GET /api/backtest/results/{id}` - Fetch results
- `GET /api/backtest/list` - List past backtests
- `POST /api/backtest/optimize` - Parameter optimization

**Frontend Components**:
- BacktestPanel, BacktestForm, BacktestResults, BacktestComparison

**Database**: `backtest_configs`, `backtest_results` tables

**Spec File**: `specs/dashboard-backtest/spec.md` (150+ lines)

---

### 2️⃣ Agent Management (TODO)

Users can monitor AI agent status, control execution (start/stop/restart), and view real-time logs.

**API Endpoints**:
- `GET /api/agents/list` - List all agents
- `GET /api/agents/{id}/status` - Agent status
- `POST /api/agents/{id}/start` - Start agent
- `POST /api/agents/{id}/stop` - Stop agent
- `GET /api/agents/{id}/logs` - Agent output
- `WS /ws/agents/{id}` - Real-time log streaming

**Frontend Components**:
- AgentManager, AgentGrid, AgentCard, AgentLogs, AgentMetrics

**Database**: `agent_logs` table

---

### 3️⃣ Risk Monitoring Dashboard (TODO)

Users can monitor portfolio risk metrics, view active alerts, run stress tests, and configure risk thresholds.

**API Endpoints**:
- `GET /api/risk/portfolio` - Portfolio risk metrics
- `GET /api/risk/var` - Value at Risk calculation
- `GET /api/risk/alerts` - Active risk alerts
- `POST /api/risk/stress-test` - Stress test scenarios
- `WS /ws/risk` - Real-time risk alerts

**Frontend Components**:
- RiskDashboard, RiskMetrics, AlertCenter, StressTestResults

**Database**: `risk_alerts` table

---

### 4️⃣ Strategy Management (TODO)

Users can browse available strategies, view performance, save custom parameters, and compare strategies.

**API Endpoints**:
- `GET /api/strategies/list` - Available strategies
- `GET /api/strategies/{id}` - Strategy details
- `POST /api/strategies` - Save custom strategy
- `GET /api/strategies/{id}/performance` - Historical perf
- `POST /api/strategies/compare` - Compare strategies

**Frontend Components**:
- StrategySelector, StrategyDetail, StrategyComparison, PerformanceChart

**Database**: `strategy_configurations` table

---

### 5️⃣ Trading Interface (TODO)

Users can place orders, monitor positions, view pending orders, and access trade history.

**API Endpoints**:
- `POST /api/trading/order` - Place order
- `GET /api/trading/orders` - List orders
- `GET /api/trading/positions` - Open positions
- `PUT /api/trading/orders/{id}` - Modify order
- `DELETE /api/trading/orders/{id}` - Cancel order
- `GET /api/trading/history` - Trade history
- `WS /ws/orders` - Order fill notifications

**Frontend Components**:
- TradingInterface, OrderForm, PositionsList, OrderBook, TradeHistory

---

### 6️⃣ Performance Analytics (TODO)

Users can view detailed performance metrics, monthly returns, drawdown analysis, and return distribution.

**API Endpoints**:
- `GET /api/performance/detailed` - Detailed metrics
- `GET /api/performance/monthly` - Monthly returns
- `GET /api/performance/drawdown` - Drawdown curve
- `GET /api/performance/distribution` - Return distribution

**Frontend Components**:
- PerformanceAnalytics, EquityCurveChart, DrawdownChart, MonthlyHeatmap

---

### 7️⃣ Alternative Data Integration (TODO)

Users can view alternative data sources (HIBOR, property, retail, GDP, etc.) and analyze correlations.

**API Endpoints**:
- `GET /api/alternative-data/list` - Available sources
- `GET /api/alternative-data/{source}` - Source data
- `GET /api/alternative-data/correlation` - Correlation matrix

**Frontend Components**:
- AlternativeDataViewer, DataSourceSelector, CorrelationMatrix

---

### 8️⃣ System Monitoring (TODO)

Users can monitor system performance (CPU, memory, disk), view system logs, and check health status.

**API Endpoints**:
- `GET /api/monitoring/metrics` - System performance
- `GET /api/monitoring/logs` - System logs
- `WS /ws/system` - Real-time metrics

**Frontend Components**:
- SystemMonitor, PerformanceChart, LogViewer, HealthIndicators

---

## 🏗️ Implementation Phases

### Phase 1: Infrastructure & Setup (Week 1)
- 10 tasks: API routes, WebSocket, Pinia store, database schema

### Phase 2: Backtest & Agents (Week 2)
- 18 tasks: Backtest API & UI, Agent API & UI

### Phase 3: Risk & Strategy (Week 3)
- 16 tasks: Risk dashboard, Strategy management

### Phase 4: Trading & Analytics (Week 4)
- 12 tasks: Trading interface, Performance analytics, Alt-data, Monitoring

### Throughout: Testing & Deployment
- 15 tasks: Unit tests, integration tests, E2E tests, performance tests, documentation

---

## 📊 Success Metrics

### Functionality
- ✅ All 8 features fully operational
- ✅ All 30+ API endpoints implemented and tested
- ✅ All 30+ frontend components working

### Quality
- ✅ 80% test coverage maintained
- ✅ No breaking changes to existing APIs
- ✅ All validation rules implemented

### Performance
- ✅ Dashboard load time < 3 seconds
- ✅ API response time < 500ms (95th percentile)
- ✅ WebSocket latency < 100ms

### User Experience
- ✅ Responsive design (works on mobile)
- ✅ Intuitive navigation
- ✅ Clear error messages

---

## 🚀 Approval Checklist

Before implementation can begin, this proposal requires approval on:

- [ ] **Executive**: Confirms timeline and resource allocation
- [ ] **Architecture**: Validates design decisions and API structure
- [ ] **Security**: Reviews authentication, input validation, data privacy
- [ ] **Product**: Confirms feature priority and user workflows
- [ ] **QA**: Agrees on testing strategy and acceptance criteria

---

## 📚 Reference Files

1. **proposal.md** - Full executive summary (2 pages)
2. **design.md** - Architecture decisions and data flows (5 pages)
3. **tasks.md** - 60 detailed implementation tasks with dependencies (4 pages)
4. **specs/dashboard-backtest/spec.md** - Detailed API & component specs

Additional specs (TODO): 7 more feature specs following the same structure as backtest spec

---

## 🔄 Next Steps

1. **Review**: Read proposal.md and design.md
2. **Feedback**: Provide comments on architecture and scope
3. **Approval**: Get sign-off from stakeholders
4. **Implementation**: Use `openspec apply add-dashboard-core-features` to begin work

---

## 📞 Questions & Discussion

This proposal opens discussion on:
- Technology choices (Vue vs React, Pinia vs Redux)
- Feature prioritization (should trading be Phase 2 instead of Phase 4?)
- Performance targets (are < 3 second load time and < 500ms API response realistic?)
- Team capacity (can 4 tasks/week be maintained?)
- Security requirements (do we need OAuth2 for dashboard?)

---

**Prepared by**: Claude Code AI
**Date**: 2025-10-26
**Proposal ID**: `add-dashboard-core-features`
**Status**: PENDING STAKEHOLDER APPROVAL

