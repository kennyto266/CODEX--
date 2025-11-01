/**
 * Theme Management System (Light/Dark Mode)
 * Phase 7: Enhanced Architecture
 */

import { THEME_CONFIG, STORAGE_KEYS } from './constants.js';

/**
 * Theme Manager Class
 */
class ThemeManager {
    constructor() {
        this.currentTheme = THEME_CONFIG.LIGHT;
        this.storageKey = STORAGE_KEYS.THEME;
        this.listeners = new Set();
        this.autoDetect = true;

        this.init();
    }

    /**
     * Initialize theme manager
     */
    init() {
        // Load saved theme or detect system preference
        const savedTheme = this.getSavedTheme();
        const systemTheme = this.getSystemTheme();

        this.currentTheme = savedTheme || systemTheme;

        // Apply theme to document
        this.applyTheme(this.currentTheme);

        // Listen for system theme changes
        if (this.autoDetect) {
            this.setupSystemThemeListener();
        }

        console.log(`🎨 Theme initialized: ${this.currentTheme}`);
    }

    /**
     * Get saved theme from localStorage
     */
    getSavedTheme() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved && (saved === THEME_CONFIG.LIGHT || saved === THEME_CONFIG.DARK)) {
                return saved;
            }
        } catch (error) {
            console.warn('Failed to read saved theme:', error);
        }
        return null;
    }

    /**
     * Get system theme preference
     */
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_CONFIG.DARK;
        }
        return THEME_CONFIG.LIGHT;
    }

    /**
     * Setup system theme change listener
     */
    setupSystemThemeListener() {
        if (!window.matchMedia) {
            return;
        }

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            const newTheme = e.matches ? THEME_CONFIG.DARK : THEME_CONFIG.LIGHT;

            // Only auto-switch if user hasn't manually set a theme
            const savedTheme = this.getSavedTheme();
            if (!savedTheme) {
                this.setTheme(newTheme, false);
            }
        });
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        if (!document.documentElement) {
            return;
        }

        document.documentElement.setAttribute(THEME_CONFIG.CLASS_ATTRIBUTE, theme);
        this.currentTheme = theme;

        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);

        // Notify listeners
        this.notifyListeners(theme);
    }

    /**
     * Update meta theme-color
     */
    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');

        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }

        metaThemeColor.content = theme === THEME_CONFIG.DARK ? '#1f2937' : '#ffffff';
    }

    /**
     * Toggle theme
     */
    toggleTheme() {
        const newTheme = this.currentTheme === THEME_CONFIG.LIGHT
            ? THEME_CONFIG.DARK
            : THEME_CONFIG.LIGHT;

        this.setTheme(newTheme);
    }

    /**
     * Set theme
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} save - Whether to save to localStorage
     */
    setTheme(theme, save = true) {
        if (theme !== THEME_CONFIG.LIGHT && theme !== THEME_CONFIG.DARK) {
            console.warn(`Invalid theme: ${theme}`);
            return;
        }

        this.applyTheme(theme);

        if (save) {
            this.saveTheme(theme);
        }
    }

    /**
     * Save theme to localStorage
     */
    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (error) {
            console.warn('Failed to save theme:', error);
        }
    }

    /**
     * Listen for theme changes
     */
    onChange(callback) {
        this.listeners.add(callback);

        // Return unsubscribe function
        return () => {
            this.listeners.delete(callback);
        };
    }

    /**
     * Notify all listeners
     */
    notifyListeners(theme) {
        this.listeners.forEach(callback => {
            try {
                callback(theme);
            } catch (error) {
                console.error('Error in theme listener:', error);
            }
        });
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Check if dark theme is active
     */
    isDark() {
        return this.currentTheme === THEME_CONFIG.DARK;
    }

    /**
     * Check if light theme is active
     */
    isLight() {
        return this.currentTheme === THEME_CONFIG.LIGHT;
    }

    /**
     * Get theme-aware CSS class
     */
    getThemeClass(lightClass, darkClass) {
        return this.isDark() ? darkClass : lightClass;
    }

    /**
     * Get theme-aware color value
     */
    getThemeColor(lightColor, darkColor) {
        return this.isDark() ? darkColor : lightColor;
    }

    /**
     * Generate CSS custom properties for theme
     */
    generateCSSVariables(theme) {
        const isDark = theme === THEME_CONFIG.DARK;

        return `
            :root[data-theme="${theme}"] {
                /* Background Colors */
                --bg-primary: ${isDark ? '#1f2937' : '#ffffff'};
                --bg-secondary: ${isDark ? '#374151' : '#f9fafb'};
                --bg-tertiary: ${isDark ? '#4b5563' : '#f3f4f6'};

                /* Text Colors */
                --text-primary: ${isDark ? '#f9fafb' : '#111827'};
                --text-secondary: ${isDark ? '#d1d5db' : '#6b7280'};
                --text-tertiary: ${isDark ? '#9ca3af' : '#9ca3af'};

                /* Border Colors */
                --border-primary: ${isDark ? '#374151' : '#e5e7eb'};
                --border-secondary: ${isDark ? '#4b5563' : '#d1d5db'};

                /* Accent Colors */
                --accent-primary: ${isDark ? '#60a5fa' : '#3b82f6'};
                --accent-secondary: ${isDark ? '#818cf8' : '#6366f1'};
                --accent-success: ${isDark ? '#34d399' : '#10b981'};
                --accent-warning: ${isDark ? '#fbbf24' : '#f59e0b'};
                --accent-error: ${isDark ? '#f87171' : '#ef4444'};

                /* Shadow */
                --shadow-sm: ${isDark ? '0 1px 2px 0 rgba(0, 0, 0, 0.3)' : '0 1px 2px 0 rgba(0, 0, 0, 0.05)'};
                --shadow-md: ${isDark ? '0 4px 6px -1px rgba(0, 0, 0, 0.3)' : '0 4px 6px -1px rgba(0, 0, 0, 0.1)'};
                --shadow-lg: ${isDark ? '0 10px 15px -3px rgba(0, 0, 0, 0.3)' : '0 10px 15px -3px rgba(0, 0, 0, 0.1)'};

                /* Code */
                --code-bg: ${isDark ? '#2d3748' : '#f7fafc'};
                --code-text: ${isDark ? '#e2e8f0' : '#2d3748'};
            }
        `;
    }

    /**
     * Inject theme CSS variables
     */
    injectThemeVariables() {
        const styleId = 'theme-variables';
        let styleElement = document.getElementById(styleId);

        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = styleId;
            document.head.appendChild(styleElement);
        }

        const lightCSS = this.generateCSSVariables(THEME_CONFIG.LIGHT);
        const darkCSS = this.generateCSSVariables(THEME_CONFIG.DARK);

        styleElement.textContent = lightCSS + '\n' + darkCSS;
    }
}

