/**
 * CODEX Trading Dashboard - Main Application Entry
 * Vue 3 Application with Pinia and Vue Router
 * Phase 7: Performance Optimization & Error Handling
 */

const { createApp, ref, onMounted, reactive, h } = Vue;
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
        selectedAgentId: null,
        lastFetch: null
    }),

    getters: {
        activeAgents: (state) => state.agents.filter(a => a.status === 'running'),
        inactiveAgents: (state) => state.agents.filter(a => a.status !== 'running'),
        selectedAgent: (state) => state.agents.find(a => a.id === state.selectedAgentId)
    },

    actions: {
        async fetchAgents() {
            this.loading = true;
            this.error = null;

            try {
                const data = await APICache.fetchWithCache('/api/agents/list', {}, 60000); // 1 minute cache
                this.agents = data;
                this.lastFetch = Date.now();
                console.log('✅ Agent data fetched successfully');
            } catch (error) {
                this.error = error.message;
                console.error('❌ Failed to fetch agents:', error);
            } finally {
                this.loading = false;
            }
        },

        selectAgent(agentId) {
            this.selectedAgentId = agentId;
        },

        // Debounced refresh to prevent API spam
        refreshAgents: debounce(function() {
            APICache.clear(); // Clear cache
            this.fetchAgents();
        }, 1000)
    }
});

// Portfolio Store
const usePortfolioStore = defineStore('portfolio', {
    state: () => ({
        positions: [],
        orders: [],
        loading: false,
        error: null,
        lastFetch: null
    }),

    getters: {
        totalValue: (state) => state.positions.reduce((sum, pos) => sum + (pos.quantity * pos.currentPrice), 0),
        totalPnL: (state) => state.positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
    },

    actions: {
        async fetchPortfolio() {
            this.loading = true;
            this.error = null;

            try {
                const data = await APICache.fetchWithCache('/api/trading/portfolio', {}, 30000); // 30 second cache
                this.positions = data.positions || [];
                this.orders = data.orders || [];
                this.lastFetch = Date.now();
                console.log('✅ Portfolio data fetched successfully');
            } catch (error) {
                this.error = error.message;
                console.error('❌ Failed to fetch portfolio:', error);
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
// Phase 7: Performance Optimization & Error Handling
// ============================================================================

// ----------------------------------------------------------------------------
// 1. Error Boundary Component
// ----------------------------------------------------------------------------
const ErrorBoundary = {
    name: 'ErrorBoundary',
    props: ['fallback'],
    data() {
        return {
            hasError: false,
            error: null,
            errorInfo: null
        };
    },
    errorCaptured(err, vm, info) {
        console.error('Error caught by boundary:', err, info);
        this.hasError = true;
        this.error = err;
        this.errorInfo = info;
        return false;
    },
    template: `
        <div v-if="hasError" class="error-boundary p-8 bg-red-900 bg-opacity-20 border border-red-700 rounded-lg">
            <h2 class="text-2xl font-bold text-red-400 mb-4">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Something went wrong
            </h2>
            <div class="bg-slate-800 p-4 rounded mb-4 overflow-auto">
                <p class="text-red-300 font-mono text-sm">{{ error.message }}</p>
                <p class="text-slate-400 text-xs mt-2">{{ errorInfo }}</p>
            </div>
            <button @click="hasError = false"
                    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                <i class="fas fa-redo mr-2"></i>
                Try Again
            </button>
            <button @click="window.location.reload()"
                    class="ml-2 px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors">
                <i class="fas fa-sync mr-2"></i>
                Reload Page
            </button>
        </div>
        <slot v-else></slot>
    `
};

// ----------------------------------------------------------------------------
// 2. Performance Monitoring
// ----------------------------------------------------------------------------
const PerformanceMonitor = {
    init() {
        if (typeof window.performance !== 'undefined') {
            // Log Core Web Vitals
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const paint = performance.getEntriesByType('paint');

                    console.log('📊 Performance Metrics:');
                    console.log(`  - DOM Content Loaded: ${navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart}ms`);
                    console.log(`  - Load Complete: ${navigation.loadEventEnd - navigation.loadEventStart}ms`);
                    console.log(`  - First Paint: ${paint.find(p => p.name === 'first-paint')?.startTime || 'N/A'}ms`);
                    console.log(`  - First Contentful Paint: ${paint.find(p => p.name === 'first-contentful-paint')?.startTime || 'N/A'}ms`);
                    console.log(`  - Total Load Time: ${navigation.loadEventEnd - navigation.fetchStart}ms`);

                    // Log to server
                    this.reportMetrics({
                        loadTime: navigation.loadEventEnd - navigation.fetchStart,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                        timestamp: Date.now()
                    });
                }, 0);
            });
        }
    },

    reportMetrics(metrics) {
        fetch('/api/monitoring/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(metrics)
        }).catch(err => console.error('Failed to report metrics:', err));
    },

    measureComponentRender(componentName, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        console.log(`⚡ ${componentName} render time: ${(end - start).toFixed(2)}ms`);
        return result;
    }
};

