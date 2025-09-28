#!/usr/bin/env python3
"""
港股技术分析代理演示
展示完整的分析流程和结果
"""

import json
from hk_stock_analyst_simple import HKStockTechnicalAnalyst


def demo_analysis():
    """演示港股技术分析功能"""
    analyst = HKStockTechnicalAnalyst()
    
    # 多个港股示例数据
    test_cases = [
        {
            "name": "腾讯控股 (0700.HK) - 上升趋势",
            "data": {
                "stock": "0700.HK",
                "close_prices": [
                    320, 325, 318, 330, 335, 328, 340, 345, 338, 350,
                    355, 348, 360, 365, 358, 370, 375, 368, 380, 385,
                    378, 390, 395, 388, 400, 405, 398, 410, 415, 408,
                    420, 425, 418, 430, 435, 428, 440, 445, 438, 450
                ],
                "volumes": [2000000 + i * 100000 for i in range(40)]
            }
        },
        {
            "name": "阿里巴巴-SW (9988.HK) - 震荡行情",
            "data": {
                "stock": "9988.HK", 
                "close_prices": [
                    80, 82, 78, 85, 83, 79, 86, 84, 81, 87,
                    85, 82, 88, 86, 83, 89, 87, 84, 90, 88,
                    85, 91, 89, 86, 92, 90, 87, 93, 91, 88,
                    94, 92, 89, 95, 93, 90, 96, 94, 91, 85
                ],
                "volumes": [3000000 + i * 50000 for i in range(40)]
            }
        },
        {
            "name": "比亚迪股份 (1211.HK) - 高波动",
            "data": {
                "stock": "1211.HK",
                "close_prices": [
                    200, 210, 195, 220, 205, 190, 225, 210, 185, 230,
                    215, 180, 235, 220, 175, 240, 225, 170, 245, 230,
                    165, 250, 235, 160, 255, 240, 155, 260, 245, 150,
                    265, 250, 145, 270, 255, 140, 275, 260, 135, 280
                ],
                "volumes": [1500000 + i * 75000 for i in range(40)]
            }
        }
    ]
    
    print("=" * 60)
    print("港股技术分析代理 - 专业分析报告")
    print("=" * 60)
    print()
    
    for case in test_cases:
        print(f"📊 {case['name']}")
        print("-" * 50)
        
        # 执行分析
        result = analyst.analyze(case['data'])
        
        if "error" in result:
            print(f"❌ 分析错误: {result['error']}")
            continue
        
        # 格式化输出分析结果
        print("🎯 交易信号分析:")
        buy_signals = result['signals'].count(1)
        sell_signals = result['signals'].count(-1)
        hold_signals = result['signals'].count(0)
        
        print(f"   • 买入信号: {buy_signals} 次")
        print(f"   • 卖出信号: {sell_signals} 次") 
        print(f"   • 持有信号: {hold_signals} 次")
        
        print("\n📈 技术指标:")
        indicators = result['technical_indicators']
        print(f"   • 当前价格: ${indicators['current_price']:.2f}")
        print(f"   • 20日均线: ${indicators['ma_20']:.2f}" if indicators['ma_20'] else "   • 20日均线: 计算中")
        print(f"   • 当前RSI: {indicators['current_rsi']:.1f}" if indicators['current_rsi'] else "   • 当前RSI: 计算中")
        print(f"   • MACD: {indicators['macd']:.4f}" if indicators['macd'] else "   • MACD: 计算中")
        
        print(f"\n📊 风险评估:")
        risk = result['risk_assessment']
        print(f"   • 波动率水平: {risk['volatility_level']}")
        print(f"   • 趋势强度: {risk['trend_strength']}")
        print(f"   • 平均RSI: {result['rsi_avg']:.1f}")
        print(f"   • Sharpe贡献: {result['sharpe_contribution']:.3f}")
        
        # Sharpe贡献解读
        sharpe_val = result['sharpe_contribution']
        if sharpe_val > 0.5:
            sharpe_desc = "优秀 🟢"
        elif sharpe_val > 0:
            sharpe_desc = "良好 🟡" 
        elif sharpe_val > -0.5:
            sharpe_desc = "一般 🟠"
        else:
            sharpe_desc = "较差 🔴"
        print(f"   • 策略评级: {sharpe_desc}")
        
        print(f"\n💡 交易建议:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📋 完整JSON输出:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n" + "="*60 + "\n")


def analyze_custom_data():
    """分析用户自定义数据的示例"""
    print("🔧 自定义数据分析示例")
    print("-" * 30)
    
    # 用户可以替换这里的数据
    custom_data = {
        "stock": "0700.HK",  # 股票代码
        "close_prices": [100, 102, 98, 105, 103, 99, 108, 106, 101, 110,
                        112, 107, 115, 113, 108, 118, 116, 111, 121, 119,
                        114, 124, 122, 117, 127, 125, 120, 130, 128, 123],
        "volumes": [1000000, 1200000, 800000, 1500000, 1100000, 900000,
                   1600000, 1300000, 1000000, 1700000, 1400000, 1100000,
                   1800000, 1500000, 1200000, 1900000, 1600000, 1300000,
                   2000000, 1700000, 1400000, 2100000, 1800000, 1500000,
                   2200000, 1900000, 1600000, 2300000, 2000000, 1700000]
    }
    
    analyst = HKStockTechnicalAnalyst()
    result = analyst.analyze(custom_data)
    
    print("📊 自定义数据分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" not in result:
        print(f"\n🎯 关键洞见：")
        print(f"股票 {result['stock']} 当前RSI为 {result['rsi_avg']:.1f}，")
        print(f"策略Sharpe贡献为 {result['sharpe_contribution']:.3f}，")
        
        if result['sharpe_contribution'] > 0.3:
            print("💰 建议积极关注买入机会，策略表现良好")
        elif result['sharpe_contribution'] > 0:
            print("⚖️ 可适度关注，但需谨慎操作")
        else:
            print("⚠️ 建议谨慎操作，当前策略表现不佳")


if __name__ == "__main__":
    # 运行演示分析
    demo_analysis()
    
    # 分析自定义数据
    analyze_custom_data()