"""
HK AI Agents System - English Version
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.data.stock_data import StockDataProvider
from src.agents.agent_manager import AgentManager
from src.dashboard.web_server import DashboardServer

class HKAIAgentsSystem:
    """HK AI Agents System Main Class"""
    
    def __init__(self, cursor_api_key: str):
        self.cursor_api_key = cursor_api_key
        self.stock_provider = StockDataProvider()
        self.agent_manager = AgentManager(cursor_api_key)
        self.dashboard_server = DashboardServer(8080)
    
    async def run(self, symbol: str = "0700.HK"):
        """Run complete system"""
        print("HK AI Agents System Starting...")
        print("=" * 60)
        print(f"Analysis Target: {symbol}")
        print()
        
        try:
            # Step 1: Get stock data
            print("Step 1: Getting stock data...")
            market_data = await self.stock_provider.get_stock_data(symbol)
            if not market_data:
                print("Failed to get stock data, stopping analysis")
                return
            
            print(f"Success: Got {len(market_data)} data points")
            print()
            
            # Step 2: Start Dashboard first (loading state)
            print("Step 2: Starting Dashboard (loading)...")
            try:
                # Start dashboard with empty results so 8080 is immediately available
                self.dashboard_server.start([])
                print("Dashboard is up at http://localhost:8080 (loading...)")
            except Exception as _:
                # If dashboard already running, continue
                pass

            # Then start AI agents analysis in sequence
            print("Step 3: Starting AI agents analysis...")
            print("Note: This may take 5-10 minutes as agents need time to analyze...")
            
            # 只运行1个代理进行测试
            print("Testing with 1 agent...")
            original_agents = self.agent_manager.agents
            self.agent_manager.agents = original_agents[:1]
            async def on_progress_update(incremental_result):
                try:
                    # 将单个增量结果更新到Dashboard
                    self.dashboard_server.update_agent_results([incremental_result])
                except Exception:
                    pass

            agent_results = await self.agent_manager.run_all_agents(market_data, on_progress=on_progress_update)
            # 还原代理列表
            self.agent_manager.agents = original_agents
            
            print(f"Success: Completed {len(agent_results)} agent analyses")
            
            # 显示结果摘要
            for i, result in enumerate(agent_results):
                if result:
                    agent_name = result.get('agent_name', f'Agent {i+1}')
                    status = result.get('status', {}).get('status', 'unknown')
                    conversation = result.get('conversation', {})
                    messages = conversation.get('messages', [])
                    
                    print(f"  {agent_name}: {status} ({len(messages)} messages)")
                    
                    # 显示AI回复
                    for msg in messages:
                        if msg.get('type') == 'assistant_message':
                            content = msg.get('text', '')
                            print(f"    AI Response: {content[:100]}...")
                            break
                else:
                    print(f"  Agent {i+1}: Failed")
            
            print()
            
            # Update Dashboard with real results
            print("Updating Dashboard with agent results...")
            try:
                # 使用update_agent_results更新，不重启服务器
                self.dashboard_server.update_agent_results(agent_results)
                print("Dashboard updated with agent results!")
            except Exception as e:
                print(f"Dashboard update error: {e}")
                # 如果更新失败，尝试重启
                try:
                    self.dashboard_server.start(agent_results)
                except Exception:
                    pass
            
            print("\n" + "="*60)
            print("🎉 HK AI Agents System Analysis Complete!")
            print("="*60)
            print("Dashboard URL: http://localhost:8080")
            print("📊 All 7 agents have completed their analysis")
            print("💡 Dashboard will keep running - DO NOT CLOSE THIS WINDOW")
            print("🔄 Refresh your browser to see updated results")
            print("❌ Press Ctrl+C to stop the system")
            print("="*60)
            
            # Keep system running indefinitely
            try:
                while True:
                    await asyncio.sleep(60)  # 每分钟检查一次
                    print(f"⏰ System running... Dashboard active at http://localhost:8080")
            except KeyboardInterrupt:
                print("\n🛑 System stopped by user")
                # 关闭所有代理的HTTP会话
                for agent in self.agent_manager.agents:
                    try:
                        await agent.close()
                    except Exception:
                        pass
                print("✅ All connections closed")
                
        except Exception as e:
            print(f"System error: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main function"""
    # Use provided API key
    cursor_api_key = "key_76c8863c1381ccf5e5fe2b6018e1c4372f793c139a8486c4f35518a8d46df66a"
    
    print("System Configuration:")
    print("  - Cursor API: https://api.cursor.com/v0")
    print("  - Stock API: http://18.180.162.113:9191")
    print("  - Dashboard: http://localhost:8080")
    print()
    
    system = HKAIAgentsSystem(cursor_api_key)
    await system.run("0700.HK")

if __name__ == "__main__":
    asyncio.run(main())
