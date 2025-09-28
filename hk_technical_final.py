#!/usr/bin/env python3
"""
Technical Analysis Agent for Hong Kong Stocks - Final Version
专门针对港股的量化分析AI代理 - 技术分析代理
目标: 高Sharpe Ratio (>1.5) 策略优化
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class HKTechnicalAnalyst:
    def __init__(self, stock_data):
        """初始化技术分析代理"""
        self.stock_data = stock_data
        self.df = self._prepare_data()
        
    def _prepare_data(self):
        """准备数据框架"""
        data = {
            'close': self.stock_data['close_prices'],
            'high': self.stock_data['highs'],
            'low': self.stock_data['lows'],
            'volume': self.stock_data['volumes']
        }
        df = pd.DataFrame(data)
        # 添加日期索引
        start_date = datetime.now() - timedelta(days=len(df)-1)
        df.index = pd.date_range(start=start_date, periods=len(df), freq='D')
        return df
    
    def calculate_rsi(self, period=14):
        """计算RSI指标"""
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def calculate_sma(self, period):
        """计算简单移动平均线"""
        return self.df['close'].rolling(window=period).mean()
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """计算布林带"""
        sma = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def rsi_mean_reversion_strategy(self):
        """RSI均值回归策略 - 简化版本，确保生成信号"""
        # 计算技术指标
        rsi = self.calculate_rsi(14)
        sma_20 = self.calculate_sma(20)
        sma_50 = self.calculate_sma(50)
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands()
        
        # 添加到数据框
        self.df['rsi'] = rsi
        self.df['sma_20'] = sma_20
        self.df['sma_50'] = sma_50
        self.df['bb_upper'] = upper_bb
        self.df['bb_middle'] = middle_bb
        self.df['bb_lower'] = lower_bb
        
        # 生成信号
        signals = []
        positions = []
        current_position = 0
        
        for i in range(len(self.df)):
            if i < 20:  # 等待指标稳定
                signals.append('hold')
                positions.append(0)
                continue
            
            current_rsi = self.df['rsi'].iloc[i]
            current_price = self.df['close'].iloc[i]
            sma20 = self.df['sma_20'].iloc[i]
            bb_lower = self.df['bb_lower'].iloc[i]
            bb_upper = self.df['bb_upper'].iloc[i]
            
            # 买入信号: RSI < 35 或价格跌破下布林带
            buy_condition = (
                (current_rsi < 35 or current_price < bb_lower) and
                current_position == 0
            )
            
            # 卖出信号: RSI > 65 或价格突破上布林带
            sell_condition = (
                (current_rsi > 65 or current_price > bb_upper) and
                current_position > 0
            )
            
            if buy_condition:
                signals.append('buy')
                current_position = 1
            elif sell_condition:
                signals.append('sell')
                current_position = 0
            else:
                signals.append('hold')
            
            positions.append(current_position)
        
        self.df['signal'] = signals
        self.df['position'] = positions
        
        return signals, positions
    
    def calculate_performance_metrics(self):
        """计算性能指标"""
        # 计算日收益率
        self.df['daily_return'] = self.df['close'].pct_change().fillna(0)
        
        # 计算策略收益率
        self.df['strategy_return'] = self.df['daily_return'] * self.df['position'].shift(1).fillna(0)
        
        # 计算累计收益率
        self.df['cumulative_return'] = (1 + self.df['strategy_return']).cumprod()
        self.df['buy_hold_return'] = (1 + self.df['daily_return']).cumprod()
        
        # 计算夏普比率
        strategy_returns = self.df['strategy_return'].dropna()
        if len(strategy_returns) > 0 and strategy_returns.std() > 0:
            risk_free_rate = 0.02 / 252
            excess_returns = strategy_returns - risk_free_rate
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        cumulative = self.df['cumulative_return']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() if len(drawdown) > 0 else 0.0
        
        # 计算波动率
        volatility = strategy_returns.std() * np.sqrt(252) if len(strategy_returns) > 0 else 0.0
        
        # 计算总收益
        total_return = (cumulative.iloc[-1] - 1) * 100 if len(cumulative) > 0 else 0.0
        
        return sharpe_ratio, max_drawdown, volatility, total_return
    
    def generate_signals_list(self):
        """生成信号列表"""
        signal_list = []
        for i, (date, signal) in enumerate(zip(self.df.index, self.df['signal'])):
            if signal in ['buy', 'sell']:
                signal_list.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "买入" if signal == 'buy' else "卖出",
                    "price": round(self.df['close'].iloc[i], 2),
                    "rsi": round(self.df['rsi'].iloc[i], 2)
                })
        return signal_list
    
    def create_visualization(self):
        """创建可视化图表"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 价格和布林带
        ax1.plot(self.df.index, self.df['close'], label='Close Price', color='black', linewidth=2)
        ax1.plot(self.df.index, self.df['bb_upper'], label='Upper BB', color='red', alpha=0.7)
        ax1.plot(self.df.index, self.df['bb_middle'], label='Middle BB', color='blue', alpha=0.7)
        ax1.plot(self.df.index, self.df['bb_lower'], label='Lower BB', color='green', alpha=0.7)
        ax1.fill_between(self.df.index, self.df['bb_upper'], self.df['bb_lower'], alpha=0.1)
        
        # 标记买卖信号
        buy_signals = self.df[self.df['signal'] == 'buy']
        sell_signals = self.df[self.df['signal'] == 'sell']
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='Buy Signal')
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='Sell Signal')
        
        ax1.set_title('0700.HK - Price & Bollinger Bands with Signals')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI
        ax2.plot(self.df.index, self.df['rsi'], color='purple', linewidth=2)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought (70)')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold (30)')
        ax2.axhline(y=65, color='orange', linestyle=':', alpha=0.7, label='Sell Trigger (65)')
        ax2.axhline(y=35, color='cyan', linestyle=':', alpha=0.7, label='Buy Trigger (35)')
        ax2.set_title('RSI (14)')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 移动平均线
        ax3.plot(self.df.index, self.df['close'], label='Close', color='black', linewidth=2)
        ax3.plot(self.df.index, self.df['sma_20'], label='SMA 20', color='blue', linewidth=1)
        ax3.plot(self.df.index, self.df['sma_50'], label='SMA 50', color='red', linewidth=1)
        ax3.set_title('Price & Moving Averages')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 累计收益率对比
        ax4.plot(self.df.index, (self.df['cumulative_return'] - 1) * 100, label='Strategy', color='green', linewidth=2)
        ax4.plot(self.df.index, (self.df['buy_hold_return'] - 1) * 100, label='Buy & Hold', color='blue', linewidth=2)
        ax4.set_title('Cumulative Returns (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/workspace/hk_technical_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_recommendations(self, rsi_avg, sharpe_ratio, max_drawdown, signals_count):
        """生成投资建议"""
        recommendations = []
        
        # 基于RSI的建议
        if rsi_avg > 65:
            recommendations.append("当前平均RSI偏高(>65)，市场处于超买状态，建议谨慎操作或考虑减仓")
        elif rsi_avg < 35:
            recommendations.append("当前平均RSI偏低(<35)，存在超卖机会，可关注反弹信号")
        else:
            recommendations.append("RSI处于中性区间(35-65)，适合趋势跟踪和均值回归策略")
        
        # 基于夏普比率的建议
        if sharpe_ratio > 1.5:
            recommendations.append("策略夏普比率优秀(>1.5)，风险调整后收益表现出色")
        elif sharpe_ratio > 1.0:
            recommendations.append("策略夏普比率良好(>1.0)，但仍有优化空间")
        elif sharpe_ratio > 0:
            recommendations.append("策略夏普比率偏低但为正，建议调整参数或更换策略")
        else:
            recommendations.append("策略夏普比率为负，建议重新评估策略有效性")
        
        # 基于信号数量的建议
        if signals_count == 0:
            recommendations.append("期间内未产生交易信号，建议调整策略参数以增加敏感度")
        elif signals_count < 3:
            recommendations.append("交易信号较少，策略较为保守，适合长期投资者")
        else:
            recommendations.append("产生多个交易信号，策略活跃度适中，需注意交易成本")
        
        # 当前技术面建议
        current_rsi = self.df['rsi'].iloc[-1]
        current_price = self.df['close'].iloc[-1]
        bb_upper = self.df['bb_upper'].iloc[-1]
        bb_lower = self.df['bb_lower'].iloc[-1]
        
        if current_rsi > 70:
            recommendations.append("技术警示: 当前RSI超买(>70)，短期调整风险增加")
        elif current_rsi < 30:
            recommendations.append("技术机会: 当前RSI超卖(<30)，可能迎来反弹机会")
        
        if current_price > bb_upper:
            recommendations.append("价格突破上布林带，注意短期回调风险")
        elif current_price < bb_lower:
            recommendations.append("价格跌破下布林带，可能存在超卖反弹机会")
        
        return recommendations[:5]  # 限制在5条以内
    
    def analyze(self):
        """主分析函数"""
        # 执行RSI均值回归策略
        signals, positions = self.rsi_mean_reversion_strategy()
        
        # 计算性能指标
        sharpe_ratio, max_drawdown, volatility, total_return = self.calculate_performance_metrics()
        
        # 生成信号列表
        signal_list = self.generate_signals_list()
        
        # 计算平均RSI
        rsi_avg = self.df['rsi'].mean()
        
        # 创建可视化
        self.create_visualization()
        
        # 生成建议
        recommendations = self.generate_recommendations(rsi_avg, sharpe_ratio, max_drawdown, len(signal_list))
        
        # 策略描述
        strategy_description = "RSI均值回归策略结合布林带突破，专注于超买超卖区间的反转机会"
        
        return {
            "discovered_strategy": strategy_description,
            "signals": signal_list,
            "rsi_avg": round(rsi_avg, 2),
            "sharpe": round(sharpe_ratio, 2),
            "max_drawdown": round(abs(max_drawdown) * 100, 2),
            "volatility": round(volatility * 100, 2),
            "total_return": round(total_return, 2),
            "recommendations": recommendations
        }

def main():
    # 输入数据
    stock_data = {
        "stocks": ["0700.HK"],
        "close_prices": [587.0, 592.5, 590.5, 593.0, 600.0, 614.5, 609.5, 599.0, 594.0, 596.5, 605.0, 600.5, 598.5, 592.5, 605.5, 617.5, 627.0, 633.5, 629.5, 643.5, 643.5, 645.0, 661.5, 642.0, 642.5, 641.0, 635.5, 648.5, 650.0, 644.0],
        "highs": [596.0, 597.0, 594.5, 597.0, 606.5, 621.0, 618.0, 614.5, 599.0, 605.0, 610.0, 608.5, 613.0, 605.0, 609.0, 619.0, 628.0, 639.0, 633.0, 649.0, 648.5, 649.5, 663.5, 664.5, 647.0, 643.5, 643.5, 651.0, 659.0, 653.0],
        "lows": [587.0, 583.0, 585.5, 589.5, 595.5, 608.0, 609.5, 595.0, 590.0, 594.0, 601.5, 599.0, 596.0, 591.0, 595.5, 605.0, 617.5, 628.0, 624.0, 642.0, 637.5, 640.5, 645.0, 635.5, 638.0, 634.0, 627.0, 628.0, 643.5, 640.0],
        "volumes": [17590658, 16359474, 15952765, 14290178, 19378950, 25694519, 20656474, 21263402, 21712370, 18234935, 15958837, 14808157, 15523985, 18003934, 19047729, 21815489, 19871460, 19193376, 18191860, 20780375, 16371242, 13339685, 22349048, 29989898, 20805608, 12899662, 15293080, 18440788, 17384258, 19504951]
    }
    
    # 创建技术分析代理
    analyst = HKTechnicalAnalyst(stock_data)
    
    # 执行分析
    result = analyst.analyze()
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result

if __name__ == "__main__":
    result = main()