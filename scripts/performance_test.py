#!/usr/bin/env python3
"""
Performance Test
Compare performance of inefficient vs optimized code
"""

import time
import asyncio
import numpy as np

def test_blocking_loop():
    """Test blocking loop (inefficient)"""
    data = list(range(10000))
    result = []
    
    start = time.time()
    for i in range(len(data)):
        result.append(data[i] * 2)
    elapsed = time.time() - start
    
    return elapsed

def test_vectorized_loop():
    """Test vectorized loop (efficient)"""
    data = np.array(list(range(10000)))
    
    start = time.time()
    result = data * 2  # Vectorized
    elapsed = time.time() - start
    
    return elapsed

def test_blocking_sleep():
    """Test blocking sleep (inefficient)"""
    start = time.time()
    time.sleep(1)
    elapsed = time.time() - start
    return elapsed

async def test_async_sleep():
    """Test async sleep (efficient)"""
    start = time.time()
    await asyncio.sleep(1)
    elapsed = time.time() - start
    return elapsed

async def test_concurrent_sleep():
    """Test concurrent async sleeps (most efficient)"""
    start = time.time()
    await asyncio.gather(*[asyncio.sleep(1) for _ in range(10)])
    elapsed = time.time() - start
    return elapsed

def main():
    print("=" * 70)
    print("PERFORMANCE COMPARISON TEST")
    print("=" * 70)
    
    # Test 1: Loop optimization
    print("\n[1] Loop Optimization Test")
    print("-" * 70)
    blocking_time = test_blocking_loop()
    vectorized_time = test_vectorized_loop()
    
    print(f"Blocking loop:     {blocking_time:.4f} seconds")
    print(f"Vectorized loop:   {vectorized_time:.4f} seconds")
    print(f"Speedup:           {blocking_time/vectorized_time:.1f}x faster")
    
    # Test 2: Sleep optimization
    print("\n[2] Sleep Optimization Test")
    print("-" * 70)
    blocking_sleep = test_blocking_sleep()
    async_sleep = asyncio.run(test_async_sleep())
    concurrent_sleep = asyncio.run(test_concurrent_sleep())
    
    print(f"Blocking sleep:    {blocking_sleep:.4f} seconds")
    print(f"Async sleep:       {async_sleep:.4f} seconds")
    print(f"Concurrent sleep:  {concurrent_sleep:.4f} seconds")
    print(f"Speedup:           {1/concurrent_sleep:.1f}x faster (10 operations)")
    
    print("\n" + "=" * 70)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 70)
    print("\n1. Use vectorized operations for data processing")
    print("   - 10-100x faster for NumPy arrays")
    print("   - 5-50x faster for Pandas DataFrames")
    print("\n2. Use asyncio for I/O-bound operations")
    print("   - 10-50x faster for concurrent API calls")
    print("   - Non-blocking event loop")
    print("\n3. Replace list comprehensions with vectorized operations where possible")
    print("\n4. Use async/await for all I/O operations")
    
    # Save results
    import json
    results = {
        'loop_optimization': {
            'blocking': blocking_time,
            'vectorized': vectorized_time,
            'speedup': blocking_time / vectorized_time
        },
        'sleep_optimization': {
            'blocking': blocking_sleep,
            'async': async_sleep,
            'concurrent': concurrent_sleep,
            'speedup': 1 / concurrent_sleep
        }
    }
    
    with open('performance_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to: performance_test_results.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
