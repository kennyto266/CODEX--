/**
 * Loading Components (Skeleton, Spinner, Progress)
 * Phase 7: Enhanced Architecture
 */

/**
 * Skeleton Loader Component
 */
export const SkeletonLoader = {
    name: 'SkeletonLoader',
    props: {
        type: {
            type: String,
            default: 'card',
            validator: (value) => ['card', 'table', 'list', 'chart', 'text', 'avatar', 'button'].includes(value)
        },
        count: {
            type: Number,
            default: 1
        },
        height: {
            type: String,
            default: null
        },
        width: {
            type: String,
            default: null
        }
    },
    computed: {
        skeletonClass() {
            return `skeleton skeleton-${this.type}`;
        }
    },
    template: `
        <div class="skeleton-container">
            <div v-for="i in count" :key="i" :class="skeletonClass" :style="{ height, width }">
                <!-- Card Skeleton -->
                <template v-if="type === 'card'">
                    <div class="skeleton-header">
                        <div class="skeleton-avatar"></div>
                        <div class="skeleton-title"></div>
                    </div>
                    <div class="skeleton-content">
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line short"></div>
                        <div class="skeleton-line"></div>
                    </div>
                </template>

                <!-- Table Skeleton -->
                <template v-else-if="type === 'table'">
                    <div class="skeleton-header-row">
                        <div class="skeleton-cell" v-for="i in 5" :key="i"></div>
                    </div>
                    <div class="skeleton-row" v-for="i in 3" :key="i">
                        <div class="skeleton-cell" v-for="j in 5" :key="j"></div>
                    </div>
                </template>

                <!-- List Skeleton -->
                <template v-else-if="type === 'list'">
                    <div class="skeleton-list-item" v-for="i in 4" :key="i">
                        <div class="skeleton-avatar small"></div>
                        <div class="skeleton-content-block">
                            <div class="skeleton-line"></div>
                            <div class="skeleton-line short"></div>
                        </div>
                    </div>
                </template>

                <!-- Chart Skeleton -->
                <template v-else-if="type === 'chart'">
                    <div class="skeleton-chart">
                        <div class="skeleton-chart-bars">
                            <div class="skeleton-bar" v-for="i in 10" :key="i"></div>
                        </div>
                    </div>
                </template>

                <!-- Text Skeleton -->
                <template v-else-if="type === 'text'">
                    <div class="skeleton-text-line" v-for="i in 3" :key="i" :class="{ 'short': i === 3 }"></div>
                </template>

                <!-- Avatar Skeleton -->
                <template v-else-if="type === 'avatar'">
                    <div class="skeleton-avatar"></div>
                </template>

                <!-- Button Skeleton -->
                <template v-else-if="type === 'button'">
                    <div class="skeleton-button"></div>
                </template>
            </div>
        </div>
    `
};

/**
 * Spinner Component
 */
export const Spinner = {
    name: 'Spinner',
    props: {
        size: {
            type: String,
            default: 'medium', // small, medium, large
            validator: (value) => ['small', 'medium', 'large'].includes(value)
        },
        color: {
            type: String,
            default: 'primary' // primary, secondary, white
        },
        text: {
            type: String,
            default: null
        }
    },
    computed: {
        spinnerClass() {
            return `spinner spinner-${this.size} spinner-${this.color}`;
        }
    },
    template: `
        <div class="spinner-wrapper">
            <div :class="spinnerClass"></div>
            <span v-if="text" class="spinner-text">{{ text }}</span>
        </div>
    `
};

/**
 * Progress Bar Component
 */
export const ProgressBar = {
    name: 'ProgressBar',
    props: {
        value: {
            type: Number,
            default: 0,
            validator: (value) => value >= 0 && value <= 100
        },
        max: {
            type: Number,
            default: 100
        },
        size: {
            type: String,
            default: 'medium', // small, medium, large
            validator: (value) => ['small', 'medium', 'large'].includes(value)
        },
        color: {
            type: String,
            default: 'primary', // primary, success, warning, error
            validator: (value) => ['primary', 'success', 'warning', 'error'].includes(value)
        },
        showLabel: {
            type: Boolean,
            default: true
        },
        animated: {
            type: Boolean,
            default: true
        }
    },
    computed: {
        percentage() {
            return Math.min((this.value / this.max) * 100, 100);
        },
        progressClass() {
            return `progress progress-${this.size} progress-${this.color}`;
        }
    },
    template: `
        <div class="progress-container">
            <div :class="progressClass">
                <div
                    class="progress-bar"
                    :style="{ width: percentage + '%' }"
                    :class="{ 'animated': animated }"
                ></div>
            </div>
            <span v-if="showLabel" class="progress-label">
                {{ percentage.toFixed(0) }}%
            </span>
        </div>
    `
};

/**
 * Loading Overlay Component
 */
