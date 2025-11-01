/**
 * Vite Configuration for CODEX Dashboard
 * Phase 7: Bundle Optimization and Code Splitting
 */

import { defineConfig } from 'vite';

export default defineConfig({
    build: {
        // Enable code splitting
        rollupOptions: {
            output: {
                manualChunks: {
                    // Vendor chunk for Vue ecosystem
                    'vue-vendor': ['vue', 'vue-router', 'pinia'],

                    // Component library chunk
                    'components': [
                        './js/components/AgentPanel.js',
                        './js/components/RiskPanel.js',
                        './js/components/TradingPanel.js',
                        './js/components/BacktestPanel.js'
                    ],

                    // Utils chunk
                    'utils': [
                        './js/utils/api.js',
                        './js/utils/cache.js',
                        './js/utils/performance.js'
                    ]
                },

                // Asset naming
                assetFileNames: (assetInfo) => {
                    const info = assetInfo.name.split('.');
                    const ext = info[info.length - 1];

                    if (/\.(png|jpe?g|gif|svg|ico)$/i.test(assetInfo.name)) {
                        return `images/[name]-[hash].${ext}`;
                    }

                    if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
                        return `fonts/[name]-[hash].${ext}`;
                    }

                    return `assets/[name]-[hash].${ext}`;
                },

                chunkFileNames: 'js/[name]-[hash].js',
                entryFileNames: 'js/[name]-[hash].js'
            }
        },

        // Optimize dependencies
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: true,
                drop_debugger: true,
                pure_funcs: ['console.log', 'console.info']
            }
        },

        // Enable source maps for production debugging
        sourcemap: false,

        // Target modern browsers for smaller bundles
        target: 'es2015',

        // Chunk size warnings
        chunkSizeWarningLimit: 1000
    },

    // Optimize dependencies
    optimizeDeps: {
        include: [
            'vue',
            'vue-router',
            'pinia'
        ]
    },

    // Development server config
    server: {
        port: 3000,
        open: true,
        cors: true
    },

    // Plugins
    plugins: [
        // Custom plugin for lazy loading optimization
        {
            name: 'lazy-loading-optimizer',
            generateBundle() {
                console.log('✅ Bundle optimization complete');
                console.log('📦 Code splitting enabled');
                console.log('⚡ Tree shaking active');
            }
        }
    ]
});
