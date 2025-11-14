"""
访港旅客数据处理器

从C&SD数据中解析访港旅客相关指标，包括：
- 总访港旅客
- 内地旅客
- 台湾旅客
- 澳门旅客
- 其他地区旅客
- 日均访客数量

支持按日、月、季度统计分析。

Author: Claude Code
Version: 1.0.0
Date: 2025-11-09
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler
from .cs_d_crawler import CSDDataType


class VisitorType(str):
    """访客类型枚举"""
    TOTAL_VISITORS = "total_visitors"  # 总访港旅客
    MAINLAND_CHINA = "mainland_china_visitors"  # 内地旅客
    TAIWAN = "taiwan_visitors"  # 台湾旅客
    MACAU = "macau_visitors"  # 澳门旅客
    OTHER_ASIA = "other_asia_visitors"  # 其他亚洲地区
    EUROPE = "europe_visitors"  # 欧洲
    NORTH_AMERICA = "north_america_visitors"  # 北美
    AUSTRALASIA = "australasia_visitors"  # 澳新
    OTHER_REGIONS = "other_regions"  # 其他地区
    DAILY_AVERAGE = "daily_average_visitors"  # 日均访客数量


class VisitorFrequency(str):
    """访客数据频率"""
    DAILY = "daily"  # 日度
    MONTHLY = "monthly"  # 月度
    QUARTERLY = "quarterly"  # 季度
    ANNUAL = "annual"  # 年度


class VisitorDataPoint(BaseModel):
    """访客数据点"""
    visitor_type: VisitorType = Field(..., description="访客类型")
    frequency: VisitorFrequency = Field(..., description="数据频率")
    date: date = Field(..., description="数据日期")
    value: Decimal = Field(..., ge=0, description="访客数量")
    unit: str = Field(default="person", description="单位")
    growth_rate: Optional[Decimal] = Field(None, description="增长率")
    source: str = Field(..., description="数据源")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('date')
    def validate_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class VisitorDataSet(BaseModel):
    """访客数据集"""
    visitor_type: VisitorType = Field(..., description="访客类型")
    frequency: VisitorFrequency = Field(..., description="频率")
    data_points: List[VisitorDataPoint] = Field(default_factory=list, description="数据点")
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
                'value': int(dp.value),
                'unit': dp.unit,
                'growth_rate': float(dp.growth_rate) if dp.growth_rate else None
            }
            for dp in self.data_points
        ]
        df = pd.DataFrame(data)
        df.sort_values('date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def calculate_growth_rates(self) -> None:
        """计算同比增长率"""
        if len(self.data_points) < 2:
            return

        # 按日期排序
        self.data_points.sort(key=lambda x: x.date)

        # 创建日期到值的映射
        date_value_map = {dp.date: dp.value for dp in self.data_points}

        # 计算增长率
        for dp in self.data_points:
            # 计算同比 (基于频率)
            if self.frequency == VisitorFrequency.ANNUAL:
                prev_date = date(dp.date.year - 1, dp.date.month, dp.date.day)
            elif self.frequency == VisitorFrequency.QUARTERLY:
                # 同比：上一年同期
                prev_year = dp.date.year - 1
                prev_date = date(prev_year, dp.date.month, dp.date.day)
            elif self.frequency == VisitorFrequency.MONTHLY:
                # 同比：上一年同月
                prev_date = date(dp.date.year - 1, dp.date.month, 1)
            elif self.frequency == VisitorFrequency.DAILY:
                # 同比：上一年同日
                prev_date = date(dp.date.year - 1, dp.date.month, dp.date.day)
            else:
                prev_date = None

            if prev_date and prev_date in date_value_map:
                prev_value = float(date_value_map[prev_date])
                curr_value = float(dp.value)

                if prev_value > 0:
                    growth_rate = ((curr_value - prev_value) / prev_value) * 100
                    dp.growth_rate = Decimal(str(growth_rate))


class VisitorParserConfig(BaseModel):
    """访客解析器配置"""
    download_dir: str = Field(default="data/csd_downloads", description="下载目录")
    parse_format_priority: List[str] = Field(
        default=['xlsx', 'csv', 'xml', 'json'],
        description="解析格式优先级"
    )
    max_workers: int = Field(default=4, description="最大工作线程数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")

    # 访客类型映射 (正则表达式模式)
    visitor_type_patterns: Dict[VisitorType, List[str]] = Field(
        default_factory=lambda: {
            VisitorType.TOTAL_VISITORS: [
                r'total.*visitor',
                r'total.*arrival',
                r'visitor.*total',
                r'total.*tourist',
                r'总.*访客',
                r'总.*旅客',
                r'全部.*访客'
            ],
            VisitorType.MAINLAND_CHINA: [
                r'mainland.*china',
                r'mainland',
                r'china.*mainland',
                r'内地',
                r'大陆',
                r'中国.*内地'
            ],
            VisitorType.TAIWAN: [
                r'taiwan',
                r'taiwanese',
                r'台湾',
                r'台灣'
            ],
            VisitorType.MACAU: [
                r'macau',
                r'macao',
                r'澳门',
                r'澳門'
            ],
            VisitorType.OTHER_ASIA: [
                r'other.*asia',
                r'asia.*other',
                r'south.*korea',
                r'japan',
                r'singapore',
                r'thailand',
                r'其他.*亚洲',
                r'亚洲.*其他',
                r'韩国',
                r'日本',
                r'新加坡',
                r'泰国'
            ],
            VisitorType.EUROPE: [
                r'europe',
                r'uk',
                r'germany',
                r'france',
                r'欧洲',
                r'英国',
                r'德国',
                r'法国'
            ],
            VisitorType.NORTH_AMERICA: [
                r'north.*america',
                r'usa',
                r'canada',
                r'北美',
                r'美国',
                r'加拿大'
            ],
            VisitorType.AUSTRALASIA: [
                r'australasia',
                r'australia',
                r'new.*zealand',
                r'澳新',
                r'澳大利亚',
                r'新西兰'
            ],
            VisitorType.OTHER_REGIONS: [
                r'other.*region',
                r'other.*area',
                r'其他.*地区',
                r'其他.*区域'
            ],
            VisitorType.DAILY_AVERAGE: [
                r'daily.*average',
                r'average.*daily',
                r'日均',
                r'平均.*每日'
            ]
        },
        description="访客类型识别模式"
    )


class VisitorDataProcessor(UnifiedBaseAdapter):
    """
    访港旅客数据处理器

    解析从C&SD获取的访港旅客数据，支持多种格式和自动数据转换。
    """

    def __init__(self, config: Optional[VisitorParserConfig] = None):
        super().__init__(config)
        self.config: VisitorParserConfig = config or VisitorParserConfig()
        self.logger = logging.getLogger("hk_quant_system.visitor_processor")

        # 缓存解析后的数据
        self._parsed_data: Dict[VisitorType, VisitorDataSet] = {}

    async def parse_file(self, file_path: Path, data_type: CSDDataType) -> Optional[Dict[VisitorType, Any]]:
        """
        解析访客数据文件

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

    async def _parse_excel(self, file_path: Path) -> Dict[VisitorType, Any]:
        """解析Excel文件"""
        results = {}

        # 读取所有工作表
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 检测访客类型
                visitor_types = self._detect_visitor_types(df, sheet_name)

                for visitor_type in visitor_types:
                    data_points = self._extract_visitor_data_points(df, visitor_type, 'xlsx', sheet_name)
                    if data_points:
                        # 推断频率
                        frequency = self._infer_frequency(sheet_name, df)

                        results[visitor_type] = VisitorDataSet(
                            visitor_type=visitor_type,
                            frequency=frequency,
                            data_points=data_points,
                            metadata={'source_file': str(file_path), 'sheet': sheet_name}
                        )

            except Exception as e:
                self.logger.warning(f"Error parsing sheet {sheet_name}: {e}")

        return results

    async def _parse_csv(self, file_path: Path) -> Dict[VisitorType, Any]:
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

        # 检测访客类型
        visitor_types = self._detect_visitor_types(df, file_path.stem)

        for visitor_type in visitor_types:
            data_points = self._extract_visitor_data_points(df, visitor_type, 'csv', file_path.stem)
            if data_points:
                frequency = self._infer_frequency(file_path.stem, df)

                results[visitor_type] = VisitorDataSet(
                    visitor_type=visitor_type,
                    frequency=frequency,
                    data_points=data_points,
                    metadata={'source_file': str(file_path)}
                )

        return results

    async def _parse_xml(self, file_path: Path) -> Dict[VisitorType, Any]:
        """解析XML文件"""
        results = {}
        import xml.etree.ElementTree as ET

        tree = ET.parse(file_path)
        root = tree.getroot()

        # 遍历XML元素，查找访客数据
        for element in root.iter():
            if element.text and 'visitor' in element.text.lower():
                # 解析访客相关数据
                pass

        return results

    async def _parse_json(self, file_path: Path) -> Dict[VisitorType, Any]:
        """解析JSON文件"""
        results = {}
        data = json.loads(file_path.read_text(encoding='utf-8'))

        if isinstance(data, dict):
            for key, value in data.items():
                visitor_type = self._detect_visitor_type_from_name(key)
                if visitor_type and isinstance(value, (list, dict)):
                    data_points = self._extract_json_data_points(value, visitor_type)
                    if data_points:
                        results[visitor_type] = VisitorDataSet(
                            visitor_type=visitor_type,
                            frequency=VisitorFrequency.MONTHLY,
                            data_points=data_points,
                            metadata={'source_file': str(file_path)}
                        )

        return results

    def _detect_visitor_types(self, df: pd.DataFrame, source: str) -> List[VisitorType]:
        """
        检测访客类型

        Args:
            df: DataFrame
            source: 数据源标识

        Returns:
            访客类型列表
        """
        visitor_types = []
        source_lower = source.lower()

        # 基于源名称检测
        for visitor_type, patterns in self.config.visitor_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, source_lower, re.IGNORECASE):
                    visitor_types.append(visitor_type)
                    break

        # 基于列名检测
        if df is not None:
            for col in df.columns:
                col_lower = str(col).lower()
                for visitor_type, patterns in self.config.visitor_type_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, col_lower, re.IGNORECASE):
                            if visitor_type not in visitor_types:
                                visitor_types.append(visitor_type)
                            break

        # 如果没有检测到特定类型，尝试从总访客推断
        if not visitor_types:
            # 检查是否包含总访客相关列
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['total', 'total', 'visitor', 'arrival', '总', '访客', '旅客']):
                    visitor_types.append(VisitorType.TOTAL_VISITORS)
                    break

        # 如果还是没有，返回TOTAL_VISITORS作为默认
        if not visitor_types:
            visitor_types.append(VisitorType.TOTAL_VISITORS)

        return visitor_types

    def _detect_visitor_type_from_name(self, name: str) -> Optional[VisitorType]:
        """从名称检测访客类型"""
        name_lower = name.lower()

        for visitor_type, patterns in self.config.visitor_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return visitor_type

        return None

    def _extract_visitor_data_points(
        self,
        df: pd.DataFrame,
        visitor_type: VisitorType,
        source_format: str,
        sheet_name: str
    ) -> List[VisitorDataPoint]:
        """
        从DataFrame提取访客数据点

        Args:
            df: DataFrame
            visitor_type: 访客类型
            source_format: 数据源格式
            sheet_name: 工作表名称

        Returns:
            访客数据点列表
        """
        data_points = []

        try:
            # 寻找日期列和数值列
            date_columns = [col for col in df.columns if self._is_date_column(df[col])]
            value_columns = [col for col in df.columns if self._is_numeric_column(df[col]) or self._is_visitor_type_column(df[col], visitor_type)]

            if not date_columns or not value_columns:
                # 如果没有明确区分，尝试从所有列中解析
                value_columns = [col for col in df.columns if self._is_numeric_column(df[col])]

            if not date_columns or not value_columns:
                self.logger.warning(f"No suitable columns found for {visitor_type}")
                return []

            # 使用第一列作为日期列
            date_col = date_columns[0]

            for value_col in value_columns:
                # 跳过日期列
                if value_col == date_col:
                    continue

                for idx, row in df.iterrows():
                    try:
                        date_val = self._parse_date(str(row[date_col]))
                        if date_val:
                            value = self._parse_numeric_value(str(row[value_col]))
                            if value is not None and value > 0:
                                dp = VisitorDataPoint(
                                    visitor_type=visitor_type,
                                    frequency=VisitorFrequency.MONTHLY,  # 默认月度
                                    date=date_val,
                                    value=Decimal(str(int(value))),  # 访客数应为整数
                                    unit='person',
                                    source=f"{source_format}:{visitor_type}"
                                )
                                data_points.append(dp)
                    except Exception as e:
                        self.logger.debug(f"Error parsing row {idx}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Error extracting data points: {e}")

        return data_points

    def _extract_json_data_points(self, data: Any, visitor_type: VisitorType) -> List[VisitorDataPoint]:
        """从JSON数据中提取访客数据点"""
        data_points = []

        # JSON结构可能不同，需要根据实际结构调整
        # 这里提供通用处理逻辑

        return data_points

    def _is_date_column(self, series: pd.Series) -> bool:
        """判断是否为日期列"""
        if series.dtype == 'datetime64[ns]':
            return True

        # 检查前几个非空值
        sample = series.dropna().head(10).astype(str)
        for val in sample:
            # 查找年月模式
            if re.search(r'\d{4}[/\-]\d{1,2}', val) or re.search(r'\d{4}年\d{1,2}月', val):
                return True
            # 查找日期
            if re.search(r'\d{4}[/\-]\d{1,2}[/\-]\d{1,2}', val) or re.search(r'\d{4}年\d{1,2}月\d{1,2}日', val):
                return True
            # 查找年份
            if re.search(r'\d{4}', val):
                return True

        return False

    def _is_numeric_column(self, series: pd.Series) -> bool:
        """判断是否为数值列"""
        return pd.api.types.is_numeric_dtype(series)

    def _is_visitor_type_column(self, series: pd.Series, visitor_type: VisitorType) -> bool:
        """判断是否为目标访客类型的列"""
        if not pd.api.types.is_string_dtype(series):
            return False

        sample = series.dropna().head(10).astype(str)
        visitor_type_patterns = self.config.visitor_type_patterns.get(visitor_type, [])

        for val in sample:
            for pattern in visitor_type_patterns:
                if re.search(pattern, val.lower(), re.IGNORECASE):
                    return True

        return False

    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        date_str = date_str.strip()

        # 解析年月日 (YYYY-MM-DD 或 YYYY/MM/DD)
        ymd_match = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', date_str)
        if ymd_match:
            year, month, day = int(ymd_match.group(1)), int(ymd_match.group(2)), int(ymd_match.group(3))
            if 1990 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                return date(year, month, day)

        # 解析年月日 (中文: YYYY年MM月DD日)
        ymd_cn_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if ymd_cn_match:
            year, month, day = int(ymd_cn_match.group(1)), int(ymd_cn_match.group(2)), int(ymd_cn_match.group(3))
            if 1990 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                return date(year, month, day)

        # 解析年月 (YYYY-MM 或 YYYY/MM)
        ym_match = re.search(r'(\d{4})[/\-](\d{1,2})', date_str)
        if ym_match:
            year, month = int(ym_match.group(1)), int(ym_match.group(2))
            if 1990 <= year <= 2030 and 1 <= month <= 12:
                return date(year, month, 1)

        # 解析年月 (中文: YYYY年MM月)
        ym_cn_match = re.search(r'(\d{4})年(\d{1,2})月', date_str)
        if ym_cn_match:
            year, month = int(ym_cn_match.group(1)), int(ym_cn_match.group(2))
            if 1990 <= year <= 2030 and 1 <= month <= 12:
                return date(year, month, 1)

        # 解析年份
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= 2030:
                return date(year, 12, 31)

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

    def _infer_frequency(self, sheet_name: str, df: pd.DataFrame) -> VisitorFrequency:
        """推断数据频率"""
        sheet_lower = sheet_name.lower()

        if 'day' in sheet_lower or 'daily' in sheet_lower or '日' in sheet_lower:
            return VisitorFrequency.DAILY
        elif 'month' in sheet_lower or '月' in sheet_lower:
            return VisitorFrequency.MONTHLY
        elif 'quarter' in sheet_lower or '季' in sheet_lower:
            return VisitorFrequency.QUARTERLY
        elif 'year' in sheet_lower or '年' in sheet_lower:
            return VisitorFrequency.ANNUAL

        # 基于列名推断
        if 'date' in df.columns:
            # 检查日期列中的数据粒度
            sample_dates = df['date'].dropna().head(10)
            for d in sample_dates:
                d_str = str(d)
                if re.search(r'\d{4}[/\-]\d{1,2}[/\-]\d{1,2}', d_str):
                    return VisitorFrequency.DAILY
                elif re.search(r'\d{4}[/\-]\d{1,2}', d_str):
                    return VisitorFrequency.MONTHLY

        return VisitorFrequency.MONTHLY  # 默认月度

    async def parse_visitor_data(
        self,
        file_path: Path,
        data_type: CSDDataType = CSDDataType.VISITOR_ARRIVALS
    ) -> Dict[VisitorType, VisitorDataSet]:
        """
        解析访客数据文件

        Args:
            file_path: 文件路径
            data_type: 数据类型

        Returns:
            访客数据集字典
        """
        context = "VisitorProcessor.parse_visitor_data"

        try:
            # 检查缓存
            cache_key = f"visitor:{hashlib.md5(str(file_path).encode()).hexdigest()}"
            cached = self.cache.get(cache_key)
            if cached and self.cache.is_valid(cache_key):
                self.logger.info("Returning cached visitor data")
                return cached

            # 解析文件
            results = await self.parse_file(file_path, data_type)

            if results:
                # 转换为VisitorDataSet并计算增长率
                datasets = {}
                for visitor_type, data in results.items():
                    if isinstance(data, VisitorDataSet):
                        # 计算增长率
                        data.calculate_growth_rates()
                        datasets[visitor_type] = data
                    else:
                        # 转换其他格式
                        pass

                # 缓存结果
                self.cache.set(cache_key, datasets, ttl=self.config.cache_ttl)

                # 更新内部缓存
                self._parsed_data.update(datasets)

                self.logger.info(f"Parsed {len(datasets)} visitor types")
                return datasets

            return {}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            self.logger.error(f"Parse error: {error_info}")
            return {}

    async def get_visitor_data(
        self,
        visitor_type: VisitorType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[VisitorDataSet]:
        """
        获取访客数据

        Args:
            visitor_type: 访客类型
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            访客数据集
        """
        if visitor_type not in self._parsed_data:
            self.logger.warning(f"Visitor type {visitor_type} not found in parsed data")
            return None

        dataset = self._parsed_data[visitor_type]

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

    async def calculate_visitor_share(
        self,
        visitor_type: VisitorType,
        date: date
    ) -> Optional[Decimal]:
        """
        计算特定类型访客在总访客中的占比

        Args:
            visitor_type: 访客类型
            date: 日期

        Returns:
            访客占比 (百分比)
        """
        type_data = await self.get_visitor_data(visitor_type)
        total_data = await self.get_visitor_data(VisitorType.TOTAL_VISITORS)

        if not type_data or not total_data:
            return None

        # 找到指定日期的数据
        type_value = None
        total_value = None

        for dp in type_data.data_points:
            if dp.date == date:
                type_value = dp.value
                break

        for dp in total_data.data_points:
            if dp.date == date:
                total_value = dp.value
                break

        if type_value and total_value and total_value > 0:
            share = (type_value / total_value) * 100
            return Decimal(str(share))

        return None

    async def get_seasonal_patterns(
        self,
        visitor_type: VisitorType
    ) -> Dict[str, Decimal]:
        """
        获取季节性访客模式

        Args:
            visitor_type: 访客类型

        Returns:
            季节性模式 {season: average_visitors}
        """
        dataset = await self.get_visitor_data(visitor_type)
        if not dataset:
            return {}

        # 计算季节平均
        seasonal_avg = {
            'spring': Decimal('0'),  # 春季 3-5月
            'summer': Decimal('0'),  # 夏季 6-8月
            'autumn': Decimal('0'),  # 秋季 9-11月
            'winter': Decimal('0'),  # 冬季 12-2月
        }

        seasonal_count = {
            'spring': 0,
            'summer': 0,
            'autumn': 0,
            'winter': 0,
        }

        for dp in dataset.data_points:
            month = dp.date.month
            if month in [3, 4, 5]:
                seasonal_avg['spring'] += dp.value
                seasonal_count['spring'] += 1
            elif month in [6, 7, 8]:
                seasonal_avg['summer'] += dp.value
                seasonal_count['summer'] += 1
            elif month in [9, 10, 11]:
                seasonal_avg['autumn'] += dp.value
                seasonal_count['autumn'] += 1
            else:  # 12, 1, 2
                seasonal_avg['winter'] += dp.value
                seasonal_count['winter'] += 1

        # 计算平均值
        for season in seasonal_avg:
            if seasonal_count[season] > 0:
                seasonal_avg[season] = seasonal_avg[season] / seasonal_count[season]

        return {k: v for k, v in seasonal_avg.items() if v > 0}

    async def get_all_visitor_types(self) -> List[VisitorType]:
        """获取所有可用的访客类型"""
        return list(self._parsed_data.keys())

    async def export_to_dataframe(self, visitor_type: VisitorType) -> Optional[pd.DataFrame]:
        """
        导出访客数据为DataFrame

        Args:
            visitor_type: 访客类型

        Returns:
            DataFrame或None
        """
        dataset = await self.get_visitor_data(visitor_type)
        if dataset:
            return dataset.to_dataframe()
        return None

    async def get_summary(self) -> Dict[str, Any]:
        """
        获取处理摘要

        Returns:
            摘要信息
        """
        return {
            'processor_name': 'VisitorDataProcessor',
            'parsed_visitor_types': [vt.value for vt in self._parsed_data.keys()],
            'total_visitor_types': len(self._parsed_data),
            'data_points_per_type': {
                vt.value: len(dataset.data_points)
                for vt, dataset in self._parsed_data.items()
            },
            'config': self.config.dict(),
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
async def parse_visitor_file(file_path: Path) -> Dict[VisitorType, VisitorDataSet]:
    """解析访客文件"""
    processor = VisitorDataProcessor()
    try:
        return await processor.parse_visitor_data(file_path)
    finally:
        await processor.close()


async def get_visitor_type(
    file_path: Path,
    visitor_type: VisitorType
) -> Optional[VisitorDataSet]:
    """获取特定访客类型"""
    processor = VisitorDataProcessor()
    try:
        await processor.parse_visitor_data(file_path)
        return await processor.get_visitor_data(visitor_type)
    finally:
        await processor.close()
