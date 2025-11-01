"""
Production FastAPI Application with Real-time Trading Integration

Phase 5: Real-time Trading System
"""

import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from datetime import datetime

from src.infrastructure.production_setup import ProductionManager
from src.dashboard.realtime_dashboard import RealtimeDashboard, create_realtime_dashboard_routes
from src.trading.realtime_trading_engine import RealtimeTradingEngine
from src.trading.realtime_risk_manager import RealtimeRiskManager
from src.monitoring.realtime_performance_monitor import RealtimePerformanceMonitor

# Initialize production manager
production_manager = ProductionManager(os.getenv('ENVIRONMENT', 'development'))

# Initialize trading components
trading_engine = RealtimeTradingEngine(
    initial_capital=float(os.getenv('INITIAL_CAPITAL', '1000000'))
)
risk_manager = RealtimeRiskManager(
    max_position_size=float(os.getenv('MAX_POSITION_SIZE', '100000')),
    max_portfolio_heat=float(os.getenv('MAX_PORTFOLIO_HEAT', '500000'))
)
performance_monitor = RealtimePerformanceMonitor()
dashboard = RealtimeDashboard()

# Create FastAPI application
app = FastAPI(
    title="Real-time Trading System - Phase 5",
    description="Complete real-time trading integration with risk management and monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include dashboard routes
dashboard_routes = create_realtime_dashboard_routes(dashboard)
app.include_router(dashboard_routes)

# ==================== Root Endpoint ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路徑處理器 - 返回完整HTML仪表板"""
    try:
        # Load dashboard template from file
        # Using absolute path construction from the application module location
        app_dir = Path(__file__).parent
        template_path = app_dir / "dashboard" / "templates" / "index.html"

        production_manager.logger.debug(f"Looking for template at: {template_path}")
        production_manager.logger.debug(f"Template exists: {template_path.exists()}")

        if template_path.exists():
            content = template_path.read_text(encoding='utf-8')
            production_manager.logger.info(f"Successfully loaded dashboard template ({len(content)} bytes)")
            return content
        else:
            production_manager.logger.warning(f"Template file not found at: {template_path}")
    except Exception as e:
        production_manager.logger.error(f"Failed to load template: {type(e).__name__}: {e}", exc_info=True)

    # Fallback HTML if template not found
    html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CODEX Trading System - Real-time Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.1);
            transition: all 0.3s ease;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body class="min-h-screen text-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
        <header class="mb-8">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent flex items-center">
                        CODEX Trading System
                        <span class="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-3 py-1 rounded-lg text-sm ml-4">Phase 5</span>
                    </h1>
                    <p class="text-gray-400 mt-2">Real-time Trading & Risk Management Platform</p>
                </div>
                <div class="flex items-center space-x-3 glass-card px-4 py-2 rounded-lg">
                    <div class="status-indicator bg-green-500"></div>
                    <span class="text-green-400 font-semibold">OPERATIONAL</span>
                </div>
            </div>
        </header>
        <div class="glass-card p-8 rounded-xl text-center">
            <p class="text-xl text-gray-300 mb-4">Dashboard Template Loading Error</p>
            <p class="text-gray-500">Check <a href="/docs" class="text-blue-400 hover:underline">/docs</a> for API documentation</p>
        </div>
    </div>
</body>
</html>"""
    return html_content

# ==================== Health & Status Endpoints ====================

@app.get("/health")
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "environment": production_manager.config.environment.value,
        "timestamp": datetime.now().isoformat(),
        "active_connections": dashboard.ws_manager.get_active_count(),
        "error_count": production_manager.error_handler.error_count
    }

@app.get("/api/system/status")
async def system_status():
    """获取详细系统状态"""
    return production_manager.get_system_status()

# ==================== Trading Engine Endpoints ====================

@app.get("/api/trading/portfolio")
async def get_portfolio():
    """获取当前投资组合摘要"""
    return trading_engine.get_portfolio_summary()

@app.get("/api/trading/performance")
async def get_performance():
    """获取交易性能指标"""
    return trading_engine.get_performance_metrics()

# ==================== Risk Manager Endpoints ====================

@app.get("/api/risk/summary")
async def get_risk_summary():
    """获取风险管理摘要"""
    return risk_manager.get_risk_summary()

# ==================== Performance Monitor Endpoints ====================

@app.get("/api/performance/summary")
async def get_performance_summary():
    """获取性能监控摘要"""
    return performance_monitor.get_performance_summary()

# ==================== Dashboard Summary ====================

@app.get("/api/dashboard/complete")
async def get_complete_dashboard():
    """获取完整仪表板数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "portfolio": trading_engine.get_portfolio_summary(),
        "performance": performance_monitor.get_performance_summary(),
        "risk": risk_manager.get_risk_summary(),
        "system": production_manager.get_system_status()
    }

# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    production_manager.logger.info("=" * 80)
    production_manager.logger.info("Phase 5: Real-time Trading System - Starting")
    production_manager.logger.info("=" * 80)
    production_manager.logger.info(f"Environment: {production_manager.config.environment.value}")
    production_manager.logger.info(f"Initial Capital: ${trading_engine.initial_capital:,.2f}")
    production_manager.logger.info(f"Max Position Size: ${risk_manager.max_position_size:,.2f}")
    production_manager.logger.info(f"Max Portfolio Heat: ${risk_manager.max_portfolio_heat:,.2f}")
    production_manager.logger.info("=" * 80)

# ==================== Shutdown Event ====================

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    production_manager.logger.info("Shutting down trading system...")
    await production_manager.shutdown()
    production_manager.logger.info("Shutdown complete")

if __name__ == "__main__":
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8001'))

    print("\n" + "=" * 80)
    print("Phase 5: Real-time Trading System")
    print("=" * 80)
    print(f"Starting server at http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    print("=" * 80 + "\n")

    uvicorn.run(
        "src.application:app",
        host=host,
        port=port,
        reload=False,
        access_log=True
    )
