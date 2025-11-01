/**
 * Data Formatting Utilities
 * Phase 7: Enhanced Architecture
 */

/**
 * Number formatting
 */
const NumberFormatter = {
    /**
     * Format number with locale separators
     */
    format(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '-';
        return new Intl.NumberFormat('en-HK', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    },

    /**
     * Format number with compact notation (K, M, B)
     */
    formatCompact(num) {
        if (num === null || num === undefined || isNaN(num)) return '-';

        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(2) + 'B';
        } else if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(2) + 'M';
        } else if (Math.abs(num) >= 1e3) {
            return (num / 1e3).toFixed(2) + 'K';
        }
        return num.toFixed(2);
    },

    /**
     * Format percentage
     */
    formatPercent(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '-';
        return `${num.toFixed(decimals)}%`;
    },

    /**
     * Format currency (Hong Kong Dollar)
     */
    formatCurrency(amount, symbol = 'HK$', decimals = 2) {
        if (amount === null || amount === undefined || isNaN(amount)) return '-';
        return `${symbol} ${new Intl.NumberFormat('en-HK', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(amount)}`;
    },

    /**
     * Format stock price
     */
    formatPrice(price, decimals = 2) {
        if (price === null || price === undefined || isNaN(price)) return '-';
        return new Intl.NumberFormat('en-HK', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(price);
    },

    /**
     * Format volume
     */
    formatVolume(volume) {
        if (volume === null || volume === undefined || isNaN(volume)) return '-';
        if (volume >= 1e9) {
            return (volume / 1e9).toFixed(2) + 'B';
        } else if (volume >= 1e6) {
            return (volume / 1e6).toFixed(2) + 'M';
        } else if (volume >= 1e3) {
            return (volume / 1e3).toFixed(2) + 'K';
        }
        return volume.toString();
    },

    /**
     * Format change with color indicator
     */
    formatChange(value, showSign = true) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        const sign = showSign && value > 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}`;
    },

    /**
     * Format change percentage with color
     */
    formatChangePercent(value, showSign = true) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        const sign = showSign && value > 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    }
};

/**
 * Date/Time formatting
 */
const DateFormatter = {
    /**
     * Format date to string
     */
    formatDate(date, format = 'yyyy-MM-dd') {
        if (!date) return '-';

        const d = new Date(date);
        if (isNaN(d.getTime())) return '-';

        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');

        const formatMap = {
            'yyyy-MM-dd': `${year}-${month}-${day}`,
            'yyyy-MM-dd HH:mm': `${year}-${month}-${day} ${hours}:${minutes}`,
            'yyyy-MM-dd HH:mm:ss': `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`,
            'dd/MM/yyyy': `${day}/${month}/${year}`,
            'dd MMM yyyy': d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
            'MMM dd, yyyy': d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
        };

        return formatMap[format] || `${year}-${month}-${day}`;
    },

    /**
     * Format relative time
     */
    formatRelativeTime(date) {
        if (!date) return '-';

        const now = new Date();
        const target = new Date(date);
        const diff = now - target;

        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`;

        return this.formatDate(date);
    },

    /**
     * Check if date is today
     */
    isToday(date) {
        const d = new Date(date);
        const today = new Date();
        return d.getDate() === today.getDate() &&
               d.getMonth() === today.getMonth() &&
               d.getFullYear() === today.getFullYear();
    },

    /**
     * Get time ago string
     */
    getTimeAgo(date) {
        if (!date) return '-';

        const now = new Date();
        const time = new Date(date);
        const diffInSeconds = Math.floor((now - time) / 1000);

        if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;

        return this.formatDate(date, 'dd/MM/yyyy');
    }
};

/**
 * String formatting
 */
const StringFormatter = {
    /**
     * Truncate string with ellipsis
     */
    truncate(str, length = 50, ellipsis = '...') {
        if (!str) return '-';
        if (str.length <= length) return str;
        return str.substring(0, length) + ellipsis;
    },

    /**
     * Capitalize first letter
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Convert to title case
     */
    titleCase(str) {
        if (!str) return '';
        return str.replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    },

    /**
     * Format stock symbol
     */
    formatStockSymbol(symbol) {
        if (!symbol) return '-';
        // Remove .HK suffix if present and add with dot
        const base = symbol.replace(/\.hk$/i, '');
        return `${base}.HK`;
    },

    /**
     * Format agent name
     */
    formatAgentName(name) {
        if (!name) return '-';
        return name.replace(/([A-Z])/g, ' $1').trim();
    }
};

/**
 * Performance metrics formatting
 */
const PerformanceFormatter = {
    /**
     * Format Sharpe ratio
     */
    formatSharpeRatio(ratio) {
        if (ratio === null || ratio === undefined || isNaN(ratio)) return '-';
        return ratio.toFixed(3);
    },

    /**
     * Format max drawdown
     */
    formatMaxDrawdown(drawdown) {
        if (drawdown === null || drawdown === undefined || isNaN(drawdown)) return '-';
        return `${drawdown.toFixed(2)}%`;
    },

    /**
     * Format beta
     */
    formatBeta(beta) {
        if (beta === null || beta === undefined || isNaN(beta)) return '-';
        return beta.toFixed(3);
    },

    /**
     * Format alpha
     */
    formatAlpha(alpha) {
        if (alpha === null || alpha === undefined || isNaN(alpha)) return '-';
        return `${alpha.toFixed(2)}%`;
    },

    /**
     * Format volatility
     */
    formatVolatility(vol) {
        if (vol === null || vol === undefined || isNaN(vol)) return '-';
        return `${vol.toFixed(2)}%`;
    },

    /**
     * Format win rate
     */
    formatWinRate(rate) {
        if (rate === null || rate === undefined || isNaN(rate)) return '-';
        return `${rate.toFixed(1)}%`;
    }
};

/**
 * Color utilities for displaying positive/negative values
 */
const ColorFormatter = {
    /**
     * Get color class for change
     */
    getChangeColor(value) {
        if (value === null || value === undefined || isNaN(value)) return 'text-gray-500';
        if (value > 0) return 'text-green-600';
        if (value < 0) return 'text-red-600';
        return 'text-gray-600';
    },

    /**
     * Get background color class for change
     */
    getChangeBgColor(value) {
        if (value === null || value === undefined || isNaN(value)) return 'bg-gray-100';
        if (value > 0) return 'bg-green-100';
        if (value < 0) return 'bg-red-100';
        return 'bg-gray-100';
    },

    /**
     * Get arrow indicator for change
     */
    getChangeArrow(value) {
        if (value === null || value === undefined || isNaN(value)) return '→';
        if (value > 0) return '↑';
        if (value < 0) return '↓';
        return '→';
    },

    /**
     * Get status color
     */
    getStatusColor(status) {
        const statusColors = {
            running: 'text-green-600',
            stopped: 'text-red-600',
            error: 'text-red-600',
            pending: 'text-yellow-600',
            completed: 'text-blue-600',
            active: 'text-green-600',
            inactive: 'text-gray-600'
        };
        return statusColors[status?.toLowerCase()] || 'text-gray-600';
    }
};

/**
 * Main formatter object combining all formatters
 */
const Formatter = {
    number: NumberFormatter,
    date: DateFormatter,
    string: StringFormatter,
    performance: PerformanceFormatter,
    color: ColorFormatter
};

// Export
export { Formatter, NumberFormatter, DateFormatter, StringFormatter, PerformanceFormatter, ColorFormatter };
