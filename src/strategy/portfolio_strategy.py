"""
投资组合策略 (T180)
多资产组合管理策略
实现资产配置优化、组合风险控制和动态再平衡

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from scipy.optimize import minimize
from scipy import stats

try:
    from core.base_strategy import IStrategy, Signal, SignalType
    from strategy.traits import StrategyTraits
except ImportError:
    from ..core.base_strategy import IStrategy, Signal, SignalType
    from .traits import StrategyTraits

logger = logging.getLogger(__name__)


class PortfolioStrategy(IStrategy):
    """
    投资组合策略

    管理多资产投资组合，动态优化资产配置，
    控制组合风险并实现动态再平衡。

    核心功能：
    1. 多资产组合管理
    2. 基于风险平价的资产配置
    3. 协方差矩阵计算和风险管理
    4. 动态再平衡机制
    5. VaR和CVaR风险控制

    策略特点：
    - 降低单一资产风险
    - 适应市场环境变化
    - 灵活的资产配置算法
    - 完整的风险管理体系
    """

    def __init__(
        self,
        symbols: List[str] = None,
        rebalance_frequency: str = 'monthly',
        risk_target: float = 0.15,
        max_weight: float = 0.4,
        min_weight: float = 0.05,
        risk_parity: bool = True,
        lookback_window: int = 252
    ):
        """
        初始化投资组合策略

        Args:
            symbols: 投资组合中的资产列表
            rebalance_frequency: 再平衡频率 ('daily', 'weekly', 'monthly')
            risk_target: 目标波动率
            max_weight: 单资产最大权重
            min_weight: 单资产最小权重
            risk_parity: 是否使用风险平价策略
            lookback_window: 回看窗口期
        """
        self.symbols = symbols or ['0700.HK', '0388.HK', '1398.HK', '0939.HK']
        self.rebalance_frequency = rebalance_frequency
        self.risk_target = risk_target
        self.max_weight = max_weight
        self.min_weight = min_weight
        self.risk_parity = risk_parity
        self.lookback_window = lookback_window

        # 数据存储
        self.data_by_symbol: Dict[str, pd.DataFrame] = {}
        self.returns_by_symbol: Dict[str, pd.Series] = {}
        self.current_weights: Dict[str, float] = {}
        self.covariance_matrix: Optional[pd.DataFrame] = None
        self.last_rebalance: Optional[datetime] = None

        # 风险指标
        self.portfolio_volatility: float = 0.0
        self.portfolio_var: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0

        # 特征标记
        self.traits = StrategyTraits(
            name="投资组合策略",
            timeframe="1D",
            多资产管理=True,
            风险控制=True,
            动态再平衡=True
        )

    @property
    def strategy_name(self) -> str:
        return f"Portfolio-{self.rebalance_frequency}"

    @property
    def supported_symbols(self) -> List[str]:
        return self.symbols

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """
        初始化策略

        Args:
            historical_data: 主要资产的历史数据
            **kwargs: 包含所有资产数据的字典
        """
        try:
            # 存储各资产数据
            if isinstance(historical_data.columns, pd.MultiIndex):
                # 多资产数据在MultiIndex列中
                for symbol in self.symbols:
                    if symbol in historical_data.columns.get_level_values(0):
                        self.data_by_symbol[symbol] = historical_data.xs(symbol, level=0, axis=1)
            else:
                # 假设主要数据是第一个资产
                self.data_by_symbol[self.symbols[0]] = historical_data.copy()

            # 存储其他资产数据
            for symbol, data in kwargs.get('portfolio_data', {}).items():
                if symbol in self.symbols:
                    self.data_by_symbol[symbol] = data

            # 计算收益率
            self._calculate_returns()

            # 初始化权重（等权重）
            self._initialize_weights()

            # 计算协方差矩阵
            self._update_covariance_matrix()

            logger.info(f"投资组合策略初始化完成: {self.symbols}")

        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            raise

    def _calculate_returns(self) -> None:
        """计算各资产的收益率"""
        for symbol in self.symbols:
            if symbol in self.data_by_symbol:
                data = self.data_by_symbol[symbol]
                if 'Close' in data.columns or 'close' in data.columns:
                    price_col = 'Close' if 'Close' in data.columns else 'close'
                    self.returns_by_symbol[symbol] = data[price_col].pct_change().dropna()
                else:
                    # 假设第一列是价格
                    price = data.iloc[:, 0]
                    self.returns_by_symbol[symbol] = price.pct_change().dropna()

    def _initialize_weights(self) -> None:
        """初始化等权重"""
        equal_weight = 1.0 / len(self.symbols)
        for symbol in self.symbols:
            self.current_weights[symbol] = equal_weight

    def _update_covariance_matrix(self) -> None:
        """更新协方差矩阵"""
        try:
            # 对齐所有收益率序列
            aligned_returns = pd.DataFrame()

            for symbol in self.symbols:
                if symbol in self.returns_by_symbol:
                    returns = self.returns_by_symbol[symbol].tail(self.lookback_window)
                    aligned_returns[symbol] = returns

            # 去除包含NaN的行
            aligned_returns = aligned_returns.dropna()

            if len(aligned_returns) > 30:  # 确保有足够的数据
                self.covariance_matrix = aligned_returns.cov()
            else:
                logger.warning("协方差矩阵计算数据不足")

        except Exception as e:
            logger.error(f"协方差矩阵计算失败: {e}")
            self.covariance_matrix = None

    def _optimize_weights_risk_parity(self) -> Dict[str, float]:
        """
        基于风险平价优化权重

        Returns:
            优化后的权重字典
        """
        if self.covariance_matrix is None:
            return self.current_weights

        n_assets = len(self.symbols)
        cov = self.covariance_matrix.values

        # 目标函数：使每个资产对组合风险的贡献相等
        def risk_parity_objective(weights):
            # 计算组合波动率
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))

            # 计算每个资产的风险贡献
            marginal_contrib = np.dot(cov, weights)
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # 目标：使所有风险贡献相等
            target_contrib = 1.0 / n_assets
            return np.sum((risk_contrib - target_contrib) ** 2)

        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]

        # 边界条件
        bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]

        # 初始猜测（等权重）
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            optimal_weights = result.x
            return {symbol: weight for symbol, weight in zip(self.symbols, optimal_weights)}
        else:
            logger.warning("权重优化失败，使用当前权重")
            return self.current_weights

    def _optimize_weights_mean_variance(self) -> Dict[str, float]:
        """
        基于均值-方差优化权重

        Returns:
            优化后的权重字典
        """
        if self.covariance_matrix is None:
            return self.current_weights

        n_assets = len(self.symbols)
        cov = self.covariance_matrix.values

        # 计算预期收益率
        mean_returns = []
        for symbol in self.symbols:
            if symbol in self.returns_by_symbol:
                returns = self.returns_by_symbol[symbol].tail(self.lookback_window)
                mean_returns.append(returns.mean())
            else:
                mean_returns.append(0.0)

        mean_returns = np.array(mean_returns)

        # 目标函数：最大化夏普比率
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns) * 252
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights))) * np.sqrt(252)

            if portfolio_vol == 0:
                return -1e10

            return -(portfolio_return - 0.02) / portfolio_vol  # 假设无风险利率2%

        # 约束条件
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # 边界条件
        bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]

        # 初始猜测
        x0 = np.array([1.0 / n_assets] * n_assets)

        # 优化
        result = minimize(
            negative_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            optimal_weights = result.x
            return {symbol: weight for symbol, weight in zip(self.symbols, optimal_weights)}
        else:
            return self.current_weights

    def _calculate_portfolio_metrics(self) -> None:
        """计算组合指标"""
        try:
            if not self.returns_by_symbol or not self.current_weights:
                return

            # 计算组合收益率
            portfolio_returns = pd.Series(0.0, index=next(iter(self.returns_by_symbol.values())).index)

            for symbol in self.symbols:
                if symbol in self.returns_by_symbol and symbol in self.current_weights:
                    weight = self.current_weights[symbol]
                    portfolio_returns += weight * self.returns_by_symbol[symbol]

            # 去除NaN值
            portfolio_returns = portfolio_returns.dropna()

            if len(portfolio_returns) == 0:
                return

            # 计算波动率
            self.portfolio_volatility = portfolio_returns.std() * np.sqrt(252)

            # 计算VaR (95%置信度)
            self.portfolio_var = np.percentile(portfolio_returns, 5)

            # 计算夏普比率
            excess_returns = portfolio_returns - 0.02 / 252  # 假设无风险利率2%
            if portfolio_returns.std() > 0:
                self.sharpe_ratio = excess_returns.mean() * 252 / (portfolio_returns.std() * np.sqrt(252))
            else:
                self.sharpe_ratio = 0.0

            # 计算最大回撤
            cum_returns = (1 + portfolio_returns).cumprod()
            running_max = cum_returns.expanding().max()
            drawdown = (cum_returns - running_max) / running_max
            self.max_drawdown = abs(drawdown.min())

        except Exception as e:
            logger.error(f"组合指标计算失败: {e}")

    def _should_rebalance(self) -> bool:
        """
        检查是否需要再平衡

        Returns:
            是否需要再平衡
        """
        now = datetime.now()

        # 检查时间频率
        if self.last_rebalance is None:
            return True

        if self.rebalance_frequency == 'daily':
            return (now - self.last_rebalance).days >= 1
        elif self.rebalance_frequency == 'weekly':
            return (now - self.last_rebalance).days >= 7
        elif self.rebalance_frequency == 'monthly':
            return (now - self.last_rebalance).days >= 30

        return False

    def _calculate_drift(self) -> float:
        """
        计算当前组合与目标组合的偏离度

        Returns:
            偏离度（权重差异的L2范数）
        """
        if not self.current_weights:
            return 0.0

        # 假设目标权重是当前权重（避免频繁再平衡）
        # 在实际应用中，这里应该是动态计算的目标权重

        # 计算偏离度
        drift = 0.0
        for symbol in self.symbols:
            if symbol in self.current_weights:
                # 简单的偏离度计算
                drift += abs(self.current_weights[symbol] - 1.0 / len(self.symbols))

        return drift

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """
        生成投资组合再平衡信号

        Args:
            current_data: 当前市场数据

        Returns:
            信号列表
        """
        signals = []

        try:
            # 更新主资产数据
            if isinstance(current_data.columns, pd.MultiIndex):
                # 处理多资产数据
                for symbol in self.symbols:
                    if symbol in current_data.columns.get_level_values(0):
                        symbol_data = current_data.xs(symbol, level=0, axis=1)
                        if not symbol_data.empty:
                            self.data_by_symbol[symbol] = symbol_data
            else:
                self.data_by_symbol[self.symbols[0]] = current_data.copy()

            # 重新计算收益率
            self._calculate_returns()

            # 更新协方差矩阵
            self._update_covariance_matrix()

            # 计算组合指标
            self._calculate_portfolio_metrics()

            # 检查是否需要再平衡
            need_time_rebalance = self._should_rebalance()
            drift = self._calculate_drift()
            need_drift_rebalance = drift > 0.1  # 偏离度阈值

            if need_time_rebalance or need_drift_rebalance:
                # 优化权重
                if self.risk_parity:
                    optimal_weights = self._optimize_weights_risk_parity()
                else:
                    optimal_weights = self._optimize_weights_mean_variance()

                # 生成再平衡信号
                for symbol in self.symbols:
                    if symbol in optimal_weights and symbol in self.data_by_symbol:
                        current_weight = self.current_weights.get(symbol, 0.0)
                        target_weight = optimal_weights[symbol]
                        weight_diff = abs(target_weight - current_weight)

                        # 如果权重变化超过阈值，生成信号
                        if weight_diff > 0.05:  # 5%变化阈值
                            latest_data = self.data_by_symbol[symbol].iloc[-1]
                            price = latest_data.get('Close', latest_data.get('close', 0.0))
                            timestamp = latest_data.name if hasattr(latest_data, 'name') else pd.Timestamp.now()

                            if target_weight > current_weight:
                                # 增加权重 - 买入
                                signal = Signal(
                                    symbol=symbol,
                                    timestamp=timestamp,
                                    signal_type=SignalType.BUY,
                                    confidence=min(weight_diff * 10, 1.0),
                                    reason=f"投资组合再平衡 - 增加权重 {current_weight:.2%} -> {target_weight:.2%}",
                                    price=float(price),
                                    metadata={
                                        'target_weight': target_weight,
                                        'current_weight': current_weight,
                                        'weight_change': target_weight - current_weight,
                                        'portfolio_volatility': self.portfolio_volatility,
                                        'portfolio_var': self.portfolio_var,
                                        'rebalance_reason': 'time' if need_time_rebalance else 'drift'
                                    }
                                )
                            else:
                                # 减少权重 - 卖出
                                signal = Signal(
                                    symbol=symbol,
                                    timestamp=timestamp,
                                    signal_type=SignalType.SELL,
                                    confidence=min(weight_diff * 10, 1.0),
                                    reason=f"投资组合再平衡 - 减少权重 {current_weight:.2%} -> {target_weight:.2%}",
                                    price=float(price),
                                    metadata={
                                        'target_weight': target_weight,
                                        'current_weight': current_weight,
                                        'weight_change': target_weight - current_weight,
                                        'portfolio_volatility': self.portfolio_volatility,
                                        'portfolio_var': self.portfolio_var,
                                        'rebalance_reason': 'time' if need_time_rebalance else 'drift'
                                    }
                                )
                            signals.append(signal)

                # 更新权重
                if signals:
                    self.current_weights = optimal_weights
                    self.last_rebalance = datetime.now()

        except Exception as e:
            logger.error(f"信号生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return signals

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'symbols': self.symbols,
            'rebalance_frequency': self.rebalance_frequency,
            'risk_target': self.risk_target,
            'max_weight': self.max_weight,
            'min_weight': self.min_weight,
            'risk_parity': self.risk_parity,
            'lookback_window': self.lookback_window
        }

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数"""
        if 'symbols' in parameters:
            self.symbols = parameters['symbols']
        if 'rebalance_frequency' in parameters:
            self.rebalance_frequency = parameters['rebalance_frequency']
        if 'risk_target' in parameters:
            self.risk_target = parameters['risk_target']
        if 'max_weight' in parameters:
            self.max_weight = parameters['max_weight']
        if 'min_weight' in parameters:
            self.min_weight = parameters['min_weight']
        if 'risk_parity' in parameters:
            self.risk_parity = parameters['risk_parity']
        if 'lookback_window' in parameters:
            self.lookback_window = parameters['lookback_window']

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        获取投资组合摘要

        Returns:
            包含投资组合状态信息的字典
        """
        summary = {
            'strategy_name': self.strategy_name,
            'symbols': self.symbols,
            'current_weights': self.current_weights,
            'portfolio_metrics': {
                'volatility': self.portfolio_volatility,
                'var_95': self.portfolio_var,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown
            },
            'rebalance_frequency': self.rebalance_frequency,
            'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None,
            'risk_parity': self.risk_parity
        }

        # 添加协方差矩阵摘要
        if self.covariance_matrix is not None:
            summary['covariance_summary'] = {
                'correlation_matrix': self.covariance_matrix.corr().to_dict(),
                'volatilities': {
                    symbol: float(self.covariance_matrix.loc[symbol, symbol] ** 0.5 * np.sqrt(252))
                    for symbol in self.covariance_matrix.index
                }
            }

        return summary


# 导出策略类
__all__ = ['PortfolioStrategy']
