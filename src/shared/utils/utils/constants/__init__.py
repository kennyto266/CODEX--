"""
Application constants
"""

# API Constants
API_TIMEOUT = 30
API_MAX_RETRIES = 3
CACHE_TTL = 3600

# Data Constants
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# HKEX Constants
HKEX_BASE_URL = "http://18.180.162.113:9191"
HKEX_SYMBOLS = [
    "0700.hk", "0388.hk", "1398.hk", "0939.hk", "3988.hk",
    "2318.hk", "2628.hk", "0386.hk", "0883.hk", "1299.hk"
]

# Risk Management
MAX_POSITION_SIZE = 0.10
STOP_LOSS_THRESHOLD = 0.05
TAKE_PROFIT_THRESHOLD = 0.10

# Performance
BENCHMARK_SYMBOL = "0700.hk"
MIN_TRADES = 10
