#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 增强策略回测系统 - 支持11种高级技术指标

集成11种技术指标到完整量化交易系统，支持参数优化和Sharpe比率优化。

## 支持的技术指标（11种）
### 基础指标 (4种)
  1. MA (移动平均交叉) - 多周期移动平均线
  2. RSI (相对强度指数) - 超买超卖检测
  3. MACD (指数平滑移动平均线) - 趋势确认
  4. Bollinger Bands (布林带) - 波动率通道

### 高级指标 (7种新增)
  5. KDJ/Stochastic (随机指标) - K/D交叉信号
  6. CCI (商品通道指标) - 极端价格检测
  7. ADX (平均趋向指标) - 趋势强度 (+DI/-DI)
  8. ATR (平均真实范围) - 波动率突破
  9. OBV (能量潮指标) - 成交量确认
  10. Ichimoku (一目均衡表) - 云图策略 (5条线)
  11. Parabolic SAR (拋物線轉向) - 趋势反转点

## 主要功能
- calculate_technical_indicators(): 计算所有11种技术指标
- run_xxx_strategy(): 7个新策略执行方法
- optimize_parameters(): 支持'all'或指定策略的参数优化
- _optimize_xxx_parameters(): 7个参数优化方法，使用多线程加速

## 参数优化范围
- KDJ: K/D周期 5-30, 阈值 20-80
- CCI: 周期 10-30, 阈值 -300 至 +300
- ADX: 周期 10-30, 阈值 15-50
- ATR: 周期 10-30, 倍数 0.5-5.0
- OBV: 趋势周期 10-100
- Ichimoku: 转换 5-15, 基准 20-40, 延迟 40-60
- Parabolic SAR: 加速因子 0.01-0.2, 最大加速 0.1-0.5

## 使用示例
```python
backtest = EnhancedStrategyBacktest('0700.HK', '2020-01-01', '2023-01-01')
backtest.load_data()

# 优化单个指标
results = backtest.optimize_parameters(strategy_type='kdj')

# 优化所有指标 (耗时较长)
all_results = backtest.optimize_parameters(strategy_type='all', max_workers=8)

# 获取最佳策略
best = backtest.get_best_strategies(top_n=10)
```
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional
import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from itertools import product
import time

warnings.filterwarnings('ignore')

