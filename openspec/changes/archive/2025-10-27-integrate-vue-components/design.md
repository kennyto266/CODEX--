# OpenSpec Design Document: Vue Components Integration

**Change ID**: `integrate-vue-components`
**Version**: 1.0
**Last Updated**: 2025-10-27
**Author**: Claude Code

---

## Architecture Overview

### Current State
```
Current Dashboard (Broken):
┌─────────────────────────────────────────┐
│   HTML + Vanilla JavaScript             │
│  - 7 basic features                     │
│  - No Vue components used               │
│  - Static files return 404              │
│  - 70% functionality missing            │
└─────────────────────────────────────────┘

Existing Resources (Unused):
┌─────────────────────────────────────────┐
│   19 Vue Components (~147 KB)           │
│   25+ API Endpoints (Working)           │
│   4 WebSocket Endpoints                 │
│   Complete Backend System               │
└─────────────────────────────────────────┘
```

### Target State
```
Integrated Vue Dashboard (Working):
┌─────────────────────────────────────────┐
│   Vue 3 Application                     │
│  ┌─────────────────────────────────┐   │
│  │  Vue Router + Pinia + Components│   │
│  │  - All 19 components integrated │   │
│  │  - Client-side routing (#/path) │   │
│  │  - State management             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  FastAPI Backend                │   │
│  │  - Static file service          │   │
│  │  - 25+ REST endpoints           │   │
│  │  - WebSocket support            │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Technical Design

### 1. Vue Application Structure

```
src/dashboard/
├── templates/
│   └── index.html          # Main Vue app entry point
├── static/
│   ├── js/
│   │   ├── components/     # 19 Vue components
│   │   ├── stores/         # Pinia stores
│   │   ├── router/         # Vue Router config
│   │   └── utils/          # Helper functions
│   └── css/
│       └── main.css        # Global styles
└── ...
```

### 2. Component Integration Strategy

#### Strategy A: CDN + Runtime Compilation (Recommended for Speed)

**Pros**:
- No build process required
- Immediate development
- Easy to debug
- No compilation step

**Cons**:
- Larger bundle size
- Slower initial load
- Template as strings

**Implementation**:
```javascript
// Convert .vue files to JS objects
const AgentPanel = {
    template: `
        <div class="agent-panel glass-card p-6 rounded-xl">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold flex items-center">
                    <i class="fas fa-robot text-blue-400 mr-3"></i>
                    Agent Management
                </h2>
                <span class="text-sm text-gray-400">
                    Active: {{ activeAgents }}/{{ totalAgents }}
                </span>
            </div>

            <!-- Tab Navigation -->
            <div class="flex border-b border-gray-700 mb-4">
                <button
                    v-for="tab in tabs"
                    :key="tab.id"
                    @click="activeTab = tab.id"
                    :class="[
                        'px-4 py-2 font-medium transition-colors',
                        activeTab === tab.id
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-gray-400 hover:text-white'
                    ]"
                >
                    {{ tab.name }}
                </button>
            </div>

            <!-- Tab Content -->
            <component :is="currentTabComponent" />

        </div>
    `,
    setup() {
        const activeTab = ref('list');
        const activeAgents = ref(7);
        const totalAgents = ref(7);

        const tabs = [
            { id: 'list', name: 'Agent List', icon: 'fa-list' },
            { id: 'status', name: 'Health Status', icon: 'fa-heartbeat' },
            { id: 'metrics', name: 'Performance', icon: 'fa-chart-line' },
            { id: 'logs', name: 'Logs', icon: 'fa-file-alt' }
        ];

        const currentTabComponent = computed(() => {
            const components = {
                'list': AgentList,
                'status': AgentStatus,
                'metrics': AgentMetrics,
                'logs': AgentLogs
            };
            return components[activeTab.value] || AgentList;
        });

        return {
            activeTab,
            activeAgents,
            totalAgents,
            tabs,
            currentTabComponent
        };
    }
};
```

#### Strategy B: Pre-compiled Bundles (Recommended for Production)

**Pros**:
- Smaller bundle size
- Better performance
- TypeScript support
- Production-ready

**Cons**:
- Requires build process
- Longer development time
- Build tool configuration

**Implementation**:
```bash
# Vite configuration
npm create vite@latest dashboard --template vue
npm install
npm run build

