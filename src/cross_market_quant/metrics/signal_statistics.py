"""
信号统计模块

计算信号触发率和有效性
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging


class SignalStatistics:
    """信号统计分析"""

    def __init__(self):
        self.logger = logging.getLogger("cross_market_quant.SignalStatistics")

    def calculate(
        self,
        signals: pd.Series,
        returns: Optional[pd.Series] = None,
        window: Optional[int] = None
    ) -> Dict:
        """
        计算信号统计

        Args:
            signals: 信号序列
            returns: 收益序列（可选）
            window: 计算窗口

        Returns:
            信号统计结果
        """
        try:
            self.logger.info("计算信号统计")

            # 过滤有效信号
            valid_signals = signals.dropna()
            non_zero_signals = valid_signals[valid_signals != 0]

            # 基础统计
            total_days = len(signals)
            signal_days = len(non_zero_signals)
            trigger_rate = signal_days / total_days if total_days > 0 else 0

            # 信号分布
            buy_signals = len(non_zero_signals[non_zero_signals == 1])
            sell_signals = len(non_zero_signals[non_zero_signals == -1])
            hold_signals = len(valid_signals[valid_signals == 0])

            # 计算胜率
            win_rate = 0
            avg_return_when_signal = 0
            avg_return_when_buy = 0
            avg_return_when_sell = 0

            if returns is not None and len(returns) > 0:
                # 对齐信号和收益
                aligned_data = pd.DataFrame({
                    'Signal': signals,
                    'Return': returns
                }).dropna()

                if len(aligned_data) > 0:
                    # 整体胜率
                    signal_returns = aligned_data[aligned_data['Signal'] != 0]['Return']
                    win_signals = signal_returns[signal_returns > 0]
                    win_rate = len(win_signals) / len(signal_returns) if len(signal_returns) > 0 else 0

                    # 平均收益
                    avg_return_when_signal = signal_returns.mean()

                    # 买入信号胜率
                    buy_data = aligned_data[aligned_data['Signal'] == 1]
                    if len(buy_data) > 0:
                        avg_return_when_buy = buy_data['Return'].mean()
                        buy_wins = len(buy_data[buy_data['Return'] > 0])
                        buy_win_rate = buy_wins / len(buy_data)

                    # 卖出信号胜率
                    sell_data = aligned_data[aligned_data['Signal'] == -1]
                    if len(sell_data) > 0:
                        avg_return_when_sell = sell_data['Return'].mean()
                        sell_wins = len(sell_data[sell_data['Return'] > 0])
                        sell_win_rate = sell_wins / len(sell_data)

            result = {
                'total_trading_days': total_days,
                'signal_trigger_days': signal_days,
                'trigger_rate': trigger_rate,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'signal_distribution': {
                    'buy_ratio': buy_signals / signal_days if signal_days > 0 else 0,
                    'sell_ratio': sell_signals / signal_days if signal_days > 0 else 0,
                    'hold_ratio': hold_signals / total_days if total_days > 0 else 0
                },
                'performance': {
                    'win_rate': win_rate,
                    'avg_return_when_signal': avg_return_when_signal,
                    'avg_return_when_buy': avg_return_when_buy,
                    'avg_return_when_sell': avg_return_when_sell
                }
            }

            self.logger.info(f"信号统计完成: 触发率 {trigger_rate:.2%}, 胜率 {win_rate:.2%}")
            return result

        except Exception as e:
            self.logger.error(f"计算信号统计失败: {e}")
            return {'error': str(e)}

    def calculate_signal_frequency(
        self,
        signals: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        计算信号频率（滚动窗口）

        Args:
            signals: 信号序列
            window: 滚动窗口

        Returns:
            信号频率序列
        """
        try:
            signal_frequency = signals.rolling(window=window).apply(
                lambda x: len(x[x != 0]) / len(x)
            )

            return signal_frequency

        except Exception as e:
            self.logger.error(f"计算信号频率失败: {e}")
            return pd.Series(index=signals.index, dtype=float)
