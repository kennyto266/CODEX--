#!/usr/bin/env python3
"""
交互式港股新闻分析器
支持自定义输入数据进行实时分析
"""

import json
import sys
from hk_stock_news_analyzer import HKStockNewsAnalyzer

def interactive_analysis():
    """交互式分析函数"""
    analyzer = HKStockNewsAnalyzer()
    
    print("=== 港股新闻分析代理 ===")
    print("请输入您的分析数据（JSON格式）或使用默认示例")
    print("格式: {\"news_items\": [\"新闻1\", \"新闻2\"], \"stock\": \"股票代码\"}")
    print("输入 'demo' 使用演示数据，'quit' 退出")
    print()
    
    while True:
        user_input = input("请输入数据: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'demo':
            # 使用演示数据
            demo_data = {
                "news_items": [
                    "腾讯(0700.HK)发布Q3财报，游戏收入增长15%，超出市场预期",
                    "港交所宣布新的科技股上市规则，简化审批流程",
                    "美联储加息预期升温，港股面临资金外流压力",
                    "中国平安(2318.HK)获监管批准设立新的保险科技子公司",
                    "恒大集团债务重组进展缓慢，影响地产板块情绪",
                    "比亚迪(1211.HK)与特斯拉签署电池供应协议，股价异动"
                ],
                "stock": "0700.HK"
            }
            analyze_and_display(analyzer, demo_data)
        else:
            try:
                # 解析用户输入的JSON
                data = json.loads(user_input)
                analyze_and_display(analyzer, data)
            except json.JSONDecodeError:
                print("❌ JSON格式错误，请重新输入")
            except Exception as e:
                print(f"❌ 分析错误: {e}")
        
        print("\n" + "="*50 + "\n")

def analyze_and_display(analyzer, data):
    """执行分析并显示结果"""
    print("🔍 正在分析...")
    
    # 执行分析
    result_json = analyzer.analyze(data)
    result = json.loads(result_json)
    
    # 显示格式化结果
    print("\n📊 === 分析结果 ===")
    print(f"目标股票: {result.get('target_stock', 'N/A')}")
    print(f"事件数量: {result['event_count']}")
    print(f"Sharpe Ratio贡献: {result['sharpe_contribution']}")
    
    print(f"\n📰 === 关键事件 ===")
    for i, event in enumerate(result['key_events'], 1):
        impact_emoji = "📈" if event['impact_score'] > 0 else "📉" if event['impact_score'] < 0 else "➖"
        print(f"{i}. {impact_emoji} {event['description']}")
        print(f"   影响分数: {event['impact_score']:.3f} | 置信度: {event['confidence']:.2f} | 类别: {event['category']}")
        if event['affected_stocks']:
            print(f"   相关股票: {', '.join(event['affected_stocks'])}")
        print()
    
    print(f"💡 === 交易建议 ===")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # 风险评估
    sharpe_contrib = result['sharpe_contribution']
    if sharpe_contrib > 0.2:
        risk_level = "🟢 低风险"
        strategy = "建议增加仓位，市场情绪积极"
    elif sharpe_contrib > -0.2:
        risk_level = "🟡 中等风险"  
        strategy = "建议保持观望，密切关注市场变化"
    else:
        risk_level = "🔴 高风险"
        strategy = "建议减少仓位或进行对冲操作"
    
    print(f"\n⚖️ === 风险评估 ===")
    print(f"风险等级: {risk_level}")
    print(f"策略建议: {strategy}")
    
    # 显示完整JSON（可选）
    show_json = input("\n是否显示完整JSON结果？(y/N): ").strip().lower()
    if show_json == 'y':
        print(f"\n📄 === 完整JSON结果 ===")
        print(result_json)

if __name__ == "__main__":
    try:
        interactive_analysis()
    except KeyboardInterrupt:
        print("\n\n👋 分析会话结束")
        sys.exit(0)