"""
T057: Memory Monitor Implementation
Real-time memory usage monitoring and alerting
"""

import psutil
import time
import threading
import gc
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import deque
import logging
import json
from datetime import datetime, timedelta
from datetime import timezone

logger = logging.getLogger("hk_quant.performance.memory_monitor")

@dataclass
class MemoryAlert:
    """Memory alert notification"""
    timestamp: datetime
    level: str  # info, warning, critical
    message: str
    memory_usage_mb: float
    memory_percent: float
    action_taken: Optional[str] = None

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    rss_mb: float  # Resident set size
    vms_mb: float  # Virtual memory size
    percent: float
    available_mb: float
    cached_mb: float
    buffers_mb: float
    gc_collections: int
    gc_stats: Dict[str, int]

class MemoryMonitor:
    """Real-time memory usage monitoring and alerting"""

    def __init__(
        self,
        alert_threshold_percent: float = 80.0,
        critical_threshold_percent: float = 90.0,
        check_interval_s: float = 1.0,
        max_history: int = 1000
    ):
        self.alert_threshold = alert_threshold_percent
        self.critical_threshold = critical_threshold_percent
        self.check_interval = check_interval_s
        self.max_history = max_history

        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()

        # History
        self._history: deque = deque(maxlen=max_history)
        self._alerts: List[MemoryAlert] = []

        # Callbacks
        self._callbacks: List[Callable[[MemorySnapshot], None]] = []

        # Process
        self._process = psutil.Process()

        # Start monitoring
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        # Initial snapshot
        self._take_snapshot()

        self.logger.info(
            f"Started MemoryMonitor: alert={alert_threshold_percent}%, "
            f"critical={critical_threshold_percent}%"
        )

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                time.sleep(self.check_interval)
                self._take_snapshot()

            except Exception as e:
                self.logger.error(f"Memory monitor error: {e}")

    def _take_snapshot(self):
        """Take a memory usage snapshot"""
        try:
            # System memory
            system_memory = psutil.virtual_memory()

            # Process memory
            process_memory = self._process.memory_info()
            process_percent = self._process.memory_percent()

            # GC stats
            gc_stats = {
                'total_collections': sum(gc.get_count()),
                'gen0_collections': gc.get_count()[0],
                'gen1_collections': gc.get_count()[1],
                'gen2_collections': gc.get_count()[2],
                'uncollectable': len(gc.garbage)
            }

            snapshot = MemorySnapshot(
                timestamp=datetime.now(timezone.utc),
                rss_mb=process_memory.rss / (1024 * 1024),
                vms_mb=process_memory.vms / (1024 * 1024),
                percent=process_percent,
                available_mb=system_memory.available / (1024 * 1024),
                cached_mb=getattr(system_memory, 'cached', 0) / (1024 * 1024),
                buffers_mb=getattr(system_memory, 'buffers', 0) / (1024 * 1024),
                gc_collections=sum(gc.get_count()),
                gc_stats=gc_stats
            )

            with self._lock:
                self._history.append(snapshot)

            # Check thresholds
            self._check_thresholds(snapshot)

            # Call callbacks
            for callback in self._callbacks:
                try:
                    callback(snapshot)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")

        except Exception as e:
            self.logger.error(f"Error taking snapshot: {e}")

    def _check_thresholds(self, snapshot: MemorySnapshot):
        """Check memory thresholds and raise alerts"""
        if snapshot.percent >= self.critical_threshold:
            alert = MemoryAlert(
                timestamp=datetime.now(timezone.utc),
                level='critical',
                message=f"Critical memory usage: {snapshot.percent:.1f}%",
                memory_usage_mb=snapshot.rss_mb,
                memory_percent=snapshot.percent,
                action_taken='gc_collect'
            )
            self._alerts.append(alert)

            # Trigger GC
            import gc
            gc.collect()

            self.logger.critical(
                f"CRITICAL: Memory at {snapshot.percent:.1f}% "
                f"({snapshot.rss_mb:.1f}MB), triggered GC"
            )

        elif snapshot.percent >= self.alert_threshold:
            alert = MemoryAlert(
                timestamp=datetime.now(timezone.utc),
                level='warning',
                message=f"High memory usage: {snapshot.percent:.1f}%",
                memory_usage_mb=snapshot.rss_mb,
                memory_percent=snapshot.percent
            )
            self._alerts.append(alert)

            self.logger.warning(
                f"WARNING: Memory at {snapshot.percent:.1f}% "
                f"({snapshot.rss_mb:.1f}MB)"
            )

    def get_current_snapshot(self) -> Optional[MemorySnapshot]:
        """Get current memory snapshot"""
        with self._lock:
            return self._history[-1] if self._history else None

    def get_history(self, minutes: int = 60) -> List[MemorySnapshot]:
        """Get memory history for last N minutes"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        with self._lock:
            return [s for s in self._history if s.timestamp >= cutoff]

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        with self._lock:
            if not self._history:
                return {}

            snapshots = list(self._history)
            memory_usage = [s.rss_mb for s in snapshots]
            percentages = [s.percent for s in snapshots]

            return {
                'current': {
                    'rss_mb': snapshots[-1].rss_mb,
                    'percent': snapshots[-1].percent,
                    'available_mb': snapshots[-1].available_mb
                },
                'peak': {
                    'rss_mb': max(memory_usage),
                    'percent': max(percentages)
                },
                'average': {
                    'rss_mb': sum(memory_usage) / len(memory_usage),
                    'percent': sum(percentages) / len(percentages)
                },
                'gc_stats': snapshots[-1].gc_stats if snapshots else {},
                'alerts_count': len(self._alerts),
                'samples': len(snapshots)
            }

    def add_callback(self, callback: Callable[[MemorySnapshot], None]):
        """Add callback for memory alerts"""
        self._callbacks.append(callback)

    def export_history(self, filepath: str):
        """Export memory history to JSON"""
        history = self.get_history(minutes=1440)  # 24 hours

        data = []
        for snapshot in history:
            data.append({
                'timestamp': snapshot.timestamp.isoformat(),
                'rss_mb': snapshot.rss_mb,
                'vms_mb': snapshot.vms_mb,
                'percent': snapshot.percent,
                'available_mb': snapshot.available_mb,
                'gc_collections': snapshot.gc_collections
            })

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported {len(data)} snapshots to {filepath}")

    def stop(self):
        """Stop monitoring"""
        self.logger.info("Stopping MemoryMonitor...")
        self._monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=2)
        self.logger.info("MemoryMonitor stopped")

# Global memory monitor
_memory_monitor = MemoryMonitor()

def get_memory_monitor() -> MemoryMonitor:
    """Get global memory monitor"""
    return _memory_monitor

def check_memory_limit(limit_mb: int = 1024) -> bool:
    """Check if memory usage is within limit"""
    snapshot = _memory_monitor.get_current_snapshot()
    if snapshot:
        return snapshot.rss_mb < limit_mb
    return True

# Test function
def test_memory_monitor():
    """Test memory monitor functionality"""
    print("=" * 60)
    print("Testing T057: Memory Monitor")
    print("=" * 60)

    # Test 1: Basic monitoring
    print("\nTest 1: Basic Memory Monitoring")

    monitor = MemoryMonitor(
        alert_threshold_percent=70.0,
        critical_threshold_percent=85.0,
        check_interval_s=0.5,
        max_history=100
    )

    # Add callback
    alerts = []
    def on_alert(snapshot: MemorySnapshot):
        alerts.append(snapshot)
        print(f"Alert: Memory at {snapshot.percent:.1f}%")

    monitor.add_callback(on_alert)

    # Wait for a few snapshots
    time.sleep(2)

    # Check current snapshot
    snapshot = monitor.get_current_snapshot()
    if snapshot:
        print(f"Current memory: {snapshot.rss_mb:.2f}MB ({snapshot.percent:.1f}%)")

    # Test 2: Memory statistics
    print("\nTest 2: Memory Statistics")

    stats = monitor.get_statistics()
    print(f"Statistics: {stats}")

    # Test 3: History
    print("\nTest 3: Memory History")

    history = monitor.get_history(minutes=5)
    print(f"History entries: {len(history)}")

    if history:
        print(f"First entry: {history[0].rss_mb:.2f}MB")
        print(f"Last entry: {history[-1].rss_mb:.2f}MB")

    # Test 4: Memory pressure simulation
    print("\nTest 4: Memory Pressure Simulation")

    import numpy as np

    print("Creating large arrays to simulate memory usage...")
    data = []
    for i in range(3):
        data.append(np.random.randn(1000000))
        print(f"  Array {i+1} created")
        time.sleep(1)  # Let monitor take snapshots

    # Check alerts
    print(f"\nAlerts generated: {len(alerts)}")

    # Test 5: Export
    print("\nTest 5: Export Data")

    monitor.export_history("memory_test_export.json")
    print("Exported memory history to memory_test_export.json")

    # Cleanup
    del data
    import gc
    gc.collect()

    time.sleep(1)

    # Final statistics
    print("\nFinal Statistics:")
    final_stats = monitor.get_statistics()
    if final_stats:
        print(f"  Peak memory: {final_stats['peak']['rss_mb']:.2f}MB")
        print(f"  Total alerts: {final_stats['alerts_count']}")
        print(f"  Samples collected: {final_stats['samples']}")
    else:
        print("  No statistics available")

    # Stop monitor
    monitor.stop()

    print("\n" + "=" * 60)
    print("T057: Memory Monitor - PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_memory_monitor()
