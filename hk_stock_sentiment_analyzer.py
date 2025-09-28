#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场情绪分析代理
专业的市场情绪分析师，提供多维度情绪分析和投资建议
"""

import json
import math
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

class SentimentLevel(Enum):
    """情绪水平枚举"""
    EXTREME_FEAR = "极度恐慌"
    FEAR = "恐慌"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"

class InvestorPsychology(Enum):
    """投资者心理状态"""
    PESSIMISTIC = "悲观"
    CAUTIOUS = "谨慎"
    NEUTRAL = "中性"
    OPTIMISTIC = "乐观"
    EUPHORIC = "狂热"

class TechnicalSentiment(Enum):
    """技术面情绪"""
    OVERSOLD = "超卖"
    BEARISH = "看跌"
    NEUTRAL = "中性"
    BULLISH = "看涨"
    OVERBOUGHT = "超买"

@dataclass
class StockData:
    """股票数据结构"""
    symbol: str
    current_price: float
    price_change: float
    price_change_pct: float
    volatility: float
    volume_ratio: float

@dataclass
class SentimentAnalysis:
    """情绪分析结果"""
    fear_greed_index: float
    investor_psychology: InvestorPsychology
    capital_flow_sentiment: Dict[str, Any]
    technical_sentiment: TechnicalSentiment
    fundamental_sentiment: Dict[str, Any]
    macro_sentiment: Dict[str, Any]
    sentiment_cycle: Dict[str, Any]
    reversal_signals: List[str]

class HKStockSentimentAnalyzer:
    """港股市场情绪分析器"""
    
    def __init__(self):
        self.analysis_timestamp = datetime.now()
        
    def calculate_fear_greed_index(self, stock_data: StockData) -> Tuple[float, SentimentLevel]:
        """
        计算恐慌贪婪指数 (0-100)
        综合价格变动、波动率、成交量等因素
        """
        # 基础分数从50开始
        base_score = 50.0
        
        # 价格变动影响 (-30 to +30)
        price_impact = min(30, max(-30, stock_data.price_change_pct * 3))
        
        # 波动率影响 (-15 to +15)
        # 低波动率增加贪婪，高波动率增加恐慌
        volatility_impact = -min(15, max(-15, (stock_data.volatility - 1.0) * 10))
        
        # 成交量影响 (-10 to +10)
        # 高成交量配合上涨为贪婪，配合下跌为恐慌
        volume_impact = (stock_data.volume_ratio - 1.0) * 10
        if stock_data.price_change < 0:
            volume_impact = -abs(volume_impact)  # 下跌时高成交量为恐慌
        else:
            volume_impact = abs(volume_impact)   # 上涨时高成交量为贪婪
            
        volume_impact = min(10, max(-10, volume_impact))
        
        # 计算最终指数
        fear_greed_score = base_score + price_impact + volatility_impact + volume_impact
        fear_greed_score = min(100, max(0, fear_greed_score))
        
        # 确定情绪水平
        if fear_greed_score <= 20:
            sentiment_level = SentimentLevel.EXTREME_FEAR
        elif fear_greed_score <= 40:
            sentiment_level = SentimentLevel.FEAR
        elif fear_greed_score <= 60:
            sentiment_level = SentimentLevel.NEUTRAL
        elif fear_greed_score <= 80:
            sentiment_level = SentimentLevel.GREED
        else:
            sentiment_level = SentimentLevel.EXTREME_GREED
            
        return fear_greed_score, sentiment_level
    
    def analyze_investor_psychology(self, stock_data: StockData, fear_greed_score: float) -> InvestorPsychology:
        """分析投资者心理状态"""
        # 综合恐慌贪婪指数和价格变动
        if fear_greed_score <= 25 or stock_data.price_change_pct <= -5:
            return InvestorPsychology.PESSIMISTIC
        elif fear_greed_score <= 45 or stock_data.price_change_pct <= -2:
            return InvestorPsychology.CAUTIOUS
        elif fear_greed_score <= 65 and abs(stock_data.price_change_pct) <= 3:
            return InvestorPsychology.NEUTRAL
        elif fear_greed_score <= 85 or stock_data.price_change_pct >= 5:
            return InvestorPsychology.OPTIMISTIC
        else:
            return InvestorPsychology.EUPHORIC
    
    def analyze_capital_flow(self, stock_data: StockData) -> Dict[str, Any]:
        """分析资金流向"""
        # 基于成交量比率和价格变动分析资金流向
        volume_strength = "强劲" if stock_data.volume_ratio > 1.2 else "适中" if stock_data.volume_ratio > 0.8 else "疲软"
        
        # 主力资金判断
        if stock_data.price_change_pct > 3 and stock_data.volume_ratio > 1.1:
            main_capital = "大幅流入"
        elif stock_data.price_change_pct > 0 and stock_data.volume_ratio > 0.9:
            main_capital = "净流入"
        elif stock_data.price_change_pct < -3 and stock_data.volume_ratio > 1.1:
            main_capital = "大幅流出"
        elif stock_data.price_change_pct < 0 and stock_data.volume_ratio > 0.9:
            main_capital = "净流出"
        else:
            main_capital = "观望"
            
        # 散户资金判断（与主力相反或跟随）
        if main_capital in ["大幅流入", "净流入"]:
            retail_capital = "跟随流入" if stock_data.volume_ratio > 1.0 else "观望"
        elif main_capital in ["大幅流出", "净流出"]:
            retail_capital = "恐慌流出" if stock_data.volume_ratio > 1.0 else "观望"
        else:
            retail_capital = "观望"
            
        return {
            "成交量强度": volume_strength,
            "主力资金": main_capital,
            "散户资金": retail_capital,
            "资金流向评分": min(100, max(0, 50 + stock_data.price_change_pct * 5 + (stock_data.volume_ratio - 1) * 30))
        }
    
    def analyze_technical_sentiment(self, stock_data: StockData) -> TechnicalSentiment:
        """分析技术面情绪"""
        # 基于价格变动和波动率判断技术面情绪
        if stock_data.price_change_pct > 8:
            return TechnicalSentiment.OVERBOUGHT
        elif stock_data.price_change_pct > 3:
            return TechnicalSentiment.BULLISH
        elif stock_data.price_change_pct < -8:
            return TechnicalSentiment.OVERSOLD
        elif stock_data.price_change_pct < -3:
            return TechnicalSentiment.BEARISH
        else:
            return TechnicalSentiment.NEUTRAL
    
    def analyze_fundamental_sentiment(self, stock_data: StockData) -> Dict[str, Any]:
        """分析基本面情绪"""
        # 基于股票代码和价格变动分析基本面情绪
        # 腾讯作为科技龙头的特殊分析
        if stock_data.symbol == "0700.HK":
            if stock_data.price_change_pct > 5:
                valuation_sentiment = "估值修复"
                growth_sentiment = "成长预期强烈"
            elif stock_data.price_change_pct > 0:
                valuation_sentiment = "估值合理"
                growth_sentiment = "成长预期乐观"
            elif stock_data.price_change_pct > -5:
                valuation_sentiment = "估值承压"
                growth_sentiment = "成长预期谨慎"
            else:
                valuation_sentiment = "估值低估"
                growth_sentiment = "成长预期悲观"
        else:
            # 一般股票的基本面分析
            if stock_data.price_change_pct > 3:
                valuation_sentiment = "估值偏高"
                growth_sentiment = "成长预期积极"
            elif stock_data.price_change_pct > 0:
                valuation_sentiment = "估值合理"
                growth_sentiment = "成长预期平稳"
            else:
                valuation_sentiment = "估值偏低"
                growth_sentiment = "成长预期疲软"
                
        return {
            "估值情绪": valuation_sentiment,
            "成长情绪": growth_sentiment,
            "基本面评分": min(100, max(0, 50 + stock_data.price_change_pct * 3))
        }
    
    def analyze_macro_sentiment(self, stock_data: StockData) -> Dict[str, Any]:
        """分析宏观情绪影响"""
        # 基于当前市场环境的宏观分析
        policy_impact = "积极" if stock_data.price_change_pct > 3 else "中性" if stock_data.price_change_pct > -3 else "消极"
        economic_impact = "支撑" if stock_data.price_change_pct > 2 else "中性" if stock_data.price_change_pct > -2 else "压制"
        geopolitical_impact = "缓解" if stock_data.price_change_pct > 1 else "中性" if stock_data.price_change_pct > -1 else "紧张"
        
        return {
            "政策影响": policy_impact,
            "经济影响": economic_impact,
            "地缘政治": geopolitical_impact,
            "宏观评分": min(100, max(0, 50 + stock_data.price_change_pct * 2))
        }
    
    def analyze_sentiment_cycle(self, stock_data: StockData, fear_greed_score: float) -> Dict[str, Any]:
        """分析情绪周期"""
        # 判断当前所处的情绪周期阶段
        if fear_greed_score <= 20:
            cycle_stage = "情绪底部"
            cycle_description = "市场恐慌情绪达到极值，可能接近反转点"
        elif fear_greed_score <= 35:
            cycle_stage = "恐慌期"
            cycle_description = "市场仍处恐慌状态，但恐慌程度有所缓解"
        elif fear_greed_score <= 65:
            cycle_stage = "平衡期"
            cycle_description = "市场情绪相对平衡，多空力量均衡"
        elif fear_greed_score <= 80:
            cycle_stage = "乐观期"
            cycle_description = "市场情绪转向乐观，投资者信心增强"
        else:
            cycle_stage = "情绪顶部"
            cycle_description = "市场贪婪情绪浓厚，需警惕回调风险"
            
        return {
            "周期阶段": cycle_stage,
            "阶段描述": cycle_description,
            "周期评分": fear_greed_score
        }
    
    def identify_reversal_signals(self, stock_data: StockData, fear_greed_score: float) -> List[str]:
        """识别情绪反转信号"""
        signals = []
        
        # 极端情绪反转信号
        if fear_greed_score <= 15:
            signals.append("极度恐慌反转信号：市场恐慌达到极值，存在反弹机会")
        elif fear_greed_score >= 85:
            signals.append("极度贪婪反转信号：市场过度乐观，存在回调风险")
            
        # 成交量异常信号
        if stock_data.volume_ratio > 2.0:
            if stock_data.price_change_pct > 0:
                signals.append("放量上涨信号：成交量异常放大配合上涨，可能是情绪转换")
            else:
                signals.append("放量下跌信号：成交量异常放大配合下跌，可能是恐慌性抛售")
                
        # 波动率异常信号
        if stock_data.volatility > 2.0:
            signals.append("高波动率信号：市场波动加剧，情绪不稳定")
            
        # 价格异常变动信号
        if abs(stock_data.price_change_pct) > 10:
            signals.append("价格异动信号：单日涨跌幅过大，市场情绪极端")
            
        if not signals:
            signals.append("无明显反转信号：市场情绪相对稳定")
            
        return signals
    
    def generate_investment_advice(self, analysis: SentimentAnalysis, stock_data: StockData) -> Dict[str, Any]:
        """生成投资建议"""
        # 基于情绪分析生成投资建议
        advice_score = analysis.fear_greed_index
        
        if advice_score <= 25:
            investment_action = "积极买入"
            position_suggestion = "可考虑分批建仓，逢低加仓"
            time_horizon = "中长期持有"
            confidence_level = "高"
        elif advice_score <= 45:
            investment_action = "谨慎买入"
            position_suggestion = "小仓位试探，观察后续走势"
            time_horizon = "中期持有"
            confidence_level = "中等"
        elif advice_score <= 65:
            investment_action = "持有观望"
            position_suggestion = "维持现有仓位，等待明确信号"
            time_horizon = "短期观察"
            confidence_level = "中等"
        elif advice_score <= 80:
            investment_action = "谨慎减仓"
            position_suggestion = "可考虑部分获利了结"
            time_horizon = "短期调整"
            confidence_level = "中等"
        else:
            investment_action = "积极减仓"
            position_suggestion = "建议大幅减仓，规避风险"
            time_horizon = "短期避险"
            confidence_level = "高"
            
        return {
            "投资操作": investment_action,
            "仓位建议": position_suggestion,
            "持有期限": time_horizon,
            "信心水平": confidence_level,
            "建议评分": advice_score
        }
    
    def assess_risks(self, analysis: SentimentAnalysis, stock_data: StockData) -> Dict[str, Any]:
        """评估投资风险"""
        risks = []
        risk_level = "低风险"
        
        # 基于恐慌贪婪指数评估风险
        if analysis.fear_greed_index >= 80:
            risks.append("高估值风险：市场情绪过度乐观，存在回调压力")
            risk_level = "高风险"
        elif analysis.fear_greed_index <= 20:
            risks.append("流动性风险：市场恐慌可能导致流动性紧张")
            risk_level = "中风险"
            
        # 基于波动率评估风险
        if stock_data.volatility > 2.0:
            risks.append("波动风险：市场波动剧烈，价格不稳定")
            if risk_level == "低风险":
                risk_level = "中风险"
                
        # 基于成交量评估风险
        if stock_data.volume_ratio > 2.0:
            risks.append("成交量风险：异常放量可能预示重大变化")
            
        # 基于价格变动评估风险
        if abs(stock_data.price_change_pct) > 8:
            risks.append("价格风险：单日涨跌幅过大，存在反向调整压力")
            risk_level = "高风险"
            
        if not risks:
            risks.append("风险可控：当前市场状况相对稳定")
            
        return {
            "风险等级": risk_level,
            "主要风险": risks,
            "风险评分": min(100, max(0, 100 - analysis.fear_greed_index if analysis.fear_greed_index > 50 else analysis.fear_greed_index))
        }
    
    def estimate_expected_return(self, analysis: SentimentAnalysis, stock_data: StockData) -> Dict[str, Any]:
        """预期收益评估"""
        # 基于情绪分析估算预期收益
        base_return = 0.0
        
        # 基于恐慌贪婪指数调整预期收益
        if analysis.fear_greed_index <= 25:
            expected_return_short = 15.0  # 短期预期收益
            expected_return_medium = 25.0  # 中期预期收益
            return_confidence = "高"
        elif analysis.fear_greed_index <= 45:
            expected_return_short = 8.0
            expected_return_medium = 15.0
            return_confidence = "中等"
        elif analysis.fear_greed_index <= 65:
            expected_return_short = 3.0
            expected_return_medium = 8.0
            return_confidence = "中等"
        elif analysis.fear_greed_index <= 80:
            expected_return_short = -2.0
            expected_return_medium = 5.0
            return_confidence = "低"
        else:
            expected_return_short = -8.0
            expected_return_medium = 0.0
            return_confidence = "低"
            
        # 基于当前价格变动调整
        momentum_factor = stock_data.price_change_pct * 0.3
        expected_return_short += momentum_factor
        expected_return_medium += momentum_factor * 0.5
        
        return {
            "短期收益预期": f"{expected_return_short:.1f}%",
            "中期收益预期": f"{expected_return_medium:.1f}%",
            "收益信心度": return_confidence,
            "收益评分": min(100, max(0, 50 + expected_return_medium))
        }
    
    def analyze_sentiment(self, stock_data: StockData) -> Dict[str, Any]:
        """执行完整的情绪分析"""
        # 1. 计算恐慌贪婪指数
        fear_greed_score, sentiment_level = self.calculate_fear_greed_index(stock_data)
        
        # 2. 分析投资者心理
        psychology = self.analyze_investor_psychology(stock_data, fear_greed_score)
        
        # 3. 分析资金流向
        capital_flow = self.analyze_capital_flow(stock_data)
        
        # 4. 分析技术面情绪
        technical_sentiment = self.analyze_technical_sentiment(stock_data)
        
        # 5. 分析基本面情绪
        fundamental_sentiment = self.analyze_fundamental_sentiment(stock_data)
        
        # 6. 分析宏观情绪
        macro_sentiment = self.analyze_macro_sentiment(stock_data)
        
        # 7. 分析情绪周期
        sentiment_cycle = self.analyze_sentiment_cycle(stock_data, fear_greed_score)
        
        # 8. 识别反转信号
        reversal_signals = self.identify_reversal_signals(stock_data, fear_greed_score)
        
        # 创建分析结果对象
        analysis = SentimentAnalysis(
            fear_greed_index=fear_greed_score,
            investor_psychology=psychology,
            capital_flow_sentiment=capital_flow,
            technical_sentiment=technical_sentiment,
            fundamental_sentiment=fundamental_sentiment,
            macro_sentiment=macro_sentiment,
            sentiment_cycle=sentiment_cycle,
            reversal_signals=reversal_signals
        )
        
        # 生成投资建议
        investment_advice = self.generate_investment_advice(analysis, stock_data)
        
        # 评估风险
        risk_assessment = self.assess_risks(analysis, stock_data)
        
        # 预期收益评估
        return_estimation = self.estimate_expected_return(analysis, stock_data)
        
        # 构建完整的分析结果
        result = {
            "分析时间": self.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "股票信息": {
                "股票代码": stock_data.symbol,
                "当前价格": stock_data.current_price,
                "价格变化": stock_data.price_change,
                "变化幅度": f"{stock_data.price_change_pct:.2f}%",
                "波动率": f"{stock_data.volatility:.2f}%",
                "成交量比率": stock_data.volume_ratio
            },
            "市场情绪指标": {
                "恐慌贪婪指数": {
                    "数值": round(fear_greed_score, 1),
                    "等级": sentiment_level.value,
                    "描述": f"当前市场情绪为{sentiment_level.value}，指数为{fear_greed_score:.1f}"
                }
            },
            "投资者心理状态": {
                "心理状态": psychology.value,
                "状态描述": self._get_psychology_description(psychology),
                "建议": self._get_psychology_advice(psychology)
            },
            "资金流向分析": capital_flow,
            "技术面情绪": {
                "技术状态": technical_sentiment.value,
                "技术描述": self._get_technical_description(technical_sentiment),
                "技术建议": self._get_technical_advice(technical_sentiment)
            },
            "基本面情绪": fundamental_sentiment,
            "宏观情绪影响": macro_sentiment,
            "情绪周期分析": sentiment_cycle,
            "情绪反转信号": {
                "信号数量": len(reversal_signals),
                "具体信号": reversal_signals
            },
            "投资建议": investment_advice,
            "风险提示": risk_assessment,
            "预期收益评估": return_estimation,
            "综合评分": {
                "情绪评分": round(fear_greed_score, 1),
                "投资评分": round(investment_advice["建议评分"], 1),
                "风险评分": round(risk_assessment["风险评分"], 1),
                "收益评分": round(return_estimation["收益评分"], 1)
            }
        }
        
        return result
    
    def _get_psychology_description(self, psychology: InvestorPsychology) -> str:
        """获取心理状态描述"""
        descriptions = {
            InvestorPsychology.PESSIMISTIC: "投资者普遍悲观，担忧情绪浓厚，倾向于避险",
            InvestorPsychology.CAUTIOUS: "投资者保持谨慎，观望情绪较重，等待明确信号",
            InvestorPsychology.NEUTRAL: "投资者心态相对平和，多空情绪基本均衡",
            InvestorPsychology.OPTIMISTIC: "投资者情绪乐观，信心较强，愿意承担风险",
            InvestorPsychology.EUPHORIC: "投资者情绪狂热，过度乐观，需警惕风险"
        }
        return descriptions.get(psychology, "心理状态未知")
    
    def _get_psychology_advice(self, psychology: InvestorPsychology) -> str:
        """获取心理状态建议"""
        advice = {
            InvestorPsychology.PESSIMISTIC: "逆向思维，关注被低估的优质标的",
            InvestorPsychology.CAUTIOUS: "保持耐心，等待更好的入场时机",
            InvestorPsychology.NEUTRAL: "均衡配置，关注基本面变化",
            InvestorPsychology.OPTIMISTIC: "适度参与，控制仓位风险",
            InvestorPsychology.EUPHORIC: "保持冷静，考虑逐步减仓"
        }
        return advice.get(psychology, "建议未知")
    
    def _get_technical_description(self, technical: TechnicalSentiment) -> str:
        """获取技术面描述"""
        descriptions = {
            TechnicalSentiment.OVERSOLD: "技术指标显示超卖，短期可能反弹",
            TechnicalSentiment.BEARISH: "技术面偏弱，下行压力较大",
            TechnicalSentiment.NEUTRAL: "技术面中性，多空力量均衡",
            TechnicalSentiment.BULLISH: "技术面向好，上行动能较强",
            TechnicalSentiment.OVERBOUGHT: "技术指标显示超买，存在调整压力"
        }
        return descriptions.get(technical, "技术状态未知")
    
    def _get_technical_advice(self, technical: TechnicalSentiment) -> str:
        """获取技术面建议"""
        advice = {
            TechnicalSentiment.OVERSOLD: "关注反弹机会，可考虑逢低买入",
            TechnicalSentiment.BEARISH: "保持谨慎，避免盲目抄底",
            TechnicalSentiment.NEUTRAL: "观望为主，等待方向选择",
            TechnicalSentiment.BULLISH: "可适度参与，注意止盈",
            TechnicalSentiment.OVERBOUGHT: "谨慎追高，考虑获利了结"
        }
        return advice.get(technical, "建议未知")

def main():
    """主函数 - 分析腾讯控股数据"""
    # 创建分析器
    analyzer = HKStockSentimentAnalyzer()
    
    # 输入的股票数据
    stock_data = StockData(
        symbol="0700.HK",
        current_price=644.0,
        price_change=57.00,
        price_change_pct=9.71,
        volatility=1.38,
        volume_ratio=0.89
    )
    
    print("=== 港股市场情绪分析代理 ===")
    print(f"正在分析股票: {stock_data.symbol} (腾讯控股)")
    print(f"当前价格: HK${stock_data.current_price}")
    print(f"价格变化: +{stock_data.price_change} (+{stock_data.price_change_pct}%)")
    print("=" * 50)
    
    # 执行分析
    analysis_result = analyzer.analyze_sentiment(stock_data)
    
    # 输出JSON格式结果
    print("\n=== 详细分析结果 (JSON格式) ===")
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return analysis_result

if __name__ == "__main__":
    result = main()