/**
 * Application Constants
 * Phase 7: Enhanced Architecture
 */

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
    AGENTS: '/api/agents',
    PORTFOLIO: '/api/trading/portfolio',
    POSITIONS: '/api/trading/positions',
    ORDERS: '/api/trading/orders',
    BACKTEST: '/api/backtest',
    STRATEGIES: '/api/strategies',
    RISK: '/api/risk',
    MARKET_DATA: '/api/market',
    HEALTH: '/api/health'
};

/**
 * WebSocket Endpoints
 */
export const WS_ENDPOINTS = {
    REAL_TIME_DATA: '/ws/real-time',
    AGENT_UPDATES: '/ws/agents',
    TRADING_SIGNALS: '/ws/signals',
    RISK_ALERTS: '/ws/risk'
};

/**
 * Chart Colors
 */
export const CHART_COLORS = {
    PRIMARY: '#3b82f6',
    SECONDARY: '#8b5cf6',
    SUCCESS: '#10b981',
    DANGER: '#ef4444',
    WARNING: '#f59e0b',
    INFO: '#06b6d4',
    ACCENT: '#ec4899',
    NEUTRAL: '#6b7280',

    // Stock colors
    GREEN: '#10b981',
    RED: '#ef4444',
    UP: '#10b981',
    DOWN: '#ef4444',

    // Portfolio colors
    LONG: '#3b82f6',
    SHORT: '#ef4444',
    CASH: '#10b981',
    POSITION: '#8b5cf6'
};

/**
 * Agent Types and Statuses
 */
export const AGENT_TYPES = {
    COORDINATOR: 'coordinator',
    DATA_SCIENTIST: 'data_scientist',
    QUANTITATIVE_ANALYST: 'quantitative_analyst',
    QUANTITATIVE_ENGINEER: 'quantitative_engineer',
    PORTFOLIO_MANAGER: 'portfolio_manager',
    RESEARCH_ANALYST: 'research_analyst',
    RISK_ANALYST: 'risk_analyst'
};

export const AGENT_STATUS = {
    RUNNING: 'running',
    STOPPED: 'stopped',
    ERROR: 'error',
    PENDING: 'pending',
    INITIALIZING: 'initializing'
};

/**
 * Order Types
 */
export const ORDER_TYPES = {
    MARKET: 'market',
    LIMIT: 'limit',
    STOP: 'stop',
    STOP_LIMIT: 'stop_limit',
    TRAILING_STOP: 'trailing_stop'
};

export const ORDER_SIDES = {
    BUY: 'buy',
    SELL: 'sell'
};

export const ORDER_STATUS = {
    NEW: 'new',
    PARTIALLY_FILLED: 'partially_filled',
    FILLED: 'filled',
    CANCELED: 'canceled',
    REJECTED: 'rejected',
    PENDING: 'pending'
};

/**
 * Strategy Types
 */
export const STRATEGY_TYPES = {
    MOVING_AVERAGE: 'moving_average',
    RSI: 'rsi',
    MACD: 'macd',
    BOLLINGER_BANDS: 'bollinger_bands',
    KDJ: 'kdj',
    CCI: 'cci',
    ADX: 'adx',
    ATR: 'atr',
    OBV: 'obv',
    ICHIMOKU: 'ichimoku',
    PARABOLIC_SAR: 'parabolic_sar'
};

/**
 * Risk Metrics
 */
export const RISK_LEVELS = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
};

export const RISK_THRESHOLDS = {
    VAR_LIMIT: 0.05, // 5% VaR limit
    DRAWDOWN_LIMIT: 0.10, // 10% max drawdown
    POSITION_LIMIT: 0.20, // 20% per position
    SECTOR_LIMIT: 0.30, // 30% per sector
    LEVERAGE_LIMIT: 2.0 // 2x max leverage
};

/**
 * Time Constants
 */
export const TIME_PERIODS = {
    ONE_MINUTE: 60 * 1000,
    FIVE_MINUTES: 5 * 60 * 1000,
    FIFTEEN_MINUTES: 15 * 60 * 1000,
    THIRTY_MINUTES: 30 * 60 * 1000,
    ONE_HOUR: 60 * 60 * 1000,
    ONE_DAY: 24 * 60 * 60 * 1000,
    ONE_WEEK: 7 * 24 * 60 * 60 * 1000,
    ONE_MONTH: 30 * 24 * 60 * 60 * 1000,
    THREE_MONTHS: 90 * 24 * 60 * 60 * 1000,
    SIX_MONTHS: 180 * 24 * 60 * 60 * 1000,
    ONE_YEAR: 365 * 24 * 60 * 60 * 1000
};

/**
 * Cache Configurations
 */
export const CACHE_CONFIG = {
    DEFAULT_TTL: 5 * 60 * 1000, // 5 minutes
    MARKET_DATA_TTL: 1 * 60 * 1000, // 1 minute
    PORTFOLIO_TTL: 30 * 1000, // 30 seconds
    AGENT_STATUS_TTL: 10 * 1000, // 10 seconds
    CACHE_SIZE: 200,
    PREFETCH_DELAY: 1000 // 1 second delay before prefetch
};

/**
 * Notification Settings
 */
export const NOTIFICATION_CONFIG = {
    DEFAULT_DURATION: 5000, // 5 seconds
    ERROR_DURATION: 0, // Requires manual dismiss
    SUCCESS_DURATION: 3000, // 3 seconds
    WARNING_DURATION: 7000, // 7 seconds
    MAX_NOTIFICATIONS: 10
};

/**
 * Theme Settings
 */
