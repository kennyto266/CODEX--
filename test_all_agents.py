"""
测试所有7个港股AI代理
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hk_demo_with_mock import HKMockExample
from src.agents.hk_prompt_templates import AgentType

async def test_all_agents():
    """测试所有7个AI代理"""
    print("🚀 测试所有7个港股AI代理")
    print("="*60)
    
    example = HKMockExample()
    
    # 获取数据
    print("📊 获取0700.HK数据...")
    raw_data = await example.get_stock_data("0700.hk")
    if not raw_data:
        print("❌ 无法获取数据")
        return
    
    market_data = example.format_market_data(raw_data, "0700.hk")
    if not market_data:
        print("❌ 数据格式化失败")
        return
    
    print(f"✅ 准备分析 {len(market_data)} 条数据")
    print()
    
    # 测试所有7个代理
    all_agents = [
        AgentType.FUNDAMENTAL_ANALYST,    # 基本面分析师
        AgentType.SENTIMENT_ANALYST,      # 情绪分析师
        AgentType.NEWS_ANALYST,           # 新闻分析师
        AgentType.TECHNICAL_ANALYST,      # 技术分析师
        AgentType.RESEARCH_DEBATE,        # 研究辩论师
        AgentType.TRADER,                 # 交易执行员
        AgentType.RISK_MANAGER            # 风险管理师
    ]
    
    results = {}
    
    for i, agent_type in enumerate(all_agents, 1):
        print(f"🤖 [{i}/7] 测试 {agent_type.value}...")
        print("-" * 50)
        
        result = await example.analyze_with_agent(agent_type, market_data, use_mock=True)
        results[agent_type] = result
        
        print()
        await asyncio.sleep(0.5)  # 短暂等待
    
    # 总结所有结果
    print("🎯 所有代理分析总结")
    print("="*60)
    
    for agent_type, result in results.items():
        if result and result.get("json_data"):
            sharpe_contrib = result["json_data"].get("sharpe_contribution", 0)
            print(f"✅ {agent_type.value}: Sharpe贡献 {sharpe_contrib}")
        else:
            print(f"❌ {agent_type.value}: 分析失败")
    
    print("\n🎉 所有代理测试完成！")

if __name__ == "__main__":
    asyncio.run(test_all_agents())
