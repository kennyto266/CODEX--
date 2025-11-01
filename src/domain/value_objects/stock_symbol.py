#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票代码值对象
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class StockSymbol:
    """股票代码值对象"""
    symbol: str

    def __post_init__(self):
        """验证股票代码格式"""
        if not self._is_valid_symbol(self.symbol):
            raise ValueError(f"无效的股票代码格式: {self.symbol}")

    @staticmethod
    def _is_valid_symbol(symbol: str) -> bool:
        """验证股票代码格式"""
        if not symbol:
            return False

        # 港股格式：4位数字 + .HK (例如：0700.HK)
        hk_pattern = r'^\d{4}\.HK$'
        # 美股格式：字母或字母+数字 (例如：AAPL, GOOGL)
        us_pattern = r'^[A-Z]{1,5}$'
        # 带市场后缀的格式：AAPL.US
        with_market_pattern = r'^[A-Z]{1,5}\.[A-Z]{2,3}$'

        return bool(
            re.match(hk_pattern, symbol) or
            re.match(us_pattern, symbol) or
            re.match(with_market_pattern, symbol)
        )

    def get_market(self) -> Optional[str]:
        """获取市场信息"""
        if '.HK' in self.symbol:
            return 'HKEX'
        elif '.US' in self.symbol:
            return 'NASDAQ'
        elif self._is_valid_symbol(self.symbol):
            return 'US'
        return None

    def without_market_suffix(self) -> str:
        """获取不带市场后缀的代码"""
        if '.' in self.symbol:
            return self.symbol.split('.')[0]
        return self.symbol

    def with_market_suffix(self, market: str) -> str:
        """添加市场后缀"""
        if '.' in self.symbol:
            return self.symbol  # 已经有后缀

        market_codes = {
            'HKEX': 'HK',
            'NASDAQ': 'US',
            'NYSE': 'US'
        }
        suffix = market_codes.get(market, market.upper())
        return f"{self.symbol}.{suffix}"

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return f"StockSymbol('{self.symbol}')"