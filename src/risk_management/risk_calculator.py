"""
風險計算器 - 核心風險指標計算

計算VaR、ES、最大回撤、夏普比率等風險指標
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
import scipy.stats as stats


class RiskLevel(str, Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskMetrics(BaseModel):
    """風險指標"""
    # 基本指標
    volatility: float = Field(..., description="波動率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    calmar_ratio: float = Field(..., description="卡爾瑪比率")
    
    # VaR指標
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    expected_shortfall_95: float = Field(..., description="95% 期望損失")
    expected_shortfall_99: float = Field(..., description="99% 期望損失")
    
    # 其他風險指標
    beta: float = Field(..., description="貝塔係數")
    tracking_error: float = Field(..., description="跟踪誤差")
    information_ratio: float = Field(..., description="信息比率")
    sortino_ratio: float = Field(..., description="索提諾比率")
    
    # 風險等級
    risk_level: RiskLevel = Field(..., description="風險等級")
    
    # 元數據
    calculation_date: datetime = Field(default_factory=datetime.now, description="計算日期")
    data_points: int = Field(..., description="數據點數量")
    confidence_level: float = Field(..., description="置信水平")


class RiskLimits(BaseModel):
    """風險限制"""
    max_position_size: float = Field(0.1, description="最大持倉比例")
    max_portfolio_risk: float = Field(0.05, description="最大組合風險")
    max_drawdown_limit: float = Field(0.15, description="最大回撤限制")
    max_var_limit: float = Field(0.02, description="最大VaR限制")
    max_leverage: float = Field(2.0, description="最大槓桿")
    max_concentration: float = Field(0.2, description="最大集中度")
    min_liquidity: float = Field(0.1, description="最小流動性要求")
    
    # 警報閾值
    var_alert_threshold: float = Field(0.015, description="VaR警報閾值")
    drawdown_alert_threshold: float = Field(0.1, description="回撤警報閾值")
    volatility_alert_threshold: float = Field(0.3, description="波動率警報閾值")


class RiskCalculator:
    """風險計算器"""
    
    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.risk_calculator")
        self.risk_free_rate = 0.02  # 無風險利率（年化）
        
    async def calculate_portfolio_risk(
        self, 
        returns: pd.Series, 
        weights: Optional[pd.Series] = None,
        benchmark_returns: Optional[pd.Series] = None
    ) -> RiskMetrics:
        """計算組合風險指標"""
        try:
            self.logger.info("Calculating portfolio risk metrics...")
            
            if len(returns) < 30:
                raise ValueError("Insufficient data for risk calculation (minimum 30 observations)")
            
            # 基本統計量
            mean_return = returns.mean()
            volatility = returns.std() * np.sqrt(252)  # 年化波動率
            
            # 夏普比率
            excess_return = mean_return - self.risk_free_rate / 252
            sharpe_ratio = excess_return / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            
            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdowns.min())
            
            # 卡爾瑪比率
            calmar_ratio = mean_return * 252 / max_drawdown if max_drawdown > 0 else 0
            
            # VaR計算
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # 期望損失（ES）
            expected_shortfall_95 = returns[returns <= var_95].mean()
            expected_shortfall_99 = returns[returns <= var_99].mean()
            
            # 貝塔係數（相對於基準）
            beta = 0.0
            tracking_error = 0.0
            information_ratio = 0.0
            
            if benchmark_returns is not None and len(benchmark_returns) == len(returns):
                # 計算貝塔
                covariance = np.cov(returns, benchmark_returns)[0, 1]
                benchmark_variance = np.var(benchmark_returns)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                
                # 跟踪誤差
                active_returns = returns - benchmark_returns
                tracking_error = active_returns.std() * np.sqrt(252)
                
                # 信息比率
                active_return = active_returns.mean() * 252
                information_ratio = active_return / tracking_error if tracking_error > 0 else 0
            
            # 索提諾比率
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
            
            # 風險等級評估
            risk_level = self._assess_risk_level(volatility, max_drawdown, var_95)
            
            metrics = RiskMetrics(
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall_95=expected_shortfall_95,
                expected_shortfall_99=expected_shortfall_99,
                beta=beta,
                tracking_error=tracking_error,
                information_ratio=information_ratio,
                sortino_ratio=sortino_ratio,
                risk_level=risk_level,
                data_points=len(returns),
                confidence_level=0.95
            )
            
            self.logger.info(f"Risk calculation completed. Risk level: {risk_level}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio risk: {e}")
            raise
    
    async def calculate_position_risk(
        self, 
        position_value: Decimal, 
        position_returns: pd.Series,
        portfolio_value: Decimal
    ) -> Dict[str, Any]:
        """計算單個持倉風險"""
        try:
            # 持倉比例
            position_weight = float(position_value / portfolio_value)
            
            # 持倉波動率
            position_volatility = position_returns.std() * np.sqrt(252)
            
            # 持倉VaR
            position_var_95 = np.percentile(position_returns, 5)
            position_var_99 = np.percentile(position_returns, 1)
            
            # 持倉對組合的風險貢獻
            portfolio_returns = position_returns * position_weight
            risk_contribution = position_volatility * position_weight
            
            return {
                "position_weight": position_weight,
                "position_volatility": position_volatility,
                "position_var_95": position_var_95,
                "position_var_99": position_var_99,
                "risk_contribution": risk_contribution,
                "portfolio_impact": float(portfolio_returns.std() * np.sqrt(252))
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position risk: {e}")
            return {}
    
    async def calculate_correlation_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """計算相關性矩陣"""
        try:
            correlation_matrix = returns_data.corr()
            return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    async def calculate_covariance_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """計算協方差矩陣"""
        try:
            covariance_matrix = returns_data.cov() * 252  # 年化協方差
            return covariance_matrix
            
        except Exception as e:
            self.logger.error(f"Error calculating covariance matrix: {e}")
            return pd.DataFrame()
    
    async def calculate_portfolio_var(
        self, 
        weights: pd.Series, 
        covariance_matrix: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> float:
        """計算組合VaR"""
        try:
            # 確保權重和協方差矩陣的標的順序一致
            common_symbols = weights.index.intersection(covariance_matrix.index)
            weights_aligned = weights[common_symbols]
            cov_aligned = covariance_matrix.loc[common_symbols, common_symbols]
            
            # 組合方差
            portfolio_variance = np.dot(weights_aligned, np.dot(cov_aligned, weights_aligned))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # VaR計算
            alpha = 1 - confidence_level
            z_score = stats.norm.ppf(alpha)
            portfolio_var = abs(z_score * portfolio_volatility)
            
            return portfolio_var
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio VaR: {e}")
            return 0.0
    
    async def calculate_marginal_var(
        self, 
        weights: pd.Series, 
        covariance_matrix: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> pd.Series:
        """計算邊際VaR"""
        try:
            # 確保權重和協方差矩陣的標的順序一致
            common_symbols = weights.index.intersection(covariance_matrix.index)
            weights_aligned = weights[common_symbols]
            cov_aligned = covariance_matrix.loc[common_symbols, common_symbols]
            
            # 組合方差
            portfolio_variance = np.dot(weights_aligned, np.dot(cov_aligned, weights_aligned))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # 邊際VaR
            alpha = 1 - confidence_level
            z_score = stats.norm.ppf(alpha)
            
            marginal_var = {}
            for symbol in common_symbols:
                marginal_var[symbol] = z_score * np.dot(cov_aligned[symbol], weights_aligned) / portfolio_volatility
            
            return pd.Series(marginal_var)
            
        except Exception as e:
            self.logger.error(f"Error calculating marginal VaR: {e}")
            return pd.Series()
    
    async def calculate_component_var(
        self, 
        weights: pd.Series, 
        covariance_matrix: pd.DataFrame,
        confidence_level: float = 0.95
    ) -> pd.Series:
        """計算成分VaR"""
        try:
            marginal_var = await self.calculate_marginal_var(weights, covariance_matrix, confidence_level)
            component_var = marginal_var * weights
            
            return component_var
            
        except Exception as e:
            self.logger.error(f"Error calculating component VaR: {e}")
            return pd.Series()
    
    async def calculate_stress_test(
        self, 
        returns: pd.Series, 
        stress_scenarios: Dict[str, float]
    ) -> Dict[str, Any]:
        """計算壓力測試"""
        try:
            stress_results = {}
            
            for scenario_name, stress_factor in stress_scenarios.items():
                # 應用壓力因子
                stressed_returns = returns * stress_factor
                
                # 計算壓力下的指標
                stressed_var_95 = np.percentile(stressed_returns, 5)
                stressed_var_99 = np.percentile(stressed_returns, 1)
                stressed_max_drawdown = self._calculate_max_drawdown(stressed_returns)
                
                stress_results[scenario_name] = {
                    "stress_factor": stress_factor,
                    "var_95": stressed_var_95,
                    "var_99": stressed_var_99,
                    "max_drawdown": stressed_max_drawdown,
                    "expected_loss": stressed_returns.mean()
                }
            
            return stress_results
            
        except Exception as e:
            self.logger.error(f"Error calculating stress test: {e}")
            return {}
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """計算最大回撤"""
        try:
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max
            return abs(drawdowns.min())
        except Exception:
            return 0.0
    
    def _assess_risk_level(self, volatility: float, max_drawdown: float, var_95: float) -> RiskLevel:
        """評估風險等級"""
        try:
            risk_score = 0
            
            # 波動率評分
            if volatility > 0.4:
                risk_score += 3
            elif volatility > 0.25:
                risk_score += 2
            elif volatility > 0.15:
                risk_score += 1
            
            # 最大回撤評分
            if max_drawdown > 0.2:
                risk_score += 3
            elif max_drawdown > 0.15:
                risk_score += 2
            elif max_drawdown > 0.1:
                risk_score += 1
            
            # VaR評分
            if var_95 < -0.05:
                risk_score += 3
            elif var_95 < -0.03:
                risk_score += 2
            elif var_95 < -0.02:
                risk_score += 1
            
            # 風險等級判定
            if risk_score >= 7:
                return RiskLevel.CRITICAL
            elif risk_score >= 5:
                return RiskLevel.HIGH
            elif risk_score >= 3:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW
                
        except Exception:
            return RiskLevel.MEDIUM
    
    async def calculate_monte_carlo_var(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """蒙特卡羅VaR計算"""
        try:
            # 擬合分佈參數
            mean_return = returns.mean()
            std_return = returns.std()
            
            # 蒙特卡羅模擬
            simulated_returns = np.random.normal(mean_return, std_return, (num_simulations, time_horizon))
            
            # 計算累積收益
            cumulative_returns = np.prod(1 + simulated_returns, axis=1) - 1
            
            # VaR計算
            alpha = 1 - confidence_level
            var = np.percentile(cumulative_returns, alpha * 100)
            
            # 期望損失
            expected_shortfall = cumulative_returns[cumulative_returns <= var].mean()
            
            return {
                "var": var,
                "expected_shortfall": expected_shortfall,
                "confidence_level": confidence_level,
                "num_simulations": num_simulations,
                "time_horizon": time_horizon
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Monte Carlo VaR: {e}")
            return {}
    
    async def calculate_historical_var(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, Any]:
        """歷史模擬VaR計算"""
        try:
            # 滾動窗口計算
            if time_horizon > 1:
                rolling_returns = returns.rolling(window=time_horizon).sum().dropna()
            else:
                rolling_returns = returns
            
            # VaR計算
            alpha = 1 - confidence_level
            var = np.percentile(rolling_returns, alpha * 100)
            
            # 期望損失
            expected_shortfall = rolling_returns[rolling_returns <= var].mean()
            
            return {
                "var": var,
                "expected_shortfall": expected_shortfall,
                "confidence_level": confidence_level,
                "time_horizon": time_horizon,
                "data_points": len(rolling_returns)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating historical VaR: {e}")
            return {}
    
    async def calculate_risk_budget(
        self, 
        weights: pd.Series, 
        risk_limits: RiskLimits
    ) -> Dict[str, Any]:
        """計算風險預算"""
        try:
            risk_budget = {}
            
            # 持倉限制檢查
            max_position_violations = weights[weights > risk_limits.max_position_size]
            if len(max_position_violations) > 0:
                risk_budget["position_violations"] = max_position_violations.to_dict()
            
            # 集中度檢查
            concentration = weights.max()
            if concentration > risk_limits.max_concentration:
                risk_budget["concentration_violation"] = {
                    "max_concentration": concentration,
                    "limit": risk_limits.max_concentration
                }
            
            # 槓桿檢查
            total_leverage = weights.abs().sum()
            if total_leverage > risk_limits.max_leverage:
                risk_budget["leverage_violation"] = {
                    "total_leverage": total_leverage,
                    "limit": risk_limits.max_leverage
                }
            
            return risk_budget
            
        except Exception as e:
            self.logger.error(f"Error calculating risk budget: {e}")
            return {}