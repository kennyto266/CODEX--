"""
T178: 5个高级技术指标变体

包含5个高级技术指标变体的实现：
1. Williams %R - 威廉指标动量振荡器
2. Stochastic RSI - 随机RSI指标
3. ADX优化 - 优化的平均趋向指数
4. ATR带 - 基于ATR的波动率带
5. OBV变异 - 改进的能量潮指标

## 1. Williams %R
- 动量指标，范围-100到0
- 衡量当前价格相对于最高价和最低价的位置
- 超买：-20以上，超卖：-80以下

## 2. Stochastic RSI
- RSI的随机化版本
- 结合RSI的超买超卖和随机指标的敏感性
- 更快的信号，更少的假信号

## 3. ADX优化
- 平均趋向指数的优化版本
- 改进趋势强度计算
- 更好的趋势确认

## 4. ATR带
- 基于ATR的波动率带
- 上轨：价格 + ATR * 倍数
- 下轨：价格 - ATR * 倍数
- 动态支撑阻力

## 5. OBV变异
- 改进的能量潮指标
- 考虑价格变化幅度
- 更准确的量价关系
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class WilliamsRIndicator:
    """
    Williams %R 指标计算器

    动量指标，衡量当前价格在周期最高价和最低价中的位置
    """

    def __init__(self, period: int = 14):
        """
        初始化Williams %R指标

        Args:
            period: 计算周期，默认14
        """
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算Williams %R

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含Williams %R指标的DataFrame
        """
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()

        try:
            # 计算周期最高价和最低价
            highest_high = df['High'].rolling(window=self.period).max()
            lowest_low = df['Low'].rolling(window=self.period).min()

            # 计算Williams %R
            # 公式: (最高价 - 当前收盘价) / (最高价 - 最低价) * -100
            df['WilliamsR'] = ((highest_high - df['Close']) / (highest_high - lowest_low)) * -100

            # 计算Williams %R的移动平均
            df['WilliamsR_MA'] = df['WilliamsR'].rolling(window=3).mean()

            # 超买超卖信号
            df['WilliamsR_Overbought'] = df['WilliamsR'] > -20
            df['WilliamsR_Oversold'] = df['WilliamsR'] < -80

            # 交叉信号
            df['WilliamsR_Signal'] = self._calculate_signals(df)

            # 信号强度
            df['WilliamsR_Strength'] = self._calculate_strength(df)

            logger.info("Williams %R计算完成")

        except Exception as e:
            logger.error(f"Williams %R计算错误: {e}")

        return df

    def _calculate_signals(self, df: pd.DataFrame) -> pd.Series:
        """计算交易信号"""
        try:
            signal = np.zeros(len(df))

            # 从超卖区域向上穿越
            oversold_recovery = (
                (df['WilliamsR'] > -80) & (df['WilliamsR'].shift(1) <= -80) &
                (df['WilliamsR'] > df['WilliamsR'].shift(1))
            )
            signal[oversold_recovery] = 1

            # 从超买区域向下穿越
            overbought_decline = (
                (df['WilliamsR'] < -20) & (df['WilliamsR'].shift(1) >= -20) &
                (df['WilliamsR'] < df['WilliamsR'].shift(1))
            )
            signal[overbought_decline] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_strength(self, df: pd.DataFrame) -> pd.Series:
        """计算信号强度"""
        try:
            # 距离极值的程度
            overbought_strength = np.where(df['WilliamsR'] > -20,
                                          (-20 - df['WilliamsR']) / 20, 0)
            oversold_strength = np.where(df['WilliamsR'] < -80,
                                         (df['WilliamsR'] - (-80)) / 20, 0)

            strength = (overbought_strength + oversold_strength).clip(0, 1)
            return pd.Series(strength, index=df.index)
        except:
            return pd.Series(0, index=df.index)


