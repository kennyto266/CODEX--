#!/usr/bin/env python3
"""
强信号示例 - 展示完整的交易决策过程
"""

import json
from hk_trader_simple import analyze_hk_stock_data


def strong_signal_analysis():
    """展示强信号下的完整分析过程"""
    
    # 强信号数据示例
    strong_signal_data = {
        "balanced_score": 0.8,  # 高质量信号
        "signals": [1, 1, -1, 1],  # 多个信号
        "close_prices": [100, 105, 98, 108]  # 价格波动
    }
    
    print("=== 港股交易代理 - 强信号分析示例 ===")
    print(f"输入数据: {strong_signal_data}")
    print("=" * 60)
    
    # ReAct 思考过程
    print("🧠 **Reasoning (推理过程)**:")
    print("1. 信号强度分析: balanced_score=0.8 属于高质量信号")
    print("2. 市场趋势识别: 价格从100→105→98→108，波动较大但整体上涨")
    print("3. 交易机会评估: 多个买入信号，一个卖出信号")
    print("4. 风险控制考虑: 港股T+2结算，需要考虑交易成本")
    print()
    
    # 执行分析
    print("⚡ **Acting (执行分析)**:")
    result = analyze_hk_stock_data(strong_signal_data)
    
    # 输出JSON结果
    print("📊 **JSON分析结果**:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 60)
    
    # 详细解读
    if result.get('orders'):
        print("💼 **交易执行计划**:")
        for i, order in enumerate(result['orders'], 1):
            print(f"   订单{i}: {order['action']} {order['symbol']}")
            print(f"          价格: HK${order['price']:.2f}")
            print(f"          仓位: {order['position_size']:.1%}")
            print(f"          信心: {order['confidence']:.2f}")
            print()
        
        print("📈 **预期表现**:")
        print(f"   • 总预期收益: {result['expected_returns']:.2%}")
        print(f"   • Sharpe贡献: {result['sharpe_contribution']:.3f}")
        print(f"   • 平均仓位: {result['analysis_summary']['avg_position_size']:.1%}")
        print(f"   • 波动率: {result['analysis_summary']['volatility_estimate']:.1%}")
        
        print("\n💡 **关键洞见**:")
        sharpe_status = "优秀" if result['sharpe_contribution'] > 1.0 else "良好" if result['sharpe_contribution'] > 0.5 else "一般"
        print(f"基于{len(result['orders'])}个有效信号生成交易订单，")
        print(f"预期收益{result['expected_returns']:.2%}，Sharpe贡献{result['sharpe_contribution']:.3f}({sharpe_status})")
        
    else:
        print("⚠️ 即使是强信号也未能通过风险控制筛选，建议:")
        print("   1. 等待更好的市场时机")
        print("   2. 考虑降低交易成本阈值")
        print("   3. 增加信号确认机制")


if __name__ == "__main__":
    strong_signal_analysis()