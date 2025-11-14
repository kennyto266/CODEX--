"""
安全系統初始化模塊
自動配置和啟動安全系統
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def initialize_security_system(
    app,
    config_path: Optional[str] = None,
    auto_config: bool = True,
) -> object:
    """
    初始化安全系統

    Args:
        app: FastAPI應用實例
        config_path: 配置文件路徑
        auto_config: 是否自動生成配置

    Returns:
        安全系統實例
    """
    try:
        from .security_integration import setup_comprehensive_security, create_security_config_file

        if auto_config and not config_path:
            config_path = "config/security_config.json"
            os.makedirs("config", exist_ok=True)

            # 檢查配置文件是否存在
            if not os.path.exists(config_path):
                create_security_config_file(config_path)
                logger.info(f"Created security config at {config_path}")

        # 應用安全系統
        security_system = setup_comprehensive_security(
            app=app,
            config_path=config_path,
            enable_all=True
        )

        logger.info("✅ Security system initialized successfully")
        return security_system

    except ImportError as e:
        logger.error(f"Failed to import security modules: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize security system: {e}")
        raise


def create_default_directories():
    """創建默認目錄結構"""
    directories = [
        "config",
        "logs",
        "data/security",
        "data/security/events",
        "data/security/whitelists",
        "data/security/blacklists",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def setup_logging():
    """設置安全日誌"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/security.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 創建安全專用日誌器
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.DEBUG)
    return security_logger


def create_ip_lists():
    """創建默認IP列表文件"""
    # 白名單
    whitelist_path = Path("config/whitelist_ips.txt")
    if not whitelist_path.exists():
        with open(whitelist_path, 'w') as f:
            f.write("# IP白名單 - 這些IP不會被速率限制\n")
            f.write("# 格式: IP地址\n")
            f.write("# 例如:\n")
            f.write("# 127.0.0.1\n")
            f.write("# 192.168.1.100\n")
        logger.info(f"Created whitelist file: {whitelist_path}")

    # 黑名單
    blacklist_path = Path("config/blacklist_ips.txt")
    if not blacklist_path.exists():
        with open(blacklist_path, 'w') as f:
            f.write("# IP黑名單 - 這些IP會被自動封鎖\n")
            f.write("# 格式: IP地址\n")
            f.write("# 例如:\n")
            f.write("# 192.168.1.200\n")
            f.write("# 10.0.0.50\n")
        logger.info(f"Created blacklist file: {blacklist_path}")


def get_security_status():
    """獲取安全系統狀態"""
    return {
        "status": "initialized",
        "version": "1.0.0",
        "components": {
            "rate_limiting": True,
            "ddos_protection": True,
            "waf": True,
            "ip_reputation": True,
            "input_validation": True,
            "cors": True,
            "security_headers": True,
        },
        "config_loaded": os.path.exists("config/security_config.json"),
        "directories_created": True,
        "ip_lists_created": True,
    }
