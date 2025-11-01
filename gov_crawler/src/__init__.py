"""
GOV 爬蟲系統 - 源代碼包
"""

from .api_handler import DataGovHKAPI
from .data_processor import DataProcessor
from .storage_manager import StorageManager
from .utils import load_config, setup_logging, create_directories

__version__ = "1.0.0"
__author__ = "GOV Crawler Team"

__all__ = [
    'DataGovHKAPI',
    'DataProcessor',
    'StorageManager',
    'load_config',
    'setup_logging',
    'create_directories'
]
