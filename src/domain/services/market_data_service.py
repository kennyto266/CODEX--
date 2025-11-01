#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据服务
提供市场数据获取和处理功能
"""

import asyncio
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import aiohttp

from ..entities import Stock
from ..value_objects import (
    StockSymbol, Price, Money, Timestamp, Percentage
)
from ..events import DomainEvent


class MarketDataService:
    """市场数据服务"""

    def __init__(self, event_bus):
        """初始化市场数据服务"""
        self.event_bus = event_bus
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, Timestamp] = {}
        self._subscribers: Dict[str, List[Callable]] = {}  # symbol -> list of callbacks
        self._running = False
        self._update_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动市场数据服务"""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())

    async def stop(self):
        """停止市场数据服务"""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    async def get_stock_price(self, symbol: StockSymbol, use_cache: bool = True) -> Optional[Price]:
        """获取股票价格"""
        symbol_str = str(symbol)

        # 检查缓存
        if use_cache and symbol_str in self._cache:
            if self._is_cache_valid(symbol_str):
                cached_price = self._cache[symbol_str].get('price')
                if cached_price:
                    return Price.from_float(cached_price)

        # 从外部API获取
        try:
            price_data = await self._fetch_price_from_api(symbol)
            if price_data:
                # 更新缓存
                self._cache[symbol_str] = price_data
                self._cache_ttl[symbol_str] = Timestamp.now()

                return Price.from_float(price_data['price'])
        except Exception as e:
            print(f"获取价格失败 {symbol}: {e}")

        return None

    async def get_market_data(self, symbol: StockSymbol) -> Optional[Dict[str, Any]]:
        """获取市场数据"""
        symbol_str = str(symbol)

        # 检查缓存
        if symbol_str in self._cache:
            if self._is_cache_valid(symbol_str):
                return self._cache[symbol_str]

        # 从外部API获取
        try:
            market_data = await self._fetch_market_data_from_api(symbol)
            if market_data:
                # 更新缓存
                self._cache[symbol_str] = market_data
                self._cache_ttl[symbol_str] = Timestamp.now()

                return market_data
        except Exception as e:
            print(f"获取市场数据失败 {symbol}: {e}")

        return None

    async def subscribe_to_price_updates(self, symbol: StockSymbol, callback: Callable):
        """订阅价格更新"""
        symbol_str = str(symbol)

        if symbol_str not in self._subscribers:
            self._subscribers[symbol_str] = []

        self._subscribers[symbol_str].append(callback)

    async def unsubscribe_from_price_updates(self, symbol: StockSymbol, callback: Callable):
        """取消订阅价格更新"""
        symbol_str = str(symbol)

        if symbol_str in self._subscribers:
            try:
                self._subscribers[symbol_str].remove(callback)
            except ValueError:
                pass

    async def get_historical_data(self, symbol: StockSymbol,
                                  days: int = 30) -> List[Dict[str, Any]]:
        """获取历史数据"""
        try:
            historical_data = await self._fetch_historical_data_from_api(symbol, days)
            return historical_data
        except Exception as e:
            print(f"获取历史数据失败 {symbol}: {e}")
            return []

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._cache_ttl.clear()

    def _is_cache_valid(self, symbol: str) -> bool:
        """检查缓存是否有效"""
        if symbol not in self._cache_ttl:
            return False

        cache_time = self._cache_ttl[symbol].value
        current_time = Timestamp.now().value
        time_diff = (current_time - cache_time).total_seconds()

        # 缓存有效期为5分钟
        return time_diff < 300

    async def _update_loop(self):
        """更新循环"""
        while self._running:
            try:
                # 获取订阅的股票列表
                symbols_to_update = list(self._subscribers.keys())

                # 更新价格
                for symbol_str in symbols_to_update:
                    symbol = StockSymbol(symbol_str)
                    price = await self.get_stock_price(symbol, use_cache=False)

                    if price:
                        # 通知订阅者
                        await self._notify_subscribers(symbol, price)

                # 每30秒更新一次
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"市场数据更新循环异常: {e}")
                await asyncio.sleep(5)

    async def _notify_subscribers(self, symbol: StockSymbol, price: Price):
        """通知订阅者"""
        symbol_str = str(symbol)

        if symbol_str in self._subscribers:
            for callback in self._subscribers[symbol_str]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(symbol, price)
                    else:
                        callback(symbol, price)
                except Exception as e:
                    print(f"通知订阅者失败: {e}")

    async def _fetch_price_from_api(self, symbol: StockSymbol) -> Optional[Dict[str, Any]]:
        """从API获取价格"""
        # 使用统一的HTTP API端点
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {
            "symbol": str(symbol).lower(),
            "duration": 1  # 1天数据获取最新价格
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_price_data(data)
                else:
                    print(f"API请求失败: {response.status}")
                    return None

    async def _fetch_market_data_from_api(self, symbol: StockSymbol) -> Optional[Dict[str, Any]]:
        """从API获取市场数据"""
        # 类似的实现，获取更完整的市场数据
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {
            "symbol": str(symbol).lower(),
            "duration": 5  # 5天数据
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_market_data(data)
                else:
                    print(f"API请求失败: {response.status}")
                    return None

    async def _fetch_historical_data_from_api(self, symbol: StockSymbol,
                                            days: int) -> List[Dict[str, Any]]:
        """从API获取历史数据"""
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {
            "symbol": str(symbol).lower(),
            "duration": days
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_historical_data(data)
                else:
                    print(f"API请求失败: {response.status}")
                    return []

    def _parse_price_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析价格数据"""
        try:
            if 'data' in data and data['data']:
                latest = data['data'][-1]  # 最新数据
                return {
                    'price': latest.get('close', 0),
                    'open': latest.get('open', 0),
                    'high': latest.get('high', 0),
                    'low': latest.get('low', 0),
                    'volume': latest.get('volume', 0),
                    'timestamp': Timestamp.now().to_string()
                }
        except Exception as e:
            print(f"解析价格数据失败: {e}")

        return {}

    def _parse_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析市场数据"""
        parsed = self._parse_price_data(data)

        if parsed:
            try:
                # 添加更多市场数据
                if 'data' in data and data['data']:
                    latest = data['data'][-1]
                    parsed['change'] = latest.get('close', 0) - latest.get('open', 0)
                    parsed['change_pct'] = (
                        (latest.get('close', 0) - latest.get('open', 0)) /
                        latest.get('open', 1)
                    ) * 100
            except Exception as e:
                print(f"解析市场数据失败: {e}")

        return parsed

    def _parse_historical_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析历史数据"""
        historical_data = []

        try:
            if 'data' in data and data['data']:
                for item in data['data']:
                    historical_data.append({
                        'date': item.get('date', ''),
                        'open': item.get('open', 0),
                        'high': item.get('high', 0),
                        'low': item.get('low', 0),
                        'close': item.get('close', 0),
                        'volume': item.get('volume', 0)
                    })
        except Exception as e:
            print(f"解析历史数据失败: {e}")

        return historical_data