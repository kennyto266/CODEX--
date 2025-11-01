/**
 * WebSocket Manager for Real-Time Data Updates
 * Phase 7: Enhanced Architecture
 */

import { apiClient } from './api.js';
import { errorHandler } from './errorHandler.js';
import { notifications } from './errorHandler.js';
import { WS_ENDPOINTS } from './constants.js';

/**
 * WebSocket Connection Manager
 */
class WebSocketManager {
    constructor(config = {}) {
        this.url = config.url || 'ws://localhost:8001';
        this.endpoints = config.endpoints || WS_ENDPOINTS;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
        this.reconnectInterval = config.reconnectInterval || 1000;
        this.pingInterval = config.pingInterval || 30000;
        this.pingTimeout = config.pingTimeout || 5000;

        this.subscribers = new Map();
        this.messageQueue = [];
        this.isConnecting = false;
        this.isReconnecting = false;
        this.shouldReconnect = true;
        this.pingTimer = null;
        this.reconnectTimer = null;

        this.listeners = {
            open: [],
            close: [],
            error: [],
            message: [],
            reconnect: []
        };
    }

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
        return () => {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        };
    }

    /**
     * Emit event
     */
    _emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Connect to WebSocket
     */
    async connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        if (this.isConnecting) {
            return;
        }

        this.isConnecting = true;
        this.isReconnecting = false;

        try {
            console.log(`🔌 Connecting to WebSocket: ${this.url}`);

            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.shouldReconnect = true;

                this._emit('open');

                // Start ping interval
                this._startPing();

                // Process queued messages
                this._processMessageQueue();

                // Re-subscribe to all channels
                this._resubscribeAll();
            };

            this.ws.onmessage = (event) => {
                this._handleMessage(event);
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this._emit('error', error);
            };

            this.ws.onclose = (event) => {
                console.log('🔌 WebSocket closed:', event.code, event.reason);
                this.isConnecting = false;

                this._emit('close', event);

                // Stop ping timer
                this._stopPing();

                // Attempt reconnection if needed
                if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this._scheduleReconnect();
                }
            };

        } catch (error) {
            this.isConnecting = false;
            errorHandler.handle(error, { context: 'WebSocket.connect' });
            throw error;
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.shouldReconnect = false;
        this._clearReconnectTimer();
        this._stopPing();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // Clear all subscribers
        this.subscribers.clear();
        this.messageQueue = [];
    }

    /**
     * Subscribe to channel
     */
    subscribe(channel, callback) {
        if (!this.subscribers.has(channel)) {
            this.subscribers.set(channel, new Set());
        }

        this.subscribers.get(channel).add(callback);

        // Send subscribe message if connected
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this._send({
                type: 'subscribe',
                channel: channel
            });
        }

        // Return unsubscribe function
        return () => {
            this.unsubscribe(channel, callback);
        };
    }

    /**
     * Unsubscribe from channel
     */
    unsubscribe(channel, callback) {
        if (!this.subscribers.has(channel)) {
            return;
        }

        this.subscribers.get(channel).delete(callback);

        // Remove channel if no more subscribers
        if (this.subscribers.get(channel).size === 0) {
            this.subscribers.delete(channel);

            // Send unsubscribe message if connected
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this._send({
                    type: 'unsubscribe',
                    channel: channel
                });
            }
        }
    }

    /**
     * Handle incoming message
     */
    _handleMessage(event) {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            console.error('Invalid WebSocket message format:', error);
            return;
        }

        // Add to processing queue for high-volume handling
        this.messageQueue.push(data);

        if (this.messageQueue.length > 100) {
            console.warn('WebSocket message queue is getting large');
        }

        // Process messages in batch
        this._processMessageQueue();
    }

    /**
     * Process message queue in batch
     */
    _processMessageQueue() {
        if (this.messageQueue.length === 0) {
            return;
        }

        const batch = this.messageQueue.splice(0, 50);

        // Process each message
        batch.forEach(message => {
            const { type, channel, payload } = message;

            if (type === 'pong') {
                // Handle ping/pong
                return;
            }

            // Notify subscribers
            if (channel && this.subscribers.has(channel)) {
                this.subscribers.get(channel).forEach(callback => {
                    try {
                        callback(payload, message);
                    } catch (error) {
                        console.error(`Error in channel ${channel}:`, error);
                    }
                });
            }

            // Emit general message event
            this._emit('message', message);
        });
    }

    /**
     * Send message
     */
    _send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, message queued');
        }
    }

    /**
     * Send ping
     */
    _ping() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        try {
            this._send({ type: 'ping', timestamp: Date.now() });

            // Wait for pong
            setTimeout(() => {
                console.warn('Ping timeout');
                this._scheduleReconnect();
            }, this.pingTimeout);

        } catch (error) {
            console.error('Ping error:', error);
        }
    }

    /**
     * Start ping interval
     */
    _startPing() {
        this._stopPing();
        this.pingTimer = setInterval(() => {
            this._ping();
        }, this.pingInterval);
    }

    /**
     * Stop ping interval
     */
    _stopPing() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    /**
     * Schedule reconnection
     */
    _scheduleReconnect() {
        if (this.isReconnecting) {
            return;
        }

        this.isReconnecting = true;
        this.reconnectAttempts++;

        const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        this._emit('reconnect', { attempt: this.reconnectAttempts, delay });

        this.reconnectTimer = setTimeout(async () => {
            this.isReconnecting = false;
            await this.connect();
        }, delay);
    }

    /**
     * Clear reconnect timer
     */
    _clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Re-subscribe to all channels after reconnect
     */
    _resubscribeAll() {
        for (const channel of this.subscribers.keys()) {
            this._send({
                type: 'subscribe',
                channel: channel
            });
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        if (!this.ws) {
            return 'disconnected';
        }

        const states = {
            [WebSocket.CONNECTING]: 'connecting',
            [WebSocket.OPEN]: 'connected',
            [WebSocket.CLOSING]: 'closing',
            [WebSocket.CLOSED]: 'disconnected'
        };

        return states[this.ws.readyState] || 'unknown';
    }

    /**
     * Get statistics
     */
    getStats() {
        return {
            status: this.getStatus(),
            reconnectAttempts: this.reconnectAttempts,
            subscribersCount: this.subscribers.size,
            messageQueueLength: this.messageQueue.length,
            pingInterval: this.pingInterval
        };
    }
}

