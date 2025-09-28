"""
港股AI代理真实系统 - 7个专业代理协作
使用真实的Cursor API进行分析
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hk_demo_with_mock import HKMockExample
from src.agents.hk_prompt_templates import AgentType

class HKRealAgentsSystem:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
        self.example = HKMockExample()
        self.base_url = "https://api.cursor.com/v0"
        
        # 7个专业代理
        self.agents = [
            AgentType.FUNDAMENTAL_ANALYST,      # 基本面分析代理
            AgentType.TECHNICAL_ANALYST,        # 技术分析代理
            AgentType.SENTIMENT_ANALYST,        # 情绪分析代理
            AgentType.NEWS_ANALYST,             # 新闻分析代理
            AgentType.RESEARCH_DEBATE,          # 研究辩论代理
            AgentType.TRADER,                   # 交易代理
            AgentType.RISK_MANAGER              # 风险管理代理
        ]
        
        # 代理中文名称
        self.agent_names = {
            AgentType.FUNDAMENTAL_ANALYST: "基本面分析代理",
            AgentType.TECHNICAL_ANALYST: "技术分析代理",
            AgentType.SENTIMENT_ANALYST: "情绪分析代理",
            AgentType.NEWS_ANALYST: "新闻分析代理",
            AgentType.RESEARCH_DEBATE: "研究辩论代理",
            AgentType.TRADER: "交易代理",
            AgentType.RISK_MANAGER: "风险管理代理"
        }
    
    async def get_stock_data(self, symbol: str = "0700.HK") -> List[Dict]:
        """获取股票数据"""
        print(f"📊 获取 {symbol} 股票数据...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://18.180.162.113:9191/inst/getInst?symbol={symbol}&duration=1825"
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        formatted_data = self.format_market_data(data, symbol)
                        if formatted_data:
                            print(f"✅ 成功获取 {len(formatted_data)} 条数据")
                            return formatted_data[-30:]  # 返回最近30天数据
                        else:
                            print("❌ 数据格式化失败")
                            return []
                    else:
                        print(f"❌ 数据获取失败: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ 数据获取出错: {e}")
            return []
    
    def format_market_data(self, raw_data, symbol):
        """格式化股票数据"""
        try:
            if not raw_data or 'data' not in raw_data:
                return None
            
            data_dict = raw_data['data']
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            missing_fields = [field for field in required_fields if field not in data_dict]
            if missing_fields:
                return None
            
            # 获取所有日期
            dates = set()
            for field in required_fields:
                if isinstance(data_dict[field], dict):
                    dates.update(data_dict[field].keys())
            
            dates = sorted(list(dates))
            if len(dates) == 0:
                return None
            
            formatted_data = []
            for date in dates:
                try:
                    open_price = data_dict['open'].get(date, 0)
                    high_price = data_dict['high'].get(date, 0)
                    low_price = data_dict['low'].get(date, 0)
                    close_price = data_dict['close'].get(date, 0)
                    volume = data_dict['volume'].get(date, 0)
                    
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
                    continue
            
            return formatted_data
            
        except Exception as e:
            print(f"❌ 格式化数据出错: {e}")
            return None
    
    async def launch_agent(self, agent_type: AgentType, market_data: List[Dict]) -> Dict:
        """启动单个代理"""
        agent_name = self.agent_names[agent_type]
        print(f"🤖 启动 {agent_name}...")
        
        # 生成代理prompt
        input_data = {"market_data": market_data}
        prompt = self.example.templates.generate_prompt(agent_type, input_data)
        
        # 构建请求数据
        data = {
            "prompt": {
                "text": f"""
作为{agent_name}，请分析以下港股数据：

{prompt}

请提供专业的分析结果，包括：
1. 详细的分析过程
2. 具体的投资建议
3. 风险提示
4. 预期收益评估

请以JSON格式输出结果。
"""
            },
            "source": {
                "repository": "https://github.com/kennyto266/CODEX--.git",
                "ref": "main"
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/agents"
                headers = {
                    "Authorization": f"Bearer {self.cursor_api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 201:
                        result = await response.json()
                        print(f"✅ {agent_name} 启动成功，ID: {result.get('id')}")
                        return {
                            "agent_type": agent_type,
                            "agent_name": agent_name,
                            "agent_id": result.get('id'),
                            "status": result.get('status'),
                            "prompt": prompt
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ {agent_name} 启动失败: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ {agent_name} 启动出错: {e}")
            return None
    
    async def get_agent_status(self, agent_id: str) -> Dict:
        """获取代理状态"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/agents/{agent_id}"
                headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
                
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        except Exception as e:
            print(f"❌ 获取代理状态出错: {e}")
            return None
    
    async def get_agent_conversation(self, agent_id: str) -> Dict:
        """获取代理对话"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/agents/{agent_id}/conversation"
                headers = {"Authorization": f"Bearer {self.cursor_api_key}"}
                
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        except Exception as e:
            print(f"❌ 获取代理对话出错: {e}")
            return None
    
    async def run_all_agents(self, symbol: str = "0700.HK"):
        """运行所有7个代理"""
        print("🚀 港股AI代理真实系统启动")
        print("="*60)
        print(f"📊 分析目标: {symbol}")
        print(f"🤖 代理数量: {len(self.agents)}")
        print()
        
        # 获取股票数据
        market_data = await self.get_stock_data(symbol)
        if not market_data:
            print("❌ 无法获取股票数据，停止分析")
            return
        
        print(f"📊 使用 {len(market_data)} 条数据进行分析")
        print()
        
        # 启动所有代理
        launched_agents = []
        for agent_type in self.agents:
            agent_result = await self.launch_agent(agent_type, market_data)
            if agent_result:
                launched_agents.append(agent_result)
            await asyncio.sleep(2)  # 避免API限制
        
        print(f"✅ 成功启动 {len(launched_agents)} 个代理")
        print()
        
        # 等待代理完成工作
        print("⏳ 等待代理完成分析...")
        await asyncio.sleep(30)  # 等待30秒
        
        # 获取所有代理的结果
        print("🔍 获取代理分析结果...")
        results = []
        
        for agent in launched_agents:
            agent_id = agent["agent_id"]
            agent_name = agent["agent_name"]
            
            print(f"📊 获取 {agent_name} 结果...")
            
            # 获取状态
            status = await self.get_agent_status(agent_id)
            if status:
                print(f"  ✅ {agent_name} 状态: {status.get('status', 'Unknown')}")
            
            # 获取对话
            conversation = await self.get_agent_conversation(agent_id)
            if conversation:
                print(f"  ✅ {agent_name} 对话获取成功")
                results.append({
                    "agent_name": agent_name,
                    "agent_id": agent_id,
                    "status": status,
                    "conversation": conversation
                })
            else:
                print(f"  ❌ {agent_name} 对话获取失败")
        
        # 显示结果
        print()
        print("🎯 分析结果汇总")
        print("="*60)
        
        for result in results:
            print(f"📊 {result['agent_name']}:")
            print(f"  ID: {result['agent_id']}")
            print(f"  状态: {result['status'].get('status', 'Unknown') if result['status'] else 'Unknown'}")
            if result['conversation']:
                print(f"  对话长度: {len(str(result['conversation']))} 字符")
            print()
        
        print("🎉 港股AI代理系统分析完成！")
        print("💡 你可以在Cursor Dashboard中查看详细的代理工作过程")
        
        return results

async def main():
    """主函数"""
    system = HKRealAgentsSystem()
    await system.run_all_agents("0700.HK")

if __name__ == "__main__":
    asyncio.run(main())