/**
 * Theme Toggle Button Component
 */
export const ThemeToggle = {
    name: 'ThemeToggle',
    props: {
        size: {
            type: String,
            default: 'medium', // small, medium, large
            validator: (value) => ['small', 'medium', 'large'].includes(value)
        },
        showLabel: {
            type: Boolean,
            default: true
        },
        position: {
            type: String,
            default: 'right' // left, center, right
        }
    },
    data() {
        return {
            currentTheme: themeManager.getCurrentTheme()
        };
    },
    computed: {
        buttonClass() {
            return `theme-toggle theme-toggle-${this.size} theme-toggle-${this.position}`;
        },
        icon() {
            return this.currentTheme === THEME_CONFIG.DARK ? '☀️' : '🌙';
        },
        label() {
            return this.currentTheme === THEME_CONFIG.DARK ? 'Light Mode' : 'Dark Mode';
        }
    },
    mounted() {
        // Subscribe to theme changes
        this.unsubscribe = themeManager.onChange((theme) => {
            this.currentTheme = theme;
        });
    },
    unmounted() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    },
    methods: {
        toggle() {
            themeManager.toggleTheme();
        }
    },
    template: `
        <button :class="buttonClass" @click="toggle" :title="label">
            <span class="theme-icon">{{ icon }}</span>
            <span v-if="showLabel" class="theme-label">{{ label }}</span>
        </button>
    `
};

/**
 * Apply theme styles
 */
const themeStyles = `
<style>
.theme-toggle {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.theme-toggle:hover {
    background: var(--bg-tertiary);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.theme-toggle:active {
    transform: translateY(0);
}

.theme-icon {
    font-size: 18px;
    line-height: 1;
}

.theme-toggle-small {
    padding: 6px 12px;
}

.theme-toggle-small .theme-icon {
    font-size: 16px;
}

.theme-toggle-small .theme-label {
    font-size: 12px;
}

.theme-toggle-large {
    padding: 12px 24px;
}

.theme-toggle-large .theme-icon {
    font-size: 24px;
}

.theme-toggle-large .theme-label {
    font-size: 16px;
}

.theme-toggle-left {
    justify-content: flex-start;
}

.theme-toggle-center {
    justify-content: center;
}

.theme-toggle-right {
    justify-content: flex-end;
}
</style>
`;

// Inject styles
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('div');
    styleElement.innerHTML = themeStyles;
    document.head.appendChild(styleElement.firstElementChild);
}

// Create global theme manager instance
const themeManager = new ThemeManager();
themeManager.injectThemeVariables();

/**
 * Mixin for Vue components to access theme
 */
export const themeMixin = {
    data() {
        return {
            theme: themeManager.getCurrentTheme()
        };
    },
    computed: {
        isDark() {
            return themeManager.isDark();
        },
        isLight() {
            return themeManager.isLight();
        }
    },
    methods: {
        getThemeClass(lightClass, darkClass) {
            return themeManager.getThemeClass(lightClass, darkClass);
        },
        getThemeColor(lightColor, darkColor) {
            return themeManager.getThemeColor(lightColor, darkColor);
        }
    },
    mounted() {
        // Subscribe to theme changes
        this.unsubscribeTheme = themeManager.onChange((theme) => {
            this.theme = theme;
        });
    },
    unmounted() {
        if (this.unsubscribeTheme) {
            this.unsubscribeTheme();
        }
    }
};

// Export
export { themeManager };
export default themeManager;
