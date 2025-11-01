"""
GOV 爬蟲系統 - 工具函數模塊
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加載 YAML 配置文件

    Args:
        config_path: 配置文件路徑

    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"成功加載配置文件: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"配置文件格式錯誤: {e}")
        raise


def setup_logging(log_config: Dict[str, Any]) -> logging.Logger:
    """
    設置日誌系統

    Args:
        log_config: 日誌配置字典

    Returns:
        Logger 對象
    """
    log_file = log_config.get('log_file', 'logs/crawler.log')
    log_level = log_config.get('log_level', 'INFO')
    log_format = log_config.get('log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 創建日誌目錄
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 配置日誌
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def create_directories(paths: Dict[str, str]) -> None:
    """
    創建必要的目錄結構

    Args:
        paths: 路徑字典
    """
    if isinstance(paths, dict):
        for key, path in paths.items():
            if isinstance(path, str):
                os.makedirs(path, exist_ok=True)
                logger.info(f"確保目錄存在: {path}")


def save_json(data: Any, file_path: str) -> None:
    """
    保存為 JSON 文件

    Args:
        data: 要保存的數據
        file_path: 文件路徑
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"數據已保存: {file_path}")


def load_json(file_path: str) -> Any:
    """
    從 JSON 文件加載

    Args:
        file_path: 文件路徑

    Returns:
        加載的數據
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"數據已加載: {file_path}")
    return data


def save_metadata(dataset_name: str, metadata: Dict[str, Any], base_dir: str = "data/metadata") -> None:
    """
    保存數據集元信息

    Args:
        dataset_name: 數據集名稱
        metadata: 元信息字典
        base_dir: 基礎目錄
    """
    metadata['last_updated'] = datetime.now().isoformat()
    metadata_file = os.path.join(base_dir, f"{dataset_name}_metadata.json")
    save_json(metadata, metadata_file)


def load_metadata(dataset_name: str, base_dir: str = "data/metadata") -> Optional[Dict[str, Any]]:
    """
    加載數據集元信息

    Args:
        dataset_name: 數據集名稱
        base_dir: 基礎目錄

    Returns:
        元信息字典，如果不存在則返回 None
    """
    metadata_file = os.path.join(base_dir, f"{dataset_name}_metadata.json")
    if os.path.exists(metadata_file):
        return load_json(metadata_file)
    return None


def get_file_size(file_path: str) -> str:
    """
    獲取文件大小（易讀格式）

    Args:
        file_path: 文件路徑

    Returns:
        易讀的文件大小字符串
    """
    if not os.path.exists(file_path):
        return "0 B"

    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def format_timestamp(ts: Optional[datetime] = None) -> str:
    """
    格式化時間戳

    Args:
        ts: datetime 對象，默認為當前時間

    Returns:
        格式化的時間字符串
    """
    if ts is None:
        ts = datetime.now()
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def check_internet_connection(url: str = "https://data.gov.hk") -> bool:
    """
    檢查互聯網連接

    Args:
        url: 測試 URL

    Returns:
        連接狀態
    """
    try:
        import requests
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except Exception as e:
        logger.warning(f"互聯網連接檢查失敗: {e}")
        return False


def validate_dataset_config(dataset_config: Dict[str, Any], dataset_name: str) -> bool:
    """
    驗證數據集配置

    Args:
        dataset_config: 數據集配置
        dataset_name: 數據集名稱

    Returns:
        驗證結果
    """
    required_fields = ['enabled', 'update_interval']
    for field in required_fields:
        if field not in dataset_config:
            logger.error(f"數據集 {dataset_name} 配置缺少 {field}")
            return False
    return True


class ProgressTracker:
    """進度跟蹤器"""

    def __init__(self, total: int, name: str = "進度"):
        self.total = total
        self.current = 0
        self.name = name
        self.start_time = datetime.now()

    def update(self, count: int = 1) -> None:
        """更新進度"""
        self.current += count
        progress = (self.current / self.total) * 100
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"{self.name}: {self.current}/{self.total} ({progress:.1f}%) - 已用時間: {elapsed:.1f}s")

    def finish(self) -> float:
        """完成進度跟蹤"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"{self.name} 已完成 - 總用時: {elapsed:.1f}s")
        return elapsed
