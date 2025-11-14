# Parameter Optimization API Endpoint

## Overview

The Parameter Optimization API endpoint (`/api/v1/backtest/optimize`) provides high-performance parallel parameter optimization for trading strategies. It uses multi-core parallelism to efficiently search through parameter combinations and find the optimal configuration for your trading strategies.

## Features

### ✅ Core Features

- **Parallel Processing**: Utilizes multiple CPU cores for parallel parameter evaluation
- **Multiple Strategies**: Support for 11+ technical indicator strategies
- **Flexible Parameter Spaces**: Define custom parameter ranges with steps
- **Multiple Objectives**: Optimize for Sharpe ratio, total return, max drawdown, or win rate
- **Real-time Progress**: WebSocket support for live progress updates
- **Performance Metrics**: Comprehensive performance reporting including speedup factor
- **Result Ranking**: Automatic ranking and top-N results return
- **Error Handling**: Robust error handling with detailed error messages

### 📊 Supported Strategies

| Strategy | Parameters | Description |
|----------|-----------|-------------|
| **SMA** | fast_period, slow_period | Simple Moving Average crossover |
| **RSI** | period | Relative Strength Index |
| **MACD** | fast, slow, signal | Moving Average Convergence Divergence |
| **Bollinger Bands** | period, std_dev | Bollinger Bands mean reversion |
| **KDJ** | k_period, d_period, oversold, overbought | Stochastic Oscillator |
| **CCI** | period | Commodity Channel Index |
| **ADX** | period | Average Directional Index |
| **ATR** | period, multiplier | Average True Range |
| **OBV** | (none) | On-Balance Volume |
| **Ichimoku** | conversion, base, lag | Ichimoku Cloud |
| **Parabolic SAR** | af, max_af | Parabolic Stop and Reverse |

## API Reference

### POST /api/v1/backtest/optimize

Run parameter optimization for a trading strategy.

#### Request Body

