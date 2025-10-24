"""
Phase 5: Production Setup Tests

Comprehensive test suite for production infrastructure:
- Configuration management
- Logging system
- Error handling and recovery
- Resource management
- Production manager integration
"""

import pytest
import asyncio
import os
import logging
from unittest.mock import patch, MagicMock, AsyncMock

from src.infrastructure.production_setup import (
    ProductionConfig,
    ProductionLogger,
    ErrorHandler,
    ResourceManager,
    ProductionManager,
    DatabaseConfig,
    Environment
)


# ==================== Configuration Tests ====================

class TestProductionConfig:
    """Test configuration management"""

    def test_config_initialization(self):
        """Test configuration initialization"""
        config = ProductionConfig("development")

        assert config.environment == Environment.DEVELOPMENT
        assert config.database is not None
        assert config.logging is not None
        assert config.cache is not None
        assert config.performance is not None

    def test_config_from_environment(self):
        """Test loading config from environment variables"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'LOG_LEVEL': 'ERROR',
            'DB_HOST': 'prod-db.example.com'
        }):
            config = ProductionConfig()

            assert config.environment == Environment.PRODUCTION
            # Production environment overrides log level to WARNING
            assert config.logging.level == 'WARNING'
            assert config.database.host == 'prod-db.example.com'

    def test_config_defaults(self):
        """Test default configuration values"""
        config = ProductionConfig("development")

        assert config.cache.cache_size == 1000
        assert config.performance.retry_attempts == 3
        assert config.database.pool_size == 10

    def test_config_dict(self):
        """Test getting config as dictionary"""
        config = ProductionConfig("staging")
        config_dict = config.get_config_dict()

        assert config_dict['environment'] == 'staging'
        assert 'database' in config_dict
        assert 'logging' in config_dict
        assert 'cache' in config_dict
        assert 'performance' in config_dict


class TestDatabaseConfig:
    """Test database configuration"""

    def test_database_config_initialization(self):
        """Test database config creation"""
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            username="user",
            password="pass",
            database="testdb"
        )

        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.pool_size == 10

    def test_connection_string(self):
        """Test connection string generation"""
        db_config = DatabaseConfig(
            host="db.example.com",
            port=5432,
            username="admin",
            password="secret",
            database="trading"
        )

        conn_str = db_config.get_connection_string()
        assert "admin:secret" in conn_str
        assert "db.example.com" in conn_str
        assert "trading" in conn_str


# ==================== Logging Tests ====================

class TestProductionLogger:
    """Test logging setup"""

    def test_setup_logging(self, tmp_path):
        """Test logging configuration"""
        config = ProductionConfig("development")
        config.logging.log_dir = str(tmp_path)

        logger = ProductionLogger.setup_logging(config)

        assert logger is not None
        assert logger.level == logging.INFO

    def test_log_directory_creation(self, tmp_path):
        """Test log directory is created"""
        config = ProductionConfig("development")
        config.logging.log_dir = str(tmp_path / "logs")

        ProductionLogger.setup_logging(config)

        assert (tmp_path / "logs").exists()

    def test_rotating_file_handler(self, tmp_path):
        """Test rotating file handler setup"""
        config = ProductionConfig("development")
        config.logging.log_dir = str(tmp_path)

        logger = ProductionLogger.setup_logging(config)
        logger.info("Test message")

        log_file = tmp_path / "trading_system.log"
        assert log_file.exists()


# ==================== Error Handler Tests ====================

class TestErrorHandler:
    """Test error handling system"""

    def test_error_handler_initialization(self):
        """Test error handler creation"""
        config = ProductionConfig("development")
        handler = ErrorHandler(config)

        assert handler.error_count == 0
        assert handler.config == config

    @pytest.mark.asyncio
    async def test_handle_recoverable_error(self):
        """Test handling recoverable errors"""
        config = ProductionConfig("development")
        config.performance.retry_attempts = 1
        config.performance.retry_delay_seconds = 0.1

        handler = ErrorHandler(config)
        error = ValueError("Test error")

        result = await handler.handle_error(error, "test_context", recoverable=True)

        assert handler.error_count == 1
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_non_recoverable_error(self):
        """Test handling non-recoverable errors"""
        config = ProductionConfig("development")
        handler = ErrorHandler(config)
        error = Exception("Critical error")

        result = await handler.handle_error(error, "test_context", recoverable=False)

        assert handler.error_count == 1
        assert result is False

    def test_error_status(self):
        """Test error status reporting"""
        config = ProductionConfig("development")
        handler = ErrorHandler(config)

        status = handler.get_error_status()

        assert status['error_count'] == 0
        assert status['status'] == 'HEALTHY'

    def test_error_count_reset(self):
        """Test error count reset"""
        config = ProductionConfig("development")
        handler = ErrorHandler(config)

        handler.error_count = 10
        handler.reset_error_count()

        assert handler.error_count == 0


# ==================== Resource Manager Tests ====================

class TestResourceManager:
    """Test resource management"""

    def test_resource_manager_initialization(self):
        """Test resource manager creation"""
        config = ProductionConfig("development")
        manager = ResourceManager(config)

        assert manager.get_active_task_count() == 0
        assert manager.config == config

    @pytest.mark.asyncio
    async def test_add_task(self):
        """Test adding task for tracking"""
        config = ProductionConfig("development")
        manager = ResourceManager(config)

        async def dummy_coro():
            await asyncio.sleep(0.01)
            return "done"

        task = asyncio.create_task(dummy_coro())
        await manager.add_task(task)

        assert manager.get_active_task_count() == 1

        await task
        await asyncio.sleep(0.01)  # Let callback execute

    @pytest.mark.asyncio
    async def test_managed_task(self):
        """Test managed task context manager"""
        config = ProductionConfig("development")
        manager = ResourceManager(config)

        async def dummy_coro():
            await asyncio.sleep(0.01)
            return "done"

        async with manager.managed_task(dummy_coro()) as task:
            assert task is not None

    @pytest.mark.asyncio
    async def test_cleanup_resources(self):
        """Test resource cleanup"""
        config = ProductionConfig("development")
        manager = ResourceManager(config)

        async def dummy_coro():
            await asyncio.sleep(1.0)

        task = asyncio.create_task(dummy_coro())
        await manager.add_task(task)

        assert manager.get_active_task_count() == 1

        await manager.cleanup_resources()

        assert manager.get_active_task_count() == 0

    @pytest.mark.asyncio
    async def test_resource_status(self):
        """Test resource status reporting"""
        config = ProductionConfig("development")
        manager = ResourceManager(config)

        status = await manager.get_resource_status()

        assert 'active_tasks' in status
        assert 'max_queue_size' in status
        assert status['status'] == 'HEALTHY'


# ==================== Production Manager Tests ====================

class TestProductionManager:
    """Test unified production manager"""

    def test_production_manager_initialization(self, tmp_path):
        """Test production manager creation"""
        with patch.dict(os.environ, {'LOG_DIR': str(tmp_path)}):
            manager = ProductionManager("development")

            assert manager.config is not None
            assert manager.error_handler is not None
            assert manager.resource_manager is not None

    def test_production_manager_config(self):
        """Test manager configuration access"""
        manager = ProductionManager("staging")

        assert manager.config.environment == Environment.STAGING

    def test_system_status(self):
        """Test system status reporting"""
        manager = ProductionManager("development")

        status = manager.get_system_status()

        assert 'timestamp' in status
        assert status['environment'] == 'development'
        assert 'error_status' in status
        assert 'config' in status

    def test_log_config(self, tmp_path):
        """Test configuration logging"""
        with patch.dict(os.environ, {'LOG_DIR': str(tmp_path)}):
            manager = ProductionManager("development")

            # Just verify the method runs without error
            manager.log_config()

            # Verify config can be retrieved
            config_dict = manager.config.get_config_dict()
            assert config_dict['environment'] == 'development'

    @pytest.mark.asyncio
    async def test_shutdown(self, tmp_path):
        """Test graceful shutdown"""
        with patch.dict(os.environ, {'LOG_DIR': str(tmp_path)}):
            manager = ProductionManager("development")

            async def dummy_task():
                await asyncio.sleep(0.1)

            task = asyncio.create_task(dummy_task())
            await manager.resource_manager.add_task(task)

            await manager.shutdown()

            assert manager.resource_manager.get_active_task_count() == 0


# ==================== Integration Tests ====================

class TestProductionIntegration:
    """Integration tests for production setup"""

    @pytest.mark.asyncio
    async def test_full_production_setup(self, tmp_path):
        """Test complete production setup"""
        with patch.dict(os.environ, {'LOG_DIR': str(tmp_path), 'ENVIRONMENT': 'production'}):
            manager = ProductionManager()

            # Verify components
            assert manager.config.environment == Environment.PRODUCTION
            assert manager.error_handler.error_count == 0
            assert manager.resource_manager.get_active_task_count() == 0

            # Test error handling
            error = RuntimeError("Test error")
            result = await manager.error_handler.handle_error(
                error, "integration_test", recoverable=True
            )

            assert manager.error_handler.error_count == 1
            assert result is True

    @pytest.mark.asyncio
    async def test_production_under_load(self, tmp_path):
        """Test production setup under load"""
        with patch.dict(os.environ, {'LOG_DIR': str(tmp_path)}):
            manager = ProductionManager("production")

            async def simulate_work():
                await asyncio.sleep(0.01)
                return "done"

            # Create multiple tasks
            tasks = [
                asyncio.create_task(simulate_work())
                for _ in range(10)
            ]

            for task in tasks:
                await manager.resource_manager.add_task(task)

            assert manager.resource_manager.get_active_task_count() == 10

            # Wait for all tasks
            await asyncio.gather(*tasks)

            # Cleanup
            await manager.shutdown()

            assert manager.resource_manager.get_active_task_count() == 0

    def test_environment_specific_config(self):
        """Test environment-specific configurations"""
        # Development config
        dev_manager = ProductionManager("development")
        assert dev_manager.config.logging.level == "INFO"

        # Production config
        prod_manager = ProductionManager("production")
        assert prod_manager.config.logging.level == "WARNING"
