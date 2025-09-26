"""
港股量化交易 AI Agent 系统核心模块

这个模块包含了系统的核心功能，包括：
- 配置管理
- 日志系统
- 基础工具类
- 系统常量
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
    """系统配置类"""
    
    # 系统基础配置
    app_name: str = "港股量化交易AI Agent系统"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/hk_quant_db",
        env="DATABASE_URL"
    )
    
    # Redis配置
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # 港股数据源配置
    hk_data_source: str = Field(default="yfinance", env="HK_DATA_SOURCE")
    data_update_interval: int = Field(default=60, env="DATA_UPDATE_INTERVAL")
    
    # Agent配置
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    agent_heartbeat_interval: int = Field(default=30, env="AGENT_HEARTBEAT_INTERVAL")
    
    # 交易配置
    trading_enabled: bool = Field(default=False, env="TRADING_ENABLED")
    max_position_size: float = Field(default=1000000.0, env="MAX_POSITION_SIZE")
    risk_limit: float = Field(default=0.02, env="RISK_LIMIT")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/hk_quant_system.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class Logger:
    """系统日志管理器"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """设置日志系统"""
        config = SystemConfig()
        
        # 创建日志目录
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # 配置日志处理器
        handlers = [
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
        
        # 设置日志级别
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        
        # 配置根日志器
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers
        )
        
        self._logger = logging.getLogger("hk_quant_system")
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取日志器"""
        if name:
            return logging.getLogger(f"hk_quant_system.{name}")
        return self._logger


# 系统常量
class SystemConstants:
    """系统常量定义"""
    
    # 港股市场常量
    HK_MARKET_TIMEZONE = "Asia/Hong_Kong"
    HK_TRADING_HOURS = {
        "morning": {"start": "09:30", "end": "12:00"},
        "afternoon": {"start": "13:00", "end": "16:00"}
    }
    
    # Agent状态
    AGENT_STATUS = {
        "IDLE": "idle",
        "RUNNING": "running", 
        "ERROR": "error",
        "STOPPED": "stopped"
    }
    
    # 交易信号类型
    SIGNAL_TYPES = {
        "BUY": "buy",
        "SELL": "sell",
        "HOLD": "hold"
    }
    
    # 风险指标
    RISK_METRICS = {
        "VAR_95": "var_95",
        "VAR_99": "var_99",
        "SHARPE_RATIO": "sharpe_ratio",
        "MAX_DRAWDOWN": "max_drawdown"
    }
    
    # 消息类型
    MESSAGE_TYPES = {
        "SIGNAL": "signal",
        "DATA": "data",
        "CONTROL": "control",
        "HEARTBEAT": "heartbeat"
    }


# 全局配置实例
config = SystemConfig()
logger = Logger()

# 导出主要组件
__all__ = [
    "SystemConfig",
    "Logger", 
    "SystemConstants",
    "config",
    "logger"
]
