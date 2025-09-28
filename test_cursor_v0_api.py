"""
使用正确的Cursor v0 API测试真实AI
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

class CursorV0APITest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
        self.base_url = "https://api.cursor.com/v0"
    
    async def test_api_key_info(self):
        """测试API密钥信息"""
        print("🔍 测试API密钥信息...")
        
        url = f"{self.base_url}/me"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ API密钥有效")
                        print(f"  📊 用户信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"  ❌ API密钥无效: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return False
    
    async def test_list_models(self):
        """测试获取模型列表"""
        print("🔍 测试获取模型列表...")
        
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 获取模型列表成功")
                        print(f"  📊 可用模型: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取模型失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_list_agents(self):
        """测试获取代理列表"""
        print("🔍 测试获取代理列表...")
        
        url = f"{self.base_url}/agents"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 获取代理列表成功")
                        print(f"  📊 代理数量: {len(result) if isinstance(result, list) else 'N/A'}")
                        print(f"  📊 代理列表: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}...")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取代理失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_launch_agent(self, prompt, repository_url=None):
        """测试启动代理"""
        print("🔍 测试启动代理...")
        
        url = f"{self.base_url}/agents"
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求数据
        data = {
            "prompt": {
                "text": prompt
            }
        }
        
        # 如果有仓库URL，添加到请求中
        if repository_url:
            data["source"] = {
                "repository": repository_url,
                "ref": "main"
            }
        
        print(f"  📝 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 201:
                        result = await response.json()
                        print(f"  ✅ 代理启动成功")
                        print(f"  📊 代理ID: {result.get('id', 'N/A')}")
                        print(f"  📊 代理状态: {result.get('status', 'N/A')}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 代理启动失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_agent_status(self, agent_id):
        """测试代理状态"""
        print(f"🔍 测试代理状态: {agent_id}")
        
        url = f"{self.base_url}/agents/{agent_id}"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 获取代理状态成功")
                        print(f"  📊 代理状态: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取代理状态失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_agent_conversation(self, agent_id):
        """测试代理对话"""
        print(f"🔍 测试代理对话: {agent_id}")
        
        url = f"{self.base_url}/agents/{agent_id}/conversation"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 获取代理对话成功")
                        print(f"  📊 对话内容: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取代理对话失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_hk_analysis_agent(self):
        """测试港股分析代理"""
        print("🔍 测试港股分析代理...")
        
        # 生成港股分析prompt
        input_data = {"market_data": [{"symbol": "0700.HK", "close": 644.0, "volume": 19504951}]}
        prompt = self.example.templates.generate_prompt(AgentType.FUNDAMENTAL_ANALYST, input_data)
        
        print(f"📝 港股分析Prompt: {prompt[:200]}...")
        
        # 启动代理
        agent_result = await self.test_launch_agent(prompt)
        
        if agent_result and agent_result.get('id'):
            agent_id = agent_result['id']
            print(f"✅ 港股分析代理启动成功，ID: {agent_id}")
            
            # 等待代理完成工作
            print("⏳ 等待代理完成分析...")
            await asyncio.sleep(5)  # 等待5秒
            
            # 检查代理状态
            status = await self.test_agent_status(agent_id)
            
            if status:
                # 获取对话结果
                conversation = await self.test_agent_conversation(agent_id)
                
                if conversation:
                    print("🎉 港股分析代理测试成功！")
                    return {
                        "agent_id": agent_id,
                        "status": status,
                        "conversation": conversation
                    }
        
        return None
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 Cursor v0 API综合测试")
        print("="*60)
        
        # 测试1: API密钥信息
        print("🔍 测试1: API密钥信息")
        api_valid = await self.test_api_key_info()
        
        if not api_valid:
            print("❌ API密钥无效，停止测试")
            return
        
        print()
        
        # 测试2: 获取模型列表
        print("🔍 测试2: 获取模型列表")
        models = await self.test_list_models()
        
        print()
        
        # 测试3: 获取代理列表
        print("🔍 测试3: 获取代理列表")
        agents = await self.test_list_agents()
        
        print()
        
        # 测试4: 港股分析代理
        print("🔍 测试4: 港股分析代理")
        hk_result = await self.test_hk_analysis_agent()
        
        if hk_result:
            print("🎉 港股分析代理测试成功！")
            print("📊 结果:")
            print(json.dumps(hk_result, indent=2, ensure_ascii=False))
        else:
            print("❌ 港股分析代理测试失败")
        
        print()
        print("🎯 测试完成！")

async def main():
    """主函数"""
    test = CursorV0APITest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
