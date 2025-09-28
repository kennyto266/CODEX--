"""
港股AI代理系统 - 专门适配Cursor API版本
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.hk_prompt_templates import HKPromptTemplates, AgentType

class HKCursorExample:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_35077fee3c6ed63beebba121090f0216273105f2a9688d3d570871c28a9eed53"
        
        # 股票数据API
        self.stock_api_url = "http://18.180.162.113:9191/inst/getInst"
        
        # 港股代码列表
        self.hk_symbols = ["0700.hk", "0005.hk", "0941.hk", "1299.hk", "0388.hk"]
        
        # Prompt模板
        self.templates = HKPromptTemplates()
        
    async def get_stock_data(self, symbol, duration=1825):
        """获取股票数据"""
        try:
            url = f"{self.stock_api_url}?symbol={symbol}&duration={duration}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"❌ 获取 {symbol} 数据失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据出错: {e}")
            return None
    
    def format_market_data(self, raw_data, symbol):
        """格式化股票数据为系统需要的格式"""
        try:
            if not raw_data or 'data' not in raw_data:
                print("❌ 原始数据为空或格式不正确")
                return None
            
            data_dict = raw_data['data']
            
            # 检查是否有必要的数据字段
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            missing_fields = [field for field in required_fields if field not in data_dict]
            if missing_fields:
                print(f"❌ 缺少必要字段: {missing_fields}")
                return None
            
            # 获取所有日期
            dates = set()
            for field in required_fields:
                if isinstance(data_dict[field], dict):
                    dates.update(data_dict[field].keys())
            
            dates = sorted(list(dates))
            print(f"🔍 找到 {len(dates)} 个交易日")
            
            if len(dates) == 0:
                print("❌ 没有找到交易日期")
                return None
            
            formatted_data = []
            
            # 处理每个交易日的数据
            for date in dates:
                try:
                    # 提取各字段的数据
                    open_price = data_dict['open'].get(date, 0)
                    high_price = data_dict['high'].get(date, 0)
                    low_price = data_dict['low'].get(date, 0)
                    close_price = data_dict['close'].get(date, 0)
                    volume = data_dict['volume'].get(date, 0)
                    
                    # 跳过无效数据
                    if open_price == 0 and high_price == 0 and low_price == 0 and close_price == 0:
                        continue
                    
                    formatted_item = {
                        "symbol": symbol.upper(),
                        "timestamp": date,
                        "open": float(open_price),
                        "high": float(high_price),
                        "low": float(low_price),
                        "close": float(close_price),
                        "volume": int(volume)
                    }
                    formatted_data.append(formatted_item)
                    
                except Exception as e:
                    print(f"⚠️ 处理日期 {date} 时出错: {e}")
                    continue
            
            print(f"✅ 成功格式化 {len(formatted_data)} 条数据")
            return formatted_data
            
        except Exception as e:
            print(f"❌ 格式化 {symbol} 数据出错: {e}")
            return None
    
    async def call_cursor_api(self, prompt):
        """调用Cursor API"""
        try:
            # Cursor API端点
            api_url = "https://api.cursor.sh/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.cursor_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的港股量化分析AI代理，请严格按照要求输出JSON格式结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        error_text = await response.text()
                        print(f"❌ Cursor API调用失败: HTTP {response.status}")
                        print(f"错误信息: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ Cursor API调用出错: {e}")
            return None
    
    async def analyze_with_agent(self, agent_type, market_data):
        """使用指定代理分析数据"""
        try:
            print(f"🤖 使用 {agent_type.value} 分析数据...")
            
            # 生成prompt
            input_data = {"market_data": market_data}
            prompt = self.templates.generate_prompt(agent_type, input_data)
            
            # 调用Cursor API
            response = await self.call_cursor_api(prompt)
            
            if response:
                # 解析响应
                parsed_data = self.templates.parse_agent_response(response)
                
                if parsed_data and parsed_data.get("json_data"):
                    print(f"✅ {agent_type.value} 分析成功")
                    print(f"📈 解释: {parsed_data.get('explanation', '无解释')}")
                    print(f"📊 数据: {json.dumps(parsed_data['json_data'], indent=2, ensure_ascii=False)}")
                    return parsed_data
                else:
                    print(f"❌ {agent_type.value} 响应解析失败")
                    print(f"原始响应: {response}")
                    return None
            else:
                print(f"❌ {agent_type.value} API调用失败")
                return None
                
        except Exception as e:
            print(f"❌ {agent_type.value} 分析出错: {e}")
            return None
    
    async def test_single_agent(self, symbol="0700.hk"):
        """测试单个代理"""
        print(f"🔍 正在分析 {symbol.upper()}...")
        
        # 1. 获取股票数据
        print("📊 获取股票数据...")
        raw_data = await self.get_stock_data(symbol)
        if not raw_data:
            print("❌ 无法获取股票数据")
            return
        
        # 2. 格式化数据
        market_data = self.format_market_data(raw_data, symbol)
        if not market_data:
            print("❌ 数据格式化失败")
            return
        
        print(f"✅ 获取到 {len(market_data)} 条数据")
        
        # 3. 使用基本面分析代理
        print("🤖 开始AI分析...")
        result = await self.analyze_with_agent(AgentType.FUNDAMENTAL_ANALYST, market_data)
        
        if result:
            print("🎉 分析完成！")
        else:
            print("❌ 分析失败")
    
    async def test_multiple_agents(self, symbol="0700.hk"):
        """测试多个代理"""
        print(f"🔍 正在用多个代理分析 {symbol.upper()}...")
        
        # 获取数据
        raw_data = await self.get_stock_data(symbol)
        if not raw_data:
            return
        
        market_data = self.format_market_data(raw_data, symbol)
        if not market_data:
            return
        
        # 测试多个代理
        agents_to_test = [
            AgentType.FUNDAMENTAL_ANALYST,
            AgentType.TECHNICAL_ANALYST,
            AgentType.SENTIMENT_ANALYST
        ]
        
        for agent_type in agents_to_test:
            print(f"\n{'='*50}")
            await self.analyze_with_agent(agent_type, market_data)
            await asyncio.sleep(1)  # 等待1秒再分析下一个
    
    async def test_all_symbols(self):
        """测试所有港股代码"""
        print("🔍 测试所有港股代码...")
        
        for symbol in self.hk_symbols:
            print(f"\n{'='*60}")
            print(f"分析 {symbol.upper()}")
            print(f"{'='*60}")
            
            await self.test_single_agent(symbol)
            await asyncio.sleep(2)  # 等待2秒再分析下一个

async def main():
    """主函数"""
    print("🚀 港股AI代理真实数据测试 (Cursor API版本)")
    print("="*60)
    
    example = HKCursorExample()
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 测试单个股票 (0700.HK)")
    print("2. 测试多个代理")
    print("3. 测试所有港股代码")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        await example.test_single_agent("0700.hk")
    elif choice == "2":
        await example.test_multiple_agents("0700.hk")
    elif choice == "3":
        await example.test_all_symbols()
    else:
        print("❌ 无效选择，默认测试单个股票")
        await example.test_single_agent("0700.hk")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
