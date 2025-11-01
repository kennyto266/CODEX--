/**
 * HTTP API Client with Interceptors, Retry, and Timeout
 * Phase 7: Enhanced Architecture
 */

class APIClient {
    constructor(config = {}) {
        this.baseURL = config.baseURL || 'http://localhost:8001';
        this.timeout = config.timeout || 30000;
        this.retryAttempts = config.retryAttempts || 3;
        this.retryDelay = config.retryDelay || 1000;

        this.requestInterceptors = [];
        this.responseInterceptors = [];

        // Add default request interceptor for auth headers
        this.addRequestInterceptor((url, config) => {
            config.headers = {
                ...config.headers,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };
            return [url, config];
        });
    }

    /**
     * Add request interceptor
     * @param {Function} interceptor - Function(url, config) => [url, config]
     */
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    /**
     * Add response interceptor
     * @param {Function} interceptor - Function(response) => response
     */
    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    /**
     * Process request through interceptors
     */
    _applyRequestInterceptors(url, config) {
        let currentUrl = url;
        let currentConfig = { ...config };

        for (const interceptor of this.requestInterceptors) {
            try {
                const [newUrl, newConfig] = interceptor(currentUrl, currentConfig);
                currentUrl = newUrl;
                currentConfig = newConfig;
            } catch (error) {
                console.error('Request interceptor error:', error);
            }
        }

        return [currentUrl, currentConfig];
    }

    /**
     * Process response through interceptors
     */
    _applyResponseInterceptors(response) {
        let processedResponse = response;

        for (const interceptor of this.responseInterceptors) {
            try {
                processedResponse = interceptor(processedResponse);
            } catch (error) {
                console.error('Response interceptor error:', error);
            }
        }

        return processedResponse;
    }

    /**
     * Execute request with retry logic
     */
    async _request(url, config = {}, attempt = 1) {
        const [processedUrl, processedConfig] = this._applyRequestInterceptors(url, config);

        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(processedUrl, {
                ...processedConfig,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Handle HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new HTTPError(response.status, errorData.message || response.statusText, errorData);
            }

            const data = await response.json();
            const processedData = this._applyResponseInterceptors(data);

            return {
                ok: true,
                status: response.status,
                data: processedData,
                headers: response.headers
            };
        } catch (error) {
            clearTimeout(timeoutId);

            // Handle timeout errors
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 'TIMEOUT', { url });
            }

            // Retry on network errors
            if (attempt < this.retryAttempts && this._shouldRetry(error)) {
                console.log(`Retrying request (attempt ${attempt + 1}/${this.retryAttempts})`);
                await this._delay(this.retryDelay * attempt);
                return this._request(url, config, attempt + 1);
            }

            throw error;
        }
    }

    /**
     * Determine if error should trigger retry
     */
    _shouldRetry(error) {
        if (error instanceof HTTPError) {
            // Retry on server errors (5xx)
            return error.status >= 500;
        }
        // Retry on network errors
        return true;
    }

    /**
     * Delay utility
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * GET request
     */
    async get(url, config = {}) {
        return this._request(url, {
            ...config,
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(url, data = {}, config = {}) {
        return this._request(url, {
            ...config,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(url, data = {}, config = {}) {
        return this._request(url, {
            ...config,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(url, config = {}) {
        return this._request(url, {
            ...config,
            method: 'DELETE'
        });
    }

    /**
     * PATCH request
     */
    async patch(url, data = {}, config = {}) {
        return this._request(url, {
            ...config,
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }
}

/**
 * Custom Error Classes
 */
class APIError extends Error {
    constructor(message, code, details = {}) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.details = details;
    }
}

class HTTPError extends Error {
    constructor(status, message, details = {}) {
        super(message);
        this.name = 'HTTPError';
        this.status = status;
        this.details = details;
    }
}

/**
 * Request Deduplication Map
 */
const pendingRequests = new Map();

/**
 * Fetch with deduplication
 */
async function fetchWithDeduplication(key, requestFn) {
    // Check if request is already in flight
    if (pendingRequests.has(key)) {
        return pendingRequests.get(key);
    }

    // Execute request
    const promise = requestFn()
        .finally(() => {
            pendingRequests.delete(key);
        });

    pendingRequests.set(key, promise);
    return promise;
}

/**
 * Global instance
 */
const apiClient = new APIClient({
    baseURL: window.location.origin,
    timeout: 30000,
    retryAttempts: 3
});

// Add default response interceptor for error handling
apiClient.addResponseInterceptor((data) => {
    // Log successful responses in development
    if (window.location.hostname === 'localhost') {
        console.log('✅ API Response:', data);
    }
    return data;
});

// Export
export { apiClient, APIClient, APIError, HTTPError, fetchWithDeduplication };
