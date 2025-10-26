#!/usr/bin/env python3
"""
港股量化交易 AI Agent 系统 - 仪表板启动脚本

这个脚本解决了相对导入问题，可以直接运行仪表板系统。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(project_root))

# 导入必要的模块
from src.core import SystemConfig, setup_logging
from src.dashboard.dashboard_ui import DashboardUI
from src.dashboard.api_routes import DashboardAPI
import asyncio
import uvicorn
import logging

def create_mock_dashboard_api():
    """创建模拟的DashboardAPI用于测试"""
    class MockDashboardAPI:
        def __init__(self):
            self.logger = logging.getLogger("mock_dashboard_api")
        
        async def get_all_agents(self):
            """返回模拟的Agent数据"""
            from src.core import SystemConstants
            
            mock_agents = []
            for i, agent_type in enumerate(SystemConstants.AGENT_TYPES):
                agent_data = {
                    "agent_id": f"{agent_type}_{i+1}",
                    "agent_type": agent_type,
                    "status": "running",
                    "last_activity": "2024-01-01T12:00:00Z",
                    "performance_metrics": {
                        "total_trades": 100 + i * 10,
                        "win_rate": 0.65 + i * 0.02,
                        "sharpe_ratio": 1.2 + i * 0.1,
                        "max_drawdown": 0.05 - i * 0.001
                    },
                    "current_strategy": f"Strategy_{i+1}",
                    "risk_level": "medium" if i % 2 == 0 else "low"
                }
                
                # 创建简单的Agent对象
                class MockAgent:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)
                    
                    def dict(self):
                        return {k: v for k, v in self.__dict__.items()}
                
                mock_agents.append(MockAgent(agent_data))
            
            return mock_agents
        
        async def get_system_status(self):
            """返回模拟的系统状态"""
            return {
                "system_health": "healthy",
                "total_agents": 7,
                "active_agents": 7,
                "system_uptime": "24h 15m",
                "total_trades": 1250,
                "system_performance": {
                    "cpu_usage": 25.5,
                    "memory_usage": 2048,
                    "disk_usage": 15.2
                },
                "last_update": "2024-01-01T12:00:00Z"
            }
    
    return MockDashboardAPI()

async def main():
    """主函数 - 使用 uvicorn.Server 低階 API 避免事件循環衝突"""
    logger = logging.getLogger("hk_quant_system.dashboard")
    dashboard_ui = None

    try:
        # 設置日誌
        config = SystemConfig()
        setup_logging(config)

        logger.info("🚀 啟動港股量化交易 AI Agent 儀表板...")

        # 創建模擬的 DashboardAPI
        dashboard_api = create_mock_dashboard_api()

        # 創建儀表板 UI
        dashboard_ui = DashboardUI(dashboard_api, config)

        # 啟動儀表板
        await dashboard_ui.start()
        logger.info("✅ 儀表板服務初始化成功")

        # 獲取 FastAPI 應用
        app = dashboard_ui.get_app()
        logger.info("🌐 訪問地址: http://localhost:8001")
        logger.info("📊 功能: 多智能體監控、實時數據、性能分析")
        logger.info("⏹️ 按 Ctrl+C 停止系統")

        # 使用 uvicorn.Server 低階 API - 避免事件循環衝突
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        server = uvicorn.Server(config)

        # 在現有事件循環中運行服務器
        await server.serve()

    except KeyboardInterrupt:
        logger.info("🛑 收到停止信號，正在關閉系統...")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}", exc_info=True)
        raise
    finally:
        if dashboard_ui is not None:
            try:
                await dashboard_ui.cleanup()
            except Exception as e:
                logger.error(f"清理失敗: {e}")
        logger.info("👋 系統已關閉")

if __name__ == "__main__":
    # 運行主函數
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger = logging.getLogger("hk_quant_system.dashboard")
        logger.error(f"致命錯誤: {e}", exc_info=True)
        sys.exit(1)
