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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import new API routes
from src.dashboard.api_backtest import create_backtest_router
from src.dashboard.api_agents import create_agents_router
from src.dashboard.api_risk import create_risk_router
from src.dashboard.api_strategies import create_strategies_router
from src.dashboard.api_trading import create_trading_router
from src.dashboard.websocket_manager import WebSocketManager


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

    # ==================== CORS Middleware ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================== Initialize WebSocket Manager ====================
    # ==================== Static File Service Configuration ====================
    from fastapi.staticfiles import StaticFiles

    # Create static directory structure
    static_dir = project_root / "src" / "dashboard" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (static_dir / "js" / "components").mkdir(parents=True, exist_ok=True)
    (static_dir / "js" / "stores").mkdir(parents=True, exist_ok=True)
    (static_dir / "js" / "router").mkdir(parents=True, exist_ok=True)
    (static_dir / "js" / "utils").mkdir(parents=True, exist_ok=True)
    (static_dir / "css").mkdir(parents=True, exist_ok=True)
    (static_dir / "assets").mkdir(parents=True, exist_ok=True)

    logger.info(f"Created static directory structure at {static_dir}")

    # Mount static files at /static
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static"
    )

    # Mount JavaScript files at /static/js
    app.mount(
        "/static/js",
        StaticFiles(directory=str(static_dir / "js")),
        name="static-js"
    )

    # Mount CSS files at /static/css
    app.mount(
        "/static/css",
        StaticFiles(directory=str(static_dir / "css")),
        name="static-css"
    )

    # Mount assets at /static/assets
    app.mount(
        "/static/assets",
        StaticFiles(directory=str(static_dir / "assets")),
        name="static-assets"
    )

    logger.info("✅ Static file services mounted at /static/*")
    ws_manager = WebSocketManager()

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

    # ==================== Register New API Routes ====================
    logger.info("註冊新的 API 路由...")

    # Register all new routers
    app.include_router(create_backtest_router())
    app.include_router(create_agents_router())
    app.include_router(create_risk_router())
    app.include_router(create_strategies_router())
    app.include_router(create_trading_router())

    logger.info("✅ 所有 API 路由已註冊")

    # ==================== WebSocket Endpoints ====================

    @app.websocket("/ws/portfolio")
    async def websocket_portfolio(websocket: WebSocket):
        """
        WebSocket 端點：投資組合實時更新

        客戶端可以訂閱投資組合變化：
        - 頭寸更新
        - 資產淨值變化
        - 性能指標更新
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
            logger.info("客戶端斷開連接: /ws/portfolio")

    @app.websocket("/ws/orders")
    async def websocket_orders(websocket: WebSocket):
        """
        WebSocket 端點：訂單實時推送

        推送事件：
        - 訂單已提交
        - 訂單已成交
        - 訂單已取消
        - 成交通知
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
            logger.info("客戶端斷開連接: /ws/orders")

    @app.websocket("/ws/risk")
    async def websocket_risk(websocket: WebSocket):
        """
        WebSocket 端點：風險告警推送

        推送事件：
        - 新告警
        - 告警確認
        - 風險指標更新
        - 壓力測試結果
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
            logger.info("客戶端斷開連接: /ws/risk")

    @app.websocket("/ws/system")
    async def websocket_system(websocket: WebSocket):
        """
        WebSocket 端點：系統監控數據

        推送事件：
        - CPU/內存使用率
        - 回測進度
        - Agent 狀態
        - 交易統計
        """
        await ws_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
            logger.info("客戶端斷開連接: /ws/system")

    @app.get("/ws/status")
    async def get_websocket_status():
        """獲取 WebSocket 連接狀態"""
        return {
            "active_connections": ws_manager.get_connection_count(),
            "connection_info": ws_manager.get_connection_info(),
            "timestamp": datetime.now().isoformat()
        }

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
    async def get_stock_data(
        symbol: str,
        duration: int = 365
    ) -> Dict[str, Any]:
        """
        獲取股票數據（連接真實 HKEX 數據源）

        注意：此端點專門用於連接真實的 HKEX 數據源。
        如果數據源不可用，將返回明確的錯誤信息，不會回退到 Mock 數據。

        HKEX 和 gov_crawler 是獨立的數據項目，請參考：
        - HKEX 數據源: /api/stock/data
        - gov_crawler 數據源: /api/gov/data

        Args:
            symbol: 股票代碼 (e.g., "0700.HK")
            duration: 時間範圍（天數，默認 365 天）

        Returns:
            股票信息字典 或 錯誤信息

        Raises:
            HTTPException: 當數據源不可用或連接失敗時
        """
        logger.debug(f"API 調用: GET /api/stock/data?symbol={symbol}&duration={duration}")

        try:
            # 導入真實數據適配器
            from src.data_adapters.realtime_hkex_adapter import get_adapter
            from fastapi import HTTPException

            # 獲取適配器實例
            adapter = get_adapter()

            # 從真實 API 獲取數據（在線程中運行同步方法以避免阻塞）
            stock_data = await asyncio.to_thread(
                adapter.fetch_stock_data,
                symbol,
                duration
            )

            if stock_data:
                logger.info(f"✅ 成功獲取 {symbol} 的 HKEX 數據")
                return stock_data
            else:
                logger.error(f"❌ HKEX 數據源返回空數據: {symbol}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "SERVICE_UNAVAILABLE",
                        "message": f"HKEX 數據源暫時無法返回 {symbol} 的數據",
                        "symbol": symbol.upper(),
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "HKEX API",
                        "note": "請檢查 HKEX 數據源連接或稍後重試"
                    }
                )

        except ImportError as e:
            logger.error(f"❌ 無法導入 HKEX 數據適配器: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "ADAPTER_NOT_AVAILABLE",
                    "message": "HKEX 數據適配器未正確安裝或配置",
                    "symbol": symbol.upper(),
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "HKEX API",
                    "note": "請檢查 src/data_adapters/realtime_hkex_adapter 是否存在"
                }
            )

        except Exception as e:
            logger.error(f"❌ 獲取 HKEX 股票數據失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "DATA_SOURCE_ERROR",
                    "message": f"無法從 HKEX 數據源獲取 {symbol} 的數據",
                    "symbol": symbol.upper(),
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "HKEX API",
                    "error_details": str(e),
                    "note": "請檢查 HKEX 數據源連接或稍後重試"
                }
            )

    logger.info("✅ FastAPI 應用已創建，共註冊 25+ 條 API 路由 + 4 個 WebSocket 端點")

    # ==================== Gov Data API ====================

    @app.get("/api/gov/data")
    async def get_gov_data(
        indicator: str = "hibor_overnight",
        start_date: str = "2024-01-01",
        end_date: str = "2025-10-28"
    ) -> Dict[str, Any]:
        """
        獲取 gov_crawler 政府數據（獨立數據項目）

        注意：此端點連接 gov_crawler 數據收集系統。
        gov_crawler 是獨立的數據項目，專門收集香港政府開放數據。

        數據源區分：
        - HKEX 數據源: /api/stock/data (股票數據)
        - gov_crawler 數據源: /api/gov/data (政府數據)

        Args:
            indicator: 指標類型 (e.g., "hibor_overnight", "property_price", "gdp")
            start_date: 開始日期 (格式: YYYY-MM-DD)
            end_date: 結束日期 (格式: YYYY-MM-DD)

        Returns:
            政府數據字典

        Raises:
            HTTPException: 當數據源不可用時
        """
        logger.debug(f"API 調用: /api/gov/data?indicator={indicator}&start_date={start_date}&end_date={end_date}")

        try:
            from fastapi import HTTPException

            # 嘗試連接 gov_crawler 數據收集系統
            # 注意：這是一個獨立的數據項目
            gov_crawler_path = project_root / "gov_crawler"

            if not gov_crawler_path.exists():
                logger.error(f"❌ gov_crawler 項目未找到: {gov_crawler_path}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "PROJECT_NOT_FOUND",
                        "message": "gov_crawler 數據收集項目未正確安裝",
                        "indicator": indicator,
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "gov_crawler",
                        "note": "請檢查 gov_crawler 目錄是否存在"
                    }
                )

            # 檢查數據文件是否存在
            data_file = gov_crawler_path / "data" / "all_alternative_data_20251023_210419.json"

            if data_file.exists():
                logger.info(f"✅ 找到 gov_crawler 數據文件: {data_file}")
                import json
                with open(data_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)

                # 根據指標返回相應數據
                # Gov crawler 數據結構: {'hibor': {'hibor_overnight': {...}}, 'property': {...}, ...}
                if indicator in all_data:
                    result = {
                        "indicator": indicator,
                        "data": all_data[indicator],
                        "source": "gov_crawler",
                        "timestamp": datetime.now().isoformat(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "note": "數據來自 gov_crawler 政府數據收集系統"
                    }
                    logger.info(f"✅ 成功獲取 gov_crawler 指標: {indicator}")
                    return result
                else:
                    # 嘗試在嵌套結構中查找
                    found = False
                    for category, indicators in all_data.items():
                        if isinstance(indicators, dict) and indicator in indicators:
                            result = {
                                "indicator": indicator,
                                "category": category,
                                "data": indicators[indicator],
                                "source": "gov_crawler",
                                "timestamp": datetime.now().isoformat(),
                                "start_date": start_date,
                                "end_date": end_date,
                                "note": "數據來自 gov_crawler 政府數據收集系統"
                            }
                            logger.info(f"✅ 成功獲取 gov_crawler 指標: {indicator} (分類: {category})")
                            return result

                    logger.warning(f"⚠️ 指標 {indicator} 不存在於 gov_crawler 數據中")
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "error": "INDICATOR_NOT_FOUND",
                            "message": f"指標 '{indicator}' 不存在於 gov_crawler 數據中",
                            "available_indicators": list(all_data.keys()),
                            "timestamp": datetime.now().isoformat(),
                            "data_source": "gov_crawler"
                        }
                    )
            else:
                logger.warning(f"⚠️ gov_crawler 數據文件不存在: {data_file}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "DATA_NOT_AVAILABLE",
                        "message": "gov_crawler 數據文件未找到或尚未生成",
                        "indicator": indicator,
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "gov_crawler",
                        "note": f"請運行 gov_crawler/collect_all_alternative_data.py 生成數據",
                        "data_file_path": str(data_file)
                    }
                )

        except HTTPException:
            # 重新拋出 HTTPException
            raise

        except Exception as e:
            logger.error(f"❌ 獲取 gov_crawler 數據失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "DATA_SOURCE_ERROR",
                    "message": f"無法從 gov_crawler 獲取 {indicator} 的數據",
                    "indicator": indicator,
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "gov_crawler",
                    "error_details": str(e),
                    "note": "請檢查 gov_crawler 系統是否正確運行"
                }
            )

    @app.get("/api/gov/indicators")
    async def get_available_gov_indicators() -> Dict[str, Any]:
        """
        獲取 gov_crawler 可用的指標列表

        Returns:
            可用指標列表
        """
        logger.debug("API 調用: GET /api/gov/indicators")

        try:
            from fastapi import HTTPException
            import json

            gov_crawler_path = project_root / "gov_crawler"
            data_file = gov_crawler_path / "data" / "all_alternative_data_20251023_210419.json"

            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)

                # 展平指標列表
                all_indicators = []
                for category, indicators in all_data.items():
                    if isinstance(indicators, dict):
                        for indicator in indicators.keys():
                            all_indicators.append(indicator)

                indicators = {
                    "total_indicators": len(all_indicators),
                    "total_categories": len(all_data),
                    "categories": list(all_data.keys()),
                    "indicators": all_indicators,
                    "data_source": "gov_crawler",
                    "last_update": datetime.now().isoformat(),
                    "note": "數據來自 gov_crawler 政府數據收集系統"
                }

                logger.info(f"✅ 成功獲取 {len(all_indicators)} 個 gov_crawler 指標")
                return indicators
            else:
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "DATA_NOT_AVAILABLE",
                        "message": "gov_crawler 數據文件未找到",
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "gov_crawler",
                        "note": "請運行 gov_crawler/collect_all_alternative_data.py 生成數據"
                    }
                )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"❌ 獲取 gov_crawler 指標列表失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "DATA_SOURCE_ERROR",
                    "message": "無法獲取 gov_crawler 指標列表",
                    "timestamp": datetime.now().isoformat(),
                    "data_source": "gov_crawler",
                    "error_details": str(e)
                }
            )

    @app.get("/api/gov/status")
    async def get_gov_crawler_status() -> Dict[str, Any]:
        """
        獲取 gov_crawler 系統狀態

        Returns:
            gov_crawler 系統狀態信息
        """
        logger.debug("API 調用: GET /api/gov/status")

        try:
            from fastapi import HTTPException
            import json
            import os

            gov_crawler_path = project_root / "gov_crawler"
            data_file = gov_crawler_path / "data" / "all_alternative_data_20251023_210419.json"

            status = {
                "project": "gov_crawler",
                "status": "unknown",
                "data_source": "gov_crawler",
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }

            # 檢查項目目錄
            if gov_crawler_path.exists():
                status["checks"]["project_directory"] = "✅ 存在"
                status["project_found"] = True
            else:
                status["checks"]["project_directory"] = "❌ 不存在"
                status["project_found"] = False
                status["status"] = "not_installed"

            # 檢查數據文件
            if data_file.exists():
                stat = os.stat(data_file)
                file_size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()

                status["checks"]["data_file"] = "✅ 存在"
                status["data_file_size"] = f"{file_size / 1024:.2f} KB"
                status["data_file_mtime"] = mtime
                status["data_available"] = True

                # 讀取指標數量
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        all_data = json.load(f)
                    status["total_indicators"] = len(all_data)
                    status["status"] = "operational"
                except Exception as e:
                    status["checks"]["data_parsing"] = f"❌ 解析失敗: {str(e)}"
                    status["status"] = "data_error"
            else:
                status["checks"]["data_file"] = "❌ 不存在"
                status["data_available"] = False
                status["status"] = "no_data"

            logger.info(f"✅ gov_crawler 狀態: {status['status']}")
            return status

        except Exception as e:
            logger.error(f"❌ 獲取 gov_crawler 狀態失敗: {e}", exc_info=True)
            return {
                "project": "gov_crawler",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "data_source": "gov_crawler"
            }

    logger.info("✅ 已註冊 gov_crawler 數據 API 端點")
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
        logger.info("🌐 訪問地址: http://localhost:8002")
        logger.info("📚 API 文檔: http://localhost:8002/docs")
        logger.info("🔧 功能: 實時儀表板、API 端點、性能監控")
        logger.info("⏹️ 按 Ctrl+C 停止系統")

        # 使用 uvicorn.Server 低階 API - 避免事件循環衝突
        server_config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8002,
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
