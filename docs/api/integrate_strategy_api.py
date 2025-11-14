"""
Week 2 Day 5: 完整API集成脚本
将strategy_api_complete.py集成到主系统
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "dashboard"))

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# 设置编码
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 创建FastAPI应用
app = FastAPI(
    title="策略框架API",
    description="基于阿程项目的港股量化交易策略API",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入完整策略API路由
try:
    from src.dashboard.api_strategies_complete import router as strategy_router
    app.include_router(strategy_router)
    print("[OK] 完整策略API路由已集成")
except Exception as e:
    print(f"[ERROR] 策略API路由集成失败: {e}")
    # 创建基础路由
    router = APIRouter(prefix="/api/strategies", tags=["strategies"])

    @router.get("/health")
    async def health_check():
        return {
            "status": "partial",
            "message": "Strategy API not fully integrated",
            "error": str(e)
        }

    app.include_router(router)

# 添加其他现有路由（如果需要）
@app.get("/")
async def root():
    return {
        "message": "策略框架API系统",
        "version": "2.0.0",
        "endpoints": {
            "health": "/api/strategies/health",
            "run_strategy": "/api/strategies/run",
            "optimize": "/api/strategies/optimize",
            "compare": "/api/strategies/compare",
            "list": "/api/strategies/list"
        }
    }

@app.get("/api/health")
async def api_health():
    """全局健康检查"""
    return {
        "status": "healthy",
        "service": "策略框架API",
        "version": "2.0.0",
        "features": [
            "策略运行",
            "参数优化",
            "策略比较",
            "性能指标计算"
        ]
    }

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("策略框架API服务器启动")
    print("="*60)
    print("\nAPI文档: http://localhost:8001/docs")
    print("健康检查: http://localhost:8001/api/health")
    print("\n主要端点:")
    print("  POST /api/strategies/run - 运行策略")
    print("  POST /api/strategies/optimize - 参数优化")
    print("  POST /api/strategies/compare - 策略比较")
    print("  GET /api/strategies/list - 策略列表")
    print("\n" + "="*60)

    uvicorn.run(app, host="0.0.0.0", port=8001)
