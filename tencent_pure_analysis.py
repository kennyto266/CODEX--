#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股(0700.HK) 純Python量化分析系統
不依賴外部庫的專業港股分析工具
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Tuple, Any

class TencentPureAnalysis:
    """騰訊控股純Python量化分析類"""
    
    def __init__(self, data: List[Dict]):
        """初始化分析器"""
        self.raw_data = data
        self.data = self._prepare_data()
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        
    def _prepare_data(self) -> List[Dict]:
        """準備和清理數據"""
        # 按時間排序
        sorted_data = sorted(self.raw_data, key=lambda x: x['timestamp'])
        
        # 計算日收益率
        for i in range(1, len(sorted_data)):
            prev_close = sorted_data[i-1]['close']
            curr_close = sorted_data[i]['close']
            sorted_data[i]['returns'] = (curr_close - prev_close) / prev_close
            sorted_data[i]['high_low_pct'] = (sorted_data[i]['high'] - sorted_data[i]['low']) / sorted_data[i]['close']
        
        # 第一天收益率設為0
        sorted_data[0]['returns'] = 0.0
        sorted_data[0]['high_low_pct'] = (sorted_data[0]['high'] - sorted_data[0]['low']) / sorted_data[0]['close']
        
        return sorted_data
    
    def _moving_average(self, values: List[float], period: int) -> List[float]:
        """計算移動平均線"""
        ma = []
        for i in range(len(values)):
            if i < period - 1:
                ma.append(None)
            else:
                avg = sum(values[i-period+1:i+1]) / period
                ma.append(avg)
        return ma
    
    def _rsi(self, closes: List[float], period: int = 14) -> List[float]:
        """計算RSI指標"""
        rsi_values = []
        gains = []
        losses = []
        
        # 計算價格變化
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        # 計算RSI
        for i in range(len(gains)):
            if i < period - 1:
                rsi_values.append(None)
            else:
                avg_gain = sum(gains[i-period+1:i+1]) / period
                avg_loss = sum(losses[i-period+1:i+1]) / period
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                rsi_values.append(rsi)
        
        # 在開頭添加None以匹配原始數據長度
        return [None] + rsi_values
    
    def _macd(self, closes: List[float]) -> Tuple[List[float], List[float], List[float]]:
        """計算MACD指標"""
        # EMA計算函數
        def ema(values, period):
            ema_values = []
            multiplier = 2 / (period + 1)
            
            for i, value in enumerate(values):
                if i == 0:
                    ema_values.append(value)
                else:
                    ema_val = (value * multiplier) + (ema_values[-1] * (1 - multiplier))
                    ema_values.append(ema_val)
            return ema_values
        
        # 計算12日和26日EMA
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        
        # 計算MACD線
        macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
        
        # 計算信號線（MACD的9日EMA）
        signal_line = ema(macd_line, 9)
        
        # 計算柱狀圖
        histogram = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]
        
        return macd_line, signal_line, histogram
    
    def _bollinger_bands(self, closes: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """計算布林帶"""
        middle_band = self._moving_average(closes, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(closes)):
            if i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                # 計算標準差
                values = closes[i-period+1:i+1]
                mean = middle_band[i]
                variance = sum((x - mean) ** 2 for x in values) / period
                std = math.sqrt(variance)
                
                upper_band.append(mean + (std_dev * std))
                lower_band.append(mean - (std_dev * std))
        
        return upper_band, middle_band, lower_band
    
    def calculate_technical_indicators(self) -> Dict[str, Any]:
        """計算技術指標"""
        closes = [item['close'] for item in self.data]
        
        # 移動平均線
        ma5 = self._moving_average(closes, 5)
        ma10 = self._moving_average(closes, 10)
        ma20 = self._moving_average(closes, 20)
        
        # RSI
        rsi = self._rsi(closes)
        
        # MACD
        macd_line, signal_line, histogram = self._macd(closes)
        
        # 布林帶
        bb_upper, bb_middle, bb_lower = self._bollinger_bands(closes)
        
        # 最新值
        latest_idx = -1
        
        return {
            'moving_averages': {
                'ma5': round(ma5[latest_idx] if ma5[latest_idx] else 0, 2),
                'ma10': round(ma10[latest_idx] if ma10[latest_idx] else 0, 2),
                'ma20': round(ma20[latest_idx] if ma20[latest_idx] else 0, 2),
                'current_vs_ma5': round((self.current_price - (ma5[latest_idx] or 0)) / (ma5[latest_idx] or 1) * 100, 2),
                'current_vs_ma10': round((self.current_price - (ma10[latest_idx] or 0)) / (ma10[latest_idx] or 1) * 100, 2),
                'current_vs_ma20': round((self.current_price - (ma20[latest_idx] or 0)) / (ma20[latest_idx] or 1) * 100, 2)
            },
            'momentum': {
                'rsi': round(rsi[latest_idx] if rsi[latest_idx] else 50, 2),
                'macd': round(macd_line[latest_idx], 2),
                'macd_signal': round(signal_line[latest_idx], 2),
                'macd_histogram': round(histogram[latest_idx], 2)
            },
            'bollinger_bands': {
                'upper': round(bb_upper[latest_idx] if bb_upper[latest_idx] else 0, 2),
                'middle': round(bb_middle[latest_idx] if bb_middle[latest_idx] else 0, 2),
                'lower': round(bb_lower[latest_idx] if bb_lower[latest_idx] else 0, 2),
                'position': round((self.current_price - (bb_lower[latest_idx] or 0)) / ((bb_upper[latest_idx] or 1) - (bb_lower[latest_idx] or 0)), 2) if bb_upper[latest_idx] and bb_lower[latest_idx] else 0.5
            }
        }
    
    def analyze_trend_and_support_resistance(self) -> Dict[str, Any]:
        """分析趨勢和支撐阻力位"""
        # 計算近期高低點
        recent_highs = [item['high'] for item in self.data[-10:]]
        recent_lows = [item['low'] for item in self.data[-10:]]
        recent_high = max(recent_highs)
        recent_low = min(recent_lows)
        
        # 尋找支撐阻力位
        resistance_levels = []
        support_levels = []
        
        # 基於局部極值點
        for i in range(2, len(self.data)-2):
            current_high = self.data[i]['high']
            current_low = self.data[i]['low']
            
            # 檢查是否為局部高點（阻力位）
            if (current_high > self.data[i-1]['high'] and 
                current_high > self.data[i-2]['high'] and
                current_high > self.data[i+1]['high'] and 
                current_high > self.data[i+2]['high']):
                resistance_levels.append(current_high)
            
            # 檢查是否為局部低點（支撐位）
            if (current_low < self.data[i-1]['low'] and 
                current_low < self.data[i-2]['low'] and
                current_low < self.data[i+1]['low'] and 
                current_low < self.data[i+2]['low']):
                support_levels.append(current_low)
        
        # 排序並取最重要的幾個位
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:3]
        support_levels = sorted(list(set(support_levels)), reverse=True)[:3]
        
        # 趨勢分析
        recent_closes = [item['close'] for item in self.data[-5:]]
        price_trend = 'neutral'
        
        if len(recent_closes) >= 3:
            if recent_closes[-1] > recent_closes[-3]:
                price_trend = 'bullish'
            elif recent_closes[-1] < recent_closes[-3]:
                price_trend = 'bearish'
        
        # 移動平均線趨勢
        closes = [item['close'] for item in self.data]
        ma5 = self._moving_average(closes, 5)
        ma10 = self._moving_average(closes, 10)
        ma20 = self._moving_average(closes, 20)
        
        ma_trend = 'neutral'
        if ma5[-1] and ma10[-1] and ma20[-1]:
            if ma5[-1] > ma10[-1] > ma20[-1]:
                ma_trend = 'bullish'
            elif ma5[-1] < ma10[-1] < ma20[-1]:
                ma_trend = 'bearish'
        
        return {
            'trend_analysis': {
                'price_trend': price_trend,
                'ma_trend': ma_trend,
                'recent_high': recent_high,
                'recent_low': recent_low
            },
            'support_resistance': {
                'resistance_levels': resistance_levels,
                'support_levels': support_levels,
                'key_resistance': resistance_levels[0] if resistance_levels else recent_high,
                'key_support': support_levels[0] if support_levels else recent_low
            }
        }
    
    def analyze_volume_patterns(self) -> Dict[str, Any]:
        """分析成交量模式"""
        volumes = [item['volume'] for item in self.data]
        
        # 成交量統計
        avg_volume = sum(volumes) / len(volumes)
        recent_volumes = volumes[-5:]
        recent_avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        volume_trend = 'increasing' if recent_avg_volume > avg_volume else 'decreasing'
        
        # 價量關係分析
        returns = [item['returns'] for item in self.data[-10:] if item['returns'] is not None]
        volume_changes = []
        
        for i in range(1, len(volumes[-10:])):
            vol_change = (volumes[-10:][i] - volumes[-10:][i-1]) / volumes[-10:][i-1]
            volume_changes.append(vol_change)
        
        # 簡單相關性計算
        if len(returns) == len(volume_changes) and len(returns) > 1:
            mean_returns = sum(returns) / len(returns)
            mean_vol_changes = sum(volume_changes) / len(volume_changes)
            
            numerator = sum((returns[i] - mean_returns) * (volume_changes[i] - mean_vol_changes) 
                          for i in range(len(returns)))
            
            sum_sq_returns = sum((r - mean_returns) ** 2 for r in returns)
            sum_sq_vol = sum((v - mean_vol_changes) ** 2 for v in volume_changes)
            
            if sum_sq_returns > 0 and sum_sq_vol > 0:
                correlation = numerator / math.sqrt(sum_sq_returns * sum_sq_vol)
            else:
                correlation = 0
        else:
            correlation = 0
        
        # 異常成交量天數
        high_volume_days = len([v for v in volumes if v > avg_volume * 1.5])
        
        return {
            'volume_statistics': {
                'average_volume': int(avg_volume),
                'recent_average_volume': int(recent_avg_volume),
                'volume_trend': volume_trend,
                'high_volume_days': high_volume_days
            },
            'price_volume_relationship': {
                'correlation': round(correlation, 3),
                'relationship_strength': 'strong' if abs(correlation) > 0.5 else 'weak'
            }
        }
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """計算風險指標"""
        returns = [item['returns'] for item in self.data if item['returns'] is not None]
        
        # 波動率計算
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility_daily = math.sqrt(variance)
        volatility_annual = volatility_daily * math.sqrt(252)
        
        # VaR計算 (95%和99%置信區間)
        sorted_returns = sorted(returns)
        var_95_idx = int(len(sorted_returns) * 0.05)
        var_99_idx = int(len(sorted_returns) * 0.01)
        
        var_95 = sorted_returns[var_95_idx] if var_95_idx < len(sorted_returns) else sorted_returns[0]
        var_99 = sorted_returns[var_99_idx] if var_99_idx < len(sorted_returns) else sorted_returns[0]
        
        # 最大回撤計算
        cumulative_returns = [1.0]
        for r in returns:
            cumulative_returns.append(cumulative_returns[-1] * (1 + r))
        
        max_drawdown = 0
        peak = cumulative_returns[0]
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率 (假設無風險利率為3%)
        risk_free_rate = 0.03 / 252  # 日化無風險利率
        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess_return = sum(excess_returns) / len(excess_returns)
        
        if volatility_daily > 0:
            sharpe_ratio = mean_excess_return / volatility_daily * math.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 風險等級評估
        risk_level = 'low'
        if volatility_annual > 0.3:
            risk_level = 'high'
        elif volatility_annual > 0.2:
            risk_level = 'medium'
        
        return {
            'volatility': {
                'daily': round(volatility_daily * 100, 2),
                'annual': round(volatility_annual * 100, 2)
            },
            'value_at_risk': {
                'var_95': round(var_95 * 100, 2),
                'var_99': round(var_99 * 100, 2)
            },
            'performance_metrics': {
                'max_drawdown': round(max_drawdown * 100, 2),
                'sharpe_ratio': round(sharpe_ratio, 2)
            },
            'risk_assessment': {
                'risk_level': risk_level,
                'risk_score': round(volatility_annual * 100, 1)
            }
        }
    
    def generate_investment_recommendation(self, technical_indicators: Dict, 
                                         trend_analysis: Dict, risk_metrics: Dict) -> Dict[str, Any]:
        """生成投資建議"""
        
        # 技術分析評分
        technical_score = 0
        
        # RSI評分
        rsi = technical_indicators['momentum']['rsi']
        if 30 <= rsi <= 70:
            technical_score += 2
        elif rsi < 30:
            technical_score += 3  # 超賣，買入信號
        elif rsi > 70:
            technical_score -= 1  # 超買
        
        # MACD評分
        if technical_indicators['momentum']['macd_histogram'] > 0:
            technical_score += 2
        else:
            technical_score -= 1
        
        # 移動平均線評分
        ma_score = 0
        if technical_indicators['moving_averages']['current_vs_ma5'] > 0:
            ma_score += 1
        if technical_indicators['moving_averages']['current_vs_ma10'] > 0:
            ma_score += 1
        if technical_indicators['moving_averages']['current_vs_ma20'] > 0:
            ma_score += 1
        
        technical_score += ma_score
        
        # 趨勢評分
        trend_score = 0
        if trend_analysis['trend_analysis']['price_trend'] == 'bullish':
            trend_score += 2
        elif trend_analysis['trend_analysis']['price_trend'] == 'bearish':
            trend_score -= 2
        
        if trend_analysis['trend_analysis']['ma_trend'] == 'bullish':
            trend_score += 2
        elif trend_analysis['trend_analysis']['ma_trend'] == 'bearish':
            trend_score -= 2
        
        # 總評分
        total_score = technical_score + trend_score
        
        # 投資建議
        if total_score >= 6:
            recommendation = 'strong_buy'
            action = '強烈買入'
        elif total_score >= 3:
            recommendation = 'buy'
            action = '買入'
        elif total_score >= 0:
            recommendation = 'hold'
            action = '持有'
        elif total_score >= -3:
            recommendation = 'sell'
            action = '賣出'
        else:
            recommendation = 'strong_sell'
            action = '強烈賣出'
        
        # 目標價位計算
        current_price = self.current_price
        
        # 基於技術分析的目標價
        if recommendation in ['strong_buy', 'buy']:
            target_price = current_price * 1.15  # 15%上漲空間
            stop_loss = current_price * 0.92     # 8%止損
        elif recommendation == 'hold':
            target_price = current_price * 1.08  # 8%上漲空間
            stop_loss = current_price * 0.95     # 5%止損
        else:
            target_price = current_price * 0.90  # 10%下跌預期
            stop_loss = current_price * 1.05     # 5%止損
        
        # 預期收益計算
        expected_return = (target_price - current_price) / current_price * 100
        
        return {
            'recommendation': {
                'action': action,
                'recommendation_code': recommendation,
                'confidence_score': min(abs(total_score) * 10, 90),
                'reasoning': f'技術分析評分: {technical_score}, 趨勢評分: {trend_score}, 總評分: {total_score}'
            },
            'price_targets': {
                'current_price': current_price,
                'target_price': round(target_price, 2),
                'stop_loss': round(stop_loss, 2),
                'upside_potential': round((target_price - current_price) / current_price * 100, 2),
                'downside_risk': round((stop_loss - current_price) / current_price * 100, 2)
            },
            'expected_returns': {
                'short_term_1m': round(expected_return * 0.3, 2),
                'medium_term_3m': round(expected_return * 0.7, 2),
                'long_term_6m': round(expected_return, 2)
            }
        }
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """運行完整分析"""
        
        print("🔍 開始騰訊控股(0700.HK)量化分析...")
        
        # 1. 技術指標分析
        print("📊 計算技術指標...")
        technical_indicators = self.calculate_technical_indicators()
        
        # 2. 趨勢和支撐阻力分析
        print("📈 分析趨勢和支撐阻力位...")
        trend_analysis = self.analyze_trend_and_support_resistance()
        
        # 3. 成交量分析
        print("📊 分析成交量模式...")
        volume_analysis = self.analyze_volume_patterns()
        
        # 4. 風險評估
        print("⚠️ 計算風險指標...")
        risk_metrics = self.calculate_risk_metrics()
        
        # 5. 投資建議
        print("💡 生成投資建議...")
        investment_recommendation = self.generate_investment_recommendation(
            technical_indicators, trend_analysis, risk_metrics
        )
        
        # 整合所有分析結果
        complete_analysis = {
            'analysis_metadata': {
                'stock_symbol': '0700.HK',
                'stock_name': '騰訊控股',
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_period': '30個交易日',
                'current_price': self.current_price,
                'price_change': self.price_change,
                'price_change_percentage': self.price_change_pct,
                'analyzer_version': 'Pure Python v1.0'
            },
            'technical_analysis': technical_indicators,
            'trend_and_levels': trend_analysis,
            'volume_analysis': volume_analysis,
            'risk_assessment': risk_metrics,
            'investment_recommendation': investment_recommendation,
            'analysis_summary': {
                'key_findings': [
                    f"當前價格 {self.current_price} 港元，較前期上漲 {self.price_change_pct}%",
                    f"RSI指標: {technical_indicators['momentum']['rsi']}，顯示{'超買' if technical_indicators['momentum']['rsi'] > 70 else '超賣' if technical_indicators['momentum']['rsi'] < 30 else '正常'}狀態",
                    f"趨勢分析: 價格趨勢{trend_analysis['trend_analysis']['price_trend']}，均線趨勢{trend_analysis['trend_analysis']['ma_trend']}",
                    f"風險等級: {risk_metrics['risk_assessment']['risk_level']}，年化波動率 {risk_metrics['volatility']['annual']}%",
                    f"投資建議: {investment_recommendation['recommendation']['action']}，置信度 {investment_recommendation['recommendation']['confidence_score']}%"
                ],
                'overall_sentiment': investment_recommendation['recommendation']['recommendation_code'],
                'key_resistance': trend_analysis['support_resistance']['key_resistance'],
                'key_support': trend_analysis['support_resistance']['key_support']
            }
        }
        
        print("✅ 分析完成！")
        return complete_analysis

def main():
    """主函數"""
    
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
    
    # 創建分析器並運行分析
    analyzer = TencentPureAnalysis(historical_data)
    analysis_result = analyzer.run_complete_analysis()
    
    # 輸出JSON格式結果
    print("\n" + "="*80)
    print("📋 騰訊控股(0700.HK) 專業量化分析報告")
    print("="*80)
    
    # 保存結果到文件
    with open('/workspace/tencent_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    return analysis_result

if __name__ == "__main__":
    main()