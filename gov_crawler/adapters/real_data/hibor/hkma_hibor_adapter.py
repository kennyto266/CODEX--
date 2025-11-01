#!/usr/bin/env python3
"""
HKMA HIBOR 適配器 - 真實數據源
從香港金融管理局獲取真實的 HIBOR 利率數據
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

class HKMAHiborAdapter(RealDataAdapter):
    """
    HKMA HIBOR 適配器
    從香港金融管理局獲取真實的銀行同業拆息數據

    支持的期限:
    - 隔夜 (Overnight)
    - 1 個月
    - 3 個月
    - 6 個月
    - 12 個月
    """

    def __init__(self):
        super().__init__(
            name="HKMA HIBOR",
            source_url="https://www.hkma.gov.hk/eng/market-info/"
        )
        self.log_real_data_warning()
        # HKMA HIBOR 數據的 API 端點（需要從官網獲取實際可用端點）
        self.api_endpoints = {
            "hibor_table": "https://www.hkma.gov.hk/eng/market-info/",
            "daily_rates": "https://www.hkma.gov.hk/eng/market-info/market-data/",
        }

    @validate_no_mock_data
    async def fetch_real_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從 HKMA 獲取真實 HIBOR 數據
        """
        logger.info("正在從 HKMA 獲取真實 HIBOR 數據...")

        try:
            # 方法 1: 嘗試從 HKMA API 獲取數據
            df = await self._fetch_from_api(start_date, end_date)
            if df is not None and not df.empty:
                return df

            # 方法 2: 如果 API 不可用，從網頁抓取（僅作為備用）
            logger.warning("API 不可用，嘗試從網頁抓取...")
            df = await self._scrape_from_webpage(start_date, end_date)
            if df is not None and not df.empty:
                return df

            raise ValueError("無法從 HKMA 獲取真實數據")

        except Exception as e:
            logger.error(f"獲取 HKMA HIBOR 數據失敗: {str(e)}")
            raise

    async def _fetch_from_api(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        嘗試從 HKMA API 獲取數據
        """
        # 這裡需要實際的 HKMA API 端點
        # 由於 HKMA 可能沒有公開的 REST API，我們需要根據實際情況調整

        possible_endpoints = [
            "https://api.hkma.gov.hk/rates/hibor",
            "https://www.hkma.gov.hk/api/market-data/hibor",
            "https://data.hkma.gov.hk/api/hibor",
        ]

        for endpoint in possible_endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')

                        if 'application/json' in content_type:
                            data = await response.json()
                            return self._parse_json_data(data)

                        elif 'text/html' in content_type:
                            # 可能是網頁而非 API
                            html = await response.text()
                            return self._parse_html_data(html)

            except Exception as e:
                logger.debug(f"端點 {endpoint} 不可用: {str(e)}")
                continue

        return None

    async def _scrape_from_webpage(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        從 HKMA 網頁抓取 HIBOR 數據
        """
        try:
            # 獲取最新 HIBOR 數據頁面
            async with self.session.get(self.source_url) as response:
                if response.status != 200:
                    logger.error(f"無法訪問 HKMA 網頁: {response.status}")
                    return None

                html = await response.text()
                return self._parse_html_data(html)

        except Exception as e:
            logger.error(f"抓取網頁數據失敗: {str(e)}")
            return None

    def _parse_json_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        解析 JSON 格式的 HIBOR 數據
        """
        records = []

        # 根據實際 API 響應格式調整解析邏輯
        if isinstance(data, dict):
            if 'hibor' in data:
                for item in data['hibor']:
                    record = {
                        'date': item.get('date'),
                        'overnight': item.get('overnight'),
                        '1m': item.get('1m'),
                        '3m': item.get('3m'),
                        '6m': item.get('6m'),
                        '12m': item.get('12m'),
                        'source': 'HKMA_API',
                        'is_real': True,
                        'is_mock': False,  # 明確標記
                    }
                    records.append(record)

        if records:
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            return df

        return pd.DataFrame()

    def _parse_html_data(self, html: str) -> pd.DataFrame:
        """
        解析 HTML 格式的 HIBOR 數據
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 查找 HIBOR 表格
        # 注意：這是示例解析邏輯，實際需要根據 HKMA 網頁結構調整

        records = []

        # 嘗試查找 HIBOR 相關表格
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            # 檢查是否為 HIBOR 表格
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            if any('overnight' in header or 'hibor' in header for header in headers):
                for row in rows[1:]:
                    cells = row.find_all(['td'])
                    if len(cells) >= 6:  # 至少需要日期 + 5 個期限
                        try:
                            date_str = cells[0].get_text().strip()
                            overnight = self._parse_rate(cells[1].get_text())
                            rate_1m = self._parse_rate(cells[2].get_text())
                            rate_3m = self._parse_rate(cells[3].get_text())
                            rate_6m = self._parse_rate(cells[4].get_text())
                            rate_12m = self._parse_rate(cells[5].get_text())

                            if date_str and overnight is not None:
                                record = {
                                    'date': date_str,
                                    'overnight': overnight,
                                    '1m': rate_1m,
                                    '3m': rate_3m,
                                    '6m': rate_6m,
                                    '12m': rate_12m,
                                    'source': 'HKMA_Webpage',
                                    'is_real': True,
                                    'is_mock': False,  # 明確標記
                                }
                                records.append(record)
                        except Exception as e:
                            logger.debug(f"解析行數據失敗: {str(e)}")
                            continue

                break  # 找到 HIBOR 表格後退出

        if records:
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # 刪除無效日期的行
            df = df.dropna(subset=['date'])
            return df

        return pd.DataFrame()

    def _parse_rate(self, rate_str: str) -> Optional[float]:
        """
        解析利率字符串為浮點數
        """
        if not rate_str:
            return None

        # 移除百分號和其他非數字字符
        cleaned = re.sub(r'[^\d.-]', '', rate_str)
        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    async def fetch_current_hibor(self) -> pd.DataFrame:
        """
        獲取最新的 HIBOR 數據（單日）
        """
        today = datetime.now().strftime('%Y-%m-%d')
        df = await self.fetch_real_data(today, today)

        if df.empty:
            # 如果今天沒有數據，嘗試獲取最近一個工作日
            for i in range(1, 7):  # 最多回溯 6 天
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                df = await self.fetch_real_data(date, date)
                if not df.empty:
                    break

        return df

    def get_supported_maturities(self) -> List[str]:
        """
        獲取支持的期限列表
        """
        return ['overnight', '1m', '3m', '6m', '12m']

    def get_data_description(self) -> Dict[str, Any]:
        """
        獲取數據描述
        """
        return {
            'source': 'Hong Kong Monetary Authority (HKMA)',
            'data_type': 'HIBOR (Hong Kong Interbank Offered Rate)',
            'currency': 'HKD',
            'unit': 'Percentage (%)',
            'update_frequency': 'Daily (Business Days)',
            'supported_maturities': self.get_supported_maturities(),
            'data_quality': 'Official Government Data',
            'is_real_data': True,
            'mock_enabled': False,
            'description': 'The HKD Hong Kong Interbank Offered Rate (HIBOR) is the rate at which banks lend to each other in Hong Kong dollars.',
        }

    def validate_hibor_values(self, df: pd.DataFrame) -> List[str]:
        """
        驗證 HIBOR 數值的合理性
        """
        errors = []

        if df.empty:
            errors.append("數據框為空")
            return errors

        # 檢查數值範圍
        maturity_cols = ['overnight', '1m', '3m', '6m', '12m']
        for col in maturity_cols:
            if col in df.columns:
                rates = df[col].dropna()
                if len(rates) > 0:
                    min_rate = rates.min()
                    max_rate = rates.max()

                    # HIBOR 合理範圍通常在 -0.5% 到 10% 之間
                    if min_rate < -1.0:
                        errors.append(f"{col} 最小值 {min_rate}% 低於合理範圍")
                    if max_rate > 15.0:
                        errors.append(f"{col} 最大值 {max_rate}% 高於合理範圍")

        # 檢查期限結構（通常長期利率 >= 短期利率）
        if 'overnight' in df.columns and '12m' in df.columns:
            overnight = df['overnight'].dropna()
            rate_12m = df['12m'].dropna()
            if len(overnight) > 0 and len(rate_12m) > 0:
                # 大部分時間長期利率應該高於短期利率
                inverted_count = (overnight.iloc[-30:] > rate_12m.iloc[-30:]).sum()
                if inverted_count > len(overnight.iloc[-30:]) * 0.3:
                    errors.append(f"利率倒掛比例過高 ({inverted_count}/{len(overnight.iloc[-30:])})")

        return errors

    async def get_data_source_authentication(self) -> Dict[str, str]:
        """
        獲取數據源認證信息
        """
        return {
            "source_name": "Hong Kong Monetary Authority",
            "website": "https://www.hkma.gov.hk/",
            "api_documentation": "https://www.hkma.gov.hk/eng/",
            "contact_email": "info@hkma.gov.hk",
            "data_license": "Open Government License",
            "authentication_required": False,
            "rate_limits": "Unknown - check with HKMA",
        }

    async def test_connection(self) -> bool:
        """
        測試與 HKMA 的連接
        """
        try:
            async with self.session.get(self.source_url) as response:
                return response.status == 200
        except Exception:
            return False

# 確保只使用真實數據的裝飾器
def require_real_data(func):
    """裝飾器：確保函數只處理真實數據"""
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if isinstance(result, pd.DataFrame):
            if 'is_mock' in result.columns and result['is_mock'].any():
                raise ValueError(f"{func.__name__}: 禁止使用 mock 數據！")
        return result
    return wrapper

# 導出適配器類
__all__ = ['HKMAHiborAdapter']
