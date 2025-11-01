#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合应用服务
处理投资组合相关的用例和协调
"""

from typing import List, Optional, Dict, Any
import asyncio

from ...domain.entities import Portfolio
from ...domain.value_objects import Money, StockSymbol
from ...domain.services import PortfolioService, RiskManagementService
from ...domain.repositories import PortfolioRepository
from ...application.dto import (
    PortfolioCreateDTO, PortfolioDTO, PortfolioResponseDTO,
    CreatePortfolioRequest, PortfolioResponse
)
from ...application.mappers import PortfolioMapper


class PortfolioApplicationService:
    """投资组合应用服务"""

    def __init__(self, portfolio_service: PortfolioService,
                 risk_service: RiskManagementService,
                 portfolio_repository: PortfolioRepository):
        """初始化投资组合应用服务"""
        self.portfolio_service = portfolio_service
        self.risk_service = risk_service
        self.portfolio_repository = portfolio_repository

    async def create_portfolio(self, request: CreatePortfolioRequest) -> PortfolioResponse:
        """创建投资组合"""
        try:
            # 验证输入
            if not request.name:
                return PortfolioResponse(
                    success=False,
                    error="投资组合名称不能为空"
                )

            if request.initial_capital <= 0:
                return PortfolioResponse(
                    success=False,
                    error="初始资金必须大于零"
                )

            # 创建投资组合
            from ...domain.value_objects import PortfolioType
            portfolio_type = PortfolioType(request.portfolio_type)

            portfolio = await self.portfolio_service.create_portfolio(
                name=request.name,
                portfolio_type=portfolio_type.value,
                initial_capital=request.initial_capital,
                currency=request.currency
            )

            # 保存到仓储
            await self.portfolio_repository.save(portfolio)

            # 转换为响应DTO
            portfolio_dto = PortfolioMapper.to_dto(portfolio)
            return PortfolioResponse(
                success=True,
                data=portfolio_dto
            )

        except ValueError as e:
            return PortfolioResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"创建投资组合失败: {str(e)}"
            )

    async def get_portfolio(self, name: str) -> PortfolioResponse:
        """获取投资组合"""
        try:
            portfolio = self.portfolio_repository.get_by_id(name)
            if not portfolio:
                return PortfolioResponse(
                    success=False,
                    error="投资组合不存在"
                )

            portfolio_dto = PortfolioMapper.to_detailed_dto(portfolio)
            return PortfolioResponse(
                success=True,
                data=portfolio_dto
            )

        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"获取投资组合失败: {str(e)}"
            )

    async def get_all_portfolios(self) -> PortfolioResponse:
        """获取所有投资组合"""
        try:
            portfolios = await self.portfolio_repository.get_all()
            portfolio_dtos = [PortfolioMapper.to_dto(p) for p in portfolios]
            return PortfolioResponse(
                success=True,
                data=portfolio_dtos
            )

        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"获取投资组合列表失败: {str(e)}"
            )

    async def get_portfolio_summary(self, name: str) -> PortfolioResponse:
        """获取投资组合摘要"""
        try:
            portfolio = self.portfolio_repository.get_by_id(name)
            if not portfolio:
                return PortfolioResponse(
                    success=False,
                    error="投资组合不存在"
                )

            # 计算性能指标
            performance_metrics = await self.portfolio_service.calculate_performance_metrics(portfolio)
            risk_summary = self.risk_service.get_risk_summary(portfolio)

            summary = {
                'portfolio': PortfolioMapper.to_detailed_dto(portfolio),
                'performance_metrics': performance_metrics,
                'risk_summary': risk_summary
            }

            return PortfolioResponse(
                success=True,
                data=summary
            )

        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"获取投资组合摘要失败: {str(e)}"
            )

    async def assess_portfolio_risk(self, name: str) -> PortfolioResponse:
        """评估投资组合风险"""
        try:
            portfolio = self.portfolio_repository.get_by_id(name)
            if not portfolio:
                return PortfolioResponse(
                    success=False,
                    error="投资组合不存在"
                )

            # 评估风险
            risk_metrics = await self.risk_service.assess_portfolio_risk(portfolio)
            risk_alerts = await self.risk_service.check_risk_limits(portfolio)

            risk_assessment = {
                'metrics': risk_metrics.to_dict(),
                'alerts': [alert.__dict__ for alert in risk_alerts],
                'risk_level': self._determine_risk_level(risk_metrics)
            }

            return PortfolioResponse(
                success=True,
                data=risk_assessment
            )

        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"评估投资组合风险失败: {str(e)}"
            )

    async def rebalance_portfolio(self, name: str,
                                target_allocations: Dict[str, float]) -> PortfolioResponse:
        """重新平衡投资组合"""
        try:
            portfolio = self.portfolio_repository.get_by_id(name)
            if not portfolio:
                return PortfolioResponse(
                    success=False,
                    error="投资组合不存在"
                )

            # 重新平衡投资组合
            trades = await self.portfolio_service.rebalance_portfolio(
                portfolio, target_allocations
            )

            return PortfolioResponse(
                success=True,
                data={
                    'trades': trades,
                    'message': f"投资组合重新平衡，建议执行 {len(trades)} 笔交易"
                }
            )

        except Exception as e:
            return PortfolioResponse(
                success=False,
                error=f"重新平衡投资组合失败: {str(e)}"
            )

    def _determine_risk_level(self, risk_metrics) -> str:
        """确定风险等级"""
        if risk_metrics.var_95 > 0.1 or risk_metrics.max_drawdown > 0.15:
            return "HIGH"
        elif risk_metrics.var_95 > 0.05 or risk_metrics.max_drawdown > 0.10:
            return "MEDIUM"
        else:
            return "LOW"