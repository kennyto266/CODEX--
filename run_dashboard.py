#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化交易 AI Agent 系統 - 儀表板啟動腳本 (已修復)

這個腳本解決了：
1. asyncio 事件循環衝突（使用 uvicorn.Server 低階 API）
2. 完整的 REST API 端點實現（5 個核心端點）
3. 系統狀態檢查和刷新功能

已修復的問題：
- 修復了 asyncio.run() 與 uvicorn.run() 的衝突
- 實現了所有缺失的 API 端點
- 添加了適當的錯誤處理和日誌記錄
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio
import logging
from typing import Dict, Any

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 設置環境變量
os.environ.setdefault("PYTHONPATH", str(project_root))

# 導入必要的模塊
try:
    from src.core import SystemConfig, setup_logging
    from src.dashboard.dashboard_ui import DashboardUI
except ImportError as e:
    logging.warning(f"無法導入 src 模塊，使用基本實現: {e}")
    SystemConfig = None
    setup_logging = None
    DashboardUI = None

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn


# ==================== Data Service ====================

class DashboardDataService:
    """儀表板數據服務 - 提供 Mock 數據"""

    def __init__(self):
        self.startup_time = datetime.now()
        logger = logging.getLogger("hk_quant_system.dashboard")
        logger.info("初始化儀表板數據服務")

    async def get_health(self) -> Dict[str, Any]:
        """系統健康檢查"""
        return {
            "status": "ok",
            "service": "dashboard",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    async def get_portfolio(self) -> Dict[str, Any]:
        """獲取投資組合數據"""
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
        """獲取性能指標"""
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
        """獲取系統狀態"""
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
        """刷新系統數據"""
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


def create_app(data_service: DashboardDataService) -> FastAPI:
    """創建並配置 FastAPI 應用"""
    app = FastAPI(
        title="CODEX Trading Dashboard",
        description="實時儀表板 - 多智能體交易系統",
        version="1.0.0"
    )

    logger = logging.getLogger("hk_quant_system.dashboard")

    # ==================== HTML Routes ====================

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """提供主儀表板 HTML"""
        try:
            with open(project_root / "src/dashboard/templates/index.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("儀表板 HTML 文件未找到，使用備用頁面")
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
                    <h1>CODEX Trading Dashboard</h1>
                    <div class="status">
                        <p class="success">儀表板 API 已啟動！</p>
                        <p>訪問 API 文檔: <a href="/docs">/docs</a></p>
                    </div>
                </div>
            </body>
            </html>
            """

    # ==================== Health Check ====================

    @app.get("/api/health")
    async def health():
        """系統健康檢查端點"""
        logger.debug("API 調用: GET /api/health")
        return await data_service.get_health()

    @app.get("/health")
    async def health_alias():
        """健康檢查別名端點"""
        logger.debug("API 調用: GET /health")
        return await data_service.get_health()

    # ==================== Trading API ====================

    @app.get("/api/trading/portfolio")
    async def get_portfolio():
        """獲取投資組合數據"""
        logger.debug("API 調用: GET /api/trading/portfolio")
        return await data_service.get_portfolio()

    @app.get("/api/trading/performance")
    async def get_performance():
        """獲取性能指標"""
        logger.debug("API 調用: GET /api/trading/performance")
        return await data_service.get_performance()

    # ==================== System API ====================

    @app.get("/api/system/status")
    async def get_system_status():
        """獲取系統狀態"""
        logger.debug("API 調用: GET /api/system/status")
        return await data_service.get_system_status()

    @app.post("/api/system/refresh")
    async def refresh_system(hard_refresh: bool = False):
        """系統刷新端點"""
        logger.debug(f"API 調用: POST /api/system/refresh (hard_refresh={hard_refresh})")
        return await data_service.refresh_system(hard_refresh)

    # ==================== Favicon ====================

    @app.get("/favicon.ico")
    async def favicon():
        """返回 favicon"""
        import base64
        from fastapi.responses import Response

        # 1x1 transparent PNG
        favicon_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return Response(content=favicon_data, media_type="image/x-icon")

    # ==================== Stock Data API ====================

    @app.get("/api/stock/data")
    async def get_stock_data(symbol: str) -> Dict[str, Any]:
        """獲取股票數據"""
        logger.debug(f"API 調用: GET /api/stock/data?symbol={symbol}")

        # Mock 股票數據 - 實際使用時應連接真實數據源
        mock_stocks = {
            "0700.HK": {
                "symbol": "0700.HK",
                "name": "Tencent (騰訊)",
                "last_price": 325.50,
                "change": 2.50,
                "change_percent": 0.77,
                "high": 328.00,
                "low": 321.00,
                "volume": 45230000,
                "market_cap": "3.2T"
            },
            "0939.HK": {
                "symbol": "0939.HK",
                "name": "China Construction Bank (中國建設銀行)",
                "last_price": 6.85,
                "change": -0.05,
                "change_percent": -0.72,
                "high": 7.00,
                "low": 6.80,
                "volume": 123450000,
                "market_cap": "1.1T"
            },
            "0388.HK": {
                "symbol": "0388.HK",
                "name": "Hong Kong Exchanges (香港交易所)",
                "last_price": 420.80,
                "change": 5.20,
                "change_percent": 1.25,
                "high": 425.00,
                "low": 415.00,
                "volume": 2340000,
                "market_cap": "354B"
            },
            "1398.HK": {
                "symbol": "1398.HK",
                "name": "ICBC (工商銀行)",
                "last_price": 5.42,
                "change": -0.02,
                "change_percent": -0.37,
                "high": 5.50,
                "low": 5.38,
                "volume": 234560000,
                "market_cap": "923B"
            }
        }

        symbol_upper = symbol.upper()

        if symbol_upper in mock_stocks:
            stock_data = mock_stocks[symbol_upper]
            stock_data["timestamp"] = datetime.now().isoformat()
            return stock_data
        else:
            # 如果沒有在 mock 數據中找到，返回默認結構
            return {
                "symbol": symbol_upper,
                "name": "Unknown Stock",
                "last_price": 0.0,
                "change": 0.0,
                "change_percent": 0.0,
                "high": 0.0,
                "low": 0.0,
                "volume": 0,
                "market_cap": "N/A",
                "timestamp": datetime.now().isoformat(),
                "note": "This is mock data. For real data, connect to actual data source."
            }

    logger.info("FastAPI 應用已創建，共註冊 9 條路由")
    return app


async def main():
    """主函數 - 使用 uvicorn.Server 低階 API 避免事件循環衝突"""
    logger = logging.getLogger("hk_quant_system.dashboard")

    try:
        # 嘗試設置日誌（如果 SystemConfig 可用）
        if SystemConfig and setup_logging:
            try:
                config = SystemConfig()
                setup_logging(config)
            except Exception as e:
                logger.warning(f"無法使用 SystemConfig，使用基本日誌: {e}")

        logger.info("🚀 啟動 CODEX Trading Dashboard...")

        # 創建儀表板數據服務
        data_service = DashboardDataService()

        # 創建 FastAPI 應用
        app = create_app(data_service)
        logger.info("✅ FastAPI 應用已創建")

        # 顯示啟動資訊
        logger.info("🌐 訪問地址: http://localhost:8001")
        logger.info("📚 API 文檔: http://localhost:8001/docs")
        logger.info("🔧 功能: 實時儀表板、API 端點、性能監控")
        logger.info("⏹️ 按 Ctrl+C 停止系統")

        # 使用 uvicorn.Server 低階 API - 避免事件循環衝突
        server_config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        server = uvicorn.Server(server_config)

        # 在現有事件循環中運行服務器
        await server.serve()

    except KeyboardInterrupt:
        logger.info("🛑 收到停止信號，正在關閉系統...")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}", exc_info=True)
        raise
    finally:
        logger.info("👋 儀表板已關閉")


if __name__ == "__main__":
    # 設置基本日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 運行主函數
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger = logging.getLogger("hk_quant_system.dashboard")
        logger.error(f"致命錯誤: {e}", exc_info=True)
        sys.exit(1)
