"""
替代数据服务管理器

统一管理所有替代数据适配器（HKEX、政府数据、Kaggle等）
支持适配器注册、发现、缓存和健康检查
包含数据管道集成（清洁、对齐、规范化）
"""

import asyncio
import logging
from datetime import date
from typing import Dict, Any, List, Optional, Type

import pandas as pd

from .alternative_data_adapter import AlternativeDataAdapter, IndicatorMetadata
from .hkex_data_collector import HKEXDataCollector
from .gov_data_collector import GovDataCollector
from .kaggle_data_collector import KaggleDataCollector
from ..data_pipeline.pipeline_processor import PipelineProcessor

logger = logging.getLogger("hk_quant_system.alternative_data_service")


class AlternativeDataService:
    """替代数据服务管理器

    统一管理多个替代数据适配器，提供适配器注册、发现、
    数据获取等功能。

    使用示例:
        service = AlternativeDataService()
        await service.initialize()
        data = await service.get_data("hkex", "hsi_futures_volume", date(2024,1,1), date(2024,1,31))
    """

    def __init__(self):
        """初始化替代数据服务"""
        self.adapters: Dict[str, AlternativeDataAdapter] = {}
        self.adapter_classes: Dict[str, Type[AlternativeDataAdapter]] = {
            "hkex": HKEXDataCollector,
            "government": GovDataCollector,
            "kaggle": KaggleDataCollector,
        }
        self._initialized = False

        # 初始化管道处理器
        self.pipeline_processor = PipelineProcessor(checkpoint_enabled=True, verbose=False)
        self.pipeline_config = {}  # 存储管道配置
        self.processed_data_cache = {}  # 缓存处理后的数据

        logger.info("✓ AlternativeDataService 初始化完成")

    async def initialize(self, mode: str = "mock") -> bool:
        """初始化所有适配器

        Args:
            mode: 操作模式 ("mock" 或 "live")

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info(f"开始初始化替代数据适配器 (模式: {mode})...")

            # 创建所有预定义的适配器
            for adapter_name, adapter_class in self.adapter_classes.items():
                try:
                    adapter = adapter_class(mode=mode)
                    await adapter.connect()
                    self.adapters[adapter_name] = adapter
                    logger.info(f"✓ 已初始化适配器: {adapter_name}")
                except Exception as e:
                    logger.error(f"✗ 初始化适配器 {adapter_name} 失败: {e}")
                    continue

            self._initialized = True
            logger.info(
                f"✓ 替代数据服务初始化完成 ({len(self.adapters)} 个适配器)"
            )
            return True

        except Exception as e:
            logger.error(f"✗ 初始化替代数据服务失败: {e}")
            return False

    def register_adapter(
        self, name: str, adapter_class: Type[AlternativeDataAdapter]
    ) -> bool:
        """注册新适配器

        Args:
            name: 适配器名称
            adapter_class: 适配器类

        Returns:
            bool: 注册是否成功
        """
        try:
            if not issubclass(adapter_class, AlternativeDataAdapter):
                logger.error(f"✗ 适配器必须继承 AlternativeDataAdapter")
                return False

            self.adapter_classes[name] = adapter_class
            logger.info(f"✓ 已注册适配器: {name}")
            return True

        except Exception as e:
            logger.error(f"✗ 注册适配器失败: {e}")
            return False

    async def get_data(
        self,
        adapter_name: str,
        indicator_code: str,
        start_date: date,
        end_date: date,
        **kwargs,
    ):
        """获取特定适配器的数据

        Args:
            adapter_name: 适配器名称
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            pd.DataFrame: 数据框
        """
        if not self._initialized:
            logger.error("✗ 服务尚未初始化")
            return None

        if adapter_name not in self.adapters:
            logger.error(f"✗ 适配器不存在: {adapter_name}")
            return None

        try:
            adapter = self.adapters[adapter_name]
            return await adapter.fetch_data(
                indicator_code, start_date, end_date, **kwargs
            )

        except Exception as e:
            logger.error(f"✗ 获取数据失败: {e}")
            return None

    async def get_realtime_data(self, adapter_name: str, indicator_code: str):
        """获取实时数据

        Args:
            adapter_name: 适配器名称
            indicator_code: 指标代码

        Returns:
            Dict: 实时数据
        """
        if not self._initialized:
            logger.error("✗ 服务尚未初始化")
            return None

        if adapter_name not in self.adapters:
            logger.error(f"✗ 适配器不存在: {adapter_name}")
            return None

        try:
            adapter = self.adapters[adapter_name]
            return await adapter.get_realtime_data(indicator_code)

        except Exception as e:
            logger.error(f"✗ 获取实时数据失败: {e}")
            return None

    async def get_indicator_metadata(
        self, adapter_name: str, indicator_code: str
    ) -> Optional[IndicatorMetadata]:
        """获取指标元数据

        Args:
            adapter_name: 适配器名称
            indicator_code: 指标代码

        Returns:
            IndicatorMetadata: 元数据
        """
        if not self._initialized:
            logger.error("✗ 服务尚未初始化")
            return None

        if adapter_name not in self.adapters:
            logger.error(f"✗ 适配器不存在: {adapter_name}")
            return None

        try:
            adapter = self.adapters[adapter_name]
            return await adapter.get_metadata(indicator_code)

        except Exception as e:
            logger.error(f"✗ 获取元数据失败: {e}")
            return None

    async def list_adapters(self) -> List[str]:
        """列出所有可用适配器

        Returns:
            List[str]: 适配器名称列表
        """
        return list(self.adapters.keys())

    async def list_indicators(self, adapter_name: str) -> List[str]:
        """列出特定适配器的所有指标

        Args:
            adapter_name: 适配器名称

        Returns:
            List[str]: 指标代码列表
        """
        if adapter_name not in self.adapters:
            logger.error(f"✗ 适配器不存在: {adapter_name}")
            return []

        try:
            adapter = self.adapters[adapter_name]
            return await adapter.list_indicators()

        except Exception as e:
            logger.error(f"✗ 列出指标失败: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """检查所有适配器的健康状态

        Returns:
            Dict: 健康检查结果
        """
        health_status = {
            "service": "AlternativeDataService",
            "initialized": self._initialized,
            "adapters": {},
        }

        try:
            for adapter_name, adapter in self.adapters.items():
                try:
                    health = await adapter.health_check()
                    health_status["adapters"][adapter_name] = health
                except Exception as e:
                    health_status["adapters"][adapter_name] = {
                        "status": "error",
                        "error": str(e),
                    }

            # 计算整体状态
            all_healthy = all(
                status.get("status") == "healthy"
                for status in health_status["adapters"].values()
            )
            health_status["overall_status"] = (
                "healthy" if all_healthy else "degraded"
            )

            return health_status

        except Exception as e:
            logger.error(f"✗ 健康检查失败: {e}")
            return health_status

    async def get_adapter_health_details(self, adapter_name: str) -> Dict[str, Any]:
        """获取特定适配器的详细健康状态

        Args:
            adapter_name: 适配器名称

        Returns:
            Dict: 详细健康状态
        """
        if adapter_name not in self.adapters:
            return {"error": f"Adapter not found: {adapter_name}"}

        try:
            adapter = self.adapters[adapter_name]
            return await adapter.health_check()

        except Exception as e:
            logger.error(f"✗ 获取适配器健康状态失败: {e}")
            return {"error": str(e)}

    async def clear_cache(self, adapter_name: Optional[str] = None) -> bool:
        """清空缓存

        Args:
            adapter_name: 适配器名称 (None则清空所有)

        Returns:
            bool: 是否成功
        """
        try:
            if adapter_name:
                if adapter_name in self.adapters:
                    self.adapters[adapter_name].clear_cache()
                    logger.info(f"✓ 已清空 {adapter_name} 的缓存")
                else:
                    logger.error(f"✗ 适配器不存在: {adapter_name}")
                    return False
            else:
                for adapter in self.adapters.values():
                    adapter.clear_cache()
                logger.info("✓ 已清空所有适配器的缓存")

            return True

        except Exception as e:
            logger.error(f"✗ 清空缓存失败: {e}")
            return False

    def configure_pipeline(
        self,
        pipeline_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        配置数据处理管道。

        Args:
            pipeline_steps: 管道步骤列表，每个步骤包含name、type和config

        Returns:
            bool: 配置是否成功
        """
        try:
            if pipeline_steps is None:
                # 使用默认管道配置
                pipeline_steps = [
                    {
                        "name": "clean",
                        "type": "clean",
                        "config": {
                            "missing_value_strategy": "interpolate",
                            "outlier_strategy": "cap",
                        },
                    },
                    {
                        "name": "align",
                        "type": "align",
                        "config": {
                            "align_to_trading_days": True,
                            "generate_lags": False,
                        },
                    },
                    {
                        "name": "normalize",
                        "type": "normalize",
                        "config": {"method": "zscore"},
                    },
                    {
                        "name": "score",
                        "type": "score",
                        "config": {"completeness_weight": 0.5},
                    },
                ]

            # 重置pipeline处理器
            self.pipeline_processor = PipelineProcessor(
                checkpoint_enabled=True, verbose=False
            )

            # 添加步骤
            for step in pipeline_steps:
                self.pipeline_processor.add_step(
                    step["name"],
                    step["type"],
                    step.get("config", {}),
                )

            self.pipeline_config = pipeline_steps
            logger.info(f"✓ 已配置管道 ({len(pipeline_steps)} 个步骤)")
            return True

        except Exception as e:
            logger.error(f"✗ 配置管道失败: {e}")
            return False

    async def get_aligned_data(
        self,
        adapter_name: str,
        indicator_code: str,
        start_date: date,
        end_date: date,
        apply_pipeline: bool = True,
        date_column: Optional[str] = None,
        **kwargs,
    ) -> Optional[pd.DataFrame]:
        """
        获取对齐和处理后的数据。

        使用配置的管道自动进行清洁、对齐、规范化处理。

        Args:
            adapter_name: 适配器名称
            indicator_code: 指标代码
            start_date: 开始日期
            end_date: 结束日期
            apply_pipeline: 是否应用管道处理
            date_column: 日期列名称
            **kwargs: 其他参数

        Returns:
            pd.DataFrame: 处理后的数据
        """
        if not self._initialized:
            logger.error("✗ 服务尚未初始化")
            return None

        try:
            # 检查缓存
            cache_key = f"{adapter_name}_{indicator_code}_{start_date}_{end_date}"
            if cache_key in self.processed_data_cache:
                logger.info(f"✓ 从缓存返回数据 ({adapter_name}:{indicator_code})")
                return self.processed_data_cache[cache_key]

            # 获取原始数据
            raw_data = await self.get_data(
                adapter_name, indicator_code, start_date, end_date, **kwargs
            )

            if raw_data is None or raw_data.empty:
                logger.warning(f"✗ 无数据返回 ({adapter_name}:{indicator_code})")
                return None

            # 应用管道处理
            if apply_pipeline:
                processed_data = self.process_data_with_pipeline(
                    raw_data, date_column=date_column or "date"
                )
            else:
                processed_data = raw_data

            # 缓存结果
            self.processed_data_cache[cache_key] = processed_data

            logger.info(
                f"✓ 返回对齐数据 ({adapter_name}:{indicator_code}): "
                f"{len(processed_data)} 行"
            )
            return processed_data

        except Exception as e:
            logger.error(f"✗ 获取对齐数据失败: {e}")
            return None

    def process_data_with_pipeline(
        self,
        df: pd.DataFrame,
        date_column: str = "date",
    ) -> pd.DataFrame:
        """
        使用配置的管道处理数据。

        Args:
            df: 输入DataFrame
            date_column: 日期列名称

        Returns:
            处理后的DataFrame
        """
        try:
            if df.empty:
                logger.warning("空数据框")
                return df

            # 执行管道处理
            processed_df = self.pipeline_processor.process(
                df, date_column=date_column
            )

            logger.info(
                f"✓ 管道处理完成: {len(df)} → {len(processed_df)} 行"
            )
            return processed_df

        except Exception as e:
            logger.error(f"✗ 管道处理失败: {e}")
            return df

    def get_pipeline_report(self) -> Dict[str, Any]:
        """获取上次管道执行的报告"""
        return self.pipeline_processor.get_report()

    def clear_processed_data_cache(self) -> bool:
        """清空处理后的数据缓存"""
        try:
            self.processed_data_cache.clear()
            logger.info("✓ 已清空处理数据缓存")
            return True
        except Exception as e:
            logger.error(f"✗ 清空缓存失败: {e}")
            return False

    async def cleanup(self) -> bool:
        """清理所有资源

        Returns:
            bool: 是否成功
        """
        try:
            logger.info("开始清理替代数据服务...")

            for adapter_name, adapter in self.adapters.items():
                try:
                    await adapter.disconnect()
                    logger.info(f"✓ 已断开适配器: {adapter_name}")
                except Exception as e:
                    logger.error(f"✗ 断开适配器失败: {e}")

            self.adapters.clear()
            self._initialized = False
            logger.info("✓ 替代数据服务清理完成")

            return True

        except Exception as e:
            logger.error(f"✗ 清理服务失败: {e}")
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息

        Returns:
            Dict: 服务信息
        """
        return {
            "service_name": "AlternativeDataService",
            "initialized": self._initialized,
            "adapters_registered": len(self.adapter_classes),
            "adapters_active": len(self.adapters),
            "active_adapters": list(self.adapters.keys()),
        }


# 使用示例
async def main():
    """演示AlternativeDataService的使用"""

    service = AlternativeDataService()

    # 初始化
    initialized = await service.initialize(mode="mock")
    print(f"Service initialized: {initialized}\n")

    # 列出适配器
    adapters = await service.list_adapters()
    print(f"Available adapters: {adapters}\n")

    # 列出指标
    print("[HKEX Indicators]")
    hkex_indicators = await service.list_indicators("hkex")
    print(f"Total: {len(hkex_indicators)}")
    for ind in hkex_indicators[:3]:
        print(f"  - {ind}")
    print()

    print("[Government Indicators]")
    gov_indicators = await service.list_indicators("government")
    print(f"Total: {len(gov_indicators)}")
    for ind in gov_indicators[:3]:
        print(f"  - {ind}")
    print()

    # 获取数据
    print("[Fetching Data]")
    data = await service.get_data(
        "hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
    )
    if data is not None:
        print(f"Data shape: {data.shape}")
        print(f"First row: {data.iloc[0].to_dict()}\n")

    # 健康检查
    print("[Health Check]")
    health = await service.health_check()
    print(f"Overall status: {health['overall_status']}")
    print(f"Adapters: {len(health['adapters'])}\n")

    # 服务信息
    info = service.get_service_info()
    print(f"Service info: {info}\n")

    # 清理
    await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
