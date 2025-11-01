# Routing System Specification

**Spec ID**: `routing-system`
**Change ID**: `integrate-vue-components`
**Version**: 1.0
**Status**: DRAFT

---

## Overview

This specification defines the client-side routing system for the Vue-integrated CODEX Trading Dashboard using Vue Router, enabling navigation between different dashboard sections without full page reloads.

---

## Requirements

### Functional Requirements

#### FR-001: Client-Side Routing
- **Description**: Implement client-side routing using Vue Router
- **Priority**: P0
- **Acceptance Criteria**:
  - Navigation between sections without page reload
  - Browser history management (back/forward buttons work)
  - Deep linking support (direct URLs load correct view)
  - Active route highlighting in navigation

#### FR-002: Route Configuration
- **Description**: Define routes for all dashboard sections
- **Priority**: P0
- **Route Definitions**:
  ```
  /                       - Dashboard Overview (current page)
  /backtest               - Strategy Backtest System
  /agents                 - Agent Management
  /risk                   - Risk Dashboard
  /trading                - Trading Interface
  /strategies             - Strategy Management
  /performance            - Performance Analytics
  /monitoring             - System Monitoring
  ```
- **Acceptance Criteria**:
  - All routes accessible via URL
  - Routes load correct components
  - Nested routes supported where needed

#### FR-003: Navigation Component
- **Description**: Create navigation component for route switching
- **Priority**: P0
- **Acceptance Criteria**:
  - Navigation menu displayed
  - Active route highlighted
  - Mobile-responsive navigation
  - Icons and labels for each section

#### FR-004: Route Guards
- **Description**: Implement route guards for authentication/authorization
- **Priority**: P1
- **Acceptance Criteria**:
  - Guard checks before route navigation
  - Redirect unauthorized access
  - Loading states during guard checks

---

## Technical Specifications

### Vue Router Configuration

#### Router Setup

```javascript
// router/index.js
import { createRouter, createWebHashHistory } from 'vue-router';

// Import components (will be converted from .vue files)
import Dashboard from '../components/Dashboard.vue';
import BacktestPanel from '../components/BacktestPanel.vue';
import AgentPanel from '../components/AgentPanel.vue';
import RiskPanel from '../components/RiskPanel.vue';
import TradingPanel from '../components/TradingPanel.vue';
import StrategyPanel from '../components/StrategyPanel.vue';
import PerformancePanel from '../components/PerformancePanel.vue';
import MonitoringPanel from '../components/MonitoringPanel.vue';

// Route definitions
const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
            title: 'Dashboard Overview',
            icon: 'fas fa-tachometer-alt',
            description: 'System overview and key metrics'
        }
    },
    {
        path: '/backtest',
        name: 'Backtest',
        component: BacktestPanel,
        meta: {
            title: 'Strategy Backtest',
            icon: 'fas fa-chart-line',
            description: 'Backtest trading strategies'
        }
    },
    {
        path: '/agents',
        name: 'Agents',
        component: AgentPanel,
        meta: {
            title: 'Agent Management',
            icon: 'fas fa-robot',
            description: 'Manage AI trading agents'
        }
    },
    {
        path: '/risk',
        name: 'Risk',
        component: RiskPanel,
        meta: {
            title: 'Risk Dashboard',
            icon: 'fas fa-shield-alt',
            description: 'Monitor portfolio risk'
        }
    },
    {
        path: '/trading',
        name: 'Trading',
        component: TradingPanel,
        meta: {
            title: 'Trading Interface',
            icon: 'fas fa-chart-bar',
            description: 'Execute trades and manage positions'
        }
    },
    {
        path: '/strategies',
        name: 'Strategies',
        component: StrategyPanel,
        meta: {
            title: 'Strategy Management',
            icon: 'fas fa-brain',
            description: 'Configure and optimize strategies'
        }
    },
    {
        path: '/performance',
        name: 'Performance',
        component: PerformancePanel,
        meta: {
            title: 'Performance Analytics',
            icon: 'fas fa-chart-pie',
            description: 'Detailed performance analysis'
        }
    },
    {
        path: '/monitoring',
        name: 'Monitoring',
        component: MonitoringPanel,
        meta: {
            title: 'System Monitoring',
            icon: 'fas fa-desktop',
            description: 'System health and metrics'
        }
    },
    // 404 catch-all route
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFound,
        meta: {
            title: 'Page Not Found'
        }
    }
];

// Create router instance
const router = createRouter({
    // Use hash history for compatibility with static hosting
    history: createWebHashHistory(),
    routes,
    // Scroll behavior
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition;
        } else {
            return { top: 0 };
        }
    }
});

// Global navigation guards
router.beforeEach((to, from, next) => {
    // Set document title
    if (to.meta && to.meta.title) {
        document.title = `${to.meta.title} - CODEX Dashboard`;
    } else {
        document.title = 'CODEX Dashboard';
    }

    // Any global authentication checks can go here
    next();
});

router.afterEach((to, from) => {
    // Track page views for analytics
    console.log(`Navigated from ${from.path} to ${to.path}`);
});

export default router;
```