/**
 * Real-time Data Store Integration
 */
class RealtimeDataManager {
    constructor(wsManager) {
        this.wsManager = wsManager;
        this.dataStores = new Map();
        this.lastUpdate = new Map();
    }

    /**
     * Register data store for updates
     */
    registerStore(name, store) {
        this.dataStores.set(name, store);
    }

    /**
     * Subscribe to data channel
     */
    subscribe(channel, handler) {
        return this.wsManager.subscribe(channel, (payload) => {
            try {
                handler(payload);
                this.lastUpdate.set(channel, Date.now());
            } catch (error) {
                console.error(`Error handling ${channel} update:`, error);
            }
        });
    }

    /**
     * Get last update time for channel
     */
    getLastUpdate(channel) {
        return this.lastUpdate.get(channel);
    }
}

/**
 * Global WebSocket Manager Instance
 */
const wsManager = new WebSocketManager({
    url: `ws://${window.location.host}/ws`,
    maxReconnectAttempts: 5,
    reconnectInterval: 1000,
    pingInterval: 30000
});

const realtimeManager = new RealtimeDataManager(wsManager);

// Auto-connect on page load
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        wsManager.connect().catch(error => {
            console.error('Failed to connect WebSocket:', error);
            notifications.show('Real-time updates unavailable', {
                type: 'warning',
                duration: 0
            });
        });
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        wsManager.disconnect();
    });
}

// Export
export { wsManager, realtimeManager, WebSocketManager, RealtimeDataManager };
