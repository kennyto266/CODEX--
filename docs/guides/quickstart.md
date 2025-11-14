# API Quickstart Guide

Welcome to the HK Stock Quant System API! This guide will help you get started quickly.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Making Your First Request](#making-your-first-request)
- [Code Examples](#code-examples)
- [SDKs and Libraries](#sdks-and-libraries)
- [Common Use Cases](#common-use-cases)
- [Rate Limits](#rate-limits)
- [Support](#support)

## Getting Started

The HK Stock Quant System API provides programmatic access to:
- Market data for Hong Kong stocks
- Backtesting engine for strategy testing
- Portfolio management tools
- Real-time trading signals

### Base URL

```
Production: https://api.example.com
Development: http://localhost:8001
```

### API Version

Current version: **2.0.0**

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

> **Note**: Future versions will implement API key authentication. We'll announce changes in advance.

## Making Your First Request

### Using cURL

Check if the API is running:

```bash
curl http://localhost:8001/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": 3600.0
}
```

### Get All Available Strategies

```bash
curl http://localhost:8001/api/strategies
```

Response:

```json
{
  "strategies": [
    {"name": "ma", "description": "Moving Average Strategy"},
    {"name": "rsi", "description": "RSI Strategy"},
    {"name": "buy_hold", "description": "Buy and Hold"}
  ]
}
```

### Run a Backtest

```bash
curl -X POST http://localhost:8001/api/backtest   -H "Content-Type: application/json"   -d '{
    "symbol": "0700.HK",
    "start_date": "2020-01-01",
    "end_date": "2023-01-01",
    "strategy": "ma",
    "initial_capital": 100000,
    "commission": 0.001
  }'
```

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8001"

class APIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def get(self, endpoint, params=None):
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint, data=None):
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

# Example usage
client = APIClient()

# Check health
health = client.get("/api/health")
print(health)

# Run backtest
backtest = client.post("/api/backtest", {
    "symbol": "0700.HK",
    "start_date": "2020-01-01",
    "end_date": "2023-01-01",
    "strategy": "ma"
})
print(backtest)
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8001";

class APIClient {
    constructor(baseUrl = BASE_URL) {
        this.baseUrl = baseUrl;
    }
    
    async get(endpoint, params = {}) {
        const url = new URL(this.baseUrl + endpoint);
        Object.keys(params).forEach(key => 
            url.searchParams.append(key, params[key])
        );
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
    
    async post(endpoint, data = {}) {
        const response = await fetch(this.baseUrl + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// Example usage
const client = new APIClient();

const health = await client.get('/api/health');
console.log(health);

const backtest = await client.post('/api/backtest', {
    symbol: '0700.HK',
    start_date: '2020-01-01',
    end_date: '2023-01-01',
    strategy: 'ma'
});
console.log(backtest);
```

## SDKs and Libraries

### Official SDKs

- **Python**: `pip install hk-quant-api`
- **JavaScript**: `npm install hk-quant-api`

### Community Libraries

- R: [hkquantR](https://github.com/example/hkquantR)
- Java: [HKQuantJava](https://github.com/example/hkquantjava)

## Common Use Cases

### 1. Strategy Backtesting

```python
# Backtest multiple strategies
strategies = ["ma", "rsi", "macd", "bb"]
results = {}

for strategy in strategies:
    result = client.post("/api/backtest", {
        "symbol": "0700.HK",
        "start_date": "2020-01-01",
        "end_date": "2023-01-01",
        "strategy": strategy
    })
    results[strategy] = result
    
print(results)
```

### 2. Performance Comparison

```python
# Compare strategy performance
def compare_strategies(symbol, start_date, end_date):
    strategies = ["ma", "rsi", "buy_hold"]
    comparison = {}
    
    for strategy in strategies:
        result = client.post("/api/backtest", {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "strategy": strategy
        })
        comparison[strategy] = {
            "total_return": result["total_return"],
            "sharpe_ratio": result["sharpe_ratio"],
            "max_drawdown": result["max_drawdown"]
        }
    
    return comparison

performance = compare_strategies("0700.HK", "2020-01-01", "2023-01-01")
for strategy, metrics in performance.items():
    print(f"{strategy}: {metrics}")
```

## Rate Limits

Current limits:
- **Requests per hour**: 1000
- **Requests per minute**: 100

Rate limit headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

If you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

Error response format:

```json
{
  "error": "error_type",
  "message": "Human readable error message",
  "details": {
    "field": "Additional error details"
  }
}
```

### Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `invalid_request` | 400 | Invalid request parameters |
| `not_found` | 404 | Resource not found |
| `server_error` | 500 | Internal server error |
| `rate_limited` | 429 | Rate limit exceeded |

## Support

Need help? We're here for you!

- **Documentation**: https://your-repo.github.io
- **Email**: support@example.com
- **GitHub Issues**: https://github.com/your-repo/issues
- **Community Forum**: https://forum.example.com

## What's Next?

- Read the [API Reference](reference.md)
- Check out [Code Examples](../examples/)
- Learn about [Authentication](authentication.md)
- Review [Error Codes](error_codes.md)
