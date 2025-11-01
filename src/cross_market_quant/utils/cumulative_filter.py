"""
累积回报过滤器 - 阿程策略12的核心组件

基于累积回报率过滤交易信号，减少噪音交易
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging

from .volatility_calculator import VolatilityCalculator


class CumulativeReturnFilter:
    """
    累积回报过滤器

    核心逻辑：
    1. 计算多天累积回报率（默认4天窗口）
    2. 当累积回报超过阈值时触发信号
    3. 支持动态阈值调整（基于波动率）

    示例：
        输入：[6.78, 6.79, 6.80, 6.81, 6.82]
        输出：[NaN, NaN, NaN, 0.0044, 0.0044]  (4天累积回报0.44%)
    """

    def __init__(
        self,
        window: int = 4,
        threshold: float = 0.004,  # ±0.4%阈值
        enable_dynamic_threshold: bool = True
    ):
        """
        初始化累积回报过滤器

        Args:
            window: 累积回报计算窗口（天数）
            threshold: 基础阈值（±0.4%）
            enable_dynamic_threshold: 是否启用动态阈值
        """
        self.window = window
        self.threshold = threshold
        self.enable_dynamic_threshold = enable_dynamic_threshold
        self.volatility_calculator = VolatilityCalculator()
        self.logger = logging.getLogger("cross_market_quant.CumulativeFilter")

    def calculate_cumulative_returns(self, prices: pd.Series) -> pd.Series:
        """
        计算累积回报率

        Args:
            prices: 价格序列

        Returns:
            累积回报率序列
        """
        try:
            if len(prices) < self.window:
                self.logger.warning(f"数据长度不足{self.window}天")
                return pd.Series([np.nan] * len(prices), index=prices.index)

            cumulative_returns = pd.Series(index=prices.index, dtype=float)

            for i in range(self.window - 1, len(prices)):
                start_price = prices.iloc[i - self.window + 1]
                end_price = prices.iloc[i]

                if start_price > 0:
                    cum_return = (end_price - start_price) / start_price
                    cumulative_returns.iloc[i] = cum_return
                else:
                    cumulative_returns.iloc[i] = np.nan

            self.logger.info(f"计算{len(cumulative_returns)}个累积回报率")
            return cumulative_returns

        except Exception as e:
            self.logger.error(f"计算累积回报率失败: {e}")
            return pd.Series([np.nan] * len(prices), index=prices.index)

    def filter_signals(
        self,
        cumulative_returns: pd.Series,
        price_data: pd.Series,
        signal_type: str = 'auto',
        volatility_window: int = 20,
        volatility_adjustment: float = 1.5
    ) -> pd.Series:
        """
        基于累积回报率过滤交易信号

        Args:
            cumulative_returns: 累积回报率序列
            price_data: 原始价格数据
            signal_type: 信号类型 ('long', 'short', 'auto')
            volatility_window: 波动率计算窗口
            volatility_adjustment: 波动率调整系数

        Returns:
            交易信号序列 (1=买入, -1=卖出, 0=持有, NaN=无效)
        """
        try:
            signals = pd.Series(index=cumulative_returns.index, dtype=float)

            if signal_type == 'auto':
                signals = self._generate_auto_signals(
                    cumulative_returns, price_data, volatility_window, volatility_adjustment
                )
            elif signal_type == 'long':
                signals = self._generate_long_signals(
                    cumulative_returns, price_data, volatility_window, volatility_adjustment
                )
            elif signal_type == 'short':
                signals = self._generate_short_signals(
                    cumulative_returns, price_data, volatility_window, volatility_adjustment
                )
            else:
                raise ValueError(f"不支持的信号类型: {signal_type}")

            # 统计信号数量
            signal_counts = signals.value_counts()
            self.logger.info(f"信号统计: {signal_counts.to_dict()}")

            return signals

        except Exception as e:
            self.logger.error(f"过滤信号失败: {e}")
            return pd.Series(index=cumulative_returns.index, dtype=float)

    def _generate_auto_signals(
        self,
        cumulative_returns: pd.Series,
        price_data: pd.Series,
        volatility_window: int,
        volatility_adjustment: float
    ) -> pd.Series:
        """
        生成自动信号（适用于跨市场策略）
        当累积回报超过阈值时：
        - 正回报：卖出信号（适用于USD/CNH上涨预测HSI下跌）
        - 负回报：买入信号
        """
        signals = pd.Series(index=cumulative_returns.index, dtype=float)

        for i in range(len(cumulative_returns)):
            if pd.isna(cumulative_returns.iloc[i]):
                signals.iloc[i] = 0
                continue

            cum_return = cumulative_returns.iloc[i]

            # 获取动态阈值
            effective_threshold = self._get_effective_threshold(
                price_data, i, volatility_window, volatility_adjustment
            )

            if cum_return >= effective_threshold:
                # 正累积回报超过阈值 → 卖出信号
                signals.iloc[i] = -1
            elif cum_return <= -effective_threshold:
                # 负累积回报超过阈值 → 买入信号
                signals.iloc[i] = 1
            else:
                # 回报在阈值内 → 持有
                signals.iloc[i] = 0

        return signals

    def _generate_long_signals(
        self,
        cumulative_returns: pd.Series,
        price_data: pd.Series,
        volatility_window: int,
        volatility_adjustment: float
    ) -> pd.Series:
        """
        生成多头信号
        负累积回报触发买入
        """
        signals = pd.Series(index=cumulative_returns.index, dtype=float)

        for i in range(len(cumulative_returns)):
            if pd.isna(cumulative_returns.iloc[i]):
                signals.iloc[i] = 0
                continue

            cum_return = cumulative_returns.iloc[i]
            effective_threshold = self._get_effective_threshold(
                price_data, i, volatility_window, volatility_adjustment
            )

            if cum_return <= -effective_threshold:
                signals.iloc[i] = 1
            else:
                signals.iloc[i] = 0

        return signals

    def _generate_short_signals(
        self,
        cumulative_returns: pd.Series,
        price_data: pd.Series,
        volatility_window: int,
        volatility_adjustment: float
    ) -> pd.Series:
        """
        生成空头信号
        正累积回报触发卖出
        """
        signals = pd.Series(index=cumulative_returns.index, dtype=float)

        for i in range(len(cumulative_returns)):
            if pd.isna(cumulative_returns.iloc[i]):
                signals.iloc[i] = 0
                continue

            cum_return = cumulative_returns.iloc[i]
            effective_threshold = self._get_effective_threshold(
                price_data, i, volatility_window, volatility_adjustment
            )

            if cum_return >= effective_threshold:
                signals.iloc[i] = -1
            else:
                signals.iloc[i] = 0

        return signals

    def _get_effective_threshold(
        self,
        price_data: pd.Series,
        index: int,
        volatility_window: int,
        volatility_adjustment: float
    ) -> float:
        """
        计算有效阈值（考虑波动率调整）

        Args:
            price_data: 价格数据
            index: 当前索引
            volatility_window: 波动率窗口
            volatility_adjustment: 调整系数

        Returns:
            有效阈值
        """
        if not self.enable_dynamic_threshold:
            return self.threshold

        # 计算历史波动率
        if index < volatility_window:
            return self.threshold

        start_idx = max(0, index - volatility_window)
        price_window = price_data.iloc[start_idx:index + 1]

        volatility = self.volatility_calculator.calculate_volatility(price_window)

        # 动态调整阈值
        adjustment_factor = 1 + volatility * volatility_adjustment
        effective_threshold = self.threshold * adjustment_factor

        return effective_threshold

    def analyze_signals(self, signals: pd.Series, cumulative_returns: pd.Series) -> Dict:
        """
        分析信号效果

        Args:
            signals: 信号序列
            cumulative_returns: 累积回报序列

        Returns:
            信号分析结果
        """
        try:
            # 有效信号（非零）
            valid_signals = signals[signals != 0]
            valid_returns = cumulative_returns[signals != 0]

            if len(valid_signals) == 0:
                return {'error': '没有有效信号'}

            # 计算信号统计
            buy_signals = len(signals[signals == 1])
            sell_signals = len(signals[signals == -1])
            hold_signals = len(signals[signals == 0])

            # 计算信号效果
            total_signals = len(valid_signals)
            win_rate = 0
            avg_return_when_signal = 0

            if len(valid_returns) > 0:
                avg_return_when_signal = valid_returns.mean()

                # 假设信号方向与回报正相关
                win_signals = valid_signals[valid_signals == 1]
                if len(win_signals) > 0:
                    win_returns = valid_returns[valid_signals == 1]
                    # 简化计算：假设正回报为胜利
                    win_rate = len(win_returns[win_returns > 0]) / len(win_returns)

            analysis = {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'signal_rate': total_signals / len(signals) if len(signals) > 0 else 0,
                'win_rate': win_rate,
                'avg_return_when_signal': avg_return_when_signal,
                'threshold_used': self.threshold,
                'window_used': self.window,
                'dynamic_threshold_enabled': self.enable_dynamic_threshold
            }

            self.logger.info(f"信号分析完成: {analysis}")
            return analysis

        except Exception as e:
            self.logger.error(f"分析信号失败: {e}")
            return {'error': str(e)}

    def visualize_cumulative_returns(
        self,
        prices: pd.Series,
        signals: pd.Series,
        cumulative_returns: pd.Series
    ) -> pd.DataFrame:
        """
        可视化累积回报和信号（返回DataFrame供前端使用）

        Args:
            prices: 价格序列
            signals: 信号序列
            cumulative_returns: 累积回报序列

        Returns:
            可视化数据
        """
        try:
            viz_data = pd.DataFrame({
                'Date': prices.index,
                'Price': prices.values,
                'Cumulative_Return': cumulative_returns.values,
                'Signal': signals.values
            })

            # 添加标记列
            viz_data['Buy_Signal'] = viz_data['Signal'] == 1
            viz_data['Sell_Signal'] = viz_data['Signal'] == -1
            viz_data['Above_Threshold'] = viz_data['Cumulative_Return'] >= self.threshold
            viz_data['Below_Threshold'] = viz_data['Cumulative_Return'] <= -self.threshold

            return viz_data

        except Exception as e:
            self.logger.error(f"生成可视化数据失败: {e}")
            return pd.DataFrame()
