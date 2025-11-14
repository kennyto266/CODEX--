"""
VaR (Value at Risk) 计算系统

实现历史模拟法、方差-协方差法、蒙特卡洛模拟等多种VaR计算方法
支持单资产和多资产组合的VaR/CVaR计算
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
import scipy.stats as stats
from scipy.linalg import cholesky
import warnings


class VaRMethod(str, Enum):
    """VaR计算方法"""
    HISTORICAL_SIMULATION = "historical_simulation"  # 历史模拟法
    PARAMETRIC = "parametric"  # 参数法 (方差-协方差)
    MONTE_CARLO = "monte_carlo"  # 蒙特卡洛模拟
    CORNISH_FISHER = "cornish_fisher"  #  Cornish-Fisher展开
    EXTREME_VALUE = "extreme_value"  # 极值理论


class VaRResult(BaseModel):
    """VaR计算结果"""
    method: VaRMethod = Field(..., description="计算方法")
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    cvar_95: float = Field(..., description="95% CVaR (期望损失)")
    cvar_99: float = Field(..., description="99% CVaR (期望损失)")
    var_90: Optional[float] = Field(None, description="90% VaR")
    confidence_intervals: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict, description="置信区间"
    )
    sample_size: int = Field(..., description="样本数量")
    calculation_date: datetime = Field(default_factory=datetime.now, description="计算日期")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="计算参数")


class PortfolioVaRResult(BaseModel):
    """组合VaR计算结果"""
    portfolio_var_95: float = Field(..., description="组合95% VaR")
    portfolio_var_99: float = Field(..., description="组合99% VaR")
    portfolio_cvar_95: float = Field(..., description="组合95% CVaR")
    portfolio_cvar_99: float = Field(..., description="组合99% CVaR")
    individual_vars: Dict[str, float] = Field(..., description="单个资产VaR")
    marginal_vars: Dict[str, float] = Field(..., description="边际VaR")
    component_vars: Dict[str, float] = Field(..., description="成分VaR")
    diversification_ratio: float = Field(..., description="分散化比率")
    correlation_matrix: Optional[np.ndarray] = Field(None, description="相关性矩阵")


class StressTestScenario(BaseModel):
    """压力测试场景"""
    name: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景描述")
    market_shock: Dict[str, float] = Field(..., description="市场冲击")
    volatility_multiplier: float = Field(1.0, description="波动率倍数")
    correlation_shift: Optional[Dict[Tuple[str, str], float]] = Field(
        None, description="相关性变化"
    )
    probability: float = Field(0.01, description="发生概率")


class VaRCalculator:
    """VaR计算引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.var_calculator")
        self.confidence_levels = [0.90, 0.95, 0.99, 0.999]
        self.risk_free_rate = 0.02 / 252  # 日无风险利率

    async def calculate_historical_var(
        self,
        returns: pd.Series,
        method: VaRMethod = VaRMethod.HISTORICAL_SIMULATION,
        window: Optional[int] = None
    ) -> VaRResult:
        """历史模拟法VaR计算"""
        try:
            self.logger.info("Calculating historical VaR")

            if len(returns) < 30:
                raise ValueError("Insufficient data for VaR calculation (minimum 30 observations)")

            # 使用滚动窗口 (如果指定)
            if window and window < len(returns):
                returns = returns.tail(window)

            # 计算不同置信水平的VaR
            var_90 = np.percentile(returns, 10)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            var_999 = np.percentile(returns, 0.1)

            # CVaR (期望损失) - 尾部条件期望
            cvar_95 = returns[returns <= var_95].mean()
            cvar_99 = returns[returns <= var_99].mean()
            cvar_999 = returns[returns <= var_999].mean()

            # 置信区间 (Bootstrap方法)
            n_bootstrap = 1000
            var_95_bootstrap = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(returns, size=len(returns), replace=True)
                var_95_bootstrap.append(np.percentile(sample, 5))

            var_95_ci = (
                np.percentile(var_95_bootstrap, 2.5),
                np.percentile(var_95_bootstrap, 97.5)
            )

            result = VaRResult(
                method=method,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                var_90=var_90,
                confidence_intervals={"var_95": var_95_ci},
                sample_size=len(returns),
                parameters={
                    "window": window,
                    "bootstrap_samples": n_bootstrap,
                    "data_period": f"{returns.index[0]} to {returns.index[-1]}"
                }
            )

            self.logger.info(f"Historical VaR calculated: 95% = {var_95:.4f}, 99% = {var_99:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating historical VaR: {e}")
            raise

    async def calculate_parametric_var(
        self,
        returns: pd.Series,
        distribution: str = "normal",
        method: VaRMethod = VaRMethod.PARAMETRIC
    ) -> VaRResult:
        """参数法VaR计算 (方差-协方差)"""
        try:
            self.logger.info("Calculating parametric VaR")

            # 计算统计量
            mean_return = returns.mean()
            std_return = returns.std()

            if std_return <= 0:
                raise ValueError("Zero or negative standard deviation")

            # 正态分布VaR
            var_95 = mean_return + std_return * stats.norm.ppf(0.05)
            var_99 = mean_return + std_return * stats.norm.ppf(0.01)
            var_90 = mean_return + std_return * stats.norm.ppf(0.10)

            # 假设正态分布的CVaR
            # CVaR = μ - σ * φ(α) / α, 其中φ是标准正态密度
            cvar_95 = mean_return - std_return * stats.norm.pdf(stats.norm.ppf(0.05)) / 0.05
            cvar_99 = mean_return - std_return * stats.norm.pdf(stats.norm.ppf(0.01)) / 0.01

            # t分布VaR (更保守)
            if distribution == "t":
                # 估计t分布的自由度
                nu = 5  # 简化为5
                var_95_t = mean_return + std_return * stats.t.ppf(0.05, nu)
                var_99_t = mean_return + std_return * stats.t.ppf(0.01, nu)

                # 更新CVaR
                cvar_95_t = mean_return - std_return * stats.t.pdf(stats.t.ppf(0.05, nu), nu) / 0.05
                cvar_99_t = mean_return - std_return * stats.t.pdf(stats.t.ppf(0.01, nu), nu) / 0.01

                var_95 = var_95_t
                var_99 = var_99_t
                cvar_95 = cvar_95_t
                cvar_99 = cvar_99_t

            # 置信区间
            n = len(returns)
            var_95_se = stats.norm.ppf(0.05) * std_return / np.sqrt(n)
            var_95_ci = (var_95 - 1.96 * var_95_se, var_95 + 1.96 * var_95_se)

            result = VaRResult(
                method=method,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                var_90=var_90,
                confidence_intervals={"var_95": var_95_ci},
                sample_size=n,
                parameters={
                    "mean": mean_return,
                    "std": std_return,
                    "distribution": distribution,
                    "df": nu if distribution == "t" else None
                }
            )

            self.logger.info(f"Parametric VaR calculated: 95% = {var_95:.4f}, 99% = {var_99:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating parametric VaR: {e}")
            raise

    async def calculate_cornish_fisher_var(
        self,
        returns: pd.Series,
        method: VaRMethod = VaRMethod.CORNISH_FISHER
    ) -> VaRResult:
        """Cornish-Fisher展开VaR计算 (考虑偏度和峰度)"""
        try:
            self.logger.info("Calculating Cornish-Fisher VaR")

            # 计算高阶矩
            mean_return = returns.mean()
            std_return = returns.std()

            if std_return <= 0:
                raise ValueError("Zero standard deviation")

            # 标准化收益
            z = (returns - mean_return) / std_return

            # 计算偏度和峰度
            skewness = stats.skew(z)
            kurtosis = stats.kurtosis(z)  # 超出正态分布的峰度

            # 修正的分位数
            z_95 = stats.norm.ppf(0.05)
            z_99 = stats.norm.ppf(0.01)

            # Cornish-Fisher展开
            cf_95 = z_95 + (skewness / 6) * (z_95 ** 2 - 1) + (kurtosis / 24) * (z_95 ** 3 - 3 * z_95) - (skewness ** 2 / 36) * (2 * z_95 ** 3 - 5 * z_95)
            cf_99 = z_99 + (skewness / 6) * (z_99 ** 2 - 1) + (kurtosis / 24) * (z_99 ** 3 - 3 * z_99) - (skewness ** 2 / 36) * (2 * z_99 ** 3 - 5 * z_99)

            # 转换为VaR
            var_95 = mean_return + std_return * cf_95
            var_99 = mean_return + std_return * cf_99
            var_90 = mean_return + std_return * stats.norm.ppf(0.10)  # 简化

            # CVaR近似
            cvar_95 = mean_return - std_return * stats.norm.pdf(stats.norm.ppf(0.05)) / 0.05
            cvar_99 = mean_return - std_return * stats.norm.pdf(stats.norm.ppf(0.01)) / 0.01

            # 置信区间 (使用Bootstrap)
            n_bootstrap = 500
            var_95_bootstrap = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(returns, size=len(returns), replace=True)
                sample_mean = sample.mean()
                sample_std = sample.std()
                sample_z = (sample - sample_mean) / sample_std
                sample_skew = stats.skew(sample_z)
                sample_kurt = stats.kurtosis(sample_z)

                z_95_sample = stats.norm.ppf(0.05)
                cf_95_sample = z_95_sample + (sample_skew / 6) * (z_95_sample ** 2 - 1)
                var_95_bootstrap.append(sample_mean + sample_std * cf_95_sample)

            var_95_ci = (
                np.percentile(var_95_bootstrap, 2.5),
                np.percentile(var_95_bootstrap, 97.5)
            )

            result = VaRResult(
                method=method,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                var_90=var_90,
                confidence_intervals={"var_95": var_95_ci},
                sample_size=len(returns),
                parameters={
                    "mean": mean_return,
                    "std": std_return,
                    "skewness": skewness,
                    "kurtosis": kurtosis
                }
            )

            self.logger.info(f"Cornish-Fisher VaR calculated: 95% = {var_95:.4f}, 99% = {var_99:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating Cornish-Fisher VaR: {e}")
            raise

    async def calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        simulations: int = 100000,
        method: VaRMethod = VaRMethod.MONTE_CARLO
    ) -> VaRResult:
        """蒙特卡洛模拟VaR计算"""
        try:
            self.logger.info("Calculating Monte Carlo VaR")

            # 估计分布参数
            mean_return = returns.mean()
            std_return = returns.std()

            if std_return <= 0:
                raise ValueError("Zero standard deviation")

            # 生成随机收益 (使用t分布，更保守)
            nu = 5  # 自由度
            random_returns = stats.t.rvs(df=nu, size=simulations)
            random_returns = random_returns * std_return + mean_return

            # 计算VaR
            var_95 = np.percentile(random_returns, 5)
            var_99 = np.percentile(random_returns, 1)
            var_90 = np.percentile(random_returns, 10)
            var_999 = np.percentile(random_returns, 0.1)

            # CVaR
            cvar_95 = random_returns[random_returns <= var_95].mean()
            cvar_99 = random_returns[random_returns <= var_99].mean()
            cvar_999 = random_returns[random_returns <= var_999].mean()

            # 置信区间
            var_95_ci = (
                np.percentile(random_returns, 5 - 1.96 * np.sqrt(0.05 * 0.95 / simulations)),
                np.percentile(random_returns, 5 + 1.96 * np.sqrt(0.05 * 0.95 / simulations))
            )

            result = VaRResult(
                method=method,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                var_90=var_90,
                confidence_intervals={"var_95": var_95_ci},
                sample_size=simulations,
                parameters={
                    "simulations": simulations,
                    "distribution": "t",
                    "degrees_of_freedom": nu
                }
            )

            self.logger.info(f"Monte Carlo VaR calculated: 95% = {var_95:.4f}, 99% = {var_99:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating Monte Carlo VaR: {e}")
            raise

    async def calculate_portfolio_var(
        self,
        returns_data: Dict[str, pd.Series],
        weights: Dict[str, float],
        method: VaRMethod = VaRMethod.HISTORICAL_SIMULATION
    ) -> PortfolioVaRResult:
        """计算组合VaR"""
        try:
            self.logger.info("Calculating portfolio VaR")

            # 准备数据
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()

            # 权重
            weight_array = np.array([weights[symbol] for symbol in returns_df.columns])
            weight_array = weight_array / weight_array.sum()  # 归一化

            # 计算组合收益
            portfolio_returns = (returns_df * weight_array).sum(axis=1)

            # 单资产VaR
            individual_vars = {}
            for symbol, series in returns_data.items():
                var_95 = np.percentile(series.dropna(), 5)
                individual_vars[symbol] = var_95

            # 组合历史VaR
            portfolio_var_95 = np.percentile(portfolio_returns, 5)
            portfolio_var_99 = np.percentile(portfolio_returns, 1)

            # 组合CVaR
            portfolio_cvar_95 = portfolio_returns[portfolio_returns <= portfolio_var_95].mean()
            portfolio_cvar_99 = portfolio_returns[portfolio_returns <= portfolio_var_99].mean()

            # 边际VaR和成分VaR
            correlation_matrix = returns_df.corr().values
            portfolio_vol = np.sqrt(np.dot(weight_array.T, np.dot(returns_df.cov(), weight_array)))

            marginal_vars = {}
            component_vars = {}

            for i, symbol in enumerate(returns_df.columns):
                # 边际VaR
                marginal_var = correlation_matrix[i, :] @ (weight_array * returns_df.std()) / portfolio_vol
                marginal_vars[symbol] = marginal_var * stats.norm.ppf(0.05)

                # 成分VaR
                component_vars[symbol] = weight_array[i] * marginal_vars[symbol]

            # 分散化比率
            weighted_individual_var = sum(
                weight_array[i] ** 2 * returns_df.iloc[:, i].std() ** 2
                for i in range(len(weight_array))
            )
            portfolio_var_95_under_independence = -stats.norm.ppf(0.05) * np.sqrt(weighted_individual_var)
            diversification_ratio = portfolio_var_95_under_independence / abs(portfolio_var_95)

            result = PortfolioVaRResult(
                portfolio_var_95=portfolio_var_95,
                portfolio_var_99=portfolio_var_99,
                portfolio_cvar_95=portfolio_cvar_95,
                portfolio_cvar_99=portfolio_cvar_99,
                individual_vars=individual_vars,
                marginal_vars=marginal_vars,
                component_vars=component_vars,
                diversification_ratio=diversification_ratio,
                correlation_matrix=correlation_matrix
            )

            self.logger.info(f"Portfolio VaR calculated: 95% = {portfolio_var_95:.4f}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating portfolio VaR: {e}")
            raise

    async def run_stress_test(
        self,
        returns_data: Dict[str, pd.Series],
        weights: Dict[str, float],
        scenarios: List[StressTestScenario]
    ) -> Dict[str, Any]:
        """压力测试分析"""
        try:
            self.logger.info(f"Running stress test with {len(scenarios)} scenarios")

            # 当前组合价值
            current_value = 1000000  # 假设100万
            weight_array = np.array([weights[symbol] for symbol in returns_data.keys()])
            weight_array = weight_array / weight_array.sum()

            stress_results = {}

            for scenario in scenarios:
                scenario_name = scenario.name
                self.logger.info(f"Running scenario: {scenario_name}")

                # 应用市场冲击
                shocked_prices = {}
                for symbol, price_shock in scenario.market_shock.items():
                    shocked_prices[symbol] = price_shock

                # 计算冲击后的组合价值
                scenario_value = current_value * (1 + sum(
                    weight_array[i] * shocked_prices[symbol]
                    for i, symbol in enumerate(returns_data.keys())
                ))

                # 损失
                loss = current_value - scenario_value
                loss_rate = loss / current_value

                stress_results[scenario_name] = {
                    "original_value": current_value,
                    "stressed_value": scenario_value,
                    "absolute_loss": loss,
                    "loss_rate": loss_rate,
                    "scenario": scenario.description,
                    "probability": scenario.probability
                }

            return stress_results

        except Exception as e:
            self.logger.error(f"Error running stress test: {e}")
            raise

    async def validate_var(
        self,
        returns: pd.Series,
        var_estimates: Dict[VaRMethod, float],
        window: int = 252
    ) -> Dict[str, Any]:
        """VaR模型验证 (回测)"""
        try:
            self.logger.info("Validating VaR models")

            # 计算失败率
            validation_results = {}

            for method, var_estimate in var_estimates.items():
                # 计算超过VaR的天数
                violations = (returns < var_estimate).sum()

                # 期望的失败次数
                expected_violations = len(returns) * 0.05  # 对于95% VaR

                # Kupiec测试
                if expected_violations > 0:
                    kupiec_lr = 2 * (violations * np.log(violations / expected_violations) + (len(returns) - violations) * np.log((len(returns) - violations) / (len(returns) - expected_violations)))
                    kupiec_p_value = 1 - stats.chi2.cdf(kupiec_lr, df=1)
                else:
                    kupiec_lr = 0
                    kupiec_p_value = 1

                validation_results[method] = {
                    "violations": violations,
                    "expected_violations": expected_violations,
                    "violation_rate": violations / len(returns),
                    "kupiec_lr_stat": kupiec_lr,
                    "kupiec_p_value": kupiec_p_value,
                    "model_acceptable": kupiec_p_value > 0.05
                }

            return validation_results

        except Exception as e:
            self.logger.error(f"Error validating VaR: {e}")
            raise
