#!/usr/bin/env python3
"""
现实场景演示 - 展示实际可执行的交易订单
"""

import json
from hk_trader_simple import HKStockTrader


def realistic_trading_demo():
    """展示现实场景下的交易决策"""
    
    trader = HKStockTrader()
    
    # 调整为更现实的参数
    trader.commission_rate = 0.001  # 降低佣金率到0.1%
    trader.stamp_duty = 0.001  # 降低印花税
    trader.min_signal_threshold = 0.02  # 降低信号阈值
    
    # 现实场景数据
    scenarios = [
        {
            "name": "用户原始数据 (优化后)",
            "data": {
                "balanced_score": 0.4,
                "signals": [1, -1],
                "close_prices": [100, 102]
            }
        },
        {
            "name": "强信号场景",
            "data": {
                "balanced_score": 0.8,
                "signals": [1, 1, -1],
                "close_prices": [100, 108, 95]
            }
        },
        {
            "name": "高频交易场景",
            "data": {
                "balanced_score": 0.6,
                "signals": [1, -1, 1, -1],
                "close_prices": [100, 103, 98, 106]
            }
        }
    ]
    
    print("🚀 === 港股交易代理现实场景演示 === 🚀\n")
    
    for scenario in scenarios:
        print(f"📊 **{scenario['name']}**")
        print(f"输入: {scenario['data']}")
        print("-" * 50)
        
        # Reasoning
        print("🧠 Reasoning: 整合信号，优化仓位，考虑港股T+2结算特点...")
        
        # Acting
        result = trader.generate_orders(scenario['data'])
        
        print("⚡ Acting: 生成JSON输出")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 关键洞见
        if result.get('orders'):
            print(f"\n💡 关键洞见: 基于{len(result['orders'])}个有效信号，")
            print(f"预期收益{result['expected_returns']:.2%}，Sharpe贡献{result['sharpe_contribution']:.3f}")
        else:
            print(f"\n💡 关键洞见: 信号强度不足，建议等待更好机会")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    realistic_trading_demo()