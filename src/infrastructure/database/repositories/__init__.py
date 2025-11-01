"""
Repository Implementations
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.trading.entities import Order, Trade, Position, OrderId, TradeId, PositionId
from src.domain.portfolio.entities import Portfolio, Asset, PortfolioId, AssetId
from src.domain.risk.entities import RiskMetric, RiskLimit, RiskAssessment, RiskMetricId, RiskLimitId
from src.domain.repositories import Repository


class InMemoryOrderRepository(Repository[Order]):
    """In-memory order repository implementation"""

    def __init__(self):
        self._orders: Dict[UUID, Order] = {}

    async def find_by_id(self, id: UUID) -> Optional[Order]:
        return self._orders.get(id)

    async def find_all(self) -> List[Order]:
        return list(self._orders.values())

    async def save(self, entity: Order) -> Order:
        self._orders[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._orders:
            del self._orders[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._orders


class InMemoryTradeRepository(Repository[Trade]):
    """In-memory trade repository implementation"""

    def __init__(self):
        self._trades: Dict[UUID, Trade] = {}

    async def find_by_id(self, id: UUID) -> Optional[Trade]:
        return self._trades.get(id)

    async def find_all(self) -> List[Trade]:
        return list(self._trades.values())

    async def save(self, entity: Trade) -> Trade:
        self._trades[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._trades:
            del self._trades[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._trades


class InMemoryPositionRepository(Repository[Position]):
    """In-memory position repository implementation"""

    def __init__(self):
        self._positions: Dict[UUID, Position] = {}

    async def find_by_id(self, id: UUID) -> Optional[Position]:
        return self._positions.get(id)

    async def find_all(self) -> List[Position]:
        return list(self._positions.values())

    async def save(self, entity: Position) -> Position:
        self._positions[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._positions:
            del self._positions[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._positions


class InMemoryPortfolioRepository(Repository[Portfolio]):
    """In-memory portfolio repository implementation"""

    def __init__(self):
        self._portfolios: Dict[UUID, Portfolio] = {}

    async def find_by_id(self, id: UUID) -> Optional[Portfolio]:
        return self._portfolios.get(id)

    async def find_all(self) -> List[Portfolio]:
        return list(self._portfolios.values())

    async def save(self, entity: Portfolio) -> Portfolio:
        self._portfolios[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._portfolios:
            del self._portfolios[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._portfolios


class InMemoryAssetRepository(Repository[Asset]):
    """In-memory asset repository implementation"""

    def __init__(self):
        self._assets: Dict[UUID, Asset] = {}

    async def find_by_id(self, id: UUID) -> Optional[Asset]:
        return self._assets.get(id)

    async def find_all(self) -> List[Asset]:
        return list(self._assets.values())

    async def save(self, entity: Asset) -> Asset:
        self._assets[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._assets:
            del self._assets[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._assets


class InMemoryRiskMetricRepository(Repository[RiskMetric]):
    """In-memory risk metric repository implementation"""

    def __init__(self):
        self._metrics: Dict[UUID, RiskMetric] = {}

    async def find_by_id(self, id: UUID) -> Optional[RiskMetric]:
        return self._metrics.get(id)

    async def find_all(self) -> List[RiskMetric]:
        return list(self._metrics.values())

    async def save(self, entity: RiskMetric) -> RiskMetric:
        self._metrics[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._metrics:
            del self._metrics[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._metrics


class InMemoryRiskLimitRepository(Repository[RiskLimit]):
    """In-memory risk limit repository implementation"""

    def __init__(self):
        self._limits: Dict[UUID, RiskLimit] = {}

    async def find_by_id(self, id: UUID) -> Optional[RiskLimit]:
        return self._limits.get(id)

    async def find_all(self) -> List[RiskLimit]:
        return list(self._limits.values())

    async def save(self, entity: RiskLimit) -> RiskLimit:
        self._limits[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._limits:
            del self._limits[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._limits


class InMemoryRiskAssessmentRepository(Repository[RiskAssessment]):
    """In-memory risk assessment repository implementation"""

    def __init__(self):
        self._assessments: Dict[UUID, RiskAssessment] = {}

    async def find_by_id(self, id: UUID) -> Optional[RiskAssessment]:
        return self._assessments.get(id)

    async def find_all(self) -> List[RiskAssessment]:
        return list(self._assessments.values())

    async def save(self, entity: RiskAssessment) -> RiskAssessment:
        self._assessments[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._assessments:
            del self._assessments[id]
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        return id in self._assessments
