/**
 * Vue Router Configuration with Lazy Loading
 * Phase 7: Enhanced Architecture
 */

import { createRouter, createWebHashHistory } from 'vue-router';
import { errorHandler } from './utils/errorHandler.js';

// Lazy load components
const AgentPanel = () => import('./components/AgentPanel.vue');
const BacktestPanel = () => import('./components/BacktestPanel.vue');
const RiskPanel = () => import('./components/RiskPanel.vue');
const TradingPanel = () => import('./components/TradingPanel.vue');
const TaskBoard = () => import('./components/TaskBoard.vue');

// Route definitions
const routes = [
    {
        path: '/',
        redirect: '/agents'
    },
    {
        path: '/agents',
        name: 'Agents',
        component: AgentPanel,
        meta: {
            title: 'Agent 管理系統',
            requiresAuth: true
        }
    },
    {
        path: '/backtest',
        name: 'Backtest',
        component: BacktestPanel,
        meta: {
            title: '策略回測',
            requiresAuth: true
        }
    },
    {
        path: '/risk',
        name: 'Risk',
        component: RiskPanel,
        meta: {
            title: '風險管理',
            requiresAuth: true
        }
    },
    {
        path: '/trading',
        name: 'Trading',
        component: TradingPanel,
        meta: {
            title: '交易執行',
            requiresAuth: true
        }
    },
    {
        path: '/tasks',
        name: 'TaskBoard',
        component: TaskBoard,
        meta: {
            title: '任務看板',
            requiresAuth: true
        }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: {
            template: `
                <div class="flex items-center justify-center min-h-screen bg-gray-50">
                    <div class="text-center">
                        <h1 class="text-6xl font-bold text-gray-400">404</h1>
                        <p class="mt-4 text-xl text-gray-600">Page Not Found</p>
                        <router-link to="/" class="mt-6 inline-block px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
                            Back to Home
                        </router-link>
                    </div>
                </div>
            `
        }
    }
];

// Create router instance
const router = createRouter({
    history: createWebHashHistory(),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition;
        } else {
            return { top: 0 };
        }
    }
});

// Global route guards
router.beforeEach((to, from, next) => {
    // Set page title
    if (to.meta?.title) {
        document.title = `${to.meta.title} - CODEX Dashboard`;
    }

    // Check authentication (placeholder)
    if (to.matched.some(record => record.meta.requiresAuth)) {
        // TODO: Add authentication check
        console.log('Route requires auth:', to.name);
    }

    next();
});

router.afterEach((to, from) => {
    console.log(`Navigation: ${from.name} -> ${to.name}`);
});

// Error handling for navigation
router.onError((error) => {
    errorHandler.handle(error, { context: 'router', from: from?.name, to: to?.name });
});

export default router;