```json
{
  "symbol": "0700.HK",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "strategy_type": "sma",
  "parameter_spaces": [
    {
      "name": "fast_period",
      "min_value": 5,
      "max_value": 30,
      "step": 5
    },
    {
      "name": "slow_period",
      "min_value": 20,
      "max_value": 60,
      "step": 10
    }
  ],
  "objective": "sharpe_ratio",
  "max_workers": 8,
  "max_combinations": 1000,
  "top_n": 10
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Stock symbol (e.g., "0700.HK") |
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |
| `strategy_type` | string | Yes | Strategy type (see supported strategies) |
| `parameter_spaces` | array | Yes | List of parameter space definitions |
| `objective` | string | No | Optimization objective (default: "sharpe_ratio") |
| `max_workers` | integer | No | Max worker threads (default: CPU cores) |
| `max_combinations` | integer | No | Max combinations to test (default: 1000, max: 10000) |
| `top_n` | integer | No | Number of top results to return (default: 10, max: 100) |

#### Parameter Space Definition

```json
{
  "name": "parameter_name",
  "min_value": 10,
  "max_value": 50,
  "step": 5
}
```

#### Response Body

```json
{
  "success": true,
  "task_id": "opt_20251109_001",
  "symbol": "0700.HK",
  "strategy_type": "sma",
  "total_combinations": 100,
  "best_result": {
    "rank": 1,
    "parameters": {
      "fast_period": 10,
      "slow_period": 30
    },
    "score": 1.5432,
    "metrics": {
      "total_return": 0.1823,
      "sharpe_ratio": 1.5432,
      "max_drawdown": 0.0923,
      "win_rate": 0.6534
    },
    "execution_time_ms": 42
  },
  "all_results": [...],
  "execution_time_ms": 5234,
  "workers_used": 8,
  "performance": {
    "mode": "parallel",
    "speedup_factor": 6.2,
    "memory_usage_mb": 125.3,
    "throughput_per_second": 12.5
  },
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### GET /api/v1/backtest/optimize/status/{task_id}

Get the status of an optimization task.

#### Response

```json
{
  "task_id": "opt_20251109_001",
  "status": "running",
  "progress": 45,
  "best_score": 1.2345,
  "start_time": 1702123456.789,
  "estimated_completion": 120
}
```

#### Status Values

- `running`: Optimization is in progress
- `completed`: Optimization completed successfully
- `failed`: Optimization failed with an error

### GET /api/v1/backtest/optimize/health

Health check for the optimization service.

#### Response

```json
{
  "status": "healthy",
  "active_tasks": 3,
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "memory_available_gb": 15.3,
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### WebSocket: /api/v1/ws/optimization/progress

WebSocket endpoint for real-time progress updates.

#### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/api/v1/ws/optimization/progress');
```

#### Messages

**Heartbeat** (every 5 seconds):
```json
{
  "type": "heartbeat",
  "timestamp": "2025-11-09T10:30:00Z",
  "active_tasks": 3
}
```

**Progress Update** (for running tasks):
```json
{
  "type": "progress",
  "task_id": "opt_20251109_001",
  "status": "running",
  "progress_percent": 45,
  "best_score": 1.2345,
  "timestamp": "2025-11-09T10:30:00Z"
}
```

## Usage Examples

### Python Client

```python
import requests
import json

# Define optimization request
request = {
    "symbol": "0700.HK",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_type": "sma",
    "parameter_spaces": [
        {"name": "fast_period", "min_value": 5, "max_value": 30, "step": 5},
        {"name": "slow_period", "min_value": 20, "max_value": 60, "step": 10}
    ],
    "objective": "sharpe_ratio",
    "max_combinations": 100,
    "top_n": 5
}

# Send request
response = requests.post(
    "http://localhost:8001/api/v1/backtest/optimize",
    json=request,
    timeout=120
)

if response.status_code == 200:
    result = response.json()
    print(f"Best parameters: {result['best_result']['parameters']}")
    print(f"Best score: {result['best_result']['score']}")
else:
    print(f"Error: {response.text}")
```

### cURL

```bash
curl -X POST "http://localhost:8001/api/v1/backtest/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "0700.HK",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "strategy_type": "sma",
    "parameter_spaces": [
      {"name": "fast_period", "min_value": 5, "max_value": 30, "step": 5},
      {"name": "slow_period", "min_value": 20, "max_value": 60, "step": 10}
    ],
    "max_combinations": 50
  }'
```

### JavaScript Client

```javascript
const request = {
  symbol: '0700.HK',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  strategy_type: 'rsi',
  parameter_spaces: [
    { name: 'period', min_value: 10, max_value: 30, step: 5 }
  ],
  objective: 'sharpe_ratio',
  max_combinations: 50
};

const response = await fetch('http://localhost:8001/api/v1/backtest/optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(request)
});

const result = await response.json();
console.log('Best result:', result.best_result);
```

## Performance Optimization

### Parallel Processing

The optimization engine uses `ThreadPoolExecutor` to parallelize parameter evaluation across CPU cores:

- **Automatic CPU Detection**: Automatically detects and uses all available CPU cores
- **Custom Worker Count**: Specify `max_workers` to control parallelism level
- **Chunked Processing**: Processes parameters in chunks for better memory management
- **Load Balancing**: Distributes work evenly across workers

### Performance Metrics

The API provides comprehensive performance metrics:

- **Execution Time**: Total time taken for optimization
- **Speedup Factor**: Parallel vs serial processing speedup
- **Memory Usage**: Peak memory consumption in MB
- **Throughput**: Combinations processed per second
- **Worker Utilization**: CPU core utilization percentage

### Best Practices

1. **Limit Combinations**: Use `max_combinations` to prevent excessive computation
   - Recommended: 100-1000 combinations for interactive use
   - Maximum: 10,000 combinations (hard limit)

2. **Optimize Parameter Ranges**: Use reasonable parameter ranges
   - Too wide ranges waste computation
   - Too narrow ranges may miss optimal values

3. **Choose Appropriate Step Size**: Balance between precision and performance
   - Larger steps = fewer combinations = faster optimization
   - Smaller steps = more combinations = better precision

4. **Use Appropriate Objectives**: Match objective to your strategy
   - **Sharpe Ratio**: Best for balanced risk/return (recommended)
   - **Total Return**: Best for pure profit maximization
   - **Max Drawdown**: Best for conservative strategies
   - **Win Rate**: Best for high-frequency strategies

5. **Monitor Progress**: Use WebSocket for long-running optimizations
   - Real-time progress updates
   - Estimated time to completion
   - Best score tracking

## Error Handling

### Common Errors

**1. Validation Error (422)**
```json
{
  "detail": [
    {
      "loc": ["body", "strategy_type"],
      "msg": "Invalid strategy type",
      "type": "value_error"
    }
  ]
}
```

**2. Too Many Combinations (400)**
```json
{
  "error": "Max combinations cannot exceed 10,000 for performance reasons",
  "task_id": "opt_20251109_001",
  "execution_time_ms": 123
}
```

**3. Invalid Parameter Space (400)**
```json
{
  "error": "Invalid parameter space: period (min >= max)",
  "task_id": "opt_20251109_001",
  "execution_time_ms": 45
}
```

**4. Invalid Date Format (400)**
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD",
  "task_id": "opt_20251109_001",
  "execution_time_ms": 12
}
```

### Troubleshooting

**Problem**: Optimization takes too long
- **Solution**: Reduce `max_combinations` or widen parameter steps

**Problem**: Out of memory errors
- **Solution**: Reduce `max_workers` or use smaller data ranges

**Problem**: "Strategy not supported" error
- **Solution**: Check that strategy_type is one of the supported strategies

**Problem**: WebSocket connection fails
- **Solution**: Ensure WebSocket is enabled in FastAPI app

## Testing

### Run Test Suite

```bash
# Run all tests
pytest tests/test_optimization_endpoint.py -v

