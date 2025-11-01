"""
Event Handlers
"""
import asyncio
from typing import Dict, Any

from src.core.logging import get_logger
from src.core.events import get_event_bus

# Get logger for event handlers
logger = get_logger("event_handlers")


# ===== Trading Event Handlers =====

async def handle_order_executed(event):
    """Handle order execution - update position and publish trade event"""
    from src.domain.trading.events import TradeExecutedEvent
    from src.domain.trading.entities import Trade, TradeId, OrderSide
    from src.domain.trading.services import PositionService
    from src.infrastructure.database.repositories import InMemoryPositionRepository

    # Get order data from event
    order_data = event.event_data
    symbol = order_data["symbol"]
    side = order_data["side"]
    executed_quantity = order_data["executed_quantity"]
    executed_price = order_data["executed_price"]

    # Create trade
    trade_id = TradeId.create()
    trade = Trade(
        trade_id=trade_id,
        symbol=symbol,
        side=OrderSide(side),
        quantity=executed_quantity,
        price=executed_price
    )

    # Update position
    position_service = PositionService(InMemoryPositionRepository())
    await position_service.update_position_from_trade(trade)

    # Publish trade executed event
    event_bus = get_event_bus()
    trade_event = TradeExecutedEvent(trade)
    await event_bus.publish(trade_event)

    logger.info(
        "Order executed and position updated",
        order_id=order_data["order_id"],
        symbol=symbol,
        quantity=executed_quantity,
        price=executed_price
    )


async def handle_trade_executed(event):
    """Handle trade execution - log trade details"""
    trade_data = event.event_data

    logger.info(
        "Trade executed",
        trade_id=trade_data["trade_id"],
        symbol=trade_data["symbol"],
        quantity=trade_data["quantity"],
        price=trade_data["price"],
        net_amount=trade_data["net_amount"]
    )


async def handle_position_updated(event):
    """Handle position update - check for concentration risk"""
    position_data = event.event_data
    symbol = position_data["symbol"]
    new_quantity = position_data["new_quantity"]
    change = position_data["change"]

    # Log position change
    logger.info(
        "Position updated",
        symbol=symbol,
        old_quantity=position_data["old_quantity"],
        new_quantity=new_quantity,
        change=change
    )

    # In real implementation, check for concentration risk
    # and trigger alerts if needed


# ===== Portfolio Event Handlers =====

async def handle_portfolio_rebalance_required(event):
    """Handle portfolio rebalance requirement"""
    event_data = event.event_data
    portfolio_id = event_data["portfolio_id"]
    threshold = event_data["deviation_threshold"]

    logger.warning(
        "Portfolio rebalancing required",
        portfolio_id=portfolio_id,
        deviation_threshold=threshold
    )

    # In real implementation, trigger rebalancing process
    # This could be done asynchronously


async def handle_allocation_updated(event):
    """Handle allocation update"""
    event_data = event.event_data

    logger.info(
        "Portfolio allocation updated",
        portfolio_id=event_data["portfolio_id"],
        symbol=event_data["symbol"],
        old_allocation=event_data["old_allocation"],
        new_allocation=event_data["new_allocation"]
    )


# ===== Risk Event Handlers =====

async def handle_risk_metric_calculated(event):
    """Handle risk metric calculation"""
    metric_data = event.event_data
    metric_type = metric_data["metric_type"]
    risk_level = metric_data["risk_level"]

    logger.info(
        "Risk metric calculated",
        metric_type=metric_type,
        value=metric_data["value"],
        risk_level=risk_level
    )

    # Log high risk metrics
    if risk_level in ["HIGH", "CRITICAL"]:
        logger.warning(
            "High risk detected",
            metric_type=metric_type,
            value=metric_data["value"],
            risk_level=risk_level
        )


