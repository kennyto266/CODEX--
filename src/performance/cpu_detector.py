"""
T053: CPU Core Detection and Auto-Configuration

Intelligent CPU core detection and automatic configuration system for
optimal parallel backtest execution.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil
import os
import platform
import subprocess

logger = logging.getLogger(__name__)


class ArchitectureType(Enum):
    """CPU architecture types"""
    X86_64 = "x86_64"
    ARM64 = "arm64"
    AARCH64 = "aarch64"
    PPC64 = "ppc64"
    UNKNOWN = "unknown"


class HyperThreading(Enum):
    """Hyper-threading status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass
class CPUInfo:
    """CPU information container"""
    brand: str
    model: str
    architecture: ArchitectureType
    vendor: str
    physical_cores: int
    logical_cores: int
    threads_per_core: float
    max_frequency_mhz: float
    min_frequency_mhz: float
    current_frequency_mhz: float
    cache_l1_kb: Optional[int] = None
    cache_l2_kb: Optional[int] = None
    cache_l3_kb: Optional[int] = None
    cpu_count: int = 0
    numa_nodes: int = 1

    @property
    def hyperthreading(self) -> HyperThreading:
        """Detect if hyper-threading is enabled"""
        if self.logical_cores > self.physical_cores:
            return HyperThreading.ENABLED
        elif self.logical_cores < self.physical_cores:
            return HyperThreading.UNKNOWN
        else:
            return HyperThreading.DISABLED

    @property
    def recommended_workers(self) -> int:
        """Get recommended worker count for backtest"""
        if self.architecture in [ArchitectureType.ARM64, ArchitectureType.AARCH64]:
            # ARM CPUs often benefit from using all logical cores
            return self.logical_cores
        elif self.hyperthreading == HyperThreading.ENABLED:
            # For x86 with HT, use physical cores for CPU-bound tasks
            return self.physical_cores
        else:
            # No HT, use all cores
            return self.logical_cores

    @property
    def max_safe_workers(self) -> int:
        """Get maximum safe worker count"""
        # Leave 1-2 cores free for system
        return max(1, self.logical_cores - 2)


@dataclass
class SystemLoad:
    """Current system load information"""
    cpu_percent: float
    memory_percent: float
    load_average: List[float]
    processes_count: int
    context_switches: int
    interrupts: int
    thermal_state: str = "normal"  # normal, throttling, critical


