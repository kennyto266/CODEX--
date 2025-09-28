"""
港股AI代理系统 - 模拟版本（用于测试系统功能）
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

class HKMockExample:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        
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
            
            # 处理每个交易日的数据（只取最近30天用于演示）
            recent_dates = dates[-30:] if len(dates) > 30 else dates
            
            for date in recent_dates:
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
            
            print(f"✅ 成功格式化 {len(formatted_data)} 条数据（最近30天）")
            return formatted_data
            
        except Exception as e:
            print(f"❌ 格式化 {symbol} 数据出错: {e}")
            return None
    
    def mock_ai_response(self, agent_type, market_data):
        """模拟AI响应（用于测试系统功能）"""
        print(f"🤖 模拟 {agent_type.value} 分析...")
        
        # 基于代理类型生成模拟响应
        if agent_type == AgentType.FUNDAMENTAL_ANALYST:
            return {
                "json_data": {
                    "undervalued_stocks": [{"code": "0700.HK", "pe": 12.5}],
                    "pe_avg": 10.35,
                    "sharpe_contribution": 0.75,
                    "recommendations": ["买入0700.HK：低PE+高成长，预期贡献Sharpe +0.3，但监测地缘风险。"]
                },
                "explanation": "0700.HK显示强劲基本面，预期提升Sharpe Ratio，但需对冲系统风险。"
            }
        elif agent_type == AgentType.TECHNICAL_ANALYST:
            return {
                "json_data": {
                    "signals": [1, -1, 1],
                    "rsi_avg": 55.2,
                    "sharpe_contribution": 0.6,
                    "recommendations": ["买入MA上穿：贡献Sharpe +0.3，但设RSI止损70。"]
                },
                "explanation": "技术信号中性偏多，有助优化入场，但需结合基本面。"
            }
        elif agent_type == AgentType.SENTIMENT_ANALYST:
            return {
                "json_data": {
                    "sentiment_scores": [0.8, -0.4],
                    "avg_score": 0.2,
                    "sharpe_contribution": 0.4,
                    "recommendations": ["买入高情绪股：如0700.HK正面偏差，贡献Sharpe +0.2，但避开负面峰值。"]
                },
                "explanation": "整体情绪中性偏正，有助稳定回报，但需监测地缘新闻触发。"
            }
        else:
            return {
                "json_data": {
                    "analysis": f"{agent_type.value} 分析完成",
                    "sharpe_contribution": 0.5,
                    "recommendations": [f"基于{agent_type.value}的建议"]
                },
                "explanation": f"{agent_type.value} 分析完成，建议继续关注。"
            }
    
    async def try_cursor_api(self, prompt):
        """尝试调用Cursor API（多种端点）"""
        endpoints = [
            "https://api.cursor.sh/v1/chat/completions",
            "https://api.cursor.com/v1/chat/completions",
            "https://cursor.sh/api/v1/chat/completions"
        ]
        
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
        
        for endpoint in endpoints:
            try:
                print(f"🔍 尝试端点: {endpoint}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint, headers=headers, json=data, timeout=10) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ 成功连接到: {endpoint}")
                            return result['choices'][0]['message']['content'].strip()
                        else:
                            print(f"❌ 端点 {endpoint} 返回状态: {response.status}")
                            
            except Exception as e:
                print(f"❌ 端点 {endpoint} 连接失败: {e}")
                continue
        
        return None
    
    async def analyze_with_agent(self, agent_type, market_data, use_mock=False):
        """使用指定代理分析数据"""
        try:
            print(f"🤖 使用 {agent_type.value} 分析数据...")
            
            # 生成prompt
            input_data = {"market_data": market_data}
            prompt = self.templates.generate_prompt(agent_type, input_data)
            
            if use_mock:
                # 使用模拟响应
                result = self.mock_ai_response(agent_type, market_data)
            else:
                # 尝试调用真实API
                response = await self.try_cursor_api(prompt)
                
                if response:
                    # 解析响应
                    parsed_data = self.templates.parse_agent_response(response)
                    result = parsed_data
                else:
                    print(f"⚠️ API调用失败，使用模拟响应")
                    result = self.mock_ai_response(agent_type, market_data)
            
            if result and result.get("json_data"):
                print(f"✅ {agent_type.value} 分析成功")
                print(f"📈 解释: {result.get('explanation', '无解释')}")
                print(f"📊 数据: {json.dumps(result['json_data'], indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"❌ {agent_type.value} 响应解析失败")
                return None
                
        except Exception as e:
            print(f"❌ {agent_type.value} 分析出错: {e}")
            return None
    
    async def test_single_agent(self, symbol="0700.hk", use_mock=False):
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
        result = await self.analyze_with_agent(AgentType.FUNDAMENTAL_ANALYST, market_data, use_mock)
        
        if result:
            print("🎉 分析完成！")
        else:
            print("❌ 分析失败")
    
    async def test_multiple_agents(self, symbol="0700.hk", use_mock=False):
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
            await self.analyze_with_agent(agent_type, market_data, use_mock)
            await asyncio.sleep(1)  # 等待1秒再分析下一个

async def main():
    """主函数"""
    print("🚀 港股AI代理真实数据测试 (模拟版本)")
    print("="*60)
    
    example = HKMockExample()
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 测试单个股票 (0700.HK) - 真实API")
    print("2. 测试单个股票 (0700.HK) - 模拟模式")
    print("3. 测试多个代理 - 真实API")
    print("4. 测试多个代理 - 模拟模式")
    
    choice = input("请输入选择 (1-4): ").strip()
    
    if choice == "1":
        await example.test_single_agent("0700.hk", use_mock=False)
    elif choice == "2":
        await example.test_single_agent("0700.hk", use_mock=True)
    elif choice == "3":
        await example.test_multiple_agents("0700.hk", use_mock=False)
    elif choice == "4":
        await example.test_multiple_agents("0700.hk", use_mock=True)
    else:
        print("❌ 无效选择，默认测试单个股票（模拟模式）")
        await example.test_single_agent("0700.hk", use_mock=True)
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
