"""
Alpha Vantage商品数据适配器 - 使用Alpha Vantage API获取真实商品数据

Alpha Vantage提供免费的大宗商品数据API
支持黄金、白银、原油等商品期货数据
需要API密钥 (免费层支持500次/天)
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import asyncio
import os
import logging

from .base_adapter import BaseAdapter


class AlphaVantageCommodityAdapter(BaseAdapter):
    """Alpha Vantage商品数据适配器 - 真实数据源"""

    # 支持的商品代码
    SUPPORTED_SYMBOLS = {
        'GOLD': 'XAU/USD - 黄金兑美元',
        'SILVER': 'XAG/USD - 白银兑美元',
        'OIL_WTI': 'WTI - WTI原油',
        'OIL_BRENT': 'BRENT - 布伦特原油',
        'COPPER': 'COPPER - 铜期货',
        'PLATINUM': 'XPT/USD - 铂金兑美元',
        'PALLADIUM': 'XPD/USD - 钯金兑美元',
        'NATURAL_GAS': 'NATGAS/USD - 天然气',
        'WHEAT': 'WHEAT - 小麦期货',
        'CORN': 'CORN - 玉米期货',
        'COFFEE': 'COFFEE - 咖啡期货',
        'SUGAR': 'SUGAR - 糖期货',
        'COTTON': 'COTTON - 棉花期货',
        'COCOA': 'COCOA - 可可期货',
        'LIVE_CATTLE': 'LIVECATTLE - 活牛期货',
        'LEAN_HOGS': 'LEANHOGS - 瘦肉猪期货',
    }

    # Alpha Vantage到内部代码的映射
    ALPHA_VANTAGE_SYMBOLS = {
        'GOLD': 'XAUUSD',
        'SILVER': 'XAGUSD',
        'OIL_WTI': 'WTI',
        'OIL_BRENT': 'BRENT',
        'COPPER': 'COPPER',
        'PLATINUM': 'XPTUSD',
        'PALLADIUM': 'XPDUSD',
        'NATURAL_GAS': 'NATGASUSD',
        'WHEAT': 'WHEAT',
        'CORN': 'CORN',
        'COFFEE': 'COFFEE',
        'SUGAR': 'SUGAR',
        'COTTON': 'COTTON',
        'COCOA': 'COCOA',
        'LIVE_CATTLE': 'LIVECATTLE',
        'LEAN_HOGS': 'LEANHOGS',
    }

    def __init__(self):
        super().__init__("AlphaVantageCommodityAdapter")
        # 从环境变量获取API密钥
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'
        self.rate_limit_delay = 12  # 免费层限制：5次/分钟，所以间隔12秒

    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取商品真实历史数据

        Args:
            symbol: 商品代码 (GOLD, OIL_WTI等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

            # 获取Alpha Vantage symbol
            av_symbol = self._get_av_symbol(symbol)

            # 构建请求参数
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': av_symbol,
                'apikey': self.api_key,
                'outputsize': 'full'
            }

            self.logger.info(f"Alpha Vantage API请求: {av_symbol}")

            # 发送请求
            async with aiohttp.ClientSession() as session:
                # 遵守API限制
                await asyncio.sleep(self.rate_limit_delay)

                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 检查是否有错误信息
                        if 'Error Message' in data:
                            raise Exception(f"Alpha Vantage API错误: {data['Error Message']}")
                        if 'Note' in data:
                            raise Exception(f"API调用频率超限: {data['Note']}")

                        return self._parse_response(data, symbol)
                    else:
                        error_msg = f"API请求失败，状态码: {response.status}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)

        except aiohttp.ClientError as e:
            error_msg = f"网络请求失败: {e}"
            self.logger.error(error_msg)
            await self.handle_error(e)
            raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            await self.handle_error(e)
            raise Exception(f"无法获取{symbol}的真实商品数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取实时商品价格数据

        Args:
            symbol: 商品代码

        Returns:
            实时价格数据

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            # 获取最新一天的数据作为实时数据
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

            # 尝试获取最近3天的数据
            data = await self.fetch_data(symbol, yesterday, today)

            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']) if latest['Volume'] else 0,
                    'timestamp': latest['Date'].isoformat(),
                    'source': 'alpha-vantage'
                }
            else:
                raise Exception("未能获取到实时数据")

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _get_av_symbol(self, symbol: str) -> str:
        """
        获取Alpha Vantage symbol

        Args:
            symbol: 内部symbol

        Returns:
            Alpha Vantage symbol
        """
        if symbol in self.ALPHA_VANTAGE_SYMBOLS:
            return self.ALPHA_VANTAGE_SYMBOLS[symbol]
        else:
            # 尝试自动生成symbol
            if symbol.upper() in ['GOLD', 'SILVER', 'OIL_WTI', 'OIL_BRENT']:
                base_mapping = {
                    'GOLD': 'XAUUSD',
                    'SILVER': 'XAGUSD',
                    'OIL_WTI': 'WTI',
                    'OIL_BRENT': 'BRENT'
                }
                return base_mapping.get(symbol.upper(), symbol.upper())
            else:
                raise ValueError(f"不支持的商品symbol: {symbol}")

    def _parse_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        """
        解析Alpha Vantage API响应

        Args:
            data: API响应数据
            symbol: 数据符号

        Returns:
            解析后的DataFrame

        Raises:
            Exception: 当解析失败时
        """
        try:
            # 查找时间序列数据
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break

            if not time_series_key:
                raise Exception(f"响应中没有找到时间序列数据")

            time_series = data[time_series_key]

            if not time_series:
                raise Exception("时间序列数据为空")

            all_data = []
            for date_str, values in time_series.items():
                try:
                    all_data.append({
                        'Date': pd.to_datetime(date_str),
                        'Open': float(values['1. open']),
                        'High': float(values['2. high']),
                        'Low': float(values['3. low']),
                        'Close': float(values['4. close']),
                        'Volume': int(values['5. volume']) if values['5. volume'] else 0
                    })
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"跳过无效记录: {date_str}, 错误: {e}")
                    continue

            if not all_data:
                raise Exception("没有有效的记录")

            df = pd.DataFrame(all_data)
            df = self.normalize_data(df)

            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条{symbol}真实数据（Alpha Vantage）")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            raise Exception(f"解析{symbol}数据失败: {e}")

    async def calculate_commodity_correlation(
        self,
        commodity_symbol: str,
        stock_symbol: str,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        计算商品与股票的真实相关性

        Args:
            commodity_symbol: 商品代码
            stock_symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            window: 滚动窗口

        Returns:
            包含相关性数据的DataFrame

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"计算{commodity_symbol}与{stock_symbol}的相关性")

            # 获取商品真实数据
            commodity_data = await self.fetch_data(commodity_symbol, start_date, end_date)
            commodity_returns = commodity_data['Close'].pct_change()

            # TODO: 需要接入真实的股票数据（使用HKEX适配器）
            raise NotImplementedError(
                "股票数据获取功能尚未完全实现，请使用HKEXAdapter获取港股数据"
            )

        except NotImplementedError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            raise Exception(f"计算{commodity_symbol}与{stock_symbol}相关性失败: {e}")

    def get_supported_symbols(self) -> Dict:
        """
        获取支持的symbol列表

        Returns:
            支持的symbol字典
        """
        return self.SUPPORTED_SYMBOLS

    async def get_commodity_info(self, symbol: str) -> Dict:
        """
        获取商品信息

        Args:
            symbol: 商品代码

        Returns:
            商品信息
        """
        try:
            av_symbol = self._get_av_symbol(symbol)

            params = {
                'function': 'OVERVIEW',
                'symbol': av_symbol,
                'apikey': self.api_key
            }

            async with aiohttp.ClientSession() as session:
                await asyncio.sleep(self.rate_limit_delay)
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        return {
                            'symbol': symbol,
                            'av_symbol': av_symbol,
                            'name': data.get('Name', 'N/A'),
                            'description': data.get('Description', 'N/A'),
                            'currency': data.get('Currency', 'USD'),
                            'exchange': data.get('Exchange', 'N/A'),
                            'api_source': 'Alpha Vantage'
                        }

            return {
                'symbol': symbol,
                'av_symbol': av_symbol,
                'name': 'Unknown',
                'description': 'N/A',
                'currency': 'USD',
                'exchange': 'N/A',
                'api_source': 'Alpha Vantage'
            }

        except Exception as e:
            self.logger.warning(f"获取{symbol}信息失败: {e}")
            return {
                'symbol': symbol,
                'av_symbol': 'N/A',
                'name': 'Unknown',
                'description': 'N/A',
                'currency': 'USD',
                'exchange': 'N/A',
                'api_source': 'Alpha Vantage'
            }
