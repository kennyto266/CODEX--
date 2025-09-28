#!/usr/bin/env python3
"""
港股技术分析代理 (HK Stock Technical Analyst)
专门针对港股的量化分析AI代理，追求高Sharpe Ratio的交易策略
"""

import json
import math
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class StockData:
    """港股数据结构"""
    stock: str
    close_prices: List[float]
    volumes: List[int] = None
    dates: List[str] = None

class HKStockTechnicalAnalyst:
    """港股技术分析代理"""
    
    def __init__(self, target_sharpe: float = 1.5):
        self.target_sharpe = target_sharpe
        self.ma_period = 20
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
    
    def _mean(self, values: List[float]) -> float:
        """计算平均值"""
        return sum(values) / len(values) if values else 0
    
    def _std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0
        mean_val = self._mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
        
    def calculate_ma(self, prices: List[float], period: int = 20) -> List[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return [float('nan')] * len(prices)
        
        ma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                ma_values.append(float('nan'))
            else:
                ma_values.append(sum(prices[i-period+1:i+1]) / period)
        return ma_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """计算相对强弱指数 (RSI)"""
        if len(prices) < period + 1:
            return [float('nan')] * len(prices)
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        rsi_values = [float('nan')]  # First value is NaN
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
        
        # Calculate subsequent RSI values using smoothed averages
        for i in range(period + 1, len(prices)):
            gain = gains[i-1]
            loss = losses[i-1]
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
        
        return rsi_values
    
    def calculate_macd(self, prices: List[float]) -> Tuple[List[float], List[float], List[float]]:
        """计算MACD指标"""
        if len(prices) < self.macd_slow:
            return ([float('nan')] * len(prices), [float('nan')] * len(prices), [float('nan')] * len(prices))
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, self.macd_fast)
        ema_slow = self._calculate_ema(prices, self.macd_slow)
        
        # MACD line
        macd_line = [fast - slow if not math.isnan(fast) and not math.isnan(slow) else float('nan') 
                    for fast, slow in zip(ema_fast, ema_slow)]
        
        # Signal line (EMA of MACD line)
        signal_line = self._calculate_ema([x for x in macd_line if not math.isnan(x)], self.macd_signal)
        
        # Pad signal line to match length
        signal_line = [float('nan')] * (len(macd_line) - len(signal_line)) + signal_line
        
        # Histogram
        histogram = [macd - signal if not math.isnan(macd) and not math.isnan(signal) else float('nan') 
                    for macd, signal in zip(macd_line, signal_line)]
        
        return macd_line, signal_line, histogram
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """计算指数移动平均线"""
        if len(prices) < period:
            return [float('nan')] * len(prices)
        
        alpha = 2 / (period + 1)
        ema_values = [float('nan')] * (period - 1)
        ema_values.append(sum(prices[:period]) / period)  # Initial SMA
        
        for i in range(period, len(prices)):
            ema_values.append(alpha * prices[i] + (1 - alpha) * ema_values[-1])
        
        return ema_values
    
    def generate_signals(self, data: StockData) -> List[int]:
        """生成买卖信号 (1=买入, -1=卖出, 0=持有)"""
        prices = data.close_prices
        ma_values = self.calculate_ma(prices, self.ma_period)
        rsi_values = self.calculate_rsi(prices, self.rsi_period)
        macd_line, signal_line, _ = self.calculate_macd(prices)
        
        signals = []
        
        for i in range(len(prices)):
            signal = 0
            
            if i < max(self.ma_period, self.rsi_period) or i >= len(rsi_values) or i >= len(ma_values):
                signals.append(signal)
                continue
            
            price = prices[i]
            ma = ma_values[i]
            rsi = rsi_values[i]
            macd = macd_line[i] if i < len(macd_line) else float('nan')
            macd_signal = signal_line[i] if i < len(signal_line) else float('nan')
            
            # 买入条件：价格突破MA，RSI不超买，MACD金叉
            if (not math.isnan(ma) and price > ma and 
                not math.isnan(rsi) and rsi < 70 and rsi > 30 and
                not math.isnan(macd) and not math.isnan(macd_signal) and macd > macd_signal):
                signal = 1
            
            # 卖出条件：RSI超买或价格跌破MA，MACD死叉
            elif (not math.isnan(rsi) and rsi > 80) or \
                 (not math.isnan(ma) and price < ma * 0.95) or \
                 (not math.isnan(macd) and not math.isnan(macd_signal) and macd < macd_signal):
                signal = -1
            
            signals.append(signal)
        
        return signals
    
    def calculate_sharpe_contribution(self, data: StockData, signals: List[int]) -> float:
        """计算策略对Sharpe Ratio的预估贡献"""
        prices = data.close_prices
        if len(prices) < 30:  # 需要足够的数据点
            return 0.0
        
        # 计算价格变化率
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # 根据信号计算策略收益
        strategy_returns = []
        for i in range(1, len(signals)):
            if signals[i-1] == 1:  # 持有多头
                strategy_returns.append(returns[i-1])
            elif signals[i-1] == -1:  # 持有空头或现金
                strategy_returns.append(-returns[i-1] * 0.5)  # 保守的空头策略
            else:
                strategy_returns.append(0)  # 现金
        
        if not strategy_returns or self._std(strategy_returns) == 0:
            return 0.0
        
        # 计算策略Sharpe比率
        mean_return = sum(strategy_returns) / len(strategy_returns)
        std_return = self._std(strategy_returns)
        sharpe = mean_return / std_return if std_return > 0 else 0
        
        # 标准化到-1到1区间
        return max(-1, min(1, sharpe / 2))
    
    def generate_recommendations(self, data: StockData, signals: List[int], 
                               rsi_values: List[float]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        current_price = data.close_prices[-1]
        current_rsi = rsi_values[-1] if not math.isnan(rsi_values[-1]) else None
        recent_signals = signals[-5:] if len(signals) >= 5 else signals
        
        # 基于当前RSI的建议
        if current_rsi:
            if current_rsi > 80:
                recommendations.append(f"⚠️ 技术警示：{data.stock} RSI超买({current_rsi:.1f})，建议减仓或止盈")
            elif current_rsi < 20:
                recommendations.append(f"💡 技术机会：{data.stock} RSI超卖({current_rsi:.1f})，可考虑逢低布局")
            elif 30 <= current_rsi <= 70:
                recommendations.append(f"✅ 技术中性：{data.stock} RSI健康区间({current_rsi:.1f})，可持续观察")
        
        # 基于信号趋势的建议
        buy_signals = sum(1 for s in recent_signals if s == 1)
        sell_signals = sum(1 for s in recent_signals if s == -1)
        
        if buy_signals > sell_signals:
            recommendations.append(f"📈 趋势信号：近期买入信号较多，{data.stock}技术面偏多")
        elif sell_signals > buy_signals:
            recommendations.append(f"📉 趋势信号：近期卖出信号较多，{data.stock}技术面偏空")
        
        # 止损建议
        ma_20 = self.calculate_ma(data.close_prices, 20)[-1]
        if not math.isnan(ma_20):
            stop_loss = ma_20 * 0.95
            recommendations.append(f"🛡️ 风险管理：建议止损位设在{stop_loss:.2f}（20日MA下方5%）")
        
        # 港股特色建议
        recommendations.append("🇭🇰 港股提示：注意美股开盘前后的波动，建议分批建仓降低风险")
        
        return recommendations[:5]  # 限制在5条以内
    
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        # 解析输入数据
        data = StockData(
            stock=input_data.get('stock', 'Unknown'),
            close_prices=input_data.get('close_prices', []),
            volumes=input_data.get('volumes', [])
        )
        
        if len(data.close_prices) < 20:
            return {
                "error": "数据不足，至少需要20个交易日数据进行技术分析",
                "stock": data.stock
            }
        
        # 计算技术指标
        rsi_values = self.calculate_rsi(data.close_prices, self.rsi_period)
        signals = self.generate_signals(data)
        sharpe_contribution = self.calculate_sharpe_contribution(data, signals)
        
        # 计算平均RSI
        valid_rsi = [rsi for rsi in rsi_values if not math.isnan(rsi)]
        rsi_avg = sum(valid_rsi) / len(valid_rsi) if valid_rsi else 0
        
        # 生成建议
        recommendations = self.generate_recommendations(data, signals, rsi_values)
        
        return {
            "stock": data.stock,
            "signals": signals,
            "rsi_avg": round(rsi_avg, 2),
            "sharpe_contribution": round(sharpe_contribution, 3),
            "recommendations": recommendations,
            "analysis_summary": {
                "total_signals": len([s for s in signals if s != 0]),
                "buy_signals": len([s for s in signals if s == 1]),
                "sell_signals": len([s for s in signals if s == -1]),
                "current_price": data.close_prices[-1],
                "current_rsi": round(rsi_values[-1], 2) if not math.isnan(rsi_values[-1]) else None
            }
        }

def main():
    """主函数 - 示例分析"""
    analyst = HKStockTechnicalAnalyst(target_sharpe=1.5)
    
    # 示例港股数据 (腾讯 0700.HK)
    sample_data = {
        "stock": "0700.HK",
        "close_prices": [
            320.0, 325.5, 318.2, 330.1, 335.8, 328.9, 340.2, 345.6, 338.1, 350.3,
            355.2, 348.7, 360.5, 365.1, 358.9, 370.2, 375.8, 368.3, 380.1, 385.5,
            378.2, 390.8, 395.3, 388.7, 400.2, 405.6, 398.1, 410.3, 415.8, 408.5,
            420.2, 425.7, 418.3, 430.5, 435.1, 428.9, 440.2, 445.8, 438.5, 450.3
        ],
        "volumes": [15000000] * 40  # 示例成交量
    }
    
    # 执行分析
    result = analyst.analyze(sample_data)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 简短解释
    print(f"\n💡 关键洞见：{result['stock']}当前RSI为{result.get('analysis_summary', {}).get('current_rsi', 'N/A')}，"
          f"策略Sharpe贡献值{result['sharpe_contribution']}，技术面{'偏多' if result['sharpe_contribution'] > 0 else '偏空'}。")

if __name__ == "__main__":
    main()