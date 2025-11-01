#!/usr/bin/env python3
"""
土地註冊處物業數據適配器 - Real Estate Data Adapter
從香港土地註冊處獲取真實的物業交易數據
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
from pathlib import Path

from ..base_real_adapter import RealDataAdapter, validate_no_mock_data

logger = logging.getLogger(__name__)

class LandRegPropertyAdapter(RealDataAdapter):
    """
    土地註冊處物業數據適配器
    從土地註冊處獲取真實的物業市場數據

    支持的數據類型:
    - 物業交易數據
    - 樓價指數
    - 交易量統計
    - 地區分析
    - 面積分布
    """

    def __init__(self):
        super().__init__(
            name="Land Registry Property Data",
            source_url="https://www.landreg.gov.hk/"
        )
        self.log_real_data_warning()

        # 香港政府開放數據源 - RVD官方數據
        self.data_endpoints = {
            "property_prices_1982_1998": "http://www.rvd.gov.hk/datagovhk/1.2Q(82-98).csv",
            "property_rents_1982_1998": "http://www.rvd.gov.hk/datagovhk/1.1Q(82-98).csv",
            "property_prices_1999_2025": "http://www.rvd.gov.hk/datagovhk/1.2Q(99-).csv",
            "property_rents_1999_2025": "http://www.rvd.gov.hk/datagovhk/1.1Q(99-).csv",
            "market_statistics": "https://www.landreg.gov.hk/en/market-statistics/",
            "transaction_data": "https://www.landreg.gov.hk/en/transaction-statistics/",
        }

        # 支持的地區
        self.districts = [
            "Central and Western",
            "Eastern",
            "Southern",
            "Wan Chai",
            "Sham Shui Po",
            "Kowloon City",
            "Kwun Tong",
            "Wong Tai Sin",
            "Yau Tsim Mong",
            "Islands",
            "Kwai Tsing",
            "North",
            "Sai Kung",
            "Sha Tin",
            "Tai Po",
            "Tsuen Wan",
            "Tuen Mun",
            "Yuen Long"
        ]

    @validate_no_mock_data
    async def fetch_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從香港政府開放數據源獲取真實物業數據 (RVD官方數據)
        """
        logger.info("正在從香港政府開放數據源獲取真實物業數據...")

        records = []

        try:
            # 從 RVD 官方 CSV 數據源獲取數據 (僅使用可用的數據源)
            csv_sources = [
                ("property_prices_1982_1998", "Property Price"),
                ("property_rents_1982_1998", "Rental Price")
            ]

            for source_key, indicator in csv_sources:
                if source_key in self.data_endpoints:
                    try:
                        df = await self._fetch_csv_data(
                            self.data_endpoints[source_key],
                            indicator,
                            source_key
                        )
                        if df is not None and not df.empty:
                            records.extend(df.to_dict('records'))
                            logger.info(f"成功獲取 {source_key} 數據: {len(df)} 條記錄")
                    except Exception as e:
                        logger.warning(f"獲取 {source_key} 數據失敗: {str(e)}")
                        continue

            if not records:
                raise ValueError("無法從土地註冊處獲取任何真實數據")

            df = pd.DataFrame(records)

            # 確保所有記錄都標記為真實數據
            df['is_real'] = True
            df['is_mock'] = False

            # 添加數據來源標記
            df['source'] = 'RVD_Official_OpenData'

            # 過濾日期範圍
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

            logger.info(f"總共獲取 {len(df)} 條真實物業數據記錄")
            return df

        except Exception as e:
            logger.error(f"獲取土地註冊處物業數據失敗: {str(e)}")
            raise

    async def _fetch_csv_data(self, url: str, indicator: str, source_key: str) -> pd.DataFrame:
        """
        從 RVD CSV 數據源獲取數據
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_csv_content(content, indicator, source_key)
                    else:
                        logger.warning(f"無法獲取 {url}: HTTP {response.status}")
                        return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取 CSV 數據失敗 {url}: {str(e)}")
            return pd.DataFrame()

    def _parse_csv_content(self, content: str, indicator: str, source_key: str) -> pd.DataFrame:
        """
        解析 RVD CSV 內容
        """
        try:
            import io
            df = pd.read_csv(io.StringIO(content))

            # 跳過第一行（標題行）
            if len(df) > 0:
                df = df.iloc[1:].reset_index(drop=True)

            records = []
            for idx, row in df.iterrows():
                try:
                    # 獲取季度信息
                    quarter = str(row.iloc[0]) if pd.notna(row.iloc[0]) else None
                    if not quarter or quarter == 'nan':
                        continue

                    # 轉換為日期
                    date = self._parse_quarter_to_date(quarter)
                    if date is None:
                        continue

                    # 處理各列數據
                    for col_idx in range(1, min(len(row), 10)):
                        col_name = df.columns[col_idx]
                        value = row.iloc[col_idx]

                        if pd.notna(value):
                            try:
                                float_value = float(value)
                                if float_value > 0:  # 確保是正數
                                    # 提取地區和類別
                                    region = self._extract_region_from_column(col_name)
                                    property_class = self._extract_class_from_column(col_name)

                                    record = {
                                        'date': date,
                                        'indicator': indicator,
                                        'value': float_value,
                                        'region': region,
                                        'property_class': property_class,
                                        'source_key': source_key,
                                        'unit': 'HKD per sqm',
                                        'frequency': 'Quarterly',
                                        'is_real': True,
                                        'is_mock': False,
                                    }
                                    records.append(record)
                            except (ValueError, TypeError):
                                continue

                except Exception as e:
                    logger.warning(f"處理行 {idx} 時出錯: {str(e)}")
                    continue

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"解析 CSV 內容失敗: {str(e)}")
            return pd.DataFrame()

    def _parse_quarter_to_date(self, quarter_str: str) -> Optional[str]:
        """
        將季度字符串轉換為日期
        """
        try:
            quarter_str = str(quarter_str).strip()

            # 處理格式如 "01-03/1982"
            import re
            match = re.search(r'(\d{2})-(\d{2})/(\d{4})', quarter_str)
            if match:
                start_month = int(match.group(1).split('-')[0])
                year = int(match.group(3))
                date = datetime(year, start_month, 1)
                return date.strftime('%Y-%m-%d')

            return None

        except Exception:
            return None

    def _extract_region_from_column(self, col_name: str) -> str:
        """
        從列名中提取地區信息
        """
        col_name = str(col_name).lower()
        if 'hong kong' in col_name:
            return 'Hong Kong'
        elif 'kowloon' in col_name:
            return 'Kowloon'
        elif 'new territories' in col_name or 'nt' in col_name:
            return 'New Territories'
        else:
            return 'Other'

    def _extract_class_from_column(self, col_name: str) -> str:
        """
        從列名中提取物業類別信息
        """
        col_name = str(col_name).lower()
        if 'class a' in col_name:
            return 'Class A'
        elif 'class b' in col_name:
            return 'Class B'
        elif 'class c' in col_name:
            return 'Class C'
        elif 'class d' in col_name:
            return 'Class D'
        elif 'class e' in col_name:
            return 'Class E'
        else:
            return 'Unknown'

    async def _fetch_data_type(self, data_type: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取特定類型的物業數據
        """
        if data_type == 'transaction_volume':
            return await self._fetch_transaction_volume_data(start_date, end_date)
        elif data_type == 'price_statistics':
            return await self._fetch_price_statistics_data(start_date, end_date)
        elif data_type == 'district_analysis':
            return await self._fetch_district_analysis_data(start_date, end_date)
        elif data_type == 'property_types':
            return await self._fetch_property_types_data(start_date, end_date)
        elif data_type == 'area_distribution':
            return await self._fetch_area_distribution_data(start_date, end_date)
        else:
            return pd.DataFrame()

    async def _fetch_transaction_volume_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取交易量數據
        """
        try:
            # 嘗試訪問土地註冊處統計頁面
            stats_url = "https://www.landreg.gov.hk/en/market-statistics/"

            async with self.session.get(stats_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_transaction_volume(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取交易量數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_price_statistics_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取價格統計數據
        """
        try:
            price_url = "https://www.landreg.gov.hk/en/property-price-index/"

            async with self.session.get(price_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_price_statistics(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取價格統計數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_district_analysis_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取地區分析數據
        """
        try:
            district_url = "https://www.landreg.gov.hk/en/market-statistics/district-analysis/"

            async with self.session.get(district_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_district_analysis(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取地區分析數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_property_types_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取物業類型數據
        """
        try:
            types_url = "https://www.landreg.gov.hk/en/market-statistics/property-types/"

            async with self.session.get(types_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_property_types(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取物業類型數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_area_distribution_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取面積分布數據
        """
        try:
            area_url = "https://www.landreg.gov.hk/en/market-statistics/area-distribution/"

            async with self.session.get(area_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_area_distribution(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取面積分布數據失敗: {str(e)}")
            return pd.DataFrame()

    def _parse_html_for_transaction_volume(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的交易量數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        # 查找交易量相關表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            # 檢查是否為交易量表格
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('transaction' in header or 'volume' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            period = cells[0].get_text().strip()
                            transactions = self._parse_number(cells[1].get_text())
                            value = self._parse_number(cells[2].get_text())

                            if period and transactions is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'Transaction Volume',
                                    'value': transactions,
                                    'transaction_value': value,
                                    'unit': 'Number of Transactions',
                                    'frequency': 'Monthly',
                                    'source': 'LandRegistry_Transactions',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_price_statistics(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的價格統計數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('price' in header or 'index' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            period = cells[0].get_text().strip()
                            avg_price = self._parse_number(cells[1].get_text())
                            price_index = self._parse_number(cells[2].get_text())

                            if period and avg_price is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'Property Price',
                                    'value': avg_price,
                                    'price_index': price_index,
                                    'unit': 'HKD per sqm',
                                    'frequency': 'Monthly',
                                    'source': 'LandRegistry_Prices',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_district_analysis(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的地區分析數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('district' in header or 'region' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 4:
                        try:
                            district = cells[0].get_text().strip()
                            transactions = self._parse_number(cells[1].get_text())
                            avg_price = self._parse_number(cells[2].get_text())
                            price_change = self._parse_number(cells[3].get_text())

                            if district and transactions is not None:
                                record = {
                                    'date': datetime.now().strftime('%Y-%m'),
                                    'indicator': 'District Analysis',
                                    'district': district,
                                    'value': transactions,
                                    'avg_price': avg_price,
                                    'price_change': price_change,
                                    'unit': 'HKD',
                                    'frequency': 'Monthly',
                                    'source': 'LandRegistry_Districts',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_property_types(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的物業類型數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('type' in header or 'category' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            property_type = cells[0].get_text().strip()
                            transactions = self._parse_number(cells[1].get_text())
                            avg_price = self._parse_number(cells[2].get_text())

                            if property_type and transactions is not None:
                                record = {
                                    'date': datetime.now().strftime('%Y-%m'),
                                    'indicator': 'Property Type',
                                    'property_type': property_type,
                                    'value': transactions,
                                    'avg_price': avg_price,
                                    'unit': 'HKD per sqm',
                                    'frequency': 'Monthly',
                                    'source': 'LandRegistry_Types',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_area_distribution(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的面積分布數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('area' in header or 'size' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            area_range = cells[0].get_text().strip()
                            transactions = self._parse_number(cells[1].get_text())
                            avg_price = self._parse_number(cells[2].get_text())

                            if area_range and transactions is not None:
                                record = {
                                    'date': datetime.now().strftime('%Y-%m'),
                                    'indicator': 'Area Distribution',
                                    'area_range': area_range,
                                    'value': transactions,
                                    'avg_price': avg_price,
                                    'unit': 'HKD per sqm',
                                    'frequency': 'Monthly',
                                    'source': 'LandRegistry_Areas',
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
        獲取支持的物業指標列表
        """
        return [
            'Transaction Volume',
            'Property Price',
            'Price Index',
            'District Analysis',
            'Property Type',
            'Area Distribution',
            'Transaction Value',
            'Price Change'
        ]

    def get_supported_districts(self) -> List[str]:
        """
        獲取支持的地區列表
        """
        return self.districts

    def get_data_description(self) -> Dict[str, Any]:
        """
        獲取數據描述
        """
        return {
            'source': 'Land Registry Department, HKSAR',
            'website': 'https://www.landreg.gov.hk/',
            'data_type': 'Property Market Statistics',
            'indicators': self.get_supported_indicators(),
            'districts': self.districts,
            'update_frequency': 'Monthly',
            'data_quality': 'Official Government Statistics',
            'is_real_data': True,
            'mock_enabled': False,
            'description': 'Property market statistics from Hong Kong Land Registry including transaction volumes, prices, and district analysis.',
        }

    async def get_data_source_authentication(self) -> Dict[str, str]:
        """
        獲取數據源認證信息
        """
        return {
            "source_name": "Land Registry Department",
            "website": "https://www.landreg.gov.hk/",
            "contact_email": "info@landreg.gov.hk",
            "data_license": "Open Government License",
            "authentication_required": False,
            "rate_limits": "Unknown - check with Land Registry",
            "notes": "Public property statistics available for research purposes",
        }

    async def test_connection(self) -> bool:
        """
        測試與香港政府開放數據源的連接
        """
        try:
            # 測試 RVD 官方數據源
            test_url = "http://www.rvd.gov.hk/datagovhk/1.2Q(82-98).csv"
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    def validate_property_values(self, df: pd.DataFrame) -> List[str]:
        """
        驗證物業數據值的合理性
        """
        errors = []

        if df.empty:
            errors.append("數據框為空")
            return errors

        # 驗證價格數據
        if 'avg_price' in df.columns:
            prices = df['avg_price'].dropna()
            if len(prices) > 0:
                if prices.min() < 0:
                    errors.append("平均價格不能為負數")
                if prices.max() > 1000000:  # 100萬/平米
                    errors.append("平均價格過高，請檢查單位")
                if prices.max() < 1000:  # 1千/平米
                    errors.append("平均價格過低，請檢查數據")

        # 驗證交易量數據
        if 'value' in df.columns and df['indicator'].str.contains('Transaction', na=False).any():
            volumes = df[df['indicator'].str.contains('Transaction', na=False)]['value'].dropna()
            if len(volumes) > 0:
                if volumes.min() < 0:
                    errors.append("交易量不能為負數")
                if volumes.max() > 100000:  # 10萬筆交易
                    errors.append("交易量過高，請檢查")

        # 驗證價格變化
        if 'price_change' in df.columns:
            changes = df['price_change'].dropna()
            if len(changes) > 0:
                if changes.min() < -50:
                    errors.append("價格變化過大 (< -50%)")
                if changes.max() > 100:
                    errors.append("價格變化過大 (> 100%)")

        return errors

    async def fetch_current_property_market(self) -> pd.DataFrame:
        """
        獲取最新的物業市場數據
        """
        today = datetime.now().strftime('%Y-%m-%d')
        # 物業數據通常按月更新，所以取最近3個月
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        df = await self.fetch_real_data(start_date, today)

        if df.empty:
            # 如果沒有數據，返回空的 DataFrame
            logger.warning("未獲取到任何物業市場數據")

        return df

# 導出適配器類
__all__ = ['LandRegPropertyAdapter']
