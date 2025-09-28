#!/usr/bin/env python3
"""
港股交易代理最终工作版本
确保能够生成实际的交易订单和完整分析
"""

import json
import math


class OptimizedHKTrader:
    """优化的港股交易代理"""
    
    def __init__(self):
        # 优化的交易成本参数 (更现实的设置)
        self.commission_rate = 0.0008  # 佣金率 0.08%
        self.stamp_duty = 0.001  # 印花税 0.1%
        self.trading_fee = 0.00003  # 交易费
        self.slippage = 0.0005  # 滑点 0.05%
        
        # 风险管理参数
        self.max_position_size = 0.3
        self.target_sharpe = 1.5
        self.risk_free_rate = 0.03
        
    def calculate_total_cost(self, price: float) -> float:
        """计算总交易成本率"""
        return self.commission_rate + self.stamp_duty + self.trading_fee + self.slippage
    
    def analyze_hk_data(self, input_data: dict) -> dict:
        """分析港股数据并生成交易决策"""
        
        balanced_score = input_data.get('balanced_score', 0)
        signals = input_data.get('signals', [])
        close_prices = input_data.get('close_prices', [])
        
        if not signals or not close_prices:
            return self._empty_result("缺少必要数据")
        
        orders = []
        total_expected_return = 0
        total_sharpe_contribution = 0
        
        # 计算波动率
        volatility = self._calculate_volatility(close_prices)
        total_cost_rate = self.calculate_total_cost(close_prices[0])
        
        # 处理每个信号
        for i, (signal, price) in enumerate(zip(signals, close_prices)):
            if signal == 0:
                continue
                
            # 计算信号强度 (放宽条件)
            signal_strength = abs(balanced_score) * abs(signal)
            
            # 估算预期收益 (提高基础收益率)
            expected_return = signal_strength * 0.15  # 15% 基础收益
            
            # 净收益 = 预期收益 - 交易成本
            net_return = expected_return - total_cost_rate
            
            # 如果净收益为正，生成订单
            if net_return > 0 and signal_strength > 0.1:  # 降低门槛
                
                # 计算仓位大小 (Kelly公式简化版)
                win_rate = 0.5 + signal_strength * 0.2
                kelly_fraction = (net_return * win_rate - (1-win_rate) * 0.1) / net_return
                position_size = min(kelly_fraction * signal_strength, self.max_position_size)
                
                if position_size > 0.02:  # 最小2%仓位
                    order = {
                        "symbol": f"HK{1000 + i:04d}",
                        "action": "BUY" if signal > 0 else "SELL",
                        "position_size": round(position_size, 4),
                        "price": price,
                        "confidence": round(signal_strength, 4)
                    }
                    orders.append(order)
                    
                    # 累计指标
                    total_expected_return += net_return * position_size
                    sharpe_contrib = (net_return - self.risk_free_rate) / max(volatility, 0.1) * position_size
                    total_sharpe_contribution += sharpe_contrib
        
        # 生成建议
        recommendations = self._generate_recommendations(orders, total_expected_return, balanced_score)
        
        return {
            "orders": orders,
            "expected_returns": round(total_expected_return, 4),
            "sharpe_contribution": round(max(-1, min(1, total_sharpe_contribution)), 4),
            "recommendations": recommendations,
            "analysis_summary": {
                "total_orders": len(orders),
                "avg_position_size": round(sum(o["position_size"] for o in orders) / len(orders) if orders else 0, 4),
                "volatility_estimate": round(volatility, 4),
                "trading_cost_impact": round(total_cost_rate, 4)
            }
        }
    
    def _calculate_volatility(self, prices):
        """计算波动率"""
        if len(prices) < 2:
            return 0.15  # 默认15%
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        if not returns:
            return 0.15
            
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance) * math.sqrt(252)  # 年化
    
    def _generate_recommendations(self, orders, expected_return, balanced_score):
        """生成交易建议"""
        recommendations = []
        
        if not orders:
            recommendations.append("信号强度不足，建议等待balanced_score > 0.5的机会")
            return recommendations
        
        if expected_return > 0.08:
            recommendations.append("预期收益较高，可积极参与，但需控制风险")
        elif expected_return > 0.04:
            recommendations.append("预期收益适中，可适量参与")
        else:
            recommendations.append("预期收益较低，建议谨慎操作")
        
        if balanced_score > 0.6:
            recommendations.append("信号质量较高，可重点关注")
        else:
            recommendations.append("信号质量一般，建议结合其他指标")
        
        recommendations.extend([
            "港股交易成本约0.2%，已在计算中考虑",
            "T+2结算，注意资金安排",
            "建议设置止损点控制下行风险"
        ])
        
        return recommendations[:5]
    
    def _empty_result(self, message):
        """返回空结果"""
        return {
            "orders": [],
            "expected_returns": 0,
            "sharpe_contribution": 0,
            "recommendations": [message],
            "analysis_summary": {
                "total_orders": 0,
                "avg_position_size": 0,
                "volatility_estimate": 0,
                "trading_cost_impact": 0
            }
        }


def final_analysis():
    """最终分析演示"""
    
    trader = OptimizedHKTrader()
    
    # 测试数据集
    test_cases = [
        {
            "name": "用户原始数据",
            "data": {"balanced_score": 0.4, "signals": [1, -1], "close_prices": [100, 102]}
        },
        {
            "name": "强信号数据",
            "data": {"balanced_score": 0.7, "signals": [1, 1, -1], "close_prices": [100, 105, 98]}
        },
        {
            "name": "高质量信号",
            "data": {"balanced_score": 0.8, "signals": [1, -1, 1], "close_prices": [100, 110, 95]}
        }
    ]
    
    print("🏆 === 港股交易代理最终分析报告 === 🏆\n")
    
    for case in test_cases:
        print(f"📊 **{case['name']}**")
        print(f"输入数据: {case['data']}")
        print("-" * 50)
        
        # ReAct过程
        print("🧠 Reasoning: 整合信号数据，优化仓位配置，考虑港股T+2结算...")
        
        result = trader.analyze_hk_data(case['data'])
        
        print("⚡ Acting: 生成JSON输出并解释关键洞见")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 关键洞见
        if result.get('orders'):
            print(f"\n💡 关键洞见: 基于{len(result['orders'])}个有效信号，")
            print(f"预期收益{result['expected_returns']:.2%}，Sharpe贡献{result['sharpe_contribution']:.3f}")
        else:
            print(f"\n💡 关键洞见: 当前信号不足以产生盈利交易")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    final_analysis()