#### Route Metadata Structure

```typescript
interface RouteMeta {
    title: string;           // Page title
    icon: string;            // FontAwesome icon class
    description: string;     // Brief description
    requiresAuth?: boolean;  // Authentication required
    roles?: string[];        // Required user roles
    keepAlive?: boolean;     // Keep component alive in memory
    hideInNav?: boolean;     // Hide from navigation menu
}
```

---

## Navigation Component

### Navigation Menu Implementation

```javascript
// components/Navigation.vue
const Navigation = {
    template: `
        <nav class="bg-gray-900 bg-opacity-95 backdrop-blur border-b border-gray-800 sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between h-16">
                    <!-- Logo/Brand -->
                    <div class="flex items-center">
                        <router-link to="/" class="flex items-center space-x-3">
                            <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
                                <span class="text-white font-bold text-sm">C</span>
                            </div>
                            <span class="text-xl font-bold text-white hidden sm:block">
                                CODEX
                            </span>
                        </router-link>
                    </div>

                    <!-- Desktop Navigation -->
                    <div class="hidden md:block">
                        <div class="ml-10 flex items-baseline space-x-2">
                            <router-link
                                v-for="item in menuItems"
                                :key="item.path"
                                :to="item.path"
                                class="nav-link group relative"
                                :class="{ 'active': $route.path === item.path }"
                                :title="item.meta.description"
                            >
                                <div class="flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors">
                                    <i :class="[item.meta.icon, 'text-sm']"></i>
                                    <span class="text-sm font-medium">{{ item.name }}</span>
                                </div>

                                <!-- Active indicator -->
                                <span
                                    v-if="$route.path === item.path"
                                    class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400 rounded-full"
                                ></span>
                            </router-link>
                        </div>
                    </div>

                    <!-- System Status -->
                    <div class="hidden lg:flex items-center space-x-4">
                        <div class="flex items-center space-x-2">
                            <div :class="['w-2 h-2 rounded-full', statusIndicatorClass]"></div>
                            <span :class="['text-sm font-medium', statusTextClass]">
                                {{ systemStatus }}
                            </span>
                        </div>
                    </div>

                    <!-- Mobile menu button -->
                    <div class="md:hidden">
                        <button
                            @click="mobileMenuOpen = !mobileMenuOpen"
                            class="text-gray-400 hover:text-white focus:outline-none"
                        >
                            <i :class="mobileMenuOpen ? 'fas fa-times' : 'fas fa-bars'"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Mobile Navigation Menu -->
            <div
                v-if="mobileMenuOpen"
                class="md:hidden bg-gray-800 border-t border-gray-700"
            >
                <div class="px-2 pt-2 pb-3 space-y-1">
                    <router-link
                        v-for="item in menuItems"
                        :key="item.path"
                        :to="item.path"
                        class="mobile-nav-link block"
                        :class="{ 'active': $route.path === item.path }"
                        @click="mobileMenuOpen = false"
                    >
                        <div class="flex items-center space-x-3 px-3 py-2 rounded-lg">
                            <i :class="[item.meta.icon, 'text-lg w-6']"></i>
                            <div>
                                <div class="font-medium">{{ item.name }}</div>
                                <div class="text-xs text-gray-400">{{ item.meta.description }}</div>
                            </div>
                        </div>
                    </router-link>
                </div>

                <!-- Mobile status -->
                <div class="px-4 py-3 border-t border-gray-700">
                    <div class="flex items-center space-x-2">
                        <div :class="['w-2 h-2 rounded-full', statusIndicatorClass]"></div>
                        <span :class="['text-sm font-medium', statusTextClass]">
                            System Status: {{ systemStatus }}
                        </span>
                    </div>
                </div>
            </div>
        </nav>
    `,
    setup() {
        const router = useRouter();
        const route = useRoute();

        const mobileMenuOpen = ref(false);
        const systemStatus = ref('OPERATIONAL');

        // Get menu items from router
        const menuItems = computed(() => {
            return router.getRoutes()
                .filter(route => route.meta && route.meta.title && !route.meta.hideInNav)
                .sort((a, b) => a.meta.order - b.meta.order);
        });

        // Active route
        const currentRoute = computed(() => route.path);

        // System status styling
        const statusIndicatorClass = computed(() => {
            switch (systemStatus.value) {
                case 'OPERATIONAL': return 'bg-green-400';
                case 'DEGRADED': return 'bg-yellow-400';
                case 'OFFLINE': return 'bg-red-400';
                default: return 'bg-gray-400';
            }
        });

        const statusTextClass = computed(() => {
            switch (systemStatus.value) {
                case 'OPERATIONAL': return 'text-green-400';
                case 'DEGRADED': return 'text-yellow-400';
                case 'OFFLINE': return 'text-red-400';
                default: return 'text-gray-400';
            }
        });

        // Close mobile menu on route change
        watch(() => route.path, () => {
            mobileMenuOpen.value = false;
        });

        return {
            mobileMenuOpen,
            menuItems,
            currentRoute,
            systemStatus,
            statusIndicatorClass,
            statusTextClass
        };
    }
};
```

