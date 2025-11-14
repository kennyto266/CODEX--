"""
风险平价策略实现

基于风险贡献的资产配置方法，确保各资产对组合风险的贡献相等
支持动态再平衡、相关性调整、风险预算分配等功能
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import scipy.optimize as opt
from scipy.linalg import inv


class RiskParityMethod(str, Enum):
    """风险平价方法"""
    EQUAL_RISK_CONTRIBUTION = "equal_risk_contribution"  # 等风险贡献
    VOLATILITY_WEIGHTING = "volatility_weighting"  # 波动率加权
    INVERSE_VOLATILITY = "inverse_volatility"  # 反向波动率
    RISK_BUDGET = "risk_budget"  # 风险预算
    DIVERSIFIED_RISK_PARITY = "diversified_risk_parity"  # 分散化风险平价


class RiskBudget(BaseModel):
    """风险预算"""
    asset: str = Field(..., description="资产代码")
    target_contribution: float = Field(..., description="目标风险贡献")
    max_contribution: float = Field(0.5, description="最大风险贡献")
    min_contribution: float = Field(0.05, description="最小风险贡献")


class RiskParityConfig(BaseModel):
    """风险平价配置"""
    method: RiskParityMethod = Field(..., description="计算方法")
    lookback_period: int = Field(252, description="回望期")
    rebalance_frequency: str = Field("M", description="再平衡频率")
    target_volatility: float = Field(0.15, description="目标波动率")
    max_leverage: float = Field(2.0, description="最大杠杆")
    min_weight: float = Field(0.01, description="最小权重")
    max_weight: float = Field(0.5, description="最大权重")
    correlation_adjustment: bool = Field(True, description="是否进行相关性调整")
    risk_budgets: Optional[List[RiskBudget]] = Field(None, description="风险预算")


class AssetRiskMetrics(BaseModel):
    """资产风险指标"""
    symbol: str = Field(..., description="资产代码")
    volatility: float = Field(..., description="波动率")
    expected_return: float = Field(0.0, description="预期收益率")
    correlation_matrix: Optional[Dict[str, float]] = Field(None, description="相关性")
    historical_var: Optional[float] = Field(None, description="历史VaR")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")


class RiskParityResult(BaseModel):
    """风险平价结果"""
    weights: Dict[str, float] = Field(..., description="资产权重")
    risk_contributions: Dict[str, float] = Field(..., description="风险贡献")
    marginal_contributions: Dict[str, float] = Field(..., description="边际风险贡献")
    component_contributions: Dict[str, float] = Field(..., description="成分风险贡献")
    portfolio_volatility: float = Field(..., description="组合波动率")
    diversification_ratio: float = Field(..., description="分散化比率")
    effective_n_assets: float = Field(..., description="有效资产数")
    calculation_date: datetime = Field(default_factory=datetime.now, description="计算日期")
    rebalancing_required: bool = Field(..., description="是否需要再平衡")


class RebalanceAction(BaseModel):
    """再平衡操作"""
    asset: str = Field(..., description="资产")
    current_weight: float = Field(..., description="当前权重")
    target_weight: float = Field(..., description="目标权重")
    action: str = Field(..., description="操作 (BUY/SELL/HOLD)")
    shares_to_trade: float = Field(..., description="交易股数")
    trade_value: float = Field(..., description="交易金额")
    transaction_cost: float = Field(0.0, description="交易成本")


class RiskParityEngine:
    """风险平价策略引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.risk_parity")
        self.risk_free_rate = 0.02

    async def calculate_equal_risk_contribution(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig
    ) -> RiskParityResult:
        """计算等风险贡献权重"""
        try:
            self.logger.info("Calculating equal risk contribution weights")

            # 准备数据
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()

            if len(returns_df) < 30:
                raise ValueError("Insufficient data for risk parity calculation")

            symbols = list(returns_data.keys())
            n_assets = len(symbols)

            # 计算协方差矩阵
            cov_matrix = returns_df.cov().values
            annual_cov = cov_matrix * 252  # 年化

            # 目标：最小化风险贡献的不平等
            def risk_contribution_objective(weights):
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
                marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
                risk_contrib = weights * marginal_contrib
                # 最大化最小风险贡献，最小化风险贡献方差
                min_contrib = np.min(risk_contrib)
                contrib_variance = np.var(risk_contrib)
                return -(min_contrib - contrib_variance)

            # 约束条件
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # 权重和为1
            ]

            bounds = [
                (config.min_weight, config.max_weight)
                for _ in range(n_assets)
            ]

            # 初始权重 (等权重)
            initial_weights = np.array([1.0 / n_assets] * n_assets)

            # 优化
            result = opt.minimize(
                risk_contribution_objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )

            if not result.success:
                self.logger.warning(f"Optimization failed: {result.message}")
                weights = initial_weights
            else:
                weights = result.x

            # 规范化权重
            weights = weights / np.sum(weights)
            weights = np.clip(weights, config.min_weight, config.max_weight)
            weights = weights / np.sum(weights)  # 重新归一化

            # 计算风险贡献
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
            marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib

            # 分散化比率
            weighted_individual_vols = sum(
                (weights[i] ** 2) * annual_cov[i, i] for i in range(n_assets)
            )
            portfolio_vol_independence = np.sqrt(weighted_individual_vols)
            diversification_ratio = portfolio_vol_independence / portfolio_vol

            # 有效资产数
            effective_n_assets = 1 / np.sum(weights ** 2)

            # 组装结果
            result_dict = {
                "weights": {symbol: float(weights[i]) for i, symbol in enumerate(symbols)},
                "risk_contributions": {symbol: float(risk_contrib[i]) for i, symbol in enumerate(symbols)},
                "marginal_contributions": {symbol: float(marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "component_contributions": {symbol: float(weights[i] * marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "portfolio_volatility": float(portfolio_vol),
                "diversification_ratio": float(diversification_ratio),
                "effective_n_assets": float(effective_n_assets),
                "rebalancing_required": False
            }

            return RiskParityResult(**result_dict)

        except Exception as e:
            self.logger.error(f"Error calculating equal risk contribution: {e}")
            raise

    async def calculate_inverse_volatility_weights(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig
    ) -> RiskParityResult:
        """计算反向波动率权重"""
        try:
            self.logger.info("Calculating inverse volatility weights")

            symbols = list(returns_data.keys())
            n_assets = len(symbols)

            # 计算各资产年化波动率
            volatilities = {}
            for symbol, returns in returns_data.items():
                vol = returns.std() * np.sqrt(252)
                volatilities[symbol] = vol

            # 反向波动率权重
            inv_vols = {symbol: 1.0 / vol for symbol, vol in volatilities.items() if vol > 0}
            total_inv_vol = sum(inv_vols.values())

            weights = {symbol: inv_vol / total_inv_vol for symbol, inv_vol in inv_vols.items()}

            # 应用权重约束
            for symbol in weights:
                weights[symbol] = np.clip(weights[symbol], config.min_weight, config.max_weight)

            # 重新归一化
            total_weight = sum(weights.values())
            for symbol in weights:
                weights[symbol] = weights[symbol] / total_weight

            # 估算风险贡献 (简化)
            avg_vol = np.mean(list(volatilities.values()))
            risk_contributions = {symbol: w * vol for symbol, w, vol in zip(
                weights.keys(), weights.values(), volatilities.values()
            )}

            result = RiskParityResult(
                weights=weights,
                risk_contributions=risk_contributions,
                marginal_contributions=risk_contributions.copy(),  # 简化
                component_contributions=risk_contributions.copy(),  # 简化
                portfolio_volatility=avg_vol,
                diversification_ratio=1.2,  # 简化估计
                effective_n_assets=n_assets,
                rebalancing_required=True
            )

            return result

        except Exception as e:
            self.logger.error(f"Error calculating inverse volatility weights: {e}")
            raise

    async def calculate_risk_budget_weights(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig
    ) -> RiskParityResult:
        """计算风险预算权重"""
        try:
            self.logger.info("Calculating risk budget weights")

            if not config.risk_budgets:
                raise ValueError("Risk budgets must be specified for risk budget method")

            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()

            symbols = list(returns_data.keys())
            n_assets = len(symbols)

            # 协方差矩阵
            cov_matrix = returns_df.cov().values
            annual_cov = cov_matrix * 252

            # 风险预算
            budget_dict = {budget.asset: budget.target_contribution for budget in config.risk_budgets}

            def risk_budget_objective(weights):
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
                marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
                risk_contrib = weights * marginal_contrib

                # 最小化与目标风险预算的偏差
                target_contrib = [budget_dict.get(symbol, 1.0 / n_assets) for symbol in symbols]
                return np.sum((risk_contrib - target_contrib) ** 2)

            # 约束条件
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            ]

            bounds = [
                (config.min_weight, config.max_weight)
                for _ in range(n_assets)
            ]

            # 初始权重
            initial_weights = np.array([1.0 / n_assets] * n_assets)

            # 优化
            result = opt.minimize(
                risk_budget_objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )

            if not result.success:
                self.logger.warning(f"Risk budget optimization failed: {result.message}")
                weights = initial_weights
            else:
                weights = result.x

            # 规范化
            weights = weights / np.sum(weights)

            # 计算风险贡献
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
            marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib

            result_dict = {
                "weights": {symbol: float(weights[i]) for i, symbol in enumerate(symbols)},
                "risk_contributions": {symbol: float(risk_contrib[i]) for i, symbol in enumerate(symbols)},
                "marginal_contributions": {symbol: float(marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "component_contributions": {symbol: float(weights[i] * marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "portfolio_volatility": float(portfolio_vol),
                "diversification_ratio": 1.0,  # 简化
                "effective_n_assets": 1.0 / np.sum(weights ** 2),
                "rebalancing_required": True
            }

            return RiskParityResult(**result_dict)

        except Exception as e:
            self.logger.error(f"Error calculating risk budget weights: {e}")
            raise

    async def calculate_diversified_risk_parity(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig
    ) -> RiskParityResult:
        """计算分散化风险平价权重"""
        try:
            self.logger.info("Calculating diversified risk parity weights")

            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()

            symbols = list(returns_data.keys())
            n_assets = len(symbols)

            cov_matrix = returns_df.cov().values
            annual_cov = cov_matrix * 252

            # 分散化风险平价目标函数
            def drp_objective(weights):
                # 计算组合方差
                portfolio_var = np.dot(weights.T, np.dot(annual_cov, weights))

                # 资产方差权重
                asset_vars = np.diag(annual_cov)
                weighted_var = sum(w ** 2 * v for w, v in zip(weights, asset_vars))

                # 分散化比率
                div_ratio = weighted_var / portfolio_var if portfolio_var > 0 else 1

                # 风险平价目标
                portfolio_vol = np.sqrt(portfolio_var)
                marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
                risk_contrib = weights * marginal_contrib

                # 最大化分散化比率，最小化风险贡献不平等
                eq_risk_penalty = np.std(risk_contrib)
                return -(div_ratio - 0.5 * eq_risk_penalty)

            # 约束和边界
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            ]

            bounds = [
                (config.min_weight, config.max_weight)
                for _ in range(n_assets)
            ]

            initial_weights = np.array([1.0 / n_assets] * n_assets)

            result = opt.minimize(
                drp_objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )

            if not result.success:
                weights = initial_weights
            else:
                weights = result.x

            weights = weights / np.sum(weights)

            # 计算指标
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))
            marginal_contrib = np.dot(annual_cov, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib

            # 分散化比率
            asset_vars = np.diag(annual_cov)
            weighted_var = sum(w ** 2 * v for w, v in zip(weights, asset_vars))
            portfolio_var = np.dot(weights.T, np.dot(annual_cov, weights))
            diversification_ratio = weighted_var / portfolio_var if portfolio_var > 0 else 1

            result_dict = {
                "weights": {symbol: float(weights[i]) for i, symbol in enumerate(symbols)},
                "risk_contributions": {symbol: float(risk_contrib[i]) for i, symbol in enumerate(symbols)},
                "marginal_contributions": {symbol: float(marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "component_contributions": {symbol: float(weights[i] * marginal_contrib[i]) for i, symbol in enumerate(symbols)},
                "portfolio_volatility": float(portfolio_vol),
                "diversification_ratio": float(diversification_ratio),
                "effective_n_assets": float(1.0 / np.sum(weights ** 2)),
                "rebalancing_required": True
            }

            return RiskParityResult(**result_dict)

        except Exception as e:
            self.logger.error(f"Error calculating diversified risk parity: {e}")
            raise

    async def calculate_risk_parity_weights(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig
    ) -> RiskParityResult:
        """统一的风险平价权重计算接口"""
        try:
            self.logger.info(f"Calculating risk parity using {config.method} method")

            if config.method == RiskParityMethod.EQUAL_RISK_CONTRIBUTION:
                return await self.calculate_equal_risk_contribution(returns_data, config)

            elif config.method == RiskParityMethod.INVERSE_VOLATILITY:
                return await self.calculate_inverse_volatility_weights(returns_data, config)

            elif config.method == RiskParityMethod.RISK_BUDGET:
                return await self.calculate_risk_budget_weights(returns_data, config)

            elif config.method == RiskParityMethod.DIVERSIFIED_RISK_PARITY:
                return await self.calculate_diversified_risk_parity(returns_data, config)

            elif config.method == RiskParityMethod.VOLATILITY_WEIGHTING:
                # 波动率加权 (简化)
                volatilities = {}
                for symbol, returns in returns_data.items():
                    vol = returns.std() * np.sqrt(252)
                    volatilities[symbol] = vol

                weights = {symbol: vol for symbol, vol in volatilities.items()}
                total_weight = sum(weights.values())
                weights = {symbol: w / total_weight for symbol, w in weights.items()}

                return RiskParityResult(
                    weights=weights,
                    risk_contributions=weights.copy(),
                    marginal_contributions=weights.copy(),
                    component_contributions=weights.copy(),
                    portfolio_volatility=np.mean(list(volatilities.values())),
                    diversification_ratio=1.1,
                    effective_n_assets=len(weights),
                    rebalancing_required=True
                )

            else:
                raise ValueError(f"Unsupported risk parity method: {config.method}")

        except Exception as e:
            self.logger.error(f"Error calculating risk parity weights: {e}")
            raise

    async def calculate_rebalancing_actions(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        transaction_cost_rate: float = 0.001,
        rebalancing_threshold: float = 0.02
    ) -> List[RebalanceAction]:
        """计算再平衡操作"""
        try:
            self.logger.info("Calculating rebalancing actions")

            actions = []

            for symbol in target_weights.keys():
                current_weight = current_weights.get(symbol, 0)
                target_weight = target_weights[symbol]

                weight_diff = target_weight - current_weight

                # 只有差异超过阈值才调整
                if abs(weight_diff) > rebalancing_threshold:
                    trade_value = portfolio_value * weight_diff

                    # 计算交易成本
                    transaction_cost = abs(trade_value) * transaction_cost_rate

                    # 简化的股数计算 (假设价格为1)
                    shares_to_trade = trade_value  # 假设价格为1

                    action = "BUY" if weight_diff > 0 else "SELL" if weight_diff < 0 else "HOLD"

                    actions.append(RebalanceAction(
                        asset=symbol,
                        current_weight=current_weight,
                        target_weight=target_weight,
                        action=action,
                        shares_to_trade=shares_to_trade,
                        trade_value=trade_value,
                        transaction_cost=transaction_cost
                    ))

            return actions

        except Exception as e:
            self.logger.error(f"Error calculating rebalancing actions: {e}")
            raise

    async def monitor_risk_parity_drift(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        returns_data: Dict[str, pd.Series],
        drift_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """监控风险平价漂移"""
        try:
            self.logger.info("Monitoring risk parity drift")

            # 计算权重漂移
            weight_drifts = {}
            for symbol in target_weights.keys():
                current = current_weights.get(symbol, 0)
                target = target_weights[symbol]
                drift = abs(current - target)
                weight_drifts[symbol] = drift

            # 总体漂移
            total_drift = sum(weight_drifts.values())
            max_drift = max(weight_drifts.values()) if weight_drifts else 0

            # 判断是否需要再平衡
            rebalance_needed = max_drift > drift_threshold

            # 计算组合风险变化
            returns_df = pd.DataFrame(returns_data)
            current_portfolio_vol = self._calculate_portfolio_volatility(current_weights, returns_df)
            target_portfolio_vol = self._calculate_portfolio_volatility(target_weights, returns_df)

            risk_drift = current_portfolio_vol - target_portfolio_vol

            return {
                "weight_drifts": weight_drifts,
                "total_drift": total_drift,
                "max_drift": max_drift,
                "rebalance_needed": rebalance_needed,
                "current_portfolio_volatility": current_portfolio_vol,
                "target_portfolio_volatility": target_portfolio_vol,
                "risk_drift": risk_drift,
                "monitoring_date": datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Error monitoring risk parity drift: {e}")
            raise

    def _calculate_portfolio_volatility(
        self,
        weights: Dict[str, float],
        returns_df: pd.DataFrame
    ) -> float:
        """计算组合波动率"""
        weight_array = np.array([weights.get(symbol, 0) for symbol in returns_df.columns])
        cov_matrix = returns_df.cov().values
        annual_cov = cov_matrix * 252

        portfolio_var = np.dot(weight_array.T, np.dot(annual_cov, weight_array))
        return np.sqrt(portfolio_var)

    async def generate_risk_parity_report(
        self,
        returns_data: Dict[str, pd.Series],
        config: RiskParityConfig,
        current_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """生成风险平价报告"""
        try:
            # 计算目标权重
            target_result = await self.calculate_risk_parity_weights(returns_data, config)

            # 监控漂移
            if current_weights:
                drift_monitoring = await self.monitor_risk_parity_drift(
                    current_weights, target_result.weights, returns_data
                )
            else:
                drift_monitoring = None

            report = {
                "calculation_date": datetime.now().isoformat(),
                "method": config.method,
                "target_weights": target_result.weights,
                "risk_contributions": target_result.risk_contributions,
                "portfolio_metrics": {
                    "volatility": target_result.portfolio_volatility,
                    "diversification_ratio": target_result.diversification_ratio,
                    "effective_n_assets": target_result.effective_n_assets
                },
                "risk_contribution_balance": {
                    "min_contribution": min(target_result.risk_contributions.values()),
                    "max_contribution": max(target_result.risk_contributions.values()),
                    "std_contribution": np.std(list(target_result.risk_contributions.values())),
                    "target_deviation": np.std(list(target_result.risk_contributions.values()))  # 简化
                },
                "drift_monitoring": drift_monitoring,
                "recommendations": self._generate_recommendations(target_result, drift_monitoring)
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating risk parity report: {e}")
            raise

    def _generate_recommendations(
        self,
        result: RiskParityResult,
        drift_monitoring: Optional[Dict[str, Any]]
    ) -> List[str]:
        """生成风险平价建议"""
        recommendations = []

        # 分散化建议
        if result.diversification_ratio < 1.5:
            recommendations.append("分散化比率较低，建议增加更多低相关资产")

        # 有效资产数建议
        if result.effective_n_assets < 5:
            recommendations.append("有效资产数较少，建议增加资产多样性")

        # 风险贡献平衡建议
        contrib_std = np.std(list(result.risk_contributions.values()))
        if contrib_std > 0.05:
            recommendations.append("风险贡献分布不均匀，建议调整权重")

        # 漂移建议
        if drift_monitoring and drift_monitoring["rebalance_needed"]:
            recommendations.append("权重漂移超过阈值，建议进行再平衡")

        if not recommendations:
            recommendations.append("风险平价配置良好，维持当前设置")

        return recommendations
