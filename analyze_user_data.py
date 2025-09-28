#!/usr/bin/env python3
"""
用户数据分析脚本 - 港股风险管理代理
"""

from hk_risk_manager_simple import HKRiskManagerSimple
import json

def analyze_user_input():
    """分析用户提供的港股数据"""
    
    # 用户提供的示例数据
    user_data = {
        "returns": [0.01, -0.02, 0.015],
        "risk_free_rate": 0.03
    }
    
    print("=== 港股风险管理代理分析报告 ===")
    print("🎯 目标：追求高Sharpe Ratio交易策略 (>1.5)")
    print("📊 输入数据分析中...\n")
    
    # 创建风险管理器
    risk_manager = HKRiskManagerSimple()
    
    # 执行专业分析
    result = risk_manager.analyze(user_data)
    
    # 输出JSON格式结果
    print("📋 专业分析结果 (JSON):")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # ReAct思考过程
    print("\n🤔 ReAct分析过程:")
    print("Reasoning: 数据量较小(3个观测值)，需要谨慎解读统计指标")
    print("Acting: 计算得出VaR、Sharpe等关键风险指标，评估港股系统风险")
    
    # 关键洞见总结
    if 'error' not in result:
        print(f"\n💡 关键洞见:")
        print(f"• Sharpe Ratio: {result['sharpe']:.2f} ({'达标' if result['sharpe'] >= 1.5 else '未达标'})")
        print(f"• VaR(95%): {result['var_95']:.3f} ({'安全' if result['var_95'] > -0.05 else '超限'})")
        print(f"• 风险等级: {result['analysis_summary']['risk_assessment']}")
        print(f"• 预期年化收益: {result['analysis_summary']['expected_return']:.1%}")

if __name__ == "__main__":
    analyze_user_input()