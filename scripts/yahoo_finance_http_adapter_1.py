"""
Yahoo Finance HTTP Adapter
從Yahoo Finance HTTP API獲取真實金融市場數據

真實可用數據源：
- API端點: https://query1.finance.yahoo.com
- 狀態: ✅ 可用，有速率限制
- 認證: 免費
- 限制: 請求頻率過快會被限制
- 數據: 股票、外匯、加密貨幣、期貨、經濟指標

這是項目中第二個真正可用的真實數據適配器。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import aiohttp
import time


class YahooFinanceHttpAdapter:
    """
    Yahoo Finance HTTP API 真實數據適配器

    使用Yahoo Finance的HTTP API而非yfinance庫
    """

    BASE_URL = "https://query1.finance.yahoo.com"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 最小請求間隔

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            self.logger.debug(f"速率限制：等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)

    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None):
        await self._ensure_session()
        await self._rate_limit()

        for attempt in range(3):
            try:
                async with self.session.get(url, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 429:
                        wait_time = 2 ** attempt
                        self.logger.warning(f"速率限制，{wait_time}s後重試")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    return await response.json()
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

    def _normalize_hk_symbol(self, symbol: str) -> str:
        """標準化港股代碼"""
        symbol = symbol.upper()
        if symbol.isdigit() and len(symbol) == 4:
            return f"{symbol}.HK"
        elif not symbol.endswith('.HK'):
            return f"{symbol}.HK"
        return symbol

    async def get_stock_info(self, symbol: str, market: str = 'hk') -> Dict[str, Any]:
        """獲取股票基本信息"""
        if market == 'hk':
            symbol = self._normalize_hk_symbol(symbol)

        url = f"{self.BASE_URL}/v10/finance/quoteSummary/{symbol}"
        params = {
            'modules': 'price,summaryDetail,assetProfile'
        }

        try:
            data = await self._make_request(url, params)
            result = data.get('quoteSummary', {}).get('result', [])

            if not result:
                raise Exception(f"未找到股票信息: {symbol}")

            info = result[0]
            price = info.get('price', {})
            summary = info.get('summaryDetail', {})

            return {
                'symbol': symbol,
                'name': price.get('longName', ''),
                'currency': price.get('currency', ''),
                'current_price': price.get('regularMarketPrice', {}).get('raw'),
                'previous_close': price.get('regularMarketPreviousClose', {}).get('raw'),
                'change': price.get('regularMarketChange', {}).get('raw'),
                'change_percent': price.get('regularMarketChangePercent', {}).get('raw'),
                'market_cap': summary.get('marketCap', {}).get('raw'),
                'volume': price.get('regularMarketVolume', {}).get('raw'),
                'day_high': summary.get('dayHigh', {}).get('raw'),
                'day_low': summary.get('dayLow', {}).get('raw'),
                'fifty_two_week_high': summary.get('fiftyTwoWeekHigh', {}).get('raw'),
                'fifty_two_week_low': summary.get('fiftyTwoWeekLow', {}).get('raw')
            }
        except Exception as e:
            self.logger.error(f"獲取股票信息失敗 {symbol}: {e}")
            raise

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime] = None,
        interval: str = '1d',
        market: str = 'hk'
    ) -> pd.DataFrame:
        """獲取歷史價格數據"""
        if market == 'hk':
            symbol = self._normalize_hk_symbol(symbol)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        url = f"{self.BASE_URL}/v8/finance/chart/{symbol}"
        params = {
            'period1': start_timestamp,
            'period2': end_timestamp,
            'interval': interval
        }

        try:
            data = await self._make_request(url, params)
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]

            records = []
            for i, ts in enumerate(timestamps):
                if quotes['close'][i] is None:
                    continue
                record = {
                    'date': datetime.fromtimestamp(ts),
                    'open': quotes['open'][i],
                    'high': quotes['high'][i],
                    'low': quotes['low'][i],
                    'close': quotes['close'][i],
                    'volume': quotes['volume'][i]
                }
                records.append(record)

            df = pd.DataFrame(records)
            df = df.sort_values('date')
            df = df.dropna()

            self.logger.info(f"獲取 {symbol} 歷史數據: {len(df)} 條記錄")
            return df

        except Exception as e:
            self.logger.error(f"獲取歷史數據失敗 {symbol}: {e}")
            raise

    async def test_connection(self) -> bool:
        """測試API連接"""
        try:
            info = await self.get_stock_info('AAPL', 'us')
            self.logger.info(f"Yahoo Finance API 連接成功，AAPL: ${info['current_price']}")
            return True
        except Exception as e:
            self.logger.error(f"Yahoo Finance API 連接失敗: {e}")
            return False

    async def get_data_source_info(self) -> Dict[str, Any]:
        """獲取數據源信息"""
        return {
            'adapter_name': 'YahooFinanceHttpAdapter',
            'data_source': 'Yahoo Finance HTTP API',
            'base_url': self.BASE_URL,
            'description': '從Yahoo Finance HTTP API獲取真實金融市場數據',
            'is_real_data': True,
            'api_status': '✅ 可用',
            'requires_api_key': False,
            'rate_limit': '無明確限制（請求過快會被限制）',
            'data_types': '股票、外匯、加密貨幣、期貨',
            'last_updated': datetime.now().isoformat()
        }

    def __repr__(self):
        return f"<YahooFinanceHttpAdapter(source=YahooFinance)>"


# 測試代碼
if __name__ == "__main__":
    async def test():
        print("Yahoo Finance HTTP API 測試")
        print("-" * 50)

        async with YahooFinanceHttpAdapter() as adapter:
            # 測試連接
            if await adapter.test_connection():
                print("[OK] API連接成功")

                # 獲取美股信息
                print("\n[INFO] 獲取 Apple (AAPL) 信息...")
                info = await adapter.get_stock_info('AAPL', 'us')
                print(f"名稱: {info['name']}")
                print(f"價格: ${info['current_price']:.2f}")
                print(f"變化: {info['change']:.2f} ({info['change_percent']:.2f}%)")

                # 獲取港股信息
                print("\n[INFO] 獲取 騰訊 (0700.HK) 信息...")
                info = await adapter.get_stock_info('0700', 'hk')
                print(f"名稱: {info['name']}")
                print(f"價格: {info['currency']} {info['current_price']:.2f}")

                # 獲取歷史數據
                print("\n[INFO] 獲取 AAPL 30天歷史數據...")
                df = await adapter.get_historical_data(
                    'AAPL',
                    start_date='2024-01-01',
                    end_date='2024-01-31',
                    market='us'
                )
                print(f"獲取 {len(df)} 條記錄")
                print(f"最新收盤價: ${df['close'].iloc[-1]:.2f}")
            else:
                print("[ERROR] API連接失敗")

    asyncio.run(test())
