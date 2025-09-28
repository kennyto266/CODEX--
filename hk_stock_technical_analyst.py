#!/usr/bin/env python3
"""
港股技术分析代理 (HK Stock Technical Analyst)
专门针对港股的量化分析AI代理，追求高Sharpe Ratio的交易策略
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    ma_20: List[float]
    rsi_14: List[float] 
    macd: List[float]
    macd_signal: List[float]
    macd_histogram: List[float]


class HKStockTechnicalAnalyst:
    """港股技术分析代理"""
    
    def __init__(self):
        self.sharpe_threshold = 1.5  # 目标Sharpe Ratio阈值
        
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """计算简单移动平均线"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(np.nan)
            else:
                sma.append(np.mean(prices[i-period+1:i+1]))
        return sma
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """计算相对强弱指数 (RSI)"""
        if len(prices) < period + 1:
            return [np.nan] * len(prices)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi_values = [np.nan] * len(prices)
        
        # 计算初始平均收益和损失
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi_values[period] = 100
        else:
            rs = avg_gain / avg_loss
            rsi_values[period] = 100 - (100 / (1 + rs))
        
        # 计算后续RSI值
        for i in range(period + 1, len(prices)):
            gain = gains[i-1] if gains[i-1] > 0 else 0
            loss = losses[i-1] if losses[i-1] > 0 else 0
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """计算MACD指标"""
        if len(prices) < slow:
            return ([np.nan] * len(prices), [np.nan] * len(prices), [np.nan] * len(prices))
        
        # 计算EMA
        def ema(data, period):
            alpha = 2 / (period + 1)
            ema_values = [data[0]]
            for i in range(1, len(data)):
                ema_values.append(alpha * data[i] + (1 - alpha) * ema_values[-1])
            return ema_values
        
        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)
        
        # MACD线
        macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
        
        # 信号线
        macd_signal = ema(macd_line, signal)
        
        # MACD柱状图
        macd_histogram = [macd - signal for macd, signal in zip(macd_line, macd_signal)]
        
        return macd_line, macd_signal, macd_histogram
    
    def generate_signals(self, prices: List[float], indicators: TechnicalIndicators) -> List[int]:
        """生成买卖信号"""
        signals = []
        
        for i in range(len(prices)):
            signal = 0  # 0: 持有, 1: 买入, -1: 卖出
            
            # 检查是否有足够的数据
            if (i < 20 or np.isnan(indicators.ma_20[i]) or 
                np.isnan(indicators.rsi_14[i]) or np.isnan(indicators.macd[i])):
                signals.append(signal)
                continue
            
            current_price = prices[i]
            ma_20 = indicators.ma_20[i]
            rsi = indicators.rsi_14[i]
            macd = indicators.macd[i]
            macd_signal = indicators.macd_signal[i]
            
            # 买入信号条件
            if (current_price > ma_20 and  # 价格在MA20之上
                rsi < 70 and  # RSI未超买
                rsi > 30 and  # RSI不在超卖区
                macd > macd_signal):  # MACD金叉
                signal = 1
            
            # 卖出信号条件  
            elif (rsi > 80 or  # RSI超买
                  current_price < ma_20 * 0.95 or  # 价格跌破MA20的95%
                  macd < macd_signal):  # MACD死叉
                signal = -1
            
            signals.append(signal)
        
        return signals
    
    def calculate_sharpe_contribution(self, prices: List[float], signals: List[int]) -> float:
        """计算策略对Sharpe Ratio的预估贡献"""
        if len(prices) < 2:
            return 0.0
        
        # 计算价格变化率
        returns = np.diff(prices) / prices[:-1]
        
        # 计算策略收益（简化版本）
        strategy_returns = []
        position = 0
        
        for i, signal in enumerate(signals[1:], 1):  # 从第二个信号开始
            if signal == 1:  # 买入信号
                position = 1
            elif signal == -1:  # 卖出信号
                position = 0
            
            # 根据持仓计算收益
            strategy_return = position * returns[i-1] if i-1 < len(returns) else 0
            strategy_returns.append(strategy_return)
        
        if len(strategy_returns) == 0:
            return 0.0
        
        # 计算Sharpe比率贡献（简化）
        mean_return = np.mean(strategy_returns)
        std_return = np.std(strategy_returns) if len(strategy_returns) > 1 else 0.01
        
        if std_return == 0:
            return 0.0
        
        sharpe_contribution = mean_return / std_return
        
        # 标准化到-1到1之间
        return np.clip(sharpe_contribution, -1, 1)
    
    def generate_recommendations(self, prices: List[float], indicators: TechnicalIndicators, 
                               signals: List[int]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        
        if len(prices) == 0:
            return ["数据不足，无法生成建议"]
        
        current_price = prices[-1]
        current_rsi = indicators.rsi_14[-1] if not np.isnan(indicators.rsi_14[-1]) else 50
        current_signal = signals[-1] if signals else 0
        
        # 基于当前技术指标生成建议
        if current_signal == 1:
            recommendations.append(f"技术指标显示买入信号，当前RSI={current_rsi:.1f}，建议关注入场机会")
        elif current_signal == -1:
            recommendations.append(f"技术指标显示卖出信号，当前RSI={current_rsi:.1f}，建议减仓或止损")
        
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
            
            indicators = TechnicalIndicators(
                ma_20=ma_20,
                rsi_14=rsi_14,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram
            )
            
            # 生成交易信号
            signals = self.generate_signals(close_prices, indicators)
            
            # 计算平均RSI
            valid_rsi = [rsi for rsi in rsi_14 if not np.isnan(rsi)]
            rsi_avg = np.mean(valid_rsi) if valid_rsi else 50
            
            # 计算Sharpe贡献
            sharpe_contribution = self.calculate_sharpe_contribution(close_prices, signals)
            
            # 生成建议
            recommendations = self.generate_recommendations(close_prices, indicators, signals)
            
            # 构建结果
            result = {
                "stock": stock_code,
                "signals": signals,
                "rsi_avg": round(rsi_avg, 2),
                "sharpe_contribution": round(sharpe_contribution, 3),
                "recommendations": recommendations,
                "technical_indicators": {
                    "current_price": close_prices[-1],
                    "ma_20": round(ma_20[-1], 2) if not np.isnan(ma_20[-1]) else None,
                    "current_rsi": round(rsi_14[-1], 2) if not np.isnan(rsi_14[-1]) else None,
                    "macd": round(macd[-1], 4) if not np.isnan(macd[-1]) else None
                },
                "risk_assessment": {
                    "volatility_level": "高" if np.std(close_prices) / np.mean(close_prices) > 0.3 else "中等",
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
    
    # 示例数据
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