"""
数据适配器模块

提供统一的数据适配器接口，支持多种数据源。
支持自动发现和注册所有可用的适配器。

Usage:
    from src.infrastructure.data_access.adapters import AdaptersRegistry

    # 自动发现适配器
    AdaptersRegistry.auto_discover()

    # 获取适配器实例
    adapter = AdaptersRegistry.get_adapter('hibor_overnight')

    # 列出所有适配器
    source_ids = AdaptersRegistry.list_source_ids()
"""

from .base_adapter import (
    BaseDataAdapter,
    NonPriceDataPoint,
    DataValidationResult,
    DataSourceCategory,
    DataQualityLevel,
    TechnicalIndicatorConfig,
)
from .adapters_registry import AdaptersRegistry, register_adapter

# 导入子模块以触发自动注册
from . import government
from . import central_bank

__all__ = [
    'BaseDataAdapter',
    'NonPriceDataPoint',
    'DataValidationResult',
    'DataSourceCategory',
    'DataQualityLevel',
    'TechnicalIndicatorConfig',
    'AdaptersRegistry',
    'register_adapter',
    'government',
    'central_bank',
]