export const LoadingOverlay = {
    name: 'LoadingOverlay',
    props: {
        show: {
            type: Boolean,
            default: false
        },
        text: {
            type: String,
            default: 'Loading...'
        },
        backdrop: {
            type: Boolean,
            default: true
        },
        opacity: {
            type: Number,
            default: 0.5
        },
        zIndex: {
            type: Number,
            default: 9999
        }
    },
    computed: {
        overlayStyle() {
            return {
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: this.show ? 'flex' : 'none',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: this.backdrop ? `rgba(0, 0, 0, ${this.opacity})` : 'transparent',
                zIndex: this.zIndex
            };
        }
    },
    template: `
        <div :style="overlayStyle">
            <div class="loading-content">
                <Spinner size="large" />
                <p class="loading-text">{{ text }}</p>
            </div>
        </div>
    `
};

/**
 * Page Loading Component
 */
export const PageLoader = {
    name: 'PageLoader',
    components: {
        SkeletonLoader
    },
    props: {
        isLoading: {
            type: Boolean,
            default: false
        },
        skeletonType: {
            type: String,
            default: 'card'
        },
        skeletonCount: {
            type: Number,
            default: 3
        }
    },
    template: `
        <div>
            <SkeletonLoader
                v-if="isLoading"
                :type="skeletonType"
                :count="skeletonCount"
            />
            <slot v-else></slot>
        </div>
    `
};

/**
 * Data Table Loading Component
 */
export const TableLoader = {
    name: 'TableLoader',
    components: {
        SkeletonLoader
    },
    props: {
        isLoading: {
            type: Boolean,
            default: false
        },
        rows: {
            type: Number,
            default: 5
        }
    },
    template: `
        <div>
            <SkeletonLoader
                v-if="isLoading"
                type="table"
                :count="rows"
            />
            <slot v-else></slot>
        </div>
    `
};

/**
 * CSS Styles for Components
 */
export const loadingStyles = `
<style>
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 37%, #f0f0f0 63%);
    background-size: 400% 100%;
    animation: skeleton-loading 1.4s ease infinite;
    border-radius: 4px;
}

@keyframes skeleton-loading {
    0% {
        background-position: 100% 50%;
    }
    100% {
        background-position: -100% 50%;
    }
}

.skeleton-container {
    width: 100%;
}

.skeleton-card {
    background: white;
    padding: 20px;
    margin-bottom: 16px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.skeleton-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
}

.skeleton-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    margin-right: 12px;
}

.skeleton-avatar.small {
    width: 36px;
    height: 36px;
}

.skeleton-title {
    flex: 1;
    height: 20px;
    border-radius: 4px;
}

.skeleton-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.skeleton-line {
    height: 16px;
    border-radius: 4px;
}

.skeleton-line.short {
    width: 60%;
}

.skeleton-header-row,
.skeleton-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    padding: 12px;
}

.skeleton-cell {
    height: 40px;
    border-radius: 4px;
}

.skeleton-list-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #eee;
}

.skeleton-content-block {
    flex: 1;
}

.skeleton-chart {
    height: 300px;
    padding: 20px;
}

.skeleton-chart-bars {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    height: 100%;
}

.skeleton-bar {
    flex: 1;
    border-radius: 4px 4px 0 0;
}

.skeleton-text-line {
    height: 16px;
    margin-bottom: 8px;
    border-radius: 4px;
}

.skeleton-text-line.short {
    width: 40%;
}

.skeleton-button {
    width: 120px;
    height: 40px;
    border-radius: 6px;
}

/* Spinner Styles */
.spinner-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.spinner {
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.spinner-small {
    width: 20px;
    height: 20px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #3b82f6;
}

.spinner-medium {
    width: 40px;
    height: 40px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3b82f6;
}

.spinner-large {
    width: 60px;
    height: 60px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3b82f6;
}

.spinner-white {
    border-color: rgba(255,255,255,0.3);
    border-top-color: white;
}

.spinner-text {
    margin-top: 12px;
    color: #6b7280;
    font-size: 14px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Progress Bar Styles */
.progress-container {
    width: 100%;
}

.progress {
    width: 100%;
    background-color: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
}

.progress-small {
    height: 6px;
}

.progress-medium {
    height: 12px;
}

.progress-large {
    height: 20px;
}

.progress-bar {
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 10px;
}

.progress-bar.animated {
    position: relative;
    overflow: hidden;
}

.progress-bar.animated::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    background-image: linear-gradient(
        -45deg,
        rgba(255, 255, 255, .2) 25%,
        transparent 25%,
        transparent 50%,
        rgba(255, 255, 255, .2) 50%,
        rgba(255, 255, 255, .2) 75%,
        transparent 75%,
        transparent
    );
    background-size: 50px 50px;
    animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
    0% {
        background-position: 50px 0;
    }
    100% {
        background-position: 0 0;
    }
}

.progress-primary .progress-bar {
    background-color: #3b82f6;
}

.progress-success .progress-bar {
    background-color: #10b981;
}

.progress-warning .progress-bar {
    background-color: #f59e0b;
}

.progress-error .progress-bar {
    background-color: #ef4444;
}

.progress-label {
    display: block;
    margin-top: 6px;
    text-align: right;
    font-size: 12px;
    color: #6b7280;
}

/* Loading Overlay Styles */
.loading-content {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    display: flex;
    flex-direction: column;
    align-items: center;
}

.loading-text {
    margin-top: 20px;
    color: #4b5563;
    font-size: 16px;
}
</style>
`;
