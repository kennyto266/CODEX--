"""
使用你的GitHub仓库测试Cursor v0 API
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hk_demo_with_mock import HKMockExample
from src.agents.hk_prompt_templates import AgentType

class CursorWithYourRepoTest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
        self.base_url = "https://api.cursor.com/v0"
        
        # 你的GitHub仓库
        self.repository_url = "https://github.com/kennyto266/CODEX--.git"
    
    async def test_launch_hk_analysis_agent(self):
        """启动港股分析代理"""
        print("🔍 启动港股分析代理...")
        
        url = f"{self.base_url}/agents"
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        # 生成港股分析prompt
        input_data = {"market_data": [{"symbol": "0700.HK", "close": 644.0, "volume": 19504951}]}
        prompt = self.example.templates.generate_prompt(AgentType.FUNDAMENTAL_ANALYST, input_data)
        
        # 构建请求数据
        data = {
            "prompt": {
                "text": f"""
请分析以下港股数据并提供投资建议：

{prompt}

请基于你的量化交易系统知识，分析腾讯(0700.HK)的投资价值，并考虑：
1. 技术指标分析
2. 基本面评估
3. 风险控制建议
4. 具体的交易策略

请以JSON格式输出结果，包含：
- 买入/卖出建议
- 目标价格
- 止损价格
- 风险等级
- 预期收益
"""
            },
            "source": {
                "repository": self.repository_url,
                "ref": "main"
            }
        }
        
        print(f"📝 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    print(f"📊 状态码: {response.status}")
                    
                    if response.status == 201:
                        result = await response.json()
                        print(f"✅ 代理启动成功")
                        print(f"📊 代理ID: {result.get('id', 'N/A')}")
                        print(f"📊 代理状态: {result.get('status', 'N/A')}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ 代理启动失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return None
    
    async def test_agent_status(self, agent_id):
        """检查代理状态"""
        print(f"🔍 检查代理状态: {agent_id}")
        
        url = f"{self.base_url}/agents/{agent_id}"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 获取代理状态成功")
                        print(f"📊 代理状态: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取代理状态失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return None
    
    async def test_agent_conversation(self, agent_id):
        """获取代理对话"""
        print(f"🔍 获取代理对话: {agent_id}")
        
        url = f"{self.base_url}/agents/{agent_id}/conversation"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 获取代理对话成功")
                        print(f"📊 对话内容: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}...")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ 获取代理对话失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return None
    
    async def test_add_followup(self, agent_id, followup_text):
        """添加后续指令"""
        print(f"🔍 添加后续指令: {agent_id}")
        
        url = f"{self.base_url}/agents/{agent_id}/followup"
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": {
                "text": followup_text
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    print(f"📊 状态码: {response.status}")
                    
                    if response.status == 201:
                        result = await response.json()
                        print(f"✅ 后续指令添加成功")
                        print(f"📊 结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ 后续指令添加失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return None
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 Cursor v0 API + 你的GitHub仓库综合测试")
        print("="*60)
        print(f"📊 使用仓库: {self.repository_url}")
        print()
        
        # 测试1: 启动港股分析代理
        print("🔍 测试1: 启动港股分析代理")
        agent_result = await self.test_launch_hk_analysis_agent()
        
        if not agent_result or not agent_result.get('id'):
            print("❌ 代理启动失败，停止测试")
            return
        
        agent_id = agent_result['id']
        print(f"✅ 代理启动成功，ID: {agent_id}")
        print()
        
        # 测试2: 检查代理状态
        print("🔍 测试2: 检查代理状态")
        status = await self.test_agent_status(agent_id)
        
        if status:
            print(f"✅ 代理状态: {status.get('status', 'Unknown')}")
        print()
        
        # 测试3: 等待代理完成工作
        print("🔍 测试3: 等待代理完成工作")
        print("⏳ 等待15秒让代理完成分析...")
        await asyncio.sleep(15)
        
        # 测试4: 再次检查状态
        print("🔍 测试4: 再次检查状态")
        status = await self.test_agent_status(agent_id)
        
        if status:
            print(f"✅ 代理状态: {status.get('status', 'Unknown')}")
        print()
        
        # 测试5: 获取对话结果
        print("🔍 测试5: 获取对话结果")
        conversation = await self.test_agent_conversation(agent_id)
        
        if conversation:
            print("✅ 获取对话成功")
            print("📊 分析结果:")
            print(json.dumps(conversation, indent=2, ensure_ascii=False))
        print()
        
        # 测试6: 添加后续指令
        print("🔍 测试6: 添加后续指令")
        followup_text = """
请基于之前的分析，提供更详细的交易策略：
1. 具体的入场时机
2. 仓位管理建议
3. 风险控制措施
4. 预期收益目标
5. 市场风险提示
"""
        
        followup_result = await self.test_add_followup(agent_id, followup_text)
        
        if followup_result:
            print("✅ 后续指令添加成功")
        print()
        
        # 测试7: 最终检查
        print("🔍 测试7: 最终检查")
        print("⏳ 等待10秒让代理处理后续指令...")
        await asyncio.sleep(10)
        
        final_conversation = await self.test_agent_conversation(agent_id)
        
        if final_conversation:
            print("✅ 最终对话获取成功")
            print("📊 完整分析结果:")
            print(json.dumps(final_conversation, indent=2, ensure_ascii=False))
        
        print()
        print("🎯 测试完成！")
        print(f"📊 代理ID: {agent_id}")
        print("💡 你可以在Cursor Dashboard中查看代理的详细工作过程")

async def main():
    """主函数"""
    test = CursorWithYourRepoTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
