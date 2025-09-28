#!/usr/bin/env python3
"""
港股交易代理最终分析报告
针对用户数据提供专业的投资建议
"""

import json
from hk_trader_simple import analyze_hk_stock_data


def comprehensive_analysis():
    """综合分析用户数据并提供专业建议"""
    
    # 用户原始数据
    user_data = {
        "balanced_score": 0.4,
        "signals": [1, -1],
        "close_prices": [100, 102]
    }
    
    # 增强版数据用于对比
    enhanced_data = {
        "balanced_score": 0.7,
        "signals": [1, 1, -1, 1],
        "close_prices": [100, 103, 99, 105]
    }
    
    print("🏦 === 港股交易代理专业分析报告 === 🏦\n")
    
    # 分析用户数据
    print("📊 **用户数据分析**")
    print(f"输入: {user_data}")
    print("-" * 50)
    
    result1 = analyze_hk_stock_data(user_data)
    print("**JSON结果:**")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60 + "\n")
    
    # 分析增强数据
    print("📈 **增强信号分析 (对比参考)**")
    print(f"输入: {enhanced_data}")
    print("-" * 50)
    
    result2 = analyze_hk_stock_data(enhanced_data)
    print("**JSON结果:**")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
    
    print("\n" + "="*60 + "\n")
    
    # 专业总结
    print("🎯 **专业投资建议总结**")
    
    print("\n**1. 详细分析过程:**")
    print(f"   • 信号质量: balanced_score = {user_data['balanced_score']} (中等强度)")
    print(f"   • 价格变动: {user_data['close_prices'][0]} → {user_data['close_prices'][1]} (+{((user_data['close_prices'][1]/user_data['close_prices'][0])-1)*100:.1f}%)")
    print(f"   • 信号方向: {user_data['signals']} (买入后卖出)")
    print(f"   • 交易成本: 约{result1['analysis_summary']['trading_cost_impact']:.2%}")
    
    print(f"\n**2. 具体投资建议:**")
    if result1.get('orders'):
        print(f"   ✅ 生成{len(result1['orders'])}个交易订单")
        for order in result1['orders']:
            print(f"   📋 {order['action']} {order['symbol']}: 仓位{order['position_size']:.1%}, 价格HK${order['price']}")
        print(f"   💰 预期收益: {result1['expected_returns']:.2%}")
        print(f"   📊 Sharpe贡献: {result1['sharpe_contribution']:.3f}")
    else:
        print("   ⚠️ 当前信号强度不足，建议:")
        print("     - 等待balanced_score > 0.6的更强信号")
        print("     - 寻找更大的价格波动机会")
        print("     - 考虑增加持仓时间以摊薄成本")
    
    print(f"\n**3. 风险提示:**")
    print(f"   🚨 港股交易成本较高(~0.4%)，需确保预期收益覆盖成本")
    print(f"   ⏰ T+2结算制度，注意资金流动性安排")
    print(f"   📉 当前波动率{result1['analysis_summary']['volatility_estimate']:.1%}，风险可控")
    print(f"   💼 建议单笔仓位不超过25%")
    
    print(f"\n**4. 预期收益评估:**")
    if result1['expected_returns'] > 0:
        annual_return = result1['expected_returns'] * 4  # 假设季度重复
        print(f"   📈 预期季度收益: {result1['expected_returns']:.2%}")
        print(f"   📊 预期年化收益: {annual_return:.1%}")
        print(f"   ⚖️ 风险调整收益: Sharpe贡献 {result1['sharpe_contribution']:.3f}")
    else:
        print(f"   📊 当前条件下预期收益为0")
        print(f"   🎯 建议等待Sharpe Ratio > 1.5的机会")
        print(f"   💡 可考虑技术分析结合基本面分析")
    
    print(f"\n**5. 操作建议:**")
    for i, rec in enumerate(result1['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # 最终洞见
    print(f"\n💡 **关键洞见 (Key Insights):**")
    if result1.get('orders'):
        print(f"基于{len(result1['orders'])}个有效信号，预期收益{result1['expected_returns']:.2%}，")
        print(f"Sharpe贡献{result1['sharpe_contribution']:.3f}，建议谨慎执行。")
    else:
        print("当前信号强度(0.4)偏低，交易成本相对较高，建议等待更强信号或")
        print("考虑长期持仓策略以摊薄交易成本影响。")


if __name__ == "__main__":
    comprehensive_analysis()