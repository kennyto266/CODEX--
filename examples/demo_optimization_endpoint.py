#!/usr/bin/env python3
"""
Demo: Parameter Optimization Endpoint

This script demonstrates how to use the optimization API endpoint for
parallel parameter optimization of trading strategies.

Features demonstrated:
- SMA strategy optimization
- RSI strategy optimization
- KDJ strategy optimization
- Parallel processing with progress tracking
- WebSocket real-time updates
- Performance metrics

Run this script while the FastAPI server is running to see the optimization
endpoint in action.
"""

import asyncio
import json
import time
import websockets
import requests
from typing import Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
API_BASE_URL = "http://localhost:8001/api/v1"
WEBSOCKET_URL = "ws://localhost:8001/api/v1/ws/optimization/progress"


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_step(step: int, description: str):
    """Print a formatted step"""
    print(f"\n[Step {step}] {description}")
    print("-" * 80)


def print_json(data: Dict[str, Any], indent: int = 2):
    """Print JSON data in a formatted way"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


async def demo_sma_optimization():
    """Demo 1: SMA (Simple Moving Average) Strategy Optimization"""
    print_header("Demo 1: SMA Strategy Optimization")

    request = {
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
        "max_combinations": 50,
        "top_n": 5
    }

    print("Optimizing SMA (Simple Moving Average) strategy...")
    print(f"Parameters:")
    print(f"  - Fast period: 5 to 30 (step 5)")
    print(f"  - Slow period: 20 to 60 (step 10)")
    print(f"  - Total combinations: 50")
    print(f"  - Objective: Sharpe Ratio")

    response = requests.post(
        f"{API_BASE_URL}/backtest/optimize",
        json=request,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Optimization completed successfully!")
        print(f"\nSummary:")
        print(f"  - Task ID: {result['task_id']}")
        print(f"  - Strategy: {result['strategy_type']}")
        print(f"  - Total combinations tested: {result['total_combinations']}")
        print(f"  - Execution time: {result['execution_time_ms']}ms")
        print(f"  - Workers used: {result['workers_used']}")

        if result['best_result']:
            best = result['best_result']
            print(f"\nBest Result (Rank #{best['rank']}):")
            print(f"  - Parameters: {best['parameters']}")
            print(f"  - Score: {best['score']:.4f}")
            print(f"  - Total Return: {best['metrics']['total_return']:.2%}")
            print(f"  - Sharpe Ratio: {best['metrics']['sharpe_ratio']:.4f}")
            print(f"  - Max Drawdown: {best['metrics']['max_drawdown']:.2%}")
            print(f"  - Win Rate: {best['metrics']['win_rate']:.2%}")

        print(f"\nPerformance Metrics:")
        perf = result['performance']
        print(f"  - Mode: {perf['mode']}")
        print(f"  - Speedup Factor: {perf.get('speedup_factor', 'N/A'):.2f}x")
        print(f"  - Memory Usage: {perf.get('memory_usage_mb', 0):.2f} MB")
        print(f"  - Throughput: {perf.get('throughput_per_second', 0):.2f} combinations/sec")

        return result
    else:
        print(f"\n✗ Optimization failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None


async def demo_rsi_optimization():
    """Demo 2: RSI (Relative Strength Index) Strategy Optimization"""
    print_header("Demo 2: RSI Strategy Optimization")

    request = {
        "symbol": "0700.HK",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy_type": "rsi",
        "parameter_spaces": [
            {
                "name": "period",
                "min_value": 10,
                "max_value": 30,
                "step": 5
            }
        ],
        "objective": "sharpe_ratio",
        "max_combinations": 20,
        "top_n": 3
    }

    print("Optimizing RSI (Relative Strength Index) strategy...")
    print(f"Parameters:")
    print(f"  - Period: 10 to 30 (step 5)")
    print(f"  - Total combinations: 20")
    print(f"  - Objective: Sharpe Ratio")

    response = requests.post(
        f"{API_BASE_URL}/backtest/optimize",
        json=request,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Optimization completed successfully!")
        print(f"\nSummary:")
        print(f"  - Task ID: {result['task_id']}")
        print(f"  - Strategy: {result['strategy_type']}")
        print(f"  - Total combinations tested: {result['total_combinations']}")
        print(f"  - Execution time: {result['execution_time_ms']}ms")

        if result['best_result']:
            best = result['best_result']
            print(f"\nBest Result (Rank #{best['rank']}):")
            print(f"  - Parameters: {best['parameters']}")
            print(f"  - Score: {best['score']:.4f}")
            print(f"  - Total Return: {best['metrics']['total_return']:.2%}")
            print(f"  - Sharpe Ratio: {best['metrics']['sharpe_ratio']:.4f}")

        return result
    else:
        print(f"\n✗ Optimization failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None


async def demo_kdj_optimization():
    """Demo 3: KDJ (Stochastic) Strategy Optimization"""
    print_header("Demo 3: KDJ Strategy Optimization")

    request = {
        "symbol": "0700.HK",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy_type": "kdj",
        "parameter_spaces": [
            {
                "name": "k_period",
                "min_value": 5,
                "max_value": 20,
                "step": 5
            },
            {
                "name": "d_period",
                "min_value": 3,
                "max_value": 7,
                "step": 2
            },
            {
                "name": "oversold",
                "min_value": 15,
                "max_value": 30,
                "step": 5
            },
            {
                "name": "overbought",
                "min_value": 70,
                "max_value": 85,
                "step": 5
            }
        ],
        "objective": "total_return",
        "max_combinations": 100,
        "top_n": 5
    }

    print("Optimizing KDJ (Stochastic) strategy...")
    print(f"Parameters:")
    print(f"  - K Period: 5 to 20 (step 5)")
    print(f"  - D Period: 3 to 7 (step 2)")
    print(f"  - Oversold: 15 to 30 (step 5)")
    print(f"  - Overbought: 70 to 85 (step 5)")
    print(f"  - Total combinations: 100 (sampled)")
    print(f"  - Objective: Total Return")

    response = requests.post(
        f"{API_BASE_URL}/backtest/optimize",
        json=request,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Optimization completed successfully!")
        print(f"\nSummary:")
        print(f"  - Task ID: {result['task_id']}")
        print(f"  - Strategy: {result['strategy_type']}")
        print(f"  - Total combinations tested: {result['total_combinations']}")

        if result['best_result']:
            best = result['best_result']
            print(f"\nBest Result (Rank #{best['rank']}):")
            print(f"  - Parameters: {best['parameters']}")
            print(f"  - Score: {best['score']:.4f}")
            print(f"  - Total Return: {best['metrics']['total_return']:.2%}")
            print(f"  - Max Drawdown: {best['metrics']['max_drawdown']:.2%}")
            print(f"  - Win Rate: {best['metrics']['win_rate']:.2%}")

        return result
    else:
        print(f"\n✗ Optimization failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None


async def demo_websocket_progress():
    """Demo 4: WebSocket Real-time Progress Updates"""
    print_header("Demo 4: WebSocket Real-time Progress Updates")

    print("Starting a longer optimization job to demonstrate WebSocket updates...")
    print("WebSocket URL:", WEBSOCKET_URL)

    request = {
        "symbol": "0700.HK",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy_type": "sma",
        "parameter_spaces": [
            {
                "name": "fast_period",
                "min_value": 5,
                "max_value": 50,
                "step": 5
            },
            {
                "name": "slow_period",
                "min_value": 20,
                "max_value": 100,
                "step": 10
            }
        ],
        "max_combinations": 200,
        "top_n": 10
    }

    # Start optimization
    response = requests.post(
        f"{API_BASE_URL}/backtest/optimize",
        json=request,
        timeout=300
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Optimization completed!")

        # Try to connect to WebSocket
        try:
            print("\nConnecting to WebSocket for progress updates...")
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                print("✓ WebSocket connected successfully!")

                # Receive a few messages
                for i in range(5):
                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(msg)
                        print(f"  [WS] Received: {data['type']} - {data.get('timestamp', '')}")
                    except asyncio.TimeoutError:
                        print("  [WS] No more messages (timeout)")
                        break

        except Exception as e:
            print(f"  [WS] Note: WebSocket test skipped: {e}")
            print("     (This is normal if the server is not running)")

        return result
    else:
        print(f"\n✗ Optimization failed: {response.status_code}")
        return None


def demo_comparison(results_list):
    """Demo 5: Compare Optimization Results"""
    print_header("Demo 5: Strategy Comparison")

    if not results_list or len(results_list) == 0:
        print("No results to compare. Run previous demos first.")
        return

    print(f"Comparing {len(results_list)} optimization runs:")
    print()

    comparison_data = []
    for i, result in enumerate(results_list, 1):
        if result and result.get('best_result'):
            best = result['best_result']
            comparison_data.append({
                'Strategy': result['strategy_type'].upper(),
                'Return': best['metrics']['total_return'],
                'Sharpe': best['metrics']['sharpe_ratio'],
                'Drawdown': best['metrics']['max_drawdown'],
                'Win Rate': best['metrics']['win_rate'],
                'Score': best['score']
            })

    if comparison_data:
        df = pd.DataFrame(comparison_data)
        print(df.to_string(index=False, float_format='%.4f'))

        print("\n\nKey Insights:")
        best_return = df.loc[df['Return'].idxmax()]
        best_sharpe = df.loc[df['Sharpe'].idxmax()]
        best_score = df.loc[df['Score'].idxmax()]

        print(f"  - Best Total Return: {best_return['Strategy']} ({best_return['Return']:.2%})")
        print(f"  - Best Sharpe Ratio: {best_sharpe['Strategy']} ({best_sharpe['Sharpe']:.4f})")
        print(f"  - Best Overall Score: {best_score['Strategy']} ({best_score['Score']:.4f})")


async def demo_health_check():
    """Demo: Health Check Endpoint"""
    print_header("Demo: Health Check")

    response = requests.get(f"{API_BASE_URL}/backtest/optimize/health")

    if response.status_code == 200:
        health = response.json()
        print("System Health Status:")
        print_json(health)
    else:
        print(f"Health check failed: {response.status_code}")


def check_server_status():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/backtest/optimize/health", timeout=2)
        return response.status_code == 200
    except:
        return False


async def main():
    """Main demo function"""
    print_header("PARAMETER OPTIMIZATION API DEMO")
    print("This demo showcases the parallel parameter optimization endpoint")
    print("for trading strategy backtesting.\n")

    # Check server status
    print_step(0, "Checking server status")
    if check_server_status():
        print("✓ FastAPI server is running on http://localhost:8001")
    else:
        print("✗ FastAPI server is not running!")
        print("  Please start the server with:")
        print("  $ python complete_project_system.py")
        print("  or")
        print("  $ uvicorn src.api.routes.optimization:router --host 0.0.0.0 --port 8001 --reload")
        return

    results = []

    # Demo 1: Health Check
    await demo_health_check()

    # Demo 2: SMA Optimization
    result = await demo_sma_optimization()
    if result:
        results.append(result)

    # Demo 3: RSI Optimization
    result = await demo_rsi_optimization()
    if result:
        results.append(result)

    # Demo 4: KDJ Optimization
    result = await demo_kdj_optimization()
    if result:
        results.append(result)

    # Demo 5: WebSocket Progress
    await demo_websocket_progress()

    # Demo 6: Comparison
    demo_comparison(results)

    # Summary
    print_header("Demo Complete")
    print("Thank you for testing the optimization endpoint!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Parallel parameter optimization")
    print("  ✓ Multiple strategy support (SMA, RSI, KDJ, etc.)")
    print("  ✓ Performance metrics and reporting")
    print("  ✓ WebSocket real-time progress updates")
    print("  ✓ Comprehensive result ranking")
    print("\nFor more information, see:")
    print("  - API Documentation: http://localhost:8001/docs")
    print("  - Test Suite: tests/test_optimization_endpoint.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
