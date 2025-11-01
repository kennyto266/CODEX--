/**
 * Keyboard Shortcuts Manager
 * Phase 7: Enhanced Architecture
 */

import { SHORTCUTS } from './constants.js';

/**
 * Shortcut Manager Class
 */
class ShortcutManager {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
        this.listeners = new Set();
    }

    /**
     * Register a keyboard shortcut
     * @param {string} name - Shortcut name
     * @param {string} combination - Key combination (e.g., 'Ctrl+K', 'Ctrl+/')
     * @param {Function} callback - Function to execute
     * @param {Object} options - Options (description, preventDefault, etc.)
     */
    register(name, combination, callback, options = {}) {
        const shortcut = {
            name,
            combination: this.parseCombination(combination),
            callback,
            description: options.description || '',
            preventDefault: options.preventDefault !== false,
            global: options.global !== false, // Listen globally or only when focused
            enabled: options.enabled !== false
        };

        this.shortcuts.set(name, shortcut);
        console.log(`⌨️ Shortcut registered: ${name} (${combination})`);

        // Return unregister function
        return () => this.unregister(name);
    }

    /**
     * Unregister a keyboard shortcut
     */
    unregister(name) {
        const deleted = this.shortcuts.delete(name);
        if (deleted) {
            console.log(`⌨️ Shortcut unregistered: ${name}`);
        }
        return deleted;
    }

    /**
     * Parse key combination string
     */
    parseCombination(combination) {
        const parts = combination.toLowerCase().split('+');
        const combo = {
            ctrl: false,
            alt: false,
            shift: false,
            meta: false, // Cmd on Mac
            key: null
        };

        parts.forEach(part => {
            part = part.trim();
            if (part === 'ctrl' || part === 'control') combo.ctrl = true;
            else if (part === 'alt') combo.alt = true;
            else if (part === 'shift') combo.shift = true;
            else if (part === 'meta' || part === 'cmd' || part === 'command') combo.meta = true;
            else combo.key = part;
        });

        return combo;
    }

    /**
     * Check if event matches combination
     */
    matches(event, combination) {
        const combo = combination;

        // Check modifiers
        if (!!combo.ctrl !== (event.ctrlKey || event.metaKey)) return false;
        if (!!combo.alt !== event.altKey) return false;
        if (!!combo.shift !== event.shiftKey) return false;

        // Check key
        const eventKey = this.getEventKey(event);
        if (combo.key !== eventKey) return false;

        return true;
    }

    /**
     * Get normalized key from event
     */
    getEventKey(event) {
        // Handle special keys
        const keyMap = {
            ' ': 'space',
            'Escape': 'esc',
            'ArrowUp': 'up',
            'ArrowDown': 'down',
            'ArrowLeft': 'left',
            'ArrowRight': 'right',
            'Enter': 'enter',
            'Tab': 'tab'
        };

        return keyMap[event.key] || event.key.toLowerCase();
    }

    /**
     * Handle keydown event
     */
    handleKeydown(event) {
        if (!this.enabled) return;

        // Don't trigger shortcuts when typing in input fields
        const target = event.target;
        if (this.shouldSkipForTarget(target)) {
            return;
        }

        // Check each registered shortcut
        for (const [name, shortcut] of this.shortcuts) {
            if (!shortcut.enabled) continue;

            if (this.matches(event, shortcut.combination)) {
                if (shortcut.preventDefault) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                try {
                    shortcut.callback(event);
                } catch (error) {
                    console.error(`Error executing shortcut ${name}:`, error);
                }
            }
        }
    }

    /**
     * Check if we should skip shortcuts for this target
     */
    shouldSkipForTarget(target) {
        const tagName = target.tagName.toLowerCase();
        const inputTypes = ['input', 'textarea', 'select'];

        if (inputTypes.includes(tagName)) return true;
        if (target.isContentEditable) return true;

        // Skip if in a form element
        let parent = target.parentElement;
        while (parent) {
            if (parent.tagName.toLowerCase() === 'form') {
                return true;
            }
            parent = parent.parentElement;
        }

        return false;
    }

    /**
     * Enable shortcuts
     */
    enable() {
        this.enabled = true;
    }

    /**
     * Disable shortcuts
     */
    disable() {
        this.enabled = false;
    }

    /**
     * Toggle shortcuts enabled state
     */
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }

    /**
     * Get all registered shortcuts
     */
    getShortcuts() {
        return Array.from(this.shortcuts.values());
    }

    /**
     * Get shortcut by name
     */
    getShortcut(name) {
        return this.shortcuts.get(name);
    }

    /**
     * Check if shortcut exists
     */
    has(name) {
        return this.shortcuts.has(name);
    }

    /**
     * Enable specific shortcut
     */
    enableShortcut(name) {
        if (this.shortcuts.has(name)) {
            this.shortcuts.get(name).enabled = true;
        }
    }

    /**
     * Disable specific shortcut
     */
    disableShortcut(name) {
        if (this.shortcuts.has(name)) {
            this.shortcuts.get(name).enabled = false;
        }
    }

    /**
     * Generate help text for all shortcuts
     */
    getHelpText() {
        const shortcuts = this.getShortcuts();
        const grouped = {};

        shortcuts.forEach(shortcut => {
            if (!grouped[shortcut.category || 'General']) {
                grouped[shortcut.category || 'General'] = [];
            }
            grouped[shortcut.category || 'General'].push(shortcut);
        });

        let help = '⌨️ Keyboard Shortcuts:\n\n';

        for (const [category, items] of Object.entries(grouped)) {
            help += `${category}:\n`;
            items.forEach(shortcut => {
                help += `  ${shortcut.combination} - ${shortcut.description}\n`;
            });
            help += '\n';
        }

        return help;
    }
}

