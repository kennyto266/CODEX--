"""
Trade Data Technical Indicators

计算贸易数据的12种技术指标并生成交易信号
包括：MA, RSI, MACD, BB, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import logging
from datetime import date
from typing import Dict, List, Optional, Tuple, Any
import warnings

import numpy as np
import pandas as pd

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning)


class TradeTechnicalIndicators:
    """
    贸易数据技术指标计算器

    支持12种技术指标的计算和交易信号生成
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.logger = logging.getLogger("hk_quant_system.trade_indicators")

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'sma_periods': [10, 20, 50, 100, 200],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2,
            'kdj_k_period': 9,
            'kdj_d_period': 3,
            'kdj_oversold': 20,
            'kdj_overbought': 80,
            'cci_period': 20,
            'cci_constant': 0.015,
            'adx_period': 14,
            'atr_period': 14,
            'ichimoku_tenkan': 9,
            'ichimoku_kijun': 26,
            'ichimoku_senkou_b': 52,
            'sar_initial': 0.02,
            'sar_max': 0.2,
            'sar_increment': 0.02
        }

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有12种技术指标

        Args:
            df: 包含'date'和'value'列的DataFrame

        Returns:
            包含所有指标的数据框
        """
        if df.empty or 'value' not in df.columns:
            self.logger.error("Invalid DataFrame: missing 'value' column or empty")
            return df.copy()

        # 确保按日期排序
        df = df.sort_values('date').reset_index(drop=True)

        try:
            # 1. 简单移动平均 (SMA)
            for period in self.config['sma_periods']:
                df[f'sma_{period}'] = self._calculate_sma(df['value'], period)

            # 2. 指数移动平均 (EMA)
            for period in self.config['ema_periods']:
                df[f'ema_{period}'] = self._calculate_ema(df['value'], period)

            # 3. 相对强弱指数 (RSI)
            df['rsi'] = self._calculate_rsi(
                df['value'],
                self.config['rsi_period']
            )

            # 4. MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(
                df['value'],
                self.config['macd_fast'],
                self.config['macd_slow'],
                self.config['macd_signal']
            )

            # 5. 布林带 (Bollinger Bands)
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(
                df['value'],
                self.config['bb_period'],
                self.config['bb_std']
            )

            # 6. KDJ指标
            df['k'], df['d'], df['j'] = self._calculate_kdj(
                df['value'],
                self.config['kdj_k_period'],
                self.config['kdj_d_period']
            )

            # 7. CCI商品通道指数
            df['cci'] = self._calculate_cci(
                df['value'],
                self.config['cci_period'],
                self.config['cci_constant']
            )

            # 8. ADX趋向指标
            df['adx'], df['plus_di'], df['minus_di'] = self._calculate_adx(
                df['value'],
                self.config['adx_period']
            )

            # 9. ATR平均真实波幅
            df['atr'] = self._calculate_atr(df['value'], self.config['atr_period'])

            # 10. OBV量价平衡 (使用价格变化代替成交量)
            df['obv'] = self._calculate_obv(df['value'])

            # 11. Ichimoku一目均衡表
            (
                df['ichimoku_tenkan'],
                df['ichimoku_kijun'],
                df['ichimoku_senkou_a'],
                df['ichimoku_senkou_b'],
                df['ichimoku_cloud']
            ) = self._calculate_ichimoku(
                df['value'],
                self.config['ichimoku_tenkan'],
                self.config['ichimoku_kijun'],
                self.config['ichimoku_senkou_b']
            )

            # 12. Parabolic SAR
            df['sar'] = self._calculate_sar(
                df['value'],
                self.config['sar_initial'],
                self.config['sar_max'],
                self.config['sar_increment']
            )

            self.logger.info("All 12 technical indicators calculated successfully")
            return df

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return df

    def _calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均"""
        return series.rolling(window=period).mean()

    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均"""
        return series.ewm(span=period, adjust=False).mean()

    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """计算RSI"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(
        self,
        series: pd.Series,
        fast: int,
        slow: int,
        signal: int
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD"""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(
        self,
        series: pd.Series,
        period: int,
        std_dev: float
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def _calculate_kdj(
        self,
        series: pd.Series,
        k_period: int,
        d_period: int
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ指标"""
        low_min = series.rolling(window=k_period).min()
        high_max = series.rolling(window=k_period).max()
        rsv = (series - low_min) / (high_max - low_min) * 100

        k = rsv.ewm(com=d_period - 1, adjust=False).mean()
        d = k.ewm(com=d_period - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        return k, d, j

    def _calculate_cci(
        self,
        series: pd.Series,
        period: int,
        constant: float
    ) -> pd.Series:
        """计算CCI指标"""
        typical_price = series  # 简化：使用收盘价
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - np.mean(x)))
        )
        cci = (typical_price - sma) / (constant * mean_deviation)
        return cci

    def _calculate_adx(
        self,
        series: pd.Series,
        period: int
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算ADX指标"""
        high = series
        low = series
        close = series

        # True Range (简化版本)
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)

        # Directional Movement
        plus_dm = (high - high.shift()).where(
            (high - high.shift()) > (low.shift() - low),
            0
        )
        minus_dm = (low.shift() - low).where(
            (low.shift() - low) > (high - high.shift()),
            0
        )

        # Smoothed values
        tr_smooth = tr.rolling(window=period).mean()
        plus_dm_smooth = plus_dm.rolling(window=period).mean()
        minus_dm_smooth = minus_dm.rolling(window=period).mean()

        # DI values
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)

        # ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx, plus_di, minus_di

    def _calculate_atr(self, series: pd.Series, period: int) -> pd.Series:
        """计算ATR"""
        high = series
        low = series
        close = series

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)

        return tr.rolling(window=period).mean()

    def _calculate_obv(self, series: pd.Series) -> pd.Series:
        """计算OBV（使用价格变化代替成交量）"""
        obv = np.zeros(len(series))
        obv[0] = series.iloc[0]

        for i in range(1, len(series)):
            if series.iloc[i] > series.iloc[i - 1]:
                obv[i] = obv[i - 1] + series.iloc[i]
            elif series.iloc[i] < series.iloc[i - 1]:
                obv[i] = obv[i - 1] - series.iloc[i]
            else:
                obv[i] = obv[i - 1]

        return pd.Series(obv, index=series.index)

    def _calculate_ichimoku(
        self,
        series: pd.Series,
        tenkan: int,
        kijun: int,
        senkou_b: int
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """计算Ichimoku指标"""
        high = series
        low = series

        # Tenkan-sen
        tenkan_sen = (high.rolling(window=tenkan).max() + low.rolling(window=tenkan).min()) / 2

        # Kijun-sen
        kijun_sen = (high.rolling(window=kijun).max() + low.rolling(window=kijun).min()) / 2

        # Senkou Span A
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)

        # Senkou Span B
        senkou_span_b = ((high.rolling(window=senkou_b).max() + low.rolling(window=senkou_b).min()) / 2).shift(kijun)

        # Cloud
        cloud = senkou_span_a - senkou_span_b

        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, cloud

    def _calculate_sar(
        self,
        series: pd.Series,
        initial: float,
        max_val: float,
        increment: float
    ) -> pd.Series:
        """计算Parabolic SAR"""
        sar = np.zeros(len(series))
        sar[0] = series.iloc[0] * 0.98  # 初始值略低于起始价格

        af = initial
        trend = 1  # 1 for uptrend, -1 for downtrend
        ep = series.iloc[0]  # Extreme point

        for i in range(1, len(series)):
            if trend == 1:  # Uptrend
                sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
                if series.iloc[i] < sar[i]:  # Trend reversal
                    trend = -1
                    af = initial
                    ep = series.iloc[i]
                    sar[i] = ep
                else:
                    if series.iloc[i] > ep:
                        ep = series.iloc[i]
                        af = min(af + increment, max_val)
            else:  # Downtrend
                sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
                if series.iloc[i] > sar[i]:  # Trend reversal
                    trend = 1
                    af = initial
                    ep = series.iloc[i]
                    sar[i] = ep
                else:
                    if series.iloc[i] < ep:
                        ep = series.iloc[i]
                        af = min(af + increment, max_val)

        return pd.Series(sar, index=series.index)

    def generate_signals(
        self,
        df: pd.DataFrame,
        indicator_type: str = 'all',
        buy_threshold: float = 30,
        sell_threshold: float = 70
    ) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            df: 包含技术指标的数据框
            indicator_type: 指标类型 ('all', 'rsi', 'kdj', 'macd', 'bb', 'sma', 'cci', 'adx', 'atr', 'obv', 'ichimoku', 'sar')
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值

        Returns:
            包含交易信号的数据框
        """
        if df.empty:
            return df.copy()

        signals_df = df.copy()
        signals_df['signal'] = 0  # 0=hold, 1=buy, -1=sell

        try:
            if indicator_type == 'all' or indicator_type == 'rsi':
                # RSI信号
                if 'rsi' in df.columns:
                    signals_df.loc[df['rsi'] < buy_threshold, 'signal'] = 1
                    signals_df.loc[df['rsi'] > sell_threshold, 'signal'] = -1

            if indicator_type == 'all' or indicator_type == 'kdj':
                # KDJ信号
                if 'k' in df.columns and 'd' in df.columns:
                    signals_df.loc[
                        (df['k'] > df['d']) & (df['k'] < self.config['kdj_oversold']), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['k'] < df['d']) & (df['k'] > self.config['kdj_overbought']), 'signal'
                    ] = -1

            if indicator_type == 'all' or indicator_type == 'macd':
                # MACD信号
                if 'macd' in df.columns and 'macd_signal' in df.columns:
                    signals_df.loc[
                        (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'
                    ] = -1

            if indicator_type == 'all' or indicator_type == 'bb':
                # 布林带信号
                if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                    signals_df.loc[df['value'] < df['bb_lower'], 'signal'] = 1
                    signals_df.loc[df['value'] > df['bb_upper'], 'signal'] = -1

            if indicator_type == 'all' or indicator_type == 'sma':
                # SMA金叉/死叉信号
                if 'sma_20' in df.columns and 'sma_50' in df.columns:
                    signals_df.loc[
                        (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1)), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1)), 'signal'
                    ] = -1

            if indicator_type == 'all' or indicator_type == 'cci':
                # CCI信号
                if 'cci' in df.columns:
                    signals_df.loc[df['cci'] < -100, 'signal'] = 1
                    signals_df.loc[df['cci'] > 100, 'signal'] = -1

            if indicator_type == 'all' or indicator_type == 'adx':
                # ADX信号
                if 'adx' in df.columns and 'plus_di' in df.columns and 'minus_di' in df.columns:
                    signals_df.loc[
                        (df['adx'] > 25) & (df['plus_di'] > df['minus_di']), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['adx'] > 25) & (df['plus_di'] < df['minus_di']), 'signal'
                    ] = -1

            if indicator_type == 'all' or indicator_type == 'ichimoku':
                # Ichimoku信号
                if all(col in df.columns for col in ['ichimoku_tenkan', 'ichimoku_kijun', 'ichimoku_cloud']):
                    signals_df.loc[
                        (df['ichimoku_tenkan'] > df['ichimoku_kijun']) & (df['value'] > df['ichimoku_cloud']), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['ichimoku_tenkan'] < df['ichimoku_kijun']) & (df['value'] < df['ichimoku_cloud']), 'signal'
                    ] = -1

            if indicator_type == 'all' or indicator_type == 'sar':
                # SAR信号
                if 'sar' in df.columns:
                    signals_df.loc[
                        (df['value'] > df['sar']) & (df['value'].shift(1) <= df['sar'].shift(1)), 'signal'
                    ] = 1
                    signals_df.loc[
                        (df['value'] < df['sar']) & (df['value'].shift(1) >= df['sar'].shift(1)), 'signal'
                    ] = -1

            # 计算信号强度
            signals_df['signal_strength'] = signals_df['signal'].abs()

            self.logger.info(f"Generated signals using {indicator_type} indicator")
            return signals_df

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return signals_df

    def get_signal_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取信号摘要统计

        Args:
            df: 包含信号的数据框

        Returns:
            信号摘要字典
        """
        if 'signal' not in df.columns:
            return {}

        buy_signals = len(df[df['signal'] == 1])
        sell_signals = len(df[df['signal'] == -1])
        hold_signals = len(df[df['signal'] == 0])
        total_signals = len(df[df['signal'] != 0])

        return {
            'total_records': len(df),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'total_trades': total_signals,
            'buy_ratio': buy_signals / len(df) if len(df) > 0 else 0,
            'sell_ratio': sell_signals / len(df) if len(df) > 0 else 0,
            'signal_frequency': total_signals / len(df) if len(df) > 0 else 0
        }


# 便捷函数
def calculate_trade_indicators(
    df: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """计算贸易数据技术指标"""
    calculator = TradeTechnicalIndicators(config)
    return calculator.calculate_all_indicators(df)


def generate_trade_signals(
    df: pd.DataFrame,
    indicator_type: str = 'rsi',
    buy_threshold: float = 30,
    sell_threshold: float = 70
) -> pd.DataFrame:
    """生成贸易数据交易信号"""
    calculator = TradeTechnicalIndicators()
    return calculator.generate_signals(df, indicator_type, buy_threshold, sell_threshold)


def analyze_trade_data(
    df: pd.DataFrame,
    indicator_type: str = 'rsi',
    buy_threshold: float = 30,
    sell_threshold: float = 70
) -> Dict[str, Any]:
    """
    分析贸易数据（计算指标+生成信号+统计摘要）

    Args:
        df: 贸易数据框
        indicator_type: 指标类型
        buy_threshold: 买入阈值
        sell_threshold: 卖出阈值

    Returns:
        分析结果字典
    """
    calculator = TradeTechnicalIndicators()

    # 计算指标
    df_with_indicators = calculator.calculate_all_indicators(df)

    # 生成信号
    df_with_signals = calculator.generate_signals(df_with_indicators, indicator_type, buy_threshold, sell_threshold)

    # 获取摘要
    summary = calculator.get_signal_summary(df_with_signals)

    return {
        'data': df_with_signals,
        'summary': summary,
        'indicators_calculated': [col for col in df_with_indicators.columns if col not in ['date', 'value']],
        'config': calculator.config
    }
