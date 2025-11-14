"""
数据适配器注册表

提供数据适配器的自动发现、注册和管理功能。
支持动态加载和使用所有可用的数据适配器。

架构设计：
- 自动发现所有可用的数据适配器
- 按source_id注册和查找适配器
- 支持适配器的生命周期管理
- 提供适配器元数据查询功能
"""

import logging
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any, Set
from abc import ABC

from .base_adapter import BaseDataAdapter


logger = logging.getLogger(__name__)


class AdaptersRegistry:
    """
    数据适配器注册表

    管理所有可用的数据适配器，提供自动发现和注册功能。
    """

    # 已注册的适配器类映射 {source_id: AdapterClass}
    _adapters: Dict[str, Type[BaseDataAdapter]] = {}

    # 适配器元数据映射 {source_id: metadata}
    _metadata: Dict[str, Dict[str, Any]] = {}

    # 已扫描的模块集合
    _scanned_modules: Set[str] = set()

    @classmethod
    def register(
        cls,
        adapter_class: Type[BaseDataAdapter],
        source_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        注册适配器类

        Args:
            adapter_class: 适配器类
            source_id: 数据源ID（如果为None则从类中提取）
            metadata: 适配器元数据

        Raises:
            TypeError: 如果adapter_class不是BaseDataAdapter的子类
        """
        if not issubclass(adapter_class, BaseDataAdapter):
            raise TypeError(
                f"适配器类必须继承自BaseDataAdapter，但得到的是 {adapter_class}"
            )

        # 提取source_id
        if source_id is None:
            # 尝试从类属性获取
            if hasattr(adapter_class, 'source_id'):
                source_id = adapter_class.source_id
            else:
                # 从类名提取
                class_name = adapter_class.__name__
                if class_name.endswith('Adapter'):
                    source_id = class_name[:-6].lower()  # 移除'Adapter'后缀
                else:
                    source_id = class_name.lower()

        if not source_id:
            raise ValueError(f"无法确定适配器 {adapter_class} 的source_id")

        # 注册适配器
        cls._adapters[source_id] = adapter_class

        # 存储元数据
        if metadata:
            cls._metadata[source_id] = metadata
        else:
            # 自动生成元数据
            cls._metadata[source_id] = {
                'source_id': source_id,
                'class_name': adapter_class.__name__,
                'module': adapter_class.__module__,
                'doc': adapter_class.__doc__ or '',
            }

        logger.info(f"注册适配器: {source_id} -> {adapter_class.__name__}")

    @classmethod
    def unregister(cls, source_id: str) -> bool:
        """
        注销适配器

        Args:
            source_id: 数据源ID

        Returns:
            bool: 是否成功注销
        """
        if source_id in cls._adapters:
            del cls._adapters[source_id]
            if source_id in cls._metadata:
                del cls._metadata[source_id]
            logger.info(f"注销适配器: {source_id}")
            return True
        return False

    @classmethod
    def get_adapter_class(cls, source_id: str) -> Optional[Type[BaseDataAdapter]]:
        """
        获取适配器类

        Args:
            source_id: 数据源ID

        Returns:
            Optional[Type[BaseDataAdapter]]: 适配器类，如果未找到则返回None
        """
        return cls._adapters.get(source_id)

    @classmethod
    def get_adapter(
        cls,
        source_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseDataAdapter]:
        """
        获取适配器实例

        Args:
            source_id: 数据源ID
            config: 配置参数

        Returns:
            Optional[BaseDataAdapter]: 适配器实例，如果未找到则返回None

        Raises:
            Exception: 适配器实例化失败
        """
        adapter_class = cls.get_adapter_class(source_id)
        if adapter_class is None:
            return None

        try:
            return adapter_class(config)
        except Exception as e:
            logger.error(f"实例化适配器 {source_id} 失败: {str(e)}")
            raise

    @classmethod
    def list_adapters(cls) -> List[Dict[str, Any]]:
        """
        列出所有注册的适配器

        Returns:
            List[Dict[str, Any]]: 适配器信息列表
        """
        result = []
        for source_id, metadata in cls._metadata.items():
            result.append({
                'source_id': source_id,
                'class_name': metadata.get('class_name'),
                'module': metadata.get('module'),
                'doc': metadata.get('doc', '')[:100],  # 截取前100字符
            })
        return sorted(result, key=lambda x: x['source_id'])

    @classmethod
    def list_source_ids(cls) -> List[str]:
        """
        列出所有已注册的数据源ID

        Returns:
            List[str]: 数据源ID列表
        """
        return sorted(cls._adapters.keys())

    @classmethod
    def get_metadata(cls, source_id: str) -> Optional[Dict[str, Any]]:
        """
        获取适配器元数据

        Args:
            source_id: 数据源ID

        Returns:
            Optional[Dict[str, Any]]: 元数据，如果未找到则返回None
        """
        return cls._metadata.get(source_id)

    @classmethod
    def has_adapter(cls, source_id: str) -> bool:
        """
        检查是否已注册指定数据源的适配器

        Args:
            source_id: 数据源ID

        Returns:
            bool: 是否已注册
        """
        return source_id in cls._adapters

    @classmethod
    def auto_discover(
        cls,
        modules: Optional[List[str]] = None,
        force_rescan: bool = False
    ) -> None:
        """
        自动发现适配器

        Args:
            modules: 要扫描的模块列表（默认扫描预定义模块）
            force_rescan: 是否强制重新扫描
        """
        if modules is None:
            # 默认扫描的模块列表
            modules = [
                'src.infrastructure.data_access.adapters.government',
                'src.infrastructure.data_access.adapters.central_bank',
            ]

        # 检查是否已经扫描过
        if not force_rescan and all(m in cls._scanned_modules for m in modules):
            logger.debug("模块已扫描，跳过自动发现")
            return

        logger.info(f"开始自动发现适配器，扫描模块: {modules}")

        for module_name in modules:
            if not force_rescan and module_name in cls._scanned_modules:
                continue

            try:
                cls._scan_module(module_name)
                cls._scanned_modules.add(module_name)
                logger.debug(f"模块扫描完成: {module_name}")
            except ModuleNotFoundError as e:
                logger.warning(f"模块不存在，跳过: {module_name} - {str(e)}")
            except Exception as e:
                logger.error(f"扫描模块失败: {module_name} - {str(e)}")

        logger.info(
            f"自动发现完成，共发现 {len(cls._adapters)} 个适配器"
        )

    @classmethod
    def _scan_module(cls, module_name: str) -> None:
        """
        扫描单个模块以查找适配器

        Args:
            module_name: 模块名称
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            logger.warning(f"无法导入模块 {module_name}: {str(e)}")
            return

        # 遍历模块中的所有类
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 跳过导入的类和ABC类
            if obj.__module__ != module_name:
                continue
            if inspect.isabstract(obj):
                continue

            # 检查是否继承自BaseDataAdapter
            if issubclass(obj, BaseDataAdapter) and obj != BaseDataAdapter:
                try:
                    cls.register(obj)
                except Exception as e:
                    logger.error(f"注册适配器失败: {name} - {str(e)}")

    @classmethod
    def scan_package(cls, package_path: str) -> None:
        """
        扫描包以查找所有适配器

        Args:
            package_path: 包路径（相对路径）
        """
        import os
        import glob

        # 查找所有Python文件
        pattern = os.path.join(package_path, '**/*.py')
        files = glob.glob(pattern, recursive=True)

        # 提取模块名
        modules = []
        for file in files:
            # 转换为模块路径
            rel_path = os.path.relpath(file, package_path)
            module_name = rel_path.replace(os.path.sep, '.').replace('.py', '')

            # 跳过__init__.py
            if '__init__' in module_name:
                continue

            full_module_name = f"{package_path.replace(os.path.sep, '.')}.{module_name}"
            modules.append(full_module_name)

        # 扫描模块
        cls.auto_discover(modules, force_rescan=True)

    @classmethod
    def clear(cls) -> None:
        """清空所有注册信息"""
        cls._adapters.clear()
        cls._metadata.clear()
        cls._scanned_modules.clear()
        logger.info("注册表已清空")

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_adapters': len(cls._adapters),
            'source_ids': list(cls._adapters.keys()),
            'scanned_modules': list(cls._scanned_modules),
            'by_category': cls._group_by_category(),
        }

    @classmethod
    def _group_by_category(cls) -> Dict[str, List[str]]:
        """
        按类别分组适配器

        Returns:
            Dict[str, List[str]]: 类别到source_id列表的映射
        """
        result = {}
        for source_id in cls._adapters.keys():
            metadata = cls.get_metadata(source_id)
            if metadata and 'category' in metadata:
                category = metadata['category']
                if category not in result:
                    result[category] = []
                result[category].append(source_id)
            else:
                if 'unknown' not in result:
                    result['unknown'] = []
                result['unknown'].append(source_id)
        return result


# 自动发现的装饰器
def register_adapter(source_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    适配器注册装饰器

    使用此装饰器装饰适配器类以自动注册。

    Args:
        source_id: 数据源ID
        metadata: 元数据

    Examples:
        @register_adapter(source_id='custom_data')
        class CustomDataAdapter(BaseDataAdapter):
            pass
    """
    def decorator(cls: Type[BaseDataAdapter]) -> Type[BaseDataAdapter]:
        AdaptersRegistry.register(cls, source_id, metadata)
        return cls
    return decorator


# 初始化时自动发现适配器
def _initialize_registry():
    """初始化注册表并自动发现适配器"""
    AdaptersRegistry.auto_discover()


# 在模块导入时自动初始化
_initialize_registry()
