"""
FX Yahoo Finance适配器 (增强版) - 优化错误处理

增强功能:
1. 自动重试机制 (指数退避)
2. 详细错误分类和日志
3. 集成缓存系统
4. 严格数据质量检查
5. 故障转移机制
6. 网络超时处理
7. API限制检测
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import logging
import asyncio
import time
import random
from functools import wraps

from .base_adapter import BaseAdapter
from ..cache.caching import get_cache_manager


class FXYahooAdapterError(Exception):
    """FX适配器基础异常"""
    pass


class NetworkError(FXYahooAdapterError):
    """网络错误"""
    pass


class DataValidationError(FXYahooAdapterError):
    """数据验证错误"""
    pass


class SymbolNotSupportedError(FXYahooAdapterError):
    """不支持的符号错误"""
    pass


class RateLimitError(FXYahooAdapterError):
    """API速率限制错误"""
    pass


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """重试装饰器 - 指数退避算法"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except (NetworkError, asyncio.TimeoutError) as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        # 指数退避 + 随机抖动
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        jitter = delay * 0.1 * random.random()
                        total_delay = delay + jitter

                        self.logger.warning(
                            f"网络错误，第{attempt + 1}次重试失败: {e}，"
                            f"{total_delay:.2f}秒后重试..."
                        )
                        await asyncio.sleep(total_delay)
                    else:
                        self.logger.error(f"网络错误，已达到最大重试次数 ({max_retries})")
                except (DataValidationError, SymbolNotSupportedError) as e:
                    # 这些错误不需要重试
                    last_exception = e
                    self.logger.error(f"致命错误: {e}")
                    break
                except Exception as e:
                    # 未知错误，记录并重试
                    last_exception = e
                    self.logger.warning(f"未知错误，第{attempt + 1}次重试: {e}")

                    if attempt < max_retries - 1:
                        await asyncio.sleep(base_delay)

            # 所有重试都失败了
            raise last_exception

        return wrapper
    return decorator


