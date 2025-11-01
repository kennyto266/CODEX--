/**
 * Responsive Design Utilities
 * Phase 7: Enhanced Architecture
 */

import { BREAKPOINTS } from './constants.js';

/**
 * Breakpoint Manager
 */
class BreakpointManager {
    constructor() {
        this.breakpoints = BREAKPOINTS;
        this.currentBreakpoint = this.getCurrentBreakpoint();
        this.listeners = new Set();

        this.setupListeners();
    }

    /**
     * Setup media query listeners
     */
    setupListeners() {
        if (!window.matchMedia) {
            return;
        }

        // Create media queries for each breakpoint
        this.mediaQueries = {
            xs: window.matchMedia(`(max-width: ${this.breakpoints.xs - 1}px)`),
            sm: window.matchMedia(`(min-width: ${this.breakpoints.xs}px) and (max-width: ${this.breakpoints.sm - 1}px)`),
            md: window.matchMedia(`(min-width: ${this.breakpoints.sm}px) and (max-width: ${this.breakpoints.md - 1}px)`),
            lg: window.matchMedia(`(min-width: ${this.breakpoints.md}px) and (max-width: ${this.breakpoints.lg - 1}px)`),
            xl: window.matchMedia(`(min-width: ${this.breakpoints.lg}px) and (max-width: ${this.breakpoints.xl - 1}px)`),
            xxl: window.matchMedia(`(min-width: ${this.breakpoints.xl}px)`),
            smAndUp: window.matchMedia(`(min-width: ${this.breakpoints.xs}px)`),
            mdAndUp: window.matchMedia(`(min-width: ${this.breakpoints.sm}px)`),
            lgAndUp: window.matchMedia(`(min-width: ${this.breakpoints.md}px)`),
            xlAndUp: window.matchMedia(`(min-width: ${this.breakpoints.lg}px)`)
        };

        // Add listeners to each breakpoint
        Object.entries(this.mediaQueries).forEach(([name, mq]) => {
            mq.addEventListener('change', () => this.handleBreakpointChange(name, mq.matches));
        });
    }

    /**
     * Handle breakpoint change
     */
    handleBreakpointChange(name, matches) {
        if (matches) {
            this.currentBreakpoint = this.getBreakpointFromMediaQuery(name);
            this.notifyListeners(this.currentBreakpoint);
        }
    }

    /**
     * Get current breakpoint from media query name
     */
    getBreakpointFromMediaQuery(name) {
        if (name === 'xs') return 'xs';
        if (name === 'sm' || name === 'smAndUp') return 'sm';
        if (name === 'md' || name === 'mdAndUp') return 'md';
        if (name === 'lg' || name === 'lgAndUp') return 'lg';
        if (name === 'xl' || name === 'xlAndUp') return 'xl';
        if (name === 'xxl') return 'xxl';
        return 'unknown';
    }

    /**
     * Get current breakpoint
     */
    getCurrentBreakpoint() {
        if (!window.matchMedia) {
            return window.innerWidth < this.breakpoints.sm ? 'xs' : 'sm';
        }

        for (const [name, mq] of Object.entries(this.mediaQueries)) {
            if (mq.matches) {
                return this.getBreakpointFromMediaQuery(name);
            }
        }

        return 'unknown';
    }

    /**
     * Check if current screen matches breakpoint
     */
    isBreakpoint(breakpoint) {
        return this.currentBreakpoint === breakpoint;
    }

    /**
     * Check if screen is smaller than breakpoint
     */
    isSmallerThan(breakpoint) {
        const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
        const currentIndex = breakpointOrder.indexOf(this.currentBreakpoint);
        const targetIndex = breakpointOrder.indexOf(breakpoint);
        return currentIndex < targetIndex;
    }

    /**
     * Check if screen is larger than breakpoint
     */
    isLargerThan(breakpoint) {
        const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
        const currentIndex = breakpointOrder.indexOf(this.currentBreakpoint);
        const targetIndex = breakpointOrder.indexOf(breakpoint);
        return currentIndex > targetIndex;
    }

    /**
     * Get viewport width
     */
    getViewportWidth() {
        return window.innerWidth;
    }

    /**
     * Get viewport height
     */
    getViewportHeight() {
        return window.innerHeight;
    }

    /**
     * Check if device is mobile
     */
    isMobile() {
        return this.isBreakpoint('xs') || this.isBreakpoint('sm');
    }

    /**
     * Check if device is tablet
     */
    isTablet() {
        return this.isBreakpoint('md') || this.isBreakpoint('lg');
    }

    /**
     * Check if device is desktop
     */
    isDesktop() {
        return this.isBreakpoint('xl') || this.isBreakpoint('xxl');
    }

