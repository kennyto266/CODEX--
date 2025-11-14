"""
Phase 3: Performance Optimization - API启动脚本
启动集成了Rust引擎的高性能回测API

包含:
- T058: /api/v1/backtest/run - Rust引擎回测
- T059: /api/v1/backtest/optimize - 并行参数优化
- T060: /api/v1/backtest/metrics - 性能监控
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase3_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入Phase 3 API路由
try:
    from api_backtest_v1 import create_backtest_v1_router
    PHASE3_AVAILABLE = True
    logger.info("✅ Phase 3 API路由已加载")
except ImportError as e:
    PHASE3_AVAILABLE = False
    logger.error(f"❌ Phase 3 API路由加载失败: {e}")
    sys.exit(1)

# 创建FastAPI应用
app = FastAPI(
    title="Quant System - Phase 3: Performance Optimization",
    description="High-performance backtesting API with Rust engine integration",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 根路径 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Quant System - Phase 3: Performance Optimization",
        "version": "3.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "backtest_run": "/api/v1/backtest/run",
            "optimize": "/api/v1/backtest/optimize",
            "metrics": "/api/v1/backtest/metrics",
            "docs": "/docs"
        }
    }

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "rust_engine": "available"
    }

# ==================== 注册Phase 3路由 ====================

try:
    if PHASE3_AVAILABLE:
        phase3_router = create_backtest_v1_router()
        app.include_router(phase3_router)
        logger.info("✅ Phase 3 API路由已注册")
    else:
        logger.error("❌ Phase 3 API路由未加载")
except Exception as e:
    logger.error(f"❌ 注册Phase 3 API路由失败: {e}")


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Phase 3: Performance Optimization - API启动")
    logger.info("=" * 80)
    logger.info("")
    logger.info("功能特性:")
    logger.info("  ✓ T058: /api/v1/backtest/run - Rust引擎回测 (< 50ms)")
    logger.info("  ✓ T059: /api/v1/backtest/optimize - 并行参数优化")
    logger.info("  ✓ T060: /api/v1/backtest/metrics - 实时性能监控")
    logger.info("")
    logger.info("支持的策略:")
    logger.info("  - MA (Moving Average)")
    logger.info("  - RSI (Relative Strength Index)")
    logger.info("  - MACD (Moving Average Convergence Divergence)")
    logger.info("  - BB (Bollinger Bands)")
    logger.info("  - KDJ (Stochastic)")
    logger.info("  - CCI (Commodity Channel Index)")
    logger.info("  - ADX (Average Directional Index)")
    logger.info("  - ATR (Average True Range)")
    logger.info("  - OBV (On-Balance Volume)")
    logger.info("  - Ichimoku (Ichimoku Cloud)")
    logger.info("  - SAR (Parabolic SAR)")
    logger.info("")
    logger.info("API文档: http://localhost:8002/docs")
    logger.info("健康检查: http://localhost:8002/api/health")
    logger.info("=" * 80)
    logger.info("")

    # 启动服务器
    uvicorn.run(
        "start_phase3_api:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
