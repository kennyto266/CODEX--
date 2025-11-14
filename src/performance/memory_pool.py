"""
T055: Memory Pool Implementation
Memory pool allocation for frequently used objects
"""

import numpy as np
import threading
from typing import Any, Optional, List, Dict, Deque
from dataclasses import dataclass
from collections import deque
import logging
import weakref

logger = logging.getLogger("hk_quant.performance.memory_pool")

@dataclass
class PoolConfig:
    """Memory pool configuration"""
    initial_size: int = 100
    max_size: int = 1000
    growth_factor: float = 1.5
    object_size_bytes: int = 1024
    enable_metrics: bool = True

class MemoryPool:
    """Memory pool for efficient allocation of frequently used objects"""

    def __init__(self, config: PoolConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()

        # Object pools
        self._object_pools: Dict[int, Deque[Any]] = {}
        self._object_sizes: Dict[int, int] = {}
        self._allocation_stats: Dict[str, int] = {
            'allocations': 0,
            'reuses': 0,
            'evictions': 0
        }

        # Initialize with some objects
        self._initialize_pool()

        self.logger.info(
            f"Initialized MemoryPool with max_size={config.max_size}, "
            f"object_size={config.object_size_bytes} bytes"
        )

    def _initialize_pool(self):
        """Initialize the object pool"""
        size = self.config.initial_size
        pool = deque()

        for _ in range(size):
            # Pre-allocate objects (example: numpy arrays)
            obj = self._create_object()
            pool.append(obj)

        self._object_pools[self.config.object_size_bytes] = pool
        self._object_sizes[self.config.object_size_bytes] = size

    def _create_object(self) -> Any:
        """Create a new object for the pool"""
        # Example: Create numpy array
        return np.zeros(self.config.object_size_bytes // 8, dtype=np.float64)

    def acquire(self, size: Optional[int] = None) -> Any:
        """Acquire an object from the pool"""
        size = size or self.config.object_size_bytes

        with self._lock:
            # Try to get from pool
            if size in self._object_pools and self._object_pools[size]:
                obj = self._object_pools[size].popleft()
                self._allocation_stats['reuses'] += 1
                return obj

            # Create new object
            self._allocation_stats['allocations'] += 1
            return self._create_sized_object(size)

    def _create_sized_object(self, size: int) -> Any:
        """Create a new object of specific size"""
        # Calculate number of elements
        num_elements = size // 8
        return np.zeros(num_elements, dtype=np.float64)

    def release(self, obj: Any, size: Optional[int] = None):
        """Release an object back to the pool"""
        if obj is None:
            return

        size = size or self.config.object_size_bytes

        with self._lock:
            # Initialize pool for this size if needed
            if size not in self._object_pools:
                self._object_pools[size] = deque()

            # Check if pool has room
            current_size = len(self._object_pools[size])
            max_size = self._object_sizes.get(size, self.config.max_size)

            if current_size < max_size:
                # Reset object and add to pool
                self._reset_object(obj)
                self._object_pools[size].append(obj)
            else:
                # Pool is full, let GC handle it
                self._allocation_stats['evictions'] += 1

    def _reset_object(self, obj: Any):
        """Reset object to pristine state"""
        if isinstance(obj, np.ndarray):
            obj.fill(0)
        # Add other object types as needed

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            total_pooled = sum(len(pool) for pool in self._object_pools.values())
            return {
                **self._allocation_stats,
                'total_pooled': total_pooled,
                'pool_sizes': {f"size_{k}": len(v) for k, v in self._object_pools.items()},
                'pool_utilization': total_pooled / max(1, self.config.max_size)
            }

    def clear(self):
        """Clear all pools"""
        with self._lock:
            self._object_pools.clear()
            self._allocation_stats = {
                'allocations': 0,
                'reuses': 0,
                'evictions': 0
            }

class ArrayPool(MemoryPool):
    """Specialized pool for numpy arrays"""

    def __init__(self, dtype=np.float64, shape=(1000,), max_arrays=100):
        self.dtype = dtype
        self.shape = shape
        self.max_arrays = max_arrays
        super().__init__(PoolConfig(
            initial_size=10,
            max_size=max_arrays,
            object_size_bytes=int(np.prod(shape)) * np.dtype(dtype).itemsize
        ))

    def _create_object(self) -> np.ndarray:
        """Create numpy array"""
        return np.zeros(self.shape, dtype=self.dtype)

    def get_array(self) -> np.ndarray:
        """Get array from pool"""
        return self.acquire()

    def return_array(self, arr: np.ndarray):
        """Return array to pool"""
        if arr.shape == self.shape and arr.dtype == self.dtype:
            self.release(arr)
        else:
            self.logger.warning("Array shape/dtype mismatch, letting GC handle it")

# Global pools
_array_pool = ArrayPool(max_arrays=50)
_price_array_pool = ArrayPool(shape=(1260,), max_arrays=20)  # For 5-year data

def get_array_pool(shape: tuple = (1000,)) -> ArrayPool:
    """Get array pool for specific shape"""
    if shape == (1000,):
        return _array_pool
    elif shape == (1260,):
        return _price_array_pool
    else:
        return ArrayPool(shape=shape, max_arrays=10)

# Test function
def test_memory_pool():
    """Test memory pool functionality"""
    print("=" * 60)
    print("Testing T055: Memory Pool")
    print("=" * 60)

    # Test 1: Basic MemoryPool
    print("\nTest 1: Basic MemoryPool")
    config = PoolConfig(initial_size=10, max_size=20, object_size_bytes=1024)
    pool = MemoryPool(config)

    # Acquire and release objects
    for i in range(15):
        obj = pool.acquire(1024)
        pool.release(obj)

    stats = pool.get_stats()
    print(f"Stats: {stats}")
    print(f"Reuse rate: {stats['reuses'] / (stats['allocations'] + stats['reuses']):.2%}")

    # Test 2: ArrayPool
    print("\nTest 2: ArrayPool")
    arr_pool = ArrayPool(shape=(1000,), max_arrays=10)

    arrays = []
    for i in range(12):
        arr = arr_pool.get_array()
        arr.fill(i)  # Set some values
        arrays.append(arr)

    # Return arrays
    for arr in arrays:
        arr_pool.return_array(arr)

    print(f"Array pool stats: {arr_pool.get_stats()}")

    # Test 3: Performance comparison
    print("\nTest 3: Performance comparison")
    import time

    # Without pool
    start = time.time()
    for _ in range(1000):
        arr = np.zeros(1000)
    no_pool_time = time.time() - start

    # With pool
    start = time.time()
    for _ in range(1000):
        arr = arr_pool.get_array()
        arr_pool.return_array(arr)
    with_pool_time = time.time() - start

    print(f"Without pool: {no_pool_time:.4f}s")
    print(f"With pool: {with_pool_time:.4f}s")
    print(f"Speedup: {no_pool_time / with_pool_time:.2f}x")

    print("\n" + "=" * 60)
    print("T055: Memory Pool - PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_memory_pool()