class EnhancedStrategyBacktest:
    """增强策略回测引擎"""
    
    def __init__(self, symbol: str, start_date: str = '2020-01-01', end_date: str = '2023-01-01'):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = []
        self.logger = logging.getLogger(__name__)
        
    def load_data(self) -> bool:
        """加载股票数据"""
        try:
            self.logger.info(f"正在加载 {self.symbol} 数据...")
            self.data = yf.download(self.symbol, start=self.start_date, end=self.end_date)
            if self.data is None or self.data.empty:
                self.logger.error(f"无法加载 {self.symbol} 数据")
                return False
            self.logger.info(f"数据加载完成: {len(self.data)} 个交易日")
            return True
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return False
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标 (支持11种指标: MA, RSI, MACD, BB, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR)"""
        df = data.copy()

        # 处理MultiIndex列（yfinance可能返回多列数据）
        if isinstance(df.columns, pd.MultiIndex):
            # 扁平化列名，只保留第一个股票的数据
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            # 去除重复列，只保留第一个
            df = df.loc[:, ~df.columns.duplicated(keep='first')]

        # 移动平均线
        for period in [5, 10, 15, 20, 30, 50, 100, 200]:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()

        # RSI指标
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.0001)
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD指标
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']

        # 布林带
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']

        # KDJ指标 (Stochastic) - 可配置周期
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        df['D'] = df['K'].rolling(window=3).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']  # KDJ中的J值

        # 威廉指标
        df['WR'] = 100 * (high_max - df['Close']) / (high_max - low_min)

        # CCI指标 (Commodity Channel Index)
        try:
            tp = (df['High'] + df['Low'] + df['Close']) / 3  # Typical Price
            sma_tp = tp.rolling(window=20).mean()
            mad_tp = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
            df['CCI'] = (tp - sma_tp) / (0.015 * mad_tp)
        except:
            df['CCI'] = np.nan

        # ATR 和 ADX 相关指标 (True Range)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(14).mean()

        # ADX指标完整计算 (+DI, -DI)
        try:
            df['plus_dm'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']),
                                      np.maximum(df['High'] - df['High'].shift(1), 0), 0)
            df['minus_dm'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)),
                                       np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)

            atr_14 = true_range.rolling(14).mean()
            df['plus_di'] = 100 * (df['plus_dm'].rolling(14).mean() / atr_14)
            df['minus_di'] = 100 * (df['minus_dm'].rolling(14).mean() / atr_14)
            df['di_diff'] = np.abs(df['plus_di'] - df['minus_di'])
            dx = 100 * df['di_diff'] / (df['plus_di'] + df['minus_di'] + 0.0001)
            df['ADX'] = dx.rolling(14).mean()
        except:
            df['plus_di'] = np.nan
            df['minus_di'] = np.nan
            df['ADX'] = np.nan

        # OBV指标 (On-Balance Volume)
        df['OBV'] = 0.0
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                df['OBV'].iloc[i] = df['OBV'].iloc[i-1] + df['Volume'].iloc[i]
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                df['OBV'].iloc[i] = df['OBV'].iloc[i-1] - df['Volume'].iloc[i]
            else:
                df['OBV'].iloc[i] = df['OBV'].iloc[i-1]
        df['OBV_MA'] = df['OBV'].rolling(window=20).mean()

        # Ichimoku Cloud (一目均衡表) - 5条线
        try:
            # 转换线 (Tenkan-sen)
            high_9 = df['High'].rolling(window=9).max()
            low_9 = df['Low'].rolling(window=9).min()
            df['Tenkan'] = (high_9 + low_9) / 2

            # 基准线 (Kijun-sen)
            high_26 = df['High'].rolling(window=26).max()
            low_26 = df['Low'].rolling(window=26).min()
            df['Kijun'] = (high_26 + low_26) / 2

            # 先行帯A (Senkou Span A)
            df['Senkou_A'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(26)

            # 先行帯B (Senkou Span B)
            high_52 = df['High'].rolling(window=52).max()
            low_52 = df['Low'].rolling(window=52).min()
            df['Senkou_B'] = ((high_52 + low_52) / 2).shift(26)

            # 延迟线 (Chikou Span)
            df['Chikou'] = df['Close'].shift(-26)
        except:
            df['Tenkan'] = np.nan
            df['Kijun'] = np.nan
            df['Senkou_A'] = np.nan
            df['Senkou_B'] = np.nan
            df['Chikou'] = np.nan

        # Parabolic SAR (拋物線轉向指標)
        try:
            df['SAR'] = np.nan
            df['AF'] = 0.02  # Acceleration Factor
            df['SAR_trend'] = 1  # 1 for uptrend, -1 for downtrend

            # 简化的SAR计算 (详细实现在策略方法中)
            for i in range(2, len(df)):
                if i > 20:  # 确保有足够数据
                    if df['SAR_trend'].iloc[i-1] == 1:  # 上升趋势
                        df['SAR'].iloc[i] = df['Low'].iloc[i-14:i].min()
                    else:  # 下降趋势
                        df['SAR'].iloc[i] = df['High'].iloc[i-14:i].max()
        except:
            df['SAR'] = np.nan

        # 成交量指标
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['Volume'] / (df['Volume_MA'] + 0.0001)

        return df
    
    def run_ma_crossover_strategy(self, short_window: int, long_window: int) -> Dict:
        """移动平均交叉策略"""
        if short_window >= long_window:
            return None
            
        df = self.data.copy()
        df[f'MA{short_window}'] = df['Close'].rolling(window=short_window).mean()
        df[f'MA{long_window}'] = df['Close'].rolling(window=long_window).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 生成交易信号
        df['signal'] = np.where(df[f'MA{short_window}'] > df[f'MA{long_window}'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"MA交叉({short_window},{long_window})")
    
    def run_rsi_strategy(self, rsi_period: int, oversold: float, overbought: float) -> Dict:
        """RSI策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # RSI策略信号
        df['signal'] = 0
        df.loc[df['RSI'] < oversold, 'signal'] = 1  # 超卖买入
        df.loc[df['RSI'] > overbought, 'signal'] = 0  # 超买卖出
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"RSI({rsi_period},{oversold},{overbought})")
    
    def run_macd_strategy(self, fast: int, slow: int, signal: int) -> Dict:
        """MACD策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # MACD策略信号
        df['signal'] = np.where(df['MACD'] > df['MACD_signal'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"MACD({fast},{slow},{signal})")
    
    def run_bollinger_bands_strategy(self, period: int, std_dev: float) -> Dict:
        """布林带策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 布林带策略信号
        df['signal'] = 0
        df.loc[df['Close'] < df['BB_lower'], 'signal'] = 1  # 价格触及下轨买入
        df.loc[df['Close'] > df['BB_upper'], 'signal'] = 0  # 价格触及上轨卖出
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, f"布林带({period},{std_dev})")
    
    def run_combined_strategy(self, params: Dict) -> Dict:
        """组合策略"""
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 组合多个指标
        conditions = []
        
        # MA条件
        if 'ma_short' in params and 'ma_long' in params:
            ma_short = params['ma_short']
            ma_long = params['ma_long']
            df[f'MA{ma_short}'] = df['Close'].rolling(window=ma_short).mean()
            df[f'MA{ma_long}'] = df['Close'].rolling(window=ma_long).mean()
            conditions.append(df[f'MA{ma_short}'] > df[f'MA{ma_long}'])
        
        # RSI条件
        if 'rsi_oversold' in params and 'rsi_overbought' in params:
            rsi_oversold = params['rsi_oversold']
            rsi_overbought = params['rsi_overbought']
            conditions.append((df['RSI'] > rsi_oversold) & (df['RSI'] < rsi_overbought))
        
        # MACD条件
        if 'macd_enabled' in params and params['macd_enabled']:
            conditions.append(df['MACD'] > df['MACD_signal'])
        
        # 布林带条件
        if 'bb_enabled' in params and params['bb_enabled']:
            conditions.append(df['Close'] > df['BB_lower'])
        
        if not conditions:
            return None
        
        # 组合所有条件
        df['signal'] = 1
        for condition in conditions:
            df['signal'] = df['signal'] & condition
        df['signal'] = df['signal'].astype(int)
        df['position'] = df['signal'].diff()
        
        return self._calculate_strategy_performance(df, "组合策略")

    # ==================== 7个新增高级指标策略 ====================

    def run_kdj_strategy(self, k_period: int = 9, d_period: int = 3, oversold: float = 20, overbought: float = 80) -> Dict:
        """KDJ/Stochastic 随机指标策略

        Args:
            k_period: K值周期（默认9）
            d_period: D值周期（默认3）
            oversold: 超卖阈值（默认20）
            overbought: 超买阈值（默认80）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < max(k_period, d_period) + 50:
            return None

        # 重新计算指定周期的KDJ
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()
        k_raw = 100 * (df['Close'] - low_min) / (high_max - low_min + 0.0001)
        k_line = k_raw.rolling(window=d_period).mean()
        d_line = k_line.rolling(window=d_period).mean()

        # 生成交易信号
        df['signal'] = 0
        for i in range(1, len(df)):
            if k_line.iloc[i] > oversold and k_line.iloc[i-1] <= oversold:
                df['signal'].iloc[i] = 1  # K从超卖区上升，买入信号
            elif k_line.iloc[i] < overbought and k_line.iloc[i-1] >= overbought:
                df['signal'].iloc[i] = 0  # K从超买区下降，卖出信号

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"KDJ({k_period},{d_period},{oversold},{overbought})")

    def run_cci_strategy(self, period: int = 20, oversold: float = -100, overbought: float = 100) -> Dict:
        """CCI 商品通道指标策略

        Args:
            period: CCI计算周期（默认20）
            oversold: 超卖阈值（默认-100）
            overbought: 超买阈值（默认100）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < period + 50:
            return None

        # 重新计算指定周期的CCI
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad_tp = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
        cci = (tp - sma_tp) / (0.015 * mad_tp + 0.0001)

        # 生成交易信号
        df['signal'] = 0
        for i in range(1, len(df)):
            if cci.iloc[i] > oversold and cci.iloc[i-1] <= oversold:
                df['signal'].iloc[i] = 1  # CCI从超卖区上升
            elif cci.iloc[i] < overbought and cci.iloc[i-1] >= overbought:
                df['signal'].iloc[i] = 0  # CCI从超买区下降

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"CCI({period},{oversold},{overbought})")

    def run_adx_strategy(self, period: int = 14, adx_threshold: float = 25) -> Dict:
        """ADX 平均趋向指标策略 (+DI, -DI, ADX)

        Args:
            period: ADX计算周期（默认14）
            adx_threshold: ADX趋势强度阈值（默认25）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < period + 50:
            return None

        # 生成交易信号
        df['signal'] = 0
        for i in range(1, len(df)):
            # 当ADX > 阈值且+DI > -DI时，买入
            if pd.notna(df['ADX'].iloc[i]) and df['ADX'].iloc[i] > adx_threshold:
                if pd.notna(df['plus_di'].iloc[i]) and pd.notna(df['minus_di'].iloc[i]):
                    if df['plus_di'].iloc[i] > df['minus_di'].iloc[i]:
                        df['signal'].iloc[i] = 1
                    elif df['minus_di'].iloc[i] > df['plus_di'].iloc[i]:
                        df['signal'].iloc[i] = 0

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"ADX({period},{adx_threshold})")

    def run_atr_strategy(self, period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """ATR 平均真实范围策略 (波动率突破)

        Args:
            period: ATR计算周期（默认14）
            atr_multiplier: ATR倍数（默认2.0）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < period + 50:
            return None

        # 计算突破阈值
        high_20 = df['High'].rolling(window=20).max()
        low_20 = df['Low'].rolling(window=20).min()
        atr_value = df['ATR'].fillna(df['ATR'].mean())

        upper_band = high_20 + (atr_value * atr_multiplier)
        lower_band = low_20 - (atr_value * atr_multiplier)

        # 生成交易信号（突破策略）
        df['signal'] = 0
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > upper_band.iloc[i]:
                df['signal'].iloc[i] = 1  # 上突破
            elif df['Close'].iloc[i] < lower_band.iloc[i]:
                df['signal'].iloc[i] = 0  # 下突破

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"ATR({period},{atr_multiplier})")

    def run_obv_strategy(self, trend_period: int = 20) -> Dict:
        """OBV 能量潮指标策略 (成交量确认)

        Args:
            trend_period: 趋势确认周期（默认20）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < trend_period + 50:
            return None

        obv_ma = df['OBV'].rolling(window=trend_period).mean()

        # 生成交易信号
        df['signal'] = 0
        for i in range(1, len(df)):
            # 价格和OBV都上升趋势
            if df['Close'].iloc[i] > df['Close'].rolling(window=5).mean().iloc[i] and \
               df['OBV'].iloc[i] > obv_ma.iloc[i]:
                df['signal'].iloc[i] = 1
            # 价格和OBV都下降趋势
            elif df['Close'].iloc[i] < df['Close'].rolling(window=5).mean().iloc[i] and \
                 df['OBV'].iloc[i] < obv_ma.iloc[i]:
                df['signal'].iloc[i] = 0

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"OBV({trend_period})")

    def run_ichimoku_strategy(self, conversion_period: int = 9, base_period: int = 26, span_b_period: int = 52) -> Dict:
        """Ichimoku 一目均衡表策略 (云图策略)

        Args:
            conversion_period: 转换线周期（默认9）
            base_period: 基准线周期（默认26）
            span_b_period: 先行帯B周期（默认52）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < span_b_period + 50:
            return None

        # 生成交易信号
        df['signal'] = 0
        for i in range(1, len(df)):
            tenkan = df['Tenkan'].iloc[i]
            kijun = df['Kijun'].iloc[i]
            senkou_a = df['Senkou_A'].iloc[i]
            senkou_b = df['Senkou_B'].iloc[i]
            price = df['Close'].iloc[i]

            if pd.notna(tenkan) and pd.notna(kijun) and pd.notna(senkou_a) and pd.notna(senkou_b):
                # 看涨信号：转换线>基准线，价格>云图
                if tenkan > kijun and price > max(senkou_a, senkou_b):
                    df['signal'].iloc[i] = 1
                # 看跌信号：转换线<基准线，价格<云图
                elif tenkan < kijun and price < min(senkou_a, senkou_b):
                    df['signal'].iloc[i] = 0

        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"Ichimoku({conversion_period},{base_period},{span_b_period})")

    def run_parabolic_sar_strategy(self, acceleration: float = 0.02, max_acceleration: float = 0.2) -> Dict:
        """Parabolic SAR 拋物線轉向指標策略 (轉向點策略)

        Args:
            acceleration: 初始加速因子（默认0.02）
            max_acceleration: 最大加速因子（默认0.2）

        Returns:
            策略绩效字典
        """
        df = self.data.copy()
        df = self.calculate_technical_indicators(df)
        df = df.dropna()

        if len(df) < 30:
            return None

        # 简化的Parabolic SAR实现
        sar = df['Low'].iloc[0]
        af = acceleration
        uptrend = True
        hp = df['High'].iloc[0]
        lp = df['Low'].iloc[0]

        df['SAR'] = np.nan
        df['trend'] = 0

        for i in range(1, len(df)):
            if uptrend:
                sar = sar + af * (hp - sar)
                if df['Low'].iloc[i] < sar:
                    uptrend = False
                    sar = hp
                    lp = df['Low'].iloc[i]
                    af = acceleration
                else:
                    if df['High'].iloc[i] > hp:
                        hp = df['High'].iloc[i]
                        af = min(af + acceleration, max_acceleration)
                    sar = min(sar, df['Low'].iloc[i-1], df['Low'].iloc[i-2] if i > 1 else df['Low'].iloc[i-1])
            else:
                sar = sar - af * (sar - lp)
                if df['High'].iloc[i] > sar:
                    uptrend = True
                    sar = lp
                    hp = df['High'].iloc[i]
                    af = acceleration
                else:
                    if df['Low'].iloc[i] < lp:
                        lp = df['Low'].iloc[i]
                        af = min(af + acceleration, max_acceleration)
                    sar = max(sar, df['High'].iloc[i-1], df['High'].iloc[i-2] if i > 1 else df['High'].iloc[i-1])

            df['SAR'].iloc[i] = sar
            df['trend'].iloc[i] = 1 if uptrend else 0

        df['signal'] = df['trend']
        df['position'] = df['signal'].diff()
        return self._calculate_strategy_performance(df, f"Parabolic_SAR({acceleration},{max_acceleration})")

    def _calculate_strategy_performance(self, df: pd.DataFrame, strategy_name: str) -> Dict:
        """计算策略绩效"""
        try:
            # 计算策略收益
            df['strategy_returns'] = df['position'].shift(1) * df['Close'].pct_change()
            df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
            
            # 计算绩效指标
            total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
            annual_return = ((df['cumulative_returns'].iloc[-1] ** (252 / len(df))) - 1) * 100
            volatility = df['strategy_returns'].std() * np.sqrt(252) * 100
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative = df['cumulative_returns']
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # 胜率
            winning_trades = (df['strategy_returns'] > 0).sum()
            total_trades = (df['strategy_returns'] != 0).sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 交易次数
            trade_count = (df['position'] != 0).sum()
            
            return {
                'strategy_name': strategy_name,
                'total_return': round(total_return, 2),
                'annual_return': round(annual_return, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'trade_count': trade_count,
                'final_value': round(df['cumulative_returns'].iloc[-1] * 100000, 2)  # 假设初始资金10万
            }
        except Exception as e:
            self.logger.error(f"计算策略绩效失败: {e}")
            return None
    
    def optimize_parameters(self, strategy_type: str = 'all', max_workers: int = None) -> List[Dict]:
        """Parameter optimization using multiprocessing with 32 cores support (MA, RSI, MACD, BB, KDJ, CCI, ADX, ATR, OBV, Ichimoku, Parabolic SAR)"""
        if max_workers is None:
            max_workers = min(mp.cpu_count(), 32)  # Use up to 32 cores for 9950X3D

        self.logger.info(f"开始参数优化，使用 {max_workers} 个线程，策略类型: {strategy_type}")

        results = []

        # 原有4种策略
        if strategy_type in ['all', 'ma']:
            self.logger.info("优化 MA 交叉策略...")
            ma_results = self._optimize_ma_parameters(max_workers)
            results.extend(ma_results)

        if strategy_type in ['all', 'rsi']:
            self.logger.info("优化 RSI 策略...")
            rsi_results = self._optimize_rsi_parameters(max_workers)
            results.extend(rsi_results)

        if strategy_type in ['all', 'macd']:
            self.logger.info("优化 MACD 策略...")
            macd_results = self._optimize_macd_parameters(max_workers)
            results.extend(macd_results)

        if strategy_type in ['all', 'bb']:
            self.logger.info("优化布林带策略...")
            bb_results = self._optimize_bb_parameters(max_workers)
            results.extend(bb_results)

        # 新增7种高级指标策略
        if strategy_type in ['all', 'kdj']:
            self.logger.info("优化 KDJ 策略...")
            kdj_results = self._optimize_kdj_parameters(max_workers)
            results.extend(kdj_results)

        if strategy_type in ['all', 'cci']:
            self.logger.info("优化 CCI 策略...")
            cci_results = self._optimize_cci_parameters(max_workers)
            results.extend(cci_results)

        if strategy_type in ['all', 'adx']:
            self.logger.info("优化 ADX 策略...")
            adx_results = self._optimize_adx_parameters(max_workers)
            results.extend(adx_results)

        if strategy_type in ['all', 'atr']:
            self.logger.info("优化 ATR 策略...")
            atr_results = self._optimize_atr_parameters(max_workers)
            results.extend(atr_results)

        if strategy_type in ['all', 'obv']:
            self.logger.info("优化 OBV 策略...")
            obv_results = self._optimize_obv_parameters(max_workers)
            results.extend(obv_results)

        if strategy_type in ['all', 'ichimoku']:
            self.logger.info("优化 Ichimoku 策略...")
            ichimoku_results = self._optimize_ichimoku_parameters(max_workers)
            results.extend(ichimoku_results)

        if strategy_type in ['all', 'parabolic_sar']:
            self.logger.info("优化 Parabolic SAR 策略...")
            sar_results = self._optimize_parabolic_sar_parameters(max_workers)
            results.extend(sar_results)

        # 按Sharpe比率排序
        results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)

        self.logger.info(f"参数优化完成，共测试 {len(results)} 个策略组合")
        return results
    
    def _optimize_ma_parameters(self, max_workers: int) -> List[Dict]:
        """Optimize MA parameters using multiprocessing"""
        results = []
        short_windows = range(5, 51, 5)
        long_windows = range(20, 201, 10)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for short, long in product(short_windows, long_windows):
                if short < long:
                    future = executor.submit(self.run_ma_crossover_strategy, short, long)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results
    
    def _optimize_rsi_parameters(self, max_workers: int) -> List[Dict]:
        """优化RSI参数"""
        results = []
        oversold_values = range(20, 41, 5)
        overbought_values = range(60, 81, 5)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for oversold, overbought in product(oversold_values, overbought_values):
                if oversold < overbought:
                    future = executor.submit(self.run_rsi_strategy, 14, oversold, overbought)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results
    
    def _optimize_macd_parameters(self, max_workers: int) -> List[Dict]:
        """优化MACD参数"""
        results = []
        fast_values = range(8, 17, 2)
        slow_values = range(20, 31, 2)
        signal_values = range(7, 12, 1)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for fast, slow, signal in product(fast_values, slow_values, signal_values):
                if fast < slow:
                    future = executor.submit(self.run_macd_strategy, fast, slow, signal)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results
    
    def _optimize_bb_parameters(self, max_workers: int) -> List[Dict]:
        """优化布林带参数"""
        results = []
        periods = range(15, 26, 2)
        std_devs = [1.5, 2.0, 2.5]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for period, std_dev in product(periods, std_devs):
                future = executor.submit(self.run_bollinger_bands_strategy, period, std_dev)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    # ==================== 7个新增策略的参数优化方法 ====================

    def _optimize_kdj_parameters(self, max_workers: int) -> List[Dict]:
        """优化KDJ参数 (K/D周期 5-30步距5，阈值 20-80步距5)"""
        results = []
        k_periods = range(5, 31, 5)
        d_periods = range(3, 6, 1)
        oversold_values = range(20, 41, 5)
        overbought_values = range(60, 81, 5)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for k_p, d_p, os, ob in product(k_periods, d_periods, oversold_values, overbought_values):
                if os < ob:
                    future = executor.submit(self.run_kdj_strategy, k_p, d_p, os, ob)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_cci_parameters(self, max_workers: int) -> List[Dict]:
        """优化CCI参数 (周期 10-30步距5，阈值 -300至+300步距25)"""
        results = []
        periods = range(10, 31, 5)
        oversold_values = range(-300, -75, 50)
        overbought_values = range(75, 325, 50)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for period, os, ob in product(periods, oversold_values, overbought_values):
                future = executor.submit(self.run_cci_strategy, period, os, ob)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_adx_parameters(self, max_workers: int) -> List[Dict]:
        """优化ADX参数 (周期 10-30步距5，阈值 15-50步距5)"""
        results = []
        periods = range(10, 31, 5)
        adx_thresholds = range(15, 51, 5)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for period, threshold in product(periods, adx_thresholds):
                future = executor.submit(self.run_adx_strategy, period, threshold)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_atr_parameters(self, max_workers: int) -> List[Dict]:
        """优化ATR参数 (周期 10-30步距5，倍数 0.5-5.0步距0.5)"""
        results = []
        periods = range(10, 31, 5)
        multipliers = [round(x * 0.5, 1) for x in range(1, 11)]  # 0.5 到 5.0

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for period, multiplier in product(periods, multipliers):
                future = executor.submit(self.run_atr_strategy, period, multiplier)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_obv_parameters(self, max_workers: int) -> List[Dict]:
        """优化OBV参数 (趋势周期 10-100步距10)"""
        results = []
        trend_periods = range(10, 101, 10)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for trend_period in trend_periods:
                future = executor.submit(self.run_obv_strategy, trend_period)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_ichimoku_parameters(self, max_workers: int) -> List[Dict]:
        """优化Ichimoku参数 (转换线 5-15步距5，基准线 20-40步距5，延迟线 40-60步距5)"""
        results = []
        conversion_periods = range(5, 16, 5)
        base_periods = range(20, 41, 5)
        span_b_periods = range(40, 61, 5)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for conv, base, span_b in product(conversion_periods, base_periods, span_b_periods):
                future = executor.submit(self.run_ichimoku_strategy, conv, base, span_b)
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def _optimize_parabolic_sar_parameters(self, max_workers: int) -> List[Dict]:
        """优化Parabolic SAR参数 (加速因子 0.01-0.2步距0.01，最大加速 0.1-0.5步距0.05)"""
        results = []
        accelerations = [round(x * 0.01, 2) for x in range(1, 21)]  # 0.01 到 0.20
        max_accelerations = [round(0.1 + x * 0.05, 2) for x in range(0, 9)]  # 0.1 到 0.5

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for accel, max_accel in product(accelerations, max_accelerations):
                if accel < max_accel:  # 确保初始加速因子小于最大值
                    future = executor.submit(self.run_parabolic_sar_strategy, accel, max_accel)
                    futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results

    def get_best_strategies(self, top_n: int = 10) -> List[Dict]:
        """获取最佳策略"""
        if not self.results:
            self.logger.warning("没有回测结果，请先运行参数优化")
            return []
        
        return self.results[:top_n]
    
    def generate_report(self, output_file: str = None) -> str:
        """生成回测报告"""
        if not self.results:
            return "没有回测结果"
        
        report = f"""
# {self.symbol} 策略回测报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
回测期间: {self.start_date} 至 {self.end_date}
测试策略数量: {len(self.results)}

## 最佳策略 (按Sharpe比率排序)

"""
        
        for i, strategy in enumerate(self.results[:10], 1):
            report += f"""
### {i}. {strategy['strategy_name']}
- 总收益率: {strategy['total_return']:.2f}%
- 年化收益率: {strategy['annual_return']:.2f}%
- 波动率: {strategy['volatility']:.2f}%
- Sharpe比率: {strategy['sharpe_ratio']:.3f}
- 最大回撤: {strategy['max_drawdown']:.2f}%
- 胜率: {strategy['win_rate']:.2f}%
- 交易次数: {strategy['trade_count']}
- 最终价值: ¥{strategy['final_value']:,.2f}

"""
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"报告已保存到: {output_file}")
        
        return report

def main():
    """Main function - example usage"""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create backtest instance
    backtest = EnhancedStrategyBacktest('0700.HK', '2020-01-01', '2023-01-01')

    # Load data
    if not backtest.load_data():
        return

    # Run parameter optimization with 32 threads
    print("Starting parameter optimization with 32 threads...")
    backtest.optimize_parameters(strategy_type='all', max_workers=32)

    # Get best strategies
    best_strategies = backtest.get_best_strategies(10)

    # Generate report
    report = backtest.generate_report('strategy_backtest_report.txt')
    try:
        print(report)
    except UnicodeEncodeError:
        # Handle encoding issue on Windows
        print("Report generated and saved to strategy_backtest_report.txt")
        print("Note: Some characters could not be displayed in console due to encoding")

if __name__ == "__main__":
    main()
