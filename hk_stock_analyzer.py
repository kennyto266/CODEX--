#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化分析工具 - 專門針對0700.HK騰訊控股的分析
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import math

class HKStockAnalyzer:
    """港股量化分析器"""
    
    def __init__(self):
        self.stock_code = "0700.HK"
        self.company_name = "騰訊控股"
        
    def calculate_technical_indicators(self, current_price: float, price_change: float, trading_days: int) -> Dict[str, Any]:
        """計算技術指標"""
        previous_price = current_price - price_change
        price_change_percent = (price_change / previous_price) * 100
        
        # 計算波動率（基於價格變化）
        volatility = abs(price_change_percent) / math.sqrt(trading_days)
        
        # RSI估算（基於價格變化）
        if price_change > 0:
            rsi_estimate = 70 + (price_change_percent - 5) * 2  # 上漲時RSI偏高
        else:
            rsi_estimate = 30 + (price_change_percent + 5) * 2  # 下跌時RSI偏低
        
        rsi_estimate = max(0, min(100, rsi_estimate))
        
        return {
            "前期價格": round(previous_price, 2),
            "漲跌幅": f"{price_change_percent:.2f}%",
            "30日波動率": f"{volatility:.2f}%",
            "RSI估算": round(rsi_estimate, 1),
            "價格動能": "強勁上升" if price_change_percent > 5 else "溫和上升" if price_change_percent > 0 else "下跌"
        }
    
    def assess_market_sentiment(self, price_change_percent: float) -> Dict[str, str]:
        """評估市場情緒"""
        if price_change_percent > 8:
            sentiment = "極度樂觀"
            market_phase = "強勢突破"
        elif price_change_percent > 5:
            sentiment = "樂觀"
            market_phase = "上升趨勢"
        elif price_change_percent > 2:
            sentiment = "中性偏多"
            market_phase = "溫和上漲"
        elif price_change_percent > -2:
            sentiment = "中性"
            market_phase = "橫盤整理"
        elif price_change_percent > -5:
            sentiment = "中性偏空"
            market_phase = "溫和下跌"
        else:
            sentiment = "悲觀"
            market_phase = "下跌趨勢"
            
        return {
            "市場情緒": sentiment,
            "市場階段": market_phase
        }
    
    def generate_investment_recommendation(self, price_change_percent: float, current_price: float) -> Dict[str, Any]:
        """生成投資建議"""
        # 基於價格表現和市場分析
        if price_change_percent > 8:
            recommendation = "持有/適量減持"
            confidence = "中等"
            reason = "短期漲幅較大，建議獲利了結部分持倉"
        elif price_change_percent > 5:
            recommendation = "買入/持有"
            confidence = "高"
            reason = "強勢上漲，基本面支撐良好"
        elif price_change_percent > 2:
            recommendation = "買入"
            confidence = "高"
            reason = "溫和上漲，適合建倉"
        else:
            recommendation = "觀望"
            confidence = "低"
            reason = "趨勢不明，等待更好時機"
        
        # 目標價位計算
        target_price_high = current_price * 1.15  # 上漲15%
        target_price_low = current_price * 0.90   # 下跌10%
        
        return {
            "投資建議": recommendation,
            "信心度": confidence,
            "建議理由": reason,
            "目標價位": {
                "上檔目標": round(target_price_high, 2),
                "下檔支撐": round(target_price_low, 2)
            },
            "建議持倉比例": "10-15%" if recommendation == "買入" else "5-10%" if recommendation == "持有" else "0-5%"
        }
    
    def assess_risks(self, price_change_percent: float, volatility: float) -> Dict[str, Any]:
        """風險評估"""
        # 技術風險
        if price_change_percent > 10:
            technical_risk = "高"
            technical_desc = "短期漲幅過大，存在回調風險"
        elif price_change_percent > 5:
            technical_risk = "中"
            technical_desc = "漲幅合理，但需關注獲利回吐壓力"
        else:
            technical_risk = "低"
            technical_desc = "價格變動溫和，技術風險較低"
        
        # 市場風險
        market_risks = [
            "港股市場受外圍因素影響較大",
            "科技股板塊波動性較高",
            "中美關係變化可能影響估值"
        ]
        
        # 公司特定風險
        company_risks = [
            "監管政策變化風險",
            "遊戲業務增長放緩風險",
            "競爭加劇影響市佔率",
            "匯率波動影響海外收入"
        ]
        
        return {
            "技術風險": {
                "風險等級": technical_risk,
                "風險描述": technical_desc
            },
            "市場風險": market_risks,
            "公司風險": company_risks,
            "整體風險評級": "中等" if technical_risk == "中" else technical_risk,
            "風險控制建議": [
                "設置止損位於590港元附近",
                "分批建倉降低成本風險",
                "關注成交量變化確認趨勢",
                "定期檢視基本面變化"
            ]
        }
    
    def analyze_stock(self, current_price: float, price_change: float, trading_days: int) -> Dict[str, Any]:
        """主要分析函數"""
        # 計算基礎指標
        previous_price = current_price - price_change
        price_change_percent = (price_change / previous_price) * 100
        
        # 技術分析
        technical_indicators = self.calculate_technical_indicators(current_price, price_change, trading_days)
        
        # 市場情緒
        market_sentiment = self.assess_market_sentiment(price_change_percent)
        
        # 投資建議
        investment_recommendation = self.generate_investment_recommendation(price_change_percent, current_price)
        
        # 風險評估
        volatility = abs(price_change_percent) / math.sqrt(trading_days)
        risk_assessment = self.assess_risks(price_change_percent, volatility)
        
        # 綜合分析結果
        analysis_result = {
            "股票資訊": {
                "股票代碼": self.stock_code,
                "公司名稱": self.company_name,
                "當前價格": current_price,
                "價格變化": price_change,
                "漲跌幅": f"{price_change_percent:.2f}%",
                "分析期間": f"{trading_days}個交易日",
                "分析時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "專業分析": {
                "技術指標": technical_indicators,
                "市場情緒": market_sentiment,
                "基本面摘要": {
                    "業務亮點": [
                        "遊戲業務收入增長15%，新遊戲貢獻顯著",
                        "廣告業務增長19%，視頻號廣告表現亮眼",
                        "金融科技業務維持雙位數增長",
                        "AI技術全面應用提升效率"
                    ],
                    "財務表現": {
                        "毛利率": "55.1%（同比提升1.8個百分點）",
                        "收入結構": "多元化業務組合，抗風險能力強"
                    }
                }
            },
            "投資建議": investment_recommendation,
            "風險評估": risk_assessment,
            "市場展望": {
                "短期展望": "技術面強勢，基本面支撐良好，短期有望維持上升趨勢",
                "中期展望": "受惠於AI技術應用和業務多元化，中期成長前景樂觀",
                "關鍵監控指標": [
                    "遊戲業務月活躍用戶數",
                    "廣告業務收入增長率",
                    "AI相關業務進展",
                    "監管政策變化"
                ]
            }
        }
        
        return analysis_result

def main():
    """主函數"""
    # 初始化分析器
    analyzer = HKStockAnalyzer()
    
    # 分析數據
    current_price = 644.0
    price_change = 57.00
    trading_days = 30
    
    # 執行分析
    result = analyzer.analyze_stock(current_price, price_change, trading_days)
    
    # 輸出JSON格式結果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()