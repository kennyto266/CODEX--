#!/usr/bin/env python3
"""
港股新闻分析代理 - 腾讯(0700.HK)事件驱动策略回测
目标：实现Sharpe > 1.5的事件驱动策略
"""

import json
import math
from datetime import datetime, timedelta

class NewsAnalysisAgent:
    def __init__(self):
        self.risk_free_rate = 0.025  # 港股无风险利率约2.5%
        
    def analyze_stock_data(self, close_prices, daily_returns):
        """分析股票数据，识别关键事件"""
        returns = [float(r) for r in daily_returns]
        prices = close_prices
        
        # 识别异常收益事件（超过2个标准差）
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        threshold = 2 * std_return
        
        key_events = []
        for i, ret in enumerate(returns):
            if abs(ret) > threshold:
                impact_score = min(max(ret, -0.1), 0.1)  # 限制在-0.1到0.1范围
                event_type = "正面突破" if ret > 0 else "负面冲击"
                key_events.append({
                    "day": i + 1,
                    "event": f"腾讯股价{event_type}，日收益率{ret:.4f}",
                    "impact_score": round(impact_score, 4),
                    "price": prices[i] if i < len(prices) else None
                })
        
        return key_events, returns
    
    def momentum_strategy_backtest(self, returns):
        """正面新闻动量策略回测"""
        strategy_returns = []
        position = 0  # 0=空仓, 1=多头, -1=空头
        
        for i, ret in enumerate(returns):
            if i == 0:
                strategy_returns.append(0)
                continue
                
            # 策略逻辑：前一日收益率>1%则做多，<-1%则做空，否则空仓
            prev_ret = returns[i-1]
            if prev_ret > 0.01:
                position = 1
            elif prev_ret < -0.01:
                position = -1
            else:
                position = 0
                
            # 当日策略收益 = 仓位 * 当日收益
            strategy_return = position * ret
            strategy_returns.append(strategy_return)
        
        return strategy_returns
    
    def calculate_sharpe_ratio(self, returns):
        """计算夏普比率"""
        if len(returns) == 0:
            return 0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0
        
        excess_returns = mean_return - self.risk_free_rate / 252  # 日化无风险利率
        return (excess_returns / std_return) * math.sqrt(252)  # 年化夏普比率
    
    def generate_analysis(self, stock_data):
        """生成完整分析报告"""
        close_prices = stock_data["close_prices"]
        daily_returns = stock_data["daily_returns"]
        
        # 分析关键事件
        key_events, returns = self.analyze_stock_data(close_prices, daily_returns)
        
        # 回测动量策略
        strategy_returns = self.momentum_strategy_backtest(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(strategy_returns)
        
        # 计算风险指标
        cumulative_returns = []
        cum_sum = 0
        for ret in strategy_returns:
            cum_sum += ret
            cumulative_returns.append(cum_sum)
        max_drawdown = self.calculate_max_drawdown(cumulative_returns)
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252)  # 年化波动率
        
        # 生成策略建议
        discovered_strategy = {
            "name": "腾讯事件驱动动量策略",
            "description": f"基于腾讯股价异常波动的事件驱动策略，通过识别超过{2}个标准差的收益率变动来调整仓位",
            "logic": "前日收益>1%做多，<-1%做空，其他时间空仓"
        }
        
        std_return = math.sqrt(variance)
        recommendations = [
            f"当腾讯日收益率超过{std_return*2:.2%}时，考虑调整仓位以捕捉动量",
            f"设置止损点在{max_drawdown:.2%}附近，控制最大回撤",
            f"密切关注腾讯财报发布、监管政策变化等关键事件",
            f"在高波动期间({volatility:.1%}年化波动率)增加对冲工具使用",
            f"维持目标夏普比率>1.5，当前策略实现{sharpe_ratio:.2f}"
        ]
        
        return {
            "discovered_strategy": discovered_strategy,
            "key_events": key_events,
            "event_count": len(key_events),
            "sharpe": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 4),
            "volatility": round(volatility, 4),
            "recommendations": recommendations
        }
    
    def calculate_max_drawdown(self, cumulative_returns):
        """计算最大回撤"""
        if not cumulative_returns:
            return 0
            
        peak = cumulative_returns[0]
        max_drawdown = 0
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (value - peak) / (peak + 1e-8) if peak != 0 else 0
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                
        return max_drawdown

# 执行分析
if __name__ == "__main__":
    # 输入数据
    stock_data = {
        "stocks": ["0700.HK"],
        "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
        "daily_returns": ['0.0094', '-0.0034', '0.0042', '0.0118', '0.0242', '-0.0081', '-0.0172', '-0.0083', '0.0042', '0.0142', '-0.0074', '-0.0033', '-0.0100', '0.0219', '0.0198', '0.0154', '0.0104', '-0.0063', '0.0222', '0.0000', '0.0023', '0.0256', '-0.0295', '0.0008', '-0.0023', '-0.0086', '0.0205', '0.0023', '-0.0092']
    }
    
    agent = NewsAnalysisAgent()
    analysis_result = agent.generate_analysis(stock_data)
    
    print(json.dumps(analysis_result, indent=2, ensure_ascii=False))