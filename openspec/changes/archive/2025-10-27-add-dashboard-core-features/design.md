# Design Document: Dashboard Core Features

**Change ID**: `add-dashboard-core-features`
**Version**: 1.0
**Date**: 2025-10-26

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Dashboard Tabs                                  │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ [Backtest] [Agents] [Risk] [Strategies]         │  │
│  │ [Trading] [Performance] [Alt-Data] [Monitor]    │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Vue.js Components (Modular & Reusable)          │  │
│  │  - BacktestPanel, AgentManager, RiskDashboard   │  │
│  │  - Charts (Chart.js), Forms, Tables               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ (HTTP + WebSocket)
┌─────────────────────────────────────────────────────────┐
│                  FASTAPI SERVER (Port 8001)             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  REST API Routes                                 │  │
│  │  - POST /api/backtest/run                        │  │
│  │  - GET  /api/agents/{id}/status                  │  │
│  │  - GET  /api/risk/portfolio                      │  │
│  │  - POST /api/trading/order                       │  │
│  │  - GET  /api/strategies/list                     │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoints (Real-time Push)            │  │
│  │  - /ws/portfolio (position updates)              │  │
│  │  - /ws/orders (filled order notifications)       │  │
│  │  - /ws/risk (alert triggers)                     │  │
│  │  - /ws/system (performance metrics)              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ (Direct Call)
┌─────────────────────────────────────────────────────────┐
│                 BACKEND SYSTEMS (Python)                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Backtest Engine (enhanced_backtest_engine.py)   │  │
│  │  Agent System (coordinator.py + 7 agents)        │  │
│  │  Risk Manager (portfolio_manager.py)             │  │
│  │  Strategy Module (strategies.py)                 │  │
│  │  Trading Engine (execution_engine.py)            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Design Decisions

### 1. Frontend Framework: Vue 3 (with Tailwind CSS)

**Rationale**:
- Dashboard already uses Tailwind CSS and simple HTML/JS
- Vue 3 is lightweight but powerful
- Great for real-time updates with reactive data binding
- Can incrementally adopt without rewriting existing code

**Alternative Considered**: React
- More boilerplate, steeper learning curve
- Better for very large teams

### 2. Real-time Communication: Native WebSocket + Polling Fallback

**Rationale**:
- Browser native WebSocket support is solid
- No additional library dependency
- Fallback to polling for browser compatibility
- Can upgrade to Socket.io later if needed

**Implementation**:
```javascript
// Primary: WebSocket
const ws = new WebSocket('ws://localhost:8001/ws/portfolio');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updatePortfolio(data);
};

// Fallback: Polling every 5 seconds
setInterval(() => {
  fetch('/api/trading/portfolio').then(...)
}, 5000);
```

### 3. State Management: Pinia (Vue State Management)

**Rationale**:
- Lightweight store for shared state
- Better than prop drilling for deeply nested components
- Works well with Vue 3 composition API
- Easier migration path from simple data binding

**Store Structure**:
```
stores/
├── backtest.js    (backtest config & results)
├── agents.js      (agent status & logs)
├── risk.js        (portfolio risk & alerts)
├── strategy.js    (selected strategy & params)
├── trading.js     (orders, positions, fills)
└── system.js      (system metrics & health)
```

### 4. Data Visualization: Chart.js

**Rationale**:
- Lightweight, no complex dependencies
- Good performance for real-time updates
- Supports all needed chart types (line, bar, heatmap)
- Easy to integrate with Vue

**Alternative**: Plotly (more features but heavier)

### 5. API Design: RESTful + WebSocket Hybrid

**REST for**:
- Configuration (POST requests to backtest, create order)
- Static data (GET strategies, performance history)
- One-time actions (refresh, validate)

**WebSocket for**:
- Real-time position updates
- Order fill notifications
- Risk alerts
- System performance metrics

**Rationale**: REST for transaction-like operations, WebSocket for streaming data

### 6. Database: Minimal Extension of Existing Schema

**Current Tables**:
- portfolios, positions, orders, backtest_results

**New Tables**:
- backtest_configs (config + metadata)
- strategy_parameters (saved configurations)
- trade_history (filled trades)
- agent_logs (agent output)
- risk_alerts (alert history)

**Rationale**: Avoid major migrations, extend existing schema

---

## Component Architecture

### Backtest Module
```
BacktestPanel (parent)
├── BacktestForm (configure & run)
│   ├── StrategySelector
│   ├── DateRangePicker
│   └── ParameterOptimizer
├── BacktestResults (display results)
│   ├── PerformanceMetrics
│   ├── EquityCurveChart
│   ├── DrawdownChart
│   └── TradeTable
└── ComparisonView (compare runs)
    └── PerformanceComparison
```

### Agent Management Module
```
AgentManager (parent)
├── AgentStatusGrid (agent cards)
│   └── AgentCard (individual agent)
│       ├── StatusIndicator
│       ├── MetricsDisplay
│       ├── ControlButtons
│       └── LogViewer
├── AgentCommunication (message flow)
│   └── MessageTimeline
└── AgentPerformance (metrics over time)
    └── PerformanceChart
```

