#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate frontend JavaScript API call test
"""
import requests
import json

def test_strategy_optimization(symbol="0700.HK", strategy_type="all"):
    """Simulate runOptimization function in frontend"""
    print(f"Testing symbol: {symbol}")
    print(f"Strategy type: {strategy_type}")

    try:
        # Simulate frontend fetch request
        url = f"http://localhost:8013/api/strategy-optimization/{symbol}"
        params = {"strategy_type": strategy_type}

        print(f"Request URL: {url}")
        print(f"Request params: {params}")

        # Send GET request
        response = requests.get(url, params=params)

        print(f"Response status: {response.status_code}")
        print(f"Response OK: {response.ok}")

        if not response.ok:
            # Simulate frontend error handling
            try:
                error_data = response.json()
                print(f"Error response: {error_data}")
                raise Exception(error_data.get('detail', f"HTTP {response.status} error"))
            except:
                print(f"Error response text: {response.text}")
                raise Exception(f"HTTP {response.status} error")

        # Simulate frontend parse response
        result = response.json()
        print(f"Response JSON: {json.dumps(result, indent=2)}")

        # Simulate frontend check success field
        if result.get('success'):
            print("SUCCESS: success = True")
            print(f"Best Sharpe Ratio: {result['data']['best_sharpe_ratio']}")
            print(f"Total Strategies: {result['data']['total_strategies']}")
            return True
        else:
            print("FAILED: success = False")
            print(f"Error message: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting API test simulation...")
    print("="*60)

    # Test single API call
    success = test_strategy_optimization("0700.HK", "all")

    if success:
        print("\nTEST PASSED! API works correctly")
    else:
        print("\nTEST FAILED!")

    print("="*60)
    print("Test completed!")
