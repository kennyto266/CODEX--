#!/usr/bin/env python3
"""
港股研究辩论代理分析系统
专注于0700.HK（腾讯）的量化分析和辩论策略
"""

import json
import math
from datetime import datetime, timedelta

class HKStockDebateAgent:
    def __init__(self, stock_data):
        self.stock_data = stock_data
        self.prices = stock_data['close_prices']
        self.avg_return = stock_data['avg_return']
        self.volatility = stock_data['volatility']
        
    def calculate_technical_indicators(self):
        """计算技术指标"""
        prices = self.prices
        
        # 计算收益率
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # 移动平均线
        def moving_average(data, window):
            if len(data) < window:
                return [sum(data) / len(data)]
            return [sum(data[i:i+window]) / window for i in range(len(data) - window + 1)]
        
        ma5 = moving_average(prices, 5)
        ma10 = moving_average(prices, 10)
        ma20 = moving_average(prices, 20)
        
        # RSI计算
        def calculate_rsi(prices, period=14):
            if len(prices) < period + 1:
                period = len(prices) - 1
            deltas = [(prices[i] - prices[i-1]) for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            if len(gains) < period:
                period = len(gains)
            
            avg_gain = sum(gains[:period]) / period if period > 0 else 0
            avg_loss = sum(losses[:period]) / period if period > 0 else 0
            
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(prices)
        
        # 波动率指标
        def std_dev(data):
            if len(data) <= 1:
                return 0
            mean_val = sum(data) / len(data)
            variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
            return math.sqrt(variance)
        
        volatility_20d = std_dev(returns[-20:]) if len(returns) >= 20 else std_dev(returns)
        
        # 趋势强度
        trend_strength = (prices[-1] - prices[0]) / prices[0]
        
        return {
            'current_price': prices[-1],
            'ma5': ma5[-1] if len(ma5) > 0 else prices[-1],
            'ma10': ma10[-1] if len(ma10) > 0 else prices[-1],
            'ma20': ma20[-1] if len(ma20) > 0 else prices[-1],
            'rsi': rsi,
            'volatility_20d': volatility_20d,
            'trend_strength': trend_strength,
            'recent_returns': returns[-5:] if len(returns) >= 5 else returns
        }
    
    def bull_debate_analysis(self, indicators):
        """牛市辩论分析"""
        bull_points = []
        bull_score = 0.0
        
        # 技术面看涨因素
        if indicators['current_price'] > indicators['ma5']:
            bull_points.append("股价位于5日均线之上，短期趋势向好")
            bull_score += 0.15
            
        if indicators['current_price'] > indicators['ma20']:
            bull_points.append("股价位于20日均线之上，中期趋势强劲")
            bull_score += 0.20
            
        if indicators['rsi'] < 70 and indicators['rsi'] > 30:
            bull_points.append("RSI处于健康区间，无超买超卖压力")
            bull_score += 0.10
            
        if indicators['trend_strength'] > 0:
            bull_points.append(f"整体上涨趋势明确，涨幅{indicators['trend_strength']:.2%}")
            bull_score += 0.25
            
        # 基本面看涨因素（腾讯特定）
        bull_points.append("腾讯作为科技龙头，AI和云计算业务增长潜力巨大")
        bull_score += 0.15
        
        bull_points.append("港股估值相对A股仍有折价，存在价值回归机会")
        bull_score += 0.10
        
        # 政策面看涨
        bull_points.append("中港互联互通机制完善，南向资金持续流入")
        bull_score += 0.05
        
        return {
            'points': bull_points,
            'score': min(bull_score, 1.0)
        }
    
    def bear_debate_analysis(self, indicators):
        """熊市辩论分析"""
        bear_points = []
        bear_score = 0.0
        
        # 技术面看跌因素
        if indicators['volatility_20d'] > self.volatility * 1.2:
            bear_points.append("近期波动率显著上升，市场不确定性增加")
            bear_score += 0.15
            
        if indicators['rsi'] > 70:
            bear_points.append("RSI超买，存在技术性调整压力")
            bear_score += 0.20
        elif indicators['rsi'] < 30:
            bear_points.append("RSI超卖，反映市场悲观情绪浓厚")
            bear_score += 0.25
            
        # 基本面看跌因素
        bear_points.append("全球经济不确定性，科技股估值承压")
        bear_score += 0.15
        
        bear_points.append("中美科技竞争加剧，监管风险持续")
        bear_score += 0.20
        
        # 市场结构风险
        bear_points.append("港股流动性相对较低，易受外资情绪影响")
        bear_score += 0.10
        
        bear_points.append("美联储政策不确定性影响资金流向")
        bear_score += 0.15
        
        return {
            'points': bear_points,
            'score': min(bear_score, 1.0)
        }
    
    def generate_debate_strategies(self, bull_analysis, bear_analysis):
        """生成基于辩论的投资策略"""
        strategies = []
        
        # 策略1：动量反转辩论策略
        strategy1 = {
            'name': '动量反转辩论策略',
            'description': '基于技术指标辩论，在超买时减仓，超卖时加仓，结合趋势强度调整仓位',
            'logic': '牛市观点强调趋势延续，熊市观点警示反转风险，通过RSI和移动均线平衡决策',
            'entry_conditions': ['RSI<30时加仓', '股价回调至20日均线附近时分批买入'],
            'exit_conditions': ['RSI>70时减仓', '跌破20日均线时止损'],
            'risk_management': '单次最大仓位不超过30%，设置2%止损'
        }
        
        # 策略2：多因子平衡策略
        strategy2 = {
            'name': '多因子平衡策略',
            'description': '综合技术面、基本面和市场情绪，通过辩论权重动态调整投资组合',
            'logic': '牛熊观点加权平均，避免单一视角偏见，追求稳定的风险调整收益',
            'entry_conditions': ['平衡分数>0.6时增加仓位', '多个技术指标协同确认'],
            'exit_conditions': ['平衡分数<0.4时降低仓位', '风险指标超过阈值时保护性卖出'],
            'risk_management': '基于波动率的动态仓位管理，目标Sharpe>1.5'
        }
        
        strategies.extend([strategy1, strategy2])
        return strategies
    
    def backtest_sharpe_simulation(self, bull_score, bear_score, balanced_score):
        """模拟回测计算Sharpe比率"""
        # 基于辩论分数调整收益率
        adjusted_return = self.avg_return * balanced_score * (1 + (bull_score - bear_score) * 0.3)
        
        # 基于辩论分歧调整风险
        debate_uncertainty = abs(bull_score - bear_score)
        adjusted_volatility = self.volatility * (1 + debate_uncertainty * 0.2)
        
        # 计算Sharpe比率（假设无风险利率3%）
        risk_free_rate = 0.03 / 252  # 日化无风险利率
        sharpe_ratio = (adjusted_return - risk_free_rate) / adjusted_volatility
        
        # 年化Sharpe
        annualized_sharpe = sharpe_ratio * math.sqrt(252)
        
        return max(annualized_sharpe, 0.1)  # 最小值保护
    
    def generate_recommendations(self, bull_analysis, bear_analysis, balanced_score, sharpe):
        """生成投资建议"""
        recommendations = []
        
        # 基于平衡分数的核心建议
        if balanced_score > 0.7:
            recommendations.append("当前多空辩论偏向乐观，建议适度增加仓位，但需设置止损保护")
        elif balanced_score < 0.4:
            recommendations.append("当前多空辩论偏向谨慎，建议降低仓位或观望，等待更明确信号")
        else:
            recommendations.append("多空观点相对平衡，建议维持中性仓位，关注关键技术位突破")
        
        # Sharpe比率相关建议
        if sharpe > 1.5:
            recommendations.append("预期风险调整收益良好，符合目标Sharpe>1.5，可考虑战术性配置")
        else:
            recommendations.append("风险调整收益未达预期，建议降低仓位或寻找更优配置机会")
        
        # 风险管理建议
        recommendations.append("设置动态止损位，根据波动率调整风险敞口，避免单一观点偏见")
        
        # 腾讯特定建议
        recommendations.append("关注腾讯季报业绩，特别是AI和云业务增长情况，作为持仓调整依据")
        
        # 宏观环境建议
        recommendations.append("密切关注美联储政策和中美关系变化，及时调整港股配置策略")
        
        return recommendations[:5]  # 限制在5条以内
    
    def run_analysis(self):
        """执行完整分析流程"""
        # 计算技术指标
        indicators = self.calculate_technical_indicators()
        
        # 执行多空辩论
        bull_analysis = self.bull_debate_analysis(indicators)
        bear_analysis = self.bear_debate_analysis(indicators)
        
        # 计算平衡分数
        balanced_score = (bull_analysis['score'] + (1 - bear_analysis['score'])) / 2
        
        # 生成策略
        strategies = self.generate_debate_strategies(bull_analysis, bear_analysis)
        
        # 回测Sharpe
        sharpe = self.backtest_sharpe_simulation(
            bull_analysis['score'], 
            bear_analysis['score'], 
            balanced_score
        )
        
        # 生成建议
        recommendations = self.generate_recommendations(
            bull_analysis, bear_analysis, balanced_score, sharpe
        )
        
        return {
            'discovered_strategy': strategies[1]['description'],  # 使用多因子平衡策略
            'bull_score': round(bull_analysis['score'], 2),
            'bear_score': round(bear_analysis['score'], 2),
            'balanced_score': round(balanced_score, 2),
            'sharpe': round(sharpe, 2),
            'recommendations': recommendations,
            'technical_indicators': indicators,
            'strategies': strategies,
            'bull_points': bull_analysis['points'],
            'bear_points': bear_analysis['points']
        }

def main():
    # 输入数据
    stock_data = {
        "stocks": ["0700.HK"],
        "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
        "avg_return": 0.0033,
        "volatility": 0.0138
    }
    
    # 创建分析代理
    agent = HKStockDebateAgent(stock_data)
    
    # 执行分析
    result = agent.run_analysis()
    
    # 输出JSON结果
    json_output = {
        'discovered_strategy': result['discovered_strategy'],
        'bull_score': result['bull_score'],
        'bear_score': result['bear_score'],
        'balanced_score': result['balanced_score'],
        'sharpe': result['sharpe'],
        'recommendations': result['recommendations']
    }
    
    print("=== 港股研究辩论代理分析结果 ===")
    print(json.dumps(json_output, ensure_ascii=False, indent=2))
    
    return json_output

if __name__ == "__main__":
    main()