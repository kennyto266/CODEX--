"""
Example: Using the Memory Management System (T055-T057)

This example demonstrates how to use the memory pool, GC optimizer,
and memory monitor together for efficient backtest operations.
"""

import sys
import os
import time
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from performance.memory_pool import get_array_pool, ArrayPool
from performance.gc_optimizer import get_gc_optimizer, GCOptimizer, GCStrategy
from performance.memory_monitor import get_memory_monitor, MemoryMonitor

def demo_memory_pool():
    """Demonstrate memory pool usage"""
    print("=" * 60)
    print("Demo 1: Memory Pool")
    print("=" * 60)

    # Get the global pool for 1260-day price data
    price_pool = get_array_pool((1260,))

    print("\nAllocating price arrays from pool...")
    arrays = []
    for i in range(5):
        # Get array from pool
        prices = price_pool.get_array()

        # Simulate loading 5 years of data (1260 trading days)
        prices[:] = np.random.randn(1260).cumsum() + 100
        arrays.append(prices)

        print(f"  Allocated array {i+1} from pool")

    # Check pool statistics
    stats = price_pool.get_stats()
    print(f"\nPool Statistics:")
    print(f"  Allocations: {stats['allocations']}")
    print(f"  Reuses: {stats['reuses']}")
    print(f"  Evictions: {stats['evictions']}")
    print(f"  Reuse rate: {stats['reuses'] / (stats['reuses'] + stats['allocations']):.2%}")

    print("\nReturning arrays to pool...")
    for arr in arrays:
        price_pool.return_array(arr)

    print("[OK] Memory pool demo completed\n")

def demo_gc_optimizer():
    """Demonstrate GC optimizer usage"""
    print("=" * 60)
    print("Demo 2: GC Optimizer")
    print("=" * 60)

    # Get global GC optimizer
    gc_opt = get_gc_optimizer()

    # Create some data to trigger GC
    print("\nCreating data to test GC...")
    data = []
    for i in range(3):
        data.append(np.random.randn(1000000))
        print(f"  Created dataset {i+1}")

    # Check current GC settings
    stats = gc_opt.get_stats()
    print(f"\nCurrent GC Configuration:")
    print(f"  Strategy: {gc_opt.config.strategy.value}")
    print(f"  Thresholds: {stats['thresholds']}")
    print(f"  Collections performed: {stats['collections']}")

    # Optimize for a medium dataset
    print("\nOptimizing for 200MB dataset...")
    result = gc_opt.optimize_for_backtest(200)
    print(f"  Recommended strategy: {result['strategy']}")
    print(f"  New thresholds: {result['thresholds']}")

    # Manually trigger GC
    print("\nRunning manual GC collection...")
    gc_result = gc_opt.collect(generation=0)
    print(f"  Collected: {gc_result['collected']} objects")
    print(f"  Time taken: {gc_result['time_ms']:.2f}ms")

    # Cleanup
    del data

    print("\n[OK] GC optimizer demo completed\n")

def demo_memory_monitor():
    """Demonstrate memory monitor usage"""
    print("=" * 60)
    print("Demo 3: Memory Monitor")
    print("=" * 60)

    # Create a new monitor (or use global)
    monitor = MemoryMonitor(
        alert_threshold_percent=70.0,
        critical_threshold_percent=85.0,
        check_interval_s=0.5
    )

    # Add callback for alerts
    alert_count = [0]  # Use list to allow modification in closure
    def on_alert(snapshot):
        alert_count[0] += 1
        print(f"  [ALERT #{alert_count[0]}] Memory at {snapshot.percent:.1f}%")

    monitor.add_callback(on_alert)

    print("\nMonitoring memory usage...")
    print("  (Creating test data to trigger monitoring)")

    # Create some test data
    data = []
    for i in range(3):
        data.append(np.random.randn(500000))
        print(f"  Created test data chunk {i+1}")
        time.sleep(1)  # Let monitor take snapshots

    # Check current snapshot
    snapshot = monitor.get_current_snapshot()
    if snapshot:
        print(f"\nCurrent Memory Status:")
        print(f"  RSS: {snapshot.rss_mb:.2f} MB")
        print(f"  VMS: {snapshot.vms_mb:.2f} MB")
        print(f"  System: {snapshot.percent:.1f}%")
        print(f"  Available: {snapshot.available_mb:.2f} MB")

    # Get statistics
    stats = monitor.get_statistics()
    if stats:
        print(f"\nStatistics:")
        print(f"  Peak: {stats['peak']['rss_mb']:.2f} MB")
        print(f"  Average: {stats['average']['rss_mb']:.2f} MB")
        print(f"  GC collections: {stats['gc_stats']['total_collections']}")

    # Export history
    export_file = "demo_memory_history.json"
    monitor.export_history(export_file)
    print(f"\nExported history to: {export_file}")

    # Cleanup
    del data
    time.sleep(0.5)
    monitor.stop()

    print(f"Alerts generated: {alert_count[0]}")
    print("[OK] Memory monitor demo completed\n")

