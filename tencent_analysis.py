#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股 (0700.HK) 量化分析
專業trader分析代理
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

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

class TencentAnalyzer:
    def __init__(self, data: List[Dict]):
        self.df = pd.DataFrame(data)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        
    def calculate_technical_indicators(self) -> Dict:
        """計算技術指標"""
        df = self.df.copy()
        
        # 移動平均線
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        # 布林帶
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # 波動率
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        self.df_with_indicators = df
        
        return {
            'current_ma5': df['MA5'].iloc[-1] if not pd.isna(df['MA5'].iloc[-1]) else None,
            'current_ma10': df['MA10'].iloc[-1] if not pd.isna(df['MA10'].iloc[-1]) else None,
            'current_ma20': df['MA20'].iloc[-1] if not pd.isna(df['MA20'].iloc[-1]) else None,
            'current_rsi': df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else None,
            'current_macd': df['MACD'].iloc[-1] if not pd.isna(df['MACD'].iloc[-1]) else None,
            'current_macd_signal': df['MACD_signal'].iloc[-1] if not pd.isna(df['MACD_signal'].iloc[-1]) else None,
            'current_bb_upper': df['BB_upper'].iloc[-1] if not pd.isna(df['BB_upper'].iloc[-1]) else None,
            'current_bb_lower': df['BB_lower'].iloc[-1] if not pd.isna(df['BB_lower'].iloc[-1]) else None,
            'volatility': volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else None
        }
    
    def analyze_trend(self) -> Dict:
        """趨勢分析"""
        df = self.df_with_indicators
        
        # 短期趨勢 (5天)
        recent_prices = df['close'].tail(5).values
        short_trend = "上升" if recent_prices[-1] > recent_prices[0] else "下降"
        
        # 中期趨勢 (20天)
        if len(df) >= 20:
            medium_prices = df['close'].tail(20).values
            medium_trend = "上升" if medium_prices[-1] > medium_prices[0] else "下降"
        else:
            medium_trend = "數據不足"
        
        # 支撐和阻力位
        highs = df['high'].tail(10)
        lows = df['low'].tail(10)
        resistance_level = highs.max()
        support_level = lows.min()
        
        # 突破分析
        current_close = df['close'].iloc[-1]
        ma20 = df['MA20'].iloc[-1] if not pd.isna(df['MA20'].iloc[-1]) else None
        
        breakthrough_status = "中性"
        if ma20:
            if current_close > ma20 * 1.02:
                breakthrough_status = "向上突破"
            elif current_close < ma20 * 0.98:
                breakthrough_status = "向下突破"
        
        return {
            'short_term_trend': short_trend,
            'medium_term_trend': medium_trend,
            'resistance_level': resistance_level,
            'support_level': support_level,
            'breakthrough_status': breakthrough_status,
            'trend_strength': self._calculate_trend_strength()
        }
    
    def _calculate_trend_strength(self) -> str:
        """計算趨勢強度"""
        df = self.df_with_indicators
        
        # 基於RSI和MACD判斷趨勢強度
        rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        macd_histogram = df['MACD_histogram'].iloc[-1] if not pd.isna(df['MACD_histogram'].iloc[-1]) else 0
        
        if rsi > 70 and macd_histogram > 0:
            return "強勢上升"
        elif rsi < 30 and macd_histogram < 0:
            return "強勢下降"
        elif rsi > 50 and macd_histogram > 0:
            return "溫和上升"
        elif rsi < 50 and macd_histogram < 0:
            return "溫和下降"
        else:
            return "盤整"
    
    def analyze_volume(self) -> Dict:
        """成交量分析"""
        df = self.df
        
        # 平均成交量
        avg_volume = df['volume'].mean()
        recent_avg_volume = df['volume'].tail(5).mean()
        
        # 成交量趨勢
        volume_trend = "增加" if recent_avg_volume > avg_volume else "減少"
        
        # 價量關係
        price_change = df['close'].pct_change().tail(5)
        volume_change = df['volume'].pct_change().tail(5)
        
        # 計算價量相關性
        correlation = price_change.corr(volume_change)
        
        volume_analysis = "健康" if correlation > 0.3 else "分歧" if correlation < -0.3 else "中性"
        
        return {
            'average_volume': int(avg_volume),
            'recent_average_volume': int(recent_avg_volume),
            'volume_trend': volume_trend,
            'volume_price_correlation': correlation,
            'volume_analysis': volume_analysis
        }
    
    def calculate_risk_metrics(self) -> Dict:
        """風險評估"""
        df = self.df_with_indicators
        
        # 波動率
        returns = df['returns'].dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # 年化波動率
        
        # VaR (Value at Risk) 95%信心水平
        var_95 = np.percentile(returns, 5) * 100
        
        # 最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 夏普比率 (假設無風險利率為3%)
        risk_free_rate = 0.03 / 252  # 日無風險利率
        excess_returns = returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252)
        
        # 風險等級評估
        if volatility < 20:
            risk_level = "低"
        elif volatility < 35:
            risk_level = "中"
        else:
            risk_level = "高"
        
        return {
            'volatility': round(volatility, 2),
            'var_95': round(var_95, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'risk_level': risk_level
        }
    
    def generate_investment_recommendation(self) -> Dict:
        """投資建議"""
        technical_indicators = self.calculate_technical_indicators()
        trend_analysis = self.analyze_trend()
        volume_analysis = self.analyze_volume()
        risk_metrics = self.calculate_risk_metrics()
        
        # 綜合評分系統
        score = 0
        
        # 技術指標評分
        rsi = technical_indicators.get('current_rsi', 50)
        if 30 < rsi < 70:
            score += 2  # 健康範圍
        elif rsi > 70:
            score -= 1  # 超買
        elif rsi < 30:
            score += 1  # 超賣但有反彈機會
        
        # 趨勢評分
        if trend_analysis['short_term_trend'] == "上升":
            score += 2
        if trend_analysis['medium_term_trend'] == "上升":
            score += 2
        
        # 突破評分
        if trend_analysis['breakthrough_status'] == "向上突破":
            score += 3
        elif trend_analysis['breakthrough_status'] == "向下突破":
            score -= 2
        
        # 成交量評分
        if volume_analysis['volume_analysis'] == "健康":
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
        elif score >= -3:
            recommendation = "減持"
            confidence = "中"
        else:
            recommendation = "賣出"
            confidence = "高"
        
        # 預期收益計算
        if recommendation in ["強烈買入", "買入"]:
            expected_return_min = 5
            expected_return_max = 15
        elif recommendation == "持有":
            expected_return_min = -5
            expected_return_max = 8
        else:
            expected_return_min = -15
            expected_return_max = 3
        
        # 目標價位
        current_price = self.current_price
        if recommendation in ["強烈買入", "買入"]:
            target_price = current_price * 1.10
            stop_loss = current_price * 0.92
        elif recommendation == "持有":
            target_price = current_price * 1.05
            stop_loss = current_price * 0.95
        else:
            target_price = current_price * 0.95
            stop_loss = current_price * 0.88
        
        return {
            'recommendation': recommendation,
            'confidence_level': confidence,
            'composite_score': score,
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'expected_return_range': f"{expected_return_min}% 至 {expected_return_max}%",
            'investment_horizon': "1-3個月",
            'key_factors': self._get_key_factors(technical_indicators, trend_analysis, volume_analysis)
        }
    
    def _get_key_factors(self, technical, trend, volume) -> List[str]:
        """獲取關鍵因素"""
        factors = []
        
        rsi = technical.get('current_rsi', 50)
        if rsi > 70:
            factors.append("RSI顯示超買狀態")
        elif rsi < 30:
            factors.append("RSI顯示超賣狀態")
        
        if trend['breakthrough_status'] != "中性":
            factors.append(f"價格{trend['breakthrough_status']}")
        
        if volume['volume_analysis'] == "健康":
            factors.append("價量配合良好")
        elif volume['volume_analysis'] == "分歧":
            factors.append("價量出現分歧")
        
        factors.append(f"短期趨勢{trend['short_term_trend']}")
        factors.append(f"中期趨勢{trend['medium_term_trend']}")
        
        return factors
    
    def generate_comprehensive_analysis(self) -> Dict:
        """生成完整分析報告"""
        technical_indicators = self.calculate_technical_indicators()
        trend_analysis = self.analyze_trend()
        volume_analysis = self.analyze_volume()
        risk_metrics = self.calculate_risk_metrics()
        investment_recommendation = self.generate_investment_recommendation()
        
        return {
            "股票信息": {
                "股票代碼": "0700.HK",
                "股票名稱": "騰訊控股",
                "當前價格": self.current_price,
                "價格變化": f"+{self.price_change} (+{self.price_change_pct}%)",
                "分析日期": datetime.now().strftime("%Y-%m-%d"),
                "數據期間": "30個交易日"
            },
            "技術指標分析": {
                "移動平均線": {
                    "MA5": round(technical_indicators.get('current_ma5', 0), 2),
                    "MA10": round(technical_indicators.get('current_ma10', 0), 2),
                    "MA20": round(technical_indicators.get('current_ma20', 0), 2)
                },
                "動量指標": {
                    "RSI": round(technical_indicators.get('current_rsi', 0), 2),
                    "MACD": round(technical_indicators.get('current_macd', 0), 2),
                    "MACD信號線": round(technical_indicators.get('current_macd_signal', 0), 2)
                },
                "布林帶": {
                    "上軌": round(technical_indicators.get('current_bb_upper', 0), 2),
                    "下軌": round(technical_indicators.get('current_bb_lower', 0), 2)
                }
            },
            "趨勢分析": {
                "短期趨勢": trend_analysis['short_term_trend'],
                "中期趨勢": trend_analysis['medium_term_trend'],
                "趨勢強度": trend_analysis['trend_strength'],
                "關鍵價位": {
                    "阻力位": trend_analysis['resistance_level'],
                    "支撐位": trend_analysis['support_level']
                },
                "突破狀態": trend_analysis['breakthrough_status']
            },
            "成交量分析": {
                "平均成交量": volume_analysis['average_volume'],
                "近期平均成交量": volume_analysis['recent_average_volume'],
                "成交量趨勢": volume_analysis['volume_trend'],
                "價量關係": volume_analysis['volume_analysis'],
                "價量相關性": round(volume_analysis['volume_price_correlation'], 3)
            },
            "風險評估": {
                "波動率": f"{risk_metrics['volatility']}%",
                "風險等級": risk_metrics['risk_level'],
                "VaR(95%)": f"{risk_metrics['var_95']}%",
                "最大回撤": f"{risk_metrics['max_drawdown']}%",
                "夏普比率": risk_metrics['sharpe_ratio']
            },
            "投資建議": {
                "建議操作": investment_recommendation['recommendation'],
                "信心水平": investment_recommendation['confidence_level'],
                "綜合評分": f"{investment_recommendation['composite_score']}/10",
                "目標價位": f"HK${investment_recommendation['target_price']}",
                "止損價位": f"HK${investment_recommendation['stop_loss']}",
                "預期收益": investment_recommendation['expected_return_range'],
                "投資期限": investment_recommendation['investment_horizon'],
                "關鍵因素": investment_recommendation['key_factors']
            },
            "詳細分析過程": {
                "數據處理": "使用30個交易日的歷史數據，計算技術指標和統計量",
                "趨勢識別": "通過移動平均線和價格走勢確定短中期趨勢",
                "技術分析": "結合RSI、MACD、布林帶等多個技術指標進行綜合判斷",
                "風險量化": "計算波動率、VaR、最大回撤等風險指標",
                "綜合評分": "基於技術指標、趨勢、成交量等因素的加權評分系統"
            },
            "市場環境評估": {
                "技術面": "多項技術指標顯示股價處於相對強勢區間",
                "資金面": f"成交量{volume_analysis['volume_trend']}，{volume_analysis['volume_analysis']}的價量關係",
                "趨勢面": f"{trend_analysis['short_term_trend']}的短期趨勢，{trend_analysis['medium_term_trend']}的中期趨勢"
            }
        }

if __name__ == "__main__":
    analyzer = TencentAnalyzer(historical_data)
    result = analyzer.generate_comprehensive_analysis()
    
    # 輸出JSON格式結果
    print(json.dumps(result, ensure_ascii=False, indent=2))