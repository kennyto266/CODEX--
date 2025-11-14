"""
API路由模块
港股量化交易系统 - RESTful API端点
"""

from fastapi import APIRouter

# 创建v1 API路由组
v1_bp = APIRouter()

# 注册各个功能模块的路由
# 注意：这些路由会在后续任务中实现
try:
    from src.application.services.api.routes import backtest  # noqa: F401
    v1_bp.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
except ImportError as e:
    pass

try:
    from src.application.services.api.routes import config  # noqa: F401
    v1_bp.include_router(config.router, prefix="/config", tags=["config"])
except ImportError:
    pass

try:
    from src.application.services.api.routes import layout  # noqa: F401
    v1_bp.include_router(layout.router, prefix="/layout", tags=["layout"])
except ImportError:
    pass

# 参数优化路由
try:
    from src.application.services.api.routes import optimization  # noqa: F401
    v1_bp.include_router(optimization.router, prefix="/backtest", tags=["optimization"])
except ImportError:
    pass

# 10大牛熊證成交路由
try:
    from src.application.services.api.routes import top_cbbc  # noqa: F401
    v1_bp.include_router(top_cbbc.router)
    print("SUCCESS: Top CBBC router registered")
except ImportError as e:
    print(f"ERROR: Top CBBC router import failed: {e}")
except Exception as e:
    print(f"ERROR: Top CBBC router registration failed: {e}")

# 股票数据路由
try:
    from src.application.services.api.routes import stock  # noqa: F401
    v1_bp.include_router(stock.router)
    print("SUCCESS: Stock router registered")
except ImportError as e:
    print(f"ERROR: Stock router import failed: {e}")
except Exception as e:
    print(f"ERROR: Stock router registration failed: {e}")

# WebSocket路由 - 暂时禁用
# try:
#     from src.application.services.api import websocket  # noqa: F401
#     v1_bp.include_router(websocket.websocket_router, prefix="/websocket", tags=["WebSocket"])
# except ImportError:
#     pass

# 其他预留路由
# v1_bp.include_router(data.router, prefix="/data", tags=["数据源"])
# v1_bp.include_router(strategies.router, prefix="/strategies", tags=["策略分析"])
# v1_bp.include_router(portfolio.router, prefix="/portfolio", tags=["投资组合"])
# v1_bp.include_router(risk.router, prefix="/risk", tags=["风险管理"])
# v1_bp.include_router(monitoring.router, prefix="/monitoring", tags=["性能监控"])
# v1_bp.include_router(agents.router, prefix="/agents", tags=["智能体管理"])
