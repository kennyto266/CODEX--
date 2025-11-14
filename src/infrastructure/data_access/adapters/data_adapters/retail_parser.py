"""
零售销售数据处理器

从C&SD数据中解析零售销售相关指标，包括：
- 零售销售总额
- 分行业销售 (服装、超市、电器、餐厅等)
- 月度/年度销售数据
- 同比增长率

支持多种数据格式的自动解析和标准化。

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
from pydantic import BaseModel, Field, ConfigDict, validator

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler
from .cs_d_crawler import CSDDataType


class RetailCategory(str):
    """零售类别枚举"""
    TOTAL_SALES = "total_retail_sales"  # 零售销售总额
    CLOTHING = "clothing_footwear"  # 服装鞋履
    SUPERMARKET = "supermarket"  # 超市
    RESTAURANTS = "restaurants"  # 餐饮
    ELECTRONICS = "electrical_appliances"  # 电器
    MOTOR_VEHICLES = "motor_vehicles"  # 汽车
    FUEL = "fuel"  # 燃料
    HARDWARE = "hardware"  # 五金
    FURNITURE = "furniture"  # 家具
    OTHER = "other_retail"  # 其他零售


class RetailFrequency(str):
    """零售数据频率"""
    MONTHLY = "monthly"  # 月度
    QUARTERLY = "quarterly"  # 季度
    ANNUAL = "annual"  # 年度


class RetailDataPoint(BaseModel):
    """零售数据点"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    category: RetailCategory = Field(..., description="零售类别")
    frequency: RetailFrequency = Field(..., description="数据频率")
    data_date: date = Field(..., description="数据日期")
    retail_value: Decimal = Field(..., ge=0, description="销售额")
    unit: str = Field(default="HKD Million", description="单位")
    growth_rate: Optional[Decimal] = Field(None, description="增长率")
    source: str = Field(..., description="数据源")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('data_date')
    def validate_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class RetailDataSet(BaseModel):
    """零售数据集"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    category: RetailCategory = Field(..., description="类别")
    frequency: RetailFrequency = Field(..., description="频率")
    data_points: List[RetailDataPoint] = Field(default_factory=list, description="数据点")
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
            # 计算同比 (假设频率为年度)
            if self.frequency == RetailFrequency.ANNUAL:
                prev_date = date(dp.date.year - 1, dp.date.month, dp.date.day)
            elif self.frequency == RetailFrequency.MONTHLY:
                # 同比：上一年同月
                prev_date = date(dp.date.year - 1, dp.date.month, 1)
            else:
                prev_date = None

            if prev_date and prev_date in date_value_map:
                prev_value = float(date_value_map[prev_date])
                curr_value = float(dp.value)

                if prev_value > 0:
                    growth_rate = ((curr_value - prev_value) / prev_value) * 100
                    dp.growth_rate = Decimal(str(growth_rate))


class RetailParserConfig(BaseModel):
    """零售解析器配置"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    download_dir: str = Field(default="data/csd_downloads", description="下载目录")
    parse_format_priority: List[str] = Field(
        default=['xlsx', 'csv', 'xml', 'json'],
        description="解析格式优先级"
    )
    max_workers: int = Field(default=4, description="最大工作线程数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")

    # 零售类别映射 (正则表达式模式)
    category_patterns: Dict[RetailCategory, List[str]] = Field(
        default_factory=lambda: {
            RetailCategory.TOTAL_SALES: [
                r'total.*retail',
                r'retail.*total',
                r'零售.*总额',
                r'总.*零售'
            ],
            RetailCategory.CLOTHING: [
                r'clothing',
                r'footwear',
                r'apparel',
                r'服装',
                r'鞋履',
                r'衣着'
            ],
            RetailCategory.SUPERMARKET: [
                r'supermarket',
                r'supermarkets',
                r'超市',
                r'超级市场'
            ],
            RetailCategory.RESTAURANTS: [
                r'restaurant',
                r'eating',
                r'food',
                r'餐饮',
                r'饮食',
                r'餐馆'
            ],
            RetailCategory.ELECTRONICS: [
                r'electrical.*appliance',
                r'electronic',
                r'electrical',
                r'电器',
                r'电子'
            ],
            RetailCategory.MOTOR_VEHICLES: [
                r'motor.*vehicle',
                r'automotive',
                r'汽车',
                r'车辆'
            ],
            RetailCategory.FUEL: [
                r'fuel',
                r'gasoline',
                r'petrol',
                r'燃料',
                r'汽油',
                r'石油'
            ],
            RetailCategory.HARDWARE: [
                r'hardware',
                r'五金',
                r'硬件'
            ],
            RetailCategory.FURNITURE: [
                r'furniture',
                r'家具'
            ],
            RetailCategory.OTHER: [
                r'other',
                r'miscellaneous',
                r'其他',
                r'杂项'
            ]
        },
        description="零售类别识别模式"
    )


