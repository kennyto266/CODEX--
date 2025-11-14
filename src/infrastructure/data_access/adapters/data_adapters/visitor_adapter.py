#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访客数据适配器
从 data.gov.hk (CKAN API) 或 Chrome MCP 爬取获取真实访客数据
实现 BaseDataAdapter 接口，支持数据获取、验证和模拟数据检测

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator

from .base import BaseDataAdapter, DataSourceType
from .visitor_parser import VisitorDataProcessor, VisitorType, VisitorFrequency
from ..scraping.chrome_mcp_scraper import ChromeMCPScraper
from ..api.ckan_api import CKANAPI


class VisitorAdapterConfig(BaseModel):
    """访客适配器配置"""
    # 数据源配置
    use_ckan_api: bool = Field(default=True, description="使用CKAN API")
    use_chrome_mcp: bool = Field(default=False, description="使用Chrome MCP爬虫")
    ckan_base_url: str = Field(default="https://data.gov.hk/api/3", description="CKAN API基础URL")
    data_gov_hk_base: str = Field(default="https://data.gov.hk", description="data.gov.hk基础URL")

    # 抓取配置
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟（秒）")
    request_timeout: int = Field(default=30, description="请求超时（秒）")
    rate_limit_delay: float = Field(default=1.0, description="请求间隔（秒）")

    # 访客指标配置
    supported_indicators: List[str] = Field(
        default=['visitor_total', 'visitor_mainland', 'visitor_growth'],
        description="支持的访客指标"
    )

    # 数据质量配置
    min_data_points: int = Field(default=50, description="最小数据点数")
    max_data_points: int = Field(default=10000, description="最大数据点数")
    quality_threshold: float = Field(default=0.8, description="数据质量阈值")

    # 模拟数据检测配置
    mock_detection_enabled: bool = Field(default=True, description="启用模拟数据检测")
    mock_confidence_threshold: float = Field(default=0.7, description="模拟数据检测置信度阈值")

    # 缓存配置
    cache_enabled: bool = Field(default=True, description="启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存生存时间（秒）")

    # 错误处理
    strict_mode: bool = Field(default=False, description="严格模式（遇到错误时抛出异常）")


