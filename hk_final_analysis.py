#!/usr/bin/env python3
"""
Technical Analysis Agent for Hong Kong Stocks - Final Analysis
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
    
    def momentum_trend_strategy(self):
        """动量趋势策略 - 基于价格动量和技术指标"""
        # 计算技术指标
        rsi = self.calculate_rsi(14)
        sma_5 = self.calculate_sma(5)
        sma_10 = self.calculate_sma(10)
        sma_20 = self.calculate_sma(20)
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands()
        
        # 添加到数据框
        self.df['rsi'] = rsi
        self.df['sma_5'] = sma_5
        self.df['sma_10'] = sma_10
        self.df['sma_20'] = sma_20
        self.df['bb_upper'] = upper_bb
        self.df['bb_middle'] = middle_bb
        self.df['bb_lower'] = lower_bb
        
        # 计算价格动量
        self.df['price_change'] = self.df['close'].pct_change()
        self.df['momentum_3'] = self.df['close'].pct_change(3)  # 3日动量
        
        # 生成信号
        signals = []
        positions = []
        current_position = 0
        
        for i in range(len(self.df)):
            if i < 20:  # 等待指标稳定
                signals.append('hold')
                positions.append(0)
                continue
            
            current_price = self.df['close'].iloc[i]
            current_rsi = self.df['rsi'].iloc[i]
            sma5 = self.df['sma_5'].iloc[i] if not pd.isna(self.df['sma_5'].iloc[i]) else current_price
            sma10 = self.df['sma_10'].iloc[i] if not pd.isna(self.df['sma_10'].iloc[i]) else current_price
            sma20 = self.df['sma_20'].iloc[i] if not pd.isna(self.df['sma_20'].iloc[i]) else current_price
            bb_upper = self.df['bb_upper'].iloc[i] if not pd.isna(self.df['bb_upper'].iloc[i]) else current_price * 1.02
            bb_lower = self.df['bb_lower'].iloc[i] if not pd.isna(self.df['bb_lower'].iloc[i]) else current_price * 0.98
            momentum_3 = self.df['momentum_3'].iloc[i] if not pd.isna(self.df['momentum_3'].iloc[i]) else 0
            
            # 买入信号 (更宽松的条件):
            # 1. 价格回调到短期均线附近 + RSI不太高
            # 2. 或者强势突破 + 动量向上
            # 3. 或者超卖反弹
            buy_condition = (
                current_position == 0 and (
                    # 回调买入
                    (current_price <= sma10 and current_rsi < 65 and momentum_3 > -0.05) or
                    # 突破买入
                    (current_price > sma5 and sma5 > sma10 and momentum_3 > 0.02) or
                    # 超卖反弹
                    (current_price < bb_lower * 1.01 and current_rsi < 60) or
                    # 均线多头排列
                    (sma5 > sma10 > sma20 and current_rsi < 70)
                )
            )
            
            # 卖出信号:
            # 1. RSI明显超买
            # 2. 价格大幅偏离均线
            # 3. 负动量加速
            sell_condition = (
                current_position > 0 and (
                    current_rsi > 80 or  # 极度超买
                    current_price > bb_upper * 1.01 or  # 大幅突破上轨
                    momentum_3 < -0.03 or  # 负动量加速
                    (current_price < sma5 and sma5 < sma10)  # 均线转空
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
        
        # 计算胜率
        winning_trades = len([r for r in strategy_returns if r > 0])
        total_trades = len([r for r in strategy_returns if r != 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return sharpe_ratio, max_drawdown, volatility, total_return, win_rate
    
    def generate_signals_list(self):
        """生成信号列表"""
        signal_list = []
        for i, (date, signal) in enumerate(zip(self.df.index, self.df['signal'])):
            if signal in ['buy', 'sell']:
                signal_list.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "买入" if signal == 'buy' else "卖出",
                    "price": round(self.df['close'].iloc[i], 2),
                    "rsi": round(self.df['rsi'].iloc[i], 2),
                    "momentum": round(self.df['momentum_3'].iloc[i] * 100, 2) if not pd.isna(self.df['momentum_3'].iloc[i]) else 0
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
        ax1.plot(self.df.index, self.df['sma_5'], label='SMA 5', color='orange', alpha=0.8)
        ax1.fill_between(self.df.index, self.df['bb_upper'], self.df['bb_lower'], alpha=0.1)
        
        # 标记买卖信号
        buy_signals = self.df[self.df['signal'] == 'buy']
        sell_signals = self.df[self.df['signal'] == 'sell']
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='Buy Signal')
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='Sell Signal')
        
        ax1.set_title('0700.HK (Tencent) - Momentum Strategy Signals')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI
        ax2.plot(self.df.index, self.df['rsi'], color='purple', linewidth=2)
        ax2.axhline(y=80, color='r', linestyle='--', alpha=0.7, label='Extreme Overbought (80)')
        ax2.axhline(y=20, color='g', linestyle='--', alpha=0.7, label='Extreme Oversold (20)')
        ax2.axhline(y=70, color='orange', linestyle=':', alpha=0.7, label='Overbought (70)')
        ax2.axhline(y=30, color='cyan', linestyle=':', alpha=0.7, label='Oversold (30)')
        ax2.set_title('RSI (14) with Dynamic Thresholds')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 动量指标
        ax3.bar(self.df.index, self.df['momentum_3'] * 100, alpha=0.6, color='gray')
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax3.axhline(y=2, color='g', linestyle='--', alpha=0.7, label='Bullish Momentum (2%)')
        ax3.axhline(y=-3, color='r', linestyle='--', alpha=0.7, label='Bearish Momentum (-3%)')
        ax3.set_title('3-Day Price Momentum (%)')
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
    
    def generate_recommendations(self, rsi_avg, sharpe_ratio, max_drawdown, signals_count, total_return, win_rate):
        """生成投资建议"""
        recommendations = []
        
        # 基于当前技术状态的建议
        current_rsi = self.df['rsi'].iloc[-1]
        current_momentum = self.df['momentum_3'].iloc[-1] * 100
        current_price = self.df['close'].iloc[-1]
        sma5 = self.df['sma_5'].iloc[-1]
        sma10 = self.df['sma_10'].iloc[-1]
        
        if current_rsi > 75:
            recommendations.append(f"技术警示：当前RSI达{current_rsi:.1f}，处于超买状态，建议谨慎操作或考虑减仓")
        elif current_rsi < 45:
            recommendations.append(f"技术机会：当前RSI为{current_rsi:.1f}，相对较低，可关注反弹机会")
        else:
            recommendations.append(f"技术中性：当前RSI为{current_rsi:.1f}，处于合理区间，可根据其他指标操作")
        
        # 基于动量的建议
        if current_momentum > 3:
            recommendations.append(f"动量强劲：3日涨幅{current_momentum:.1f}%，上升动能良好，可考虑趋势跟踪")
        elif current_momentum < -3:
            recommendations.append(f"动量转弱：3日跌幅{abs(current_momentum):.1f}%，注意下行风险，考虑减仓或止损")
        else:
            recommendations.append(f"动量平稳：3日变动{current_momentum:.1f}%，市场处于整理状态")
        
        # 基于策略表现的建议
        if sharpe_ratio > 1.5:
            recommendations.append(f"策略优秀：夏普比率{sharpe_ratio:.2f}，风险调整后收益表现出色")
        elif sharpe_ratio > 1.0:
            recommendations.append(f"策略良好：夏普比率{sharpe_ratio:.2f}，表现良好，可持续使用")
        elif sharpe_ratio > 0.5:
            recommendations.append(f"策略一般：夏普比率{sharpe_ratio:.2f}，需要进一步优化参数")
        else:
            recommendations.append(f"策略待优化：夏普比率{sharpe_ratio:.2f}，建议调整策略或暂停使用")
        
        # 基于均线排列的趋势判断
        if sma5 > sma10 and current_price > sma5:
            recommendations.append("均线多头排列，价格位于均线之上，短期趋势向好")
        elif sma5 < sma10 and current_price < sma5:
            recommendations.append("均线空头排列，价格位于均线之下，短期趋势偏弱")
        else:
            recommendations.append("均线交织，市场方向不明确，建议观望或轻仓操作")
        
        # 风险管理建议
        if abs(max_drawdown) > 10:
            recommendations.append(f"风险提示：最大回撤{abs(max_drawdown):.1f}%，建议设置止损点控制风险")
        
        return recommendations[:5]  # 限制在5条以内
    
    def analyze(self):
        """主分析函数"""
        # 执行动量趋势策略
        signals, positions = self.momentum_trend_strategy()
        
        # 计算性能指标
        sharpe_ratio, max_drawdown, volatility, total_return, win_rate = self.calculate_performance_metrics()
        
        # 生成信号列表
        signal_list = self.generate_signals_list()
        
        # 计算平均RSI
        rsi_avg = self.df['rsi'].mean()
        
        # 创建可视化
        self.create_visualization()
        
        # 生成建议
        recommendations = self.generate_recommendations(rsi_avg, sharpe_ratio, max_drawdown, len(signal_list), total_return, win_rate)
        
        # 策略描述
        strategy_description = "动量趋势策略：结合RSI、移动平均线和价格动量的多因子模型，适应腾讯股价波动特征"
        
        return {
            "discovered_strategy": strategy_description,
            "signals": signal_list,
            "rsi_avg": round(rsi_avg, 2),
            "sharpe": round(sharpe_ratio, 2),
            "max_drawdown": round(abs(max_drawdown) * 100, 2),
            "volatility": round(volatility * 100, 2),
            "total_return": round(total_return, 2),
            "win_rate": round(win_rate, 2),
            "recommendations": recommendations
        }

def main():
    # 腾讯(0700.HK)输入数据
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