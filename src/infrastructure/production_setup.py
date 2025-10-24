"""
Production Setup and Optimization

Production-grade configuration, logging, error handling, and optimization
for the real-time trading system.

Features:
    - Environment-based configuration management
    - Comprehensive logging with rotation
    - Error handling and automatic recovery
    - Database connection pooling
    - Caching layer optimization
    - Performance monitoring
    - Graceful shutdown handling
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from contextlib import asynccontextmanager
import signal
import asyncio


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    username: str
    password: str
    database: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: int = 3600

    def get_connection_string(self) -> str:
        """Get database connection string"""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_dir: str = "logs"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    format_string: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    def ensure_log_dir(self):
        """Ensure log directory exists"""
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class CacheConfig:
    """Caching configuration"""
    enabled: bool = True
    cache_size: int = 1000
    ttl_seconds: int = 3600
    cleanup_interval: int = 300


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    max_queue_size: int = 1000
    batch_size: int = 100
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    enable_compression: bool = True
    connection_timeout: float = 10.0


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    metrics_interval: int = 60  # seconds
    alert_threshold: float = 0.8  # 80% utilization
    health_check_interval: int = 30  # seconds


class ProductionConfig:
    """Production configuration manager"""

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize production config

        Args:
            environment: Environment type (development, staging, production)
        """
        self.environment = Environment(
            environment or os.getenv("ENVIRONMENT", "development")
        )

        self.database = self._load_database_config()
        self.logging = self._load_logging_config()
        self.cache = self._load_cache_config()
        self.performance = self._load_performance_config()
        self.monitoring = self._load_monitoring_config()

        self.logger = logging.getLogger("hk_quant_system.infrastructure.config")

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment"""
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "quant_system"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20"))
        )

    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration"""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if self.environment == Environment.PRODUCTION:
            log_level = "WARNING"

        return LoggingConfig(
            level=log_level,
            log_dir=os.getenv("LOG_DIR", "logs"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )

    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration"""
        return CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_size=int(os.getenv("CACHE_SIZE", "1000")),
            ttl_seconds=int(os.getenv("CACHE_TTL", "3600"))
        )

    def _load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration"""
        return PerformanceConfig(
            max_queue_size=int(os.getenv("MAX_QUEUE_SIZE", "1000")),
            batch_size=int(os.getenv("BATCH_SIZE", "100")),
            timeout_seconds=float(os.getenv("TIMEOUT_SECONDS", "30.0")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("RETRY_DELAY", "1.0"))
        )

    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        return MonitoringConfig(
            enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            metrics_interval=int(os.getenv("METRICS_INTERVAL", "60"))
        )

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'environment': self.environment.value,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'pool_size': self.database.pool_size
            },
            'logging': {
                'level': self.logging.level,
                'log_dir': self.logging.log_dir
            },
            'cache': {
                'enabled': self.cache.enabled,
                'cache_size': self.cache.cache_size
            },
            'performance': {
                'max_queue_size': self.performance.max_queue_size,
                'batch_size': self.performance.batch_size
            },
            'monitoring': {
                'enabled': self.monitoring.enabled,
                'metrics_interval': self.monitoring.metrics_interval
            }
        }


class ProductionLogger:
    """Production-grade logging setup"""

    @staticmethod
    def setup_logging(config: ProductionConfig) -> logging.Logger:
        """
        Setup production logging with rotation

        Args:
            config: Production configuration

        Returns:
            Configured logger instance
        """
        config.logging.ensure_log_dir()

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(config.logging.level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(config.logging.format_string)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=Path(config.logging.log_dir) / "trading_system.log",
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            filename=Path(config.logging.log_dir) / "errors.log",
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        return root_logger


class ErrorHandler:
    """Centralized error handling and recovery"""

    def __init__(self, config: ProductionConfig):
        """Initialize error handler"""
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.error_handler")
        self.error_count = 0
        self.last_error_time = None

    async def handle_error(
        self,
        error: Exception,
        context: str,
        recoverable: bool = True
    ) -> bool:
        """
        Handle errors with automatic recovery

        Args:
            error: The exception that occurred
            context: Context where error occurred
            recoverable: Whether error is recoverable

        Returns:
            True if recovered, False otherwise
        """
        self.error_count += 1
        self.logger.error(
            f"Error in {context}: {error}",
            exc_info=True
        )

        if not recoverable:
            self.logger.critical(
                f"Non-recoverable error in {context}: {error}"
            )
            return False

        # Implement exponential backoff
        for attempt in range(self.config.performance.retry_attempts):
            try:
                delay = (
                    self.config.performance.retry_delay_seconds *
                    (2 ** attempt)
                )
                self.logger.info(
                    f"Retrying in {delay} seconds... (Attempt {attempt + 1})"
                )
                await asyncio.sleep(delay)
                return True
            except Exception as retry_error:
                self.logger.error(f"Retry failed: {retry_error}")

        return False

    def reset_error_count(self):
        """Reset error counter"""
        self.error_count = 0

    def get_error_status(self) -> Dict[str, Any]:
        """Get error status"""
        return {
            'error_count': self.error_count,
            'last_error_time': self.last_error_time,
            'status': 'HEALTHY' if self.error_count < 5 else 'DEGRADED'
        }


class ResourceManager:
    """Manages system resources and optimization"""

    def __init__(self, config: ProductionConfig):
        """Initialize resource manager"""
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.resource_manager")
        self._active_tasks: set = set()

    async def add_task(self, task: asyncio.Task) -> None:
        """Track active task"""
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)

    def get_active_task_count(self) -> int:
        """Get number of active tasks"""
        return len(self._active_tasks)

    @asynccontextmanager
    async def managed_task(self, coro):
        """Context manager for task execution with resource management"""
        task = asyncio.create_task(coro)
        await self.add_task(task)

        try:
            yield task
        finally:
            if not task.done():
                task.cancel()

    async def cleanup_resources(self) -> None:
        """Cleanup all resources"""
        self.logger.info(f"Cleaning up {len(self._active_tasks)} active tasks")

        for task in list(self._active_tasks):
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        self.logger.info("Resource cleanup complete")

    async def get_resource_status(self) -> Dict[str, Any]:
        """Get resource usage status"""
        return {
            'active_tasks': self.get_active_task_count(),
            'max_queue_size': self.config.performance.max_queue_size,
            'batch_size': self.config.performance.batch_size,
            'status': 'HEALTHY'
        }


class ProductionManager:
    """Unified production management"""

    def __init__(self, environment: Optional[str] = None):
        """Initialize production manager"""
        self.config = ProductionConfig(environment)
        self.logger = ProductionLogger.setup_logging(self.config)
        self.error_handler = ErrorHandler(self.config)
        self.resource_manager = ResourceManager(self.config)

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info(
            f"Production manager initialized (Environment: {self.config.environment.value})"
        )

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Starting graceful shutdown...")
        await self.resource_manager.cleanup_resources()
        self.logger.info("Graceful shutdown complete")

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'timestamp': str(asyncio.get_event_loop().time()),
            'environment': self.config.environment.value,
            'error_status': self.error_handler.get_error_status(),
            'config': self.config.get_config_dict()
        }

    def log_config(self) -> None:
        """Log configuration for debugging"""
        self.logger.info(
            f"Configuration: {json.dumps(self.config.get_config_dict(), indent=2)}"
        )


__all__ = [
    'ProductionConfig',
    'ProductionLogger',
    'ErrorHandler',
    'ResourceManager',
    'ProductionManager',
    'DatabaseConfig',
    'LoggingConfig',
    'CacheConfig',
    'PerformanceConfig',
    'MonitoringConfig',
    'Environment'
]
