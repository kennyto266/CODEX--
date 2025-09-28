import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.hk_prompt_engine import HKPromptEngine, LLMConfig, LLMProvider
from src.agents.hk_prompt_templates import AgentType

class HKRealExample:
    def __init__(self):
        # 你的Cursor API密钥
        self.cursor_api_key = "key_35077fee3c6ed63beebba121090f0216273105f2a9688d3d570871c28a9eed53"
        
        # 股票数据API
        self.stock_api_url = "http://18.180.162.113:9191/inst/getInst"
        
        # 港股代码列表
        self.hk_symbols = ["0700.hk", "0005.hk", "0941.hk", "1299.hk", "0388.hk"]
        
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
            print(f"🔍 调试原始数据: {type(raw_data)}")
            
            if not raw_data or 'data' not in raw_data:
                print("❌ 原始数据为空或格式不正确")
                return None
            
            data_dict = raw_data['data']
            print(f"🔍 数据字段: {list(data_dict.keys())}")
            
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
            
            # 显示前几条数据作为示例
            if len(formatted_data) > 0:
                print(f"🔍 第一条数据示例: {formatted_data[0]}")
                if len(formatted_data) > 1:
                    print(f"🔍 最后一条数据示例: {formatted_data[-1]}")
            
            return formatted_data
            
        except Exception as e:
            print(f"❌ 格式化 {symbol} 数据出错: {e}")
            import traceback
            traceback.print_exc()
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
        
        # 3. 配置AI引擎（使用Cursor API）
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,  # 使用OpenAI格式
            api_key=self.cursor_api_key,
            model="gpt-4",
            base_url="https://api.cursor.sh/v1",  # Cursor API端点
            max_tokens=2000,
            temperature=0.1
        )
        
        # 4. 创建AI引擎
        prompt_engine = HKPromptEngine(llm_config)
        
        # 5. 测试基本面分析
        print("🤖 开始AI分析...")
        try:
            result = await prompt_engine.execute_prompt(
                AgentType.FUNDAMENTAL_ANALYST,
                {"market_data": market_data}
            )
            
            if result.success:
                print("✅ 分析成功！")
                print(f"📈 分析结果: {result.explanation}")
                print(f"📊 数据: {json.dumps(result.parsed_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 分析失败: {result.error}")
                
        except Exception as e:
            print(f"❌ AI分析出错: {e}")
    
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
        
        # 配置AI引擎
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key=self.cursor_api_key,
            model="gpt-4",
            base_url="https://api.cursor.sh/v1",
            max_tokens=2000,
            temperature=0.1
        )
        
        prompt_engine = HKPromptEngine(llm_config)
        
        # 测试多个代理
        agents_to_test = [
            AgentType.FUNDAMENTAL_ANALYST,
            AgentType.TECHNICAL_ANALYST,
            AgentType.SENTIMENT_ANALYST
        ]
        
        for agent_type in agents_to_test:
            print(f"\n🤖 测试 {agent_type.value}...")
            try:
                result = await prompt_engine.execute_prompt(
                    agent_type,
                    {"market_data": market_data}
                )
                
                if result.success:
                    print(f"✅ {agent_type.value} 分析成功")
                    print(f"📈 解释: {result.explanation}")
                else:
                    print(f"❌ {agent_type.value} 分析失败: {result.error}")
                    
            except Exception as e:
                print(f"❌ {agent_type.value} 出错: {e}")
    
    async def test_all_symbols(self):
        """测试所有港股代码"""
        print("🔍 测试所有港股代码...")
        
        for symbol in self.hk_symbols:
            print(f"\n{'='*50}")
            print(f"分析 {symbol.upper()}")
            print(f"{'='*50}")
            
            await self.test_single_agent(symbol)
            await asyncio.sleep(2)  # 等待2秒再分析下一个

async def main():
    """主函数"""
    print("🚀 港股AI代理真实数据测试")
    print("="*60)
    
    example = HKRealExample()
    
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
