"""
T177: VROC (Volume Rate of Change) 技术指标

成交量变化率指标，测量成交量变化的速度。

## 计算公式
VROC = (V - Vn) / Vn * 100
其中：
- V = 当前成交量
- Vn = n期前的成交量

## 用途
- 确认价格趋势的强度
- 检测成交量背离
- 识别突破时机
- 量价配合分析

## 交易信号
- VROC > 0：成交量增加
- VROC < 0：成交量减少
- VROC大幅上升：可能的突破
- 价涨量增：确认上涨趋势
- 价跌量增：确认下跌趋势
- 价涨量缩：可能见顶
- 价跌量缩：可能见底

## 参数
- period: 计算周期，默认12或14
- threshold: 显著变化阈值，默认50
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VROCIndicator:
    """
    VROC (Volume Rate of Change) 指标计算器

    提供成交量变化率分析，包括量价配合和背离检测。
    """

    def __init__(self, period: int = 12, threshold: float = 50):
        """
        初始化VROC指标

        Args:
            period: 计算周期，默认12
            threshold: 显著变化阈值，默认50
        """
        self.period = period
        self.threshold = threshold

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算VROC的所有组件

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含所有VROC指标的DataFrame
        """
        if data is None or data.empty:
            logger.error("输入数据为空")
            return pd.DataFrame()

        df = data.copy()

        try:
            # 1. 计算VROC
            df['VROC'] = self._calculate_vroc(df)

            # 2. 计算VROC的移动平均（信号线）
            df['VROC_Signal'] = df['VROC'].rolling(window=9).mean()

            # 3. 计算VROC的EMA
            df['VROC_EMA'] = df['VROC'].ewm(span=self.period, adjust=False).mean()

            # 4. 计算成交量移动平均
            df['Volume_MA'] = df['Volume'].rolling(window=self.period).mean()
            df['Volume_MA_Fast'] = df['Volume'].rolling(window=5).mean()
            df['Volume_MA_Slow'] = df['Volume'].rolling(window=20).mean()

            # 5. 计算成交量变化率
            df['Volume_Change'] = df['Volume'].pct_change() * 100

            # 6. 计算量价背离
            df['VROC_Price_Divergence'] = self._calculate_price_volume_divergence(df)

            # 7. 计算突破信号
            df['VROC_Breakout'] = self._calculate_breakout_signals(df)

            # 8. 计算量价配合度
            df['VROC_Price_Alignment'] = self._calculate_price_volume_alignment(df)

            # 9. 计算交易信号
            df['VROC_Signal_Trade'] = self._calculate_trading_signals(df)

            # 10. 计算信号强度
            df['VROC_Strength'] = self._calculate_signal_strength(df)

            # 11. 计算成交量状态
            df['VROC_Volume_State'] = self._calculate_volume_state(df)

            logger.info("VROC计算完成")

        except Exception as e:
            logger.error(f"VROC计算错误: {e}")

        return df

    def _calculate_vroc(self, df: pd.DataFrame) -> pd.Series:
        """
        计算VROC值

        Args:
            df: 包含成交量数据的DataFrame

        Returns:
            VROC序列
        """
        try:
            # 当前成交量与n期前成交量的比较
            current_volume = df['Volume']
            past_volume = df['Volume'].shift(self.period)

            # 避免除以零
            vroc = ((current_volume - past_volume) / (past_volume + 1)) * 100

            return vroc
        except:
            return pd.Series(0, index=df.index)

    def _calculate_price_volume_divergence(self, df: pd.DataFrame, lookback: int = 50) -> pd.Series:
        """
        计算价量背离信号

        Args:
            df: 包含VROC和价格数据的DataFrame
            lookback: 查找背离的回望周期

        Returns:
            背离信号序列 (1=看涨背离, -1=看跌背离, 0=无背离)
        """
        try:
            signal = np.zeros(len(df))

            for i in range(lookback, len(df)):
                # 获取价格窗口
                price_window = df['Close'].iloc[i-lookback:i+1]
                vroc_window = df['VROC'].iloc[i-lookback:i+1]

                # 去除NaN值
                price_window = price_window.dropna()
                vroc_window = vroc_window.dropna()

                if len(price_window) < 10 or len(vroc_window) < 10:
                    continue

                # 寻找价格和VROC的窗口极值
                price_peak_idx = price_window.idxmax()
                price_trough_idx = price_window.idxmin()
                vroc_peak_idx = vroc_window.idxmax()
                vroc_trough_idx = vroc_window.idxmin()

                # 看涨背离：价格创新低但VROC没有创新低
                if (price_trough_idx == price_window.index[-1] and
                    vroc_trough_idx != vroc_window.index[-1]):

                    # 检查VROC是否在某个阈值之上
                    if vroc_window.iloc[-1] > vroc_window.quantile(0.3):
                        signal[i] = 1

                # 看跌背离：价格创新高但VROC没有创新高
                elif (price_peak_idx == price_window.index[-1] and
                      vroc_peak_idx != vroc_window.index[-1]):

                    # 检查VROC是否在某个阈值之下
                    if vroc_window.iloc[-1] < vroc_window.quantile(0.7):
                        signal[i] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_breakout_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算突破信号

        Args:
            df: 包含VROC数据的DataFrame

        Returns:
            突破信号序列 (1=强突破, 0.5=一般突破, -1=弱突破, 0=无突破)
        """
        try:
            signal = np.zeros(len(df))

            # 计算VROC的变化率
            vroc_change = df['VROC'].diff()

            # 强突破：VROC > 阈值且快速上升
            strong_breakout = (df['VROC'] > self.threshold) & (vroc_change > 10)
            signal[strong_breakout] = 1

            # 一般突破：VROC > 0
            normal_breakout = (df['VROC'] > 0) & (vroc_change > 0) & ~strong_breakout
            signal[normal_breakout] = 0.5

            # 弱突破：VROC < -阈值且快速下降
            weak_breakout = (df['VROC'] < -self.threshold) & (vroc_change < -10)
            signal[weak_breakout] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_price_volume_alignment(self, df: pd.DataFrame) -> pd.Series:
        """
        计算量价配合度

        Args:
            df: 包含VROC和价格数据的DataFrame

        Returns:
            量价配合度序列 (1=完美配合, 0.5=一般配合, 0=反向配合, -0.5=一般背离, -1=完全背离)
        """
        try:
            alignment = np.zeros(len(df))

            # 价格和成交量的变化
            price_change = df['Close'].pct_change()
            volume_change = df['Volume'].pct_change()

            # 完美配合：价涨量增 或 价跌量减
            perfect_alignment = (
                ((price_change > 0) & (volume_change > 0)) |
                ((price_change < 0) & (volume_change < 0))
            )

            # 一般配合：方向一致但变化幅度适中
            normal_alignment = (
                ((price_change > 0) & (volume_change > 0)) |
                ((price_change < 0) & (volume_change < 0))
            )
            alignment[perfect_alignment] = 1
            alignment[normal_alignment] = 0.5

            # 反向配合：价涨量减 或 价跌量增
            opposite_alignment = (
                ((price_change > 0) & (volume_change < 0)) |
                ((price_change < 0) & (volume_change > 0))
            )
            alignment[opposite_alignment] = 0

            return pd.Series(alignment, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_trading_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算交易信号

        Args:
            df: 包含VROC数据的DataFrame

        Returns:
            交易信号序列 (1=买入, -1=卖出, 0=无信号)
        """
        try:
            signal = np.zeros(len(df))

            # 买入信号1：价涨量增确认突破
            price_volume_breakout = (
                (df['Close'] > df['Close'].shift(1)) &  # 价格上涨
                (df['VROC'] > self.threshold) &  # 成交量大幅增加
                (df['VROC'] > df['VROC'].shift(1))  # VROC上升
            )
            signal[price_volume_breakout] = 1

            # 买入信号2：看涨背离
            bullish_divergence = df['VROC_Price_Divergence'] == 1
            signal[bullish_divergence] = 1

            # 买入信号3：VROC向上穿越信号线
            vroc_cross_up = (
                (df['VROC'] > df['VROC_Signal']) &
                (df['VROC'].shift(1) <= df['VROC_Signal'].shift(1)) &
                (df['Close'] >= df['Close'].rolling(5).mean())  # 价格在均线上方
            )
            signal[vroc_cross_up] = 1

            # 买入信号4：成交量均线金叉
            volume_ma_golden_cross = (
                (df['Volume_MA_Fast'] > df['Volume_MA_Slow']) &
                (df['Volume_MA_Fast'].shift(1) <= df['Volume_MA_Slow'].shift(1))
            )
            signal[volume_ma_golden_cross] = 1

            # 卖出信号1：价跌量增确认下跌
            price_volume_decline = (
                (df['Close'] < df['Close'].shift(1)) &  # 价格下跌
                (df['VROC'] > self.threshold) &  # 成交量大幅增加
                (df['VROC'] < df['VROC'].shift(1))  # VROC下降
            )
            signal[price_volume_decline] = -1

            # 卖出信号2：看跌背离
            bearish_divergence = df['VROC_Price_Divergence'] == -1
            signal[bearish_divergence] = -1

            # 卖出信号3：VROC向下穿越信号线
            vroc_cross_down = (
                (df['VROC'] < df['VROC_Signal']) &
                (df['VROC'].shift(1) >= df['VROC_Signal'].shift(1)) &
                (df['Close'] <= df['Close'].rolling(5).mean())  # 价格在均线下方
            )
            signal[vroc_cross_down] = -1

            # 卖出信号4：成交量均线死叉
            volume_ma_death_cross = (
                (df['Volume_MA_Fast'] < df['Volume_MA_Slow']) &
                (df['Volume_MA_Fast'].shift(1) >= df['Volume_MA_Slow'].shift(1))
            )
            signal[volume_ma_death_cross] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        计算信号强度

        Args:
            df: 包含VROC数据的DataFrame

        Returns:
            信号强度序列 (0-1)
        """
        try:
            # 多个信号因子的加权组合
            signals = {
                'vroc_level': (abs(df['VROC']) / 200).clip(0, 1) * 0.3,  # VROC绝对值
                'vroc_direction': np.where(df['VROC'] > df['VROC'].shift(1), abs(df['VROC']) / 200, 0) * 0.2,  # VROC方向
                'breakout': abs(df['VROC_Breakout']) * 0.3,  # 突破信号
                'alignment': abs(df['VROC_Price_Alignment']) * 0.2,  # 量价配合度
            }

            # 加权平均
            strength = (
                signals['vroc_level'] +
                signals['vroc_direction'] +
                signals['breakout'] +
                signals['alignment']
            )

            # 限制在0-1范围
            strength = strength.clip(0, 1)
            return strength
        except:
            return pd.Series(0, index=df.index)

    def _calculate_volume_state(self, df: pd.DataFrame) -> pd.Series:
        """
        计算成交量状态

        Args:
            df: 包含VROC数据的DataFrame

        Returns:
            成交量状态序列 (1=异常放量, 0.5=放量, 0=正常, -0.5=缩量, -1=异常缩量)
        """
        try:
            volume_state = np.zeros(len(df))

            # 异常放量：VROC > 200%
            abnormal_high = df['VROC'] > 200
            volume_state[abnormal_high] = 1

            # 放量：VROC > 50%
            high = (df['VROC'] > 50) & (df['VROC'] <= 200)
            volume_state[high] = 0.5

            # 缩量：VROC < -50%
            low = (df['VROC'] < -50) & (df['VROC'] >= -200)
            volume_state[low] = -0.5

            # 异常缩量：VROC < -200%
            abnormal_low = df['VROC'] < -200
            volume_state[abnormal_low] = -1

            return pd.Series(volume_state, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def get_latest_signal(self, data: pd.DataFrame) -> Dict:
        """
        获取最新交易信号

        Args:
            data: 包含VROC数据的DataFrame

        Returns:
            包含最新信号的字典
        """
        if data is None or data.empty:
            return {'signal': 0, 'strength': 0, 'description': '数据不足'}

        try:
            latest = data.iloc[-1]

            signal = int(latest['VROC_Signal_Trade'])
            strength = float(latest['VROC_Strength'])
            vroc_value = float(latest['VROC'])
            volume_state = latest['VROC_Volume_State']

            # 生成描述
            if signal == 1:
                if volume_state == 1:
                    desc = f"买入信号 - 异常放量突破 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
                elif latest['VROC_Price_Divergence'] == 1:
                    desc = f"买入信号 - 看涨背离 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
                else:
                    desc = f"买入信号 - 量价配合 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
            elif signal == -1:
                if volume_state == -1:
                    desc = f"卖出信号 - 异常放量下跌 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
                elif latest['VROC_Price_Divergence'] == -1:
                    desc = f"卖出信号 - 看跌背离 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
                else:
                    desc = f"卖出信号 - 量价配合 (VROC: {vroc_value:.2f}%, 强度: {strength:.2f})"
            else:
                if volume_state > 0.5:
                    desc = f"无信号 - 放量中 (VROC: {vroc_value:.2f}%)"
                elif volume_state < -0.5:
                    desc = f"无信号 - 缩量中 (VROC: {vroc_value:.2f}%)"
                else:
                    desc = f"无信号 - 成交量正常 (VROC: {vroc_value:.2f}%)"

            return {
                'signal': signal,
                'strength': strength,
                'description': desc,
                'vroc': vroc_value,
                'signal_line': float(latest['VROC_Signal']),
                'ema': float(latest['VROC_EMA']),
                'breakout': float(latest['VROC_Breakout']),
                'divergence': int(latest['VROC_Price_Divergence']),
                'alignment': float(latest['VROC_Price_Alignment']),
                'volume_state': float(volume_state),
                'volume': int(latest['Volume']),
                'volume_ma': float(latest['Volume_MA']),
            }
        except Exception as e:
            logger.error(f"获取最新信号错误: {e}")
            return {'signal': 0, 'strength': 0, 'description': f'错误: {e}'}

    def get_visualization_data(self, data: pd.DataFrame, periods: int = 50) -> Dict:
        """
        获取用于可视化的数据

        Args:
            data: 包含VROC数据的DataFrame
            periods: 返回的周期数

        Returns:
            用于可视化的数据字典
        """
        if data is None or data.empty:
            return {}

        try:
            recent_data = data.tail(periods)
            close = recent_data['Close'].values.tolist()
            volume = recent_data['Volume'].values.tolist()
            dates = recent_data.index.strftime('%Y-%m-%d').tolist()

            return {
                'dates': dates,
                'close': close,
                'volume': volume,
                'vroc': recent_data['VROC'].tolist(),
                'signal': recent_data['VROC_Signal'].tolist(),
                'ema': recent_data['VROC_EMA'].tolist(),
                'breakout': recent_data['VROC_Breakout'].tolist(),
                'divergence': recent_data['VROC_Price_Divergence'].tolist(),
                'alignment': recent_data['VROC_Price_Alignment'].tolist(),
                'signals': recent_data['VROC_Signal_Trade'].tolist(),
                'threshold': self.threshold,
            }
        except Exception as e:
            logger.error(f"获取可视化数据错误: {e}")
            return {}


def calculate_vroc(data: pd.DataFrame, period: int = 12, threshold: float = 50) -> pd.DataFrame:
    """
    VROC快速计算函数

    Args:
        data: 包含OHLCV的DataFrame
        period: 计算周期
        threshold: 显著变化阈值

    Returns:
        包含VROC指标的DataFrame
    """
    indicator = VROCIndicator(period, threshold)
    return indicator.calculate(data)