// Initialize performance monitoring
PerformanceMonitor.init();

// ----------------------------------------------------------------------------
// 3. API Cache System
// ----------------------------------------------------------------------------
const APICache = {
    cache: new Map(),
    ttl: new Map(),
    maxSize: 100,

    set(key, value, ttlMs = 300000) { // Default 5 minutes
        // Evict oldest entries if cache is full
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.delete(firstKey);
        }

        this.cache.set(key, value);
        this.ttl.set(key, Date.now() + ttlMs);
    },

    get(key) {
        if (!this.cache.has(key)) return null;

        const expiry = this.ttl.get(key);
        if (Date.now() > expiry) {
            this.delete(key);
            return null;
        }

        return this.cache.get(key);
    },

    has(key) {
        return this.get(key) !== null;
    },

    delete(key) {
        this.cache.delete(key);
        this.ttl.delete(key);
    },

    clear() {
        this.cache.clear();
        this.ttl.clear();
    },

    async fetchWithCache(url, options = {}, ttlMs = 300000) {
        const cacheKey = `${url}:${JSON.stringify(options)}`;
        const cached = this.get(cacheKey);

        if (cached) {
            console.log(`📦 Cache hit for ${url}`);
            return cached;
        }

        console.log(`🌐 Fetching from network: ${url}`);
        const response = await fetch(url, options);
        const data = await response.json();
        this.set(cacheKey, data, ttlMs);
        return data;
    }
};

// ----------------------------------------------------------------------------
// 4. Debounce & Throttle Utilities
// ----------------------------------------------------------------------------
const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(null, args), delay);
    };
};

