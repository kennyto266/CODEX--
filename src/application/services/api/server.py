"""
FastAPI Application Server
港股量化交易系统 - API服务器主入口
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog.stdlib import add_log_level

from src.application.services.api.logging import setup_logging
from src.application.services.api.middleware.errors import setup_error_handlers
from src.application.services.api.routes import health, v1_bp

# WebSocket后台任务（可选）
try:
    from src.application.services.api.websocket import start_background_tasks
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    start_background_tasks = None

# 设置结构化日志
setup_logging()
logger = structlog.get_logger("api.server")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """
    应用生命周期管理
    启动和关闭时的初始化和清理工作
    """
    # 启动时的初始化
    logger.info("API服务器启动中...")
    start_time = time.time()

    # 初始化数据库连接、缓存等资源
    await initialize_services()

    # 启动WebSocket后台任务（如果可用）
    if HAS_WEBSOCKET and start_background_tasks:
        background_tasks = await start_background_tasks()
        logger.info("WebSocket后台任务已启动", task_count=len(background_tasks))
    else:
        logger.info("WebSocket后台任务未启用")

    # 应用启动完成
    startup_time = time.time() - start_time
    logger.info("API服务器启动完成", startup_time_ms=startup_time * 1000)

    yield

    # 关闭时的清理工作
    logger.info("API服务器关闭中...")
    await cleanup_services()
    logger.info("API服务器已关闭")


async def initialize_services() -> None:
    """初始化服务资源"""
    # TODO: 在这里初始化数据库、缓存、消息队列等服务
    # 例如：
    # - 数据库连接池
    # - Redis缓存
    # - 消息队列
    # - 外部API连接
    pass


async def cleanup_services() -> None:
    """清理服务资源"""
    # TODO: 关闭所有服务连接
    pass


def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用实例

    Returns:
        FastAPI: 配置完成的FastAPI应用
    """
    # 创建应用实例，使用OpenAPI文档
    app = FastAPI(
        title="港股量化交易系统 API",
        description="""
        基于多智能体协作的港股量化交易系统

        ## 功能模块

        * **回测引擎** - 策略回测和优化
        * **数据源** - 实时和历史数据获取
        * **策略分析** - 量化策略研究和分析
        * **风险管理** - 投资组合风险控制
        * **性能监控** - 实时性能指标
        * **WebSocket** - 实时数据推送和更新
        """,
        version="1.0.0",
        contact={
            "name": "港股量化交易系统",
            "url": "https://github.com/codex-quant/hk-quant-system",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Vue.js开发服务器
            "http://localhost:8001",  # 后台服务
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 设置请求日志中间件
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """记录所有HTTP请求"""
        start_time = time.time()

        # 生成请求ID用于追踪
        request_id = request.headers.get("X-Request-ID", "unknown")

        # 记录请求开始
        logger.info(
            "请求开始",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
        )

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求结束
        logger.info(
            "请求完成",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=process_time * 1000,
        )

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response

    # 设置安全头中间件
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        """添加安全响应头"""
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

    # 注册错误处理中间件
    setup_error_handlers(app)

    # 注册API路由
    app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
    app.include_router(v1_bp, prefix="/api/v1")

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("启动API服务器", host="0.0.0.0", port=8001)
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None,  # 使用structlog
    )
