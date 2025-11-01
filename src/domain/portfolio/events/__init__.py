"""
Portfolio Domain Events
"""
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from ...entities import DomainEvent
from ..entities import Portfolio, Allocation


class PortfolioCreatedEvent(DomainEvent):
    """Event fired when a portfolio is created"""

    def __init__(self, portfolio: Portfolio):
        super().__init__()
        self.event_type = "Portfolio.Created"
        self.event_data = {
            "portfolio_id": str(portfolio.id),
            "name": portfolio.name,
            "initial_capital": portfolio.initial_capital,
            "allocation_strategy": portfolio.allocation_strategy.value,
            "timestamp": datetime.now().isoformat()
        }


class AssetAddedEvent(DomainEvent):
    """Event fired when an asset is added to a portfolio"""

    def __init__(self, portfolio_id: UUID, symbol: str, target_allocation: float):
        super().__init__()
        self.event_type = "Portfolio.AssetAdded"
        self.event_data = {
            "portfolio_id": str(portfolio_id),
            "symbol": symbol,
            "target_allocation": target_allocation,
            "timestamp": datetime.now().isoformat()
        }


class AllocationUpdatedEvent(DomainEvent):
    """Event fired when portfolio allocation is updated"""

    def __init__(self, portfolio_id: UUID, symbol: str, old_allocation: float, new_allocation: float):
        super().__init__()
        self.event_type = "Portfolio.AllocationUpdated"
        self.event_data = {
            "portfolio_id": str(portfolio_id),
            "symbol": symbol,
            "old_allocation": old_allocation,
            "new_allocation": new_allocation,
            "change": new_allocation - old_allocation,
            "timestamp": datetime.now().isoformat()
        }


class PortfolioRebalancedEvent(DomainEvent):
    """Event fired when a portfolio is rebalanced"""

    def __init__(self, portfolio_id: UUID, trades: Dict[str, float]):
        super().__init__()
        self.event_type = "Portfolio.Rebalanced"
        self.event_data = {
            "portfolio_id": str(portfolio_id),
            "trades": trades,
            "trade_count": len(trades),
            "timestamp": datetime.now().isoformat()
        }