class CPUDetector:
    """CPU detection and configuration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cpu_info: Optional[CPUInfo] = None
        self._cache_ttl = 300  # 5 minutes

    def detect_cpu(self) -> CPUInfo:
        """Detect CPU information"""
        if self._cpu_info is not None:
            return self._cpu_info

        # Get basic CPU info
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        frequency = psutil.cpu_freq()

        # Detect architecture
        arch = self._detect_architecture()

        # Detect brand and model
        brand, vendor = self._detect_cpu_brand()

        # Calculate threads per core
        threads_per_core = (
            cpu_count_logical / cpu_count_physical
            if cpu_count_physical else 1.0
        )

        # Get frequency info
        max_freq = frequency.max if frequency else 0
        min_freq = frequency.min if frequency else 0
        current_freq = frequency.current if frequency else 0

        # Get cache info
        cache_l1, cache_l2, cache_l3 = self._detect_cache_info()

        # Get NUMA info
        numa_nodes = self._detect_numa_nodes()

        self._cpu_info = CPUInfo(
            brand=brand,
            model=vendor,
            architecture=arch,
            vendor=vendor,
            physical_cores=cpu_count_physical or 1,
            logical_cores=cpu_count_logical or 1,
            threads_per_core=threads_per_core,
            max_frequency_mhz=max_freq,
            min_frequency_mhz=min_freq,
            current_frequency_mhz=current_freq,
            cache_l1_kb=cache_l1,
            cache_l2_kb=cache_l2,
            cache_l3_kb=cache_l3,
            cpu_count=cpu_count_logical or 1,
            numa_nodes=numa_nodes
        )

        self.logger.info(f"Detected CPU: {self._cpu_info.brand} "
                        f"({self._cpu_info.physical_cores}P/{self._cpu_info.logical_cores}L cores)")

        return self._cpu_info

    def _detect_architecture(self) -> ArchitectureType:
        """Detect CPU architecture"""
        machine = platform.machine().lower()

        if machine in ['x86_64', 'amd64']:
            return ArchitectureType.X86_64
        elif machine in ['arm64', 'aarch64']:
            return ArchitectureType.ARM64
        elif machine in ['ppc64', 'ppc64le']:
            return ArchitectureType.PPC64
        else:
            return ArchitectureType.UNKNOWN

    def _detect_cpu_brand(self) -> Tuple[str, str]:
        """Detect CPU brand and model"""
        try:
            if platform.system() == "Linux":
                # Read from /proc/cpuinfo
                with open('/proc/cpuinfo', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('model name'):
                            brand = line.split(':')[1].strip()
                            return brand, "Unknown"
                        elif line.startswith('CPU'):
                            brand = line.split(':')[1].strip()
                            return brand, "Unknown"

            elif platform.system() == "Darwin":
                # Use sysctl on macOS
                result = subprocess.run(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    brand = result.stdout.strip()
                    return brand, "Apple"

            elif platform.system() == "Windows":
                # Use WMI on Windows
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'name', '/value'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Name='):
                            brand = line.split('=')[1].strip()
                            return brand, "Intel/AMD"

        except Exception as e:
            self.logger.warning(f"Error detecting CPU brand: {e}")

        # Fallback
        return platform.processor() or "Unknown CPU", "Unknown"

    def _detect_cache_info(self) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Detect CPU cache sizes"""
        try:
            if platform.system() == "Linux":
                with open('/sys/devices/system/cpu/cpu0/cache/index0/size', 'r') as f:
                    l1_size_kb = int(f.read().strip())

                with open('/sys/devices/system/cpu/cpu0/cache/index2/size', 'r') as f:
                    l2_size_kb = int(f.read().strip())

                with open('/sys/devices/system/cpu/cpu0/cache/index3/size', 'r') as f:
                    l3_size_kb = int(f.read().strip())

                return l1_size_kb, l2_size_kb, l3_size_kb

        except Exception as e:
            self.logger.debug(f"Could not detect cache info: {e}")

        return None, None, None

    def _detect_numa_nodes(self) -> int:
        """Detect number of NUMA nodes"""
        try:
            if platform.system() == "Linux":
                # Count NUMA nodes
                numa_nodes_path = '/sys/devices/system/node'
                if os.path.exists(numa_nodes_path):
                    nodes = [n for n in os.listdir(numa_nodes_path) if n.startswith('node')]
                    return len(nodes)

        except Exception as e:
            self.logger.debug(f"Could not detect NUMA nodes: {e}")

        return 1  # Default to 1 NUMA node

    def get_system_load(self) -> SystemLoad:
        """Get current system load"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]

        # Get process count
        processes = len(psutil.pids())

        # Get context switches and interrupts (Linux only)
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('ctxt'):
                        context_switches = int(line.split()[1])
                    elif line.startswith('intr'):
                        interrupts = int(line.split()[1])
        except:
            context_switches = 0
            interrupts = 0

        # Detect thermal state
        thermal_state = self._detect_thermal_state()

        return SystemLoad(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            load_average=list(load_avg),
            processes_count=processes,
            context_switches=context_switches,
            interrupts=interrupts,
            thermal_state=thermal_state
        )

    def _detect_thermal_state(self) -> str:
        """Detect CPU thermal throttling state"""
        try:
            if platform.system() == "Linux":
                # Check thermal zones
                thermal_zones = '/sys/class/thermal/thermal_zone'
                if os.path.exists(thermal_zones):
                    zones = [z for z in os.listdir(thermal_zones) if z.startswith('thermal_zone')]
                    for zone in zones:
                        temp_file = f"{thermal_zones}/{zone}/temp"
                        if os.path.exists(temp_file):
                            with open(temp_file, 'r') as f:
                                temp_millic = int(f.read().strip())
                                temp_c = temp_millic / 1000
                                if temp_c > 90:
                                    return "critical"
                                elif temp_c > 80:
                                    return "throttling"

            # Default to normal
            return "normal"

        except Exception:
            return "unknown"

    def recommend_worker_count(
        self,
        workload_type: str = "backtest",
        memory_gb: Optional[float] = None,
        min_workers: int = 1,
        max_workers: Optional[int] = None
    ) -> int:
        """Recommend optimal worker count"""
        cpu_info = self.detect_cpu()
        system_load = self.get_system_load()

        # Base recommendation
        if workload_type == "backtest":
            # Backtest is CPU-bound, use physical cores
            recommended = cpu_info.physical_cores
        elif workload_type == "optimization":
            # Optimization can use all cores with HT
            recommended = cpu_info.logical_cores
        else:
            # Default to recommended from CPU info
            recommended = cpu_info.recommended_workers

        # Adjust based on system load
        if system_load.cpu_percent > 80:
            # Reduce workers if system is under high load
            recommended = max(min_workers, int(recommended * 0.7))
        elif system_load.cpu_percent < 30:
            # Increase workers if system is under low load
            recommended = min(cpu_info.logical_cores, int(recommended * 1.2))

        # Adjust based on memory
        if memory_gb and memory_gb > 0:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)

            if available_gb < memory_gb * 2:
                # Reduce workers if memory is tight
                recommended = max(min_workers, int(recommended * 0.8))

        # Ensure within bounds
        if max_workers:
            recommended = min(recommended, max_workers)

        recommended = max(min_workers, recommended)

        self.logger.info(
            f"Worker count recommendation: {recommended} "
            f"(CPU: {cpu_info.physical_cores}P/{cpu_info.logical_cores}L, "
            f"Load: {system_load.cpu_percent:.1f}%)"
        )

        return recommended

    def get_numa_topology(self) -> Dict[int, List[int]]:
        """Get NUMA topology (core to node mapping)"""
        topology = {}

        try:
            if platform.system() == "Linux":
                # Parse NUMA topology
                cpuinfo_path = '/sys/devices/system/node'
                if os.path.exists(cpuinfo_path):
                    for node_dir in os.listdir(cpuinfo_path):
                        if node_dir.startswith('node'):
                            node_id = int(node_dir.replace('node', ''))
                            node_cpus_file = f"{cpuinfo_path}/{node_dir}/cpulist"

                            if os.path.exists(node_cpus_file):
                                with open(node_cpus_file, 'r') as f:
                                    cpus_str = f.read().strip()
                                    # Parse CPU list (e.g., "0-7,16-23")
                                    cpus = self._parse_cpu_list(cpus_str)
                                    for cpu in cpus:
                                        if cpu not in topology:
                                            topology[cpu] = []
                                        topology[cpu].append(node_id)

        except Exception as e:
            self.logger.warning(f"Could not detect NUMA topology: {e}")

        return topology

    def _parse_cpu_list(self, cpu_list_str: str) -> List[int]:
        """Parse CPU list string (e.g., "0-7,16-23")"""
        cpus = []
        for part in cpu_list_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                cpus.extend(range(start, end + 1))
            else:
                cpus.append(int(part))
        return cpus

    def optimize_for_backtest(
        self,
        strategy_type: str = "sma",
        data_size_mb: float = 100,
        num_strategies: int = 1
    ) -> Dict[str, Any]:
        """Get optimization recommendations for backtest workload"""
        cpu_info = self.detect_cpu()
        system_load = self.get_system_load()

        # Calculate memory requirements
        memory_required_gb = (data_size_mb / 1024) * num_strategies * 2  # 2x safety margin

        # Get recommended worker count
        workers = self.recommend_worker_count(
            workload_type="backtest",
            memory_gb=memory_required_gb
        )

        # Estimate execution time
        base_time_seconds = 0.05  # 50ms per backtest (rough estimate)
        parallel_speedup = min(workers, cpu_info.physical_cores * 1.5)
        estimated_time = base_time_seconds / parallel_speedup

        recommendations = {
            'worker_count': workers,
            'memory_required_gb': memory_required_gb,
            'parallel_speedup': parallel_speedup,
            'estimated_time_per_backtest_ms': estimated_time * 1000,
            'cpu_utilization_estimate': min(100, workers / cpu_info.physical_cores * 80),
            'numa_aware': cpu_info.numa_nodes > 1,
            'hyperthreading_benefit': cpu_info.hyperthreading == HyperThreading.ENABLED,
            'strategy_specific': {
                'sma': {'optimal_threads': cpu_info.physical_cores},
                'rsi': {'optimal_threads': cpu_info.physical_cores},
                'macd': {'optimal_threads': cpu_info.physical_cores},
                'optimization': {'optimal_threads': cpu_info.logical_cores}
            }
        }

        return recommendations

    def benchmark_cpu(self) -> Dict[str, float]:
        """Simple CPU benchmark"""
        import time
        import math

        # CPU-intensive calculation
        iterations = 1000000
        start_time = time.time()

        result = 0
        for i in range(iterations):
            result += math.sqrt(i) * math.sin(i)

        end_time = time.time()
        elapsed = end_time - start_time

        # Calculate score (higher is better)
        score = iterations / elapsed

        return {
            'elapsed_seconds': elapsed,
            'iterations_per_second': score,
            'operations_per_second': score * 10  # Approximate
        }

    def print_detailed_report(self):
        """Print a detailed CPU detection report"""
        cpu_info = self.detect_cpu()
        system_load = self.get_system_load()
        numa_topology = self.get_numa_topology()

        print("\n" + "=" * 70)
        print("CPU Detection and Configuration Report")
        print("=" * 70)

        # CPU Information
        print("\n[CPU Information]")
        print(f"  Brand: {cpu_info.brand}")
        print(f"  Model: {cpu_info.model}")
        print(f"  Architecture: {cpu_info.architecture.value}")
        print(f"  Vendor: {cpu_info.vendor}")
        print(f"  Physical Cores: {cpu_info.physical_cores}")
        print(f"  Logical Cores: {cpu_info.logical_cores}")
        print(f"  Threads per Core: {cpu_info.threads_per_core:.2f}")
        print(f"  Hyper-Threading: {cpu_info.hyperthreading.value}")

        # Frequency Information
        print("\n[Frequency Information]")
        print(f"  Max Frequency: {cpu_info.max_frequency_mhz:.2f} MHz")
        print(f"  Min Frequency: {cpu_info.min_frequency_mhz:.2f} MHz")
        print(f"  Current Frequency: {cpu_info.current_frequency_mhz:.2f} MHz")

        # Cache Information
        print("\n[Cache Information]")
        print(f"  L1 Cache: {cpu_info.cache_l1_kb} KB" if cpu_info.cache_l1_kb else "  L1 Cache: N/A")
        print(f"  L2 Cache: {cpu_info.cache_l2_kb} KB" if cpu_info.cache_l2_kb else "  L2 Cache: N/A")
        print(f"  L3 Cache: {cpu_info.cache_l3_kb} KB" if cpu_info.cache_l3_kb else "  L3 Cache: N/A")

        # NUMA Information
        print("\n[NUMA Topology]")
        print(f"  NUMA Nodes: {cpu_info.numa_nodes}")
        if numa_topology:
            print("  Core to Node Mapping:")
            for core, nodes in sorted(numa_topology.items())[:8]:  # Show first 8 cores
                print(f"    Core {core}: Node {', '.join(map(str, nodes))}")
            if len(numa_topology) > 8:
                print(f"    ... and {len(numa_topology) - 8} more cores")

        # System Load
        print("\n[System Load]")
        print(f"  CPU Usage: {system_load.cpu_percent:.1f}%")
        print(f"  Memory Usage: {system_load.memory_percent:.1f}%")
        print(f"  Load Average: {', '.join(f'{x:.2f}' for x in system_load.load_average)}")
        print(f"  Process Count: {system_load.processes_count}")
        print(f"  Thermal State: {system_load.thermal_state}")

        # Worker Recommendations
        print("\n[Worker Count Recommendations]")
        backtest_workers = self.recommend_worker_count(workload_type="backtest")
        optimization_workers = self.recommend_worker_count(workload_type="optimization")
        print(f"  For Backtest: {backtest_workers} workers")
        print(f"  For Optimization: {optimization_workers} workers")
        print(f"  Max Safe Workers: {cpu_info.max_safe_workers} workers")

        # Backtest Optimization
        print("\n[Backtest Optimization]")
        backtest_opt = self.optimize_for_backtest(
            strategy_type="sma",
            data_size_mb=500,
            num_strategies=100
        )
        print(f"  Recommended Workers: {backtest_opt['worker_count']}")
        print(f"  Memory Required: {backtest_opt['memory_required_gb']:.2f} GB")
        print(f"  Parallel Speedup: {backtest_opt['parallel_speedup']:.2f}x")
        print(f"  Est. Time per Backtest: {backtest_opt['estimated_time_per_backtest_ms']:.1f} ms")
        print(f"  CPU Utilization Est.: {backtest_opt['cpu_utilization_estimate']:.1f}%")
        print(f"  NUMA Aware: {backtest_opt['numa_aware']}")
        print(f"  Hyper-Threading Benefit: {backtest_opt['hyperthreading_benefit']}")

        print("=" * 70)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create detector
    detector = CPUDetector()

    # Print detailed report
    detector.print_detailed_report()

    # Run benchmark
    print("\n[CPU Benchmark]")
    benchmark = detector.benchmark_cpu()
    print(f"  Elapsed: {benchmark['elapsed_seconds']:.4f} seconds")
    print(f"  Iterations/second: {benchmark['iterations_per_second']:.0f}")
    print(f"  Operations/second: {benchmark['operations_per_second']:.0f}")

    # Get NUMA topology
    print("\n[NUMA Topology]")
    numa = detector.get_numa_topology()
    if numa:
        print(f"  Detected {len(numa)} cores with NUMA mapping")
    else:
        print("  NUMA topology not detected (single node system)")
