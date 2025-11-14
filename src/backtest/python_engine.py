"""
Pure Python Fallback Backtest Engine

Provides identical functionality to Rust engine when PyO3 bindings are unavailable.
High-performance implementation using NumPy and pandas for vectorized operations.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PythonMarketData:
    """
    Pure Python market data container with memory optimization.

    Provides efficient data access and caching for technical indicators.
    """
    symbol: str
    timestamps: List[str]
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    _cached_smas: Dict[int, np.ndarray] = field(default_factory=dict)
    _cached_rsis: Dict[int, np.ndarray] = field(default_factory=dict)
    _cached_emas: Dict[Tuple[int], np.ndarray] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data and convert to optimized numpy arrays"""
        # Convert to numpy arrays with proper dtypes
        self.open = np.array(self.open, dtype=np.float64)
        self.high = np.array(self.high, dtype=np.float64)
        self.low = np.array(self.low, dtype=np.float64)
        self.close = np.array(self.close, dtype=np.float64)
        self.volume = np.array(self.volume, dtype=np.int64)

        # Validate data consistency
        lengths = [
            len(self.timestamps), len(self.open), len(self.high),
            len(self.low), len(self.close), len(self.volume)
        ]
        if len(set(lengths)) != 1:
            raise ValueError(
                f"All arrays must have the same length. Got: {lengths}"
            )

        # Validate OHLC relationships
        for i in range(len(self.close)):
            if self.low[i] > self.high[i]:
                raise ValueError(
                    f"Low price ({self.low[i]}) cannot exceed high price "
                    f"({self.high[i]}) at index {i}"
                )
            if self.open[i] < self.low[i] or self.open[i] > self.high[i]:
                raise ValueError(
                    f"Open price ({self.open[i]}) outside range "
                    f"[{self.low[i]}, {self.high[i]}] at index {i}"
                )
            if self.close[i] < self.low[i] or self.close[i] > self.high[i]:
                raise ValueError(
                    f"Close price ({self.close[i]}) outside range "
                    f"[{self.low[i]}, {self.high[i]}] at index {i}"
                )

        logger.info(f"Initialized PythonMarketData for {self.symbol} "
                   f"with {len(self.close)} data points")

    @classmethod
    def from_pandas(cls, df: pd.DataFrame, symbol: str = "UNKNOWN") -> 'PythonMarketData':
        """
        Create from pandas DataFrame.

        Args:
            df: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            symbol: Stock symbol

        Returns:
            PythonMarketData instance
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index(pd.to_datetime(df['date']))

        return cls(
            symbol=symbol,
            timestamps=df.index.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
            open=df['open'].values,
            high=df['high'].values,
            low=df['low'].values,
            close=df['close'].values,
            volume=df['volume'].values.astype(np.int64)
        )

    @property
    def length(self) -> int:
        """Get data length"""
        return len(self.close)

    def get_price(self, field: str) -> np.ndarray:
        """
        Get price array by field name.

        Args:
            field: Field name (open, high, low, close, volume)

        Returns:
            Numpy array of the requested field
        """
        if field not in ['open', 'high', 'low', 'close', 'volume']:
            raise ValueError(f"Invalid field: {field}")
        return getattr(self, field)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timestamps': self.timestamps,
            'open': self.open.tolist(),
            'high': self.high.tolist(),
            'low': self.low.tolist(),
            'close': self.close.tolist(),
            'volume': self.volume.tolist(),
            'length': self.length
        }


@dataclass
class Trade:
    """Individual trade record"""
    id: int
    entry_time: str
    exit_time: Optional[str]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: Optional[float]
    commission: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'pnl': self.pnl,
            'commission': self.commission
        }


@dataclass
class PythonBacktestResult:
    """Pure Python backtest result matching Rust engine API"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    execution_time_ms: int
    total_trades: int
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching Rust engine output"""
        return {
            'total_return': float(self.total_return),
            'annualized_return': float(self.annualized_return),
            'volatility': float(self.volatility),
            'sharpe_ratio': float(self.sharpe_ratio),
            'max_drawdown': float(self.max_drawdown),
            'win_rate': float(self.win_rate),
            'execution_time_ms': int(self.execution_time_ms),
            'total_trades': int(self.total_trades),
            'trades': [trade.to_dict() for trade in self.trades],
            'equity_curve': [(ts, float(val)) for ts, val in self.equity_curve]
        }


class TechnicalIndicators:
    """
    Pure Python technical indicators implementation.

    Optimized using NumPy vectorized operations and pandas rolling functions.
    All methods return numpy arrays with same length as input.
    """

    @staticmethod
    def sma(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Simple Moving Average

        Args:
            prices: Price array
            period: Moving average period

        Returns:
            SMA values (NaN for insufficient data)
        """
        if period <= 0 or len(prices) < period:
            return np.full(len(prices), np.nan)

        # Use pandas for efficient rolling calculation
        return pd.Series(prices).rolling(window=period, min_periods=1).mean().values

    @staticmethod
    def ema(prices: np.ndarray, period: int) -> np.ndarray:
        """
        Exponential Moving Average

        Args:
            prices: Price array
            period: EMA period

        Returns:
            EMA values
        """
        if period <= 0 or len(prices) == 0:
            return np.full(len(prices), np.nan)

        alpha = 2.0 / (period + 1)
        ema = np.zeros(len(prices))

        # Initialize with first value
        ema[0] = prices[0]

        # Calculate EMA using vectorized operations
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]

        return ema

    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index

        Args:
            prices: Price array
            period: RSI period (default 14)

        Returns:
            RSI values (0-100)
        """
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Use pandas for rolling averages
        avg_gains = pd.Series(gains).rolling(window=period, min_periods=1).mean()
        avg_losses = pd.Series(losses).rolling(window=period, min_periods=1).mean()

        # Calculate RS and RSI
        rs = avg_gains / (avg_losses + 1e-10)  # Add small epsilon to avoid division by zero
        rsi = 100 - (100 / (1 + rs))

        # Prepend NaN for the first value
        return np.concatenate([[np.nan], rsi.values])

    @staticmethod
    def macd(
        prices: np.ndarray,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        MACD (Moving Average Convergence Divergence)

        Args:
            prices: Price array
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)

        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bollinger Bands

        Args:
            prices: Price array
            period: Period for moving average (default 20)
            std_dev: Number of standard deviations (default 2.0)

        Returns:
            Tuple of (Upper band, Middle band (SMA), Lower band)
        """
        if len(prices) < period:
            return (
                np.full(len(prices), np.nan),
                np.full(len(prices), np.nan),
                np.full(len(prices), np.nan)
            )

        sma = TechnicalIndicators.sma(prices, period)
        std = pd.Series(prices).rolling(window=period, min_periods=1).std().values

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, sma, lower_band

    @staticmethod
    def kdj(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        k_period: int = 9,
        d_period: int = 3,
        oversold: float = 20.0,
        overbought: float = 80.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        KDJ Indicator (Stochastic oscillator variant)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: K period (default 9)
            d_period: D period (default 3)
            oversold: Oversold threshold (default 20)
            overbought: Overbought threshold (default 80)

        Returns:
            Tuple of (K values, D values, J values)
        """
        lowest_low = pd.Series(low).rolling(window=k_period, min_periods=1).min()
        highest_high = pd.Series(high).rolling(window=k_period, min_periods=1).max()

        rsv = (close - lowest_low) / (highest_high - lowest_low + 1e-10) * 100
        k = rsv.ewm(com=d_period - 1, adjust=False).mean()
        d = k.ewm(com=d_period - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        return k.values, d.values, j.values

    @staticmethod
    def cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> np.ndarray:
        """
        Commodity Channel Index (CCI)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period (default 20)

        Returns:
            CCI values
        """
        typical_price = (high + low + close) / 3.0
        sma_tp = pd.Series(typical_price).rolling(window=period, min_periods=1).mean()
        mean_dev = pd.Series(typical_price).rolling(window=period, min_periods=1).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        cci = (typical_price - sma_tp) / (0.015 * mean_dev + 1e-10)
        return cci.values

    @staticmethod
    def adx(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Average Directional Index (ADX)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period (default 14)

        Returns:
            Tuple of (ADX, +DI, -DI)
        """
        if len(close) < period + 1:
            return (
                np.full(len(close), np.nan),
                np.full(len(close), np.nan),
                np.full(len(close), np.nan)
            )

        high_diff = np.diff(high)
        low_diff = np.diff(low)

        plus_dm = np.where(
            (high_diff > low_diff) & (high_diff > 0),
            high_diff,
            0
        )
        minus_dm = np.where(
            (low_diff > high_diff) & (low_diff > 0),
            low_diff,
            0
        )

        atr = TechnicalIndicators.atr(high, low, close, period)

        # Get ATR for the same index range as plus_dm and minus_dm
        atr_for_dm = atr[1:]  # ATR is same length as high/low/close, so we need to align it

        plus_di = pd.Series(plus_dm).rolling(window=period, min_periods=1).mean() / (
            atr_for_dm + 1e-10
        ) * 100
        minus_di = pd.Series(minus_dm).rolling(window=period, min_periods=1).mean() / (
            atr_for_dm + 1e-10
        ) * 100

        dx = np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
        adx = pd.Series(dx).rolling(window=period, min_periods=1).mean()

        # Prepend NaN to match original close price length (all arrays need same length)
        return np.concatenate([[np.nan], adx.values]), np.concatenate([[np.nan], plus_di.values]), np.concatenate([[np.nan], minus_di.values])

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average True Range (ATR)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period (default 14)

        Returns:
            ATR values
        """
        if len(close) < 2:
            return np.full(len(close), np.nan)

        high_low = high - low
        high_close = np.abs(np.diff(close, prepend=close[0]))
        low_close = np.abs(np.diff(close, prepend=close[0]))

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = pd.Series(true_range).rolling(window=period, min_periods=1).mean()

        return atr.values

    @staticmethod
    def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        On-Balance Volume (OBV)

        Args:
            close: Close prices
            volume: Volume data

        Returns:
            OBV values
        """
        if len(close) < 2:
            return np.full(len(close), 0.0)

        obv = np.zeros(len(close))
        obv[0] = volume[0]

        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif close[i] < close[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]

        return obv

    @staticmethod
    def ichimoku(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        conv: int = 9,
        base: int = 26,
        lag: int = 52
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Ichimoku Kinko Hyo (Ichimoku Cloud)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            conv: Conversion line period (default 9)
            base: Base line period (default 26)
            lag: Lagging span period (default 52)

        Returns:
            Tuple of (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span)
        """
        tenkan_sen = (pd.Series(high).rolling(window=conv, min_periods=1).max() +
                      pd.Series(low).rolling(window=conv, min_periods=1).min()) / 2

        kijun_sen = (pd.Series(high).rolling(window=base, min_periods=1).max() +
                     pd.Series(low).rolling(window=base, min_periods=1).min()) / 2

        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        senkou_span_b = (pd.Series(high).rolling(window=lag, min_periods=1).max() +
                         pd.Series(low).rolling(window=lag, min_periods=1).min()) / 2

        chikou_span = np.concatenate([[np.nan] * (len(close) - 1), close[:1]])

        return tenkan_sen.values, kijun_sen.values, senkou_span_a.values, senkou_span_b.values, chikou_span

    @staticmethod
    def parabolic_sar(
        high: np.ndarray,
        low: np.ndarray,
        af_start: float = 0.02,
        af_max: float = 0.2
    ) -> np.ndarray:
        """
        Parabolic SAR (Stop and Reverse)

        Args:
            high: High prices
            low: Low prices
            af_start: Starting acceleration factor (default 0.02)
            af_max: Maximum acceleration factor (default 0.2)

        Returns:
            SAR values
        """
        if len(high) < 2:
            return np.full(len(high), np.nan)

        sar = np.zeros(len(high))
        sar[0] = low[0]
        af = af_start
        ep = high[0]
        trend = 1  # 1 for uptrend, -1 for downtrend

        for i in range(1, len(high)):
            sar[i] = sar[i - 1] + af * (ep - sar[i - 1])

            # Check for trend reversal
            if trend == 1 and low[i] <= sar[i]:
                trend = -1
                sar[i] = ep
                af = af_start
                ep = low[i]
            elif trend == -1 and high[i] >= sar[i]:
                trend = 1
                sar[i] = ep
                af = af_start
                ep = high[i]
            else:
                # Update EP
                if trend == 1 and high[i] > ep:
                    ep = high[i]
                    af = min(af + af_start, af_max)
                elif trend == -1 and low[i] < ep:
                    ep = low[i]
                    af = min(af + af_start, af_max)

        return sar

    @staticmethod
    def williams_r(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Williams %R (Williams Percent Range)

        Momentum oscillator that measures overbought/oversold levels.
        Similar to Stochastic Oscillator but with different scaling.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period (default 14)

        Returns:
            Williams %R values (-100 to 0, where -20 is overbought, -80 is oversold)
        """
        if len(close) < period:
            return np.full(len(close), np.nan)

        highest_high = pd.Series(high).rolling(window=period, min_periods=1).max()
        lowest_low = pd.Series(low).rolling(window=period, min_periods=1).min()

        williams_r = ((highest_high - close) / (highest_high - lowest_low + 1e-10)) * -100
        return williams_r.values

    @staticmethod
    def stochastic_rsi(
        rsi_values: np.ndarray,
        k_period: int = 3,
        d_period: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Stochastic RSI

        Applies Stochastic oscillator formula to RSI values.
        Combines momentum (RSI) with overbought/oversold detection (Stochastic).

        Args:
            rsi_values: RSI values array
            k_period: K period (default 3)
            d_period: D period (default 3)

        Returns:
            Tuple of (Stochastic %K, Stochastic %D)
        """
        if len(rsi_values) < max(k_period, d_period):
            return np.full(len(rsi_values), np.nan), np.full(len(rsi_values), np.nan)

        # Convert RSI to stochastic values
        rsi_series = pd.Series(rsi_values)
        rsi_min = rsi_series.rolling(window=k_period, min_periods=1).min()
        rsi_max = rsi_series.rolling(window=k_period, min_periods=1).max()

        stoch_rsi = (rsi_series - rsi_min) / (rsi_max - rsi_min + 1e-10) * 100

        # Calculate %K and %D
        stoch_k = stoch_rsi.rolling(window=d_period, min_periods=1).mean()
        stoch_d = stoch_k.rolling(window=d_period, min_periods=1).mean()

        return stoch_k.values, stoch_d.values

    @staticmethod
    def ultimate_oscillator(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        short_period: int = 7,
        medium_period: int = 14,
        long_period: int = 28
    ) -> np.ndarray:
        """
        Ultimate Oscillator

        Uses three different timeframes to reduce false divergences and
        premature buy/sell signals. Developed by Larry Williams.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            short_period: Short period (default 7)
            medium_period: Medium period (default 14)
            long_period: Long period (default 28)

        Returns:
            Ultimate Oscillator values (0-100)
        """
        if len(close) < long_period:
            return np.full(len(close), np.nan)

        # Calculate True Range and Buying Pressure
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        true_range = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - prev_close),
                np.abs(low - prev_close)
            )
        )

        buying_pressure = close - np.minimum(low, prev_close)

        # Calculate averages for each period
        bp_short = pd.Series(buying_pressure).rolling(window=short_period, min_periods=1).sum()
        tr_short = pd.Series(true_range).rolling(window=short_period, min_periods=1).sum()

        bp_medium = pd.Series(buying_pressure).rolling(window=medium_period, min_periods=1).sum()
        tr_medium = pd.Series(true_range).rolling(window=medium_period, min_periods=1).sum()

        bp_long = pd.Series(buying_pressure).rolling(window=long_period, min_periods=1).sum()
        tr_long = pd.Series(true_range).rolling(window=long_period, min_periods=1).sum()

        # Calculate raw Ultimate Oscillator
        uo_raw = 4 * (bp_short / tr_short) + 2 * (bp_medium / tr_medium) + (bp_long / tr_long)

        # Normalize to 0-100 scale
        uo = 100 * uo_raw / 7

        return uo.values

    @staticmethod
    def aroon_oscillator(
        high: np.ndarray,
        low: np.ndarray,
        period: int = 25
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Aroon Oscillator

        Measures the time between highs and lows to identify trend changes.
        Aroon Up measures the time since the highest high.
        Aroon Down measures the time since the lowest low.

        Args:
            high: High prices
            low: Low prices
            period: Period (default 25)

        Returns:
            Tuple of (Aroon Up, Aroon Down, Aroon Oscillator)
        """
        if len(high) < period:
            return (
                np.full(len(high), np.nan),
                np.full(len(high), np.nan),
                np.full(len(high), np.nan)
            )

        aroon_up = np.full(len(high), np.nan)
        aroon_down = np.full(len(high), np.nan)

        for i in range(period - 1, len(high)):
            # Look back window
            window_start = i - period + 1
            window_high = high[window_start:i + 1]
            window_low = low[window_start:i + 1]

            # Find days since last high and low
            last_high_idx = np.argmax(window_high)
            last_low_idx = np.argmin(window_low)

            days_since_high = period - 1 - last_high_idx
            days_since_low = period - 1 - last_low_idx

            # Calculate Aroon values (0-100 scale)
            aroon_up[i] = ((period - days_since_high) / period) * 100
            aroon_down[i] = ((period - days_since_low) / period) * 100

        # Calculate Aroon Oscillator (difference between Aroon Up and Down)
        aroon_oscillator = aroon_up - aroon_down

        return aroon_up, aroon_down, aroon_oscillator


class PythonBacktestEngine:
    """
    Pure Python backtest engine providing identical API to Rust engine.

    High-performance implementation using vectorized operations.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        position_size: float = 1.0,
        risk_free_rate: float = 0.03
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Initial capital amount
            commission: Commission rate (0.001 = 0.1%)
            slippage: Slippage rate
            position_size: Position size ratio (1.0 = 100%)
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
        self.risk_free_rate = risk_free_rate
        self.indicators = TechnicalIndicators()

        logger.info(
            f"Initialized PythonBacktestEngine: capital={initial_capital}, "
            f"commission={commission:.4f}, slippage={slippage:.4f}"
        )

    def run_backtest(
        self,
        data: List[Dict[str, Any]],
        strategy_type: str,
        params: Optional[Dict[str, float]] = None
    ) -> PythonBacktestResult:
        """
        Run backtest with given data and strategy.

        This method provides identical API to Rust engine's PyBacktestEngine.run_backtest().

        Args:
            data: List of data point dictionaries with keys:
                  'timestamp', 'open', 'high', 'low', 'close', 'volume'
            strategy_type: Strategy type ('ma', 'rsi', 'macd', 'bb', 'kdj', 'cci', 'adx', 'atr', 'obv', 'ichimoku', 'psar')
            params: Strategy parameters dictionary

        Returns:
            PythonBacktestResult with all metrics
        """
        start_time = time.time()

        if not data:
            raise ValueError("Data cannot be empty")

        # Default parameters
        if params is None:
            params = {}

        # Convert data to PythonMarketData
        market_data = self._convert_data_to_market_data(data)

        # Run strategy-specific backtest
        if strategy_type.lower() == 'ma':
            result = self._run_ma_strategy(market_data, params)
        elif strategy_type.lower() == 'rsi':
            result = self._run_rsi_strategy(market_data, params)
        elif strategy_type.lower() == 'macd':
            result = self._run_macd_strategy(market_data, params)
        elif strategy_type.lower() == 'bb':
            result = self._run_bb_strategy(market_data, params)
        elif strategy_type.lower() == 'kdj':
            result = self._run_kdj_strategy(market_data, params)
        elif strategy_type.lower() == 'cci':
            result = self._run_cci_strategy(market_data, params)
        elif strategy_type.lower() == 'adx':
            result = self._run_adx_strategy(market_data, params)
        elif strategy_type.lower() == 'atr':
            result = self._run_atr_strategy(market_data, params)
        elif strategy_type.lower() == 'obv':
            result = self._run_obv_strategy(market_data, params)
        elif strategy_type.lower() == 'ichimoku':
            result = self._run_ichimoku_strategy(market_data, params)
        elif strategy_type.lower() == 'psar':
            result = self._run_psar_strategy(market_data, params)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        result.execution_time_ms = execution_time_ms

        logger.info(
            f"Backtest completed: {strategy_type} strategy, "
            f"{result.total_trades} trades, {execution_time_ms}ms"
        )

        return result

    def _convert_data_to_market_data(self, data: List[Dict[str, Any]]) -> PythonMarketData:
        """Convert list of dicts to PythonMarketData"""
        timestamps = []
        opens, highs, lows, closes, volumes = [], [], [], [], []

        for item in data:
            timestamps.append(item['timestamp'])
            opens.append(float(item['open']))
            highs.append(float(item['high']))
            lows.append(float(item['low']))
            closes.append(float(item['close']))
            volumes.append(int(item['volume']))

        return PythonMarketData(
            symbol="UNKNOWN",
            timestamps=timestamps,
            open=np.array(opens),
            high=np.array(highs),
            low=np.array(lows),
            close=np.array(closes),
            volume=np.array(volumes)
        )

    def _simulate_trades(
        self,
        market_data: PythonMarketData,
        signals: np.ndarray
    ) -> Tuple[List[Trade], List[Tuple[str, float]]]:
        """
        Simulate trades based on signals.

        Args:
            market_data: Market data
            signals: Trading signals (1=buy, -1=sell, 0=hold)

        Returns:
            Tuple of (trades list, equity curve)
        """
        trades = []
        equity_curve = [(market_data.timestamps[0], self.initial_capital)]

        position = 0.0
        cash = self.initial_capital
        entry_price = 0.0
        trade_id = 1
        entry_time = None

        for i in range(1, len(signals)):
            current_price = market_data.close[i]
            current_time = market_data.timestamps[i]

            # Buy signal and no position
            if signals[i] == 1 and position == 0:
                available_capital = cash * self.position_size
                shares = int(available_capital / current_price)

                if shares > 0:
                    position = float(shares)
                    cost = shares * current_price
                    commission = cost * self.commission * (1 + self.slippage)
                    cash = cash - cost - commission
                    entry_price = current_price
                    entry_time = current_time

                    trades.append(Trade(
                        id=trade_id,
                        entry_time=entry_time,
                        exit_time=None,
                        entry_price=current_price,
                        exit_price=None,
                        quantity=position,
                        pnl=None,
                        commission=commission
                    ))
                    trade_id += 1

            # Sell signal and have position
            elif signals[i] == -1 and position > 0:
                proceeds = position * current_price
                commission = proceeds * self.commission * (1 + self.slippage)
                cash = cash + proceeds - commission

                pnl = (proceeds - commission) - (position * entry_price)

                # Update trade record
                trades[-1].exit_time = current_time
                trades[-1].exit_price = current_price
                trades[-1].pnl = pnl
                trades[-1].commission += commission

                position = 0.0

            # Calculate current portfolio value
            current_value = cash + (position * current_price)
            equity_curve.append((current_time, current_value))

        # Close any remaining position at the end
        if position > 0:
            final_price = market_data.close[-1]
            final_time = market_data.timestamps[-1]
            proceeds = position * final_price
            commission = proceeds * self.commission

            cash = cash + proceeds - commission
            pnl = proceeds - commission - (position * entry_price)

            trades[-1].exit_time = final_time
            trades[-1].exit_price = final_price
            trades[-1].pnl = pnl
            trades[-1].commission += commission

            equity_curve.append((final_time, cash))

        return trades, equity_curve

    def _calculate_metrics(
        self,
        equity_curve: List[Tuple[str, float]],
        trades: List[Trade],
        data_length: int
    ) -> Dict[str, float]:
        """
        Calculate performance metrics.

        Args:
            equity_curve: List of (timestamp, value) tuples
            trades: List of trades
            data_length: Number of data points

        Returns:
            Dictionary of metrics
        """
        if not equity_curve:
            return {
                'total_return': 0.0,
                'annualized_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            }

        values = np.array([val for _, val in equity_curve])
        initial_value = values[0]
        final_value = values[-1]

        # Total return
        total_return = (final_value - initial_value) / initial_value if initial_value > 0 else 0

        # Annualized return
        years = data_length / 252.0
        annualized_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1

        # Volatility (annualized)
        returns = np.diff(values) / values[:-1]
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0.0

        # Sharpe ratio
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0

        # Maximum drawdown
        max_dd = self._calculate_max_drawdown(values)

        # Win rate
        closed_trades = [t for t in trades if t.exit_time is not None]
        winning_trades = sum(1 for t in closed_trades if t.pnl and t.pnl > 0)
        win_rate = winning_trades / max(len(closed_trades), 1)

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_dd,
            'win_rate': win_rate
        }

    def _calculate_max_drawdown(self, values: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        if len(values) == 0:
            return 0.0

        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value

            if peak > 0:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)

        return max_dd

    # Strategy implementations
    def _run_ma_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run Moving Average Crossover strategy"""
        fast_period = int(params.get('fast_period', 10))
        slow_period = int(params.get('slow_period', 20))

        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")

        fast_sma = self.indicators.sma(data.close, fast_period)
        slow_sma = self.indicators.sma(data.close, slow_period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(fast_sma[i]) or np.isnan(slow_sma[i]):
                signals[i] = 0
            elif fast_sma[i-1] <= slow_sma[i-1] and fast_sma[i] > slow_sma[i]:
                signals[i] = 1  # Buy
            elif fast_sma[i-1] >= slow_sma[i-1] and fast_sma[i] < slow_sma[i]:
                signals[i] = -1  # Sell
            else:
                signals[i] = 0  # Hold

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_rsi_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run RSI strategy"""
        period = int(params.get('period', 14))
        oversold = params.get('oversold', 30.0)
        overbought = params.get('overbought', 70.0)

        rsi = self.indicators.rsi(data.close, period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(rsi[i]):
                signals[i] = 0
            elif rsi[i-1] > oversold and rsi[i] <= oversold:
                signals[i] = 1  # Buy (oversold bounce)
            elif rsi[i-1] < overbought and rsi[i] >= overbought:
                signals[i] = -1  # Sell (overbought decline)
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_macd_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run MACD strategy"""
        fast = int(params.get('fast', 12))
        slow = int(params.get('slow', 26))
        signal = int(params.get('signal', 9))

        macd, signal_line, _ = self.indicators.macd(data.close, fast, slow, signal)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(macd[i]) or np.isnan(signal_line[i]):
                signals[i] = 0
            elif macd[i-1] <= signal_line[i-1] and macd[i] > signal_line[i]:
                signals[i] = 1  # Bullish crossover
            elif macd[i-1] >= signal_line[i-1] and macd[i] < signal_line[i]:
                signals[i] = -1  # Bearish crossover
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_bb_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run Bollinger Bands strategy"""
        period = int(params.get('period', 20))
        std_dev = params.get('std_dev', 2.0)

        upper, middle, lower = self.indicators.bollinger_bands(data.close, period, std_dev)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(upper[i]) or np.isnan(lower[i]):
                signals[i] = 0
            elif data.close[i-1] > lower[i-1] and data.close[i] <= lower[i]:
                signals[i] = 1  # Bounce off lower band
            elif data.close[i-1] < upper[i-1] and data.close[i] >= upper[i]:
                signals[i] = -1  # Rejection at upper band
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_kdj_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run KDJ strategy"""
        k_period = int(params.get('k_period', 9))
        d_period = int(params.get('d_period', 3))
        oversold = params.get('oversold', 20.0)
        overbought = params.get('overbought', 80.0)

        k, d, _ = self.indicators.kdj(data.high, data.low, data.close, k_period, d_period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(k[i]) or np.isnan(d[i]):
                signals[i] = 0
            elif k[i-1] <= d[i-1] and k[i] > d[i] and k[i] <= oversold:
                signals[i] = 1  # K crosses above D from oversold
            elif k[i-1] >= d[i-1] and k[i] < d[i] and k[i] >= overbought:
                signals[i] = -1  # K crosses below D from overbought
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_cci_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run CCI strategy"""
        period = int(params.get('period', 20))

        cci = self.indicators.cci(data.high, data.low, data.close, period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(cci[i]):
                signals[i] = 0
            elif cci[i-1] > -100 and cci[i] <= -100:
                signals[i] = 1  # Oversold bounce
            elif cci[i-1] < 100 and cci[i] >= 100:
                signals[i] = -1  # Overbought decline
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_adx_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run ADX strategy"""
        period = int(params.get('period', 14))
        threshold = params.get('threshold', 25.0)

        adx, plus_di, minus_di = self.indicators.adx(data.high, data.low, data.close, period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(adx[i]) or np.isnan(plus_di[i]) or np.isnan(minus_di[i]):
                signals[i] = 0
            elif adx[i] > threshold and plus_di[i] > minus_di[i]:
                signals[i] = 1  # Strong uptrend
            elif adx[i] > threshold and plus_di[i] < minus_di[i]:
                signals[i] = -1  # Strong downtrend
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_atr_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run ATR strategy"""
        period = int(params.get('period', 14))
        multiplier = params.get('multiplier', 2.0)

        atr = self.indicators.atr(data.high, data.low, data.close, period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(atr[i]):
                signals[i] = 0
            elif data.close[i] > data.close[i-1] + (multiplier * atr[i]):
                signals[i] = 1  # Breakout above
            elif data.close[i] < data.close[i-1] - (multiplier * atr[i]):
                signals[i] = -1  # Breakdown below
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_obv_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run OBV strategy"""
        period = int(params.get('period', 20))

        obv = self.indicators.obv(data.close, data.volume)
        obv_ma = self.indicators.sma(obv, period)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(obv_ma[i]):
                signals[i] = 0
            elif obv[i-1] <= obv_ma[i-1] and obv[i] > obv_ma[i]:
                signals[i] = 1  # OBV crosses above MA
            elif obv[i-1] >= obv_ma[i-1] and obv[i] < obv_ma[i]:
                signals[i] = -1  # OBV crosses below MA
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_ichimoku_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run Ichimoku strategy"""
        conv = int(params.get('conv', 9))
        base = int(params.get('base', 26))
        lag = int(params.get('lag', 52))

        tenkan, kijun, span_a, span_b, chikou = self.indicators.ichimoku(
            data.high, data.low, data.close, conv, base, lag
        )

        signals = np.zeros(len(data.close))
        for i in range(base, len(data.close)):
            if np.isnan(tenkan[i]) or np.isnan(kijun[i]) or np.isnan(span_a[i]) or np.isnan(span_b[i]):
                signals[i] = 0
            elif (tenkan[i] > kijun[i] and
                  data.close[i] > span_a[i] and
                  data.close[i] > span_b[i]):
                signals[i] = 1  # Bullish signal
            elif (tenkan[i] < kijun[i] and
                  data.close[i] < span_a[i] and
                  data.close[i] < span_b[i]):
                signals[i] = -1  # Bearish signal
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )

    def _run_psar_strategy(self, data: PythonMarketData, params: Dict[str, float]) -> PythonBacktestResult:
        """Run Parabolic SAR strategy"""
        af_start = params.get('af_start', 0.02)
        af_max = params.get('af_max', 0.2)

        sar = self.indicators.parabolic_sar(data.high, data.low, af_start, af_max)

        signals = np.zeros(len(data.close))
        for i in range(1, len(data.close)):
            if np.isnan(sar[i]):
                signals[i] = 0
            elif data.close[i-1] <= sar[i-1] and data.close[i] > sar[i]:
                signals[i] = 1  # Price crosses above SAR
            elif data.close[i-1] >= sar[i-1] and data.close[i] < sar[i]:
                signals[i] = -1  # Price crosses below SAR
            else:
                signals[i] = 0

        trades, equity_curve = self._simulate_trades(data, signals)
        metrics = self._calculate_metrics(equity_curve, trades, len(data.close))

        return PythonBacktestResult(
            total_return=metrics['total_return'],
            annualized_return=metrics['annualized_return'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            execution_time_ms=0,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve
        )


# Utility functions
def validate_market_data(data: PythonMarketData) -> bool:
    """
    Validate market data integrity.

    Args:
        data: PythonMarketData instance

    Returns:
        True if valid, False otherwise
    """
    try:
        # Try to access all properties
        _ = data.length
        _ = data.get_price('close')
        return True
    except Exception as e:
        logger.error(f"Market data validation failed: {e}")
        return False


def calculate_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of portfolio values

    Returns:
        Maximum drawdown as a percentage (0-1)
    """
    if not equity_curve:
        return 0.0

    equity_array = np.array(equity_curve)
    engine = PythonBacktestEngine()
    return engine._calculate_max_drawdown(equity_array)


# API compatibility functions matching Rust engine
def create_engine(
    initial_capital: float = 100000.0,
    commission: float = 0.001,
    slippage: float = 0.0005,
    position_size: float = 1.0,
    risk_free_rate: float = 0.03
) -> PythonBacktestEngine:
    """
    Create a new backtest engine instance.

    This function provides compatibility with the Rust engine API.

    Args:
        initial_capital: Initial capital
        commission: Commission rate
        slippage: Slippage rate
        position_size: Position size
        risk_free_rate: Risk-free rate

    Returns:
        PythonBacktestEngine instance
    """
    return PythonBacktestEngine(
        initial_capital=initial_capital,
        commission=commission,
        slippage=slippage,
        position_size=position_size,
        risk_free_rate=risk_free_rate
    )


def calculate_sma(data: List[float], period: int) -> List[float]:
    """
    Calculate Simple Moving Average.

    Args:
        data: Price data
        period: Moving average period

    Returns:
        SMA values
    """
    prices = np.array(data, dtype=np.float64)
    return TechnicalIndicators.sma(prices, period).tolist()


def calculate_rsi(data: List[float], period: int = 14) -> List[float]:
    """
    Calculate RSI.

    Args:
        data: Price data
        period: RSI period

    Returns:
        RSI values
    """
    prices = np.array(data, dtype=np.float64)
    return TechnicalIndicators.rsi(prices, period).tolist()


def calculate_macd(
    data: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[List[float], List[float], List[float]]:
    """
    Calculate MACD.

    Args:
        data: Price data
        fast: Fast period
        slow: Slow period
        signal: Signal period

    Returns:
        Tuple of (MACD, Signal, Histogram)
    """
    prices = np.array(data, dtype=np.float64)
    macd, signal_line, histogram = TechnicalIndicators.macd(prices, fast, slow, signal)
    return macd.tolist(), signal_line.tolist(), histogram.tolist()


def calculate_bollinger_bands(
    data: List[float],
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[List[float], List[float], List[float]]:
    """
    Calculate Bollinger Bands.

    Args:
        data: Price data
        period: Period
        num_std: Number of standard deviations

    Returns:
        Tuple of (Upper, Middle, Lower)
    """
    prices = np.array(data, dtype=np.float64)
    upper, middle, lower = TechnicalIndicators.bollinger_bands(prices, period, num_std)
    return upper.tolist(), middle.tolist(), lower.tolist()