### Navigation Styles

```css
/* styles/navigation.css */
.nav-link {
    @apply relative text-gray-300 hover:text-white px-3 py-2 rounded-lg transition-colors;
}

.nav-link:hover {
    @apply bg-gray-800 bg-opacity-50;
}

.nav-link.active {
    @apply text-blue-400;
}

.nav-link.active::before {
    content: '';
    @apply absolute left-0 top-0 bottom-0 w-1 bg-blue-400 rounded-r-full;
}

.mobile-nav-link {
    @apply text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors;
}

.mobile-nav-link.active {
    @apply text-blue-400 bg-gray-700 bg-opacity-50;
}
```

---

## Route Guards

### Authentication Guard

```javascript
// router/guards/auth.js
export function setupAuthGuard(router) {
    router.beforeEach(async (to, from, next) => {
        // Check if route requires authentication
        if (to.meta.requiresAuth) {
            // Check if user is authenticated
            const isAuthenticated = await checkAuthentication();

            if (!isAuthenticated) {
                // Redirect to login page
                next({
                    path: '/login',
                    query: { redirect: to.fullPath }
                });
                return;
            }

            // Check role-based access
            if (to.meta.roles && to.meta.roles.length > 0) {
                const userRoles = await getUserRoles();

                const hasRequiredRole = to.meta.roles.some(
                    role => userRoles.includes(role)
                );

                if (!hasRequiredRole) {
                    next({ path: '/403' });
                    return;
                }
            }
        }

        next();
    });
}
```

### Loading Guard

```javascript
// router/guards/loading.js
export function setupLoadingGuard(router) {
    router.beforeEach((to, from, next) => {
        // Show loading indicator
        const loadingElement = document.getElementById('global-loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }

        next();
    });

    router.afterEach(() => {
        // Hide loading indicator
        const loadingElement = document.getElementById('global-loading');
        if (loadingElement) {
            setTimeout(() => {
                loadingElement.style.display = 'none';
            }, 300); // Small delay for smooth transition
        }
    });
}
```

---

## Layout Component

### Main Layout Wrapper

