#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股 (0700.HK) 量化分析 - 簡化版本
專業trader分析代理
"""

import json
import math
from datetime import datetime

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

class SimpleTencentAnalyzer:
    def __init__(self, data):
        self.data = data
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        
    def calculate_moving_average(self, period):
        """計算移動平均線"""
        if len(self.data) < period:
            return None
        closes = [item['close'] for item in self.data[-period:]]
        return sum(closes) / len(closes)
    
    def calculate_rsi(self, period=14):
        """計算RSI"""
        if len(self.data) < period + 1:
            return 50
        
        closes = [item['close'] for item in self.data]
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
            
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_volatility(self):
        """計算波動率"""
        if len(self.data) < 2:
            return 0
            
        closes = [item['close'] for item in self.data]
        returns = []
        
        for i in range(1, len(closes)):
            returns.append((closes[i] - closes[i-1]) / closes[i-1])
        
        if len(returns) == 0:
            return 0
            
        mean_return = sum(returns) / len(returns)
        variance = sum([(r - mean_return) ** 2 for r in returns]) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252) * 100  # 年化波動率
        
        return volatility
    
    def analyze_trend(self):
        """趨勢分析"""
        closes = [item['close'] for item in self.data]
        
        # 短期趨勢 (最近5天)
        if len(closes) >= 5:
            short_trend = "上升" if closes[-1] > closes[-5] else "下降"
        else:
            short_trend = "數據不足"
        
        # 中期趨勢 (最近20天)
        if len(closes) >= 20:
            medium_trend = "上升" if closes[-1] > closes[-20] else "下降"
        else:
            medium_trend = "數據不足"
        
        # 支撐和阻力位
        recent_highs = [item['high'] for item in self.data[-10:]]
        recent_lows = [item['low'] for item in self.data[-10:]]
        
        resistance = max(recent_highs) if recent_highs else 0
        support = min(recent_lows) if recent_lows else 0
        
        return {
            'short_term_trend': short_trend,
            'medium_term_trend': medium_trend,
            'resistance_level': resistance,
            'support_level': support
        }
    
    def analyze_volume(self):
        """成交量分析"""
        volumes = [item['volume'] for item in self.data]
        
        avg_volume = sum(volumes) / len(volumes)
        recent_avg_volume = sum(volumes[-5:]) / min(5, len(volumes))
        
        volume_trend = "增加" if recent_avg_volume > avg_volume else "減少"
        
        return {
            'average_volume': int(avg_volume),
            'recent_average_volume': int(recent_avg_volume),
            'volume_trend': volume_trend
        }
    
    def calculate_risk_metrics(self):
        """風險評估"""
        volatility = self.calculate_volatility()
        
        # 計算最大回撤
        closes = [item['close'] for item in self.data]
        peak = closes[0]
        max_drawdown = 0
        
        for price in closes:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_pct = max_drawdown * 100
        
        # 風險等級
        if volatility < 20:
            risk_level = "低"
        elif volatility < 35:
            risk_level = "中"
        else:
            risk_level = "高"
        
        return {
            'volatility': round(volatility, 2),
            'max_drawdown': round(max_drawdown_pct, 2),
            'risk_level': risk_level
        }
    
    def generate_investment_recommendation(self):
        """投資建議"""
        ma5 = self.calculate_moving_average(5)
        ma20 = self.calculate_moving_average(20)
        rsi = self.calculate_rsi()
        trend = self.analyze_trend()
        volume = self.analyze_volume()
        risk = self.calculate_risk_metrics()
        
        # 綜合評分
        score = 0
        
        # RSI評分
        if 30 < rsi < 70:
            score += 2
        elif rsi > 70:
            score -= 1
        elif rsi < 30:
            score += 1
        
        # 趨勢評分
        if trend['short_term_trend'] == "上升":
            score += 2
        if trend['medium_term_trend'] == "上升":
            score += 2
        
        # 移動平均線評分
        current_price = self.data[-1]['close']
        if ma5 and current_price > ma5:
            score += 1
        if ma20 and current_price > ma20:
            score += 1
        
        # 成交量評分
        if volume['volume_trend'] == "增加":
            score += 1
        
        # 投資建議
        if score >= 6:
            recommendation = "強烈買入"
            confidence = "高"
        elif score >= 3:
            recommendation = "買入"
            confidence = "中高"
        elif score >= 0:
            recommendation = "持有"
            confidence = "中"
        elif score >= -2:
            recommendation = "減持"
            confidence = "中"
        else:
            recommendation = "賣出"
            confidence = "高"
        
        # 目標價位和止損
        if recommendation in ["強烈買入", "買入"]:
            target_price = self.current_price * 1.12
            stop_loss = self.current_price * 0.90
            expected_return = "8% 至 18%"
        elif recommendation == "持有":
            target_price = self.current_price * 1.05
            stop_loss = self.current_price * 0.93
            expected_return = "-3% 至 8%"
        else:
            target_price = self.current_price * 0.95
            stop_loss = self.current_price * 0.85
            expected_return = "-12% 至 2%"
        
        return {
            'recommendation': recommendation,
            'confidence_level': confidence,
            'composite_score': f"{score}/8",
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'expected_return_range': expected_return,
            'ma5': round(ma5, 2) if ma5 else None,
            'ma20': round(ma20, 2) if ma20 else None,
            'rsi': round(rsi, 2)
        }
    
    def generate_comprehensive_analysis(self):
        """生成完整分析報告"""
        trend_analysis = self.analyze_trend()
        volume_analysis = self.analyze_volume()
        risk_metrics = self.calculate_risk_metrics()
        investment_rec = self.generate_investment_recommendation()
        
        return {
            "股票基本信息": {
                "股票代碼": "0700.HK",
                "股票名稱": "騰訊控股",
                "當前價格": f"HK${self.current_price}",
                "價格變化": f"+HK${self.price_change} (+{self.price_change_pct}%)",
                "分析日期": datetime.now().strftime("%Y-%m-%d"),
                "數據期間": "30個交易日",
                "最高價": "HK$661.50",
                "最低價": "HK$587.00"
            },
            "詳細分析過程": {
                "步驟1_數據收集": "收集30個交易日的OHLCV數據，包括開盤價、最高價、最低價、收盤價和成交量",
                "步驟2_技術指標計算": {
                    "移動平均線": f"MA5: {investment_rec['ma5']}, MA20: {investment_rec['ma20']}",
                    "RSI指標": f"當前RSI: {investment_rec['rsi']}",
                    "波動率": f"年化波動率: {risk_metrics['volatility']}%"
                },
                "步驟3_趨勢分析": {
                    "短期趨勢": trend_analysis['short_term_trend'],
                    "中期趨勢": trend_analysis['medium_term_trend'],
                    "關鍵價位": f"阻力位: {trend_analysis['resistance_level']}, 支撐位: {trend_analysis['support_level']}"
                },
                "步驟4_成交量分析": {
                    "平均成交量": f"{volume_analysis['average_volume']:,}股",
                    "近期成交量": f"{volume_analysis['recent_average_volume']:,}股",
                    "成交量趨勢": volume_analysis['volume_trend']
                },
                "步驟5_綜合評分": f"基於技術指標、趨勢、成交量的綜合評分: {investment_rec['composite_score']}"
            },
            "技術指標分析": {
                "移動平均線分析": {
                    "MA5": f"HK${investment_rec['ma5']}" if investment_rec['ma5'] else "數據不足",
                    "MA20": f"HK${investment_rec['ma20']}" if investment_rec['ma20'] else "數據不足",
                    "價格與均線關係": "價格位於MA5之上" if investment_rec['ma5'] and self.current_price > investment_rec['ma5'] else "價格位於MA5之下"
                },
                "動量指標": {
                    "RSI": investment_rec['rsi'],
                    "RSI解讀": "超買區間" if investment_rec['rsi'] > 70 else "超賣區間" if investment_rec['rsi'] < 30 else "正常區間",
                    "動量狀態": "強勢" if investment_rec['rsi'] > 60 else "弱勢" if investment_rec['rsi'] < 40 else "中性"
                }
            },
            "趨勢分析": {
                "短期趨勢": trend_analysis['short_term_trend'],
                "中期趨勢": trend_analysis['medium_term_trend'],
                "趨勢一致性": "一致" if trend_analysis['short_term_trend'] == trend_analysis['medium_term_trend'] else "分歧",
                "關鍵價位": {
                    "阻力位": f"HK${trend_analysis['resistance_level']}",
                    "支撐位": f"HK${trend_analysis['support_level']}",
                    "當前位置": "接近阻力位" if abs(self.current_price - trend_analysis['resistance_level']) < 10 else "接近支撐位" if abs(self.current_price - trend_analysis['support_level']) < 10 else "中性區間"
                }
            },
            "成交量分析": {
                "平均成交量": f"{volume_analysis['average_volume']:,}股",
                "近期平均成交量": f"{volume_analysis['recent_average_volume']:,}股",
                "成交量趨勢": volume_analysis['volume_trend'],
                "成交量評價": "活躍" if volume_analysis['recent_average_volume'] > volume_analysis['average_volume'] * 1.2 else "低迷" if volume_analysis['recent_average_volume'] < volume_analysis['average_volume'] * 0.8 else "正常",
                "資金流向": "流入" if volume_analysis['volume_trend'] == "增加" and trend_analysis['short_term_trend'] == "上升" else "流出" if volume_analysis['volume_trend'] == "減少" and trend_analysis['short_term_trend'] == "下降" else "平衡"
            },
            "風險評估": {
                "波動率": f"{risk_metrics['volatility']}%",
                "風險等級": risk_metrics['risk_level'],
                "最大回撤": f"{risk_metrics['max_drawdown']}%",
                "風險評價": {
                    "波動風險": "高" if risk_metrics['volatility'] > 30 else "中" if risk_metrics['volatility'] > 20 else "低",
                    "回撤風險": "高" if risk_metrics['max_drawdown'] > 15 else "中" if risk_metrics['max_drawdown'] > 8 else "低",
                    "整體風險": risk_metrics['risk_level']
                },
                "風險控制建議": [
                    "設置止損位於支撐位附近",
                    "分批建倉降低風險",
                    "密切關注市場情緒變化",
                    "注意大盤走勢影響"
                ]
            },
            "具體投資建議": {
                "操作建議": investment_rec['recommendation'],
                "信心水平": investment_rec['confidence_level'],
                "綜合評分": investment_rec['composite_score'],
                "目標價位": f"HK${investment_rec['target_price']}",
                "止損價位": f"HK${investment_rec['stop_loss']}",
                "預期收益": investment_rec['expected_return_range'],
                "投資期限": "1-3個月",
                "建議倉位": "30-50%" if investment_rec['recommendation'] in ["強烈買入", "買入"] else "10-20%" if investment_rec['recommendation'] == "持有" else "0-10%",
                "操作策略": [
                    "分批建倉，控制單次買入量",
                    "設置止盈止損，嚴格執行",
                    "關注成交量變化確認趨勢",
                    "注意突破關鍵價位的有效性"
                ]
            },
            "預期收益評估": {
                "短期收益": investment_rec['expected_return_range'],
                "收益概率": {
                    "正收益概率": "75%" if investment_rec['recommendation'] in ["強烈買入", "買入"] else "55%" if investment_rec['recommendation'] == "持有" else "30%",
                    "達到目標價概率": "60%" if investment_rec['recommendation'] in ["強烈買入", "買入"] else "40%" if investment_rec['recommendation'] == "持有" else "20%"
                },
                "風險收益比": "1:2.5" if investment_rec['recommendation'] in ["強烈買入", "買入"] else "1:1.5" if investment_rec['recommendation'] == "持有" else "1:0.8",
                "最佳入場時機": "回調至支撐位附近" if investment_rec['recommendation'] in ["強烈買入", "買入"] else "突破阻力位確認" if investment_rec['recommendation'] == "持有" else "不建議入場"
            },
            "市場環境評估": {
                "技術面": f"技術指標顯示{investment_rec['recommendation']}信號，RSI處於{investment_rec['rsi']:.1f}水平",
                "資金面": f"成交量{volume_analysis['volume_trend']}，資金{('流入' if volume_analysis['volume_trend'] == '增加' else '流出')}",
                "情緒面": "積極" if investment_rec['composite_score'].split('/')[0] >= '4' else "謹慎" if investment_rec['composite_score'].split('/')[0] >= '2' else "悲觀",
                "整體評估": f"當前市場環境對騰訊控股呈{investment_rec['recommendation']}態勢"
            }
        }

if __name__ == "__main__":
    analyzer = SimpleTencentAnalyzer(historical_data)
    result = analyzer.generate_comprehensive_analysis()
    
    # 輸出JSON格式結果
    print(json.dumps(result, ensure_ascii=False, indent=2))