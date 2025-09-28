#!/usr/bin/env python3
"""
Technical Analysis Agent for Hong Kong Stocks
专门针对港股的量化分析AI代理 - 技术分析代理
目标: 高Sharpe Ratio (>1.5) 策略优化
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
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
        return rsi
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        exp1 = self.df['close'].ewm(span=fast).mean()
        exp2 = self.df['close'].ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """计算布林带"""
        sma = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def momentum_strategy(self):
        """动量策略 - 基于RSI和MACD的组合信号"""
        # 计算技术指标
        rsi = self.calculate_rsi()
        macd, signal_line, histogram = self.calculate_macd()
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands()
        
        # 添加到数据框
        self.df['rsi'] = rsi
        self.df['macd'] = macd
        self.df['macd_signal'] = signal_line
        self.df['macd_histogram'] = histogram
        self.df['bb_upper'] = upper_bb
        self.df['bb_middle'] = middle_bb
        self.df['bb_lower'] = lower_bb
        
        # 生成信号
        signals = []
        positions = []
        current_position = 0
        
        for i in range(len(self.df)):
            if i < 26:  # 等待指标稳定
                signals.append('hold')
                positions.append(0)
                continue
            
            # 获取当前指标值
            current_rsi = self.df['rsi'].iloc[i] if not pd.isna(self.df['rsi'].iloc[i]) else 50
            current_macd = self.df['macd'].iloc[i] if not pd.isna(self.df['macd'].iloc[i]) else 0
            current_signal = self.df['macd_signal'].iloc[i] if not pd.isna(self.df['macd_signal'].iloc[i]) else 0
            prev_macd = self.df['macd'].iloc[i-1] if not pd.isna(self.df['macd'].iloc[i-1]) else 0
            prev_signal = self.df['macd_signal'].iloc[i-1] if not pd.isna(self.df['macd_signal'].iloc[i-1]) else 0
            current_price = self.df['close'].iloc[i]
            bb_middle = self.df['bb_middle'].iloc[i] if not pd.isna(self.df['bb_middle'].iloc[i]) else current_price
            bb_upper = self.df['bb_upper'].iloc[i] if not pd.isna(self.df['bb_upper'].iloc[i]) else current_price * 1.02
            
            # 买入信号: RSI < 40 且 MACD上穿信号线 且价格低于中轨
            buy_condition = (
                current_rsi < 40 and
                current_macd > current_signal and
                prev_macd <= prev_signal and
                current_price <= bb_middle and
                current_position == 0
            )
            
            # 卖出信号: RSI > 60 或 MACD下穿信号线 或价格接近上布林带
            sell_condition = (
                current_position > 0 and (
                    current_rsi > 60 or
                    (current_macd < current_signal and prev_macd >= prev_signal) or
                    current_price >= bb_upper * 0.98
                )
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
    
    def calculate_returns_and_sharpe(self):
        """计算收益率和夏普比率"""
        # 计算日收益率
        self.df['daily_return'] = self.df['close'].pct_change().fillna(0)
        
        # 计算策略收益率
        self.df['strategy_return'] = self.df['daily_return'] * self.df['position'].shift(1).fillna(0)
        
        # 计算累计收益率
        self.df['cumulative_return'] = (1 + self.df['strategy_return']).cumprod()
        self.df['buy_hold_return'] = (1 + self.df['daily_return']).cumprod()
        
        # 计算夏普比率 (假设无风险利率为2%)
        risk_free_rate = 0.02 / 252  # 日化无风险利率
        strategy_returns = self.df['strategy_return'].dropna()
        
        if len(strategy_returns) == 0 or strategy_returns.std() == 0:
            return 0.0
            
        excess_returns = strategy_returns - risk_free_rate
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        
        if std_excess == 0:
            return 0.0
            
        sharpe_ratio = mean_excess / std_excess * np.sqrt(252)
        
        return sharpe_ratio
    
    def generate_signals_list(self):
        """生成信号列表"""
        signal_list = []
        for i, (date, signal) in enumerate(zip(self.df.index, self.df['signal'])):
            if signal in ['buy', 'sell']:
                signal_list.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "买入" if signal == 'buy' else "卖出",
                    "price": round(self.df['close'].iloc[i], 2),
                    "rsi": round(self.df['rsi'].iloc[i], 2) if not pd.isna(self.df['rsi'].iloc[i]) else None
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
        ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='Buy Signal')
        ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='Sell Signal')
        
        ax1.set_title('0700.HK - Price & Bollinger Bands with Signals')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI
        ax2.plot(self.df.index, self.df['rsi'], color='purple', linewidth=2)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought (70)')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold (30)')
        ax2.set_title('RSI (14)')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # MACD
        ax3.plot(self.df.index, self.df['macd'], label='MACD', color='blue', linewidth=2)
        ax3.plot(self.df.index, self.df['macd_signal'], label='Signal Line', color='red', linewidth=2)
        ax3.bar(self.df.index, self.df['macd_histogram'], label='Histogram', alpha=0.6, color='gray')
        ax3.set_title('MACD')
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
        
        return None
    
    def analyze(self):
        """主分析函数"""
        # 执行动量策略
        signals, positions = self.momentum_strategy()
        
        # 计算夏普比率
        sharpe_ratio = self.calculate_returns_and_sharpe()
        
        # 生成信号列表
        signal_list = self.generate_signals_list()
        
        # 计算平均RSI
        rsi_avg = self.df['rsi'].mean()
        
        # 创建可视化
        self.create_visualization()
        
        # 风险评估
        max_drawdown = self.calculate_max_drawdown()
        volatility = self.df['strategy_return'].std() * np.sqrt(252)
        
        # 生成建议
        recommendations = self.generate_recommendations(rsi_avg, sharpe_ratio, max_drawdown)
        
        # 策略描述
        strategy_description = "基于RSI动量过滤和MACD趋势确认的组合策略，结合布林带进行入场时机优化"
        
        return {
            "discovered_strategy": strategy_description,
            "signals": signal_list,
            "rsi_avg": round(rsi_avg, 2),
            "sharpe": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "volatility": round(volatility * 100, 2),
            "total_return": round((self.df['cumulative_return'].iloc[-1] - 1) * 100, 2),
            "recommendations": recommendations
        }
    
    def calculate_max_drawdown(self):
        """计算最大回撤"""
        cumulative = self.df['cumulative_return']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def generate_recommendations(self, rsi_avg, sharpe_ratio, max_drawdown):
        """生成投资建议"""
        recommendations = []
        
        # 基于RSI的建议
        if rsi_avg > 60:
            recommendations.append("当前平均RSI偏高，市场可能处于超买状态，建议谨慎操作")
        elif rsi_avg < 40:
            recommendations.append("当前平均RSI偏低，可能存在超卖机会，关注反弹信号")
        else:
            recommendations.append("RSI处于中性区间，适合趋势跟踪策略")
        
        # 基于夏普比率的建议
        if sharpe_ratio > 1.5:
            recommendations.append("策略夏普比率优秀，风险调整后收益表现良好")
        elif sharpe_ratio > 1.0:
            recommendations.append("策略夏普比率良好，但仍有优化空间")
        else:
            recommendations.append("策略夏普比率偏低，建议调整参数或更换策略")
        
        # 基于最大回撤的风险提示
        if abs(max_drawdown) > 0.15:
            recommendations.append("最大回撤较大，建议设置更严格的止损机制")
        else:
            recommendations.append("最大回撤控制良好，风险管理有效")
        
        # 技术面警示
        current_rsi = self.df['rsi'].iloc[-1]
        if current_rsi > 70:
            recommendations.append("技术警示: 当前RSI超买，短期调整风险增加")
        elif current_rsi < 30:
            recommendations.append("技术警示: 当前RSI超卖，可能迎来反弹机会")
        
        # 趋势建议
        recent_macd = self.df['macd'].iloc[-3:].mean()
        recent_signal = self.df['macd_signal'].iloc[-3:].mean()
        if recent_macd > recent_signal:
            recommendations.append("MACD显示上升趋势，维持多头思维")
        else:
            recommendations.append("MACD显示下降趋势，注意趋势转换风险")
        
        return recommendations[:5]  # 限制在5条以内

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