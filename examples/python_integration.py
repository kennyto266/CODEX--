#!/usr/bin/env python3
"""
Python integration example for Rust quant-backtest-pyo3

This example demonstrates how to use the Rust backtest engine from Python
with all 11 technical indicators and parameter optimization.
"""

import sys
import time
from datetime import datetime, timedelta

# Import the Rust module
try:
    from quant_backtest_pyo3 import (
        run_backtest,
        optimize_parameters,
        calculate_indicator,
        list_strategies,
        list_indicators,
        get_strategy_defaults,
    )
except ImportError as e:
    print(f"Error importing quant_backtest_pyo3: {e}")
    print("Make sure to build the module with: maturin build --release")
    sys.exit(1)


def generate_sample_data(symbol, days=1000):
    """Generate sample OHLCV data for testing"""
    data = []
    base_price = 100.0
    current_price = base_price

    for i in range(days):
        # Generate realistic price movement
        change = (i * 0.01) % (2 * 3.14159)
        price_change = (change.sin() * 5.0) + (change.cos() * 2.0)
        current_price += price_change

        # Generate OHLC
        open_price = current_price
        close_price = current_price + (price_change * 0.5)
        high_price = max(open_price, close_price) + abs(price_change)
        low_price = min(open_price, close_price) - abs(price_change)
        volume = 1000 + (i % 100) * 10

        # Create timestamp
        timestamp = int((datetime.now() - timedelta(days=days - i)).timestamp())

        data.append({
            "timestamp": timestamp,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
        })

        current_price = close_price

    return data


