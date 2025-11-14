"""
数据编排器
协调多个数据源的数据获取、验证和处理
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data_adapters.base import BaseDataAdapter, DataSourceType
from src.validators.data_validator import DataValidator


class DataOrchestrator:
    """
    数据编排器
    负责：
    1. 协调多个数据源的并行数据获取
    2. 统一数据验证和质量检查
    3. 数据合并和标准化
    4. 错误处理和重试机制
    """

    def __init__(self, max_workers: int = 4):
        """
        初始化数据编排器

        Args:
            max_workers: 最大并行工作线程数
        """
        self.adapters: Dict[DataSourceType, BaseDataAdapter] = {}
        self.validator = DataValidator()
        self.logger = logging.getLogger('nonprice_data.orchestrator')
        self.max_workers = max_workers

    def register_adapter(self, adapter: BaseDataAdapter):
        """
        注册数据适配器

        Args:
            adapter: 数据适配器实例
        """
        self.adapters[adapter.data_source_type] = adapter
        self.logger.info(f"Registered adapter for {adapter.data_source_type.value}")

    def get_registered_sources(self) -> List[DataSourceType]:
        """获取已注册的数据源"""
        return list(self.adapters.keys())

    async def fetch_single_source(
        self,
        data_source: DataSourceType,
        indicator: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True
    ) -> Tuple[DataSourceType, pd.DataFrame, Dict[str, Any]]:
        """
        获取单个数据源的数据

        Args:
            data_source: 数据源类型
            indicator: 指标名称
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            Tuple[DataSourceType, DataFrame, Dict]: (数据源, 数据, 质量报告)
        """
        if data_source not in self.adapters:
            raise ValueError(f"No adapter registered for {data_source.value}")

        adapter = self.adapters[data_source]

        try:
            self.logger.info(
                f"Fetching {indicator} from {data_source.value} "
                f"({start_date} to {end_date})"
            )

            # 获取数据
            df = await adapter.get_data(indicator, start_date, end_date, use_cache)

            # 生成质量报告
            quality_report = await self.validator.get_data_quality_report(
                df, data_source.value
            )

            self.logger.info(
                f"Successfully fetched {len(df)} records from {data_source.value}"
            )

            return data_source, df, quality_report

        except Exception as e:
            self.logger.error(
                f"Failed to fetch {indicator} from {data_source.value}: {str(e)}"
            )
            raise

    async def fetch_multiple_sources(
        self,
        indicators: Dict[DataSourceType, List[str]],
        start_date: date,
        end_date: date,
        use_cache: bool = True
    ) -> Dict[DataSourceType, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """
        并行获取多个数据源的数据

        Args:
            indicators: 数据源和指标的映射 {DataSourceType: [indicator1, indicator2]}
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            Dict[DataSourceType, Tuple[DataFrame, Dict]]: 数据源到(数据, 质量报告)的映射
        """
        results = {}

        # 创建任务列表
        tasks = []
        for data_source, indicator_list in indicators.items():
            for indicator in indicator_list:
                task = self.fetch_single_source(
                    data_source, indicator, start_date, end_date, use_cache
                )
                tasks.append((data_source, indicator, task))

        self.logger.info(f"Starting parallel fetch of {len(tasks)} data requests")

        # 执行所有任务
        completed_tasks = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)

        # 处理结果
        for i, (data_source, indicator, result) in enumerate(zip(
            [t[0] for t in tasks],
            [t[1] for t in tasks],
            completed_tasks
        )):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Task failed for {data_source.value}/{indicator}: {str(result)}"
                )
                # 继续处理其他任务
                continue

            source, df, quality_report = result

            if source not in results:
                results[source] = (df, quality_report)
            else:
                # 合并同一数据源的数据
                existing_df, existing_report = results[source]
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['symbol', 'date'])
                combined_df = combined_df.sort_values('date')

                results[source] = (combined_df, quality_report)

        self.logger.info(f"Completed fetch for {len(results)} data sources")

        return results

    async def fetch_all_indicators(
        self,
        data_source: DataSourceType,
        start_date: date,
        end_date: date,
        use_cache: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        获取数据源的所有指标

        Args:
            data_source: 数据源类型
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            Tuple[DataFrame, Dict]: (合并的数据, 质量报告)
        """
        if data_source not in self.adapters:
            raise ValueError(f"No adapter registered for {data_source.value}")

        adapter = self.adapters[data_source]
        indicators = adapter.get_supported_indicators()

        self.logger.info(
            f"Fetching all {len(indicators)} indicators from {data_source.value}"
        )

        results = await self.fetch_multiple_sources(
            {data_source: indicators},
            start_date,
            end_date,
            use_cache
        )

        if data_source not in results:
            raise ValueError(f"No data retrieved from {data_source.value}")

        df, quality_report = results[data_source]
        return df, quality_report

    async def merge_data(
        self,
        data_dict: Dict[DataSourceType, pd.DataFrame],
        add_source_column: bool = True
    ) -> pd.DataFrame:
        """
        合并多个数据源的数据

        Args:
            data_dict: 数据源到DataFrame的映射
            add_source_column: 是否添加数据源列

        Returns:
            DataFrame: 合并后的数据
        """
        all_dfs = []

        for data_source, df in data_dict.items():
            df_copy = df.copy()

            if add_source_column:
                df_copy['data_source'] = data_source.value

            all_dfs.append(df_copy)

        if not all_dfs:
            return pd.DataFrame(columns=['symbol', 'date', 'value', 'source'])

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # 去除重复
        combined_df = combined_df.drop_duplicates(
            subset=['symbol', 'date', 'source'] if add_source_column else ['symbol', 'date']
        )

        # 排序
        combined_df = combined_df.sort_values(['date', 'source', 'symbol'])

        self.logger.info(f"Merged {len(all_dfs)} data sources into {len(combined_df)} records")

        return combined_df

    async def get_aggregated_quality_report(
        self,
        results: Dict[DataSourceType, Tuple[pd.DataFrame, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        生成聚合质量报告

        Args:
            results: 数据源结果

        Returns:
            Dict[str, Any]: 聚合报告
        """
        report = {
            'total_sources': len(results),
            'sources': {},
            'overall_quality': {
                'total_records': 0,
                'valid_records': 0,
                'mock_data_sources': [],
                'average_quality_score': 0.0
            }
        }

        total_quality_score = 0.0
        total_records = 0
        valid_records = 0
        mock_sources = []

        for data_source, (df, quality_report) in results.items():
            total_records += len(df)

            # 统计有效记录
            if quality_report['data_quality']['is_valid']:
                valid_records += len(df)

            # 模拟数据源
            if quality_report['mock_detection']['is_mock']:
                mock_sources.append(data_source.value)

            # 质量分数
            quality_score = quality_report['data_quality']['quality_score']
            total_quality_score += quality_score

            # 添加到报告
            report['sources'][data_source.value] = quality_report

        # 计算总体指标
        report['overall_quality']['total_records'] = total_records
        report['overall_quality']['valid_records'] = valid_records
        report['overall_quality']['mock_data_sources'] = mock_sources
        report['overall_quality']['average_quality_score'] = (
            total_quality_score / len(results) if results else 0.0
        )
        report['overall_quality']['data_validity_rate'] = (
            valid_records / total_records if total_records > 0 else 0.0
        )

        return report

    def clear_all_caches(self):
        """清空所有适配器的缓存"""
        for adapter in self.adapters.values():
            adapter.clear_cache()
        self.logger.info("Cleared all adapter caches")

    def get_status(self) -> Dict[str, Any]:
        """获取编排器状态"""
        return {
            'registered_sources': [source.value for source in self.adapters.keys()],
            'max_workers': self.max_workers,
            'adapters': {
                source.value: {
                    'class': adapter.__class__.__name__,
                    'cache_size': len(adapter._cache)
                }
                for source, adapter in self.adapters.items()
            }
        }
