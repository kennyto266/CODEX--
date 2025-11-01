"""
收益归因模块

进行Brinson归因分析，计算allocation effect、selection effect和interaction effect
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging


class ReturnAttribution:
    """收益归因分析"""

    def __init__(self):
        self.logger = logging.getLogger("cross_market_quant.ReturnAttribution")

    def brinson_analysis(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        portfolio_weights: Optional[pd.Series] = None,
        benchmark_weights: Optional[pd.Series] = None
    ) -> Dict:
        """
        进行Brinson归因分析

        Args:
            portfolio_returns: 组合收益序列
            benchmark_returns: 基准收益序列
            portfolio_weights: 组合权重（简化实现中使用均等权重）
            benchmark_weights: 基准权重（简化实现中使用均等权重）

        Returns:
            归因分析结果
        """
        try:
            self.logger.info("进行Brinson归因分析")

            # 简化实现：假设只有一个资产
            # 实际应用中需要多个资产和权重

            total_portfolio_return = portfolio_returns.mean()
            total_benchmark_return = benchmark_returns.mean()

            # 计算allocation effect（权重效应）
            # 简化：假设权重相同，allocation effect = 0
            allocation_effect = 0.0

            # 计算selection effect（选择效应）
            # 简化：收益差异
            selection_effect = total_portfolio_return - total_benchmark_return

            # 计算interaction effect（交互效应）
            # 简化：假设interaction effect = 0
            interaction_effect = 0.0

            result = {
                'total_portfolio_return': total_portfolio_return,
                'total_benchmark_return': total_benchmark_return,
                'excess_return': total_portfolio_return - total_benchmark_return,
                'allocation_effect': allocation_effect,
                'selection_effect': selection_effect,
                'interaction_effect': interaction_effect,
                'attribution_summary': {
                    'allocation_contribution': allocation_effect / (selection_effect + 1e-10) * 100,
                    'selection_contribution': selection_effect / (selection_effect + 1e-10) * 100,
                    'interaction_contribution': interaction_effect / (selection_effect + 1e-10) * 100
                }
            }

            self.logger.info(f"归因分析完成: 超额收益 {result['excess_return']:.2%}")
            return result

        except Exception as e:
            self.logger.error(f"归因分析失败: {e}")
            return {'error': str(e)}

    def factor_attribution(
        self,
        returns: pd.Series,
        factors: pd.DataFrame
    ) -> Dict:
        """
        因子归因分析

        Args:
            returns: 收益序列
            factors: 因子数据框

        Returns:
            因子归因结果
        """
        try:
            # 简化实现：计算因子与收益的相关性
            correlations = returns.corr(factors)

            result = {
                'factor_correlations': correlations.to_dict(),
                'factor_exposure': correlations.abs().to_dict(),
                'dominant_factor': correlations.abs().idxmax() if len(correlations) > 0 else None
            }

            return result

        except Exception as e:
            self.logger.error(f"因子归因失败: {e}")
            return {'error': str(e)}
