#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易服务
处理订单执行和交易相关的业务逻辑
"""

from typing import List, Optional, Dict, Any
from ..entities import Order, Trade
from ..value_objects import (
    OrderId, StockSymbol, Price, Quantity,
    OrderType, OrderSide, Timestamp, Money
)
from ..events import DomainEvent


class TradingService:
    """交易服务"""

    def __init__(self, event_bus):
        """初始化交易服务"""
        self.event_bus = event_bus
        self._orders: Dict[str, Order] = {}
        self._trades: Dict[str, Trade] = {}

    async def submit_order(self, symbol: StockSymbol, side: OrderSide,
                          quantity: Quantity, order_type: OrderType,
                          price: Optional[Price] = None,
                          stop_price: Optional[Price] = None) -> Order:
        """提交订单"""
        # 生成订单ID
        order_id = OrderId.generate()

        # 创建订单
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )

        # 验证订单
        self._validate_order(order)

        # 提交订单
        if order.submit():
            self._orders[str(order_id)] = order

            # 发布订单提交事件
            events = order.get_domain_events()
            for event in events:
                await self.event_bus.publish(event)
            order.clear_domain_events()

        return order

    async def cancel_order(self, order_id: OrderId, reason: str = "") -> bool:
        """取消订单"""
        order = self._orders.get(str(order_id))
        if not order:
            return False

        # 检查是否可以取消
        if not order.can_cancel():
            return False

        # 取消订单
        if order.cancel(reason):
            # 发布订单取消事件
            events = order.get_domain_events()
            for event in events:
                await self.event_bus.publish(event)
            order.clear_domain_events()

            return True

        return False

    async def execute_trade(self, order_id: OrderId, trade_quantity: int,
                           trade_price: Price) -> Optional[Trade]:
        """执行交易"""
        order = self._orders.get(str(order_id))
        if not order:
            return None

        # 验证交易
        if not self._validate_trade(order, trade_quantity, trade_price):
            return None

        # 执行交易
        trade_id = f"trade_{str(order_id)}_{len(self._trades) + 1}"

        trade = Trade(
            trade_id=trade_id,
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=Quantity(trade_quantity),
            price=trade_price,
            commission=self._calculate_commission(trade_quantity, trade_price),
            trade_time=Timestamp.now()
        )

        # 更新订单
        if order.fill(trade_quantity, trade_price):
            # 发布订单成交事件
            events = order.get_domain_events()
            for event in events:
                await self.event_bus.publish(event)
            order.clear_domain_events()

            # 触发交易成交
            trade.fill(trade_quantity, trade_price)
            self._trades[trade_id] = trade

            # 发布交易事件
            events = trade.get_domain_events()
            for event in events:
                await self.event_bus.publish(event)
            trade.clear_domain_events()

            return trade

        return None

    def get_order(self, order_id: OrderId) -> Optional[Order]:
        """获取订单"""
        return self._orders.get(str(order_id))

    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """获取交易"""
        return self._trades.get(trade_id)

    def get_all_orders(self) -> List[Order]:
        """获取所有订单"""
        return list(self._orders.values())

    def get_all_trades(self) -> List[Trade]:
        """获取所有交易"""
        return list(self._trades.get(trade_id, Trade) for trade_id in self._trades)

    def get_orders_by_symbol(self, symbol: StockSymbol) -> List[Order]:
        """获取指定股票的所有订单"""
        return [order for order in self._orders.values() if order.symbol == symbol]

    def get_trades_by_symbol(self, symbol: StockSymbol) -> List[Trade]:
        """获取指定股票的所有交易"""
        return [trade for trade in self._trades.values() if trade.symbol == symbol]

    def get_pending_orders(self) -> List[Order]:
        """获取待处理订单"""
        return [order for order in self._orders.values() if order.is_active()]

    def _validate_order(self, order: Order):
        """验证订单"""
        if not order.symbol:
            raise ValueError("股票代码不能为空")

        if order.quantity.value <= 0:
            raise ValueError("数量必须大于零")

        if order.order_type == OrderType.LIMIT and not order.price:
            raise ValueError("限价单必须指定价格")

        if order.order_type == OrderType.MARKET and order.price:
            raise ValueError("市价单不能指定价格")

    def _validate_trade(self, order: Order, trade_quantity: int, trade_price: Price) -> bool:
        """验证交易"""
        # 检查订单状态
        if not order.is_active():
            return False

        # 检查交易数量
        if trade_quantity <= 0 or trade_quantity > order.remaining_quantity:
            return False

        # 检查价格
        if not trade_price or trade_price.value <= 0:
            return False

        # 检查限价单价格
        if order.order_type == OrderType.LIMIT and order.price:
            if order.side == OrderSide.BUY and trade_price.value > order.price.value:
                return False
            if order.side == OrderSide.SELL and trade_price.value < order.price.value:
                return False

        return True

    def _calculate_commission(self, quantity: int, price: Price) -> Money:
        """计算佣金（简化计算）"""
        # 假设佣金为成交金额的0.1%
        commission_rate = 0.001
        trade_value = quantity * price.value
        commission = trade_value * commission_rate
        return Money.from_float(commission, 'HKD')

    def calculate_portfolio_value(self, symbol: StockSymbol, current_price: Price,
                                 trades: List[Trade]) -> Money:
        """计算投资组合价值"""
        # 获取该股票的所有交易
        symbol_trades = [t for t in trades if t.symbol == symbol]

        # 计算净持仓
        total_quantity = 0
        total_cost = 0

        for trade in symbol_trades:
            if trade.side == OrderSide.BUY:
                total_quantity += trade.quantity.value
                total_cost += trade.quantity.value * trade.price.value
            else:  # SELL
                total_quantity -= trade.quantity.value
                total_cost -= trade.quantity.value * trade.price.value

        # 计算市场价值
        market_value = total_quantity * current_price.value
        return Money.from_float(market_value, 'HKD')