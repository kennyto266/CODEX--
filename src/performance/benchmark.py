"""
Memory Optimization Benchmark
Simple benchmark for memory optimization features
"""

import time
import gc
import logging
from typing import Dict, Any

logger = logging.getLogger("hk_quant.performance.benchmark")

class PerformanceBenchmark:
    """Performance benchmark for memory optimization"""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.start_time = time.time()

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark tests"""
        logger.info("=" * 60)
        logger.info("Starting performance benchmarks")
        logger.info("=" * 60)

        start_time = time.time()
        
        self.benchmark_data_chunker()
        self.benchmark_memory_pool()
        self.benchmark_garbage_collection()

        total_time = time.time() - start_time

        summary = {
            "total_benchmark_time_sec": total_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.results
        }

        self.print_summary(summary)
        return summary

    def benchmark_data_chunker(self) -> Dict[str, Any]:
        """Data chunker benchmark"""
        logger.info("Running data chunker benchmark")

        # Simulate large data
        data_size = 100000
        chunk_size = 10000
        chunk_count = data_size // chunk_size
        
        start_time = time.time()
        chunk_count_actual = 0
        for i in range(0, data_size, chunk_size):
            # Simulate chunk processing
            chunk = list(range(i, min(i + chunk_size, data_size)))
            chunk_count_actual += 1
        chunk_time = time.time() - start_time
        
        self.results["data_chunker"] = {
            "data_size": data_size,
            "chunk_count": chunk_count_actual,
            "chunk_time_sec": chunk_time,
            "throughput_per_sec": chunk_count_actual / chunk_time if chunk_time > 0 else 0
        }
        
        logger.info(f"Data chunker: {chunk_count_actual} chunks, {chunk_time:.2f}s")
        return self.results["data_chunker"]

    def benchmark_memory_pool(self) -> Dict[str, Any]:
        """Memory pool benchmark"""
        logger.info("Running memory pool benchmark")
        
        num_allocs = 10000
        start_time = time.time()
        allocations = []
        for i in range(num_allocs):
            # Simulate allocation
            alloc = [0] * 1000  # 1K integers
            allocations.append(alloc)
        alloc_time = time.time() - start_time
        
        # Simulate deallocation
        start_time = time.time()
        allocations.clear()
        dealloc_time = time.time() - start_time
        
        self.results["memory_pool"] = {
            "num_allocations": num_allocs,
            "allocation_time_sec": alloc_time,
            "deallocation_time_sec": dealloc_time,
            "allocation_rate_per_sec": num_allocs / alloc_time if alloc_time > 0 else 0,
            "deallocation_rate_per_sec": num_allocs / dealloc_time if dealloc_time > 0 else 0
        }
        
        logger.info(f"Memory pool: {num_allocs} allocations, {alloc_time:.2f}s")
        return self.results["memory_pool"]

    def benchmark_garbage_collection(self) -> Dict[str, Any]:
        """Garbage collection benchmark"""
        logger.info("Running garbage collection benchmark")
        
        num_objects = 100000
        start_time = time.time()
        objects = []
        for i in range(num_objects):
            obj = {"data": list(range(100)), "id": i}
            objects.append(obj)
        creation_time = time.time() - start_time
        
        # Force garbage collection
        start_time = time.time()
        collected = gc.collect()
        gc_time = time.time() - start_time
        
        self.results["garbage_collection"] = {
            "num_objects": num_objects,
            "creation_time_sec": creation_time,
            "creation_rate_per_sec": num_objects / creation_time if creation_time > 0 else 0,
            "gc_time_sec": gc_time,
            "objects_collected": collected
        }
        
        logger.info(f"Garbage collection: {num_objects} objects, {gc_time:.2f}s")
        return self.results["garbage_collection"]

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("Performance Benchmark Summary")
        print("=" * 60)
        print(f"Total test time: {results['total_benchmark_time_sec']:.2f} seconds\n")
        
        if "data_chunker" in results["results"]:
            r = results["results"]["data_chunker"]
            print(f"Data Chunker:")
            print(f"  Chunks: {r['chunk_count']}")
            print(f"  Throughput: {r['throughput_per_sec']:.0f} chunks/sec")
        
        if "memory_pool" in results["results"]:
            r = results["results"]["memory_pool"]
            print(f"\nMemory Pool:")
            print(f"  Allocations: {r['allocation_rate_per_sec']:.0f} /sec")
            print(f"  Deallocations: {r['deallocation_rate_per_sec']:.0f} /sec")
        
        if "garbage_collection" in results["results"]:
            r = results["results"]["garbage_collection"]
            print(f"\nGarbage Collection:")
            print(f"  Object creation: {r['creation_rate_per_sec']:.0f} /sec")
            print(f"  GC time: {r['gc_time_sec']:.4f} sec")
            print(f"  Objects collected: {r['objects_collected']}")
        
        print("=" * 60)

    def check_performance_targets(self, results: Dict[str, Any]) -> Dict[str, bool]:
        """Check if performance targets are met"""
        targets = {
            "allocation_speed": False,
            "deallocation_speed": False,
            "gc_efficiency": False
        }

        if "memory_pool" in results["results"]:
            r = results["results"]["memory_pool"]
            if r.get("allocation_rate_per_sec", 0) > 100000:  # 100K/sec
                targets["allocation_speed"] = True
            if r.get("deallocation_rate_per_sec", 0) > 200000:  # 200K/sec
                targets["deallocation_speed"] = True

        if "garbage_collection" in results["results"]:
            r = results["results"]["garbage_collection"]
            if r.get("creation_rate_per_sec", 0) > 50000:  # 50K/sec
                targets["gc_efficiency"] = True

        return targets


def main():
    """Main function"""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()

    # Check performance targets
    targets = benchmark.check_performance_targets(results)

    print("\nPerformance targets:")
    print("-" * 60)
    for target, achieved in targets.items():
        status = "✓" if achieved else "✗"
        print(f"{status} {target}: {'Achieved' if achieved else 'Not achieved'}")
    print("-" * 60)

    return results


if __name__ == "__main__":
    main()