# Output: dist/assets/*.js
```

**Build Output**:
```
dist/
├── assets/
│   ├── index-abc123.js      # Main bundle
│   ├── vendor-def456.js     # Vue runtime
│   └── components-ghi789.js # All components
└── index.html               # Entry point
```

### 3. Routing System Design

#### Hash-based Routing (Recommended)
```javascript
const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: DashboardOverview,
        meta: { title: 'Dashboard Overview' }
    },
    {
        path: '/backtest',
        name: 'Backtest',
        component: BacktestPanel,
        meta: { title: 'Strategy Backtest' }
    },
    {
        path: '/agents',
        name: 'Agents',
        component: AgentPanel,
        meta: { title: 'Agent Management' }
    },
    {
        path: '/risk',
        name: 'Risk',
        component: RiskPanel,
        meta: { title: 'Risk Dashboard' }
    },
    {
        path: '/trading',
        name: 'Trading',
        component: TradingPanel,
        meta: { title: 'Trading Interface' }
    }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes
});

// Navigation guard
router.beforeEach((to, from, next) => {
    document.title = to.meta.title || 'CODEX Dashboard';
    next();
});
```

#### Navigation Component
```javascript
const Navigation = {
    template: `
        <nav class="bg-gray-900 bg-opacity-90 backdrop-blur border-b border-gray-800">
            <div class="max-w-7xl mx-auto px-4">
                <div class="flex items-center justify-between h-16">
                    <!-- Logo -->
                    <div class="flex items-center">
                        <h1 class="text-xl font-bold text-white">
                            CODEX
                        </h1>
                    </div>

                    <!-- Menu Items -->
                    <div class="flex space-x-4">
                        <router-link
                            v-for="item in menuItems"
                            :key="item.path"
                            :to="item.path"
                            class="nav-link"
                            :class="{ 'active': $route.path === item.path }"
                        >
                            <i :class="item.icon" class="mr-2"></i>
                            {{ item.name }}
                        </router-link>
                    </div>
                </div>
            </div>
        </nav>
    `,
    setup() {
        const menuItems = [
            { path: '/', name: 'Dashboard', icon: 'fas fa-tachometer-alt' },
            { path: '/backtest', name: 'Backtest', icon: 'fas fa-chart-line' },
            { path: '/agents', name: 'Agents', icon: 'fas fa-robot' },
            { path: '/risk', name: 'Risk', icon: 'fas fa-shield-alt' },
            { path: '/trading', name: 'Trading', icon: 'fas fa-chart-bar' }
        ];

        return { menuItems };
    }
};
```

### 4. State Management with Pinia

#### Agent Store
```javascript
const useAgentStore = defineStore('agents', {
    state: () => ({
        agents: [],
        loading: false,
        error: null,
        selectedAgent: null,
        filters: {
            status: 'all',
            search: ''
        }
    }),

    getters: {
        activeAgents: (state) => state.agents.filter(a => a.status === 'running'),
        inactiveAgents: (state) => state.agents.filter(a => a.status !== 'running'),
        filteredAgents: (state) => {
            let result = state.agents;
            if (state.filters.status !== 'all') {
                result = result.filter(a => a.status === state.filters.status);
            }
            if (state.filters.search) {
                result = result.filter(a =>
                    a.name.toLowerCase().includes(state.filters.search.toLowerCase())
                );
            }
            return result;
        }
    },

    actions: {
        async fetchAgents() {
            this.loading = true;
            this.error = null;
            try {
                const response = await axios.get('/api/agents/list');
                this.agents = response.data;
            } catch (error) {
                this.error = error.message;
                console.error('Failed to fetch agents:', error);
            } finally {
                this.loading = false;
            }
        },

        async startAgent(agentId) {
            try {
                await axios.post(`/api/agents/${agentId}/start`);
                const agent = this.agents.find(a => a.id === agentId);
                if (agent) agent.status = 'running';
            } catch (error) {
                this.error = error.message;
            }
        },

        async stopAgent(agentId) {
            try {
                await axios.post(`/api/agents/${agentId}/stop`);
                const agent = this.agents.find(a => a.id === agentId);
                if (agent) agent.status = 'stopped';
            } catch (error) {
                this.error = error.message;
            }
        },

        setFilter(key, value) {
            this.filters[key] = value;
        }
    }
});
```

#### Portfolio Store
```javascript
const usePortfolioStore = defineStore('portfolio', {
    state: () => ({
        positions: [],
        orders: [],
        history: [],
        loading: false
    }),

    getters: {
        totalValue: (state) => {
            return state.positions.reduce((sum, pos) =>
                sum + (pos.quantity * pos.currentPrice), 0
            );
        },
        totalPnL: (state) => {
            return state.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);
        }
    },

    actions: {
        async fetchPortfolio() {
            this.loading = true;
            try {
                const response = await axios.get('/api/trading/portfolio');
                this.positions = response.data.positions || [];
            } catch (error) {
                console.error('Failed to fetch portfolio:', error);
            } finally {
                this.loading = false;
            }
        },

        async placeOrder(orderData) {
            try {
                const response = await axios.post('/api/trading/order', orderData);
                this.orders.push(response.data);
                return response.data;
            } catch (error) {
                throw error;
            }
        }
    }
});
```

### 5. Static File Service Configuration

#### FastAPI StaticFiles Setup
```python
# run_dashboard.py additions
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Create static directory structure
static_dir = project_root / "src" / "dashboard" / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# Create subdirectories
(static_dir / "js" / "components").mkdir(parents=True, exist_ok=True)
(static_dir / "js" / "stores").mkdir(parents=True, exist_ok=True)
(static_dir / "js" / "router").mkdir(parents=True, exist_ok=True)
(static_dir / "css").mkdir(parents=True, exist_ok=True)

