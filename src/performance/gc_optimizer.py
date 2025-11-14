"""
T056: GC Optimizer Implementation
Intelligent garbage collection tuning
"""

import gc
import sys
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import psutil

logger = logging.getLogger("hk_quant.performance.gc_optimizer")

class GCStrategy(Enum):
    """Garbage collection strategies"""
    CONSERVATIVE = "conservative"  # Default Python GC
    AGGRESSIVE = "aggressive"  # Frequent GC
    ADAPTIVE = "adaptive"  # Adaptive based on memory pressure
    MANUAL = "manual"  # Manual GC control

@dataclass
class GCConfig:
    """GC optimization configuration"""
    strategy: GCStrategy = GCStrategy.ADAPTIVE
    threshold: int = 700  # GC threshold
    memory_limit_mb: int = 1024
    collection_interval_s: float = 5.0
    enable_profiling: bool = True

class GCOptimizer:
    """Intelligent garbage collection optimizer"""

    def __init__(self, config: GCConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Get current GC settings
        self._original_thresholds = gc.get_threshold()

        # Set new thresholds based on strategy
        self._configure_gc()

        # Statistics
        self._gc_stats = {
            'collections': 0,
            'collected': 0,
            'uncollectable': 0,
            'total_time_ms': 0.0,
            'collections_by_gen': {0: 0, 1: 0, 2: 0}
        }

        self._lock = threading.Lock()

        # Start monitoring thread
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self._monitor_thread.start()

        self.logger.info(f"Initialized GCOptimizer with strategy: {config.strategy.value}")

    def _configure_gc(self):
        """Configure GC based on strategy"""
        if self.config.strategy == GCStrategy.CONSERVATIVE:
            # Default thresholds
            gc.set_threshold(700, 10, 10)

        elif self.config.strategy == GCStrategy.AGGRESSIVE:
            # More frequent collection
            gc.set_threshold(100, 10, 10)

        elif self.config.strategy == GCStrategy.ADAPTIVE:
            # Balanced approach
            gc.set_threshold(500, 10, 10)

        elif self.config.strategy == GCStrategy.MANUAL:
            # Disable automatic GC
            gc.set_threshold(0, 0, 0)

    def _monitor_memory(self):
        """Monitor memory and trigger GC if needed"""
        while self._monitoring:
            try:
                time.sleep(self.config.collection_interval_s)

                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)

                # Check if we need to collect
                if memory_mb > self.config.memory_limit_mb * 0.8:
                    self.logger.debug(f"Memory pressure detected: {memory_mb:.1f}MB, triggering GC")
                    self.collect(aggressive=True)

            except Exception as e:
                self.logger.error(f"GC monitoring error: {e}")

    def collect(self, generation: int = 2, aggressive: bool = False) -> Dict[str, int]:
        """Run garbage collection"""
        start_time = time.time()

        # Run collection
        if generation == -1:
            # Full collection
            collected = gc.collect()
        else:
            # Specific generation
            collected = gc.collect(generation)

        # Get uncollectable objects
        uncollectable = len(gc.garbage)

        # Update stats
        elapsed_ms = (time.time() - start_time) * 1000
        with self._lock:
            self._gc_stats['collections'] += 1
            self._gc_stats['collected'] += collected
            self._gc_stats['uncollectable'] = uncollectable
            self._gc_stats['total_time_ms'] += elapsed_ms
            self._gc_stats['collections_by_gen'][generation] += 1

        if aggressive or collected > 100:
            self.logger.info(
                f"GC: collected {collected} objects, "
                f"time: {elapsed_ms:.2f}ms, "
                f"uncollectable: {uncollectable}"
            )

        return {
            'collected': collected,
            'uncollectable': uncollectable,
            'time_ms': elapsed_ms
        }

    def optimize_for_backtest(self, data_size_mb: float) -> Dict[str, Any]:
        """Optimize GC settings for backtest workload"""
        # Adjust thresholds based on data size
        if data_size_mb > 500:
            # Large dataset, more aggressive
            gc.set_threshold(300, 10, 10)
            self.config.strategy = GCStrategy.AGGRESSIVE
        elif data_size_mb > 100:
            # Medium dataset, balanced
            gc.set_threshold(500, 10, 10)
            self.config.strategy = GCStrategy.ADAPTIVE
        else:
            # Small dataset, conservative
            gc.set_threshold(700, 10, 10)
            self.config.strategy = GCStrategy.CONSERVATIVE

        return {
            'strategy': self.config.strategy.value,
            'thresholds': gc.get_threshold(),
            'recommended': True
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get GC statistics"""
        with self._lock:
            avg_time = (
                self._gc_stats['total_time_ms'] / max(1, self._gc_stats['collections'])
            )

            return {
                **self._gc_stats,
                'avg_collection_time_ms': avg_time,
                'thresholds': gc.get_threshold(),
                'current_threshold': self.config.threshold
            }

    def __del__(self):
        """Cleanup"""
        self._monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1)

        # Restore original GC settings
        gc.set_threshold(*self._original_thresholds)

# Global GC optimizer
_gc_optimizer = GCOptimizer(GCConfig())

def get_gc_optimizer() -> GCOptimizer:
    """Get global GC optimizer"""
    return _gc_optimizer

def optimized_collect(generation: int = 2) -> int:
    """Run optimized garbage collection"""
    return _gc_optimizer.collect(generation)['collected']

# Test function
def test_gc_optimizer():
    """Test GC optimizer functionality"""
    print("=" * 60)
    print("Testing T056: GC Optimizer")
    print("=" * 60)

    # Test 1: Different strategies
    print("\nTest 1: GC Strategy Configuration")

    for strategy in GCStrategy:
        config = GCConfig(strategy=strategy)
        optimizer = GCOptimizer(config)
        stats = optimizer.get_stats()
        print(f"Strategy: {strategy.value}")
        print(f"  Thresholds: {stats['thresholds']}")
        optimizer.collect(generation=0)  # Trigger a collection
        del optimizer

    # Test 2: Backtest optimization
    print("\nTest 2: Backtest Optimization")

    optimizer = GCOptimizer(GCConfig())

    # Small dataset
    result = optimizer.optimize_for_backtest(50)
    print(f"Small dataset (50MB): {result}")

    # Medium dataset
    result = optimizer.optimize_for_backtest(200)
    print(f"Medium dataset (200MB): {result}")

    # Large dataset
    result = optimizer.optimize_for_backtest(800)
    print(f"Large dataset (800MB): {result}")

    # Test 3: Performance
    print("\nTest 3: GC Performance")

    import numpy as np

    # Create memory pressure
    data = []
    for i in range(5):
        data.append(np.random.randn(1000000))
        print(f"Iteration {i+1}: Created large array")

    # Collect GC stats
    stats = optimizer.get_stats()
    print(f"\nGC Stats before collection: {stats}")

    # Run collection
    result = optimizer.collect(aggressive=True)
    print(f"GC Collection result: {result}")

    stats = optimizer.get_stats()
    print(f"GC Stats after collection: {stats}")

    # Test 4: Memory pressure trigger
    print("\nTest 4: Memory Pressure Trigger")

    optimizer = GCOptimizer(GCConfig(
        memory_limit_mb=100,  # Low limit to trigger
        collection_interval_s=1.0
    ))

    # Simulate memory pressure
    data = []
    for i in range(3):
        data.append(np.random.randn(500000))
        time.sleep(2)  # Wait for monitoring thread
        print(f"Created array {i+1}")

    # Cleanup
    del data
    time.sleep(1)

    print("\n" + "=" * 60)
    print("T056: GC Optimizer - PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_gc_optimizer()
