"""
风险调整收益模块

计算夏普比率、索提诺比率、卡玛比率等
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging


class RiskAdjustedReturns:
    """风险调整收益计算"""

    def __init__(self, risk_free_rate: float = 0.02):
        """
        初始化

        Args:
            risk_free_rate: 无风险利率（年化）
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger("cross_market_quant.RiskAdjustedReturns")

    def calculate_all(self, returns: pd.Series) -> Dict:
        """
        计算所有风险调整收益指标

        Args:
            returns: 收益序列

        Returns:
            风险调整收益指标
        """
        try:
            self.logger.info("计算风险调整收益指标")

            # 去除NaN值
            clean_returns = returns.dropna()

            if len(clean_returns) == 0:
                raise Exception("没有有效的收益数据")

            # 年化参数
            annual_factor = 252  # 假设252个交易日

            # 计算年化收益
            mean_return = clean_returns.mean()
            annualized_return = mean_return * annual_factor

            # 计算年化波动率
            volatility = clean_returns.std()
            annualized_vol = volatility * np.sqrt(annual_factor)

            # 计算下行波动率
            downside_returns = clean_returns[clean_returns < 0]
            downside_volatility = downside_returns.std() if len(downside_returns) > 0 else 0
            annualized_downside_vol = downside_volatility * np.sqrt(annual_factor)

            # 计算最大回撤
            cumulative = (1 + clean_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # 计算各种比率
            sharpe_ratio = self._calculate_sharpe_ratio(
                annualized_return, annualized_vol
            )

            sortino_ratio = self._calculate_sortino_ratio(
                annualized_return, annualized_downside_vol
            )

            calmar_ratio = self._calculate_calmar_ratio(
                annualized_return, max_drawdown
            )

            # 信息比率（简化：假设基准收益为0）
            excess_returns = clean_returns - self.risk_free_rate / annual_factor
            information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(annual_factor)

            result = {
                'total_return': cumulative.iloc[-1] - 1,
                'annualized_return': annualized_return,
                'annualized_volatility': annualized_vol,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'information_ratio': information_ratio,
                'downside_volatility': annualized_downside_vol,
                'positive_days': len(clean_returns[clean_returns > 0]),
                'negative_days': len(clean_returns[clean_returns < 0]),
                'win_rate': len(clean_returns[clean_returns > 0]) / len(clean_returns)
            }

            self.logger.info(f"风险调整收益计算完成: 夏普比率 {sharpe_ratio:.2f}")
            return result

        except Exception as e:
            self.logger.error(f"计算风险调整收益失败: {e}")
            return {'error': str(e)}

    def _calculate_sharpe_ratio(
        self,
        annualized_return: float,
        annualized_volatility: float
    ) -> float:
        """计算夏普比率"""
        excess_return = annualized_return - self.risk_free_rate
        return excess_return / annualized_volatility if annualized_volatility > 0 else 0

    def _calculate_sortino_ratio(
        self,
        annualized_return: float,
        annualized_downside_volatility: float
    ) -> float:
        """计算索提诺比率"""
        excess_return = annualized_return - self.risk_free_rate
        return excess_return / annualized_downside_volatility if annualized_downside_volatility > 0 else 0

    def _calculate_calmar_ratio(
        self,
        annualized_return: float,
        max_drawdown: float
    ) -> float:
        """计算卡玛比率"""
        return annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0

    def calculate_rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 60
    ) -> pd.DataFrame:
        """
        计算滚动风险调整指标

        Args:
            returns: 收益序列
            window: 滚动窗口

        Returns:
            滚动指标数据框
        """
        try:
            metrics = pd.DataFrame(index=returns.index)

            # 滚动夏普比率
            rolling_sharpe = returns.rolling(window=window).apply(
                lambda x: self._calculate_sharpe_ratio(
                    x.mean() * 252, x.std() * np.sqrt(252)
                ) if len(x.dropna()) >= window else np.nan
            )

            # 滚动索提诺比率
            rolling_sortino = returns.rolling(window=window).apply(
                lambda x: self._calculate_sortino_ratio(
                    x.mean() * 252, x[x < 0].std() * np.sqrt(252)
                ) if len(x.dropna()) >= window else np.nan
            )

            # 滚动最大回撤
            rolling_dd = returns.rolling(window=window).apply(
                lambda x: self._calculate_max_drawdown(x)
            )

            metrics['Rolling_Sharpe'] = rolling_sharpe
            metrics['Rolling_Sortino'] = rolling_sortino
            metrics['Rolling_MaxDrawdown'] = rolling_dd

            return metrics

        except Exception as e:
            self.logger.error(f"计算滚动指标失败: {e}")
            return pd.DataFrame()

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
