#!/usr/bin/env python3
"""
港股量化分析AI代理 - Sentiment分析專用工具（獨立版本）
專門針對港股市場進行sentiment分析、風險評估和投資建議
無需外部依賴庫
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

class HKStockSentimentAnalyzer:
    """港股Sentiment分析代理"""
    
    def __init__(self):
        self.stock_code = None
        self.current_price = None
        self.price_change = None
        self.change_percentage = None
        self.analysis_period = None
        
    def load_stock_data(self, stock_code: str, current_price: float, 
                       price_change: float, change_percentage: float, 
                       period_days: int = 30):
        """載入股票基本數據"""
        self.stock_code = stock_code
        self.current_price = current_price
        self.price_change = price_change
        self.change_percentage = change_percentage
        self.analysis_period = period_days
        
    def get_stock_info(self) -> Dict[str, Any]:
        """獲取股票基本信息"""
        stock_info = {
            "0700.HK": {
                "name": "騰訊控股",
                "name_en": "Tencent Holdings Ltd",
                "sector": "科技股",
                "market_cap_tier": "大型股",
                "industry": "互聯網軟件與服務",
                "hsi_component": True,
                "trading_currency": "HKD"
            }
        }
        return stock_info.get(self.stock_code, {})
    
    def _calculate_mean(self, values: List[float]) -> float:
        """計算平均值"""
        return sum(values) / len(values) if values else 0
    
    def _calculate_std(self, values: List[float]) -> float:
        """計算標準差"""
        if len(values) < 2:
            return 0
        mean = self._calculate_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
        
    def calculate_technical_indicators(self) -> Dict[str, Any]:
        """計算技術指標（基於價格變化模擬）"""
        # 基於當前價格變化計算技術指標
        base_price = self.current_price - self.price_change
        
        # 模擬30日價格數據（基於實際變化）
        random.seed(42)  # 確保結果一致性
        daily_returns = []
        for i in range(self.analysis_period):
            if i == self.analysis_period - 1:
                # 最後一日為實際變化
                daily_returns.append(self.change_percentage / 100)
            else:
                # 模擬正態分布的日收益率
                u1 = random.random()
                u2 = random.random()
                z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
                daily_returns.append(0.002 + 0.03 * z)
        
        prices = [base_price]
        for ret in daily_returns:
            prices.append(prices[-1] * (1 + ret))
            
        prices = prices[1:]  # 移除初始價格
        
        # 計算技術指標
        sma_5 = self._calculate_mean(prices[-5:]) if len(prices) >= 5 else self.current_price
        sma_20 = self._calculate_mean(prices[-20:]) if len(prices) >= 20 else self.current_price
        
        # RSI計算
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
                
        avg_gain = self._calculate_mean(gains[-14:]) if len(gains) >= 14 else self._calculate_mean(gains)
        avg_loss = self._calculate_mean(losses[-14:]) if len(losses) >= 14 else self._calculate_mean(losses)
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # 波動率
        volatility = self._calculate_std(daily_returns) * math.sqrt(252) * 100
        
        return {
            "sma_5": round(sma_5, 2),
            "sma_20": round(sma_20, 2),
            "rsi": round(rsi, 2),
            "volatility_annualized": round(volatility, 2),
            "price_momentum": "強勢" if self.change_percentage > 5 else "中性" if self.change_percentage > -2 else "弱勢"
        }
    
    def analyze_sentiment(self) -> Dict[str, Any]:
        """Sentiment分析"""
        tech_indicators = self.calculate_technical_indicators()
        
        # Sentiment評分計算
        sentiment_score = 0
        sentiment_factors = []
        
        # 價格變化sentiment
        if self.change_percentage > 8:
            sentiment_score += 30
            sentiment_factors.append("大幅上漲帶來強烈正面情緒")
        elif self.change_percentage > 3:
            sentiment_score += 15
            sentiment_factors.append("溫和上漲提升市場信心")
        elif self.change_percentage > -2:
            sentiment_score += 5
            sentiment_factors.append("價格穩定維持中性情緒")
        else:
            sentiment_score -= 15
            sentiment_factors.append("下跌壓抑市場情緒")
            
        # RSI sentiment
        if tech_indicators["rsi"] > 70:
            sentiment_score += 10
            sentiment_factors.append("RSI顯示強勢但接近超買")
        elif tech_indicators["rsi"] > 50:
            sentiment_score += 15
            sentiment_factors.append("RSI處於健康上升趨勢")
        elif tech_indicators["rsi"] > 30:
            sentiment_score += 5
            sentiment_factors.append("RSI顯示中性偏弱")
        else:
            sentiment_score -= 10
            sentiment_factors.append("RSI顯示超賣狀態")
            
        # 波動率sentiment
        if tech_indicators["volatility_annualized"] > 40:
            sentiment_score -= 5
            sentiment_factors.append("高波動率增加市場不確定性")
        elif tech_indicators["volatility_annualized"] < 25:
            sentiment_score += 10
            sentiment_factors.append("低波動率顯示市場穩定")
        else:
            sentiment_score += 5
            sentiment_factors.append("波動率處於正常範圍")
            
        # 行業sentiment（騰訊特定）
        if self.stock_code == "0700.HK":
            sentiment_score += 10
            sentiment_factors.append("科技龍頭地位提供長期支撐")
            
        # 確定sentiment等級
        if sentiment_score >= 50:
            sentiment_level = "極度樂觀"
            sentiment_color = "深綠"
        elif sentiment_score >= 30:
            sentiment_level = "樂觀"
            sentiment_color = "綠"
        elif sentiment_score >= 10:
            sentiment_level = "偏樂觀"
            sentiment_color = "淺綠"
        elif sentiment_score >= -10:
            sentiment_level = "中性"
            sentiment_color = "黃"
        elif sentiment_score >= -30:
            sentiment_level = "偏悲觀"
            sentiment_color = "橙"
        else:
            sentiment_level = "悲觀"
            sentiment_color = "紅"
            
        return {
            "sentiment_score": sentiment_score,
            "sentiment_level": sentiment_level,
            "sentiment_color": sentiment_color,
            "contributing_factors": sentiment_factors,
            "confidence_level": "高" if abs(self.change_percentage) > 5 else "中等"
        }
    
    def assess_risk(self) -> Dict[str, Any]:
        """風險評估"""
        tech_indicators = self.calculate_technical_indicators()
        
        risk_factors = []
        risk_score = 0
        
        # 價格風險
        if abs(self.change_percentage) > 10:
            risk_score += 25
            risk_factors.append("單日大幅波動增加短期風險")
        elif abs(self.change_percentage) > 5:
            risk_score += 15
            risk_factors.append("中等幅度波動需要關注")
        else:
            risk_score += 5
            risk_factors.append("價格波動在正常範圍")
            
        # 技術風險
        if tech_indicators["rsi"] > 75:
            risk_score += 20
            risk_factors.append("RSI超買警示潛在回調風險")
        elif tech_indicators["rsi"] < 25:
            risk_score += 15
            risk_factors.append("RSI超賣但存在進一步下跌風險")
            
        # 波動率風險
        if tech_indicators["volatility_annualized"] > 45:
            risk_score += 20
            risk_factors.append("高波動率增加投資不確定性")
        elif tech_indicators["volatility_annualized"] > 35:
            risk_score += 10
            risk_factors.append("波動率偏高需要謹慎")
            
        # 市場環境風險（港股特有）
        risk_score += 10
        risk_factors.append("港股受外圍市場影響較大")
        
        # 行業風險（科技股）
        if self.stock_code == "0700.HK":
            risk_score += 15
            risk_factors.append("科技股受監管政策影響")
            
        # 確定風險等級
        if risk_score >= 70:
            risk_level = "極高風險"
        elif risk_score >= 50:
            risk_level = "高風險"
        elif risk_score >= 30:
            risk_level = "中等風險"
        elif risk_score >= 15:
            risk_level = "低風險"
        else:
            risk_level = "極低風險"
            
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "max_position_size": "5%" if risk_score >= 70 else "10%" if risk_score >= 50 else "15%" if risk_score >= 30 else "20%",
            "stop_loss_suggestion": f"{self.current_price * 0.92:.1f}" if risk_score >= 50 else f"{self.current_price * 0.90:.1f}"
        }
    
    def generate_investment_recommendation(self) -> Dict[str, Any]:
        """生成投資建議"""
        sentiment = self.analyze_sentiment()
        risk = self.assess_risk()
        tech_indicators = self.calculate_technical_indicators()
        
        # 綜合評分
        total_score = sentiment["sentiment_score"] - (risk["risk_score"] * 0.5)
        
        # 投資建議
        if total_score >= 30 and self.change_percentage > 0:
            recommendation = "強烈買入"
            action_color = "深綠"
            reasoning = "強勢上漲配合正面sentiment，建議積極建倉"
        elif total_score >= 15:
            recommendation = "買入"
            action_color = "綠"
            reasoning = "技術面和sentiment均偏正面，適合逢低買入"
        elif total_score >= 0:
            recommendation = "持有"
            action_color = "黃"
            reasoning = "中性偏正面，持有觀望或小幅加倉"
        elif total_score >= -15:
            recommendation = "減持"
            action_color = "橙"
            reasoning = "sentiment轉弱，建議減少倉位"
        else:
            recommendation = "賣出"
            action_color = "紅"
            reasoning = "負面sentiment配合高風險，建議止損離場"
            
        # 目標價位
        if self.change_percentage > 5:
            target_price = self.current_price * 1.08  # 上漲趨勢目標
            support_price = self.current_price * 0.95
        else:
            target_price = self.current_price * 1.05
            support_price = self.current_price * 0.92
            
        return {
            "recommendation": recommendation,
            "action_color": action_color,
            "reasoning": reasoning,
            "total_score": round(total_score, 1),
            "target_price": round(target_price, 1),
            "support_price": round(support_price, 1),
            "time_horizon": "1-3個月",
            "position_sizing": risk["max_position_size"]
        }
    
    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """生成綜合分析報告"""
        stock_info = self.get_stock_info()
        tech_indicators = self.calculate_technical_indicators()
        sentiment = self.analyze_sentiment()
        risk = self.assess_risk()
        recommendation = self.generate_investment_recommendation()
        
        return {
            "分析時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "股票基本信息": {
                "股票代碼": self.stock_code,
                "公司名稱": stock_info.get("name", "未知"),
                "英文名稱": stock_info.get("name_en", "Unknown"),
                "所屬行業": stock_info.get("industry", "未分類"),
                "市場類別": stock_info.get("market_cap_tier", "未知"),
                "是否恒指成分股": stock_info.get("hsi_component", False)
            },
            "當前市場數據": {
                "當前價格": f"HK${self.current_price}",
                "價格變化": f"+HK${self.price_change}" if self.price_change > 0 else f"HK${self.price_change}",
                "漲跌幅": f"+{self.change_percentage}%" if self.change_percentage > 0 else f"{self.change_percentage}%",
                "分析週期": f"{self.analysis_period}個交易日"
            },
            "技術指標分析": {
                "5日均線": f"HK${tech_indicators['sma_5']}",
                "20日均線": f"HK${tech_indicators['sma_20']}",
                "相對強弱指標RSI": tech_indicators['rsi'],
                "年化波動率": f"{tech_indicators['volatility_annualized']}%",
                "價格動量": tech_indicators['price_momentum']
            },
            "Sentiment分析": {
                "Sentiment評分": f"{sentiment['sentiment_score']}/100",
                "Sentiment等級": sentiment['sentiment_level'],
                "信心水平": sentiment['confidence_level'],
                "主要影響因素": sentiment['contributing_factors']
            },
            "風險評估": {
                "風險評分": f"{risk['risk_score']}/100",
                "風險等級": risk['risk_level'],
                "主要風險因素": risk['risk_factors'],
                "建議倉位上限": risk['max_position_size'],
                "建議止損價位": f"HK${risk['stop_loss_suggestion']}"
            },
            "投資建議": {
                "操作建議": recommendation['recommendation'],
                "建議理由": recommendation['reasoning'],
                "綜合評分": recommendation['total_score'],
                "目標價位": f"HK${recommendation['target_price']}",
                "支撐價位": f"HK${recommendation['support_price']}",
                "投資時間範圍": recommendation['time_horizon'],
                "建議倉位配置": recommendation['position_sizing']
            },
            "專業分析總結": {
                "技術面分析": f"當前價格{self.current_price}港元，相對於基準價格上漲{self.change_percentage}%，顯示{tech_indicators['price_momentum']}。RSI指標為{tech_indicators['rsi']}，處於{'超買' if tech_indicators['rsi'] > 70 else '超賣' if tech_indicators['rsi'] < 30 else '正常'}區間。",
                "市場情緒分析": f"基於價格動量、技術指標和市場環境的綜合分析，當前市場情緒為{sentiment['sentiment_level']}（評分：{sentiment['sentiment_score']}/100），主要受到{len(sentiment['contributing_factors'])}個因素影響。",
                "風險控制建議": f"當前風險等級為{risk['risk_level']}（評分：{risk['risk_score']}/100），建議最大倉位不超過{risk['max_position_size']}，止損價位設定在{risk['stop_loss_suggestion']}港元。"
            },
            "重要提醒": [
                "本分析僅供參考，不構成投資建議",
                "港股市場波動較大，請控制風險",
                "建議結合基本面分析做出投資決策",
                "請根據個人風險承受能力調整倉位",
                "科技股受政策影響較大，需密切關注監管動態"
            ]
        }

def main():
    """主函數 - 分析0700.HK"""
    print("=" * 60)
    print("港股量化分析AI代理 - Sentiment分析報告")
    print("=" * 60)
    
    analyzer = HKStockSentimentAnalyzer()
    
    # 載入實際數據
    analyzer.load_stock_data(
        stock_code="0700.HK",
        current_price=644.0,
        price_change=57.00,
        change_percentage=9.71,
        period_days=30
    )
    
    # 生成綜合分析
    analysis_result = analyzer.generate_comprehensive_analysis()
    
    # 輸出JSON格式結果
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return analysis_result

if __name__ == "__main__":
    main()