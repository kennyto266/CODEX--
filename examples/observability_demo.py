"""
T060: Observability System Demo
Demonstrates structured logging, correlation IDs, and performance tracking
"""
import sys
import time
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.observability import (
    StructuredLogger,
    CorrelationIdManager,
    PerformanceLogger
)
import json

def demo_basic():
    print("\n=== Observability System Demo ===\n")
    
    # 1. Create correlation ID
    corr_manager = CorrelationIdManager()
    request_id = corr_manager.generate_request_id()
    print(f"1. Generated Request ID: {request_id}")
    
    # 2. Create structured logger
    logger = StructuredLogger(
        component="backtest_engine",
        log_level="INFO",
        log_dir="logs/demo"
    )
    print("2. Created Structured Logger")
    
    # 3. Log backtest execution
    logger.log_backtest_execution(
        user_id="user_789",
        symbol="0700.HK",
        strategy_type="SMA",
        duration_ms=45.2,
        success=True,
        correlation_id=request_id,
        data_points=252
    )
    print("3. Logged backtest execution")
    
    # 4. Create performance logger
    perf_logger = PerformanceLogger(
        component="demo",
        log_dir="logs/demo"
    )
    print("4. Created Performance Logger")
    
    # 5. Log performance
    perf_logger.log_backtest_performance(
        user_id="user_789",
        symbol="0700.HK",
        execution_time_ms=1250,
        memory_usage_mb=85.3,
        cpu_percent=12.5,
        trade_count=45,
        total_return=15.7,
        correlation_id=request_id
    )
    print("5. Logged performance metrics")
    
    # 6. Cleanup
    logger.shutdown()
    print("6. Shutdown loggers")
    
    print("\nDemo completed successfully!\n")

if __name__ == "__main__":
    demo_basic()
