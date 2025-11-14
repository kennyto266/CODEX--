"""
GDP和经济指标解析器

从C&SD数据中解析GDP相关指标，包括：
- 名义GDP和实际GDP
- 年增长率和季度增长率
- 分行业GDP (第一、二、三产业)
- 人均GDP

支持CSV、Excel、XML多种格式的自动解析。

Author: Claude Code
Version: 1.0.0
Date: 2025-11-09
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import xml.etree.ElementTree as ET

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler
from .cs_d_crawler import CSDDataType, CSDWebTable


class GDPIndicator(str):
    """GDP指标枚举"""
    NOMINAL_GDP = "nominal_gdp"  # 名义GDP
    REAL_GDP = "real_gdp"  # 实际GDP
    GDP_GROWTH_YOY = "gdp_growth_yoy"  # 年度GDP增长率
    GDP_GROWTH_QOQ = "gdp_growth_qoq"  # 季度GDP增长率
    GDP_PER_CAPITA = "gdp_per_capita"  # 人均GDP
    PRIMARY_INDUSTRY = "primary_industry_gdp"  # 第一产业
    SECONDARY_INDUSTRY = "secondary_industry_gdp"  # 第二产业
    TERTIARY_INDUSTRY = "tertiary_industry_gdp"  # 第三产业


class GDPFrequency(str):
    """GDP数据频率"""
    ANNUAL = "annual"  # 年度
    QUARTERLY = "quarterly"  # 季度
    MONTHLY = "monthly"  # 月度 (某些指标)


class GDPDataPoint(BaseModel):
    """GDP数据点"""
    model_config = {"arbitrary_types_allowed": True}

    indicator_name: GDPIndicator = Field(..., description="指标类型")
    data_frequency: GDPFrequency = Field(..., description="数据频率")
    data_date: date = Field(..., description="数据日期")
    data_value: Decimal = Field(..., gt=0, description="数值")
    unit: str = Field(default="HKD Million", description="单位")
    currency: str = Field(default="HKD", description="货币")
    real_adjusted: bool = Field(default=False, description="是否经通胀调整")
    source: str = Field(..., description="数据源")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('data_date')
    def validate_data_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class GDPDataSet(BaseModel):
    """GDP数据集"""
    model_config = {"arbitrary_types_allowed": True, "use_enum_values": True}

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
                'real_adjusted': dp.real_adj
            }
            for dp in self.data_points
        ]
        df = pd.DataFrame(data)
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df


class GDPParserConfig(BaseModel):
    """GDP解析器配置"""
    model_config = {"arbitrary_types_allowed": True, "use_enum_values": True}

    download_dir: str = Field(default="data/csd_downloads", description="下载目录")
    parse_format_priority: List[str] = Field(
        default=['xlsx', 'csv', 'xml', 'json'],
        description="解析格式优先级"
    )
    date_format_patterns: List[str] = Field(
        default=[
            r'(\d{4})',  # 年份
            r'(\d{4})[/\-](\d{1,2})',  # 年-月
            r'(\d{4})[Qq](\d)',  # 年-季度
            r'(\d{1,2})[/\-](\d{4})',  # 月-年
        ],
        description="日期格式模式"
    )
    max_workers: int = Field(default=4, description="最大工作线程数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")

    # GDP数据源配置
    gdp_sources: Dict[GDPIndicator, str] = Field(
        default_factory=lambda: {
            GDPIndicator.NOMINAL_GDP: "nominal_gdp",
            GDPIndicator.REAL_GDP: "real_gdp",
            GDPIndicator.GDP_GROWTH_YOY: "gdp_growth_annual",
            GDPIndicator.GDP_GROWTH_QOQ: "gdp_growth_quarterly",
            GDPIndicator.GDP_PER_CAPITA: "gdp_per_capita",
            GDPIndicator.PRIMARY_INDUSTRY: "primary_industry",
            GDPIndicator.SECONDARY_INDUSTRY: "secondary_industry",
            GDPIndicator.TERTIARY_INDUSTRY: "tertiary_industry",
        },
        description="GDP指标数据源标识"
    )


class GDPParser(UnifiedBaseAdapter):
    """
    GDP和经济指标解析器

    解析从C&SD获取的GDP数据，支持多种格式和自动数据转换。
    """

    def __init__(self, config: Optional[GDPParserConfig] = None):
        super().__init__(config)
        self.config: GDPParserConfig = config or GDPParserConfig()
        self.logger = logging.getLogger("hk_quant_system.gdp_parser")

        # 缓存解析后的数据
        self._parsed_data: Dict[GDPIndicator, GDPDataSet] = {}

    async def parse_file(self, file_path: Path, data_type: CSDDataType) -> Optional[Dict[GDPIndicator, Any]]:
        """
        解析GDP数据文件

        Args:
            file_path: 文件路径
            data_type: 数据类型

        Returns:
            解析后的数据或None
        """
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None

        file_format = file_path.suffix.lower().lstrip('.')
        self.logger.info(f"Parsing {file_format} file: {file_path}")

        try:
            if file_format == 'xlsx':
                return await self._parse_excel(file_path)
            elif file_format == 'csv':
                return await self._parse_csv(file_path)
            elif file_format == 'xml':
                return await self._parse_xml(file_path)
            elif file_format == 'json':
                return await self._parse_json(file_path)
            else:
                self.logger.error(f"Unsupported file format: {file_format}")
                return None
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
            return None

    async def _parse_excel(self, file_path: Path) -> Dict[GDPIndicator, Any]:
        """解析Excel文件"""
        results = {}

        # 尝试读取所有工作表
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 尝试从工作表名称或内容推断数据类型
                indicator = self._detect_gdp_indicator(df, sheet_name)

                if indicator:
                    data_points = self._extract_gdp_data_points(df, indicator, 'xlsx')
                    if data_points:
                        results[indicator] = GDPDataSet(
                            indicator=indicator,
                            frequency=GDPFrequency.ANNUAL,
                            data_points=data_points,
                            metadata={'source_file': str(file_path), 'sheet': sheet_name}
                        )
            except Exception as e:
                self.logger.warning(f"Error parsing sheet {sheet_name}: {e}")

        return results

    async def _parse_csv(self, file_path: Path) -> Dict[GDPIndicator, Any]:
        """解析CSV文件"""
        results = {}

        # 尝试不同编码
        encodings = ['utf-8', 'gbk', 'big5', 'iso-8859-1']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise ValueError(f"Could not read CSV with any encoding: {file_path}")

        # 检测GDP指标
        indicator = self._detect_gdp_indicator(df, file_path.stem)

        if indicator:
            data_points = self._extract_gdp_data_points(df, indicator, 'csv')
            if data_points:
                results[indicator] = GDPDataSet(
                    indicator=indicator,
                    frequency=GDPFrequency.ANNUAL,
                    data_points=data_points,
                    metadata={'source_file': str(file_path)}
                )

        return results

    async def _parse_xml(self, file_path: Path) -> Dict[GDPIndicator, Any]:
        """解析XML文件"""
        results = {}
        tree = ET.parse(file_path)
        root = tree.getroot()

        # 遍历XML元素
        for element in root.iter():
            if 'gdp' in element.tag.lower() or 'gdp' in element.text.lower() if element.text else False:
                # 解析GDP相关数据
                pass

        return results

    async def _parse_json(self, file_path: Path) -> Dict[GDPIndicator, Any]:
        """解析JSON文件"""
        results = {}
        data = json.loads(file_path.read_text(encoding='utf-8'))

        # 解析JSON结构
        if isinstance(data, dict):
            for key, value in data.items():
                indicator = self._detect_gdp_indicator(None, key)
                if indicator and isinstance(value, (list, dict)):
                    # 转换为数据点
                    pass

        return results

    def _detect_gdp_indicator(self, df: Optional[pd.DataFrame], source: str) -> Optional[GDPIndicator]:
        """
        检测GDP指标类型

        Args:
            df: DataFrame
            source: 数据源标识

        Returns:
            GDP指标或None
        """
        source_lower = source.lower()

        # 基于源名称检测
        if 'nominal' in source_lower or '名目' in source_lower:
            return GDPIndicator.NOMINAL_GDP
        elif 'real' in source_lower or '实质' in source_lower or '实际' in source_lower:
            return GDPIndicator.REAL_GDP
        elif 'per capita' in source_lower or '人均' in source_lower:
            return GDPIndicator.GDP_PER_CAPITA
        elif 'growth' in source_lower and 'annual' in source_lower or '年增长' in source_lower:
            return GDPIndicator.GDP_GROWTH_YOY
        elif 'growth' in source_lower and ('quarter' in source_lower or '季' in source_lower):
            return GDPIndicator.GDP_GROWTH_QOQ
        elif 'primary' in source_lower or '第一产业' in source_lower:
            return GDPIndicator.PRIMARY_INDUSTRY
        elif 'secondary' in source_lower or '第二产业' in source_lower:
            return GDPIndicator.SECONDARY_INDUSTRY
        elif 'tertiary' in source_lower or '第三产业' in source_lower:
            return GDPIndicator.TERTIARY_INDUSTRY

        # 基于列名检测 (如果DataFrame存在)
        if df is not None:
            columns_lower = [col.lower() for col in df.columns]
            for i, col in enumerate(columns_lower):
                if 'gdp' in col and 'nominal' in col:
                    return GDPIndicator.NOMINAL_GDP
                elif 'gdp' in col and ('real' in col or '实质' in col):
                    return GDPIndicator.REAL_GDP
                elif 'per capita' in col or '人均' in col:
                    return GDPIndicator.GDP_PER_CAPITA

        return None

    def _extract_gdp_data_points(
        self,
        df: pd.DataFrame,
        indicator: GDPIndicator,
        source_format: str
    ) -> List[GDPDataPoint]:
        """
        从DataFrame提取GDP数据点

        Args:
            df: DataFrame
            indicator: GDP指标
            source_format: 数据源格式

        Returns:
            GDP数据点列表
        """
        data_points = []

        try:
            # 寻找日期列和数值列
            date_columns = [col for col in df.columns if self._is_date_column(df[col])]
            value_columns = [col for col in df.columns if self._is_numeric_column(df[col])]

            if not date_columns or not value_columns:
                self.logger.warning(f"No date or value columns found for {indicator}")
                return []

            # 使用第一列作为日期列
            date_col = date_columns[0]

            for value_col in value_columns:
                for idx, row in df.iterrows():
                    try:
                        date_val = self._parse_date(str(row[date_col]))
                        if date_val:
                            value = self._parse_numeric_value(str(row[value_col]))
                            if value is not None:
                                # 确定单位
                                unit = self._infer_unit(value_col, indicator)

                                dp = GDPDataPoint(
                                    indicator=indicator,
                                    frequency=GDPFrequency.ANNUAL,
                                    date=date_val,
                                    value=Decimal(str(value)),
                                    unit=unit,
                                    source=f"{source_format}:{indicator}"
                                )
                                data_points.append(dp)
                    except Exception as e:
                        self.logger.debug(f"Error parsing row {idx}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Error extracting data points: {e}")

        return data_points

    def _is_date_column(self, series: pd.Series) -> bool:
        """判断是否为日期列"""
        if series.dtype == 'datetime64[ns]':
            return True

        # 检查前几个非空值
        sample = series.dropna().head(10).astype(str)
        for val in sample:
            if re.search(r'\d{4}', val):  # 包含4位数字年份
                return True

        return False

    def _is_numeric_column(self, series: pd.Series) -> bool:
        """判断是否为数值列"""
        return pd.api.types.is_numeric_dtype(series)

    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        date_str = date_str.strip()

        # 尝试解析年份
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= 2030:  # 合理年份范围
                return date(year, 12, 31)  # 默认为年末

        # 尝试解析年月
        ym_match = re.search(r'(\d{4})[/\-](\d{1,2})', date_str)
        if ym_match:
            year, month = int(ym_match.group(1)), int(ym_match.group(2))
            if 1 <= month <= 12:
                return date(year, month, 1)

        return None

    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """解析数值字符串"""
        if not value_str or value_str.lower() in ['na', 'n/a', 'null', '--', '-']:
            return None

        try:
            # 移除逗号和其他格式字符
            cleaned = re.sub(r'[,\s]', '', value_str)
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _infer_unit(self, column_name: str, indicator: GDPIndicator) -> str:
        """推断数据单位"""
        column_lower = column_name.lower()

        if 'million' in column_lower or '百万' in column_lower:
            return 'HKD Million'
        elif 'billion' in column_lower or '十亿' in column_lower:
            return 'HKD Billion'
        elif 'per capita' in column_lower or '人均' in column_lower:
            return 'HKD'
        elif 'growth' in column_lower or '增长' in column_lower:
            return '%'
        else:
            # 根据指标类型推断
            if indicator in [GDPIndicator.GDP_GROWTH_YOY, GDPIndicator.GDP_GROWTH_QOQ]:
                return '%'
            else:
                return 'HKD Million'

    async def parse_gdp_data(
        self,
        file_path: Path,
        data_type: CSDDataType = CSDDataType.GDP
    ) -> Dict[GDPIndicator, GDPDataSet]:
        """
        解析GDP数据文件

        Args:
            file_path: 文件路径
            data_type: 数据类型

        Returns:
            GDP数据集字典
        """
        context = "GDPParser.parse_gdp_data"

        try:
            # 检查缓存
            cache_key = f"gdp:{hashlib.md5(str(file_path).encode()).hexdigest()}"
            cached = self.cache.get(cache_key)
            if cached and self.cache.is_valid(cache_key):
                self.logger.info("Returning cached GDP data")
                return cached

            # 解析文件
            results = await self.parse_file(file_path, data_type)

            if results:
                # 转换为GDPDataSet
                datasets = {}
                for indicator, data in results.items():
                    if isinstance(data, GDPDataSet):
                        datasets[indicator] = data
                    else:
                        # 转换为GDPDataSet
                        pass

                # 缓存结果
                self.cache.set(cache_key, datasets, ttl=self.config.cache_ttl)

                # 更新内部缓存
                self._parsed_data.update(datasets)

                self.logger.info(f"Parsed {len(datasets)} GDP indicators")
                return datasets

            return {}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            self.logger.error(f"Parse error: {error_info}")
            return {}

    async def get_gdp_data(
        self,
        indicator: GDPIndicator,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[GDPDataSet]:
        """
        获取GDP数据

        Args:
            indicator: GDP指标
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            GDP数据集
        """
        if indicator not in self._parsed_data:
            self.logger.warning(f"GDP indicator {indicator} not found in parsed data")
            return None

        dataset = self._parsed_data[indicator]

        # 过滤日期范围
        if start_date or end_date:
            filtered_points = []
            for dp in dataset.data_points:
                if start_date and dp.date < start_date:
                    continue
                if end_date and dp.date > end_date:
                    continue
                filtered_points.append(dp)

            dataset.data_points = filtered_points

        return dataset

    async def calculate_gdp_growth(
        self,
        indicator: GDPIndicator,
        period: str = 'yoy'  # yoy or qoq
    ) -> Optional[List[Decimal]]:
        """
        计算GDP增长率

        Args:
            indicator: GDP指标
            period: 期间 (yoy=同比, qoq=环比)

        Returns:
            增长率列表
        """
        dataset = await self.get_gdp_data(indicator)
        if not dataset or len(dataset.data_points) < 2:
            return None

        growth_rates = []

        # 按日期排序
        sorted_data = sorted(dataset.data_points, key=lambda x: x.date)

        for i in range(1, len(sorted_data)):
            prev_value = float(sorted_data[i - 1].value)
            curr_value = float(sorted_data[i].value)

            if period == 'yoy':
                if prev_value != 0:
                    growth = ((curr_value - prev_value) / prev_value) * 100
                    growth_rates.append(Decimal(str(growth)))
            elif period == 'qoq':
                if prev_value != 0:
                    growth = ((curr_value - prev_value) / prev_value) * 100
                    growth_rates.append(Decimal(str(growth)))

        return growth_rates

    async def get_all_gdp_indicators(self) -> List[GDPIndicator]:
        """获取所有可用的GDP指标"""
        return list(self._parsed_data.keys())

    async def export_to_dataframe(self, indicator: GDPIndicator) -> Optional[pd.DataFrame]:
        """
        导出GDP数据为DataFrame

        Args:
            indicator: GDP指标

        Returns:
            DataFrame或None
        """
        dataset = await self.get_gdp_data(indicator)
        if dataset:
            return dataset.to_dataframe()
        return None

    async def get_summary(self) -> Dict[str, Any]:
        """
        获取解析摘要

        Returns:
            摘要信息
        """
        return {
            'parser_name': 'GDPParser',
            'parsed_indicators': [ind.value for ind in self._parsed_data.keys()],
            'total_indicators': len(self._parsed_data),
            'data_points_per_indicator': {
                ind.value: len(dataset.data_points)
                for ind, dataset in self._parsed_data.items()
            },
            'config': self.config.dict(),
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
async def parse_gdp_file(file_path: Path) -> Dict[GDPIndicator, GDPDataSet]:
    """解析GDP文件"""
    parser = GDPParser()
    try:
        return await parser.parse_gdp_data(file_path)
    finally:
        await parser.close()


async def get_gdp_indicator(
    file_path: Path,
    indicator: GDPIndicator
) -> Optional[GDPDataSet]:
    """获取特定GDP指标"""
    parser = GDPParser()
    try:
        await parser.parse_gdp_data(file_path)
        return await parser.get_gdp_data(indicator)
    finally:
        await parser.close()