### Risk Management Module
```
RiskDashboard (parent)
├── RiskMetrics (summary cards)
│   ├── VaRCard
│   ├── DrawdownCard
│   ├── ExpectedShortfallCard
│   └── PositionSizeCard
├── AlertCenter (active alerts)
│   └── AlertList (with colors: red, yellow, green)
├── RiskHeatmap (position risk by asset)
│   └── Heatmap visualization
└── StressTestResults (stress test scenarios)
    └── ScenarioComparison
```

### Trading Interface Module
```
TradingInterface (parent)
├── OrderForm (place orders)
│   ├── SymbolSearch
│   ├── QuantityInput
│   ├── PriceInput
│   └── OrderTypeSelector
├── PositionsList (open positions)
│   └── PositionCard
│       ├── PnLDisplay
│       ├── ReduceButton
│       └── DetailedStats
├── OrderBook (pending orders)
│   └── OrderTable
└── TradeHistory (filled trades)
    └── HistoryTable
```

---

## Data Flow

### Backtest Workflow
```
1. User selects strategy + parameters
2. Click "Run Backtest" → POST /api/backtest/run
3. Backend queues task, returns backtest_id
4. Frontend polls /api/backtest/status/{id} every 2 seconds
5. When complete, fetch /api/backtest/results/{id}
6. Display results: equity curve, metrics, trade list
7. User can export or run comparison
```

### Real-time Position Update Workflow
```
1. WebSocket connection established: ws://localhost:8001/ws/portfolio
2. Backend monitors position changes (every second)
3. On change: broadcast {type: 'position_update', data: {...}}
4. Frontend receives and updates Pinia store
5. Vue components reactively re-render
6. No page refresh needed
```

### Agent Control Workflow
```
1. User clicks "Start Agent" button on AgentManager
2. POST /api/agents/{agent_id}/start
3. Backend routes to agent_manager.start_agent()
4. Frontend opens WebSocket to /ws/agents/{agent_id}
5. Receive real-time agent output and status
6. Display in LogViewer and StatusIndicator
```

---

## Performance Considerations

### Dashboard Load Time Target: < 3 seconds
- Lazy load component modules (code splitting)
- Compress static assets (HTML, CSS, JS)
- Cache API responses (5 minute TTL)
- Virtualize long lists (1000+ items)

### WebSocket Scaling
- Connection pooling for 100+ concurrent users
- Message rate limiting (max 100 msgs/sec per client)
- Broadcast optimization (group channels, not individual connections)

### Data Visualization
- Limit chart datasets to last 100 candles (for performance)
- Use aggregation for large timescales (daily vs minute)
- Virtual scrolling for trade history

### API Response Times Target
- Backtest results: < 500ms (cached after first fetch)
- Portfolio update: < 100ms (via WebSocket)
- Agent status: < 200ms
- Strategy list: < 100ms (cached)

---

## Security Considerations

### Input Validation
- All user inputs validated on backend
- Rate limiting on API endpoints (100 req/min per IP)
- CSRF protection for order placement

### Data Privacy
- Backtest results tied to user account
- No trading data accessible across users
- API keys not exposed in frontend

### WebSocket Security
- Only authenticated users can subscribe
- Message validation before processing
- Connection timeout after 30 minutes inactivity

---

## Testing Strategy

### Unit Tests
- Component tests: Vue component rendering
- API route tests: Request/response validation
- Business logic tests: Backtest calculations, risk metrics

### Integration Tests
- API + Database: Create backtest, fetch results
- WebSocket: Real-time position updates
- Multi-component: Agent control + log viewing

### E2E Tests
- Complete backtest workflow
- Order execution end-to-end
- Alert notification cycle

### Load Tests
- 100 concurrent WebSocket connections
- 1000 trades in trade history (performance)
- Large backtest result JSON (100MB+)

---

## Rollout Plan

### Phase 1: Infrastructure (Week 1)
1. Create API routes for all features (stubs)
2. Set up frontend folder structure
3. Implement WebSocket endpoints
4. Add database schema extensions

### Phase 2: Core Features (Week 2-3)
1. Backtest UI + API integration
2. Agent management UI
3. Risk dashboard
4. Strategy management

### Phase 3: Advanced Features (Week 4)
1. Trading interface
2. Performance analytics
3. Alternative data
4. System monitoring

### Deployment
- Feature flag each component (dark launch)
- Gradual rollout: 10% → 25% → 50% → 100%
- Monitor performance metrics and error rates
- Rollback capability for each feature

---

## Monitoring & Observability

### Metrics to Track
- Dashboard load time (target < 3s)
- API response times (by endpoint)
- WebSocket connection count
- Error rate by feature
- CPU/memory usage spike on backtest runs

### Logging
- All API requests: timestamp, endpoint, user, response time
- WebSocket events: connection, disconnection, message rate
- Error logs: stack traces, user context, recovery action

### Alerts
- Dashboard load time > 5 seconds
- API error rate > 1%
- WebSocket connections > 500
- Backtest failure (timeout or exception)

---

## Future Enhancements

### Phase 4+ Ideas
- Mobile app (responsive design first, then native)
- Authentication system (OAuth2, LDAP)
- Multi-user support with role-based access
- Email/SMS alerts
- Trading paper trading (simulated with real prices)
- Machine learning model updates UI
- Advanced charting (TradingView Lightweight Charts)
- Dark mode toggle

---

**Document Status**: DRAFT
**Ready for Implementation**: NO (pending approval)
