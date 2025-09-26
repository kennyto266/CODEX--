#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 快速启动脚本

这个脚本演示如何快速启动和使用系统。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# 导入系统核心组件
from src.core.message_queue import MessageQueue, Message
from src.agents.coordinator import AgentCoordinator
from src.agents.base_agent import AgentConfig
from src.agents.quantitative_analyst import QuantitativeAnalystAgent
from src.agents.quantitative_trader import QuantitativeTraderAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.agents.risk_analyst import RiskAnalystAgent
from src.agents.data_scientist import DataScientistAgent
from src.agents.quantitative_engineer import QuantitativeEngineerAgent
from src.agents.research_analyst import ResearchAnalystAgent
from src.models.base import MarketData, TradingSignal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hk_quant_system")


class HKQuantSystemDemo:
    """港股量化交易系统演示类"""
    
    def __init__(self):
        self.message_queue = None
        self.coordinator = None
        self.agents = {}
        self.running = False
    
    async def initialize_system(self):
        """初始化系统"""
        logger.info("🚀 正在初始化港股量化交易AI Agent系统...")
        
        # 1. 初始化消息队列
        logger.info("📡 初始化消息队列...")
        self.message_queue = MessageQueue()
        await self.message_queue.initialize()
        
        # 2. 创建Agent协调器
        logger.info("🎯 创建Agent协调器...")
        self.coordinator = AgentCoordinator(self.message_queue)
        await self.coordinator.initialize()
        
        # 3. 创建所有AI Agent
        logger.info("🤖 创建AI Agent...")
        await self._create_agents()
        
        # 4. 注册Agent到协调器
        logger.info("📋 注册Agent到协调器...")
        await self._register_agents()
        
        # 5. 启动所有Agent
        logger.info("▶️ 启动所有Agent...")
        await self.coordinator.start_all_agents()
        
        self.running = True
        logger.info("✅ 系统初始化完成！")
    
    async def _create_agents(self):
        """创建所有AI Agent"""
        
        # Agent配置
        agent_configs = {
            "quantitative_analyst": AgentConfig(
                agent_id="quant_analyst_001",
                agent_type="QuantitativeAnalyst",
                status="active"
            ),
            "quantitative_trader": AgentConfig(
                agent_id="quant_trader_001",
                agent_type="QuantitativeTrader",
                status="active"
            ),
            "portfolio_manager": AgentConfig(
                agent_id="portfolio_manager_001",
                agent_type="PortfolioManager",
                status="active"
            ),
            "risk_analyst": AgentConfig(
                agent_id="risk_analyst_001",
                agent_type="RiskAnalyst",
                status="active"
            ),
            "data_scientist": AgentConfig(
                agent_id="data_scientist_001",
                agent_type="DataScientist",
                status="active"
            ),
            "quantitative_engineer": AgentConfig(
                agent_id="quant_engineer_001",
                agent_type="QuantitativeEngineer",
                status="active"
            ),
            "research_analyst": AgentConfig(
                agent_id="research_analyst_001",
                agent_type="ResearchAnalyst",
                status="active"
            )
        }
        
        # 创建Agent实例
        self.agents["quantitative_analyst"] = QuantitativeAnalystAgent(
            agent_configs["quantitative_analyst"], self.message_queue
        )
        self.agents["quantitative_trader"] = QuantitativeTraderAgent(
            agent_configs["quantitative_trader"], self.message_queue
        )
        self.agents["portfolio_manager"] = PortfolioManagerAgent(
            agent_configs["portfolio_manager"], self.message_queue
        )
        self.agents["risk_analyst"] = RiskAnalystAgent(
            agent_configs["risk_analyst"], self.message_queue
        )
        self.agents["data_scientist"] = DataScientistAgent(
            agent_configs["data_scientist"], self.message_queue
        )
        self.agents["quantitative_engineer"] = QuantitativeEngineerAgent(
            agent_configs["quantitative_engineer"], self.message_queue
        )
        self.agents["research_analyst"] = ResearchAnalystAgent(
            agent_configs["research_analyst"], self.message_queue
        )
        
        # 初始化所有Agent
        for agent_name, agent in self.agents.items():
            await agent.initialize()
            logger.info(f"  ✅ {agent_name} Agent 已创建并初始化")
    
    async def _register_agents(self):
        """注册Agent到协调器"""
        for agent_name, agent in self.agents.items():
            await self.coordinator.register_agent(
                agent.config.agent_id, 
                agent.config.agent_type
            )
    
    async def demo_trading_workflow(self):
        """演示完整的交易工作流程"""
        logger.info("\n🎯 开始演示完整交易工作流程...")
        
        # 1. 模拟市场数据输入
        logger.info("📊 步骤1: 输入市场数据")
        market_data = MarketData(
            id=str(uuid.uuid4()),
            symbol="2800.HK",
            timestamp=datetime.now(),
            open_price=25.50,
            high_price=25.80,
            low_price=25.40,
            close_price=25.70,
            volume=1000000,
            vwap=25.60
        )
        
        market_message = Message(
            id=str(uuid.uuid4()),
            sender_id="market_data_source",
            receiver_id="data_scientist_001",
            message_type="MARKET_DATA",
            payload=market_data.dict(),
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(market_message)
        logger.info(f"  📈 已发送市场数据: {market_data.symbol} @ {market_data.close_price}")
        
        # 等待处理
        await asyncio.sleep(1)
        
        # 2. 数据科学家处理数据
        logger.info("🔬 步骤2: 数据科学家处理数据")
        features_message = Message(
            id=str(uuid.uuid4()),
            sender_id="data_scientist_001",
            receiver_id="quant_analyst_001",
            message_type="PROCESSED_DATA",
            payload={
                "features": {
                    "momentum": 0.8,
                    "volatility": 0.15,
                    "volume_ratio": 1.2,
                    "rsi": 65.0
                },
                "symbol": "2800.HK",
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(features_message)
        logger.info("  🧠 已发送处理后的特征数据")
        
        await asyncio.sleep(1)
        
        # 3. 量化分析师生成交易信号
        logger.info("📊 步骤3: 量化分析师生成交易信号")
        trading_signal = TradingSignal(
            id=str(uuid.uuid4()),
            symbol="2800.HK",
            signal_type="BUY",
            strength=0.8,
            price=25.70,
            timestamp=datetime.now(),
            confidence=0.85,
            reasoning="动量指标显示买入信号"
        )
        
        signal_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_analyst_001",
            receiver_id="quant_trader_001",
            message_type="TRADING_SIGNAL",
            payload=trading_signal.dict(),
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await self.message_queue.publish_message(signal_message)
        logger.info(f"  🎯 已生成交易信号: {trading_signal.signal_type} {trading_signal.symbol}")
        
        await asyncio.sleep(1)
        
        # 4. 风险分析师评估风险
        logger.info("⚠️ 步骤4: 风险分析师评估风险")
        risk_message = Message(
            id=str(uuid.uuid4()),
            sender_id="quant_trader_001",
            receiver_id="risk_analyst_001",
            message_type="RISK_ASSESSMENT",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "total_value": 2570.0
            },
            timestamp=datetime.now(),
            priority="HIGH"
        )
        
        await self.message_queue.publish_message(risk_message)
        logger.info("  🛡️ 已发送风险评估请求")
        
        await asyncio.sleep(1)
        
        # 5. 投资组合经理更新投资组合
        logger.info("💼 步骤5: 投资组合经理更新投资组合")
        portfolio_message = Message(
            id=str(uuid.uuid4()),
            sender_id="risk_analyst_001",
            receiver_id="portfolio_manager_001",
            message_type="RISK_APPROVED",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "risk_score": 0.3,
                "approved": True
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(portfolio_message)
        logger.info("  ✅ 风险已批准，投资组合将更新")
        
        await asyncio.sleep(1)
        
        # 6. 量化交易员执行交易
        logger.info("💰 步骤6: 量化交易员执行交易")
        execute_message = Message(
            id=str(uuid.uuid4()),
            sender_id="portfolio_manager_001",
            receiver_id="quant_trader_001",
            message_type="EXECUTE_TRADE",
            payload={
                "symbol": "2800.HK",
                "action": "BUY",
                "quantity": 100,
                "price": 25.70,
                "order_id": str(uuid.uuid4())
            },
            timestamp=datetime.now(),
            priority="URGENT"
        )
        
        await self.message_queue.publish_message(execute_message)
        logger.info("  🚀 交易指令已执行")
        
        logger.info("✅ 完整交易工作流程演示完成！")
    
    async def demo_research_workflow(self):
        """演示研究工作流程"""
        logger.info("\n🔬 开始演示研究工作流程...")
        
        # 1. 启动研究项目
        logger.info("📚 步骤1: 启动研究项目")
        research_message = Message(
            id=str(uuid.uuid4()),
            sender_id="user",
            receiver_id="research_analyst_001",
            message_type="CONTROL",
            payload={
                "command": "start_research",
                "parameters": {
                    "research_type": "strategy_hypothesis",
                    "focus_area": "momentum_strategies"
                }
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(research_message)
        logger.info("  📖 研究项目已启动")
        
        await asyncio.sleep(2)
        
        # 2. 请求数据支持
        logger.info("📊 步骤2: 请求数据支持")
        data_request_message = Message(
            id=str(uuid.uuid4()),
            sender_id="research_analyst_001",
            receiver_id="data_scientist_001",
            message_type="DATA_REQUEST",
            payload={
                "data_type": "historical_prices",
                "symbols": ["2800.HK", "0700.HK"],
                "period": "1Y",
                "features": ["returns", "volatility", "volume"]
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(data_request_message)
        logger.info("  📈 已请求历史数据")
        
        await asyncio.sleep(2)
        
        # 3. 生成研究报告
        logger.info("📝 步骤3: 生成研究报告")
        report_message = Message(
            id=str(uuid.uuid4()),
            sender_id="user",
            receiver_id="research_analyst_001",
            message_type="CONTROL",
            payload={
                "command": "generate_report",
                "parameters": {
                    "research_type": "strategy_hypothesis"
                }
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(report_message)
        logger.info("  📋 研究报告生成中...")
        
        logger.info("✅ 研究工作流程演示完成！")
    
    async def demo_monitoring_workflow(self):
        """演示监控工作流程"""
        logger.info("\n📊 开始演示系统监控工作流程...")
        
        # 1. 收集系统指标
        logger.info("📈 步骤1: 收集系统指标")
        metrics_message = Message(
            id=str(uuid.uuid4()),
            sender_id="system",
            receiver_id="quant_engineer_001",
            message_type="CONTROL",
            payload={
                "command": "collect_metrics",
                "parameters": {}
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(metrics_message)
        logger.info("  📊 系统指标收集中...")
        
        await asyncio.sleep(1)
        
        # 2. 执行健康检查
        logger.info("🏥 步骤2: 执行健康检查")
        health_message = Message(
            id=str(uuid.uuid4()),
            sender_id="system",
            receiver_id="quant_engineer_001",
            message_type="CONTROL",
            payload={
                "command": "run_health_check",
                "parameters": {}
            },
            timestamp=datetime.now(),
            priority="NORMAL"
        )
        
        await self.message_queue.publish_message(health_message)
        logger.info("  🔍 系统健康检查中...")
        
        logger.info("✅ 系统监控工作流程演示完成！")
    
    async def get_system_status(self):
        """获取系统状态"""
        logger.info("\n📊 系统状态:")
        
        if self.coordinator:
            statuses = await self.coordinator.get_all_agent_statuses()
            
            for agent_id, status in statuses.items():
                logger.info(f"  🤖 {agent_id}: {status['status']}")
            
            logger.info(f"  📈 活跃Agent数量: {len(statuses)}")
        
        # 获取各Agent摘要信息
        for agent_name, agent in self.agents.items():
            try:
                summary = agent.get_agent_summary()
                logger.info(f"  📋 {agent_name}: {summary}")
            except Exception as e:
                logger.warning(f"  ⚠️ {agent_name}: 无法获取状态 - {e}")
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        logger.info("\n🎮 交互式演示模式")
        logger.info("可用命令:")
        logger.info("  1. trading - 演示交易工作流程")
        logger.info("  2. research - 演示研究工作流程")
        logger.info("  3. monitoring - 演示监控工作流程")
        logger.info("  4. status - 显示系统状态")
        logger.info("  5. quit - 退出演示")
        
        while self.running:
            try:
                command = input("\n请输入命令: ").strip().lower()
                
                if command == "trading":
                    await self.demo_trading_workflow()
                elif command == "research":
                    await self.demo_research_workflow()
                elif command == "monitoring":
                    await self.demo_monitoring_workflow()
                elif command == "status":
                    await self.get_system_status()
                elif command == "quit":
                    break
                else:
                    logger.info("❌ 未知命令，请重试")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ 命令执行错误: {e}")
    
    async def cleanup(self):
        """清理系统资源"""
        logger.info("🧹 正在清理系统资源...")
        
        if self.coordinator:
            await self.coordinator.cleanup()
        
        if self.message_queue:
            await self.message_queue.cleanup()
        
        logger.info("✅ 系统清理完成")


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 港股量化交易 AI Agent 系统")
    print("=" * 60)
    
    demo = HKQuantSystemDemo()
    
    try:
        # 初始化系统
        await demo.initialize_system()
        
        # 显示系统状态
        await demo.get_system_status()
        
        # 运行演示
        print("\n选择演示模式:")
        print("1. 自动演示 (运行所有工作流程)")
        print("2. 交互式演示 (手动选择命令)")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            # 自动演示所有工作流程
            await demo.demo_trading_workflow()
            await asyncio.sleep(2)
            
            await demo.demo_research_workflow()
            await asyncio.sleep(2)
            
            await demo.demo_monitoring_workflow()
            await asyncio.sleep(2)
            
            await demo.get_system_status()
            
        elif choice == "2":
            # 交互式演示
            await demo.run_interactive_demo()
        
        else:
            logger.info("❌ 无效选择，退出")
    
    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断，正在退出...")
    
    except Exception as e:
        logger.error(f"❌ 系统错误: {e}")
    
    finally:
        await demo.cleanup()
        print("\n👋 感谢使用港股量化交易 AI Agent 系统！")


if __name__ == "__main__":
    asyncio.run(main())
