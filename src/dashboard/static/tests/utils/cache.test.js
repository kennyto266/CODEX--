/**
 * Cache Tests
 * Phase 7: Enhanced Architecture
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LRUCache, TTLCache, SmartCache, APICache } from '../js/utils/cache.js';

describe('LRUCache', () => {
    let cache;

    beforeEach(() => {
        cache = new LRUCache(3);
    });

    it('should set and get values', () => {
        cache.set('key1', 'value1');
        expect(cache.get('key1')).toBe('value1');
    });

    it('should track hits and misses', () => {
        cache.set('key1', 'value1');
        cache.get('key1'); // hit
        cache.get('key2'); // miss

        const stats = cache.getStats();
        expect(stats.hits).toBe(1);
        expect(stats.misses).toBe(1);
    });

    it('should evict least recently used item', () => {
        cache.set('key1', 'value1');
        cache.set('key2', 'value2');
        cache.set('key3', 'value3');
        cache.set('key4', 'value4'); // should evict key1

        expect(cache.get('key1')).toBeNull();
        expect(cache.get('key2')).toBe('value2');
        expect(cache.get('key3')).toBe('value3');
        expect(cache.get('key4')).toBe('value4');
    });

    it('should update existing key position', () => {
        cache.set('key1', 'value1');
        cache.set('key2', 'value2');
        cache.set('key1', 'updated');
        cache.set('key3', 'value3');
        cache.set('key4', 'value4'); // should evict key2, not key1

        expect(cache.get('key1')).toBe('updated');
        expect(cache.get('key2')).toBeNull();
        expect(cache.get('key3')).toBe('value3');
        expect(cache.get('key4')).toBe('value4');
    });
});

describe('TTLCache', () => {
    let cache;

    beforeEach(() => {
        cache = new TTLCache(1000); // 1 second TTL
    });

    it('should set and get values within TTL', () => {
        cache.set('key1', 'value1');
        expect(cache.get('key1')).toBe('value1');
    });

    it('should expire values after TTL', () => {
        cache.set('key1', 'value1');

        vi.useFakeTimers();
        vi.advanceTimersByTime(1000);

        expect(cache.get('key1')).toBeNull();

        vi.useRealTimers();
    });

    it('should respect custom TTL', () => {
        cache.set('key1', 'value1', 2000); // 2 seconds
        cache.set('key2', 'value2', 500); // 0.5 seconds

        vi.useFakeTimers();

        vi.advanceTimersByTime(750);

        expect(cache.get('key1')).toBe('value1');
        expect(cache.get('key2')).toBeNull();

        vi.useRealTimers();
    });

    it('should track statistics', () => {
        cache.set('key1', 'value1');
        cache.get('key1'); // hit

        const stats = cache.getStats();
        expect(stats.sets).toBe(1);
        expect(stats.hits).toBe(1);
    });
});

describe('SmartCache', () => {
    let cache;

    beforeEach(() => {
        cache = new SmartCache({ maxSize: 3, defaultTTL: 1000 });
    });

    it('should combine LRU and TTL', () => {
        cache.set('key1', 'value1', 1000);
        expect(cache.get('key1')).toBe('value1');

        vi.useFakeTimers();
        vi.advanceTimersByTime(1000);
        vi.useRealTimers();

        expect(cache.get('key1')).toBeNull();
    });

    it('should evict from both caches', () => {
        cache.set('key1', 'value1', 1000);
        cache.set('key2', 'value2', 1000);
        cache.set('key3', 'value3', 1000);
        cache.set('key4', 'value4', 1000); // should evict from LRU

        expect(cache.lruCache.has('key1')).toBe(false);
        expect(cache.ttlCache.has('key1')).toBe(false);
    });
});
