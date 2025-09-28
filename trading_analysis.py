#!/usr/bin/env python3
"""
港股交易执行代理 - 交互式版本
可接受用户输入的港股数据进行分析
"""

import json
import sys
from hk_trader_simple import HKStockTrader

def analyze_custom_data():
    """分析用户提供的自定义数据"""
    
    print("=== 港股交易执行代理 ===")
    print("请提供港股数据进行分析")
    print()
    
    # 获取用户输入
    try:
        print("请输入balanced_score (0-1之间的浮点数): ", end="")
        balanced_score = float(input())
        
        print("请输入signals (用逗号分隔的整数，如: 1,-1,0,1): ", end="")
        signals_input = input().strip()
        signals = [int(x.strip()) for x in signals_input.split(",")]
        
        print("请输入close_prices (用逗号分隔的价格，如: 100,102,98,105): ", end="")
        prices_input = input().strip()
        close_prices = [float(x.strip()) for x in prices_input.split(",")]
        
        print("请输入symbols (可选，用逗号分隔，如: 0700.HK,0941.HK): ", end="")
        symbols_input = input().strip()
        if symbols_input:
            symbols = [x.strip() for x in symbols_input.split(",")]
        else:
            symbols = [f"HK_{i:04d}" for i in range(len(signals))]
            
    except (ValueError, KeyboardInterrupt):
        print("\n输入格式错误或用户取消，使用默认示例数据...")
        return analyze_default_data()
    
    # 构建输入数据
    input_data = {
        "balanced_score": balanced_score,
        "signals": signals,
        "close_prices": close_prices,
        "symbols": symbols[:len(signals)]  # 确保长度匹配
    }
    
    return perform_analysis(input_data)

def analyze_default_data():
    """使用默认示例数据进行分析"""
    
    print("\n=== 使用示例数据进行分析 ===")
    
    # 高质量信号示例
    sample_data = {
        "balanced_score": 0.75,  # 较高的信号质量
        "signals": [1, -1, 1, 0, 1, -1],
        "close_prices": [320.5, 85.2, 128.0, 45.6, 180.3, 92.8],
        "symbols": ["0700.HK", "0941.HK", "2318.HK", "0005.HK", "1299.HK", "3690.HK"]
    }
    
    return perform_analysis(sample_data)

def perform_analysis(input_data):
    """执行交易分析"""
    
    print(f"\n=== 输入数据 ===")
    print(json.dumps(input_data, indent=2, ensure_ascii=False))
    
    trader = HKStockTrader()
    
    try:
        # 执行分析
        result = trader.analyze_and_trade(input_data)
        
        print(f"\n=== 交易分析结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 关键洞见
        print(f"\n=== 关键洞见 ===")
        print(f"📊 组合Sharpe比率: {result['portfolio_sharpe']:.3f}")
        print(f"💰 预期年化收益: {result['expected_returns']:.2%}")
        print(f"⚠️ 总风险水平: {result['total_risk']:.2%}")
        print(f"🎯 生成订单数量: {len(result['orders'])}")
        
        # 风险评估
        if result['portfolio_sharpe'] > 1.5:
            print("✅ 优秀的风险调整收益，建议执行")
        elif result['portfolio_sharpe'] > 1.0:
            print("🟡 中等风险调整收益，谨慎执行")
        else:
            print("🔴 风险调整收益偏低，建议观望")
            
        # 订单总结
        if result['orders']:
            print(f"\n=== 订单摘要 ===")
            for order in result['orders']:
                action_emoji = "📈" if order['action'] == 'BUY' else "📉"
                print(f"{action_emoji} {order['symbol']}: {order['action']} {order['position_size']:.1%} "
                      f"@ {order['price']} (预期收益: {order['expected_return']:.2%})")
        
        return result
        
    except Exception as e:
        print(f"❌ 分析错误: {e}")
        return None

def main():
    """主函数"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # 交互模式
        analyze_custom_data()
    else:
        # 默认示例模式
        analyze_default_data()

if __name__ == "__main__":
    main()