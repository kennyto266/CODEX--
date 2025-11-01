/**
 * Global Error Handling System
 * Phase 7: Enhanced Architecture
 */

import { APIError, HTTPError } from './api.js';

/**
 * Error Types
 */
const ERROR_TYPES = {
    NETWORK_ERROR: 'NETWORK_ERROR',
    API_ERROR: 'API_ERROR',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
    PARSE_ERROR: 'PARSE_ERROR',
    UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

/**
 * Error Severity Levels
 */
const SEVERITY = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
};

/**
 * Error Handler Class
 */
class ErrorHandler {
    constructor() {
        this.errors = [];
        this.listeners = [];
        this.maxErrors = 100;
        this.isProduction = window.location.hostname !== 'localhost';
    }

    /**
     * Add error event listener
     */
    onError(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    }

    /**
     * Get error type from error object
     */
    _getErrorType(error) {
        if (error instanceof APIError) return ERROR_TYPES.API_ERROR;
        if (error instanceof HTTPError) return ERROR_TYPES.API_ERROR;
        if (error.name === 'AbortError') return ERROR_TYPES.TIMEOUT_ERROR;
        if (error.name === 'TypeError' && error.message.includes('fetch')) return ERROR_TYPES.NETWORK_ERROR;
        if (error.message.includes('timeout')) return ERROR_TYPES.TIMEOUT_ERROR;
        if (error.message.includes('JSON')) return ERROR_TYPES.PARSE_ERROR;
        return ERROR_TYPES.UNKNOWN_ERROR;
    }

    /**
     * Get error severity
     */
    _getSeverity(error) {
        if (error instanceof HTTPError) {
            if (error.status >= 500) return SEVERITY.HIGH;
            if (error.status >= 400) return SEVERITY.MEDIUM;
        }
        if (error instanceof APIError) {
            if (error.code === 'TIMEOUT') return SEVERITY.MEDIUM;
            return SEVERITY.MEDIUM;
        }
        if (error.name === 'AbortError') return SEVERITY.LOW;
        return SEVERITY.MEDIUM;
    }

    /**
     * Create error record
     */
    _createErrorRecord(error, context = {}) {
        return {
            id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date().toISOString(),
            type: this._getErrorType(error),
            severity: this._getSeverity(error),
            message: error.message,
            stack: error.stack,
            name: error.name,
            context,
            userAgent: navigator.userAgent,
            url: window.location.href,
            statusCode: error.status || null
        };
    }

    /**
     * Handle and log error
     */
    handle(error, context = {}) {
        const errorRecord = this._createErrorRecord(error, context);

        // Add to errors array
        this.errors.push(errorRecord);
        if (this.errors.length > this.maxErrors) {
            this.errors.shift();
        }

        // Notify listeners
        this.listeners.forEach(listener => {
            try {
                listener(errorRecord);
            } catch (e) {
                console.error('Error in error listener:', e);
            }
        });

        // Log to console
        console.group(`❌ Error: ${errorRecord.type}`);
        console.error('Message:', errorRecord.message);
        console.error('Stack:', errorRecord.stack);
        console.error('Context:', context);
        console.groupEnd();

        // In production, send to error reporting service
        if (this.isProduction) {
            this._reportToService(errorRecord);
        }

        return errorRecord;
    }

    /**
     * Report error to external service
     */
    async _reportToService(errorRecord) {
        try {
            // This would be replaced with actual error reporting service
            console.log('📤 Reporting error:', errorRecord.id);
        } catch (e) {
            console.error('Failed to report error:', e);
        }
    }

    /**
     * Get all errors
     */
    getErrors(filter = {}) {
        let filteredErrors = [...this.errors];

        if (filter.type) {
            filteredErrors = filteredErrors.filter(e => e.type === filter.type);
        }
        if (filter.severity) {
            filteredErrors = filteredErrors.filter(e => e.severity === filter.severity);
        }
        if (filter.since) {
            filteredErrors = filteredErrors.filter(e => e.timestamp >= filter.since);
        }

        return filteredErrors;
    }

    /**
     * Get error statistics
     */
    getStats() {
        const errors = this.errors;
        const typeCount = {};
        const severityCount = {};

        errors.forEach(error => {
            typeCount[error.type] = (typeCount[error.type] || 0) + 1;
            severityCount[error.severity] = (severityCount[error.severity] || 0) + 1;
        });

        return {
            total: errors.length,
            typeCount,
            severityCount,
            recentErrors: errors.slice(-10)
        };
    }

    /**
     * Clear errors
     */
    clear() {
        this.errors = [];
    }
}

/**
 * User Notification System
 */
class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.container = null;
        this._initContainer();
    }

    /**
     * Initialize notification container
     */
    _initContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }

    /**
     * Show notification
     */
    show(message, options = {}) {
        const {
            type = 'info', // info, success, warning, error
            duration = 5000,
            dismissible = true
        } = options;

        const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const notification = this._createNotification(id, message, type, dismissible);

        this.notifications.push(notification);
        this.container.appendChild(notification.element);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }

        return id;
    }

    /**
     * Create notification element
     */
    _createNotification(id, message, type, dismissible) {
        const colors = {
            info: { bg: '#3b82f6', border: '#2563eb' },
            success: { bg: '#10b981', border: '#059669' },
            warning: { bg: '#f59e0b', border: '#d97706' },
            error: { bg: '#ef4444', border: '#dc2626' }
        };

        const color = colors[type] || colors.info;

        const element = document.createElement('div');
        element.style.cssText = `
            pointer-events: auto;
            background: ${color.bg};
            color: white;
            padding: 16px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-width: 300px;
            max-width: 500px;
            animation: slideIn 0.3s ease-out;
        `;

        // Animation keyframes
        if (!document.getElementById('notif-styles')) {
            const style = document.createElement('style');
            style.id = 'notif-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        element.innerHTML = `
            <span>${message}</span>
            ${dismissible ? '<button style="background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:10px;">×</button>' : ''}
        `;

        if (dismissible) {
            const button = element.querySelector('button');
            button.addEventListener('click', () => this.dismiss(id));
        }

        return { id, element, type };
    }

    /**
     * Dismiss notification
     */
    dismiss(id) {
        const index = this.notifications.findIndex(n => n.id === id);
        if (index === -1) return;

        const notification = this.notifications[index];
        notification.element.style.animation = 'slideOut 0.3s ease-out';

        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
        }, 300);

        this.notifications.splice(index, 1);
    }

    /**
     * Clear all notifications
     */
    clear() {
        this.notifications.forEach(n => {
            if (n.element.parentNode) {
                n.element.parentNode.removeChild(n.element);
            }
        });
        this.notifications = [];
    }
}

/**
 * Global instances
 */
const errorHandler = new ErrorHandler();
const notifications = new NotificationSystem();

/**
 * Wrapper for async functions with error handling
 */
function withErrorHandling(fn, context = {}) {
    return async (...args) => {
        try {
            return await fn(...args);
        } catch (error) {
            errorHandler.handle(error, { ...context, function: fn.name });
            notifications.show(error.message || 'An error occurred', { type: 'error' });
            throw error;
        }
    };
}

/**
 * Automatic global error handlers
 */
window.addEventListener('error', (event) => {
    errorHandler.handle(event.error, { source: 'window.onerror' });
});

window.addEventListener('unhandledrejection', (event) => {
    errorHandler.handle(event.reason, { source: 'unhandledrejection' });
});

// Export
export { errorHandler, notifications, withErrorHandling, ERROR_TYPES, SEVERITY };