class FXYahooAdapterEnhanced(BaseAdapter):
    """FX适配器增强版 - 优化错误处理"""

    SUPPORTED_SYMBOLS = {
        'USD_CNH': 'CNHY=X - 美元兑人民币',
        'EUR_USD': 'EURUSD=X - 欧元兑美元',
        'GBP_USD': 'GBPUSD=X - 英镑兑美元',
        'USD_JPY': 'USDJPY=X - 美元兑日元',
        'AUD_USD': 'AUDUSD=X - 澳元兑美元',
        'USD_CHF': 'USDCHF=X - 美元兑瑞士法郎',
        'USD_CAD': 'USDCAD=X - 美元兑加元',
        'NZD_USD': 'NZDUSD=X - 纽元兑美元',
    }

    # 备用symbol映射 (当主symbol失败时尝试)
    BACKUP_SYMBOL_MAPPING = {
        'USD_CNH': ['USDCNY=X', 'CNHY=X', 'CNH=X'],
        'EUR_USD': ['EURUSD=X', 'EUR=X'],
        'GBP_USD': ['GBPUSD=X', 'GBP=X'],
        'USD_JPY': ['USDJPY=X', 'JPY=X'],
        'AUD_USD': ['AUDUSD=X', 'AUD=X'],
        'USD_CHF': ['USDCHF=X', 'CHF=X'],
        'USD_CAD': ['USDCAD=X', 'CAD=X'],
        'NZD_USD': ['NZDUSD=X', 'NZD=X'],
    }

    def __init__(self):
        super().__init__("FXYahooAdapterEnhanced")
        # Yahoo Finance symbol映射
        self.symbol_mapping = {
            'USD_CNH': 'USDCNY=X',
            'EUR_USD': 'EURUSD=X',
            'GBP_USD': 'GBPUSD=X',
            'USD_JPY': 'USDJPY=X',
            'AUD_USD': 'AUDUSD=X',
            'USD_CHF': 'USDCHF=X',
            'USD_CAD': 'USDCAD=X',
            'NZD_USD': 'NZDUSD=X',
        }

        # 初始化缓存管理器
        self.cache_manager = get_cache_manager()

        # 数据质量阈值
        self.max_missing_data_ratio = 0.1  # 最大缺失数据比例
        self.min_data_points = 5  # 最少数据点要求
        self.max_price_change_ratio = 0.5  # 单日最大价格变化比例 (50%)

    @retry_on_failure(max_retries=3, base_delay=1.0)
    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取FX真实历史数据 (增强版)

        Args:
            symbol: 货币对 (USD_CNH, EUR_USD等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            use_cache: 是否使用缓存
            **kwargs: 额外参数

        Returns:
            DataFrame with OHLCV data

        Raises:
            FXYahooAdapterError: 当无法获取真实数据时
        """
        cache_key = f"fx_data:{symbol}:{start_date}:{end_date}"

        # 尝试从缓存获取
        if use_cache:
            cached_data = self.cache_manager.get(cache_key, namespace='fx')
            if cached_data is not None:
                self.logger.info(f"缓存命中: {symbol}")
                return cached_data

        self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

        # 尝试主symbol和备用symbol
        symbols_to_try = self._get_symbols_to_try(symbol)
        last_error = None

        for yf_symbol in symbols_to_try:
            try:
                data = await self._fetch_with_yf(yf_symbol, start_date, end_date)
                df = self._process_raw_data(data, symbol)

                # 严格数据质量检查
                self._validate_data_quality(df, symbol)

                # 设置缓存
                if use_cache:
                    self.cache_manager.set(
                        cache_key,
                        df,
                        namespace='fx',
                        ttl=3600  # 1小时缓存
                    )

                self.logger.info(
                    f"成功获取{len(df)}条{symbol}真实数据 (使用{yf_symbol})"
                )
                return df

            except Exception as e:
                last_error = e
                self.logger.warning(f"尝试{yf_symbol}失败: {e}")
                continue

        # 所有symbol都失败了
        error_msg = (
            f"无法获取{symbol}的真实FX数据。已尝试所有可用symbol: {symbols_to_try}。"
            f"最后错误: {last_error}"
        )
        self.logger.error(error_msg)
        raise FXYahooAdapterError(error_msg)

    async def _fetch_with_yf(self, yf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """使用yfinance获取数据"""
        try:
            # 创建ticker对象
            ticker = yf.Ticker(yf_symbol)

            # 设置超时 (使用asyncio.wait_for)
            data = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: ticker.history(
                        start=start_date,
                        end=end_date,
                        interval='1d',
                        auto_adjust=True,
                        prepost=True
                    )
                ),
                timeout=30  # 30秒超时
            )

            if data.empty:
                raise DataValidationError(f"Yahoo Finance返回空数据: {yf_symbol}")

            return data

        except asyncio.TimeoutError:
            raise NetworkError(f"Yahoo Finance请求超时: {yf_symbol}")
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                raise RateLimitError(f"API速率限制: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError(f"网络错误: {e}")
            else:
                raise FXYahooAdapterError(f"Yahoo Finance错误: {e}")

    def _process_raw_data(self, data, symbol: str) -> pd.DataFrame:
        """处理原始数据"""
        try:
            # 转换为标准OHLCV格式
            df = pd.DataFrame({
                'Date': data.index,
                'Open': data['Open'],
                'High': data['High'],
                'Low': data['Low'],
                'Close': data['Close'],
                'Volume': data['Volume'].fillna(0)
            })

            # 重置索引
            df = df.reset_index(drop=True)

            # 数据类型转换和清洗
            df = df.astype({
                'Open': 'float64',
                'High': 'float64',
                'Low': 'float64',
                'Close': 'float64',
                'Volume': 'int64'
            })

            return df

        except Exception as e:
            raise DataValidationError(f"数据处理失败: {e}")

    def _validate_data_quality(self, df: pd.DataFrame, symbol: str) -> None:
        """严格的数据质量检查"""
        if df.empty:
            raise DataValidationError(f"数据为空: {symbol}")

        # 检查最少数据点
        if len(df) < self.min_data_points:
            raise DataValidationError(
                f"数据点不足: {symbol}，需要至少{self.min_data_points}个，实际{len(df)}个"
            )

        # 检查缺失值
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_ratio > self.max_missing_data_ratio:
            raise DataValidationError(
                f"缺失数据过多: {symbol}，缺失比例{missing_ratio:.2%}，"
                f"最大允许{self.max_missing_data_ratio:.2%}"
            )

        # 检查异常价格变化
        df['price_change'] = df['Close'].pct_change().abs()
        max_change = df['price_change'].max()

        if max_change > self.max_price_change_ratio:
            self.logger.warning(
                f"检测到异常价格变化: {symbol}，最大变化{max_change:.2%}，"
                f"可能存在数据错误"
            )

        # 检查价格合理性
        for col in ['Open', 'High', 'Low', 'Close']:
            if (df[col] <= 0).any():
                raise DataValidationError(f"存在非正价格: {symbol}")

            # 检查极值
            if df[col].isna().any():
                raise DataValidationError(f"存在空值: {symbol}.{col}")

        self.logger.debug(f"数据质量检查通过: {symbol}")

    def _get_symbols_to_try(self, symbol: str) -> List[str]:
        """获取要尝试的symbol列表"""
        # 主symbol
        primary_symbol = self._get_yf_symbol(symbol)

        # 备用symbols
        backup_symbols = self.BACKUP_SYMBOL_MAPPING.get(symbol, [])

        # 组合并去重
        all_symbols = [primary_symbol] + [
            s for s in backup_symbols if s != primary_symbol
        ]

        return all_symbols

    def _get_yf_symbol(self, symbol: str) -> str:
        """获取Yahoo Finance symbol"""
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol]
        else:
            # 尝试自动生成symbol
            if '_' in symbol:
                base, quote = symbol.split('_')
                return f"{base}{quote}=X"
            else:
                raise SymbolNotSupportedError(f"不支持的FX symbol: {symbol}")

    async def get_realtime_data(
        self,
        symbol: str,
        use_cache: bool = True,
        cache_ttl: int = 60,
        **kwargs
    ) -> Dict:
        """
        获取FX实时数据 (增强版)

        Args:
            symbol: 货币对
            use_cache: 是否使用缓存
            cache_ttl: 缓存TTL (秒)
            **kwargs: 额外参数

        Returns:
            实时汇率数据

        Raises:
            FXYahooAdapterError: 当无法获取真实数据时
        """
        cache_key = f"fx_realtime:{symbol}"

        # 尝试从缓存获取
        if use_cache:
            cached_data = self.cache_manager.get(cache_key, namespace='fx')
            if cached_data is not None:
                self.logger.info(f"实时数据缓存命中: {symbol}")
                return cached_data

        # 检查市场是否开放 (FX市场周末关闭)
        if self._is_weekend():
            self.logger.warning(f"周末市场关闭，使用最新数据: {symbol}")

        symbols_to_try = self._get_symbols_to_try(symbol)
        last_error = None

        for yf_symbol in symbols_to_try:
            try:
                data = await self._fetch_realtime_with_yf(yf_symbol)

                result = {
                    'symbol': symbol,
                    'yf_symbol': yf_symbol,
                    'rate': float(data['rate']),
                    'open': float(data['open']),
                    'high': float(data['high']),
                    'low': float(data['low']),
                    'volume': int(data['volume']) if data['volume'] > 0 else 0,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yahoo-finance',
                    'is_realtime': not self._is_weekend(),
                    'data_freshness': data.get('data_freshness', 'unknown')
                }

                # 设置缓存
                if use_cache:
                    self.cache_manager.set(
                        cache_key,
                        result,
                        namespace='fx',
                        ttl=cache_ttl
                    )

                return result

            except Exception as e:
                last_error = e
                self.logger.warning(f"实时数据获取失败 {yf_symbol}: {e}")
                continue

        error_msg = f"无法获取{symbol}的实时数据，已尝试所有symbol"
        self.logger.error(error_msg)
        raise FXYahooAdapterError(f"{error_msg}。最后错误: {last_error}")

    async def _fetch_realtime_with_yf(self, yf_symbol: str) -> Dict:
        """使用yfinance获取实时数据"""
        try:
            ticker = yf.Ticker(yf_symbol)

            # 获取实时数据
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )

            hist = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.history(period='5d', interval='1d')
            )

            if hist.empty:
                raise DataValidationError(f"无历史数据: {yf_symbol}")

            latest = hist.iloc[-1]

            return {
                'rate': latest['Close'],
                'open': latest['Open'],
                'high': hist['High'].max(),
                'low': hist['Low'].min(),
                'volume': latest['Volume'] if not pd.isna(latest['Volume']) else 0,
                'data_freshness': 'daily'  # FX通常是日线数据
            }

        except Exception as e:
            raise FXYahooAdapterError(f"实时数据获取错误: {e}")

    def _is_weekend(self) -> bool:
        """检查是否为周末"""
        today = datetime.now().weekday()
        return today >= 5  # 5=周六, 6=周日

    async def health_check(self) -> Dict:
        """
        健康检查

        Returns:
            健康状态字典
        """
        try:
            # 尝试获取一个常用symbol的数据
            test_data = await self.fetch_data('USD_CNH', '2024-01-01', '2024-01-05', use_cache=False)

            return {
                'status': 'healthy',
                'adapter': self.name,
                'test_symbol': 'USD_CNH',
                'test_result': 'success',
                'data_points': len(test_data),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'adapter': self.name,
                'test_symbol': 'USD_CNH',
                'test_result': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_supported_symbols(self) -> Dict:
        """获取支持的symbol列表"""
        return self.SUPPORTED_SYMBOLS

    async def get_currency_info(self, symbol: str) -> Dict:
        """获取货币对信息 (增强版)"""
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)

            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )

            return {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'name': info.get('longName', 'N/A'),
                'currency': info.get('currency', 'N/A'),
                'exchange': info.get('exchange', 'N/A'),
                'timezone': info.get('exchangeTimezoneName', 'N/A'),
                'is_trading_now': not self._is_weekend(),
                'source': 'yahoo-finance'
            }

        except Exception as e:
            self.logger.warning(f"获取{symbol}信息失败: {e}")
            return {
                'symbol': symbol,
                'yf_symbol': 'N/A',
                'name': 'Unknown',
                'currency': 'N/A',
                'exchange': 'N/A',
                'timezone': 'N/A',
                'is_trading_now': False,
                'source': 'yahoo-finance'
            }

    async def clear_cache(self) -> None:
        """清空缓存"""
        self.cache_manager.clear(namespace='fx')
        self.logger.info("FX缓存已清空")
