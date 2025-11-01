"""
策略模块 - 提供基础和标准技术分析策略
包含 RSI, MACD, Bollinger Bands 等策略的实现
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, symbol: str = None):
        self.symbol = symbol
        self.signals = None
        self.parameters = {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信号

        Args:
            data: OHLCV DataFrame

        Returns:
            信号Series (1: 买入, -1: 卖出, 0: 无信号)
        """
        pass

    def backtest(self, data: pd.DataFrame) -> dict:
        """基础回测"""
        signals = self.generate_signals(data)
        returns = signals.shift(1) * data['Close'].pct_change()

        return {
            'signals': signals,
            'returns': returns,
            'total_return': (1 + returns).cumprod().iloc[-1] - 1 if len(returns) > 0 else 0,
            'sharpe_ratio': self._calculate_sharpe(returns),
            'max_drawdown': self._calculate_max_drawdown(returns)
        }

    @staticmethod
    def _calculate_sharpe(returns: pd.Series, rf_rate: float = 0.0) -> float:
        """计算夏普比率"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns - rf_rate / 252
        return (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))

    @staticmethod
    def _calculate_max_drawdown(returns: pd.Series) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        return abs(drawdown.min())


class RSIStrategy(BaseStrategy):
    """
    相对强弱指数 (RSI) 策略

    参数:
        period: RSI周期 (默认14)
        overbought: 超买阈值 (默认70)
        oversold: 超卖阈值 (默认30)
    """

    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30, symbol: str = None):
        super().__init__(symbol)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.parameters = {
            'period': period,
            'overbought': overbought,
            'oversold': oversold
        }

    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        # 避免除以零
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        基于RSI生成交易信号

        - RSI < oversold: 买入信号 (1)
        - RSI > overbought: 卖出信号 (-1)
        - 其他: 无信号 (0)
        """
        if 'Close' not in data.columns and 'close' not in data.columns:
            return pd.Series(0, index=data.index)

        prices = data['Close'] if 'Close' in data.columns else data['close']
        rsi = self._calculate_rsi(prices)

        signals = pd.Series(0, index=data.index, dtype=float)
        signals[rsi < self.oversold] = 1      # 买入
        signals[rsi > self.overbought] = -1   # 卖出

        return signals


class MACDStrategy(BaseStrategy):
    """
    MACD (移动平均线收敛散度) 策略

    参数:
        fast_period: 快速EMA周期 (默认12)
        slow_period: 慢速EMA周期 (默认26)
        signal_period: 信号线周期 (默认9)
    """

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, symbol: str = None):
        super().__init__(symbol)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.parameters = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        }

    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = prices.ewm(span=self.fast_period).mean()
        ema_slow = prices.ewm(span=self.slow_period).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        基于MACD生成交易信号

        - MACD线向上穿过信号线: 买入信号 (1)
        - MACD线向下穿过信号线: 卖出信号 (-1)
        - 其他: 无信号 (0)
        """
        if 'Close' not in data.columns and 'close' not in data.columns:
            return pd.Series(0, index=data.index)

        prices = data['Close'] if 'Close' in data.columns else data['close']
        macd_line, signal_line, histogram = self._calculate_macd(prices)

        signals = pd.Series(0, index=data.index, dtype=float)

        # MACD线穿过信号线
        prev_histogram = histogram.shift(1)

        # 从负变正: 买入
        signals[(prev_histogram <= 0) & (histogram > 0)] = 1

        # 从正变负: 卖出
        signals[(prev_histogram >= 0) & (histogram < 0)] = -1

        return signals


class BollingerStrategy(BaseStrategy):
    """
    布林带 (Bollinger Bands) 策略

    参数:
        period: 移动平均线周期 (默认20)
        std_dev: 标准差倍数 (默认2.0)
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0, symbol: str = None):
        super().__init__(symbol)
        self.period = period
        self.std_dev = std_dev
        self.parameters = {
            'period': period,
            'std_dev': std_dev
        }

    def _calculate_bollinger(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        sma = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()

        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)

        return sma, upper_band, lower_band

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        基于布林带生成交易信号

        - 价格穿过下边界: 买入信号 (1)
        - 价格穿过上边界: 卖出信号 (-1)
        - 其他: 无信号 (0)
        """
        if 'Close' not in data.columns and 'close' not in data.columns:
            return pd.Series(0, index=data.index)

        prices = data['Close'] if 'Close' in data.columns else data['close']
        sma, upper_band, lower_band = self._calculate_bollinger(prices)

        signals = pd.Series(0, index=data.index, dtype=float)

        # 价格与布林带关系
        prev_prices = prices.shift(1)

        # 穿过下边界: 买入
        signals[(prev_prices >= lower_band.shift(1)) & (prices < lower_band)] = 1

        # 穿过上边界: 卖出
        signals[(prev_prices <= upper_band.shift(1)) & (prices > upper_band)] = -1

        return signals


# 导出策略类供外部使用
__all__ = [
    'BaseStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerStrategy'
]