class StochasticRSIIndicator:
    """
    Stochastic RSI 指标计算器

    RSI的随机化版本，结合了两者的优点
    """

    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, smooth_k: int = 3, smooth_d: int = 3):
        """
        初始化Stochastic RSI指标

        Args:
            rsi_period: RSI计算周期
            stoch_period: 随机指标计算周期
            smooth_k: %K平滑周期
            smooth_d: %D平滑周期
        """
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.smooth_k = smooth_k
        self.smooth_d = smooth_d

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算Stochastic RSI

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含Stochastic RSI指标的DataFrame
        """
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()

        try:
            # 首先计算RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / (loss + 0.0001)
            df['RSI'] = 100 - (100 / (1 + rs))

            # 然后计算Stochastic RSI
            # Stochastic RSI = (RSI - RSI的最低值) / (RSI的最高值 - RSI的最低值) * 100
            rsi_min = df['RSI'].rolling(window=self.stoch_period).min()
            rsi_max = df['RSI'].rolling(window=self.stoch_period).max()

            df['StochRSI'] = ((df['RSI'] - rsi_min) / (rsi_max - rsi_min + 0.0001)) * 100

            # 平滑处理
            df['StochRSI_K'] = df['StochRSI'].rolling(window=self.smooth_k).mean()
            df['StochRSI_D'] = df['StochRSI_K'].rolling(window=self.smooth_d).mean()

            # 超买超卖信号
            df['StochRSI_Overbought'] = df['StochRSI_K'] > 80
            df['StochRSI_Oversold'] = df['StochRSI_K'] < 20

            # 交叉信号
            df['StochRSI_Signal'] = self._calculate_signals(df)

            # 信号强度
            df['StochRSI_Strength'] = self._calculate_strength(df)

            logger.info("Stochastic RSI计算完成")

        except Exception as e:
            logger.error(f"Stochastic RSI计算错误: {e}")

        return df

    def _calculate_signals(self, df: pd.DataFrame) -> pd.Series:
        """计算交易信号"""
        try:
            signal = np.zeros(len(df))

            # K线上穿D线
            golden_cross = (
                (df['StochRSI_K'] > df['StochRSI_D']) &
                (df['StochRSI_K'].shift(1) <= df['StochRSI_D'].shift(1))
            )
            signal[golden_cross] = 1

            # K线下穿D线
            death_cross = (
                (df['StochRSI_K'] < df['StochRSI_D']) &
                (df['StochRSI_K'].shift(1) >= df['StochRSI_D'].shift(1))
            )
            signal[death_cross] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_strength(self, df: pd.DataFrame) -> pd.Series:
        """计算信号强度"""
        try:
            # 距离极值的程度
            overbought_strength = np.where(df['StochRSI_K'] > 80,
                                          (df['StochRSI_K'] - 80) / 20, 0)
            oversold_strength = np.where(df['StochRSI_K'] < 20,
                                         (20 - df['StochRSI_K']) / 20, 0)

            strength = (overbought_strength + oversold_strength).clip(0, 1)
            return pd.Series(strength, index=df.index)
        except:
            return pd.Series(0, index=df.index)


class OptimizedADXIndicator:
    """
    优化的ADX指标计算器

    改进的趋势强度计算和信号确认
    """

    def __init__(self, period: int = 14, adx_threshold: int = 25):
        """
        初始化优化的ADX指标

        Args:
            period: 计算周期
            adx_threshold: 趋势强度阈值
        """
        self.period = period
        self.adx_threshold = adx_threshold

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算优化的ADX

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含优化ADX指标的DataFrame
        """
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()

        try:
            # 计算真实波幅和方向移动
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())

            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=self.period).mean()

            # 计算方向移动
            df['plus_dm'] = np.where(
                (df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']),
                np.maximum(df['High'] - df['High'].shift(1), 0), 0
            )

            df['minus_dm'] = np.where(
                (df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)),
                np.maximum(df['Low'].shift(1) - df['Low'], 0), 0
            )

            # 优化：添加方向移动的方向判断
            plus_dm_direction = np.where(
                (df['High'] - df['High'].shift(1)) > 0,
                np.maximum(df['High'] - df['High'].shift(1), 0), 0
            )
            minus_dm_direction = np.where(
                (df['Low'].shift(1) - df['Low']) > 0,
                np.maximum(df['Low'].shift(1) - df['Low'], 0), 0
            )

            # 计算方向指数
            plus_di = 100 * (plus_dm_direction.rolling(window=self.period).mean() / df['ATR'])
            minus_di = 100 * (minus_dm_direction.rolling(window=self.period).mean() / df['ATR'])

            # 计算ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
            df['ADX_Opt'] = dx.rolling(window=self.period).mean()

            df['ADX_PlusDI'] = plus_di
            df['ADX_MinusDI'] = minus_di

            # 趋势强度信号
            df['ADX_Strong_Trend'] = df['ADX_Opt'] > self.adx_threshold

            # 趋势方向信号
            df['ADX_Uptrend'] = (df['ADX_PlusDI'] > df['ADX_MinusDI']) & df['ADX_Strong_Trend']
            df['ADX_Downtrend'] = (df['ADX_PlusDI'] < df['ADX_MinusDI']) & df['ADX_Strong_Trend']

            # 交叉信号
            df['ADX_Signal'] = self._calculate_signals(df)

            # 信号强度
            df['ADX_Strength'] = (df['ADX_Opt'] / 100).clip(0, 1)

            logger.info("优化ADX计算完成")

        except Exception as e:
            logger.error(f"优化ADX计算错误: {e}")

        return df

    def _calculate_signals(self, df: pd.DataFrame) -> pd.Series:
        """计算交易信号"""
        try:
            signal = np.zeros(len(df))

            # +DI上穿-DI
            plus_di_cross_up = (
                (df['ADX_PlusDI'] > df['ADX_MinusDI']) &
                (df['ADX_PlusDI'].shift(1) <= df['ADX_MinusDI'].shift(1)) &
                df['ADX_Strong_Trend']
            )
            signal[plus_di_cross_up] = 1

            # +DI下穿-DI
            plus_di_cross_down = (
                (df['ADX_PlusDI'] < df['ADX_MinusDI']) &
                (df['ADX_PlusDI'].shift(1) >= df['ADX_MinusDI'].shift(1)) &
                df['ADX_Strong_Trend']
            )
            signal[plus_di_cross_down] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)


