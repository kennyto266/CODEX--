"""
利率数据适配器工厂
统一管理所有利率数据适配器 (FED, PBOC, SIBOR, HKMA)

提供统一的接口创建和使用各种利率数据适配器，
支持智能回退和模拟数据模式。

Author: Phase 2 Development
Date: 2025-11-12
"""

import logging
from enum import Enum
from typing import Dict, Optional, Type, Union, List
import asyncio

from .fed_adapter import FedAdapter
from .pboc_adapter import PBOCAdapter
from .sibor_adapter import SIBORAdapter
from .hkma_hibor import HKMAHibiorAdapter
from .unified_rate_adapter import BaseRateAdapter, RateIndicator, RateDataPoint

logger = logging.getLogger(__name__)


class RateDataSource(str, Enum):
    """利率数据源枚举"""
    FED = "fed"
    PBOC = "pboc"
    SIBOR = "sibor"
    HKMA = "hkma"  # 香港金管局HIBOR


class RateAdapterFactory:
    """利率数据适配器工厂"""

    # 适配器映射
    ADAPTER_REGISTRY: Dict[RateDataSource, Type[BaseRateAdapter]] = {
        RateDataSource.FED: FedAdapter,
        RateDataSource.PBOC: PBOCAdapter,
        RateDataSource.SIBOR: SIBORAdapter,
        RateDataSource.HKMA: HKMAHibiorAdapter  # 需要适配
    }

    # 数据源支持的指标（只使用已定义的枚举值）
    SUPPORTED_INDICATORS: Dict[RateDataSource, List[RateIndicator]] = {
        RateDataSource.FED: [
            RateIndicator.FED_FUNDS,
            RateIndicator.DISCOUNT_RATE,
            RateIndicator.TREASURY_10Y,
        ],
        RateDataSource.PBOC: [
            RateIndicator.ONE_MONTH,
            RateIndicator.THREE_MONTHS,
            RateIndicator.SIX_MONTHS,
        ],
        RateDataSource.SIBOR: [
            RateIndicator.OVERNIGHT,
            RateIndicator.ONE_MONTH,
            RateIndicator.THREE_MONTHS,
        ],
        RateDataSource.HKMA: [
            RateIndicator.OVERNIGHT,
            RateIndicator.ONE_MONTH,
            RateIndicator.THREE_MONTHS,
        ]
    }

    @classmethod
    def create_adapter(
        cls,
        source: RateDataSource,
        config: Optional[Dict] = None
    ) -> BaseRateAdapter:
        """
        创建指定数据源的适配器

        Args:
            source: 数据源类型
            config: 配置字典

        Returns:
            适配器实例

        Raises:
            ValueError: 不支持的数据源
        """
        if source not in cls.ADAPTER_REGISTRY:
            raise ValueError(
                f"不支持的数据源: {source}. "
                f"支持的数据源: {list(cls.ADAPTER_REGISTRY.keys())}"
            )

        adapter_class = cls.ADAPTER_REGISTRY[source]
        logger.info(f"创建{source.value}适配器")
        return adapter_class(config)

    @classmethod
    def get_supported_indicators(
        cls,
        source: RateDataSource
    ) -> List[RateIndicator]:
        """
        获取指定数据源支持的指标

        Args:
            source: 数据源类型

        Returns:
            支持的指标列表
        """
        return cls.SUPPORTED_INDICATORS.get(source, [])

    @classmethod
    def is_indicator_supported(
        cls,
        source: RateDataSource,
        indicator: RateIndicator
    ) -> bool:
        """
        检查数据源是否支持指定指标

        Args:
            source: 数据源类型
            indicator: 利率指标

        Returns:
            是否支持
        """
        supported = cls.get_supported_indicators(source)
        return indicator in supported

    @classmethod
    def find_best_data_source(
        cls,
        indicator: RateIndicator
    ) -> Optional[RateDataSource]:
        """
        为指定指标找到最佳数据源

        Args:
            indicator: 利率指标

        Returns:
            最佳数据源或None
        """
        for source in cls.SUPPORTED_INDICATORS.keys():
            if cls.is_indicator_supported(source, indicator):
                logger.debug(f"指标{indicator}的最佳数据源: {source.value}")
                return source

        logger.warning(f"未找到支持指标{indicator}的数据源")
        return None

    @classmethod
    async def fetch_latest_rate_from_best_source(
        cls,
        indicator: RateIndicator,
        config: Optional[Dict] = None,
        use_mock: bool = True
    ) -> Optional[RateDataPoint]:
        """
        从最佳数据源获取最新利率

        Args:
            indicator: 利率指标
            config: 配置字典
            use_mock: 是否使用模拟数据

        Returns:
            利率数据点或None
        """
        best_source = cls.find_best_data_source(indicator)

        if not best_source:
            logger.error(f"未找到支持{indicator}的数据源")
            return None

        config = config or {}
        config['use_mock_data'] = use_mock

        try:
            adapter = cls.create_adapter(best_source, config)
            async with adapter:
                return await adapter.fetch_latest_rate(indicator)
        except Exception as e:
            logger.error(f"从{best_source.value}获取{indicator}失败: {e}")
            return None

    @classmethod
    async def fetch_rates_from_multiple_sources(
        cls,
        indicators: List[RateIndicator],
        config: Optional[Dict] = None,
        use_mock: bool = True
    ) -> Dict[RateIndicator, Dict[str, Optional[RateDataPoint]]]:
        """
        从多个数据源获取利率数据

        Args:
            indicators: 指标列表
            config: 配置字典
            use_mock: 是否使用模拟数据

        Returns:
            各指标从各数据源获取的利率数据
        """
        logger.info(f"从多个数据源获取{len(indicators)}个指标...")

        results: Dict[RateIndicator, Dict[str, Optional[RateDataPoint]]] = {}

        for indicator in indicators:
            results[indicator] = {}
            best_source = cls.find_best_data_source(indicator)

            if best_source:
                config = config or {}
                config['use_mock_data'] = use_mock

                try:
                    adapter = cls.create_adapter(best_source, config)
                    async with adapter:
                        rate_data = await adapter.fetch_latest_rate(indicator)
                        results[indicator][best_source.value] = rate_data

                        if rate_data:
                            logger.info(f"从{best_source.value}获取{indicator}: {rate_data.value}%")
                        else:
                            logger.warning(f"从{best_source.value}未获取到{indicator}数据")
                except Exception as e:
                    logger.error(f"从{best_source.value}获取{indicator}失败: {e}")
                    results[indicator][best_source.value] = None
            else:
                logger.warning(f"未找到支持{indicator}的数据源")
                results[indicator] = {}

        return results

    @classmethod
    def get_data_source_info(cls, source: RateDataSource) -> Dict:
        """
        获取数据源信息

        Args:
            source: 数据源类型

        Returns:
            数据源信息字典
        """
        info = {
            'source': source.value,
            'adapter_class': cls.ADAPTER_REGISTRY[source].__name__,
            'supported_indicators_count': len(cls.get_supported_indicators(source)),
        }

        # 尝试获取更多信息
        try:
            adapter = cls.create_adapter(source, {'use_mock_data': True})
            info['adapter_name'] = getattr(adapter, 'ADAPTER_NAME', 'Unknown')
            info['data_source_url'] = getattr(adapter, 'DATA_SOURCE_URL', 'Unknown')
        except Exception as e:
            logger.debug(f"获取{source.value}信息失败: {e}")

        return info

    @classmethod
    def list_all_sources(cls) -> List[Dict]:
        """列出所有支持的数据源"""
        return [cls.get_data_source_info(source) for source in RateDataSource]


