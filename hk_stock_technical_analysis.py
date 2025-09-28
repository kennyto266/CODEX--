#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股技術分析AI代理
專門針對港股市場的量化技術分析工具
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Any, Tuple

class HKStockTechnicalAnalyzer:
    """港股技術分析器"""
    
    def __init__(self):
        self.analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_technical_indicators(self, current_price: float, price_change: float, 
                                     change_percent: float, period_days: int) -> Dict[str, Any]:
        """計算技術指標"""
        
        # 計算前期價格
        previous_price = current_price - price_change
        
        # 波動率分析 (基於價格變化幅度)
        volatility = abs(change_percent)
        
        # 動量指標
        momentum_strength = self._classify_momentum(change_percent)
        
        # 支撐阻力位分析
        support_resistance = self._calculate_support_resistance(current_price, previous_price)
        
        # 趨勢強度
        trend_strength = self._analyze_trend_strength(change_percent, period_days)
        
        return {
            "current_price": current_price,
            "previous_price": round(previous_price, 2),
            "price_change": price_change,
            "change_percent": change_percent,
            "volatility": volatility,
            "momentum_strength": momentum_strength,
            "support_resistance": support_resistance,
            "trend_strength": trend_strength,
            "period_days": period_days
        }
    
    def _classify_momentum(self, change_percent: float) -> Dict[str, Any]:
        """分類動量強度"""
        if change_percent >= 10:
            return {"level": "極強", "score": 5, "description": "強烈上漲動量，市場情緒極度樂觀"}
        elif change_percent >= 5:
            return {"level": "強", "score": 4, "description": "強勁上漲動量，積極市場情緒"}
        elif change_percent >= 2:
            return {"level": "中等", "score": 3, "description": "溫和上漲動量，市場情緒正面"}
        elif change_percent >= -2:
            return {"level": "弱", "score": 2, "description": "橫盤整理，市場情緒中性"}
        elif change_percent >= -5:
            return {"level": "負面", "score": 1, "description": "下跌動量，市場情緒轉弱"}
        else:
            return {"level": "極弱", "score": 0, "description": "強烈下跌動量，市場情緒悲觀"}
    
    def _calculate_support_resistance(self, current_price: float, previous_price: float) -> Dict[str, float]:
        """計算支撐阻力位"""
        price_range = abs(current_price - previous_price)
        
        # 基於價格波動計算關鍵位
        if current_price > previous_price:
            # 上漲趨勢
            support_1 = round(previous_price, 2)
            support_2 = round(previous_price - price_range * 0.5, 2)
            resistance_1 = round(current_price + price_range * 0.618, 2)  # 黃金分割
            resistance_2 = round(current_price + price_range * 1.0, 2)
        else:
            # 下跌或橫盤
            support_1 = round(current_price - price_range * 0.618, 2)
            support_2 = round(current_price - price_range * 1.0, 2)
            resistance_1 = round(previous_price, 2)
            resistance_2 = round(previous_price + price_range * 0.5, 2)
        
        return {
            "support_1": support_1,
            "support_2": support_2,
            "resistance_1": resistance_1,
            "resistance_2": resistance_2
        }
    
    def _analyze_trend_strength(self, change_percent: float, period_days: int) -> Dict[str, Any]:
        """分析趨勢強度"""
        daily_avg_change = change_percent / period_days
        
        if abs(daily_avg_change) >= 0.5:
            strength = "強勁"
            confidence = 0.85
        elif abs(daily_avg_change) >= 0.3:
            strength = "中等"
            confidence = 0.70
        elif abs(daily_avg_change) >= 0.1:
            strength = "溫和"
            confidence = 0.60
        else:
            strength = "微弱"
            confidence = 0.45
        
        direction = "上升" if change_percent > 0 else "下降" if change_percent < 0 else "橫盤"
        
        return {
            "direction": direction,
            "strength": strength,
            "confidence": confidence,
            "daily_avg_change": round(daily_avg_change, 3)
        }
    
    def generate_investment_advice(self, indicators: Dict[str, Any], stock_code: str) -> Dict[str, Any]:
        """生成投資建議"""
        
        momentum_score = indicators["momentum_strength"]["score"]
        trend_confidence = indicators["trend_strength"]["confidence"]
        change_percent = indicators["change_percent"]
        
        # 綜合評分 (0-100)
        technical_score = (momentum_score * 20) + (trend_confidence * 50) + min(abs(change_percent), 10) * 3
        technical_score = min(100, max(0, technical_score))
        
        # 投資建議邏輯
        if technical_score >= 80 and change_percent > 5:
            recommendation = "強烈買入"
            action = "BUY_STRONG"
            reasoning = "技術指標顯示強勁上漲動量，建議積極買入"
        elif technical_score >= 65 and change_percent > 2:
            recommendation = "買入"
            action = "BUY"
            reasoning = "技術面偏向正面，適合逢低買入"
        elif technical_score >= 45:
            recommendation = "持有"
            action = "HOLD"
            reasoning = "技術面中性，建議持有觀望"
        elif technical_score >= 30:
            recommendation = "減持"
            action = "REDUCE"
            reasoning = "技術面轉弱，建議適度減持"
        else:
            recommendation = "賣出"
            action = "SELL"
            reasoning = "技術指標顯示下跌風險，建議賣出"
        
        # 目標價位計算
        current_price = indicators["current_price"]
        if change_percent > 0:
            target_price_high = round(current_price * (1 + min(change_percent/100 * 0.5, 0.15)), 2)
            target_price_low = round(current_price * 0.95, 2)
        else:
            target_price_high = round(current_price * 1.05, 2)
            target_price_low = round(current_price * (1 + max(change_percent/100 * 0.5, -0.15)), 2)
        
        return {
            "recommendation": recommendation,
            "action": action,
            "reasoning": reasoning,
            "technical_score": round(technical_score, 1),
            "target_price_range": {
                "high": target_price_high,
                "low": target_price_low
            },
            "time_horizon": "1-3個月",
            "confidence_level": round(trend_confidence * 100, 1)
        }
    
    def assess_risks(self, indicators: Dict[str, Any], stock_code: str) -> Dict[str, Any]:
        """風險評估"""
        
        volatility = indicators["volatility"]
        momentum_score = indicators["momentum_strength"]["score"]
        change_percent = indicators["change_percent"]
        
        # 風險等級評估
        if volatility >= 15:
            risk_level = "極高"
            risk_score = 5
        elif volatility >= 10:
            risk_level = "高"
            risk_score = 4
        elif volatility >= 5:
            risk_level = "中等"
            risk_score = 3
        elif volatility >= 2:
            risk_level = "低"
            risk_score = 2
        else:
            risk_level = "極低"
            risk_score = 1
        
        # 具體風險因素
        risk_factors = []
        
        if volatility > 10:
            risk_factors.append("高波動性風險：價格波動劇烈，短期風險較大")
        
        if abs(change_percent) > 8:
            risk_factors.append("動量風險：價格變化過於劇烈，可能面臨回調")
        
        if momentum_score <= 2:
            risk_factors.append("趨勢風險：技術面轉弱，下跌風險增加")
        
        # 騰訊特定風險 (0700.HK)
        if stock_code == "0700.HK":
            risk_factors.extend([
                "監管風險：中國科技股面臨政策不確定性",
                "市場風險：港股受外圍市場影響較大",
                "流動性風險：大型股票交易量波動影響價格"
            ])
        
        # 風險管理建議
        risk_management = {
            "stop_loss": round(indicators["current_price"] * 0.92, 2),
            "position_sizing": "建議單一股票持倉不超過組合的10-15%",
            "diversification": "建議分散投資不同行業和地區",
            "monitoring": "密切關注技術指標變化和基本面消息"
        }
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "risk_management": risk_management,
            "volatility_assessment": {
                "current_volatility": volatility,
                "volatility_level": "高" if volatility > 8 else "中等" if volatility > 4 else "低"
            }
        }
    
    def analyze_stock(self, stock_code: str, current_price: float, 
                     price_change: float, change_percent: float, period_days: int) -> Dict[str, Any]:
        """完整股票分析"""
        
        # 計算技術指標
        technical_indicators = self.calculate_technical_indicators(
            current_price, price_change, change_percent, period_days
        )
        
        # 生成投資建議
        investment_advice = self.generate_investment_advice(technical_indicators, stock_code)
        
        # 風險評估
        risk_assessment = self.assess_risks(technical_indicators, stock_code)
        
        # 市場環境分析
        market_context = self._analyze_market_context(change_percent, stock_code)
        
        return {
            "analysis_metadata": {
                "stock_code": stock_code,
                "analysis_date": self.analysis_date,
                "analyzer_type": "技術分析代理",
                "data_period": f"{period_days}個交易日"
            },
            "technical_analysis": {
                "price_data": {
                    "current_price": current_price,
                    "price_change": price_change,
                    "change_percent": change_percent,
                    "previous_price": technical_indicators["previous_price"]
                },
                "technical_indicators": {
                    "momentum": technical_indicators["momentum_strength"],
                    "trend": technical_indicators["trend_strength"],
                    "support_resistance": technical_indicators["support_resistance"],
                    "volatility": technical_indicators["volatility"]
                }
            },
            "investment_recommendation": investment_advice,
            "risk_assessment": risk_assessment,
            "market_context": market_context
        }
    
    def _analyze_market_context(self, change_percent: float, stock_code: str) -> Dict[str, Any]:
        """市場環境分析"""
        
        # 基於股票代碼和價格變化分析市場環境
        if stock_code == "0700.HK":  # 騰訊
            sector = "科技股"
            market_cap = "大型股"
            
            if change_percent > 5:
                market_sentiment = "樂觀"
                sector_outlook = "科技股受到資金追捧，市場對成長性期待較高"
            elif change_percent < -5:
                market_sentiment = "謹慎"
                sector_outlook = "科技股面臨壓力，投資者對監管和增長前景擔憂"
            else:
                market_sentiment = "中性"
                sector_outlook = "科技股表現平穩，市場處於觀望狀態"
        else:
            sector = "港股"
            market_cap = "未知"
            market_sentiment = "中性"
            sector_outlook = "港股市場表現平穩"
        
        return {
            "sector": sector,
            "market_cap": market_cap,
            "market_sentiment": market_sentiment,
            "sector_outlook": sector_outlook,
            "hk_market_factors": [
                "美聯儲利率政策影響",
                "中美關係發展",
                "中國經濟數據表現",
                "港元匯率穩定性"
            ]
        }

