#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股 (0700.HK) Sentiment Analysis
專業量化分析報告生成器
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any
import math

class TencentSentimentAnalyzer:
    def __init__(self, historical_data: List[Dict], current_price: float):
        """
        初始化分析器
        
        Args:
            historical_data: 歷史交易數據
            current_price: 當前價格
        """
        self.historical_data = historical_data
        self.current_price = current_price
        self.df = self._prepare_dataframe()
        
    def _prepare_dataframe(self) -> pd.DataFrame:
        """準備數據框架"""
        df = pd.DataFrame(self.historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # 計算技術指標
        df['daily_return'] = df['close'].pct_change()
        df['price_range'] = df['high'] - df['low']
        df['price_range_pct'] = (df['high'] - df['low']) / df['close'] * 100
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['price_ma5'] = df['close'].rolling(window=5).mean()
        df['price_ma10'] = df['close'].rolling(window=10).mean()
        
        return df
    
    def analyze_price_trend(self) -> Dict[str, Any]:
        """分析價格趋势"""
        recent_5_days = self.df.tail(5)
        recent_10_days = self.df.tail(10)
        
        # 價格變化分析
        price_change_30d = (self.current_price - self.df.iloc[0]['close']) / self.df.iloc[0]['close'] * 100
        price_change_5d = (self.current_price - recent_5_days.iloc[0]['close']) / recent_5_days.iloc[0]['close'] * 100
        
        # 趨勢強度
        ma5_trend = "上升" if recent_5_days['close'].iloc[-1] > recent_5_days['price_ma5'].iloc[-1] else "下降"
        ma10_trend = "上升" if recent_10_days['close'].iloc[-1] > recent_10_days['price_ma10'].iloc[-1] else "下降"
        
        # 支撐和阻力位
        support_level = self.df['low'].min()
        resistance_level = self.df['high'].max()
        
        return {
            "price_change_30d": round(price_change_30d, 2),
            "price_change_5d": round(price_change_5d, 2),
            "ma5_trend": ma5_trend,
            "ma10_trend": ma10_trend,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "trend_strength": "強勢" if price_change_5d > 2 else "弱勢" if price_change_5d < -2 else "中性"
        }
    
    def analyze_volume_sentiment(self) -> Dict[str, Any]:
        """分析成交量情緒"""
        avg_volume = self.df['volume'].mean()
        recent_volume = self.df.tail(5)['volume'].mean()
        volume_trend = (recent_volume - avg_volume) / avg_volume * 100
        
        # 價量關係分析
        price_volume_correlation = self.df['daily_return'].corr(self.df['volume'])
        
        # 異常成交量天數
        high_volume_days = len(self.df[self.df['volume'] > avg_volume * 1.5])
        
        return {
            "average_volume": int(avg_volume),
            "recent_volume_trend": round(volume_trend, 2),
            "price_volume_correlation": round(price_volume_correlation, 3),
            "high_volume_days": high_volume_days,
            "volume_sentiment": "積極" if volume_trend > 10 else "消極" if volume_trend < -10 else "中性"
        }
    
    def calculate_volatility_risk(self) -> Dict[str, Any]:
        """計算波動性和風險指標"""
        daily_returns = self.df['daily_return'].dropna()
        
        # 波動率計算
        volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波動率
        
        # VaR計算 (95%置信區間)
        var_95 = np.percentile(daily_returns, 5) * 100
        
        # 最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # 夏普比率 (假設無風險利率2%)
        risk_free_rate = 0.02
        excess_return = daily_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_return / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
        
        return {
            "annualized_volatility": round(volatility, 2),
            "var_95": round(var_95, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "risk_level": "高" if volatility > 30 else "中" if volatility > 20 else "低"
        }
    
    def sentiment_scoring(self) -> Dict[str, Any]:
        """綜合情緒評分"""
        price_analysis = self.analyze_price_trend()
        volume_analysis = self.analyze_volume_sentiment()
        risk_analysis = self.calculate_volatility_risk()
        
        # 評分邏輯 (0-100)
        price_score = 0
        if price_analysis["price_change_5d"] > 5:
            price_score = 85
        elif price_analysis["price_change_5d"] > 2:
            price_score = 70
        elif price_analysis["price_change_5d"] > -2:
            price_score = 50
        elif price_analysis["price_change_5d"] > -5:
            price_score = 30
        else:
            price_score = 15
            
        # 成交量評分
        volume_score = 50
        if volume_analysis["volume_sentiment"] == "積極":
            volume_score = 75
        elif volume_analysis["volume_sentiment"] == "消極":
            volume_score = 25
            
        # 風險調整評分
        risk_penalty = 0
        if risk_analysis["risk_level"] == "高":
            risk_penalty = 15
        elif risk_analysis["risk_level"] == "中":
            risk_penalty = 5
            
        overall_sentiment_score = max(0, min(100, (price_score + volume_score) / 2 - risk_penalty))
        
        return {
            "price_score": price_score,
            "volume_score": volume_score,
            "risk_penalty": risk_penalty,
            "overall_sentiment_score": round(overall_sentiment_score, 1),
            "sentiment_level": "非常樂觀" if overall_sentiment_score > 80 else 
                            "樂觀" if overall_sentiment_score > 65 else
                            "中性" if overall_sentiment_score > 35 else
                            "悲觀" if overall_sentiment_score > 20 else "非常悲觀"
        }
    
    def generate_investment_advice(self) -> Dict[str, Any]:
        """生成投資建議"""
        sentiment = self.sentiment_scoring()
        price_analysis = self.analyze_price_trend()
        risk_analysis = self.calculate_volatility_risk()
        
        # 投資建議邏輯
        if sentiment["overall_sentiment_score"] > 70:
            action = "買入"
            confidence = "高"
            target_price = self.current_price * 1.08
            stop_loss = self.current_price * 0.95
        elif sentiment["overall_sentiment_score"] > 50:
            action = "持有"
            confidence = "中"
            target_price = self.current_price * 1.05
            stop_loss = self.current_price * 0.97
        else:
            action = "觀望"
            confidence = "低"
            target_price = self.current_price * 1.02
            stop_loss = self.current_price * 0.92
            
        return {
            "recommended_action": action,
            "confidence_level": confidence,
            "target_price": round(target_price, 2),
            "stop_loss_price": round(stop_loss, 2),
            "holding_period": "1-3個月",
            "position_sizing": "建議倉位不超過組合的10-15%"
        }
    
    def expected_return_analysis(self) -> Dict[str, Any]:
        """預期收益分析"""
        daily_returns = self.df['daily_return'].dropna()
        
        # 預期收益計算
        mean_daily_return = daily_returns.mean()
        expected_annual_return = mean_daily_return * 252 * 100
        
        # 概率分析
        positive_days = len(daily_returns[daily_returns > 0])
        total_days = len(daily_returns)
        win_rate = positive_days / total_days * 100
        
        # 收益區間預測
        std_daily = daily_returns.std()
        
        scenarios = {
            "樂觀情境 (75%)": round((mean_daily_return + std_daily) * 252 * 100, 2),
            "基準情境 (50%)": round(expected_annual_return, 2),
            "悲觀情境 (25%)": round((mean_daily_return - std_daily) * 252 * 100, 2)
        }
        
        return {
            "expected_annual_return": round(expected_annual_return, 2),
            "win_rate": round(win_rate, 1),
            "return_scenarios": scenarios,
            "risk_adjusted_return": round(expected_annual_return / (daily_returns.std() * np.sqrt(252) * 100), 3)
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成綜合分析報告"""
        price_trend = self.analyze_price_trend()
        volume_sentiment = self.analyze_volume_sentiment()
        risk_metrics = self.calculate_volatility_risk()
        sentiment_score = self.sentiment_scoring()
        investment_advice = self.generate_investment_advice()
        return_analysis = self.expected_return_analysis()
        
        # 詳細分析過程
        analysis_process = {
            "技術面分析": {
                "價格趨勢": f"30天累計漲幅{price_trend['price_change_30d']}%，5天漲幅{price_trend['price_change_5d']}%",
                "移動平均": f"5日均線{price_trend['ma5_trend']}，10日均線{price_trend['ma10_trend']}",
                "支撐阻力": f"支撐位{price_trend['support_level']}，阻力位{price_trend['resistance_level']}"
            },
            "成交量分析": {
                "成交量趨勢": f"近期成交量較平均水平{volume_sentiment['recent_volume_trend']}%",
                "價量關係": f"價格與成交量相關係數{volume_sentiment['price_volume_correlation']}",
                "市場參與度": volume_sentiment['volume_sentiment']
            },
            "風險評估": {
                "波動率": f"年化波動率{risk_metrics['annualized_volatility']}%",
                "最大回撤": f"{risk_metrics['max_drawdown']}%",
                "風險等級": risk_metrics['risk_level']
            },
            "情緒指標": {
                "綜合評分": f"{sentiment_score['overall_sentiment_score']}/100",
                "情緒水平": sentiment_score['sentiment_level']
            }
        }
        
        return {
            "股票資訊": {
                "股票代碼": "0700.HK",
                "股票名稱": "騰訊控股",
                "當前價格": self.current_price,
                "分析日期": datetime.now().strftime("%Y-%m-%d"),
                "數據期間": "30個交易日"
            },
            "詳細分析過程": analysis_process,
            "投資建議": investment_advice,
            "風險評估": {
                "整體風險等級": risk_metrics['risk_level'],
                "主要風險因素": [
                    "市場波動風險",
                    "科技股估值風險",
                    "監管政策風險",
                    "宏觀經濟風險"
                ],
                "風險指標": {
                    "年化波動率": f"{risk_metrics['annualized_volatility']}%",
                    "95% VaR": f"{risk_metrics['var_95']}%",
                    "最大回撤": f"{risk_metrics['max_drawdown']}%",
                    "夏普比率": risk_metrics['sharpe_ratio']
                }
            },
            "預期收益評估": {
                "預期年化收益率": f"{return_analysis['expected_annual_return']}%",
                "勝率": f"{return_analysis['win_rate']}%",
                "收益情境分析": return_analysis['return_scenarios'],
                "風險調整收益": return_analysis['risk_adjusted_return']
            },
            "sentiment分析總結": {
                "綜合評分": f"{sentiment_score['overall_sentiment_score']}/100",
                "情緒水平": sentiment_score['sentiment_level'],
                "價格動能": price_trend['trend_strength'],
                "成交量情緒": volume_sentiment['volume_sentiment'],
                "建議操作": investment_advice['recommended_action'],
                "信心水平": investment_advice['confidence_level']
            }
        }

def main():
    """主函數"""
    # 歷史數據
    historical_data = [
        {"symbol": "0700.HK", "timestamp": "2025-08-18T00:00:00+00:00", "open": 594.0, "high": 596.0, "low": 587.0, "close": 587.0, "volume": 17590658},
        {"symbol": "0700.HK", "timestamp": "2025-08-19T00:00:00+00:00", "open": 588.0, "high": 597.0, "low": 583.0, "close": 592.5, "volume": 16359474},
        {"symbol": "0700.HK", "timestamp": "2025-08-20T00:00:00+00:00", "open": 589.0, "high": 594.5, "low": 585.5, "close": 590.5, "volume": 15952765},
        {"symbol": "0700.HK", "timestamp": "2025-08-21T00:00:00+00:00", "open": 590.5, "high": 597.0, "low": 589.5, "close": 593.0, "volume": 14290178},
        {"symbol": "0700.HK", "timestamp": "2025-08-22T00:00:00+00:00", "open": 599.0, "high": 606.5, "low": 595.5, "close": 600.0, "volume": 19378950},
        {"symbol": "0700.HK", "timestamp": "2025-08-25T00:00:00+00:00", "open": 608.5, "high": 621.0, "low": 608.0, "close": 614.5, "volume": 25694519},
        {"symbol": "0700.HK", "timestamp": "2025-08-26T00:00:00+00:00", "open": 612.0, "high": 618.0, "low": 609.5, "close": 609.5, "volume": 20656474},
        {"symbol": "0700.HK", "timestamp": "2025-08-27T00:00:00+00:00", "open": 613.0, "high": 614.5, "low": 595.0, "close": 599.0, "volume": 21263402},
        {"symbol": "0700.HK", "timestamp": "2025-08-28T00:00:00+00:00", "open": 595.0, "high": 599.0, "low": 590.0, "close": 594.0, "volume": 21712370},
        {"symbol": "0700.HK", "timestamp": "2025-08-29T00:00:00+00:00", "open": 595.5, "high": 605.0, "low": 594.0, "close": 596.5, "volume": 18234935},
        {"symbol": "0700.HK", "timestamp": "2025-09-01T00:00:00+00:00", "open": 605.0, "high": 610.0, "low": 601.5, "close": 605.0, "volume": 15958837},
        {"symbol": "0700.HK", "timestamp": "2025-09-02T00:00:00+00:00", "open": 605.5, "high": 608.5, "low": 599.0, "close": 600.5, "volume": 14808157},
        {"symbol": "0700.HK", "timestamp": "2025-09-03T00:00:00+00:00", "open": 606.5, "high": 613.0, "low": 596.0, "close": 598.5, "volume": 15523985},
        {"symbol": "0700.HK", "timestamp": "2025-09-04T00:00:00+00:00", "open": 605.0, "high": 605.0, "low": 591.0, "close": 592.5, "volume": 18003934},
        {"symbol": "0700.HK", "timestamp": "2025-09-05T00:00:00+00:00", "open": 599.5, "high": 609.0, "low": 595.5, "close": 605.5, "volume": 19047729},
        {"symbol": "0700.HK", "timestamp": "2025-09-08T00:00:00+00:00", "open": 605.5, "high": 619.0, "low": 605.0, "close": 617.5, "volume": 21815489},
        {"symbol": "0700.HK", "timestamp": "2025-09-09T00:00:00+00:00", "open": 620.0, "high": 628.0, "low": 617.5, "close": 627.0, "volume": 19871460},
        {"symbol": "0700.HK", "timestamp": "2025-09-10T00:00:00+00:00", "open": 630.0, "high": 639.0, "low": 628.0, "close": 633.5, "volume": 19193376},
        {"symbol": "0700.HK", "timestamp": "2025-09-11T00:00:00+00:00", "open": 633.0, "high": 633.0, "low": 624.0, "close": 629.5, "volume": 18191860},
        {"symbol": "0700.HK", "timestamp": "2025-09-12T00:00:00+00:00", "open": 645.0, "high": 649.0, "low": 642.0, "close": 643.5, "volume": 20780375},
        {"symbol": "0700.HK", "timestamp": "2025-09-15T00:00:00+00:00", "open": 646.0, "high": 648.5, "low": 637.5, "close": 643.5, "volume": 16371242},
        {"symbol": "0700.HK", "timestamp": "2025-09-16T00:00:00+00:00", "open": 647.0, "high": 649.5, "low": 640.5, "close": 645.0, "volume": 13339685},
        {"symbol": "0700.HK", "timestamp": "2025-09-17T00:00:00+00:00", "open": 646.5, "high": 663.5, "low": 645.0, "close": 661.5, "volume": 22349048},
        {"symbol": "0700.HK", "timestamp": "2025-09-18T00:00:00+00:00", "open": 662.0, "high": 664.5, "low": 635.5, "close": 642.0, "volume": 29989898},
        {"symbol": "0700.HK", "timestamp": "2025-09-19T00:00:00+00:00", "open": 647.0, "high": 647.0, "low": 638.0, "close": 642.5, "volume": 20805608},
        {"symbol": "0700.HK", "timestamp": "2025-09-22T00:00:00+00:00", "open": 642.0, "high": 643.5, "low": 634.0, "close": 641.0, "volume": 12899662},
        {"symbol": "0700.HK", "timestamp": "2025-09-23T00:00:00+00:00", "open": 641.5, "high": 643.5, "low": 627.0, "close": 635.5, "volume": 15293080},
        {"symbol": "0700.HK", "timestamp": "2025-09-24T00:00:00+00:00", "open": 633.5, "high": 651.0, "low": 628.0, "close": 648.5, "volume": 18440788},
        {"symbol": "0700.HK", "timestamp": "2025-09-25T00:00:00+00:00", "open": 651.0, "high": 659.0, "low": 643.5, "close": 650.0, "volume": 17384258},
        {"symbol": "0700.HK", "timestamp": "2025-09-26T00:00:00+00:00", "open": 645.0, "high": 653.0, "low": 640.0, "close": 644.0, "volume": 19504951}
    ]
    
    # 當前價格
    current_price = 644.00
    
    # 創建分析器並生成報告
    analyzer = TencentSentimentAnalyzer(historical_data, current_price)
    report = analyzer.generate_comprehensive_report()
    
    # 輸出JSON格式報告
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 保存報告到文件
    with open('/workspace/tencent_sentiment_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n分析報告已保存到 tencent_sentiment_report.json")

if __name__ == "__main__":
    main()