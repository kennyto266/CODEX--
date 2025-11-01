#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易应用服务
处理交易相关的用例和协调
"""

from typing import List, Optional, Dict, Any
import asyncio

from ...domain.entities import Trade
from ...domain.value_objects import StockSymbol, Price
from ...domain.services import TradingService, MarketDataService
from ...domain.repositories import TradeRepository
from ...application.dto import (
    TradeDTO, TradeResponseDTO,
    TradeResponse
)
from ...application.mappers import TradeMapper


class TradingApplicationService:
    """交易应用服务"""

    def __init__(self, trading_service: TradingService,
                 market_data_service: MarketDataService,
                 trade_repository: TradeRepository):
        """初始化交易应用服务"""
        self.trading_service = trading_service
        self.market_data_service = market_data_service
        self.trade_repository = trade_repository

    async def get_all_trades(self, symbol: Optional[str] = None) -> TradeResponse:
        """获取所有交易"""
        try:
            trades = await self.trade_repository.get_all()

            # 应用过滤
            if symbol:
                symbol_obj = StockSymbol(symbol)
                # 这里需要实现按股票代码过滤
                pass

            trade_dtos = [TradeMapper.to_dto(trade) for trade in trades]
            return TradeResponse(
                success=True,
                data=trade_dtos
            )

        except Exception as e:
            return TradeResponse(
                success=False,
                error=f"获取交易列表失败: {str(e)}"
            )

    async def get_trade_statistics(self) -> TradeResponse:
        """获取交易统计"""
        try:
            trades = await self.trade_repository.get_all()

            if not trades:
                return TradeResponse(
                    success=True,
                    data={
                        'total_trades': 0,
                        'total_volume': 0,
                        'total_value': 0,
                        'average_price': 0
                    }
                )

            # 计算统计数据
            total_trades = len(trades)
            total_volume = sum(trade.quantity.value for trade in trades)
            total_value = sum(
                trade.quantity.value * trade.price.value
                for trade in trades
            )
            average_price = total_value / total_volume if total_volume > 0 else 0

            statistics = {
                'total_trades': total_trades,
                'total_volume': total_volume,
                'total_value': total_value,
                'average_price': average_price,
                'buy_trades': len([t for t in trades if t.side.value == 'buy']),
                'sell_trades': len([t for t in trades if t.side.value == 'sell'])
            }

            return TradeResponse(
                success=True,
                data=statistics
            )

        except Exception as e:
            return TradeResponse(
                success=False,
                error=f"获取交易统计失败: {str(e)}"
            )

    async def get_market_data(self, symbol: str) -> TradeResponse:
        """获取市场数据"""
        try:
            symbol_obj = StockSymbol(symbol)

            # 从市场数据服务获取数据
            market_data = await self.market_data_service.get_market_data(symbol_obj)
            if not market_data:
                return TradeResponse(
                    success=False,
                    error="获取市场数据失败"
                )

            return TradeResponse(
                success=True,
                data=market_data
            )

        except Exception as e:
            return TradeResponse(
                success=False,
                error=f"获取市场数据失败: {str(e)}"
            )

    async def get_historical_data(self, symbol: str, days: int = 30) -> TradeResponse:
        """获取历史数据"""
        try:
            symbol_obj = StockSymbol(symbol)

            historical_data = await self.market_data_service.get_historical_data(
                symbol_obj, days
            )

            return TradeResponse(
                success=True,
                data=historical_data
            )

        except Exception as e:
            return TradeResponse(
                success=False,
                error=f"获取历史数据失败: {str(e)}"
            )