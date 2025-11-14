"""
T060f: PerformanceLogger - Performance metrics and logging for backtest operations
"""
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from .structured_logger import StructuredLogger


class PerformanceLogger:
    """Performance metrics and logging for backtest operations"""
    
    def __init__(
        self,
        component: str = "performance",
        log_dir: str = "logs",
        sample_rate: float = 1.0
    ):
        self.component = component
        self.log_dir = Path(log_dir)
        self.sample_rate = sample_rate
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create structured logger for performance logs
        self.logger = StructuredLogger(
            component=component,
            log_level="INFO",
            log_dir=str(log_dir),
            use_async=True
        )
        
        # Standard logger for fallback
        self.std_logger = logging.getLogger(f"performance.{component}")
    
    def log_backtest_performance(
        self,
        user_id: str,
        symbol: str,
        execution_time_ms: int,
        memory_usage_mb: float,
        cpu_percent: float,
        trade_count: int,
        total_return: float,
        correlation_id: str,
        **kwargs
    ):
        """Log detailed backtest performance metrics"""
        metadata = {
            "execution_time_ms": execution_time_ms,
            "memory_usage_mb": memory_usage_mb,
            "cpu_percent": cpu_percent,
            "trade_count": trade_count,
            "total_return": total_return,
            "data_points_processed": kwargs.get("data_points", 0),
            "strategy_parameters": kwargs.get("parameters", {}),
            **kwargs
        }
        
        # Calculate derived metrics
        trades_per_second = trade_count / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
        metadata["trades_per_second"] = round(trades_per_second, 2)
        
        message = f"Backtest completed: {symbol} in {execution_time_ms}ms, {trade_count} trades, {total_return}% return"
        
        # Log via structured logger
        self.logger.log_backtest_execution(
            user_id=user_id,
            symbol=symbol,
            strategy_type=kwargs.get("strategy_type", "unknown"),
            duration_ms=execution_time_ms,
            success=True,
            correlation_id=correlation_id,
            **metadata
        )
    
    def log_optimization_performance(
        self,
        user_id: str,
        combinations_tested: int,
        parallel_workers: int,
        total_time_s: float,
        best_sharpe: float,
        best_params: dict,
        correlation_id: str,
        **kwargs
    ):
        """Log parameter optimization performance"""
        metadata = {
            "combinations_tested": combinations_tested,
            "parallel_workers": parallel_workers,
            "total_time_s": total_time_s,
            "best_sharpe": best_sharpe,
            "best_parameters": best_params,
            "combinations_per_second": combinations_tested / total_time_s if total_time_s > 0 else 0,
            **kwargs
        }
        
        message = f"Optimization completed: {combinations_tested} combinations in {total_time_s}s with Sharpe {best_sharpe}"
        
        self.logger._log(
            level="INFO",
            operation="OPTIMIZATION_PERFORMANCE",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            duration_ms=total_time_s * 1000,
            metadata=metadata
        )
    
    def log_api_performance(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        correlation_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log API endpoint performance"""
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        }
        
        # Determine log level based on status code
        level = "INFO"
        if status_code >= 500:
            level = "ERROR"
        elif status_code >= 400:
            level = "WARN"
        
        message = f"API {method} {endpoint} - {status_code} in {duration_ms}ms"
        
        self.logger._log(
            level=level,
            operation="API_PERFORMANCE",
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            duration_ms=duration_ms,
            metadata=metadata
        )
    
    def log_memory_usage(
        self,
        component: str,
        allocated_mb: float,
        used_mb: float,
        gc_collections: int,
        correlation_id: Optional[str] = None,
        **kwargs
    ):
        """Log memory usage statistics"""
        metadata = {
            "component": component,
            "allocated_mb": allocated_mb,
            "used_mb": used_mb,
            "usage_percent": (used_mb / allocated_mb * 100) if allocated_mb > 0 else 0,
            "gc_collections": gc_collections,
            **kwargs
        }
        
        message = f"Memory usage for {component}: {used_mb:.2f}MB / {allocated_mb:.2f}MB ({metadata['usage_percent']:.1f}%)"
        
        self.logger._log(
            level="INFO",
            operation="MEMORY_USAGE",
            message=message,
            correlation_id=correlation_id or "system",
            metadata=metadata
        )


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(
        self,
        logger: PerformanceLogger,
        operation: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        self.logger = logger
        self.operation = operation
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.metadata = kwargs
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log"""
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        if self.operation == "backtest":
            self.logger.log_backtest_performance(
                user_id=self.user_id or "system",
                symbol=self.metadata.get("symbol", "N/A"),
                execution_time_ms=duration_ms,
                memory_usage_mb=self.metadata.get("memory_mb", 0),
                cpu_percent=self.metadata.get("cpu_percent", 0),
                trade_count=self.metadata.get("trade_count", 0),
                total_return=self.metadata.get("total_return", 0),
                correlation_id=self.correlation_id,
                **self.metadata
            )
        elif self.operation == "optimization":
            self.logger.log_optimization_performance(
                user_id=self.user_id or "system",
                combinations_tested=self.metadata.get("combinations", 0),
                parallel_workers=self.metadata.get("workers", 1),
                total_time_s=duration_ms / 1000,
                best_sharpe=self.metadata.get("best_sharpe", 0),
                best_params=self.metadata.get("best_params", {}),
                correlation_id=self.correlation_id
            )
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        if self.start_time is None:
            return 0
        current = time.time() if self.end_time is None else self.end_time
        return (current - self.start_time) * 1000
