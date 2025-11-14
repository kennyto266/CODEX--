"""
Configuration management for the scraping module

Handles NLP model configuration, pipet settings, and system-wide parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field


class NLPConfig(BaseSettings):
    """Natural Language Processing configuration"""

    model_name: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        description="NLP model name for text processing"
    )

    cache_dir: Optional[str] = Field(
        default="./models",
        description="Directory for model caching"
    )

    max_sequence_length: int = Field(
        default=512,
        ge=1,
        le=1024,
        description="Maximum sequence length for tokenization"
    )

    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for accepting results"
    )

    batch_size: int = Field(
        default=16,
        ge=1,
        le=64,
        description="Batch size for processing multiple requests"
    )

    device: str = Field(
        default="auto",
        description="Device for model inference (auto, cpu, cuda)"
    )

    class Config:
        env_prefix = "NLP"


class PipetConfig(BaseSettings):
    """Pipet execution configuration"""

    default_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Default timeout for pipet execution (seconds)"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed executions"
    )

    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Delay between retry attempts (seconds)"
    )

    backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff factor for retries"
    )

    max_retry_time: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
        description="Maximum total time for retry attempts (seconds)"
    )

    output_format: str = Field(
        default="json",
        description="Default output format for scraped data"
    )

    user_agent: str = Field(
        default="pipet-nlp-interface/1.0",
        description="User agent string for HTTP requests"
    )

    class Config:
        env_prefix = "PIPET"


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration"""

    requests_per_second: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Maximum requests per second"
    )

    burst_limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum burst of requests allowed"
    )

    cooldown_period: float = Field(
        default=10.0,
        ge=1.0,
        le=300.0,
        description="Cooldown period between bursts (seconds)"
    )

    class Config:
        env_prefix = "RATE_LIMIT"


class QualityConfig(BaseSettings):
    """Data quality monitoring configuration"""

    completeness_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Minimum completeness threshold for data quality"
    )

    accuracy_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum accuracy threshold for data quality"
    )

    consistency_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Minimum consistency threshold for data quality"
    )

    timeliness_threshold_hours: float = Field(
        default=24.0,
        ge=1.0,
        le=168.0,
        description="Timeliness threshold in hours"
    )

    max_missing_data_percentage: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Maximum allowed percentage of missing data"
    )

    max_duplicate_percentage: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Maximum allowed percentage of duplicate data"
    )

    class Config:
        env_prefix = "QUALITY"


class ScrapingConfig(BaseSettings):
    """Main configuration class for scraping module"""

    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Paths
    data_dir: str = Field(
        default="./data",
        description="Directory for scraped data storage"
    )

    config_dir: str = Field(
        default="./configs",
        description="Directory for pipet configurations"
    )

    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (None for stdout only)"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Performance
    max_concurrent_executions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent scraping executions"
    )

    memory_limit_mb: int = Field(
        default=2048,
        ge=512,
        le=8192,
        description="Memory limit per execution (MB)"
    )

    # NLP sub-configuration
    nlp: NLPConfig = Field(default_factory=NLPConfig)

    # Pipet sub-configuration
    pipet: PipetConfig = Field(default_factory=PipetConfig)

    # Rate limiting sub-configuration
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    # Quality monitoring sub-configuration
    quality: QualityConfig = Field(default_factory=QualityConfig)

    class Config:
        env_prefix = "SCRAPING"
        case_sensitive = False


def load_config(config_file: Optional[str] = None) -> ScrapingConfig:
    """
    Load scraping configuration from environment variables and optional config file

    Args:
        config_file: Optional path to configuration file

    Returns:
        ScrapingConfig instance
    """
    config = ScrapingConfig()

    # Load additional configuration from file if provided
    if config_file and Path(config_file).exists():
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)

        # Update configuration with file values
        for key, value in file_config.items():
            if hasattr(config, key):
                setattr(config, key, value)

    # Ensure directories exist
    Path(config.data_dir).mkdir(parents=True, exist_ok=True)
    Path(config.config_dir).mkdir(parents=True, exist_ok=True)

    if config.nlp.cache_dir:
        Path(config.nlp.cache_dir).mkdir(parents=True, exist_ok=True)

    return config


def get_config() -> ScrapingConfig:
    """Get global configuration instance"""
    return load_config()


# Configuration singleton
_config: Optional[ScrapingConfig] = None


def init_config(config_file: Optional[str] = None) -> ScrapingConfig:
    """
    Initialize global configuration

    Args:
        config_file: Optional path to configuration file

    Returns:
        ScrapingConfig instance
    """
    global _config
    _config = load_config(config_file)
    return _config


def get_global_config() -> ScrapingConfig:
    """Get global configuration instance"""
    if _config is None:
        _config = get_config()
    return _config