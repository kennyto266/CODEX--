"""
T176: CMO (Chande Momentum Oscillator) 技术指标

钱德动量振荡器是一个动量指标，测量价格变动的速度。

## 计算公式
CMO = 100 * (Su - Sd) / (Su + Sd)
其中：
- Su = 收盘价上涨期间的总和
- Sd = 收盘价下跌期间的总和

## 范围
- CMO值范围：-100 到 +100
- 正值：表示上涨动量
- 负值：表示下跌动量

## 交易信号
- CMO > +50：可能的超买区域
- CMO < -50：可能的超卖区域
- CMO从下方穿越中线(0)：买入信号
- CMO从上方穿越中线(0)：卖出信号
- CMO与价格背离：趋势反转信号

## 参数
- period: 计算周期，默认14
- upper_threshold: 超买阈值，默认50
- lower_threshold: 超卖阈值，默认-50
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CMOIndicator:
    """
    CMO (Chande Momentum Oscillator) 指标计算器

    提供钱德动量振荡器分析，包括超买超卖信号和背离检测。
    """

    def __init__(self, period: int = 14, upper_threshold: float = 50, lower_threshold: float = -50):
        """
        初始化CMO指标

        Args:
            period: 计算周期，默认14
            upper_threshold: 超买阈值，默认50
            lower_threshold: 超卖阈值，默认-50
        """
        self.period = period
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算CMO的所有组件

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含所有CMO指标的DataFrame
        """
        if data is None or data.empty:
            logger.error("输入数据为空")
            return pd.DataFrame()

        df = data.copy()

        try:
            # 1. 计算价格变化
            df['CMO_Price_Change'] = df['Close'].diff()

            # 2. 分别计算上涨和下跌的总和
            df['CMO_Up_Move'] = np.where(df['CMO_Price_Change'] > 0, df['CMO_Price_Change'], 0)
            df['CMO_Down_Move'] = np.where(df['CMO_Price_Change'] < 0, -df['CMO_Price_Change'], 0)

            # 3. 计算CMO
            df['CMO'] = self._calculate_cmo(df)

            # 4. 计算CMO的移动平均（信号线）
            df['CMO_Signal'] = df['CMO'].rolling(window=9).mean()

            # 5. 计算超买超卖信号
            df['CMO_Overbought'] = df['CMO'] > self.upper_threshold
            df['CMO_Oversold'] = df['CMO'] < self.lower_threshold

            # 6. 计算交叉信号
            df['CMO_Cross'] = self._calculate_cross_signals(df)

            # 7. 计算背离信号
            df['CMO_Divergence'] = self._calculate_divergence(df)

            # 8. 计算交易信号
            df['CMO_Signal_Trade'] = self._calculate_trading_signals(df)

            # 9. 计算信号强度
            df['CMO_Strength'] = self._calculate_signal_strength(df)

            # 10. 计算动量状态
            df['CMO_Momentum'] = self._calculate_momentum_state(df)

            logger.info("CMO计算完成")

        except Exception as e:
            logger.error(f"CMO计算错误: {e}")

        return df

    def _calculate_cmo(self, df: pd.DataFrame) -> pd.Series:
        """
        计算CMO值

        Args:
            df: 包含价格变化数据的DataFrame

        Returns:
            CMO序列
        """
        try:
            # 计算上涨和下跌的总和
            up_sum = df['CMO_Up_Move'].rolling(window=self.period).sum()
            down_sum = df['CMO_Down_Move'].rolling(window=self.period).sum()

            # 计算CMO
            cmo = 100 * (up_sum - down_sum) / (up_sum + down_sum + 0.0001)

            return cmo
        except:
            return pd.Series(0, index=df.index)

    def _calculate_cross_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算交叉信号

        Args:
            df: 包含CMO数据的DataFrame

        Returns:
            交叉信号序列 (1=向上交叉, -1=向下交叉, 0=无交叉)
        """
        try:
            signal = np.zeros(len(df))

            # CMO向上穿越0轴
            cmo_cross_up = (df['CMO'] > 0) & (df['CMO'].shift(1) <= 0)
            signal[cmo_cross_up] = 1

            # CMO向下穿越0轴
            cmo_cross_down = (df['CMO'] < 0) & (df['CMO'].shift(1) >= 0)
            signal[cmo_cross_down] = -1

            # CMO与信号线交叉
            # CMO向上穿越信号线
            cmo_cross_signal_up = (df['CMO'] > df['CMO_Signal']) & (df['CMO'].shift(1) <= df['CMO_Signal'].shift(1))
            signal[cmo_cross_signal_up] = 1

            # CMO向下穿越信号线
            cmo_cross_signal_down = (df['CMO'] < df['CMO_Signal']) & (df['CMO'].shift(1) >= df['CMO_Signal'].shift(1))
            signal[cmo_cross_signal_down] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_divergence(self, df: pd.DataFrame, lookback: int = 50) -> pd.Series:
        """
        计算背离信号

        Args:
            df: 包含CMO和价格数据的DataFrame
            lookback: 查找背离的回望周期

        Returns:
            背离信号序列 (1=看涨背离, -1=看跌背离, 0=无背离)
        """
        try:
            signal = np.zeros(len(df))

            for i in range(lookback, len(df)):
                # 获取价格和CMO的窗口数据
                price_window = df['Close'].iloc[i-lookback:i+1]
                cmo_window = df['CMO'].iloc[i-lookback:i+1]

                # 去除NaN值
                price_window = price_window.dropna()
                cmo_window = cmo_window.dropna()

                if len(price_window) < 10 or len(cmo_window) < 10:
                    continue

                # 寻找局部极值
                price_peak_idx = price_window.idxmax()
                price_trough_idx = price_window.idxmin()
                cmo_peak_idx = cmo_window.idxmax()
                cmo_trough_idx = cmo_window.idxmin()

                # 看涨背离：价格创新低但CMO没有创新低
                if (price_trough_idx == price_window.index[-1] and
                    cmo_trough_idx != cmo_window.index[-1]):

                    # 检查CMO是否在某个阈值之上
                    if cmo_window.iloc[-1] > cmo_window[cmo_window < 0].quantile(0.3):
                        signal[i] = 1

                # 看跌背离：价格创新高但CMO没有创新高
                elif (price_peak_idx == price_window.index[-1] and
                      cmo_peak_idx != cmo_window.index[-1]):

                    # 检查CMO是否在某个阈值之下
                    if cmo_window.iloc[-1] < cmo_window[cmo_window > 0].quantile(0.7):
                        signal[i] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_trading_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算交易信号

        Args:
            df: 包含CMO数据的DataFrame

        Returns:
            交易信号序列 (1=买入, -1=卖出, 0=无信号)
        """
        try:
            signal = np.zeros(len(df))

            # 买入信号1：CMO从超卖区域向上穿越
            oversold_recovery = (
                (df['CMO'] < self.lower_threshold) &
                (df['CMO'] > df['CMO'].shift(1)) &
                (df['CMO'].shift(1) < self.lower_threshold)
            )
            signal[oversold_recovery] = 1

            # 买入信号2：CMO向上穿越0轴
            cmo_cross_up = df['CMO_Cross'] == 1
            signal[cmo_cross_up] = 1

            # 买入信号3：看涨背离
            bullish_divergence = df['CMO_Divergence'] == 1
            signal[bullish_divergence] = 1

            # 买入信号4：CMO从下方穿越信号线
            cmo_cross_signal_up = (
                (df['CMO'] > df['CMO_Signal']) &
                (df['CMO'].shift(1) <= df['CMO_Signal'].shift(1)) &
                (df['CMO'] > -20)  # 不在极端超卖区域
            )
            signal[cmo_cross_signal_up] = 1

            # 卖出信号1：CMO从超买区域向下穿越
            overbought_decline = (
                (df['CMO'] > self.upper_threshold) &
                (df['CMO'] < df['CMO'].shift(1)) &
                (df['CMO'].shift(1) > self.upper_threshold)
            )
            signal[overbought_decline] = -1

            # 卖出信号2：CMO向下穿越0轴
            cmo_cross_down = df['CMO_Cross'] == -1
            signal[cmo_cross_down] = -1

            # 卖出信号3：看跌背离
            bearish_divergence = df['CMO_Divergence'] == -1
            signal[bearish_divergence] = -1

            # 卖出信号4：CMO从上方穿越信号线
            cmo_cross_signal_down = (
                (df['CMO'] < df['CMO_Signal']) &
                (df['CMO'].shift(1) >= df['CMO_Signal'].shift(1)) &
                (df['CMO'] < 20)  # 不在极端超买区域
            )
            signal[cmo_cross_signal_down] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        计算信号强度

        Args:
            df: 包含CMO数据的DataFrame

        Returns:
            信号强度序列 (0-1)
        """
        try:
            # 多个信号因子的加权组合
            signals = {
                'cmo_level': abs(df['CMO']) / 100 * 0.3,  # CMO绝对值
                'cmo_direction': np.where(df['CMO'] > df['CMO'].shift(1), df['CMO'] / 100, 0) * 0.2,  # CMO方向
                'cross': abs(df['CMO_Cross']) * 0.3,  # 交叉信号
                'divergence': abs(df['CMO_Divergence']) * 0.2,  # 背离信号
            }

            # 加权平均
            strength = (
                signals['cmo_level'] +
                signals['cmo_direction'] +
                signals['cross'] +
                signals['divergence']
            )

            # 限制在0-1范围
            strength = strength.clip(0, 1)
            return strength
        except:
            return pd.Series(0, index=df.index)

    def _calculate_momentum_state(self, df: pd.DataFrame) -> pd.Series:
        """
        计算动量状态

        Args:
            df: 包含CMO数据的DataFrame

        Returns:
            动量状态序列 (1=强上涨, 0.5=上涨, 0=中性, -0.5=下跌, -1=强下跌)
        """
        try:
            momentum = np.zeros(len(df))

            # 强上涨：CMO > 50
            strong_up = df['CMO'] > 50
            momentum[strong_up] = 1

            # 上涨：0 < CMO < 50
            up = (df['CMO'] > 0) & (df['CMO'] <= 50)
            momentum[up] = 0.5

            # 下跌：-50 < CMO < 0
            down = (df['CMO'] < 0) & (df['CMO'] >= -50)
            momentum[down] = -0.5

            # 强下跌：CMO < -50
            strong_down = df['CMO'] < -50
            momentum[strong_down] = -1

            return pd.Series(momentum, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def get_latest_signal(self, data: pd.DataFrame) -> Dict:
        """
        获取最新交易信号

        Args:
            data: 包含CMO数据的DataFrame

        Returns:
            包含最新信号的字典
        """
        if data is None or data.empty:
            return {'signal': 0, 'strength': 0, 'description': '数据不足'}

        try:
            latest = data.iloc[-1]

            signal = int(latest['CMO_Signal_Trade'])
            strength = float(latest['CMO_Strength'])
            cmo_value = float(latest['CMO'])

            # 生成描述
            if signal == 1:
                if latest['CMO_Oversold']:
                    desc = f"买入信号 - 超卖反弹 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                elif latest['CMO_Cross'] == 1:
                    desc = f"买入信号 - 向上穿越 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                elif latest['CMO_Divergence'] == 1:
                    desc = f"买入信号 - 看涨背离 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                else:
                    desc = f"买入信号 - 动量转强 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
            elif signal == -1:
                if latest['CMO_Overbought']:
                    desc = f"卖出信号 - 超买回调 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                elif latest['CMO_Cross'] == -1:
                    desc = f"卖出信号 - 向下穿越 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                elif latest['CMO_Divergence'] == -1:
                    desc = f"卖出信号 - 看跌背离 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
                else:
                    desc = f"卖出信号 - 动量转弱 (CMO: {cmo_value:.2f}, 强度: {strength:.2f})"
            else:
                if cmo_value > 30:
                    desc = f"无信号 - 上涨动量 (CMO: {cmo_value:.2f})"
                elif cmo_value < -30:
                    desc = f"无信号 - 下跌动量 (CMO: {cmo_value:.2f})"
                else:
                    desc = f"无信号 - 中性区域 (CMO: {cmo_value:.2f})"

            return {
                'signal': signal,
                'strength': strength,
                'description': desc,
                'cmo': cmo_value,
                'signal_line': float(latest['CMO_Signal']),
                'overbought': bool(latest['CMO_Overbought']),
                'oversold': bool(latest['CMO_Oversold']),
                'cross': int(latest['CMO_Cross']),
                'divergence': int(latest['CMO_Divergence']),
                'momentum': float(latest['CMO_Momentum']),
            }
        except Exception as e:
            logger.error(f"获取最新信号错误: {e}")
            return {'signal': 0, 'strength': 0, 'description': f'错误: {e}'}

    def get_visualization_data(self, data: pd.DataFrame, periods: int = 50) -> Dict:
        """
        获取用于可视化的数据

        Args:
            data: 包含CMO数据的DataFrame
            periods: 返回的周期数

        Returns:
            用于可视化的数据字典
        """
        if data is None or data.empty:
            return {}

        try:
            recent_data = data.tail(periods)
            close = recent_data['Close'].values.tolist()
            dates = recent_data.index.strftime('%Y-%m-%d').tolist()

            return {
                'dates': dates,
                'close': close,
                'cmo': recent_data['CMO'].tolist(),
                'signal': recent_data['CMO_Signal'].tolist(),
                'overbought': recent_data['CMO_Overbought'].tolist(),
                'oversold': recent_data['CMO_Oversold'].tolist(),
                'cross': recent_data['CMO_Cross'].tolist(),
                'divergence': recent_data['CMO_Divergence'].tolist(),
                'signals': recent_data['CMO_Signal_Trade'].tolist(),
                'upper_threshold': self.upper_threshold,
                'lower_threshold': self.lower_threshold,
            }
        except Exception as e:
            logger.error(f"获取可视化数据错误: {e}")
            return {}


def calculate_cmo(data: pd.DataFrame, period: int = 14, upper_threshold: float = 50, lower_threshold: float = -50) -> pd.DataFrame:
    """
    CMO快速计算函数

    Args:
        data: 包含OHLCV的DataFrame
        period: 计算周期
        upper_threshold: 超买阈值
        lower_threshold: 超卖阈值

    Returns:
        包含CMO指标的DataFrame
    """
    indicator = CMOIndicator(period, upper_threshold, lower_threshold)
    return indicator.calculate(data)
