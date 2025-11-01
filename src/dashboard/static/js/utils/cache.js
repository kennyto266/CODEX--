/**
 * Intelligent Caching System with LRU, TTL, and Prefetch
 * Phase 7: Enhanced Architecture
 */

/**
 * LRU Cache Implementation
 */
class LRUCache {
    constructor(maxSize = 100) {
        this.maxSize = maxSize;
        this.cache = new Map();
        this.stats = {
            hits: 0,
            misses: 0,
            evictions: 0
        };
    }

    /**
     * Get value from cache
     */
    get(key) {
        if (!this.cache.has(key)) {
            this.stats.misses++;
            return null;
        }

        // Move to end (most recently used)
        const value = this.cache.get(key);
        this.cache.delete(key);
        this.cache.set(key, value);

        this.stats.hits++;
        return value;
    }

    /**
     * Set value in cache
     */
    set(key, value) {
        // If key exists, remove it first (to re-insert at end)
        if (this.cache.has(key)) {
            this.cache.delete(key);
        }
        // If at max capacity, remove least recently used
        else if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
            this.stats.evictions++;
        }

        this.cache.set(key, value);
    }

    /**
     * Check if key exists
     */
    has(key) {
        return this.cache.has(key);
    }

    /**
     * Delete key from cache
     */
    delete(key) {
        return this.cache.delete(key);
    }

    /**
     * Clear cache
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache size
     */
    size() {
        return this.cache.size;
    }

    /**
     * Get statistics
     */
    getStats() {
        const total = this.stats.hits + this.stats.misses;
        const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(2) : 0;
        return {
            ...this.stats,
            hitRate: `${hitRate}%`,
            size: this.size(),
            maxSize: this.maxSize
        };
    }
}

/**
 * Cache with TTL (Time To Live)
 */
class TTLCache {
    constructor(defaultTTL = 300000) { // 5 minutes default
        this.cache = new Map();
        this.defaultTTL = defaultTTL;
        this.stats = {
            sets: 0,
            hits: 0,
            misses: 0,
            expired: 0
        };
    }

    /**
     * Set value with TTL
     */
    set(key, value, ttl = this.defaultTTL) {
        const expirationTime = Date.now() + ttl;
        this.cache.set(key, {
            value,
            expirationTime
        });
        this.stats.sets++;
    }

    /**
     * Get value if not expired
     */
    get(key) {
        const entry = this.cache.get(key);

        if (!entry) {
            this.stats.misses++;
            return null;
        }

        // Check if expired
        if (Date.now() > entry.expirationTime) {
            this.cache.delete(key);
            this.stats.expired++;
            this.stats.misses++;
            return null;
        }

        this.stats.hits++;
        return entry.value;
    }

    /**
     * Check if key exists and not expired
     */
    has(key) {
        const entry = this.cache.get(key);
        if (!entry) return false;

        if (Date.now() > entry.expirationTime) {
            this.cache.delete(key);
            return false;
        }

        return true;
    }

    /**
     * Delete key
     */
    delete(key) {
        return this.cache.delete(key);
    }

    /**
     * Clear expired entries
     */
    cleanExpired() {
        const now = Date.now();
        let expiredCount = 0;

        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expirationTime) {
                this.cache.delete(key);
                expiredCount++;
            }
        }

        return expiredCount;
    }

    /**
     * Get statistics
     */
    getStats() {
        const total = this.stats.hits + this.stats.misses;
        const hitRate = total > 0 ? (this.stats.hits / total * 100).toFixed(2) : 0;
        return {
            ...this.stats,
            hitRate: `${hitRate}%`,
            size: this.cache.size,
            expiredCount: this.stats.expired
        };
    }
}

/**
 * Smart Cache Manager
 * Combines LRU + TTL + Prefetch
 */
class SmartCache {
    constructor(config = {}) {
        this.lruCache = new LRUCache(config.maxSize || 100);
        this.ttlCache = new TTLCache(config.defaultTTL || 300000);
        this.prefetchQueue = new Set();
        this.config = {
            ...config,
            enablePrefetch: config.enablePrefetch !== false
        };
    }

    /**
     * Get cached data with LRU + TTL check
     */
    get(key) {
        // Try LRU cache first
        const lruValue = this.lruCache.get(key);
        if (lruValue !== null) {
            // Also check TTL
            const ttlValue = this.ttlCache.get(key);
            if (ttlValue !== null) {
                return ttlValue;
            }
            // TTL expired, remove from LRU too
            this.lruCache.delete(key);
        }

        return null;
    }

    /**
     * Set cached data with both LRU and TTL
     */
    set(key, value, ttl) {
        this.lruCache.set(key, value);
        this.ttlCache.set(key, value, ttl);
    }

    /**
     * Prefetch data for anticipated use
     */
    async prefetch(key, fetcher, ttl = 300000) {
        if (this.has(key) || this.prefetchQueue.has(key)) {
            return; // Already cached or fetching
        }

        this.prefetchQueue.add(key);

        try {
            const data = await fetcher();
            this.set(key, data, ttl);
            console.log(`✅ Prefetched: ${key}`);
        } catch (error) {
            console.error(`❌ Prefetch failed: ${key}`, error);
        } finally {
            this.prefetchQueue.delete(key);
        }
    }

    /**
     * Check if key exists in either cache
     */
    has(key) {
        return this.lruCache.has(key) && this.ttlCache.has(key);
    }

    /**
     * Delete from both caches
     */
    delete(key) {
        this.lruCache.delete(key);
        this.ttlCache.delete(key);
    }

    /**
     * Clear all caches
     */
    clear() {
        this.lruCache.clear();
        this.ttlCache.cache.clear();
        this.prefetchQueue.clear();
    }

    /**
     * Get combined statistics
     */
    getStats() {
        return {
            lru: this.lruCache.getStats(),
            ttl: this.ttlCache.getStats(),
            prefetchQueue: this.prefetchQueue.size
        };
    }

    /**
     * Generate cache key from URL and params
     */
    static generateKey(url, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}:${params[key]}`)
            .join('|');
        return `${url}?${sortedParams}`;
    }
}

/**
 * APICache wrapper with smart caching
 */
class APICache {
    constructor() {
        this.cache = new SmartCache({
            maxSize: 200,
            defaultTTL: 300000, // 5 minutes
            enablePrefetch: true
        });
    }

    /**
     * Fetch with automatic caching
     */
    async fetchWithCache(url, params = {}, ttl = 300000) {
        const cacheKey = SmartCache.generateKey(url, params);

        // Try cache first
        let data = this.cache.get(cacheKey);
        if (data !== null) {
            console.log(`📦 Cache hit: ${cacheKey}`);
            return data;
        }

        // Fetch from API
        console.log(`🌐 Fetching: ${cacheKey}`);
        try {
            const response = await apiClient.get(url, { params });
            data = response.data;

            // Cache the result
            this.cache.set(cacheKey, data, ttl);

            return data;
        } catch (error) {
            console.error(`❌ API fetch failed: ${cacheKey}`, error);
            throw error;
        }
    }

    /**
     * Clear specific cache entry
     */
    delete(url, params = {}) {
        const cacheKey = SmartCache.generateKey(url, params);
        this.cache.delete(cacheKey);
    }

    /**
     * Clear all cache
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     */
    getStats() {
        return this.cache.getStats();
    }
}

/**
 * Global cache instance
 */
const apiCache = new APICache();

/**
 * Debounce utility for preventing cache spam
 */
function debounce(fn, delay = 1000) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
}

// Export
export { LRUCache, TTLCache, SmartCache, APICache, apiCache, debounce };