const throttle = (fn, limit) => {
    let inThrottle;
    return (...args) => {
        if (!inThrottle) {
            fn.apply(null, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// ----------------------------------------------------------------------------
// 5. Skeleton Loading Component
// ----------------------------------------------------------------------------
const SkeletonLoader = {
    name: 'SkeletonLoader',
    props: {
        type: {
            type: String,
            default: 'card' // card, table, list, chart
        },
        count: {
            type: Number,
            default: 1
        }
    },
    template: `
        <div class="skeleton-loader">
            <template v-if="type === 'card'">
                <div v-for="i in count" :key="i"
                     class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 animate-pulse">
                    <div class="h-4 bg-slate-700 rounded w-3/4 mb-4"></div>
                    <div class="h-8 bg-slate-700 rounded w-1/2 mb-4"></div>
                    <div class="h-4 bg-slate-700 rounded w-full mb-2"></div>
                    <div class="h-4 bg-slate-700 rounded w-5/6"></div>
                </div>
            </template>

            <template v-else-if="type === 'table'">
                <div class="bg-slate-800 bg-opacity-70 rounded-lg border border-slate-700 animate-pulse">
                    <div class="p-4 border-b border-slate-700">
                        <div class="h-6 bg-slate-700 rounded w-1/4"></div>
                    </div>
                    <div v-for="i in count" :key="i" class="p-4 border-b border-slate-700 last:border-b-0">
                        <div class="flex space-x-4">
                            <div class="h-4 bg-slate-700 rounded flex-1"></div>
                            <div class="h-4 bg-slate-700 rounded w-20"></div>
                            <div class="h-4 bg-slate-700 rounded w-20"></div>
                        </div>
                    </div>
                </div>
            </template>

            <template v-else-if="type === 'chart'">
                <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 animate-pulse">
                    <div class="h-6 bg-slate-700 rounded w-1/3 mb-6"></div>
                    <div class="h-64 bg-slate-700 rounded"></div>
                </div>
            </template>
        </div>
    `
};

// ----------------------------------------------------------------------------
// Component Loader with Enhanced Features
// ----------------------------------------------------------------------------

const loadComponent = async (componentName) => {
    const startTime = performance.now();

    try {
        // Check cache first
        const cacheKey = `component_${componentName}`;
        const cached = APICache.get(cacheKey);

        if (cached) {
            console.log(`✅ Loaded ${componentName} from cache`);
            return cached;
        }

        const script = document.createElement('script');
        script.src = `/static/js/components/${componentName}.js`;

        return new Promise((resolve, reject) => {
            script.onload = () => {
                const endTime = performance.now();
                console.log(`⚡ Loaded ${componentName} in ${(endTime - startTime).toFixed(2)}ms`);

                const component = window[componentName];
                if (component) {
                    // Cache the component
                    APICache.set(cacheKey, component, 600000); // 10 minutes
                    resolve(component);
                } else {
                    reject(new Error(`Component ${componentName} not found in window object`));
                }
            };
            script.onerror = () => {
                console.error(`❌ Failed to load ${componentName} component`);
                reject(new Error(`Failed to load ${componentName}`));
            };
        });
    } catch (error) {
        console.error(`Failed to load ${componentName}:`, error);
        throw error;
    }
};

const loadComponentAsync = (componentName) => {
    return async () => {
        try {
            const component = await loadComponent(componentName);
            return {
                ...component,
                // Wrap in error boundary
                render() {
                    try {
                        return h(component);
                    } catch (err) {
                        console.error(`Error rendering ${componentName}:`, err);
                        return h(ErrorBoundary, { fallback: componentName }, {
                            default: () => h('div', 'Component render error')
                        });
                    }
                }
            };
        } catch (error) {
            return {
                render() {
                    return h(ErrorBoundary, {
                        fallback: componentName,
                        error: error.message
                    });
                }
            };
        }
    };
};

// ============================================================================
// Initialize Application
// ============================================================================

// Create Pinia store
const pinia = createPinia();

// Create a root component that preserves existing HTML
const AppComponent = {
    template: `
        <div>
            <nav class="bg-slate-900 bg-opacity-80 backdrop-blur border-b border-slate-700 sticky top-0 z-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex items-center justify-between h-16">
                        <div class="flex items-center">
                            <router-link to="/" class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
                                    <span class="text-white font-bold text-sm">C</span>
                                </div>
                                <span class="text-xl font-bold text-white">CODEX Trading System</span>
                            </router-link>
                        </div>
                        <div class="hidden md:block">
                            <div class="ml-10 flex items-baseline space-x-2">
                                <router-link to="/" class="nav-link">
                                    <i class="fas fa-tachometer-alt text-sm mr-2"></i>Dashboard
                                </router-link>
                                <router-link to="/agents" class="nav-link">
                                    <i class="fas fa-robot text-sm mr-2"></i>Agents
                                </router-link>
                                <router-link to="/backtest" class="nav-link">
                                    <i class="fas fa-chart-line text-sm mr-2"></i>Backtest
                                </router-link>
                                <router-link to="/risk" class="nav-link">
                                    <i class="fas fa-shield-alt text-sm mr-2"></i>Risk
                                </router-link>
                                <router-link to="/trading" class="nav-link">
                                    <i class="fas fa-chart-bar text-sm mr-2"></i>Trading
                                </router-link>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <div class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                            <span class="text-sm font-medium text-green-400">OPERATIONAL</span>
                        </div>
                    </div>
                </div>
            </nav>
            <main class="flex-1">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <router-view></router-view>
                </div>
            </main>
        </div>
    `,
    setup() {
        return {};
    }
};

// Initialize Vue app
const app = createApp(AppComponent);

// Use plugins
app.use(router);
app.use(pinia);

// Mount the app
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

// Manual DOM manipulation for router-view
// This is a temporary solution until we migrate to a proper SPA
const updateActiveNavLink = () => {
    const currentHash = window.location.hash || '#/';
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentHash) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
};

// Handle navigation
window.addEventListener('hashchange', () => {
    updateActiveNavLink();

    // Update router-view content based on route
    const route = window.location.hash.substring(1) || '/';
    const routerView = document.getElementById('router-view');

    if (routerView) {
        let content = '';
        switch(route) {
            case '/':
                content = `
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
                                <a href="#/agents" class="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                                    View Agents
                                </a>
                            </div>
                            <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 hover:border-purple-500 transition-colors">
                                <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                                    <i class="fas fa-chart-line mr-2 text-purple-400"></i>
                                    Strategy Backtest
                                </h2>
                                <p class="text-slate-400 mb-4">Test trading strategies</p>
                                <a href="#/backtest" class="inline-block px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors">
                                    Run Backtest
                                </a>
                            </div>
                            <div class="bg-slate-800 bg-opacity-70 p-6 rounded-lg border border-slate-700 hover:border-red-500 transition-colors">
                                <h2 class="text-xl font-bold mb-4 text-white flex items-center">
                                    <i class="fas fa-shield-alt mr-2 text-red-400"></i>
                                    Risk Dashboard
                                </h2>
                                <p class="text-slate-400 mb-4">Monitor portfolio risk</p>
                                <a href="#/risk" class="inline-block px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors">
                                    View Risk
                                </a>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case '/agents':
                content = '<h1 class="text-3xl font-bold text-white mb-6">Agent Management</h1><p class="text-slate-400">Vue components will be loaded dynamically...</p>';
                break;
            case '/backtest':
                content = '<h1 class="text-3xl font-bold text-white mb-6">Strategy Backtest</h1><p class="text-slate-400">Vue components will be loaded dynamically...</p>';
                break;
            case '/risk':
                content = '<h1 class="text-3xl font-bold text-white mb-6">Risk Management</h1><p class="text-slate-400">Vue components will be loaded dynamically...</p>';
                break;
            case '/trading':
                content = '<h1 class="text-3xl font-bold text-white mb-6">Trading Interface</h1><p class="text-slate-400">Vue components will be loaded dynamically...</p>';
                break;
            default:
                content = '<h1 class="text-3xl font-bold text-white mb-6">Not Found</h1><p class="text-slate-400">Page not found</p>';
        }
        routerView.innerHTML = content;
    }
};

// Initialize active nav link
updateActiveNavLink();

// Trigger initial load
window.dispatchEvent(new HashChangeEvent('hashchange'));