# Mount static files with explicit paths
app.mount(
    "/static",
    StaticFiles(directory=str(static_dir)),
    name="static"
)

# Specific mounts for better organization
app.mount(
    "/static/js",
    StaticFiles(directory=str(static_dir / "js")),
    name="static-js"
)

app.mount(
    "/static/css",
    StaticFiles(directory=str(static_dir / "css")),
    name="static-css"
)

# Enable CORS for static files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

#### Directory Structure
```
static/
├── js/
│   ├── components/
│   │   ├── AgentPanel.vue
│   │   ├── AgentList.vue
│   │   ├── BacktestPanel.vue
│   │   └── ... (19 components total)
│   ├── stores/
│   │   ├── agents.js
│   │   ├── portfolio.js
│   │   ├── risk.js
│   │   └── index.js
│   ├── router/
│   │   └── index.js
│   └── main.js
├── css/
│   ├── components.css
│   └── main.css
└── index.html
```

### 6. API Integration Pattern

#### HTTP Client Setup
```javascript
// utils/api.js
import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
    },
    (error) => {
        console.error(`API Error: ${error.response?.status} ${error.config?.url}`);
        return Promise.reject(error);
    }
);

export default api;
```

#### Service Layer Pattern
```javascript
// services/agentService.js
import api from '../utils/api';

export const agentService = {
    async getAllAgents() {
        const { data } = await api.get('/agents/list');
        return data;
    },

    async getAgentStatus(id) {
        const { data } = await api.get(`/agents/${id}/status`);
        return data;
    },

    async startAgent(id) {
        const { data } = await api.post(`/agents/${id}/start`);
        return data;
    },

    async stopAgent(id) {
        const { data } = await api.post(`/agents/${id}/stop`);
        return data;
    },

    async getAgentLogs(id, limit = 100) {
        const { data } = await api.get(`/agents/${id}/logs?limit=${limit}`);
        return data;
    }
};
```

### 7. WebSocket Integration

#### WebSocket Manager
```javascript
// utils/websocket.js
class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect(path, onMessage, onError) {
        const wsUrl = `ws://${window.location.host}${path}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log(`WebSocket connected: ${path}`);
            this.reconnectAttempts = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage?.(data);
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };

        ws.onerror = (error) => {
            console.error(`WebSocket error (${path}):`, error);
            onError?.(error);
        };

        ws.onclose = () => {
            console.log(`WebSocket disconnected: ${path}`);
            this.reconnect();

            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.connect(path, onMessage, onError);
                }, 1000 * this.reconnectAttempts);
            }
        };

        this.connections.set(path, ws);
        return ws;
    }

    reconnect() {
        this.reconnectAttempts++;
    }

    disconnect(path) {
        const ws = this.connections.get(path);
        if (ws) {
            ws.close();
            this.connections.delete(path);
        }
    }

    disconnectAll() {
        this.connections.forEach((ws, path) => {
            ws.close();
        });
        this.connections.clear();
    }
}

export default new WebSocketManager();
```

#### Usage in Components
```javascript
// In AgentPanel.vue
import wsManager from '../utils/websocket';

