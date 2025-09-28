"""
测试真实AI代理 - 尝试多种API方法
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

class HKRealAITest:
    def __init__(self):
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
    
    async def test_openai_compatible_api(self, prompt):
        """测试OpenAI兼容的API"""
        print("🔍 尝试OpenAI兼容API...")
        
        # 尝试不同的API端点
        endpoints = [
            "https://api.openai.com/v1/chat/completions",
            "https://api.anthropic.com/v1/messages",
            "https://api.groq.com/openai/v1/chat/completions",
            "https://api.together.xyz/v1/chat/completions"
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
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        for endpoint in endpoints:
            try:
                print(f"  🔍 尝试: {endpoint}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint, headers=headers, json=data, timeout=15) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"  ✅ 成功连接到: {endpoint}")
                            return result['choices'][0]['message']['content'].strip()
                        else:
                            print(f"  ❌ 状态码: {response.status}")
                            
            except Exception as e:
                print(f"  ❌ 连接失败: {str(e)[:50]}...")
                continue
        
        return None
    
    async def test_local_llm(self, prompt):
        """测试本地LLM（如果有的话）"""
        print("🔍 尝试本地LLM...")
        
        # 这里可以添加本地LLM的调用
        # 比如Ollama、LocalAI等
        print("  ℹ️ 本地LLM未配置")
        return None
    
    async def test_alternative_apis(self, prompt):
        """测试其他AI API"""
        print("🔍 尝试其他AI API...")
        
        # 可以尝试其他AI服务
        apis = [
            {
                "name": "Hugging Face",
                "url": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                "headers": {"Authorization": f"Bearer {self.cursor_api_key}"}
            }
        ]
        
        for api in apis:
            try:
                print(f"  🔍 尝试: {api['name']}")
                # 这里可以添加具体的API调用逻辑
                print(f"  ℹ️ {api['name']} 未实现")
            except Exception as e:
                print(f"  ❌ {api['name']} 失败: {e}")
        
        return None
    
    async def test_real_ai_analysis(self, agent_type, market_data):
        """测试真实AI分析"""
        print(f"🤖 测试真实AI: {agent_type.value}")
        
        # 生成prompt
        input_data = {"market_data": market_data}
        prompt = self.example.templates.generate_prompt(agent_type, input_data)
        
        print(f"📝 Prompt长度: {len(prompt)} 字符")
        print(f"📝 Prompt预览: {prompt[:200]}...")
        
        # 尝试不同的AI API
        response = None
        
        # 方法1: OpenAI兼容API
        response = await self.test_openai_compatible_api(prompt)
        
        if not response:
            # 方法2: 本地LLM
            response = await self.test_local_llm(prompt)
        
        if not response:
            # 方法3: 其他API
            response = await self.test_alternative_apis(prompt)
        
        if response:
            print("✅ 真实AI响应成功！")
            print(f"📊 响应长度: {len(response)} 字符")
            print(f"📊 响应预览: {response[:300]}...")
            
            # 尝试解析响应
            try:
                parsed = self.example.templates.parse_agent_response(response)
                if parsed.get("json_data"):
                    print("✅ JSON解析成功！")
                    return parsed
                else:
                    print("⚠️ JSON解析失败，但获得了响应")
                    return {"raw_response": response}
            except Exception as e:
                print(f"⚠️ 解析出错: {e}")
                return {"raw_response": response}
        else:
            print("❌ 所有AI API都失败了")
            return None
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 港股AI代理真实AI测试")
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
            print("  1. 检查网络连接")
            print("  2. 验证API密钥")
            print("  3. 尝试其他AI服务")
            print("  4. 使用模拟模式继续开发")

async def main():
    """主函数"""
    test = HKRealAITest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