export const THEME_CONFIG = {
    LIGHT: 'light',
    DARK: 'dark',
    STORAGE_KEY: 'dashboard-theme',
    CLASS_ATTRIBUTE: 'data-theme'
};

/**
 * Local Storage Keys
 */
export const STORAGE_KEYS = {
    THEME: 'dashboard-theme',
    USER_PREFERENCES: 'dashboard-preferences',
    API_CACHE: 'dashboard-api-cache',
    CACHED_DATA: 'dashboard-cached-data'
};

/**
 * Performance Thresholds
 */
export const PERFORMANCE_THRESHOLDS = {
    PAGE_LOAD_TIME: 3000, // 3 seconds
    API_RESPONSE_TIME: 2000, // 2 seconds
    WEBSOCKET_PING_INTERVAL: 30000, // 30 seconds
    MEMORY_USAGE_WARNING: 100 * 1024 * 1024, // 100MB
    CPU_USAGE_WARNING: 80 // 80%
};

/**
 * Chart Configurations
 */
export const CHART_CONFIG = {
    DEFAULT_HEIGHT: 400,
    DEFAULT_WIDTH: 800,
    ANIMATION_DURATION: 300,
    AXIS_FONT_SIZE: 12,
    LEGEND_FONT_SIZE: 14,
    TOOLTIP_FONT_SIZE: 13,
    COLORS_COUNT: 10,
    GRID_LINE_COLOR: '#e5e7eb',
    TEXT_COLOR: '#6b7280'
};

/**
 * Pagination Settings
 */
export const PAGINATION_CONFIG = {
    DEFAULT_PAGE_SIZE: 10,
    PAGE_SIZE_OPTIONS: [10, 25, 50, 100],
    MAX_PAGE_SIZE: 1000,
    MAX_PAGES_TO_SHOW: 5
};

/**
 * Table Configuration
 */
export const TABLE_CONFIG = {
    DEFAULT_ROW_HEIGHT: 50,
    SORT_ICON_SIZE: 16,
    PAGINATION_HEIGHT: 60,
    ROWS_PER_PAGE_OPTIONS: [10, 25, 50, 100],
    STICKY_HEADER_HEIGHT: 60
};

/**
 * Modal/Dialog Settings
 */
export const MODAL_CONFIG = {
    DEFAULT_WIDTH: '600px',
    LARGE_WIDTH: '800px',
    SMALL_WIDTH: '400px',
    BACKDROP_COLOR: 'rgba(0, 0, 0, 0.5)',
    ANIMATION_DURATION: 300
};

/**
 * Loading States
 */
export const LOADING_STATES = {
    IDLE: 'idle',
    LOADING: 'loading',
    SUCCESS: 'success',
    ERROR: 'error',
    PARTIAL: 'partial'
};

/**
 * Animation Durations (ms)
 */
export const ANIMATION_DURATION = {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
    EXTRA_SLOW: 1000
};

/**
 * Breakpoints for Responsive Design
 */
export const BREAKPOINTS = {
    XS: 480,
    SM: 768,
    MD: 1024,
    LG: 1280,
    XL: 1536
};

/**
 * Z-Index Layers
 */
export const Z_INDEX = {
    DROPDOWN: 1000,
    STICKY: 1020,
    FIXED: 1030,
    MODAL_BACKDROP: 1040,
    MODAL: 1050,
    POPOVER: 1060,
    TOOLTIP: 1070,
    NOTIFICATION: 1080
};

/**
 * Animation Easing Functions
 */
export const EASING = {
    EASE_IN: 'cubic-bezier(0.4, 0, 1, 1)',
    EASE_OUT: 'cubic-bezier(0, 0, 0.2, 1)',
    EASE_IN_OUT: 'cubic-bezier(0.4, 0, 0.2, 1)',
    EASE_OUT_BACK: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
};

/**
 * Form Validation Rules
 */
export const VALIDATION_RULES = {
    REQUIRED: (value) => value !== null && value !== undefined && value !== '',
    EMAIL: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    MIN_LENGTH: (min) => (value) => value && value.length >= min,
    MAX_LENGTH: (max) => (value) => !value || value.length <= max,
    NUMERIC: (value) => !isNaN(value),
    POSITIVE: (value) => !isNaN(value) && parseFloat(value) > 0,
    STOCK_SYMBOL: (value) => /^\d{4}\.HK$/.test(value)
};

/**
 * Keyboard Shortcuts
 */
export const SHORTCUTS = {
    SEARCH: 'Ctrl+K',
    HELP: 'Ctrl+/',
    TOGGLE_THEME: 'Ctrl+T',
    REFRESH_DATA: 'Ctrl+R',
    EXPORT_DATA: 'Ctrl+E',
    SAVE: 'Ctrl+S'
};

// Export all constants
export default {
    API_ENDPOINTS,
    WS_ENDPOINTS,
    CHART_COLORS,
    AGENT_TYPES,
    AGENT_STATUS,
    ORDER_TYPES,
    ORDER_SIDES,
    ORDER_STATUS,
    STRATEGY_TYPES,
    RISK_LEVELS,
    RISK_THRESHOLDS,
    TIME_PERIODS,
    CACHE_CONFIG,
    NOTIFICATION_CONFIG,
    THEME_CONFIG,
    STORAGE_KEYS,
    PERFORMANCE_THRESHOLDS,
    CHART_CONFIG,
    PAGINATION_CONFIG,
    TABLE_CONFIG,
    MODAL_CONFIG,
    LOADING_STATES,
    ANIMATION_DURATION,
    BREAKPOINTS,
    Z_INDEX,
    EASING,
    VALIDATION_RULES,
    SHORTCUTS
};
