#!/usr/bin/env python3
"""
港股数据分析脚本
处理用户输入的港股数据，进行专业的风险管理分析
"""

import json
import sys
from hk_risk_manager import HKStockRiskManager

def analyze_user_data():
    """分析用户提供的港股数据"""
    
    # 示例数据（如果没有提供具体数据）
    default_data = {
        "returns": [0.01, -0.02, 0.015, -0.008, 0.025, -0.012, 0.018, -0.005, 0.009, -0.015],
        "risk_free_rate": 0.03
    }
    
    # 您可以在这里替换为实际的港股数据
    # 数据格式：{"returns": [日收益率列表], "risk_free_rate": 无风险利率}
    user_data = default_data
    
    # 创建风险管理器
    risk_manager = HKStockRiskManager(risk_free_rate=user_data["risk_free_rate"])
    
    # 执行分析
    result = risk_manager.analyze(user_data)
    
    # 输出专业分析结果
    print("=" * 60)
    print("🇭🇰 港股风险管理分析报告 (Risk Management Analysis)")
    print("=" * 60)
    
    # 核心风险指标
    print(f"\n📊 核心风险指标:")
    print(f"   • 95% VaR (风险价值): {result['var_95']:.2%}")
    print(f"   • 95% CVaR (条件VaR): {result['cvar_95']:.2%}")
    print(f"   • Sharpe比率: {result['sharpe']:.3f}")
    print(f"   • 最大回撤: {result['max_drawdown']:.2%}")
    
    # 风险评级
    print(f"\n🎯 风险评估:")
    print(f"   • 风险等级: {result['analysis_summary']['risk_level']}")
    print(f"   • Sharpe评级: {result['analysis_summary']['sharpe_rating']}")
    print(f"   • 综合评分: {result['analysis_summary']['overall_score']}/100")
    
    # 风险限额检查
    print(f"\n⚖️ 风险限额检查:")
    for limit in result['risk_limits']:
        print(f"   {limit}")
    
    # 投资建议
    print(f"\n💡 专业投资建议:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # 压力测试结果
    print(f"\n🔥 港股黑天鹅压力测试:")
    for scenario, data in result['stress_test'].items():
        scenario_name = {
            "2008_financial_crisis": "2008金融危机",
            "2020_covid_crash": "2020疫情暴跌", 
            "china_policy_shock": "中国政策冲击",
            "us_interest_hike": "美联储加息"
        }.get(scenario, scenario)
        
        print(f"   • {scenario_name}: Sharpe降至{data['stressed_sharpe']:.2f}, VaR恶化{data['var_deterioration']:.2%}")
    
    # JSON格式输出
    print(f"\n" + "=" * 60)
    print("📋 JSON格式分析结果:")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 关键洞察
    print(f"\n" + "=" * 60)
    print("🔍 关键洞察 (Key Insights):")
    print("=" * 60)
    
    if result['sharpe'] >= 1.5:
        print("✅ 当前策略风险调整收益良好，Sharpe比率达标")
    else:
        print("⚠️ 当前策略需要优化，Sharpe比率未达到1.5目标")
        
    if result['var_95'] > -0.05:
        print("✅ VaR风险可控，符合-5%限额要求")
    else:
        print("🔴 VaR超出限额，需要立即采取风险控制措施")
    
    return result

if __name__ == "__main__":
    analyze_user_data()