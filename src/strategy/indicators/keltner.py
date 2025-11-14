"""
T175: Keltner Channel (肯特纳通道) 技术指标

肯特纳通道是基于ATR(平均真实波幅)的波动率通道指标。

## 组成
1. 中心线：EMA 20 (可配置)
2. 上轨：EMA + ATR * 倍数
3. 下轨：EMA - ATR * 倍数

## 交易信号
- 价格突破上轨：可能的上升趋势延续或超买
- 价格突破下轨：可能的下降趋势延续或超卖
- 价格在通道内：横盘整理
- 通道收缩：波动率降低，可能有大动作
- 通道扩张：波动率增加

## 参数
- ema_period: EMA周期，默认20
- atr_period: ATR周期，默认14
- atr_multiplier: ATR倍数，默认2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class KeltnerIndicator:
    """
    肯特纳通道指标计算器

    提供基于EMA和ATR的波动率通道分析。
    """

    def __init__(self, ema_period: int = 20, atr_period: int = 14, atr_multiplier: float = 2.0):
        """
        初始化肯特纳通道指标

        Args:
            ema_period: EMA周期，默认20
            atr_period: ATR周期，默认14
            atr_multiplier: ATR倍数，默认2.0
        """
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算肯特纳通道的所有组件

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含所有肯特纳通道指标的DataFrame
        """
        if data is None or data.empty:
            logger.error("输入数据为空")
            return pd.DataFrame()

        df = data.copy()

        try:
            # 1. 计算EMA中心线
            df['Keltner_EMA'] = df['Close'].ewm(span=self.ema_period, adjust=False).mean()

            # 2. 计算ATR
            df['Keltner_ATR'] = self._calculate_atr(df)

            # 3. 计算上轨和下轨
            df['Keltner_Upper'] = df['Keltner_EMA'] + (df['Keltner_ATR'] * self.atr_multiplier)
            df['Keltner_Lower'] = df['Keltner_EMA'] - (df['Keltner_ATR'] * self.atr_multiplier)

            # 4. 计算通道宽度
            df['Keltner_Width'] = df['Keltner_Upper'] - df['Keltner_Lower']
            df['Keltner_Width_Pct'] = (df['Keltner_Width'] / df['Keltner_EMA']) * 100

            # 5. 计算价格在通道中的位置
            df['Keltner_Price_Position'] = self._calculate_price_position(df)

            # 6. 计算突破信号
            df['Keltner_Breakout'] = self._calculate_breakout_signals(df)

            # 7. 计算通道方向
            df['Keltner_Trend'] = self._calculate_trend_direction(df)

            # 8. 计算波动率状态
            df['Keltner_Volatility_State'] = self._calculate_volatility_state(df)

            # 9. 计算交易信号
            df['Keltner_Signal'] = self._calculate_trading_signals(df)

            # 10. 计算信号强度
            df['Keltner_Signal_Strength'] = self._calculate_signal_strength(df)

            logger.info("肯特纳通道计算完成")

        except Exception as e:
            logger.error(f"肯特纳通道计算错误: {e}")

        return df

    def _calculate_atr(self, data: pd.DataFrame, period: Optional[int] = None) -> pd.Series:
        """
        计算ATR (平均真实波幅)

        Args:
            data: 包含OHLCV的DataFrame
            period: ATR周期，为None则使用默认值

        Returns:
            ATR序列
        """
        period = period or self.atr_period

        high = data['High']
        low = data['Low']
        close = data['Close']

        # 计算真实波幅
        tr1 = high - low  # 当日最高价 - 当日最低价
        tr2 = abs(high - close.shift(1))  # 当日最高价 - 昨日收盘价
        tr3 = abs(low - close.shift(1))  # 当日最低价 - 昨日收盘价

        # 取最大值
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算ATR (移动平均)
        atr = true_range.rolling(window=period).mean()

        return atr

    def _calculate_price_position(self, df: pd.DataFrame) -> pd.Series:
        """
        计算价格在肯特纳通道中的位置

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            价格位置序列 (0-1, 0=下轨, 1=上轨)
        """
        try:
            price_position = (df['Close'] - df['Keltner_Lower']) / (df['Keltner_Upper'] - df['Keltner_Lower'])
            price_position = price_position.clip(0, 1)
            return price_position
        except:
            return pd.Series(0.5, index=df.index)

    def _calculate_breakout_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算突破信号

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            突破信号序列 (1=上破, -1=下破, 0=无突破)
        """
        try:
            # 上破：价格上穿通道上轨
            upper_breakout = (df['Close'] > df['Keltner_Upper']) & (df['Close'].shift(1) <= df['Keltner_Upper'].shift(1))

            # 下破：价格下穿通道下轨
            lower_breakout = (df['Close'] < df['Keltner_Lower']) & (df['Close'].shift(1) >= df['Keltner_Lower'].shift(1))

            signal = np.zeros(len(df))
            signal[upper_breakout] = 1
            signal[lower_breakout] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_trend_direction(self, df: pd.DataFrame) -> pd.Series:
        """
        计算通道趋势方向

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            趋势方向序列 (1=上升, -1=下降, 0=横盘)
        """
        try:
            # EMA方向
            ema_rising = df['Keltner_EMA'] > df['Keltner_EMA'].shift(1)
            ema_rising_count = ema_rising.rolling(window=3).sum()

            # 通道宽度变化
            width_expanding = df['Keltner_Width'] > df['Keltner_Width'].shift(1)
            width_expanding_count = width_expanding.rolling(window=3).sum()

            # 趋势判断
            trend = np.zeros(len(df))

            # 上升趋势：EMA上升 + 通道扩张 + 价格在通道上半部分
            uptrend = (ema_rising_count >= 2) & (width_expanding_count >= 1) & (df['Keltner_Price_Position'] > 0.5)
            trend[uptrend] = 1

            # 下降趋势：EMA下降 + 通道扩张 + 价格在通道下半部分
            downtrend = (ema_rising_count <= 1) & (width_expanding_count >= 1) & (df['Keltner_Price_Position'] < 0.5)
            trend[downtrend] = -1

            return pd.Series(trend, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_volatility_state(self, df: pd.DataFrame) -> pd.Series:
        """
        计算波动率状态

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            波动率状态序列 (1=高波动, 0=低波动)
        """
        try:
            # 计算通道宽度的移动平均
            width_ma = df['Keltner_Width_Pct'].rolling(window=20).mean()
            width_std = df['Keltner_Width_Pct'].rolling(window=20).std()

            # 当前宽度与历史平均的比较
            volatility_state = df['Keltner_Width_Pct'] > (width_ma + width_std * 0.5)
            volatility_state = volatility_state.astype(int)

            return volatility_state
        except:
            return pd.Series(0, index=df.index)

    def _calculate_trading_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        计算交易信号

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            交易信号序列 (1=买入, -1=卖出, 0=无信号)
        """
        try:
            signal = np.zeros(len(df))

            # 买入信号1：价格从下方突破下轨后的反弹
            rebound_buy = (
                (df['Keltner_Breakout'] == -1) &  # 下破
                (df['Close'] > df['Keltner_Lower']) &  # 价格回到通道内
                (df['Close'] > df['Close'].shift(1))  # 价格上涨
            )
            signal[rebound_buy] = 1

            # 买入信号2：强上升趋势中价格回调到下轨
            trend_buy = (
                (df['Keltner_Trend'] == 1) &  # 上升趋势
                (df['Keltner_Price_Position'] < 0.3) &  # 价格接近下轨
                (df['Close'] > df['Close'].shift(1))  # 价格上涨
            )
            signal[trend_buy] = 1

            # 买入信号3：通道收缩后的向上突破
            squeeze_buy = (
                (df['Keltner_Width_Pct'] < df['Keltner_Width_Pct'].rolling(20).quantile(0.2).fillna(0)) &  # 通道收缩
                (df['Keltner_Breakout'] == 1)  # 上破
            )
            signal[squeeze_buy] = 1

            # 卖出信号1：价格从上方突破上轨后的回落
            reversal_sell = (
                (df['Keltner_Breakout'] == 1) &  # 上破
                (df['Close'] < df['Keltner_Upper']) &  # 价格回到通道内
                (df['Close'] < df['Close'].shift(1))  # 价格下跌
            )
            signal[reversal_sell] = -1

            # 卖出信号2：强下降趋势中价格反弹到上轨
            trend_sell = (
                (df['Keltner_Trend'] == -1) &  # 下降趋势
                (df['Keltner_Price_Position'] > 0.7) &  # 价格接近上轨
                (df['Close'] < df['Close'].shift(1))  # 价格下跌
            )
            signal[trend_sell] = -1

            # 卖出信号3：通道收缩后的向下突破
            squeeze_sell = (
                (df['Keltner_Width_Pct'] < df['Keltner_Width_Pct'].rolling(20).quantile(0.2).fillna(0)) &  # 通道收缩
                (df['Keltner_Breakout'] == -1)  # 下破
            )
            signal[squeeze_sell] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        计算信号强度

        Args:
            df: 包含肯特纳通道数据的DataFrame

        Returns:
            信号强度序列 (0-1)
        """
        try:
            # 多个信号因子的加权组合
            signals = {
                'breakout': abs(df['Keltner_Breakout']) * 0.4,
                'position': abs(df['Keltner_Price_Position'] - 0.5) * 2 * 0.3,  # 距离通道中心的距离
                'trend': abs(df['Keltner_Trend']) * 0.2,
                'volatility': df['Keltner_Volatility_State'] * 0.1,
            }

            # 加权平均
            strength = (
                signals['breakout'] +
                signals['position'] +
                signals['trend'] +
                signals['volatility']
            )

            # 限制在0-1范围
            strength = strength.clip(0, 1)
            return strength
        except:
            return pd.Series(0, index=df.index)

    def get_latest_signal(self, data: pd.DataFrame) -> Dict:
        """
        获取最新交易信号

        Args:
            data: 包含肯特纳通道数据的DataFrame

        Returns:
            包含最新信号的字典
        """
        if data is None or data.empty:
            return {'signal': 0, 'strength': 0, 'description': '数据不足'}

        try:
            latest = data.iloc[-1]

            signal = int(latest['Keltner_Signal'])
            strength = float(latest['Keltner_Signal_Strength'])

            # 生成描述
            price_pos = latest['Keltner_Price_Position']
            trend = latest['Keltner_Trend']
            volatility = latest['Keltner_Volatility_State']

            if signal == 1:
                if price_pos < 0.3:
                    desc = f"买入信号 - 回调至下轨 (强度: {strength:.2f})"
                elif volatility == 1:
                    desc = f"买入信号 - 突破上轨 (强度: {strength:.2f})"
                else:
                    desc = f"买入信号 - 趋势延续 (强度: {strength:.2f})"
            elif signal == -1:
                if price_pos > 0.7:
                    desc = f"卖出信号 - 反弹至 上轨 (强度: {strength:.2f})"
                elif volatility == 1:
                    desc = f"卖出信号 - 突破下轨 (强度: {strength:.2f})"
                else:
                    desc = f"卖出信号 - 趋势延续 (强度: {strength:.2f})"
            else:
                desc = f"无信号 - 价格在通道{price_pos*100:.1f}%处"

            return {
                'signal': signal,
                'strength': strength,
                'description': desc,
                'trend': int(trend),
                'price_position': float(price_pos),
                'breakout': int(latest['Keltner_Breakout']),
                'volatility_state': int(volatility),
                'upper': float(latest['Keltner_Upper']),
                'lower': float(latest['Keltner_Lower']),
                'ema': float(latest['Keltner_EMA']),
                'atr': float(latest['Keltner_ATR']),
                'width_pct': float(latest['Keltner_Width_Pct']),
            }
        except Exception as e:
            logger.error(f"获取最新信号错误: {e}")
            return {'signal': 0, 'strength': 0, 'description': f'错误: {e}'}

    def get_visualization_data(self, data: pd.DataFrame, periods: int = 50) -> Dict:
        """
        获取用于可视化的数据

        Args:
            data: 包含肯特纳通道数据的DataFrame
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
                'upper': recent_data['Keltner_Upper'].tolist(),
                'lower': recent_data['Keltner_Lower'].tolist(),
                'ema': recent_data['Keltner_EMA'].tolist(),
                'price_position': recent_data['Keltner_Price_Position'].tolist(),
                'breakout': recent_data['Keltner_Breakout'].tolist(),
                'signals': recent_data['Keltner_Signal'].tolist(),
                'width_pct': recent_data['Keltner_Width_Pct'].tolist(),
            }
        except Exception as e:
            logger.error(f"获取可视化数据错误: {e}")
            return {}


def calculate_keltner(data: pd.DataFrame, ema_period: int = 20, atr_period: int = 14, atr_multiplier: float = 2.0) -> pd.DataFrame:
    """
    肯特纳通道快速计算函数

    Args:
        data: 包含OHLCV的DataFrame
        ema_period: EMA周期
        atr_period: ATR周期
        atr_multiplier: ATR倍数

    Returns:
        包含肯特纳通道指标的DataFrame
    """
    indicator = KeltnerIndicator(ema_period, atr_period, atr_multiplier)
    return indicator.calculate(data)
