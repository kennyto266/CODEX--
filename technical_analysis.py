#!/usr/bin/env python3
"""
Technical Analysis Agent for Hong Kong Stock Market
Focus: High Sharpe Ratio Strategies for 0700.HK (Tencent)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta

# Input data for 0700.HK
data = {
    "stocks": ["0700.HK"],
    "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
    "highs": [596.0, 597.0, 594.5, 597.0, 606.5, 621.0, 618.0, 614.5, 599.0, 605.0, 610.0, 608.5, 613.0, 605.0, 609.0, 619.0, 628.0, 639.0, 633.0, 649.0, 648.5, 649.5, 663.5, 664.5, 647.0, 643.5, 643.5, 651.0, 659.0, 653.0],
    "lows": [587.0, 583.0, 585.5, 589.5, 595.5, 608.0, 609.5, 595.0, 590.0, 594.0, 601.5, 599.0, 596.0, 591.0, 595.5, 605.0, 617.5, 628.0, 624.0, 642.0, 637.5, 640.5, 645.0, 635.5, 638.0, 634.0, 627.0, 628.0, 643.5, 640.0],
    "volumes": [17590658, 16359474, 15952765, 14290178, 19378950, 25694519, 20656474, 21263402, 21712370, 18234935, 15958837, 14808157, 15523985, 18003934, 19047729, 21815489, 19871460, 19193376, 18191860, 20780375, 16371242, 13339685, 22349048, 29989898, 20805608, 12899662, 15293080, 18440788, 17384258, 19504951]
}

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.convolve(gains, np.ones(period), 'valid') / period
    avg_loss = np.convolve(losses, np.ones(period), 'valid') / period
    
    rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    
    # Pad with NaN for the first period-1 values
    rsi = np.concatenate([np.full(period, np.nan), rsi])
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    exp_fast = pd.Series(prices).ewm(span=fast).mean()
    exp_slow = pd.Series(prices).ewm(span=slow).mean()
    macd_line = exp_fast - exp_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line.values, signal_line.values, histogram.values

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    df = pd.Series(prices)
    rolling_mean = df.rolling(window=period).mean()
    rolling_std = df.rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band.values, rolling_mean.values, lower_band.values

def calculate_moving_averages(prices, short=10, long=20):
    """Calculate short and long moving averages"""
    short_ma = pd.Series(prices).rolling(window=short).mean().values
    long_ma = pd.Series(prices).rolling(window=long).mean().values
    return short_ma, long_ma

def generate_signals(prices, rsi, macd_line, signal_line, short_ma, long_ma):
    """Generate buy/sell signals based on multiple indicators"""
    signals = []
    positions = []
    
    for i in range(len(prices)):
        signal = "HOLD"
        reason = ""
        
        if i > 20:  # Ensure we have enough data
            # RSI Filtered Momentum Strategy
            if (rsi[i] < 30 and rsi[i-1] >= 30 and 
                macd_line[i] > signal_line[i] and 
                short_ma[i] > long_ma[i]):
                signal = "BUY"
                reason = "RSI oversold + MACD bullish + MA uptrend"
            
            elif (rsi[i] > 70 and rsi[i-1] <= 70) or (macd_line[i] < signal_line[i]):
                signal = "SELL"
                reason = "RSI overbought or MACD bearish"
            
            # Moving Average Crossover Strategy
            elif (short_ma[i] > long_ma[i] and short_ma[i-1] <= long_ma[i-1] and rsi[i] < 60):
                signal = "BUY"
                reason = "MA golden cross + RSI neutral"
            
            elif (short_ma[i] < long_ma[i] and short_ma[i-1] >= long_ma[i-1]):
                signal = "SELL"
                reason = "MA death cross"
        
        signals.append({"day": i, "signal": signal, "reason": reason, "price": prices[i]})
        positions.append(1 if signal == "BUY" else (-1 if signal == "SELL" else 0))
    
    return signals, positions

def calculate_returns_and_sharpe(prices, positions, risk_free_rate=0.02):
    """Calculate strategy returns and Sharpe ratio"""
    price_returns = np.diff(prices) / prices[:-1]
    strategy_returns = np.array(positions[:-1]) * price_returns
    
    # Remove NaN values
    strategy_returns = strategy_returns[~np.isnan(strategy_returns)]
    
    if len(strategy_returns) == 0:
        return 0, 0
    
    avg_return = np.mean(strategy_returns) * 252  # Annualized
    volatility = np.std(strategy_returns) * np.sqrt(252)  # Annualized
    
    if volatility == 0:
        return avg_return, 0
    
    sharpe_ratio = (avg_return - risk_free_rate) / volatility
    return avg_return, sharpe_ratio

def analyze_tencent_data():
    """Main analysis function"""
    prices = np.array(data["close_prices"])
    highs = np.array(data["highs"])
    lows = np.array(data["lows"])
    volumes = np.array(data["volumes"])
    
    # Calculate technical indicators
    rsi = calculate_rsi(prices)
    macd_line, signal_line, histogram = calculate_macd(prices)
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(prices)
    short_ma, long_ma = calculate_moving_averages(prices)
    
    # Generate trading signals
    signals, positions = generate_signals(prices, rsi, macd_line, signal_line, short_ma, long_ma)
    
    # Calculate performance metrics
    avg_return, sharpe_ratio = calculate_returns_and_sharpe(prices, positions)
    
    # Filter significant signals
    significant_signals = [s for s in signals if s["signal"] != "HOLD"]
    
    # Calculate average RSI (excluding NaN values)
    valid_rsi = rsi[~np.isnan(rsi)]
    avg_rsi = np.mean(valid_rsi) if len(valid_rsi) > 0 else 50
    
    # Create visualization
    plt.figure(figsize=(15, 12))
    
    # Price and moving averages
    plt.subplot(4, 1, 1)
    plt.plot(prices, label='Close Price', linewidth=2)
    plt.plot(short_ma, label='MA10', alpha=0.7)
    plt.plot(long_ma, label='MA20', alpha=0.7)
    plt.plot(upper_bb, label='BB Upper', alpha=0.5, linestyle='--')
    plt.plot(lower_bb, label='BB Lower', alpha=0.5, linestyle='--')
    plt.title('0700.HK (Tencent) - Price Action & Technical Indicators')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # RSI
    plt.subplot(4, 1, 2)
    plt.plot(rsi, label='RSI', color='orange')
    plt.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought')
    plt.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold')
    plt.axhline(y=50, color='gray', linestyle='-', alpha=0.5)
    plt.title('RSI (14-period)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # MACD
    plt.subplot(4, 1, 3)
    plt.plot(macd_line, label='MACD', color='blue')
    plt.plot(signal_line, label='Signal', color='red')
    plt.bar(range(len(histogram)), histogram, label='Histogram', alpha=0.6)
    plt.title('MACD')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Volume
    plt.subplot(4, 1, 4)
    plt.bar(range(len(volumes)), volumes, alpha=0.7, color='purple')
    plt.title('Volume')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/workspace/technical_analysis_0700HK.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Prepare results
    results = {
        "discovered_strategy": [
            {
                "name": "RSI过滤动量策略",
                "description": "结合RSI超卖信号、MACD多头排列和均线上升趋势的多重确认买入策略，目标Sharpe比率>1.5"
            },
            {
                "name": "均线交叉策略",
                "description": "基于10日和20日均线金叉/死叉，结合RSI中性区域过滤的趋势跟踪策略"
            }
        ],
        "signals": [
            {
                "day": s["day"],
                "signal": s["signal"],
                "reason": s["reason"],
                "price": round(s["price"], 2)
            } for s in significant_signals[-5:]  # Last 5 significant signals
        ],
        "rsi_avg": round(avg_rsi, 1),
        "sharpe": round(sharpe_ratio, 2),
        "annual_return": round(avg_return * 100, 2),
        "current_price": prices[-1],
        "price_change": round(((prices[-1] / prices[0]) - 1) * 100, 2),
        "recommendations": [
            f"当前RSI为{round(rsi[-1], 1)}，{'接近超买区域，建议谨慎' if rsi[-1] > 65 else '处于中性区域，可关注买入机会' if rsi[-1] < 55 else '中性偏强，持续观察'}",
            f"MACD显示{'多头排列' if macd_line[-1] > signal_line[-1] else '空头排列'}，{'支持上涨' if macd_line[-1] > signal_line[-1] else '谨慎操作'}",
            f"价格{'突破' if prices[-1] > upper_bb[-1] else '接近' if prices[-1] > middle_bb[-1] else '跌破'}布林带中轨，注意{'回调风险' if prices[-1] > upper_bb[-1] else '支撑位' if prices[-1] < lower_bb[-1] else '方向选择'}",
            "设定止损位于近期低点635港元附近，控制下行风险",
            "关注成交量变化，放量突破更具可信度"
        ]
    }
    
    return results

if __name__ == "__main__":
    results = analyze_tencent_data()
    
    # Save results to JSON
    with open('/workspace/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))