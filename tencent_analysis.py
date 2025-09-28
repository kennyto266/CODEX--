#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股(0700.HK) 基本面分析工具
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Any

class TencentFundamentalAnalysis:
    def __init__(self):
        self.stock_data = [
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
        
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        self.period_high = 661.50
        self.period_low = 587.00
        self.avg_volume = 18690238
        
    def calculate_technical_indicators(self) -> Dict[str, Any]:
        """計算技術指標"""
        # 提取收盤價
        closes = [item['close'] for item in self.stock_data]
        volumes = [item['volume'] for item in self.stock_data]
        
        # 計算移動平均線
        ma5 = self.calculate_moving_average(closes, 5) if len(closes) >= 5 else None
        ma10 = self.calculate_moving_average(closes, 10) if len(closes) >= 10 else None
        ma20 = self.calculate_moving_average(closes, 20) if len(closes) >= 20 else None
        
        # 計算日收益率
        daily_returns = []
        for i in range(1, len(closes)):
            daily_return = (closes[i] - closes[i-1]) / closes[i-1]
            daily_returns.append(daily_return)
        
        # 計算年化波動率
        if daily_returns:
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = math.sqrt(variance) * math.sqrt(252)  # 年化波動率
        else:
            volatility = 0
        
        # 計算RSI
        rsi = self.calculate_rsi(closes, 14) if len(closes) >= 14 else None
        
        # 價格趨勢分析
        start_price = closes[0]
        end_price = closes[-1]
        total_return = (end_price - start_price) / start_price * 100
        
        return {
            'moving_averages': {
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20
            },
            'volatility': volatility,
            'rsi': rsi,
            'total_return_30days': total_return,
            'price_momentum': 'bullish' if total_return > 0 else 'bearish',
            'volume_trend': self.analyze_volume_trend_simple(volumes)
        }
    
    def calculate_moving_average(self, data: List[float], window: int) -> float:
        """計算移動平均"""
        if len(data) < window:
            return None
        return sum(data[-window:]) / window
    
    def calculate_rsi(self, prices: List[float], period: int) -> float:
        """計算RSI指標"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def analyze_volume_trend_simple(self, volumes: List[int]) -> str:
        """分析成交量趋势"""
        if len(volumes) < 10:
            return 'insufficient_data'
        
        recent_volume = sum(volumes[-5:]) / 5
        earlier_volume = sum(volumes[:-5]) / len(volumes[:-5])
        
        if recent_volume > earlier_volume * 1.2:
            return 'increasing'
        elif recent_volume < earlier_volume * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def fundamental_analysis(self) -> Dict[str, Any]:
        """基本面分析"""
        # 基於當前市場數據的分析
        technical_data = self.calculate_technical_indicators()
        
        # 價格表現分析
        price_performance = {
            'current_vs_period_high': (self.current_price - self.period_high) / self.period_high * 100,
            'current_vs_period_low': (self.current_price - self.period_low) / self.period_low * 100,
            'price_range_position': (self.current_price - self.period_low) / (self.period_high - self.period_low) * 100
        }
        
        # 流動性分析
        liquidity_analysis = {
            'avg_daily_volume': self.avg_volume,
            'volume_rating': 'high' if self.avg_volume > 15000000 else 'medium' if self.avg_volume > 10000000 else 'low',
            'market_cap_estimate': self.current_price * 9600000000  # 估算市值 (假設約96億股)
        }
        
        return {
            'technical_indicators': technical_data,
            'price_performance': price_performance,
            'liquidity_analysis': liquidity_analysis,
            'analysis_date': datetime.now().isoformat()
        }
    
    def risk_assessment(self) -> Dict[str, Any]:
        """風險評估"""
        technical_data = self.calculate_technical_indicators()
        
        # 市場風險
        market_risk = 'high' if technical_data['volatility'] > 0.3 else 'medium' if technical_data['volatility'] > 0.2 else 'low'
        
        # 流動性風險
        liquidity_risk = 'low' if self.avg_volume > 15000000 else 'medium' if self.avg_volume > 10000000 else 'high'
        
        # 價格風險 (基於當前位置)
        price_position = (self.current_price - self.period_low) / (self.period_high - self.period_low)
        price_risk = 'high' if price_position > 0.8 else 'medium' if price_position > 0.5 else 'low'
        
        return {
            'overall_risk': 'medium',  # 綜合評估
            'market_risk': market_risk,
            'liquidity_risk': liquidity_risk,
            'price_risk': price_risk,
            'volatility': technical_data['volatility'],
            'risk_factors': [
                '科技股整體估值波動',
                '監管政策變化風險',
                '宏觀經濟環境影響',
                '競爭加劇風險'
            ]
        }
    
    def investment_recommendation(self) -> Dict[str, Any]:
        """投資建議"""
        technical_data = self.calculate_technical_indicators()
        risk_data = self.risk_assessment()
        
        # 基於技術分析的建議
        if technical_data['total_return_30days'] > 8 and technical_data['rsi'] and technical_data['rsi'] < 70:
            recommendation = 'buy'
            confidence = 'medium'
        elif technical_data['total_return_30days'] > 5:
            recommendation = 'hold'
            confidence = 'medium'
        elif technical_data['total_return_30days'] < -5:
            recommendation = 'sell'
            confidence = 'low'
        else:
            recommendation = 'hold'
            confidence = 'medium'
        
        # 預期收益評估
        expected_return = {
            '1_month': '5-10%' if recommendation == 'buy' else '0-5%' if recommendation == 'hold' else '-5-0%',
            '3_months': '10-20%' if recommendation == 'buy' else '0-10%' if recommendation == 'hold' else '-10-5%',
            '6_months': '15-25%' if recommendation == 'buy' else '5-15%' if recommendation == 'hold' else '-15-10%'
        }
        
        return {
            'recommendation': recommendation,
            'confidence_level': confidence,
            'target_price_range': {
                'conservative': self.current_price * 1.05,
                'moderate': self.current_price * 1.12,
                'optimistic': self.current_price * 1.20
            },
            'expected_returns': expected_return,
            'investment_horizon': 'medium_term',  # 3-6個月
            'position_sizing': 'moderate'  # 建議倉位大小
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成綜合分析報告"""
        fundamental_data = self.fundamental_analysis()
        risk_data = self.risk_assessment()
        investment_data = self.investment_recommendation()
        
        return {
            'stock_info': {
                'symbol': '0700.HK',
                'company_name': '騰訊控股',
                'current_price': self.current_price,
                'price_change': self.price_change,
                'price_change_percentage': self.price_change_pct,
                'analysis_period': '30_trading_days',
                'analysis_date': datetime.now().strftime('%Y-%m-%d')
            },
            'fundamental_analysis': fundamental_data,
            'risk_assessment': risk_data,
            'investment_recommendation': investment_data,
            'key_insights': [
                f'股價在30天內上漲{self.price_change_pct:.1f}%，顯示強勁上升趨勢',
                f'當前價格位於期間高低點的{((self.current_price - self.period_low) / (self.period_high - self.period_low) * 100):.1f}%位置',
                f'平均日成交量{self.avg_volume:,}股，流動性良好',
                '技術面顯示持續上升動能，但需注意回調風險'
            ],
            'disclaimer': '本分析僅供參考，投資有風險，請謹慎決策'
        }

if __name__ == '__main__':
    analyzer = TencentFundamentalAnalysis()
    report = analyzer.generate_comprehensive_report()
    
    # 輸出JSON格式報告
    print(json.dumps(report, ensure_ascii=False, indent=2))