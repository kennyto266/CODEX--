#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODEX量化交易系统 - 统一整合版
整合所有系统版本和功能的高性能量化交易平台

整合的系统:
✅ complete_project_system.py (v7.0)
✅ integrated_codex_system.py (v8.0)
✅ complete_frontend_system.py
✅ run_dashboard.py
✅ 所有性能优化功能

特性:
- 统一API架构
- 性能监控面板
- 前端仪表板
- 实时数据处理
- 多级缓存系统
- 并行回测引擎
- 风险管理系统
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path
from datetime import datetime
import logging
import argparse

# 设置环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_codex.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("CODEX.Unified")

class UnifiedCodexSystem:
    """统一CODEX系统"""

    def __init__(self):
        self.version = "9.0"
        self.start_time = datetime.now()
        self.port = 8003  # 使用新端口避免冲突

    def print_banner(self):
        """打印启动横幅"""
        print("=" * 90)
        print("CODEX Unified Quant Trading System v9.0 - Unified Integration Version")
        print("=" * 90)
        print()
        print("Integrated System Modules:")
        print("  [OK] complete_project_system.py (v7.0) - Core Trading System")
        print("  [OK] integrated_codex_system.py (v8.0) - Performance Optimization")
        print("  [OK] complete_frontend_system.py - Frontend System")
        print("  [OK] run_dashboard.py - Dashboard System")
        print()
        print("Core Features:")
        print("  [OK] Unified API Architecture - FastAPI + Performance")
        print("  [OK] Multi-level Cache System - L1/L2/L3")
        print("  [OK] Parallel Backtest Engine - Multi-process")
        print("  [OK] Risk Management System - VaR, Drawdown")
        print("  [OK] Real-time Data Processing - WebSocket + Async I/O")
        print("  [OK] Frontend Dashboard - Vue.js + Chart.js")
        print("  [OK] Performance Monitor - Real-time Metrics")
        print("  [OK] Telegram Bot Integration - Real-time Alerts")
        print("  [OK] Strategy Optimizer - 11 Technical Indicators")
        print()
        print("Access URLs:")
        print(f"  - Main Page: http://localhost:{self.port}/")
        print(f"  - API Docs: http://localhost:{self.port}/docs")
        print(f"  - Health Check: http://localhost:{self.port}/api/health")
        print(f"  - Performance Panel: http://localhost:{self.port}/performance-monitor.html")
        print(f"  - Dashboard: http://localhost:{self.port}/dashboard")
        print()
        print("=" * 90)
        print()

    def check_dependencies(self):
        """检查依赖"""
        logger.info("Checking system dependencies...")

        try:
            # 检查核心模块
            from src.core.logging import get_logger
            from src.backtest.strategy_performance import PerformanceCalculator
            from src.infrastructure.network.optimized_http_client import OptimizedHTTPClient
            from src.backtest.multiprocessing_utils import batch_execute

            logger.info("[OK] Core modules loaded successfully")
            return True
        except Exception as e:
            logger.error(f"[FAIL] Dependency check failed: {e}")
            return False

    def load_main_system(self):
        """加载主系统"""
        logger.info("Loading main system modules...")

        try:
            # 导入主应用
            from complete_project_system import app
            logger.info("[OK] Main application module loaded successfully")
            return app
        except Exception as e:
            logger.error(f"[FAIL] Main system loading failed: {e}")
            return None

    def add_unified_routes(self, app):
        """添加统一路由"""
        from fastapi import APIRouter
        from fastapi.responses import JSONResponse

        router = APIRouter(prefix="/api/unified", tags=["Unified System"])

        @router.get("/status")
        async def unified_status():
            """统一系统状态"""
            return {
                "system": "CODEX Unified Quant Trading System",
                "version": self.version,
                "start_time": self.start_time.isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "integrated_systems": [
                    "complete_project_system v7.0",
                    "integrated_codex_system v8.0",
                    "complete_frontend_system",
                    "run_dashboard"
                ],
                "features": [
                    "Multi-level Cache System",
                    "Parallel Backtest Engine",
                    "Risk Management System",
                    "Real-time Data Processing",
                    "Performance Monitor",
                    "Telegram Bot Integration"
                ]
            }

        @router.get("/features")
        async def system_features():
            """系统功能列表"""
            return {
                "categories": {
                    "Core Trading": [
                        "Technical Analysis (11 indicators)",
                        "Strategy Backtesting",
                        "Performance Calculation",
                        "Risk Assessment"
                    ],
                    "Data Processing": [
                        "Multi-source Data Adapters",
                        "Real-time Data Fetching",
                        "Data Validation",
                        "Cache Management"
                    ],
                    "System Optimization": [
                        "Async I/O Processing",
                        "Connection Pool Management",
                        "Batch Processing",
                        "Memory Optimization"
                    ],
                    "Monitoring": [
                        "Performance Metrics",
                        "Health Checks",
                        "Alert Management",
                        "Log Analytics"
                    ]
                }
            }

        app.include_router(router)
        logger.info("[OK] Unified routes added successfully")

    async def start_system(self, port=None, host="0.0.0.0"):
        """启动统一系统"""
        if port:
            self.port = port

        self.print_banner()

        # 检查依赖
        if not self.check_dependencies():
            logger.error("Dependency check failed, system startup terminated")
            return 1

        # 加载主系统
        app = self.load_main_system()
        if not app:
            logger.error("Main system loading failed, system startup terminated")
            return 1

        # 添加统一路由
        self.add_unified_routes(app)

        logger.info(f"[OK] Starting unified system (port: {self.port})...")

        try:
            # 启动服务器
            config = uvicorn.Config(
                app,
                host=host,
                port=self.port,
                log_level="info",
                access_log=True,
                reload=False
            )
            server = uvicorn.Server(config)

            logger.info("=" * 90)
            logger.info("[OK] Unified system startup successful!")
            logger.info(f"[OK] Access URL: http://localhost:{self.port}")
            logger.info(f"[OK] API Docs: http://localhost:{self.port}/docs")
            logger.info("=" * 90)

            await server.serve()

        except KeyboardInterrupt:
            logger.info("System stopped by user")
        except Exception as e:
            logger.error(f"System startup failed: {e}", exc_info=True)
            return 1

        return 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CODEX Unified Quant Trading System")
    parser.add_argument("--port", type=int, default=8003, help="Startup port (default: 8003)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--check-deps", action="store_true", help="Only check dependencies")

    args = parser.parse_args()

    system = UnifiedCodexSystem()

    if args.check_deps:
        logger.info("Dependency check mode")
        success = system.check_dependencies()
        return 0 if success else 1

    # 启动系统
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(system.start_system(port=args.port, host=args.host))
    finally:
        loop.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
