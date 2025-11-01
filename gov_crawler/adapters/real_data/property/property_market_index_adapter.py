#!/usr/bin/env python3
"""
物業市場指數適配器 - Property Market Index Adapter
從多個來源獲取香港物業市場指數和統計數據
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

class PropertyMarketIndexAdapter(RealDataAdapter):
    """
    物業市場指數適配器
    從多個來源獲取物業市場指數和統計數據

    數據來源:
    - 中原城市領先指數 (CCL)
    - 差餉物業估價署 (RVD) 指數
    - 市場統計數據
    """

    def __init__(self):
        super().__init__(
            name="Property Market Index",
            source_url="https://www.centadata.com/"
        )
        self.log_real_data_warning()

        # 物業指數數據端點
        self.data_endpoints = {
            "ccl": "https://www.centadata.com/CCL_History.aspx",
            "rvd_index": "https://www.rvd.gov.hk/",
            "market_stats": "https://www.property.hk/",
            "price_trends": "https://www.prices.com.hk/",
        }

    @validate_no_mock_data
    async def fetch_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取真實物業市場指數數據
        """
        logger.info("正在獲取真實物業市場指數數據...")

        records = []

        try:
            # 嘗試獲取不同類型的指數數據
            index_types = [
                'ccl_index',
                'rvd_index',
                'price_trends',
                'market_statistics',
                'rental_index'
            ]

            for index_type in index_types:
                try:
                    df = await self._fetch_index_data(index_type, start_date, end_date)
                    if df is not None and not df.empty:
                        records.extend(df.to_dict('records'))
                    logger.info(f"成功獲取 {index_type} 數據: {len(df)} 條記錄")
                except Exception as e:
                    logger.warning(f"獲取 {index_type} 數據失敗: {str(e)}")
                    continue

            if not records:
                raise ValueError("無法獲取任何真實物業指數數據")

            df = pd.DataFrame(records)

            # 確保所有記錄都標記為真實數據
            df['is_real'] = True
            df['is_mock'] = False

            # 添加數據來源標記
            df['source'] = 'PropertyIndex_Official'

            return df

        except Exception as e:
            logger.error(f"獲取物業市場指數數據失敗: {str(e)}")
            raise

    async def _fetch_index_data(self, index_type: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取特定類型的指數數據
        """
        if index_type == 'ccl_index':
            return await self._fetch_ccl_index_data(start_date, end_date)
        elif index_type == 'rvd_index':
            return await self._fetch_rvd_index_data(start_date, end_date)
        elif index_type == 'price_trends':
            return await self._fetch_price_trends_data(start_date, end_date)
        elif index_type == 'market_statistics':
            return await self._fetch_market_statistics_data(start_date, end_date)
        elif index_type == 'rental_index':
            return await self._fetch_rental_index_data(start_date, end_date)
        else:
            return pd.DataFrame()

    async def _fetch_ccl_index_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取中原城市領先指數 (CCL)
        """
        try:
            ccl_url = "https://www.centadata.com/CCL_History.aspx"
            async with self.session.get(ccl_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_ccl(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取 CCL 指數失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_rvd_index_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取差餉物業估價署指數
        """
        try:
            rvd_url = "https://www.rvd.gov.hk/en/property-statistics/"
            async with self.session.get(rvd_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_rvd(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取 RVD 指數失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_price_trends_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取價格趨勢數據
        """
        try:
            trends_url = "https://www.prices.com.hk/"
            async with self.session.get(trends_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_trends(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取價格趨勢數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_market_statistics_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取市場統計數據
        """
        try:
            stats_url = "https://www.property.hk/"
            async with self.session.get(stats_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_market_stats(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取市場統計數據失敗: {str(e)}")
            return pd.DataFrame()

    async def _fetch_rental_index_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        獲取租金指數數據
        """
        try:
            rental_url = "https://www.centadata.com/Rental_History.aspx"
            async with self.session.get(rental_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html_for_rental(html)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"獲取租金指數失敗: {str(e)}")
            return pd.DataFrame()

    def _parse_html_for_ccl(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的 CCL 指數數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        # 查找 CCL 指數表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('ccl' in header or 'centaline' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            date_str = cells[0].get_text().strip()
                            ccl_value = self._parse_number(cells[1].get_text())
                            change = self._parse_number(cells[2].get_text())

                            if date_str and ccl_value is not None:
                                record = {
                                    'date': date_str,
                                    'indicator': 'CCL Index',
                                    'value': ccl_value,
                                    'change': change,
                                    'unit': 'Index',
                                    'frequency': 'Weekly',
                                    'source': 'Centaline_CCL',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_rvd(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的 RVD 指數數據
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
                            index_value = self._parse_number(cells[1].get_text())
                            change = self._parse_number(cells[2].get_text())

                            if period and index_value is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'RVD Price Index',
                                    'value': index_value,
                                    'change': change,
                                    'unit': 'Index (Base Year: 1999)',
                                    'frequency': 'Monthly',
                                    'source': 'RVD_Official',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_trends(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的價格趨勢數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('trend' in header or 'price' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            month = cells[0].get_text().strip()
                            avg_price = self._parse_number(cells[1].get_text())
                            transactions = self._parse_number(cells[2].get_text())

                            if month and avg_price is not None:
                                record = {
                                    'date': month,
                                    'indicator': 'Market Price Trends',
                                    'value': avg_price,
                                    'transactions': transactions,
                                    'unit': 'HKD per sqm',
                                    'frequency': 'Monthly',
                                    'source': 'Property_Prices_HK',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_market_stats(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的市場統計數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('statistic' in header or 'market' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            statistic = cells[0].get_text().strip()
                            value = self._parse_number(cells[1].get_text())
                            period = cells[2].get_text().strip()

                            if statistic and value is not None:
                                record = {
                                    'date': period,
                                    'indicator': 'Market Statistics',
                                    'statistic_name': statistic,
                                    'value': value,
                                    'unit': 'Various',
                                    'frequency': 'Monthly',
                                    'source': 'Property_HK',
                                    'is_real': True,
                                    'is_mock': False,
                                }
                                records.append(record)
                        except Exception:
                            continue
                break

        return pd.DataFrame(records)

    def _parse_html_for_rental(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 中的租金指數數據
        """
        soup = BeautifulSoup(html, 'html.parser')
        records = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('rental' in header or 'rent' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 3:
                        try:
                            date_str = cells[0].get_text().strip()
                            rental_index = self._parse_number(cells[1].get_text())
                            change = self._parse_number(cells[2].get_text())

                            if date_str and rental_index is not None:
                                record = {
                                    'date': date_str,
                                    'indicator': 'Rental Index',
                                    'value': rental_index,
                                    'change': change,
                                    'unit': 'Index',
                                    'frequency': 'Weekly',
                                    'source': 'Centaline_Rental',
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
        獲取支持的指數指標列表
        """
        return [
            'CCL Index (中原城市領先指數)',
            'RVD Price Index (差餉物業估價署指數)',
            'Rental Index (租金指數)',
            'Market Price Trends (市場價格趨勢)',
            'Market Statistics (市場統計)'
        ]

    def get_data_description(self) -> Dict[str, Any]:
        """
        獲取數據描述
        """
        return {
            'source': 'Property Market Index Providers',
            'sources': [
                'Centaline Property Agency (中原地產)',
                'Rating and Valuation Department (差餉物業估價署)',
                'Property.HK',
                'Prices.com.hk'
            ],
            'data_type': 'Property Market Indices',
            'indicators': self.get_supported_indicators(),
            'update_frequency': 'Weekly/Monthly',
            'data_quality': 'Professional Market Data',
            'is_real_data': True,
            'mock_enabled': False,
            'description': 'Comprehensive property market indices from multiple professional providers in Hong Kong.',
        }

    async def get_data_source_authentication(self) -> Dict[str, str]:
        """
        獲取數據源認證信息
        """
        return {
            "sources": [
                "Centaline Property Agency",
                "Rating and Valuation Department",
                "Property.HK",
                "Prices.com.hk"
            ],
            "data_license": "Public Market Data",
            "authentication_required": False,
            "rate_limits": "Unknown - check with providers",
            "notes": "Market data is publicly available but may require scraping or API access",
        }

    async def test_connection(self) -> bool:
        """
        測試與數據源的連接
        """
        try:
            async with self.session.get(self.source_url) as response:
                return response.status == 200
        except Exception:
            return False

    def validate_index_values(self, df: pd.DataFrame) -> List[str]:
        """
        驗證指數數據值的合理性
        """
        errors = []

        if df.empty:
            errors.append("數據框為空")
            return errors

        # 驗證指數值範圍
        if 'value' in df.columns:
            values = df['value'].dropna()
            if len(values) > 0:
                if values.min() < 0:
                    errors.append("指數值不能為負數")

                # 檢查是否為合理的指數範圍
                if values.max() > 10000:  # 指數通常不會超過 10000
                    errors.append(f"指數值過高: {values.max()}")

        # 驗證變化率
        if 'change' in df.columns:
            changes = df['change'].dropna()
            if len(changes) > 0:
                if changes.min() < -30:
                    errors.append("價格變化過大 (< -30%)")
                if changes.max() > 30:
                    errors.append("價格變化過大 (> 30%)")

        # 驗證 CCL 指數合理性
        ccl_data = df[df['indicator'].str.contains('CCL', na=False)]
        if not ccl_data.empty:
            ccl_values = ccl_data['value'].dropna()
            if len(ccl_values) > 0:
                # CCL 指數合理範圍通常在 50-200 之間
                if ccl_values.min() < 30 or ccl_values.max() > 300:
                    errors.append(f"CCL 指數值異常: {ccl_values.min()} - {ccl_values.max()}")

        return errors

    async def fetch_current_indices(self) -> pd.DataFrame:
        """
        獲取最新的物業指數數據
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        df = await self.fetch_real_data(start_date, end_date)

        if df.empty:
            logger.warning("未獲取到任何物業指數數據")

        return df

# 導出適配器類
__all__ = ['PropertyMarketIndexAdapter']
