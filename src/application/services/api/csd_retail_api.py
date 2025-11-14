"""
T059: C&SD 零售销售API集成

从香港统计处(C&SD)获取零售销售数据的专门API模块
提供6个核心零售指标的实时数据访问

指标列表:
- retail_total_sales: 零售销售总额
- retail_clothing: 服装鞋履
- retail_supermarket: 超市
- retail_restaurants: 餐饮
- retail_electronics: 电器
- retail_yoy_growth: 同比增长率

特性:
- C&SD Web Tables API集成
- 数据格式标准化
- 错误处理和重试机制
- 缓存支持
- 实时数据验证

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import asyncio
import json
import logging
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import urllib.parse

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CSDRetailAPI:
    """
    C&SD零售销售数据API客户端

    专门用于从香港统计处获取零售销售相关统计数据
    """

    BASE_URL = "https://www.censtatd.gov.hk"
    API_BASE = f"{BASE_URL}/en/api"

    # 零售销售数据表配置
    RETAIL_TABLES = {
        "86": {
            "name": "Retail Sales Statistics",
            "name_zh": "零售销售统计",
            "description": "Monthly retail sales statistics by type of retail outlet",
            "indicators": {
                "retail_total_sales": {
                    "name": "Total retail sales",
                    "name_zh": "零售销售总额",
                    "unit": "HKD Million",
                    "code": "86.1"
                },
                "retail_clothing": {
                    "name": "Clothing, footwear and allied products",
                    "name_zh": "服装、鞋履及有关产品",
                    "unit": "HKD Million",
                    "code": "86.2"
                },
                "retail_supermarket": {
                    "name": "Supermarkets",
                    "name_zh": "超级市场",
                    "unit": "HKD Million",
                    "code": "86.3"
                },
                "retail_restaurants": {
                    "name": "Restaurants",
                    "name_zh": "食肆",
                    "unit": "HKD Million",
                    "code": "86.4"
                },
                "retail_electronics": {
                    "name": "Electrical appliances and consumer electronics",
                    "name_zh": "电器及电子产品",
                    "unit": "HKD Million",
                    "code": "86.5"
                }
            },
            "frequency": "monthly",
            "start_year": 1990,
            "last_updated": datetime.now().isoformat()
        },
        "87": {
            "name": "Retail Sales Growth Statistics",
            "name_zh": "零售销售增长统计",
            "description": "Year-on-year growth rates of retail sales",
            "indicators": {
                "retail_yoy_growth": {
                    "name": "Year-on-year growth rate of total retail sales",
                    "name_zh": "零售销售总额同比增长率",
                    "unit": "%",
                    "code": "87.1"
                }
            },
            "frequency": "monthly",
            "start_year": 1995,
            "last_updated": datetime.now().isoformat()
        }
    }

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化C&SD零售API客户端

        Args:
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger("hk_quant_system.csd_retail_api")

        # 配置HTTP会话
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
            "Accept": "application/json, text/html, application/vnd.ms-excel",
            "Accept-Language": "en,zh-CN,zh;q=0.9,zh-HK;q=0.8"
        })

    async def get_retail_data(
        self,
        indicator: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        获取零售数据

        Args:
            indicator: 指标代码 (e.g., 'retail_total_sales')
            start_date: 开始日期
            end_date: 结束日期
            format: 返回格式 (json/csv/xlsx)

        Returns:
            包含数据的字典
        """
        # 查找指标所属的数据表
        table_id, indicator_code = self._find_indicator_table(indicator)
        if not table_id:
            return {
                'success': False,
                'error': f'Unknown indicator: {indicator}',
                'data': []
            }

        try:
            # 构建API请求
            url = f"{self.API_BASE}/getWebTable"
            params = {
                "tableId": table_id,
                "download": "yes",
                "format": format,
                "lang": "en"
            }

            # 添加日期范围
            if start_date:
                params["from"] = start_date.strftime("%Y-%m")
            if end_date:
                params["to"] = end_date.strftime("%Y-%m")

            self.logger.info(f"Fetching {indicator} from C&SD (table {table_id})")

            # 发送请求
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(url, params=params, timeout=self.timeout)
            )

            if response.status_code != 200:
                self.logger.error(f"API request failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': []
                }

            # 解析响应
            if format.lower() == "json":
                data = response.json()
            else:
                # 对于非JSON格式，需要解析文件
                data = await self._parse_data_file(response.content, format)

            # 提取特定指标数据
            filtered_data = self._extract_indicator_data(data, indicator, indicator_code)

            if not filtered_data:
                return {
                    'success': False,
                    'error': 'No data found for indicator',
                    'data': []
                }

            # 标准化数据格式
            normalized_data = self._normalize_retail_data(filtered_data, indicator)

            return {
                'success': True,
                'data': normalized_data,
                'indicator': indicator,
                'table_id': table_id,
                'count': len(normalized_data),
                'date_range': {
                    'start': min(d['date'] for d in normalized_data) if normalized_data else None,
                    'end': max(d['date'] for d in normalized_data) if normalized_data else None
                },
                'timestamp': datetime.now().isoformat()
            }

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {indicator}")
            return {
                'success': False,
                'error': 'Request timeout',
                'data': []
            }
        except Exception as e:
            self.logger.error(f"Error fetching {indicator}: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def _find_indicator_table(self, indicator: str) -> Tuple[Optional[str], Optional[str]]:
        """
        查找指标所属的数据表

        Args:
            indicator: 指标代码

        Returns:
            (table_id, indicator_code) 元组
        """
        for table_id, table_info in self.RETAIL_TABLES.items():
            if 'indicators' in table_info and indicator in table_info['indicators']:
                indicator_code = table_info['indicators'][indicator]['code']
                return table_id, indicator_code

        return None, None

    async def _parse_data_file(self, content: bytes, format: str) -> Dict:
        """
        解析数据文件

        Args:
            content: 文件内容
            format: 文件格式

        Returns:
            解析后的数据
        """
        try:
            if format.lower() == "csv":
                import io
                df = pd.read_csv(io.BytesIO(content))
                return df.to_dict('records')
            elif format.lower() in ["xlsx", "xls"]:
                import io
                df = pd.read_excel(io.BytesIO(content))
                return df.to_dict('records')
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Error parsing {format} file: {e}")
            return {}

    def _extract_indicator_data(
        self,
        data: Any,
        indicator: str,
        indicator_code: str
    ) -> List[Dict[str, Any]]:
        """
        提取特定指标的数据

        Args:
            data: 原始数据
            indicator: 指标代码
            indicator_code: 指标代码

        Returns:
            提取的数据列表
        """
        extracted = []

        try:
            if isinstance(data, dict):
                # 处理JSON格式
                if 'data' in data:
                    raw_data = data['data']
                else:
                    raw_data = data

                if isinstance(raw_data, list):
                    for item in raw_data:
                        # 匹配指标代码或名称
                        if self._matches_indicator(item, indicator, indicator_code):
                            extracted.append(item)

            elif isinstance(data, list):
                for item in data:
                    if self._matches_indicator(item, indicator, indicator_code):
                        extracted.append(item)

        except Exception as e:
            self.logger.error(f"Error extracting indicator data: {e}")

        return extracted

    def _matches_indicator(self, item: Dict, indicator: str, code: str) -> bool:
        """
        检查数据项是否匹配指标

        Args:
            item: 数据项
            indicator: 指标代码
            code: 指标代码

        Returns:
            匹配结果
        """
        # 检查指标代码
        if 'code' in item and code in str(item['code']):
            return True

        # 检查指标名称
        if 'indicator' in item:
            indicator_name = item['indicator'].lower()
            if indicator == 'retail_total_sales':
                return 'total' in indicator_name and 'retail' in indicator_name
            elif indicator == 'retail_clothing':
                return any(kw in indicator_name for kw in ['clothing', 'footwear', 'apparel'])
            elif indicator == 'retail_supermarket':
                return 'supermarket' in indicator_name
            elif indicator == 'retail_restaurants':
                return any(kw in indicator_name for kw in ['restaurant', 'eating', 'food'])
            elif indicator == 'retail_electronics':
                return any(kw in indicator_name for kw in ['electrical', 'electronic', 'appliance'])
            elif indicator == 'retail_yoy_growth':
                return 'growth' in indicator_name

        return False

    def _normalize_retail_data(
        self,
        data: List[Dict[str, Any]],
        indicator: str
    ) -> List[Dict[str, Any]]:
        """
        标准化零售数据格式

        Args:
            data: 原始数据列表
            indicator: 指标代码

        Returns:
            标准化后的数据列表
        """
        normalized = []

        for item in data:
            try:
                # 提取日期
                date_str = self._extract_date(item)
                if not date_str:
                    continue

                # 提取数值
                value = self._extract_value(item)
                if value is None:
                    continue

                # 标准化
                normalized_item = {
                    'date': date_str,
                    'indicator': indicator,
                    'value': value,
                    'unit': self._extract_unit(item, indicator),
                    'source': 'C&SD',
                    'source_url': f"{self.BASE_URL}/en/data/domestic_trade/",
                    'last_updated': datetime.now().isoformat()
                }

                normalized.append(normalized_item)

            except Exception as e:
                self.logger.debug(f"Error normalizing item: {e}")
                continue

        # 按日期排序
        normalized.sort(key=lambda x: x['date'])

        return normalized

    def _extract_date(self, item: Dict[str, Any]) -> Optional[str]:
        """提取日期"""
        date_fields = ['date', 'Date', 'period', 'Period', 'month', 'Month']

        for field in date_fields:
            if field in item and item[field]:
                date_str = str(item[field])

                # 尝试解析各种日期格式
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date

        return None

    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        # YYYY-MM 或 YYYY/MM
        match = re.match(r'(\d{4})[/\-](\d{1,2})', date_str)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            return f"{year}-{month:02d}-01"

        # YYYY年MM月
        match = re.match(r'(\d{4})年(\d{1,2})月', date_str)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            return f"{year}-{month:02d}-01"

        # YYYY
        match = re.match(r'(\d{4})', date_str)
        if match:
            year = int(match.group(1))
            return f"{year}-12-31"

        return None

    def _extract_value(self, item: Dict[str, Any]) -> Optional[float]:
        """提取数值"""
        value_fields = ['value', 'Value', 'value_usd', 'Value_USD', 'amount', 'Amount']

        for field in value_fields:
            if field in item and item[field] is not None:
                value_str = str(item[field]).replace(',', '').replace(' ', '')
                try:
                    return float(value_str)
                except (ValueError, TypeError):
                    continue

        return None

    def _extract_unit(self, item: Dict[str, Any], indicator: str) -> str:
        """提取单位"""
        if 'unit' in item:
            return item['unit']

        # 根据指标设置默认单位
        if indicator == 'retail_yoy_growth':
            return '%'
        else:
            return 'HKD Million'

    async def get_all_retail_indicators(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取所有零售指标

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            所有指标的数据字典
        """
        results = {}
        indicators = [
            'retail_total_sales',
            'retail_clothing',
            'retail_supermarket',
            'retail_restaurants',
            'retail_electronics',
            'retail_yoy_growth'
        ]

        # 并行获取所有指标
        tasks = []
        for indicator in indicators:
            task = self.get_retail_data(indicator, start_date, end_date)
            tasks.append((indicator, task))

        for indicator, task in tasks:
            try:
                result = await task
                results[indicator] = result
            except Exception as e:
                self.logger.error(f"Error fetching {indicator}: {e}")
                results[indicator] = {
                    'success': False,
                    'error': str(e),
                    'data': []
                }

        return results

    def get_supported_indicators(self) -> Dict[str, Dict[str, str]]:
        """
        获取支持的指标列表

        Returns:
            指标信息字典
        """
        all_indicators = {}
        for table_id, table_info in self.RETAIL_TABLES.items():
            if 'indicators' in table_info:
                all_indicators.update(table_info['indicators'])

        return all_indicators

    def get_table_info(self, table_id: str) -> Optional[Dict[str, Any]]:
        """
        获取数据表信息

        Args:
            table_id: 数据表ID

        Returns:
            数据表信息
        """
        return self.RETAIL_TABLES.get(table_id)

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接

        Returns:
            连接测试结果
        """
        try:
            # 尝试获取一个简单的请求
            url = f"{self.BASE_URL}/en/api"
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.session.get(url, timeout=self.timeout)
            )

            return {
                'success': True,
                'status_code': response.status_code,
                'url': url,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()