setup() {
    const agents = ref([]);
    const wsConnected = ref(false);

    onMounted(() => {
        // Connect to WebSocket
        wsManager.connect(
            '/ws/system',
            (data) => {
                if (data.type === 'agent_update') {
                    // Update agent status in real-time
                    const index = agents.value.findIndex(a => a.id === data.agentId);
                    if (index !== -1) {
                        agents.value[index] = { ...agents.value[index], ...data.update };
                    }
                }
            },
            (error) => {
                console.error('WebSocket error:', error);
                wsConnected.value = false;
            }
        );
        wsConnected.value = true;
    });

    onUnmounted(() => {
        wsManager.disconnect('/ws/system');
    });

    return { agents, wsConnected };
}
```

---

## Implementation Phases

### Phase 1: Foundation (Day 1)
1. Set up Vue 3 application shell
2. Configure Vue Router
3. Set up Pinia stores
4. Configure static file service
5. Test basic navigation

### Phase 2: Core Integration (Day 2-3)
1. Integrate Phase 3 components (Agent Management)
2. Integrate Phase 4 components (Risk Dashboard)
3. Test API integration
4. Implement state management

### Phase 3: Feature Completion (Day 3-4)
1. Integrate Phase 2 components (Backtest)
2. Integrate Phase 5 components (Trading)
3. Add WebSocket real-time updates
4. Implement error handling

### Phase 4: Polish & Testing (Day 4-5)
1. UI/UX optimization
2. Responsive design
3. Performance optimization
4. End-to-end testing
5. Browser compatibility testing

---

## Performance Considerations

### Bundle Size Optimization
- Use CDN for Vue runtime (reduce initial bundle)
- Code splitting by route
- Lazy load non-critical components
- Tree shake unused code

### Loading Strategy
```
Initial Load:
├─ Vue Runtime (CDN) ~ 100KB
├─ Main App ~ 50KB
└─ Dashboard View ~ 20KB

Lazy Load (on demand):
├─ Backtest Module ~ 80KB
├─ Agent Module ~ 70KB
├─ Risk Module ~ 90KB
└─ Trading Module ~ 60KB

Total: ~470KB (vs current 0KB)
```

### Caching Strategy
- Vue runtime: Cache 1 year
- App code: Cache 1 day (with version hash)
- API responses: Cache 5 seconds
- Static assets: Cache 1 week

---

## Testing Strategy

### Unit Tests (Jest + Vue Test Utils)
```javascript
// tests/components/AgentPanel.test.js
import { mount } from '@vue/test-utils';
import AgentPanel from '@/components/AgentPanel.vue';

describe('AgentPanel', () => {
    it('renders agent list', async () => {
        const wrapper = mount(AgentPanel);
        expect(wrapper.find('.agent-list').exists()).toBe(true);
    });

    it('filters agents by status', async () => {
        const wrapper = mount(AgentPanel, {
            data() {
                return {
                    filters: { status: 'running' }
                };
            }
        });
        // Test filtering logic
    });
});
```

### Integration Tests (Cypress)
```javascript
// cypress/e2e/dashboard.cy.js
describe('Dashboard Navigation', () => {
    it('navigates between sections', () => {
        cy.visit('/');

        cy.get('[data-testid="nav-backtest"]').click();
        cy.url().should('include', '/backtest');
        cy.get('[data-testid="backtest-panel"]').should('be.visible');

        cy.get('[data-testid="nav-agents"]').click();
        cy.url().should('include', '/agents');
        cy.get('[data-testid="agent-panel"]').should('be.visible');
    });
});
```

---

## Security Considerations

### API Security
- Input validation on all endpoints
- Rate limiting for API calls
- CORS configuration
- No sensitive data in client-side code

### WebSocket Security
- Authenticate WebSocket connections
- Validate message format
- Limit message rate

---

## Deployment Strategy

### Development
```bash
# Start development server
python run_dashboard.py

# Auto-reload enabled for HTML/CSS
# Manual refresh for .js changes
```

### Production
```bash
# Pre-compile Vue components
npm run build

# Copy dist/ to static/
cp -r dist/* src/dashboard/static/

# Start production server
python run_dashboard.py
```

---

## Monitoring & Observability

### Client-side Logging
```javascript
// utils/logger.js
export const logger = {
    info: (message, data) => console.log(`[INFO] ${message}`, data),
    warn: (message, data) => console.warn(`[WARN] ${message}`, data),
    error: (message, data) => console.error(`[ERROR] ${message}`, data)
};
```

### Error Tracking
```javascript
// Global error handler
window.addEventListener('error', (event) => {
    logger.error('Global error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
});
```

---

## Rollback Procedure

### Quick Rollback (30 seconds)
1. Revert `index.html` to previous version
2. Restart server
3. Dashboard returns to basic functionality

### Gradual Rollback (5 minutes)
1. Disable components one by one
2. Keep API backend unchanged
3. Identify problematic component

### Full Rollback (10 minutes)
1. Restore from git commit
2. Redeploy application
3. Verify all endpoints work

---

**Design Document Version**: 1.0
**Next Review**: After Phase 1 completion
**Contact**: Project Lead for questions
