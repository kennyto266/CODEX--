"""
System Configuration Module.

This module contains system-level configuration classes, constants,
and utility functions for the Hong Kong quantitative trading AI Agent system.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class SystemConfig(BaseSettings):
    """系統配置類

    Centralized configuration management for the entire system.
    """

    # 系統基礎配置
    app_name: str = "港股量化交易AI Agent系統"
    app_version: str = "1.0.0"
    debug: bool = False

    # 數據庫配置
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/hk_quant_db",
        env="DATABASE_URL"
    )

    # Redis配置
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # 港股數據源配置
    hk_data_source: str = Field(default="yfinance", env="HK_DATA_SOURCE")
    data_update_interval: int = Field(default=60, env="DATA_UPDATE_INTERVAL")

    # Agent配置
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    agent_heartbeat_interval: int = Field(default=30, env="AGENT_HEARTBEAT_INTERVAL")
    update_interval: int = Field(default=5, env="UPDATE_INTERVAL")

    # 交易配置
    trading_enabled: bool = Field(default=False, env="TRADING_ENABLED")
    max_position_size: float = Field(default=1000000.0, env="MAX_POSITION_SIZE")
    risk_limit: float = Field(default=0.02, env="RISK_LIMIT")

    # 日誌配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/hk_quant_system.log", env="LOG_FILE")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略額外的環境變量


class SystemConstants:
    """系統常量

    Centralized constant definitions for the system.
    """

    # Agent類型
    AGENT_TYPES = [
        "quant_analyst",      # 量化分析師
        "quant_trader",       # 量化交易員
        "portfolio_manager",  # 投資組合經理
        "risk_analyst",       # 風險分析師
        "data_scientist",     # 數據科學家
        "quant_engineer",     # 量化工程師
        "research_analyst"    # 研究分析師
    ]

    # Agent狀態
    AGENT_STATUS = {
        "IDLE": "idle",
        "RUNNING": "running",
        "STOPPED": "stopped",
        "ERROR": "error",
        "MAINTENANCE": "maintenance"
    }

    # 消息類型
    MESSAGE_TYPES = {
        "HEARTBEAT": "heartbeat",
        "CONTROL": "control",
        "DATA": "data",
        "ALERT": "alert",
        "STATUS": "status"
    }

    # 默認配置
    DEFAULT_CONFIG = {
        "max_agents": 10,
        "heartbeat_interval": 30,
        "data_update_interval": 60,
        "log_level": "INFO"
    }


def setup_logging(config: SystemConfig = None):
    """設置日誌配置

    Configures logging for the entire system.

    Args:
        config: SystemConfig instance. If None, uses default config.

    Returns:
        Logger instance for "hk_quant_system"
    """
    if config is None:
        config = SystemConfig()

    # 創建日誌目錄
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(exist_ok=True)

    # 配置日誌格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 設置日誌級別
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # 配置日誌處理器
    handlers = [
        logging.StreamHandler(),  # 控制台輸出
        logging.FileHandler(config.log_file, encoding='utf-8')  # 文件輸出
    ]

    # 應用配置
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

    return logging.getLogger("hk_quant_system")


def get_project_root() -> Path:
    """獲取項目根目錄

    Returns:
        Path to the project root directory
    """
    return Path(__file__).parent.parent.parent


def get_config_path() -> Path:
    """獲取配置文件路徑

    Returns:
        Path to the config directory
    """
    return get_project_root() / "config"


def get_logs_path() -> Path:
    """獲取日誌目錄路徑

    Returns:
        Path to the logs directory
    """
    return get_project_root() / "logs"


# 導出主要類和函數
__all__ = [
    "SystemConfig",
    "SystemConstants",
    "setup_logging",
    "get_project_root",
    "get_config_path",
    "get_logs_path"
]
