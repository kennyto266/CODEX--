"""
根据Cursor官方文档测试正确的API端点
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

class CursorAPIEndpointTest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
    
    async def test_cursor_endpoints(self, prompt):
        """根据官方文档测试Cursor API端点"""
        print("🔍 根据Cursor官方文档测试API端点...")
        
        # 根据Cursor文档，可能的端点格式
        base_urls = [
            "https://api.cursor.com",
            "https://api.cursor.sh", 
            "https://cursor.com/api",
            "https://api.cursor.ai"
        ]
        
        # 可能的端点路径
        endpoints = [
            "/v1/background-agent",
            "/v1/agent",
            "/v1/chat",
            "/v1/completions",
            "/v1/chat/completions",
            "/v1/agent/execute",
            "/v1/agent/run",
            "/v1/agent/chat",
            "/v1/agent/background",
            "/v1/background-agent/execute",
            "/v1/background-agent/run",
            "/v1/background-agent/chat"
        ]
        
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        # 尝试不同的请求格式
        request_formats = [
            # 格式1: 简单prompt
            {"prompt": prompt, "model": "gpt-4"},
            # 格式2: messages格式
            {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "你是一位专业的港股量化分析AI代理。"},
                    {"role": "user", "content": prompt}
                ]
            },
            # 格式3: 带参数的格式
            {
                "prompt": prompt,
                "model": "gpt-4",
                "max_tokens": 1000,
                "temperature": 0.1
            }
        ]
        
        for base_url in base_urls:
            for endpoint in endpoints:
                for i, data in enumerate(request_formats, 1):
                    full_url = base_url + endpoint
                    
                    try:
                        print(f"  🔍 测试: {full_url} (格式{i})")
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.post(full_url, headers=headers, json=data, timeout=10) as response:
                                status = response.status
                                print(f"    📊 状态码: {status}")
                                
                                if status == 200:
                                    result = await response.json()
                                    print(f"    ✅ 成功连接到: {full_url}")
                                    print(f"    📊 响应: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
                                    return result
                                elif status == 401:
                                    print(f"    🔑 认证问题: {full_url}")
                                elif status == 403:
                                    print(f"    🚫 权限问题: {full_url}")
                                elif status == 404:
                                    print(f"    ❌ 端点不存在: {full_url}")
                                else:
                                    error_text = await response.text()
                                    print(f"    ⚠️ 其他错误: {status} - {error_text[:100]}...")
                                    
                    except Exception as e:
                        print(f"    ❌ 连接失败: {str(e)[:50]}...")
                        continue
        
        return None
    
    async def test_cursor_alternative_methods(self, prompt):
        """测试Cursor的其他可能方法"""
        print("🔍 测试Cursor的其他可能方法...")
        
        # 方法1: 尝试GET请求
        print("  🔍 尝试GET请求...")
        try:
            url = "https://api.cursor.com/v1/background-agent"
            params = {"prompt": prompt, "model": "gpt-4"}
            headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"    ✅ GET请求成功: {url}")
                        return result
                    else:
                        print(f"    ❌ GET请求失败: {response.status}")
        except Exception as e:
            print(f"    ❌ GET请求异常: {e}")
        
        # 方法2: 尝试不同的认证方式
        print("  🔍 尝试不同的认证方式...")
        auth_headers = [
            {"Authorization": f"Bearer {self.cursor_api_key}"},
            {"Authorization": f"Token {self.cursor_api_key}"},
            {"X-API-Key": self.cursor_api_key},
            {"api-key": self.cursor_api_key}
        ]
        
        for i, auth_header in enumerate(auth_headers, 1):
            try:
                print(f"    🔍 认证方式{i}: {list(auth_header.keys())[0]}")
                headers = {**auth_header, "Content-Type": "application/json"}
                
                url = "https://api.cursor.com/v1/background-agent"
                data = {"prompt": prompt, "model": "gpt-4"}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=10) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"      ✅ 认证方式{i}成功")
                            return result
                        else:
                            print(f"      ❌ 认证方式{i}失败: {response.status}")
                            
            except Exception as e:
                print(f"      ❌ 认证方式{i}异常: {e}")
        
        return None
    
    async def test_cursor_documentation_endpoints(self, prompt):
        """根据文档测试特定的端点"""
        print("🔍 根据Cursor文档测试特定端点...")
        
        # 根据Cursor文档，可能的端点
        documented_endpoints = [
            {
                "url": "https://api.cursor.com/v1/background-agent/execute",
                "method": "POST",
                "data": {"prompt": prompt, "model": "gpt-4"}
            },
            {
                "url": "https://api.cursor.com/v1/background-agent/run", 
                "method": "POST",
                "data": {"prompt": prompt, "model": "gpt-4"}
            },
            {
                "url": "https://api.cursor.com/v1/background-agent/chat",
                "method": "POST", 
                "data": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
        ]
        
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        for endpoint in documented_endpoints:
            try:
                print(f"  🔍 测试文档端点: {endpoint['url']}")
                
                async with aiohttp.ClientSession() as session:
                    if endpoint['method'] == 'POST':
                        async with session.post(endpoint['url'], headers=headers, json=endpoint['data'], timeout=15) as response:
                            status = response.status
                            print(f"    📊 状态码: {status}")
                            
                            if status == 200:
                                result = await response.json()
                                print(f"    ✅ 成功: {endpoint['url']}")
                                return result
                            else:
                                error_text = await response.text()
                                print(f"    ❌ 失败: {status} - {error_text[:100]}...")
                    else:
                        async with session.get(endpoint['url'], headers=headers, params=endpoint['data'], timeout=15) as response:
                            status = response.status
                            print(f"    📊 状态码: {status}")
                            
                            if status == 200:
                                result = await response.json()
                                print(f"    ✅ 成功: {endpoint['url']}")
                                return result
                            else:
                                error_text = await response.text()
                                print(f"    ❌ 失败: {status} - {error_text[:100]}...")
                                
            except Exception as e:
                print(f"    ❌ 异常: {e}")
                continue
        
        return None
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 Cursor API端点综合测试")
        print("="*60)
        
        # 简单的测试prompt
        test_prompt = "请分析港股0700.HK的基本面，输出JSON格式结果。"
        
        print(f"📝 测试Prompt: {test_prompt}")
        print()
        
        # 测试1: 所有可能的端点
        print("🔍 测试1: 所有可能的端点")
        result1 = await self.test_cursor_endpoints(test_prompt)
        
        if result1:
            print("✅ 测试1成功！")
            return result1
        
        print()
        
        # 测试2: 其他方法
        print("🔍 测试2: 其他方法")
        result2 = await self.test_cursor_alternative_methods(test_prompt)
        
        if result2:
            print("✅ 测试2成功！")
            return result2
        
        print()
        
        # 测试3: 文档特定端点
        print("🔍 测试3: 文档特定端点")
        result3 = await self.test_cursor_documentation_endpoints(test_prompt)
        
        if result3:
            print("✅ 测试3成功！")
            return result3
        
        print()
        print("❌ 所有测试都失败了")
        print("💡 可能的原因:")
        print("  1. Cursor API端点可能不是公开的")
        print("  2. 需要特殊的认证方式")
        print("  3. API密钥可能不是用于外部调用的")
        print("  4. 需要使用Cursor客户端而不是直接API调用")
        print()
        print("🎯 建议:")
        print("  1. 继续使用模拟模式开发")
        print("  2. 联系Cursor支持获取正确的API使用方法")
        print("  3. 考虑使用其他AI服务（OpenAI、Claude等）")

async def main():
    """主函数"""
    test = CursorAPIEndpointTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
