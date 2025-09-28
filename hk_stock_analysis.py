#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化技術分析工具
專門針對港股市場的技術分析代理
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Any

class HKStockTechnicalAnalyzer:
    """港股技術分析器"""
    
    def __init__(self):
        self.analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_technical_indicators(self, current_price: float, price_change: float, 
                                     change_percent: float, period_days: int) -> Dict[str, Any]:
        """計算技術指標"""
        
        # 計算前期價格
        previous_price = current_price - price_change
        
        # 波動率分析（基於價格變化幅度）
        volatility = abs(change_percent)
        
        # 動量指標
        momentum_strength = self._calculate_momentum_strength(change_percent)
        
        # 趨勢強度
        trend_strength = self._calculate_trend_strength(change_percent, period_days)
        
        # RSI估算（基於價格變化）
        rsi_estimate = self._estimate_rsi(change_percent)
        
        return {
            "previous_price": round(previous_price, 2),
            "volatility": round(volatility, 2),
            "momentum_strength": momentum_strength,
            "trend_strength": trend_strength,
            "rsi_estimate": rsi_estimate,
            "price_position": self._analyze_price_position(change_percent)
        }
    
    def _calculate_momentum_strength(self, change_percent: float) -> str:
        """計算動量強度"""
        if abs(change_percent) >= 10:
            return "極強"
        elif abs(change_percent) >= 7:
            return "強"
        elif abs(change_percent) >= 4:
            return "中等"
        elif abs(change_percent) >= 2:
            return "弱"
        else:
            return "極弱"
    
    def _calculate_trend_strength(self, change_percent: float, period_days: int) -> str:
        """計算趋勢強度"""
        daily_avg_change = change_percent / period_days
        
        if abs(daily_avg_change) >= 0.5:
            return "強勢趨勢"
        elif abs(daily_avg_change) >= 0.3:
            return "中等趨勢"
        else:
            return "弱勢趨勢"
    
    def _estimate_rsi(self, change_percent: float) -> int:
        """估算RSI值"""
        # 基於價格變化估算RSI
        if change_percent > 0:
            # 上漲時RSI偏高
            base_rsi = 50 + min(change_percent * 2, 30)
        else:
            # 下跌時RSI偏低
            base_rsi = 50 + max(change_percent * 2, -30)
        
        return int(max(0, min(100, base_rsi)))
    
    def _analyze_price_position(self, change_percent: float) -> str:
        """分析價格位置"""
        if change_percent >= 8:
            return "突破上漲"
        elif change_percent >= 3:
            return "上漲趨勢"
        elif change_percent >= -3:
            return "橫盤整理"
        elif change_percent >= -8:
            return "下跌趨勢"
        else:
            return "深度回調"
    
    def generate_professional_analysis(self, stock_code: str, current_price: float, 
                                     price_change: float, change_percent: float, 
                                     period_days: int) -> Dict[str, Any]:
        """生成專業分析報告"""
        
        # 計算技術指標
        technical_data = self.calculate_technical_indicators(
            current_price, price_change, change_percent, period_days
        )
        
        # 專業分析
        professional_analysis = {
            "技術面分析": self._technical_analysis(change_percent, technical_data),
            "市場情緒": self._market_sentiment_analysis(change_percent),
            "支撐阻力位": self._support_resistance_analysis(current_price, change_percent),
            "成交量分析": self._volume_analysis(change_percent),
            "趨勢判斷": self._trend_analysis(change_percent, period_days)
        }
        
        # 投資建議
        investment_advice = self._generate_investment_advice(change_percent, technical_data)
        
        # 風險評估
        risk_assessment = self._generate_risk_assessment(change_percent, technical_data)
        
        return {
            "股票代碼": stock_code,
            "分析時間": self.analysis_date,
            "當前數據": {
                "價格": current_price,
                "變化": f"{price_change:+.2f}",
                "變化百分比": f"{change_percent:+.2f}%",
                "分析週期": f"{period_days}個交易日"
            },
            "技術指標": technical_data,
            "專業分析": professional_analysis,
            "投資建議": investment_advice,
            "風險評估": risk_assessment
        }
    
    def _technical_analysis(self, change_percent: float, technical_data: Dict) -> Dict[str, str]:
        """技術面分析"""
        analysis = {}
        
        if change_percent > 8:
            analysis["短期趨勢"] = "強勢突破，動能充足，技術面非常樂觀"
            analysis["技術形態"] = "突破性上漲，可能形成新的上升趨勢"
        elif change_percent > 3:
            analysis["短期趨勢"] = "上漲趨勢確立，技術面偏多"
            analysis["技術形態"] = "健康上漲，技術面支持繼續上行"
        elif change_percent > -3:
            analysis["短期趨勢"] = "橫盤整理，方向待定"
            analysis["技術形態"] = "震盪格局，需要觀察突破方向"
        else:
            analysis["短期趨勢"] = "下跌趨勢，技術面偏弱"
            analysis["技術形態"] = "調整壓力較大，需要關注支撐位"
        
        analysis["動量指標"] = f"動量強度為{technical_data['momentum_strength']}"
        analysis["相對強弱"] = f"RSI估值約{technical_data['rsi_estimate']}"
        
        return analysis
    
    def _market_sentiment_analysis(self, change_percent: float) -> Dict[str, str]:
        """市場情緒分析"""
        if change_percent > 8:
            return {
                "整體情緒": "極度樂觀",
                "投資者行為": "積極買入，追漲情緒濃厚",
                "市場氛圍": "多頭氣氛濃厚，信心充足"
            }
        elif change_percent > 3:
            return {
                "整體情緒": "樂觀",
                "投資者行為": "買盤活躍，持續看好",
                "市場氛圍": "正面情緒主導"
            }
        elif change_percent > -3:
            return {
                "整體情緒": "中性",
                "投資者行為": "觀望為主，等待方向明確",
                "市場氛圍": "謹慎樂觀"
            }
        else:
            return {
                "整體情緒": "悲觀",
                "投資者行為": "賣壓較重，信心不足",
                "市場氛圍": "謹慎情緒升溫"
            }
    
    def _support_resistance_analysis(self, current_price: float, change_percent: float) -> Dict[str, float]:
        """支撐阻力位分析"""
        previous_price = current_price - (current_price * change_percent / 100)
        
        if change_percent > 0:
            # 上漲時
            support_1 = round(previous_price * 0.95, 1)  # 5%回調支撐
            support_2 = round(previous_price * 0.90, 1)  # 10%回調支撐
            resistance_1 = round(current_price * 1.05, 1)  # 5%阻力
            resistance_2 = round(current_price * 1.10, 1)  # 10%阻力
        else:
            # 下跌時
            support_1 = round(current_price * 0.95, 1)
            support_2 = round(current_price * 0.90, 1)
            resistance_1 = round(previous_price * 0.98, 1)
            resistance_2 = round(previous_price * 1.02, 1)
        
        return {
            "第一支撐位": support_1,
            "第二支撐位": support_2,
            "第一阻力位": resistance_1,
            "第二阻力位": resistance_2
        }
    
    def _volume_analysis(self, change_percent: float) -> Dict[str, str]:
        """成交量分析（基於價格變化推斷）"""
        if abs(change_percent) > 8:
            return {
                "成交量水平": "放量",
                "量價關係": "量價配合良好" if change_percent > 0 else "放量下跌",
                "市場參與度": "高度活躍"
            }
        elif abs(change_percent) > 3:
            return {
                "成交量水平": "溫和放量",
                "量價關係": "量價關係健康",
                "市場參與度": "活躍"
            }
        else:
            return {
                "成交量水平": "成交平淡",
                "量價關係": "縮量整理",
                "市場參與度": "一般"
            }
    
    def _trend_analysis(self, change_percent: float, period_days: int) -> Dict[str, str]:
        """趨勢分析"""
        daily_avg = change_percent / period_days
        
        analysis = {
            "主要趨勢": "",
            "趨勢強度": "",
            "持續性預期": ""
        }
        
        if change_percent > 8:
            analysis["主要趨勢"] = "強勢上升趨勢"
            analysis["趨勢強度"] = "非常強"
            analysis["持續性預期"] = "短期內有望延續"
        elif change_percent > 3:
            analysis["主要趨勢"] = "上升趨勢"
            analysis["趨勢強度"] = "較強"
            analysis["持續性預期"] = "有一定持續性"
        elif change_percent > -3:
            analysis["主要趨勢"] = "橫盤整理"
            analysis["趨勢強度"] = "中性"
            analysis["持續性預期"] = "等待突破方向"
        else:
            analysis["主要趨勢"] = "下降趨勢"
            analysis["趨勢強度"] = "較弱"
            analysis["持續性預期"] = "需要觀察反彈信號"
        
        return analysis
    
    def _generate_investment_advice(self, change_percent: float, technical_data: Dict) -> Dict[str, Any]:
        """生成投資建議"""
        advice = {
            "操作建議": "",
            "建議倉位": "",
            "進場時機": "",
            "止盈止損": {},
            "投資週期": ""
        }
        
        if change_percent > 8:
            advice["操作建議"] = "積極看多，但需要注意短期獲利回吐風險"
            advice["建議倉位"] = "中等倉位（50-70%）"
            advice["進場時機"] = "回調至支撐位附近可考慮分批建倉"
            advice["止盈止損"] = {
                "止盈": "階段性獲利了結，分批減倉",
                "止損": f"跌破{technical_data['previous_price']}考慮止損"
            }
            advice["投資週期"] = "短中期（1-3個月）"
        elif change_percent > 3:
            advice["操作建議"] = "看多為主，適度參與"
            advice["建議倉位"] = "中等倉位（40-60%）"
            advice["進場時機"] = "逢低分批建倉"
            advice["止盈止損"] = {
                "止盈": "達到目標價位分批獲利",
                "止損": "跌破重要支撐位止損"
            }
            advice["投資週期"] = "中期（2-6個月）"
        elif change_percent > -3:
            advice["操作建議"] = "觀望為主，等待明確信號"
            advice["建議倉位"] = "輕倉位（20-40%）"
            advice["進場時機"] = "等待突破確認後再行動"
            advice["止盈止損"] = {
                "止盈": "小幅獲利即可考慮獲利了結",
                "止損": "嚴格執行止損紀律"
            }
            advice["投資週期"] = "短期（1個月內）"
        else:
            advice["操作建議"] = "謹慎為主，等待反彈機會"
            advice["建議倉位"] = "輕倉或空倉（0-30%）"
            advice["進場時機"] = "等待明確的反彈信號"
            advice["止盈止損"] = {
                "止盈": "反彈至阻力位附近減倉",
                "止損": "嚴格控制風險"
            }
            advice["投資週期"] = "等待時機"
        
        return advice
    
    def _generate_risk_assessment(self, change_percent: float, technical_data: Dict) -> Dict[str, Any]:
        """生成風險評估"""
        risk = {
            "整體風險等級": "",
            "主要風險因素": [],
            "風險控制建議": [],
            "波動性評估": "",
            "流動性風險": ""
        }
        
        volatility = abs(change_percent)
        
        if volatility > 10:
            risk["整體風險等級"] = "高風險"
            risk["波動性評估"] = "極高波動"
            risk["主要風險因素"] = [
                "價格波動劇烈",
                "市場情緒極端",
                "獲利回吐風險較高",
                "技術面可能出現反轉"
            ]
        elif volatility > 5:
            risk["整體風險等級"] = "中高風險"
            risk["波動性評估"] = "高波動"
            risk["主要風險因素"] = [
                "價格波動較大",
                "短期調整風險",
                "市場情緒變化快"
            ]
        elif volatility > 2:
            risk["整體風險等級"] = "中等風險"
            risk["波動性評估"] = "中等波動"
            risk["主要風險因素"] = [
                "正常市場波動",
                "需關注趨勢延續性"
            ]
        else:
            risk["整體風險等級"] = "低風險"
            risk["波動性評估"] = "低波動"
            risk["主要風險因素"] = [
                "市場相對平穩",
                "缺乏明確方向"
            ]
        
        # 風險控制建議
        risk["風險控制建議"] = [
            "嚴格執行止損紀律",
            "分批建倉降低風險",
            "關注市場重要消息",
            "控制倉位大小",
            "定期檢視投資組合"
        ]
        
        risk["流動性風險"] = "港股流動性良好，騰訊為藍籌股，流動性風險較低"
        
        return risk

def main():
    """主函數"""
    # 初始化分析器
    analyzer = HKStockTechnicalAnalyzer()
    
    # 輸入數據
    stock_data = {
        "stock_code": "0700.HK",
        "current_price": 644.0,
        "price_change": 57.00,
        "change_percent": 9.71,
        "period_days": 30
    }
    
    # 生成分析報告
    analysis_result = analyzer.generate_professional_analysis(
        stock_data["stock_code"],
        stock_data["current_price"],
        stock_data["price_change"],
        stock_data["change_percent"],
        stock_data["period_days"]
    )
    
    # 輸出JSON格式結果
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return analysis_result

if __name__ == "__main__":
    main()