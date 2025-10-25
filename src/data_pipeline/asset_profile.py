"""
Asset Profile System for CODEX quantitative trading.

This module provides asset metadata and trading parameters:
- AssetProfile: Defines trading parameters for a single asset
- AssetProfileRegistry: Central registry for all asset profiles
- Predefined profiles for common HK stocks

An asset profile contains:
- Basic metadata (symbol, name, market, currency)
- Trading parameters (multiplier, lot size, position limits)
- Cost parameters (commission, slippage)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum
import json


class Market(Enum):
    """Supported trading markets."""
    HKEX = "HKEX"  # Hong Kong Exchanges and Clearing Limited
    NYSE = "NYSE"  # New York Stock Exchange
    NASDAQ = "NASDAQ"  # NASDAQ Stock Market
    SSE = "SSE"  # Shanghai Stock Exchange
    SZSE = "SZSE"  # Shenzhen Stock Exchange


class Currency(Enum):
    """Supported trading currencies."""
    HKD = "HKD"  # Hong Kong Dollar
    USD = "USD"  # US Dollar
    CNY = "CNY"  # Chinese Yuan
    EUR = "EUR"  # Euro


@dataclass
class AssetProfile:
    """
    Trading metadata and parameters for a single asset.

    Attributes:
        symbol: Unique ticker symbol (e.g., '0700.HK')
        name: Company or asset name (e.g., 'Tencent Holdings')
        market: Trading market (HKEX, NYSE, etc.)
        currency: Trading currency (HKD, USD, etc.)
        multiplier: Contract multiplier (usually 1.0 for stocks)
        min_lot_size: Minimum order quantity
        max_position: Maximum position size in units (None = unlimited)
        commission_fixed: Fixed commission per trade (in base currency)
        commission_pct: Percentage commission (0.001 = 0.1%)
        slippage_bps: Expected slippage in basis points (0.05% = 5 bps)
        description: Optional description of the asset
        metadata: Additional custom metadata
    """

    symbol: str
    name: str
    market: Market
    currency: Currency

    # Trading parameters
    multiplier: float = 1.0
    min_lot_size: int = 100
    max_position: Optional[float] = None

    # Cost parameters
    commission_fixed: float = 0.0
    commission_pct: float = 0.001
    slippage_bps: float = 5.0

    # Optional metadata
    description: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.multiplier <= 0:
            raise ValueError(f"Multiplier must be positive, got {self.multiplier}")
        if self.min_lot_size <= 0:
            raise ValueError(f"Min lot size must be positive, got {self.min_lot_size}")
        if self.max_position is not None and self.max_position <= 0:
            raise ValueError(f"Max position must be positive or None, got {self.max_position}")
        if self.commission_fixed < 0:
            raise ValueError(f"Commission fixed must be non-negative, got {self.commission_fixed}")
        if not (0 <= self.commission_pct <= 0.1):
            raise ValueError(f"Commission percentage must be 0-10%, got {self.commission_pct*100}%")
        if not (0 <= self.slippage_bps <= 100):
            raise ValueError(f"Slippage must be 0-100 bps, got {self.slippage_bps}")

    @property
    def total_cost_bps(self) -> float:
        """
        Total trading cost in basis points.

        Combines percentage commission and slippage.
        Fixed commission is not included as it depends on position size.
        """
        return (self.commission_pct * 10000) + self.slippage_bps

    @property
    def total_cost_pct(self) -> float:
        """Total trading cost as percentage (0.005 = 0.5%)."""
        return self.total_cost_bps / 10000

    def get_commission(self, trade_value: float) -> float:
        """
        Calculate total commission for a trade.

        Args:
            trade_value: Total trade value in base currency

        Returns:
            Total commission (fixed + percentage)
        """
        percentage_comm = trade_value * self.commission_pct
        return self.commission_fixed + percentage_comm

    def get_cost_per_unit(self, price: float) -> float:
        """
        Calculate cost per unit including all fees.

        Args:
            price: Price per unit

        Returns:
            Cost per unit (price + transaction costs)
        """
        total_cost_pct = self.total_cost_pct
        return price * (1 + total_cost_pct)

    def validate_order_size(self, quantity: int) -> tuple[bool, str]:
        """
        Validate if order quantity is acceptable.

        Args:
            quantity: Requested order quantity

        Returns:
            (is_valid, error_message)
        """
        if quantity < self.min_lot_size:
            return False, f"Order quantity {quantity} below minimum {self.min_lot_size}"

        if quantity % self.min_lot_size != 0:
            return False, f"Order quantity {quantity} not multiple of lot size {self.min_lot_size}"

        if self.max_position is not None and quantity > self.max_position:
            return False, f"Order quantity {quantity} exceeds maximum position {self.max_position}"

        return True, ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'market': self.market.value,
            'currency': self.currency.value,
            'multiplier': self.multiplier,
            'min_lot_size': self.min_lot_size,
            'max_position': self.max_position,
            'commission_fixed': self.commission_fixed,
            'commission_pct': self.commission_pct,
            'slippage_bps': self.slippage_bps,
            'description': self.description,
            'metadata': self.metadata,
            'total_cost_bps': self.total_cost_bps,
            'total_cost_pct': self.total_cost_pct,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AssetProfile':
        """Create from dictionary."""
        # Convert string enums back to enum types
        if isinstance(data.get('market'), str):
            data['market'] = Market[data['market']]
        if isinstance(data.get('currency'), str):
            data['currency'] = Currency[data['currency']]

        # Remove computed fields if present
        computed_fields = ['total_cost_bps', 'total_cost_pct']
        for field_name in computed_fields:
            data.pop(field_name, None)

        return cls(**data)


class AssetProfileRegistry:
    """
    Central registry for asset profiles.

    Manages and retrieves asset profiles for all traded instruments.
    """

    # Default profiles for commonly traded HK stocks
    _DEFAULT_PROFILES = {
        # Tech sector
        '0700.HK': AssetProfile(
            symbol='0700.HK',
            name='Tencent Holdings Limited',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=5.0,
            min_lot_size=100,
            description='Hong Kong technology giant, major internet and gaming company'
        ),

        '0388.HK': AssetProfile(
            symbol='0388.HK',
            name='Hong Kong Exchanges and Clearing Limited',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=3.0,
            min_lot_size=100,
            description='Stock exchange operator'
        ),

        # Banking sector
        '2800.HK': AssetProfile(
            symbol='2800.HK',
            name='HSI Tracker Fund',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=4.0,
            min_lot_size=100,
            description='Hang Seng Index tracker fund'
        ),

        '0939.HK': AssetProfile(
            symbol='0939.HK',
            name='China Construction Bank Corporation',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=5.0,
            min_lot_size=100,
            description='Major Chinese state-owned bank'
        ),

        '1398.HK': AssetProfile(
            symbol='1398.HK',
            name='Industrial and Commercial Bank of China Limited',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=5.0,
            min_lot_size=100,
            description='Largest Chinese bank by assets'
        ),

        '3988.HK': AssetProfile(
            symbol='3988.HK',
            name='Bank of China Limited',
            market=Market.HKEX,
            currency=Currency.HKD,
            commission_pct=0.001,
            slippage_bps=5.0,
            min_lot_size=100,
            description='Second largest Chinese bank'
        ),

        # US market example
        'AAPL': AssetProfile(
            symbol='AAPL',
            name='Apple Inc.',
            market=Market.NASDAQ,
            currency=Currency.USD,
            commission_pct=0.0001,
            slippage_bps=2.0,
            min_lot_size=1,
            description='US technology company'
        ),

        'MSFT': AssetProfile(
            symbol='MSFT',
            name='Microsoft Corporation',
            market=Market.NASDAQ,
            currency=Currency.USD,
            commission_pct=0.0001,
            slippage_bps=2.0,
            min_lot_size=1,
            description='US software and cloud computing company'
        ),
    }

    def __init__(self):
        """Initialize registry with default profiles."""
        self._profiles = self._DEFAULT_PROFILES.copy()
        self._custom_profiles = {}

    @property
    def profiles(self) -> Dict[str, AssetProfile]:
        """Get all registered profiles."""
        return {**self._profiles, **self._custom_profiles}

    def get(self, symbol: str) -> Optional[AssetProfile]:
        """
        Get asset profile by symbol.

        Args:
            symbol: Asset symbol (e.g., '0700.HK')

        Returns:
            AssetProfile or None if not found
        """
        # Check custom profiles first
        if symbol in self._custom_profiles:
            return self._custom_profiles[symbol]
        return self._profiles.get(symbol)

    def register(self, profile: AssetProfile) -> None:
        """
        Register a new asset profile.

        Args:
            profile: AssetProfile instance to register
        """
        if profile.symbol in self._profiles:
            raise ValueError(f"Cannot override default profile for {profile.symbol}")
        self._custom_profiles[profile.symbol] = profile

    def update(self, profile: AssetProfile) -> None:
        """
        Update existing asset profile.

        Args:
            profile: AssetProfile instance to update
        """
        if profile.symbol in self._profiles:
            raise ValueError(f"Cannot update default profile for {profile.symbol}")
        self._custom_profiles[profile.symbol] = profile

    def remove(self, symbol: str) -> bool:
        """
        Remove custom asset profile.

        Args:
            symbol: Asset symbol to remove

        Returns:
            True if removed, False if not found
        """
        if symbol in self._custom_profiles:
            del self._custom_profiles[symbol]
            return True
        return False

    def list_symbols(self) -> List[str]:
        """Get list of all registered symbols."""
        return sorted(self.profiles.keys())

    def list_by_market(self, market: Market) -> List[AssetProfile]:
        """Get all profiles for a specific market."""
        return [p for p in self.profiles.values() if p.market == market]

    def list_by_currency(self, currency: Currency) -> List[AssetProfile]:
        """Get all profiles for a specific currency."""
        return [p for p in self.profiles.values() if p.currency == currency]

    def export_to_json(self) -> str:
        """Export all profiles to JSON."""
        profiles_dict = {symbol: profile.to_dict() for symbol, profile in self.profiles.items()}
        return json.dumps(profiles_dict, indent=2, default=str)

    def import_from_json(self, json_str: str) -> None:
        """
        Import profiles from JSON string.

        Args:
            json_str: JSON string containing profile definitions
        """
        data = json.loads(json_str)
        for symbol, profile_data in data.items():
            profile = AssetProfile.from_dict(profile_data)
            self.register(profile)


# Global singleton registry
_global_registry = None


def get_registry() -> AssetProfileRegistry:
    """Get or create global asset profile registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AssetProfileRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None


# Convenience functions for common operations
def get_profile(symbol: str) -> Optional[AssetProfile]:
    """Get asset profile by symbol from global registry."""
    return get_registry().get(symbol)


def list_profiles() -> List[str]:
    """List all registered symbols from global registry."""
    return get_registry().list_symbols()


def register_profile(profile: AssetProfile) -> None:
    """Register new profile in global registry."""
    get_registry().register(profile)
