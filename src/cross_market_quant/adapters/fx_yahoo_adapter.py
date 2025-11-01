"""
FX Yahoo Finance适配器 - 使用Yahoo Finance获取真实FX数据

Yahoo Finance免费提供FX数据，支持多种货币对
零成本，高可靠性
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import logging

from .base_adapter import BaseAdapter


class FXYahooAdapter(BaseAdapter):
    """FX适配器 - 使用Yahoo Finance (真实数据源)"""

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

    def __init__(self):
        super().__init__("FXYahooAdapter")
        # Yahoo Finance symbol映射 (已验证可工作)
        self.symbol_mapping = {
            'USD_CNH': 'USDCNY=X',  # 使用USDCNY而不是CNHY
            'EUR_USD': 'EURUSD=X',
            'GBP_USD': 'GBPUSD=X',
            'USD_JPY': 'USDJPY=X',
            'AUD_USD': 'AUDUSD=X',
            'USD_CHF': 'USDCHF=X',
            'USD_CAD': 'USDCAD=X',
            'NZD_USD': 'NZDUSD=X',
        }

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

            # 获取Yahoo Finance symbol
            yf_symbol = self._get_yf_symbol(symbol)

            # 创建ticker对象
            ticker = yf.Ticker(yf_symbol)

            # 获取历史数据
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval='1d',
                auto_adjust=True,
                prepost=True
            )

            if data.empty:
                raise Exception(f"未能获取到{symbol}的Yahoo Finance数据")

            # 转换为标准OHLCV格式
            df = pd.DataFrame({
                'Date': data.index,
                'Open': data['Open'],
                'High': data['High'],
                'Low': data['Low'],
                'Close': data['Close'],
                'Volume': data['Volume'].fillna(0)  # FX通常没有成交量，填充为0
            })

            # 重置索引
            df = df.reset_index(drop=True)

            # 数据验证
            if self.validate_data(df):
                self.logger.info(f"成功获取{len(df)}条{symbol}真实数据（Yahoo Finance）")
                return df
            else:
                raise Exception(f"{symbol}数据验证失败")

        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            await self.handle_error(e)
            raise Exception(f"无法获取{symbol}的真实FX数据: {e}")

    async def get_realtime_data(self, symbol: str, **kwargs) -> Dict:
        """
        获取FX实时数据

        Args:
            symbol: 货币对

        Returns:
            实时汇率数据

        Raises:
            Exception: 当无法获取真实数据时
        """
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)

            # 获取实时数据
            info = ticker.info
            hist = ticker.history(period='1d', interval='1m')

            if hist.empty:
                raise Exception(f"未能获取{symbol}的实时数据")

            latest = hist.iloc[-1]

            return {
                'symbol': symbol,
                'rate': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo-finance'
            }

        except Exception as e:
            error_msg = f"获取{symbol}实时数据失败: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _get_yf_symbol(self, symbol: str) -> str:
        """
        获取Yahoo Finance symbol

        Args:
            symbol: 内部symbol

        Returns:
            Yahoo Finance symbol
        """
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol]
        else:
            # 尝试自动生成symbol
            if '_' in symbol:
                base, quote = symbol.split('_')
                return f"{base}{quote}=X"
            else:
                raise ValueError(f"不支持的FX symbol: {symbol}")

    def get_supported_symbols(self) -> Dict:
        """
        获取支持的symbol列表

        Returns:
            支持的symbol字典
        """
        return self.SUPPORTED_SYMBOLS

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

            # TODO: 需要接入真实的港股数据（使用HKEX适配器）
            # 这里先简化处理
            raise NotImplementedError(
                f"股票数据获取功能尚未完全实现，请使用HKEXAdapter获取港股数据"
            )

        except NotImplementedError as e:
            self.logger.warning(str(e))
            raise
        except Exception as e:
            self.logger.error(f"计算相关性失败: {e}")
            raise Exception(f"计算{fx_symbol}与{stock_symbol}相关性失败: {e}")

    def get_currency_info(self, symbol: str) -> Dict:
        """
        获取货币对信息

        Args:
            symbol: 货币对

        Returns:
            货币对信息
        """
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info

            return {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'name': info.get('longName', 'N/A'),
                'currency': info.get('currency', 'N/A'),
                'exchange': info.get('exchange', 'N/A'),
                'timezone': info.get('exchangeTimezoneName', 'N/A')
            }

        except Exception as e:
            self.logger.warning(f"获取{symbol}信息失败: {e}")
            return {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'name': 'Unknown',
                'currency': 'N/A',
                'exchange': 'N/A',
                'timezone': 'N/A'
            }
