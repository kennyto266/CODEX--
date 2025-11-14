"""
統一股票數據適配器
整合 AlphaVantageAdapter 和 YahooFinanceAdapter
支援股票、外匯和加密貨幣數據
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf

from .unified_base_adapter import UnifiedBaseAdapter

class UnifiedStockDataAdapter(UnifiedBaseAdapter):
    """
    統一股票數據適配器
    支援多個數據源：Alpha Vantage、Yahoo Finance等
    """

    SUPPORTED_SOURCES = ['alpha_vantage', 'yahoo', 'iex', 'finnhub']

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.api_keys = {
            'alpha_vantage': self.config.get('alpha_vantage_key'),
            'iex': self.config.get('iex_key'),
            'finnhub': self.config.get('finnhub_key')
        }
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取HTTP會話"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """關閉會話"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _fetch_yahoo_stock(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """從Yahoo Finance獲取股票數據"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                raise ValueError(f"No data found for {symbol}")

            latest = hist.iloc[-1]
            return {
                'symbol': symbol,
                'name': ticker.info.get('longName', symbol),
                'current_price': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']),
                'timestamp': latest.name.isoformat(),
                'source': 'yahoo',
                'data': hist.to_dict('records')
            }
        except Exception as e:
            raise Exception(f"Yahoo Finance error: {str(e)}")

    async def _fetch_alpha_vantage_stock(self, symbol: str) -> Dict[str, Any]:
        """從Alpha Vantage獲取股票數據"""
        api_key = self.api_keys.get('alpha_vantage')
        if not api_key:
            raise ValueError("Alpha Vantage API key not configured")

        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

        session = await self._get_session()
        async with session.get(url) as response:
            data = await response.json()

            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if "Note" in data:
                raise ValueError(f"API Limit: {data['Note']}")

            quote = data.get("Global Quote", {})
            if not quote:
                raise ValueError("No data returned")

            return {
                'symbol': symbol,
                'name': symbol,
                'current_price': float(quote.get("05. price", 0)),
                'open': float(quote.get("02. open", 0)),
                'high': float(quote.get("03. high", 0)),
                'low': float(quote.get("04. low", 0)),
                'volume': int(quote.get("06. volume", 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'alpha_vantage'
            }

    async def get_stock_data(self, symbol: str, source: str = "yahoo", period: str = "1y") -> Dict[str, Any]:
        """
        獲取股票數據

        Args:
            symbol: 股票代碼 (e.g., "AAPL", "0700.HK")
            source: 數據源 ("yahoo", "alpha_vantage")
            period: 時間期間 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")

        Returns:
            股票數據字典
        """
        params = {
            'symbol': symbol,
            'source': source,
            'period': period
        }

        if source == "yahoo":
            data = await self._fetch_yahoo_stock(symbol, period)
        elif source == "alpha_vantage":
            data = await self._fetch_alpha_vantage_stock(symbol)
        else:
            raise ValueError(f"Unsupported source: {source}. Supported: {self.SUPPORTED_SOURCES}")

        return {
            'success': True,
            'data': data,
            'source': source,
            'timestamp': datetime.now().isoformat()
        }

    async def get_fx_data(self, from_currency: str, to_currency: str, source: str = "yahoo") -> Dict[str, Any]:
        """
        獲取外匯數據

        Args:
            from_currency: 源貨幣 (e.g., "USD")
            to_currency: 目標貨幣 (e.g., "HKD")
            source: 數據源

        Returns:
            外匯數據字典
        """
        pair = f"{from_currency}{to_currency}=X"
        params = {
            'symbol': pair,
            'source': source
        }

        if source == "yahoo":
            try:
                ticker = yf.Ticker(pair)
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise ValueError(f"No FX data for {pair}")

                latest = hist.iloc[-1]
                return {
                    'success': True,
                    'pair': pair,
                    'rate': float(latest['Close']),
                    'timestamp': latest.name.isoformat(),
                    'source': 'yahoo'
                }
            except Exception as e:
                raise Exception(f"Yahoo FX error: {str(e)}")
        else:
            raise ValueError(f"FX data only supported from Yahoo in this implementation")

    async def get_crypto_data(self, symbol: str, exchange: str = "USD", source: str = "yahoo") -> Dict[str, Any]:
        """
        獲取加密貨幣數據

        Args:
            symbol: 加密貨幣代碼 (e.g., "BTC")
            exchange: 計價貨幣 (e.g., "USD", "HKD")
            source: 數據源

        Returns:
            加密貨幣數據字典
        """
        if source == "yahoo":
            ticker_symbol = f"{symbol}-{exchange}"
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise ValueError(f"No crypto data for {ticker_symbol}")

                latest = hist.iloc[-1]
                return {
                    'success': True,
                    'symbol': symbol,
                    'exchange': exchange,
                    'price': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'timestamp': latest.name.isoformat(),
                    'source': 'yahoo'
                }
            except Exception as e:
                raise Exception(f"Yahoo Crypto error: {str(e)}")
        else:
            raise ValueError(f"Crypto data only supported from Yahoo in this implementation")

    async def get_multiple_stocks(self, symbols: List[str], source: str = "yahoo") -> Dict[str, Any]:
        """批量獲取多個股票數據"""
        results = []
        errors = []

        # 並行獲取
        tasks = []
        for symbol in symbols:
            task = self.get_stock_data(symbol, source)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, response in zip(symbols, responses):
            if isinstance(response, Exception):
                errors.append({
                    'symbol': symbol,
                    'error': str(response)
                })
            else:
                results.append(response['data'])

        return {
            'success': len(results) > 0,
            'data': results,
            'errors': errors,
            'total': len(symbols),
            'successful': len(results),
            'failed': len(errors)
        }

    async def fetch_data(self, params: Dict[str, Any]) -> Any:
        """實現基礎適配器的fetch_data方法"""
        data_type = params.get('type', 'stock')

        if data_type == 'stock':
            return await self.get_stock_data(
                params['symbol'],
                params.get('source', 'yahoo'),
                params.get('period', '1y')
            )
        elif data_type == 'fx':
            return await self.get_fx_data(
                params['from_currency'],
                params['to_currency'],
                params.get('source', 'yahoo')
            )
        elif data_type == 'crypto':
            return await self.get_crypto_data(
                params['symbol'],
                params.get('exchange', 'USD'),
                params.get('source', 'yahoo')
            )
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def get_supported_sources(self) -> List[str]:
        """獲取支持的數據源"""
        return self.SUPPORTED_SOURCES

    def get_data_source_info(self) -> Dict[str, Any]:
        """獲取數據源信息"""
        info = super().get_data_source_info()
        info.update({
            'supported_sources': self.SUPPORTED_SOURCES,
            'data_types': ['stock', 'fx', 'crypto'],
            'api_keys_configured': list(self.api_keys.keys())
        })
        return info
