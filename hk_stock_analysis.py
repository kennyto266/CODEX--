#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股技术分析代理 - 腾讯0700.HK分析
高夏普比率策略回测
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta

# 输入数据
data = {
    "stocks": ["0700.HK"],
    "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
    "highs": [596.0, 597.0, 594.5, 597.0, 606.5, 621.0, 618.0, 614.5, 599.0, 605.0, 610.0, 608.5, 613.0, 605.0, 609.0, 619.0, 628.0, 639.0, 633.0, 649.0, 648.5, 649.5, 663.5, 664.5, 647.0, 643.5, 643.5, 651.0, 659.0, 653.0],
    "lows": [587.0, 583.0, 585.5, 589.5, 595.5, 608.0, 609.5, 595.0, 590.0, 594.0, 601.5, 599.0, 596.0, 591.0, 595.5, 605.0, 617.5, 628.0, 624.0, 642.0, 637.5, 640.5, 645.0, 635.5, 638.0, 634.0, 627.0, 628.0, 643.5, 640.0],
    "volumes": [17590658, 16359474, 15952765, 14290178, 19378950, 25694519, 20656474, 21263402, 21712370, 18234935, 15958837, 14808157, 15523985, 18003934, 19047729, 21815489, 19871460, 19193376, 18191860, 20780375, 16371242, 13339685, 22349048, 29989898, 20805608, 12899662, 15293080, 18440788, 17384258, 19504951]
}

