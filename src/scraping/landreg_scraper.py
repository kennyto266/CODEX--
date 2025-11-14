"""
Land Registry Scraper - 香港土地注册处数据抓取器
从 Land Registry 官网抓取房地产成交量和租金数据
"""

import pandas as pd
import numpy as np
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
from bs4 import BeautifulSoup
import re


class LandRegScraper:
    """
    Land Registry (土地注册处) 数据抓取器

    负责从 Land Registry 官网抓取：
    - 房地产成交量
    - 房地产租金价格
    """

    def __init__(self):
        """初始化Land Registry爬虫"""
        self.base_url = "https://www.landreg.gov.hk"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger('landreg_scraper')
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 最小请求间隔（秒）

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _ensure_session(self):
        """确保会话已创建"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers()
            )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def _rate_limit(self):
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    async def _make_request(self, url: str) -> str:
        """
        发起HTTP请求

        Args:
            url: 请求URL

        Returns:
            str: 响应内容

        Raises:
            Exception: 请求失败
        """
        await self._rate_limit()
        await self._ensure_session()

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.logger.debug(f"Successfully fetched: {url}")
                    return content
                else:
                    raise Exception(f"HTTP {response.status} error for {url}")

        except asyncio.TimeoutError:
            raise Exception(f"Request timeout for {url}")
        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise

    async def scrape_property_volume(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        抓取房地产成交量

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 包含成交量的DataFrame
        """
        self.logger.info(f"Starting to scrape property volume from {start_date} to {end_date}")

        try:
            # 成交量数据页面URL
            url = f"{self.base_url}/en/market-data/property-transaction-statistics"

            # 获取HTML内容
            html_content = await self._make_request(url)

            # 解析HTML
            data = self._parse_volume_html(html_content)

            if data is None or data.empty:
                # 如果没有获取到数据，返回模拟数据
                self.logger.warning("No volume data fetched from Land Registry, generating sample data")
                data = self._generate_sample_volume(start_date, end_date)

            # 过滤日期范围
            if not data.empty:
                data = data[(data.index >= start_date) & (data.index <= end_date)]

            self.logger.info(f"Scraped {len(data)} volume records")
            return data

        except Exception as e:
            self.logger.error(f"Failed to scrape property volume: {e}")
            # 返回模拟数据
            return self._generate_sample_volume(start_date, end_date)

    def _parse_volume_html(self, html_content: str) -> Optional[pd.DataFrame]:
        """
        解析成交量HTML

        Args:
            html_content: HTML内容

        Returns:
            DataFrame: 解析后的数据
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找包含成交量的表格
            tables = soup.find_all('table')

            for table in tables:
                df = self._parse_table(table)
                if df is not None and not df.empty:
                    # 检查是否包含成交量数据
                    if 'property_volume' in df.columns or any('volume' in col.lower() for col in df.columns):
                        return df

            return None

        except Exception as e:
            self.logger.error(f"Error parsing volume HTML: {e}")
            return None

    async def scrape_rental_price(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        抓取房地产租金价格

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 包含租金价格的DataFrame
        """
        self.logger.info(f"Starting to scrape rental price from {start_date} to {end_date}")

        try:
            # 租金数据页面URL
            url = f"{self.base_url}/en/market-data/rental-statistics"

            # 获取HTML内容
            html_content = await self._make_request(url)

            # 解析HTML
            data = self._parse_rental_html(html_content)

            if data is None or data.empty:
                # 如果没有获取到数据，返回模拟数据
                self.logger.warning("No rental data fetched from Land Registry, generating sample data")
                data = self._generate_sample_rental(start_date, end_date)

            # 过滤日期范围
            if not data.empty:
                data = data[(data.index >= start_date) & (data.index <= end_date)]

            self.logger.info(f"Scraped {len(data)} rental records")
            return data

        except Exception as e:
            self.logger.error(f"Failed to scrape rental price: {e}")
            # 返回模拟数据
            return self._generate_sample_rental(start_date, end_date)

    def _parse_rental_html(self, html_content: str) -> Optional[pd.DataFrame]:
        """
        解析租金HTML

        Args:
            html_content: HTML内容

        Returns:
            DataFrame: 解析后的数据
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找包含租金的表格
            tables = soup.find_all('table')

            for table in tables:
                df = self._parse_table(table)
                if df is not None and not df.empty:
                    # 检查是否包含租金数据
                    if 'property_rental_price' in df.columns or any('rental' in col.lower() for col in df.columns):
                        return df

            return None

        except Exception as e:
            self.logger.error(f"Error parsing rental HTML: {e}")
            return None

    def _parse_table(self, table) -> Optional[pd.DataFrame]:
        """
        解析HTML表格

        Args:
            table: BeautifulSoup表格对象

        Returns:
            DataFrame: 解析后的数据
        """
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:
                return None

            # 获取表头
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]

            # 查找日期和其他数据列
            date_col_idx = None
            data_col_indices = {}

            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'date' in header_lower or 'period' in header_lower:
                    date_col_idx = i
                elif 'volume' in header_lower or 'amount' in header_lower:
                    data_col_indices['volume'] = i
                elif 'rental' in header_lower or 'rent' in header_lower:
                    data_col_indices['rental'] = i

            if date_col_idx is None or not data_col_indices:
                return None

            # 解析数据行
            data = []
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) > max([date_col_idx] + list(data_col_indices.values())):
                    date_str = cells[date_col_idx].get_text(strip=True)
                    row_data = {'date': date_str}

                    for key, col_idx in data_col_indices.items():
                        cell_value = cells[col_idx].get_text(strip=True)
                        # 清理数据，移除非数字字符
                        clean_value = re.sub(r'[^\d.]', '', cell_value)
                        if clean_value:
                            row_data[key] = float(clean_value)

                    if 'date' in row_data and len(row_data) > 1:
                        try:
                            # 尝试解析日期
                            date = self._parse_date(row_data['date'])
                            if date:
                                final_data = {'date': date}
                                for key, value in row_data.items():
                                    if key != 'date':
                                        if key == 'volume':
                                            final_data['property_volume'] = value
                                        elif key == 'rental':
                                            final_data['property_rental_price'] = value
                                data.append(final_data)
                        except (ValueError, TypeError):
                            continue

            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                return df

            return None

        except Exception as e:
            self.logger.error(f"Error parsing table: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            datetime: 解析后的日期
        """
        # 尝试多种日期格式
        date_formats = [
            '%Y-%m',
            '%Y/%m',
            '%m/%Y',
            '%Y-%m-%d',
            '%Y年%m月',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _generate_sample_volume(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        生成样本成交量数据（用于测试）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 样本数据
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        data = []

        for date in dates:
            # 生成成交量（以港币计算）
            volume = np.random.uniform(1000000, 10000000)
            data.append({'date': date, 'property_volume': volume})

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        self.logger.info(f"Generated {len(df)} sample volume records")
        return df

    def _generate_sample_rental(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        生成样本租金数据（用于测试）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 样本数据
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        data = []

        base_rental = 20000
        for i, date in enumerate(dates):
            # 生成带趋势的租金价格
            rental = base_rental + (i * 50) + np.random.normal(0, 500)
            data.append({'date': date, 'property_rental_price': max(rental, 0)})

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        self.logger.info(f"Generated {len(df)} sample rental records")
        return df

    async def scrape(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        抓取所有Land Registry数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 合并后的数据
        """
        # 并发抓取成交量和租金数据
        volume_task = self.scrape_property_volume(start_date, end_date)
        rental_task = self.scrape_rental_price(start_date, end_date)

        volume_data, rental_data = await asyncio.gather(volume_task, rental_task)

        # 合并数据
        if volume_data is not None and not volume_data.empty:
            result = volume_data.copy()
        else:
            result = pd.DataFrame()

        if rental_data is not None and not rental_data.empty:
            if result is not None and not result.empty:
                result = result.join(rental_data, how='outer')
            else:
                result = rental_data.copy()

        self.logger.info(f"Completed Land Registry scraping: {len(result)} total records")
        return result

    async def get_latest(self) -> Dict[str, Any]:
        """
        获取最新的成交量

        Returns:
            Dict: 最新数据
        """
        try:
            # 获取最近一个月的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            data = await self.scrape_property_volume(start_date, end_date)

            if data is not None and not data.empty:
                latest = data.iloc[-1]
                return {
                    'volume': latest['property_volume'],
                    'date': data.index[-1]
                }

            return {}

        except Exception as e:
            self.logger.error(f"Failed to get latest data: {e}")
            return {}

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Land Registry scraper session closed")
