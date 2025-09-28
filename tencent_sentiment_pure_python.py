#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股 (0700.HK) Sentiment Analysis - 純Python版本
專業量化分析報告生成器
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Tuple, Any

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
        self.processed_data = self._prepare_data()
        
    def _prepare_data(self) -> List[Dict]:
        """準備和處理數據"""
        processed = []
        
        for i, data in enumerate(self.historical_data):
            item = data.copy()
            
            # 計算日收益率
            if i > 0:
                prev_close = self.historical_data[i-1]['close']
                item['daily_return'] = (data['close'] - prev_close) / prev_close
            else:
                item['daily_return'] = 0
                
            # 計算價格波幅
            item['price_range'] = data['high'] - data['low']
            item['price_range_pct'] = (data['high'] - data['low']) / data['close'] * 100
            
            processed.append(item)
            
        # 計算移動平均
        for i in range(len(processed)):
            # 5日移動平均
            if i >= 4:
                ma5_sum = sum(processed[j]['close'] for j in range(i-4, i+1))
                processed[i]['price_ma5'] = ma5_sum / 5
            else:
                processed[i]['price_ma5'] = processed[i]['close']
                
            # 10日移動平均
            if i >= 9:
                ma10_sum = sum(processed[j]['close'] for j in range(i-9, i+1))
                processed[i]['price_ma10'] = ma10_sum / 10
            else:
                processed[i]['price_ma10'] = processed[i]['close']
                
            # 5日成交量移動平均
            if i >= 4:
                vol_ma5_sum = sum(processed[j]['volume'] for j in range(i-4, i+1))
                processed[i]['volume_ma5'] = vol_ma5_sum / 5
            else:
                processed[i]['volume_ma5'] = processed[i]['volume']
                
        return processed
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """計算基本統計量"""
        n = len(values)
        if n == 0:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance)
        
        return {
            'mean': mean,
            'std': std,
            'min': min(values),
            'max': max(values)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """計算百分位數"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        index = percentile * (n - 1)
        
        if index == int(index):
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def analyze_price_trend(self) -> Dict[str, Any]:
        """分析價格趋势"""
        recent_5_days = self.processed_data[-5:]
        recent_10_days = self.processed_data[-10:]
        
        # 價格變化分析
        initial_price = self.processed_data[0]['close']
        price_change_30d = (self.current_price - initial_price) / initial_price * 100
        
        recent_5_start = recent_5_days[0]['close']
        price_change_5d = (self.current_price - recent_5_start) / recent_5_start * 100
        
        # 趨勢強度判斷
        latest_data = self.processed_data[-1]
        ma5_trend = "上升" if latest_data['close'] > latest_data['price_ma5'] else "下降"
        ma10_trend = "上升" if latest_data['close'] > latest_data['price_ma10'] else "下降"
        
        # 支撐和阻力位
        all_lows = [data['low'] for data in self.processed_data]
        all_highs = [data['high'] for data in self.processed_data]
        support_level = min(all_lows)
        resistance_level = max(all_highs)
        
        # 趨勢強度評估
        if price_change_5d > 3:
            trend_strength = "強勢"
        elif price_change_5d < -3:
            trend_strength = "弱勢"
        else:
            trend_strength = "中性"
        
        return {
            "price_change_30d": round(price_change_30d, 2),
            "price_change_5d": round(price_change_5d, 2),
            "ma5_trend": ma5_trend,
            "ma10_trend": ma10_trend,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "trend_strength": trend_strength
        }
    
    def analyze_volume_sentiment(self) -> Dict[str, Any]:
        """分析成交量情緒"""
        all_volumes = [data['volume'] for data in self.processed_data]
        recent_volumes = [data['volume'] for data in self.processed_data[-5:]]
        
        avg_volume = sum(all_volumes) / len(all_volumes)
        recent_avg_volume = sum(recent_volumes) / len(recent_volumes)
        volume_trend = (recent_avg_volume - avg_volume) / avg_volume * 100
        
        # 價量關係分析 - 計算相關係數
        prices = [data['close'] for data in self.processed_data[1:]]  # 排除第一天（沒有收益率）
        volumes = [data['volume'] for data in self.processed_data[1:]]
        
        # 簡化的相關係數計算
        n = len(prices)
        if n > 1:
            price_mean = sum(prices) / n
            volume_mean = sum(volumes) / n
            
            numerator = sum((prices[i] - price_mean) * (volumes[i] - volume_mean) for i in range(n))
            price_var = sum((p - price_mean) ** 2 for p in prices)
            volume_var = sum((v - volume_mean) ** 2 for v in volumes)
            
            if price_var > 0 and volume_var > 0:
                correlation = numerator / math.sqrt(price_var * volume_var)
            else:
                correlation = 0
        else:
            correlation = 0
        
        # 異常成交量天數
        high_volume_threshold = avg_volume * 1.5
        high_volume_days = sum(1 for vol in all_volumes if vol > high_volume_threshold)
        
        # 成交量情緒判斷
        if volume_trend > 15:
            volume_sentiment = "積極"
        elif volume_trend < -15:
            volume_sentiment = "消極"
        else:
            volume_sentiment = "中性"
        
        return {
            "average_volume": int(avg_volume),
            "recent_volume_trend": round(volume_trend, 2),
            "price_volume_correlation": round(correlation, 3),
            "high_volume_days": high_volume_days,
            "volume_sentiment": volume_sentiment
        }
    
    def calculate_volatility_risk(self) -> Dict[str, Any]:
        """計算波動性和風險指標"""
        daily_returns = [data['daily_return'] for data in self.processed_data[1:]]  # 排除第一天
        
        if not daily_returns:
            return {
                "annualized_volatility": 0,
                "var_95": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "risk_level": "低"
            }
        
        # 波動率計算（年化）
        returns_stats = self._calculate_statistics(daily_returns)
        volatility = returns_stats['std'] * math.sqrt(252) * 100
        
        # VaR計算 (95%置信區間)
        var_95 = self._percentile(daily_returns, 0.05) * 100
        
        # 最大回撤計算
        cumulative_returns = [1.0]
        for ret in daily_returns:
            cumulative_returns.append(cumulative_returns[-1] * (1 + ret))
        
        peak = cumulative_returns[0]
        max_drawdown = 0
        
        for value in cumulative_returns[1:]:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_pct = max_drawdown * 100
        
        # 夏普比率計算（假設無風險利率2%）
        risk_free_rate = 0.02
        mean_annual_return = returns_stats['mean'] * 252
        excess_return = mean_annual_return - risk_free_rate
        annual_volatility = returns_stats['std'] * math.sqrt(252)
        
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0
        
        # 風險等級評估
        if volatility > 35:
            risk_level = "高"
        elif volatility > 25:
            risk_level = "中"
        else:
            risk_level = "低"
        
        return {
            "annualized_volatility": round(volatility, 2),
            "var_95": round(var_95, 2),
            "max_drawdown": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "risk_level": risk_level
        }
    
    def sentiment_scoring(self) -> Dict[str, Any]:
        """綜合情緒評分"""
        price_analysis = self.analyze_price_trend()
        volume_analysis = self.analyze_volume_sentiment()
        risk_analysis = self.calculate_volatility_risk()
        
        # 價格評分 (0-100)
        price_change_5d = price_analysis["price_change_5d"]
        if price_change_5d > 5:
            price_score = 85
        elif price_change_5d > 2:
            price_score = 70
        elif price_change_5d > -2:
            price_score = 50
        elif price_change_5d > -5:
            price_score = 30
        else:
            price_score = 15
            
        # 成交量評分
        volume_sentiment = volume_analysis["volume_sentiment"]
        if volume_sentiment == "積極":
            volume_score = 75
        elif volume_sentiment == "消極":
            volume_score = 25
        else:
            volume_score = 50
            
        # 風險調整
        risk_level = risk_analysis["risk_level"]
        if risk_level == "高":
            risk_penalty = 15
        elif risk_level == "中":
            risk_penalty = 8
        else:
            risk_penalty = 0
            
        # 綜合評分
        overall_sentiment_score = max(0, min(100, (price_score + volume_score) / 2 - risk_penalty))
        
        # 情緒水平判斷
        if overall_sentiment_score > 80:
            sentiment_level = "非常樂觀"
        elif overall_sentiment_score > 65:
            sentiment_level = "樂觀"
        elif overall_sentiment_score > 35:
            sentiment_level = "中性"
        elif overall_sentiment_score > 20:
            sentiment_level = "悲觀"
        else:
            sentiment_level = "非常悲觀"
        
        return {
            "price_score": price_score,
            "volume_score": volume_score,
            "risk_penalty": risk_penalty,
            "overall_sentiment_score": round(overall_sentiment_score, 1),
            "sentiment_level": sentiment_level
        }
    
    def generate_investment_advice(self) -> Dict[str, Any]:
        """生成投資建議"""
        sentiment = self.sentiment_scoring()
        price_analysis = self.analyze_price_trend()
        risk_analysis = self.calculate_volatility_risk()
        
        sentiment_score = sentiment["overall_sentiment_score"]
        
        # 投資建議邏輯
        if sentiment_score > 70:
            action = "買入"
            confidence = "高"
            target_multiplier = 1.08
            stop_multiplier = 0.95
        elif sentiment_score > 50:
            action = "持有"
            confidence = "中"
            target_multiplier = 1.05
            stop_multiplier = 0.97
        else:
            action = "觀望"
            confidence = "低"
            target_multiplier = 1.02
            stop_multiplier = 0.92
            
        target_price = self.current_price * target_multiplier
        stop_loss = self.current_price * stop_multiplier
        
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
        daily_returns = [data['daily_return'] for data in self.processed_data[1:]]
        
        if not daily_returns:
            return {
                "expected_annual_return": 0,
                "win_rate": 50,
                "return_scenarios": {},
                "risk_adjusted_return": 0
            }
        
        returns_stats = self._calculate_statistics(daily_returns)
        mean_daily_return = returns_stats['mean']
        std_daily = returns_stats['std']
        
        # 預期年化收益率
        expected_annual_return = mean_daily_return * 252 * 100
        
        # 勝率計算
        positive_days = sum(1 for ret in daily_returns if ret > 0)
        win_rate = positive_days / len(daily_returns) * 100
        
        # 情境分析
        scenarios = {
            "樂觀情境 (75%)": round((mean_daily_return + std_daily) * 252 * 100, 2),
            "基準情境 (50%)": round(expected_annual_return, 2),
            "悲觀情境 (25%)": round((mean_daily_return - std_daily) * 252 * 100, 2)
        }
        
        # 風險調整收益
        annual_volatility = std_daily * math.sqrt(252) * 100
        risk_adjusted_return = expected_annual_return / annual_volatility if annual_volatility > 0 else 0
        
        return {
            "expected_annual_return": round(expected_annual_return, 2),
            "win_rate": round(win_rate, 1),
            "return_scenarios": scenarios,
            "risk_adjusted_return": round(risk_adjusted_return, 3)
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
                "價格趨勢": f"30天累計漲幅{price_trend['price_change_30d']}%，近5天漲幅{price_trend['price_change_5d']}%",
                "移動平均線": f"5日均線呈{price_trend['ma5_trend']}趨勢，10日均線呈{price_trend['ma10_trend']}趨勢",
                "支撐阻力位": f"關鍵支撐位{price_trend['support_level']}港元，阻力位{price_trend['resistance_level']}港元",
                "趨勢強度": price_trend['trend_strength']
            },
            "成交量分析": {
                "成交量變化": f"近期成交量較30天平均水平{volume_sentiment['recent_volume_trend']:+.1f}%",
                "價量關係": f"價格與成交量相關係數為{volume_sentiment['price_volume_correlation']}",
                "市場參與度": f"共有{volume_sentiment['high_volume_days']}天出現異常放量",
                "成交量情緒": volume_sentiment['volume_sentiment']
            },
            "風險評估": {
                "波動率水平": f"年化波動率{risk_metrics['annualized_volatility']}%，屬於{risk_metrics['risk_level']}風險水平",
                "下行風險": f"95%置信區間的日最大損失為{risk_metrics['var_95']}%",
                "最大回撤": f"30天期間最大回撤{risk_metrics['max_drawdown']}%",
                "風險調整收益": f"夏普比率{risk_metrics['sharpe_ratio']}"
            },
            "情緒綜合評估": {
                "技術面評分": f"{sentiment_score['price_score']}/100分",
                "成交量評分": f"{sentiment_score['volume_score']}/100分",
                "風險調整": f"扣除{sentiment_score['risk_penalty']}分風險溢價",
                "綜合情緒評分": f"{sentiment_score['overall_sentiment_score']}/100分",
                "市場情緒": sentiment_score['sentiment_level']
            }
        }
        
        return {
            "股票資訊": {
                "股票代碼": "0700.HK",
                "股票名稱": "騰訊控股",
                "當前價格": f"{self.current_price}港元",
                "分析日期": datetime.now().strftime("%Y年%m月%d日"),
                "數據期間": "30個交易日",
                "數據起始日": "2025年8月18日",
                "數據結束日": "2025年9月26日"
            },
            "詳細分析過程": analysis_process,
            "投資建議": {
                "推薦操作": investment_advice['recommended_action'],
                "信心水平": investment_advice['confidence_level'],
                "目標價位": f"{investment_advice['target_price']}港元",
                "止損價位": f"{investment_advice['stop_loss_price']}港元",
                "建議持有期": investment_advice['holding_period'],
                "倉位建議": investment_advice['position_sizing'],
                "操作理由": f"基於{sentiment_score['overall_sentiment_score']}/100的綜合情緒評分，當前市場情緒為{sentiment_score['sentiment_level']}"
            },
            "風險評估": {
                "整體風險等級": risk_metrics['risk_level'],
                "主要風險因素": [
                    "市場系統性風險：港股市場整體波動影響",
                    "行業風險：科技股估值波動和監管政策變化",
                    "個股風險：公司業績變化和競爭環境影響",
                    "流動性風險：大額交易可能面臨的衝擊成本",
                    "匯率風險：港元匯率波動對投資收益的影響"
                ],
                "量化風險指標": {
                    "年化波動率": f"{risk_metrics['annualized_volatility']}%",
                    "日均VaR(95%)": f"{risk_metrics['var_95']}%",
                    "最大歷史回撤": f"{risk_metrics['max_drawdown']}%",
                    "夏普比率": risk_metrics['sharpe_ratio'],
                    "風險等級評定": risk_metrics['risk_level']
                },
                "風險控制建議": [
                    "設置合理的止損位，建議不超過8-10%",
                    "分批建倉，避免一次性大額投入",
                    "密切關注宏觀經濟和行業政策變化",
                    "定期檢視投資組合，及時調整倉位"
                ]
            },
            "預期收益評估": {
                "預期年化收益率": f"{return_analysis['expected_annual_return']}%",
                "歷史勝率": f"{return_analysis['win_rate']}%",
                "收益情境分析": {
                    "樂觀情境": f"{return_analysis['return_scenarios']['樂觀情境 (75%)']}% (發生概率25%)",
                    "基準情境": f"{return_analysis['return_scenarios']['基準情境 (50%)']}% (發生概率50%)",
                    "悲觀情境": f"{return_analysis['return_scenarios']['悲觀情境 (25%)']}% (發生概率25%)"
                },
                "風險調整收益": return_analysis['risk_adjusted_return'],
                "收益評估說明": "基於30天歷史數據統計分析，實際收益可能因市場環境變化而有所差異"
            },
            "sentiment分析總結": {
                "綜合情緒評分": f"{sentiment_score['overall_sentiment_score']}/100分",
                "市場情緒水平": sentiment_score['sentiment_level'],
                "價格動能": price_trend['trend_strength'],
                "成交量情緒": volume_sentiment['volume_sentiment'],
                "技術面信號": f"5日均線{price_trend['ma5_trend']}，10日均線{price_trend['ma10_trend']}",
                "推薦操作": investment_advice['recommended_action'],
                "操作信心": investment_advice['confidence_level'],
                "關鍵支撐位": f"{price_trend['support_level']}港元",
                "關鍵阻力位": f"{price_trend['resistance_level']}港元",
                "分析師建議": f"當前騰訊控股呈現{sentiment_score['sentiment_level']}的市場情緒，建議{investment_advice['recommended_action']}，目標價位{investment_advice['target_price']}港元"
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
    
    print("\n" + "="*80)
    print("騰訊控股(0700.HK) Sentiment分析報告已生成完成")
    print("="*80)
    print(f"報告文件已保存至: /workspace/tencent_sentiment_report.json")
    print(f"分析日期: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()