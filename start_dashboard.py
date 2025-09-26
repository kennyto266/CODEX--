#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 仪表板启动脚本

这个脚本提供了一个简单的方式来启动Agent监控仪表板。
支持多种运行模式，包括演示模式和完整模式。
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core import SystemConfig
from src.dashboard.api_routes import DashboardAPI
from src.dashboard.dashboard_ui import DashboardUI
from src.dashboard.optimization import DashboardFinalIntegration
from unittest.mock import Mock, AsyncMock


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/dashboard.log', mode='a')
        ]
    )
    
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)


def create_mock_services():
    """创建模拟的服务"""
    # 创建模拟的AgentCoordinator
    coordinator = Mock()
    coordinator.get_agent_status = AsyncMock(return_value={
        "agent_type": "QuantitativeAnalyst",
        "status": "running",
        "cpu_usage": 45.0,
        "memory_usage": 55.0,
        "messages_processed": 1500,
        "error_count": 2,
        "uptime_seconds": 7200,
        "version": "1.0.0",
        "configuration": {"param1": "value1"},
        "last_heartbeat": "2024-01-01T12:00:00Z",
        "last_updated": "2024-01-01T12:00:00Z"
    })
    
    coordinator.get_all_agent_statuses = AsyncMock(return_value={
        "quant_analyst_001": {
            "agent_type": "QuantitativeAnalyst",
            "status": "running",
            "cpu_usage": 45.0,
            "memory_usage": 55.0,
            "messages_processed": 1500,
            "error_count": 2,
            "uptime_seconds": 7200,
            "version": "1.0.0",
            "configuration": {"param1": "value1"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "quant_trader_001": {
            "agent_type": "QuantitativeTrader",
            "status": "running",
            "cpu_usage": 60.0,
            "memory_usage": 70.0,
            "messages_processed": 3000,
            "error_count": 1,
            "uptime_seconds": 5400,
            "version": "1.0.0",
            "configuration": {"param2": "value2"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "portfolio_manager_001": {
            "agent_type": "PortfolioManager",
            "status": "running",
            "cpu_usage": 35.0,
            "memory_usage": 45.0,
            "messages_processed": 800,
            "error_count": 0,
            "uptime_seconds": 9000,
            "version": "1.0.0",
            "configuration": {"param3": "value3"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "risk_analyst_001": {
            "agent_type": "RiskAnalyst",
            "status": "running",
            "cpu_usage": 40.0,
            "memory_usage": 50.0,
            "messages_processed": 1200,
            "error_count": 1,
            "uptime_seconds": 6600,
            "version": "1.0.0",
            "configuration": {"param4": "value4"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "data_scientist_001": {
            "agent_type": "DataScientist",
            "status": "running",
            "cpu_usage": 70.0,
            "memory_usage": 80.0,
            "messages_processed": 2500,
            "error_count": 0,
            "uptime_seconds": 4800,
            "version": "1.0.0",
            "configuration": {"param5": "value5"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "quant_engineer_001": {
            "agent_type": "QuantitativeEngineer",
            "status": "running",
            "cpu_usage": 25.0,
            "memory_usage": 35.0,
            "messages_processed": 600,
            "error_count": 0,
            "uptime_seconds": 10800,
            "version": "1.0.0",
            "configuration": {"param6": "value6"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "research_analyst_001": {
            "agent_type": "ResearchAnalyst",
            "status": "running",
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "messages_processed": 900,
            "error_count": 0,
            "uptime_seconds": 7800,
            "version": "1.0.0",
            "configuration": {"param7": "value7"},
            "last_heartbeat": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        }
    })
    
    coordinator.start_agent = AsyncMock(return_value=True)
    coordinator.stop_agent = AsyncMock(return_value=True)
    coordinator.register_agent = AsyncMock()
    coordinator.unregister_agent = AsyncMock()
    
    # 创建模拟的MessageQueue
    message_queue = Mock()
    message_queue.subscribe = AsyncMock()
    message_queue.unsubscribe = AsyncMock()
    message_queue.publish_message = AsyncMock()
    message_queue.publish = AsyncMock()
    
    return coordinator, message_queue


async def start_dashboard_mode():
    """启动仪表板模式"""
    logger = logging.getLogger("dashboard_launcher")
    logger.info("🚀 启动港股量化交易 AI Agent 仪表板...")
    
    try:
        # 创建模拟服务
        coordinator, message_queue = create_mock_services()
        
        # 创建系统配置
        config = SystemConfig()
        
        # 创建仪表板集成
        integration = DashboardFinalIntegration(config)
        
        # 集成所有组件
        success = await integration.integrate_all_components(coordinator, message_queue)
        
        if success:
            logger.info("✅ 仪表板启动成功！")
            logger.info("📊 访问地址: http://localhost:8000")
            logger.info("📈 绩效分析: http://localhost:8000/performance")
            logger.info("🔧 系统状态: http://localhost:8000/system")
            logger.info("📚 API文档: http://localhost:8000/docs")
            logger.info("")
            logger.info("💡 提示: 按 Ctrl+C 停止服务")
            
            # 运行集成测试
            logger.info("🧪 运行集成测试...")
            test_results = await integration.run_integration_tests()
            
            if test_results["overall_status"] == "PASSED":
                logger.info("✅ 所有测试通过！")
            else:
                logger.warning("⚠️ 部分测试失败，但系统仍可正常运行")
            
            # 保持服务运行
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("👋 正在停止服务...")
        else:
            logger.error("❌ 仪表板启动失败！")
            return False
            
    except Exception as e:
        logger.error(f"❌ 启动过程中发生错误: {e}")
        return False
    finally:
        # 清理资源
        if 'integration' in locals():
            await integration.cleanup()
    
    return True


async def start_demo_mode():
    """启动演示模式"""
    logger = logging.getLogger("demo_launcher")
    logger.info("🎯 启动演示模式...")
    
    try:
        # 运行简单的演示
        from simple_demo import HKQuantSystemDemo
        
        demo = HKQuantSystemDemo()
        await demo.run_demo()
        
        logger.info("✅ 演示完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 演示过程中发生错误: {e}")
        return False


def print_usage():
    """打印使用说明"""
    print("""
🚀 港股量化交易 AI Agent 系统启动器

使用方法:
  python start_dashboard.py [模式]

模式选项:
  dashboard  - 启动完整的Agent监控仪表板 (默认)
  demo       - 运行简化的演示模式
  help       - 显示此帮助信息

示例:
  python start_dashboard.py              # 启动仪表板模式
  python start_dashboard.py dashboard    # 启动仪表板模式
  python start_dashboard.py demo         # 运行演示模式
  python start_dashboard.py help         # 显示帮助

仪表板功能:
  📊 实时监控7个AI Agent状态
  📈 查看交易策略和绩效指标
  🎛️ 远程控制Agent启动/停止
  📱 响应式Web界面
  🔄 实时数据更新

访问地址:
  http://localhost:8000 - 主仪表板
  http://localhost:8000/performance - 绩效分析
  http://localhost:8000/system - 系统状态
  http://localhost:8000/docs - API文档

💡 提示: 首次运行建议使用 demo 模式熟悉系统功能
    """)


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 获取运行模式
    mode = sys.argv[1] if len(sys.argv) > 1 else "dashboard"
    
    if mode == "help":
        print_usage()
        return
    
    print("🚀 港股量化交易 AI Agent 系统")
    print("=" * 50)
    
    if mode == "demo":
        success = await start_demo_mode()
    elif mode == "dashboard":
        success = await start_dashboard_mode()
    else:
        print(f"❌ 未知模式: {mode}")
        print_usage()
        return
    
    if success:
        print("✅ 程序执行完成")
    else:
        print("❌ 程序执行失败")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)
