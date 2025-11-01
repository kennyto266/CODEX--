# CODEX Dashboard Developer Guide

**Version**: 1.0.0
**Updated**: 2025-10-27

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Core Utilities](#core-utilities)
5. [Store Management](#store-management)
6. [Components](#components)
7. [Testing](#testing)
8. [Best Practices](#best-practices)

---

## Project Overview

The CODEX Dashboard is a Vue 3-based frontend for a quantitative trading system. It features real-time data updates, agent management, and comprehensive analytics.

### Tech Stack

- **Framework**: Vue 3 (Composition API)
- **State Management**: Pinia
- **Routing**: Vue Router
- **Build Tool**: Vite
- **Testing**: Vitest
- **Language**: JavaScript (ES6+)

---

## Architecture

### Directory Structure

```
src/dashboard/static/js/
├── components/          # Vue components
├── stores/              # Pinia stores
├── utils/               # Utility libraries
│   ├── api.js           # HTTP client
│   ├── cache.js         # Caching system
│   ├── errorHandler.js  # Error management
│   ├── formatters.js    # Data formatters
│   ├── constants.js     # Constants
│   ├── websocket.js     # WebSocket manager
│   ├── theme.js         # Theme system
│   ├── responsive.js    # Responsive utilities
│   ├── shortcuts.js     # Keyboard shortcuts
│   └── performance.js   # Performance monitoring
├── router.js            # Vue Router configuration
└── main.js              # Application entry point
```

---

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

---

## Core Utilities

### API Client

```javascript
import { apiClient } from './utils/api.js';

// GET request
const data = await apiClient.get('/api/agents');

// POST request
const response = await apiClient.post('/api/agents/start', { agentId: '123' });
```

### Caching

```javascript
import { apiCache } from './utils/cache.js';

// Automatic caching
const data = await apiCache.fetchWithCache('/api/agents', {}, 60000);
```

### Error Handling

```javascript
import { errorHandler, notifications } from './utils/errorHandler.js';

try {
    await riskyOperation();
} catch (error) {
    errorHandler.handle(error, { context: 'myOperation' });
    notifications.show('Error occurred', { type: 'error' });
}
```

### Theme

```javascript
import { themeManager } from './utils/theme.js';

// Toggle theme
themeManager.toggleTheme();

// Listen to changes
themeManager.onChange((theme) => {
    console.log('Theme changed:', theme);
});
```

### WebSocket

```javascript
import { wsManager } from './utils/websocket.js';

// Connect and subscribe
await wsManager.connect();
const unsubscribe = wsManager.subscribe('agents', (data) => {
    console.log('Update:', data);
});
```

### Shortcuts

```javascript
import { shortcutManager } from './utils/shortcuts.js';

// Register shortcut
shortcutManager.register('search', 'Ctrl+K', () => {
    // Open search
}, { description: 'Open search dialog' });
```

---

## Store Example

```javascript
import { defineStore } from 'pinia';
import { apiClient } from '../utils/api.js';

export const useMyStore = defineStore('myStore', () => {
    const items = ref([]);
    const loading = ref(false);

    async function fetchItems() {
        loading.value = true;
        try {
            const response = await apiClient.get('/api/items');
            items.value = response.data;
        } finally {
            loading.value = false;
        }
    }

    return { items, loading, fetchItems };
});
```

---

## Testing

```javascript
import { describe, it, expect } from 'vitest';
import { apiClient } from '../js/utils/api.js';

describe('API Client', () => {
    it('should make GET request', async () => {
        // Test implementation
    });
});
```

---

## Best Practices

1. Use Composition API (<script setup>)
2. Implement proper error handling
3. Cache API responses when appropriate
4. Use responsive design patterns
5. Follow accessibility guidelines
6. Write comprehensive tests
7. Keep components focused and small
8. Use TypeScript for type safety (optional)

---

## Troubleshooting

### Module not found
- Check import paths and extensions

### Store not updating
- Ensure reactive state and proper actions

### WebSocket not connecting
- Check URL and CORS settings

### Theme not applying
- Verify CSS variables and data-theme attribute

---

**For more details, refer to inline code comments and test files.**
