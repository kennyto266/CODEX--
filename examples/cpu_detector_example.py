"""
CPU Detector Usage Examples - Task T053

This example demonstrates how to use the CPUDetector class to:
- Detect CPU information
- Monitor system load
- Get optimal worker count recommendations
- Optimize for backtest workloads
"""

import logging
from src.performance.cpu_detector import CPUDetector, ArchitectureType, HyperThreading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_1_basic_detection():
    """Example 1: Basic CPU detection"""
    print("=" * 70)
    print("Example 1: Basic CPU Detection")
    print("=" * 70)

    detector = CPUDetector()
    cpu_info = detector.detect_cpu()

    print(f"\nCPU Brand: {cpu_info.brand}")
    print(f"Architecture: {cpu_info.architecture.value}")
    print(f"Physical Cores: {cpu_info.physical_cores}")
    print(f"Logical Cores: {cpu_info.logical_cores}")
    print(f"Hyper-Threading: {cpu_info.hyperthreading.value}")
    print(f"Max Frequency: {cpu_info.max_frequency_mhz:.2f} MHz")
    print(f"Cache L3: {cpu_info.cache_l3_kb} KB" if cpu_info.cache_l3_kb else "Cache L3: N/A")
    print(f"NUMA Nodes: {cpu_info.numa_nodes}")


def example_2_system_monitoring():
    """Example 2: System load monitoring"""
    print("\n" + "=" * 70)
    print("Example 2: System Load Monitoring")
    print("=" * 70)

    detector = CPUDetector()
    load = detector.get_system_load()

    print(f"\nCPU Usage: {load.cpu_percent:.1f}%")
    print(f"Memory Usage: {load.memory_percent:.1f}%")
    print(f"Load Average: {', '.join(f'{x:.2f}' for x in load.load_average)}")
    print(f"Thermal State: {load.thermal_state}")
    print(f"Process Count: {load.processes_count}")


def example_3_worker_recommendations():
    """Example 3: Worker count recommendations"""
    print("\n" + "=" * 70)
    print("Example 3: Worker Count Recommendations")
    print("=" * 70)

    detector = CPUDetector()

    # Different workload types
    backtest_workers = detector.recommend_worker_count(workload_type="backtest")
    optimization_workers = detector.recommend_worker_count(workload_type="optimization")
    default_workers = detector.recommend_worker_count()

    print(f"\nRecommended Workers:")
    print(f"  For Backtest: {backtest_workers} workers")
    print(f"  For Optimization: {optimization_workers} workers")
    print(f"  Default: {default_workers} workers")

    # With constraints
    constrained_workers = detector.recommend_worker_count(
        min_workers=4,
        max_workers=8
    )
    print(f"  With constraints (4-8): {constrained_workers} workers")


def example_4_backtest_optimization():
    """Example 4: Backtest optimization"""
    print("\n" + "=" * 70)
    print("Example 4: Backtest Optimization")
    print("=" * 70)

    detector = CPUDetector()

    # Optimize for different scenarios
    scenarios = [
        {"strategy": "SMA", "data_mb": 100, "strategies": 50},
        {"strategy": "RSI", "data_mb": 500, "strategies": 100},
        {"strategy": "MACD", "data_mb": 1000, "strategies": 200},
    ]

    for scenario in scenarios:
        print(f"\nScenario: {scenario['strategy']} Strategy")
        print(f"  Data Size: {scenario['data_mb']} MB")
        print(f"  Number of Strategies: {scenario['strategies']}")

        optimization = detector.optimize_for_backtest(
            strategy_type=scenario['strategy'].lower(),
            data_size_mb=scenario['data_mb'],
            num_strategies=scenario['strategies']
        )

        print(f"  Recommended Workers: {optimization['worker_count']}")
        print(f"  Memory Required: {optimization['memory_required_gb']:.2f} GB")
        print(f"  Parallel Speedup: {optimization['parallel_speedup']:.2f}x")
        print(f"  Est. Time per Backtest: {optimization['estimated_time_per_backtest_ms']:.1f} ms")


def example_5_numa_topology():
    """Example 5: NUMA topology detection"""
    print("\n" + "=" * 70)
    print("Example 5: NUMA Topology Detection")
    print("=" * 70)

    detector = CPUDetector()
    numa = detector.get_numa_topology()

    if numa:
        print(f"\nDetected {len(numa)} cores with NUMA mapping")
        print("Core to Node Mapping:")
        for core, nodes in sorted(numa.items())[:10]:  # Show first 10
            print(f"  Core {core}: Node {', '.join(map(str, nodes))}")
        if len(numa) > 10:
            print(f"  ... and {len(numa) - 10} more cores")
    else:
        print("\nNUMA topology not detected (single node system)")


def example_6_architecture_specific():
    """Example 6: Architecture-specific recommendations"""
    print("\n" + "=" * 70)
    print("Example 6: Architecture-Specific Recommendations")
    print("=" * 70)

    detector = CPUDetector()
    cpu_info = detector.detect_cpu()

    print(f"\nArchitecture: {cpu_info.architecture.value}")
    print(f"Hyper-Threading: {cpu_info.hyperthreading.value}")

    if cpu_info.architecture == ArchitectureType.ARM64:
        print("\nARM64-specific recommendations:")
        print("  - ARM CPUs benefit from using all logical cores")
        print("  - Consider using all available threads for parallel tasks")
    elif cpu_info.hyperthreading == HyperThreading.ENABLED:
        print("\nHyper-Threading enabled recommendations:")
        print("  - CPU-bound tasks use physical cores")
        print("  - I/O-bound tasks can use logical cores")
        print("  - Backtest: use physical cores only")
        print("  - Optimization: can use all logical cores")
    else:
        print("\nNo Hyper-Threading:")
        print("  - Use all available cores for all tasks")


def example_7_performance_benchmark():
    """Example 7: CPU performance benchmark"""
    print("\n" + "=" * 70)
    print("Example 7: CPU Performance Benchmark")
    print("=" * 70)

    detector = CPUDetector()
    print("\nRunning CPU benchmark...")
    print("This may take a few seconds...")

    benchmark = detector.benchmark_cpu()

    print(f"\nBenchmark Results:")
    print(f"  Elapsed Time: {benchmark['elapsed_seconds']:.4f} seconds")
    print(f"  Iterations/second: {benchmark['iterations_per_second']:,.0f}")
    print(f"  Operations/second: {benchmark['operations_per_second']:,.0f}")


def example_8_complete_report():
    """Example 8: Complete detailed report"""
    print("\n" + "=" * 70)
    print("Example 8: Complete Detailed Report")
    print("=" * 70)

    detector = CPUDetector()
    detector.print_detailed_report()


if __name__ == "__main__":
    # Run all examples
    example_1_basic_detection()
    example_2_system_monitoring()
    example_3_worker_recommendations()
    example_4_backtest_optimization()
    example_5_numa_topology()
    example_6_architecture_specific()
    example_7_performance_benchmark()
    example_8_complete_report()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