def demo_integration():
    """Demonstrate all components working together"""
    print("=" * 60)
    print("Demo 4: Integrated System")
    print("=" * 60)

    # Initialize all components
    print("\nInitializing memory management system...")
    price_pool = get_array_pool((1260,))
    gc_opt = get_gc_optimizer()
    monitor = get_memory_monitor()

    # Get initial memory
    initial = monitor.get_current_snapshot()
    initial_mb = initial.rss_mb if initial else 0
    print(f"Initial memory: {initial_mb:.2f} MB")

    # Optimize GC for expected workload
    print("\nOptimizing GC for 5-year backtest (1260 days)...")
    gc_opt.optimize_for_backtest(150)  # ~150MB expected
    print("  GC optimized")

    # Simulate backtest operations
    print("\nSimulating backtest operations...")
    datasets = []
    for i in range(5):
        # Allocate from pool
        data = price_pool.get_array()

        # Simulate indicator calculation
        data[:] = np.random.randn(1260)
        processed = np.cumsum(data)  # Cumulative sum as example

        datasets.append(processed)
        print(f"  Processed dataset {i+1}")

        # Check memory periodically
        current = monitor.get_current_snapshot()
        if current:
            print(f"    Memory: {current.rss_mb:.2f} MB ({current.percent:.1f}%)")

        time.sleep(0.5)

    # Force GC
    print("\nRunning garbage collection...")
    gc_opt.collect(generation=0)

    # Get final memory
    final = monitor.get_current_snapshot()
    final_mb = final.rss_mb if final else 0
    print(f"Final memory: {final_mb:.2f} MB")
    print(f"Memory increase: {final_mb - initial_mb:.2f} MB")

    # Get statistics
    stats = monitor.get_statistics()
    if stats:
        print(f"Peak memory: {stats['peak']['rss_mb']:.2f} MB")

    # Cleanup
    print("\nCleaning up...")
    for data in datasets:
        price_pool.return_array(data)
    del datasets

    # Final GC
    gc_opt.collect(generation=0)

    final2 = monitor.get_current_snapshot()
    final2_mb = final2.rss_mb if final2 else 0
    print(f"After cleanup: {final2_mb:.2f} MB")
    print(f"Net change: {final2_mb - initial_mb:.2f} MB")

    print("[OK] Integrated system demo completed\n")

def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("Memory Management System (T055-T057) - Demo")
    print("=" * 60 + "\n")

    try:
        # Run individual demos
        demo_memory_pool()
        time.sleep(1)

        demo_gc_optimizer()
        time.sleep(1)

        demo_memory_monitor()
        time.sleep(1)

        demo_integration()

        print("=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  1. Memory pool reduces allocations and GC pressure")
        print("  2. GC optimizer adapts to your workload")
        print("  3. Memory monitor provides real-time visibility")
        print("  4. Integration provides comprehensive memory management")
        print("\nFor production use:")
        print("  - Set appropriate alert thresholds")
        print("  - Use global instances for consistency")
        print("  - Monitor trends over time")
        print("  - Export data for analysis")
        print()

    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
