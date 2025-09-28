#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股技术分析代理 - 腾讯0700.HK分析 (简化版)
不依赖外部库的技术分析
"""

import json
import math
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
    """计算RSI指标"""
    if len(prices) < window + 1:
        return [50.0] * len(prices)
    
    rsi_values = []
    
    for i in range(len(prices)):
        if i < window:
            rsi_values.append(50.0)
            continue
            
        gains = []
        losses = []
        
        for j in range(i - window + 1, i + 1):
            change = prices[j] - prices[j - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        avg_gain = sum(gains) / window
        avg_loss = sum(losses) / window
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    return rsi_values

def calculate_moving_average(prices, window):
    """计算移动平均线"""
    ma_values = []
    
    for i in range(len(prices)):
        if i < window - 1:
            ma_values.append(prices[i])
        else:
            window_prices = prices[i - window + 1:i + 1]
            ma = sum(window_prices) / window
            ma_values.append(ma)
    
    return ma_values

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """简化MACD计算"""
    if len(prices) < slow:
        return [0] * len(prices), [0] * len(prices)
    
    # 计算EMA
    def calculate_ema(data, period):
        ema = [data[0]]
        multiplier = 2 / (period + 1)
        
        for i in range(1, len(data)):
            ema.append((data[i] * multiplier) + (ema[-1] * (1 - multiplier)))
        
        return ema
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
    signal_line = calculate_ema(macd_line, signal)
    
    return macd_line, signal_line

def generate_signals_and_analysis():
    """生成交易信号和完整分析"""
    prices = data['close_prices']
    highs = data['highs']
    lows = data['lows']
    volumes = data['volumes']
    
    # 计算技术指标
    rsi_values = calculate_rsi(prices)
    ma_10 = calculate_moving_average(prices, 10)
    ma_20 = calculate_moving_average(prices, 20)
    macd_line, signal_line = calculate_macd(prices)
    
    # 生成交易信号
    signals = []
    dates = []
    
    # 创建日期序列
    base_date = datetime.now() - timedelta(days=29)
    
    for i in range(len(prices)):
        current_date = base_date + timedelta(days=i)
        dates.append(current_date)
        
        if i < 26:  # 前26天等待指标稳定
            continue
            
        # 策略1: RSI过滤动量策略
        buy_condition = (
            rsi_values[i] < 40 and  # RSI超卖
            ma_10[i] > ma_20[i] and  # 短期均线上穿长期均线
            macd_line[i] > signal_line[i] and  # MACD金叉
            volumes[i] > sum(volumes[max(0, i-5):i])/5  # 成交量放大
        )
        
        sell_condition = (
            rsi_values[i] > 65 or  # RSI超买
            ma_10[i] < ma_20[i] or  # 短期均线下穿长期均线
            macd_line[i] < signal_line[i]  # MACD死叉
        )
        
        if buy_condition:
            signals.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "signal": "买入",
                "price": prices[i],
                "reason": f"RSI={rsi_values[i]:.1f}(<40超卖), 均线金叉, MACD金叉, 成交量放大"
            })
        elif sell_condition:
            signals.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "signal": "卖出", 
                "price": prices[i],
                "reason": f"RSI={rsi_values[i]:.1f}(>65超买) 或 均线死叉 或 MACD死叉"
            })
    
    # 计算策略收益和夏普比率
    returns = []
    position = 0
    
    for i in range(1, len(prices)):
        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
        
        # 简化的信号判断
        if rsi_values[i] < 40 and ma_10[i] > ma_20[i]:
            position = 1  # 做多
        elif rsi_values[i] > 65 or ma_10[i] < ma_20[i]:
            position = 0  # 空仓
        
        strategy_return = daily_return * position
        returns.append(strategy_return)
    
    # 计算夏普比率
    if len(returns) > 0 and any(r != 0 for r in returns):
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        
        # 年化夏普比率 (假设无风险利率2%)
        risk_free_daily = 0.02 / 252
        if std_return > 0:
            sharpe_ratio = (mean_return - risk_free_daily) / std_return * math.sqrt(252)
        else:
            sharpe_ratio = 0
    else:
        sharpe_ratio = 0
    
    # 计算平均RSI
    valid_rsi = [r for r in rsi_values if r != 50.0 or len([x for x in rsi_values if x != 50.0]) == 0]
    avg_rsi = sum(valid_rsi) / len(valid_rsi) if valid_rsi else 50.0
    
    # 计算波动率和最大回撤
    price_returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    volatility = math.sqrt(sum(r**2 for r in price_returns) / len(price_returns)) * math.sqrt(252) if price_returns else 0
    
    # 计算最大回撤
    peak = prices[0]
    max_drawdown = 0
    for price in prices:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # 当前市场状态分析
    current_rsi = rsi_values[-1]
    current_price = prices[-1]
    price_trend = "上涨" if prices[-1] > prices[-5] else "下跌"
    
    # 生成最终分析结果
    result = {
        "discovered_strategy": [
            {
                "name": "RSI过滤动量策略",
                "description": "结合RSI(<40买入,>65卖出)、10/20日均线交叉和MACD信号，配合成交量确认的多重过滤策略"
            },
            {
                "name": "趋势跟踪策略",
                "description": "基于移动平均线交叉配合RSI极值，捕捉中短期趋势转换点，优化入场时机"
            }
        ],
        "signals": signals,
        "rsi_avg": round(avg_rsi, 1),
        "sharpe": round(sharpe_ratio, 2),
        "volatility": round(volatility * 100, 1),
        "max_drawdown": round(max_drawdown * 100, 1),
        "current_analysis": {
            "current_price": current_price,
            "current_rsi": round(current_rsi, 1),
            "price_trend": price_trend,
            "ma_10": round(ma_10[-1], 1),
            "ma_20": round(ma_20[-1], 1)
        },
        "recommendations": [
            f"当前RSI为{current_rsi:.1f}，{'超买区域，建议减仓' if current_rsi > 70 else '超卖区域，可考虑买入' if current_rsi < 30 else '中性区域，等待明确信号'}",
            f"策略夏普比率{sharpe_ratio:.2f}，{'表现优异，策略有效' if sharpe_ratio > 1.5 else '表现一般，需要优化' if sharpe_ratio > 0 else '策略需要重新调整'}",
            f"股价呈{price_trend}趋势，10日均线{'上穿' if ma_10[-1] > ma_20[-1] else '下穿'}20日均线",
            f"最大回撤{max_drawdown*100:.1f}%，建议设定{max_drawdown*100*0.8:.1f}%止损位",
            "RSI<30时积极买入，RSI>70时分批减仓，RSI30-70区间持股观望",
            f"当前年化波动率{volatility*100:.1f}%，属于{'高波动' if volatility > 0.3 else '中等波动' if volatility > 0.2 else '低波动'}股票，注意仓位管理"
        ]
    }
    
    return result

def main():
    """主函数"""
    print("开始港股技术分析...")
    
    # 执行分析
    analysis_result = generate_signals_and_analysis()
    
    # 更新TODO状态
    print("分析完成，生成结果...")
    
    return analysis_result

if __name__ == "__main__":
    result = main()
    
    # 输出结果
    print("\n" + "="*50)
    print("港股技术分析结果 - 腾讯0700.HK")
    print("="*50)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存到文件
    with open('/workspace/analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到: /workspace/analysis_result.json")