```javascript
// components/Layout.vue
const Layout = {
    template: `
        <div id="app-layout" class="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
            <!-- Navigation -->
            <Navigation />

            <!-- Main Content -->
            <main class="flex-1">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <!-- Page Header -->
                    <div v-if="showHeader" class="mb-8">
                        <div class="flex items-center justify-between">
                            <div>
                                <h1 class="text-3xl font-bold text-white">
                                    {{ currentPageTitle }}
                                </h1>
                                <p v-if="currentPageDescription" class="text-gray-400 mt-1">
                                    {{ currentPageDescription }}
                                </p>
                            </div>

                            <!-- Page Actions -->
                            <div v-if="pageActions" class="flex space-x-2">
                                <slot name="actions"></slot>
                            </div>
                        </div>

                        <!-- Breadcrumbs -->
                        <nav v-if="breadcrumbs.length > 0" class="mt-4" aria-label="Breadcrumb">
                            <ol class="flex items-center space-x-2 text-sm text-gray-400">
                                <li v-for="(crumb, index) in breadcrumbs" :key="index">
                                    <router-link
                                        v-if="crumb.path && index < breadcrumbs.length - 1"
                                        :to="crumb.path"
                                        class="hover:text-white transition-colors"
                                    >
                                        {{ crumb.name }}
                                    </router-link>
                                    <span v-else class="text-white">{{ crumb.name }}</span>
                                    <i v-if="index < breadcrumbs.length - 1" class="fas fa-chevron-right ml-2 text-xs"></i>
                                </li>
                            </ol>
                        </nav>
                    </div>

                    <!-- Router View -->
                    <router-view v-slot="{ Component, route }">
                        <transition
                            :name="route.meta.transition || 'fade'"
                            mode="out-in"
                        >
                            <component :is="Component" :key="route.path" />
                        </transition>
                    </router-view>
                </div>
            </main>

            <!-- Global Loading Indicator -->
            <div
                id="global-loading"
                class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
                style="display: none;"
            >
                <div class="bg-gray-800 rounded-lg p-6 flex items-center space-x-3">
                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
                    <span class="text-white">Loading...</span>
                </div>
            </div>
        </div>
    `,
    setup() {
        const route = useRoute();
        const router = useRouter();

        const currentRoute = computed(() => route);
        const currentPageTitle = computed(() => route.meta?.title || 'Dashboard');
        const currentPageDescription = computed(() => route.meta?.description);
        const showHeader = computed(() => route.meta?.showHeader !== false);
        const pageActions = computed(() => route.meta?.actions);

        // Generate breadcrumbs
        const breadcrumbs = computed(() => {
            const matched = route.matched.filter(item => item.meta && item.meta.title);
            return matched.map(item => ({
                name: item.meta.title,
                path: item.path
            }));
        });

        return {
            currentRoute,
            currentPageTitle,
            currentPageDescription,
            showHeader,
            pageActions,
            breadcrumbs
        };
    }
};
```

---

## Nested Routes

### Example: Agent Management with Tabs

```javascript
// In router configuration
{
    path: '/agents',
    component: AgentPanel,
    children: [
        {
            path: '',
            redirect: '/agents/list'
        },
        {
            path: 'list',
            name: 'AgentList',
            component: AgentList,
            meta: { title: 'Agent List' }
        },
        {
            path: 'status',
            name: 'AgentStatus',
            component: AgentStatus,
            meta: { title: 'Health Status' }
        },
        {
            path: 'logs',
            name: 'AgentLogs',
            component: AgentLogs,
            meta: { title: 'Agent Logs' }
        }
    ]
}
```

---

## Transitions & Animations

### Page Transitions

```css
/* transitions.css */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
    transition: all 0.3s ease;
}

.slide-left-enter-from {
    transform: translateX(100px);
    opacity: 0;
}

.slide-left-leave-to {
    transform: translateX(-100px);
    opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
    transition: all 0.3s ease;
}

.slide-right-enter-from {
    transform: translateX(-100px);
    opacity: 0;
}

.slide-right-leave-to {
    transform: translateX(100px);
    opacity: 0;
}
```

---

## Programmatic Navigation

### Programmatic Route Methods

```javascript
// utils/navigation.js
import { useRouter } from 'vue-router';

export function useNavigation() {
    const router = useRouter();

    const navigateTo = (path, options = {}) => {
        return router.push({
            path,
            ...options
        });
    };

    const navigateWithParams = (name, params, options = {}) => {
        return router.push({
            name,
            params,
            ...options
        });
    };

    const replaceRoute = (path) => {
        return router.replace(path);
    };

    const goBack = (steps = -1) => {
        return router.go(steps);
    };

    const refreshRoute = () => {
        return router.push(route.fullPath);
    };

    return {
        navigateTo,
        navigateWithParams,
        replaceRoute,
        goBack,
        refreshRoute
    };
}
```

### Navigation in Components

```javascript
// In a component
setup() {
    const { navigateTo, goBack } = useNavigation();

    const handleBacktestComplete = () => {
        navigateTo('/backtest/results');
    };

    const handleCancel = () => {
        goBack();
    };

    return {
        handleBacktestComplete,
        handleCancel
    };
}
```

---

## URL Structure

### Deep Linking Support

```
http://localhost:8001/#/                      → Dashboard Overview
http://localhost:8001/#/backtest              → Backtest System
http://localhost:8001/#/backtest/results      → Backtest Results
http://localhost:8001/#/agents                → Agent Management
http://localhost:8001/#/agents/list           → Agent List
http://localhost:8001/#/risk                  → Risk Dashboard
http://localhost:8001/#/trading               → Trading Interface
http://localhost:8001/#/trading/orders        → Orders List
http://localhost:8001/#/trading/history       → Trade History
```

