"""
統一港交所適配器
整合 HKEXAdapter、HKEXHttpAdapter 和 RealtimeHKEXAdapter
支援歷史數據、實時數據、期權和期貨
"""

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json

from .unified_base_adapter import UnifiedBaseAdapter

class UnifiedHKEXAdapter(UnifiedBaseAdapter):
    """
    統一港交所適配器
    支援港交所的歷史數據、實時數據、期權和期貨
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.base_url = self.config.get('hkex_base_url', 'http://18.180.162.113:9191')
        self.session = None
        self.subscribers = {}  # 實時數據訂閱者

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取HTTP會話"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """關閉會話"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _fetch_hkex_data(self, symbol: str, duration: int = 365) -> Dict[str, Any]:
        """
        從港交所API獲取數據

        Args:
            symbol: 股票代碼 (lowercase, e.g., "0700.hk")
            duration: 天數 (e.g., 365 for 1 year)

        Returns:
            港交所數據
        """
        url = f"{self.base_url}/inst/getInst"
        params = {
            "symbol": symbol.lower(),
            "duration": duration
        }

        session = await self._get_session()

        try:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
        except asyncio.TimeoutError:
            raise Exception("Request timeout")
        except Exception as e:
            raise Exception(f"API Error: {str(e)}")

    async def get_historical_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """
        獲取港股歷史數據

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")
            period: 時間期間 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y")

        Returns:
            歷史數據字典
        """
        # 轉換期間到天數
        period_map = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        duration = period_map.get(period, 365)

        try:
            data = await self._fetch_hkex_data(symbol, duration)
            return {
                'success': True,
                'symbol': symbol,
                'period': period,
                'data': data,
                'source': 'hkex_api',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }

    async def get_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """
        獲取港股實時數據

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")

        Returns:
            實時數據字典
        """
        try:
            # 獲取最新數據
            data = await self._fetch_hkex_data(symbol, 1)

            # 提取最新價格
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                return {
                    'success': True,
                    'symbol': symbol,
                    'price': latest.get('close', 0),
                    'volume': latest.get('volume', 0),
                    'timestamp': latest.get('date', datetime.now().isoformat()),
                    'source': 'hkex_realtime',
                    'raw_data': latest
                }
            else:
                return {
                    'success': False,
                    'error': 'No data available',
                    'symbol': symbol
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol
            }

    async def get_options_chain(self, symbol: str) -> Dict[str, Any]:
        """
        獲取期權鏈數據

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")

        Returns:
            期權鏈數據
        """
        # 注意：實際實現需要港交所期權API
        # 這裡是佔位符實現
        return {
            'success': False,
            'error': 'Options chain not yet implemented',
            'symbol': symbol,
            'note': 'Contact HKEX for options API access'
        }

    async def subscribe(self, symbol: str, callback: Callable) -> str:
        """
        訂閱實時數據

        Args:
            symbol: 股票代碼
            callback: 回調函數

        Returns:
            訂閱ID
        """
        subscription_id = f"{symbol}_{datetime.now().timestamp()}"

        if symbol not in self.subscribers:
            self.subscribers[symbol] = []

        self.subscribers[symbol].append({
            'id': subscription_id,
            'callback': callback
        })

        # 啟動實時監控任務
        asyncio.create_task(self._monitor_symbol(symbol))

        return subscription_id

    async def unsubscribe(self, symbol: str, subscription_id: str) -> bool:
        """
        取消訂閱

        Args:
            symbol: 股票代碼
            subscription_id: 訂閱ID

        Returns:
            是否成功
        """
        if symbol in self.subscribers:
            self.subscribers[symbol] = [
                sub for sub in self.subscribers[symbol]
                if sub['id'] != subscription_id
            ]
            return True
        return False

    async def _monitor_symbol(self, symbol: str):
        """監控符號的實時數據變化"""
        while symbol in self.subscribers and self.subscribers[symbol]:
            try:
                data = await self.get_realtime_data(symbol)

                if data['success']:
                    # 通知所有訂閱者
                    for subscriber in self.subscribers[symbol]:
                        await subscriber['callback'](data)

                await asyncio.sleep(5)  # 每5秒更新一次

            except Exception as e:
                print(f"Error monitoring {symbol}: {e}")
                await asyncio.sleep(10)

    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """批量獲取多個港股數據"""
        results = []
        errors = []

        # 並行獲取
        tasks = []
        for symbol in symbols:
            task = self.get_historical_data(symbol)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, response in zip(symbols, responses):
            if isinstance(response, Exception):
                errors.append({
                    'symbol': symbol,
                    'error': str(response)
                })
            else:
                results.append(response)

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
        data_type = params.get('type', 'historical')

        if data_type == 'historical':
            return await self.get_historical_data(
                params['symbol'],
                params.get('period', '1y')
            )
        elif data_type == 'realtime':
            return await self.get_realtime_data(params['symbol'])
        elif data_type == 'options':
            return await self.get_options_chain(params['symbol'])
        elif data_type == 'multiple':
            return await self.get_multiple_stocks(params['symbols'])
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def get_supported_features(self) -> List[str]:
        """獲取支持的功能"""
        return [
            'historical_data',
            'realtime_data',
            'options_chain',
            'bulk_requests',
            'subscriptions'
        ]

    def get_data_source_info(self) -> Dict[str, Any]:
        """獲取數據源信息"""
        info = super().get_data_source_info()
        info.update({
            'base_url': self.base_url,
            'supported_features': self.get_supported_features(),
            'active_subscriptions': len(self.subscribers)
        })
        return info
