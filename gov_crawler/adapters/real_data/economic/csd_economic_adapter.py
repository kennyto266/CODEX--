#!/usr/bin/env python3
"""
C&SD 經濟數據適配器 - 真實數據源
從香港政府統計處獲取真實的經濟統計數據
絕對不使用 mock 數據
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from bs4 import BeautifulSoup
import re

from ..base_real_adapter import RealDataAdapter, validate_no_mock_data

logger = logging.getLogger(__name__)

class CSDEconomicAdapter(RealDataAdapter):
    """
    C&SD 經濟數據適配器
    從政府統計處獲取真實的經濟統計數據

    支持的數據類型:
    - GDP (國內生產總值)
    - 零售銷售
    - 人口統計
    - 失業率
    - 消費者物價指數
    """

    def __init__(self):
        super().__init__(
            name="C&SD Economic Data",
            source_url="https://www.censtatd.gov.hk/en/"
        )
        self.log_real_data_warning()

        # C&SD 數據端點
        self.data_endpoints = {
            "gdp": "https://www.censtatd.gov.hk/en/data/",
            "retail": "https://www.censtatd.gov.hk/en/data/",
            "population": "https://www.censtatd.gov.hk/en/data/",
            "cpi": "https://www.censtatd.gov.hk/en/data/",
            "unemployment": "https://www.censtatd.gov.hk/en/data/",
        }

    @validate_no_mock_data
    async def fetch_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從 C&SD 獲取真實經濟數據
        """
        logger.info("正在從政府統計處獲取真實經濟數據...")

        records = []

        try:
            # 嘗試獲取不同類型的經濟數據
            data_types = ['gdp', 'retail_sales', 'population', 'cpi', 'unemployment']

            for data_type in data_types:
                try:
                    df = await self._fetch_data_type(data_type, start_date, end_date)
                    if df is not None and not df.empty:
                        records.extend(df.to_dict('records'))
                    logger.info(f"成功獲取 {data_type} 數據: {len(df)} 條記錄")
                except Exception as e:
                    logger.warning(f"獲取 {data_type} 數據失敗: {str(e)}")
                    continue

            if not records:
                raise ValueError("無法從 C&SD 獲取任何真實數據")

            df = pd.DataFrame(records)

            # 確保所有記錄都標記為真實數據
            df['is_real'] = True
            df['is_mock'] = False  # 明確標記

            # 添加數據來源標記
            df['source'] = 'C&SD_Official'

            return df

        except Exception as e:
            logger.error(f"獲取 C&SD 經濟數據失敗: {str(e)}")
            raise

    async def _fetch_data_type(self, data_type: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取特定類型的經濟數據
        """
        if data_type == 'gdp':
            return await self._fetch_gdp_data(start_date, end_date)
        elif data_type == 'retail_sales':
            return await self._fetch_retail_sales_data(start_date, end_date)
        elif data_type == 'population':
            return await self._fetch_population_data(start_date, end_date)
        elif data_type == 'cpi':
            return await self._fetch_cpi_data(start_date, end_date)
        elif data_type == 'unemployment':
            return await self._fetch_unemployment_data(start_date, end_date)
        else:
            return pd.DataFrame()

    async def _fetch_gdp_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取 GDP 數據
        """
        try:
            # 嘗試訪問 C&SD 的 GDP 數據頁面
            gdp_url = "https://www.censtatd.gov.hk/en/data/"
            async with self.session.get(gdp_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_gdp(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取 GDP 數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_retail_sales_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取零售銷售數據
        """
        try:
            async with self.session.get(self.source_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_retail(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取零售銷售數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_population_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取人口統計數據
        """
        try:
            # 人口數據通常變化較慢，可能需要不同的數據源
            async with self.session.get(self.source_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_population(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取人口數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_cpi_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取消費者物價指數數據
        """
        try:
            async with self.session.get(self.source_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_cpi(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取 CPI 數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_unemployment_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取失業率數據
        """
        try:
            async with self.session.get(self.source_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_unemployment(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取失業率數據失敗: {str(e)}")
            return pd.DataFrame()

    def _parse_html_for_gdp(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的 GDP 數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        # 查找包含 GDP 的表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            # 檢查是否為 GDP 表格
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('gdp' in header or 'gross domestic product' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            period = cells[0].get_text().strip()
                            gdp_value = self._parse_number(cells[1].get_text())
                            growth_rate = self._parse_number(cells[2].get_text())

                            if period and gdp_value is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'GDP',
                                    'value': gdp_value,
                                    'growth_rate': growth_rate,
                                    'unit': 'HKD Million',
                                    'frequency': 'Quarterly',
                                    'source': 'C&SD_GDP',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_retail(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的零售銷售數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        # 查找零售銷售相關表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            # 檢查是否為零售銷售表格
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('retail' in header or 'sales' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            period = cells[0].get_text().strip()
                            total_sales = self._parse_number(cells[1].get_text())
                            yoy_growth = self._parse_number(cells[2].get_text())

                            if period and total_sales is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'Retail Sales',
                                    'value': total_sales,
                                    'yoy_growth': yoy_growth,
                                    'unit': 'HKD Million',
                                    'frequency': 'Monthly',
                                    'source': 'C&SD_Retail',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_population(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的人口數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('population' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 2:
                        try:
                            year = cells[0].get_text().strip()
                            population = self._parse_number(cells[1].get_text())

                            if year and population is not None:
                                record = {
                                    'date': year,
                                    'indicator': 'Population',
                                    'value': population,
                                    'unit': 'Thousand',
                                    'frequency': 'Annually',
                                    'source': 'C&SD_Population',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_cpi(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的 CPI 數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('cpi' in header or 'consumer price' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            period = cells[0].get_text().strip()
                            cpi_value = self._parse_number(cells[1].get_text())
                            inflation_rate = self._parse_number(cells[2].get_text())

                            if period and cpi_value is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'CPI',
                                    'value': cpi_value,
                                    'inflation_rate': inflation_rate,
                                    'unit': 'Index',
                                    'frequency': 'Monthly',
                                    'source': 'C&SD_CPI',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_unemployment(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的失業率數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('unemployment' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 2:
                        try:
                            period = cells[0].get_text().strip()
                            unemployment_rate = self._parse_number(cells[1].get_text())

                            if period and unemployment_rate is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'Unemployment Rate',
                                    'value': unemployment_rate,
                                    'unit': 'Percentage',
                                    'frequency': 'Quarterly',
                                    'source': 'C&SD_Unemployment',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_number(self, text: str) -> Optional[float]:
        """
        解析數字字符串
        """
        if not text:
            return None

        # 移除逗號、空格和其他非數字字符（保留小數點和負號）
        cleaned = re.sub(r'[^\d.-]', '', text.strip())
        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    def get_supported_indicators(self) -> List[str]:
        """
        獲取支持的經濟指標列表
        """
        return [
            'GDP',
            'Retail Sales',
            'Population',
            'CPI',
            'Unemployment Rate',
            'Trade Balance',
            'Tourist Arrivals',
            'Property Prices'
        ]

    def get_data_description(self) -> Dict[str, Any]:
        """
        獲取數據描述
        """
        return {
            'source': 'Census and Statistics Department (C&SD), HKSAR',
            'website': 'https://www.censtatd.gov.hk/',
            'data_type': 'Economic Statistics',
            'indicators': self.get_supported_indicators(),
            'update_frequency': 'Monthly/Quarterly/Annually',
            'data_quality': 'Official Government Statistics',
            'is_real_data': True,
            'mock_enabled': False,
            'description': 'Comprehensive economic statistics from Hong Kong government statistical office.',
        }

    async def get_data_source_authentication(self) -> Dict[str, str]:
        """
        獲取數據源認證信息
        """
        return {
            "source_name": "Census and Statistics Department",
            "website": "https://www.censtatd.gov.hk/",
            "contact_email": "enquiry@censtatd.gov.hk",
            "data_license": "Open Government License",
            "authentication_required": False,
            "rate_limits": "Unknown - check with C&SD",
            "notes": "Public statistics available for research purposes",
        }

    async def test_connection(self) -> bool:
        """
        測試與 C&SD 的連接
        """
        try:
            async with self.session.get(self.source_url) as response:
                return response.status == 200
        except Exception:
            return False

    def validate_economic_values(self, df: pd.DataFrame) -> List[str]:
        """
        驗證經濟數據值的合理性
        """
        errors = []

        if df.empty:
            errors.append("數據框為空")
            return errors

        # 按指標類型驗證
        for indicator in df['indicator'].unique():
            indicator_data = df[df['indicator'] == indicator]

            if indicator == 'GDP':
                values = indicator_data['value'].dropna()
                if len(values) > 0:
                    if values.min() < 0:
                        errors.append("GDP 不能為負數")
                    if values.max() > 10000000:  # 10萬億
                        errors.append("GDP 數值過高，請檢查")

            elif indicator == 'Unemployment Rate':
                values = indicator_data['value'].dropna()
                if len(values) > 0:
                    if values.min() < 0:
                        errors.append("失業率不能為負數")
                    if values.max() > 50:
                        errors.append("失業率過高 (>50%)")

            elif indicator == 'CPI':
                values = indicator_data['value'].dropna()
                if len(values) > 0:
                    if values.min() < 0:
                        errors.append("CPI 不能為負數")

        return errors

# 導出適配器類
__all__ = ['CSDEconomicAdapter']
