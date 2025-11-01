"""
Configuration Management System
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field


class AppConfig(BaseSettings):
    """Application configuration"""
    name: str = Field(default="CODEX Trading System")
    version: str = Field(default="7.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://user:password@localhost:5432/codex_db")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)


class RedisConfig(BaseSettings):
    """Redis configuration"""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: str = Field(default="", env="REDIS_PASSWORD")
    db: int = Field(default=0)
    max_connections: int = Field(default=100)


class APIConfig(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    workers: int = Field(default=4)
    reload: bool = Field(default=False)


class DataSourcesConfig(BaseSettings):
    """Data sources configuration"""
    hkex_endpoint: str = Field(default="http://18.180.162.113:9191")
    hkex_timeout: int = Field(default=30)
    hkex_retry_attempts: int = Field(default=3)
    yahoo_timeout: int = Field(default=30)
    yahoo_rate_limit: int = Field(default=2000)


class TradingConfig(BaseSettings):
    """Trading configuration"""
    enabled: bool = Field(default=False)
    initial_capital: float = Field(default=1000000.0)
    max_position_size: float = Field(default=100000.0)
    max_portfolio_heat: float = Field(default=500000.0)
    risk_limit: float = Field(default=0.02)


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO")
    format: str = Field(default="json")


class CachingConfig(BaseSettings):
    """Caching configuration"""
    l1_size: int = Field(default=1000)
    l2_ttl: int = Field(default=300)
    l3_ttl: int = Field(default=3600)


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    health_check_interval: int = Field(default=30)


class Settings(BaseSettings):
    """Main settings class"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    data_sources: DataSourcesConfig = Field(default_factory=DataSourcesConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    caching: CachingConfig = Field(default_factory=CachingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


def load_config_from_yaml(environment: str = None) -> Dict[str, Any]:
    """Load configuration from YAML files"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")

    config_dir = Path(__file__).parent.parent.parent / "config" / "environments"

    # Load base config
    base_config_path = config_dir / "base.yaml"
    if base_config_path.exists():
        with open(base_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Load environment-specific config
    env_config_path = config_dir / f"{environment}.yaml"
    if env_config_path.exists():
        with open(env_config_path, 'r', encoding='utf-8') as f:
            env_config = yaml.safe_load(f) or {}
            # Merge configs (env overrides base)
            config.update(env_config)

    return config


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Try to load from YAML first
    environment = os.getenv("ENVIRONMENT", "development")

    try:
        yaml_config = load_config_from_yaml(environment)

        # Convert nested dict to Settings
        if yaml_config:
            return Settings(**yaml_config)
    except Exception as e:
        print(f"Warning: Could not load YAML config: {e}")

    # Fallback to environment variables and defaults
    return Settings()


def get_config() -> Dict[str, Any]:
    """Get raw configuration dictionary"""
    return load_config_from_yaml(os.getenv("ENVIRONMENT", "development"))