# Run specific test class
pytest tests/test_optimization_endpoint.py::TestOptimizationAPI -v

# Run with coverage
pytest tests/test_optimization_endpoint.py --cov=src.api.routes.optimization --cov-report=html
```

### Run Demo Script

```bash
# Ensure server is running
python complete_project_system.py

# Run demo
python examples/demo_optimization_endpoint.py
```

The demo will:
1. Check server status
2. Run SMA optimization
3. Run RSI optimization
4. Run KDJ optimization
5. Test WebSocket progress
6. Compare results

### Test Coverage

The test suite includes:
- ✅ Unit tests for all models (ParameterSpace, OptimizationRequest, etc.)
- ✅ Integration tests for full optimization flow
- ✅ WebSocket tests for progress updates
- ✅ Performance tests for parallel processing
- ✅ Error handling tests
- ✅ Validation tests for all parameters

## Architecture

### System Components

```
┌─────────────────────────────────────┐
│     Client (Python/cURL/JS)         │
└──────────────┬──────────────────────┘
               │ HTTP POST
               ▼
┌─────────────────────────────────────┐
│   FastAPI Endpoint                   │
│   /api/v1/backtest/optimize          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Optimization Orchestrator          │
│   - Validates request                │
│   - Generates parameter combos       │
│   - Manages parallel execution       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   ThreadPoolExecutor (Parallel)      │
│   ┌──┐  ┌──┐  ┌──┐  ┌──┐            │
│   │W1│  │W2│  │W3│  │W4│            │
│   └──┘  └──┘  └──┘  └──┘            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Backtest Engine (Rust/Python)      │
│   - SMA, RSI, MACD, KDJ, etc.       │
│   - Returns performance metrics      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Results Processing                 │
│   - Sort by objective                │
│   - Calculate rankings               │
│   - Generate response                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Client (JSON Response)             │
└─────────────────────────────────────┘
```

### Data Flow

1. **Request Validation**: Validate all parameters and constraints
2. **Parameter Generation**: Generate all parameter combinations
3. **Chunking**: Split combinations into chunks for parallel processing
4. **Parallel Evaluation**: Evaluate each parameter set in parallel
5. **Result Collection**: Collect and merge results from all workers
6. **Ranking**: Sort results by objective and assign ranks
7. **Response**: Return top N results with performance metrics

## Monitoring

### Metrics Collected

The optimization service collects the following metrics:

- `optimization_requests_total`: Total number of optimization requests
- `optimization_completed_total`: Total completed optimizations
- `optimization_errors_total`: Total failed optimizations
- `optimization_duration_ms`: Histogram of optimization durations

### Logging

The service uses structured logging with correlation IDs:

```json
{
  "timestamp": "2025-11-09T10:30:00Z",
  "level": "INFO",
  "logger": "optimization_api",
  "correlation_id": "opt_20251109_001",
  "message": "Optimization request received",
  "symbol": "0700.HK",
  "strategy": "sma",
  "combinations": 100,
  "user_action": "optimization_request"
}
```

## Limitations

1. **Max Combinations**: Limited to 10,000 parameter combinations
2. **Date Range**: Limited to 5 years of historical data
3. **Strategies**: Limited to predefined strategies in Rust engine
4. **Memory**: Large parameter spaces may cause memory pressure
5. **Timeouts**: Individual parameter evaluations timeout after 30 seconds

## Future Enhancements

- [ ] Support for custom user-defined strategies
- [ ] Bayesian optimization for smarter parameter search
- [ ] GPU acceleration for indicator calculations
- [ ] Distributed optimization across multiple machines
- [ ] Caching of intermediate results
- [ ] Advanced multi-objective optimization
- [ ] Walk-forward analysis optimization
- [ ] Portfolio-level parameter optimization

## Contributing

When adding new features:

1. Update the strategy implementations in `src/backtest/rust_engine.py`
2. Add parameter validation in `_validate_optimization_request()`
3. Add strategy-specific evaluation in `_evaluate_parameters()`
4. Add tests in `tests/test_optimization_endpoint.py`
5. Update this documentation

## License

This optimization endpoint is part of the CODEX--港股量化交易系统 project.

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Run the demo script for examples
- Check the test suite for usage patterns
- Review the logs for error details