def main():
    """主函數 - 分析0700.HK"""
    
    # 創建分析器實例
    analyzer = HKStockTechnicalAnalyzer()
    
    # 股票數據
    stock_data = {
        "stock_code": "0700.HK",
        "current_price": 644.0,
        "price_change": 57.00,
        "change_percent": 9.71,
        "period_days": 30
    }
    
    print("=== 港股技術分析AI代理 ===")
    print(f"正在分析股票: {stock_data['stock_code']}")
    print(f"當前價格: HK${stock_data['current_price']}")
    print(f"價格變化: +{stock_data['price_change']} (+{stock_data['change_percent']}%)")
    print(f"分析期間: {stock_data['period_days']}個交易日")
    print("\n" + "="*50 + "\n")
    
    # 執行完整分析
    analysis_result = analyzer.analyze_stock(
        stock_data["stock_code"],
        stock_data["current_price"],
        stock_data["price_change"],
        stock_data["change_percent"],
        stock_data["period_days"]
    )
    
    # 輸出JSON格式結果
    json_result = json.dumps(analysis_result, ensure_ascii=False, indent=2)
    print("分析結果 (JSON格式):")
    print(json_result)
    
    # 保存結果到文件
    with open('/workspace/hk_stock_analysis_result.json', 'w', encoding='utf-8') as f:
        f.write(json_result)
    
    print(f"\n分析結果已保存至: /workspace/hk_stock_analysis_result.json")
    
    return analysis_result

if __name__ == "__main__":
    result = main()