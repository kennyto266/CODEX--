#!/usr/bin/env python3
"""
騰訊控股 (0700.HK) Sentiment 分析工具
專業量化分析系統 - 情緒分析代理
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

class TencentSentimentAnalyzer:
    def __init__(self):
        self.symbol = "0700.HK"
        self.company_name = "騰訊控股"
        
    def load_data(self, data: List[Dict]) -> List[Dict]:
        """載入並處理歷史數據"""
        # 按時間排序
        sorted_data = sorted(data, key=lambda x: x['timestamp'])
        
        # 計算技術指標
        for i in range(len(sorted_data)):
            if i > 0:
                prev_close = sorted_data[i-1]['close']
                current_close = sorted_data[i]['close']
                sorted_data[i]['daily_return'] = (current_close - prev_close) / prev_close
            else:
                sorted_data[i]['daily_return'] = 0
                
            sorted_data[i]['price_range'] = sorted_data[i]['high'] - sorted_data[i]['low']
        
        return sorted_data
    
    def calculate_moving_average(self, data: List[Dict], window: int, field: str = 'close') -> List[float]:
        """計算移動平均線"""
        ma_values = []
        for i in range(len(data)):
            if i < window - 1:
                ma_values.append(None)
            else:
                window_sum = sum(data[j][field] for j in range(i - window + 1, i + 1))
                ma_values.append(window_sum / window)
        return ma_values
    
    def calculate_rsi(self, data: List[Dict], window: int = 14) -> List[float]:
        """計算RSI指標"""
        rsi_values = []
        
        for i in range(len(data)):
            if i < window:
                rsi_values.append(None)
            else:
                gains = []
                losses = []
                
                for j in range(i - window + 1, i + 1):
                    daily_return = data[j]['daily_return']
                    if daily_return > 0:
                        gains.append(daily_return)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(daily_return))
                
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                
                if avg_loss == 0:
                    rsi_values.append(100)
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    rsi_values.append(rsi)
        
        return rsi_values
    
    def calculate_macd(self, data: List[Dict]) -> Tuple[List[float], List[float], List[float]]:
        """計算MACD指標"""
        # 計算EMA
        def calculate_ema(prices, span):
            ema_values = []
            multiplier = 2 / (span + 1)
            
            for i, price in enumerate(prices):
                if i == 0:
                    ema_values.append(price)
                else:
                    ema = (price * multiplier) + (ema_values[-1] * (1 - multiplier))
                    ema_values.append(ema)
            return ema_values
        
        prices = [item['close'] for item in data]
        ema12 = calculate_ema(prices, 12)
        ema26 = calculate_ema(prices, 26)
        
        macd_line = [ema12[i] - ema26[i] for i in range(len(prices))]
        signal_line = calculate_ema(macd_line, 9)
        histogram = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, data: List[Dict], window: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """計算布林帶"""
        prices = [item['close'] for item in data]
        middle_band = self.calculate_moving_average(data, window, 'close')
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < window - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                window_prices = prices[i - window + 1:i + 1]
                mean_price = sum(window_prices) / len(window_prices)
                variance = sum((p - mean_price) ** 2 for p in window_prices) / len(window_prices)
                std = math.sqrt(variance)
                
                upper_band.append(mean_price + (std_dev * std))
                lower_band.append(mean_price - (std_dev * std))
        
        return upper_band, middle_band, lower_band
    
    def calculate_technical_indicators(self, data: List[Dict]) -> List[Dict]:
        """計算技術指標"""
        # 移動平均線
        ma5 = self.calculate_moving_average(data, 5)
        ma10 = self.calculate_moving_average(data, 10)
        ma20 = self.calculate_moving_average(data, 20)
        
        # RSI
        rsi = self.calculate_rsi(data)
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(data)
        
        # 布林帶
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data)
        
        # 添加指標到數據中
        for i in range(len(data)):
            data[i]['ma5'] = ma5[i]
            data[i]['ma10'] = ma10[i]
            data[i]['ma20'] = ma20[i]
            data[i]['rsi'] = rsi[i]
            data[i]['macd'] = macd_line[i]
            data[i]['macd_signal'] = signal_line[i]
            data[i]['macd_histogram'] = histogram[i]
            data[i]['bb_upper'] = bb_upper[i]
            data[i]['bb_middle'] = bb_middle[i]
            data[i]['bb_lower'] = bb_lower[i]
            
            # 布林帶位置
            if bb_upper[i] and bb_lower[i]:
                data[i]['bb_position'] = (data[i]['close'] - bb_lower[i]) / (bb_upper[i] - bb_lower[i])
            else:
                data[i]['bb_position'] = None
        
        return data
    
    def analyze_volume_sentiment(self, data: List[Dict]) -> Dict[str, Any]:
        """成交量情緒分析"""
        volumes = [item['volume'] for item in data]
        recent_volume = sum(volumes[-5:]) / 5
        avg_volume = sum(volumes) / len(volumes)
        volume_ratio = recent_volume / avg_volume
        
        # 價量關係分析
        returns = [item['daily_return'] for item in data if item['daily_return'] != 0]
        volume_changes = []
        for i in range(1, len(volumes)):
            volume_changes.append((volumes[i] - volumes[i-1]) / volumes[i-1])
        
        # 計算相關係數
        if len(returns) > 1 and len(volume_changes) > 1:
            min_len = min(len(returns), len(volume_changes))
            returns = returns[-min_len:]
            volume_changes = volume_changes[-min_len:]
            
            mean_returns = sum(returns) / len(returns)
            mean_volume_changes = sum(volume_changes) / len(volume_changes)
            
            numerator = sum((returns[i] - mean_returns) * (volume_changes[i] - mean_volume_changes) for i in range(min_len))
            sum_sq_returns = sum((r - mean_returns) ** 2 for r in returns)
            sum_sq_volume = sum((v - mean_volume_changes) ** 2 for v in volume_changes)
            
            if sum_sq_returns > 0 and sum_sq_volume > 0:
                correlation = numerator / math.sqrt(sum_sq_returns * sum_sq_volume)
            else:
                correlation = 0
        else:
            correlation = 0
        
        volume_sentiment = {
            "recent_volume_avg": int(recent_volume),
            "overall_volume_avg": int(avg_volume),
            "volume_ratio": round(volume_ratio, 2),
            "price_volume_correlation": round(correlation, 3),
            "volume_trend": "上升" if volume_ratio > 1.1 else "下降" if volume_ratio < 0.9 else "平穩"
        }
        
        return volume_sentiment
    
    def analyze_price_momentum(self, data: List[Dict]) -> Dict[str, Any]:
        """價格動能分析"""
        latest = data[-1]
        
        # 短期趨勢
        ma5_trend = "上升" if latest['close'] > (latest['ma5'] or 0) else "下降"
        ma10_trend = "上升" if latest['close'] > (latest['ma10'] or 0) else "下降"
        ma20_trend = "上升" if latest['close'] > (latest['ma20'] or 0) else "下降"
        
        # RSI 情緒
        rsi_value = latest['rsi'] or 50
        if rsi_value > 70:
            rsi_sentiment = "超買"
        elif rsi_value < 30:
            rsi_sentiment = "超賣"
        else:
            rsi_sentiment = "中性"
        
        # MACD 信號
        macd_signal = "看多" if (latest['macd'] or 0) > (latest['macd_signal'] or 0) else "看空"
        
        # 布林帶位置
        bb_pos = latest['bb_position'] or 0.5
        if bb_pos > 0.8:
            bb_sentiment = "接近上軌"
        elif bb_pos < 0.2:
            bb_sentiment = "接近下軌"
        else:
            bb_sentiment = "中軌附近"
        
        momentum = {
            "ma5_trend": ma5_trend,
            "ma10_trend": ma10_trend,
            "ma20_trend": ma20_trend,
            "rsi_value": round(rsi_value, 2),
            "rsi_sentiment": rsi_sentiment,
            "macd_signal": macd_signal,
            "bollinger_position": round(bb_pos, 3),
            "bollinger_sentiment": bb_sentiment
        }
        
        return momentum
    
    def calculate_support_resistance(self, data: List[Dict]) -> Dict[str, float]:
        """計算支撐阻力位"""
        recent_data = data[-20:] if len(data) >= 20 else data
        
        # 支撐位：最近的低點
        lows = [item['low'] for item in recent_data]
        support_levels = sorted(lows)[:3]
        
        # 阻力位：最近的高點
        highs = [item['high'] for item in recent_data]
        resistance_levels = sorted(highs, reverse=True)[:3]
        
        return {
            "primary_support": min(support_levels),
            "secondary_support": support_levels[1] if len(support_levels) > 1 else min(support_levels),
            "primary_resistance": max(resistance_levels),
            "secondary_resistance": resistance_levels[1] if len(resistance_levels) > 1 else max(resistance_levels)
        }
    
    def calculate_volatility_metrics(self, data: List[Dict]) -> Dict[str, float]:
        """計算波動率指標"""
        returns = [item['daily_return'] for item in data if item['daily_return'] != 0]
        
        if not returns:
            return {
                "historical_volatility": 0,
                "recent_volatility": 0,
                "value_at_risk_95": 0,
                "volatility_trend": "無法計算"
            }
        
        # 歷史波動率
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        historical_vol = math.sqrt(variance) * math.sqrt(252)  # 年化波動率
        
        # 近期波動率
        recent_returns = returns[-10:] if len(returns) >= 10 else returns
        recent_mean = sum(recent_returns) / len(recent_returns)
        recent_variance = sum((r - recent_mean) ** 2 for r in recent_returns) / len(recent_returns)
        recent_vol = math.sqrt(recent_variance) * math.sqrt(252)
        
        # VaR 計算 (95% 置信區間)
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = sorted_returns[var_index] if var_index < len(sorted_returns) else sorted_returns[0]
        
        return {
            "historical_volatility": round(historical_vol * 100, 2),
            "recent_volatility": round(recent_vol * 100, 2),
            "value_at_risk_95": round(var_95 * 100, 2),
            "volatility_trend": "上升" if recent_vol > historical_vol else "下降"
        }
    
    def generate_sentiment_score(self, data: List[Dict]) -> Dict[str, Any]:
        """生成綜合情緒評分"""
        latest = data[-1]
        
        # 技術面評分 (0-100)
        technical_score = 50  # 基準分
        
        # RSI 調整
        rsi_val = latest['rsi'] or 50
        if 30 <= rsi_val <= 70:
            technical_score += 10
        elif rsi_val > 80 or rsi_val < 20:
            technical_score -= 15
        
        # 移動平均線調整
        close = latest['close']
        ma5 = latest['ma5'] or close
        ma10 = latest['ma10'] or close
        ma20 = latest['ma20'] or close
        
        if close > ma5 > ma10 > ma20:
            technical_score += 20
        elif close < ma5 < ma10 < ma20:
            technical_score -= 20
        
        # MACD 調整
        macd = latest['macd'] or 0
        macd_signal = latest['macd_signal'] or 0
        macd_hist = latest['macd_histogram'] or 0
        
        if macd > macd_signal and macd_hist > 0:
            technical_score += 10
        elif macd < macd_signal and macd_hist < 0:
            technical_score -= 10
        
        # 布林帶調整
        bb_pos = latest['bb_position'] or 0.5
        if 0.2 <= bb_pos <= 0.8:
            technical_score += 5
        
        # 成交量調整
        volumes = [item['volume'] for item in data]
        recent_vol = sum(volumes[-5:]) / 5
        avg_vol = sum(volumes) / len(volumes)
        volume_ratio = recent_vol / avg_vol
        
        if volume_ratio > 1.2:
            technical_score += 5
        elif volume_ratio < 0.8:
            technical_score -= 5
        
        # 確保評分在 0-100 範圍內
        technical_score = max(0, min(100, technical_score))
        
        # 情緒標籤
        if technical_score >= 75:
            sentiment_label = "非常樂觀"
        elif technical_score >= 60:
            sentiment_label = "樂觀"
        elif technical_score >= 40:
            sentiment_label = "中性"
        elif technical_score >= 25:
            sentiment_label = "悲觀"
        else:
            sentiment_label = "非常悲觀"
        
        return {
            "technical_score": technical_score,
            "sentiment_label": sentiment_label,
            "confidence_level": min(95, max(60, technical_score + 10))
        }
    
    def generate_investment_recommendation(self, data: List[Dict], sentiment_score: Dict, support_resistance: Dict) -> Dict[str, Any]:
        """生成投資建議"""
        latest_price = data[-1]['close']
        score = sentiment_score['technical_score']
        
        if score >= 70:
            recommendation = "買入"
            target_price = latest_price * 1.08
            stop_loss = support_resistance['primary_support']
        elif score >= 55:
            recommendation = "持有"
            target_price = latest_price * 1.05
            stop_loss = support_resistance['secondary_support']
        elif score >= 35:
            recommendation = "觀望"
            target_price = latest_price * 1.02
            stop_loss = latest_price * 0.95
        else:
            recommendation = "減持"
            target_price = latest_price * 0.98
            stop_loss = latest_price * 0.92
        
        risk_reward = (target_price - latest_price) / (latest_price - stop_loss) if latest_price > stop_loss else 0
        
        return {
            "recommendation": recommendation,
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "holding_period": "1-3個月"
        }
    
    def assess_risks(self, data: List[Dict], volatility_metrics: Dict) -> Dict[str, Any]:
        """風險評估"""
        latest = data[-1]
        
        # 技術風險
        technical_risks = []
        rsi_val = latest['rsi'] or 50
        bb_pos = latest['bb_position'] or 0.5
        
        if rsi_val > 80:
            technical_risks.append("RSI超買，回調風險較高")
        if bb_pos > 0.9:
            technical_risks.append("價格接近布林帶上軌，存在回落風險")
        
        volumes = [item['volume'] for item in data]
        recent_vol = sum(volumes[-5:]) / 5
        avg_vol = sum(volumes) / len(volumes)
        
        if recent_vol > avg_vol * 1.5:
            technical_risks.append("成交量異常放大，需關注後續走勢")
        
        # 市場風險等級
        recent_volatility = volatility_metrics['recent_volatility']
        if recent_volatility > 30:
            risk_level = "高"
        elif recent_volatility > 20:
            risk_level = "中"
        else:
            risk_level = "低"
        
        return {
            "risk_level": risk_level,
            "technical_risks": technical_risks,
            "volatility_risk": f"{recent_volatility:.1f}% (年化)",
            "max_potential_loss": f"{abs(volatility_metrics['value_at_risk_95']):.1f}%",
            "liquidity_risk": "低" if avg_vol > 15000000 else "中"
        }
    
    def calculate_expected_returns(self, data: List[Dict], investment_rec: Dict) -> Dict[str, Any]:
        """預期收益評估"""
        latest_price = data[-1]['close']
        target_price = investment_rec['target_price']
        
        # 基於目標價的預期收益
        expected_return = (target_price - latest_price) / latest_price * 100
        
        # 基於歷史數據的收益分析
        monthly_returns = []
        window_size = 20  # 約一個月的交易日
        
        for i in range(0, len(data) - window_size, window_size):
            if i + window_size < len(data):
                start_price = data[i]['close']
                end_price = data[i + window_size]['close']
                monthly_return = (end_price - start_price) / start_price
                monthly_returns.append(monthly_return)
        
        if monthly_returns:
            avg_monthly_return = sum(monthly_returns) / len(monthly_returns) * 100
            mean_return = sum(monthly_returns) / len(monthly_returns)
            return_variance = sum((r - mean_return) ** 2 for r in monthly_returns) / len(monthly_returns)
            return_volatility = math.sqrt(return_variance) * 100
        else:
            avg_monthly_return = 0
            return_volatility = 0
        
        sharpe_ratio = avg_monthly_return / return_volatility if return_volatility > 0 else 0
        
        return {
            "target_return": round(expected_return, 2),
            "probability_of_profit": max(50, min(85, 60 + expected_return)),
            "average_monthly_return": round(avg_monthly_return, 2),
            "return_volatility": round(return_volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2)
        }
    
    def _generate_reasoning(self, sentiment_score: Dict, momentum: Dict, volume_sentiment: Dict) -> str:
        """生成操作理由"""
        score = sentiment_score['technical_score']
        reasons = []
        
        if score >= 70:
            reasons.append(f"技術面評分達到{score}分，顯示強勢")
            if momentum['rsi_value'] < 70:
                reasons.append("RSI未進入超買區間，仍有上漲空間")
            if volume_sentiment['volume_ratio'] > 1.1:
                reasons.append("成交量放大支持價格上漲")
        elif score >= 55:
            reasons.append("技術指標整體偏正面")
            reasons.append("建議持有等待更明確信號")
        elif score >= 35:
            reasons.append("技術面信號混合")
            reasons.append("建議觀望等待方向明確")
        else:
            reasons.append(f"技術面評分僅{score}分，顯示弱勢")
            reasons.append("建議降低持倉風險")
        
        return "；".join(reasons)
    
    def _generate_short_term_outlook(self, sentiment_score: Dict) -> str:
        """生成短期展望"""
        score = sentiment_score['technical_score']
        if score >= 65:
            return "短期技術面偏強，預期繼續上漲，但需注意回調風險"
        elif score >= 45:
            return "短期走勢可能震盪整理，等待方向選擇"
        else:
            return "短期技術面偏弱，存在進一步下跌風險"
    
    def _generate_medium_term_outlook(self, data: List[Dict], sentiment_score: Dict) -> str:
        """生成中期展望"""
        if len(data) >= 20:
            trend_strength = abs(data[-1]['close'] - data[-20]['close']) / data[-20]['close']
        else:
            trend_strength = 0
        
        score = sentiment_score['technical_score']
        if score >= 60 and trend_strength > 0.05:
            return "中期上升趨勢有望延續，建議逢低布局"
        elif score <= 40 and trend_strength < -0.05:
            return "中期下降趨勢可能持續，建議謹慎操作"
        else:
            return "中期走勢不明朗，建議密切關注基本面變化"
    
    def generate_comprehensive_analysis(self, historical_data: List[Dict], current_info: Dict) -> Dict[str, Any]:
        """生成綜合分析報告"""
        # 載入並計算技術指標
        data = self.load_data(historical_data)
        data = self.calculate_technical_indicators(data)
        
        # 各項分析
        volume_sentiment = self.analyze_volume_sentiment(data)
        momentum = self.analyze_price_momentum(data)
        support_resistance = self.calculate_support_resistance(data)
        sentiment_score = self.generate_sentiment_score(data)
        investment_rec = self.generate_investment_recommendation(data, sentiment_score, support_resistance)
        volatility_metrics = self.calculate_volatility_metrics(data)
        risk_assessment = self.assess_risks(data, volatility_metrics)
        expected_returns = self.calculate_expected_returns(data, investment_rec)
        
        # 綜合報告
        analysis_report = {
            "股票基本信息": {
                "股票代碼": self.symbol,
                "公司名稱": self.company_name,
                "當前價格": current_info.get("current_price", data[-1]['close']),
                "分析日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "數據期間": f"{data[0]['timestamp'][:10]} 至 {data[-1]['timestamp'][:10]}"
            },
            
            "詳細分析過程": {
                "技術指標分析": {
                    "移動平均線": {
                        "MA5趨勢": momentum['ma5_trend'],
                        "MA10趨勢": momentum['ma10_trend'],
                        "MA20趨勢": momentum['ma20_trend']
                    },
                    "動量指標": {
                        "RSI": momentum['rsi_value'],
                        "RSI情緒": momentum['rsi_sentiment'],
                        "MACD信號": momentum['macd_signal']
                    },
                    "布林帶分析": {
                        "位置": momentum['bollinger_position'],
                        "情緒": momentum['bollinger_sentiment']
                    }
                },
                "成交量分析": volume_sentiment,
                "支撐阻力位": support_resistance,
                "情緒評分": sentiment_score
            },
            
            "投資建議": {
                "建議操作": investment_rec['recommendation'],
                "目標價位": investment_rec['target_price'],
                "止損價位": investment_rec['stop_loss'],
                "風險收益比": investment_rec['risk_reward_ratio'],
                "建議持有期": investment_rec['holding_period'],
                "操作理由": self._generate_reasoning(sentiment_score, momentum, volume_sentiment)
            },
            
            "風險評估": risk_assessment,
            
            "預期收益評估": expected_returns,
            
            "市場展望": {
                "短期展望": self._generate_short_term_outlook(sentiment_score),
                "中期展望": self._generate_medium_term_outlook(data, sentiment_score),
                "關鍵監控指標": [
                    f"支撐位: {support_resistance['primary_support']:.2f}",
                    f"阻力位: {support_resistance['primary_resistance']:.2f}",
                    f"RSI: {momentum['rsi_value']:.1f}",
                    "成交量變化",
                    "MACD金叉死叉"
                ]
            }
        }
        
        return analysis_report

def main():
    # 騰訊控股歷史數據
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
    
    # 當前股票信息
    current_info = {
        "current_price": 644.00,
        "price_change": 57.00,
        "change_percent": 9.71,
        "high": 661.50,
        "low": 587.00,
        "avg_volume": 18690238
    }
    
    # 創建分析器並執行分析
    analyzer = TencentSentimentAnalyzer()
    analysis_result = analyzer.generate_comprehensive_analysis(historical_data, current_info)
    
    # 輸出JSON格式結果
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()