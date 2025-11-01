"""
Repository unit tests
"""
import pytest
import asyncio
from uuid import uuid4

from src.domain.trading.entities import Order, OrderId, OrderSide, OrderType
from src.domain.portfolio.entities import Portfolio, PortfolioId, Asset, AssetId, AssetClass, AllocationStrategy
from src.domain.risk.entities import RiskMetric, RiskMetricId, RiskMetricType
from src.infrastructure.database.repositories import (
    InMemoryOrderRepository,
    InMemoryPortfolioRepository,
    InMemoryAssetRepository,
    InMemoryRiskMetricRepository,
)


@pytest.mark.asyncio
async def test_order_repository():
    """Test order repository operations"""
    repo = InMemoryOrderRepository()

    # Create an order
    order_id = OrderId.create()
    order = Order(
        order_id=order_id,
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )

    # Save order
    await repo.save(order)

    # Find by ID
    found_order = await repo.find_by_id(order_id.value)
    assert found_order is not None
    assert found_order.symbol == "0700.HK"
    assert found_order.side == OrderSide.BUY

    # Check exists
    assert await repo.exists(order_id.value) is True

    # Find all
    all_orders = await repo.find_all()
    assert len(all_orders) == 1

    # Update order
    order.execute(500, 350.0)
    await repo.save(order)
    updated_order = await repo.find_by_id(order_id.value)
    assert updated_order.executed_quantity == 500

    # Delete order
    assert await repo.delete(order_id.value) is True
    assert await repo.find_by_id(order_id.value) is None
    assert await repo.exists(order_id.value) is False


@pytest.mark.asyncio
async def test_portfolio_repository():
    """Test portfolio repository operations"""
    portfolio_repo = InMemoryPortfolioRepository()
    asset_repo = InMemoryAssetRepository()

    # Create an asset
    asset_id = AssetId.create()
    asset = Asset(
        asset_id=asset_id,
        symbol="0700.HK",
        name="Tencent Holdings",
        asset_class=AssetClass.EQUITY
    )
    await asset_repo.save(asset)

    # Create a portfolio
    portfolio_id = PortfolioId.create()
    portfolio = Portfolio(
        portfolio_id=portfolio_id,
        name="My Portfolio",
        description="Test portfolio",
        initial_capital=100000.0,
        allocation_strategy=AllocationStrategy.EQUAL_WEIGHT
    )

    # Add asset to portfolio
    portfolio.add_asset(asset)
    portfolio.set_allocation("0700.HK", 50.0)

    # Save portfolio
    await portfolio_repo.save(portfolio)

    # Find by ID
    found_portfolio = await portfolio_repo.find_by_id(portfolio_id.value)
    assert found_portfolio is not None
    assert found_portfolio.name == "My Portfolio"
    assert found_portfolio.asset_count == 1

    # Find all
    all_portfolios = await portfolio_repo.find_all()
    assert len(all_portfolios) == 1

    # Delete portfolio
    await portfolio_repo.delete(portfolio_id.value)
    assert await portfolio_repo.find_by_id(portfolio_id.value) is None


@pytest.mark.asyncio
async def test_risk_metric_repository():
    """Test risk metric repository operations"""
    repo = InMemoryRiskMetricRepository()

    # Create a risk metric
    metric_id = RiskMetricId.create()
    metric = RiskMetric(
        metric_id=metric_id,
        metric_type=RiskMetricType.VOLATILITY,
        value=0.25,
        confidence_level=0.95,
        time_horizon=1
    )

    # Save metric
    await repo.save(metric)

    # Find by ID
    found_metric = await repo.find_by_id(metric_id.value)
    assert found_metric is not None
    assert found_metric.metric_type == RiskMetricType.VOLATILITY
    assert found_metric.value == 0.25

    # Check exists
    assert await repo.exists(metric_id.value) is True

    # Find all
    all_metrics = await repo.find_all()
    assert len(all_metrics) == 1

    # Delete metric
    await repo.delete(metric_id.value)
    assert await repo.find_by_id(metric_id.value) is None


@pytest.mark.asyncio
async def test_repository_integration():
    """Test integration between repositories"""
    order_repo = InMemoryOrderRepository()
    portfolio_repo = InMemoryPortfolioRepository()
    asset_repo = InMemoryAssetRepository()

    # Create asset
    asset_id = AssetId.create()
    asset = Asset(
        asset_id=asset_id,
        symbol="0700.HK",
        name="Tencent",
        asset_class=AssetClass.EQUITY
    )
    await asset_repo.save(asset)

    # Create portfolio
    portfolio_id = PortfolioId.create()
    portfolio = Portfolio(
        portfolio_id=portfolio_id,
        name="Test Portfolio",
        initial_capital=100000.0
    )
    portfolio.add_asset(asset)
    await portfolio_repo.save(portfolio)

    # Create order
    order_id = OrderId.create()
    order = Order(
        order_id=order_id,
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )
    await order_repo.save(order)

    # Verify all entities exist
    assert await asset_repo.find_by_id(asset_id.value) is not None
    assert await portfolio_repo.find_by_id(portfolio_id.value) is not None
    assert await order_repo.find_by_id(order_id.value) is not None

    # Clean up
    await order_repo.delete(order_id.value)
    await portfolio_repo.delete(portfolio_id.value)
    await asset_repo.delete(asset_id.value)

    # Verify all deleted
    assert await order_repo.find_by_id(order_id.value) is None
    assert await portfolio_repo.find_by_id(portfolio_id.value) is None
    assert await asset_repo.find_by_id(asset_id.value) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
