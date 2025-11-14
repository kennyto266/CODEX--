"""
C&SD Web Tables API 集成模块

从香港特别行政区政府统计处(C&SD)获取GDP和其他经济数据
支持官方Web Tables API和数据文件下载

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import re
import zipfile
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import urllib.parse

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CSDWebTableAPI:
    """
    C&SD Web Tables API 客户端

    提供从C&SD网站获取统计数据的接口
    """

    BASE_URL = "https://www.censtatd.gov.hk"
    API_BASE = f"{BASE_URL}/en/api"

    # 支持的数据表
    SUPPORTED_TABLES = {
        # GDP相关数据表
        "33": {
            "name": "Gross Domestic Product (GDP)",
            "description": "本地生产总值",
            "indicators": [
                "gdp_nominal",
                "gdp_real",
                "gdp_growth",
                "gdp_per_capita",
                "gdp_primary",
                "gdp_secondary",
                "gdp_tertiary"
            ],
            "frequency": "quarterly",
            "start_year": 1970
        },
        # 贸易数据
        "52": {
            "name": "Merchandise Trade Statistics",
            "description": "商品贸易统计",
            "indicators": [
                "trade_export",
                "trade_import",
                "trade_balance"
            ],
            "frequency": "monthly",
            "start_year": 1960
        },
        # 人口数据
        "11": {
            "name": "Population Statistics",
            "description": "人口统计",
            "indicators": [
                "population",
                "population_growth"
            ],
            "frequency": "annual",
            "start_year": 1961
        }
    }

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化API客户端

        Args:
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.logger = logging.getLogger("hk_quant_system.csd_api")

        # 配置重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置请求头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; HKQuantSystem/1.0)",
            "Accept": "application/json, text/html",
            "Accept-Language": "en,zh-CN,zh;q=0.9"
        })

    def get_web_table_data(
        self,
        table_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: str = "json"
    ) -> Optional[Dict]:
        """
        获取Web Table数据

        Args:
            table_id: 数据表ID
            start_date: 开始日期
            end_date: 结束日期
            format: 返回格式 (json/csv/xlsx)

        Returns:
            数据字典或None
        """
        if table_id not in self.SUPPORTED_TABLES:
            self.logger.error(f"Unsupported table ID: {table_id}")
            return None

        try:
            # 构建API URL
            url = f"{self.API_BASE}/web_table"
            params = {
                "id": table_id,
                "download": "yes",
                "format": format
            }

            # 添加日期范围
            if start_date:
                params["from"] = start_date.isoformat()
            if end_date:
                params["to"] = end_date.isoformat()

            self.logger.info(f"Fetching table {table_id} from C&SD")

            # 发送请求
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                if format.lower() == "json":
                    return response.json()
                else:
                    # 对于其他格式，保存到临时文件
                    return self._save_temp_file(response.content, format)
            else:
                self.logger.error(f"API request failed: {response.status_code} {response.reason}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching web table data: {e}")
            return None

    def search_tables(self, keyword: str) -> List[Dict]:
        """
        搜索数据表

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的数据表列表
        """
        results = []
        keyword_lower = keyword.lower()

        for table_id, table_info in self.SUPPORTED_TABLES.items():
            # 在名称、描述和指标中搜索
            searchable_text = f"{table_info['name']} {table_info['description']} {' '.join(table_info['indicators'])}"
            if keyword_lower in searchable_text.lower():
                results.append({
                    "table_id": table_id,
                    **table_info
                })

        return results

    def get_table_info(self, table_id: str) -> Optional[Dict]:
        """
        获取数据表信息

        Args:
            table_id: 数据表ID

        Returns:
            数据表信息
        """
        return self.SUPPORTED_TABLES.get(table_id)

    def download_excel(
        self,
        table_id: str,
        output_path: Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> bool:
        """
        下载Excel文件

        Args:
            table_id: 数据表ID
            output_path: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            下载是否成功
        """
        try:
            url = f"{self.BASE_URL}/en/data/web_table/{table_id}"
            params = {"download": "yes"}

            if start_date:
                params["from"] = start_date.isoformat()
            if end_date:
                params["to"] = end_date.isoformat()

            self.logger.info(f"Downloading Excel for table {table_id}")

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Excel file saved to {output_path}")
                return True
            else:
                self.logger.error(f"Download failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error downloading Excel: {e}")
            return False

    def parse_excel_data(
        self,
        file_path: Path,
        table_id: str
    ) -> Optional[Dict]:
        """
        解析Excel数据文件

        Args:
            file_path: Excel文件路径
            table_id: 数据表ID

        Returns:
            解析后的数据字典
        """
        try:
            self.logger.info(f"Parsing Excel file: {file_path}")

            # 尝试读取Excel文件
            # C&SD的Excel文件可能有多个工作表，需要尝试不同的读取方式
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            results = {}

            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if df.empty:
                        continue

                    # 解析数据
                    parsed_data = self._extract_data_from_df(df, table_id)
                    if parsed_data:
                        results[sheet_name] = parsed_data

                except Exception as e:
                    self.logger.warning(f"Error parsing sheet {sheet_name}: {e}")
                    continue

            return results if results else None

        except Exception as e:
            self.logger.error(f"Error parsing Excel file: {e}")
            return None

    def _extract_data_from_df(
        self,
        df: pd.DataFrame,
        table_id: str
    ) -> Optional[List[Dict]]:
        """
        从DataFrame提取数据

        Args:
            df: DataFrame
            table_id: 数据表ID

        Returns:
            提取的数据列表
        """
        try:
            data = []
            table_info = self.SUPPORTED_TABLES.get(table_id, {})

            # 尝试找到日期列和数值列
            date_columns = self._find_date_columns(df)
            value_columns = self._find_value_columns(df)

            if not date_columns or not value_columns:
                self.logger.warning(f"Could not find date or value columns in table {table_id}")
                return None

            # 使用第一个日期列和所有数值列
            date_col = date_columns[0]

            for idx, row in df.iterrows():
                try:
                    # 解析日期
                    date_str = str(row[date_col])
                    parsed_date = self._parse_date_string(date_str)

                    if not parsed_date:
                        continue

                    # 提取数值
                    for value_col in value_columns:
                        value_str = str(row[value_col])
                        value = self._parse_numeric_value(value_str)

                        if value is not None:
                            # 确定指标类型
                            indicator = self._detect_indicator_from_column(
                                value_col, table_info.get('indicators', [])
                            )

                            data.append({
                                'date': parsed_date,
                                'value': value,
                                'indicator': indicator,
                                'unit': self._infer_unit(value_col),
                                'source': f"censtatd.gov.hk/table/{table_id}",
                                'raw_column': value_col
                            })

                except Exception as e:
                    self.logger.debug(f"Error parsing row {idx}: {e}")
                    continue

            return data

        except Exception as e:
            self.logger.error(f"Error extracting data from DataFrame: {e}")
            return None

    def _find_date_columns(self, df: pd.DataFrame) -> List[str]:
        """查找日期列"""
        date_columns = []

        for col in df.columns:
            # 检查列名
            if re.search(r'date|year|period|time', str(col).lower()):
                date_columns.append(col)
                continue

            # 检查数据类型和内容
            sample = df[col].dropna().head(10).astype(str)
            if any(self._parse_date_string(str(val)) for val in sample):
                date_columns.append(col)

        return date_columns

    def _find_value_columns(self, df: pd.DataFrame) -> List[str]:
        """查找数值列"""
        value_columns = []

        for col in df.columns:
            # 跳过明显不是数值的列
            if re.search(r'date|year|period|time|note|remark', str(col).lower()):
                continue

            # 检查是否为数值列
            if pd.api.types.is_numeric_dtype(df[col]):
                value_columns.append(col)
            else:
                # 尝试检查样本值
                sample = df[col].dropna().head(10)
                numeric_count = sum(1 for val in sample if self._parse_numeric_value(str(val)) is not None)
                if numeric_count / len(sample) > 0.8:  # 80%以上为数值
                    value_columns.append(col)

        return value_columns

    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        date_str = date_str.strip()

        # 季度格式: 2023Q1, 2023 Q1
        q_match = re.search(r'(\d{4})[Qq](\d)', date_str)
        if q_match:
            year, quarter = int(q_match.group(1)), int(q_match.group(2))
            month = quarter * 3
            return date(year, month, 1)

        # 年份格式: 2023
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1950 <= year <= 2030:
                return date(year, 12, 31)

        # 年月格式: 2023-01, 2023/01
        ym_match = re.search(r'(\d{4})[/\-](\d{1,2})', date_str)
        if ym_match:
            year, month = int(ym_match.group(1)), int(ym_match.group(2))
            if 1 <= month <= 12:
                return date(year, month, 1)

        # 完整日期格式
        try:
            parsed = pd.to_datetime(date_str)
            return parsed.date()
        except:
            pass

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

    def _detect_indicator_from_column(
        self,
        column_name: str,
        available_indicators: List[str]
    ) -> str:
        """
        从列名检测指标类型

        Args:
            column_name: 列名
            available_indicators: 可用指标列表

        Returns:
            检测到的指标类型
        """
        column_lower = column_name.lower()

        # 优先匹配可用指标
        for indicator in available_indicators:
            if indicator.lower() in column_lower:
                return indicator

        # 基于列名模式匹配
        if 'nominal' in column_lower or '名目' in column_lower:
            return 'gdp_nominal'
        elif 'real' in column_lower or '实质' in column_lower:
            return 'gdp_real'
        elif 'growth' in column_lower or '增长' in column_lower:
            return 'gdp_growth'
        elif 'primary' in column_lower or '第一产业' in column_lower:
            return 'gdp_primary'
        elif 'secondary' in column_lower or '第二产业' in column_lower:
            return 'gdp_secondary'
        elif 'tertiary' in column_lower or '第三产业' in column_lower:
            return 'gdp_tertiary'

        # 默认返回第一个可用指标
        return available_indicators[0] if available_indicators else 'unknown'

    def _infer_unit(self, column_name: str) -> str:
        """推断数据单位"""
        column_lower = column_name.lower()

        if 'million' in column_lower or '百万' in column_lower:
            return 'HKD Million'
        elif 'billion' in column_lower or '十亿' in column_lower:
            return 'HKD Billion'
        elif '%' in column_lower or 'percent' in column_lower or '%' in column_name:
            return '%'
        else:
            # 默认单位
            return 'HKD Million'

    def _save_temp_file(self, content: bytes, format: str) -> Dict:
        """保存临时文件"""
        temp_dir = Path("data/temp_csd")
        temp_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"csd_data_{timestamp}.{format}"
        file_path = temp_dir / filename

        with open(file_path, 'wb') as f:
            f.write(content)

        return {
            "file_path": str(file_path),
            "format": format,
            "size": len(content)
        }

    def get_available_tables(self) -> List[Dict]:
        """获取所有可用数据表"""
        return [
            {"table_id": table_id, **table_info}
            for table_id, table_info in self.SUPPORTED_TABLES.items()
        ]

    def close(self):
        """关闭会话"""
        self.session.close()


# 便捷函数
async def get_gdp_data_from_csd(
    table_id: str = "33",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Optional[Dict]:
    """
    从C&SD获取GDP数据

    Args:
        table_id: 数据表ID (默认33为GDP)
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        GDP数据字典
    """
    api = CSDWebTableAPI()
    try:
        return api.get_web_table_data(table_id, start_date, end_date, "json")
    finally:
        api.close()


async def download_and_parse_gdp_excel(
    output_dir: Path,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Optional[Dict]:
    """
    下载并解析GDP Excel文件

    Args:
        output_dir: 输出目录
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        解析后的数据
    """
    api = CSDWebTableAPI()
    try:
        # 下载Excel文件
        excel_path = output_dir / "gdp_data.xlsx"
        if api.download_excel("33", excel_path, start_date, end_date):
            # 解析数据
            return api.parse_excel_data(excel_path, "33")
        return None
    finally:
        api.close()
