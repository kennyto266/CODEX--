/**
 * Performance Optimization Utilities
 * Phase 7: CODEX Dashboard Performance Tools
 */

const { h } = Vue;

// ============================================================================
// Error Boundary Component
// ============================================================================
export const ErrorBoundary = {
    name: 'ErrorBoundary',
    props: ['fallback', 'error'],
    data() {
        return {
            hasError: false,
            errorInfo: null
        };
    },
    errorCaptured(err, vm, info) {
        console.error('❌ Error caught by boundary:', err, info);
        this.hasError = true;
        this.errorInfo = info;

        // Report to monitoring system
        this.reportError({
            message: err.message,
            stack: err.stack,
            component: this.fallback,
            info: info,
            timestamp: Date.now()
        });

        return false;
    },
    methods: {
        reportError(errorData) {
            fetch('/api/monitoring/errors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(errorData)
            }).catch(err => console.error('Failed to report error:', err));
        },
        retry() {
            this.hasError = false;
            this.errorInfo = null;
        }
    },
    template: `
        <div v-if="hasError" class="error-boundary p-8 bg-red-900 bg-opacity-20 border border-red-700 rounded-lg">
            <h2 class="text-2xl font-bold text-red-400 mb-4">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Component Error
            </h2>
            <div class="bg-slate-800 p-4 rounded mb-4 overflow-auto">
                <p class="text-red-300 font-mono text-sm">{{ errorInfo?.message || 'An unexpected error occurred' }}</p>
                <p class="text-slate-400 text-xs mt-2">Component: {{ fallback }}</p>
            </div>
            <div class="flex space-x-2">
                <button @click="retry"
                        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                    <i class="fas fa-redo mr-2"></i>
                    Try Again
                </button>
                <button @click="window.location.reload()"
                        class="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-700 transition-colors">
                    <i class="fas fa-sync mr-2"></i>
                    Reload Page
                </button>
            </div>
        </div>
        <slot v-else></slot>
    `
};

// ============================================================================
// Performance Monitor
// ============================================================================
export const PerformanceMonitor = {
    metrics: {
        renders: new Map(),
        apiCalls: new Map(),
        memoryUsage: []
    },

    init() {
        if (typeof window.performance === 'undefined') {
            console.warn('⚠️ Performance API not supported');
            return;
        }

        // Monitor Core Web Vitals
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.measurePageLoad();
            }, 0);
        });

        // Monitor memory usage periodically
        setInterval(() => {
            if (window.performance.memory) {
                this.metrics.memoryUsage.push({
                    used: window.performance.memory.usedJSHeapSize,
                    total: window.performance.memory.totalJSHeapSize,
                    timestamp: Date.now()
                });

                // Keep only last 100 measurements
                if (this.metrics.memoryUsage.length > 100) {
                    this.metrics.memoryUsage.shift();
                }
            }
        }, 5000);

        console.log('✅ Performance monitoring initialized');
    },

    measurePageLoad() {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');

        const metrics = {
            loadTime: navigation.loadEventEnd - navigation.fetchStart,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
            firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
            timestamp: Date.now()
        };

        console.log('📊 Page Load Metrics:', metrics);
        this.reportMetrics(metrics);
    },

    measureComponentRender(componentName, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        const renderTime = end - start;

        this.metrics.renders.set(componentName, {
            time: renderTime,
            timestamp: Date.now()
        });

        // Warn if render time is too high
        if (renderTime > 16) { // 16ms = 60fps
            console.warn(`⚠️ Slow render: ${componentName} took ${renderTime.toFixed(2)}ms`);
        }

        return result;
    },

    measureAPICall(url, fn) {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        const duration = end - start;

        this.metrics.apiCalls.set(url, {
            duration: duration,
            timestamp: Date.now()
        });

        if (duration > 1000) {
            console.warn(`⚠️ Slow API call: ${url} took ${duration.toFixed(2)}ms`);
        }

        return result;
    },

    reportMetrics(metrics) {
        fetch('/api/monitoring/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(metrics)
        }).catch(err => console.error('Failed to report metrics:', err));
    },

    getReport() {
        return {
            renders: Object.fromEntries(this.metrics.renders),
            apiCalls: Object.fromEntries(this.metrics.apiCalls),
            memory: this.metrics.memoryUsage
        };
    }
};

// ============================================================================
// Skeleton Loader Component
// ============================================================================
export const SkeletonLoader = {
    name: 'SkeletonLoader',
    props: {
        type: {
            type: String,
            default: 'card',
            validator: (value) => ['card', 'table', 'list', 'chart', 'text'].includes(value)
        },
        count: {
            type: Number,
            default: 1
        },
        height: {
            type: String,
            default: 'h-4'
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
                <div class="bg-slate-800 bg-opacity-70 rounded-lg border border-slate-700 overflow-hidden">
                    <div class="p-4 border-b border-slate-700">
                        <div class="h-6 bg-slate-700 rounded w-1/4 animate-pulse"></div>
                    </div>
                    <div v-for="i in count" :key="i" class="p-4 border-b border-slate-700 last:border-b-0 animate-pulse">
                        <div class="flex space-x-4">
                            <div class="h-4 bg-slate-700 rounded flex-1"></div>
                            <div class="h-4 bg-slate-700 rounded w-20"></div>
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

            <template v-else-if="type === 'text'">
                <div v-for="i in count" :key="i"
                     :class="\`bg-slate-700 rounded \${height} mb-2 animate-pulse\`">
                </div>
            </template>
        </div>
    `
};

// ============================================================================
// Memory Optimizer
// ============================================================================
export const MemoryOptimizer = {
    cache: new WeakMap(),

    cacheResult(fn, key) {
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        const result = fn();
        this.cache.set(key, result);
        return result;
    },

    clearCache() {
        this.cache = new WeakMap();
    },

    // Clean up event listeners and observers
    cleanupVueComponent(component) {
        if (component.$once) {
            component.$once('hook:beforeDestroy', () => {
                // Cleanup logic
            });
        }
    }
};

// ============================================================================
export default {
    ErrorBoundary,
    PerformanceMonitor,
    SkeletonLoader,
    MemoryOptimizer
};
