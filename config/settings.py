"""
系统配置
"""

import os
from typing import Dict, Any

class Settings:
    """系统设置"""
    
    # API配置
    CURSOR_API_KEY: str = os.getenv("CURSOR_API_KEY", "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a")
    CURSOR_BASE_URL: str = "https://api.cursor.com/v0"
    
    # 股票数据API配置
    STOCK_API_BASE_URL: str = "http://18.180.162.113:9191"
    STOCK_DATA_DURATION: int = 1825  # 默认5年数据
    
    # Dashboard配置
    DASHBOARD_PORT: int = 8080
    DASHBOARD_HOST: str = "localhost"
    
    # 代理配置
    AGENT_TIMEOUT: int = 30  # 代理超时时间（秒）
    AGENT_RETRY_COUNT: int = 3  # 代理重试次数
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 系统配置
    MAX_CONCURRENT_AGENTS: int = 7
    DATA_CACHE_TTL: int = 300  # 数据缓存时间（秒）
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            "cursor_api_key": cls.CURSOR_API_KEY,
            "cursor_base_url": cls.CURSOR_BASE_URL,
            "stock_api_base_url": cls.STOCK_API_BASE_URL,
            "stock_data_duration": cls.STOCK_DATA_DURATION,
            "dashboard_port": cls.DASHBOARD_PORT,
            "dashboard_host": cls.DASHBOARD_HOST,
            "agent_timeout": cls.AGENT_TIMEOUT,
            "agent_retry_count": cls.AGENT_RETRY_COUNT,
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "max_concurrent_agents": cls.MAX_CONCURRENT_AGENTS,
            "data_cache_ttl": cls.DATA_CACHE_TTL,
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置"""
        if not cls.CURSOR_API_KEY:
            return False
        
        if cls.DASHBOARD_PORT < 1024 or cls.DASHBOARD_PORT > 65535:
            return False
        
        if cls.AGENT_TIMEOUT <= 0:
            return False
        
        return True

# 全局配置实例
settings = Settings()
