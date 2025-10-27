/**
 * CODEX Trading Dashboard - Main Application Entry
 * Vue 3 Application with Pinia and Vue Router
 */

const { createApp, ref, onMounted } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;
const { createPinia, defineStore } = Pinia;

// ============================================================================
// Pinia Stores
// ============================================================================

// Agent Store
const useAgentStore = defineStore('agents', {
    state: () => ({
        agents: [],
        loading: false,
        error: null,
        selectedAgentId: null
    }),

    getters: {
        activeAgents: (state) => state.agents.filter(a => a.status === 'running'),
        inactiveAgents: (state) => state.agents.filter(a => a.status !== 'running'),
        selectedAgent: (state) => state.agents.find(a => a.id === state.selectedAgentId)
    },

    actions: {
        async fetchAgents() {
            this.loading = true;
            try {
                const response = await fetch('/api/agents/list');
                this.agents = await response.json();
            } catch (error) {
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },

        selectAgent(agentId) {
            this.selectedAgentId = agentId;
        }
    }
});

// Portfolio Store
const usePortfolioStore = defineStore('portfolio', {
    state: () => ({
        positions: [],
        orders: [],
        loading: false
    }),

    getters: {
        totalValue: (state) => state.positions.reduce((sum, pos) => sum + (pos.quantity * pos.currentPrice), 0),
        totalPnL: (state) => state.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
    },

    actions: {
        async fetchPortfolio() {
            this.loading = true;
            try {
                const response = await fetch('/api/trading/portfolio');
                const data = await response.json();
                this.positions = data.positions || [];
            } catch (error) {
                console.error('Failed to fetch portfolio:', error);
            } finally {
                this.loading = false;
            }
        }
    }
});

// ============================================================================
// Vue Components
// ============================================================================

// Dashboard Component
const DashboardComponent = {
    template: `
        <div class="dashboard">
            <h1 class="text-3xl font-bold mb-6 text-white">Dashboard Overview</h1>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700">
                    <h3 class="text-slate-400 text-sm mb-2">Initial Capital</h3>
                    <p class="text-3xl font-bold text-white">$1,000,000</p>
                </div>

                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700">
                    <h3 class="text-slate-400 text-sm mb-2">Portfolio Value</h3>
                    <p class="text-3xl font-bold text-white">$1,000,000</p>
                </div>

                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700">
                    <h3 class="text-slate-400 text-sm mb-2">Active Positions</h3>
                    <p class="text-3xl font-bold text-white">0</p>
                </div>

                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700">
                    <h3 class="text-slate-400 text-sm mb-2">Total Return</h3>
                    <p class="text-3xl font-bold text-green-400">0.00%</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 hover:border-blue-500 transition-colors">
                    <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                        <i class="fas fa-robot mr-2 text-blue-400"></i>
                        Agent Management
                    </h2>
                    <p class="text-slate-400 mb-4">Monitor and control AI agents</p>
                    <router-link to="/agents" class="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                        View Agents
                    </router-link>
                </div>

                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 hover:border-purple-500 transition-colors">
                    <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                        <i class="fas fa-chart-line mr-2 text-purple-400"></i>
                        Strategy Backtest
                    </h2>
                    <p class="text-slate-400 mb-4">Test trading strategies</p>
                    <router-link to="/backtest" class="inline-block px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors">
                        Run Backtest
                    </router-link>
                </div>

                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 hover:border-red-500 transition-colors">
                    <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                        <i class="fas fa-shield-alt mr-2 text-red-400"></i>
                        Risk Dashboard
                    </h2>
                    <p class="text-slate-400 mb-4">Monitor portfolio risk</p>
                    <router-link to="/risk" class="inline-block px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors">
                        View Risk
                    </router-link>
                </div>
            </div>

            <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700">
                <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                    <i class="fas fa-check-circle mr-2 text-green-400"></i>
                    System Status
                </h2>
                <div class="flex items-center space-x-2 mb-2">
                    <div class="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                    <span class="text-green-400 font-semibold">Vue Dashboard Active</span>
                </div>
                <p class="text-slate-400">
                    All systems operational. Vue 3, Router, and Pinia are configured and ready.
                </p>
            </div>
        </div>
    `
};

// ============================================================================
// Vue Router Configuration
// ============================================================================

const routes = [
    { path: '/', component: DashboardComponent, name: 'Dashboard' },
    {
        path: '/agents',
        component: () => loadComponentAsync('AgentPanel'),
        name: 'Agents'
    },
    {
        path: '/backtest',
        component: () => loadComponentAsync('BacktestPanel'),
        name: 'Backtest'
    },
    {
        path: '/risk',
        component: () => loadComponentAsync('RiskPanel'),
        name: 'Risk'
    },
    {
        path: '/trading',
        component: () => loadComponentAsync('TradingPanel'),
        name: 'Trading'
    }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes
});

// ============================================================================
// Component Loader
// ============================================================================

const loadComponent = async (componentName) => {
    try {
        const script = document.createElement('script');
        script.src = `/static/js/components/${componentName}.js`;
        document.head.appendChild(script);

        return new Promise((resolve) => {
            script.onload = () => {
                console.log(`✅ Loaded ${componentName} component`);
                resolve(window[componentName]);
            };
            script.onerror = () => {
                console.error(`❌ Failed to load ${componentName} component`);
                resolve(null);
            };
        });
    } catch (error) {
        console.error(`Failed to load ${componentName}:`, error);
        return null;
    }
};

const loadComponentAsync = (componentName) => {
    return () => loadComponent(componentName);
};

// ============================================================================
// Initialize Application
// ============================================================================

// Create Pinia store
const pinia = createPinia();

// Get the app element
const appElement = document.getElementById('app');

// Initialize Vue app without a custom component
// This will use the existing HTML as the template
const app = createApp({
    template: '',
    setup() {
        // No setup needed, we're using the HTML template
        return {};
    }
});

app.use(router);
app.use(pinia);
app.mount('#app');

// Export for global access
window.App = {
    router,
    pinia,
    useAgentStore,
    usePortfolioStore
};

console.log('✅ CODEX Dashboard initialized with Vue 3 + Router + Pinia');
console.log('✅ Routes configured:', routes.map(r => r.path).join(', '));
