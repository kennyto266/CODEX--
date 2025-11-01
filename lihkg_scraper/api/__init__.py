"""
LIHKG API 模塊
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 創建 FastAPI 應用
app = FastAPI(
    title="LIHKG 情緒分析 API",
    description="LIHKG 散戶情緒分析與股票討論數據 API",
    version="1.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 導入路由
from . import routes

app.include_router(routes.router, prefix="/api/lihkg", tags=["LIHKG"])

@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "message": "LIHKG 情緒分析 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy"}
