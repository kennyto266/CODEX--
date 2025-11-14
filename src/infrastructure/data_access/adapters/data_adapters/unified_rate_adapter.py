"""
统一利率数据适配器
Base class for all rate data adapters (PBOC, FED, SIBOR)

基于HKMA HIBOR适配器架构，提供标准化的利率数据获取接口。
支持异步操作、错误处理、重试机制和数据验证。

Author: Phase 2 Development
Date: 2025-11-12
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
import aiohttp
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class RateIndicator(Enum):
    """利率指标枚举"""
    OVERNIGHT = "overnight"  # 隔夜
    ONE_WEEK = "1w"  # 1周
    ONE_MONTH = "1m"  # 1个月
    THREE_MONTHS = "3m"  # 3个月
    SIX_MONTHS = "6m"  # 6个月
    TWELVE_MONTHS = "12m"  # 12个月
    FED_FUNDS = "fed_funds"  # 联邦基金利率
    DISCOUNT_RATE = "discount_rate"  # 贴现率
    TREASURY_10Y = "treasury_10y"  # 10年期国债


class Currency(Enum):
    """货币类型"""
    USD = "USD"
    HKD = "HKD"
    CNY = "CNY"
    SGD = "SGD"


class RateDataPoint(BaseModel):
    """利率数据点"""
    indicator: RateIndicator
    currency: Currency
    date: date
    value: float  # 百分比形式，如 5.25 表示 5.25%
    unit: str = "%"
    source: str
    is_mock: bool = False
    last_updated: datetime = Field(default_factory=datetime.now)

    @validator('value')
    def validate_value(cls, v):
        """验证利率值"""
        if v < 0 or v > 100:
            raise ValueError(f"Rate value must be between 0 and 100, got {v}")
        return v


class BaseRateAdapter(ABC):
    """统一利率数据适配器基类"""

    # 适配器元数据
    ADAPTER_NAME: str
    DATA_SOURCE_URL: str
    SUPPORTED_INDICATORS: Dict[str, Dict] = {}
    DEFAULT_CURRENCY: Currency = Currency.USD

    # 请求配置
    TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 1.0  # 秒

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化适配器

        Args:
            config: 配置字典
                - timeout: 超时时间（秒）
                - max_retries: 最大重试次数
                - rate_limit_delay: 限流延迟（秒）
                - use_mock_data: 是否使用模拟数据
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', self.TIMEOUT)
        self.max_retries = self.config.get('max_retries', self.MAX_RETRIES)
        self.rate_limit_delay = self.config.get('rate_limit_delay', self.RATE_LIMIT_DELAY)
        self.use_mock_data = self.config.get('use_mock_data', False)

        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_bucket = 0  # 简单限流令牌桶

        logger.info(f"Initialized {self.ADAPTER_NAME} adapter")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _rate_limit(self):
        """简单限流机制"""
        if self.rate_limit_delay > 0:
            # 使用令牌桶算法进行简单限流
            if self._rate_limit_bucket >= 10:
                await asyncio.sleep(self.rate_limit_delay)
                self._rate_limit_bucket = 0
            else:
                self._rate_limit_bucket += 1

    async def _make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[aiohttp.ClientResponse]:
        """
        发送HTTP请求（带重试和限流）

        Args:
            url: 请求URL
            method: HTTP方法
            params: 查询参数
            retry_count: 当前重试次数

        Returns:
            响应对象或None
        """
        if retry_count >= self.max_retries:
            logger.error(f"达到最大重试次数 ({self.max_retries}): {url}")
            return None

        await self._rate_limit()

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params
            ) as response:
                if response.status == 200:
                    return response
                else:
                    logger.warning(
                        f"HTTP {response.status} for {url}, "
                        f"retry {retry_count + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(1 * (2 ** retry_count))
                    return await self._make_request(url, method, params, retry_count + 1)

        except aiohttp.ClientError as e:
            logger.warning(
                f"请求错误 {url}: {e}, retry {retry_count + 1}/{self.max_retries}"
            )
            if retry_count < self.max_retries:
                await asyncio.sleep(1 * (2 ** retry_count))
                return await self._make_request(url, method, params, retry_count + 1)
            return None

    async def fetch_latest_rate(
        self,
        indicator: RateIndicator
    ) -> Optional[RateDataPoint]:
        """
        获取最新利率

        Args:
            indicator: 利率指标

        Returns:
            RateDataPoint或None
        """
        logger.info(f"获取最新{indicator}利率...")

        if self.use_mock_data:
            return self._generate_mock_data(indicator, date.today())

        try:
            if indicator == RateIndicator.FED_FUNDS:
                return await self._fetch_fed_funds_rate()
            elif indicator == RateIndicator.DISCOUNT_RATE:
                return await self._fetch_discount_rate()
            else:
                return await self._fetch_generic_rate(indicator)
        except Exception as e:
            logger.error(f"获取{indicator}利率失败: {e}")
            return None

    async def fetch_historical_rates(
        self,
        indicator: RateIndicator,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Optional[List[RateDataPoint]]:
        """
        获取历史利率数据

        Args:
            indicator: 利率指标
            start_date: 开始日期
            end_date: 结束日期（默认今天）

        Returns:
            RateDataPoint列表或None
        """
        if end_date is None:
            end_date = date.today()

        logger.info(f"获取{indicator}历史数据: {start_date} 到 {end_date}")

        if self.use_mock_data:
            return self._generate_mock_historical(indicator, start_date, end_date)

        try:
            return await self._fetch_historical_data(indicator, start_date, end_date)
        except Exception as e:
            logger.error(f"获取{indicator}历史数据失败: {e}")
            return None

    async def _fetch_fed_funds_rate(self) -> Optional[RateDataPoint]:
        """获取联邦基金利率（特定适配器需重写）"""
        # 子类需实现具体逻辑
        return None

    async def _fetch_discount_rate(self) -> Optional[RateDataPoint]:
        """获取贴现率（特定适配器需重写）"""
        # 子类需实现具体逻辑
        return None

    async def _fetch_generic_rate(
        self,
        indicator: RateIndicator
    ) -> Optional[RateDataPoint]:
        """获取通用利率（特定适配器需重写）"""
        # 子类需实现具体逻辑
        return None

    async def _fetch_historical_data(
        self,
        indicator: RateIndicator,
        start_date: date,
        end_date: date
    ) -> Optional[List[RateDataPoint]]:
        """获取历史数据（特定适配器需重写）"""
        # 子类需实现具体逻辑
        return None

    def _generate_mock_data(
        self,
        indicator: RateIndicator,
        data_date: date
    ) -> RateDataPoint:
        """生成模拟数据（用于测试）"""
        # 生成合理的模拟利率值
        base_rates = {
            RateIndicator.FED_FUNDS: 5.25,
            RateIndicator.DISCOUNT_RATE: 5.50,
            RateIndicator.OVERNIGHT: 5.25,
            RateIndicator.ONE_MONTH: 5.35,
            RateIndicator.THREE_MONTHS: 5.45,
            RateIndicator.SIX_MONTHS: 5.55,
            RateIndicator.TWELVE_MONTHS: 5.65,
        }

        base_value = base_rates.get(indicator, 5.00)
        # 添加随机波动
        import random
        value = base_value + random.uniform(-0.5, 0.5)

        return RateDataPoint(
            indicator=indicator,
            currency=self.DEFAULT_CURRENCY,
            date=data_date,
            value=value,
            source=self.ADAPTER_NAME,
            is_mock=True
        )

    def _generate_mock_historical(
        self,
        indicator: RateIndicator,
        start_date: date,
        end_date: date
    ) -> List[RateDataPoint]:
        """生成模拟历史数据"""
        data = []
        current = start_date

        base_rates = {
            RateIndicator.FED_FUNDS: 5.25,
            RateIndicator.DISCOUNT_RATE: 5.50,
            RateIndicator.OVERNIGHT: 5.25,
            RateIndicator.ONE_MONTH: 5.35,
            RateIndicator.THREE_MONTHS: 5.45,
            RateIndicator.SIX_MONTHS: 5.55,
            RateIndicator.TWELVE_MONTHS: 5.65,
        }

        base_value = base_rates.get(indicator, 5.00)

        while current <= end_date:
            # 只在工作日生成数据
            if current.weekday() < 5:
                import random
                value = base_value + random.uniform(-1.0, 1.0)

                data.append(RateDataPoint(
                    indicator=indicator,
                    currency=self.DEFAULT_CURRENCY,
                    date=current,
                    value=max(0, min(20, value)),  # 限制在0-20%之间
                    source=self.ADAPTER_NAME,
                    is_mock=True
                ))
            current += timedelta(days=1)

        return data

    def get_supported_indicators(self) -> Dict[str, Dict]:
        """获取支持的指标列表"""
        return self.SUPPORTED_INDICATORS.copy()

    def to_dataframe(
        self,
        data_points: List[RateDataPoint]
    ) -> pd.DataFrame:
        """将数据点转换为DataFrame"""
        if not data_points:
            return pd.DataFrame()

        data = [{
            'date': dp.date,
            'indicator': dp.indicator,
            'currency': dp.currency,
            'value': dp.value,
            'unit': dp.unit,
            'source': dp.source,
            'is_mock': dp.is_mock
        } for dp in data_points]

        df = pd.DataFrame(data)
        df = df.sort_values('date')
        return df


# 便捷函数
async def get_latest_rate(
    adapter: BaseRateAdapter,
    indicator: RateIndicator
) -> Optional[RateDataPoint]:
    """获取最新利率的便捷函数"""
    async with adapter:
        return await adapter.fetch_latest_rate(indicator)


async def get_historical_rates(
    adapter: BaseRateAdapter,
    indicator: RateIndicator,
    start_date: date,
    end_date: Optional[date] = None
) -> Optional[List[RateDataPoint]]:
    """获取历史利率的便捷函数"""
    async with adapter:
        return await adapter.fetch_historical_rates(indicator, start_date, end_date)
