"""
適配器工廠
統一創建和管理所有適配器
"""

from typing import Dict, Any, Optional, Type
import logging

from .unified_base_adapter import UnifiedBaseAdapter
from .unified_stock_adapter import UnifiedStockDataAdapter
from .unified_hkex_adapter import UnifiedHKEXAdapter
from .unified_data_collector import UnifiedDataCollector

logger = logging.getLogger(__name__)

class AdapterFactory:
    """
    適配器工廠類
    統一管理所有適配器的創建和配置
    """

    # 適配器映射表
    _adapters = {
        # 股票API適配器
        'stock_alpha_vantage': UnifiedStockDataAdapter,
        'stock_yahoo': UnifiedStockDataAdapter,
        'stock_api': UnifiedStockDataAdapter,
        'fx_api': UnifiedStockDataAdapter,
        'crypto_api': UnifiedStockDataAdapter,

        # 港交所適配器
        'hkex': UnifiedHKEXAdapter,
        'hkex_realtime': UnifiedHKEXAdapter,
        'hkex_options': UnifiedHKEXAdapter,
        'hkex_futures': UnifiedHKEXAdapter,

        # 數據收集器
        'collector_gov': UnifiedDataCollector,
        'collector_hkex': UnifiedDataCollector,
        'collector_kaggle': UnifiedDataCollector,
        'collector_web': UnifiedDataCollector,

        # 統一代稱
        'stock': UnifiedStockDataAdapter,
        'hkex_data': UnifiedHKEXAdapter,
        'data_collector': UnifiedDataCollector
    }

    @classmethod
    def create_adapter(cls, adapter_type: str, config: Optional[Dict[str, Any]] = None) -> UnifiedBaseAdapter:
        """
        創建適配器實例

        Args:
            adapter_type: 適配器類型
            config: 配置參數

        Returns:
            適配器實例

        Raises:
            ValueError: 如果不支持的適配器類型
        """
        adapter_class = cls._adapters.get(adapter_type)

        if not adapter_class:
            available = cls.get_available_adapters()
            raise ValueError(
                f"Unknown adapter type: {adapter_type}\n"
                f"Available types: {', '.join(available)}"
            )

        logger.info(f"Creating adapter: {adapter_type} -> {adapter_class.__name__}")
        return adapter_class(config)

    @classmethod
    def get_available_adapters(cls) -> list:
        """獲取可用的適配器類型列表"""
        return list(cls._adapters.keys())

    @classmethod
    def get_adapter_class(cls, adapter_type: str) -> Optional[Type[UnifiedBaseAdapter]]:
        """獲取適配器類"""
        return cls._adapters.get(adapter_type)

    @classmethod
    def get_adapter_info(cls, adapter_type: str) -> Dict[str, Any]:
        """
        獲取適配器信息

        Args:
            adapter_type: 適配器類型

        Returns:
            適配器信息字典
        """
        adapter_class = cls._adapters.get(adapter_type)

        if not adapter_class:
            return {
                'type': adapter_type,
                'available': False,
                'error': 'Unknown adapter type'
            }

        # 獲取類的文檔字符串
        doc = adapter_class.__doc__ or ''
        doc = doc.strip().split('\n')[0] if doc else ''

        return {
            'type': adapter_type,
            'class_name': adapter_class.__name__,
            'module': adapter_class.__module__,
            'description': doc,
            'available': True
        }

    @classmethod
    def list_all_adapters(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有適配器信息"""
        return {
            adapter_type: cls.get_adapter_info(adapter_type)
            for adapter_type in cls.get_available_adapters()
        }

    @classmethod
    def register_adapter(cls, adapter_type: str, adapter_class: Type[UnifiedBaseAdapter]) -> None:
        """
        註冊新的適配器

        Args:
            adapter_type: 適配器類型
            adapter_class: 適配器類
        """
        if not issubclass(adapter_class, UnifiedBaseAdapter):
            raise ValueError(f"Adapter class must inherit from UnifiedBaseAdapter")

        cls._adapters[adapter_type] = adapter_class
        logger.info(f"Registered adapter: {adapter_type} -> {adapter_class.__name__}")

    @classmethod
    def get_config_template(cls, adapter_type: str) -> Dict[str, Any]:
        """
        獲取適配器配置模板

        Args:
            adapter_type: 適配器類型

        Returns:
            配置模板字典
        """
        templates = {
            'stock': {
                'alpha_vantage_key': 'YOUR_ALPHA_VANTAGE_API_KEY',
                'iex_key': 'YOUR_IEX_API_KEY',
                'finnhub_key': 'YOUR_FINNHUB_API_KEY',
                'cache_ttl': 3600,
                'timeout': 30
            },
            'hkex': {
                'hkex_base_url': 'http://18.180.162.113:9191',
                'timeout': 30,
                'retry_attempts': 3
            },
            'data_collector': {
                'output_dir': './data/collector',
                'api_timeout': 30,
                'max_retries': 3
            }
        }

        return templates.get(adapter_type, {})

# 全局適配器實例緩存
_adapter_instances = {}

def get_adapter(adapter_type: str, config: Optional[Dict[str, Any]] = None,
                use_cache: bool = True) -> UnifiedBaseAdapter:
    """
    獲取適配器實例（支持緩存）

    Args:
        adapter_type: 適配器類型
        config: 配置參數
        use_cache: 是否使用緩存

    Returns:
        適配器實例
    """
    cache_key = f"{adapter_type}_{hash(str(sorted(config.items()))) if config else 'default'}"

    if use_cache and cache_key in _adapter_instances:
        return _adapter_instances[cache_key]

    adapter = AdapterFactory.create_adapter(adapter_type, config)

    if use_cache:
        _adapter_instances[cache_key] = adapter

    return adapter

def clear_adapter_cache():
    """清除適配器實例緩存"""
    global _adapter_instances
    _adapter_instances = {}
    logger.info("Adapter cache cleared")