class RetailDataProcessor(UnifiedBaseAdapter):
    """
    零售销售数据处理器

    解析从C&SD获取的零售销售数据，支持多种格式和自动数据转换。
    """

    def __init__(self, config: Optional[RetailParserConfig] = None):
        super().__init__(config)
        self.config: RetailParserConfig = config or RetailParserConfig()
        self.logger = logging.getLogger("hk_quant_system.retail_processor")

        # 缓存解析后的数据
        self._parsed_data: Dict[RetailCategory, RetailDataSet] = {}

    async def parse_file(self, file_path: Path, data_type: CSDDataType) -> Optional[Dict[RetailCategory, Any]]:
        """
        解析零售数据文件

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

    async def _parse_excel(self, file_path: Path) -> Dict[RetailCategory, Any]:
        """解析Excel文件"""
        results = {}

        # 读取所有工作表
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 检测零售类别
                categories = self._detect_retail_categories(df, sheet_name)

                for category in categories:
                    data_points = self._extract_retail_data_points(df, category, 'xlsx', sheet_name)
                    if data_points:
                        results[category] = RetailDataSet(
                            category=category,
                            frequency=RetailFrequency.MONTHLY,
                            data_points=data_points,
                            metadata={'source_file': str(file_path), 'sheet': sheet_name}
                        )

            except Exception as e:
                self.logger.warning(f"Error parsing sheet {sheet_name}: {e}")

        return results

    async def _parse_csv(self, file_path: Path) -> Dict[RetailCategory, Any]:
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

        # 检测零售类别
        categories = self._detect_retail_categories(df, file_path.stem)

        for category in categories:
            data_points = self._extract_retail_data_points(df, category, 'csv', file_path.stem)
            if data_points:
                results[category] = RetailDataSet(
                    category=category,
                    frequency=RetailFrequency.MONTHLY,
                    data_points=data_points,
                    metadata={'source_file': str(file_path)}
                )

        return results

    async def _parse_xml(self, file_path: Path) -> Dict[RetailCategory, Any]:
        """解析XML文件"""
        results = {}
        import xml.etree.ElementTree as ET

        tree = ET.parse(file_path)
        root = tree.getroot()

        # 遍历XML元素，查找零售数据
        for element in root.iter():
            if element.text and 'retail' in element.text.lower():
                # 解析零售相关数据
                pass

        return results

    async def _parse_json(self, file_path: Path) -> Dict[RetailCategory, Any]:
        """解析JSON文件"""
        results = {}
        data = json.loads(file_path.read_text(encoding='utf-8'))

        if isinstance(data, dict):
            for key, value in data.items():
                category = self._detect_category_from_name(key)
                if category and isinstance(value, (list, dict)):
                    data_points = self._extract_json_data_points(value, category)
                    if data_points:
                        results[category] = RetailDataSet(
                            category=category,
                            frequency=RetailFrequency.MONTHLY,
                            data_points=data_points,
                            metadata={'source_file': str(file_path)}
                        )

        return results

    def _detect_retail_categories(self, df: pd.DataFrame, source: str) -> List[RetailCategory]:
        """
        检测零售类别

        Args:
            df: DataFrame
            source: 数据源标识

        Returns:
            零售类别列表
        """
        categories = []
        source_lower = source.lower()

        # 基于源名称检测
        for category, patterns in self.config.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, source_lower, re.IGNORECASE):
                    categories.append(category)
                    break

        # 基于列名检测
        if df is not None:
            for col in df.columns:
                col_lower = str(col).lower()
                for category, patterns in self.config.category_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, col_lower, re.IGNORECASE):
                            if category not in categories:
                                categories.append(category)
                            break

        # 如果没有检测到特定类别，返回TOTAL_SALES
        if not categories:
            categories.append(RetailCategory.TOTAL_SALES)

        return categories

    def _detect_category_from_name(self, name: str) -> Optional[RetailCategory]:
        """从名称检测类别"""
        name_lower = name.lower()

        for category, patterns in self.config.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return category

        return None

    def _extract_retail_data_points(
        self,
        df: pd.DataFrame,
        category: RetailCategory,
        source_format: str,
        sheet_name: str
    ) -> List[RetailDataPoint]:
        """
        从DataFrame提取零售数据点

        Args:
            df: DataFrame
            category: 零售类别
            source_format: 数据源格式
            sheet_name: 工作表名称

        Returns:
            零售数据点列表
        """
        data_points = []

        try:
            # 寻找日期列和数值列
            date_columns = [col for col in df.columns if self._is_date_column(df[col])]
            value_columns = [col for col in df.columns if self._is_numeric_column(df[col]) or self._is_category_column(df[col], category)]

            if not date_columns or not value_columns:
                # 如果没有明确区分，尝试从所有列中解析
                value_columns = [col for col in df.columns if self._is_numeric_column(df[col])]

            if not date_columns or not value_columns:
                self.logger.warning(f"No suitable columns found for {category}")
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
                                # 推断频率
                                frequency = self._infer_frequency(date_col, value_col, sheet_name)

                                dp = RetailDataPoint(
                                    category=category,
                                    frequency=frequency,
                                    date=date_val,
                                    value=Decimal(str(value)),
                                    unit='HKD Million',
                                    source=f"{source_format}:{category}"
                                )
                                data_points.append(dp)
                    except Exception as e:
                        self.logger.debug(f"Error parsing row {idx}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Error extracting data points: {e}")

        return data_points

    def _extract_json_data_points(self, data: Any, category: RetailCategory) -> List[RetailDataPoint]:
        """从JSON数据中提取零售数据点"""
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
            # 查找年份
            if re.search(r'\d{4}', val):
                return True

        return False

    def _is_numeric_column(self, series: pd.Series) -> bool:
        """判断是否为数值列"""
        return pd.api.types.is_numeric_dtype(series)

    def _is_category_column(self, series: pd.Series, category: RetailCategory) -> bool:
        """判断是否为目标类别的列"""
        if not pd.api.types.is_string_dtype(series):
            return False

        sample = series.dropna().head(10).astype(str)
        category_patterns = self.config.category_patterns.get(category, [])

        for val in sample:
            for pattern in category_patterns:
                if re.search(pattern, val.lower(), re.IGNORECASE):
                    return True

        return False

    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        date_str = date_str.strip()

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

    def _infer_frequency(self, date_col: str, value_col: str, sheet_name: str) -> RetailFrequency:
        """推断数据频率"""
        sheet_lower = sheet_name.lower()

        if 'month' in sheet_lower or '月' in sheet_lower:
            return RetailFrequency.MONTHLY
        elif 'quarter' in sheet_lower or '季' in sheet_lower:
            return RetailFrequency.QUARTERLY
        elif 'year' in sheet_lower or '年' in sheet_lower:
            return RetailFrequency.ANNUAL

        # 基于列名推断
        if 'month' in date_col.lower() or '月' in date_col:
            return RetailFrequency.MONTHLY
        elif 'quarter' in date_col.lower() or '季' in date_col:
            return RetailFrequency.QUARTERLY
        else:
            return RetailFrequency.MONTHLY  # 默认月度

    async def parse_retail_data(
        self,
        file_path: Path,
        data_type: CSDDataType = CSDDataType.RETAIL_SALES
    ) -> Dict[RetailCategory, RetailDataSet]:
        """
        解析零售数据文件

        Args:
            file_path: 文件路径
            data_type: 数据类型

        Returns:
            零售数据集字典
        """
        context = "RetailProcessor.parse_retail_data"

        try:
            # 检查缓存
            cache_key = f"retail:{hashlib.md5(str(file_path).encode()).hexdigest()}"
            cached = self.cache.get(cache_key)
            if cached and self.cache.is_valid(cache_key):
                self.logger.info("Returning cached retail data")
                return cached

            # 解析文件
            results = await self.parse_file(file_path, data_type)

            if results:
                # 转换为RetailDataSet并计算增长率
                datasets = {}
                for category, data in results.items():
                    if isinstance(data, RetailDataSet):
                        # 计算增长率
                        data.calculate_growth_rates()
                        datasets[category] = data
                    else:
                        # 转换其他格式
                        pass

                # 缓存结果
                self.cache.set(cache_key, datasets, ttl=self.config.cache_ttl)

                # 更新内部缓存
                self._parsed_data.update(datasets)

                self.logger.info(f"Parsed {len(datasets)} retail categories")
                return datasets

            return {}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            self.logger.error(f"Parse error: {error_info}")
            return {}

    async def get_retail_data(
        self,
        category: RetailCategory,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[RetailDataSet]:
        """
        获取零售数据

        Args:
            category: 零售类别
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            零售数据集
        """
        if category not in self._parsed_data:
            self.logger.warning(f"Retail category {category} not found in parsed data")
            return None

        dataset = self._parsed_data[category]

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

    async def calculate_market_share(
        self,
        category: RetailCategory,
        date: date
    ) -> Optional[Decimal]:
        """
        计算特定类别在零售总额中的市场份额

        Args:
            category: 零售类别
            date: 日期

        Returns:
            市场份额 (百分比)
        """
        category_data = await self.get_retail_data(category)
        total_data = await self.get_retail_data(RetailCategory.TOTAL_SALES)

        if not category_data or not total_data:
            return None

        # 找到指定日期的数据
        category_value = None
        total_value = None

        for dp in category_data.data_points:
            if dp.date == date:
                category_value = dp.value
                break

        for dp in total_data.data_points:
            if dp.date == date:
                total_value = dp.value
                break

        if category_value and total_value and total_value > 0:
            share = (category_value / total_value) * 100
            return Decimal(str(share))

        return None

    async def get_all_retail_categories(self) -> List[RetailCategory]:
        """获取所有可用的零售类别"""
        return list(self._parsed_data.keys())

    async def export_to_dataframe(self, category: RetailCategory) -> Optional[pd.DataFrame]:
        """
        导出零售数据为DataFrame

        Args:
            category: 零售类别

        Returns:
            DataFrame或None
        """
        dataset = await self.get_retail_data(category)
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
            'processor_name': 'RetailDataProcessor',
            'parsed_categories': [cat.value for cat in self._parsed_data.keys()],
            'total_categories': len(self._parsed_data),
            'data_points_per_category': {
                cat.value: len(dataset.data_points)
                for cat, dataset in self._parsed_data.items()
            },
            'config': self.config.dict(),
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
async def parse_retail_file(file_path: Path) -> Dict[RetailCategory, RetailDataSet]:
    """解析零售文件"""
    processor = RetailDataProcessor()
    try:
        return await processor.parse_retail_data(file_path)
    finally:
        await processor.close()


async def get_retail_category(
    file_path: Path,
    category: RetailCategory
) -> Optional[RetailDataSet]:
    """获取特定零售类别"""
    processor = RetailDataProcessor()
    try:
        await processor.parse_retail_data(file_path)
        return await processor.get_retail_data(category)
    finally:
        await processor.close()