def test_rsi_strategy():
    """Test RSI strategy"""
    print("\n" + "=" * 60)
    print("Testing RSI Strategy")
    print("=" * 60)

    data = generate_sample_data("0700.HK", 1000)

    params = {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
    }

    start_time = time.time()
    result = run_backtest("0700.HK", data, "rsi", params, 100000.0)
    elapsed = time.time() - start_time

    print(f"\nBacktest completed in {elapsed:.3f} seconds")
    print(f"Total Return: {result['total_return']:.2%}")
    print(f"Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    print(f"Win Rate: {result['win_rate']:.2%}")
    print(f"Number of Trades: {result['num_trades']}")
    print(f"Number of Signals: {len(result['signals'])}")

    return result


def test_ma_strategy():
    """Test Moving Average strategy"""
    print("\n" + "=" * 60)
    print("Testing Moving Average Strategy")
    print("=" * 60)

    data = generate_sample_data("0388.HK", 1000)

    params = {
        "period": 20,
    }

    start_time = time.time()
    result = run_backtest("0388.HK", data, "ma", params, 100000.0)
    elapsed = time.time() - start_time

    print(f"\nBacktest completed in {elapsed:.3f} seconds")
    print(f"Total Return: {result['total_return']:.2%}")
    print(f"Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    print(f"Number of Trades: {result['num_trades']}")

    return result


def test_all_strategies():
    """Test all 11 strategies"""
    print("\n" + "=" * 60)
    print("Testing All 11 Technical Indicators")
    print("=" * 60)

    strategies = list_strategies()
    print(f"\nAvailable strategies: {', '.join(strategies)}")

    data = generate_sample_data("1398.HK", 1000)

    results = {}
    for strategy in strategies:
        print(f"\n--- Testing {strategy.upper()} strategy ---")
        params = get_strategy_defaults(strategy)

        start_time = time.time()
        result = run_backtest("1398.HK", data, strategy, params, 100000.0)
        elapsed = time.time() - start_time

        results[strategy] = result

        print(f"  Time: {elapsed:.3f}s")
        print(f"  Return: {result['total_return']:.2%}")
        print(f"  Trades: {result['num_trades']}")

    return results


def test_parameter_optimization():
    """Test parameter optimization"""
    print("\n" + "=" * 60)
    print("Testing Parameter Optimization")
    print("=" * 60)

    data = generate_sample_data("0939.HK", 1000)

    param_ranges = {
        "period": [10, 14, 20, 30],
        "overbought": [65, 70, 75],
        "oversold": [25, 30, 35],
    }

    print(f"\nParameter combinations: {len(param_ranges['period']) * len(param_ranges['overbought']) * len(param_ranges['oversold'])}")

    start_time = time.time()
    result = optimize_parameters("0939.HK", data, "rsi", param_ranges, max_workers=4)
    elapsed = time.time() - start_time

    print(f"\nOptimization completed in {elapsed:.3f} seconds")
    print(f"Best performance: {result['best_performance']:.2%}")
    print(f"Best parameters:")
    for key, value in result['best_params'].items():
        print(f"  {key}: {value}")

    return result


def test_indicator_calculation():
    """Test technical indicator calculations"""
    print("\n" + "=" * 60)
    print("Testing Technical Indicator Calculations")
    print("=" * 60)

    data = generate_sample_data("3988.HK", 1000)

    # Test SMA
    print("\n--- Calculating SMA ---")
    start_time = time.time()
    result = calculate_indicator(data, "sma", {"period": 20})
    elapsed = time.time() - start_time
    sma_values = result['sma']
    valid_values = [v for v in sma_values if not (v != v)]  # Filter NaN
    print(f"Time: {elapsed:.3f}s")
    print(f"Valid values: {len(valid_values)}/{len(sma_values)}")
    print(f"Last SMA: {valid_values[-1]:.2f}" if valid_values else "No valid values")

    # Test RSI
    print("\n--- Calculating RSI ---")
    start_time = time.time()
    result = calculate_indicator(data, "rsi", {"period": 14})
    elapsed = time.time() - start_time
    rsi_values = result['rsi']
    valid_values = [v for v in rsi_values if not (v != v)]  # Filter NaN
    print(f"Time: {elapsed:.3f}s")
    print(f"Valid values: {len(valid_values)}/{len(rsi_values)}")
    print(f"Last RSI: {valid_values[-1]:.2f}" if valid_values else "No valid values")

    # Test MACD
    print("\n--- Calculating MACD ---")
    start_time = time.time()
    result = calculate_indicator(data, "macd", {"fast": 12, "slow": 26, "signal": 9})
    elapsed = time.time() - start_time
    print(f"Time: {elapsed:.3f}s")
    print(f"MACD values: {len(result['macd'])}")
    print(f"Signal values: {len(result['signal'])}")
    print(f"Histogram values: {len(result['histogram'])}")


def benchmark_performance():
    """Benchmark performance with different data sizes"""
    print("\n" + "=" * 60)
    print("Performance Benchmark")
    print("=" * 60)

    data_sizes = [100, 500, 1000, 2000, 5000]

    for size in data_sizes:
        print(f"\n--- Data size: {size} days ---")
        data = generate_sample_data("0000.HK", size)
        params = get_strategy_defaults("rsi")

        start_time = time.time()
        result = run_backtest("0000.HK", data, "rsi", params, 100000.0)
        elapsed = time.time() - start_time

        print(f"  Time: {elapsed:.3f}s")
        print(f"  Return: {result['total_return']:.2%}")
        print(f"  Trades: {result['num_trades']}")


def main():
    """Main test function"""
    print("=" * 60)
    print("Rust Quant Backtest - Python Integration Tests")
    print("=" * 60)
    print(f"\nPython version: {sys.version}")

    # Test individual strategies
    rsi_result = test_rsi_strategy()
    ma_result = test_ma_strategy()

    # Test all strategies
    all_results = test_all_strategies()

    # Test parameter optimization
    opt_result = test_parameter_optimization()

    # Test indicator calculations
    test_indicator_calculation()

    # Benchmark performance
    benchmark_performance()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("\nAll tests completed successfully!")
    print("\nKey Metrics:")
    print(f"  RSI Return: {rsi_result['total_return']:.2%}")
    print(f"  MA Return: {ma_result['total_return']:.2%}")
    print(f"  Best Optimization: {opt_result['best_performance']:.2%}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
