#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
访客数据技术指标计算
为访客数据计算12种技术指标：RSI, MACD, EMA(12), EMA(26), SMA(20), SMA(50),
Bollinger Bands, Stochastic, CCI, Williams %R, ROC, ADX

Author: Claude Code
Version: 1.0.0
Date: 2025-11-10
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import date

import numpy as np
import pandas as pd
import talib


class VisitorTechnicalIndicators:
    """访客数据技术指标计算器"""

    def __init__(self):
        """初始化指标计算器"""
        self.logger = logging.getLogger(__name__)

    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        indicator: str = 'visitor_total'
    ) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 包含访客数据的DataFrame，必须有'date'和'value'列
            indicator: 指标名称

        Returns:
            DataFrame: 包含所有技术指标的DataFrame
        """
        # 过滤指定指标的数据
        indicator_data = df[df['symbol'] == indicator].copy()
        indicator_data = indicator_data.sort_values('date').reset_index(drop=True)

        if len(indicator_data) < 50:  # 需要至少50个数据点计算所有指标
            self.logger.warning(f"Insufficient data for {indicator}: {len(indicator_data)} points")

        # 重命名列以便计算
        data = indicator_data[['date', 'value']].copy()
        data = data.rename(columns={'value': 'close'})

        # 确保数据是数值类型
        data['close'] = pd.to_numeric(data['close'], errors='coerce')
        data = data.dropna()

        if len(data) < 2:
            self.logger.error("Insufficient data for indicator calculation")
            return pd.DataFrame()

        # 计算所有指标
        result = data.copy()

        # 1. RSI (Relative Strength Index) - 周期14
        result['rsi'] = self._calculate_rsi(data['close'], period=14)

        # 2. MACD (Moving Average Convergence Divergence) - 快线12, 慢线26, 信号线9
        result['macd'], result['macd_signal'], result['macd_hist'] = self._calculate_macd(
            data['close'], fast=12, slow=26, signal=9
        )

        # 3. EMA (Exponential Moving Average) - 12和26
        result['ema_12'] = self._calculate_ema(data['close'], period=12)
        result['ema_26'] = self._calculate_ema(data['close'], period=26)

        # 4. SMA (Simple Moving Average) - 20和50
        result['sma_20'] = self._calculate_sma(data['close'], period=20)
        result['sma_50'] = self._calculate_sma(data['close'], period=50)

        # 5. Bollinger Bands - 周期20, 标准差2
        result['bb_upper'], result['bb_middle'], result['bb_lower'] = self._calculate_bollinger_bands(
            data['close'], period=20, std=2
        )

        # 6. Stochastic Oscillator - K周期14, D周期3
        result['stoch_k'], result['stoch_d'] = self._calculate_stochastic(
            data['close'], k_period=14, d_period=3
        )

        # 7. CCI (Commodity Channel Index) - 周期20
        result['cci'] = self._calculate_cci(data['close'], period=20)

        # 8. Williams %R - 周期14
        result['williams_r'] = self._calculate_williams_r(data['close'], period=14)

        # 9. ROC (Rate of Change) - 周期12
        result['roc'] = self._calculate_roc(data['close'], period=12)

        # 10. ADX (Average Directional Index) - 周期14
        result['adx'], result['adx_pos'], result['adx_neg'] = self._calculate_adx(
            data['close'], period=14
        )

        return result

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        try:
            rsi = talib.RSI(prices.values, timeperiod=period)
            return pd.Series(rsi, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD"""
        try:
            macd, macd_signal, macd_hist = talib.MACD(
                prices.values,
                fastperiod=fast,
                slowperiod=slow,
                signalperiod=signal
            )
            return (
                pd.Series(macd, index=prices.index),
                pd.Series(macd_signal, index=prices.index),
                pd.Series(macd_hist, index=prices.index)
            )
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return (
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index)
            )

    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """计算EMA"""
        try:
            ema = talib.EMA(prices.values, timeperiod=period)
            return pd.Series(ema, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating EMA: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """计算SMA"""
        try:
            sma = talib.SMA(prices.values, timeperiod=period)
            return pd.Series(sma, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating SMA: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std: float = 2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算Bollinger Bands"""
        try:
            upper, middle, lower = talib.BBANDS(
                prices.values,
                timeperiod=period,
                nbdevup=std,
                nbdevdn=std
            )
            return (
                pd.Series(upper, index=prices.index),
                pd.Series(middle, index=prices.index),
                pd.Series(lower, index=prices.index)
            )
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return (
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index)
            )

    def _calculate_stochastic(
        self,
        prices: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """计算Stochastic Oscillator"""
        try:
            # 使用价格序列作为高低价（实际应该使用真实的高低价）
            high = prices
            low = prices
            close = prices

            stoch_k = talib.STOCH(
                high.values,
                low.values,
                close.values,
                fastk_period=k_period,
                slowk_period=d_period
            )[0]

            stoch_d = talib.STOCH(
                high.values,
                low.values,
                close.values,
                fastk_period=k_period,
                slowk_period=d_period
            )[1]

            return (
                pd.Series(stoch_k, index=prices.index),
                pd.Series(stoch_d, index=prices.index)
            )
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic: {e}")
            return (
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index)
            )

    def _calculate_cci(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """计算CCI"""
        try:
            # 使用价格序列作为高低价
            high = prices
            low = prices
            close = prices

            cci = talib.CCI(
                high.values,
                low.values,
                close.values,
                timeperiod=period
            )
            return pd.Series(cci, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating CCI: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_williams_r(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算Williams %R"""
        try:
            # 使用价格序列作为高低价
            high = prices
            low = prices
            close = prices

            williams_r = talib.WILLR(
                high.values,
                low.values,
                close.values,
                timeperiod=period
            )
            return pd.Series(williams_r, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_roc(self, prices: pd.Series, period: int = 12) -> pd.Series:
        """计算ROC (Rate of Change)"""
        try:
            roc = talib.ROC(prices.values, timeperiod=period)
            return pd.Series(roc, index=prices.index)
        except Exception as e:
            self.logger.error(f"Error calculating ROC: {e}")
            return pd.Series(np.nan, index=prices.index)

    def _calculate_adx(self, prices: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算ADX"""
        try:
            # 使用价格序列作为高低价
            high = prices
            low = prices
            close = prices

            adx = talib.ADX(
                high.values,
                low.values,
                close.values,
                timeperiod=period
            )
            adx_pos = talib.PLUS_DI(
                high.values,
                low.values,
                close.values,
                timeperiod=period
            )
            adx_neg = talib.MINUS_DI(
                high.values,
                low.values,
                close.values,
                timeperiod=period
            )
            return (
                pd.Series(adx, index=prices.index),
                pd.Series(adx_pos, index=prices.index),
                pd.Series(adx_neg, index=prices.index)
            )
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return (
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index),
                pd.Series(np.nan, index=prices.index)
            )

    def generate_signals(
        self,
        indicators_df: pd.DataFrame,
        buy_threshold: float = 30,
        sell_threshold: float = 70
    ) -> pd.DataFrame:
        """
        基于技术指标生成交易信号

        Args:
            indicators_df: 包含技术指标的DataFrame
            buy_threshold: 买入阈值（RSI等指标）
            sell_threshold: 卖出阈值

        Returns:
            DataFrame: 包含交易信号的DataFrame
        """
        if len(indicators_df) == 0:
            return indicators_df

        result = indicators_df.copy()
        result['signal'] = 'HOLD'
        result['signal_reason'] = ''

        # 1. 基于RSI的信号
        if 'rsi' in result.columns:
            result.loc[result['rsi'] < buy_threshold, 'signal'] = 'BUY'
            result.loc[result['rsi'] > sell_threshold, 'signal'] = 'SELL'
            result.loc[result['rsi'] < buy_threshold, 'signal_reason'] = 'RSI Oversold'
            result.loc[result['rsi'] > sell_threshold, 'signal_reason'] = 'RSI Overbought'

        # 2. 基于MACD的信号
        if 'macd' in result.columns and 'macd_signal' in result.columns:
            macd_buy = (result['macd'] > result['macd_signal']) & (
                result['macd'].shift(1) <= result['macd_signal'].shift(1)
            )
            macd_sell = (result['macd'] < result['macd_signal']) & (
                result['macd'].shift(1) >= result['macd_signal'].shift(1)
            )

            result.loc[macd_buy, 'signal'] = 'BUY'
            result.loc[macd_sell, 'signal'] = 'SELL'
            result.loc[macd_buy, 'signal_reason'] = 'MACD Bullish Crossover'
            result.loc[macd_sell, 'signal_reason'] = 'MACD Bearish Crossover'

        # 3. 基于Bollinger Bands的信号
        if 'bb_upper' in result.columns and 'bb_lower' in result.columns and 'close' in result.columns:
            bb_buy = result['close'] < result['bb_lower']
            bb_sell = result['close'] > result['bb_upper']

            result.loc[bb_buy, 'signal'] = 'BUY'
            result.loc[bb_sell, 'signal'] = 'SELL'
            result.loc[bb_buy, 'signal_reason'] = 'BB Oversold'
            result.loc[bb_sell, 'signal_reason'] = 'BB Overbought'

        # 4. 基于Stochastic的信号
        if 'stoch_k' in result.columns and 'stoch_d' in result.columns:
            stoch_buy = (result['stoch_k'] < buy_threshold) & (result['stoch_k'] > result['stoch_d'])
            stoch_sell = (result['stoch_k'] > sell_threshold) & (result['stoch_k'] < result['stoch_d'])

            result.loc[stoch_buy, 'signal'] = 'BUY'
            result.loc[stoch_sell, 'signal'] = 'SELL'
            result.loc[stoch_buy, 'signal_reason'] = 'Stochastic Oversold'
            result.loc[stoch_sell, 'signal_reason'] = 'Stochastic Overbought'

        # 5. 基于移动平均线的信号
        if 'ema_12' in result.columns and 'ema_26' in result.columns and 'close' in result.columns:
            golden_cross = (result['ema_12'] > result['ema_26']) & (
                result['ema_12'].shift(1) <= result['ema_26'].shift(1)
            )
            death_cross = (result['ema_12'] < result['ema_26']) & (
                result['ema_12'].shift(1) >= result['ema_26'].shift(1)
            )

            result.loc[golden_cross, 'signal'] = 'BUY'
            result.loc[death_cross, 'signal'] = 'SELL'
            result.loc[golden_cross, 'signal_reason'] = 'EMA Golden Cross'
            result.loc[death_cross, 'signal_reason'] = 'EMA Death Cross'

        return result

    def get_indicator_summary(self, indicators_df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取技术指标摘要

        Args:
            indicators_df: 包含技术指标的DataFrame

        Returns:
            Dict: 指标摘要
        """
        if len(indicators_df) == 0:
            return {}

        summary = {
            'total_records': len(indicators_df),
            'date_range': {
                'start': str(indicators_df['date'].min()),
                'end': str(indicators_df['date'].max())
            },
            'price_statistics': {
                'min': float(indicators_df['close'].min()),
                'max': float(indicators_df['close'].max()),
                'mean': float(indicators_df['close'].mean()),
                'std': float(indicators_df['close'].std())
            },
            'indicators': {}
        }

        # 计算各指标的统计信息
        for col in indicators_df.columns:
            if col not in ['date', 'close', 'signal', 'signal_reason']:
                values = indicators_df[col].dropna()
                if len(values) > 0:
                    summary['indicators'][col] = {
                        'min': float(values.min()),
                        'max': float(values.max()),
                        'mean': float(values.mean()),
                        'std': float(values.std())
                    }

        # 统计交易信号
        if 'signal' in indicators_df.columns:
            signal_counts = indicators_df['signal'].value_counts()
            summary['signal_distribution'] = signal_counts.to_dict()

        return summary

    def export_indicators(self, indicators_df: pd.DataFrame, filename: str) -> bool:
        """
        导出技术指标到CSV文件

        Args:
            indicators_df: 包含技术指标的DataFrame
            filename: 输出文件名

        Returns:
            bool: 是否成功
        """
        try:
            indicators_df.to_csv(filename, index=False)
            self.logger.info(f"Indicators exported to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting indicators: {e}")
            return False


# 便捷函数
def calculate_visitor_indicators(
    df: pd.DataFrame,
    indicator: str = 'visitor_total'
) -> pd.DataFrame:
    """
    计算访客数据技术指标的便捷函数

    Args:
        df: 访客数据DataFrame
        indicator: 指标名称

    Returns:
        DataFrame: 包含技术指标的数据
    """
    calculator = VisitorTechnicalIndicators()
    return calculator.calculate_all_indicators(df, indicator)


def generate_visitor_signals(
    indicators_df: pd.DataFrame,
    buy_threshold: float = 30,
    sell_threshold: float = 70
) -> pd.DataFrame:
    """
    生成访客数据交易信号的便捷函数

    Args:
        indicators_df: 包含技术指标的数据
        buy_threshold: 买入阈值
        sell_threshold: 卖出阈值

    Returns:
        DataFrame: 包含交易信号的数据
    """
    calculator = VisitorTechnicalIndicators()
    return calculator.generate_signals(indicators_df, buy_threshold, sell_threshold)


if __name__ == '__main__':
    # 测试代码
    import asyncio
    from datetime import date, timedelta

    async def test():
        # 创建测试数据
        dates = [date(2020, 1, 1) + timedelta(days=i*30) for i in range(60)]
        values = [500000 + i*1000 + np.sin(i/5)*50000 for i in range(60)]

        data = {
            'symbol': ['visitor_total'] * 60,
            'date': dates,
            'value': values,
            'source': ['test'] * 60
        }
        df = pd.DataFrame(data)

        # 计算技术指标
        calculator = VisitorTechnicalIndicators()
        indicators = calculator.calculate_all_indicators(df, 'visitor_total')

        print("Technical Indicators Calculated:")
        print(f"Shape: {indicators.shape}")
        print(indicators.head())

        # 生成交易信号
        signals = calculator.generate_signals(indicators)
        print("\nTrade Signals:")
        print(signals[['date', 'close', 'rsi', 'signal', 'signal_reason']].head())

        # 导出指标
        calculator.export_indicators(indicators, 'test_indicators.csv')
        print("\nIndicators exported to test_indicators.csv")

    asyncio.run(test())
