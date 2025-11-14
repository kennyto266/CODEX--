"""
T060d: StructuredLogger - JSON-formatted structured logging with metadata
"""
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import psutil
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor


class AsyncLogWriter:
    """Asynchronous log writer for high-performance scenarios"""
    
    def __init__(self, log_dir: str, max_workers: int = 4):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.queue = Queue(maxsize=10000)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.shutdown = False
        self.writer_thread = threading.Thread(target=self._write_logs, daemon=True)
        self.writer_thread.start()
    
    def _write_logs(self):
        """Background thread for writing logs"""
        while not self.shutdown or not self.queue.empty():
            try:
                entry = self.queue.get(timeout=0.1)
                self._write_log_entry(entry)
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                # Fallback to console logging
                print(f"Log write error: {e}")
        
        # Write remaining entries on shutdown
        while not self.queue.empty():
            try:
                entry = self.queue.get_nowait()
                self._write_log_entry(entry)
                self.queue.task_done()
            except Empty:
                break
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write single log entry to file"""
        log_type = entry.get('type', 'general')
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        log_file = self.log_dir / f"{log_type}_{date_str}.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def async_write(self, entry: Dict[str, Any]):
        """Add entry to async write queue"""
        if not self.shutdown:
            try:
                self.queue.put_nowait(entry)
            except:
                # Queue full, write synchronously
                self._write_log_entry(entry)
    
    def shutdown_writer(self):
        """Shutdown async writer"""
        self.shutdown = True
        self.writer_thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)


class StructuredLogger:
    """JSON-formatted structured logging with metadata and correlation IDs"""
    
    def __init__(
        self,
        component: str,
        log_level: str = "INFO",
        log_dir: str = "logs",
        use_async: bool = True
    ):
        self.component = component
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.use_async = use_async
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup async writer if enabled
        self.async_writer = None
        if self.use_async:
            self.async_writer = AsyncLogWriter(str(self.log_dir))
        
        # Setup standard logger for fallback
        self.logger = logging.getLogger(f"structured.{component}")
        self.logger.setLevel(self.log_level)
        
        # Ensure no duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(self.log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": mem_info.rss / (1024 * 1024)
            }
        except Exception:
            return {
                "cpu_percent": 0.0,
                "memory_mb": 0.0
            }
    
    def _create_log_entry(
        self,
        level: str,
        operation: str,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "correlation_id": correlation_id,
            "operation": operation,
            "component": self.component,
            "message": message,
            "resource_usage": self._get_system_resources()
        }
        
        if user_id:
            entry["user_id"] = user_id
        
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        
        if metadata:
            entry["metadata"] = metadata
        
        return entry
    
    def _log(
        self,
        level: str,
        operation: str,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Internal logging method"""
        entry = self._create_log_entry(
            level, operation, message, correlation_id,
            user_id, duration_ms, metadata
        )
        
        # Also log to standard logger for debugging
        log_msg = f"{operation}: {message}"
        if user_id:
            log_msg += f" (user: {user_id})"
        
        if level == "ERROR":
            self.logger.error(log_msg)
        elif level == "WARN":
            self.logger.warning(log_msg)
        elif level == "INFO":
            self.logger.info(log_msg)
        elif level == "DEBUG":
            self.logger.debug(log_msg)
        
        # Write to structured log
        if self.use_async and self.async_writer:
            self.async_writer.async_write(entry)
        else:
            # Write synchronously
            self._write_log_entry(entry)
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write log entry to file"""
        log_type = entry.get('operation', 'general').lower()
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        log_file = self.log_dir / f"{log_type}_{date_str}.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def log_backtest_execution(
        self,
        user_id: str,
        symbol: str,
        strategy_type: str,
        duration_ms: float,
        success: bool,
        correlation_id: str,
        **kwargs
    ):
        """Log backtest execution with structured data"""
        metadata = {
            "symbol": symbol,
            "strategy_type": strategy_type,
            "success": success,
            **kwargs
        }
        
        message = f"{strategy_type} backtest {'completed successfully' if success else 'failed'}"
        if success:
            message += f" in {duration_ms:.2f}ms"
        
        self._log(
            level="INFO" if success else "ERROR",
            operation="BACKTEST_EXECUTE",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            duration_ms=duration_ms,
            metadata=metadata
        )
    
    def log_optimization_start(
        self,
        user_id: str,
        parameter_combinations: int,
        estimated_duration_s: float,
        correlation_id: str
    ):
        """Log parameter optimization start"""
        metadata = {
            "parameter_combinations": parameter_combinations,
            "estimated_duration_s": estimated_duration_s
        }
        
        message = f"Starting optimization of {parameter_combinations} parameter combinations"
        
        self._log(
            level="INFO",
            operation="OPTIMIZATION_START",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def log_trade_signal(
        self,
        symbol: str,
        date: str,
        action: str,
        price: float,
        signal_strength: float,
        correlation_id: str,
        **kwargs
    ):
        """Log trading signal generation"""
        metadata = {
            "symbol": symbol,
            "date": date,
            "action": action,
            "price": price,
            "signal_strength": signal_strength,
            **kwargs
        }
        
        message = f"Generated {action} signal for {symbol} at {price}"
        
        self._log(
            level="INFO",
            operation="TRADE_SIGNAL",
            message=message,
            correlation_id=correlation_id,
            metadata=metadata
        )
    
    def log_error(
        self,
        error: Exception,
        context: dict,
        correlation_id: str,
        user_id: Optional[str] = None
    ):
        """Log errors with full context"""
        metadata = {
            "error_type": type(error).__name__,
            "context": context
        }
        
        self._log(
            level="ERROR",
            operation="ERROR",
            message=str(error),
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def log_info(
        self,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log info message"""
        self._log(
            level="INFO",
            operation="INFO",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def log_warn(
        self,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log warning message"""
        self._log(
            level="WARN",
            operation="WARNING",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def log_debug(
        self,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log debug message"""
        self._log(
            level="DEBUG",
            operation="DEBUG",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def log_trace(
        self,
        message: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log trace message"""
        self._log(
            level="TRACE",
            operation="TRACE",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            metadata=metadata
        )
    
    def shutdown(self):
        """Shutdown async log writer"""
        if self.async_writer:
            self.async_writer.shutdown_writer()
