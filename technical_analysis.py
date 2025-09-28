#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股(0700.HK)技術分析工具
專業量化分析AI代理 - Technical分析模組
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

class TechnicalAnalyzer:
    def __init__(self, data: List[Dict]):
        """
        初始化技術分析器
        
        Args:
            data: 歷史交易數據列表
        """
        self.raw_data = data
        self.df = self._prepare_dataframe()
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        
    def _prepare_dataframe(self) -> List[Dict]:
        """準備數據並計算基本指標"""
        # 按時間排序
        data = sorted(self.raw_data, key=lambda x: x['timestamp'])
        
        # 計算額外指標
        for i, item in enumerate(data):
            # 計算日內波幅
            item['daily_range'] = round(((item['high'] - item['low']) / item['close'] * 100), 2)
            item['body_size'] = abs(item['close'] - item['open'])
            item['upper_shadow'] = item['high'] - max(item['open'], item['close'])
            item['lower_shadow'] = min(item['open'], item['close']) - item['low']
        
        return data
    
    def calculate_moving_averages(self) -> Dict[str, float]:
        """計算移動平均線"""
        ma_periods = [5, 10, 20, 50]
        mas = {}
        
        closes = [item['close'] for item in self.df]
        
        for period in ma_periods:
            if len(closes) >= period:
                ma_value = sum(closes[-period:]) / period
                mas[f'MA{period}'] = round(ma_value, 2)
                
        return mas
    
    def calculate_rsi(self, period: int = 14) -> float:
        """計算RSI指標"""
        if len(self.df) < period + 1:
            return 50.0  # 默認中性值
            
        closes = [item['close'] for item in self.df]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def calculate_macd(self) -> Dict[str, float]:
        """計算MACD指標"""
        if len(self.df) < 26:
            return {'MACD': 0, 'Signal': 0, 'Histogram': 0}
        
        closes = [item['close'] for item in self.df]
        
        # 計算EMA
        def calculate_ema(prices, period):
            multiplier = 2 / (period + 1)
            ema = [prices[0]]  # 第一個值作為初始EMA
            for i in range(1, len(prices)):
                ema.append((prices[i] * multiplier) + (ema[-1] * (1 - multiplier)))
            return ema
        
        ema12 = calculate_ema(closes, 12)
        ema26 = calculate_ema(closes, 26)
        
        # MACD線 = EMA12 - EMA26
        macd_line = [ema12[i] - ema26[i] for i in range(len(ema26))]
        
        # 信號線 = MACD的9日EMA
        signal_line = calculate_ema(macd_line, 9)
        
        # 柱狀圖 = MACD - 信號線
        histogram = macd_line[-1] - signal_line[-1]
        
        return {
            'MACD': round(macd_line[-1], 2),
            'Signal': round(signal_line[-1], 2),
            'Histogram': round(histogram, 2)
        }
    
    def calculate_bollinger_bands(self, period: int = 20) -> Dict[str, float]:
        """計算布林帶"""
        closes = [item['close'] for item in self.df]
        
        if len(closes) < period:
            current_close = closes[-1]
            return {
                'Upper': round(current_close * 1.02, 2),
                'Middle': round(current_close, 2),
                'Lower': round(current_close * 0.98, 2)
            }
        
        recent_closes = closes[-period:]
        middle = sum(recent_closes) / len(recent_closes)
        
        # 計算標準差
        variance = sum((x - middle) ** 2 for x in recent_closes) / len(recent_closes)
        std = math.sqrt(variance)
        
        upper = middle + (2 * std)
        lower = middle - (2 * std)
        
        return {
            'Upper': round(upper, 2),
            'Middle': round(middle, 2),
            'Lower': round(lower, 2)
        }
    
    def identify_support_resistance(self) -> Dict[str, List[float]]:
        """識別支撐和阻力位"""
        highs = [item['high'] for item in self.df]
        lows = [item['low'] for item in self.df]
        closes = [item['close'] for item in self.df]
        
        # 找出近期重要的高點和低點
        resistance_levels = []
        support_levels = []
        
        # 最近20天的重要價位
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        recent_closes = closes[-20:] if len(closes) >= 20 else closes
        
        # 阻力位：近期高點
        max_high = max(recent_highs)
        resistance_levels.append(max_high)
        
        # 心理價位
        current_price = closes[-1]
        resistance_levels.append(round((current_price // 10 + 1) * 10, 0))  # 下一個整數位
        
        # 支撐位：近期低點
        min_low = min(recent_lows)
        support_levels.append(min_low)
        
        # 移動平均線作為支撐
        ma20 = sum(recent_closes) / len(recent_closes)
        support_levels.append(ma20)
        
        return {
            'resistance': sorted(set([round(x, 2) for x in resistance_levels]), reverse=True),
            'support': sorted(set([round(x, 2) for x in support_levels]), reverse=True)
        }
    
    def analyze_volume_pattern(self) -> Dict[str, Any]:
        """分析成交量模式"""
        volumes = [item['volume'] for item in self.df]
        closes = [item['close'] for item in self.df]
        
        # 平均成交量
        avg_volume = sum(volumes) / len(volumes)
        recent_avg_volume = sum(volumes[-5:]) / min(5, len(volumes))  # 最近5天平均
        
        # 成交量趨勢
        volume_trend = "增加" if recent_avg_volume > avg_volume else "減少"
        
        # 最近的價量關係
        if len(closes) >= 6:
            recent_price_change = closes[-1] - closes[-6]  # 5天價格變化
        else:
            recent_price_change = closes[-1] - closes[0]
        
        price_volume_sync = "良好" if (recent_price_change > 0 and recent_avg_volume > avg_volume) or \
                                   (recent_price_change < 0 and recent_avg_volume < avg_volume) else "分歧"
        
        return {
            'avg_volume': int(avg_volume),
            'recent_avg_volume': int(recent_avg_volume),
            'volume_trend': volume_trend,
            'price_volume_sync': price_volume_sync,
            'volume_ratio': round(recent_avg_volume / avg_volume, 2)
        }
    
    def determine_trend(self) -> Dict[str, str]:
        """判斷趨勢方向"""
        closes = [item['close'] for item in self.df]
        
        # 短期趨勢 (5天)
        if len(closes) >= 6:
            short_trend = "上升" if closes[-1] > closes[-6] else "下降"
        else:
            short_trend = "震盪"
        
        # 中期趨勢 (20天)
        if len(closes) >= 21:
            medium_trend = "上升" if closes[-1] > closes[-21] else "下降"
        else:
            medium_trend = "震盪"
        
        # 長期趨勢 (基於移動平均線)
        mas = self.calculate_moving_averages()
        if 'MA20' in mas and 'MA50' in mas:
            long_trend = "上升" if mas['MA20'] > mas['MA50'] else "下降"
        else:
            long_trend = "震盪"
        
        return {
            'short_term': short_trend,
            'medium_term': medium_trend,
            'long_term': long_trend
        }
    
    def calculate_volatility(self) -> float:
        """計算波動率"""
        closes = [item['close'] for item in self.df]
        
        if len(closes) < 2:
            return 20.0  # 默認值
        
        # 計算日收益率
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        
        # 計算標準差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        # 年化波動率 (假設252個交易日)
        volatility = std_dev * math.sqrt(252) * 100
        
        return round(volatility, 2)
    
    def generate_signals(self) -> Dict[str, str]:
        """生成交易信號"""
        rsi = self.calculate_rsi()
        macd = self.calculate_macd()
        mas = self.calculate_moving_averages()
        bb = self.calculate_bollinger_bands()
        
        signals = []
        
        # RSI信號
        if rsi > 70:
            signals.append("RSI超買")
        elif rsi < 30:
            signals.append("RSI超賣")
        else:
            signals.append("RSI中性")
        
        # MACD信號
        if macd['MACD'] > macd['Signal'] and macd['Histogram'] > 0:
            signals.append("MACD看多")
        elif macd['MACD'] < macd['Signal'] and macd['Histogram'] < 0:
            signals.append("MACD看空")
        else:
            signals.append("MACD中性")
        
        # 移動平均線信號
        current_price = self.current_price
        if 'MA20' in mas:
            if current_price > mas['MA20']:
                signals.append("價格在MA20之上")
            else:
                signals.append("價格在MA20之下")
        
        # 布林帶信號
        if current_price > bb['Upper']:
            signals.append("突破布林帶上軌")
        elif current_price < bb['Lower']:
            signals.append("跌破布林帶下軌")
        else:
            signals.append("在布林帶內運行")
        
        return {'signals': signals}
    
    def assess_risk_reward(self) -> Dict[str, Any]:
        """風險收益評估"""
        volatility = self.calculate_volatility()
        support_resistance = self.identify_support_resistance()
        
        current_price = self.current_price
        
        # 計算潛在上漲空間
        if support_resistance['resistance']:
            upside_target = support_resistance['resistance'][0]
            upside_potential = ((upside_target - current_price) / current_price * 100)
        else:
            upside_potential = 5.0  # 默認5%
        
        # 計算潛在下跌風險
        if support_resistance['support']:
            downside_target = support_resistance['support'][-1]
            downside_risk = ((current_price - downside_target) / current_price * 100)
        else:
            downside_risk = 5.0  # 默認5%
        
        # 風險等級評估
        if volatility > 30:
            risk_level = "高"
        elif volatility > 20:
            risk_level = "中"
        else:
            risk_level = "低"
        
        return {
            'volatility': volatility,
            'upside_potential': round(upside_potential, 2),
            'downside_risk': round(downside_risk, 2),
            'risk_level': risk_level,
            'risk_reward_ratio': round(upside_potential / max(downside_risk, 1), 2)
        }
    
    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """生成綜合分析報告"""
        
        # 計算所有技術指標
        mas = self.calculate_moving_averages()
        rsi = self.calculate_rsi()
        macd = self.calculate_macd()
        bb = self.calculate_bollinger_bands()
        support_resistance = self.identify_support_resistance()
        volume_analysis = self.analyze_volume_pattern()
        trend_analysis = self.determine_trend()
        signals = self.generate_signals()
        risk_reward = self.assess_risk_reward()
        
        # 生成投資建議
        investment_advice = self._generate_investment_advice(rsi, macd, trend_analysis, risk_reward)
        
        # 構建完整報告
        analysis_report = {
            "股票信息": {
                "股票代碼": "0700.HK",
                "股票名稱": "騰訊控股",
                "當前價格": self.current_price,
                "價格變化": f"+{self.price_change} (+{self.price_change_pct}%)",
                "分析日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            
            "技術指標分析": {
                "移動平均線": mas,
                "RSI指標": {
                    "數值": rsi,
                    "解讀": self._interpret_rsi(rsi)
                },
                "MACD指標": {
                    **macd,
                    "解讀": self._interpret_macd(macd)
                },
                "布林帶": {
                    **bb,
                    "當前位置": self._interpret_bollinger_position(self.current_price, bb)
                }
            },
            
            "趨勢分析": {
                **trend_analysis,
                "整體趨勢": self._determine_overall_trend(trend_analysis)
            },
            
            "支撐阻力分析": {
                "關鍵阻力位": support_resistance['resistance'],
                "關鍵支撐位": support_resistance['support'],
                "當前位置分析": self._analyze_current_position(self.current_price, support_resistance)
            },
            
            "成交量分析": volume_analysis,
            
            "交易信號": signals,
            
            "風險收益評估": {
                **risk_reward,
                "風險評級說明": self._explain_risk_level(risk_reward['risk_level'])
            },
            
            "投資建議": investment_advice,
            
            "預期收益評估": {
                "短期目標": f"{support_resistance['resistance'][0] if support_resistance['resistance'] else self.current_price * 1.05:.2f}",
                "預期收益": f"{risk_reward['upside_potential']:.1f}%",
                "止損位": f"{support_resistance['support'][-1] if support_resistance['support'] else self.current_price * 0.95:.2f}",
                "最大風險": f"-{risk_reward['downside_risk']:.1f}%"
            }
        }
        
        return analysis_report
    
    def _interpret_rsi(self, rsi: float) -> str:
        """解讀RSI指標"""
        if rsi > 70:
            return "超買區域，可能面臨回調壓力"
        elif rsi > 50:
            return "強勢區域，多頭佔優"
        elif rsi > 30:
            return "弱勢區域，空頭佔優"
        else:
            return "超賣區域，可能出現反彈"
    
    def _interpret_macd(self, macd: Dict[str, float]) -> str:
        """解讀MACD指標"""
        if macd['MACD'] > macd['Signal'] and macd['Histogram'] > 0:
            return "金叉向上，買入信號"
        elif macd['MACD'] < macd['Signal'] and macd['Histogram'] < 0:
            return "死叉向下，賣出信號"
        else:
            return "震盪整理，觀望為主"
    
    def _interpret_bollinger_position(self, price: float, bb: Dict[str, float]) -> str:
        """解讀布林帶位置"""
        if price > bb['Upper']:
            return "突破上軌，強勢上漲"
        elif price > bb['Middle']:
            return "上軌區域，偏強運行"
        elif price > bb['Lower']:
            return "下軌區域，偏弱運行"
        else:
            return "跌破下軌，弱勢下跌"
    
    def _determine_overall_trend(self, trends: Dict[str, str]) -> str:
        """判斷整體趨勢"""
        up_count = sum(1 for trend in trends.values() if trend == "上升")
        down_count = sum(1 for trend in trends.values() if trend == "下降")
        
        if up_count >= 2:
            return "多頭趨勢"
        elif down_count >= 2:
            return "空頭趨勢"
        else:
            return "震盪趨勢"
    
    def _analyze_current_position(self, price: float, sr: Dict[str, List[float]]) -> str:
        """分析當前價位"""
        if sr['resistance'] and price >= sr['resistance'][-1]:
            return "接近阻力位，上方壓力較大"
        elif sr['support'] and price <= sr['support'][0]:
            return "接近支撐位，下方支撐較強"
        else:
            return "在支撐阻力區間內運行"
    
    def _explain_risk_level(self, risk_level: str) -> str:
        """解釋風險等級"""
        explanations = {
            "低": "波動率較小，適合穩健型投資者",
            "中": "波動率適中，適合平衡型投資者",
            "高": "波動率較大，適合積極型投資者，需嚴格控制倉位"
        }
        return explanations.get(risk_level, "風險等級待評估")
    
    def _generate_investment_advice(self, rsi: float, macd: Dict, trends: Dict, risk_reward: Dict) -> Dict[str, Any]:
        """生成投資建議"""
        
        # 綜合評分
        score = 0
        
        # RSI評分
        if 30 <= rsi <= 70:
            score += 1
        elif rsi < 30:
            score += 2  # 超賣更積極
        
        # MACD評分
        if macd['MACD'] > macd['Signal']:
            score += 1
        
        # 趨勢評分
        up_trends = sum(1 for trend in trends.values() if trend == "上升")
        score += up_trends
        
        # 風險收益比評分
        if risk_reward['risk_reward_ratio'] > 2:
            score += 2
        elif risk_reward['risk_reward_ratio'] > 1:
            score += 1
        
        # 生成建議
        if score >= 5:
            recommendation = "強烈買入"
            confidence = "高"
            position_size = "可考慮較大倉位(30-50%)"
        elif score >= 3:
            recommendation = "買入"
            confidence = "中"
            position_size = "建議中等倉位(20-30%)"
        elif score >= 1:
            recommendation = "觀望"
            confidence = "低"
            position_size = "建議小倉位試探(10-20%)"
        else:
            recommendation = "避險"
            confidence = "低"
            position_size = "建議空倉或減倉"
        
        return {
            "總體建議": recommendation,
            "信心度": confidence,
            "建議倉位": position_size,
            "操作策略": self._generate_strategy(recommendation, risk_reward),
            "注意事項": [
                "密切關注成交量變化",
                "設置合理止損位",
                "分批建倉降低風險",
                "關注市場整體環境"
            ]
        }
    
    def _generate_strategy(self, recommendation: str, risk_reward: Dict) -> str:
        """生成操作策略"""
        strategies = {
            "強烈買入": f"積極建倉，目標收益{risk_reward['upside_potential']:.1f}%，止損{risk_reward['downside_risk']:.1f}%",
            "買入": f"分批建倉，目標收益{risk_reward['upside_potential']:.1f}%，嚴格止損",
            "觀望": "等待更明確信號，或小倉位試探",
            "避險": "減倉或空倉，等待更好機會"
        }
        return strategies.get(recommendation, "持續觀察市場動態")


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
    
    # 創建分析器並生成報告
    analyzer = TechnicalAnalyzer(historical_data)
    analysis_report = analyzer.generate_comprehensive_analysis()
    
    # 輸出JSON格式報告
    print(json.dumps(analysis_report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()