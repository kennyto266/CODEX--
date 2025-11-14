"""
HKMA HIBOR数据爬虫
从香港金融管理局(HKMA)官网获取HIBOR利率数据

支持期限:
- HIBOR Overnight (隔夜)
- HIBOR 1M (1个月)
- HIBOR 3M (3个月)
- HIBOR 6M (6个月)
- HIBOR 12M (12个月)

数据源: https://www.hkma.gov.hk/eng/market-information/
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import pandas as pd
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class HKBusinessCalendar:
    """香港工作日日历"""

    @staticmethod
    def is_business_day(dt: date) -> bool:
        """检查是否为香港工作日"""
        # 周六周日
        if dt.weekday() >= 5:
            return False

        # 公共假期检查（简化版，实际需要完整的假期表）
        hk_public_holidays = [
            (1, 1),   # 元旦
            (4, 4),   # 清明节
            (5, 1),   # 劳动节
            (7, 1),   # 香港特别行政区成立纪念日
            (10, 1),  # 国庆日
            (12, 25), # 圣诞节
            (12, 26), # 圣诞节次日
        ]

        for month, day in hk_public_holidays:
            if dt.month == month and dt.day == day:
                return False

        return True

    @staticmethod
    def get_latest_business_day(today: Optional[date] = None) -> date:
        """获取最新工作日"""
        if today is None:
            today = date.today()

        for i in range(7):  # 检查最多7天
            check_date = today - timedelta(days=i)
            if HKBusinessCalendar.is_business_day(check_date):
                return check_date

        return today


class HKMAHibiorAdapter:
    """HKMA HIBOR数据适配器"""

    # HIBOR数据类型
    HIBOR_TYPES = {
        'overnight': {'code': 'HIBORO/N', 'name': 'HIBOR隔夜', 'days': 1},
        '1w': {'code': 'HIBOR1W', 'name': 'HIBOR1周', 'days': 7},
        '1m': {'code': 'HIBOR1M', 'name': 'HIBOR1月', 'days': 30},
        '3m': {'code': 'HIBOR3M', 'name': 'HIBOR3月', 'days': 90},
        '6m': {'code': 'HIBOR6M', 'name': 'HIBOR6月', 'days': 180},
        '12m': {'code': 'HIBOR12M', 'name': 'HIBOR12月', 'days': 365}
    }

    # HKMA数据源URL
    BASE_URL = "https://www.hkma.gov.hk"
    HIBOR_API_URL = "https://www.hkma.gov.hk/eng/market-information/interbank-rates"

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化HKMA HIBOR适配器

        Args:
            config: 配置字典，包含timeout、retries等参数
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.session = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[aiohttp.ClientResponse]:
        """
        发送HTTP请求（带重试机制）

        Args:
            url: 请求URL
            method: HTTP方法
            params: 查询参数
            headers: 请求头
            retry_count: 重试次数

        Returns:
            响应对象或None
        """
        if retry_count >= self.max_retries:
            self.logger.error(f"达到最大重试次数 ({self.max_retries}): {url}")
            return None

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers or {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            ) as response:
                if response.status == 200:
                    return response
                else:
                    self.logger.warning(
                        f"HTTP {response.status} for {url}, "
                        f"retry {retry_count + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(1 * (2 ** retry_count))
                    return await self._make_request(
                        url, method, params, headers, retry_count + 1
                    )
        except aiohttp.ClientError as e:
            self.logger.warning(
                f"请求错误 {url}: {e}, retry {retry_count + 1}/{self.max_retries}"
            )
            if retry_count < self.max_retries:
                await asyncio.sleep(1 * (2 ** retry_count))
                return await self._make_request(
                    url, method, params, headers, retry_count + 1
                )
            return None

    async def _scrape_hkma_page(self) -> Optional[pd.DataFrame]:
        """
        从HKMA网页抓取HIBOR数据

        Returns:
            包含HIBOR数据的DataFrame
        """
        self.logger.info("正在从HKMA官网抓取HIBOR数据...")

        # 方法1: 尝试XML数据源
        xml_data = await self._fetch_xml_data()
        if xml_data is not None:
            return xml_data

        # 方法2: 尝试HTML解析
        html_data = await self._fetch_html_data()
        if html_data is not None:
            return html_data

        # 方法3: 尝试CSV/Excel下载
        csv_data = await self._fetch_csv_data()
        if csv_data is not None:
            return csv_data

        self.logger.error("所有数据获取方法都失败了")
        return None

    async def _fetch_xml_data(self) -> Optional[pd.DataFrame]:
        """尝试从XML格式获取数据"""
        try:
            # 尝试HKMA可能的XML数据端点
            xml_urls = [
                "https://www.hkma.gov.hk/eng/market-information/rates/chart1.xml",
                "https://www.hkma.gov.hk/eng/market-information/interbank-rates/data/hkma_interbank_rates.xml",
            ]

            for xml_url in xml_urls:
                self.logger.debug(f"尝试获取XML数据: {xml_url}")
                response = await self._make_request(xml_url)

                if response:
                    xml_content = await response.text()
                    return self._parse_xml_data(xml_content)

            return None
        except Exception as e:
            self.logger.warning(f"XML数据获取失败: {e}")
            return None

    async def _fetch_html_data(self) -> Optional[pd.DataFrame]:
        """尝试从HTML网页解析数据"""
        try:
            response = await self._make_request(self.HIBOR_API_URL)

            if not response:
                return None

            html_content = await response.text()
            return self._parse_html_data(html_content)

        except Exception as e:
            self.logger.warning(f"HTML数据解析失败: {e}")
            return None

    async def _fetch_csv_data(self) -> Optional[pd.DataFrame]:
        """尝试从CSV/Excel文件获取数据"""
        try:
            # 尝试可能的CSV端点
            csv_urls = [
                "https://www.hkma.gov.hk/eng/market-information/interbank-rates/hkma_interbank_rates.csv",
                "https://www.hkma.gov.hk/eng/data/d2.csv",
            ]

            for csv_url in csv_urls:
                self.logger.debug(f"尝试获取CSV数据: {csv_url}")
                response = await self._make_request(csv_url)

                if response:
                    csv_content = await response.text()
                    if "<?xml" in csv_content[:100] or "rates" in csv_content.lower():
                        # 可能是HTML响应中的CSV
                        return self._parse_csv_like_data(csv_content)

            return None
        except Exception as e:
            self.logger.warning(f"CSV数据获取失败: {e}")
            return None

    def _parse_xml_data(self, xml_content: str) -> Optional[pd.DataFrame]:
        """解析XML数据"""
        try:
            root = ET.fromstring(xml_content)

            # 查找HIBOR数据
            data = []
            for element in root.iter():
                if 'hibor' in element.tag.lower() or 'rate' in element.tag.lower():
                    # 尝试解析HIBOR记录
                    record = {}
                    for child in element:
                        record[child.tag] = child.text

                    if 'date' in record and 'rate' in record:
                        data.append({
                            'date': record['date'],
                            'rate': float(record['rate']) if record['rate'] else None,
                            'type': 'HIBOR'
                        })

            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                return df.sort_values('date')

            return None
        except Exception as e:
            self.logger.error(f"XML解析错误: {e}")
            return None

    def _parse_html_data(self, html_content: str) -> Optional[pd.DataFrame]:
        """解析HTML数据"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找表格数据
            tables = soup.find_all('table')

            # 尝试不同的选择器
            data = []
            hibor_table = None

            # 查找HIBOR表格
            for table in tables:
                if 'hibor' in table.get_text().lower() or 'interbank' in table.get_text().lower():
                    hibor_table = table
                    break

            if not hibor_table:
                # 使用第一个表格
                hibor_table = tables[0] if tables else None

            if hibor_table:
                rows = hibor_table.find_all('tr')

                for row in rows[1:]:  # 跳过标题行
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 2:
                        # 尝试解析日期和利率
                        date_str = cells[0].get_text(strip=True)
                        rate_str = cells[1].get_text(strip=True)

                        if date_str and rate_str and '%' in rate_str:
                            try:
                                # 解析日期
                                date_obj = self._parse_date(date_str)

                                # 解析利率（移除%符号）
                                rate = float(rate_str.replace('%', '').strip())

                                data.append({
                                    'date': date_obj,
                                    'rate': rate,
                                    'type': 'HIBOR',
                                    'raw_date': date_str,
                                    'raw_rate': rate_str
                                })
                            except (ValueError, TypeError) as e:
                                self.logger.debug(f"跳过无效行: {date_str} -> {rate_str}: {e}")
                                continue

            if data:
                df = pd.DataFrame(data)
                df = df.sort_values('date')
                df = df.drop_duplicates(subset=['date'], keep='last')

                self.logger.info(f"成功解析 {len(df)} 条HIBOR记录")
                return df

            return None
        except Exception as e:
            self.logger.error(f"HTML解析错误: {e}")
            return None

    def _parse_csv_like_data(self, content: str) -> Optional[pd.DataFrame]:
        """解析类似CSV的文本数据"""
        try:
            lines = content.strip().split('\n')

            if len(lines) < 2:
                return None

            # 尝试识别分隔符
            if ',' in lines[0]:
                sep = ','
            elif ';' in lines[0]:
                sep = ';'
            elif '\t' in lines[0]:
                sep = '\t'
            else:
                return None

            # 解析数据
            data = []
            for line in lines[1:]:
                parts = line.split(sep)

                if len(parts) >= 2:
                    try:
                        date_obj = self._parse_date(parts[0])
                        rate = float(parts[1].replace('%', '').strip())

                        data.append({
                            'date': date_obj,
                            'rate': rate,
                            'type': 'HIBOR'
                        })
                    except (ValueError, IndexError):
                        continue

            if data:
                return pd.DataFrame(data).sort_values('date')

            return None
        except Exception as e:
            self.logger.error(f"CSV解析错误: {e}")
            return None

    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串"""
        date_str = date_str.strip()

        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d',      # 2023-12-25
            '%d/%m/%Y',      # 25/12/2023
            '%d-%m-%Y',      # 25-12-2023
            '%Y/%m/%d',      # 2023/12/25
            '%d %b %Y',      # 25 Dec 2023
            '%d %B %Y',      # 25 December 2023
            '%b %d, %Y',     # Dec 25, 2023
            '%B %d, %Y',     # December 25, 2023
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # 如果所有格式都失败，尝试pandas
        try:
            return pd.to_datetime(date_str).date()
        except (ValueError, TypeError):
            raise ValueError(f"无法解析日期: {date_str}")

    async def fetch_latest_hibor(self) -> Optional[Dict[str, Any]]:
        """
        获取最新HIBOR利率

        Returns:
            包含所有HIBOR期限的字典
        """
        self.logger.info("获取最新HIBOR利率...")

        latest_date = HKBusinessCalendar.get_latest_business_day()
        self.logger.info(f"目标日期: {latest_date}")

        # 首先尝试获取今日数据
        hibor_data = await self._get_hibor_for_date(latest_date)

        if not hibor_data or hibor_data.empty:
            # 如果今天没有数据，尝试昨天
            yesterday = latest_date - timedelta(days=1)
            self.logger.warning(f"今日无数据，尝试获取昨日数据: {yesterday}")
            hibor_data = await self._get_hibor_for_date(yesterday)

        if not hibor_data or hibor_data.empty:
            # 如果还是没有数据，尝试抓取当前页面
            self.logger.warning("静态数据无果，尝试实时抓取...")
            hibor_data = await self._scrape_hkma_page()

        if hibor_data is None or hibor_data.empty:
            self.logger.error("无法获取HIBOR数据")
            return None

        # 转换为字典格式
        result = {
            'date': latest_date.isoformat(),
            'data': {}
        }

        if not hibor_data.empty:
            latest_row = hibor_data.iloc[-1]
            result['data'] = {
                'hibor_overnight': hibor_data['rate'].iloc[-1] if len(hibor_data) > 0 else None,
                'date_recorded': latest_row['date'].isoformat() if 'date' in latest_row else None
            }

        self.logger.info(f"获取到HIBOR数据: {result}")
        return result

    async def _get_hibor_for_date(self, target_date: date) -> Optional[pd.DataFrame]:
        """
        获取指定日期的HIBOR数据

        Args:
            target_date: 目标日期

        Returns:
            DataFrame包含HIBOR数据
        """
        # 在实际实现中，这里会查询本地数据库或缓存
        # 现在我们先返回空，让抓取方法处理
        return None

    async def fetch_historical_hibor(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取历史HIBOR数据

        Args:
            start_date: 开始日期
            end_date: 结束日期（默认今天）

        Returns:
            包含历史HIBOR数据的DataFrame
        """
        if end_date is None:
            end_date = date.today()

        self.logger.info(f"获取HIBOR历史数据: {start_date} 到 {end_date}")

        all_data = []

        # 如果时间跨度较长，分段获取
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        current_date = start_date

        # 每次获取30天数据，避免请求过大
        while current_date <= end_date:
            chunk_end = min(current_date + timedelta(days=30), end_date)
            self.logger.debug(f"获取数据片段: {current_date} 到 {chunk_end}")

            # 尝试获取这段数据
            chunk_data = await self._fetch_data_range(current_date, chunk_end)

            if chunk_data is not None and not chunk_data.empty:
                all_data.append(chunk_data)
            else:
                # 如果没有数据，尝试抓取完整页面
                self.logger.warning(f"分段获取无果，尝试完整抓取...")
                page_data = await self._scrape_hkma_page()

                if page_data is not None:
                    # 过滤日期范围
                    filtered_data = page_data[
                        (page_data['date'] >= current_date) &
                        (page_data['date'] <= chunk_end)
                    ]

                    if not filtered_data.empty:
                        all_data.append(filtered_data)

            current_date = chunk_end + timedelta(days=1)

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.drop_duplicates(subset=['date'])
            result = result.sort_values('date')

            self.logger.info(f"成功获取 {len(result)} 条HIBOR记录")
            return result

        return None

    async def _fetch_data_range(
        self,
        start: date,
        end: date
    ) -> Optional[pd.DataFrame]:
        """
        获取指定日期范围的数据

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            DataFrame或None
        """
        # 实际实现中，这里会查询数据库或缓存
        return None

    async def get_hibor_for_term(
        self,
        term: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取特定期限的HIBOR数据

        Args:
            term: 期限 ('overnight', '1m', '3m', '6m', '12m')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含特定期限HIBOR数据的DataFrame
        """
        if term not in self.HIBOR_TYPES:
            raise ValueError(f"不支持的HIBOR期限: {term}")

        self.logger.info(f"获取HIBOR {term} 数据: {start_date} 到 {end_date}")

        # 获取所有HIBOR数据
        all_data = await self.fetch_historical_hibor(start_date, end_date)

        if all_data is None or all_data.empty:
            return None

        # 在实际实现中，这里会根据期限过滤数据
        # 目前的简化实现返回所有数据
        return all_data

    def get_hibor_types(self) -> Dict[str, Dict]:
        """获取支持的HIBOR类型"""
        return self.HIBOR_TYPES.copy()

    def is_business_day(self, dt: date) -> bool:
        """检查是否为工作日"""
        return HKBusinessCalendar.is_business_day(dt)


# 便捷函数
async def get_latest_hibor() -> Optional[Dict[str, Any]]:
    """获取最新HIBOR利率的便捷函数"""
    async with HKMAHibiorAdapter() as adapter:
        return await adapter.fetch_latest_hibor()


async def get_historical_hibor(
    start_date: date,
    end_date: Optional[date] = None
) -> Optional[pd.DataFrame]:
    """获取历史HIBOR数据的便捷函数"""
    async with HKMAHibiorAdapter() as adapter:
        return await adapter.fetch_historical_hibor(start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    async def test():
        async with HKMAHibiorAdapter() as adapter:
            # 获取最新HIBOR
            latest = await adapter.fetch_latest_hibor()
            print("最新HIBOR:", json.dumps(latest, indent=2, default=str))

            # 获取历史数据（最近7天）
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            historical = await adapter.fetch_historical_hibor(start_date, end_date)

            if historical is not None:
                print(f"\n历史数据 ({len(historical)} 条):")
                print(historical.to_string())

    asyncio.run(test())
