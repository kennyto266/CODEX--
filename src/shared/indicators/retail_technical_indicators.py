"""
T064: 零售数据技术指标计算

为零售销售数据计算12个技术指标，用于生成交易信号

技术指标列表:
1. MA (Moving Average) - 移动平均
2. RSI (Relative Strength Index) - 相对强度指数
3. MACD (Moving Average Convergence Divergence) - 指数平滑异同移动平均
4. BB (Bollinger Bands) - 布林带
5. KDJ - 随机指标
6. CCI (Commodity Channel Index) - 商品通道指数
7. ADX (Average Directional Index) - 平均趋向指数
8. ATR (Average True Range) - 平均真实波幅
9. OBV (On-Balance Volume) - 能量潮
10. Ichimoku (Ichimoku Cloud) - 一目均衡表
11. Parabolic SAR - 抛物线转向指标
12. Williams %R - 威廉指标

支持的数据指标:
- retail_total_sales
- retail_clothing
- retail_supermarket
- retail_restaurants
- retail_electronics
- retail_yoy_growth

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

# 导入基础技术指标
from ..strategy.indicators.advanced_indicators import (
    WilliamsRIndicator,
    StochasticRSIIndicator
)


class RetailTechnicalIndicators:
    """
    零售数据技术指标计算器

    为零售销售数据计算12个技术指标并生成交易信号
    """

    def __init__(self):
        """初始化技术指标计算器"""
        self.logger = logging.getLogger("hk_quant_system.retail_indicators")
        self.williams_r = WilliamsRIndicator()
        self.stoch_rsi = StochasticRSIIndicator()

    def calculate_all_indicators(
        self,
        data: pd.DataFrame,
        indicator: str = "retail_total_sales"
    ) -> pd.DataFrame:
        """
        计算所有12个技术指标

        Args:
            data: 包含日期和数值的DataFrame
            indicator: 指标类型

        Returns:
            包含所有技术指标的DataFrame
        """
        if data is None or data.empty:
            self.logger.error("Empty data provided")
            return pd.DataFrame()

        df = data.copy()

        # 确保有正确的列
        if 'date' not in df.columns or 'value' not in df.columns:
            self.logger.error("Data must contain 'date' and 'value' columns")
            return pd.DataFrame()

        # 设置日期为索引
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        try:
            # 1. 移动平均 (MA)
            df = self._calculate_moving_averages(df)

            # 2. 相对强度指数 (RSI)
            df = self._calculate_rsi(df)

            # 3. MACD
            df = self._calculate_macd(df)

            # 4. 布林带 (BB)
            df = self._calculate_bollinger_bands(df)

            # 5. KDJ
            df = self._calculate_kdj(df)

            # 6. CCI
            df = self._calculate_cci(df)

            # 7. ADX
            df = self._calculate_adx(df)

            # 8. ATR
            df = self._calculate_atr(df)

            # 9. OBV
            df = self._calculate_obv(df)

            # 10. Ichimoku
            df = self._calculate_ichimoku(df)

            # 11. Parabolic SAR
            df = self._calculate_sar(df)

            # 12. Williams %R
            df = self._calculate_williams_r(df)

            # 计算交易信号
            df = self._calculate_signals(df)

            self.logger.info(f"Calculated 12 technical indicators for {indicator}")

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")

        return df

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算移动平均线"""
        # 简单移动平均
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'MA_{period}'] = df['value'].rolling(window=period).mean()

        # 指数移动平均
        df['EMA_12'] = df['value'].ewm(span=12).mean()
        df['EMA_26'] = df['value'].ewm(span=26).mean()

        return df

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        delta = df['value'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # RSI信号
        df['RSI_Oversold'] = df['RSI'] < 30
        df['RSI_Overbought'] = df['RSI'] > 70

        return df

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        # MACD线 = EMA12 - EMA26
        df['MACD'] = df['EMA_12'] - df['EMA_26']

        # Signal线 = MACD的EMA9
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()

        # MACD柱状图
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # MACD信号
        df['MACD_Bullish'] = (df['MACD'] > df['MACD_Signal']) & \
                             (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        df['MACD_Bearish'] = (df['MACD'] < df['MACD_Signal']) & \
                             (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))

        return df

    def _calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2
    ) -> pd.DataFrame:
        """计算布林带"""
        df['BB_Middle'] = df['value'].rolling(window=period).mean()
        bb_std = df['value'].rolling(window=period).std()

        df['BB_Upper'] = df['BB_Middle'] + (bb_std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * std_dev)

        # 带宽
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100

        # %B指标
        df['BB_PercentB'] = ((df['value'] - df['BB_Lower']) / \
                             (df['BB_Upper'] - df['BB_Lower'])) * 100

        # 布林带信号
        df['BB_Buy'] = (df['value'] <= df['BB_Lower']) | \
                       (df['BB_PercentB'] < 10)
        df['BB_Sell'] = (df['value'] >= df['BB_Upper']) | \
                        (df['BB_PercentB'] > 90)

        return df

    def _calculate_kdj(
        self,
        df: pd.DataFrame,
        k_period: int = 9,
        d_period: int = 3,
        oversold: int = 20,
        overbought: int = 80
    ) -> pd.DataFrame:
        """计算KDJ指标"""
        low_min = df['value'].rolling(window=k_period).min()
        high_max = df['value'].rolling(window=k_period).max()

        # RSV = (C - Ln) / (Hn - Ln) * 100
        df['KDJ_RSV'] = ((df['value'] - low_min) / (high_max - low_min)) * 100

        # K = RSV的移动平均
        df['KDJ_K'] = df['KDJ_RSV'].ewm(alpha=1/d_period).mean()

        # D = K的移动平均
        df['KDJ_D'] = df['KDJ_K'].ewm(alpha=1/d_period).mean()

        # J = 3K - 2D
        df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']

        # KDJ信号
        df['KDJ_Oversold'] = df['KDJ_K'] < oversold
        df['KDJ_Overbought'] = df['KDJ_K'] > overbought

        # 金叉死叉
        df['KDJ_Golden_Cross'] = (df['KDJ_K'] > df['KDJ_D']) & \
                                 (df['KDJ_K'].shift(1) <= df['KDJ_D'].shift(1))
        df['KDJ_Death_Cross'] = (df['KDJ_K'] < df['KDJ_D']) & \
                                (df['KDJ_K'].shift(1) >= df['KDJ_D'].shift(1))

        return df

    def _calculate_cci(
        self,
        df: pd.DataFrame,
        period: int = 20
    ) -> pd.DataFrame:
        """计算CCI指标"""
        # 典型价格
        df['TP'] = df['value']  # 使用收盘价作为典型价格

        # 移动平均
        df['TP_MA'] = df['TP'].rolling(window=period).mean()

        # 平均绝对偏差
        df['CCI_MAD'] = df['TP'].rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )

        # CCI
        df['CCI'] = (df['TP'] - df['TP_MA']) / (0.015 * df['CCI_MAD'])

        # CCI信号
        df['CCI_Oversold'] = df['CCI'] < -100
        df['CCI_Overbought'] = df['CCI'] > 100

        return df

    def _calculate_adx(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """计算ADX指标"""
        # 价格变化
        high_diff = df['value'].diff()
        low_diff = df['value'].diff().shift(-1)

        # +DM和-DM
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        # 平滑
        plus_dm = pd.Series(plus_dm, index=df.index).rolling(window=period).mean()
        minus_dm = pd.Series(minus_dm, index=df.index).rolling(window=period).mean()

        # True Range (简化)
        tr = df['value'].rolling(window=period).max() - df['value'].rolling(window=period).min()
        tr = tr.rolling(window=period).mean()

        # +DI和-DI
        df['ADX_PLUS_DI'] = (plus_dm / tr) * 100
        df['ADX_MINUS_DI'] = (minus_dm / tr) * 100

        # ADX
        dx = np.abs(df['ADX_PLUS_DI'] - df['ADX_MINUS_DI']) / \
             (df['ADX_PLUS_DI'] + df['ADX_MINUS_DI']) * 100
        df['ADX'] = pd.Series(dx, index=df.index).rolling(window=period).mean()

        # ADX信号
        df['ADX_Strong_Trend'] = df['ADX'] > 25
        df['ADX_Buy'] = (df['ADX_PLUS_DI'] > df['ADX_MINUS_DI']) & \
                        (df['ADX_Strength'] > 25)
        df['ADX_Sell'] = (df['ADX_MINUS_DI'] > df['ADX_PLUS_DI']) & \
                         (df['ADX_Strength'] > 25)

        return df

    def _calculate_atr(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """计算ATR指标"""
        # 真实波幅 (简化版)
        high_low = df['value'].max() - df['value'].min()
        high_close = np.abs(df['value'].max() - df['value'].shift(1))
        low_close = np.abs(df['value'].min() - df['value'].shift(1))

        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        df['ATR'] = pd.Series(tr, index=df.index).rolling(window=period).mean()

        # ATR信号
        df['ATR_High'] = df['ATR'] > df['ATR'].rolling(window=period*2).mean()
        df['ATR_Low'] = df['ATR'] < df['ATR'].rolling(window=period*2).mean()

        return df

    def _calculate_obv(
        self,
        df: pd.DataFrame,
        period: int = 20
    ) -> pd.DataFrame:
        """计算OBV指标"""
        # OBV = OBV(前一日) + 成交量
        # 由于零售数据没有成交量，我们使用价格变化作为近似
        price_change = df['value'].diff()
        obv = np.where(price_change > 0, df['value'],
                      np.where(price_change < 0, -df['value'], 0))
        df['OBV'] = pd.Series(obv, index=df.index).cumsum()

        # OBV移动平均
        df['OBV_MA'] = df['OBV'].rolling(window=period).mean()

        # OBV信号
        df['OBV_Bullish'] = df['OBV'] > df['OBV_MA']
        df['OBV_Bearish'] = df['OBV'] < df['OBV_MA']

        return df

    def _calculate_ichimoku(
        self,
        df: pd.DataFrame,
        conversion: int = 9,
        base: int = 26,
        lagging: int = 52
    ) -> pd.DataFrame:
        """计算一目均衡表"""
        # 转换线
        df['ICHIMOKU_Conversion'] = (df['value'].rolling(window=conversion).max() +
                                     df['value'].rolling(window=conversion).min()) / 2

        # 基准线
        df['ICHIMOKU_Base'] = (df['value'].rolling(window=base).max() +
                               df['value'].rolling(window=base).min()) / 2

        # 先行带
        df['ICHIMOKU_SpanA'] = ((df['ICHIMOKU_Conversion'] + df['ICHIMOKU_Base']) / 2).shift(base)
        high_span = pd.concat([
            df['value'].rolling(window=lagging).max(),
            df['ICHIMOKU_Conversion'].rolling(window=lagging).max()
        ], axis=1).max(axis=1)
        low_span = pd.concat([
            df['value'].rolling(window=lagging).min(),
            df['ICHIMOKU_Conversion'].rolling(window=lagging).min()
        ], axis=1).min(axis=1)
        df['ICHIMOKU_SpanB'] = ((high_span + low_span) / 2).shift(base)

        # 滞行线
        df['ICHIMOKU_Lagging'] = df['value'].shift(-base)

        # 一目均衡表信号
        df['ICHIMOKU_Cloud_Above'] = df['value'] > df['ICHIMOKU_SpanA']
        df['ICHIMOKU_Cloud_Below'] = df['value'] < df['ICHIMOKU_SpanB']

        return df

    def _calculate_sar(
        self,
        df: pd.DataFrame,
        acceleration: float = 0.02,
        maximum: float = 0.2
    ) -> pd.DataFrame:
        """计算抛物线SAR"""
        # 初始化
        df['SAR'] = 0.0
        df['SAR_EP'] = 0.0  # 极端价格
        df['SAR_Trend'] = 1  # 1为上升，-1为下降

        # 计算SAR
        for i in range(1, len(df)):
            if df['SAR_Trend'].iloc[i-1] == 1:  # 上升趋势
                df.loc[df.index[i], 'SAR'] = df['SAR_EP'].iloc[i-1]
                if df['value'].iloc[i] > df['SAR_EP'].iloc[i-1]:
                    df.loc[df.index[i], 'SAR_EP'] = df['value'].iloc[i]
                    af = min(acceleration * (i // 10 + 1), maximum)
                else:
                    df.loc[df.index[i], 'SAR_Trend'] = -1
                    df.loc[df.index[i], 'SAR_EP'] = df['value'].iloc[i-1]
            else:  # 下降趋势
                df.loc[df.index[i], 'SAR'] = df['SAR_EP'].iloc[i-1]
                if df['value'].iloc[i] < df['SAR_EP'].iloc[i-1]:
                    df.loc[df.index[i], 'SAR_EP'] = df['value'].iloc[i]
                else:
                    df.loc[df.index[i], 'SAR_Trend'] = 1
                    df.loc[df.index[i], 'SAR_EP'] = df['value'].iloc[i-1]

        # SAR信号
        df['SAR_Buy'] = (df['value'] > df['SAR']) & (df['value'].shift(1) <= df['SAR'].shift(1))
        df['SAR_Sell'] = (df['value'] < df['SAR']) & (df['value'].shift(1) >= df['SAR'].shift(1))

        return df

    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算Williams %R指标"""
        highest_high = df['value'].rolling(window=period).max()
        lowest_low = df['value'].rolling(window=period).min()

        df['WilliamsR'] = ((highest_high - df['value']) / (highest_high - lowest_low)) * -100

        # Williams %R信号
        df['WilliamsR_Oversold'] = df['WilliamsR'] < -80
        df['WilliamsR_Overbought'] = df['WilliamsR'] > -20

        return df

    def _calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """综合计算交易信号"""
        buy_signals = 0
        sell_signals = 0

        # 统计买入信号
        buy_conditions = [
            df.get('RSI_Oversold', pd.Series(False, index=df.index)),
            df.get('MACD_Bullish', pd.Series(False, index=df.index)),
            df.get('BB_Buy', pd.Series(False, index=df.index)),
            df.get('KDJ_Golden_Cross', pd.Series(False, index=df.index)),
            df.get('CCI_Oversold', pd.Series(False, index=df.index)),
            df.get('OBV_Bullish', pd.Series(False, index=df.index)),
            df.get('SAR_Buy', pd.Series(False, index=df.index)),
            df.get('WilliamsR_Oversold', pd.Series(False, index=df.index))
        ]

        for condition in buy_conditions:
            if isinstance(condition, pd.Series):
                buy_signals += condition.astype(int)

        # 统计卖出信号
        sell_conditions = [
            df.get('RSI_Overbought', pd.Series(False, index=df.index)),
            df.get('MACD_Bearish', pd.Series(False, index=df.index)),
            df.get('BB_Sell', pd.Series(False, index=df.index)),
            df.get('KDJ_Death_Cross', pd.Series(False, index=df.index)),
            df.get('CCI_Overbought', pd.Series(False, index=df.index)),
            df.get('OBV_Bearish', pd.Series(False, index=df.index)),
            df.get('SAR_Sell', pd.Series(False, index=df.index)),
            df.get('WilliamsR_Overbought', pd.Series(False, index=df.index))
        ]

        for condition in sell_conditions:
            if isinstance(condition, pd.Series):
                sell_signals += condition.astype(int)

        df['Buy_Signals'] = buy_signals
        df['Sell_Signals'] = sell_signals

        # 最终交易信号
        df['Signal'] = np.where(
            df['Buy_Signals'] >= 3, 1,
            np.where(df['Sell_Signals'] >= 3, -1, 0)
        )

        return df

    def get_indicator_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取技术指标摘要

        Args:
            df: 包含技术指标的DataFrame

        Returns:
            指标摘要字典
        """
        if df.empty:
            return {}

        summary = {
            'total_records': len(df),
            'indicators_calculated': [
                'MA', 'RSI', 'MACD', 'BB', 'KDJ', 'CCI',
                'ADX', 'ATR', 'OBV', 'Ichimoku', 'SAR', 'WilliamsR'
            ],
            'buy_signals': int(df['Buy_Signals'].sum()),
            'sell_signals': int(df['Sell_Signals'].sum()),
            'net_signals': int((df['Buy_Signals'] - df['Sell_Signals']).sum())
        }

        # 添加当前指标值
        current_values = {
            'RSI': df['RSI'].iloc[-1] if 'RSI' in df else None,
            'MACD': df['MACD'].iloc[-1] if 'MACD' in df else None,
            'ADX': df['ADX'].iloc[-1] if 'ADX' in df else None,
            'ATR': df['ATR'].iloc[-1] if 'ATR' in df else None
        }

        # 过滤None值
        current_values = {k: v for k, v in current_values.items() if v is not None}
        summary['current_values'] = current_values

        return summary
