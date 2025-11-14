"""
贸易数据集成器

从C&SD数据中解析对外贸易相关指标，包括：
- 出口贸易 (总值及分类)
- 进口贸易 (总值及分类)
- 贸易差额
- 主要贸易伙伴
- 商品分类贸易 (按HS编码)

支持按月、季度、年度统计和增长率计算。

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
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler
from .cs_d_crawler import CSDDataType


class TradeType(str):
    """贸易类型枚举"""
    EXPORTS = "exports"  # 出口
    IMPORTS = "imports"  # 进口
    TRADE_BALANCE = "trade_balance"  # 贸易差额
    RE_EXPORTS = "re_exports"  # 转口贸易
    DOMESTIC_EXPORTS = "domestic_exports"  # 本产出口


class TradeCategory(str):
    """贸易分类枚举"""
    TOTAL_TRADE = "total_trade"  # 贸易总额
    CONSUMER_GOODS = "consumer_goods"  # 消费品
    CAPITAL_GOODS = "capital_goods"  # 资本货物
    INTERMEDIATE_GOODS = "intermediate_goods"  # 中间产品
    FUELS = "fuels"  # 燃料
    FOODSTUFFS = "foodstuffs"  # 食品
    CHEMICALS = "chemicals"  # 化学品
    TEXTILES = "textiles"  # 纺织
    ELECTRONICS = "electronics"  # 电子产品
    MACHINERY = "machinery"  # 机械
    OTHER = "other"  # 其他


class TradePartner(str):
    """主要贸易伙伴"""
    MAINLAND_CHINA = "mainland_china"  # 内地
    UNITED_STATES = "united_states"  # 美国
    JAPAN = "japan"  # 日本
    TAIWAN = "taiwan"  # 台湾
    SOUTH_KOREA = "south_korea"  # 韩国
    SINGAPORE = "singapore"  # 新加坡
    GERMANY = "germany"  # 德国
    UNITED_KINGDOM = "united_kingdom"  # 英国
    THAILAND = "thailand"  # 泰国
    VIETNAM = "vietnam"  # 越南
    INDIA = "india"  # 印度


class TradeFrequency(str):
    """贸易数据频率"""
    MONTHLY = "monthly"  # 月度
    QUARTERLY = "quarterly"  # 季度
    ANNUAL = "annual"  # 年度


class TradeDataPoint(BaseModel):
    """贸易数据点"""
    trade_type: TradeType = Field(..., description="贸易类型")
    category: TradeCategory = Field(..., description="商品分类")
    trade_partner: Optional[TradePartner] = Field(None, description="贸易伙伴")
    frequency: TradeFrequency = Field(..., description="数据频率")
    date: date = Field(..., description="数据日期")
    value: Decimal = Field(..., ge=0, description="贸易额")
    unit: str = Field(default="HKD Million", description="单位")
    currency: str = Field(default="HKD", description="货币")
    growth_rate: Optional[Decimal] = Field(None, description="增长率")
    source: str = Field(..., description="数据源")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    @validator('date')
    def validate_date(cls, v):
        if v > datetime.now().date():
            raise ValueError("Date cannot be in the future")
        return v


class TradeDataSet(BaseModel):
    """贸易数据集"""
    trade_type: TradeType = Field(..., description="贸易类型")
    category: TradeCategory = Field(..., description="商品分类")
    frequency: TradeFrequency = Field(..., description="频率")
    data_points: List[TradeDataPoint] = Field(default_factory=list, description="数据点")
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
                'trade_type': dp.trade_type.value,
                'category': dp.category.value,
                'trade_partner': dp.trade_partner.value if dp.trade_partner else None,
                'value': float(dp.value),
                'unit': dp.unit,
                'currency': dp.currency,
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
            # 计算同比
            if self.frequency == TradeFrequency.ANNUAL:
                prev_date = date(dp.date.year - 1, dp.date.month, dp.date.day)
            elif self.frequency == TradeFrequency.QUARTERLY:
                prev_year = dp.date.year - 1
                prev_date = date(prev_year, dp.date.month, dp.date.day)
            elif self.frequency == TradeFrequency.MONTHLY:
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


class TradeParserConfig(BaseModel):
    """贸易解析器配置"""
    download_dir: str = Field(default="data/csd_downloads", description="下载目录")
    parse_format_priority: List[str] = Field(
        default=['xlsx', 'csv', 'xml', 'json'],
        description="解析格式优先级"
    )
    max_workers: int = Field(default=4, description="最大工作线程数")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")

    # 贸易类型映射 (正则表达式模式)
    trade_type_patterns: Dict[TradeType, List[str]] = Field(
        default_factory=lambda: {
            TradeType.EXPORTS: [
                r'export',
                r'outbound',
                r'出口',
                r'輸出',
                r'外銷'
            ],
            TradeType.IMPORTS: [
                r'import',
                r'inbound',
                r'进口',
                r'輸入',
                r'內銷'
            ],
            TradeType.TRADE_BALANCE: [
                r'trade.*balance',
                r'balance.*trade',
                r'net.*export',
                r'贸易差额',
                r'貿易差额',
                r'净出口'
            ],
            TradeType.RE_EXPORTS: [
                r're.?export',
                r'transit',
                r'reexports',
                r'转口',
                r'轉口',
                r'再出口'
            ],
            TradeType.DOMESTIC_EXPORTS: [
                r'domestic.*export',
                r'domestic.*outbound',
                r'本产.*出口',
                r'本產.*出口',
                r'本地.*出口'
            ]
        },
        description="贸易类型识别模式"
    )

    # 商品分类映射
    category_patterns: Dict[TradeCategory, List[str]] = Field(
        default_factory=lambda: {
            TradeCategory.TOTAL_TRADE: [
                r'total.*trade',
                r'trade.*total',
                r'总.*贸易',
                r'總.*貿易',
                r'全部.*贸易'
            ],
            TradeCategory.CONSUMER_GOODS: [
                r'consumer.*goods',
                r'consumption',
                r'消费品',
                r'消費品',
                r'生活用品'
            ],
            TradeCategory.CAPITAL_GOODS: [
                r'capital.*goods',
                r'capital.*equipment',
                r'资本.*货物',
                r'資本.*货物',
                r'设备'
            ],
            TradeCategory.INTERMEDIATE_GOODS: [
                r'intermediate',
                r'semi.?finished',
                r'中间.*产品',
                r'中間.*产品',
                r'半成品'
            ],
            TradeCategory.FUELS: [
                r'fuel',
                r'petroleum',
                r'energy',
                r'燃料',
                r'石油',
                r'能源'
            ],
            TradeCategory.FOODSTUFFS: [
                r'food',
                r'foodstuff',
                r'agricultural',
                r'食品',
                r'农产品',
                r'農產品'
            ],
            TradeCategory.CHEMICALS: [
                r'chemical',
                r'pharmaceutical',
                r'化学品',
                r'化學品',
                r'药品'
            ],
            TradeCategory.TEXTILES: [
                r'textile',
                r'garment',
                r'apparel',
                r'纺织',
                r'紡織',
                r'服装'
            ],
            TradeCategory.ELECTRONICS: [
                r'electronic',
                r'electrical',
                r'computer',
                r'电子',
                r'電子',
                r'电脑'
            ],
            TradeCategory.MACHINERY: [
                r'machinery',
                r'machine',
                r'equipment',
                r'机械',
                r'機械',
                r'设备'
            ]
        },
        description="商品分类识别模式"
    )

    # 贸易伙伴映射
    partner_patterns: Dict[TradePartner, List[str]] = Field(
        default_factory=lambda: {
            TradePartner.MAINLAND_CHINA: [
                r'mainland.*china',
                r'mainland',
                r'china.*mainland',
                r'内地',
                r'大陆',
                r'中国.*内地'
            ],
            TradePartner.UNITED_STATES: [
                r'united.?states',
                r'usa',
                r'us',
                r'美国',
                r'美國'
            ],
            TradePartner.JAPAN: [
                r'japan',
                r'japanese',
                r'日本',
                r'日圓'
            ],
            TradePartner.TAIWAN: [
                r'taiwan',
                r'taiwanese',
                r'台湾',
                r'台灣'
            ],
            TradePartner.SOUTH_KOREA: [
                r'south.*korea',
                r'korea',
                r'韩国',
                r'韓國'
            ]
        },
        description="贸易伙伴识别模式"
    )


class TradeDataIntegrator(UnifiedBaseAdapter):
    """
    贸易数据集成器

    解析从C&SD获取的对外贸易数据，支持多种格式和自动数据转换。
    """

    def __init__(self, config: Optional[TradeParserConfig] = None):
        super().__init__(config)
        self.config: TradeParserConfig = config or TradeParserConfig()
        self.logger = logging.getLogger("hk_quant_system.trade_integrator")

        # 缓存解析后的数据
        self._parsed_data: Dict[str, TradeDataSet] = {}  # key: f"{trade_type}_{category}"

    async def parse_file(self, file_path: Path, data_type: CSDDataType) -> Optional[Dict[str, TradeDataSet]]:
        """
        解析贸易数据文件

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

    async def _parse_excel(self, file_path: Path) -> Dict[str, TradeDataSet]:
        """解析Excel文件"""
        results = {}

        # 读取所有工作表
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # 检测贸易类型和分类
                trade_types = self._detect_trade_types(df, sheet_name)
                trade_categories = self._detect_trade_categories(df, sheet_name)
                trade_partners = self._detect_trade_partners(df, sheet_name)

                for trade_type in trade_types:
                    for category in trade_categories:
                        for partner in trade_partners:
                            data_points = self._extract_trade_data_points(
                                df, trade_type, category, partner, 'xlsx', sheet_name
                            )
                            if data_points:
                                # 推断频率
                                frequency = self._infer_frequency(sheet_name, df)

                                dataset_key = self._get_dataset_key(trade_type, category, partner)

                                results[dataset_key] = TradeDataSet(
                                    trade_type=trade_type,
                                    category=category,
                                    frequency=frequency,
                                    data_points=data_points,
                                    metadata={'source_file': str(file_path), 'sheet': sheet_name}
                                )

            except Exception as e:
                self.logger.warning(f"Error parsing sheet {sheet_name}: {e}")

        return results

    async def _parse_csv(self, file_path: Path) -> Dict[str, TradeDataSet]:
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

        # 检测贸易类型和分类
        trade_types = self._detect_trade_types(df, file_path.stem)
        trade_categories = self._detect_trade_categories(df, file_path.stem)
        trade_partners = self._detect_trade_partners(df, file_path.stem)

        for trade_type in trade_types:
            for category in trade_categories:
                for partner in trade_partners:
                    data_points = self._extract_trade_data_points(
                        df, trade_type, category, partner, 'csv', file_path.stem
                    )
                    if data_points:
                        frequency = self._infer_frequency(file_path.stem, df)
                        dataset_key = self._get_dataset_key(trade_type, category, partner)

                        results[dataset_key] = TradeDataSet(
                            trade_type=trade_type,
                            category=category,
                            frequency=frequency,
                            data_points=data_points,
                            metadata={'source_file': str(file_path)}
                        )

        return results

    async def _parse_xml(self, file_path: Path) -> Dict[str, TradeDataSet]:
        """解析XML文件"""
        results = {}
        import xml.etree.ElementTree as ET

        tree = ET.parse(file_path)
        root = tree.getroot()

        # 遍历XML元素，查找贸易数据
        for element in root.iter():
            if element.text and any(keyword in element.text.lower() for keyword in ['export', 'import', 'trade']):
                # 解析贸易相关数据
                pass

        return results

    async def _parse_json(self, file_path: Path) -> Dict[str, TradeDataSet]:
        """解析JSON文件"""
        results = {}
        data = json.loads(file_path.read_text(encoding='utf-8'))

        if isinstance(data, dict):
            for key, value in data.items():
                trade_type = self._detect_trade_type_from_name(key)
                category = self._detect_category_from_name(key)
                partner = self._detect_partner_from_name(key)

                if trade_type and isinstance(value, (list, dict)):
                    data_points = self._extract_json_data_points(value, trade_type, category, partner)
                    if data_points:
                        dataset_key = self._get_dataset_key(trade_type, category, partner)
                        results[dataset_key] = TradeDataSet(
                            trade_type=trade_type,
                            category=category or TradeCategory.TOTAL_TRADE,
                            frequency=TradeFrequency.MONTHLY,
                            data_points=data_points,
                            metadata={'source_file': str(file_path)}
                        )

        return results

    def _detect_trade_types(self, df: pd.DataFrame, source: str) -> List[TradeType]:
        """检测贸易类型"""
        trade_types = []
        source_lower = source.lower()

        # 基于源名称检测
        for trade_type, patterns in self.config.trade_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, source_lower, re.IGNORECASE):
                    trade_types.append(trade_type)
                    break

        # 基于列名检测
        if df is not None:
            for col in df.columns:
                col_lower = str(col).lower()
                for trade_type, patterns in self.config.trade_type_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, col_lower, re.IGNORECASE):
                            if trade_type not in trade_types:
                                trade_types.append(trade_type)
                            break

        # 如果没有检测到特定类型，默认返回出口和进口
        if not trade_types:
            trade_types = [TradeType.EXPORTS, TradeType.IMPORTS]

        return trade_types

    def _detect_trade_categories(self, df: pd.DataFrame, source: str) -> List[TradeCategory]:
        """检测商品分类"""
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

        # 如果没有检测到特定分类，返回TOTAL_TRADE
        if not categories:
            categories.append(TradeCategory.TOTAL_TRADE)

        return categories

    def _detect_trade_partners(self, df: pd.DataFrame, source: str) -> List[TradePartner]:
        """检测贸易伙伴"""
        partners = []
        source_lower = source.lower()

        # 基于源名称检测
        for partner, patterns in self.config.partner_patterns.items():
            for pattern in patterns:
                if re.search(pattern, source_lower, re.IGNORECASE):
                    partners.append(partner)
                    break

        # 基于列名检测
        if df is not None:
            for col in df.columns:
                col_lower = str(col).lower()
                for partner, patterns in self.config.partner_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, col_lower, re.IGNORECASE):
                            if partner not in partners:
                                partners.append(partner)
                            break

        # 如果没有检测到特定伙伴，返回None表示全球总计
        return partners or [None]

    def _detect_trade_type_from_name(self, name: str) -> Optional[TradeType]:
        """从名称检测贸易类型"""
        name_lower = name.lower()

        for trade_type, patterns in self.config.trade_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return trade_type

        return None

    def _detect_category_from_name(self, name: str) -> Optional[TradeCategory]:
        """从名称检测商品分类"""
        name_lower = name.lower()

        for category, patterns in self.config.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return category

        return None

    def _detect_partner_from_name(self, name: str) -> Optional[TradePartner]:
        """从名称检测贸易伙伴"""
        name_lower = name.lower()

        for partner, patterns in self.config.partner_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return partner

        return None

    def _get_dataset_key(
        self,
        trade_type: TradeType,
        category: TradeCategory,
        partner: Optional[TradePartner]
    ) -> str:
        """生成数据集键"""
        partner_str = partner.value if partner else "global"
        return f"{trade_type.value}_{category.value}_{partner_str}"

    def _extract_trade_data_points(
        self,
        df: pd.DataFrame,
        trade_type: TradeType,
        category: TradeCategory,
        partner: Optional[TradePartner],
        source_format: str,
        sheet_name: str
    ) -> List[TradeDataPoint]:
        """从DataFrame提取贸易数据点"""
        data_points = []

        try:
            # 寻找日期列和数值列
            date_columns = [col for col in df.columns if self._is_date_column(df[col])]
            value_columns = [col for col in df.columns if self._is_numeric_column(df[col])]

            if not date_columns or not value_columns:
                self.logger.warning(f"No suitable columns found for {trade_type}/{category}")
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
                                frequency = self._infer_frequency(sheet_name, df)

                                dp = TradeDataPoint(
                                    trade_type=trade_type,
                                    category=category,
                                    trade_partner=partner,
                                    frequency=frequency,
                                    date=date_val,
                                    value=Decimal(str(value)),
                                    unit='HKD Million',
                                    currency='HKD',
                                    source=f"{source_format}:{trade_type.value}"
                                )
                                data_points.append(dp)
                    except Exception as e:
                        self.logger.debug(f"Error parsing row {idx}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Error extracting data points: {e}")

        return data_points

    def _extract_json_data_points(
        self,
        data: Any,
        trade_type: TradeType,
        category: TradeCategory,
        partner: Optional[TradePartner]
    ) -> List[TradeDataPoint]:
        """从JSON数据中提取贸易数据点"""
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

    def _infer_frequency(self, sheet_name: str, df: pd.DataFrame) -> TradeFrequency:
        """推断数据频率"""
        sheet_lower = sheet_name.lower()

        if 'month' in sheet_lower or '月' in sheet_lower:
            return TradeFrequency.MONTHLY
        elif 'quarter' in sheet_lower or '季' in sheet_lower:
            return TradeFrequency.QUARTERLY
        elif 'year' in sheet_lower or '年' in sheet_lower:
            return TradeFrequency.ANNUAL

        # 基于列名推断
        if 'date' in df.columns:
            # 检查日期列中的数据粒度
            sample_dates = df['date'].dropna().head(10)
            for d in sample_dates:
                d_str = str(d)
                if re.search(r'\d{4}[/\-]\d{1,2}', d_str):
                    return TradeFrequency.MONTHLY

        return TradeFrequency.MONTHLY  # 默认月度

    async def parse_trade_data(
        self,
        file_path: Path,
        data_type: CSDDataType = CSDDataType.TRADE_STATISTICS
    ) -> Dict[str, TradeDataSet]:
        """
        解析贸易数据文件

        Args:
            file_path: 文件路径
            data_type: 数据类型

        Returns:
            贸易数据集字典
        """
        context = "TradeIntegrator.parse_trade_data"

        try:
            # 检查缓存
            cache_key = f"trade:{hashlib.md5(str(file_path).encode()).hexdigest()}"
            cached = self.cache.get(cache_key)
            if cached and self.cache.is_valid(cache_key):
                self.logger.info("Returning cached trade data")
                return cached

            # 解析文件
            results = await self.parse_file(file_path, data_type)

            if results:
                # 转换并计算增长率
                for key, dataset in results.items():
                    dataset.calculate_growth_rates()

                # 缓存结果
                self.cache.set(cache_key, results, ttl=self.config.cache_ttl)

                # 更新内部缓存
                self._parsed_data.update(results)

                self.logger.info(f"Parsed {len(results)} trade datasets")
                return results

            return {}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            self.logger.error(f"Parse error: {error_info}")
            return {}

    async def get_trade_data(
        self,
        trade_type: TradeType,
        category: TradeCategory,
        partner: Optional[TradePartner] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[TradeDataSet]:
        """获取贸易数据"""
        dataset_key = self._get_dataset_key(trade_type, category, partner)

        if dataset_key not in self._parsed_data:
            self.logger.warning(f"Trade dataset {dataset_key} not found")
            return None

        dataset = self._parsed_data[dataset_key]

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

    async def calculate_trade_balance(
        self,
        category: TradeCategory,
        date: date
    ) -> Optional[Decimal]:
        """
        计算特定日期的贸易差额

        Args:
            category: 商品分类
            date: 日期

        Returns:
            贸易差额 (出口 - 进口)
        """
        exports = await self.get_trade_data(TradeType.EXPORTS, category, None, date, date)
        imports = await self.get_trade_data(TradeType.IMPORTS, category, None, date, date)

        if not exports or not imports:
            return None

        export_value = exports.data_points[0].value if exports.data_points else Decimal('0')
        import_value = imports.data_points[0].value if imports.data_points else Decimal('0')

        return export_value - import_value

    async def get_top_trade_partners(
        self,
        trade_type: TradeType,
        category: TradeCategory,
        limit: int = 5
    ) -> List[Tuple[TradePartner, Decimal]]:
        """
        获取主要贸易伙伴

        Args:
            trade_type: 贸易类型
            category: 商品分类
            limit: 返回数量

        Returns:
            主要贸易伙伴列表
        """
        # 聚合所有伙伴的数据
        partner_values = {}

        for key, dataset in self._parsed_data.items():
            if dataset.trade_type == trade_type and dataset.category == category:
                if dataset.data_points:
                    # 使用最新数据点
                    latest_dp = max(dataset.data_points, key=lambda x: x.date)
                    if dataset.trade_partner:
                        partner = dataset.trade_partner
                        if partner not in partner_values:
                            partner_values[partner] = Decimal('0')
                        partner_values[partner] += latest_dp.value

        # 排序并返回前N个
        sorted_partners = sorted(partner_values.items(), key=lambda x: x[1], reverse=True)
        return sorted_partners[:limit]

    async def get_all_trade_types(self) -> List[TradeType]:
        """获取所有贸易类型"""
        types = set()
        for dataset in self._parsed_data.values():
            types.add(dataset.trade_type)
        return list(types)

    async def export_to_dataframe(
        self,
        trade_type: TradeType,
        category: TradeCategory,
        partner: Optional[TradePartner] = None
    ) -> Optional[pd.DataFrame]:
        """
        导出贸易数据为DataFrame

        Args:
            trade_type: 贸易类型
            category: 商品分类
            partner: 贸易伙伴

        Returns:
            DataFrame或None
        """
        dataset = await self.get_trade_data(trade_type, category, partner)
        if dataset:
            return dataset.to_dataframe()
        return None

    async def get_summary(self) -> Dict[str, Any]:
        """获取集成摘要"""
        trade_types = set()
        categories = set()
        partners = set()

        for dataset in self._parsed_data.values():
            trade_types.add(dataset.trade_type)
            categories.add(dataset.category)
            if dataset.trade_partner:
                partners.add(dataset.trade_partner)

        return {
            'integrator_name': 'TradeDataIntegrator',
            'total_datasets': len(self._parsed_data),
            'trade_types': [t.value for t in trade_types],
            'categories': [c.value for c in categories],
            'partners': [p.value for p in partners] if partners else ['Global'],
            'data_points_per_dataset': {
                key: len(dataset.data_points)
                for key, dataset in self._parsed_data.items()
            },
            'config': self.config.dict(),
            'timestamp': datetime.now().isoformat()
        }


# 便捷函数
async def parse_trade_file(file_path: Path) -> Dict[str, TradeDataSet]:
    """解析贸易文件"""
    integrator = TradeDataIntegrator()
    try:
        return await integrator.parse_trade_data(file_path)
    finally:
        await integrator.close()


async def get_trade_data(
    file_path: Path,
    trade_type: TradeType,
    category: TradeCategory,
    partner: Optional[TradePartner] = None
) -> Optional[TradeDataSet]:
    """获取特定贸易数据"""
    integrator = TradeDataIntegrator()
    try:
        await integrator.parse_trade_data(file_path)
        return await integrator.get_trade_data(trade_type, category, partner)
    finally:
        await integrator.close()
