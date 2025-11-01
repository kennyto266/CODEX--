"""
Portfolio Domain Services
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities import Portfolio, PortfolioId, Asset, AssetId, Allocation, AllocationStrategy
from ...repositories import Repository


class PortfolioService:
    """Domain service for portfolio operations"""

    def __init__(self, portfolio_repository: Repository[Portfolio], asset_repository: Repository[Asset]):
        self._portfolio_repository = portfolio_repository
        self._asset_repository = asset_repository

    async def create_portfolio(
        self,
        name: str,
        description: Optional[str] = None,
        initial_capital: float = 0.0,
        allocation_strategy: AllocationStrategy = AllocationStrategy.EQUAL_WEIGHT
    ) -> Portfolio:
        """Create a new portfolio"""
        portfolio_id = PortfolioId.create()
        portfolio = Portfolio(
            portfolio_id=portfolio_id,
            name=name,
            description=description,
            initial_capital=initial_capital,
            allocation_strategy=allocation_strategy
        )

        await self._portfolio_repository.save(portfolio)
        return portfolio

    async def get_portfolio_by_id(self, portfolio_id: PortfolioId) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        return await self._portfolio_repository.find_by_id(portfolio_id.value)

    async def get_all_portfolios(self) -> List[Portfolio]:
        """Get all portfolios"""
        return await self._portfolio_repository.find_all()

    async def add_asset_to_portfolio(self, portfolio_id: PortfolioId, asset: Asset) -> Portfolio:
        """Add an asset to a portfolio"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        portfolio.add_asset(asset)
        await self._portfolio_repository.save(portfolio)
        return portfolio

    async def remove_asset_from_portfolio(self, portfolio_id: PortfolioId, symbol: str) -> Portfolio:
        """Remove an asset from a portfolio"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        portfolio.remove_asset(symbol)
        await self._portfolio_repository.save(portfolio)
        return portfolio

    async def set_portfolio_allocation(
        self,
        portfolio_id: PortfolioId,
        symbol: str,
        target_percentage: float
    ) -> Portfolio:
        """Set target allocation for an asset"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        portfolio.set_allocation(symbol, target_percentage)
        await self._portfolio_repository.save(portfolio)
        return portfolio

    async def rebalance_portfolio(self, portfolio_id: PortfolioId, tolerance: float = 5.0) -> Dict[str, Any]:
        """Rebalance portfolio to target allocations"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        # Get current market values (in real implementation, get from market data service)
        # For now, use placeholder prices
        market_values = {}
        for asset in portfolio.assets:
            market_values[asset.symbol] = 100.0  # Placeholder price

        # Calculate total value and current allocations
        portfolio.calculate_total_value(market_values)
        portfolio.calculate_allocation_percentages(market_values)

        # Calculate rebalancing trades
        rebalancing_trades = portfolio.rebalance(tolerance)

        await self._portfolio_repository.save(portfolio)

        return {
            "portfolio_id": str(portfolio_id.value),
            "total_value": portfolio.total_value,
            "rebalancing_trades": rebalancing_trades,
            "is_balanced": portfolio.is_balanced(tolerance),
            "current_allocations": [alloc.to_dict() for alloc in portfolio.allocations]
        }

    async def get_portfolio_performance(self, portfolio_id: PortfolioId) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        # In real implementation, get historical prices and calculate returns
        # For now, return basic metrics
        return {
            "portfolio_id": str(portfolio_id.value),
            "name": portfolio.name,
            "initial_capital": portfolio.initial_capital,
            "current_capital": portfolio.current_capital,
            "total_value": portfolio.total_value,
            "total_pnl": portfolio.total_pnl,
            "return_percent": portfolio.return_percent,
            "allocation_strategy": portfolio.allocation_strategy.value,
            "asset_count": portfolio.asset_count,
            "is_balanced": portfolio.is_balanced(),
        }

    async def get_portfolio_risk_analysis(self, portfolio_id: PortfolioId) -> Dict[str, Any]:
        """Get portfolio risk analysis"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        allocations = portfolio.allocations

        # Calculate concentration risk
        max_allocation = max(alloc.current_percentage for alloc in allocations) if allocations else 0

        # Calculate diversification score (simplified)
        if allocations:
            # HHI (Herfindahl-Hirschman Index) - measures concentration
            hhi = sum((alloc.current_percentage / 100) ** 2 for alloc in allocations)
            diversification_score = 1 - hhi  # Higher is more diversified
        else:
            diversification_score = 0

        # Identify over/under allocated assets
        over_allocated = portfolio.get_overallocated_assets()
        under_allocated = portfolio.get_underallocated_assets()

        return {
            "portfolio_id": str(portfolio_id.value),
            "max_single_allocation": max_allocation,
            "diversification_score": diversification_score,
            "concentration_risk": "HIGH" if max_allocation > 30 else "MEDIUM" if max_allocation > 20 else "LOW",
            "over_allocated_assets": [alloc.to_dict() for alloc in over_allocated],
            "under_allocated_assets": [alloc.to_dict() for alloc in under_allocated],
            "needs_rebalancing": not portfolio.is_balanced(),
        }

    async def get_portfolio_summary(self, portfolio_id: PortfolioId) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        performance = await self.get_portfolio_performance(portfolio_id)
        risk_analysis = await self.get_portfolio_risk_analysis(portfolio_id)

        return {
            "portfolio": portfolio.to_dict(),
            "performance": performance,
            "risk_analysis": risk_analysis,
            "generated_at": datetime.now().isoformat(),
        }
