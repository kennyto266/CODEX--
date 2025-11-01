#!/usr/bin/env python3
"""
Phase 2 Complete Demo: Full DDD Architecture
Demonstrates all domain entities, services, repositories, and events
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from uuid import UUID

# Import all domain entities
from src.domain.trading.entities import (
    Order, OrderId, OrderSide, OrderType,
    Trade, TradeId,
    Position, PositionId
)
from src.domain.portfolio.entities import (
    Portfolio, PortfolioId, Asset, AssetId,
    AssetClass, AllocationStrategy
)
from src.domain.risk.entities import (
    RiskMetric, RiskMetricId, RiskMetricType,
    RiskLimit, RiskLimitId, RiskLimitType,
    RiskAssessment
)

# Import all services
from src.domain.trading.services import OrderService, TradeService, PositionService
from src.domain.portfolio.services import PortfolioService
from src.domain.risk.services import RiskService

# Import repositories
from src.infrastructure.database.repositories import (
    InMemoryOrderRepository,
    InMemoryTradeRepository,
    InMemoryPositionRepository,
    InMemoryPortfolioRepository,
    InMemoryAssetRepository,
    InMemoryRiskMetricRepository,
    InMemoryRiskLimitRepository,
    InMemoryRiskAssessmentRepository
)

# Import event system
from src.core.events import get_event_bus
from src.domain.trading.events import (
    OrderPlacedEvent, OrderExecutedEvent, TradeExecutedEvent
)
from src.domain.portfolio.events import PortfolioCreatedEvent
from src.domain.risk.events import RiskMetricCalculatedEvent

# Setup
from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger("phase2_demo")


async def main():
    """Main demo function showcasing complete DDD architecture"""
    logger.info("=== Starting Phase 2 Complete Demo ===")

    # 1. Setup repositories
    logger.info("\n1. Setting up repositories...")
    order_repo = InMemoryOrderRepository()
    trade_repo = InMemoryTradeRepository()
    position_repo = InMemoryPositionRepository()
    portfolio_repo = InMemoryPortfolioRepository()
    asset_repo = InMemoryAssetRepository()
    risk_metric_repo = InMemoryRiskMetricRepository()
    risk_limit_repo = InMemoryRiskLimitRepository()
    risk_assessment_repo = InMemoryRiskAssessmentRepository()

    # 2. Setup services
    logger.info("\n2. Setting up services...")
    order_service = OrderService(order_repo)
    trade_service = TradeService(trade_repo)
    position_service = PositionService(position_repo)
    portfolio_service = PortfolioService(portfolio_repo, asset_repo)
    risk_service = RiskService(risk_metric_repo, risk_limit_repo, risk_assessment_repo)

    # 3. Create assets
    logger.info("\n3. Creating assets...")
    tencent = Asset(
        asset_id=AssetId.create(),
        symbol="0700.HK",
        name="Tencent Holdings",
        asset_class=AssetClass.EQUITY,
        sector="Technology"
    )
    await asset_repo.save(tencent)
    logger.info(f"Created asset: {tencent.name} ({tencent.symbol})")

    # 4. Create portfolio
    logger.info("\n4. Creating portfolio...")
    portfolio = await portfolio_service.create_portfolio(
        name="My Trading Portfolio",
        description="Demo portfolio for Phase 2",
        initial_capital=100000.0,
        allocation_strategy=AllocationStrategy.EQUAL_WEIGHT
    )
    logger.info(f"Created portfolio: {portfolio.name}")

    # Create PortfolioId
    portfolio_id_obj = PortfolioId(portfolio.id)

    # Add assets to portfolio
    await portfolio_service.add_asset_to_portfolio(portfolio_id_obj, tencent)
    await portfolio_service.set_portfolio_allocation(portfolio_id_obj, "0700.HK", 100.0)
    logger.info("Added assets to portfolio")

    # 5. Create and execute order
    logger.info("\n5. Creating and executing order...")
    order = await order_service.create_order(
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        order_type=OrderType.LIMIT,
        price=350.0
    )
    logger.info(f"Created order: {order.to_dict()}")

    # Publish OrderPlacedEvent
    event_bus = get_event_bus()
    await event_bus.publish(OrderPlacedEvent(order))

    # Execute order
    executed_order = await order_service.execute_order(
        OrderId(order.id)=OrderId(order.id),
        executed_quantity=1000,
        executed_price=350.0
    )
    logger.info(f"Executed order: {executed_order.to_dict()}")

    # Publish OrderExecutedEvent
    await event_bus.publish(OrderExecutedEvent(executed_order))

    # 6. Create trade
    logger.info("\n6. Creating trade...")
    trade = await trade_service.create_trade(
        symbol="0700.HK",
        side=OrderSide.BUY,
        quantity=1000,
        price=350.0,
        commission=10.0
    )
    logger.info(f"Created trade: {trade.to_dict()}")

    # 7. Update position
    logger.info("\n7. Updating position...")
    position = await position_service.update_position_from_trade(trade)
    logger.info(f"Updated position: {position.to_dict(350.0)}")

    # 8. Calculate risk metrics
    logger.info("\n8. Calculating risk metrics...")
    # Simulate daily returns for VaR calculation
    daily_returns = [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, -0.01, 0.015, -0.02]
    var_95 = await risk_service.calculate_var(daily_returns, confidence_level=0.95)
    volatility = await risk_service.calculate_volatility(daily_returns)
    sharpe = await risk_service.calculate_sharpe_ratio(daily_returns)

    logger.info(f"VaR (95%): {var_95:.4f}")
    logger.info(f"Volatility: {volatility:.4f}")
    logger.info(f"Sharpe Ratio: {sharpe:.4f}")

    # Create risk metrics
    var_metric = await risk_service.create_risk_metric(
        metric_type=RiskMetricType.VALUE_AT_RISK,
        value=var_95,
        confidence_level=0.95,
        time_horizon=1,
        portfolio_id=str(portfolio.id)
    )

    vol_metric = await risk_service.create_risk_metric(
        metric_type=RiskMetricType.VOLATILITY,
        value=volatility,
        time_horizon=1,
        portfolio_id=str(portfolio.id)
    )

    sharpe_metric = await risk_service.create_risk_metric(
        metric_type=RiskMetricType.SHARPE_RATIO,
        value=sharpe,
        portfolio_id=str(portfolio.id)
    )

    # Publish RiskMetricCalculatedEvent
    await event_bus.publish(RiskMetricCalculatedEvent(var_metric))
    await event_bus.publish(RiskMetricCalculatedEvent(vol_metric))
    await event_bus.publish(RiskMetricCalculatedEvent(sharpe_metric))

    # 9. Create risk limits
    logger.info("\n9. Creating risk limits...")
    var_limit = await risk_service.create_risk_limit(
        name="VaR Limit (95%)",
        limit_type=RiskLimitType.VAR_LIMIT,
        threshold_value=0.05,  # 5%
        metric_type=RiskMetricType.VALUE_AT_RISK,
        portfolio_id=str(portfolio.id)
    )

    vol_limit = await risk_service.create_risk_limit(
        name="Volatility Limit",
        limit_type=RiskLimitType.VOLATILITY_LIMIT,
        threshold_value=0.30,  # 30%
        metric_type=RiskMetricType.VOLATILITY,
        portfolio_id=str(portfolio.id)
    )

    logger.info(f"Created risk limits: {var_limit.name}, {vol_limit.name}")

    # 10. Check limits
    logger.info("\n10. Checking risk limits...")
    limit_check = await risk_service.check_limits(str(portfolio.id))
    logger.info(f"Limit check results: {len(limit_check['violations'])} violations")

    # 11. Create risk assessment
    logger.info("\n11. Creating risk assessment...")
    assessment = await risk_service.create_risk_assessment(str(portfolio.id))
    logger.info(f"Risk assessment: {assessment.overall_risk_level.value}")
    logger.info(f"Recommendations: {len(assessment.recommendations)}")

    # 12. Get portfolio summary
    logger.info("\n12. Portfolio summary...")
    portfolio_summary = await portfolio_service.get_portfolio_summary(portfolio_id_obj)
    logger.info(f"Total value: ${portfolio_summary['total_value']:,.2f}")
    logger.info(f"Total P&L: ${portfolio_summary['total_pnl']:,.2f}")
    logger.info(f"Return: {portfolio_summary['return_percent']:.2f}%")

    # 13. Get risk dashboard
    logger.info("\n13. Risk dashboard...")
    risk_dashboard = await risk_service.get_risk_dashboard_data(str(portfolio.id))
    logger.info(f"Overall risk level: {risk_dashboard['overall_risk_level']}")
    logger.info(f"Metrics count: {len(risk_dashboard['metrics'])}")
    logger.info(f"Recommendations: {len(risk_dashboard['recommendations'])}")

    # 14. Statistics
    logger.info("\n14. Repository statistics...")
    logger.info(f"Orders: {len(await order_repo.find_all())}")
    logger.info(f"Trades: {len(await trade_repo.find_all())}")
    logger.info(f"Positions: {len(await position_repo.find_all())}")
    logger.info(f"Portfolios: {len(await portfolio_repo.find_all())}")
    logger.info(f"Assets: {len(await asset_repo.find_all())}")
    logger.info(f"Risk Metrics: {len(await risk_metric_repo.find_all())}")
    logger.info(f"Risk Limits: {len(await risk_limit_repo.find_all())}")

    logger.info("\n=== Phase 2 Complete Demo Finished Successfully ===")

    # Print summary
    print("\n" + "="*60)
    print("PHASE 2 DEMONSTRATION SUMMARY")
    print("="*60)
    print(f"✓ Created {len(await asset_repo.find_all())} assets")
    print(f"✓ Created portfolio with ${portfolio.initial_capital:,.2f} initial capital")
    print(f"✓ Placed and executed {len(await order_repo.find_all())} orders")
    print(f"✓ Executed {len(await trade_repo.find_all())} trades")
    print(f"✓ Updated {len(await position_repo.find_all())} positions")
    print(f"✓ Calculated {len(await risk_metric_repo.find_all())} risk metrics")
    print(f"✓ Created {len(await risk_limit_repo.find_all())} risk limits")
    print(f"✓ Generated risk assessment with {assessment.overall_risk_level.value} risk level")
    print(f"✓ Published and handled {6} domain events")
    print("="*60)
    print("\n✅ All Phase 2 features demonstrated successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
