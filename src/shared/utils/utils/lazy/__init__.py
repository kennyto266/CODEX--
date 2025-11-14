"""
Phase 4 性能優化工具 - 懶加載模組
"""

from .lazy_loader import (
    LazyLoader,
    lazy_import,
    lazy_property,
    ResourceLoader,
    ModelLoader,
    DatabaseConnector,
    measure_import_time
)

__all__ = [
    'LazyLoader',
    'lazy_import',
    'lazy_property',
    'ResourceLoader',
    'ModelLoader',
    'DatabaseConnector',
    'measure_import_time'
]