### Query Parameters Support

```javascript
// Pass parameters via query string
router.push({
    path: '/backtest',
    query: {
        symbol: '0700.HK',
        period: '1Y',
        strategy: 'KDJ'
    }
});

// Access parameters in component
const route = useRoute();
const symbol = computed(() => route.query.symbol);
const period = computed(() => route.query.period);
```

---

## Performance Optimization

### Route-Based Code Splitting

```javascript
// Lazy load routes
const routes = [
    {
        path: '/backtest',
        name: 'Backtest',
        component: () => import('../components/BacktestPanel.vue')
    },
    {
        path: '/agents',
        name: 'Agents',
        component: () => import('../components/AgentPanel.vue')
    }
];
```

### Preloading Routes

```javascript
// Preload critical routes
router.onReady(() => {
    // Preload immediately
    router.resolve({ path: '/agents' });

    // Preload after idle
    requestIdleCallback(() => {
        router.resolve({ path: '/trading' });
        router.resolve({ path: '/risk' });
    });
});
```

---

## Testing

### Unit Tests

```javascript
// tests/router.test.js
import { createRouter, createWebHashHistory } from 'vue-router';
import { mount } from '@vue/test-utils';

describe('Router Configuration', () => {
    it('navigates to dashboard', async () => {
        const wrapper = mount(App, {
            global: {
                plugins: [router]
            }
        });

        await router.push('/');
        await router.isReady();

        expect(wrapper.find('[data-testid="dashboard"]').exists()).toBe(true);
    });

    it('highlights active route', async () => {
        const wrapper = mount(Navigation, {
            global: {
                plugins: [router]
            }
        });

        await router.push('/agents');
        await router.isReady();

        const agentsLink = wrapper.find('[data-testid="nav-agents"]');
        expect(agentsLink.classes()).toContain('active');
    });
});
```

### E2E Tests

```javascript
// cypress/e2e/routing.cy.js
describe('Client-side Routing', () => {
    it('navigates between sections', () => {
        cy.visit('/');

        // Navigate to backtest
        cy.get('[data-testid="nav-backtest"]').click();
        cy.url().should('include', '/#/backtest');
        cy.get('[data-testid="backtest-panel"]').should('be.visible');

        // Navigate to agents
        cy.get('[data-testid="nav-agents"]').click();
        cy.url().should('include', '/#/agents');
        cy.get('[data-testid="agent-panel"]').should('be.visible');
    });

    it('deep links work', () => {
        cy.visit('/#/agents');
        cy.get('[data-testid="agent-panel"]').should('be.visible');
    });

    it('browser back button works', () => {
        cy.visit('/#/agents');
        cy.go('back');
        cy.url().should('include', '/#/');
    });
});
```

---

## Accessibility

### ARIA Labels

```html
<!-- Navigation with ARIA -->
<nav aria-label="Main navigation">
    <ul role="menubar">
        <li role="none">
            <a
                role="menuitem"
                href="#/"
                aria-current="{{ $route.path === '/' ? 'page' : undefined }}"
            >
                Dashboard
            </a>
        </li>
    </ul>
</nav>
```

### Keyboard Navigation

```javascript
// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Alt + 1-8: Quick navigation
    if (e.altKey && !e.ctrlKey && !e.shiftKey) {
        const routes = ['/', '/backtest', '/agents', '/risk', '/trading'];
        const index = parseInt(e.key) - 1;
        if (index >= 0 && index < routes.length) {
            router.push(routes[index]);
        }
    }

    // Escape: Go back
    if (e.key === 'Escape' && !e.altKey && !e.ctrlKey) {
        router.go(-1);
    }
});
```

---

## Acceptance Criteria

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001 | Client-Side Routing | P0 | - |
| FR-002 | Route Configuration | P0 | - |
| FR-003 | Navigation Component | P0 | - |
| FR-004 | Route Guards | P1 | - |
| PERF-001 | Route Navigation < 200ms | P0 | - |
| PERF-002 | Code Splitting | P1 | - |
| ACCESS-001 | Keyboard Navigation | P1 | - |
| ACCESS-002 | ARIA Labels | P1 | - |
| TEST-001 | Unit Test Coverage | P1 | - |
| TEST-002 | E2E Test Coverage | P1 | - |

---

**Spec Status**: DRAFT
**Review Date**: TBD
**Approved By**: TBD
