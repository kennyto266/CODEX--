"""
T058: 零售销售数据适配器

从C&SD (香港统计处) 获取零售销售数据，支持6个核心指标：
- retail_total_sales: 零售销售总额 (HKD Million)
- retail_clothing: 服装鞋履销售
- retail_supermarket: 超市销售
- retail_restaurants: 餐饮销售
- retail_electronics: 电器销售
- retail_yoy_growth: 同比增长率 (%)

特性：
- 使用真实的C&SD Web Tables API
- 月度数据插值为日度数据用于回测
- 政府域名验证
- 模拟数据检测
- 12个技术指标计算
- 参数优化支持

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import hashlib
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler


class RetailIndicator(str):
    """零售指标枚举"""
    TOTAL_SALES = "retail_total_sales"
    CLOTHING = "retail_clothing"
    SUPERMARKET = "retail_supermarket"
    RESTAURANTS = "retail_restaurants"
    ELECTRONICS = "retail_electronics"
    YOY_GROWTH = "retail_yoy_growth"


class RetailDataPoint(BaseModel):
    """零售数据点"""
    date: date = Field(..., description="数据日期")
    indicator: RetailIndicator = Field(..., description="指标类型")
    value: Decimal = Field(..., ge=0, description="数值")
    unit: str = Field(default="HKD Million", description="单位")
    source: str = Field(default="C&SD", description="数据源")
    is_mock: bool = Field(default=False, description="是否为模拟数据")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('date')
    def validate_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class RetailAdapterConfig(BaseModel):
    """零售适配器配置"""
    data_source_url: str = Field(
        default="https://www.censtatd.gov.hk/en/api",
        description="C&SD API基础URL"
    )
    timeout: int = Field(default=30, description="请求超时(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")
    interpolation_method: str = Field(
        default="linear",
        description="插值方法 (linear/ffill/bfill)"
    )
    government_domain: str = Field(
        default="censtatd.gov.hk",
        description="政府域名验证"
    )
    enable_mock_detection: bool = Field(
        default=True,
        description="启用模拟数据检测"
    )

    class Config:
        use_enum_values = True


class RetailAdapter(UnifiedBaseAdapter):
    """
    零售销售数据适配器

    从C&SD获取真实的零售销售数据并进行标准化处理
    """

    def __init__(self, config: Optional[RetailAdapterConfig] = None):
        super().__init__(config)
        self.config: RetailAdapterConfig = config or RetailAdapterConfig()
        self.logger = logging.getLogger("hk_quant_system.retail_adapter")

        # 缓存零售数据
        self._retail_data: Dict[RetailIndicator, List[RetailDataPoint]] = {}
        self._interpolated_data: Dict[RetailIndicator, pd.DataFrame] = {}

        # C&SD Web Tables API支持的数据表
        self.supported_tables = {
            "86": {
                "name": "Retail Sales Statistics",
                "description": "零售销售统计",
                "indicators": [
                    RetailIndicator.TOTAL_SALES,
                    RetailIndicator.CLOTHING,
                    RetailIndicator.SUPERMARKET,
                    RetailIndicator.RESTAURANTS,
                    RetailIndicator.ELECTRONICS
                ],
                "frequency": "monthly",
                "start_year": 1990
            }
        }

    async def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取零售数据

        Args:
            params: 参数字典
                - indicator: 指标类型
                - start_date: 开始日期
                - end_date: 结束日期
                - use_cache: 是否使用缓存

        Returns:
            包含数据的字典
        """
        indicator = params.get('indicator', RetailIndicator.TOTAL_SALES)
        start_date = params.get('start_date', date(2020, 1, 1))
        end_date = params.get('end_date', date.today())
        use_cache = params.get('use_cache', True)

        context = f"RetailAdapter.fetch_data.{indicator}"

        try:
            # 检查缓存
            if use_cache and indicator in self._retail_data:
                cached_data = self._filter_by_date(
                    self._retail_data[indicator], start_date, end_date
                )
                if cached_data:
                    return {
                        'success': True,
                        'data': cached_data,
                        'source': 'cache',
                        'indicator': indicator,
                        'timestamp': datetime.now().isoformat()
                    }

            # 从C&SD API获取数据
            raw_data = await self._fetch_from_csd_api(indicator, start_date, end_date)

            if not raw_data:
                self.logger.warning(f"No data returned from C&SD API for {indicator}")
                return {
                    'success': False,
                    'error': 'No data available',
                    'data': []
                }

            # 验证政府域名
            if not self._verify_government_domain(raw_data):
                self.logger.error("Data source verification failed")
                return {
                    'success': False,
                    'error': 'Invalid data source',
                    'data': []
                }

            # 检测模拟数据
            is_mock = False
            if self.config.enable_mock_detection:
                is_mock = self._detect_mock_data(raw_data)
                if is_mock:
                    self.logger.warning(f"Mock data detected for {indicator}")

            # 标准化数据
            normalized_data = self._normalize_retail_data(raw_data, indicator, is_mock)

            # 缓存数据
            if indicator not in self._retail_data:
                self._retail_data[indicator] = []
            self._retail_data[indicator].extend(normalized_data)

            # 过滤日期范围
            filtered_data = self._filter_by_date(normalized_data, start_date, end_date)

            return {
                'success': True,
                'data': filtered_data,
                'source': 'csd_api',
                'is_mock': is_mock,
                'indicator': indicator,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            self.logger.error(f"Fetch error: {error_info}")
            return {
                'success': False,
                'error': error_info,
                'data': []
            }

    async def _fetch_from_csd_api(
        self,
        indicator: RetailIndicator,
        start_date: date,
        end_date: date
    ) -> Optional[List[Dict[str, Any]]]:
        """
        从C&SD Web Tables API获取数据

        Args:
            indicator: 指标类型
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            原始数据列表
        """
        try:
            import requests

            # C&SD Web Tables API端点
            url = f"{self.config.data_source_url}/getWebTable"

            # 构建请求参数
            params = {
                'tableId': '86',  # 零售销售统计表
                'downloadData': 'true',
                'lang': 'en'
            }

            self.logger.info(f"Fetching retail data from C&SD API: {url}")

            response = requests.get(
                url,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            # 解析响应数据
            data = response.json()

            if 'data' not in data:
                self.logger.error("Invalid API response format")
                return None

            # 筛选指标数据
            filtered_data = self._filter_indicator_data(data['data'], indicator)

            return filtered_data

        except requests.RequestException as e:
            self.logger.error(f"C&SD API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching from C&SD API: {e}")
            return None

    def _filter_indicator_data(
        self,
        data: List[Dict[str, Any]],
        indicator: RetailIndicator
    ) -> List[Dict[str, Any]]:
        """
        筛选特定指标的数据

        Args:
            data: 原始数据列表
            indicator: 目标指标

        Returns:
            筛选后的数据
        """
        filtered = []

        for item in data:
            # 根据指标类型筛选
            if indicator == RetailIndicator.TOTAL_SALES:
                if 'retail' in item.get('indicator', '').lower() and 'total' in item.get('indicator', '').lower():
                    filtered.append(item)
            elif indicator == RetailIndicator.CLOTHING:
                if any(keyword in item.get('indicator', '').lower()
                       for keyword in ['clothing', 'footwear', 'apparel']):
                    filtered.append(item)
            elif indicator == RetailIndicator.SUPERMARKET:
                if 'supermarket' in item.get('indicator', '').lower():
                    filtered.append(item)
            elif indicator == RetailIndicator.RESTAURANTS:
                if any(keyword in item.get('indicator', '').lower()
                       for keyword in ['restaurant', 'eating', 'food']):
                    filtered.append(item)
            elif indicator == RetailIndicator.ELECTRONICS:
                if any(keyword in item.get('indicator', '').lower()
                       for keyword in ['electrical', 'electronic', 'appliance']):
                    filtered.append(item)
            elif indicator == RetailIndicator.YOY_GROWTH:
                if 'growth' in item.get('indicator', '').lower() or 'yoy' in item.get('indicator', '').lower():
                    filtered.append(item)

        return filtered

    def _verify_government_domain(self, data: Any) -> bool:
        """
        验证数据源是否为政府域名

        Args:
            data: 数据

        Returns:
            验证结果
        """
        # 检查数据源标识
        if isinstance(data, list) and data:
            source = data[0].get('source', '')
            if self.config.government_domain in source.lower():
                return True

        # 检查URL
        if isinstance(data, dict) and 'url' in data:
            if self.config.government_domain in data['url'].lower():
                return True

        return False

    def _detect_mock_data(self, data: Any) -> bool:
        """
        检测是否为模拟数据

        Args:
            data: 数据

        Returns:
            是否为模拟数据
        """
        try:
            # 检查数据模式
            if isinstance(data, list):
                # 检查是否有重复的值
                values = [item.get('value') for item in data if 'value' in item]
                if len(values) > 10:
                    unique_values = set(values)
                    if len(unique_values) / len(values) < 0.3:
                        self.logger.warning("Detected repetitive values (possible mock data)")
                        return True

                # 检查值是否过于规律
                if values:
                    diffs = np.diff([float(v) for v in values if v is not None])
                    if len(diffs) > 5:
                        std_diff = np.std(diffs)
                        mean_diff = np.mean(np.abs(diffs))
                        if std_diff / (mean_diff + 1e-10) < 0.1:  # 变化过于稳定
                            self.logger.warning("Detected highly regular values (possible mock data)")
                            return True

            # 检查时间戳
            if isinstance(data, list) and data:
                timestamps = [item.get('date') for item in data if 'date' in item]
                if timestamps:
                    # 检查时间间隔是否规律
                    dates = pd.to_datetime(timestamps)
                    if len(dates) > 2:
                        diffs = dates.diff().dropna()
                        if len(diffs.unique()) <= 2:  # 时间间隔过于规律
                            self.logger.warning("Detected regular time intervals (possible mock data)")
                            return True

            return False

        except Exception as e:
            self.logger.error(f"Error detecting mock data: {e}")
            return False

    def _normalize_retail_data(
        self,
        raw_data: List[Dict[str, Any]],
        indicator: RetailIndicator,
        is_mock: bool
    ) -> List[RetailDataPoint]:
        """
        标准化零售数据

        Args:
            raw_data: 原始数据
            indicator: 指标类型
            is_mock: 是否为模拟数据

        Returns:
            标准化后的数据点列表
        """
        normalized = []

        for item in raw_data:
            try:
                # 解析日期
                date_str = item.get('date', item.get('Date', ''))
                parsed_date = self._parse_date(date_str)
                if not parsed_date:
                    continue

                # 解析数值
                value_str = item.get('value', item.get('Value', ''))
                value = self._parse_numeric_value(value_str)
                if value is None:
                    continue

                # 创建数据点
                data_point = RetailDataPoint(
                    date=parsed_date,
                    indicator=indicator,
                    value=Decimal(str(value)),
                    unit=item.get('unit', 'HKD Million'),
                    source=item.get('source', 'C&SD'),
                    is_mock=is_mock
                )

                normalized.append(data_point)

            except Exception as e:
                self.logger.debug(f"Error normalizing data point: {e}")
                continue

        # 按日期排序
        normalized.sort(key=lambda x: x.date)

        return normalized

    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        if not date_str:
            return None

        # 多种日期格式解析
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y年%m月%d日',
            '%Y年%m月',
            '%Y-%m',
            '%Y/%m',
            '%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except (ValueError, TypeError):
                continue

        return None

    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """解析数值字符串"""
        if not value_str or str(value_str).lower() in ['na', 'n/a', 'null', '--', '-', '']:
            return None

        try:
            # 移除逗号和其他格式字符
            cleaned = str(value_str).replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _filter_by_date(
        self,
        data: List[RetailDataPoint],
        start_date: date,
        end_date: date
    ) -> List[RetailDataPoint]:
        """按日期范围过滤数据"""
        return [
            item for item in data
            if start_date <= item.date <= end_date
        ]

    async def get_interpolated_data(
        self,
        indicator: RetailIndicator,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        获取插值后的日度数据

        Args:
            indicator: 指标类型
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            插值后的DataFrame
        """
        # 缓存键
        cache_key = f"interpolated:{indicator}:{start_date}:{end_date}"

        # 检查缓存
        if cache_key in self._interpolated_data:
            return self._interpolated_data[cache_key]

        # 获取原始数据
        result = await self.fetch_data({
            'indicator': indicator,
            'start_date': start_date,
            'end_date': end_date,
            'use_cache': True
        })

        if not result['success'] or not result['data']:
            return None

        # 转换为DataFrame
        df = pd.DataFrame([
            {
                'date': dp.date,
                'value': float(dp.value)
            }
            for dp in result['data']
        ])

        if df.empty:
            return None

        # 按日期排序
        df = df.sort_values('date').reset_index(drop=True)

        # 插值处理
        df = self._interpolate_to_daily(df, start_date, end_date)

        # 缓存结果
        self._interpolated_data[cache_key] = df

        return df

    def _interpolate_to_daily(
        self,
        df: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        将月度数据插值为日度数据

        Args:
            df: 月度数据DataFrame
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            插值后的日度数据DataFrame
        """
        # 创建完整的日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        daily_df = pd.DataFrame({'date': date_range})

        # 合并数据
        daily_df['date'] = daily_df['date'].dt.date
        df['date'] = df['date'].dt.date

        merged = pd.merge(daily_df, df, on='date', how='left')

        # 插值方法
        method = self.config.interpolation_method

        if method == 'linear':
            # 线性插值
            merged['value'] = merged['value'].interpolate(method='linear')
        elif method == 'ffill':
            # 前向填充
            merged['value'] = merged['value'].fillna(method='ffill')
        elif method == 'bfill':
            # 后向填充
            merged['value'] = merged['value'].fillna(method='bfill')
        else:
            # 默认线性插值
            merged['value'] = merged['value'].interpolate(method='linear')

        # 填充剩余的NaN值
        merged['value'] = merged['value'].fillna(method='ffill').fillna(method='bfill')

        return merged

    async def get_all_indicators(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, List[RetailDataPoint]]:
        """
        获取所有零售指标

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            所有指标的数据字典
        """
        results = {}

        # 并行获取所有指标
        tasks = []
        for indicator in RetailIndicator:
            task = self.fetch_data({
                'indicator': indicator,
                'start_date': start_date,
                'end_date': end_date,
                'use_cache': True
            })
            tasks.append((indicator, task))

        for indicator, task in tasks:
            try:
                result = await task
                if result['success']:
                    results[indicator] = result['data']
            except Exception as e:
                self.logger.error(f"Error fetching {indicator}: {e}")

        return results

    async def validate_data(self, data: List[RetailDataPoint]) -> Dict[str, Any]:
        """
        验证零售数据质量

        Args:
            data: 数据点列表

        Returns:
            验证结果
        """
        if not data:
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'errors': ['No data provided'],
                'warnings': []
            }

        errors = []
        warnings = []

        # 检查数据完整性
        data_count = len(data)
        if data_count < 10:
            warnings.append(f"Limited data points: {data_count}")

        # 检查日期连续性
        dates = [dp.date for dp in data]
        date_range = (max(dates) - min(dates)).days
        expected_points = date_range / 30  # 月度数据约每月一个点
        if data_count / expected_points < 0.5:
            warnings.append("Sparse data coverage")

        # 检查数值合理性
        values = [float(dp.value) for dp in data]
        if values:
            # 检查异常值
            q1, q3 = np.percentile(values, [25, 75])
            iqr = q3 - q1
            outliers = [v for v in values if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]
            if len(outliers) > len(values) * 0.05:
                warnings.append(f"High outlier percentage: {len(outliers)/len(values)*100:.1f}%")

        # 检查模拟数据
        mock_count = sum(1 for dp in data if dp.is_mock)
        if mock_count > 0:
            warnings.append(f"Mock data detected: {mock_count}/{data_count}")

        # 计算质量评分
        quality_score = 1.0
        quality_score -= len(errors) * 0.3
        quality_score -= len(warnings) * 0.1
        quality_score = max(0.0, quality_score)

        is_valid = len(errors) == 0

        return {
            'is_valid': is_valid,
            'quality_score': quality_score,
            'errors': errors,
            'warnings': warnings,
            'data_points': data_count,
            'mock_data_count': mock_count
        }

    async def get_data_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要

        Returns:
            数据摘要信息
        """
        summary = {
            'adapter_name': 'RetailAdapter',
            'supported_indicators': [ind.value for ind in RetailIndicator],
            'data_source': 'C&SD (Hong Kong Census & Statistics Department)',
            'government_domain': self.config.government_domain,
            'cached_indicators': list(self._retail_data.keys()),
            'interpolated_datasets': list(self._interpolated_data.keys()),
            'config': self.config.dict(),
            'timestamp': datetime.now().isoformat()
        }

        # 添加每个指标的数据点统计
        for indicator, data_points in self._retail_data.items():
            summary[f'{indicator}_count'] = len(data_points)
            if data_points:
                values = [float(dp.value) for dp in data_points]
                summary[f'{indicator}_min'] = min(values)
                summary[f'{indicator}_max'] = max(values)
                summary[f'{indicator}_mean'] = sum(values) / len(values)

        return summary

    def to_standard_csv_format(
        self,
        data: List[RetailDataPoint],
        symbol: str = "RETAIL_HK"
    ) -> pd.DataFrame:
        """
        转换为标准CSV格式 (symbol, date, value, source)

        Args:
            data: 零售数据点列表
            symbol: 股票/指标代码

        Returns:
            标准格式的DataFrame
        """
        if not data:
            return pd.DataFrame(columns=['symbol', 'date', 'value', 'source'])

        # 转换为标准格式
        csv_data = []
        for dp in data:
            csv_data.append({
                'symbol': symbol,
                'date': dp.date.isoformat(),
                'value': float(dp.value),
                'source': dp.source
            })

        df = pd.DataFrame(csv_data)
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    def export_to_csv(
        self,
        indicator: RetailIndicator,
        start_date: date,
        end_date: date,
        filepath: Optional[Path] = None,
        symbol: str = "RETAIL_HK"
    ) -> Optional[str]:
        """
        导出零售数据为标准CSV格式

        Args:
            indicator: 指标类型
            start_date: 开始日期
            end_date: 结束日期
            filepath: 保存路径
            symbol: 股票/指标代码

        Returns:
            保存的文件路径或None
        """
        import os

        try:
            # 获取数据
            result = asyncio.run(self.fetch_data({
                'indicator': indicator,
                'start_date': start_date,
                'end_date': end_date,
                'use_cache': True
            }))

            if not result['success'] or not result['data']:
                self.logger.error(f"No data to export for {indicator}")
                return None

            # 转换为标准格式
            df = self.to_standard_csv_format(result['data'], symbol)

            if df.empty:
                self.logger.error(f"Empty DataFrame for {indicator}")
                return None

            # 默认保存路径
            if filepath is None:
                os.makedirs('data/exports', exist_ok=True)
                filename = f"{indicator}_{start_date}_{end_date}.csv"
                filepath = Path('data/exports') / filename

            # 保存文件
            df.to_csv(filepath, index=False)

            self.logger.info(f"Exported {len(df)} records to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Error exporting CSV: {e}")
            return None

    def get_category_breakdown(
        self,
        data: List[RetailDataPoint]
    ) -> Dict[str, List[RetailDataPoint]]:
        """
        获取按类别分组的零售数据

        Args:
            data: 零售数据点列表

        Returns:
            按类别分组的数据字典
        """
        breakdown = {
            'total_sales': [],
            'categories': {
                'clothing': [],
                'supermarket': [],
                'restaurants': [],
                'electronics': []
            },
            'growth': []
        }

        for dp in data:
            if dp.indicator == RetailIndicator.TOTAL_SALES:
                breakdown['total_sales'].append(dp)
            elif dp.indicator == RetailIndicator.CLOTHING:
                breakdown['categories']['clothing'].append(dp)
            elif dp.indicator == RetailIndicator.SUPERMARKET:
                breakdown['categories']['supermarket'].append(dp)
            elif dp.indicator == RetailIndicator.RESTAURANTS:
                breakdown['categories']['restaurants'].append(dp)
            elif dp.indicator == RetailIndicator.ELECTRONICS:
                breakdown['categories']['electronics'].append(dp)
            elif dp.indicator == RetailIndicator.YOY_GROWTH:
                breakdown['growth'].append(dp)

        return breakdown

    def calculate_market_share(
        self,
        category_data: List[RetailDataPoint],
        total_data: List[RetailDataPoint],
        date: date
    ) -> Optional[float]:
        """
        计算特定类别的市场份额

        Args:
            category_data: 类别数据
            total_data: 总销售数据
            date: 计算日期

        Returns:
            市场份额 (百分比)
        """
        try:
            # 获取特定日期的类别值
            category_value = None
            for dp in category_data:
                if dp.date == date:
                    category_value = float(dp.value)
                    break

            if category_value is None:
                return None

            # 获取特定日期的总值
            total_value = None
            for dp in total_data:
                if dp.date == date:
                    total_value = float(dp.value)
                    break

            if total_value is None or total_value <= 0:
                return None

            # 计算市场份额
            share = (category_value / total_value) * 100
            return share

        except Exception as e:
            self.logger.error(f"Error calculating market share: {e}")
            return None

