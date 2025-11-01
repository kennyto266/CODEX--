#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域模型单元测试
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime

# 测试值对象
def test_stock_symbol_creation():
    """测试股票代码创建"""
    from src.domain.value_objects.stock_symbol import StockSymbol

    # 有效股票代码
    symbol = StockSymbol("0700.HK")
    assert symbol.symbol == "0700.HK"
    assert symbol.get_market() == "HKEX"

    # 无效股票代码
    with pytest.raises(ValueError):
        StockSymbol("INVALID")


def test_price_creation():
    """测试价格值对象"""
    from src.domain.value_objects.price import Price

    # 有效价格
    price = Price(Decimal("100.50"))
    assert price.amount == Decimal("100.50")

    # 无效价格（负数）
    with pytest.raises(ValueError):
        Price(Decimal("-10.00"))


def test_quantity_validation():
    """测试数量验证"""
    from src.domain.value_objects.quantity import Quantity

    # 有效数量
    quantity = Quantity.from_int(1000)
    assert quantity.value == 1000

    # 无效数量（零或负数）
    with pytest.raises(ValueError):
        Quantity.from_int(0)

    with pytest.raises(ValueError):
        Quantity.from_int(-100)


# 测试实体
def test_order_entity():
    """测试订单实体"""
    from src.domain.entities.order import Order
    from src.domain.value_objects import StockSymbol, OrderId, Quantity, Price, OrderSide, OrderType

    # 创建订单
    order_id = OrderId.generate()
    symbol = StockSymbol("0700.HK")
    quantity = Quantity.from_int(1000)
    price = Price(Decimal("350.50"))

    order = Order(
        order_id=order_id,
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price
    )

    assert order.order_id == order_id
    assert order.symbol == symbol
    assert order.quantity == quantity
    assert order.price == price

    # 测试订单提交
    order.submit()
    assert order.status == OrderStatus.SUBMITTED

    # 测试事件发布
    assert len(order.get_events()) > 0


def test_portfolio_entity():
    """测试投资组合实体"""
    from src.domain.entities.portfolio import Portfolio, PortfolioId, PortfolioType

    # 创建投资组合
    portfolio_id = PortfolioId.generate()
    portfolio = Portfolio(
        portfolio_id=portfolio_id,
        name="测试投资组合",
        portfolio_type=PortfolioType.LONG_ONLY,
        initial_capital=Decimal("1000000.00")
    )

    assert portfolio.name == "测试投资组合"
    assert portfolio.total_value == Decimal("1000000.00")

    # 测试投资组合更新
    portfolio.update_performance(
        total_value=Decimal("1050000.00"),
        total_return=Decimal("50000.00")
    )

    assert portfolio.total_value == Decimal("1050000.00")
    assert portfolio.total_return == Decimal("50000.00")


def test_trade_entity():
    """测试交易实体"""
    from src.domain.entities.trade import Trade, TradeId
    from src.domain.value_objects import StockSymbol, TradeSide

    # 创建交易
    trade_id = TradeId.generate()
    trade = Trade(
        trade_id=trade_id,
        symbol=StockSymbol("0700.HK"),
        side=TradeSide.BUY,
        quantity=1000,
        price=Decimal("350.50"),
        trade_time=datetime.utcnow()
    )

    assert trade.symbol == StockSymbol("0700.HK")
    assert trade.quantity == 1000
    assert trade.price == Decimal("350.50")


# 测试值对象的不变性
def test_value_objects_immutability():
    """测试值对象的不可变性"""
    from src.domain.value_objects import StockSymbol

    symbol = StockSymbol("0700.HK")

    # 尝试修改值对象的属性应该失败
    with pytest.raises(AttributeError):
        symbol.symbol = "0388.HK"


# 测试业务规则
def test_order_business_rules():
    """测试订单业务规则"""
    from src.domain.entities.order import Order
    from src.domain.value_objects import StockSymbol, OrderId, Quantity, Price, OrderSide, OrderType, OrderStatus

    # 测试市场订单不能有价格
    order_id = OrderId.generate()
    symbol = StockSymbol("0700.HK")
    quantity = Quantity.from_int(1000)

    order = Order(
        order_id=order_id,
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=quantity
    )

    # 市场订单不应该有价格
    assert order.price is None

    # 测试限价订单必须有价格
    limit_order = Order(
        order_id=OrderId.generate(),
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=Price(Decimal("350.00"))
    )

    assert limit_order.price is not None


# 测试聚合根边界
def test_portfolio_aggregates():
    """测试投资组合聚合"""
    from src.domain.entities.portfolio import Portfolio, PortfolioId, PortfolioType
    from src.domain.entities.position import Position

    # 创建投资组合
    portfolio_id = PortfolioId.generate()
    portfolio = Portfolio(
        portfolio_id=portfolio_id,
        name="测试投资组合",
        portfolio_type=PortfolioType.LONG_ONLY,
        initial_capital=Decimal("1000000.00")
    )

    # 创建持仓
    position = Position(
        symbol="0700.HK",
        quantity=1000,
        average_cost=Decimal("300.00")
    )

    # 添加持仓到投资组合
    portfolio.add_position(position)

    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].symbol == "0700.HK"


# 性能测试
def test_performance_value_objects():
    """测试值对象性能"""
    from src.domain.value_objects import StockSymbol, Price, Quantity

    import time

    # 测试创建大量值对象的性能
    start_time = time.time()

    for i in range(10000):
        symbol = StockSymbol(f"{i:04d}.HK")
        price = Price(Decimal(str(i)))
        quantity = Quantity.from_int(i)

    end_time = time.time()
    execution_time = end_time - start_time

    # 应该能够在合理时间内完成
    assert execution_time < 5.0  # 5秒内


# 测试异常处理
def test_exception_handling():
    """测试异常处理"""
    from src.domain.value_objects import StockSymbol

    # 测试无效输入
    with pytest.raises(TypeError):
        StockSymbol(None)

    with pytest.raises(TypeError):
        StockSymbol(123)

    with pytest.raises(ValueError):
        StockSymbol("")