async def handle_risk_limit_violation(event):
    """Handle risk limit violation"""
    event_data = event.event_data
    limit_name = event_data["limit_name"]
    severity = event_data["severity"]

    # Log violation based on severity
    if severity == "CRITICAL":
        logger.critical(
            "CRITICAL: Risk limit violated",
            limit_name=limit_name,
            metric_value=event_data["metric_value"],
            threshold=event_data["threshold"],
            breach_amount=event_data["breach_amount"]
        )
    else:
        logger.warning(
            "Risk limit violated",
            limit_name=limit_name,
            metric_value=event_data["metric_value"],
            threshold=event_data["threshold"],
            breach_amount=event_data["breach_amount"]
        )


async def handle_portfolio_risk_assessment(event):
    """Handle portfolio risk assessment completion"""
    event_data = event.event_data
    risk_level = event_data["overall_risk_level"]
    violation_count = event_data["violation_count"]

    logger.info(
        "Portfolio risk assessment completed",
        portfolio_id=event_data["portfolio_id"],
        overall_risk_level=risk_level,
        violation_count=violation_count
    )


async def handle_risk_alert(event):
    """Handle risk alert"""
    event_data = event.event_data
    alert_type = event_data["alert_type"]
    severity = event_data["severity"]

    # Log alert based on severity
    if severity == "CRITICAL":
        logger.critical(
            "CRITICAL RISK ALERT",
            alert_type=alert_type,
            message=event_data["message"],
            portfolio_id=event_data["portfolio_id"]
        )
    elif severity == "HIGH":
        logger.error(
            "HIGH RISK ALERT",
            alert_type=alert_type,
            message=event_data["message"],
            portfolio_id=event_data["portfolio_id"]
        )
    else:
        logger.warning(
            "Risk alert",
            alert_type=alert_type,
            message=event_data["message"],
            portfolio_id=event_data["portfolio_id"]
        )


# ===== Event Handler Registration =====

def register_all_event_handlers():
    """Register all event handlers with the event bus"""
    event_bus = get_event_bus()

    # Import events to ensure classes are defined
    from src.domain.trading.events import (
        OrderExecutedEvent,
        TradeExecutedEvent,
        PositionUpdatedEvent,
        PortfolioRebalanceRequiredEvent,
        AllocationUpdatedEvent,
    )
    from src.domain.portfolio.events import (
        PortfolioCreatedEvent,
        AssetAddedEvent,
        PortfolioRebalancedEvent,
    )
    from src.domain.risk.events import (
        RiskMetricCalculatedEvent,
        RiskLimitViolationEvent,
        PortfolioRiskAssessmentEvent,
        RiskAlertEvent,
    )

    # Register trading event handlers
    event_bus.subscribe(OrderExecutedEvent, handle_order_executed)
    event_bus.subscribe(TradeExecutedEvent, handle_trade_executed)
    event_bus.subscribe(PositionUpdatedEvent, handle_position_updated)
    event_bus.subscribe(PortfolioRebalanceRequiredEvent, handle_portfolio_rebalance_required)
    event_bus.subscribe(AllocationUpdatedEvent, handle_allocation_updated)

    # Register portfolio event handlers
    event_bus.subscribe(PortfolioCreatedEvent, lambda e: logger.info("Portfolio created", portfolio_id=e.event_data["portfolio_id"]))
    event_bus.subscribe(AssetAddedEvent, lambda e: logger.info("Asset added", symbol=e.event_data["symbol"]))
    event_bus.subscribe(PortfolioRebalancedEvent, lambda e: logger.info("Portfolio rebalanced", portfolio_id=e.event_data["portfolio_id"]))

    # Register risk event handlers
    event_bus.subscribe(RiskMetricCalculatedEvent, handle_risk_metric_calculated)
    event_bus.subscribe(RiskLimitViolationEvent, handle_risk_limit_violation)
    event_bus.subscribe(PortfolioRiskAssessmentEvent, handle_portfolio_risk_assessment)
    event_bus.subscribe(RiskAlertEvent, handle_risk_alert)

    logger.info("All event handlers registered successfully")


# Auto-register handlers when module is imported
register_all_event_handlers()
