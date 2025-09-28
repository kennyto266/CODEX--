#!/usr/bin/env python3
"""
港股技术分析代理 (HK Stock Technical Analyst) - 简化版
专门针对港股的量化分析AI代理，追求高Sharpe Ratio的交易策略
不依赖外部库，使用纯Python实现
"""

import json
import math
from typing import Dict, List, Any, Tuple


class HKStockTechnicalAnalyst:
    """港股技术分析代理 - 简化版"""
    
    def __init__(self):
        self.sharpe_threshold = 1.5  # 目标Sharpe Ratio阈值
        
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """计算简单移动平均线"""
        if len(prices) < period:
            return [None] * len(prices)
        
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                sma.append(sum(prices[i-period+1:i+1]) / period)
        return sma
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """计算相对强弱指数 (RSI)"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        # 计算价格变化
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        rsi_values = [None] * len(prices)
        
        # 计算初始平均收益和损失
        gains = [d if d > 0 else 0 for d in deltas[:period]]
        losses = [-d if d < 0 else 0 for d in deltas[:period]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            rsi_values[period] = 100
        else:
            rs = avg_gain / avg_loss
            rsi_values[period] = 100 - (100 / (1 + rs))
        
        # 计算后续RSI值
        for i in range(period + 1, len(prices)):
            gain = deltas[i-1] if deltas[i-1] > 0 else 0
            loss = -deltas[i-1] if deltas[i-1] < 0 else 0
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """计算指数移动平均线"""
        if len(prices) == 0:
            return []
        
        alpha = 2 / (period + 1)
        ema_values = [prices[0]]
        
        for i in range(1, len(prices)):
            ema_values.append(alpha * prices[i] + (1 - alpha) * ema_values[-1])
        
        return ema_values
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """计算MACD指标"""
        if len(prices) < slow:
            return ([None] * len(prices), [None] * len(prices), [None] * len(prices))
        
        # 计算快线和慢线EMA
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        # MACD线
        macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
        
        # 信号线
        macd_signal = self.calculate_ema(macd_line, signal)
        
        # MACD柱状图
        macd_histogram = [macd - signal for macd, signal in zip(macd_line, macd_signal)]
        
        return macd_line, macd_signal, macd_histogram
    
    def generate_signals(self, prices: List[float], ma_20: List[float], rsi_14: List[float], 
                        macd: List[float], macd_signal: List[float]) -> List[int]:
        """生成买卖信号"""
        signals = []
        
        for i in range(len(prices)):
            signal = 0  # 0: 持有, 1: 买入, -1: 卖出
            
            # 检查是否有足够的数据
            if (i < 20 or ma_20[i] is None or rsi_14[i] is None or 
                macd[i] is None or macd_signal[i] is None):
                signals.append(signal)
                continue
            
            current_price = prices[i]
            ma_20_val = ma_20[i]
            rsi = rsi_14[i]
            macd_val = macd[i]
            macd_sig = macd_signal[i]
            
            # 买入信号条件
            if (current_price > ma_20_val and  # 价格在MA20之上
                rsi < 70 and  # RSI未超买
                rsi > 30 and  # RSI不在超卖区
                macd_val > macd_sig):  # MACD金叉
                signal = 1
            
            # 卖出信号条件  
            elif (rsi > 80 or  # RSI超买
                  current_price < ma_20_val * 0.95 or  # 价格跌破MA20的95%
                  macd_val < macd_sig):  # MACD死叉
                signal = -1
            
            signals.append(signal)
        
        return signals
    
    def calculate_sharpe_contribution(self, prices: List[float], signals: List[int]) -> float:
        """计算策略对Sharpe Ratio的预估贡献"""
        if len(prices) < 2:
            return 0.0
        
        # 计算价格变化率
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        # 计算策略收益（简化版本）
        strategy_returns = []
        position = 0
        
        for i, signal in enumerate(signals[1:], 1):  # 从第二个信号开始
            if signal == 1:  # 买入信号
                position = 1
            elif signal == -1:  # 卖出信号
                position = 0
            
            # 根据持仓计算收益
            if i-1 < len(returns):
                strategy_return = position * returns[i-1]
                strategy_returns.append(strategy_return)
        
        if len(strategy_returns) == 0:
            return 0.0
        
        # 计算Sharpe比率贡献（简化）
        mean_return = sum(strategy_returns) / len(strategy_returns)
        
        if len(strategy_returns) > 1:
            variance = sum((r - mean_return) ** 2 for r in strategy_returns) / (len(strategy_returns) - 1)
            std_return = math.sqrt(variance)
        else:
            std_return = 0.01
        
        if std_return == 0:
            return 0.0
        
        sharpe_contribution = mean_return / std_return
        
        # 标准化到-1到1之间
        return max(-1, min(1, sharpe_contribution))
    
    def calculate_average(self, values: List[float]) -> float:
        """计算平均值，忽略None值"""
        valid_values = [v for v in values if v is not None]
        return sum(valid_values) / len(valid_values) if valid_values else 50
    
    def generate_recommendations(self, prices: List[float], ma_20: List[float], 
                               rsi_14: List[float], signals: List[int]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        if len(prices) == 0:
            return ["数据不足，无法生成建议"]
        
        current_price = prices[-1]
        current_rsi = rsi_14[-1] if rsi_14[-1] is not None else 50
        current_signal = signals[-1] if signals else 0
        
        # 基于当前技术指标生成建议
        if current_signal == 1:
            recommendations.append(f"技术指标显示买入信号，当前RSI={current_rsi:.1f}，建议关注入场机会")
        elif current_signal == -1:
            recommendations.append(f"技术指标显示卖出信号，当前RSI={current_rsi:.1f}，建议减仓或止损")
        else:
            recommendations.append(f"当前无明确交易信号，RSI={current_rsi:.1f}，建议观望")
        
        # RSI相关建议
        if current_rsi > 80:
            recommendations.append("RSI超买警告：当前RSI>80，存在回调风险，建议谨慎操作")
        elif current_rsi < 20:
            recommendations.append("RSI超卖机会：当前RSI<20，可能存在反弹机会，建议关注")
        
        # 风险管理建议
        recommendations.append(f"建议设置止损位于{current_price * 0.95:.2f}（当前价格95%）")
        
        # 港股特有建议
        recommendations.append("港股市场波动较大，建议控制单次交易仓位不超过总资金20%")
        
        # 流动性建议
        recommendations.append("优先选择成交量大于日均成交量150%的高流动性时段进行交易")
        
        return recommendations[:5]  # 限制在5条以内
    
    def calculate_volatility(self, prices: List[float]) -> str:
        """计算价格波动率"""
        if len(prices) < 2:
            return "无法计算"
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        if volatility > 0.03:
            return "高"
        elif volatility > 0.015:
            return "中等"
        else:
            return "低"
    
    def analyze(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """主分析函数"""
        try:
            # 提取数据
            stock_code = stock_data.get('stock', 'Unknown')
            close_prices = stock_data.get('close_prices', [])
            volumes = stock_data.get('volumes', [])
            
            if len(close_prices) < 20:
                return {
                    "error": "数据不足，至少需要20个交易日数据进行技术分析",
                    "stock": stock_code
                }
            
            # 计算技术指标
            ma_20 = self.calculate_sma(close_prices, 20)
            rsi_14 = self.calculate_rsi(close_prices, 14)
            macd, macd_signal, macd_histogram = self.calculate_macd(close_prices)
            
            # 生成交易信号
            signals = self.generate_signals(close_prices, ma_20, rsi_14, macd, macd_signal)
            
            # 计算平均RSI
            rsi_avg = self.calculate_average(rsi_14)
            
            # 计算Sharpe贡献
            sharpe_contribution = self.calculate_sharpe_contribution(close_prices, signals)
            
            # 生成建议
            recommendations = self.generate_recommendations(close_prices, ma_20, rsi_14, signals)
            
            # 构建结果
            result = {
                "stock": stock_code,
                "signals": signals,
                "rsi_avg": round(rsi_avg, 2),
                "sharpe_contribution": round(sharpe_contribution, 3),
                "recommendations": recommendations,
                "technical_indicators": {
                    "current_price": close_prices[-1],
                    "ma_20": round(ma_20[-1], 2) if ma_20[-1] is not None else None,
                    "current_rsi": round(rsi_14[-1], 2) if rsi_14[-1] is not None else None,
                    "macd": round(macd[-1], 4) if macd[-1] is not None else None
                },
                "risk_assessment": {
                    "volatility_level": self.calculate_volatility(close_prices),
                    "trend_strength": "强" if abs(sharpe_contribution) > 0.5 else "弱"
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"分析过程中出现错误: {str(e)}",
                "stock": stock_data.get('stock', 'Unknown')
            }


def main():
    """主函数 - 示例用法"""
    analyst = HKStockTechnicalAnalyst()
    
    # 示例数据 - 腾讯控股(0700.HK)模拟数据
    sample_data = {
        "stock": "0700.HK",
        "close_prices": [
            580, 585, 578, 590, 595, 588, 600, 605, 598, 610,
            615, 608, 620, 625, 618, 630, 635, 628, 640, 645,
            638, 650, 655, 648, 660, 665, 658, 670, 675, 668
        ],
        "volumes": [1000000 + i * 50000 for i in range(30)]
    }
    
    # 执行分析
    result = analyst.analyze(sample_data)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 简短解释
    if "error" not in result:
        print(f"\n关键洞见：{result['stock']}当前RSI为{result['rsi_avg']}，"
              f"策略Sharpe贡献为{result['sharpe_contribution']}，"
              f"{'建议关注买入机会' if result['sharpe_contribution'] > 0 else '建议谨慎操作'}。")


if __name__ == "__main__":
    main()