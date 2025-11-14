# API Reference

## Overview

This document provides a complete reference for the HK Stock Quant System API v2.0.0.

## Base URL

```
Development: http://localhost:8001
Production: https://api.example.com
```

## Endpoints

### GET /

Root endpoint providing basic API information.

**Response:**
```json
{
  "message": "HK Stock Quant System API",
  "version": "2.0.0",
  "docs": "/docs",
  "health": "/api/health"
}
```

### GET /api/health

Returns the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime": 3600.0
}
```

### POST /api/backtest

Executes a trading strategy backtest on historical data.

**Request Body:**
```json
{
  "symbol": "0700.HK",
  "start_date": "2020-01-01",
  "end_date": "2023-01-01",
  "strategy": "ma",
  "initial_capital": 100000,
  "commission": 0.001
}
```

**Response:**
```json
{
  "symbol": "0700.HK",
  "strategy": "ma",
  "total_return": 0.25,
  "sharpe_ratio": 1.5,
  "max_drawdown": -0.1,
  "win_rate": 0.6,
  "total_trades": 100,
  "final_value": 125000,
  "execution_time": 2.5
}
```

### GET /api/strategies

Returns a list of all available trading strategies.

**Response:**
```json
{
  "strategies": [
    {"name": "ma", "description": "Moving Average Strategy"},
    {"name": "rsi", "description": "RSI Strategy"},
    {"name": "buy_hold", "description": "Buy and Hold"}
  ]
}
```

### GET /api/metrics

Returns system performance metrics.

**Response:**
```json
{
  "uptime": 3600,
  "request_count": 100,
  "memory_usage": "N/A",
  "cpu_usage": "N/A",
  "version": "2.0.0"
}
```

## Strategies

### ma (Moving Average)

Simple moving average crossover strategy.

**Parameters:**
- No additional parameters required

**Logic:**
- Buy when MA20 > MA50
- Sell when MA20 < MA50

### rsi (RSI)

Relative Strength Index strategy.

**Parameters:**
- No additional parameters required

**Logic:**
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)

### buy_hold (Buy and Hold)

Simple buy and hold strategy.

**Parameters:**
- No additional parameters required

**Logic:**
- Buy at the start
- Hold throughout the period

## Rate Limits

- 1000 requests per hour
- 100 requests per minute

## Support

For questions and support:
- Email: support@example.com
- GitHub: https://github.com/your-repo/issues
