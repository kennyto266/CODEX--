#!/usr/bin/env python3
"""
Hong Kong Stock Market Sentiment Analysis System
专业港股市场情绪分析系统

Analyzes market sentiment for Hong Kong stocks using multiple indicators
and provides comprehensive investment insights.
"""

import json
import math
from datetime import datetime
from typing import Dict, Any, List, Tuple

class HKStockSentimentAnalyzer:
    """港股市场情绪分析器"""
    
    def __init__(self):
        self.analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def calculate_fear_greed_index(self, price_change_pct: float, volume_ratio: float, volatility: float) -> Dict[str, Any]:
        """
        计算恐慌贪婪指数
        Fear & Greed Index calculation based on multiple factors
        """
        # 价格动量权重 (40%)
        price_momentum_score = min(100, max(0, (price_change_pct + 10) * 5))
        
        # 成交量权重 (30%)
        volume_score = min(100, max(0, volume_ratio * 100))
        
        # 波动率权重 (30%) - 低波动率表示贪婪，高波动率表示恐慌
        volatility_score = min(100, max(0, 100 - (volatility * 50)))
        
        # 综合恐慌贪婪指数
        fear_greed_index = (price_momentum_score * 0.4 + volume_score * 0.3 + volatility_score * 0.3)
        
        # 情绪分类
        if fear_greed_index >= 75:
            sentiment_level = "极度贪婪"
            sentiment_en = "Extreme Greed"
        elif fear_greed_index >= 55:
            sentiment_level = "贪婪"
            sentiment_en = "Greed"
        elif fear_greed_index >= 45:
            sentiment_level = "中性"
            sentiment_en = "Neutral"
        elif fear_greed_index >= 25:
            sentiment_level = "恐慌"
            sentiment_en = "Fear"
        else:
            sentiment_level = "极度恐慌"
            sentiment_en = "Extreme Fear"
            
        return {
            "fear_greed_index": round(fear_greed_index, 2),
            "sentiment_level": sentiment_level,
            "sentiment_level_en": sentiment_en,
            "components": {
                "price_momentum_score": round(price_momentum_score, 2),
                "volume_score": round(volume_score, 2),
                "volatility_score": round(volatility_score, 2)
            }
        }
    
    def analyze_investor_psychology(self, price_change: float, price_change_pct: float, volume_ratio: float) -> Dict[str, Any]:
        """
        分析投资者心理状态
        Analyze investor psychological state
        """
        # 基于价格变化和成交量分析心理状态
        if price_change_pct > 5 and volume_ratio > 1.2:
            psychology = "极度乐观"
            psychology_en = "Extremely Optimistic"
            confidence_level = "高"
            market_participation = "活跃"
        elif price_change_pct > 2 and volume_ratio > 0.8:
            psychology = "乐观"
            psychology_en = "Optimistic"
            confidence_level = "中高"
            market_participation = "积极"
        elif -2 <= price_change_pct <= 2:
            psychology = "中性观望"
            psychology_en = "Neutral/Wait-and-see"
            confidence_level = "中等"
            market_participation = "谨慎"
        elif price_change_pct < -2 and volume_ratio > 1.0:
            psychology = "恐慌性抛售"
            psychology_en = "Panic Selling"
            confidence_level = "低"
            market_participation = "恐慌"
        else:
            psychology = "悲观"
            psychology_en = "Pessimistic"
            confidence_level = "低"
            market_participation = "消极"
            
        return {
            "psychology_state": psychology,
            "psychology_state_en": psychology_en,
            "confidence_level": confidence_level,
            "market_participation": market_participation,
            "risk_appetite": "高" if price_change_pct > 3 else "中" if price_change_pct > -3 else "低"
        }
    
    def analyze_capital_flow(self, price_change: float, volume_ratio: float, volatility: float) -> Dict[str, Any]:
        """
        分析资金流向
        Analyze capital flow patterns
        """
        # 基于成交量比率和价格变化分析资金流向
        if volume_ratio > 1.5 and price_change > 0:
            main_capital_flow = "大量流入"
            retail_capital_flow = "跟随流入"
            capital_type = "主力主导上涨"
        elif volume_ratio > 1.2 and price_change > 0:
            main_capital_flow = "流入"
            retail_capital_flow = "适度流入"
            capital_type = "机构散户共振"
        elif volume_ratio < 0.8 and price_change > 0:
            main_capital_flow = "小幅流入"
            retail_capital_flow = "观望"
            capital_type = "缺乏量能支撑"
        elif volume_ratio > 1.0 and price_change < 0:
            main_capital_flow = "流出"
            retail_capital_flow = "恐慌流出"
            capital_type = "集中抛售"
        else:
            main_capital_flow = "平衡"
            retail_capital_flow = "平衡"
            capital_type = "资金观望"
            
        # 计算资金流向强度
        flow_intensity = abs(price_change) * volume_ratio * 10
        
        return {
            "main_capital_flow": main_capital_flow,
            "retail_capital_flow": retail_capital_flow,
            "capital_flow_type": capital_type,
            "flow_intensity": round(flow_intensity, 2),
            "capital_concentration": "集中" if volume_ratio > 1.3 else "分散"
        }
    
    def analyze_technical_sentiment(self, current_price: float, price_change_pct: float, volatility: float) -> Dict[str, Any]:
        """
        分析技术面情绪
        Analyze technical sentiment indicators
        """
        # RSI估算 (基于价格变化)
        rsi_estimate = 50 + (price_change_pct * 2)
        rsi_estimate = min(100, max(0, rsi_estimate))
        
        # 技术面情绪判断
        if rsi_estimate > 70:
            technical_sentiment = "超买"
            technical_signal = "卖出信号"
            momentum = "强劲上涨但需警惕回调"
        elif rsi_estimate > 60:
            technical_sentiment = "偏强"
            technical_signal = "持有或减仓"
            momentum = "上涨趋势良好"
        elif rsi_estimate > 40:
            technical_sentiment = "中性"
            technical_signal = "观望"
            momentum = "横盘整理"
        elif rsi_estimate > 30:
            technical_sentiment = "偏弱"
            technical_signal = "关注买入机会"
            momentum = "下跌趋势放缓"
        else:
            technical_sentiment = "超卖"
            technical_signal = "买入信号"
            momentum = "超跌反弹机会"
            
        # 波动率分析
        volatility_level = "高" if volatility > 2.0 else "中" if volatility > 1.0 else "低"
        
        return {
            "technical_sentiment": technical_sentiment,
            "rsi_estimate": round(rsi_estimate, 2),
            "technical_signal": technical_signal,
            "momentum_description": momentum,
            "volatility_level": volatility_level,
            "trend_strength": "强" if abs(price_change_pct) > 5 else "中" if abs(price_change_pct) > 2 else "弱"
        }
    
    def analyze_fundamental_sentiment(self, stock_code: str, current_price: float, price_change_pct: float) -> Dict[str, Any]:
        """
        分析基本面情绪
        Analyze fundamental sentiment
        """
        # 0700.HK 是腾讯控股的特殊分析
        if stock_code == "0700.HK":
            # 基于当前价格水平的估值情绪
            if current_price > 600:
                valuation_sentiment = "估值偏高"
                growth_sentiment = "成长性关注"
            elif current_price > 400:
                valuation_sentiment = "估值合理"
                growth_sentiment = "成长性良好"
            else:
                valuation_sentiment = "估值低估"
                growth_sentiment = "成长性被低估"
        else:
            # 通用分析
            valuation_sentiment = "需要更多基本面数据"
            growth_sentiment = "需要更多财务数据"
            
        # 基于价格变化的市场预期
        if price_change_pct > 5:
            market_expectation = "业绩预期大幅上调"
            earnings_sentiment = "乐观"
        elif price_change_pct > 2:
            market_expectation = "业绩预期上调"
            earnings_sentiment = "偏乐观"
        elif price_change_pct > -2:
            market_expectation = "业绩预期稳定"
            earnings_sentiment = "中性"
        else:
            market_expectation = "业绩预期下调"
            earnings_sentiment = "悲观"
            
        return {
            "valuation_sentiment": valuation_sentiment,
            "growth_sentiment": growth_sentiment,
            "market_expectation": market_expectation,
            "earnings_sentiment": earnings_sentiment,
            "fundamental_score": round(50 + price_change_pct * 3, 2)
        }
    
    def analyze_macro_sentiment(self, price_change_pct: float) -> Dict[str, Any]:
        """
        分析宏观情绪影响
        Analyze macroeconomic sentiment impact
        """
        # 基于价格表现推断宏观情绪
        if price_change_pct > 8:
            policy_sentiment = "政策利好强烈"
            economic_sentiment = "经济预期改善"
            geopolitical_impact = "地缘政治风险缓解"
        elif price_change_pct > 3:
            policy_sentiment = "政策偏向利好"
            economic_sentiment = "经济预期稳定"
            geopolitical_impact = "地缘政治影响有限"
        elif price_change_pct > -3:
            policy_sentiment = "政策中性"
            economic_sentiment = "经济预期平稳"
            geopolitical_impact = "地缘政治风险可控"
        else:
            policy_sentiment = "政策担忧"
            economic_sentiment = "经济预期下行"
            geopolitical_impact = "地缘政治风险上升"
            
        return {
            "policy_sentiment": policy_sentiment,
            "economic_sentiment": economic_sentiment,
            "geopolitical_impact": geopolitical_impact,
            "macro_environment": "利好" if price_change_pct > 2 else "中性" if price_change_pct > -2 else "利空",
            "systemic_risk": "低" if price_change_pct > 0 else "中" if price_change_pct > -5 else "高"
        }
    
    def analyze_sentiment_cycle(self, price_change_pct: float, volume_ratio: float, volatility: float) -> Dict[str, Any]:
        """
        分析情绪周期
        Analyze sentiment cycle
        """
        # 情绪周期评分
        cycle_score = (price_change_pct * 0.5 + (volume_ratio - 1) * 50 + (2 - volatility) * 10)
        
        if cycle_score > 15:
            cycle_position = "情绪顶部区域"
            cycle_stage = "亢奋期"
            next_direction = "情绪回落风险"
        elif cycle_score > 5:
            cycle_position = "情绪上升期"
            cycle_stage = "乐观期"
            next_direction = "情绪继续上升"
        elif cycle_score > -5:
            cycle_position = "情绪平衡期"
            cycle_stage = "平静期"
            next_direction = "等待方向选择"
        elif cycle_score > -15:
            cycle_position = "情绪下降期"
            cycle_stage = "悲观期"
            next_direction = "情绪继续下行"
        else:
            cycle_position = "情绪底部区域"
            cycle_stage = "绝望期"
            next_direction = "情绪反弹机会"
            
        return {
            "cycle_position": cycle_position,
            "cycle_stage": cycle_stage,
            "cycle_score": round(cycle_score, 2),
            "next_direction": next_direction,
            "reversal_probability": "高" if abs(cycle_score) > 20 else "中" if abs(cycle_score) > 10 else "低"
        }
    
    def identify_reversal_signals(self, price_change_pct: float, volume_ratio: float, volatility: float) -> Dict[str, Any]:
        """
        识别情绪反转信号
        Identify sentiment reversal signals
        """
        reversal_signals = []
        reversal_strength = 0
        
        # 极端价格变化信号
        if abs(price_change_pct) > 8:
            reversal_signals.append("极端价格变化")
            reversal_strength += 3
            
        # 成交量异常信号
        if volume_ratio > 2.0:
            reversal_signals.append("成交量异常放大")
            reversal_strength += 2
        elif volume_ratio < 0.5:
            reversal_signals.append("成交量异常萎缩")
            reversal_strength += 1
            
        # 波动率异常信号
        if volatility > 3.0:
            reversal_signals.append("波动率异常升高")
            reversal_strength += 2
            
        # 综合反转信号
        if price_change_pct > 10 and volume_ratio > 1.5:
            reversal_signals.append("疯狂上涨信号")
            reversal_strength += 4
        elif price_change_pct < -8 and volume_ratio > 1.3:
            reversal_signals.append("恐慌性下跌信号")
            reversal_strength += 4
            
        # 反转概率评估
        if reversal_strength >= 6:
            reversal_probability = "很高"
            reversal_timeframe = "1-3个交易日"
        elif reversal_strength >= 4:
            reversal_probability = "高"
            reversal_timeframe = "3-7个交易日"
        elif reversal_strength >= 2:
            reversal_probability = "中等"
            reversal_timeframe = "1-2周"
        else:
            reversal_probability = "低"
            reversal_timeframe = "不确定"
            
        return {
            "reversal_signals": reversal_signals,
            "reversal_strength": reversal_strength,
            "reversal_probability": reversal_probability,
            "reversal_timeframe": reversal_timeframe,
            "recommended_action": "减仓观望" if reversal_strength >= 4 else "正常持有" if reversal_strength >= 2 else "可适当加仓"
        }
    
    def generate_investment_advice(self, sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成投资建议
        Generate investment advice based on sentiment analysis
        """
        fear_greed = sentiment_analysis["market_sentiment"]["fear_greed_index"]
        psychology = sentiment_analysis["investor_psychology"]["psychology_state"]
        technical = sentiment_analysis["technical_sentiment"]["technical_sentiment"]
        reversal_prob = sentiment_analysis["reversal_signals"]["reversal_probability"]
        
        # 综合评分
        if fear_greed > 70:
            action = "建议减仓"
            position_size = "25-50%"
            risk_level = "高"
        elif fear_greed > 55:
            action = "适当减仓"
            position_size = "50-75%"
            risk_level = "中高"
        elif fear_greed > 45:
            action = "维持仓位"
            position_size = "75-100%"
            risk_level = "中等"
        elif fear_greed > 25:
            action = "适当加仓"
            position_size = "100-125%"
            risk_level = "中低"
        else:
            action = "积极买入"
            position_size = "125-150%"
            risk_level = "低"
            
        # 时间框架建议
        if reversal_prob in ["很高", "高"]:
            time_horizon = "短期(1-2周)"
            strategy_type = "波段操作"
        else:
            time_horizon = "中期(1-3个月)"
            strategy_type = "趋势跟随"
            
        return {
            "recommended_action": action,
            "position_size": position_size,
            "risk_level": risk_level,
            "time_horizon": time_horizon,
            "strategy_type": strategy_type,
            "entry_timing": "立即" if fear_greed < 30 else "分批" if fear_greed < 60 else "谨慎",
            "stop_loss_suggestion": f"{abs(sentiment_analysis['stock_data']['price_change_pct'] * 0.5):.1f}%"
        }
    
    def assess_risk_warnings(self, sentiment_analysis: Dict[str, Any]) -> List[str]:
        """
        评估风险提示
        Assess risk warnings
        """
        warnings = []
        
        fear_greed = sentiment_analysis["market_sentiment"]["fear_greed_index"]
        volatility = sentiment_analysis["stock_data"]["volatility"]
        reversal_strength = sentiment_analysis["reversal_signals"]["reversal_strength"]
        
        if fear_greed > 80:
            warnings.append("⚠️ 市场情绪过度乐观，存在泡沫风险")
        elif fear_greed < 20:
            warnings.append("⚠️ 市场情绪过度悲观，可能存在超跌")
            
        if volatility > 2.5:
            warnings.append("⚠️ 波动率异常升高，短期风险较大")
            
        if reversal_strength >= 6:
            warnings.append("⚠️ 强烈反转信号，趋势可能即将改变")
            
        if sentiment_analysis["capital_flow"]["flow_intensity"] > 100:
            warnings.append("⚠️ 资金流动异常活跃，需注意流动性风险")
            
        if sentiment_analysis["macro_sentiment"]["systemic_risk"] == "高":
            warnings.append("⚠️ 系统性风险较高，建议降低仓位")
            
        return warnings if warnings else ["✅ 当前风险水平可控，但仍需密切关注市场变化"]
    
    def calculate_return_expectation(self, sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算预期收益评估
        Calculate expected return assessment
        """
        fear_greed = sentiment_analysis["market_sentiment"]["fear_greed_index"]
        price_change_pct = sentiment_analysis["stock_data"]["price_change_pct"]
        
        # 基于情绪指标预测收益
        if fear_greed > 75:
            expected_return_1w = f"-2% 到 -8%"
            expected_return_1m = f"-5% 到 -15%"
            probability = "60-70%"
        elif fear_greed > 55:
            expected_return_1w = f"-1% 到 +3%"
            expected_return_1m = f"-3% 到 +8%"
            probability = "55-65%"
        elif fear_greed > 45:
            expected_return_1w = f"-2% 到 +2%"
            expected_return_1m = f"-5% 到 +5%"
            probability = "50-60%"
        elif fear_greed > 25:
            expected_return_1w = f"+1% 到 +5%"
            expected_return_1m = f"+3% 到 +12%"
            probability = "55-65%"
        else:
            expected_return_1w = f"+3% 到 +10%"
            expected_return_1m = f"+8% 到 +25%"
            probability = "60-75%"
            
        return {
            "expected_return_1week": expected_return_1w,
            "expected_return_1month": expected_return_1m,
            "confidence_probability": probability,
            "risk_adjusted_return": f"夏普比率预估: {(fear_greed - 50) / 100:.2f}",
            "maximum_drawdown_risk": f"{max(5, abs(price_change_pct * 0.8)):.1f}%"
        }
    
    def analyze_stock_sentiment(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主要分析函数
        Main analysis function
        """
        # 提取股票数据
        stock_code = stock_data["stock_code"]
        current_price = stock_data["current_price"]
        price_change = stock_data["price_change"]
        price_change_pct = stock_data["price_change_pct"]
        volatility = stock_data["volatility"]
        volume_ratio = stock_data["volume_ratio"]
        
        # 执行各项分析
        market_sentiment = self.calculate_fear_greed_index(price_change_pct, volume_ratio, volatility)
        investor_psychology = self.analyze_investor_psychology(price_change, price_change_pct, volume_ratio)
        capital_flow = self.analyze_capital_flow(price_change, volume_ratio, volatility)
        technical_sentiment = self.analyze_technical_sentiment(current_price, price_change_pct, volatility)
        fundamental_sentiment = self.analyze_fundamental_sentiment(stock_code, current_price, price_change_pct)
        macro_sentiment = self.analyze_macro_sentiment(price_change_pct)
        sentiment_cycle = self.analyze_sentiment_cycle(price_change_pct, volume_ratio, volatility)
        reversal_signals = self.identify_reversal_signals(price_change_pct, volume_ratio, volatility)
        
        # 综合分析结果
        analysis_result = {
            "analysis_metadata": {
                "stock_code": stock_code,
                "analysis_date": self.analysis_date,
                "analyzer_version": "1.0.0"
            },
            "stock_data": stock_data,
            "market_sentiment": market_sentiment,
            "investor_psychology": investor_psychology,
            "capital_flow": capital_flow,
            "technical_sentiment": technical_sentiment,
            "fundamental_sentiment": fundamental_sentiment,
            "macro_sentiment": macro_sentiment,
            "sentiment_cycle": sentiment_cycle,
            "reversal_signals": reversal_signals
        }
        
        # 生成投资建议和风险评估
        investment_advice = self.generate_investment_advice(analysis_result)
        risk_warnings = self.assess_risk_warnings(analysis_result)
        return_expectation = self.calculate_return_expectation(analysis_result)
        
        # 完整分析报告
        analysis_result.update({
            "investment_advice": investment_advice,
            "risk_warnings": risk_warnings,
            "return_expectation": return_expectation,
            "overall_sentiment_score": round(market_sentiment["fear_greed_index"], 2),
            "recommendation_summary": {
                "primary_recommendation": investment_advice["recommended_action"],
                "confidence_level": "高" if market_sentiment["fear_greed_index"] > 60 or market_sentiment["fear_greed_index"] < 40 else "中等",
                "key_risk_factors": risk_warnings[:2] if len(risk_warnings) > 2 else risk_warnings
            }
        })
        
        return analysis_result


def main():
    """主函数"""
    # 输入的港股数据
    stock_data = {
        "stock_code": "0700.HK",
        "current_price": 644.0,
        "price_change": 57.00,
        "price_change_pct": 9.71,
        "volatility": 1.38,
        "volume_ratio": 0.89
    }
    
    # 创建分析器并执行分析
    analyzer = HKStockSentimentAnalyzer()
    analysis_result = analyzer.analyze_stock_sentiment(stock_data)
    
    # 输出JSON格式结果
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()