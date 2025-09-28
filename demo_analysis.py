#!/usr/bin/env python3
"""
港股交易代理演示分析
展示不同信号强度下的交易决策
"""

import json
from hk_trader_simple import analyze_hk_stock_data


def demo_analysis():
    """演示不同场景下的分析结果"""
    
    scenarios = [
        {
            "name": "强买入信号",
            "data": {
                "balanced_score": 0.8,
                "signals": [1, 1, -1],
                "close_prices": [100, 105, 98]
            }
        },
        {
            "name": "混合信号",
            "data": {
                "balanced_score": 0.6,
                "signals": [1, -1, 1],
                "close_prices": [100, 102, 104]
            }
        },
        {
            "name": "弱信号",
            "data": {
                "balanced_score": 0.3,
                "signals": [1, 0, -1],
                "close_prices": [100, 101, 99]
            }
        },
        {
            "name": "高波动环境",
            "data": {
                "balanced_score": 0.7,
                "signals": [1, -1],
                "close_prices": [100, 120, 90, 110]
            }
        }
    ]
    
    print("=== 港股交易代理多场景分析演示 ===\n")
    
    for scenario in scenarios:
        print(f"📈 场景: {scenario['name']}")
        print(f"输入数据: {scenario['data']}")
        print("-" * 50)
        
        result = analyze_hk_stock_data(scenario['data'])
        
        print("📊 分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 关键指标总结
        if result.get('orders'):
            print(f"\n💡 关键洞见:")
            print(f"  • 生成订单数: {len(result['orders'])}")
            print(f"  • 预期收益率: {result['expected_returns']:.2%}")
            print(f"  • Sharpe贡献: {result['sharpe_contribution']:.3f}")
            print(f"  • 平均仓位: {result['analysis_summary']['avg_position_size']:.2%}")
            print(f"  • 波动率估算: {result['analysis_summary']['volatility_estimate']:.2%}")
        else:
            print(f"\n💡 关键洞见: 信号不足，建议观望")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    demo_analysis()