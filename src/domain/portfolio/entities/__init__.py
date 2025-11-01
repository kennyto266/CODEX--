"""
Portfolio Domain Entities
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional, Dict, Any, List
from ...entities import DomainEntity


class AssetClass(Enum):
    """Asset class enumeration"""
    EQUITY = "equity"
    BOND = "bond"
    COMMODITY = "commodity"
    CASH = "cash"
    CRYPTO = "crypto"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class AllocationStrategy(Enum):
    """Allocation strategy enumeration"""
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP = "market_cap"
    VOLATILITY_WEIGHT = "volatility_weight"
    RISK_PARITY = "risk_parity"
    CUSTOM = "custom"


@dataclass
class PortfolioId:
    """Value object for portfolio ID"""
    value: UUID

    @staticmethod
    def create() -> PortfolioId:
        return PortfolioId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class AssetId:
    """Value object for asset ID"""
    value: UUID

    @staticmethod
    def create() -> AssetId:
        return AssetId(uuid4())

    def __str__(self) -> str:
        return str(self.value)


class Asset(DomainEntity):
    """
    Asset entity
    Represents a financial instrument
    """

    def __init__(
        self,
        asset_id: AssetId,
        symbol: str,
        name: str,
        asset_class: AssetClass,
        currency: str = "HKD",
        sector: Optional[str] = None
    ):
        from datetime import datetime
        super().__init__(id=asset_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._symbol = symbol
        self._name = name
        self._asset_class = asset_class
        self._currency = currency
        self._sector = sector

    @property
    def symbol(self) -> str:
        """Get asset symbol"""
        return self._symbol

    @property
    def name(self) -> str:
        """Get asset name"""
        return self._name

    @property
    def asset_class(self) -> AssetClass:
        """Get asset class"""
        return self._asset_class

    @property
    def currency(self) -> str:
        """Get currency"""
        return self._currency

    @property
    def sector(self) -> Optional[str]:
        """Get sector"""
        return self._sector

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "symbol": self._symbol,
            "name": self._name,
            "asset_class": self._asset_class.value,
            "currency": self._currency,
            "sector": self._sector,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Allocation:
    """
    Value object representing asset allocation
    """
    asset_id: AssetId
    target_percentage: float
    current_percentage: float = 0.0

    def __post_init__(self):
        """Validate allocation"""
        if self.target_percentage < 0 or self.target_percentage > 100:
            raise ValueError("Target percentage must be between 0 and 100")

    @property
    def deviation(self) -> float:
        """Calculate deviation from target"""
        return self.current_percentage - self.target_percentage

    def is_within_tolerance(self, tolerance: float = 5.0) -> bool:
        """Check if allocation is within tolerance"""
        return abs(self.deviation) <= tolerance

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "asset_id": str(self.asset_id.value),
            "target_percentage": self.target_percentage,
            "current_percentage": self.current_percentage,
            "deviation": self.deviation,
            "within_tolerance": self.is_within_tolerance()
        }


class Portfolio(DomainEntity):
    """
    Portfolio aggregate root
    Manages a collection of assets and their allocations
    """

    def __init__(
        self,
        portfolio_id: PortfolioId,
        name: str,
        description: Optional[str] = None,
        initial_capital: float = 0.0,
        allocation_strategy: AllocationStrategy = AllocationStrategy.EQUAL_WEIGHT
    ):
        from datetime import datetime
        super().__init__(id=portfolio_id.value, created_at=datetime.now(), updated_at=datetime.now())

        self._name = name
        self._description = description
        self._initial_capital = initial_capital
        self._current_capital = initial_capital
        self._allocation_strategy = allocation_strategy
        self._assets: Dict[str, Asset] = {}
        self._allocations: Dict[str, Allocation] = {}
        self._total_value = 0.0
        self._total_pnl = 0.0
        self._return_percent = 0.0

    @property
    def name(self) -> str:
        """Get portfolio name"""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Get portfolio description"""
        return self._description

    @property
    def initial_capital(self) -> float:
        """Get initial capital"""
        return self._initial_capital

    @property
    def current_capital(self) -> float:
        """Get current capital"""
        return self._current_capital

    @property
    def allocation_strategy(self) -> AllocationStrategy:
        """Get allocation strategy"""
        return self._allocation_strategy

    @property
    def total_value(self) -> float:
        """Get total portfolio value"""
        return self._total_value

    @property
    def total_pnl(self) -> float:
        """Get total P&L"""
        return self._total_pnl

    @property
    def return_percent(self) -> float:
        """Get return percentage"""
        return self._return_percent

    @property
    def assets(self) -> List[Asset]:
        """Get all assets"""
        return list(self._assets.values())

    @property
    def allocations(self) -> List[Allocation]:
        """Get all allocations"""
        return list(self._allocations.values())

    @property
    def asset_count(self) -> int:
        """Get number of assets"""
        return len(self._assets)

    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the portfolio"""
        if asset.symbol in self._assets:
            raise ValueError(f"Asset {asset.symbol} already exists in portfolio")

        self._assets[asset.symbol] = asset
        self._allocations[asset.symbol] = Allocation(
            asset_id=asset.id,
            target_percentage=0.0,
            current_percentage=0.0
        )
        self._mark_updated()

    def remove_asset(self, symbol: str) -> None:
        """Remove an asset from the portfolio"""
        if symbol not in self._assets:
            raise ValueError(f"Asset {symbol} not found in portfolio")

        del self._assets[symbol]
        del self._allocations[symbol]
        self._mark_updated()

    def set_allocation(self, symbol: str, target_percentage: float) -> None:
        """Set target allocation for an asset"""
        if symbol not in self._assets:
            raise ValueError(f"Asset {symbol} not found in portfolio")

        self._allocations[symbol].target_percentage = target_percentage
        self._mark_updated()

    def update_allocation(self, symbol: str, current_percentage: float) -> None:
        """Update current allocation for an asset"""
        if symbol not in self._allocations:
            raise ValueError(f"Allocation for {symbol} not found")

        self._allocations[symbol].current_percentage = current_percentage
        self._mark_updated()

    def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get an asset by symbol"""
        return self._assets.get(symbol)

    def get_allocation(self, symbol: str) -> Optional[Allocation]:
        """Get allocation by symbol"""
        return self._allocations.get(symbol)

    def get_overallocated_assets(self, tolerance: float = 5.0) -> List[Allocation]:
        """Get assets that are over allocated beyond tolerance"""
        return [alloc for alloc in self._allocations.values()
                if alloc.deviation > tolerance]

    def get_underallocated_assets(self, tolerance: float = 5.0) -> List[Allocation]:
        """Get assets that are under allocated beyond tolerance"""
        return [alloc for alloc in self._allocations.values()
                if alloc.deviation < -tolerance]

    def calculate_total_value(self, market_values: Dict[str, float]) -> None:
        """Calculate total portfolio value"""
        total = sum(market_values.get(symbol, 0.0) for symbol in self._assets.keys())
        self._total_value = total

        # Calculate P&L
        self._total_pnl = self._total_value - self._initial_capital

        # Calculate return percentage
        if self._initial_capital > 0:
            self._return_percent = (self._total_pnl / self._initial_capital) * 100

        self._mark_updated()

    def calculate_allocation_percentages(self, market_values: Dict[str, float]) -> None:
        """Calculate current allocation percentages based on market values"""
        if self._total_value == 0:
            return

        for symbol in self._assets.keys():
            market_value = market_values.get(symbol, 0.0)
            current_percentage = (market_value / self._total_value) * 100
            self.update_allocation(symbol, current_percentage)

    def rebalance(self, tolerance: float = 5.0) -> Dict[str, float]:
        """
        Calculate rebalancing trades needed
        Returns a dict of symbol -> quantity_change
        """
        trades = {}

        for symbol, allocation in self._allocations.items():
            deviation = allocation.deviation

            # If deviation is significant, calculate rebalance quantity
            if abs(deviation) > tolerance:
                # This is a simplified calculation
                # In reality, you'd use current price and market value
                target_value = (allocation.target_percentage / 100) * self._total_value
                current_value = (allocation.current_percentage / 100) * self._total_value
                value_diff = target_value - current_value

                # Assume we have current price (in real implementation, get from market data)
                current_price = 100.0  # Placeholder
                quantity_change = value_diff / current_price

                if abs(quantity_change) > 0.01:  # Only include significant trades
                    trades[symbol] = quantity_change

        return trades

    def is_balanced(self, tolerance: float = 5.0) -> bool:
        """Check if portfolio is balanced within tolerance"""
        return all(alloc.is_within_tolerance(tolerance) for alloc in self._allocations.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self._name,
            "description": self._description,
            "initial_capital": self._initial_capital,
            "current_capital": self._current_capital,
            "allocation_strategy": self._allocation_strategy.value,
            "total_value": self._total_value,
            "total_pnl": self._total_pnl,
            "return_percent": self._return_percent,
            "asset_count": self.asset_count,
            "is_balanced": self.is_balanced(),
            "assets": [asset.to_dict() for asset in self.assets],
            "allocations": [alloc.to_dict() for alloc in self.allocations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
