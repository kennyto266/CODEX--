#!/usr/bin/env python3
"""
最小化启动脚本 - 不依赖外部包
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class SimpleConfig:
    """简单配置类"""
    def __init__(self):
        self.app_name = "港股量化交易AI Agent系统"
        self.app_version = "1.0.0"
        self.debug = False
        self.update_interval = 10
        self.max_concurrent_agents = 10
        self.agent_heartbeat_interval = 30

class SimpleAgentInfo:
    """简单Agent信息类"""
    def __init__(self, agent_id, agent_type, status="running"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = status
        self.last_heartbeat = datetime.now()
        self.cpu_usage = 25.0
        self.memory_usage = 30.0
        self.messages_processed = 100
        self.error_count = 0
        self.uptime = 3600
        self.version = "1.0.0"
        self.configuration = {}
    
    def dict(self):
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "messages_processed": self.messages_processed,
            "error_count": self.error_count,
            "uptime": self.uptime,
            "version": self.version,
            "configuration": self.configuration
        }

class SimpleDashboardAPI:
    """简单仪表板API"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.simple_api")
    
    async def get_all_agents(self):
        """获取所有Agent信息"""
        agents = []
        agent_types = [
            "quant_analyst", "quant_trader", "portfolio_manager", 
            "risk_analyst", "data_scientist", "quant_engineer", "research_analyst"
        ]
        
        for i, agent_type in enumerate(agent_types):
            agent_id = f"{agent_type}_001"
            agent = SimpleAgentInfo(agent_id, agent_type)
            agent.cpu_usage = 25.0 + i * 5
            agent.memory_usage = 30.0 + i * 3
            agent.messages_processed = 100 + i * 50
            agent.uptime = 3600 + i * 100
            agents.append(agent)
        
        return agents
    
    async def get_agent_info(self, agent_id):
        """获取特定Agent信息"""
        agents = await self.get_all_agents()
        for agent in agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    async def get_strategy_info(self, agent_id):
        """获取策略信息"""
        return {
            "agent_id": agent_id,
            "strategy_name": "技术分析策略",
            "parameters": {
                "period": 20,
                "threshold": 0.02
            },
            "metrics": {
                "sharpe_ratio": 1.85,
                "total_return": 0.12,
                "max_drawdown": 0.05
            }
        }
    
    async def get_performance_data(self):
        """获取性能数据"""
        return {
            "total_return": 0.1286,
            "sharpe_ratio": 1.92,
            "max_drawdown": 0.0386,
            "win_rate": 0.65,
            "avg_trade_duration": 5.2
        }
    
    async def get_system_status(self):
        """获取系统状态"""
        return {
            "status": "running",
            "uptime": 3600,
            "memory_usage": 45.2,
            "cpu_usage": 25.8,
            "active_agents": 7,
            "total_trades": 150
        }
    
    async def start_agent(self, agent_id):
        """启动Agent"""
        self.logger.info(f"启动Agent: {agent_id}")
        return True
    
    async def stop_agent(self, agent_id):
        """停止Agent"""
        self.logger.info(f"停止Agent: {agent_id}")
        return True
    
    async def restart_agent(self, agent_id):
        """重启Agent"""
        self.logger.info(f"重启Agent: {agent_id}")
        return True

class SimpleDashboardUI:
    """简单仪表板UI"""
    
    def __init__(self, dashboard_api, config):
        self.dashboard_api = dashboard_api
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.simple_ui")
        self._running = False
        self._cached_data = {}
        self._last_update = {}
    
    async def start(self):
        """启动仪表板"""
        try:
            self.logger.info("启动简单仪表板...")
            self._running = True
            
            # 启动数据更新任务
            self._update_task = asyncio.create_task(self._data_update_loop())
            
            self.logger.info("简单仪表板启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动简单仪表板失败: {e}")
            return False
    
    async def stop(self):
        """停止仪表板"""
        try:
            self.logger.info("停止简单仪表板...")
            self._running = False
            
            if hasattr(self, '_update_task'):
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("简单仪表板已停止")
            
        except Exception as e:
            self.logger.error(f"停止简单仪表板失败: {e}")
    
    async def _data_update_loop(self):
        """数据更新循环"""
        while self._running:
            try:
                # 获取最新数据
                await self._update_cached_data()
                
                # 等待下次更新
                await asyncio.sleep(self.config.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"数据更新循环异常: {e}")
                await asyncio.sleep(5)
    
    async def _update_cached_data(self):
        """更新缓存数据"""
        try:
            # 获取所有Agent数据
            agents = await self.dashboard_api.get_all_agents()
            agent_data = {agent.agent_id: agent.dict() for agent in agents}
            
            # 更新缓存
            self._cached_data["agents"] = agent_data
            self._last_update["agents"] = datetime.now()
            
            # 获取系统状态
            system_status = await self.dashboard_api.get_system_status()
            self._cached_data["system"] = system_status
            self._last_update["system"] = datetime.now()
            
            self.logger.info(f"数据更新完成，Agent数量: {len(agent_data)}")
            
        except Exception as e:
            self.logger.error(f"更新缓存数据失败: {e}")
    
    def get_cached_data(self, key):
        """获取缓存数据"""
        return self._cached_data.get(key)
    
    def get_connection_count(self):
        """获取连接数"""
        return 0  # 简化版本没有WebSocket连接

async def start_minimal_dashboard():
    """启动最小化仪表板"""
    try:
        print("🚀 启动最小化仪表板...")
        
        # 创建配置
        config = SimpleConfig()
        
        # 创建DashboardAPI
        dashboard_api = SimpleDashboardAPI(config)
        
        # 创建DashboardUI
        dashboard_ui = SimpleDashboardUI(dashboard_api, config)
        
        # 启动服务
        await dashboard_ui.start()
        
        print("✅ 最小化仪表板启动成功!")
        print("📊 系统状态:")
        
        # 显示Agent信息
        agents = await dashboard_api.get_all_agents()
        print(f"   Agent数量: {len(agents)}")
        for agent in agents:
            print(f"   - {agent.agent_id}: {agent.status}")
        
        # 显示系统状态
        system_status = await dashboard_api.get_system_status()
        print(f"   系统状态: {system_status['status']}")
        print(f"   活跃Agent: {system_status['active_agents']}")
        
        print("⏹️ 按 Ctrl+C 停止服务")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止服务...")
            await dashboard_ui.stop()
            print("✅ 服务已停止")
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 建议使用演示模式: python demo.py")

def main():
    """主函数"""
    print("🚀 港股量化交易 AI Agent 系统 - 最小化启动")
    print("=" * 50)
    
    setup_logging()
    
    try:
        asyncio.run(start_minimal_dashboard())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        print("💡 建议使用演示模式: python demo.py")

if __name__ == "__main__":
    main()