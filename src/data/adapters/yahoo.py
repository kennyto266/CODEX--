"""
Phase 2: Enhanced Yahoo Finance Adapter
========================================

Yahoo Finance数据适配器 - 获取港股、美股等市场数据

特性：
1. 完全异步实现
2. 支持港股格式转换 (.HK)
3. 内置缓存和重试机制
4. 数据质量验证
5. 性能优化
6. 支持批量获取
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from decimal import Decimal

from .base import BaseAdapter, AdapterConfig, OHLCV, DataValidationResult, DataQuality, DataSourceType


class YahooFinanceAdapter(BaseAdapter):
    """
    Yahoo Finance数据适配器

    支持港股、美股、加密货币等多种市场数据
    """

    # 支持的市场和对应的后缀
    MARKET_SUFFIXES = {
        'HK': '.HK',  # 港股
        'US': '',     # 美股
        'CRYPTO': '-USD',  # 加密货币
    }

    # 常用港股代码映射
    HK_SYMBOLS = {
        '0700': '0700.HK',  # 腾讯
        '0388': '0388.HK',  # 港交所
        '0939': '0939.HK',  # 建设银行
        '1398': '1398.HK',  # 工商银行
        '3988': '3988.HK',  # 中国银行
        '2800': '2800.HK',  # 盈富基金
        '0941': '0941.HK',  # 中国移动
        '1299': '1299.HK',  # 友邦保险
        '2318': '2318.HK',  # 中国平安
        '2628': '2628.HK',  # 中国人寿
    }

    def __init__(self, config: Optional[AdapterConfig] = None):
        """初始化Yahoo Finance适配器"""

        if config is None:
            config = AdapterConfig(
                source_type=DataSourceType.YAHOO_FINANCE,
                source_name="Yahoo Finance",
                update_frequency=60,
                max_retries=3,
                timeout=30,
                cache_enabled=True,
                cache_ttl=300,
                quality_threshold=0.8,
                rate_limit=60  # 每分钟60次请求
            )

        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.adapters.yahoo_finance")

        # 验证yfinance库
        try:
            import yfinance
            self.logger.info("Yahoo Finance adapter initialized successfully")
        except ImportError:
            raise ImportError(
                "yfinance library is required. Install with: pip install yfinance"
            )

    async def connect(self) -> bool:
        """连接到Yahoo Finance"""
        try:
            self.status = "connecting"

            # 测试连接
            test_symbol = "AAPL"
            ticker = yf.Ticker(test_symbol)

            # 尝试获取测试数据
            info = await asyncio.get_event_loop().run_in_executor(
                None, ticker.info.get, 'regularMarketPrice'
            )

            if info:
                self.status = "connected"
                self.logger.info("Successfully connected to Yahoo Finance")
                return True
            else:
                self.status = "error"
                self.logger.error("Failed to connect to Yahoo Finance")
                return False

        except Exception as e:
            self.status = "error"
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            self.status = "idle"
            self.logger.info("Disconnected from Yahoo Finance")
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码

        Args:
            symbol: 原始股票代码

        Returns:
            str: 标准化后的代码
        """
        # 去除空格
        symbol = symbol.strip().upper()

        # 如果已经包含后缀，直接返回
        if any(suffix in symbol for suffix in self.MARKET_SUFFIXES.values()):
            return symbol

        # 检查是否是港股简码
        if symbol in self.HK_SYMBOLS:
            return self.HK_SYMBOLS[symbol]

        # 默认添加港股后缀
        if len(symbol) == 4 and symbol.isdigit():
            return f"{symbol}.HK"

        return symbol

    async def fetch_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        **kwargs
    ) -> List[OHLCV]:
        """
        获取市场数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 额外参数
                - interval: 数据间隔 (1d, 1h, 5m等)
                - actions: 是否包含分红和股票分割 (默认False)
                - auto_adjust: 是否自动调整 (默认True)

        Returns:
            List[OHLCV]: 市场数据列表
        """
        try:
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol)

            # 检查缓存
            cache_key = self._get_cache_key(normalized_symbol, start_date, end_date, **kwargs)
            cached_data = self._get_cache(cache_key)
            if cached_data:
                self.logger.debug(f"Using cached data for {symbol}")
                return cached_data

            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=365)  # 默认1年数据

            # 获取参数
            interval = kwargs.get('interval', '1d')
            actions = kwargs.get('actions', False)
            auto_adjust = kwargs.get('auto_adjust', True)

            self.logger.info(
                f"Fetching {interval} data for {symbol} from {start_date} to {end_date}"
            )

            # 使用线程池执行yfinance操作（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(normalized_symbol)

            def _fetch_history():
                return ticker.history(
                    start=start_date,
                    end=end_date + timedelta(days=1),  # 包含结束日期
                    interval=interval,
                    actions=actions,
                    auto_adjust=auto_adjust,
                    prepost=True
                )

            hist = await loop.run_in_executor(None, _fetch_history)

            if hist.empty:
                self.logger.warning(f"No data found for symbol: {symbol}")
                return []

            # 转换为标准OHLCV格式
            market_data = await self._transform_data(hist, symbol)

            # 验证数据质量
            validation_result = await self.validate_data(market_data)
            if validation_result.quality_level in [DataQuality.POOR, DataQuality.UNKNOWN]:
                self.logger.warning(
                    f"Poor data quality for {symbol}: {validation_result.errors}"
                )

            # 缓存数据
            self._set_cache(cache_key, market_data)

            self.logger.info(
                f"Successfully fetched {len(market_data)} data points for {symbol}"
            )

            return market_data

        except Exception as e:
            self.logger.error(f"Error fetching market data for {symbol}: {e}")
            raise

    async def _transform_data(
        self, raw_data: pd.DataFrame, original_symbol: str
    ) -> List[OHLCV]:
        """
        转换原始数据为标准格式

        Args:
            raw_data: Yahoo Finance原始数据
            original_symbol: 原始股票代码

        Returns:
            List[OHLCV]: 转换后的标准数据
        """
        try:
            market_data = []

            for timestamp, row in raw_data.iterrows():
                # 处理可能的NaN值
                ohlcv = OHLCV(
                    timestamp=pd.to_datetime(timestamp).to_pydatetime(),
                    open=float(row['Open']) if pd.notna(row['Open']) else 0.0,
                    high=float(row['High']) if pd.notna(row['High']) else 0.0,
                    low=float(row['Low']) if pd.notna(row['Low']) else 0.0,
                    close=float(row['Close']) if pd.notna(row['Close']) else 0.0,
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0,
                    adj_close=float(row['Adj Close']) if pd.notna(row.get('Adj Close', np.nan)) else None,
                    symbol=original_symbol
                )

                market_data.append(ohlcv)

            return market_data

        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            raise

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
            data_points = len(data)

            # 检查数据完整性
            for i, item in enumerate(data):
                # 检查价格数据
                if any(price <= 0 for price in [item.open, item.high, item.low, item.close]):
                    errors.append(f"Invalid price data at index {i}")

                # 检查价格逻辑
                if item.high < item.low:
                    errors.append(f"High price < Low price at index {i}")

                if item.high < item.open or item.high < item.close:
                    errors.append(f"High price not highest at index {i}")

                if item.low > item.open or item.low > item.close:
                    errors.append(f"Low price not lowest at index {i}")

                # 检查成交量
                if item.volume < 0:
                    errors.append(f"Negative volume at index {i}")

                # 检查时间戳
                if item.timestamp > datetime.now():
                    warnings.append(f"Future timestamp at index {i}")

            # 计算质量评分
            quality_score = self.calculate_quality_score(data)
            quality_level = self.get_quality_level(quality_score)

            # 检查数据连续性
            if len(data) > 1:
                time_gaps = []
                for i in range(1, len(data)):
                    gap = (data[i].timestamp - data[i-1].timestamp).days
                    if gap > 7:  # 超过7天的间隔
                        warnings.append(
                            f"Large time gap: {gap} days between "
                            f"{data[i-1].timestamp.date()} and {data[i].timestamp.date()}"
                        )

            is_valid = len(errors) == 0 and quality_score >= self.config.quality_threshold

            return DataValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                quality_level=quality_level,
                errors=errors,
                warnings=warnings,
                metadata={
                    "data_points": data_points,
                    "symbol": data[0].symbol if data else None,
                    "date_range": {
                        "start": data[0].timestamp if data else None,
                        "end": data[-1].timestamp if data else None
                    },
                    "price_range": {
                        "min": min(item.low for item in data) if data else None,
                        "max": max(item.high for item in data) if data else None
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

    async def get_realtime_data(self, symbol: str) -> Optional[OHLCV]:
        """
        获取实时数据

        Args:
            symbol: 股票代码

        Returns:
            Optional[OHLCV]: 实时数据点
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)

            # 使用线程池执行
            loop = asyncio.get_event_loop()

            def _get_info():
                return ticker.info

            def _get_history():
                return ticker.history(period="1d", interval="1m")

            info, hist = await asyncio.gather(
                loop.run_in_executor(None, _get_info),
                loop.run_in_executor(None, _get_history)
            )

            if not info or 'regularMarketPrice' not in info:
                self.logger.warning(f"No real-time data available for {symbol}")
                return None

            current_price = float(info.get('regularMarketPrice', 0))
            open_price = float(info.get('regularMarketOpen', current_price))
            day_high = float(info.get('dayHigh', current_price))
            day_low = float(info.get('dayLow', current_price))
            volume = int(info.get('regularMarketVolume', 0))

            # 如果有分钟级数据，使用最新的数据点
            if not hist.empty:
                latest = hist.iloc[-1]
                current_price = float(latest['Close'])
                open_price = float(latest['Open'])
                day_high = float(latest['High'])
                day_low = float(latest['Low'])
                volume = int(latest['Volume'])

            data_point = OHLCV(
                timestamp=datetime.now(),
                open=open_price,
                high=day_high,
                low=day_low,
                close=current_price,
                volume=volume,
                adj_close=current_price,
                symbol=symbol
            )

            return data_point

        except Exception as e:
            self.logger.error(f"Error fetching real-time data for {symbol}: {e}")
            return None

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_concurrent: int = 10,
        **kwargs
    ) -> Dict[str, List[OHLCV]]:
        """
        批量获取多个标的的数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            max_concurrent: 最大并发数
            **kwargs: 额外参数

        Returns:
            Dict[str, List[OHLCV]]: 各股票的数据字典
        """
        try:
            self.logger.info(f"Fetching data for {len(symbols)} symbols")

            # 设置默认日期
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=365)

            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(max_concurrent)

            async def fetch_with_semaphore(symbol):
                async with semaphore:
                    try:
                        return await self.fetch_data(symbol, start_date, end_date, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Error fetching {symbol}: {e}")
                        return []

            # 并行获取数据
            tasks = [fetch_with_semaphore(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 整理结果
            symbol_data = {}
            successful_count = 0

            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error fetching data for {symbol}: {result}")
                    symbol_data[symbol] = []
                elif result:
                    symbol_data[symbol] = result
                    successful_count += 1
                else:
                    symbol_data[symbol] = []

            self.logger.info(
                f"Successfully fetched data for {successful_count}/{len(symbols)} symbols"
            )

            return symbol_data

        except Exception as e:
            self.logger.error(f"Error fetching multiple symbols data: {e}")
            return {}

    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索股票代码

        Args:
            query: 搜索关键词

        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        try:
            # 扩展的常用股票列表
            common_symbols = {
                # 港股
                "0700.HK": "腾讯控股",
                "0941.HK": "中国移动",
                "1299.HK": "友邦保险",
                "2800.HK": "盈富基金",
                "0388.HK": "香港交易所",
                "0939.HK": "建设银行",
                "1398.HK": "工商银行",
                "3988.HK": "中国银行",
                "2318.HK": "中国平安",
                "2628.HK": "中国人寿",
                "3690.HK": "美团",
                "1810.HK": "小米集团",
                "9618.HK": "京东",
                "2382.HK": "舜宇光学",
                "1928.HK": "金沙中国",

                # 美股
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com Inc.",
                "TSLA": "Tesla Inc.",
                "META": "Meta Platforms",
                "NVDA": "NVIDIA Corporation",
                "JPM": "JPMorgan Chase",
                "V": "Visa Inc.",
                "JNJ": "Johnson & Johnson",

                # 加密货币
                "BTC-USD": "Bitcoin",
                "ETH-USD": "Ethereum",
                "BNB-USD": "Binance Coin",
                "ADA-USD": "Cardano",
                "SOL-USD": "Solana"
            }

            results = []
            query_lower = query.lower()

            for symbol, name in common_symbols.items():
                if (query_lower in symbol.lower() or
                    query_lower in name.lower()):
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "exchange": self._get_exchange(symbol)
                    })

            return results

        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []

    def _get_exchange(self, symbol: str) -> str:
        """获取交易所信息"""
        if ".HK" in symbol:
            return "HKEX"
        elif "-USD" in symbol:
            return "CRYPTO"
        else:
            return "NASDAQ"

    async def get_market_status(self) -> Dict[str, Any]:
        """
        获取市场状态

        Returns:
            Dict[str, Any]: 市场状态信息
        """
        try:
            # 检查主要市场状态
            markets = {
                "HK": {"symbol": "2800.HK", "name": "香港市场"},
                "US": {"symbol": "SPY", "name": "美国市场"},
                "CRYPTO": {"symbol": "BTC-USD", "name": "加密货币市场"}
            }

            market_status = {}

            for market_code, market_info in markets.items():
                try:
                    ticker = yf.Ticker(market_info["symbol"])
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, ticker.info.get, 'marketState'
                    )

                    market_status[market_code] = {
                        "name": market_info["name"],
                        "status": "open" if info == 'REGULAR' else "closed",
                        "symbol": market_info["symbol"],
                        "last_update": datetime.now().isoformat()
                    }
                except Exception as e:
                    market_status[market_code] = {
                        "name": market_info["name"],
                        "status": "error",
                        "error": str(e)
                    }

            return market_status

        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {}


# 使用示例
async def main():
    """示例用法"""
    # 创建配置
    config = AdapterConfig(
        source_type=DataSourceType.YAHOO_FINANCE,
        source_name="Yahoo Finance",
        cache_enabled=True,
        cache_ttl=300
    )

    # 创建适配器
    async with YahooFinanceAdapter(config) as adapter:
        # 测试连接
        if await adapter.connect():
            print("✓ Connected to Yahoo Finance")

            # 获取腾讯数据
            data = await adapter.fetch_data("0700.HK", days=30)
            print(f"✓ Fetched {len(data)} data points for 0700.HK")

            # 获取实时数据
            realtime = await adapter.get_realtime_data("0700.HK")
            if realtime:
                print(f"✓ Current price: {realtime.close}")

            # 批量获取
            symbols = ["0700.HK", "0388.HK", "0939.HK"]
            multi_data = await adapter.get_multiple_symbols(symbols, days=7)
            print(f"✓ Batch fetched data for {len(multi_data)} symbols")

        else:
            print("✗ Failed to connect")

if __name__ == "__main__":
    asyncio.run(main())
