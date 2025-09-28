#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股(0700.HK) Fundamental分析
專業量化分析AI代理
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import statistics

class TencentFundamentalAnalysis:
    def __init__(self):
        # 股票基本信息
        self.stock_info = {
            "symbol": "0700.HK",
            "company_name": "騰訊控股",
            "current_price": 644.00,
            "price_change": 57.00,
            "price_change_pct": 9.71,
            "high_30d": 661.50,
            "low_30d": 587.00,
            "avg_volume_30d": 18690238
        }
        
        # 完整歷史數據
        self.historical_data = [
            {"timestamp": "2025-08-18", "open": 594.0, "high": 596.0, "low": 587.0, "close": 587.0, "volume": 17590658},
            {"timestamp": "2025-08-19", "open": 588.0, "high": 597.0, "low": 583.0, "close": 592.5, "volume": 16359474},
            {"timestamp": "2025-08-20", "open": 589.0, "high": 594.5, "low": 585.5, "close": 590.5, "volume": 15952765},
            {"timestamp": "2025-08-21", "open": 590.5, "high": 597.0, "low": 589.5, "close": 593.0, "volume": 14290178},
            {"timestamp": "2025-08-22", "open": 599.0, "high": 606.5, "low": 595.5, "close": 600.0, "volume": 19378950},
            {"timestamp": "2025-08-25", "open": 608.5, "high": 621.0, "low": 608.0, "close": 614.5, "volume": 25694519},
            {"timestamp": "2025-08-26", "open": 612.0, "high": 618.0, "low": 609.5, "close": 609.5, "volume": 20656474},
            {"timestamp": "2025-08-27", "open": 613.0, "high": 614.5, "low": 595.0, "close": 599.0, "volume": 21263402},
            {"timestamp": "2025-08-28", "open": 595.0, "high": 599.0, "low": 590.0, "close": 594.0, "volume": 21712370},
            {"timestamp": "2025-08-29", "open": 595.5, "high": 605.0, "low": 594.0, "close": 596.5, "volume": 18234935},
            {"timestamp": "2025-09-01", "open": 605.0, "high": 610.0, "low": 601.5, "close": 605.0, "volume": 15958837},
            {"timestamp": "2025-09-02", "open": 605.5, "high": 608.5, "low": 599.0, "close": 600.5, "volume": 14808157},
            {"timestamp": "2025-09-03", "open": 606.5, "high": 613.0, "low": 596.0, "close": 598.5, "volume": 15523985},
            {"timestamp": "2025-09-04", "open": 605.0, "high": 605.0, "low": 591.0, "close": 592.5, "volume": 18003934},
            {"timestamp": "2025-09-05", "open": 599.5, "high": 609.0, "low": 595.5, "close": 605.5, "volume": 19047729},
            {"timestamp": "2025-09-08", "open": 605.5, "high": 619.0, "low": 605.0, "close": 617.5, "volume": 21815489},
            {"timestamp": "2025-09-09", "open": 620.0, "high": 628.0, "low": 617.5, "close": 627.0, "volume": 19871460},
            {"timestamp": "2025-09-10", "open": 630.0, "high": 639.0, "low": 628.0, "close": 633.5, "volume": 19193376},
            {"timestamp": "2025-09-11", "open": 633.0, "high": 633.0, "low": 624.0, "close": 629.5, "volume": 18191860},
            {"timestamp": "2025-09-12", "open": 645.0, "high": 649.0, "low": 642.0, "close": 643.5, "volume": 20780375},
            {"timestamp": "2025-09-15", "open": 646.0, "high": 648.5, "low": 637.5, "close": 643.5, "volume": 16371242},
            {"timestamp": "2025-09-16", "open": 647.0, "high": 649.5, "low": 640.5, "close": 645.0, "volume": 13339685},
            {"timestamp": "2025-09-17", "open": 646.5, "high": 663.5, "low": 645.0, "close": 661.5, "volume": 22349048},
            {"timestamp": "2025-09-18", "open": 662.0, "high": 664.5, "low": 635.5, "close": 642.0, "volume": 29989898},
            {"timestamp": "2025-09-19", "open": 647.0, "high": 647.0, "low": 638.0, "close": 642.5, "volume": 20805608},
            {"timestamp": "2025-09-22", "open": 642.0, "high": 643.5, "low": 634.0, "close": 641.0, "volume": 12899662},
            {"timestamp": "2025-09-23", "open": 641.5, "high": 643.5, "low": 627.0, "close": 635.5, "volume": 15293080},
            {"timestamp": "2025-09-24", "open": 633.5, "high": 651.0, "low": 628.0, "close": 648.5, "volume": 18440788},
            {"timestamp": "2025-09-25", "open": 651.0, "high": 659.0, "low": 643.5, "close": 650.0, "volume": 17384258},
            {"timestamp": "2025-09-26", "open": 645.0, "high": 653.0, "low": 640.0, "close": 644.0, "volume": 19504951}
        ]
        
        # 轉換為DataFrame以便分析
        self.df = pd.DataFrame(self.historical_data)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values('timestamp')
        
    def calculate_technical_indicators(self):
        """計算技術指標"""
        # 計算移動平均線
        self.df['MA5'] = self.df['close'].rolling(window=5).mean()
        self.df['MA10'] = self.df['close'].rolling(window=10).mean()
        self.df['MA20'] = self.df['close'].rolling(window=20).mean()
        
        # 計算日收益率
        self.df['daily_return'] = self.df['close'].pct_change()
        
        # 計算波動率(20日滾動標準差)
        self.df['volatility'] = self.df['daily_return'].rolling(window=20).std() * np.sqrt(252)
        
        # 計算RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        
        # 計算布林帶
        self.df['BB_middle'] = self.df['close'].rolling(window=20).mean()
        bb_std = self.df['close'].rolling(window=20).std()
        self.df['BB_upper'] = self.df['BB_middle'] + (bb_std * 2)
        self.df['BB_lower'] = self.df['BB_middle'] - (bb_std * 2)
        
    def analyze_price_trend(self):
        """分析價格趨勢"""
        latest_data = self.df.tail(10)
        
        # 短期趨勢分析
        short_trend = "上升" if latest_data['close'].iloc[-1] > latest_data['close'].iloc[-5] else "下降"
        
        # 中期趨勢分析
        medium_trend = "上升" if latest_data['close'].iloc[-1] > self.df['MA20'].iloc[-1] else "下降"
        
        # 價格位置分析
        current_price = self.stock_info['current_price']
        price_position = (current_price - self.stock_info['low_30d']) / (self.stock_info['high_30d'] - self.stock_info['low_30d'])
        
        return {
            "short_term_trend": short_trend,
            "medium_term_trend": medium_trend,
            "price_position_in_range": round(price_position * 100, 2),
            "current_vs_ma5": round((current_price / self.df['MA5'].iloc[-1] - 1) * 100, 2),
            "current_vs_ma20": round((current_price / self.df['MA20'].iloc[-1] - 1) * 100, 2)
        }
    
    def analyze_volume_pattern(self):
        """分析成交量模式"""
        recent_volumes = self.df['volume'].tail(10)
        avg_volume = self.stock_info['avg_volume_30d']
        
        # 近期成交量趨勢
        volume_trend = "增加" if recent_volumes.mean() > avg_volume else "減少"
        
        # 成交量與價格關係
        price_volume_correlation = self.df['close'].tail(20).corr(self.df['volume'].tail(20))
        
        return {
            "volume_trend": volume_trend,
            "recent_avg_volume": int(recent_volumes.mean()),
            "volume_vs_30d_avg": round((recent_volumes.mean() / avg_volume - 1) * 100, 2),
            "price_volume_correlation": round(price_volume_correlation, 3)
        }
    
    def assess_volatility_risk(self):
        """評估波動性和風險"""
        # 計算歷史波動率
        daily_returns = self.df['daily_return'].dropna()
        volatility_annual = daily_returns.std() * np.sqrt(252)
        
        # VaR計算(95%信心水準)
        var_95 = np.percentile(daily_returns, 5)
        
        # 最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        return {
            "annual_volatility": round(volatility_annual * 100, 2),
            "var_95_daily": round(var_95 * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "risk_level": self._classify_risk(volatility_annual)
        }
    
    def _classify_risk(self, volatility):
        """風險等級分類"""
        if volatility < 0.15:
            return "低風險"
        elif volatility < 0.25:
            return "中等風險"
        elif volatility < 0.35:
            return "中高風險"
        else:
            return "高風險"
    
    def analyze_market_momentum(self):
        """分析市場動能"""
        latest_rsi = self.df['RSI'].iloc[-1] if not pd.isna(self.df['RSI'].iloc[-1]) else 50
        
        # 布林帶位置
        current_price = self.stock_info['current_price']
        bb_upper = self.df['BB_upper'].iloc[-1]
        bb_lower = self.df['BB_lower'].iloc[-1]
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if not pd.isna(bb_upper) else 0.5
        
        # 動量評分
        momentum_score = self._calculate_momentum_score()
        
        return {
            "rsi": round(latest_rsi, 2),
            "rsi_signal": self._interpret_rsi(latest_rsi),
            "bollinger_position": round(bb_position * 100, 2),
            "momentum_score": momentum_score,
            "momentum_signal": self._interpret_momentum(momentum_score)
        }
    
    def _calculate_momentum_score(self):
        """計算動量評分"""
        score = 0
        
        # 價格趨勢評分
        if self.stock_info['price_change_pct'] > 5:
            score += 30
        elif self.stock_info['price_change_pct'] > 2:
            score += 20
        elif self.stock_info['price_change_pct'] > 0:
            score += 10
        
        # 成交量評分
        recent_volume = self.df['volume'].tail(5).mean()
        if recent_volume > self.stock_info['avg_volume_30d'] * 1.2:
            score += 20
        elif recent_volume > self.stock_info['avg_volume_30d']:
            score += 10
        
        # 技術指標評分
        if not pd.isna(self.df['RSI'].iloc[-1]):
            rsi = self.df['RSI'].iloc[-1]
            if 40 <= rsi <= 60:
                score += 10
            elif 30 <= rsi <= 70:
                score += 5
        
        return min(score, 100)
    
    def _interpret_rsi(self, rsi):
        """解讀RSI信號"""
        if rsi > 70:
            return "超買"
        elif rsi < 30:
            return "超賣"
        else:
            return "中性"
    
    def _interpret_momentum(self, score):
        """解讀動量信號"""
        if score >= 70:
            return "強勢"
        elif score >= 50:
            return "中性偏強"
        elif score >= 30:
            return "中性"
        else:
            return "弱勢"
    
    def generate_investment_recommendation(self):
        """生成投資建議"""
        trend_analysis = self.analyze_price_trend()
        volume_analysis = self.analyze_volume_pattern()
        risk_assessment = self.assess_volatility_risk()
        momentum_analysis = self.analyze_market_momentum()
        
        # 綜合評分
        total_score = 0
        
        # 趨勢評分
        if trend_analysis['short_term_trend'] == "上升":
            total_score += 25
        if trend_analysis['medium_term_trend'] == "上升":
            total_score += 25
        
        # 動量評分
        total_score += momentum_analysis['momentum_score'] * 0.3
        
        # 風險調整
        if risk_assessment['risk_level'] == "高風險":
            total_score -= 10
        elif risk_assessment['risk_level'] == "低風險":
            total_score += 5
        
        # 生成建議
        recommendation = self._generate_recommendation(total_score)
        
        return {
            "overall_score": round(total_score, 1),
            "recommendation": recommendation,
            "confidence_level": self._calculate_confidence(total_score),
            "key_factors": self._identify_key_factors(trend_analysis, momentum_analysis, risk_assessment)
        }
    
    def _generate_recommendation(self, score):
        """根據評分生成建議"""
        if score >= 80:
            return "強烈買入"
        elif score >= 65:
            return "買入"
        elif score >= 50:
            return "持有"
        elif score >= 35:
            return "觀望"
        else:
            return "減持"
    
    def _calculate_confidence(self, score):
        """計算信心水準"""
        if score >= 80 or score <= 20:
            return "高"
        elif score >= 65 or score <= 35:
            return "中"
        else:
            return "低"
    
    def _identify_key_factors(self, trend, momentum, risk):
        """識別關鍵因素"""
        factors = []
        
        if trend['short_term_trend'] == "上升":
            factors.append("短期趨勢向上")
        
        if momentum['momentum_score'] > 60:
            factors.append("動能強勁")
        
        if risk['risk_level'] in ["低風險", "中等風險"]:
            factors.append("風險可控")
        
        if self.stock_info['price_change_pct'] > 5:
            factors.append("近期表現強勢")
        
        return factors
    
    def estimate_expected_returns(self):
        """預期收益評估"""
        # 基於歷史數據計算預期收益
        daily_returns = self.df['daily_return'].dropna()
        
        # 短期預期(1個月)
        short_term_return = daily_returns.tail(20).mean() * 20
        
        # 中期預期(3個月)
        medium_term_return = daily_returns.mean() * 60
        
        # 考慮當前動量調整
        momentum_analysis = self.analyze_market_momentum()
        momentum_multiplier = 1 + (momentum_analysis['momentum_score'] - 50) / 100
        
        return {
            "expected_return_1m": round(short_term_return * momentum_multiplier * 100, 2),
            "expected_return_3m": round(medium_term_return * momentum_multiplier * 100, 2),
            "upside_potential": round(((self.stock_info['high_30d'] / self.stock_info['current_price']) - 1) * 100, 2),
            "downside_risk": round(((self.stock_info['low_30d'] / self.stock_info['current_price']) - 1) * 100, 2)
        }
    
    def generate_comprehensive_analysis(self):
        """生成綜合分析報告"""
        # 更新TODO狀態
        print("正在進行綜合fundamental分析...")
        
        # 計算技術指標
        self.calculate_technical_indicators()
        
        # 執行各項分析
        trend_analysis = self.analyze_price_trend()
        volume_analysis = self.analyze_volume_pattern()
        risk_assessment = self.assess_volatility_risk()
        momentum_analysis = self.analyze_market_momentum()
        investment_rec = self.generate_investment_recommendation()
        expected_returns = self.estimate_expected_returns()
        
        # 生成綜合報告
        analysis_report = {
            "股票基本信息": {
                "股票代碼": self.stock_info['symbol'],
                "公司名稱": self.stock_info['company_name'],
                "當前價格": self.stock_info['current_price'],
                "價格變化": f"{self.stock_info['price_change']} ({self.stock_info['price_change_pct']}%)",
                "30日高低": f"{self.stock_info['high_30d']} / {self.stock_info['low_30d']}",
                "分析日期": datetime.now().strftime("%Y-%m-%d")
            },
            
            "詳細分析過程": {
                "價格趨勢分析": {
                    "短期趨勢": trend_analysis['short_term_trend'],
                    "中期趨勢": trend_analysis['medium_term_trend'],
                    "價格位置": f"{trend_analysis['price_position_in_range']}%",
                    "相對MA5": f"{trend_analysis['current_vs_ma5']}%",
                    "相對MA20": f"{trend_analysis['current_vs_ma20']}%"
                },
                
                "成交量分析": {
                    "成交量趨勢": volume_analysis['volume_trend'],
                    "近期平均成交量": volume_analysis['recent_avg_volume'],
                    "相對30日平均": f"{volume_analysis['volume_vs_30d_avg']}%",
                    "價量相關性": volume_analysis['price_volume_correlation']
                },
                
                "市場動能分析": {
                    "RSI指標": momentum_analysis['rsi'],
                    "RSI信號": momentum_analysis['rsi_signal'],
                    "布林帶位置": f"{momentum_analysis['bollinger_position']}%",
                    "動量評分": momentum_analysis['momentum_score'],
                    "動量信號": momentum_analysis['momentum_signal']
                }
            },
            
            "風險評估": {
                "年化波動率": f"{risk_assessment['annual_volatility']}%",
                "風險等級": risk_assessment['risk_level'],
                "日VaR(95%)": f"{risk_assessment['var_95_daily']}%",
                "最大回撤": f"{risk_assessment['max_drawdown']}%",
                "風險控制建議": self._generate_risk_advice(risk_assessment)
            },
            
            "投資建議": {
                "綜合評分": investment_rec['overall_score'],
                "投資建議": investment_rec['recommendation'],
                "信心水準": investment_rec['confidence_level'],
                "關鍵支撐因素": investment_rec['key_factors'],
                "建議持倉比例": self._suggest_position_size(investment_rec, risk_assessment)
            },
            
            "預期收益評估": {
                "1個月預期收益": f"{expected_returns['expected_return_1m']}%",
                "3個月預期收益": f"{expected_returns['expected_return_3m']}%",
                "上漲空間": f"{expected_returns['upside_potential']}%",
                "下跌風險": f"{expected_returns['downside_risk']}%",
                "風險收益比": round(abs(expected_returns['upside_potential'] / expected_returns['downside_risk']), 2) if expected_returns['downside_risk'] != 0 else "N/A"
            },
            
            "專業建議": {
                "進場時機": self._assess_entry_timing(trend_analysis, momentum_analysis),
                "止損建議": self._suggest_stop_loss(),
                "目標價位": self._calculate_target_price(expected_returns),
                "注意事項": self._generate_warnings(risk_assessment, momentum_analysis)
            }
        }
        
        return analysis_report
    
    def _generate_risk_advice(self, risk_assessment):
        """生成風險控制建議"""
        if risk_assessment['risk_level'] == "高風險":
            return "建議嚴格控制倉位，設置較緊的止損"
        elif risk_assessment['risk_level'] == "中高風險":
            return "適中倉位，密切關注市場變化"
        elif risk_assessment['risk_level'] == "中等風險":
            return "正常倉位配置，定期檢視"
        else:
            return "風險相對較低，可適當增加配置"
    
    def _suggest_position_size(self, investment_rec, risk_assessment):
        """建議持倉比例"""
        base_size = 0.1  # 基礎10%
        
        # 根據投資建議調整
        if investment_rec['recommendation'] == "強烈買入":
            base_size = 0.15
        elif investment_rec['recommendation'] == "買入":
            base_size = 0.12
        elif investment_rec['recommendation'] == "觀望":
            base_size = 0.05
        elif investment_rec['recommendation'] == "減持":
            base_size = 0.02
        
        # 根據風險調整
        if risk_assessment['risk_level'] == "高風險":
            base_size *= 0.7
        elif risk_assessment['risk_level'] == "低風險":
            base_size *= 1.2
        
        return f"{round(base_size * 100, 1)}%"
    
    def _assess_entry_timing(self, trend, momentum):
        """評估進場時機"""
        if trend['short_term_trend'] == "上升" and momentum['momentum_score'] > 60:
            return "良好，趨勢和動能均支持"
        elif trend['short_term_trend'] == "上升":
            return "尚可，但需關注動能變化"
        elif momentum['momentum_score'] > 60:
            return "謹慎樂觀，動能良好但趨勢需確認"
        else:
            return "建議等待更好時機"
    
    def _suggest_stop_loss(self):
        """建議止損位"""
        current_price = self.stock_info['current_price']
        support_level = self.stock_info['low_30d']
        
        # 基於ATR的止損
        atr_stop = current_price * 0.95  # 5% ATR止損
        support_stop = support_level * 1.02  # 支撐位上方2%
        
        return f"{max(atr_stop, support_stop):.2f} (約{round((1 - max(atr_stop, support_stop)/current_price) * 100, 1)}%)"
    
    def _calculate_target_price(self, expected_returns):
        """計算目標價位"""
        current_price = self.stock_info['current_price']
        target_1m = current_price * (1 + expected_returns['expected_return_1m'] / 100)
        target_3m = current_price * (1 + expected_returns['expected_return_3m'] / 100)
        
        return {
            "1個月目標": f"{target_1m:.2f}",
            "3個月目標": f"{target_3m:.2f}"
        }
    
    def _generate_warnings(self, risk_assessment, momentum_analysis):
        """生成注意事項"""
        warnings = []
        
        if risk_assessment['annual_volatility'] > 30:
            warnings.append("股價波動較大，注意風險控制")
        
        if momentum_analysis['rsi'] > 70:
            warnings.append("RSI顯示超買，注意回調風險")
        
        if momentum_analysis['rsi'] < 30:
            warnings.append("RSI顯示超賣，可能存在反彈機會")
        
        if self.stock_info['price_change_pct'] > 10:
            warnings.append("短期漲幅較大，注意獲利了結")
        
        if not warnings:
            warnings.append("暫無特殊風險提示")
        
        return warnings


def main():
    """主函數"""
    print("=== 騰訊控股(0700.HK) Fundamental分析 ===")
    
    # 創建分析實例
    analyzer = TencentFundamentalAnalysis()
    
    # 生成綜合分析報告
    report = analyzer.generate_comprehensive_analysis()
    
    # 輸出JSON格式報告
    json_report = json.dumps(report, ensure_ascii=False, indent=2)
    
    # 保存到文件
    with open('/workspace/tencent_analysis_report.json', 'w', encoding='utf-8') as f:
        f.write(json_report)
    
    print("\n=== 分析報告 (JSON格式) ===")
    print(json_report)
    
    return report


if __name__ == "__main__":
    main()