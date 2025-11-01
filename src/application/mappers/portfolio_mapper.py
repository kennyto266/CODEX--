#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合映射器
"""

from typing import List, Dict
from ...application.dto import PortfolioDTO, PortfolioDetailDTO, PositionDTO
from ...domain.entities import Portfolio, Position


class PortfolioMapper:
    """投资组合映射器"""

    @staticmethod
    def to_dto(portfolio: Portfolio) -> PortfolioDTO:
        """将投资组合实体转换为DTO"""
        return PortfolioDTO(
            name=portfolio.name,
            portfolio_type=portfolio.portfolio_type.value,
            initial_capital=portfolio.initial_capital.value,
            cash=portfolio.cash.value,
            total_value=portfolio.total_value.value,
            realized_pnl=portfolio.realized_pnl.value,
            unrealized_pnl=portfolio.unrealized_pnl.value,
            total_return=portfolio.total_return.value,
            number_of_positions=portfolio.get_number_of_positions(),
            number_of_strategies=portfolio.get_number_of_strategies(),
            cash_percentage=portfolio.get_cash_percentage(),
            leverage_ratio=portfolio.get_leverage_ratio(),
            created_at=portfolio.created_at.to_string(),
            updated_at=portfolio.updated_at.to_string()
        )

    @staticmethod
    def to_detailed_dto(portfolio: Portfolio) -> PortfolioDetailDTO:
        """将投资组合实体转换为详细DTO"""
        # 转换仓位信息
        detailed_positions = []
        for symbol, position in portfolio.positions.items():
            position_dto = PositionDTO(
                symbol=symbol,
                quantity=position.quantity.value,
                avg_price=position.avg_price.value,
                market_price=position.market_value.value / position.quantity.value if position.quantity.value > 0 else 0,
                market_value=position.market_value.value,
                unrealized_pnl=position.unrealized_pnl.value,
                position_type=position.position_type.value
            )
            detailed_positions.append(position_dto)

        # 转换基础信息
        base_dto = PortfolioMapper.to_dto(portfolio)

        return PortfolioDetailDTO(
            **base_dto.dict(),
            detailed_positions=detailed_positions
        )

    @staticmethod
    def from_dto(portfolio_dto: PortfolioDTO) -> Portfolio:
        """将DTO转换为投资组合实体"""
        from ...domain.value_objects import Money, PortfolioType
        from ...domain.value_objects import Timestamp

        # 注意：这个方法需要更多的业务逻辑来完全重建投资组合
        # 这里只提供基本转换，实际使用时需要更完整的实现
        portfolio = Portfolio(
            name=portfolio_dto.name,
            portfolio_type=PortfolioType(portfolio_dto.portfolio_type),
            initial_capital=Money.from_float(portfolio_dto.initial_capital),
            cash=Money.from_float(portfolio_dto.cash)
        )

        # 设置其他属性
        portfolio.total_value = Money.from_float(portfolio_dto.total_value)
        portfolio.realized_pnl = Money.from_float(portfolio_dto.realized_pnl)
        portfolio.unrealized_pnl = Money.from_float(portfolio_dto.unrealized_pnl)
        portfolio.total_return = Money.from_float(portfolio_dto.total_return)
        portfolio.created_at = Timestamp.from_string(portfolio_dto.created_at)
        portfolio.updated_at = Timestamp.from_string(portfolio_dto.updated_at)

        return portfolio