/**
 * Shortcuts Panel Component
 */
export const ShortcutsPanel = {
    name: 'ShortcutsPanel',
    data() {
        return {
            show: false,
            searchTerm: ''
        };
    },
    computed: {
        filteredShortcuts() {
            if (!this.searchTerm) {
                return shortcutManager.getShortcuts();
            }

            return shortcutManager.getShortcuts().filter(shortcut => {
                const term = this.searchTerm.toLowerCase();
                return (
                    shortcut.name.toLowerCase().includes(term) ||
                    shortcut.combination.key.toLowerCase().includes(term) ||
                    (shortcut.description || '').toLowerCase().includes(term)
                );
            });
        }
    },
    methods: {
        togglePanel() {
            this.show = !this.show;
        },
        closePanel() {
            this.show = false;
        },
        formatCombination(combo) {
            const parts = [];
            if (combo.ctrl) parts.push('Ctrl');
            if (combo.alt) parts.push('Alt');
            if (combo.shift) parts.push('Shift');
            if (combo.meta) parts.push('Cmd');
            parts.push(combo.key.toUpperCase());
            return parts.join('+');
        }
    },
    template: `
        <div class="shortcuts-panel" v-if="show">
            <div class="shortcuts-header">
                <h3>Keyboard Shortcuts</h3>
                <button @click="closePanel" class="close-button">&times;</button>
            </div>
            <div class="shortcuts-search">
                <input
                    v-model="searchTerm"
                    type="text"
                    placeholder="Search shortcuts..."
                    class="search-input"
                />
            </div>
            <div class="shortcuts-list">
                <div
                    v-for="shortcut in filteredShortcuts"
                    :key="shortcut.name"
                    class="shortcut-item"
                >
                    <div class="shortcut-combo">
                        {{ formatCombination(shortcut.combination) }}
                    </div>
                    <div class="shortcut-info">
                        <div class="shortcut-name">{{ shortcut.name }}</div>
                        <div class="shortcut-desc" v-if="shortcut.description">
                            {{ shortcut.description }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

/**
 * Vue Composition Hook for Shortcuts
 */
export const useShortcuts = () => {
    const shortcuts = ref([]);

    const registerShortcut = (name, combination, callback, options) => {
        return shortcutManager.register(name, combination, callback, options);
    };

    const unregisterShortcut = (name) => {
        return shortcutManager.unregister(name);
    };

    const getShortcuts = () => {
        shortcuts.value = shortcutManager.getShortcuts();
        return shortcuts.value;
    };

    onMounted(() => {
        getShortcuts();
    });

    return {
        shortcuts,
        registerShortcut,
        unregisterShortcut,
        getShortcuts
    };
};

/**
 * Shortcuts Styles
 */
const shortcutsStyles = `
<style>
.shortcuts-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    z-index: var(--z-modal);
    display: flex;
    flex-direction: column;
}

.shortcuts-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border-primary);
}

.shortcuts-header h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: 20px;
}

.close-button {
    background: none;
    border: none;
    font-size: 24px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: background 0.2s;
}

.close-button:hover {
    background: var(--bg-tertiary);
}

.shortcuts-search {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-primary);
}

.search-input {
    width: 100%;
    padding: 10px 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 14px;
}

.search-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.shortcuts-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
}

.shortcut-item {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    transition: background 0.2s;
}

.shortcut-item:hover {
    background: var(--bg-secondary);
}

.shortcut-combo {
    min-width: 120px;
    padding: 6px 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    font-family: monospace;
    font-size: 13px;
    color: var(--text-primary);
    text-align: center;
    font-weight: 600;
    margin-right: 16px;
}

.shortcut-info {
    flex: 1;
}

.shortcut-name {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
}

.shortcut-desc {
    font-size: 13px;
    color: var(--text-secondary);
}

@media (max-width: 767px) {
    .shortcuts-panel {
        width: 95%;
        max-height: 90vh;
    }

    .shortcut-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .shortcut-combo {
        margin-right: 0;
    }
}
</style>
`;

// Inject styles
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('div');
    styleElement.innerHTML = shortcutsStyles;
    document.head.appendChild(styleElement.firstElementChild);
}

// Create global shortcut manager instance
const shortcutManager = new ShortcutManager();

// Register global keyboard listener
if (typeof document !== 'undefined') {
    document.addEventListener('keydown', (event) => {
        shortcutManager.handleKeydown(event);
    });
}

// Export
export { shortcutManager };
export default shortcutManager;
