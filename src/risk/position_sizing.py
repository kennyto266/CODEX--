"""
动态仓位管理系统

实现基于Kelly公式、风险平价、均值方差优化等算法的动态仓位计算
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pydantic import BaseModel, Field, validator
import scipy.optimize as opt
from scipy.stats import norm


class SizingMethod(str, Enum):
    """仓位计算方法"""
    KELLY = "kelly"  # Kelly公式
    RISK_PARITY = "risk_parity"  # 风险平价
    MEAN_VARIANCE = "mean_variance"  # 均值方差
    VOLATILITY_ADJUSTED = "volatility_adjusted"  # 波动率调整
    MAX_DRAWDOWN_CONSTRAINED = "max_drawdown_constrained"  # 最大回撤约束
    EQUAL_WEIGHT = "equal_weight"  # 等权重


class PositionSizingRequest(BaseModel):
    """仓位调整请求"""
    symbol: str = Field(..., description="股票代码")
    current_price: float = Field(..., description="当前价格")
    expected_return: float = Field(..., description="预期收益率")
    volatility: float = Field(..., description="波动率")
    portfolio_value: float = Field(..., description="组合总价值")
    method: SizingMethod = Field(..., description="仓位计算方法")
    max_position: float = Field(0.2, description="最大仓位比例")
    risk_free_rate: float = Field(0.02, description="无风险利率")
    target_volatility: float = Field(0.15, description="目标波动率")
    correlation_matrix: Optional[Dict[str, float]] = Field(None, description="相关性矩阵")
    portfolio_assets: Optional[List[str]] = Field(None, description="组合资产列表")


class PositionSizingResult(BaseModel):
    """仓位计算结果"""
    symbol: str = Field(..., description="股票代码")
    recommended_position: float = Field(..., description="建议仓位价值")
    position_weight: float = Field(..., description="建议仓位比例")
    position_shares: int = Field(..., description="建议股数")
    kelly_fraction: Optional[float] = Field(None, description="Kelly比例")
    risk_contribution: float = Field(..., description="风险贡献")
    expected_sharpe: float = Field(..., description="预期夏普比率")
    max_theoretical_weight: float = Field(..., description="理论最大权重")
    adjusted_reason: str = Field(..., description="调整原因")
    calculation_date: datetime = Field(default_factory=datetime.now, description="计算日期")


class RiskParityWeights(BaseModel):
    """风险平价权重"""
    asset: str = Field(..., description="资产代码")
    weight: float = Field(..., description="权重")
    risk_contribution: float = Field(..., description="风险贡献")
    marginal_risk_contribution: float = Field(..., description="边际风险贡献")


class VolatilitySizingParams(BaseModel):
    """波动率调整参数"""
    volatility_window: int = Field(30, description="波动率计算窗口")
    target_vol: float = Field(0.15, description="目标波动率")
    min_position: float = Field(0.01, description="最小仓位")
    max_position: float = Field(0.3, description="最大仓位")
    volatility_multiplier: float = Field(1.0, description="波动率乘数")


class PositionSizingEngine:
    """动态仓位管理引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.position_sizing")
        self.risk_free_rate = 0.02
        self.min_position = 0.01  # 最小仓位比例
        self.max_leverage = 2.0  # 最大杠杆

    async def calculate_kelly_position(
        self,
        request: PositionSizingRequest
    ) -> PositionSizingResult:
        """使用Kelly公式计算最优仓位"""
        try:
            self.logger.info(f"Calculating Kelly position for {request.symbol}")

            # Kelly公式: f = (bp - q) / b
            # 其中: b = 胜率, p = 盈亏比, q = 亏损率
            expected_return = request.expected_return
            volatility = request.volatility

            # 简化Kelly: 基于预期收益和波动率
            if expected_return <= 0:
                return PositionSizingResult(
                    symbol=request.symbol,
                    recommended_position=0.0,
                    position_weight=0.0,
                    position_shares=0,
                    kelly_fraction=0.0,
                    risk_contribution=0.0,
                    expected_sharpe=0.0,
                    max_theoretical_weight=0.0,
                    adjusted_reason="Non-positive expected return"
                )

            # 风险调整Kelly
            excess_return = expected_return - request.risk_free_rate
            if volatility <= 0:
                return PositionSizingResult(
                    symbol=request.symbol,
                    recommended_position=0.0,
                    position_weight=0.0,
                    position_shares=0,
                    kelly_fraction=0.0,
                    risk_contribution=0.0,
                    expected_sharpe=0.0,
                    max_theoretical_weight=0.0,
                    adjusted_reason="Zero volatility"
                )

            kelly_fraction = min(
                excess_return / (volatility ** 2),
                1.0
            )

            # 保守调整 (Kelly通常过于激进)
            kelly_fraction = kelly_fraction * 0.25

            # 约束条件
            kelly_fraction = np.clip(kelly_fraction, 0, request.max_position)

            # 计算仓位
            position_value = request.portfolio_value * kelly_fraction
            position_shares = int(position_value / request.current_price)

            # 风险贡献
            risk_contribution = volatility * kelly_fraction

            # 预期夏普比率
            expected_sharpe = excess_return / volatility if volatility > 0 else 0

            return PositionSizingResult(
                symbol=request.symbol,
                recommended_position=position_value,
                position_weight=kelly_fraction,
                position_shares=position_shares,
                kelly_fraction=kelly_fraction,
                risk_contribution=risk_contribution,
                expected_sharpe=expected_sharpe,
                max_theoretical_weight=1.0,
                adjusted_reason="Kelly formula with conservative adjustment"
            )

        except Exception as e:
            self.logger.error(f"Error calculating Kelly position: {e}")
            raise

    async def calculate_risk_parity_weights(
        self,
        assets: List[Dict[str, Any]]
    ) -> List[RiskParityWeights]:
        """计算风险平价权重"""
        try:
            self.logger.info("Calculating risk parity weights")

            if len(assets) < 2:
                raise ValueError("At least 2 assets required for risk parity")

            # 提取波动率
            volatilities = np.array([asset['volatility'] for asset in assets])
            symbols = [asset['symbol'] for asset in assets]

            # 风险平价权重 = 1 / volatility / sum(1 / volatility)
            inv_vol = 1 / volatilities
            weights = inv_vol / inv_vol.sum()
            weights = np.clip(weights, 0, 1)
            weights = weights / weights.sum()  # 归一化

            # 计算风险贡献 (简化版本，假设独立性)
            risk_contributions = weights * volatilities

            results = [
                RiskParityWeights(
                    asset=symbol,
                    weight=float(w),
                    risk_contribution=float(rc),
                    marginal_risk_contribution=float(rc)
                )
                for symbol, w, rc in zip(symbols, weights, risk_contributions)
            ]

            self.logger.info(f"Risk parity weights calculated: {results}")
            return results

        except Exception as e:
            self.logger.error(f"Error calculating risk parity weights: {e}")
            raise

    async def calculate_mean_variance_position(
        self,
        request: PositionSizingRequest,
        covariance_matrix: Optional[np.ndarray] = None
    ) -> PositionSizingResult:
        """均值方差优化仓位计算"""
        try:
            self.logger.info(f"Calculating mean-variance position for {request.symbol}")

            # 简化的均值方差优化
            # 目标: 最大化 Sharpe 比率
            expected_return = request.expected_return
            volatility = request.volatility

            if expected_return <= 0 or volatility <= 0:
                return PositionSizingResult(
                    symbol=request.symbol,
                    recommended_position=0.0,
                    position_weight=0.0,
                    position_shares=0,
                    kelly_fraction=None,
                    risk_contribution=0.0,
                    expected_sharpe=0.0,
                    max_theoretical_weight=0.0,
                    adjusted_reason="Invalid return or volatility"
                )

            # 目标权重
            excess_return = expected_return - request.risk_free_rate
            target_weight = excess_return / (volatility ** 2)

            # 约束优化
            target_weight = np.clip(target_weight, 0, request.max_position)

            # 波动率调整
            current_vol = volatility
            target_vol = request.target_volatility
            vol_adjustment = target_vol / current_vol

            final_weight = target_weight * vol_adjustment
            final_weight = np.clip(final_weight, 0, request.max_position)

            # 计算仓位
            position_value = request.portfolio_value * final_weight
            position_shares = int(position_value / request.current_price)

            # 风险贡献
            risk_contribution = volatility * final_weight

            # 预期夏普比率
            expected_sharpe = excess_return / volatility

            return PositionSizingResult(
                symbol=request.symbol,
                recommended_position=position_value,
                position_weight=final_weight,
                position_shares=position_shares,
                kelly_fraction=target_weight,
                risk_contribution=risk_contribution,
                expected_sharpe=expected_sharpe,
                max_theoretical_weight=1.0,
                adjusted_reason="Mean-variance optimization"
            )

        except Exception as e:
            self.logger.error(f"Error calculating mean-variance position: {e}")
            raise

    async def calculate_volatility_adjusted_position(
        self,
        request: PositionSizingRequest,
        params: VolatilitySizingParams
    ) -> PositionSizingResult:
        """波动率调整仓位计算"""
        try:
            self.logger.info(f"Calculating volatility-adjusted position for {request.symbol}")

            current_vol = request.volatility
            target_vol = params.target_vol

            # 波动率调整因子
            vol_ratio = target_vol / current_vol
            vol_adjustment = min(vol_ratio, 2.0)  # 限制最大调整

            # 基础仓位 (基于历史表现)
            base_weight = abs(request.expected_return) / current_vol if current_vol > 0 else 0
            base_weight = np.clip(base_weight, params.min_position, params.max_position)

            # 应用波动率调整
            adjusted_weight = base_weight * vol_adjustment * params.volatility_multiplier
            adjusted_weight = np.clip(adjusted_weight, params.min_position, params.max_position)

            # 计算仓位
            position_value = request.portfolio_value * adjusted_weight
            position_shares = int(position_value / request.current_price)

            # 风险贡献
            risk_contribution = current_vol * adjusted_weight

            return PositionSizingResult(
                symbol=request.symbol,
                recommended_position=position_value,
                position_weight=adjusted_weight,
                position_shares=position_shares,
                kelly_fraction=None,
                risk_contribution=risk_contribution,
                expected_sharpe=0.0,
                max_theoretical_weight=params.max_position,
                adjusted_reason=f"Volatility adjustment (ratio: {vol_adjustment:.2f})"
            )

        except Exception as e:
            self.logger.error(f"Error calculating volatility-adjusted position: {e}")
            raise

    async def calculate_max_drawdown_constrained_position(
        self,
        request: PositionSizingRequest,
        max_drawdown_limit: float = 0.15
    ) -> PositionSizingResult:
        """最大回撤约束仓位计算"""
        try:
            self.logger.info(f"Calculating drawdown-constrained position for {request.symbol}")

            # 估算回撤
            # 假设回撤约为波动的2-3倍
            estimated_max_drawdown = request.volatility * 2.5

            # 基于回撤限制调整仓位
            if estimated_max_drawdown > max_drawdown_limit:
                drawdown_adjustment = max_drawdown_limit / estimated_max_drawdown
            else:
                drawdown_adjustment = 1.0

            # 基础仓位
            base_weight = request.expected_return / request.volatility if request.volatility > 0 else 0
            base_weight = max(0, base_weight)
            base_weight = min(base_weight, request.max_position)

            # 应用回撤约束
            final_weight = base_weight * drawdown_adjustment
            final_weight = np.clip(final_weight, 0, request.max_position)

            # 计算仓位
            position_value = request.portfolio_value * final_weight
            position_shares = int(position_value / request.current_price)

            # 风险贡献
            risk_contribution = request.volatility * final_weight

            return PositionSizingResult(
                symbol=request.symbol,
                recommended_position=position_value,
                position_weight=final_weight,
                position_shares=position_shares,
                kelly_fraction=None,
                risk_contribution=risk_contribution,
                expected_sharpe=0.0,
                max_theoretical_weight=request.max_position,
                adjusted_reason=f"Drawdown constraint (adjustment: {drawdown_adjustment:.2f})"
            )

        except Exception as e:
            self.logger.error(f"Error calculating drawdown-constrained position: {e}")
            raise

    async def calculate_position(
        self,
        request: PositionSizingRequest
    ) -> PositionSizingResult:
        """统一的仓位计算接口"""
        try:
            self.logger.info(f"Calculating position using {request.method} method")

            if request.method == SizingMethod.KELLY:
                return await self.calculate_kelly_position(request)

            elif request.method == SizingMethod.RISK_PARITY:
                # 风险平价需要多个资产
                if not request.portfolio_assets:
                    raise ValueError("Portfolio assets required for risk parity")

                # 这里简化处理，使用等权重
                equal_weight = 1.0 / len(request.portfolio_assets)
                position_value = request.portfolio_value * equal_weight
                position_shares = int(position_value / request.current_price)

                return PositionSizingResult(
                    symbol=request.symbol,
                    recommended_position=position_value,
                    position_weight=equal_weight,
                    position_shares=position_shares,
                    kelly_fraction=None,
                    risk_contribution=request.volatility * equal_weight,
                    expected_sharpe=0.0,
                    max_theoretical_weight=1.0,
                    adjusted_reason="Risk parity (equal weight approximation)"
                )

            elif request.method == SizingMethod.MEAN_VARIANCE:
                return await self.calculate_mean_variance_position(request)

            elif request.method == SizingMethod.VOLATILITY_ADJUSTED:
                params = VolatilitySizingParams()
                return await self.calculate_volatility_adjusted_position(request, params)

            elif request.method == SizingMethod.MAX_DRAWDOWN_CONSTRAINED:
                return await self.calculate_max_drawdown_constrained_position(request)

            elif request.method == SizingMethod.EQUAL_WEIGHT:
                # 等权重
                weight = 1.0 / len(request.portfolio_assets) if request.portfolio_assets else 0.1
                weight = min(weight, request.max_position)

                position_value = request.portfolio_value * weight
                position_shares = int(position_value / request.current_price)

                return PositionSizingResult(
                    symbol=request.symbol,
                    recommended_position=position_value,
                    position_weight=weight,
                    position_shares=position_shares,
                    kelly_fraction=None,
                    risk_contribution=request.volatility * weight,
                    expected_sharpe=0.0,
                    max_theoretical_weight=request.max_position,
                    adjusted_reason="Equal weight"
                )

            else:
                raise ValueError(f"Unsupported sizing method: {request.method}")

        except Exception as e:
            self.logger.error(f"Error calculating position: {e}")
            raise

    async def rebalance_portfolio(
        self,
        current_positions: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        transaction_cost_rate: float = 0.001
    ) -> Dict[str, Any]:
        """组合再平衡计算"""
        try:
            self.logger.info("Calculating portfolio rebalancing")

            rebalancing_actions = []
            total_transaction_cost = 0

            for symbol in current_positions.keys():
                current_weight = current_positions[symbol] / portfolio_value
                target_weight = target_weights.get(symbol, 0)

                weight_diff = target_weight - current_weight
                if abs(weight_diff) > 0.01:  # 只有差异超过1%才调整
                    action_value = portfolio_value * weight_diff
                    transaction_cost = abs(action_value) * transaction_cost_rate

                    rebalancing_actions.append({
                        "symbol": symbol,
                        "current_weight": current_weight,
                        "target_weight": target_weight,
                        "action": "BUY" if weight_diff > 0 else "SELL",
                        "action_value": action_value,
                        "transaction_cost": transaction_cost
                    })

                    total_transaction_cost += transaction_cost

            return {
                "rebalancing_actions": rebalancing_actions,
                "total_transaction_cost": total_transaction_cost,
                "net_portfolio_cost": total_transaction_cost,
                "expected_benefit": "Improved risk-return profile"
            }

        except Exception as e:
            self.logger.error(f"Error calculating portfolio rebalancing: {e}")
            raise
