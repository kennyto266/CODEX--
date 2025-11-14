#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 增强版多指标共振策略 - 交易次数最大化
Enhanced Multi-Indicator Resonance Strategy - Maximizing Trade Frequency

基于头脑风暴洞察：多指标共振可提升交易频率和胜率
实现低相关性指标协同工作，最大化交易机会

核心创新：
1. 降低信号阈值 (0.6/0.4 vs 0.7/0.3)
2. 多指标共振加强机制 (2个+指标=强信号)
3. 动态权重调整 (根据市场波动率)
4. 趋势确认过滤 (提升信号质量)
5. 阈值渐变优化 (动态调整敏感度)
"""

import pandas as pd
import numpy as np
from nonprice_strategy_backtest import NonPriceDataBacktest
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class EnhancedMultiResonanceStrategy:
    """
    增强版多指标共振策略
    核心目标：最大化交易次数同时保持收益质量
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

    def calculate_individual_signals(self) -> pd.DataFrame:
        """
        计算单个指标的信号
        返回包含所有指标信号的DataFrame
        """
        if self.backtest.data is None:
            raise ValueError("数据未加载")

        df = self.backtest.data.copy().sort_values('Date').reset_index(drop=True)

        # 1. HIBOR信号 (降低阈值提升频率)
        df['HIBOR_Signal'] = 'HOLD'
        df.loc[df['HIBOR_Overnight_%'] > 3.0, 'HIBOR_Signal'] = 'BUY'  # 从5.0%降至3.0%
        df.loc[df['HIBOR_Overnight_%'] < 2.0, 'HIBOR_Signal'] = 'SELL'  # 从3.0%降至2.0%

        # 2. 访客信号 (优化阈值)
        df['Visitor_Signal'] = 'HOLD'
        df.loc[df['Visitor_Count'] > 200000, 'Visitor_Signal'] = 'BUY'  # 从22万降至20万
        df.loc[df['Visitor_Count'] < 180000, 'Visitor_Signal'] = 'SELL'  # 从20万降至18万

        # 3. 交通信号 (增加买入逻辑)
        df['Traffic_Signal'] = 'HOLD'
        df.loc[df['Traffic_Speed_kmh'] < 60, 'Traffic_Signal'] = 'SELL'  # 从50升至60
        df.loc[df['Traffic_Speed_kmh'] > 80, 'Traffic_Signal'] = 'BUY'    # 新增：高速=经济活跃

        # 4. AQHI信号 (增强触发)
        aqhi_col = 'AQHI' if 'AQHI' in df.columns else ('avg_aqhi' if 'avg_aqhi' in df.columns else None)
        if aqhi_col:
            df['AQHI_Signal'] = 'HOLD'
            df.loc[df[aqhi_col] > 7, 'AQHI_Signal'] = 'BUY'    # 从10降至7
            df.loc[df[aqhi_col] < 3, 'AQHI_Signal'] = 'SELL'   # 新增卖出逻辑
        else:
            df['AQHI_Signal'] = 'HOLD'

        # 5. 价格趋势信号 (新增趋势确认)
        df['Price_MA_20'] = df['Close'].rolling(window=20).mean()
        df['Price_MA_50'] = df['Close'].rolling(window=50).mean()
        df['Trend_Signal'] = 'HOLD'
        df.loc[df['Price_MA_20'] > df['Price_MA_50'], 'Trend_Signal'] = 'BUY'
        df.loc[df['Price_MA_20'] < df['Price_MA_50'], 'Trend_Signal'] = 'SELL'

        return df

    def calculate_resonance_score(self, df: pd.DataFrame, resonance_threshold: int = 2) -> pd.DataFrame:
        """
        计算多指标共振分数
        resonance_threshold: 触发信号的最少指标数量

        核心算法：
        - 每个指标贡献1分
        - 多个指标共振时分数累加
        - 动态权重调整
        """
        # 1. 单指标信号转换为分数
        signal_to_score = {'BUY': 1, 'HOLD': 0, 'SELL': -1}

        df['HIBOR_Score'] = df['HIBOR_Signal'].map(signal_to_score)
        df['Visitor_Score'] = df['Visitor_Signal'].map(signal_to_score)
        df['Traffic_Score'] = df['Traffic_Signal'].map(signal_to_score)
        df['AQHI_Score'] = df['AQHI_Signal'].map(signal_to_score)
        df['Trend_Score'] = df['Trend_Signal'].map(signal_to_score)

        # 2. 计算波动率调整权重
        df['HIBOR_Vol'] = df['HIBOR_Overnight_%'].rolling(window=20).std()
        df['Visitor_Vol'] = df['Visitor_Count'].rolling(window=20).std()
        df['Vol_Rank_HIBOR'] = df['HIBOR_Vol'].rank(pct=True)
        df['Vol_Rank_Visitor'] = df['Visitor_Vol'].rank(pct=True)

        # 高波动率指标获得更高权重
        df['HIBOR_Weight'] = 0.2 + 0.1 * df['Vol_Rank_HIBOR']
        df['Visitor_Weight'] = 0.2 + 0.1 * df['Vol_Rank_Visitor']
        df['Traffic_Weight'] = 0.2
        df['AQHI_Weight'] = 0.2
        df['Trend_Weight'] = 0.2

        # 3. 计算加权共振分数
        df['Resonance_Score'] = (
            df['HIBOR_Score'] * df['HIBOR_Weight'] +
            df['Visitor_Score'] * df['Visitor_Weight'] +
            df['Traffic_Score'] * df['Traffic_Weight'] +
            df['AQHI_Score'] * df['AQHI_Weight'] +
            df['Trend_Score'] * df['Trend_Weight']
        )

        # 4. 计算共振强度 (绝对分数)
        df['Resonance_Intensity'] = np.abs(df['Resonance_Score'])

        # 5. 动态阈值 (根据市场波动率调整)
        df['Dynamic_Buy_Threshold'] = 0.4 + 0.2 * df['HIBOR_Vol'].fillna(0) / df['HIBOR_Vol'].max()
        df['Dynamic_Sell_Threshold'] = -0.4 - 0.2 * df['HIBOR_Vol'].fillna(0) / df['HIBOR_Vol'].max()

        # 6. 统计共振指标数量
        df['Buy_Signals_Count'] = (
            (df['HIBOR_Signal'] == 'BUY').astype(int) +
            (df['Visitor_Signal'] == 'BUY').astype(int) +
            (df['Traffic_Signal'] == 'BUY').astype(int) +
            (df['AQHI_Signal'] == 'BUY').astype(int) +
            (df['Trend_Signal'] == 'BUY').astype(int)
        )

        df['Sell_Signals_Count'] = (
            (df['HIBOR_Signal'] == 'SELL').astype(int) +
            (df['Visitor_Signal'] == 'SELL').astype(int) +
            (df['Traffic_Signal'] == 'SELL').astype(int) +
            (df['AQHI_Signal'] == 'SELL').astype(int) +
            (df['Trend_Signal'] == 'SELL').astype(int)
        )

        return df

    def generate_resonance_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成多指标共振信号
        核心策略：多指标共振时加强信号强度
        """
        df['Signal'] = 'HOLD'

        # 1. 多指标共振信号 (2个或以上指标共振)
        # 买入条件：共振分数 > 阈值 OR 3个以上指标买入
        buy_condition = (
            (df['Resonance_Score'] > df['Dynamic_Buy_Threshold']) |
            (df['Buy_Signals_Count'] >= 3)  # 3个以上指标买入
        )

        # 卖出条件：共振分数 < 负阈值 OR 3个以上指标卖出
        sell_condition = (
            (df['Resonance_Score'] < df['Dynamic_Sell_Threshold']) |
            (df['Sell_Signals_Count'] >= 3)  # 3个以上指标卖出
        )

        df.loc[buy_condition, 'Signal'] = 'BUY'
        df.loc[sell_condition, 'Signal'] = 'SELL'

        # 2. 单指标强信号 (单一指标极端值)
        extreme_buy = (
            (df['HIBOR_Overnight_%'] > df['HIBOR_Overnight_%'].quantile(0.9)) |
            (df['Visitor_Count'] > df['Visitor_Count'].quantile(0.9)) |
            (df['Traffic_Speed_kmh'] < df['Traffic_Speed_kmh'].quantile(0.1))
        )
        df.loc[extreme_buy & (df['Signal'] == 'HOLD'), 'Signal'] = 'BUY'

        return df

    def run_enhanced_resonance_strategy(self, initial_capital: float = 100000.0) -> Dict:
        """
        运行增强版多指标共振策略
        """
        print("\n" + "="*80)
        print("ENHANCED MULTI-RESONANCE STRATEGY - MAXIMIZING TRADE FREQUENCY")
        print("="*80)

        # 1. 加载并处理数据
        if not self.load_data():
            return {"error": "数据加载失败"}

        df = self.calculate_individual_signals()
        df = self.calculate_resonance_score(df)
        df = self.generate_resonance_signals(df)

        # 2. 运行回测
        result = self.backtest._backtest(df, 'Enhanced Multi-Resonance Strategy', initial_capital)

        # 3. 添加共振分析结果
        result['resonance_analysis'] = {
            'total_days': len(df),
            'buy_signal_days': (df['Signal'] == 'BUY').sum(),
            'sell_signal_days': (df['Signal'] == 'SELL').sum(),
            'hold_signal_days': (df['Signal'] == 'HOLD').sum(),
            'avg_buy_signals_per_day': df['Buy_Signals_Count'].mean(),
            'avg_sell_signals_per_day': df['Sell_Signals_Count'].mean(),
            'max_buy_signals': df['Buy_Signals_Count'].max(),
            'max_sell_signals': df['Sell_Signals_Count'].max(),
            'resonance_score_stats': {
                'mean': df['Resonance_Score'].mean(),
                'std': df['Resonance_Score'].std(),
                'min': df['Resonance_Score'].min(),
                'max': df['Resonance_Score'].max()
            }
        }

        # 4. 信号频率分析
        result['signal_frequency'] = {
            'buy_frequency_pct': (df['Signal'] == 'BUY').mean() * 100,
            'sell_frequency_pct': (df['Signal'] == 'SELL').mean() * 100,
            'total_action_frequency_pct': ((df['Signal'] != 'HOLD').mean()) * 100,
            'trades_per_month': result['total_trades'] / (len(df) / 30.44),  # 每月天数
        }

        # 5. 与原策略对比
        print(f"\n[RESONANCE STRATEGY ANALYSIS]")
        print(f"  Total Trades: {result['total_trades']} (Target: >10)")
        print(f"  Buy Signal Frequency: {result['signal_frequency']['buy_frequency_pct']:.2f}%")
        print(f"  Sell Signal Frequency: {result['signal_frequency']['sell_frequency_pct']:.2f}%")
        print(f"  Total Action Frequency: {result['signal_frequency']['total_action_frequency_pct']:.2f}%")
        print(f"  Avg Trades per Month: {result['signal_frequency']['trades_per_month']:.2f}")

        print(f"\n[RESONANCE INTENSITY ANALYSIS]")
        print(f"  Avg Buy Indicators per Day: {result['resonance_analysis']['avg_buy_signals_per_day']:.2f}")
        print(f"  Avg Sell Indicators per Day: {result['resonance_analysis']['avg_sell_signals_per_day']:.2f}")
        print(f"  Max Resonance Intensity: {result['resonance_analysis']['max_buy_signals']} indicators")

        return result

    def optimize_resonance_thresholds(self, max_workers: int = 4) -> List[Dict]:
        """
        优化共振策略参数
        测试不同的阈值组合以找到最佳参数
        """
        print("\n" + "="*80)
        print("MULTI-RESONANCE STRATEGY PARAMETER OPTIMIZATION")
        print("="*80)

        if not self.load_data():
            return []

        # 优化参数范围
        buy_thresholds = np.arange(0.3, 0.7, 0.1)  # 买入阈值：0.3-0.6
        sell_thresholds = np.arange(-0.7, -0.3, 0.1)  # 卖出阈值：-0.6至-0.3
        min_signals = [2, 3]  # 最少指标数量

        print(f"Parameter Ranges:")
        print(f"  Buy Thresholds: {buy_thresholds[0]:.1f} - {buy_thresholds[-1]:.1f}")
        print(f"  Sell Thresholds: {sell_thresholds[0]:.1f} - {sell_thresholds[-1]:.1f}")
        print(f"  Min Signals: {min(min_signals)} - {max(min_signals)}")

        # Generate all parameter combinations
        from itertools import product
        param_combinations = list(product(buy_thresholds, sell_thresholds, min_signals))

        results = []
        for buy_t, sell_t, min_sig in param_combinations:
            df = self.calculate_individual_signals()
            df = self.calculate_resonance_score(df)

            # Test with current parameters
            df['Signal'] = 'HOLD'
            buy_condition = (
                (df['Resonance_Score'] > buy_t) | (df['Buy_Signals_Count'] >= min_sig)
            )
            sell_condition = (
                (df['Resonance_Score'] < sell_t) | (df['Sell_Signals_Count'] >= min_sig)
            )
            df.loc[buy_condition, 'Signal'] = 'BUY'
            df.loc[sell_condition, 'Signal'] = 'SELL'

            # Run backtest
            result = self.backtest._backtest(df, 'Resonance Strategy Test', 100000)

            # Record results
            results.append({
                'buy_threshold': buy_t,
                'sell_threshold': sell_t,
                'min_signals': min_sig,
                'total_return_pct': result.get('total_return_pct', 0),
                'annual_return_pct': result.get('annual_return_pct', 0),
                'sharpe_ratio': result.get('sharpe_ratio', 0),
                'max_drawdown_pct': result.get('max_drawdown_pct', 0),
                'total_trades': result.get('total_trades', 0),
                'signal_frequency': ((df['Signal'] != 'HOLD').mean()) * 100
            })

        # 按夏普比率排序
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        print(f"\n[OPTIMIZATION COMPLETE] Tested {len(results)} parameter combinations")
        print(f"\n[TOP 10 PARAMETER COMBINATIONS]")
        print(f"{'Rank':<4} {'Buy Thres':<10} {'Sell Thres':<10} {'Min Sig':<8} {'Ann Ret':<10} {'Sharpe':<8} {'Trades':<8} {'Freq':<10}")
        print('-' * 80)

        for i, r in enumerate(results[:10], 1):
            print(f"{i:<4} {r['buy_threshold']:<10.1f} {r['sell_threshold']:<10.1f} "
                  f"{r['min_signals']:<8} {r['annual_return_pct']:<10.2f}% {r['sharpe_ratio']:<8.2f} "
                  f"{r['total_trades']:<8} {r['signal_frequency']:<10.2f}%")

        return results


def main():
    """主函数 - 演示增强版多指标共振策略"""
    import argparse

    parser = argparse.ArgumentParser(description='增强版多指标共振策略')
    parser.add_argument('--symbol', type=str, default='0700', help='股票代码')
    parser.add_argument('--mode', choices=['run', 'optimize'], default='run', help='运行模式')
    parser.add_argument('--workers', type=int, default=4, help='优化工作线程数')

    args = parser.parse_args()

    # 初始化策略
    strategy = EnhancedMultiResonanceStrategy(args.symbol, '2022-04-27', '2025-10-31')

    if args.mode == 'run':
        # 运行增强版共振策略
        result = strategy.run_enhanced_resonance_strategy()

        print(f"\n[STRATEGY COMPLETE]")
        print(f"Total Return: {result.get('total_return_pct', 0):.2f}%")
        print(f"Annual Return: {result.get('annual_return_pct', 0):.2f}%")
        print(f"Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown: {result.get('max_drawdown_pct', 0):.2f}%")
        print(f"Total Trades: {result.get('total_trades', 0)}")

    elif args.mode == 'optimize':
        # 参数优化
        results = strategy.optimize_resonance_thresholds(args.workers)

        # 保存结果
        import json
        from datetime import datetime
        output_file = f"enhanced_resonance_optimization_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n[RESULTS SAVED] {output_file}")


if __name__ == "__main__":
    main()