def calculate_rsi(prices, window=14):
    """计算相对强弱指数RSI"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = pd.Series(gains).rolling(window=window).mean()
    avg_losses = pd.Series(losses).rolling(window=window).mean()
    
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    return rsi.values

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    prices_series = pd.Series(prices)
    ema_fast = prices_series.ewm(span=fast).mean()
    ema_slow = prices_series.ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line.values, signal_line.values, histogram.values

def calculate_moving_averages(prices, short_window=10, long_window=20):
    """计算移动平均线"""
    prices_series = pd.Series(prices)
    ma_short = prices_series.rolling(window=short_window).mean()
    ma_long = prices_series.rolling(window=long_window).mean()
    return ma_short.values, ma_long.values

def generate_signals(prices, rsi, macd_line, signal_line, ma_short, ma_long):
    """生成交易信号"""
    signals = []
    positions = []
    
    for i in range(len(prices)):
        if i < 26:  # 等待指标稳定
            signals.append('hold')
            positions.append(0)
            continue
            
        # RSI过滤的动量策略
        buy_signal = (
            rsi[i] < 40 and  # RSI超卖
            ma_short[i] > ma_long[i] and  # 短期均线在长期均线上方
            macd_line[i] > signal_line[i]  # MACD金叉
        )
        
        sell_signal = (
            rsi[i] > 65 or  # RSI超买
            ma_short[i] < ma_long[i] or  # 短期均线在长期均线下方
            macd_line[i] < signal_line[i]  # MACD死叉
        )
        
        if buy_signal and (len(positions) == 0 or positions[-1] <= 0):
            signals.append('buy')
            positions.append(1)
        elif sell_signal and (len(positions) == 0 or positions[-1] >= 0):
            signals.append('sell')
            positions.append(-1)
        else:
            signals.append('hold')
            positions.append(positions[-1] if positions else 0)
    
    return signals, positions

def calculate_returns_and_sharpe(prices, positions):
    """计算收益率和夏普比率"""
    returns = []
    
    for i in range(1, len(prices)):
        price_return = (prices[i] - prices[i-1]) / prices[i-1]
        strategy_return = price_return * positions[i-1]  # 使用前一期的仓位
        returns.append(strategy_return)
    
    returns = np.array(returns)
    
    # 计算夏普比率 (假设无风险利率为2%)
    risk_free_rate = 0.02 / 252  # 日化无风险利率
    excess_returns = returns - risk_free_rate
    
    if np.std(returns) == 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)
    
    return returns, sharpe_ratio

def main():
    """主分析函数"""
    prices = np.array(data['close_prices'])
    highs = np.array(data['highs'])
    lows = np.array(data['lows'])
    volumes = np.array(data['volumes'])
    
    # 计算技术指标
    rsi = calculate_rsi(prices)
    macd_line, signal_line, histogram = calculate_macd(prices)
    ma_short, ma_long = calculate_moving_averages(prices)
    
    # 生成交易信号
    signals, positions = generate_signals(prices, rsi, macd_line, signal_line, ma_short, ma_long)
    
    # 计算收益和夏普比率
    returns, sharpe_ratio = calculate_returns_and_sharpe(prices, positions)
    
    # 创建日期序列
    dates = [datetime.now() - timedelta(days=30-i) for i in range(30)]
    
    # 生成信号列表
    signal_list = []
    for i, (date, signal, price) in enumerate(zip(dates, signals, prices)):
        if signal in ['buy', 'sell']:
            reason = ""
            if signal == 'buy':
                reason = f"RSI={rsi[i]:.1f}(<40), 均线金叉, MACD金叉"
            else:
                reason = f"RSI={rsi[i]:.1f}(>65), 均线死叉或MACD死叉"
            
            signal_list.append({
                "date": date.strftime("%Y-%m-%d"),
                "signal": "买入" if signal == 'buy' else "卖出",
                "price": price,
                "reason": reason
            })
    
    # 计算平均RSI
    valid_rsi = rsi[~np.isnan(rsi)]
    avg_rsi = np.mean(valid_rsi) if len(valid_rsi) > 0 else 50
    
    # 绘制分析图表
    plt.figure(figsize=(15, 12))
    
    # 价格和移动平均线
    plt.subplot(4, 1, 1)
    plt.plot(prices, label='收盘价', linewidth=2)
    plt.plot(ma_short, label='10日均线', alpha=0.7)
    plt.plot(ma_long, label='20日均线', alpha=0.7)
    
    # 标记买卖信号
    buy_points = [i for i, s in enumerate(signals) if s == 'buy']
    sell_points = [i for i, s in enumerate(signals) if s == 'sell']
    
    if buy_points:
        plt.scatter(buy_points, [prices[i] for i in buy_points], 
                   color='green', marker='^', s=100, label='买入信号')
    if sell_points:
        plt.scatter(sell_points, [prices[i] for i in sell_points], 
                   color='red', marker='v', s=100, label='卖出信号')
    
    plt.title('0700.HK 腾讯 - 价格与交易信号')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # RSI
    plt.subplot(4, 1, 2)
    plt.plot(rsi, label='RSI', color='purple')
    plt.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='超买线(70)')
    plt.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='超卖线(30)')
    plt.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
    plt.title('RSI指标')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # MACD
    plt.subplot(4, 1, 3)
    plt.plot(macd_line, label='MACD线', color='blue')
    plt.plot(signal_line, label='信号线', color='red')
    plt.bar(range(len(histogram)), histogram, alpha=0.3, label='MACD柱')
    plt.title('MACD指标')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 累计收益
    plt.subplot(4, 1, 4)
    cumulative_returns = np.cumprod(1 + returns)
    plt.plot(cumulative_returns, label=f'策略累计收益 (Sharpe: {sharpe_ratio:.2f})', color='green')
    
    # 基准收益（买入持有）
    benchmark_returns = [(prices[i] - prices[0]) / prices[0] for i in range(len(prices))]
    plt.plot(benchmark_returns[1:], label='基准收益(买入持有)', color='gray', alpha=0.7)
    
    plt.title('策略收益对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/workspace/hk_analysis_chart.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 风险评估
    volatility = np.std(returns) * np.sqrt(252)
    max_drawdown = np.min(np.minimum.accumulate(cumulative_returns) / np.maximum.accumulate(cumulative_returns) - 1)
    
    # 生成最终结果
    result = {
        "discovered_strategy": [
            {
                "name": "RSI过滤动量策略",
                "description": "结合RSI(<40买入,>65卖出)、均线交叉和MACD信号的多重过滤策略，优化入场时机"
            },
            {
                "name": "趋势跟踪策略", 
                "description": "基于10日/20日均线交叉配合MACD确认，捕捉中短期趋势转换点"
            }
        ],
        "signals": signal_list,
        "rsi_avg": round(avg_rsi, 1),
        "sharpe": round(sharpe_ratio, 2),
        "volatility": round(volatility * 100, 1),
        "max_drawdown": round(max_drawdown * 100, 1),
        "recommendations": [
            f"当前RSI平均值{avg_rsi:.1f}，处于中性区间，建议等待极值信号",
            f"策略夏普比率{sharpe_ratio:.2f}，{'表现优异' if sharpe_ratio > 1.5 else '有待优化'}",
            "建议设定5%止损位，控制单笔交易风险",
            f"最大回撤{max_drawdown*100:.1f}%，需要关注风险管理",
            "在RSI<30时积极买入，RSI>70时谨慎减仓",
            "关注MACD金叉死叉配合均线信号，提高胜率"
        ]
    }
    
    return result

if __name__ == "__main__":
    analysis_result = main()
    
    # 输出JSON结果
    print("\n=== 港股技术分析结果 ===")
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    # 保存结果到文件
    with open('/workspace/analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)