#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库集成测试
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime

from src.infrastructure.database.connection import get_database_manager, DatabaseConfig
from src.infrastructure.database.models import (
    OrderModel, PortfolioModel, TradeModel, PositionModel,
    StrategyModel, StockModel, EventModel
)
from src.infrastructure.database.repositories.base import BaseRepository


class TestDatabaseIntegration:
    """数据库集成测试类"""

    @pytest.fixture(scope="class")
    async def db_manager(self):
        """数据库管理器夹具"""
        # 使用SQLite进行测试
        config = DatabaseConfig.sqlite(":memory:")
        manager = get_database_manager()
        await manager.initialize()
        await manager.create_tables()
        yield manager
        await manager.close()

    @pytest.fixture
    async def db_session(self, db_manager):
        """数据库会话夹具"""
        async with db_manager.get_session() as session:
            yield session

    async def test_database_connection(self, db_manager):
        """测试数据库连接"""
        health = await db_manager.health_check()
        assert health["status"] == "healthy"
        assert health["database"] == "connected"

    async def test_order_model_operations(self, db_session):
        """测试订单模型操作"""
        # 创建订单模型
        order = OrderModel(
            symbol="0700.HK",
            side="buy",
            order_type="limit",
            quantity=1000,
            price=Decimal("350.50"),
            status="created"
        )

        db_session.add(order)
        await db_session.flush()

        # 验证创建
        assert order.id is not None
        assert order.symbol == "0700.HK"

        # 更新订单
        order.status = "submitted"
        order.submitted_at = datetime.utcnow()
        await db_session.flush()

        # 验证更新
        assert order.status == "submitted"

        # 查询订单
        from sqlalchemy import select
        query = select(OrderModel).where(OrderModel.symbol == "0700.HK")
        result = await db_session.execute(query)
        found_order = result.scalar_one()

        assert found_order.symbol == "0700.HK"
        assert found_order.status == "submitted"

    async def test_portfolio_model_operations(self, db_session):
        """测试投资组合模型操作"""
        # 创建投资组合
        portfolio = PortfolioModel(
            name="测试投资组合",
            description="用于测试的投资组合",
            portfolio_type="long_only",
            initial_capital=Decimal("1000000.00"),
            base_currency="HKD"
        )

        db_session.add(portfolio)
        await db_session.flush()

        # 验证创建
        assert portfolio.id is not None
        assert portfolio.name == "测试投资组合"
        assert portfolio.initial_capital == Decimal("1000000.00")

        # 更新投资组合
        portfolio.total_value = Decimal("1050000.00")
        portfolio.total_return = Decimal("50000.00")
        portfolio.total_return_percentage = Decimal("5.00")
        await db_session.flush()

        # 验证更新
        assert portfolio.total_value == Decimal("1050000.00")
        assert portfolio.total_return_percentage == Decimal("5.00")

    async def test_trade_model_operations(self, db_session):
        """测试交易模型操作"""
        # 创建交易
        trade = TradeModel(
            symbol="0700.HK",
            side="buy",
            quantity=1000,
            price=Decimal("350.50"),
            total_amount=Decimal("350500.00"),
            commission=Decimal("35.05"),
            trade_time=datetime.utcnow()
        )

        db_session.add(trade)
        await db_session.flush()

        # 验证创建
        assert trade.id is not None
        assert trade.symbol == "0700.HK"
        assert trade.quantity == 1000

        # 验证净成交金额计算
        assert trade.net_amount == Decimal("350464.95")  # total_amount - total_fees

    async def test_position_model_operations(self, db_session):
        """测试持仓模型操作"""
        # 先创建投资组合
        portfolio = PortfolioModel(
            name="测试投资组合",
            portfolio_type="long_only",
            initial_capital=Decimal("1000000.00")
        )
        db_session.add(portfolio)
        await db_session.flush()

        # 创建持仓
        position = PositionModel(
            symbol="0700.HK",
            portfolio_name="测试投资组合",
            portfolio_id=portfolio.id,
            quantity=1000,
            available_quantity=1000,
            side="long",
            average_cost=Decimal("300.00"),
            total_cost=Decimal("300000.00"),
            current_price=Decimal("350.50"),
            current_value=Decimal("350500.00"),
            unrealized_pnl=Decimal("50500.00")
        )

        db_session.add(position)
        await db_session.flush()

        # 验证创建
        assert position.id is not None
        assert position.symbol == "0700.HK"
        assert position.side == "long"

        # 验证属性计算
        assert position.net_position == 1000
        assert position.is_long_position is True
        assert position.is_short_position is False

    async def test_event_model_operations(self, db_session):
        """测试事件模型操作"""
        # 创建事件
        event = EventModel(
            event_type="OrderSubmitted",
            aggregate_type="Order",
            aggregate_id="550e8400-e29b-41d4-a716-446655440000",
            event_data={"order_id": "550e8400-e29b-41d4-a716-446655440000", "symbol": "0700.HK"},
            version=1,
            sequence_number=1,
            occurred_at=datetime.utcnow()
        )

        db_session.add(event)
        await db_session.flush()

        # 验证创建
        assert event.id is not None
        assert event.event_type == "OrderSubmitted"
        assert event.aggregate_type == "Order"
        assert event.is_processed is False

        # 测试标记为已处理
        event.mark_as_processed("test_processor")
        await db_session.flush()

        assert event.is_processed is True
        assert event.processed_at is not None

        # 测试标记为失败
        event_fail = EventModel(
            event_type="OrderFailed",
            aggregate_type="Order",
            aggregate_id="550e8400-e29b-41d4-a716-446655440000",
            event_data={"error": "Insufficient funds"},
            version=1,
            sequence_number=2
        )
        db_session.add(event_fail)
        await db_session.flush()

        event_fail.mark_as_failed("Insufficient funds", {"error_code": "E001"})
        await db_session.flush()

        assert event_fail.is_failed is True
        assert event_fail.retry_count == 1

    async def test_model_relationships(self, db_session):
        """测试模型关系"""
        # 创建投资组合
        portfolio = PortfolioModel(
            name="测试投资组合",
            portfolio_type="long_only",
            initial_capital=Decimal("1000000.00")
        )
        db_session.add(portfolio)
        await db_session.flush()

        # 创建订单
        order = OrderModel(
            symbol="0700.HK",
            side="buy",
            order_type="limit",
            quantity=1000,
            price=Decimal("350.50"),
            status="created",
            portfolio_name="测试投资组合"
        )
        db_session.add(order)
        await db_session.flush()

        # 创建交易
        trade = TradeModel(
            symbol="0700.HK",
            side="buy",
            quantity=1000,
            price=Decimal("350.50"),
            total_amount=Decimal("350500.00"),
            portfolio_name="测试投资组合",
            order_id=order.id
        )
        db_session.add(trade)
        await db_session.flush()

        # 验证关系
        assert trade.portfolio_name == "测试投资组合"
        assert trade.order_id == order.id

        # 测试级联删除
        await db_session.delete(order)
        await db_session.flush()

        # 交易应该仍然存在（根据外键设置）
        from sqlalchemy import select
        query = select(TradeModel).where(TradeModel.id == trade.id)
        result = await db_session.execute(query)
        found_trade = result.scalar_one_or_none()
        assert found_trade is not None

    async def test_database_constraints(self, db_session):
        """测试数据库约束"""
        # 测试唯一约束
        portfolio1 = PortfolioModel(
            name="唯一投资组合",
            portfolio_type="long_only",
            initial_capital=Decimal("1000000.00")
        )
        db_session.add(portfolio1)
        await db_session.flush()

        # 尝试创建同名投资组合
        portfolio2 = PortfolioModel(
            name="唯一投资组合",
            portfolio_type="long_only",
            initial_capital=Decimal("2000000.00")
        )
        db_session.add(portfolio2)

        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_complex_query_operations(self, db_session):
        """测试复杂查询操作"""
        # 创建多个投资组合
        portfolios = [
            PortfolioModel(name=f"投资组合{i}", portfolio_type="long_only", initial_capital=Decimal(f"{1000000 + i * 100000}.00"))
            for i in range(5)
        ]
        db_session.add_all(portfolios)
        await db_session.flush()

        # 测试聚合查询
        from sqlalchemy import func, select

        # 计算总投资组合数量
        query = select(func.count()).select_from(PortfolioModel)
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 5

        # 计算总初始资金
        query = select(func.sum(PortfolioModel.initial_capital))
        result = await db_session.execute(query)
        total_capital = result.scalar()
        assert total_capital == Decimal("6000000.00")

        # 测试条件查询
        from sqlalchemy import and_

        query = select(PortfolioModel).where(
            and_(
                PortfolioModel.initial_capital >= Decimal("2000000.00"),
                PortfolioModel.portfolio_type == "long_only"
            )
        )
        result = await db_session.execute(query)
        large_portfolios = result.scalars().all()
        assert len(large_portfolios) == 4

    async def test_concurrent_database_operations(self, db_session):
        """测试并发数据库操作"""
        import asyncio

        async def create_portfolio(name: str, capital: Decimal):
            """并发创建投资组合"""
            portfolio = PortfolioModel(
                name=name,
                portfolio_type="long_only",
                initial_capital=capital
            )
            db_session.add(portfolio)
            await db_session.flush()
            return portfolio

        # 并发创建多个投资组合
        tasks = [
            create_portfolio(f"并发投资组合{i}", Decimal(f"{1000000 + i * 100000}.00"))
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # 验证所有投资组合都成功创建
        assert len(results) == 10
        assert all(p.id is not None for p in results)

        # 验证没有重复的名称
        names = [p.name for p in results]
        assert len(names) == len(set(names))

    async def test_database_migrations(self, db_manager):
        """测试数据库迁移"""
        # 确保表存在
        await db_manager.create_tables(checkfirst=True)

        # 验证所有模型都已创建
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine.sync_engine)
        table_names = inspector.get_table_names()

        expected_tables = [
            "orders", "portfolios", "trades", "positions",
            "strategies", "stocks", "events"
        ]

        for table in expected_tables:
            assert table in table_names, f"Table {table} not found"

        # 验证表结构
        orders_columns = {c["name"] for c in inspector.get_columns("orders")}
        assert "symbol" in orders_columns
        assert "side" in orders_columns
        assert "quantity" in orders_columns
        assert "price" in orders_columns

    async def test_performance_benchmarks(self, db_session):
        """测试性能基准"""
        import time

        # 测试批量插入性能
        start_time = time.time()

        portfolios = [
            PortfolioModel(name=f"性能测试{i}", portfolio_type="long_only", initial_capital=Decimal("1000000.00"))
            for i in range(100)
        ]
        db_session.add_all(portfolios)
        await db_session.flush()

        insert_time = time.time() - start_time
        assert insert_time < 2.0  # 应该在2秒内完成

        # 测试查询性能
        start_time = time.time()

        from sqlalchemy import select
        for i in range(50):
            query = select(PortfolioModel).where(PortfolioModel.name == f"性能测试{i}")
            result = await db_session.execute(query)
            portfolio = result.scalar_one_or_none()
            assert portfolio is not None

        query_time = time.time() - start_time
        assert query_time < 1.0  # 应该在1秒内完成
