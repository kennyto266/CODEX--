#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股Sentiment分析代理 - 專業量化分析工具
針對0700.HK (騰訊控股) 進行綜合分析
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import math

class HKStockSentimentAnalyzer:
    """港股Sentiment分析器"""
    
    def __init__(self):
        self.stock_code = "0700.HK"
        self.stock_name = "騰訊控股"
        self.current_price = 644.0
        self.price_change = 57.00
        self.price_change_percent = 9.71
        self.analysis_period = 30  # 交易日
        
    def calculate_technical_indicators(self) -> Dict[str, Any]:
        """計算技術指標"""
        # 基於價格變動計算技術指標
        previous_price = self.current_price - self.price_change
        volatility = abs(self.price_change_percent)
        
        # RSI估算 (基於價格變動幅度)
        rsi_estimate = 50 + (self.price_change_percent * 2)
        rsi_estimate = max(0, min(100, rsi_estimate))
        
        # 動量指標
        momentum_strength = "強勁" if abs(self.price_change_percent) > 8 else "中等" if abs(self.price_change_percent) > 4 else "溫和"
        
        return {
            "previous_price": previous_price,
            "volatility": volatility,
            "rsi_estimate": round(rsi_estimate, 2),
            "momentum_strength": momentum_strength,
            "price_trend": "上升" if self.price_change > 0 else "下跌"
        }
    
    def analyze_market_sentiment(self) -> Dict[str, Any]:
        """分析市場情緒"""
        technical_data = self.calculate_technical_indicators()
        
        # 情緒評分 (0-100)
        sentiment_score = 50  # 基準分數
        
        # 基於價格變動調整情緒分數
        if self.price_change_percent > 8:
            sentiment_score += 30  # 強勁上漲
        elif self.price_change_percent > 4:
            sentiment_score += 20  # 中等上漲
        elif self.price_change_percent > 0:
            sentiment_score += 10  # 溫和上漲
        elif self.price_change_percent < -8:
            sentiment_score -= 30  # 強勁下跌
        elif self.price_change_percent < -4:
            sentiment_score -= 20  # 中等下跌
        else:
            sentiment_score -= 10  # 溫和下跌
            
        sentiment_score = max(0, min(100, sentiment_score))
        
        # 情緒標籤
        if sentiment_score >= 80:
            sentiment_label = "極度樂觀"
        elif sentiment_score >= 65:
            sentiment_label = "樂觀"
        elif sentiment_score >= 45:
            sentiment_label = "中性"
        elif sentiment_score >= 30:
            sentiment_label = "悲觀"
        else:
            sentiment_label = "極度悲觀"
            
        return {
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "market_momentum": technical_data["momentum_strength"],
            "trend_direction": technical_data["price_trend"]
        }
    
    def generate_professional_analysis(self) -> Dict[str, Any]:
        """生成專業分析"""
        technical_data = self.calculate_technical_indicators()
        sentiment_data = self.analyze_market_sentiment()
        
        # 技術面分析
        technical_analysis = {
            "price_action": f"股價從{technical_data['previous_price']:.2f}港元上升至{self.current_price}港元",
            "percentage_move": f"漲幅{self.price_change_percent}%，表現{technical_data['momentum_strength']}",
            "rsi_indication": f"RSI估算值{technical_data['rsi_estimate']}，" + 
                            ("可能進入超買區域" if technical_data['rsi_estimate'] > 70 else 
                             "可能進入超賣區域" if technical_data['rsi_estimate'] < 30 else "處於正常範圍"),
            "volatility_assessment": f"波動率{technical_data['volatility']:.2f}%，" +
                                  ("高波動" if technical_data['volatility'] > 8 else 
                                   "中等波動" if technical_data['volatility'] > 4 else "低波動")
        }
        
        # 基本面考量 (基於騰訊的業務特性)
        fundamental_factors = [
            "遊戲業務受監管政策影響",
            "雲服務業務增長潛力",
            "金融科技業務發展",
            "廣告收入受經濟週期影響",
            "國際業務擴張進展"
        ]
        
        return {
            "technical_analysis": technical_analysis,
            "fundamental_considerations": fundamental_factors,
            "market_sentiment": sentiment_data,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def generate_investment_advice(self) -> Dict[str, Any]:
        """生成投資建議"""
        sentiment_data = self.analyze_market_sentiment()
        
        # 基於sentiment分數生成建議
        if sentiment_data["sentiment_score"] >= 75:
            recommendation = "買入"
            rationale = "市場情緒極度樂觀，技術面強勁，適合積極投資者"
            target_price = self.current_price * 1.15  # 15%上漲目標
        elif sentiment_data["sentiment_score"] >= 60:
            recommendation = "持有/小幅買入"
            rationale = "市場情緒樂觀，可考慮逐步建倉"
            target_price = self.current_price * 1.08  # 8%上漲目標
        elif sentiment_data["sentiment_score"] >= 40:
            recommendation = "持有"
            rationale = "市場情緒中性，建議觀望"
            target_price = self.current_price * 1.03  # 3%上漲目標
        elif sentiment_data["sentiment_score"] >= 25:
            recommendation = "減持"
            rationale = "市場情緒悲觀，建議降低持倉"
            target_price = self.current_price * 0.95  # 5%下跌預期
        else:
            recommendation = "賣出"
            rationale = "市場情緒極度悲觀，建議退出持倉"
            target_price = self.current_price * 0.90  # 10%下跌預期
            
        return {
            "recommendation": recommendation,
            "rationale": rationale,
            "target_price": round(target_price, 2),
            "time_horizon": "1-3個月",
            "position_sizing": "建議單一股票持倉不超過投資組合的10%"
        }
    
    def assess_risks(self) -> Dict[str, Any]:
        """評估投資風險"""
        technical_data = self.calculate_technical_indicators()
        
        # 風險等級評估
        risk_factors = []
        risk_score = 0
        
        # 波動性風險
        if technical_data["volatility"] > 10:
            risk_factors.append("高波動性風險")
            risk_score += 3
        elif technical_data["volatility"] > 5:
            risk_factors.append("中等波動性風險")
            risk_score += 2
        else:
            risk_factors.append("低波動性風險")
            risk_score += 1
            
        # 技術面風險
        if technical_data["rsi_estimate"] > 80:
            risk_factors.append("技術面超買風險")
            risk_score += 3
        elif technical_data["rsi_estimate"] < 20:
            risk_factors.append("技術面超賣風險")
            risk_score += 2
            
        # 行業特定風險
        industry_risks = [
            "監管政策變化風險",
            "競爭加劇風險",
            "技術變革風險",
            "宏觀經濟風險",
            "匯率波動風險"
        ]
        
        risk_factors.extend(industry_risks)
        risk_score += len(industry_risks)
        
        # 風險等級
        if risk_score >= 12:
            risk_level = "高風險"
        elif risk_score >= 8:
            risk_level = "中高風險"
        elif risk_score >= 5:
            risk_level = "中等風險"
        else:
            risk_level = "低風險"
            
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "mitigation_strategies": [
                "分散投資降低單一股票風險",
                "設定止損點控制下跌風險",
                "定期檢視持倉並調整策略",
                "關注公司基本面變化",
                "留意市場整體趨勢"
            ]
        }
    
    def generate_complete_analysis(self) -> Dict[str, Any]:
        """生成完整分析報告"""
        return {
            "股票信息": {
                "代碼": self.stock_code,
                "名稱": self.stock_name,
                "當前價格": self.current_price,
                "價格變化": self.price_change,
                "變化百分比": f"{self.price_change_percent}%",
                "分析期間": f"{self.analysis_period}個交易日"
            },
            "專業分析": self.generate_professional_analysis(),
            "投資建議": self.generate_investment_advice(),
            "風險評估": self.assess_risks(),
            "免責聲明": "本分析僅供參考，投資有風險，請謹慎決策"
        }

def main():
    """主函數"""
    analyzer = HKStockSentimentAnalyzer()
    analysis_result = analyzer.generate_complete_analysis()
    
    # 輸出JSON格式結果
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return analysis_result

if __name__ == "__main__":
    main()