    /**
     * Add breakpoint change listener
     */
    addListener(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notify listeners of breakpoint change
     */
    notifyListeners(breakpoint) {
        this.listeners.forEach(callback => {
            try {
                callback(breakpoint);
            } catch (error) {
                console.error('Error in breakpoint listener:', error);
            }
        });
    }
}

/**
 * Responsive Table Component
 */
export const ResponsiveTable = {
    name: 'ResponsiveTable',
    props: {
        data: {
            type: Array,
            required: true
        },
        columns: {
            type: Array,
            required: true
        },
        keyField: {
            type: String,
            default: 'id'
        }
    },
    data() {
        return {
            isMobileView: false,
            selectedRow: null
        };
    },
    computed: {
        tableClass() {
            return this.isMobileView ? 'responsive-table mobile' : 'responsive-table';
        }
    },
    mounted() {
        // Check if mobile on mount
        this.isMobileView = breakpointManager.isMobile();

        // Listen for breakpoint changes
        this.unsubscribe = breakpointManager.addListener((breakpoint) => {
            this.isMobileView = breakpointManager.isMobile();
        });
    },
    unmounted() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    },
    methods: {
        toggleRow(row) {
            this.selectedRow = this.selectedRow === row ? null : row;
        }
    },
    template: `
        <div :class="tableClass">
            <!-- Desktop Table View -->
            <table v-if="!isMobileView" class="table">
                <thead>
                    <tr>
                        <th v-for="column in columns" :key="column.key">
                            {{ column.label }}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="row in data" :key="row[keyField]">
                        <td v-for="column in columns" :key="column.key">
                            {{ row[column.key] }}
                        </td>
                    </tr>
                </tbody>
            </table>

            <!-- Mobile Card View -->
            <div v-else class="table-cards">
                <div v-for="row in data" :key="row[keyField]" class="table-card">
                    <div
                        class="card-header"
                        @click="toggleRow(row)"
                    >
                        <div class="card-title">
                            {{ row[columns[0].key] }}
                        </div>
                        <div class="card-toggle">
                            {{ selectedRow === row ? '▲' : '▼' }}
                        </div>
                    </div>
                    <div v-if="selectedRow === row" class="card-content">
                        <div
                            v-for="column in columns.slice(1)"
                            :key="column.key"
                            class="card-row"
                        >
                            <span class="card-label">{{ column.label }}:</span>
                            <span class="card-value">{{ row[column.key] }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

/**
 * Responsive Grid Component
 */
export const ResponsiveGrid = {
    name: 'ResponsiveGrid',
    props: {
        items: {
            type: Array,
            default: () => []
        },
        minItemWidth: {
            type: Number,
            default: 250 // Minimum width per item in px
        },
        gap: {
            type: String,
            default: '16px'
        }
    },
    computed: {
        columnsCount() {
            const containerWidth = breakpointManager.getViewportWidth();
            const padding = 32; // Account for padding
            const availableWidth = containerWidth - padding;
            const count = Math.floor(availableWidth / this.minItemWidth);
            return Math.max(1, count);
        },
        gridStyle() {
            return {
                display: 'grid',
                gridTemplateColumns: `repeat(${this.columnsCount}, 1fr)`,
                gap: this.gap
            };
        }
    },
    template: `
        <div class="responsive-grid" :style="gridStyle">
            <slot v-for="item in items" :key="item.id" :item="item"></slot>
        </div>
    `
};

/**
 * Media Query Hook for Vue
 */
export const useMediaQuery = (breakpoint) => {
    const isMatching = ref(breakpointManager.isBreakpoint(breakpoint));

    const updateMatch = () => {
        isMatching.value = breakpointManager.isBreakpoint(breakpoint);
    };

    onMounted(() => {
        const unsubscribe = breakpointManager.addListener(updateMatch);
        onUnmounted(() => unsubscribe());
    });

    return isMatching;
};

/**
 * Responsive Mixin for Vue Components
 */
export const responsiveMixin = {
    data() {
        return {
            currentBreakpoint: breakpointManager.getCurrentBreakpoint(),
            isMobile: breakpointManager.isMobile(),
            isTablet: breakpointManager.isTablet(),
            isDesktop: breakpointManager.isDesktop()
        };
    },
    mounted() {
        this.unsubscribe = breakpointManager.addListener((breakpoint) => {
            this.currentBreakpoint = breakpoint;
            this.isMobile = breakpointManager.isMobile();
            this.isTablet = breakpointManager.isTablet();
            this.isDesktop = breakpointManager.isDesktop();
        });
    },
    unmounted() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    },
    methods: {
        isBreakpoint(breakpoint) {
            return breakpointManager.isBreakpoint(breakpoint);
        },
        isSmallerThan(breakpoint) {
            return breakpointManager.isSmallerThan(breakpoint);
        },
        isLargerThan(breakpoint) {
            return breakpointManager.isLargerThan(breakpoint);
        }
    }
};

/**
 * Responsive Styles
 */
const responsiveStyles = `
<style>
.responsive-table {
    width: 100%;
    overflow-x: auto;
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table th,
.table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-primary);
}

.table th {
    background: var(--bg-secondary);
    font-weight: 600;
    color: var(--text-primary);
}

.table tr:hover {
    background: var(--bg-tertiary);
}

.table-cards {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.table-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    overflow: hidden;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    cursor: pointer;
    background: var(--bg-secondary);
}

.card-title {
    font-weight: 600;
    color: var(--text-primary);
}

.card-toggle {
    color: var(--text-secondary);
    font-size: 12px;
}

.card-content {
    padding: 16px;
}

.card-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-primary);
}

.card-row:last-child {
    border-bottom: none;
}

.card-label {
    color: var(--text-secondary);
    font-weight: 500;
}

.card-value {
    color: var(--text-primary);
}

.responsive-grid {
    width: 100%;
}

@media (max-width: 767px) {
    .table {
        font-size: 14px;
    }

    .table th,
    .table td {
        padding: 8px;
    }

    .responsive-grid {
        grid-template-columns: 1fr !important;
    }
}
</style>
`;

// Inject styles
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('div');
    styleElement.innerHTML = responsiveStyles;
    document.head.appendChild(styleElement.firstElementChild);
}

// Create global breakpoint manager instance
const breakpointManager = new BreakpointManager();

// Export
export { breakpointManager };
export default breakpointManager;
