#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易映射器
"""

from ...application.dto import TradeDTO
from ...domain.entities import Trade


class TradeMapper:
    """交易映射器"""

    @staticmethod
    def to_dto(trade: Trade) -> TradeDTO:
        """将交易实体转换为DTO"""
        return TradeDTO(
            trade_id=trade.trade_id,
            order_id=str(trade.order_id),
            symbol=str(trade.symbol),
            side=trade.side.value,
            quantity=trade.quantity.value,
            price=trade.price.value,
            commission=trade.commission.value,
            trade_time=trade.trade_time.to_string(),
            status=trade.status.value
        )

    @staticmethod
    def from_dto(trade_dto: TradeDTO) -> Trade:
        """将DTO转换为交易实体"""
        from ...domain.value_objects import (
            OrderId, StockSymbol, Quantity, Price, Money, OrderSide, Timestamp
        )
        from ...domain.entities.trade import TradeStatus

        return Trade(
            trade_id=trade_dto.trade_id,
            order_id=OrderId.from_string(trade_dto.order_id),
            symbol=StockSymbol(trade_dto.symbol),
            side=OrderSide(trade_dto.side),
            quantity=Quantity.from_int(trade_dto.quantity),
            price=Price.from_float(trade_dto.price),
            commission=Money.from_float(trade_dto.commission),
            trade_time=Timestamp.from_string(trade_dto.trade_time),
            status=TradeStatus(trade_dto.status)
        )