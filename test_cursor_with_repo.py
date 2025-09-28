"""
使用GitHub仓库测试Cursor v0 API
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

class CursorWithRepoTest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
        self.base_url = "https://api.cursor.com/v0"
    
    async def test_list_repositories(self):
        """测试获取GitHub仓库列表"""
        print("🔍 测试获取GitHub仓库列表...")
        
        url = f"{self.base_url}/repositories"
        headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    print(f"  📊 状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 获取仓库列表成功")
                        print(f"  📊 仓库数量: {len(result.get('repositories', []))}")
                        
                        repositories = result.get('repositories', [])
                        if repositories:
                            print(f"  📊 可用仓库:")
                            for i, repo in enumerate(repositories[:5], 1):  # 只显示前5个
                                print(f"    {i}. {repo.get('name', 'N/A')} - {repo.get('full_name', 'N/A')}")
                                print(f"       URL: {repo.get('html_url', 'N/A')}")
                        else:
                            print(f"  ⚠️ 没有找到可用的仓库")
                        
                        return repositories
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取仓库失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_launch_agent_with_repo(self, prompt, repository_url):
        """使用仓库启动代理"""
        print(f"🔍 使用仓库启动代理: {repository_url}")
        
        url = f"{self.base_url}/agents"
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求数据，包含必需的source参数
        data = {
            "prompt": {
                "text": prompt
            },
            "source": {
                "repository": repository_url,
                "ref": "main"
            }
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
    
    async def test_hk_analysis_with_repo(self, repository_url):
        """使用仓库测试港股分析代理"""
        print("🔍 使用仓库测试港股分析代理...")
        
        # 生成港股分析prompt
        input_data = {"market_data": [{"symbol": "0700.HK", "close": 644.0, "volume": 19504951}]}
        prompt = self.example.templates.generate_prompt(AgentType.FUNDAMENTAL_ANALYST, input_data)
        
        print(f"📝 港股分析Prompt: {prompt[:200]}...")
        
        # 启动代理
        agent_result = await self.test_launch_agent_with_repo(prompt, repository_url)
        
        if agent_result and agent_result.get('id'):
            agent_id = agent_result['id']
            print(f"✅ 港股分析代理启动成功，ID: {agent_id}")
            
            # 等待代理完成工作
            print("⏳ 等待代理完成分析...")
            await asyncio.sleep(10)  # 等待10秒
            
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
        print("🚀 Cursor v0 API + GitHub仓库综合测试")
        print("="*60)
        
        # 测试1: 获取仓库列表
        print("🔍 测试1: 获取GitHub仓库列表")
        repositories = await self.test_list_repositories()
        
        if not repositories:
            print("❌ 没有可用的仓库，无法继续测试")
            print("💡 建议:")
            print("  1. 确保你的GitHub账户已连接到Cursor")
            print("  2. 检查仓库权限设置")
            print("  3. 或者使用模拟模式继续开发")
            return
        
        print()
        
        # 选择第一个仓库进行测试
        first_repo = repositories[0]
        repo_url = first_repo.get('html_url', '')
        repo_name = first_repo.get('name', 'Unknown')
        
        print(f"🎯 选择仓库进行测试: {repo_name}")
        print(f"📊 仓库URL: {repo_url}")
        print()
        
        # 测试2: 港股分析代理
        print("🔍 测试2: 港股分析代理")
        hk_result = await self.test_hk_analysis_with_repo(repo_url)
        
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
    test = CursorWithRepoTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
