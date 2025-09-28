"""
使用正确的Cursor API方法测试真实AI
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

class CursorAPITest:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
    
    async def test_cursor_background_agent_api(self, prompt):
        """测试Cursor Background Agent API"""
        print("🔍 尝试Cursor Background Agent API...")
        
        # 根据Cursor文档，使用正确的API端点
        api_url = "https://api.cursor.com/v1/background-agent"
        
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建Cursor API请求
        data = {
            "prompt": prompt,
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        try:
            print(f"  🔍 请求URL: {api_url}")
            print(f"  🔍 请求数据: {json.dumps(data, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=data, timeout=30) as response:
                    print(f"  📊 响应状态: {response.status}")
                    print(f"  📊 响应头: {dict(response.headers)}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ 成功连接到Cursor API")
                        print(f"  📊 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"  ❌ API调用失败: HTTP {response.status}")
                        print(f"  📊 错误信息: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            return None
    
    async def test_cursor_chat_api(self, prompt):
        """测试Cursor Chat API"""
        print("🔍 尝试Cursor Chat API...")
        
        # 尝试不同的Cursor API端点
        endpoints = [
            "https://api.cursor.com/v1/chat/completions",
            "https://api.cursor.com/v1/completions",
            "https://api.cursor.com/v1/chat",
            "https://api.cursor.com/v1/agent"
        ]
        
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一位专业的港股量化分析AI代理，请严格按照要求输出JSON格式结果。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        for endpoint in endpoints:
            try:
                print(f"  🔍 尝试端点: {endpoint}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint, headers=headers, json=data, timeout=15) as response:
                        print(f"    📊 状态码: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"    ✅ 成功连接到: {endpoint}")
                            return result
                        else:
                            error_text = await response.text()
                            print(f"    ❌ 失败: {error_text[:100]}...")
                            
            except Exception as e:
                print(f"    ❌ 连接失败: {str(e)[:50]}...")
                continue
        
        return None
    
    async def test_cursor_agent_api(self, prompt):
        """测试Cursor Agent API"""
        print("🔍 尝试Cursor Agent API...")
        
        # 尝试Agent相关的端点
        endpoints = [
            "https://api.cursor.com/v1/agent/execute",
            "https://api.cursor.com/v1/agent/run",
            "https://api.cursor.com/v1/agent/chat",
            "https://api.cursor.com/v1/agent/background"
        ]
        
        headers = {
            "Authorization": f"Bearer {self.cursor_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        for endpoint in endpoints:
            try:
                print(f"  🔍 尝试端点: {endpoint}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint, headers=headers, json=data, timeout=15) as response:
                        print(f"    📊 状态码: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"    ✅ 成功连接到: {endpoint}")
                            return result
                        else:
                            error_text = await response.text()
                            print(f"    ❌ 失败: {error_text[:100]}...")
                            
            except Exception as e:
                print(f"    ❌ 连接失败: {str(e)[:50]}...")
                continue
        
        return None
    
    async def test_real_ai_analysis(self, agent_type, market_data):
        """测试真实AI分析"""
        print(f"🤖 测试真实AI: {agent_type.value}")
        
        # 生成prompt
        input_data = {"market_data": market_data}
        prompt = self.example.templates.generate_prompt(agent_type, input_data)
        
        print(f"📝 Prompt长度: {len(prompt)} 字符")
        print(f"📝 Prompt预览: {prompt[:200]}...")
        print()
        
        # 尝试不同的Cursor API方法
        response = None
        
        # 方法1: Background Agent API
        response = await self.test_cursor_background_agent_api(prompt)
        
        if not response:
            # 方法2: Chat API
            response = await self.test_cursor_chat_api(prompt)
        
        if not response:
            # 方法3: Agent API
            response = await self.test_cursor_agent_api(prompt)
        
        if response:
            print("✅ 真实AI响应成功！")
            print(f"📊 响应类型: {type(response)}")
            print(f"📊 响应内容: {json.dumps(response, indent=2, ensure_ascii=False)[:500]}...")
            
            # 尝试提取文本内容
            if isinstance(response, dict):
                # 尝试不同的响应格式
                text_content = None
                if 'choices' in response and response['choices']:
                    text_content = response['choices'][0].get('message', {}).get('content', '')
                elif 'content' in response:
                    text_content = response['content']
                elif 'text' in response:
                    text_content = response['text']
                elif 'response' in response:
                    text_content = response['response']
                elif 'result' in response:
                    text_content = response['result']
                
                if text_content:
                    print(f"📊 提取的文本: {text_content[:300]}...")
                    
                    # 尝试解析为JSON
                    try:
                        parsed = self.example.templates.parse_agent_response(text_content)
                        if parsed.get("json_data"):
                            print("✅ JSON解析成功！")
                            return parsed
                        else:
                            print("⚠️ JSON解析失败，但获得了文本响应")
                            return {"raw_response": text_content}
                    except Exception as e:
                        print(f"⚠️ 解析出错: {e}")
                        return {"raw_response": text_content}
                else:
                    print("⚠️ 无法提取文本内容")
                    return {"raw_response": response}
            else:
                print("⚠️ 响应格式不是字典")
                return {"raw_response": str(response)}
        else:
            print("❌ 所有Cursor API都失败了")
            return None
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 Cursor API真实AI测试")
        print("="*60)
        
        # 获取数据
        print("📊 获取测试数据...")
        raw_data = await self.example.get_stock_data("0700.hk")
        if not raw_data:
            print("❌ 无法获取数据")
            return
        
        market_data = self.example.format_market_data(raw_data, "0700.hk")
        if not market_data:
            print("❌ 数据格式化失败")
            return
        
        print(f"✅ 准备测试 {len(market_data)} 条数据")
        print()
        
        # 测试基本面分析代理
        print("🔍 测试基本面分析代理...")
        result = await self.test_real_ai_analysis(AgentType.FUNDAMENTAL_ANALYST, market_data)
        
        if result:
            print("🎉 真实AI测试成功！")
            print("📊 结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ 真实AI测试失败")
            print("💡 建议:")
            print("  1. 检查Cursor API文档")
            print("  2. 验证API密钥权限")
            print("  3. 联系Cursor支持")
            print("  4. 使用模拟模式继续开发")

async def main():
    """主函数"""
    test = CursorAPITest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
