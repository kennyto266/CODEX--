#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODEX Trading System - Fixed Dashboard with Complete API Endpoints

Fixed implementation addressing all 5 API endpoints required by index.html:
- GET /api/health - 系統健康檢查
- GET /api/trading/portfolio - 投資組合數據
- GET /api/trading/performance - 性能指標
- GET /api/system/status - 系統狀態
- POST /api/system/refresh - 系統刷新

Features:
- Proper asyncio event loop management (no conflicts)
- Complete REST API endpoints with proper status codes
- Mock data for testing/development
- Comprehensive logging
- Graceful shutdown handling
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio
import logging
from typing import Dict, Any

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
os.environ.setdefault("PYTHONPATH", str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hk_quant_system.dashboard")


class DashboardDataService:
    """Mock data service for dashboard API endpoints"""

    def __init__(self):
        self.startup_time = datetime.now()
        logger.info("初始化儀表板數據服務")

    async def get_health(self) -> Dict[str, Any]:
        """System health check"""
        return {
            "status": "ok",
            "service": "dashboard",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    async def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio data"""
        return {
            "initial_capital": 1000000.0,
            "portfolio_value": 1000000.0,
            "active_positions": 0,
            "total_return": 0.0,
            "total_return_pct": 0.0,
            "currency": "USD",
            "last_update": datetime.now().isoformat(),
            "positions": []
        }

    async def get_performance(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "total_return_pct": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "last_update": datetime.now().isoformat()
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        uptime = datetime.now() - self.startup_time
        uptime_seconds = int(uptime.total_seconds())
        minutes = uptime_seconds // 60
        hours = minutes // 60
        minutes = minutes % 60

        return {
            "status": "operational",
            "agents": {
                "total": 7,
                "active": 7,
                "inactive": 0
            },
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": f"{hours}h {minutes}m",
            "resources": {
                "memory_usage_mb": 256,
                "memory_available_mb": 8192,
                "cpu_usage_pct": 15.5,
                "disk_usage_pct": 45.2
            },
            "performance": {
                "active_trades": 0,
                "pending_orders": 0,
                "last_trade_timestamp": None
            },
            "last_update": datetime.now().isoformat()
        }

    async def refresh_system(self, hard_refresh: bool = False) -> Dict[str, Any]:
        """Refresh system data"""
        return {
            "status": "success",
            "refresh_type": "hard" if hard_refresh else "soft",
            "timestamp": datetime.now().isoformat(),
            "affected_systems": [
                "portfolio",
                "performance",
                "agent_status"
            ]
        }


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="CODEX Trading Dashboard",
        description="Real-time Dashboard for Multi-Agent Trading System",
        version="1.0.0"
    )

    # Initialize data service
    data_service = DashboardDataService()

    # ==================== HTML Routes ====================

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve main dashboard HTML"""
        try:
            with open(project_root / "src/dashboard/templates/index.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Dashboard HTML 文件未找到，使用備用頁面")
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>CODEX Trading Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    h1 { color: #333; }
                    .status { padding: 20px; background: #f0f0f0; border-radius: 5px; }
                    .success { color: green; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ CODEX Trading Dashboard</h1>
                    <div class="status">
                        <p class="success">Dashboard API 已啟動！</p>
                        <p>訪問 API 文檔: <a href="/docs">/docs</a></p>
                    </div>
                </div>
            </body>
            </html>
            """

    # ==================== Health Check ====================

    @app.get("/api/health")
    async def health():
        """System health check endpoint"""
        logger.debug("API 調用: GET /api/health")
        return await data_service.get_health()

    @app.get("/health")
    async def health_alias():
        """Health check alias endpoint"""
        logger.debug("API 調用: GET /health")
        return await data_service.get_health()

    # ==================== Trading API ====================

    @app.get("/api/trading/portfolio")
    async def get_portfolio():
        """Get portfolio data endpoint"""
        logger.debug("API 調用: GET /api/trading/portfolio")
        return await data_service.get_portfolio()

    @app.get("/api/trading/performance")
    async def get_performance():
        """Get performance metrics endpoint"""
        logger.debug("API 調用: GET /api/trading/performance")
        return await data_service.get_performance()

    # ==================== System API ====================

    @app.get("/api/system/status")
    async def get_system_status():
        """Get system status endpoint"""
        logger.debug("API 調用: GET /api/system/status")
        return await data_service.get_system_status()

    @app.post("/api/system/refresh")
    async def refresh_system(hard_refresh: bool = False):
        """System refresh endpoint"""
        logger.debug(f"API 調用: POST /api/system/refresh (hard_refresh={hard_refresh})")
        return await data_service.refresh_system(hard_refresh)

    # ==================== Favicon ====================

    @app.get("/favicon.ico")
    async def favicon():
        """Return a simple favicon (base64 encoded 1x1 transparent PNG)"""
        import base64
        from fastapi.responses import Response

        # 1x1 transparent PNG in base64
        favicon_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return Response(content=favicon_data, media_type="image/x-icon")

    logger.info("✅ FastAPI 應用已創建，共註冊 8 條路由")
    return app


async def main():
    """Main async entry point"""
    logger = logging.getLogger("hk_quant_system.dashboard")

    try:
        logger.info("🚀 啟動 CODEX Trading Dashboard...")

        # Create FastAPI application
        app = create_app()

        # Create uvicorn config
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )

        # Create server
        server = uvicorn.Server(config)

        logger.info("✅ 儀表板服務啟動成功")
        logger.info("🌐 訪問地址: http://localhost:8001")
        logger.info("📚 API 文檔: http://localhost:8001/docs")
        logger.info("⏹️ 按 Ctrl+C 停止系統")

        # Run server in current event loop
        await server.serve()

    except KeyboardInterrupt:
        logger.info("🛑 收到停止信號，正在關閉系統...")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}", exc_info=True)
        raise
    finally:
        logger.info("👋 儀表板已關閉")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("系統已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"致命錯誤: {e}", exc_info=True)
        sys.exit(1)
