#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騰訊控股(0700.HK) 量化分析系統
專業的港股量化分析工具
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class TencentQuantAnalysis:
    """騰訊控股量化分析類"""
    
    def __init__(self, data: List[Dict]):
        """初始化分析器"""
        self.raw_data = data
        self.df = self._prepare_data()
        self.current_price = 644.00
        self.price_change = 57.00
        self.price_change_pct = 9.71
        
    def _prepare_data(self) -> pd.DataFrame:
        """準備和清理數據"""
        df = pd.DataFrame(self.raw_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        df.reset_index(drop=True, inplace=True)
        
        # 計算技術指標
        df['returns'] = df['close'].pct_change()
        df['high_low_pct'] = (df['high'] - df['low']) / df['close'] * 100
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        return df
    
    def calculate_technical_indicators(self) -> Dict[str, Any]:
        """計算技術指標"""
        df = self.df
        
        # 移動平均線
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # 布林帶
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 最新指標值
        latest = df.iloc[-1]
        
        return {
            'moving_averages': {
                'ma5': round(latest['ma5'], 2),
                'ma10': round(latest['ma10'], 2),
                'ma20': round(latest['ma20'], 2),
                'current_vs_ma5': round((self.current_price - latest['ma5']) / latest['ma5'] * 100, 2),
                'current_vs_ma10': round((self.current_price - latest['ma10']) / latest['ma10'] * 100, 2),
                'current_vs_ma20': round((self.current_price - latest['ma20']) / latest['ma20'] * 100, 2)
            },
            'momentum': {
                'rsi': round(latest['rsi'], 2),
                'macd': round(latest['macd'], 2),
                'macd_signal': round(latest['macd_signal'], 2),
                'macd_histogram': round(latest['macd_histogram'], 2)
            },
            'bollinger_bands': {
                'upper': round(latest['bb_upper'], 2),
                'middle': round(latest['bb_middle'], 2),
                'lower': round(latest['bb_lower'], 2),
                'position': round(latest['bb_position'], 2)
            }
        }
    
    def analyze_trend_and_support_resistance(self) -> Dict[str, Any]:
        """分析趋势和支撑阻力位"""
        df = self.df
        
        # 計算近期高低點
        recent_high = df['high'].tail(10).max()
        recent_low = df['low'].tail(10).min()
        
        # 支撑和阻力位
        resistance_levels = []
        support_levels = []
        
        # 基于历史高点找阻力位
        for i in range(2, len(df)-2):
            if (df.iloc[i]['high'] > df.iloc[i-1]['high'] and 
                df.iloc[i]['high'] > df.iloc[i-2]['high'] and
                df.iloc[i]['high'] > df.iloc[i+1]['high'] and 
                df.iloc[i]['high'] > df.iloc[i+2]['high']):
                resistance_levels.append(df.iloc[i]['high'])
        
        # 基于历史低点找支撑位
        for i in range(2, len(df)-2):
            if (df.iloc[i]['low'] < df.iloc[i-1]['low'] and 
                df.iloc[i]['low'] < df.iloc[i-2]['low'] and
                df.iloc[i]['low'] < df.iloc[i+1]['low'] and 
                df.iloc[i]['low'] < df.iloc[i+2]['low']):
                support_levels.append(df.iloc[i]['low'])
        
        # 取最近的支撑阻力位
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:3]
        support_levels = sorted(list(set(support_levels)), reverse=True)[:3]
        
        # 趋势分析
        price_trend = 'neutral'
        ma_trend = 'neutral'
        
        # 基于价格走势判断趋势
        recent_closes = df['close'].tail(5).values
        if len(recent_closes) >= 3:
            if recent_closes[-1] > recent_closes[-3] and recent_closes[-2] > recent_closes[-4]:
                price_trend = 'bullish'
            elif recent_closes[-1] < recent_closes[-3] and recent_closes[-2] < recent_closes[-4]:
                price_trend = 'bearish'
        
        # 基于移动平均线判断趋势
        latest = df.iloc[-1]
        if latest['ma5'] > latest['ma10'] > latest['ma20']:
            ma_trend = 'bullish'
        elif latest['ma5'] < latest['ma10'] < latest['ma20']:
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
        df = self.df
        
        # 成交量統計
        avg_volume = df['volume'].mean()
        recent_avg_volume = df['volume'].tail(5).mean()
        volume_trend = 'increasing' if recent_avg_volume > avg_volume else 'decreasing'
        
        # 價量關係分析
        price_volume_correlation = df['returns'].tail(10).corr(df['volume'].tail(10).pct_change())
        
        # 異常成交量天數
        high_volume_days = len(df[df['volume'] > avg_volume * 1.5])
        
        return {
            'volume_statistics': {
                'average_volume': int(avg_volume),
                'recent_average_volume': int(recent_avg_volume),
                'volume_trend': volume_trend,
                'high_volume_days': high_volume_days
            },
            'price_volume_relationship': {
                'correlation': round(price_volume_correlation, 3),
                'relationship_strength': 'strong' if abs(price_volume_correlation) > 0.5 else 'weak'
            }
        }
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """計算風險指標"""
        df = self.df
        
        # 波動率計算
        daily_returns = df['returns'].dropna()
        volatility_daily = daily_returns.std()
        volatility_annual = volatility_daily * np.sqrt(252)
        
        # VaR計算 (95%置信區間)
        var_95 = np.percentile(daily_returns, 5)
        var_99 = np.percentile(daily_returns, 1)
        
        # 最大回撤
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 夏普比率 (假設無風險利率為3%)
        risk_free_rate = 0.03 / 252  # 日化無風險利率
        excess_returns = daily_returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
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
        
        # 基于技術分析的目標價
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
                'price_change_percentage': self.price_change_pct
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
                    f"投資建議: {investment_recommendation['recommendation']['action']}"
                ],
                'overall_sentiment': investment_recommendation['recommendation']['recommendation_code']
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
    analyzer = TencentQuantAnalysis(historical_data)
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