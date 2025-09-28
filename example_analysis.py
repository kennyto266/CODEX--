#!/usr/bin/env python3
"""
港股技术分析示例 - 多种市场情况演示
"""

from hk_stock_technical_analyst import HKStockTechnicalAnalyst
import json

def analyze_different_scenarios():
    """分析不同市场情况的港股数据"""
    analyst = HKStockTechnicalAnalyst(target_sharpe=1.5)
    
    scenarios = {
        "上升趋势_阿里巴巴": {
            "stock": "9988.HK",
            "close_prices": [
                85.0, 87.2, 89.5, 86.8, 90.3, 92.7, 95.1, 93.4, 97.2, 99.8,
                102.3, 100.6, 104.7, 107.2, 105.8, 109.4, 112.6, 110.9, 115.3, 118.7,
                116.2, 120.8, 123.4, 121.7, 126.3, 129.1, 127.5, 132.4, 135.8, 133.9,
                138.7, 142.3, 140.1, 145.9, 149.2, 147.6, 152.8, 156.4, 154.7, 160.3
            ]
        },
        
        "下降趋势_美团": {
            "stock": "3690.HK",
            "close_prices": [
                180.0, 175.3, 172.8, 177.1, 169.4, 165.7, 162.3, 167.9, 159.8, 155.2,
                158.7, 152.4, 148.9, 153.6, 146.3, 142.7, 145.8, 139.2, 135.6, 132.1,
                136.4, 128.9, 125.3, 129.7, 122.8, 119.4, 123.1, 116.7, 113.2, 117.5,
                110.8, 107.3, 111.6, 105.2, 101.7, 106.1, 99.4, 95.8, 100.2, 93.6
            ]
        },
        
        "震荡市场_小米": {
            "stock": "1810.HK",
            "close_prices": [
                12.5, 13.2, 12.8, 13.7, 12.9, 13.4, 12.6, 13.8, 12.7, 13.5,
                12.9, 13.3, 12.4, 13.9, 12.8, 13.6, 12.5, 13.7, 12.9, 13.2,
                12.6, 13.8, 12.7, 13.4, 12.8, 13.5, 12.9, 13.3, 12.5, 13.6,
                12.8, 13.7, 12.6, 13.4, 12.9, 13.2, 12.7, 13.8, 12.5, 13.5
            ]
        }
    }
    
    print("🔍 港股技术分析 - 多场景对比分析\n" + "="*60)
    
    for scenario_name, data in scenarios.items():
        print(f"\n📊 【{scenario_name}】分析结果：")
        print("-" * 40)
        
        result = analyst.analyze(data)
        
        # 输出关键指标
        summary = result.get('analysis_summary', {})
        print(f"股票代码: {result['stock']}")
        print(f"当前价格: {summary.get('current_price', 'N/A')}")
        print(f"当前RSI: {summary.get('current_rsi', 'N/A')}")
        print(f"平均RSI: {result['rsi_avg']}")
        print(f"Sharpe贡献: {result['sharpe_contribution']}")
        print(f"买入信号: {summary.get('buy_signals', 0)}次")
        print(f"卖出信号: {summary.get('sell_signals', 0)}次")
        
        # 技术建议
        print("\n💡 技术建议:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # 信号分析
        signals = result['signals']
        recent_signals = signals[-10:]  # 最近10个信号
        signal_summary = f"最近10期信号: {recent_signals}"
        print(f"\n📈 {signal_summary}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    analyze_different_scenarios()