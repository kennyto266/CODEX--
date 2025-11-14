"""
GDP数据适配器

从香港特别行政区政府统计处(C&SD)获取GDP数据，支持：
- 名义GDP和实际GDP
- 年增长率和季度增长率
- 分行业GDP (第一、二、三产业)
- 季度数据插值为日度数据用于回测

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import warnings

import numpy as np
import pandas as pd
import requests
from pydantic import BaseModel, Field, validator

from .base_adapter import BaseDataAdapter, DataAdapterConfig, DataSourceType, DataValidationResult
from .cs_d_crawler import CSDDataType


class GDPIndicator(str):
    """GDP指标枚举"""
    NOMINAL_GDP = "gdp_nominal"  # 名义GDP
    REAL_GDP = "gdp_real"  # 实际GDP
    GDP_GROWTH_YOY = "gdp_growth"  # 年增长率
    GDP_GROWTH_QOQ = "gdp_growth_qoq"  # 季度增长率
    GDP_PER_CAPITA = "gdp_per_capita"  # 人均GDP
    PRIMARY_SECTOR = "gdp_primary"  # 第一产业占比
    SECONDARY_SECTOR = "gdp_secondary"  # 第二产业占比
    TERTIARY_SECTOR = "gdp_tertiary"  # 第三产业占比


class GDPFrequency(str):
    """GDP数据频率"""
    ANNUAL = "annual"  # 年度
    QUARTERLY = "quarterly"  # 季度
    MONTHLY = "monthly"  # 月度


class GDPDataPoint(BaseModel):
    """GDP数据点"""
    indicator: GDPIndicator = Field(..., description="指标类型")
    frequency: GDPFrequency = Field(..., description="数据频率")
    date: date = Field(..., description="数据日期")
    value: Decimal = Field(..., gt=0, description="数值")
    unit: str = Field(default="HKD Million", description="单位")
    currency: str = Field(default="HKD", description="货币")
    real_adj: bool = Field(default=False, description="是否经通胀调整")
    source: str = Field(..., description="数据源")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    is_mock: bool = Field(default=False, description="是否为模拟数据")

    @validator('date')
    def validate_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class GDPDataSet(BaseModel):
    """GDP数据集"""
    indicator: GDPIndicator = Field(..., description="指标")
    frequency: GDPFrequency = Field(..., description="频率")
    data_points: List[GDPDataPoint] = Field(default_factory=list, description="数据点")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    latest_value: Optional[Decimal] = Field(None, description="最新值")
    latest_date: Optional[date] = Field(None, description="最新日期")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        if not self.data_points:
            return pd.DataFrame()

        data = [
            {
                'date': dp.date,
                'value': float(dp.value),
                'unit': dp.unit,
                'currency': dp.currency,
                'real_adjusted': dp.real_adj,
                'is_mock': dp.is_mock
            }
            for dp in self.data_points
        ]
        df = pd.DataFrame(data)
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def interpolate_to_daily(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> pd.DataFrame:
        """
        将季度或年度数据插值为日度数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            插值后的日度DataFrame
        """
        if not self.data_points:
            return pd.DataFrame()

        # 转换为基础DataFrame
        df = self.to_dataframe()
        if df.empty:
            return df

        # 设置日期为索引
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # 过滤日期范围
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        # 重新采样到日度
        df_daily = df.resample('D').ffill()

        # 插值填充
        df_daily['value'] = df_daily['value'].interpolate(method='linear')

        # 重置索引
        df_daily.reset_index(inplace=True)

        return df_daily


class GDPAdapterConfig(BaseModel):
    """GDP适配器配置"""
    base_url: str = Field(default="https://www.censtatd.gov.hk", description="C&SD基础URL")
    api_timeout: int = Field(default=30, description="API超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")
    interpolation_method: str = Field(default="linear", description="插值方法")
    validate_government_domain: bool = Field(default=True, description="验证政府域名")
    detect_mock_data: bool = Field(default=True, description="检测模拟数据")


class GDPAdapter(BaseDataAdapter):
    """
    GDP数据适配器

    从C&SD获取GDP数据并进行预处理
    """

    def __init__(self, config: Optional[GDPAdapterConfig] = None):
        self.config = config or GDPAdapterConfig()
        data_config = DataAdapterConfig(
            source_type=DataSourceType.CUSTOM,
            source_path=self.config.base_url,
            timeout=self.config.api_timeout,
            max_retries=self.config.max_retries
        )
        super().__init__(data_config)
        self.logger = logging.getLogger("hk_quant_system.gdp_adapter")
        self._parsed_data: Dict[GDPIndicator, GDPDataSet] = {}
        self._cache_dir = Path("data/gdp_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> bool:
        """
        连接到C&SD数据源

        Returns:
            bool: 连接是否成功
        """
        try:
            # 测试连接
            response = requests.get(
                f"{self.config.base_url}/en/",
                timeout=self.config.api_timeout
            )
            connected = response.status_code == 200
            self.logger.info(f"C&SD connection test: {'success' if connected else 'failed'}")
            return connected
        except Exception as e:
            self.logger.error(f"Failed to connect to C&SD: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        断开数据源连接

        Returns:
            bool: 断开是否成功
        """
        self.logger.info("C&SD adapter disconnected")
        return True

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List:
        """
        获取GDP数据 (实现抽象方法)

        Args:
            symbol: 指标代码 (e.g., "gdp_nominal", "gdp_growth")
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据列表 (为了兼容BaseDataAdapter接口)
        """
        # 转换为GDPIndicator
        try:
            indicator = GDPIndicator(symbol)
        except ValueError:
            self.logger.error(f"Invalid GDP indicator: {symbol}")
            return []

        dataset = await self.get_gdp_data(indicator, start_date, end_date)
        if not dataset:
            return []

        # 转换为日度数据
        df = dataset.interpolate_to_daily(start_date, end_date)
        return df.to_dict('records') if not df.empty else []

    async def validate_data(self, data: List) -> DataValidationResult:
        """
        验证GDP数据

        Args:
            data: 待验证的数据列表

        Returns:
            验证结果
        """
        errors = []
        warnings_list = []
        quality_score = 1.0

        if not data:
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level="UNKNOWN",
                errors=["No data provided"],
                warnings=[],
                metadata={}
            )

        # 检查政府域名验证
        if self.config.validate_government_domain:
            # 验证数据源是否来自政府域名
            source_valid = all(
                isinstance(item, dict) and
                item.get('source', '').startswith(('censtatd.gov.hk', 'gov.hk'))
                for item in data
            )
            if not source_valid:
                errors.append("Data source is not from verified government domain")
                quality_score -= 0.3

        # 检查模拟数据检测
        if self.config.detect_mock_data:
            mock_count = sum(1 for item in data if item.get('is_mock', False))
            if mock_count > 0:
                warnings_list.append(f"Detected {mock_count} mock data points")
                quality_score -= 0.2 * (mock_count / len(data))

        # 检查数据完整性
        null_values = sum(1 for item in data if not item.get('value'))
        if null_values > 0:
            errors.append(f"Found {null_values} null values")
            quality_score -= 0.3

        # 检查数值合理性
        negative_count = sum(1 for item in data if item.get('value', 0) < 0)
        if negative_count > 0 and negative_count < len(data):
            warnings_list.append(f"Found {negative_count} negative values")

        # 确定质量等级
        if quality_score >= 0.9:
            quality_level = "EXCELLENT"
        elif quality_score >= 0.8:
            quality_level = "GOOD"
        elif quality_score >= 0.6:
            quality_level = "FAIR"
        elif quality_score >= 0.4:
            quality_level = "POOR"
        else:
            quality_level = "UNKNOWN"

        is_valid = len(errors) == 0

        return DataValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            quality_level=quality_level,
            errors=errors,
            warnings=warnings_list,
            metadata={
                'total_records': len(data),
                'null_values': null_values,
                'negative_count': negative_count,
                'mock_data_count': mock_count if self.config.detect_mock_data else 0
            }
        )

    async def transform_data(self, raw_data: Any) -> List:
        """
        转换原始数据为标准格式

        Args:
            raw_data: 原始数据

        Returns:
            转换后的标准数据
        """
        # 如果是字典列表，直接返回
        if isinstance(raw_data, list) and all(isinstance(item, dict) for item in raw_data):
            return raw_data

        # 如果是DataFrame，转换为字典列表
        if isinstance(raw_data, pd.DataFrame):
            return raw_data.to_dict('records')

        self.logger.error(f"Unsupported data format: {type(raw_data)}")
        return []

    async def get_gdp_data(
        self,
        indicator: GDPIndicator,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[GDPDataSet]:
        """
        获取特定GDP指标数据

        Args:
            indicator: GDP指标
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            GDP数据集
        """
        # 检查缓存
        cache_key = f"gdp:{indicator.value}:{start_date or 'all'}:{end_date or 'all'}"
        cached = self.get_cache(cache_key)
        if cached:
            self.logger.info(f"Returning cached GDP data for {indicator}")
            return cached

        try:
            # 从C&SD获取数据
            data = await self._fetch_from_csd(indicator)
            if not data:
                self.logger.error(f"No data received for {indicator}")
                return None

            # 验证数据
            validation_result = await self.validate_data(data)
            if not validation_result.is_valid:
                self.logger.warning(f"Data validation failed: {validation_result.errors}")

            # 转换为GDPDataSet
            dataset = await self._build_dataset(indicator, data)
            if dataset:
                # 缓存结果
                self.set_cache(cache_key, dataset)
                return dataset

            return None

        except Exception as e:
            self.logger.error(f"Error getting GDP data: {e}")
            return None

    async def _fetch_from_csd(self, indicator: GDPIndicator) -> Optional[List[Dict]]:
        """
        从C&SD获取数据

        Args:
            indicator: GDP指标

        Returns:
            原始数据列表
        """
        try:
            # 尝试从C&SD Web Tables API获取数据
            # 注意：实际实现需要根据C&SD的具体API格式调整
            url = f"{self.config.base_url}/api/web_table"
            params = {
                'table_id': self._get_table_id(indicator),
                'download': 'json'
            }

            self.logger.info(f"Fetching {indicator} from C&SD")
            response = requests.get(
                url,
                params=params,
                timeout=self.config.api_timeout
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_csd_response(indicator, data)

            # 如果API不可用，尝试从数据文件读取
            return await self._fetch_from_cache_file(indicator)

        except Exception as e:
            self.logger.error(f"Error fetching from C&SD: {e}")
            # 回退到缓存文件
            return await self._fetch_from_cache_file(indicator)

    def _get_table_id(self, indicator: GDPIndicator) -> str:
        """获取C&SD表格ID"""
        table_map = {
            GDPIndicator.NOMINAL_GDP: "33",
            GDPIndicator.REAL_GDP: "33",
            GDPIndicator.GDP_GROWTH_YOY: "33",
            GDPIndicator.GDP_GROWTH_QOQ: "33",
            GDPIndicator.PRIMARY_SECTOR: "33",
            GDPIndicator.SECONDARY_SECTOR: "33",
            GDPIndicator.TERTIARY_SECTOR: "33",
        }
        return table_map.get(indicator, "33")

    def _parse_csd_response(self, indicator: GDPIndicator, data: Dict) -> List[Dict]:
        """
        解析C&SD响应

        Args:
            indicator: GDP指标
            data: 原始响应

        Returns:
            解析后的数据列表
        """
        results = []

        try:
            # 解析JSON响应
            if 'data' in data:
                for item in data['data']:
                    date_str = item.get('date', '')
                    value_str = item.get('value', '')

                    # 解析日期
                    parsed_date = self._parse_date(date_str)
                    if not parsed_date:
                        continue

                    # 解析数值
                    parsed_value = self._parse_numeric_value(value_str)
                    if parsed_value is None:
                        continue

                    results.append({
                        'date': parsed_date,
                        'value': parsed_value,
                        'unit': item.get('unit', 'HKD Million'),
                        'currency': item.get('currency', 'HKD'),
                        'real_adjusted': item.get('real_adjusted', False),
                        'source': f"censtatd.gov.hk",
                        'is_mock': False
                    })

        except Exception as e:
            self.logger.error(f"Error parsing C&SD response: {e}")

        return results

    async def _fetch_from_cache_file(self, indicator: GDPIndicator) -> Optional[List[Dict]]:
        """
        从缓存文件获取数据

        Args:
            indicator: GDP指标

        Returns:
            缓存数据列表
        """
        cache_file = self._cache_dir / f"{indicator.value}.json"

        if not cache_file.exists():
            self.logger.warning(f"Cache file not found: {cache_file}")
            return []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"Loaded {len(data)} records from cache")
            return data
        except Exception as e:
            self.logger.error(f"Error reading cache file: {e}")
            return []

    async def _build_dataset(
        self,
        indicator: GDPIndicator,
        data: List[Dict]
    ) -> Optional[GDPDataSet]:
        """
        构建GDP数据集

        Args:
            indicator: GDP指标
            data: 数据列表

        Returns:
            GDP数据集
        """
        if not data:
            return None

        try:
            # 构建数据点
            data_points = []
            for item in data:
                dp = GDPDataPoint(
                    indicator=indicator,
                    frequency=GDPFrequency.QUARTERLY,  # GDP通常为季度数据
                    date=item['date'],
                    value=Decimal(str(item['value'])),
                    unit=item.get('unit', 'HKD Million'),
                    currency=item.get('currency', 'HKD'),
                    real_adj=item.get('real_adjusted', False),
                    source=item.get('source', 'censtatd.gov.hk'),
                    is_mock=item.get('is_mock', True)  # 默认为模拟数据直到验证
                )
                data_points.append(dp)

            # 按日期排序
            data_points.sort(key=lambda x: x.date)

            # 获取统计信息
            values = [float(dp.value) for dp in data_points]
            latest_value = max(values) if values else None
            latest_date = max(dp.date for dp in data_points) if data_points else None

            dataset = GDPDataSet(
                indicator=indicator,
                frequency=GDPFrequency.QUARTERLY,
                data_points=data_points,
                start_date=data_points[0].date if data_points else None,
                end_date=data_points[-1].date if data_points else None,
                latest_value=latest_value,
                latest_date=latest_date,
                metadata={
                    'total_records': len(data_points),
                    'value_range': {
                        'min': min(values) if values else None,
                        'max': max(values) if values else None
                    },
                    'cache_source': 'csd_api' if not data_points[0].is_mock else 'cache_file'
                }
            )

            return dataset

        except Exception as e:
            self.logger.error(f"Error building dataset: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        date_str = date_str.strip()

        # 尝试解析年份
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= 2030:
                return date(year, 12, 31)

        # 尝试解析季度
        q_match = re.search(r'(\d{4})[Qq](\d)', date_str)
        if q_match:
            year, quarter = int(q_match.group(1)), int(q_match.group(2))
            month = quarter * 3  # Q1=3, Q2=6, Q3=9, Q4=12
            return date(year, month, 1)

        # 尝试解析年月
        ym_match = re.search(r'(\d{4})[/\-](\d{1,2})', date_str)
        if ym_match:
            year, month = int(ym_match.group(1)), int(ym_match.group(2))
            if 1 <= month <= 12:
                return date(year, month, 1)

        return None

    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """解析数值字符串"""
        if not value_str or str(value_str).lower() in ['na', 'n/a', 'null', '--', '-', 'n.a.']:
            return None

        try:
            # 移除逗号和空格
            cleaned = re.sub(r'[,\s]', '', str(value_str))
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    async def normalize_gdp_data(self, dataset: GDPDataSet) -> GDPDataSet:
        """
        标准化GDP数据

        Args:
            dataset: 原始数据集

        Returns:
            标准化后的数据集
        """
        self.logger.info(f"Normalizing {dataset.indicator}")

        normalized_points = []
        for dp in dataset.data_points:
            # 标准化单位
            if dp.unit == 'HKD Billion':
                dp.value = dp.value * 1000  # 转换为百万
                dp.unit = 'HKD Million'
            elif dp.unit == 'HKD Thousand':
                dp.value = dp.value / 1000  # 转换为百万
                dp.unit = 'HKD Million'

            # 标准化百分比
            if dp.unit == '%' and dp.value > 1:
                dp.value = dp.value / 100  # 转换为小数

            normalized_points.append(dp)

        dataset.data_points = normalized_points
        return dataset

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            connected = await self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "adapter": "GDPAdapter",
                "source": "censtatd.gov.hk",
                "parsed_indicators": [ind.value for ind in self._parsed_data.keys()],
                "cache_dir": str(self._cache_dir),
                "config": self.config.dict()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "adapter": "GDPAdapter"
            }


# 便捷函数
async def get_gdp_data(
    indicator: GDPIndicator,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Optional[GDPDataSet]:
    """获取GDP数据"""
    adapter = GDPAdapter()
    try:
        await adapter.connect()
        return await adapter.get_gdp_data(indicator, start_date, end_date)
    finally:
        await adapter.disconnect()


async def normalize_gdp_datasets(
    datasets: List[GDPDataSet]
) -> List[GDPDataSet]:
    """标准化多个GDP数据集"""
    results = []
    for dataset in datasets:
        adapter = GDPAdapter()
        try:
            normalized = await adapter.normalize_gdp_data(dataset)
            results.append(normalized)
        finally:
            await adapter.disconnect()
    return results