class ATRBandsIndicator:
    """
    ATR带指标计算器

    基于ATR的动态波动率带
    """

    def __init__(self, period: int = 14, multiplier: float = 2.0):
        """
        初始化ATR带指标

        Args:
            period: ATR计算周期
            multiplier: ATR倍数
        """
        self.period = period
        self.multiplier = multiplier

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算ATR带

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含ATR带指标的DataFrame
        """
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()

        try:
            # 计算ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())

            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(window=self.period).mean()

            # 计算EMA作为中心线
            df['ATR_EMA'] = df['Close'].ewm(span=self.period, adjust=False).mean()

            # 计算ATR带
            df['ATR_Upper'] = df['ATR_EMA'] + (df['ATR'] * self.multiplier)
            df['ATR_Lower'] = df['ATR_EMA'] - (df['ATR'] * self.multiplier)

            # 扩展带：更宽的波动范围
            df['ATR_Upper_Wide'] = df['ATR_EMA'] + (df['ATR'] * self.multiplier * 1.5)
            df['ATR_Lower_Wide'] = df['ATR_EMA'] - (df['ATR'] * self.multiplier * 1.5)

            # 压缩带：更窄的波动范围
            df['ATR_Upper_Narrow'] = df['ATR_EMA'] + (df['ATR'] * self.multiplier * 0.5)
            df['ATR_Lower_Narrow'] = df['ATR_EMA'] - (df['ATR'] * self.multiplier * 0.5)

            # 带宽
            df['ATR_Bandwidth'] = (df['ATR_Upper'] - df['ATR_Lower']) / df['ATR_EMA'] * 100

            # 价格位置
            df['ATR_Price_Position'] = (df['Close'] - df['ATR_Lower']) / (df['ATR_Upper'] - df['ATR_Lower'])

            # 突破信号
            df['ATR_Signal'] = self._calculate_signals(df)

            # 信号强度
            df['ATR_Strength'] = self._calculate_strength(df)

            logger.info("ATR带计算完成")

        except Exception as e:
            logger.error(f"ATR带计算错误: {e}")

        return df

    def _calculate_signals(self, df: pd.DataFrame) -> pd.Series:
        """计算交易信号"""
        try:
            signal = np.zeros(len(df))

            # 上破带
            upper_breakout = (df['Close'] > df['ATR_Upper']) & (df['Close'].shift(1) <= df['ATR_Upper'].shift(1))
            signal[upper_breakout] = 1

            # 下破带
            lower_breakout = (df['Close'] < df['ATR_Lower']) & (df['Close'].shift(1) >= df['ATR_Lower'].shift(1))
            signal[lower_breakout] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_strength(self, df: pd.DataFrame) -> pd.Series:
        """计算信号强度"""
        try:
            # 距离带的距离
            upper_distance = np.where(df['Close'] > df['ATR_Upper'],
                                      (df['Close'] - df['ATR_Upper']) / df['ATR_EMA'], 0)
            lower_distance = np.where(df['Close'] < df['ATR_Lower'],
                                      (df['ATR_Lower'] - df['Close']) / df['ATR_EMA'], 0)

            strength = (upper_distance + lower_distance).clip(0, 1)
            return pd.Series(strength, index=df.index)
        except:
            return pd.Series(0, index=df.index)


class ImprovedOBVIndicator:
    """
    改进的OBV指标计算器

    考虑价格变化幅度的能量潮指标
    """

    def __init__(self, volume_weight: float = 1.0, price_weight: float = 0.5):
        """
        初始化改进的OBV指标

        Args:
            volume_weight: 成交量权重
            price_weight: 价格变化权重
        """
        self.volume_weight = volume_weight
        self.price_weight = price_weight

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算改进的OBV

        Args:
            data: 包含OHLCV的DataFrame

        Returns:
            包含改进OBV指标的DataFrame
        """
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()

        try:
            # 计算价格变化
            price_change = df['Close'].diff()
            price_change_pct = (price_change / df['Close'].shift(1)) * 100

            # 计算OBV
            obv = np.zeros(len(df))
            obv[0] = df['Volume'].iloc[0]

            for i in range(1, len(df)):
                if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                    # 价格上涨
                    obv[i] = obv[i-1] + (df['Volume'].iloc[i] * self.volume_weight *
                                         (1 + self.price_weight * abs(price_change_pct.iloc[i]) / 100))
                elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                    # 价格下跌
                    obv[i] = obv[i-1] - (df['Volume'].iloc[i] * self.volume_weight *
                                         (1 + self.price_weight * abs(price_change_pct.iloc[i]) / 100))
                else:
                    # 价格不变
                    obv[i] = obv[i-1]

            df['OBV_Improved'] = obv

            # OBV移动平均
            df['OBV_Improved_MA'] = df['OBV_Improved'].rolling(window=20).mean()
            df['OBV_Improved_EMA'] = df['OBV_Improved'].ewm(span=20, adjust=False).mean()

            # OBV趋势
            df['OBV_Improved_Trend'] = np.where(
                df['OBV_Improved'] > df['OBV_Improved_MA'], 1,
                np.where(df['OBV_Improved'] < df['OBV_Improved_MA'], -1, 0)
            )

            # 背离信号
            df['OBV_Improved_Divergence'] = self._calculate_divergence(df)

            # 交易信号
            df['OBV_Improved_Signal'] = self._calculate_signals(df)

            # 信号强度
            df['OBV_Improved_Strength'] = self._calculate_strength(df)

            logger.info("改进的OBV计算完成")

        except Exception as e:
            logger.error(f"改进的OBV计算错误: {e}")

        return df

    def _calculate_divergence(self, df: pd.DataFrame, lookback: int = 50) -> pd.Series:
        """计算背离信号"""
        try:
            signal = np.zeros(len(df))

            for i in range(lookback, len(df)):
                # 获取窗口数据
                price_window = df['Close'].iloc[i-lookback:i+1]
                obv_window = df['OBV_Improved'].iloc[i-lookback:i+1]

                price_window = price_window.dropna()
                obv_window = obv_window.dropna()

                if len(price_window) < 10 or len(obv_window) < 10:
                    continue

                # 寻找极值
                price_peak_idx = price_window.idxmax()
                price_trough_idx = price_window.idxmin()
                obv_peak_idx = obv_window.idxmax()
                obv_trough_idx = obv_window.idxmin()

                # 看涨背离
                if (price_trough_idx == price_window.index[-1] and
                    obv_trough_idx != obv_window.index[-1]):
                    signal[i] = 1

                # 看跌背离
                elif (price_peak_idx == price_window.index[-1] and
                      obv_peak_idx != obv_window.index[-1]):
                    signal[i] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_signals(self, df: pd.DataFrame) -> pd.Series:
        """计算交易信号"""
        try:
            signal = np.zeros(len(df))

            # OBV向上穿越移动平均
            obv_cross_up = (
                (df['OBV_Improved'] > df['OBV_Improved_MA']) &
                (df['OBV_Improved'].shift(1) <= df['OBV_Improved_MA'].shift(1))
            )
            signal[obv_cross_up] = 1

            # OBV向下穿越移动平均
            obv_cross_down = (
                (df['OBV_Improved'] < df['OBV_Improved_MA']) &
                (df['OBV_Improved'].shift(1) >= df['OBV_Improved_MA'].shift(1))
            )
            signal[obv_cross_down] = -1

            # 背离信号
            signal[df['OBV_Improved_Divergence'] == 1] = 1
            signal[df['OBV_Improved_Divergence'] == -1] = -1

            return pd.Series(signal, index=df.index)
        except:
            return pd.Series(0, index=df.index)

    def _calculate_strength(self, df: pd.DataFrame) -> pd.Series:
        """计算信号强度"""
        try:
            # OBV变化率
            obv_change = df['OBV_Improved'].pct_change().abs() * 100

            # 距离移动平均的距离
            ma_distance = abs(df['OBV_Improved'] - df['OBV_Improved_MA']) / df['OBV_Improved_MA'] * 100

            strength = (obv_change * 0.3 + ma_distance * 0.7).clip(0, 1)
            return strength
        except:
            return pd.Series(0, index=df.index)


# 便捷函数
def calculate_williams_r(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """快速计算Williams %R"""
    indicator = WilliamsRIndicator(period)
    return indicator.calculate(data)


def calculate_stochastic_rsi(data: pd.DataFrame, rsi_period: int = 14, stoch_period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
    """快速计算Stochastic RSI"""
    indicator = StochasticRSIIndicator(rsi_period, stoch_period, smooth_k, smooth_d)
    return indicator.calculate(data)


def calculate_optimized_adx(data: pd.DataFrame, period: int = 14, adx_threshold: int = 25) -> pd.DataFrame:
    """快速计算优化的ADX"""
    indicator = OptimizedADXIndicator(period, adx_threshold)
    return indicator.calculate(data)


def calculate_atr_bands(data: pd.DataFrame, period: int = 14, multiplier: float = 2.0) -> pd.DataFrame:
    """快速计算ATR带"""
    indicator = ATRBandsIndicator(period, multiplier)
    return indicator.calculate(data)


def calculate_improved_obv(data: pd.DataFrame, volume_weight: float = 1.0, price_weight: float = 0.5) -> pd.DataFrame:
    """快速计算改进的OBV"""
    indicator = ImprovedOBVIndicator(volume_weight, price_weight)
    return indicator.calculate(data)
