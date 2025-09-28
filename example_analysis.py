#!/usr/bin/env python3
"""
港股新闻分析示例
演示如何分析具体的港股数据
"""

import json
from hk_stock_news_analyzer import HKStockNewsAnalyzer

def run_example_analysis():
    """运行示例分析"""
    analyzer = HKStockNewsAnalyzer()
    
    # 示例输入数据（基于您的要求格式）
    input_data = {
        "news_items": [
            "腾讯(0700.HK)宣布与Meta达成战略合作，共同开发元宇宙平台",
            "港股监管收紧，证监会对多家科技公司展开合规审查", 
            "阿里巴巴(9988.HK)云计算业务获得新的国际认证，业绩预期提升",
            "中美贸易谈判出现新进展，市场情绪回暖",
            "恒生科技指数连续三日下跌，投资者担忧监管风险",
            "小米(1810.HK)发布新一代智能手机，预订量超预期",
            "香港金管局宣布数字港币试点计划，金融科技股受益"
        ],
        "stock": "0700.HK"
    }
    
    print("=== 港股新闻分析代理 ===")
    print("目标: 追求高Sharpe Ratio交易策略 (>1.5)")
    print("专注: 香港/全球新闻对恒生指数影响分析")
    print()
    
    print("📊 输入数据:")
    print(f"目标股票: {input_data['stock']}")
    print(f"新闻条数: {len(input_data['news_items'])}")
    print()
    
    # ReAct思考过程
    print("🤔 === ReAct分析过程 ===")
    print("Reasoning: 扫描新闻内容，识别关键事件类型...")
    print("- 发现并购合作事件: 腾讯-Meta合作 (+)")
    print("- 发现监管事件: 证监会审查 (-)")  
    print("- 发现业绩预期事件: 阿里云认证 (+)")
    print("- 发现市场情绪事件: 贸易谈判进展 (+)")
    print("- 发现指数下跌事件: 恒生科技指数 (-)")
    print("- 发现产品发布事件: 小米新手机 (+)")
    print("- 发现政策利好事件: 数字港币 (+)")
    print()
    
    print("Acting: 量化影响分数，计算Sharpe贡献...")
    
    # 执行分析
    result_json = analyzer.analyze(input_data)
    result = json.loads(result_json)
    
    print("✅ 分析完成!")
    print()
    
    # 输出JSON结果
    print("📄 === JSON分析结果 ===")
    print(result_json)
    
    print()
    print("🎯 === 关键洞见 ===")
    
    # 解析关键信息
    sharpe_contrib = result['sharpe_contribution']
    event_count = result['event_count']
    positive_events = [e for e in result['key_events'] if e['impact_score'] > 0]
    negative_events = [e for e in result['key_events'] if e['impact_score'] < 0]
    
    print(f"检测到 {event_count} 个关键事件 (正面: {len(positive_events)}, 负面: {len(negative_events)})")
    
    if sharpe_contrib > 0:
        print(f"✅ Sharpe Ratio预期贡献为正值 ({sharpe_contrib:.3f})，市场机会大于风险")
        print("建议: 适度增加科技股仓位，重点关注0700.HK")
    else:
        print(f"⚠️ Sharpe Ratio预期贡献为负值 ({sharpe_contrib:.3f})，需要谨慎操作")
        print("建议: 控制仓位规模，考虑恒指期货对冲")
    
    # 风险提示
    high_impact_negative = [e for e in result['key_events'] if e['impact_score'] < -0.05]
    if high_impact_negative:
        print(f"🚨 风险警示: 发现 {len(high_impact_negative)} 个高风险负面事件")
        for event in high_impact_negative:
            print(f"   - {event['description']} (影响: {event['impact_score']:.3f})")

if __name__ == "__main__":
    run_example_analysis()