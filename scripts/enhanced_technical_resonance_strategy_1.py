#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 技术指标共振策略 - 增加信号源提升交易频率
Enhanced Technical-Indicator Resonance Strategy

结合阿程的洞察 + 技术指标 (Z-SCORE, RSI, SMA, MACD等)
解决非价格数据信号少的问题

核心改进：
1. 加入技术指标 (Z-SCORE标准化, RSI, SMA, MACD等)
2. 增加信号触发条件
3. 参考阿程的连续信号逻辑
4. 降低阈值增加交易频率
5. 多时间框架确认
"""

import pandas as pd
import numpy as np
from nonprice_strategy_backtest import NonPriceDataBacktest
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class EnhancedTechnicalResonanceStrategy:
    """
    技术指标共振策略
    结合非价格数据 + 技术指标，提升信号频率
    """

    def __init__(self, symbol: str, start_date: str = '2022-04-27', end_date: str = '2025-10-31'):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.backtest = NonPriceDataBacktest(symbol, start_date, end_date)
        self.data = None

    def load_data(self) -> bool:
        """加载数据"""
        return self.backtest.load_integrated_data()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        Z-SCORE标准化, RSI, SMA, MACD, Bollinger Bands等
        """
        # 确保数值列为数字类型
        numeric_cols = ['Close', 'Volume', 'HIBOR_Overnight_%', 'Visitor_Count', 'Traffic_Speed_kmh']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 1. Z-SCORE标准化 (基于价格)
        df['Close_ZScore'] = (df['Close'] - df['Close'].rolling(window=20).mean()) / df['Close'].rolling(window=20).std()

        # 2. RSI 相对强弱指数
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 3. SMA 移动平均
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()

        # 4. MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 5. Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])

        # 6. 成交量指标
        if 'Volume' in df.columns and df['Volume'].notna().any():
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        else:
            df['Volume_Ratio'] = 1.0

        # 7. 动量指标
        df['ROC'] = df['Close'].pct_change(periods=10) * 100  # Rate of Change
        df['Momentum'] = df['Close'] - df['Close'].shift(10)

        return df

    def calculate_nonprice_technical_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算非价格数据的技术指标信号
        参考阿程的连续信号逻辑
        """
        # 1. HIBOR Z-SCORE (标准化)
        hibor_mean = df['HIBOR_Overnight_%'].rolling(window=60).mean()
        hibor_std = df['HIBOR_Overnight_%'].rolling(window=60).std()
        df['HIBOR_ZScore'] = (df['HIBOR_Overnight_%'] - hibor_mean) / hibor_std

        # 2. HIBOR连续信号 (参考阿程)
        df['HIBOR_Return_1d'] = df['HIBOR_Overnight_%'].pct_change(1)
        df['HIBOR_Return_2d'] = df['HIBOR_Overnight_%'].pct_change(2)
        df['HIBOR_Return_3d'] = df['HIBOR_Overnight_%'].pct_change(3)

        # 3. 访客数移动平均和Z-SCORE
        df['Visitor_MA_3'] = df['Visitor_Count'].rolling(window=3).mean()
        df['Visitor_ZScore'] = (df['Visitor_Count'] - df['Visitor_Count'].rolling(window=60).mean()) / df['Visitor_Count'].rolling(window=60).std()

        # 4. 交通速度Z-SCORE
        df['Traffic_ZScore'] = (df['Traffic_Speed_kmh'] - df['Traffic_Speed_kmh'].rolling(window=60).mean()) / df['Traffic_Speed_kmh'].rolling(window=60).std()

        # 5. 组合指标 Z-SCORE (多指标共振)
        df['Composite_NonPrice_ZScore'] = (
            df['HIBOR_ZScore'] * 0.4 +
            df['Visitor_ZScore'] * 0.3 +
            df['Traffic_ZScore'] * 0.3
        )

        return df

    def generate_technical_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成技术指标信号
        多重确认机制提升信号质量
        """
        # 初始化所有信号为HOLD
        df['Signal'] = 'HOLD'

        # 1. 价格技术指标信号
        df['Price_Tech_Signal'] = 'HOLD'

        # RSI信号
        df.loc[df['RSI'] < 30, 'RSI_Signal'] = 'BUY'
        df.loc[df['RSI'] > 70, 'RSI_Signal'] = 'SELL'
        df['RSI_Signal'] = df['RSI_Signal'].fillna('HOLD')

        # SMA信号 (金叉死叉)
        df.loc[(df['SMA_5'] > df['SMA_20']) & (df['SMA_5'].shift(1) <= df['SMA_20'].shift(1)), 'SMA_Signal'] = 'BUY'
        df.loc[(df['SMA_5'] < df['SMA_20']) & (df['SMA_5'].shift(1) >= df['SMA_20'].shift(1)), 'SMA_Signal'] = 'SELL'
        df['SMA_Signal'] = df['SMA_Signal'].fillna('HOLD')

        # MACD信号
        df.loc[(df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)), 'MACD_Signal_Trigger'] = 'BUY'
        df.loc[(df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1)), 'MACD_Signal_Trigger'] = 'SELL'
        df['MACD_Signal_Trigger'] = df['MACD_Signal_Trigger'].fillna('HOLD')

        # Bollinger Bands信号
        df.loc[df['Close'] < df['BB_Lower'], 'BB_Signal'] = 'BUY'
        df.loc[df['Close'] > df['BB_Upper'], 'BB_Signal'] = 'SELL'
        df['BB_Signal'] = df['BB_Signal'].fillna('HOLD')

        # Z-SCORE信号
        df.loc[df['Close_ZScore'] < -2, 'ZScore_Signal'] = 'BUY'  # 超卖
        df.loc[df['Close_ZScore'] > 2, 'ZScore_Signal'] = 'SELL'  # 超买
        df['ZScore_Signal'] = df['ZScore_Signal'].fillna('HOLD')

        # 2. 非价格数据技术信号
        df['NonPrice_Signal'] = 'HOLD'

        # HIBOR连续信号 (参考阿程的4天逻辑)
        hibor_4day = df['HIBOR_Overnight_%'].pct_change(4)
        df.loc[hibor_4day > 0.002, 'HIBOR_Cont_Signal'] = 'SELL'  # 4天涨幅>0.2%，卖银行股
        df.loc[hibor_4day < -0.002, 'HIBOR_Cont_Signal'] = 'BUY'  # 4天跌幅>0.2%，买银行股
        df['HIBOR_Cont_Signal'] = df['HIBOR_Cont_Signal'].fillna('HOLD')

        # 非价格数据Z-SCORE信号
        df.loc[df['Composite_NonPrice_ZScore'] > 1, 'NonPrice_ZScore_Signal'] = 'SELL'
        df.loc[df['Composite_NonPrice_ZScore'] < -1, 'NonPrice_ZScore_Signal'] = 'BUY'
        df['NonPrice_ZScore_Signal'] = df['NonPrice_ZScore_Signal'].fillna('HOLD')

        # 3. 组合技术指标信号
        # 统计各技术指标的买入/卖出信号数量
        buy_signals = (
            (df['RSI_Signal'] == 'BUY').astype(int) +
            (df['SMA_Signal'] == 'BUY').astype(int) +
            (df['MACD_Signal_Trigger'] == 'BUY').astype(int) +
            (df['BB_Signal'] == 'BUY').astype(int) +
            (df['ZScore_Signal'] == 'BUY').astype(int) +
            (df['HIBOR_Cont_Signal'] == 'BUY').astype(int) +
            (df['NonPrice_ZScore_Signal'] == 'BUY').astype(int)
        )

        sell_signals = (
            (df['RSI_Signal'] == 'SELL').astype(int) +
            (df['SMA_Signal'] == 'SELL').astype(int) +
            (df['MACD_Signal_Trigger'] == 'SELL').astype(int) +
            (df['BB_Signal'] == 'SELL').astype(int) +
            (df['ZScore_Signal'] == 'SELL').astype(int) +
            (df['HIBOR_Cont_Signal'] == 'SELL').astype(int) +
            (df['NonPrice_ZScore_Signal'] == 'SELL').astype(int)
        )

        df['Buy_Signal_Count'] = buy_signals
        df['Sell_Signal_Count'] = sell_signals

        # 4. 生成最终信号 (降低阈值至2个指标)
        # 买入条件：2个或以上指标买入 OR Z-SCORE极端值
        buy_condition = (
            (buy_signals >= 2) |  # 2个以上技术指标买入
            (df['Close_ZScore'] < -2) |  # Z-SCORE超卖
            (df['RSI'] < 25) |  # RSI极值
            (df['HIBOR_ZScore'] < -1.5)  # HIBOR极端值
        )

        # 卖出条件：2个或以上指标卖出 OR Z-SCORE极端值
        sell_condition = (
            (sell_signals >= 2) |  # 2个以上技术指标卖出
            (df['Close_ZScore'] > 2) |  # Z-SCORE超买
            (df['RSI'] > 75) |  # RSI极值
            (df['HIBOR_ZScore'] > 1.5)  # HIBOR极端值
        )

        df.loc[buy_condition, 'Signal'] = 'BUY'
        df.loc[sell_condition, 'Signal'] = 'SELL'

        return df

    def run_enhanced_technical_resonance_strategy(self, initial_capital: float = 100000.0) -> Dict:
        """
        运行增强版技术指标共振策略
        """
        print("\n" + "="*100)
        print("ENHANCED TECHNICAL-RESONANCE STRATEGY")
        print("Combining Non-Price Data + Technical Indicators (Z-SCORE, RSI, SMA, MACD)")
        print("="*100)

        # 1. 加载数据
        if not self.load_data():
            return {"error": "Data loading failed"}

        df = self.backtest.data.copy().sort_values('Date').reset_index(drop=True)

        # 2. 计算技术指标
        print("\n[CALCULATING TECHNICAL INDICATORS]")
        df = self.calculate_technical_indicators(df)
        df = self.calculate_nonprice_technical_signals(df)

        print(f"  Calculated: RSI, SMA(5/10/20/50), MACD, Bollinger Bands, Z-SCORE")
        print(f"  Calculated: HIBOR/Visitor/Traffic Z-SCORE, 4-day consecutive signals")

        # 3. 生成信号
        print("\n[GENERATING SIGNALS]")
        df = self.generate_technical_signals(df)

        # 4. 运行回测
        result = self.backtest._backtest(df, 'Enhanced Technical-Resonance Strategy', initial_capital)

        # 5. 详细分析
        buy_signals = (df['Signal'] == 'BUY').sum()
        sell_signals = (df['Signal'] == 'SELL').sum()
        total_signals = buy_signals + sell_signals

        print(f"\n[STRATEGY ANALYSIS]")
        print(f"  Total Signals: {total_signals} ({total_signals/len(df)*100:.1f}% of days)")
        print(f"  Buy Signals: {buy_signals} ({buy_signals/len(df)*100:.1f}% of days)")
        print(f"  Sell Signals: {sell_signals} ({sell_signals/len(df)*100:.1f}% of days)")
        print(f"  Max Buy Signals per Day: {df['Buy_Signal_Count'].max()}")
        print(f"  Max Sell Signals per Day: {df['Sell_Signal_Count'].max()}")
        print(f"  Avg Signals per Day: {df['Buy_Signal_Count'].mean() + df['Sell_Signal_Count'].mean():.2f}")

        # 6. 技术指标贡献分析
        print(f"\n[TECHNICAL INDICATOR CONTRIBUTION]")
        print(f"  RSI Triggers: {df['RSI_Signal'].value_counts().get('BUY', 0)} BUY, {df['RSI_Signal'].value_counts().get('SELL', 0)} SELL")
        print(f"  SMA Triggers: {df['SMA_Signal'].value_counts().get('BUY', 0)} BUY, {df['SMA_Signal'].value_counts().get('SELL', 0)} SELL")
        print(f"  MACD Triggers: {df['MACD_Signal_Trigger'].value_counts().get('BUY', 0)} BUY, {df['MACD_Signal_Trigger'].value_counts().get('SELL', 0)} SELL")
        print(f"  BB Triggers: {df['BB_Signal'].value_counts().get('BUY', 0)} BUY, {df['BB_Signal'].value_counts().get('SELL', 0)} SELL")
        print(f"  Z-SCORE Triggers: {df['ZScore_Signal'].value_counts().get('BUY', 0)} BUY, {df['ZScore_Signal'].value_counts().get('SELL', 0)} SELL")

        # 7. 非价格数据贡献
        print(f"\n[NON-PRICE DATA CONTRIBUTION]")
        print(f"  HIBOR Consecutive Signals: {df['HIBOR_Cont_Signal'].value_counts().get('BUY', 0)} BUY, {df['HIBOR_Cont_Signal'].value_counts().get('SELL', 0)} SELL")
        print(f"  NonPrice Z-SCORE: {df['NonPrice_ZScore_Signal'].value_counts().get('BUY', 0)} BUY, {df['NonPrice_ZScore_Signal'].value_counts().get('SELL', 0)} SELL")

        # 8. 添加分析结果
        result['technical_analysis'] = {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'signal_frequency_pct': total_signals/len(df)*100,
            'max_buy_count': df['Buy_Signal_Count'].max(),
            'max_sell_count': df['Sell_Signal_Count'].max(),
            'avg_signals_per_day': df['Buy_Signal_Count'].mean() + df['Sell_Signal_Count'].mean(),
            'rsi_contribution': {
                'buy': df['RSI_Signal'].value_counts().get('BUY', 0),
                'sell': df['RSI_Signal'].value_counts().get('SELL', 0)
            },
            'sma_contribution': {
                'buy': df['SMA_Signal'].value_counts().get('BUY', 0),
                'sell': df['SMA_Signal'].value_counts().get('SELL', 0)
            },
            'hibor_contribution': {
                'buy': df['HIBOR_Cont_Signal'].value_counts().get('BUY', 0),
                'sell': df['HIBOR_Cont_Signal'].value_counts().get('SELL', 0)
            }
        }

        print(f"\n[FINAL PERFORMANCE]")
        print(f"  Total Return: {result.get('total_return_pct', 0):.2f}%")
        print(f"  Annual Return: {result.get('annual_return_pct', 0):.2f}%")
        print(f"  Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {result.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Total Trades: {result.get('total_trades', 0)}")

        return result


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Technical-Resonance Strategy')
    parser.add_argument('--symbol', type=str, default='0700', help='Stock symbol')
    parser.add_argument('--start', type=str, default='2022-04-27', help='Start date')
    parser.add_argument('--end', type=str, default='2025-10-31', help='End date')

    args = parser.parse_args()

    # 运行策略
    strategy = EnhancedTechnicalResonanceStrategy(args.symbol, args.start, args.end)
    result = strategy.run_enhanced_technical_resonance_strategy()

    print("\n" + "="*100)
    print("ENHANCED TECHNICAL-RESONANCE STRATEGY COMPLETED!")
    print("="*100)


if __name__ == "__main__":
    main()
