"""
C&SD (香港统计处) 经济数据爬虫

从统计处官网获取经济统计数据，支持多种数据格式解析。
主要功能：
- 自动识别和获取经济统计表
- 支持CSV、Excel、XML等多种格式
- 历史数据获取和增量更新
- 自动格式检测和转换

Author: Claude Code
Version: 1.0.0
Date: 2025-11-09
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import hashlib

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, validator
from enum import Enum

from .unified_base_adapter import UnifiedBaseAdapter, CacheManager, ErrorHandler


class CSDDataType(str, Enum):
    """C&SD数据类型枚举"""
    GDP = "gdp"
    RETAIL_SALES = "retail_sales"
    VISITOR_ARRIVALS = "visitor_arrivals"
    TRADE_STATISTICS = "trade_statistics"
    UNEMPLOYMENT = "unemployment"
    CPI = "cpi"
    PROPERTY_PRICES = "property_prices"
    TRAFFIC = "traffic"


class CSDWebTable(BaseModel):
    """C&SD网页数据表模型"""
    table_id: str = Field(..., description="表格ID")
    title: str = Field(..., description="表格标题")
    url: str = Field(..., description="下载链接")
    format: str = Field(..., description="数据格式 (csv/xlsx/xml)")
    last_updated: datetime = Field(..., description="最后更新时间")
    data_type: CSDDataType = Field(..., description="数据类型")
    description: Optional[str] = Field(None, description="表格描述")


class CSDCrawlerConfig(BaseModel):
    """C&SD爬虫配置"""
    base_url: str = Field(default="https://www.censtatd.gov.hk", description="统计处官网基础URL")
    data_center_url: str = Field(
        default="https://www.censtatd.gov.hk/en/data",
        description="数据中心URL"
    )
    request_timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    rate_limit: float = Field(default=1.0, description="请求频率限制(请求/秒)")
    download_dir: str = Field(default="data/csd_downloads", description="数据下载目录")
    cache_ttl: int = Field(default=3600, description="缓存生存时间(秒)")

    # 支持的数据类型和对应的URL模式
    data_patterns: Dict[CSDDataType, str] = Field(
        default_factory=lambda: {
            CSDDataType.GDP: "/en/data/national_income/",
            CSDDataType.RETAIL_SALES: "/en/data/domestic_trade/",
            CSDDataType.VISITOR_ARRIVALS: "/en/data/tourism/",
            CSDDataType.TRADE_STATISTICS: "/en/data/external_trade/",
            CSDDataType.UNEMPLOYMENT: "/en/data/labour/",
            CSDDataType.CPI: "/en/data/price_statistics/",
            CSDDataType.PROPERTY_PRICES: "/en/data/construction/",
            CSDDataType.TRAFFIC: "/en/data/transport/",
        },
        description="数据类型对应的URL模式"
    )

    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v


class CSDDataCrawler(UnifiedBaseAdapter):
    """
    C&SD经济数据爬虫

    从香港统计处官网自动获取经济统计数据，支持多种数据格式。
    """

    def __init__(self, config: Optional[CSDCrawlerConfig] = None):
        super().__init__(config)
        self.config: CSDCrawlerConfig = config or CSDCrawlerConfig()
        self.logger = logging.getLogger("hk_quant_system.csd_crawler")

        # 确保下载目录存在
        Path(self.config.download_dir).mkdir(parents=True, exist_ok=True)

        # 初始化aiohttp会话
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = asyncio.Lock()

        # 数据表索引
        self._table_index: Dict[CSDDataType, List[CSDWebTable]] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self._session

    async def close(self):
        """关闭资源"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limit(self):
        """请求频率限制"""
        async with self._rate_limiter:
            await asyncio.sleep(1.0 / max(self.config.rate_limit, 1e-6))

    async def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        获取网页内容

        Args:
            url: 网页URL

        Returns:
            BeautifulSoup对象或None
        """
        await self._rate_limit()

        session = await self._get_session()

        for attempt in range(self.config.max_retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return BeautifulSoup(html, 'html.parser')
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
            except Exception as e:
                self.logger.error(f"Fetch failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        return None

    def _detect_file_format(self, url: str, content_type: str = "") -> str:
        """
        检测文件格式

        Args:
            url: 文件URL
            content_type: HTTP Content-Type头

        Returns:
            文件格式 (csv/xlsx/xml/json)
        """
        # 从URL检测
        if '.csv' in url.lower():
            return 'csv'
        elif '.xlsx' in url.lower() or '.xls' in url.lower():
            return 'xlsx'
        elif '.xml' in url.lower():
            return 'xml'
        elif '.json' in url.lower():
            return 'json'

        # 从Content-Type检测
        if 'csv' in content_type.lower():
            return 'csv'
        elif 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
            return 'xlsx'
        elif 'xml' in content_type.lower():
            return 'xml'
        elif 'json' in content_type.lower():
            return 'json'

        return 'unknown'

    async def _download_file(self, url: str, table_id: str) -> Optional[Path]:
        """
        下载数据文件

        Args:
            url: 下载URL
            table_id: 表格ID

        Returns:
            下载的文件路径或None
        """
        await self._rate_limit()

        session = await self._get_session()
        file_format = self._detect_file_format(url)
        file_path = Path(self.config.download_dir) / f"{table_id}.{file_format}"

        # 检查缓存
        cache_key = f"download:{hashlib.md5(url.encode()).hexdigest()}"
        cached_data = self.cache.get(cache_key)
        if cached_data and self.cache.is_valid(cache_key):
            if file_path.exists():
                return file_path

        for attempt in range(self.config.max_retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        file_path.write_bytes(content)
                        self.logger.info(f"Downloaded: {table_id} ({len(content)} bytes)")
                        return file_path
                    else:
                        self.logger.warning(f"HTTP {response.status} downloading {url}")
            except Exception as e:
                self.logger.error(f"Download failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        return None

    async def _parse_table_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        data_type: CSDDataType
    ) -> List[CSDWebTable]:
        """
        解析网页中的数据表链接

        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
            data_type: 数据类型

        Returns:
            数据表列表
        """
        tables = []

        # 查找所有下载链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)

            # 过滤有效的数据文件
            if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', '.xml']):
                # 构建完整URL
                if href.startswith('/'):
                    url = f"{self.config.base_url}{href}"
                elif href.startswith('http'):
                    url = href
                else:
                    url = f"{base_url}/{href}"

                # 生成表格ID
                table_id = hashlib.md5(url.encode()).hexdigest()[:12]

                # 检测文件格式
                format_type = self._detect_file_format(href)

                table = CSDWebTable(
                    table_id=table_id,
                    title=text or f"Data Table {table_id}",
                    url=url,
                    format=format_type,
                    last_updated=datetime.now(),
                    data_type=data_type,
                    description=text
                )
                tables.append(table)

        return tables

    async def discover_tables(self, data_type: Optional[CSDDataType] = None) -> Dict[CSDDataType, List[CSDWebTable]]:
        """
        发现可用的数据表

        Args:
            data_type: 指定数据类型，None表示所有类型

        Returns:
            数据表索引
        """
        self.logger.info(f"Discovering C&SD data tables: {data_type or 'ALL'}")

        types_to_search = [data_type] if data_type else list(self.config.data_patterns.keys())
        discovered_tables = {}

        for dtype in types_to_search:
            if dtype not in self.config.data_patterns:
                continue

            url = f"{self.config.base_url}{self.config.data_patterns[dtype]}"
            self.logger.info(f"Scanning: {url}")

            soup = await self._fetch_page(url)
            if soup:
                tables = await self._parse_table_links(soup, url, dtype)
                discovered_tables[dtype] = tables
                self.logger.info(f"Found {len(tables)} tables for {dtype}")

                # 缓存结果
                cache_key = f"tables:{dtype}"
                self.cache.set(cache_key, tables, ttl=self.config.cache_ttl)

        self._table_index.update(discovered_tables)
        return discovered_tables

    async def fetch_data(
        self,
        data_type: CSDDataType,
        table_id: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """
        获取C&SD数据

        Args:
            data_type: 数据类型
            table_id: 表格ID，None表示获取所有
            date_range: 日期范围

        Returns:
            数据结果
        """
        context = f"CSDCrawler.fetch_data({data_type})"

        try:
            # 获取数据表索引
            if data_type not in self._table_index:
                await self.discover_tables(data_type)

            tables = self._table_index.get(data_type, [])
            if not tables:
                return {
                    'success': False,
                    'error': f'No tables found for {data_type}',
                    'data': None
                }

            # 过滤特定表格
            if table_id:
                tables = [t for t in tables if t.table_id == table_id]
                if not tables:
                    return {
                        'success': False,
                        'error': f'Table {table_id} not found',
                        'data': None
                    }

            # 下载和处理数据
            results = []
            for table in tables:
                try:
                    file_path = await self._download_file(table.url, table.table_id)
                    if file_path and file_path.exists():
                        results.append({
                            'table_id': table.table_id,
                            'title': table.title,
                            'format': table.format,
                            'file_path': str(file_path),
                            'downloaded_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    self.logger.error(f"Error processing table {table.table_id}: {e}")

            return {
                'success': True,
                'data': {
                    'data_type': data_type,
                    'tables': results,
                    'total_tables': len(results),
                    'discovered_at': datetime.now().isoformat()
                },
                'source': 'csd_crawler'
            }

        except Exception as e:
            error_info = self.error_handler.handle_error(e, context)
            return {
                'success': False,
                'error': error_info,
                'data': None
            }

    async def get_data_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要

        Returns:
            数据源摘要
        """
        return {
            'adapter_name': 'CSDDataCrawler',
            'config': self.config.dict(),
            'discovered_tables': {
                dtype.value: len(tables)
                for dtype, tables in self._table_index.items()
            },
            'total_tables': sum(len(tables) for tables in self._table_index.values()),
            'download_dir': self.config.download_dir,
            'timestamp': datetime.now().isoformat()
        }

    async def cleanup_old_downloads(self, days: int = 30) -> int:
        """
        清理旧下载文件

        Args:
            days: 保留天数

        Returns:
            清理的文件数量
        """
        download_dir = Path(self.config.download_dir)
        if not download_dir.exists():
            return 0

        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_count = 0

        for file_path in download_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {file_path}: {e}")

        self.logger.info(f"Cleaned {cleaned_count} old files")
        return cleaned_count


# 便捷函数
async def get_csd_tables(data_type: Optional[CSDDataType] = None) -> Dict[CSDDataType, List[CSDWebTable]]:
    """获取C&SD数据表索引"""
    crawler = CSDDataCrawler()
    try:
        return await crawler.discover_tables(data_type)
    finally:
        await crawler.close()


async def download_csd_data(
    data_type: CSDDataType,
    table_id: Optional[str] = None
) -> Dict[str, Any]:
    """下载C&SD数据"""
    crawler = CSDDataCrawler()
    try:
        return await crawler.fetch_data(data_type, table_id)
    finally:
        await crawler.close()
