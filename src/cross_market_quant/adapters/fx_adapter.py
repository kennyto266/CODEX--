"""
FX数据适配器 - 外汇数据获取

使用统一数据API端点获取真实的FX数据
支持USD/CNH、EUR/USD等汇率数据
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import asyncio

from .base_adapter import BaseAdapter


class FXAdapter(BaseAdapter):
    """外汇数据适配器 - 仅使用真实数据源"""

    SUPPORTED_SYMBOLS = {
        'USD_CNH': 'USD/CNH - 美元兑人民币',
        'EUR_USD': 'EUR/USD - 欧元兑美元',
        'GBP_USD': 'GBP/USD - 英镑兑美元',
        'USD_JPY': 'USD/JPY - 美元兑日元',
        'AUD_USD': 'AUD/USD - 澳元兑美元',
    }

    def __init__(self):
        super().__init__("FXAdapter")
        # 使用统一的数据API端点
        self.base_url = "http://18.180.162.113:9191"
        self.endpoint = "/inst/getInst"

    async def fetch_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        获取FX真实历史数据

        Args:
            symbol: 货币对 (USD_CNH, EUR_USD等)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            self.logger.info(f"获取{symbol}真实数据，从{start_date}到{end_date}")

            # 计算天数
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days

            # 使用统一数据API端点
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{self.endpoint}"
                params = {
                    "symbol": symbol.lower(),
                    "duration": duration_days
                }

                self.logger.info(f"API请求: {url}?symbol={symbol.lower()}&duration={duration_days}")

                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
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
            raise Exception(f"无法获取{symbol}的真实数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取实时汇率真实数据

        Args:
            symbol: 货币对

        Returns:
            实时汇率数据

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            # 获取最新一天的数据作为实时数据
            today = datetime.now().strftime('%Y-%m-%d')
            data = await self.fetch_data(symbol, today, today)

            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'rate': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']) if latest['Volume'] else 0,
                    'timestamp': latest['Date'].isoformat(),
                    'source': 'unified-api'
                }
            else:
                raise Exception("未能获取到实时数据")

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _parse_response(self, data: Dict, symbol: str) -> pd.DataFrame:
        """
        解析统一API响应

        Args:
            data: API响应数据
            symbol: 数据符号

        Returns:
            解析后的DataFrame

        Raises:
            Exception: 当解析失败时
        """
        try:
            if not isinstance(data, dict):
                raise Exception(f"响应数据格式错误，期望字典，得到: {type(data)}")

            # 尝试多种可能的响应格式
            records = None
            if 'data' in data:
                records = data['data']
            elif 'results' in data:
                records = data['results']
            elif isinstance(data, list):
                records = data
            else:
                raise Exception(f"无法找到数据记录，响应键: {list(data.keys())}")

            if not records or len(records) == 0:
                raise Exception("响应数据为空")

            all_data = []
            for record in records:
                try:
                    all_data.append({
                        'Date': pd.to_datetime(record.get('date', record.get('Date'))),
                        'Open': float(record.get('open', record.get('Open', 0))),
                        'High': float(record.get('high', record.get('High', 0))),
                        'Low': float(record.get('low', record.get('Low', 0))),
                        'Close': float(record.get('close', record.get('Close', 0))),
                        'Volume': int(record.get('volume', record.get('Volume', 0)))
                    })
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"跳过无效记录: {record}, 错误: {e}")
                    continue

            if not all_data:
                raise Exception("没有有效的记录")

            df = pd.DataFrame(all_data)
            df = self.normalize_data(df)

            if self.validate_data(df):
                self.logger.info(f"成功解析{len(df)}条{symbol}真实数据")
                return df
            else:
                raise Exception("数据验证失败")

        except Exception as e:
            self.logger.error(f"解析响应失败: {e}")
            raise Exception(f"解析{symbol}数据失败: {e}")

    def _parse_symbol(self, symbol: str) -> tuple:
        """
        解析货币对符号

        Args:
            symbol: 货币对符号 (如USD_CNH)

        Returns:
            (base_currency, quote_currency)
        """
        if '_' in symbol:
            return symbol.split('_')
        else:
            # 默认USD_CNH
            return 'USD', 'CNH'

    async def get_cross_market_correlation(
        self,
        fx_symbol: str,
        stock_symbol: str,
        start_date: str,
        end_date: str,
        window: int = 20
    ) -> pd.DataFrame:
        """
        计算FX与股票的真实相关性

        Args:
            fx_symbol: 货币对
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
            self.logger.info(f"计算{fx_symbol}与{stock_symbol}的相关性")

            # 获取FX真实数据
            fx_data = await self.fetch_data(fx_symbol, start_date, end_date)
            fx_returns = fx_data['Close'].pct_change()

            # TODO: 需要接入真实的股票数据API
            # 目前使用真实FX数据和模拟股票数据进行演示
            # 实际使用时应该替换为真实的股票数据
            raise NotImplementedError(
                "股票数据获取功能尚未实现，请接入真实的股票数据API"
            )

        except NotImplementedError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            raise Exception(f"计算{fx_symbol}与{stock_symbol}相关性失败: {e}")
