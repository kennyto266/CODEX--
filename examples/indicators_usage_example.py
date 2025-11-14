#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级技术指标使用示例

演示如何使用所有5个高级技术指标进行技术分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# 导入所有指标
from src.strategy.indicators import (
    IchimokuIndicator, calculate_ichimoku,
    KeltnerIndicator, calculate_keltner,
    CMOIndicator, calculate_cmo,
    VROCIndicator, calculate_vroc,
    WilliamsRIndicator, calculate_williams_r,
    StochasticRSIIndicator, calculate_stochastic_rsi,
    OptimizedADXIndicator, calculate_optimized_adx,
    ATRBandsIndicator, calculate_atr_bands,
    ImprovedOBVIndicator, calculate_improved_obv
)


def generate_sample_data(start_date='2020-01-01', end_date='2024-01-01'):
    """
    生成示例市场数据

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        DataFrame: 包含OHLCV数据的DataFrame
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(42)

    # 创建有趋势、周期和噪声的价格数据
    base_price = 100
    trend = np.linspace(0, 50, len(dates))
    cycles = 20 * np.sin(np.linspace(0, 4*np.pi, len(dates)))
    noise = np.random.normal(0, 3, len(dates))
    close_prices = base_price + trend + cycles + noise

    high_prices = close_prices + np.random.uniform(0, 5, len(dates))
    low_prices = close_prices - np.random.uniform(0, 5, len(dates))
    volumes = np.random.lognormal(15, 0.5, len(dates)).astype(int)

    return pd.DataFrame({
        'Open': close_prices - np.random.uniform(0, 2, len(dates)),
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volumes
    }, index=dates)


def example_ichimoku(data):
    """一目均衡表示例"""
    print("\n" + "="*60)
    print("1. 一目均衡表 (Ichimoku Cloud)")
    print("="*60)

    # 创建指标实例
    ichimoku = IchimokuIndicator()

    # 计算指标
    df = ichimoku.calculate(data.copy())

    # 获取最新信号
    signal = ichimoku.get_latest_signal(df)

    print(f"\n最新信号:")
    print(f"  信号: {signal['signal']} ({'买入' if signal['signal'] == 1 else '卖出' if signal['signal'] == -1 else '无信号'})")
    print(f"  强度: {signal['strength']:.2f}")
    print(f"  描述: {signal['description']}")

    print(f"\n指标值:")
    print(f"  转换线 (Tenkan): {signal.get('tenkan', 0):.2f}")
    print(f"  基准线 (Kijun): {signal.get('kijun', 0):.2f}")
    print(f"  云图颜色: {'绿云' if signal.get('cloud_color', 0) == 1 else '红云' if signal.get('cloud_color', 0) == -1 else '中性'}")
    print(f"  价格位置: {'云上' if signal.get('price_position', 0) == 1 else '云下' if signal.get('price_position', 0) == -1 else '云中'}")

    return df


def example_keltner(data):
    """肯特纳通道示例"""
    print("\n" + "="*60)
    print("2. 肯特纳通道 (Keltner Channel)")
    print("="*60)

    keltner = KeltnerIndicator(ema_period=20, atr_period=14, atr_multiplier=2.0)
    df = keltner.calculate(data.copy())

    signal = keltner.get_latest_signal(df)

    print(f"\n最新信号:")
    print(f"  信号: {signal['signal']} ({'买入' if signal['signal'] == 1 else '卖出' if signal['signal'] == -1 else '无信号'})")
    print(f"  强度: {signal['strength']:.2f}")
    print(f"  描述: {signal['description']}")

    print(f"\n指标值:")
    print(f"  上轨: {signal.get('upper', 0):.2f}")
    print(f"  下轨: {signal.get('lower', 0):.2f}")
    print(f"  EMA中心线: {signal.get('ema', 0):.2f}")
    print(f"  ATR: {signal.get('atr', 0):.2f}")
    print(f"  趋势: {'上升' if signal.get('trend', 0) == 1 else '下降' if signal.get('trend', 0) == -1 else '横盘'}")

    return df


def example_cmo(data):
    """CMO示例"""
    print("\n" + "="*60)
    print("3. 钱德动量振荡器 (CMO)")
    print("="*60)

    cmo = CMOIndicator(period=14, upper_threshold=50, lower_threshold=-50)
    df = cmo.calculate(data.copy())

    signal = cmo.get_latest_signal(df)

    print(f"\n最新信号:")
    print(f"  信号: {signal['signal']} ({'买入' if signal['signal'] == 1 else '卖出' if signal['signal'] == -1 else '无信号'})")
    print(f"  强度: {signal['strength']:.2f}")
    print(f"  描述: {signal['description']}")

    print(f"\n指标值:")
    print(f"  CMO: {signal.get('cmo', 0):.2f}")
    print(f"  信号线: {signal.get('signal_line', 0):.2f}")
    print(f"  超买: {'是' if signal.get('overbought', False) else '否'}")
    print(f"  超卖: {'是' if signal.get('oversold', False) else '否'}")
    print(f"  动量: {'强上涨' if signal.get('momentum', 0) == 1 else '上涨' if signal.get('momentum', 0) == 0.5 else '中性' if signal.get('momentum', 0) == 0 else '下跌' if signal.get('momentum', 0) == -0.5 else '强下跌'}")

    return df


def example_vroc(data):
    """VROC示例"""
    print("\n" + "="*60)
    print("4. 成交量变化率 (VROC)")
    print("="*60)

    vroc = VROCIndicator(period=12, threshold=50)
    df = vroc.calculate(data.copy())

    signal = vroc.get_latest_signal(df)

    print(f"\n最新信号:")
    print(f"  信号: {signal['signal']} ({'买入' if signal['signal'] == 1 else '卖出' if signal['signal'] == -1 else '无信号'})")
    print(f"  强度: {signal['strength']:.2f}")
    print(f"  描述: {signal['description']}")

    print(f"\n指标值:")
    print(f"  VROC: {signal.get('vroc', 0):.2f}%")
    print(f"  信号线: {signal.get('signal_line', 0):.2f}%")
    print(f"  成交量: {signal.get('volume', 0):,}")
    print(f"  成交量均线: {signal.get('volume_ma', 0):,.0f}")
    print(f"  量价配合: {'完美' if signal.get('alignment', 0) > 0.8 else '良好' if signal.get('alignment', 0) > 0.5 else '一般' if signal.get('alignment', 0) > 0 else '背离'}")

    return df


def example_advanced_indicators(data):
    """高级指标变体示例"""
    print("\n" + "="*60)
    print("5. 高级指标变体")
    print("="*60)

    # Williams %R
    print("\n  5.1 Williams %R")
    williams_r = WilliamsRIndicator(period=14)
    df_wr = williams_r.calculate(data.copy())
    print(f"    最新值: {df_wr['WilliamsR'].iloc[-1]:.2f}")
    print(f"    超买: {'是' if df_wr['WilliamsR'].iloc[-1] > -20 else '否'}")
    print(f"    超卖: {'是' if df_wr['WilliamsR'].iloc[-1] < -80 else '否'}")

    # Stochastic RSI
    print("\n  5.2 Stochastic RSI")
    stoch_rsi = StochasticRSIIndicator()
    df_srsi = stoch_rsi.calculate(data.copy())
    print(f"    %K: {df_srsi['StochRSI_K'].iloc[-1]:.2f}")
    print(f"    %D: {df_srsi['StochRSI_D'].iloc[-1]:.2f}")
    print(f"    超买: {'是' if df_srsi['StochRSI_K'].iloc[-1] > 80 else '否'}")
    print(f"    超卖: {'是' if df_srsi['StochRSI_K'].iloc[-1] < 20 else '否'}")

    # 优化ADX
    print("\n  5.3 优化的ADX")
    adx = OptimizedADXIndicator()
    df_adx = adx.calculate(data.copy())
    print(f"    ADX: {df_adx['ADX_Opt'].iloc[-1]:.2f}")
    print(f"    +DI: {df_adx['ADX_PlusDI'].iloc[-1]:.2f}")
    print(f"    -DI: {df_adx['ADX_MinusDI'].iloc[-1]:.2f}")
    print(f"    趋势强度: {'强' if df_adx['ADX_Opt'].iloc[-1] > 25 else '弱'}")
    print(f"    趋势方向: {'上升' if df_adx['ADX_PlusDI'].iloc[-1] > df_adx['ADX_MinusDI'].iloc[-1] else '下降'}")

    # ATR带
    print("\n  5.4 ATR带")
    atr_bands = ATRBandsIndicator()
    df_atr = atr_bands.calculate(data.copy())
    print(f"    上轨: {df_atr['ATR_Upper'].iloc[-1]:.2f}")
    print(f"    下轨: {df_atr['ATR_Lower'].iloc[-1]:.2f}")
    print(f"    带宽: {df_atr['ATR_Bandwidth'].iloc[-1]:.2f}%")

    # 改进OBV
    print("\n  5.5 改进的OBV")
    improved_obv = ImprovedOBVIndicator()
    df_obv = improved_obv.calculate(data.copy())
    print(f"    OBV: {df_obv['OBV_Improved'].iloc[-1]:,.0f}")
    print(f"    趋势: {'上升' if df_obv['OBV_Improved_Trend'].iloc[-1] == 1 else '下降' if df_obv['OBV_Improved_Trend'].iloc[-1] == -1 else '横盘'}")


def example_combined_strategy(data):
    """组合策略示例"""
    print("\n" + "="*60)
    print("6. 组合策略示例")
    print("="*60)

    # 计算所有指标
    ichimoku = IchimokuIndicator()
    keltner = KeltnerIndicator()
    cmo = CMOIndicator()
    vroc = VROCIndicator()

    df = data.copy()
    df = ichimoku.calculate(df)
    df = keltner.calculate(df)
    df = cmo.calculate(df)
    df = vroc.calculate(df)

    # 获取所有信号
    signals = {
        'Ichimoku': ichimoku.get_latest_signal(df),
        'Keltner': keltner.get_latest_signal(df),
        'CMO': cmo.get_latest_signal(df),
        'VROC': vroc.get_latest_signal(df)
    }

    print("\n各指标信号:")
    for name, signal in signals.items():
        print(f"  {name:<15}: {signal['description']}")

    # 计算综合信号
    total_signal = sum(sig['signal'] * sig['strength'] for sig in signals.values())
    avg_strength = np.mean([sig['strength'] for sig in signals.values()])

    print(f"\n综合信号:")
    print(f"  总信号: {total_signal:.2f}")
    print(f"  平均强度: {avg_strength:.2f}")

    if total_signal > 0.5:
        print(f"  建议: 买入 (多指标共振)")
    elif total_signal < -0.5:
        print(f"  建议: 卖出 (多指标共振)")
    else:
        print(f"  建议: 观望 (信号不明确)")


def example_performance_comparison(data):
    """性能对比示例"""
    import time

    print("\n" + "="*60)
    print("7. 性能对比")
    print("="*60)

    indicators = {
        'Ichimoku': IchimokuIndicator(),
        'Keltner': KeltnerIndicator(),
        'CMO': CMOIndicator(),
        'VROC': VROCIndicator(),
        'Williams %R': WilliamsRIndicator(),
        'Stochastic RSI': StochasticRSIIndicator(),
        '优化ADX': OptimizedADXIndicator(),
        'ATR带': ATRBandsIndicator(),
        '改进OBV': ImprovedOBVIndicator()
    }

    results = {}

    for name, indicator in indicators.items():
        times = []
        for _ in range(10):
            start_time = time.perf_counter()
            indicator.calculate(data.copy())
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = np.mean(times)
        results[name] = avg_time

    print(f"\n计算时间 (10次平均, 1000行数据):")
    for name, avg_time in sorted(results.items(), key=lambda x: x[1]):
        print(f"  {name:<20}: {avg_time*1000:.2f}ms")


def main():
    """主函数"""
    print("="*60)
    print("高级技术指标使用示例")
    print("="*60)

    # 生成示例数据
    print("\n正在生成示例数据...")
    data = generate_sample_data()
    print(f"数据范围: {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据行数: {len(data)}")
    print(f"最新收盘价: {data['Close'].iloc[-1]:.2f}")

    # 演示每个指标
    example_ichimoku(data)
    example_keltner(data)
    example_cmo(data)
    example_vroc(data)
    example_advanced_indicators(data)

    # 组合策略
    example_combined_strategy(data)

    # 性能对比
    example_performance_comparison(data)

    print("\n" + "="*60)
    print("演示完成")
    print("="*60)

    # 保存示例数据
    output_file = "examples/sample_market_data.csv"
    data.to_csv(output_file)
    print(f"\n示例数据已保存到: {output_file}")


if __name__ == '__main__':
    main()
