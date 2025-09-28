#!/usr/bin/env python3
"""
简化启动脚本 - 避免内存问题
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def start_simple_dashboard():
    """启动简化仪表板"""
    try:
        print("🚀 启动简化仪表板...")
        
        # 导入必要的模块
        from src.core import SystemConfig
        from src.dashboard.api_routes import DashboardAPI
        from src.dashboard.dashboard_ui import DashboardUI
        from unittest.mock import Mock, AsyncMock
        
        # 创建模拟的coordinator和message_queue
        coordinator = Mock()
        coordinator.get_status = AsyncMock(return_value={"status": "running"})
        
        message_queue = Mock()
        message_queue.get_status = AsyncMock(return_value={"status": "connected"})
        
        # 创建配置
        config = SystemConfig()
        config.update_interval = 10  # 增加更新间隔，减少资源消耗
        
        # 创建DashboardAPI
        dashboard_api = DashboardAPI(coordinator, message_queue, config)
        
        # 创建DashboardUI
        dashboard_ui = DashboardUI(dashboard_api, config)
        
        # 启动服务
        await dashboard_ui.start()
        
        print("✅ 简化仪表板启动成功!")
        print("🌐 访问地址: http://localhost:8000")
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
    print("🚀 港股量化交易 AI Agent 系统 - 简化启动")
    print("=" * 50)
    
    setup_logging()
    
    try:
        asyncio.run(start_simple_dashboard())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        print("💡 建议使用演示模式: python demo.py")

if __name__ == "__main__":
    main()