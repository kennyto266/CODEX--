"""
集成策略 (T181)
多种策略融合与投票机制
实现策略集成、权重优化和冲突解决

Author: Claude Code
Date: 2025-11-09
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import logging
from collections import Counter
import copy

try:
    from core.base_strategy import IStrategy, Signal, SignalType
    from strategy.traits import StrategyTraits
except ImportError:
    from ..core.base_strategy import IStrategy, Signal, SignalType
    from .traits import StrategyTraits

logger = logging.getLogger(__name__)


class EnsembleStrategy(IStrategy):
    """
    集成策略

    融合多种量化策略，通过投票机制、权重优化和冲突解决
    生成更准确、更稳定的交易信号。

    核心功能：
    1. 多策略融合（技术分析、基本面分析、机器学习等）
    2. 多种投票机制（简单投票、加权投票、概率投票）
    3. 动态权重优化
    4. 策略冲突解决
    5. 性能跟踪和自适应调整

    策略特点：
    - 提高信号准确性和稳定性
    - 降低单一策略失效风险
    - 适应市场环境变化
    - 灵活的策略组合和权重管理
    """

    def __init__(
        self,
        strategies: List[IStrategy] = None,
        voting_method: str = 'weighted',
        min_consensus: float = 0.6,
        confidence_threshold: float = 0.5,
        adaptive_weights: bool = True,
        lookback_window: int = 60
    ):
        """
        初始化集成策略

        Args:
            strategies: 基础策略列表
            voting_method: 投票方法 ('simple', 'weighted', 'probability', 'stacking')
            min_consensus: 最小共识度
            confidence_threshold: 置信度阈值
            adaptive_weights: 是否使用自适应权重
            lookback_window: 权重自适应回看窗口
        """
        self.strategies = strategies or []
        self.voting_method = voting_method
        self.min_consensus = min_consensus
        self.confidence_threshold = confidence_threshold
        self.adaptive_weights = adaptive_weights
        self.lookback_window = lookback_window

        # 权重管理
        self.strategy_weights: Dict[str, float] = {}
        self.performance_history: Dict[str, List[float]] = {}

        # 策略数据缓存
        self.signals_history: Dict[str, List[Signal]] = {}
        self.performance_metrics: Dict[str, float] = {}

        # 初始化权重
        self._initialize_weights()

        # 特征标记
        self.traits = StrategyTraits(
            name="集成策略",
            timeframe="1D",
            多策略融合=True,
            投票机制=True,
            自适应=True
        )

    @property
    def strategy_name(self) -> str:
        return f"Ensemble-{self.voting_method}"

    @property
    def supported_symbols(self) -> List[str]:
        if not self.strategies:
            return []
        return list(set(
            symbol
            for strategy in self.strategies
            for symbol in strategy.supported_symbols
        ))

    def initialize(self, historical_data: pd.DataFrame, **kwargs) -> None:
        """
        初始化集成策略

        Args:
            historical_data: 历史数据
            **kwargs: 额外参数
        """
        try:
            # 初始化所有基础策略
            for strategy in self.strategies:
                if hasattr(strategy, 'initialize'):
                    strategy.initialize(historical_data, **kwargs)

            logger.info(f"集成策略初始化完成: {len(self.strategies)} 个基础策略")

        except Exception as e:
            logger.error(f"策略初始化失败: {e}")
            raise

    def _initialize_weights(self) -> None:
        """初始化策略权重"""
        if not self.strategies:
            return

        # 等权重初始化
        equal_weight = 1.0 / len(self.strategies)
        for strategy in self.strategies:
            strategy_name = strategy.strategy_name
            self.strategy_weights[strategy_name] = equal_weight
            self.performance_history[strategy_name] = []

    def _update_performance_history(self, signal: Signal, actual_return: float) -> None:
        """
        更新策略性能历史

        Args:
            signal: 生成的信号
            actual_return: 实际收益率
        """
        # 简单的收益匹配（实际实现中需要更复杂的逻辑）
        if signal.signal_type == SignalType.BUY:
            score = actual_return
        elif signal.signal_type == SignalType.SELL:
            score = -actual_return
        else:
            score = 0.0

        # 存储到性能历史
        strategy_name = signal.metadata.get('strategy_name', 'unknown')
        if strategy_name in self.performance_history:
            self.performance_history[strategy_name].append(score)
            # 保持历史长度
            if len(self.performance_history[strategy_name]) > self.lookback_window:
                self.performance_history[strategy_name].pop(0)

    def _calculate_strategy_performance(self) -> Dict[str, float]:
        """
        计算各策略的性能指标

        Returns:
            策略性能字典
        """
        performance = {}
        for strategy_name, history in self.performance_history.items():
            if history:
                # 计算累计收益
                cumulative_return = np.sum(history)
                # 计算准确率（假设信号方向与收益正相关）
                correct_signals = sum(1 for h in history if h > 0)
                accuracy = correct_signals / len(history) if history else 0.5

                # 综合评分
                score = 0.6 * cumulative_return + 0.4 * accuracy
                performance[strategy_name] = score
            else:
                performance[strategy_name] = 0.0

        return performance

    def _update_weights(self) -> None:
        """更新策略权重"""
        if not self.adaptive_weights:
            return

        # 计算性能
        performance = self._calculate_strategy_performance()

        # 使用性能来调整权重
        total_performance = sum(max(p, 0) for p in performance.values())

        if total_performance > 0:
            for strategy_name, perf in performance.items():
                if perf > 0:
                    # 基于性能的权重更新
                    base_weight = 1.0 / len(self.strategies)
                    performance_weight = perf / total_performance
                    # 混合原始权重和性能权重
                    self.strategy_weights[strategy_name] = (
                        0.3 * self.strategy_weights[strategy_name] +
                        0.7 * performance_weight
                    )
        else:
            # 如果所有性能都非正，使用等权重
            self._initialize_weights()

    def _simple_voting(
        self,
        signals_by_strategy: Dict[str, List[Signal]]
    ) -> Optional[Signal]:
        """
        简单投票机制

        Args:
            signals_by_strategy: 各策略的信号

        Returns:
            投票结果信号
        """
        # 收集所有信号
        all_signals = []
        for strategy_signals in signals_by_strategy.values():
            all_signals.extend(strategy_signals)

        if not all_signals:
            return None

        # 统计信号类型
        signal_types = [s.signal_type for s in all_signals]
        type_counts = Counter(signal_types)

        # 找出得票最多的信号类型
        most_common_type = type_counts.most_common(1)[0][0]
        votes = type_counts[most_common_type]
        total_votes = len(all_signals)
        consensus = votes / total_votes

        # 检查共识度
        if consensus < self.min_consensus:
            return None

        # 选择置信度最高的信号
        best_signal = max(
            [s for s in all_signals if s.signal_type == most_common_type],
            key=lambda x: x.confidence
        )

        # 创建集成信号
        ensemble_signal = Signal(
            symbol=best_signal.symbol,
            timestamp=best_signal.timestamp,
            signal_type=most_common_type,
            confidence=consensus * 0.7 + best_signal.confidence * 0.3,
            reason=f"简单投票 - 共识度: {consensus:.2f}, 策略数: {len(signals_by_strategy)}",
            price=best_signal.price,
            metadata={
                'voting_method': 'simple',
                'consensus': consensus,
                'votes': votes,
                'total_votes': total_votes,
                'strategy_contributions': {
                    strategy: [s.signal_type for s in signals]
                    for strategy, signals in signals_by_strategy.items()
                }
            }
        )

        return ensemble_signal

    def _weighted_voting(
        self,
        signals_by_strategy: Dict[str, List[Signal]]
    ) -> Optional[Signal]:
        """
        加权投票机制

        Args:
            signals_by_strategy: 各策略的信号

        Returns:
            投票结果信号
        """
        # 计算加权得分
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0

        for strategy_name, strategy_signals in signals_by_strategy.items():
            weight = self.strategy_weights.get(strategy_name, 0.0)
            total_weight += weight

            for signal in strategy_signals:
                if signal.signal_type == SignalType.BUY:
                    buy_score += weight * signal.confidence
                elif signal.signal_type == SignalType.SELL:
                    sell_score += weight * signal.confidence

        if total_weight == 0:
            return None

        # 归一化
        buy_score /= total_weight
        sell_score /= total_weight

        # 确定获胜方向
        if buy_score > sell_score and buy_score > self.confidence_threshold:
            winner_type = SignalType.BUY
            winner_score = buy_score
        elif sell_score > buy_score and sell_score > self.confidence_threshold:
            winner_type = SignalType.SELL
            winner_score = sell_score
        else:
            return None

        # 计算共识度
        total_score = buy_score + sell_score
        consensus = winner_score / total_score if total_score > 0 else 0

        if consensus < self.min_consensus:
            return None

        # 获取最佳信号作为参考
        best_signals = []
        for strategy_signals in signals_by_strategy.values():
            best_signals.extend(strategy_signals)

        best_signal = max(best_signals, key=lambda x: x.confidence)

        # 创建集成信号
        ensemble_signal = Signal(
            symbol=best_signal.symbol,
            timestamp=best_signal.timestamp,
            signal_type=winner_type,
            confidence=consensus,
            reason=f"加权投票 - 共识度: {consensus:.2f}, 权重和: {total_weight:.2f}",
            price=best_signal.price,
            metadata={
                'voting_method': 'weighted',
                'consensus': consensus,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'strategy_weights': self.strategy_weights,
                'winner_score': winner_score
            }
        )

        return ensemble_signal

    def _probability_voting(
        self,
        signals_by_strategy: Dict[str, List[Signal]]
    ) -> Optional[Signal]:
        """
        概率投票机制

        Args:
            signals_by_strategy: 各策略的信号

        Returns:
            投票结果信号
        """
        # 使用贝叶斯概率模型
        prior_prob = 0.5  # 先验概率

        # 计算似然
        buy_likelihood = 0.0
        sell_likelihood = 0.0
        total_likelihood = 0.0

        for strategy_name, strategy_signals in signals_by_strategy.items():
            weight = self.strategy_weights.get(strategy_name, 0.0)
            total_likelihood += weight

            for signal in strategy_signals:
                if signal.signal_type == SignalType.BUY:
                    # 使用置信度作为似然
                    buy_likelihood += weight * (0.5 + signal.confidence / 2)
                elif signal.signal_type == SignalType.SELL:
                    sell_likelihood += weight * (0.5 + signal.confidence / 2)

        if total_likelihood == 0:
            return None

        # 归一化
        buy_likelihood /= total_likelihood
        sell_likelihood /= total_likelihood

        # 计算后验概率
        buy_posterior = (buy_likelihood * prior_prob) / (
            buy_likelihood * prior_prob + sell_likelihood * (1 - prior_prob)
        )
        sell_posterior = (sell_likelihood * (1 - prior_prob)) / (
            buy_likelihood * prior_prob + sell_likelihood * (1 - prior_prob)
        )

        # 确定获胜方向
        if buy_posterior > sell_posterior and buy_posterior > self.confidence_threshold:
            winner_type = SignalType.BUY
            winner_posterior = buy_posterior
        elif sell_posterior > buy_posterior and sell_posterior > self.confidence_threshold:
            winner_type = SignalType.SELL
            winner_posterior = sell_posterior
        else:
            return None

        # 计算共识度
        consensus = max(buy_posterior, sell_posterior)

        if consensus < self.min_consensus:
            return None

        # 获取最佳信号作为参考
        best_signals = []
        for strategy_signals in signals_by_strategy.values():
            best_signals.extend(strategy_signals)

        best_signal = max(best_signals, key=lambda x: x.confidence)

        # 创建集成信号
        ensemble_signal = Signal(
            symbol=best_signal.symbol,
            timestamp=best_signal.timestamp,
            signal_type=winner_type,
            confidence=consensus,
            reason=f"概率投票 - 后验概率: {winner_posterior:.2f}",
            price=best_signal.price,
            metadata={
                'voting_method': 'probability',
                'consensus': consensus,
                'buy_posterior': buy_posterior,
                'sell_posterior': sell_posterior,
                'buy_likelihood': buy_likelihood,
                'sell_likelihood': sell_likelihood
            }
        )

        return ensemble_signal

    def _stacking_voting(
        self,
        signals_by_strategy: Dict[str, List[Signal]]
    ) -> Optional[Signal]:
        """
        Stacking投票机制（元学习）

        Args:
            signals_by_strategy: 各策略的信号

        Returns:
            投票结果信号
        """
        # 简化的Stacking实现
        # 在实际应用中，这里会使用更复杂的元学习模型

        features = []
        labels = []

        # 构建特征矩阵
        for strategy_name, strategy_signals in signals_by_strategy.items():
            weight = self.strategy_weights.get(strategy_name, 0.0)
            for signal in strategy_signals:
                features.append([
                    weight,
                    signal.confidence,
                    1 if signal.signal_type == SignalType.BUY else -1,
                    len(signal.reason) / 100.0  # 归一化原因长度
                ])
                # 标签（实际实现中需要真实标签）
                labels.append(1 if signal.signal_type == SignalType.BUY else -1)

        if not features or len(features) < 10:
            # 数据不足，使用加权投票
            return self._weighted_voting(signals_by_strategy)

        features = np.array(features)
        labels = np.array(labels)

        # 简单线性组合（模拟元学习器）
        try:
            # 标准化特征
            features_norm = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)

            # 简单的线性模型
            weights = np.mean(features_norm, axis=0)
            bias = 0.0

            # 计算最终得分
            buy_score = 0.0
            sell_score = 0.0
            total_confidence = 0.0

            for strategy_name, strategy_signals in signals_by_strategy.items():
                for signal in strategy_signals:
                    # 简单特征
                    feature = np.array([
                        self.strategy_weights.get(strategy_name, 0.0),
                        signal.confidence,
                        1 if signal.signal_type == SignalType.BUY else -1,
                        len(signal.reason) / 100.0
                    ])

                    feature_norm = (feature - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
                    prediction = np.dot(weights, feature_norm) + bias

                    if prediction > 0:
                        buy_score += signal.confidence * abs(prediction)
                    else:
                        sell_score += signal.confidence * abs(prediction)

                    total_confidence += signal.confidence

            if total_confidence == 0:
                return None

            # 归一化
            buy_score /= total_confidence
            sell_score /= total_confidence

            # 确定获胜方向
            if buy_score > sell_score and buy_score > self.confidence_threshold:
                winner_type = SignalType.BUY
                winner_score = buy_score
            elif sell_score > buy_score and sell_score > self.confidence_threshold:
                winner_type = SignalType.SELL
                winner_score = sell_score
            else:
                return None

            # 计算共识度
            total_score = buy_score + sell_score
            consensus = winner_score / total_score if total_score > 0 else 0

            if consensus < self.min_consensus:
                return None

            # 获取最佳信号作为参考
            best_signals = []
            for strategy_signals in signals_by_strategy.values():
                best_signals.extend(strategy_signals)

            best_signal = max(best_signals, key=lambda x: x.confidence)

            # 创建集成信号
            ensemble_signal = Signal(
                symbol=best_signal.symbol,
                timestamp=best_signal.timestamp,
                signal_type=winner_type,
                confidence=consensus,
                reason=f"Stacking投票 - 模型得分: {winner_score:.2f}",
                price=best_signal.price,
                metadata={
                    'voting_method': 'stacking',
                    'consensus': consensus,
                    'model_weights': weights.tolist(),
                    'buy_score': buy_score,
                    'sell_score': sell_score
                }
            )

            return ensemble_signal

        except Exception as e:
            logger.error(f"Stacking投票失败: {e}")
            # 回退到加权投票
            return self._weighted_voting(signals_by_strategy)

    def generate_signals(self, current_data: pd.DataFrame) -> List[Signal]:
        """
        生成集成信号

        Args:
            current_data: 当前市场数据

        Returns:
            集成信号列表
        """
        signals = []

        try:
            if not self.strategies:
                logger.warning("没有配置基础策略")
                return signals

            # 收集各策略的信号
            signals_by_strategy = {}

            for strategy in self.strategies:
                try:
                    strategy_signals = strategy.generate_signals(current_data.copy())
                    signals_by_strategy[strategy.strategy_name] = strategy_signals

                    # 为信号添加策略名称
                    for signal in strategy_signals:
                        if 'metadata' not in signal.metadata:
                            signal.metadata = {}
                        signal.metadata['strategy_name'] = strategy.strategy_name

                except Exception as e:
                    logger.error(f"策略 {strategy.strategy_name} 信号生成失败: {e}")
                    continue

            # 执行投票
            if self.voting_method == 'simple':
                ensemble_signal = self._simple_voting(signals_by_strategy)
            elif self.voting_method == 'weighted':
                ensemble_signal = self._weighted_voting(signals_by_strategy)
            elif self.voting_method == 'probability':
                ensemble_signal = self._probability_voting(signals_by_strategy)
            elif self.voting_method == 'stacking':
                ensemble_signal = self._stacking_voting(signals_by_strategy)
            else:
                logger.warning(f"未知的投票方法: {self.voting_method}")
                ensemble_signal = self._weighted_voting(signals_by_strategy)

            if ensemble_signal:
                signals.append(ensemble_signal)

            # 更新权重（如果启用自适应）
            if self.adaptive_weights and ensemble_signal:
                self._update_weights()

        except Exception as e:
            logger.error(f"集成信号生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return signals

    def add_strategy(self, strategy: IStrategy) -> None:
        """
        添加基础策略

        Args:
            strategy: 要添加的策略
        """
        self.strategies.append(strategy)
        strategy_name = strategy.strategy_name
        self.strategy_weights[strategy_name] = 1.0 / len(self.strategies)
        self.performance_history[strategy_name] = []

    def remove_strategy(self, strategy_name: str) -> None:
        """
        移除基础策略

        Args:
            strategy_name: 策略名称
        """
        self.strategies = [s for s in self.strategies if s.strategy_name != strategy_name]
        if strategy_name in self.strategy_weights:
            del self.strategy_weights[strategy_name]
        if strategy_name in self.performance_history:
            del self.performance_history[strategy_name]

        # 重新归一化权重
        if self.strategies:
            equal_weight = 1.0 / len(self.strategies)
            for name in self.strategy_weights:
                self.strategy_weights[name] = equal_weight

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            'strategies': [s.strategy_name for s in self.strategies],
            'voting_method': self.voting_method,
            'min_consensus': self.min_consensus,
            'confidence_threshold': self.confidence_threshold,
            'adaptive_weights': self.adaptive_weights,
            'lookback_window': self.lookback_window,
            'strategy_weights': self.strategy_weights
        }

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数"""
        if 'voting_method' in parameters:
            self.voting_method = parameters['voting_method']
        if 'min_consensus' in parameters:
            self.min_consensus = parameters['min_consensus']
        if 'confidence_threshold' in parameters:
            self.confidence_threshold = parameters['confidence_threshold']
        if 'adaptive_weights' in parameters:
            self.adaptive_weights = parameters['adaptive_weights']
        if 'lookback_window' in parameters:
            self.lookback_window = parameters['lookback_window']
        if 'strategy_weights' in parameters:
            self.strategy_weights = parameters['strategy_weights']

    def get_ensemble_summary(self) -> Dict[str, Any]:
        """
        获取集成策略摘要

        Returns:
            包含集成状态信息的字典
        """
        performance = self._calculate_strategy_performance()

        summary = {
            'strategy_name': self.strategy_name,
            'base_strategies': [s.strategy_name for s in self.strategies],
            'voting_method': self.voting_method,
            'strategy_weights': self.strategy_weights,
            'performance_metrics': performance,
            'adaptive_weights': self.adaptive_weights,
            'min_consensus': self.min_consensus,
            'confidence_threshold': self.confidence_threshold
        }

        # 添加各策略详细信息
        for strategy in self.strategies:
            strategy_name = strategy.strategy_name
            summary[f'strategy_{strategy_name}'] = {
                'parameters': strategy.get_parameters(),
                'weight': self.strategy_weights.get(strategy_name, 0.0),
                'performance': performance.get(strategy_name, 0.0),
                'history_length': len(self.performance_history.get(strategy_name, []))
            }

        return summary


# 导出策略类
__all__ = ['EnsembleStrategy']
