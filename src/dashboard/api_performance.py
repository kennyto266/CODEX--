#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CODEX性能优化API路由
集成API缓存、性能监控和优化功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import time
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# 导入优化器和缓存
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from simple_performance_optimizer import SimplePerformanceOptimizer
    from api_cache import api_cache, get_cache_stats, clear_cache
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Performance modules not available: {e}")
    PERFORMANCE_AVAILABLE = False

router = APIRouter(prefix="/performance", tags=["performance"])

class PerformanceAPIManager:
    """性能API管理器"""

    def __init__(self):
        self.optimizer = SimplePerformanceOptimizer() if PERFORMANCE_AVAILABLE else None
        self.last_optimization = None
        self.cache_stats = {"cache_size": 0, "hit_rate": 0}

    async def run_optimization(self) -> Dict[str, Any]:
        """运行性能优化"""
        if not self.optimizer:
            return {"error": "Performance optimizer not available"}

        try:
            # 同步运行优化器
            loop = asyncio.get_event_loop()
            metrics = await loop.run_in_executor(None, self.optimizer.get_basic_metrics)
            mem_opt = await loop.run_in_executor(None, self.optimizer.optimize_memory)
            db_opt = await loop.run_in_executor(None, self.optimizer.optimize_database)
            cache_opt = await loop.run_in_executor(None, self.optimizer.clear_cache)

            self.last_optimization = datetime.now()

            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "optimizations": {
                    "memory": mem_opt,
                    "database": db_opt,
                    "cache": cache_opt
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not PERFORMANCE_AVAILABLE:
            return {"error": "Cache not available"}

        try:
            return get_cache_stats()
        except Exception as e:
            return {"error": str(e)}

    async def clear_api_cache(self) -> Dict[str, Any]:
        """清空API缓存"""
        if not PERFORMANCE_AVAILABLE:
            return {"error": "Cache not available"}

        try:
            clear_cache()
            return {"success": True, "message": "Cache cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# 全局性能管理器
perf_manager = PerformanceAPIManager()

@router.get("/status")
async def get_performance_status():
    """获取性能状态"""
    return {
        "status": "active",
        "optimizer_available": PERFORMANCE_AVAILABLE,
        "last_optimization": perf_manager.last_optimization.isoformat() if perf_manager.last_optimization else None,
        "cache_stats": perf_manager.get_cache_statistics(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/optimize")
async def optimize_system(background_tasks: BackgroundTasks):
    """运行系统优化"""
    result = await perf_manager.run_optimization()
    return result

@router.get("/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    if not perf_manager.optimizer:
        raise HTTPException(status_code=503, detail="Performance optimizer not available")

    try:
        metrics = perf_manager.optimizer.get_basic_metrics()
        cache_stats = perf_manager.get_cache_statistics()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": metrics,
            "cache_statistics": cache_stats,
            "optimization_status": "available" if perf_manager.last_optimization else "never_run"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    stats = perf_manager.get_cache_statistics()
    return stats

@router.delete("/cache")
async def clear_cache_endpoint():
    """清空缓存"""
    result = await perf_manager.clear_api_cache()
    if result.get("success"):
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))

@router.get("/report")
async def generate_performance_report():
    """生成性能报告"""
    if not perf_manager.optimizer:
        raise HTTPException(status_code=503, detail="Performance optimizer not available")

    try:
        metrics = perf_manager.optimizer.get_basic_metrics()
        cache_stats = perf_manager.get_cache_statistics()

        report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "performance_summary",
            "system_metrics": metrics,
            "cache_statistics": cache_stats,
            "recommendations": perf_manager.optimizer.generate_recommendations(metrics) if metrics else []
        }

        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize/memory")
async def optimize_memory():
    """仅优化内存"""
    if not perf_manager.optimizer:
        raise HTTPException(status_code=503, detail="Performance optimizer not available")

    try:
        result = perf_manager.optimizer.optimize_memory()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize/database")
async def optimize_database():
    """仅优化数据库"""
    if not perf_manager.optimizer:
        raise HTTPException(status_code=503, detail="Performance optimizer not available")

    try:
        result = perf_manager.optimizer.optimize_database()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_performance_router():
    """创建性能优化路由"""
    return router
