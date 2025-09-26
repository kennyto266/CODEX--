"""System integration and configuration management for Hong Kong quantitative trading.

This package provides comprehensive system integration capabilities including
component orchestration, configuration management, and system lifecycle management.
"""

from .system_integration import (
    SystemIntegration,
    IntegrationConfig,
    SystemStatus,
    ComponentStatus,
    IntegrationError
)
from .config_manager import (
    ConfigManager,
    ConfigValidationError,
    EnvironmentConfig,
    DatabaseConfig,
    RedisConfig,
    LoggingConfig
)
from .component_orchestrator import (
    ComponentOrchestrator,
    ComponentType,
    ComponentInfo,
    OrchestrationPlan
)
from .system_initializer import (
    SystemInitializer,
    InitializationStep,
    InitializationStatus,
    DependencyGraph
)
from .health_monitor import (
    SystemHealthMonitor,
    HealthCheckResult,
    ComponentHealth,
    SystemHealth
)

__all__ = [
    # System integration
    'SystemIntegration',
    'IntegrationConfig',
    'SystemStatus',
    'ComponentStatus',
    'IntegrationError',
    
    # Configuration management
    'ConfigManager',
    'ConfigValidationError',
    'EnvironmentConfig',
    'DatabaseConfig',
    'RedisConfig',
    'LoggingConfig',
    
    # Component orchestration
    'ComponentOrchestrator',
    'ComponentType',
    'ComponentInfo',
    'OrchestrationPlan',
    
    # System initialization
    'SystemInitializer',
    'InitializationStep',
    'InitializationStatus',
    'DependencyGraph',
    
    # Health monitoring
    'SystemHealthMonitor',
    'HealthCheckResult',
    'ComponentHealth',
    'SystemHealth'
]
