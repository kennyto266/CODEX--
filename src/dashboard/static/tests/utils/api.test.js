/**
 * API Client Tests
 * Phase 7: Enhanced Architecture
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { APIClient, apiClient } from '../js/utils/api.js';

describe('APIClient', () => {
    let client;

    beforeEach(() => {
        client = new APIClient({
            baseURL: 'http://localhost:8001',
            timeout: 5000,
            retryAttempts: 3
        });

        // Mock fetch
        global.fetch = vi.fn();
    });

    describe('Initialization', () => {
        it('should create client with default config', () => {
            const defaultClient = new APIClient();
            expect(defaultClient.baseURL).toBe(window.location.origin);
            expect(defaultClient.timeout).toBe(30000);
            expect(defaultClient.retryAttempts).toBe(3);
        });

        it('should create client with custom config', () => {
            expect(client.baseURL).toBe('http://localhost:8001');
            expect(client.timeout).toBe(5000);
            expect(client.retryAttempts).toBe(3);
        });
    });

    describe('Request Interceptors', () => {
        it('should add request interceptor', () => {
            const interceptor = vi.fn((url, config) => [url, config]);
            client.addRequestInterceptor(interceptor);

            expect(client.requestInterceptors).toContain(interceptor);
        });

        it('should apply request interceptors', async () => {
            const interceptor = vi.fn((url, config) => {
                config.headers = { ...config.headers, 'X-Custom': 'value' };
                return [url, config];
            });

            client.addRequestInterceptor(interceptor);

            global.fetch.mockResolvedValue({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ data: 'test' })
            });

            await client.get('/api/test');

            expect(interceptor).toHaveBeenCalled();
        });
    });

    describe('Response Interceptors', () => {
        it('should add response interceptor', () => {
            const interceptor = vi.fn((data) => data);
            client.addResponseInterceptor(interceptor);

            expect(client.responseInterceptors).toContain(interceptor);
        });

        it('should apply response interceptors', async () => {
            const interceptor = vi.fn((data) => ({ ...data, transformed: true }));

            client.addResponseInterceptor(interceptor);

            global.fetch.mockResolvedValue({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ data: 'test' })
            });

            const response = await client.get('/api/test');

            expect(interceptor).toHaveBeenCalled();
            expect(response.data.transformed).toBe(true);
        });
    });

    describe('HTTP Methods', () => {
        beforeEach(() => {
            global.fetch.mockResolvedValue({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ data: 'success' })
            });
        });

        it('should make GET request', async () => {
            const response = await client.get('/api/data');

            expect(fetch).toHaveBeenCalledWith('/api/data', {
                method: 'GET',
                headers: expect.any(Object),
                signal: expect.any(AbortSignal)
            });

            expect(response.ok).toBe(true);
            expect(response.data).toEqual({ data: 'success' });
        });

        it('should make POST request', async () => {
            const payload = { name: 'test' };

            await client.post('/api/data', payload);

            expect(fetch).toHaveBeenCalledWith('/api/data', {
                method: 'POST',
                headers: expect.any(Object),
                body: JSON.stringify(payload),
                signal: expect.any(AbortSignal)
            });
        });

        it('should make PUT request', async () => {
            const payload = { name: 'updated' };

            await client.put('/api/data/1', payload);

            expect(fetch).toHaveBeenCalledWith('/api/data/1', {
                method: 'PUT',
                headers: expect.any(Object),
                body: JSON.stringify(payload),
                signal: expect.any(AbortSignal)
            });
        });

        it('should make DELETE request', async () => {
            await client.delete('/api/data/1');

            expect(fetch).toHaveBeenCalledWith('/api/data/1', {
                method: 'DELETE',
                headers: expect.any(Object),
                signal: expect.any(AbortSignal)
            });
        });
    });

    describe('Error Handling', () => {
        it('should throw error for HTTP error status', async () => {
            global.fetch.mockResolvedValue({
                ok: false,
                status: 404,
                statusText: 'Not Found',
                json: () => Promise.resolve({ message: 'Not found' })
            });

            await expect(client.get('/api/notfound')).rejects.toThrow('Not Found');
        });

        it('should throw error for timeout', async () => {
            const controller = new AbortController();
            global.fetch.mockImplementation(() => {
                controller.abort();
                return Promise.reject(new Error('Timeout'));
            });

            // Mock setTimeout to avoid actual delay
            vi.useFakeTimers();

            const promise = client.get('/api/slow');

            vi.advanceTimersByTime(5000);

            await expect(promise).rejects.toThrow('Request timeout');

            vi.useRealTimers();
        });

        it('should retry on network failure', async () => {
            let callCount = 0;
            global.fetch.mockImplementation(() => {
                callCount++;
                if (callCount < 3) {
                    return Promise.reject(new Error('Network error'));
                }
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({ data: 'success' })
                });
            });

            const response = await client.get('/api/test');

            expect(callCount).toBe(3);
            expect(response.data).toEqual({ data: 'success' });
        });

        it('should not retry on client error (4xx)', async () => {
            global.fetch.mockRejectedValue({
                name: 'HTTPError',
                status: 400,
                message: 'Bad Request'
            });

            await expect(client.get('/api/bad')).rejects.toThrow();
            expect(fetch).toHaveBeenCalledTimes(1);
        });
    });
});

describe('API Error Classes', () => {
    it('should create APIError', () => {
        const error = new APIError('Test error', 'TEST_ERROR', { details: 'value' });

        expect(error.name).toBe('APIError');
        expect(error.message).toBe('Test error');
        expect(error.code).toBe('TEST_ERROR');
        expect(error.details).toEqual({ details: 'value' });
    });

    it('should create HTTPError', () => {
        const error = new HTTPError(404, 'Not Found', { url: '/api/test' });

        expect(error.name).toBe('HTTPError');
        expect(error.status).toBe(404);
        expect(error.message).toBe('Not Found');
        expect(error.details).toEqual({ url: '/api/test' });
    });
});
