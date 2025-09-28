#!/usr/bin/env python3
"""
港股交易执行代理 (Hong Kong Stock Trading Agent)
简化版本 - 无外部依赖
"""

import json
import math
import random

class HKStockTrader:
    """港股交易执行代理"""
    
    def __init__(self):
        # 港股交易成本参数
        self.commission_rate = 0.0025  # 0.25% 佣金
        self.stamp_duty = 0.001        # 0.1% 印花税
        self.trading_fee = 0.00005     # 0.005% 交易费
        self.settlement_fee = 5        # 固定结算费 HKD
        self.bid_ask_spread = 0.002    # 0.2% 滑点估算
        
        # 风险参数
        self.max_position_size = 0.3   # 单个标的最大仓位30%
        self.target_sharpe = 1.5       # 目标Sharpe比率
        self.risk_free_rate = 0.03     # 无风险利率3%
        
    def calculate_trading_cost(self, trade_value: float) -> float:
        """计算港股交易总成本"""
        commission = max(trade_value * self.commission_rate, 100)  # 最低100港币
        stamp_duty = trade_value * self.stamp_duty
        trading_fee = trade_value * self.trading_fee
        slippage = trade_value * self.bid_ask_spread
        
        total_cost = commission + stamp_duty + trading_fee + self.settlement_fee + slippage
        return total_cost / trade_value  # 返回成本率
        
    def optimize_position_size(self, signal_strength: float, balanced_score: float, 
                             expected_volatility: float) -> float:
        """基于Kelly公式和风险调整优化仓位大小"""
        if expected_volatility <= 0:
            return 0
            
        # 信号强度调整 (-1 到 1)
        adjusted_signal = signal_strength * balanced_score
        
        # 预期超额收益率估算
        expected_excess_return = abs(adjusted_signal) * 0.1  # 假设10%潜在收益
        
        # Kelly比例计算
        kelly_fraction = expected_excess_return / (expected_volatility ** 2)
        
        # 风险调整：限制最大仓位
        optimal_size = min(abs(kelly_fraction), self.max_position_size)
        
        # 考虑交易成本的调整
        cost_adjustment = 1 - self.calculate_trading_cost(100000)  # 基于10万港币计算
        optimal_size *= cost_adjustment
        
        return optimal_size if adjusted_signal > 0 else -optimal_size
        
    def calculate_sharpe_contribution(self, position_size: float, expected_return: float,
                                    volatility: float) -> float:
        """计算该订单对组合Sharpe比率的贡献"""
        if volatility <= 0:
            return 0
            
        excess_return = expected_return - self.risk_free_rate
        sharpe_contribution = (excess_return * abs(position_size)) / volatility
        
        # 标准化到-1到1区间
        return max(-1, min(1, sharpe_contribution / 2))
        
    def monte_carlo_simulation(self, position_size: float, expected_return: float,
                             volatility: float, num_simulations: int = 1000) -> dict:
        """蒙特卡洛风险模拟（简化版）"""
        random.seed(42)
        
        returns = []
        for _ in range(num_simulations):
            # 简化的正态分布近似
            u1, u2 = random.random(), random.random()
            z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            random_return = expected_return + volatility * z
            portfolio_return = position_size * random_return
            returns.append(portfolio_return)
        
        returns.sort()
        
        return {
            "var_95": returns[int(0.05 * len(returns))],      # 95% VaR
            "var_99": returns[int(0.01 * len(returns))],      # 99% VaR
            "expected_return": sum(returns) / len(returns),
            "volatility": math.sqrt(sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns)),
            "max_drawdown": min(returns),
            "probability_profit": sum(1 for r in returns if r > 0) / len(returns)
        }
        
    def analyze_and_trade(self, input_data: dict) -> dict:
        """主要分析和交易决策函数"""
        
        # 解析输入数据
        balanced_score = input_data.get("balanced_score", 0)
        signals = input_data.get("signals", [])
        close_prices = input_data.get("close_prices", [])
        symbols = input_data.get("symbols", [f"HK_{i:04d}" for i in range(len(signals))])
        
        if len(signals) != len(close_prices):
            raise ValueError("信号数量与价格数量不匹配")
            
        orders = []
        total_expected_return = 0
        total_risk = 0
        
        # 分析每个信号
        for i, (signal, price, symbol) in enumerate(zip(signals, close_prices, symbols)):
            if signal == 0:  # 跳过无信号
                continue
                
            # 估算波动率（简化版本，实际应用中需要历史数据）
            estimated_volatility = 0.25  # 假设25%年化波动率
            
            # 优化仓位大小
            position_size = self.optimize_position_size(
                signal, balanced_score, estimated_volatility
            )
            
            if abs(position_size) < 0.01:  # 忽略过小仓位
                continue
                
            # 预期收益计算
            expected_return = signal * balanced_score * 0.08  # 假设8%基础收益潜力
            
            # Sharpe贡献计算
            sharpe_contrib = self.calculate_sharpe_contribution(
                position_size, expected_return, estimated_volatility
            )
            
            # 蒙特卡洛模拟
            mc_results = self.monte_carlo_simulation(
                position_size, expected_return, estimated_volatility
            )
            
            # 生成订单
            order = {
                "symbol": symbol,
                "action": "BUY" if position_size > 0 else "SELL",
                "position_size": round(abs(position_size), 4),
                "price": price,
                "expected_return": round(expected_return, 4),
                "sharpe_contribution": round(sharpe_contrib, 4),
                "trading_cost_rate": round(self.calculate_trading_cost(price * 1000), 6),
                "monte_carlo": {k: round(v, 6) for k, v in mc_results.items()}
            }
            
            orders.append(order)
            total_expected_return += expected_return * abs(position_size)
            total_risk += (estimated_volatility * abs(position_size)) ** 2
            
        # 计算组合总体指标
        total_risk = math.sqrt(total_risk) if total_risk > 0 else 0
        portfolio_sharpe = (total_expected_return - self.risk_free_rate) / total_risk if total_risk > 0 else 0
        
        # 生成执行建议
        recommendations = self._generate_recommendations(orders, portfolio_sharpe, balanced_score)
        
        return {
            "orders": orders,
            "expected_returns": round(total_expected_return, 4),
            "sharpe_contribution": round(max(-1, min(1, portfolio_sharpe / self.target_sharpe)), 4),
            "portfolio_sharpe": round(portfolio_sharpe, 4),
            "total_risk": round(total_risk, 4),
            "recommendations": recommendations
        }
        
    def _generate_recommendations(self, orders: list, portfolio_sharpe: float, 
                                balanced_score: float) -> list:
        """生成执行建议"""
        recommendations = []
        
        if portfolio_sharpe < 1.0:
            recommendations.append("⚠️ 组合Sharpe比率偏低，建议减少仓位或等待更好机会")
            
        if balanced_score < 0.3:
            recommendations.append("📊 信号强度较弱，建议采用较小仓位进行试探性交易")
            
        if len(orders) > 5:
            recommendations.append("🎯 订单数量较多，注意分散化执行以减少市场冲击")
            
        total_cost = sum(order.get("trading_cost_rate", 0) for order in orders)
        if total_cost > 0.01:
            recommendations.append(f"💰 总交易成本较高({total_cost:.2%})，考虑合并小额订单")
            
        recommendations.append("🕐 港股T+2结算，注意资金安排和流动性管理")
        
        if portfolio_sharpe > 1.5:
            recommendations.append("✅ 优秀的风险调整收益预期，建议积极执行")
            
        return recommendations[:5]  # 限制最多5条建议


def main():
    """示例运行"""
    trader = HKStockTrader()
    
    # 示例数据
    sample_data = {
        "balanced_score": 0.6,
        "signals": [1, -1, 0, 1, -1],
        "close_prices": [100, 102, 98, 105, 95],
        "symbols": ["0700.HK", "0941.HK", "0005.HK", "2318.HK", "1299.HK"]
    }
    
    try:
        result = trader.analyze_and_trade(sample_data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n=== 关键洞见 ===")
        print(f"预期组合Sharpe比率: {result['portfolio_sharpe']:.3f}")
        print(f"预期年化收益: {result['expected_returns']:.2%}")
        print(f"总风险水平: {result['total_risk']:.2%}")
        
    except Exception as e:
        print(f"分析错误: {e}")


if __name__ == "__main__":
    main()