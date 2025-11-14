"""
非价格数据配置管理
加载和管理数据源配置
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class DataSourceConfig(BaseModel):
    """数据源配置"""

    id: str
    name: str
    description: str
    data_source_type: str
    provider: str
    frequency: str

    # 访问配置
    access: Dict[str, Any] = Field(default_factory=dict)

    # 指标配置
    indicators: Dict[str, list] = Field(default_factory=dict)

    # 时间范围
    date_range: Dict[str, Any] = Field(default_factory=dict)

    # 质量配置
    quality: Dict[str, Any] = Field(default_factory=dict)

    # 验证规则
    validation: Dict[str, Any] = Field(default_factory=dict)


class GlobalConfig(BaseModel):
    """全局配置"""

    cache: Dict[str, Any] = Field(default_factory=dict)
    parallel: Dict[str, Any] = Field(default_factory=dict)
    retry: Dict[str, Any] = Field(default_factory=dict)
    mock_detection: Dict[str, Any] = Field(default_factory=dict)
    quality: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)


class NonPriceConfig:
    """
    非价格数据配置管理器
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 config/nonprice/data_sources.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "nonprice" / "data_sources.yaml"

        self.config_path = Path(config_path)
        self._data_sources: Dict[str, DataSourceConfig] = {}
        self._global_config: Optional[GlobalConfig] = None

        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 加载数据源配置
        for source_name, source_config in config_data.items():
            if source_name == 'global':
                continue

            self._data_sources[source_name] = DataSourceConfig(**source_config)

        # 加载全局配置
        if 'global' in config_data:
            self._global_config = GlobalConfig(**config_data['global'])

    def get_data_source_config(self, source_name: str) -> Optional[DataSourceConfig]:
        """
        获取数据源配置

        Args:
            source_name: 数据源名称

        Returns:
            DataSourceConfig or None: 数据源配置或None
        """
        return self._data_sources.get(source_name)

    def get_all_data_sources(self) -> Dict[str, DataSourceConfig]:
        """
        获取所有数据源配置

        Returns:
            Dict[str, DataSourceConfig]: 数据源配置字典
        """
        return self._data_sources.copy()

    def get_global_config(self) -> Optional[GlobalConfig]:
        """
        获取全局配置

        Returns:
            GlobalConfig or None: 全局配置或None
        """
        return self._global_config

    def get_required_indicators(self, source_name: str) -> list:
        """
        获取必需指标

        Args:
            source_name: 数据源名称

        Returns:
            list: 必需指标列表
        """
        config = self.get_data_source_config(source_name)
        if config:
            return config.indicators.get('required', [])
        return []

    def get_optional_indicators(self, source_name: str) -> list:
        """
        获取可选指标

        Args:
            source_name: 数据源名称

        Returns:
            list: 可选指标列表
        """
        config = self.get_data_source_config(source_name)
        if config:
            return config.indicators.get('optional', [])
        return []

    def get_all_indicators(self, source_name: str) -> list:
        """
        获取所有指标

        Args:
            source_name: 数据源名称

        Returns:
            list: 所有指标列表
        """
        return self.get_required_indicators(source_name) + self.get_optional_indicators(source_name)

    def get_validation_rules(self, source_name: str) -> Dict[str, Any]:
        """
        获取验证规则

        Args:
            source_name: 数据源名称

        Returns:
            Dict[str, Any]: 验证规则
        """
        config = self.get_data_source_config(source_name)
        if config:
            return config.validation
        return {}

    def is_mock_detection_enabled(self, source_name: str) -> bool:
        """
        检查是否启用模拟数据检测

        Args:
            source_name: 数据源名称

        Returns:
            bool: 是否启用
        """
        config = self.get_data_source_config(source_name)
        if config and 'mock_detection_enabled' in config.quality:
            return config.quality['mock_detection_enabled']
        return True  # 默认启用

    def get_confidence_threshold(self, source_name: str) -> float:
        """
        获取置信度阈值

        Args:
            source_name: 数据源名称

        Returns:
            float: 置信度阈值
        """
        config = self.get_data_source_config(source_name)
        if config and 'confidence_threshold' in config.quality:
            return config.quality['confidence_threshold']
        return 0.8  # 默认阈值

    def get_rate_limit(self, source_name: str) -> int:
        """
        获取API速率限制

        Args:
            source_name: 数据源名称

        Returns:
            int: 速率限制
        """
        config = self.get_data_source_config(source_name)
        if config and 'rate_limit' in config.access:
            return config.access['rate_limit']
        return 100  # 默认速率限制

    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        if self._global_config and 'cache' in self._global_config.dict():
            return self._global_config.cache
        return {'enabled': True, 'ttl': 3600, 'max_size': 1000}

    def get_parallel_config(self) -> Dict[str, Any]:
        """获取并行处理配置"""
        if self._global_config and 'parallel' in self._global_config.dict():
            return self._global_config.parallel
        return {'max_workers': 4, 'timeout': 300}

    def get_retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        if self._global_config and 'retry' in self._global_config.dict():
            return self._global_config.retry
        return {
            'max_attempts': 3,
            'backoff_factor': 2,
            'retry_on_errors': []
        }

    def get_mock_detection_config(self) -> Dict[str, Any]:
        """获取模拟数据检测配置"""
        if self._global_config and 'mock_detection' in self._global_config.dict():
            return self._global_config.mock_detection
        return {
            'enabled': True,
            'confidence_threshold': 0.5,
            'features': {}
        }

    def reload(self):
        """重新加载配置"""
        self._load_config()

    def __repr__(self) -> str:
        return (
            f"<NonPriceConfig("
            f"data_sources={len(self._data_sources)}, "
            f"global_config={self._global_config is not None}"
            f")>"
        )


# 全局配置实例
config = NonPriceConfig()
