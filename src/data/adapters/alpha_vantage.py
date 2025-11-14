"""
Phase 2: Enhanced Alpha Vantage Adapter
========================================

Alpha Vantage数据适配器 - 获取全球股票、外汇、加密货币数据

特性：
1. 完全异步实现
2. 速率限制控制
3. 多种数据类型支持
4. 数据质量验证
5. 自动重试和错误处理
6. 缓存机制
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List, Tuple
import aiohttp
import pandas as pd
import json

from .base import BaseAdapter, AdapterConfig, OHLCV, DataValidationResult, DataQuality, DataSourceType


class AlphaVantageAdapter(BaseAdapter):
    """
    Alpha Vantage数据适配器

    支持股票、外汇、加密货币、技术指标等多种数据类型
    官网: https://www.alphavantage.co/
    API: https://www.alphavantage.co/query
    """

    # 支持的功能映射
    FUNCTIONS = {
        # 股票数据
        'stock_daily': 'TIME_SERIES_DAILY',
        'stock_daily_adjusted': 'TIME_SERIES_DAILY_ADJUSTED',
        'stock_intraday': 'TIME_SERIES_INTRADAY',
        'stock_weekly': 'TIME_SERIES_WEEKLY',
        'stock_monthly': 'TIME_SERIES_MONTHLY',
        'stock_monthly_adjusted': 'TIME_SERIES_MONTHLY_ADJUSTED',

        # 外汇数据
        'fx_intraday': 'FX_INTRADAY',
        'fx_daily': 'FX_DAILY',
        'fx_weekly': 'FX_WEEKLY',
        'fx_monthly': 'FX_MONTHLY',

        # 加密货币
        'crypto_intraday': 'CRYPTO_INTRADAY',
        'crypto_daily': 'CRYPTO_DAILY',
        'crypto_weekly': 'CRYPTO_WEEKLY',
        'crypto_monthly': 'CRYPTO_MONTHLY',

        # 技术指标
        'sma': 'SMA',
        'ema': 'EMA',
        'rsi': 'RSI',
        'macd': 'MACD',
        'bbands': 'BBANDS',
        'stoch': 'STOCH',
        'atr': 'ATR',
        'adx': 'ADX',
        'cci': 'CCI',
        'mom': 'MOM',
        'mfi': 'MFI',
        'trix': 'TRIX',
        'obv': 'OBV',

        # 经济指标
        'gdp': 'REAL_GDP',
        'inflation': 'CPI',
        'treasury_yield': 'TREASURY_YIELD',
        'unemployment': 'UNEMPLOYMENT',
    }

    # 时间间隔映射
    INTERVALS = {
        '1min': '1min',
        '5min': '5min',
        '15min': '15min',
        '30min': '30min',
        '60min': '60min',
    }

    def __init__(self, config: Optional[AdapterConfig] = None, api_key: Optional[str] = None):
        """
        初始化Alpha Vantage适配器

        Args:
            config: 适配器配置
            api_key: Alpha Vantage API密钥
        """

        if config is None:
            config = AdapterConfig(
                source_type=DataSourceType.ALPHA_VANTAGE,
                source_name="Alpha Vantage",
                update_frequency=60,
                max_retries=3,
                timeout=30,
                cache_enabled=True,
                cache_ttl=300,
                quality_threshold=0.8,
                rate_limit=5  # 免费版每分钟5次请求
            )

        super().__init__(config)

        # 获取API密钥
        self.api_key = api_key or os.getenv('ALPHAVANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key is required\n"
                "1. Get free key: https://www.alphavantage.co/support/#api-key\n"
                "2. Set environment variable: export ALPHAVANTAGE_API_KEY=your_key\n"
                "3. Or pass to constructor: AlphaVantageAdapter(api_key='your_key')"
            )

        self.base_url = "https://www.alphavantage.co/query"
        self.session: Optional[aiohttp.ClientSession] = None

        # 速率限制控制
        self._last_request_time = 0
        self._min_interval = 60.0 / self.config.rate_limit if self.config.rate_limit else 12.0

        self.logger = logging.getLogger("hk_quant_system.adapters.alpha_vantage")

    async def connect(self) -> bool:
        """连接到Alpha Vantage API"""
        try:
            self.status = "connecting"

            await self._ensure_session()

            # 测试连接 - 外汇数据
            test_params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': 'USD',
                'to_currency': 'HKD',
                'apikey': self.api_key
            }

            async with self.session.get(self.base_url, params=test_params) as response:
                if response.status == 200:
                    data = await response.json()

                    # 检查API错误
                    if "Error Message" in data or "Note" in data:
                        error_msg = data.get("Error Message") or data.get("Note")
                        self.logger.error(f"API error: {error_msg}")
                        self.status = "error"
                        return False

                    self.status = "connected"
                    self.logger.info("Successfully connected to Alpha Vantage API")
                    return True
                else:
                    self.status = "error"
                    self.logger.error(f"HTTP error: {response.status}")
                    return False

        except Exception as e:
            self.status = "error"
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()

            self.status = "idle"
            self.logger.info("Disconnected from Alpha Vantage API")
            return True

        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def _ensure_session(self):
        """确保aiohttp会话存在"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _make_request(
        self,
        function: str,
        **params
    ) -> Dict[str, Any]:
        """
        执行API请求（带速率限制控制）

        Args:
            function: Alpha Vantage功能名称
            **params: 额外参数

        Returns:
            API响应数据
        """
        await self._ensure_session()

        # 速率限制控制
        await self._rate_limit()

        # 构建请求参数
        request_params = {
            'function': function,
            'apikey': self.api_key,
            **params
        }

        try:
            self.logger.debug(f"Requesting: {function} {params.get('symbol', '')}")

            async with self.session.get(self.base_url, params=request_params) as response:
                self._last_request_time = time.time()

                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                data = await response.json()

                # 检查API错误
                if "Error Message" in data:
                    raise Exception(f"API Error: {data['Error Message']}")

                if "Note" in data:
                    raise Exception(f"API Limit: {data['Note']}")

                # 检查数据是否为空
                if not data or len(data) <= 1:
                    raise Exception("No data received")

                self.logger.debug(f"Successfully received data")
                return data

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    async def _rate_limit(self):
        """速率限制控制"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_interval:
            wait_time = self._min_interval - time_since_last
            self.logger.debug(f"Rate limiting: waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)

    async def fetch_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        function: str = 'stock_daily',
        interval: Optional[str] = None,
        outputsize: str = 'compact',
        **kwargs
    ) -> List[OHLCV]:
        """
        获取市场数据

        Args:
            symbol: 股票代码 (如 '0700.HK' 或 'AAPL')
            start_date: 开始日期
            end_date: 结束日期
            function: 数据类型 ('stock_daily', 'crypto_daily' 等)
            interval: 时间间隔 ('1min', '5min', 'daily' 等)
            outputsize: 数据量 ('compact' 最近100天, 'full' 完整历史)
            **kwargs: 额外参数

        Returns:
            List[OHLCV]: 市场数据列表
        """
        try:
            # 检查缓存
            cache_key = self._get_cache_key(
                symbol, start_date, end_date,
                function=function, interval=interval, outputsize=outputsize, **kwargs
            )
            cached_data = self._get_cache(cache_key)
            if cached_data:
                self.logger.debug(f"Using cached data for {symbol}")
                return cached_data

            # 验证函数
            if function not in self.FUNCTIONS:
                raise ValueError(f"Unsupported function: {function}")

            av_function = self.FUNCTIONS[function]

            # 构建参数
            params = {
                'function': av_function,
                'outputsize': outputsize,
                **kwargs
            }

            # 添加时间间隔（如果是时间序列数据）
            if 'stock_intraday' in function and interval:
                params['interval'] = interval
            elif 'crypto_intraday' in function and interval:
                params['interval'] = interval
            elif 'fx_intraday' in function and interval:
                params['interval'] = interval

            # 处理股票/外汇/加密货币
            if function.startswith('stock'):
                # 港股代码转换 (Alpha Vantage使用一般格式)
                av_symbol = self._convert_symbol(symbol)
                params['symbol'] = av_symbol

            elif function.startswith('fx'):
                # 外汇数据 (如 USD, HKD)
                params['from_symbol'] = symbol.split('/')[0] if '/' in symbol else symbol
                params['to_symbol'] = symbol.split('/')[1] if '/' in symbol else 'USD'

            elif function.startswith('crypto'):
                # 加密货币 (如 BTC, USD)
                params['symbol'] = symbol
                params['market'] = kwargs.get('market', 'USD')

            self.logger.info(
                f"Fetching {function} data for {symbol} from {start_date} to {end_date}"
            )

            # 执行请求
            data = await self._execute_with_retry(
                self._make_request,
                function=av_function,
                **params
            )

            # 解析响应
            market_data = await self._parse_time_series(data, symbol, function)

            # 过滤日期范围
            if start_date or end_date:
                market_data = self._filter_by_date(market_data, start_date, end_date)

            # 验证数据质量
            validation_result = await self.validate_data(market_data)
            if validation_result.quality_level in [DataQuality.POOR, DataQuality.UNKNOWN]:
                self.logger.warning(
                    f"Poor data quality for {symbol}: {validation_result.errors}"
                )

            # 缓存数据
            self._set_cache(cache_key, market_data)

            self.logger.info(f"Successfully fetched {len(market_data)} data points")

            return market_data

        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            raise

    def _convert_symbol(self, symbol: str) -> str:
        """
        转换股票代码格式

        Args:
            symbol: 原始股票代码 (如 '0700.HK', 'AAPL')

        Returns:
            str: Alpha Vantage格式的代码
        """
        # 去除空格
        symbol = symbol.strip().upper()

        # 港股转换: 0700.HK -> 700
        if symbol.endswith('.HK'):
            code = symbol.replace('.HK', '').lstrip('0') or '0'
            return code

        # 美股直接返回
        return symbol

    async def _parse_time_series(
        self,
        data: Dict[str, Any],
        symbol: str,
        function: str
    ) -> List[OHLCV]:
        """
        解析时间序列数据

        Args:
            data: API响应数据
            symbol: 股票代码
            function: 功能类型

        Returns:
            List[OHLCV]: 解析后的数据
        """
        try:
            # 查找时间序列键
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break

            if not time_series_key:
                # 检查是否是单一数据点（如外汇汇率）
                if 'Realtime Currency Exchange Rate' in data:
                    return await self._parse_fx_realtime(data, symbol)

                raise Exception("No time series data found")

            time_series = data[time_series_key]

            # 解析时间序列
            market_data = []
            for date_str, values in time_series.items():
                try:
                    # 解析日期
                    if 'Time Series' in time_series_key:
                        # 标准时间序列
                        if '1. open' in values:
                            ohlcv = OHLCV(
                                timestamp=pd.to_datetime(date_str).to_pydatetime(),
                                open=float(values['1. open']),
                                high=float(values['2. high']),
                                low=float(values['3. low']),
                                close=float(values['4. close']),
                                volume=int(values['5. volume']),
                                adj_close=float(values.get('5. adjusted close', 0)) if '5. adjusted close' in values else None,
                                symbol=symbol
                            )
                        else:
                            # 技术指标数据格式不同
                            continue

                        market_data.append(ohlcv)

                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Skipping invalid data point: {e}")
                    continue

            # 按时间排序
            market_data.sort(key=lambda x: x.timestamp)

            return market_data

        except Exception as e:
            self.logger.error(f"Error parsing time series: {e}")
            raise

    async def _parse_fx_realtime(self, data: Dict[str, Any], symbol: str) -> List[OHLCV]:
        """解析外汇实时数据"""
        try:
            rate_data = data.get("Realtime Currency Exchange Rate", {})
            if not rate_data:
                return []

            # 转换为OHLCV格式（只有一个点）
            ohlcv = OHLCV(
                timestamp=datetime.now(),
                open=float(rate_data.get('5. Exchange Rate', 0)),
                high=float(rate_data.get('5. Exchange Rate', 0)),
                low=float(rate_data.get('5. Exchange Rate', 0)),
                close=float(rate_data.get('5. Exchange Rate', 0)),
                volume=0,
                symbol=symbol
            )

            return [ohlcv]

        except Exception as e:
            self.logger.error(f"Error parsing FX data: {e}")
            return []

    def _filter_by_date(
        self,
        data: List[OHLCV],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[OHLCV]:
        """按日期范围过滤数据"""
        filtered = data

        if start_date:
            filtered = [d for d in filtered if d.timestamp.date() >= start_date]

        if end_date:
            filtered = [d for d in filtered if d.timestamp.date() <= end_date]

        return filtered

    async def validate_data(self, data: List[OHLCV]) -> DataValidationResult:
        """
        验证数据质量

        Args:
            data: 待验证的数据列表

        Returns:
            DataValidationResult: 验证结果
        """
        try:
            if not data:
                return DataValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    quality_level=DataQuality.POOR,
                    errors=["No data provided"],
                    warnings=[]
                )

            errors = []
            warnings = []

            # 检查数据完整性
            for i, item in enumerate(data):
                # 检查价格数据
                if any(price <= 0 for price in [item.open, item.high, item.low, item.close]):
                    errors.append(f"Invalid price data at index {i}")

                # 检查价格逻辑
                if item.high < item.low:
                    errors.append(f"High < Low at index {i}")

                # 检查成交量（外汇数据可能为0）
                if item.volume < 0:
                    errors.append(f"Negative volume at index {i}")

            # 计算质量评分
            quality_score = self.calculate_quality_score(data)
            quality_level = self.get_quality_level(quality_score)

            is_valid = len(errors) == 0 and quality_score >= self.config.quality_threshold

            return DataValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                quality_level=quality_level,
                errors=errors,
                warnings=warnings,
                metadata={
                    "data_points": len(data),
                    "function": "time_series",
                    "date_range": {
                        "start": data[0].timestamp if data else None,
                        "end": data[-1].timestamp if data else None
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )

    async def get_fx_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        获取外汇汇率

        Args:
            from_currency: 源货币 (如 'USD')
            to_currency: 目标货币 (如 'HKD')

        Returns:
            float: 汇率值
        """
        try:
            data = await self._make_request(
                function='CURRENCY_EXCHANGE_RATE',
                from_currency=from_currency,
                to_currency=to_currency
            )

            rate_key = "Realtime Currency Exchange Rate"
            if rate_key not in data:
                raise Exception("FX data format error")

            exchange_rate = data[rate_key].get("5. Exchange Rate")
            if not exchange_rate:
                raise Exception("No exchange rate data")

            return float(exchange_rate)

        except Exception as e:
            self.logger.error(f"Error fetching FX rate: {e}")
            raise

    async def get_supported_functions(self) -> List[str]:
        """
        获取支持的功能列表

        Returns:
            List[str]: 功能名称列表
        """
        return list(self.FUNCTIONS.keys())

    async def get_data_source_info(self) -> Dict[str, Any]:
        """
        获取数据源信息

        Returns:
            Dict[str, Any]: 数据源信息
        """
        return {
            "name": "Alpha Vantage",
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "rate_limit": f"{self.config.rate_limit}/minute" if self.config.rate_limit else "N/A",
            "supported_functions": len(self.FUNCTIONS),
            "supported_types": list(set(key.split('_')[0] for key in self.FUNCTIONS.keys())),
            "description": "Financial data APIs for stocks, forex, crypto, and technical indicators",
            "website": "https://www.alphavantage.co/",
            "last_update": datetime.now().isoformat()
        }


# 使用示例
async def main():
    """示例用法"""
    import os

    # 设置API密钥
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    if not api_key:
        print("Please set ALPHAVANTAGE_API_KEY environment variable")
        return

    # 创建配置
    config = AdapterConfig(
        source_type=DataSourceType.ALPHA_VANTAGE,
        source_name="Alpha Vantage",
        rate_limit=5,  # 免费版限制
        cache_enabled=True
    )

    # 创建适配器
    async with AlphaVantageAdapter(config, api_key) as adapter:
        # 测试连接
        if await adapter.connect():
            print("✓ Connected to Alpha Vantage")

            # 获取腾讯数据
            data = await adapter.fetch_data("0700.HK", days=30)
            print(f"✓ Fetched {len(data)} data points for 0700.HK")

            # 获取USD/HKD汇率
            rate = await adapter.get_fx_rate('USD', 'HKD')
            print(f"✓ USD/HKD rate: {rate:.4f}")

            # 获取支持的功能
            functions = await adapter.get_supported_functions()
            print(f"✓ Supported functions: {len(functions)}")

        else:
            print("✗ Failed to connect")

if __name__ == "__main__":
    asyncio.run(main())
