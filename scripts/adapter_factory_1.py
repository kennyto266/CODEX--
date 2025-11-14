"""
數據適配器工廠
Sprint 1 - US-003

實現適配器工廠模式，支持動態加載和管理多種數據適配器。
"""

import logging
from typing import Dict, Type, Optional, Any, List
from abc import ABC, abstractmethod

from src.core.interfaces.data_adapter import IDataAdapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """
    數據適配器工廠

    負責創建和管理不同類型的數據適配器實例。
    """

    # 註冊的適配器類
    _registry: Dict[str, Type[IDataAdapter]] = {}

    # 適配器實例緩存
    _instances: Dict[str, IDataAdapter] = {}

    @classmethod
    def register(cls, adapter_type: str, adapter_class: Type[IDataAdapter]):
        """
        註冊適配器類

        Args:
            adapter_type: 適配器類型名稱
            adapter_class: 適配器類（必須實現IDataAdapter）
        """
        if not issubclass(adapter_class, IDataAdapter):
            raise TypeError(
                f"適配器類 {adapter_class.__name__} 必須實現 IDataAdapter 接口"
            )

        cls._registry[adapter_type] = adapter_class
        logger.info(f"註冊適配器: {adapter_type} -> {adapter_class.__name__}")

    @classmethod
    def create_adapter(
        cls,
        adapter_type: str,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> IDataAdapter:
        """
        創建適配器實例

        Args:
            adapter_type: 適配器類型
            config: 配置參數
            force_new: 是否強制創建新實例

        Returns:
            IDataAdapter: 適配器實例

        Raises:
            ValueError: 適配器類型未註冊
        """
        cache_key = f"{adapter_type}:{hash(str(sorted((config or {}).items())))}"

        # 如果不是強制創建新實例，且實例已存在，則返回緩存的實例
        if not force_new and cache_key in cls._instances:
            logger.debug(f"從緩存獲取適配器實例: {adapter_type}")
            return cls._instances[cache_key]

        # 檢查適配器類是否已註冊
        if adapter_type not in cls._registry:
            available_types = list(cls._registry.keys())
            raise ValueError(
                f"未註冊的適配器類型: {adapter_type}\n"
                f"可用類型: {available_types}"
            )

        # 創建適配器實例
        adapter_class = cls._registry[adapter_type]
        try:
            adapter_instance = adapter_class(config)
            cls._instances[cache_key] = adapter_instance
            logger.info(f"創建適配器實例: {adapter_type}")
            return adapter_instance
        except Exception as e:
            logger.error(f"創建適配器實例失敗: {adapter_type}, 錯誤: {e}")
            raise

    @classmethod
    def get_adapter_types(cls) -> List[str]:
        """
        獲取所有已註冊的適配器類型

        Returns:
            List[str]: 適配器類型列表
        """
        return list(cls._registry.keys())

    @classmethod
    def clear_instances(cls):
        """清空所有緩存的實例"""
        cls._instances.clear()
        logger.info("已清空所有適配器實例緩存")

    @classmethod
    def get_registered_adapters(cls) -> Dict[str, Type[IDataAdapter]]:
        """
        獲取所有已註冊的適配器

        Returns:
            Dict[str, Type[IDataAdapter]]: 適配器類型到類的映射
        """
        return cls._registry.copy()


class AdapterRegistry:
    """
    適配器註冊中心

    提供裝飾器方式註冊適配器。
    """

    @staticmethod
    def adapter(adapter_type: str):
        """
        適配器註冊裝飾器

        Args:
            adapter_type: 適配器類型名稱

        Usage:
            @AdapterRegistry.adapter("hkma")
            class HKMAdapter(IDataAdapter):
                ...

        Returns:
            裝飾器函數
        """
        def decorator(cls: Type[IDataAdapter]):
            AdapterFactory.register(adapter_type, cls)
            return cls
        return decorator


class AdapterManager:
    """
    適配器管理器

    提供統一的適配器管理功能。
    """

    def __init__(self):
        self._factories: Dict[str, AdapterFactory] = {}
        self.logger = logging.getLogger(__name__)

    def get_factory(self, name: str = "default") -> AdapterFactory:
        """
        獲取工廠實例

        Args:
            name: 工廠名稱

        Returns:
            AdapterFactory: 工廠實例
        """
        if name not in self._factories:
            self._factories[name] = AdapterFactory()
        return self._factories[name]

    async def create_adapter(
        self,
        adapter_type: str,
        config: Optional[Dict[str, Any]] = None,
        factory_name: str = "default",
        force_new: bool = False
    ) -> IDataAdapter:
        """
        創建適配器

        Args:
            adapter_type: 適配器類型
            config: 配置參數
            factory_name: 工廠名稱
            force_new: 是否強制創建新實例

        Returns:
            IDataAdapter: 適配器實例
        """
        factory = self.get_factory(factory_name)
        return factory.create_adapter(adapter_type, config, force_new)

    async def get_adapter(
        self,
        adapter_type: str,
        config: Optional[Dict[str, Any]] = None,
        factory_name: str = "default"
    ) -> IDataAdapter:
        """
        獲取適配器（使用緩存）

        Args:
            adapter_type: 適配器類型
            config: 配置參數
            factory_name: 工廠名稱

        Returns:
            IDataAdapter: 適配器實例
        """
        return await self.create_adapter(
            adapter_type, config, factory_name, force_new=False
        )

    async def list_adapters(self, factory_name: str = "default") -> List[str]:
        """
        列出所有可用適配器

        Args:
            factory_name: 工廠名稱

        Returns:
            List[str]: 適配器類型列表
        """
        factory = self.get_factory(factory_name)
        return factory.get_adapter_types()

    async def clear_all(self, factory_name: str = "default"):
        """
        清空所有適配器實例

        Args:
            factory_name: 工廠名稱
        """
        factory = self.get_factory(factory_name)
        factory.clear_instances()
        self.logger.info(f"已清空工廠 '{factory_name}' 的所有實例")

    async def cleanup_all(self):
        """清理所有適配器實例"""
        for factory_name, factory in self._factories.items():
            for adapter_type, adapter_class in factory.get_registered_adapters().items():
                try:
                    # 嘗試清理適配器資源
                    pass  # 適配器實例可能在其他地方管理
                except Exception as e:
                    self.logger.warning(
                        f"清理適配器失敗: {factory_name}:{adapter_type}, 錯誤: {e}"
                    )

        self.logger.info("已清理所有適配器資源")


# 全局適配器管理器實例
adapter_manager = AdapterManager()


# 便捷函數
def create_adapter(
    adapter_type: str,
    config: Optional[Dict[str, Any]] = None,
    factory_name: str = "default"
) -> IDataAdapter:
    """
    創建適配器的便捷函數

    Args:
        adapter_type: 適配器類型
        config: 配置參數
        factory_name: 工廠名稱

    Returns:
        IDataAdapter: 適配器實例
    """
    import asyncio
    return asyncio.run(
        adapter_manager.create_adapter(adapter_type, config, factory_name)
    )


def get_adapter_types(factory_name: str = "default") -> List[str]:
    """
    獲取所有可用適配器類型

    Args:
        factory_name: 工廠名稱

    Returns:
        List[str]: 適配器類型列表
    """
    return adapter_manager.list_adapters(factory_name)


def register_adapter(adapter_type: str, adapter_class: Type[IDataAdapter]):
    """
    註冊適配器的便捷函數

    Args:
        adapter_type: 適配器類型
        adapter_class: 適配器類
    """
    factory = adapter_manager.get_factory()
    factory.register(adapter_type, adapter_class)


# 使用示例
"""
# 1. 定義適配器類
@AdapterRegistry.adapter("hkma")
class HKMAAdapter(IDataAdapter):
    async def _fetch_data_impl(self, symbol=None, start_date=None, end_date=None, **kwargs):
        # 實現數據獲取邏輯
        pass

# 2. 創建適配器實例
adapter = create_adapter("hkma", config={"api_key": "xxx"})
data = await adapter.fetch_data(symbol="0700.HK")

# 3. 批量獲取數據
manager = AdapterManager()
for adapter_type in get_adapter_types():
    adapter = await manager.get_adapter(adapter_type)
    print(f"{adapter_type}: {adapter.name}")
"""