# 便捷函数
async def get_latest_rate(
    indicator: RateIndicator,
    source: Optional[RateDataSource] = None,
    api_key: Optional[str] = None,
    use_mock: bool = True
) -> Optional[RateDataPoint]:
    """
    便捷函数：获取最新利率

    Args:
        indicator: 利率指标
        source: 数据源（可选，自动选择最佳）
        api_key: API密钥
        use_mock: 是否使用模拟数据

    Returns:
        利率数据点或None
    """
    config = {'api_key': api_key} if api_key else {}
    config['use_mock_data'] = use_mock

    if source:
        adapter = RateAdapterFactory.create_adapter(source, config)
        async with adapter:
            return await adapter.fetch_latest_rate(indicator)
    else:
        return await RateAdapterFactory.fetch_latest_rate_from_best_source(
            indicator, config, use_mock
        )


async def get_multiple_rates(
    indicators: List[RateIndicator],
    sources: Optional[List[RateDataSource]] = None,
    config: Optional[Dict] = None,
    use_mock: bool = True
) -> Dict[RateIndicator, Dict[str, Optional[RateDataPoint]]]:
    """
    便捷函数：获取多个利率

    Args:
        indicators: 指标列表
        sources: 数据源列表（可选，自动选择最佳）
        config: 配置字典
        use_mock: 是否使用模拟数据

    Returns:
        各指标的利率数据
    """
    if sources:
        # 从指定数据源获取
        results: Dict[RateIndicator, Dict[str, Optional[RateDataPoint]]] = {}

        for source in sources:
            config = config or {}
            config['use_mock_data'] = use_mock

            try:
                adapter = RateAdapterFactory.create_adapter(source, config)
                async with adapter:
                    for indicator in indicators:
                        if indicator not in results:
                            results[indicator] = {}
                        rate_data = await adapter.fetch_latest_rate(indicator)
                        results[indicator][source.value] = rate_data
            except Exception as e:
                logger.error(f"从{source.value}获取数据失败: {e}")

        return results
    else:
        # 自动选择最佳数据源
        return await RateAdapterFactory.fetch_rates_from_multiple_sources(
            indicators, config, use_mock
        )


# 测试代码
if __name__ == "__main__":
    async def test():
        # 测试适配器工厂
        print("\n=== 数据源信息 ===")
        for info in RateAdapterFactory.list_all_sources():
            print(f"数据源: {info['source']}")
            print(f"  适配器: {info['adapter_name']}")
            print(f"  支持指标数: {info['supported_indicators_count']}")
            print(f"  数据源URL: {info['data_source_url']}")
            print()

        # 测试获取利率
        print("\n=== 获取最新利率 ===")
        fed_funds = await get_latest_rate(
            RateIndicator.FED_FUNDS,
            use_mock=True
        )
        print(f"联邦基金利率: {fed_funds.value if fed_funds else 'N/A'}%")

        # 测试批量获取
        print("\n=== 批量获取利率 ===")
        indicators = [
            RateIndicator.FED_FUNDS,
            RateIndicator.ONE_MONTH,
            RateIndicator.THREE_MONTHS
        ]

        results = await get_multiple_rates(indicators, use_mock=True)

        for indicator, source_data in results.items():
            print(f"\n{indicator}:")
            for source, rate_data in source_data.items():
                if rate_data:
                    print(f"  {source}: {rate_data.value}%")

    asyncio.run(test())
