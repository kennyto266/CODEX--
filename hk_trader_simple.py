#!/usr/bin/env python3
"""
港股交易代理 (HK Stock Trading Agent) - 简化版
专门针对港股的量化分析AI代理，追求高Sharpe Ratio的交易策略
"""

import json
import math


class HKStockTrader:
    """港股交易代理主类"""
    
    def __init__(self):
        # 港股交易成本参数
        self.commission_rate = 0.0025  # 佣金率 0.25%
        self.stamp_duty = 0.0013  # 印花税 0.13%
        self.trading_fee = 0.00005  # 交易费 0.005%
        self.settlement_fee = 5  # 结算费 HKD 5
        self.slippage = 0.001  # 滑点 0.1%
        
        # 风险管理参数
        self.max_position_size = 0.25  # 单个股票最大仓位
        self.target_sharpe = 1.5  # 目标Sharpe Ratio
        self.risk_free_rate = 0.03  # 无风险收益率 3%
        self.min_signal_threshold = 0.05  # 最小信号强度阈值 (降低以允许更多交易)
        
    def calculate_trading_cost(self, price: float, quantity: float = 1000) -> float:
        """计算港股交易成本"""
        transaction_value = price * quantity
        
        # 佣金（最低HKD 100）
        commission = max(100, transaction_value * self.commission_rate)
        
        # 印花税（买卖双方各付，向上取整到最近的分）
        stamp_duty = math.ceil(transaction_value * self.stamp_duty * 100) / 100
        
        # 交易费
        trading_fee = transaction_value * self.trading_fee
        
        # 总成本
        total_cost = commission + stamp_duty + trading_fee + self.settlement_fee
        
        return total_cost / transaction_value  # 返回成本率
    
    def calculate_volatility(self, prices):
        """计算价格波动率"""
        if len(prices) < 2:
            return 0.2  # 默认波动率
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        if not returns:
            return 0.2
        
        # 计算标准差
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        # 年化波动率
        return std_dev * math.sqrt(252)
    
    def calculate_position_size(self, signal_strength: float, volatility: float, 
                              expected_return: float) -> float:
        """基于Kelly公式和风险管理计算仓位大小"""
        if expected_return <= 0:
            return 0
        
        # 简化的Kelly公式计算
        win_rate = 0.5 + signal_strength * 0.3  # 基于信号强度调整胜率
        loss_rate = 1 - win_rate
        odds = expected_return / volatility if volatility > 0 else 0
        
        kelly_fraction = (odds * win_rate - loss_rate) / odds if odds > 0 else 0
        
        # 应用风险管理限制
        kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
        
        # 根据信号强度调整
        position_size = kelly_fraction * signal_strength
        
        return round(position_size, 4)
    
    def calculate_sharpe_contribution(self, expected_return: float, 
                                    volatility: float, position_size: float) -> float:
        """计算对Sharpe Ratio的贡献"""
        if volatility <= 0:
            return 0
        
        excess_return = expected_return - self.risk_free_rate
        sharpe_contribution = (excess_return / volatility) * position_size
        
        # 标准化到 -1 到 1 范围
        return max(-1, min(1, sharpe_contribution / 2))
    
    def generate_orders(self, input_data: dict) -> dict:
        """
        基于输入数据生成交易订单
        
        Args:
            input_data: 包含 balanced_score, signals, close_prices 等的字典
        
        Returns:
            包含订单、预期收益、Sharpe贡献值和建议的字典
        """
        try:
            # 解析输入数据
            balanced_score = input_data.get('balanced_score', 0)
            signals = input_data.get('signals', [])
            close_prices = input_data.get('close_prices', [])
            
            if not signals or not close_prices:
                raise ValueError("缺少必要的信号或价格数据")
            
            # 确保数据长度一致
            min_length = min(len(signals), len(close_prices))
            signals = signals[:min_length]
            close_prices = close_prices[:min_length]
            
            orders = []
            total_expected_return = 0
            total_sharpe_contribution = 0
            
            # 计算价格波动率
            volatility = self.calculate_volatility(close_prices)
            
            # 处理每个信号
            for i, (signal, price) in enumerate(zip(signals, close_prices)):
                if signal == 0:  # 无信号，跳过
                    continue
                
                # 计算信号强度
                signal_strength = abs(balanced_score) * abs(signal)
                
                # 检查信号强度是否达到最小阈值
                if signal_strength < self.min_signal_threshold:
                    continue
                
                # 估算预期收益 (调整为更现实的预期)
                base_return = signal * signal_strength * 0.12  # 基础预期收益12%
                expected_return = abs(base_return)  # 使用绝对值确保为正
                
                # 考虑交易成本
                trading_cost = self.calculate_trading_cost(price)
                net_expected_return = expected_return - trading_cost
                
                # 只有净预期收益为正才考虑交易
                if net_expected_return > 0:
                    # 计算仓位大小
                    position_size = self.calculate_position_size(
                        signal_strength, volatility, net_expected_return
                    )
                    
                    if position_size > 0.01:  # 最小仓位阈值
                        # 创建订单
                        action = "BUY" if signal > 0 else "SELL"
                        order = {
                            "symbol": f"HK{1000 + i:04d}",  # 模拟港股代码
                            "action": action,
                            "position_size": position_size,
                            "price": price,
                            "confidence": round(signal_strength, 4)
                        }
                        orders.append(order)
                        
                        # 累计指标
                        total_expected_return += net_expected_return * position_size
                        total_sharpe_contribution += self.calculate_sharpe_contribution(
                            net_expected_return, volatility, position_size
                        )
            
            # 生成建议
            recommendations = self._generate_recommendations(
                orders, total_expected_return, volatility, balanced_score
            )
            
            # 构建输出
            result = {
                "orders": orders,
                "expected_returns": round(total_expected_return, 4),
                "sharpe_contribution": round(total_sharpe_contribution, 4),
                "recommendations": recommendations,
                "analysis_summary": {
                    "total_orders": len(orders),
                    "avg_position_size": round(sum(o["position_size"] for o in orders) / len(orders) if orders else 0, 4),
                    "volatility_estimate": round(volatility, 4),
                    "trading_cost_impact": round(self.calculate_trading_cost(close_prices[0] if close_prices else 100), 4)
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"分析过程中出现错误: {str(e)}",
                "orders": [],
                "expected_returns": 0,
                "sharpe_contribution": 0,
                "recommendations": ["请检查输入数据格式"]
            }
    
    def _generate_recommendations(self, orders: list, expected_return: float, 
                                volatility: float, balanced_score: float) -> list:
        """生成交易建议"""
        recommendations = []
        
        if not orders:
            recommendations.append("当前信号强度不足，建议观望等待更好机会")
            return recommendations
        
        # 基于预期收益的建议
        if expected_return > 0.1:
            recommendations.append("预期收益较高，但需注意控制仓位风险")
        elif expected_return > 0.05:
            recommendations.append("预期收益适中，可适量参与")
        else:
            recommendations.append("预期收益较低，建议谨慎操作")
        
        # 基于波动率的建议
        if volatility > 0.3:
            recommendations.append("市场波动较大，建议降低仓位或设置止损")
        elif volatility < 0.15:
            recommendations.append("市场波动较小，可适当增加仓位")
        
        # 基于信号质量的建议
        if abs(balanced_score) > 0.6:
            recommendations.append("信号质量较高，可重点关注")
        else:
            recommendations.append("信号质量一般，建议结合其他指标确认")
        
        # 成本提醒
        recommendations.append("港股交易成本较高（约0.4%），需确保预期收益覆盖成本")
        
        # T+2结算提醒
        recommendations.append("港股实行T+2结算，注意资金安排和流动性管理")
        
        return recommendations[:5]  # 限制在5条以内


def analyze_hk_stock_data(input_data):
    """分析港股数据的主函数"""
    trader = HKStockTrader()
    
    # Reasoning: 先整合信号，优化仓位，考虑港股T+2结算
    print("🔍 Reasoning: 整合信号数据，计算最优仓位配置，考虑港股交易特点...")
    
    # Acting: 生成JSON输出
    result = trader.generate_orders(input_data)
    
    return result


def main():
    """主函数 - 示例用法"""
    # 示例输入数据
    sample_data = {
        "balanced_score": 0.4,
        "signals": [1, -1],
        "close_prices": [100, 102]
    }
    
    print("=== 港股交易代理分析结果 ===\n")
    
    # 执行分析
    result = analyze_hk_stock_data(sample_data)
    
    # 输出JSON结果
    print("📊 JSON分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 简短解释
    if result.get('orders'):
        print(f"\n💡 关键洞见: 基于{result['analysis_summary']['total_orders']}个有效信号，"
              f"预期收益{result['expected_returns']:.2%}，Sharpe贡献{result['sharpe_contribution']:.3f}")
        print(f"平均仓位{result['analysis_summary']['avg_position_size']:.2%}，"
              f"估算波动率{result['analysis_summary']['volatility_estimate']:.2%}")
    else:
        print("\n💡 关键洞见: 当前市场信号不足，建议观望等待更好的交易机会")


if __name__ == "__main__":
    main()