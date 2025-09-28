"""
测试Cursor API的基本功能（不需要GitHub仓库）
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

class CursorSimpleTest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
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
                        print(f"  📊 代理数量: {len(result.get('agents', []))}")
                        print(f"  📊 代理列表: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ 获取代理失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_list_repositories(self):
        """测试获取仓库列表"""
        print("🔍 测试获取仓库列表...")
        
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
                            for i, repo in enumerate(repositories[:3], 1):  # 只显示前3个
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
    
    async def run_basic_test(self):
        """运行基本测试"""
        print("🚀 Cursor API基本功能测试")
        print("="*50)
        
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
        
        # 测试4: 获取仓库列表
        print("🔍 测试4: 获取仓库列表")
        repositories = await self.test_list_repositories()
        
        print()
        
        # 总结
        print("🎯 测试总结:")
        print(f"  ✅ API密钥: {'有效' if api_valid else '无效'}")
        print(f"  ✅ 模型列表: {'成功' if models else '失败'}")
        print(f"  ✅ 代理列表: {'成功' if agents else '失败'}")
        print(f"  ✅ 仓库列表: {'成功' if repositories else '失败'}")
        
        if repositories and len(repositories) > 0:
            print(f"  📊 可用仓库数量: {len(repositories)}")
            print("  💡 你可以使用这些仓库来启动代理")
        else:
            print("  ⚠️ 没有可用的仓库")
            print("  💡 请安装 Cursor GitHub App 来访问你的仓库")
            print("  🔗 安装链接: https://cursor.com/api/auth/connect-github")
        
        print()
        print("🎉 基本测试完成！")

async def main():
    """主函数"""
    test = CursorSimpleTest()
    await test.run_basic_test()

if __name__ == "__main__":
    asyncio.run(main())