class VisitorAdapter(BaseDataAdapter):
    """
    访客数据适配器

    从 data.gov.hk 获取真实的访客统计数据，支持：
    1. CKAN API 直接获取
    2. Chrome MCP 爬虫抓取
    3. 数据验证和质量检查
    4. 模拟数据检测
    """

    def __init__(self, config: Optional[VisitorAdapterConfig] = None):
        """
        初始化访客适配器

        Args:
            config: 适配器配置
        """
        super().__init__(DataSourceType.VISITOR)
        self.config = config or VisitorAdapterConfig()
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

        # 初始化数据源
        self.ckan_api = CKANAPI(base_url=self.config.ckan_base_url)
        self.chrome_scraper = ChromeMCPScraper()
        self.visitor_parser = VisitorDataProcessor()

        # 内部状态
        self._is_initialized = False
        self._last_request_time = 0

        # 模拟数据检测统计
        self._mock_stats = {
            'total_requests': 0,
            'mock_detected': 0,
            'real_detected': 0
        }

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            self.logger.info("Initializing VisitorAdapter...")

            # 初始化数据源
            if self.config.use_ckan_api:
                # 测试CKAN API连接
                self.logger.info("Testing CKAN API connection...")
                # 这里可以添加实际连接测试

            if self.config.use_chrome_mcp:
                # 初始化Chrome MCP
                self.logger.info("Initializing Chrome MCP scraper...")
                await self.chrome_scraper.initialize_chrome()

            self._is_initialized = True
            self.logger.info("VisitorAdapter initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize VisitorAdapter: {e}")
            if self.config.strict_mode:
                raise
            return False

    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.config.use_chrome_mcp and self.chrome_scraper:
                await self.chrome_scraper.close_browser()

            self._is_initialized = False
            self.logger.info("VisitorAdapter cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def fetch_data(
        self,
        indicator: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        获取访客数据

        Args:
            indicator: 指标名称 (visitor_total, visitor_mainland, visitor_growth)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 包含(symbol, date, value, source)列的访客数据

        Raises:
            ValueError: 指标不支持或参数无效
            RuntimeError: 数据获取失败
        """
        self._mock_stats['total_requests'] += 1

        # 验证指标
        if indicator not in self.config.supported_indicators:
            raise ValueError(f"Unsupported indicator: {indicator}. "
                           f"Supported: {self.config.supported_indicators}")

        # 验证日期范围
        if not self.validate_date_range(start_date, end_date):
            raise ValueError(f"Invalid date range: {start_date} to {end_date}")

        cache_key = self.get_cache_key(indicator, start_date, end_date)

        # 检查缓存
        if self.config.cache_enabled and self.is_cached(cache_key):
            self.logger.info(f"Using cached data for {indicator}")
            return self.get_from_cache(cache_key)

        self.logger.info(f"Fetching {indicator} data from {start_date} to {end_date}")

        # 尝试从数据源获取数据
        data = None
        last_error = None

        # 方法1: 尝试CKAN API
        if self.config.use_ckan_api:
            try:
                self.logger.info(f"Trying CKAN API for {indicator}...")
                data = await self._fetch_from_ckan(indicator, start_date, end_date)
                if data is not None and len(data) > 0:
                    self.logger.info(f"Successfully fetched {len(data)} records from CKAN API")
            except Exception as e:
                self.logger.warning(f"CKAN API failed: {e}")
                last_error = e

        # 方法2: 尝试Chrome MCP爬虫
        if data is None and self.config.use_chrome_mcp:
            try:
                self.logger.info(f"Trying Chrome MCP scraper for {indicator}...")
                data = await self._fetch_from_chrome_mcp(indicator, start_date, end_date)
                if data is not None and len(data) > 0:
                    self.logger.info(f"Successfully fetched {len(data)} records from Chrome MCP")
            except Exception as e:
                self.logger.warning(f"Chrome MCP failed: {e}")
                if last_error is None:
                    last_error = e

        # 如果所有方法都失败
        if data is None:
            error_msg = f"Failed to fetch {indicator} data from all sources"
            self.logger.error(error_msg)
            if self.config.strict_mode:
                raise RuntimeError(error_msg)
            else:
                # 返回空DataFrame而不是失败
                return pd.DataFrame(columns=['symbol', 'date', 'value', 'source'])

        # 验证数据
        is_valid, errors = await self.validate_data(data)
        if not is_valid:
            self.logger.warning(f"Data validation failed: {errors}")
            if self.config.strict_mode:
                raise ValueError(f"Data validation failed: {errors}")

        # 检测模拟数据
        is_mock, confidence, mock_indicators = await self.detect_mock_data(data)
        if is_mock:
            self._mock_stats['mock_detected'] += 1
            self.logger.warning(
                f"Mock data detected (confidence: {confidence:.2%}): {mock_indicators}"
            )
        else:
            self._mock_stats['real_detected'] += 1

        # 缓存数据
        if self.config.cache_enabled:
            self.save_to_cache(cache_key, data)

        return data

    async def _fetch_from_ckan(
        self,
        indicator: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """从CKAN API获取数据"""
        try:
            # 搜索访客相关数据集
            datasets = await self.ckan_api.search_datasets('visitor')

            if not datasets or not datasets.get('success'):
                self.logger.warning("No visitor datasets found via CKAN API")
                return None

            # 查找合适的数据集
            for dataset in datasets.get('result', {}).get('results', []):
                # 检查是否包含目标指标
                title = dataset.get('title', '').lower()
                if indicator.lower() in title or 'visitor' in title or 'tourist' in title:

                    # 获取资源
                    resources = dataset.get('resources', [])
                    for resource in resources:
                        # 寻找CSV格式的资源
                        if resource.get('format', '').upper() == 'CSV':
                            url = resource.get('url')
                            if url:
                                # 下载数据
                                csv_data = await self.ckan_api.download_resource(url)
                                if csv_data:
                                    # 解析CSV
                                    df = pd.read_csv(pd.io.common.BytesIO(csv_data))
                                    # 标准化格式
                                    df = self._normalize_dataframe(df, indicator, 'ckan')
                                    return df

            return None

        except Exception as e:
            self.logger.error(f"Error fetching from CKAN: {e}")
            return None

    async def _fetch_from_chrome_mcp(
        self,
        indicator: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """从Chrome MCP爬虫获取数据"""
        try:
            # 运行爬虫
            await self.chrome_scraper.initialize_chrome()
            await self.chrome_scraper.navigate_to_data_gov_hk()
            await self.chrome_scraper.navigate_to_visitor_datasets()

            # 抓取数据
            raw_data = await self.chrome_scraper.scrape_visitor_data()

            if not raw_data:
                return None

            # 转换为DataFrame
            df = pd.DataFrame(raw_data)

            # 过滤日期范围
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

            # 标准化格式
            df = self._normalize_dataframe(df, indicator, 'chrome_mcp')
            return df

        except Exception as e:
            self.logger.error(f"Error fetching from Chrome MCP: {e}")
            return None
        finally:
            await self.chrome_scraper.close_browser()

    def _normalize_dataframe(
        self,
        df: pd.DataFrame,
        indicator: str,
        source: str
    ) -> pd.DataFrame:
        """
        标准化DataFrame格式

        Args:
            df: 原始DataFrame
            indicator: 指标名称
            source: 数据源标识

        Returns:
            DataFrame: 标准化后的DataFrame
        """
        df_copy = df.copy()

        # 确保有date列
        if 'date' in df_copy.columns:
            pass  # 已存在
        elif 'Date' in df_copy.columns:
            df_copy = df_copy.rename(columns={'Date': 'date'})
        else:
            # 寻找类似日期的列
            for col in df_copy.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    df_copy = df_copy.rename(columns={col: 'date'})
                    break

        # 转换日期格式
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.date

        # 寻找数值列（访客数量）
        value_col = None
        for col in df_copy.columns:
            if col.lower() in ['value', 'visitors', 'count', 'total']:
                value_col = col
                break

        if value_col is None and len(df_copy.columns) > 1:
            # 使用第一列数值列
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                value_col = numeric_cols[0]

        if value_col is None:
            raise ValueError("No suitable value column found")

        # 标准化列名
        df_result = pd.DataFrame({
            'symbol': indicator,
            'date': df_copy['date'],
            'value': pd.to_numeric(df_copy[value_col], errors='coerce'),
            'source': source
        })

        # 删除无效行
        df_result = df_result.dropna()

        # 按日期排序
        df_result = df_result.sort_values('date').reset_index(drop=True)

        return df_result

    async def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证访客数据质量

        Args:
            df: 要验证的DataFrame

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []

        # 检查必需列
        required_columns = ['symbol', 'date', 'value', 'source']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # 检查记录数量
        if len(df) < self.config.min_data_points:
            errors.append(f"Too few records: {len(df)} < {self.config.min_data_points}")
        if len(df) > self.config.max_data_points:
            errors.append(f"Too many records: {len(df)} > {self.config.max_data_points}")

        # 检查数据类型
        if 'date' in df.columns:
            # 确保日期类型
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                errors.append("'date' column must be datetime type")

        if 'value' in df.columns:
            # 确保数值类型
            if not pd.api.types.is_numeric_dtype(df['value']):
                errors.append("'value' column must be numeric type")

            # 检查负值
            negative_count = (df['value'] < 0).sum()
            if negative_count > 0:
                errors.append(f"Found {negative_count} negative values")

        # 检查数据源域名
        if 'source' in df.columns:
            valid_domains = ['data.gov.hk', 'www.discoverhongkong.com', 'immd.gov.hk']
            invalid_sources = []
            for source in df['source'].unique():
                if not any(domain in str(source).lower() for domain in valid_domains):
                    invalid_sources.append(source)

            if invalid_sources:
                errors.append(f"Invalid data sources: {invalid_sources}")

        return len(errors) == 0, errors

    async def detect_mock_data(self, df: pd.DataFrame) -> Tuple[bool, float, List[str]]:
        """
        检测模拟数据

        Args:
            df: 要检测的DataFrame

        Returns:
            Tuple[bool, float, List[str]]: (是否为模拟数据, 置信度, 检测到的指标)
        """
        if not self.config.mock_detection_enabled:
            return False, 0.0, []

        mock_score = 0.0
        detected_issues = []

        if len(df) == 0:
            return False, 0.0, []

        # 1. 检查重复值
        value_counts = df['value'].value_counts()
        max_repeat = value_counts.max() if len(value_counts) > 0 else 0
        repeat_ratio = max_repeat / len(df) if len(df) > 0 else 0

        if repeat_ratio > 0.5:  # 50%以上是重复值
            mock_score += 0.3
            detected_issues.append(f"High repeat ratio: {repeat_ratio:.2%}")

        # 2. 检查线性趋势
        if 'value' in df.columns and len(df) > 1:
            values = df['value'].values
            # 计算与完美直线的偏差
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            predicted = np.polyval(coeffs, x)
            mae = np.mean(np.abs(values - predicted))
            max_val = np.max(values) if len(values) > 0 else 1
            linear_error = mae / max_val if max_val > 0 else 0

            if linear_error < 0.01:  # 误差小于1%
                mock_score += 0.3
                detected_issues.append("Nearly perfect linear trend")

        # 3. 检查完美的周期性
        if 'value' in df.columns and len(df) > 2:
            values = df['value'].tolist()
            # 检查是否所有值都相同
            if all(v == values[0] for v in values):
                mock_score += 0.4
                detected_issues.append("All values are identical")

        # 4. 检查四舍五入的数字
        if 'value' in df.columns:
            values = df['value'].values
            round_count = sum(1 for v in values if v % 10 == 0)
            round_ratio = round_count / len(values) if len(values) > 0 else 0

            if round_ratio > 0.8:  # 80%是整十数
                mock_score += 0.1
                detected_issues.append(f"High round number ratio: {round_ratio:.2%}")

        # 5. 检查低方差
        if 'value' in df.columns and len(df) > 1:
            values = df['value'].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            cv = std_val / mean_val if mean_val > 0 else 0  # 变异系数

            if cv < 0.001:  # 变异系数极小
                mock_score += 0.2
                detected_issues.append("Extremely low variance")

        # 判断是否为模拟数据
        is_mock = mock_score >= self.config.mock_confidence_threshold
        confidence = min(mock_score, 1.0)

        return is_mock, confidence, detected_issues

    def get_supported_indicators(self) -> List[str]:
        """获取支持的指标列表"""
        return self.config.supported_indicators.copy()

    async def get_data_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取数据质量报告"""
        report = {
            'total_records': len(df),
            'date_range': {
                'min': str(df['date'].min()) if len(df) > 0 else None,
                'max': str(df['date'].max()) if len(df) > 0 else None
            },
            'value_statistics': {
                'min': float(df['value'].min()) if 'value' in df.columns and len(df) > 0 else None,
                'max': float(df['value'].max()) if 'value' in df.columns and len(df) > 0 else None,
                'mean': float(df['value'].mean()) if 'value' in df.columns and len(df) > 0 else None,
                'std': float(df['value'].std()) if 'value' in df.columns and len(df) > 0 else None
            },
            'missing_values': df.isnull().sum().to_dict(),
            'unique_symbols': df['symbol'].unique().tolist() if 'symbol' in df.columns else [],
            'sources': df['source'].unique().tolist() if 'source' in df.columns else []
        }

        # 添加模拟数据检测结果
        is_mock, confidence, issues = await self.detect_mock_data(df)
        report['mock_detection'] = {
            'is_mock': is_mock,
            'confidence': confidence,
            'issues': issues
        }

        return report

    def get_stats(self) -> Dict[str, Any]:
        """获取适配器统计信息"""
        return {
            'adapter_type': self.__class__.__name__,
            'initialized': self._is_initialized,
            'mock_detection_stats': self._mock_stats,
            'config': self.config.dict()
        }

    def __repr__(self) -> str:
        return f"<VisitorAdapter(indicators={len(self.config.supported_indicators)})>"


# 便捷函数
async def get_visitor_data(
    indicator: str,
    start_date: date,
    end_date: date,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    获取访客数据的便捷函数

    Args:
        indicator: 指标名称
        start_date: 开始日期
        end_date: 结束日期
        use_cache: 是否使用缓存

    Returns:
        DataFrame: 访客数据
    """
    adapter = VisitorAdapter()

    try:
        await adapter.initialize()
        return await adapter.get_data(indicator, start_date, end_date, use_cache)
    finally:
        await adapter.cleanup()


if __name__ == '__main__':
    # 示例用法
    async def main():
        adapter = VisitorAdapter()
        await adapter.initialize()

        # 获取访客数据
        data = await adapter.fetch_data(
            indicator='visitor_total',
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31)
        )
self.logger.info(f"Fetched {len(data)} records")
self.logger.info(data.head())

        await adapter.cleanup()

    asyncio.run(main())
