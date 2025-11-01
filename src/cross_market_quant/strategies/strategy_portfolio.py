"""
策略组合 - 组合多个跨市场策略

通过动态权重组合多个策略信号，提高整体预测准确性
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging


class StrategyPortfolio:
    """多策略组合管理器"""

    def __init__(self, strategies: List, weights: Optional[List[float]] = None):
        """
        初始化策略组合

        Args:
            strategies: 策略列表
            weights: 权重列表（默认均等权重）
        """
        self.strategies = strategies
        self.n_strategies = len(strategies)

        # 设置权重
        if weights is None:
            self.weights = [1.0 / self.n_strategies] * self.n_strategies
        else:
            if len(weights) != self.n_strategies:
                raise ValueError("权重数量必须等于策略数量")
            self.weights = np.array(weights) / np.sum(weights)  # 归一化

        self.logger = logging.getLogger("cross_market_quant.StrategyPortfolio")

    async def combine_signals(
        self,
        start_date: str,
        end_date: str,
        method: str = 'weighted_vote'
    ) -> pd.DataFrame:
        """
        组合多个策略的信号

        Args:
            start_date: 开始日期
            end_date: 结束日期
            method: 组合方法 ('weighted_vote', 'majority_vote', 'best_signal')

        Returns:
            组合信号结果
        """
        try:
            self.logger.info(f"组合{self.n_strategies}个策略的信号")

            # 获取所有策略的信号
            all_signals = []
            strategy_names = []

            for i, strategy in enumerate(self.strategies):
                try:
                    signals_data = await strategy.generate_signals(start_date, end_date)
                    if not signals_data.empty:
                        all_signals.append(signals_data['Signal'])
                        strategy_names.append(strategy.__class__.__name__)
                except Exception as e:
                    self.logger.warning(f"获取策略{i}信号失败: {e}")
                    continue

            if not all_signals:
                raise Exception("未能获取任何策略信号")

            # 合并所有信号
            combined_signals = pd.concat(all_signals, axis=1, keys=strategy_names)

            # 应用组合方法
            if method == 'weighted_vote':
                final_signal = self._weighted_vote(combined_signals)
            elif method == 'majority_vote':
                final_signal = self._majority_vote(combined_signals)
            elif method == 'best_signal':
                final_signal = self._best_signal(combined_signals)
            else:
                raise ValueError(f"不支持的组合方法: {method}")

            # 计算信号强度
            signal_strength = self._calculate_signal_strength(combined_signals)

            # 构建结果
            result = pd.DataFrame({
                'Date': combined_signals.index,
                'Combined_Signal': final_signal,
                'Signal_Strength': signal_strength,
                'Vote_Buy': (final_signal > 0).astype(int),
                'Vote_Sell': (final_signal < 0).astype(int),
                'Vote_Hold': (final_signal == 0).astype(int)
            })

            # 添加各策略信号详情
            for name in strategy_names:
                result[f'Signal_{name}'] = combined_signals[name]

            self.logger.info(f"组合完成: {len(result)}条信号")
            return result

        except Exception as e:
            self.logger.error(f"组合信号失败: {e}")
            return pd.DataFrame()

    def _weighted_vote(self, signals: pd.DataFrame) -> pd.Series:
        """加权投票"""
        vote_result = pd.Series(index=signals.index, dtype=float)

        for i in range(len(signals)):
            weighted_sum = 0
            total_weight = 0

            for j, col in enumerate(signals.columns):
                signal = signals.iloc[i, j]
                if not pd.isna(signal):
                    weighted_sum += signal * self.weights[j]
                    total_weight += self.weights[j]

            if total_weight > 0:
                vote_result.iloc[i] = weighted_sum / total_weight
            else:
                vote_result.iloc[i] = 0

        return vote_result

    def _majority_vote(self, signals: pd.DataFrame) -> pd.Series:
        """多数投票"""
        vote_result = pd.Series(index=signals.index, dtype=float)

        for i in range(len(signals)):
            buy_votes = 0
            sell_votes = 0
            hold_votes = 0

            for col in signals.columns:
                signal = signals.iloc[i, col]
                if signal > 0:
                    buy_votes += 1
                elif signal < 0:
                    sell_votes += 1
                else:
                    hold_votes += 1

            # 选择得票最多的信号
            if buy_votes > sell_votes and buy_votes > hold_votes:
                vote_result.iloc[i] = 1
            elif sell_votes > buy_votes and sell_votes > hold_votes:
                vote_result.iloc[i] = -1
            else:
                vote_result.iloc[i] = 0

        return vote_result

    def _best_signal(self, signals: pd.DataFrame) -> pd.Series:
        """选择最佳信号（简化版：选择绝对值最大的信号）"""
        return signals.mean(axis=1)  # 简化实现

    def _calculate_signal_strength(self, signals: pd.DataFrame) -> pd.Series:
        """计算信号强度（0-1之间）"""
        # 计算每个时间点的信号一致性
        consistency = pd.Series(index=signals.index, dtype=float)

        for i in range(len(signals)):
            # 获取该时间点的所有信号
            row_signals = signals.iloc[i].dropna()

            if len(row_signals) == 0:
                consistency.iloc[i] = 0
                continue

            # 计算信号的标准差（越小表示一致性越高）
            signal_std = row_signals.std()
            max_possible_std = 2  # 信号范围是[-1, 1]，最大标准差约为2

            # 转换为强度（1 - 标准化标准差）
            strength = 1 - (signal_std / max_possible_std)
            consistency.iloc[i] = max(0, strength)

        return consistency
