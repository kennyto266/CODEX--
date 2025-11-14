"""
健康检查端点
提供系统健康状态和基本信息
"""

import time
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger("api.health")

router = APIRouter()


class HealthStatus(BaseModel):
    """健康状态响应模型"""
    status: str
    timestamp: float
    uptime_seconds: float
    version: str
    service: str
    checks: Dict[str, Any]


class ServiceInfo(BaseModel):
    """服务信息模型"""
    name: str
    version: str
    status: str
    description: str


# 存储应用启动时间
start_time = time.time()


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="系统健康检查",
    description="""
    返回系统的健康状态信息，包括：
    - 服务状态
    - 运行时长
    - 版本信息
    - 各项服务检查结果
    """,
)
async def health_check() -> HealthStatus:
    """
    获取系统健康状态

    返回系统当前状态、运行时间和基础信息
    """
    try:
        # 检查各项服务状态
        checks = await perform_health_checks()

        # 检查是否有关键服务不可用
        critical_failed = any(
            check.get("critical", False) and check.get("status") == "error"
            for check in checks.values()
        )

        status = "healthy" if not critical_failed else "unhealthy"

        logger.info("健康检查", status=status, checks=checks)

        return HealthStatus(
            status=status,
            timestamp=time.time(),
            uptime_seconds=time.time() - start_time,
            version="1.0.0",
            service="港股量化交易系统 API",
            checks=checks,
        )

    except Exception as e:
        logger.error("健康检查失败", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")


@router.get(
    "/health/ready",
    summary="就绪检查",
    description="检查服务是否已准备好接收请求",
)
async def readiness_check() -> Dict[str, Any]:
    """
    检查服务就绪状态

    用于Kubernetes等容器编排系统的就绪探针
    """
    try:
        # 这里可以检查数据库连接、缓存等关键资源
        # db_status = await check_database()
        # cache_status = await check_cache()

        # 目前所有检查都通过
        return {
            "status": "ready",
            "timestamp": time.time(),
            "checks": {
                "database": {"status": "ok", "critical": True},
                "cache": {"status": "ok", "critical": False},
            },
        }
    except Exception as e:
        logger.error("就绪检查失败", error=str(e))
        return {
            "status": "not_ready",
            "timestamp": time.time(),
            "error": str(e),
        }


@router.get(
    "/health/live",
    summary="存活检查",
    description="简单的存活检查，不依赖外部资源",
)
async def liveness_check() -> Dict[str, str]:
    """
    简单的存活检查

    用于Kubernetes等容器编排系统的存活探针
    """
    return {
        "status": "alive",
        "timestamp": str(time.time()),
    }


@router.get(
    "/info",
    response_model=ServiceInfo,
    summary="服务信息",
    description="返回服务的基本信息和版本",
)
async def service_info() -> ServiceInfo:
    """
    获取服务信息
    """
    return ServiceInfo(
        name="港股量化交易系统 API",
        version="1.0.0",
        status="running",
        description="基于多智能体协作的港股量化交易系统",
    )


async def perform_health_checks() -> Dict[str, Any]:
    """
    执行各项健康检查

    Returns:
        Dict: 各项检查的结果
    """
    checks = {
        "api": {
            "status": "ok",
            "message": "API服务正常",
            "critical": True,
        },
        "memory": await check_memory(),
        "disk": await check_disk(),
    }

    # TODO: 添加更多健康检查
    # - 数据库连接检查
    # - 外部API连接检查
    # - 消息队列检查
    # - 缓存检查

    return checks


async def check_memory() -> Dict[str, Any]:
    """检查内存使用情况"""
    import psutil

    try:
        memory = psutil.virtual_memory()
        return {
            "status": "ok" if memory.percent < 90 else "warning",
            "usage_percent": memory.percent,
            "available_gb": round(memory.available / (1024**3), 2),
            "critical": memory.percent > 95,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "critical": True,
        }


async def check_disk() -> Dict[str, Any]:
    """检查磁盘使用情况"""
    import psutil

    try:
        disk = psutil.disk_usage("/")
        return {
            "status": "ok" if disk.percent < 90 else "warning",
            "usage_percent": round(disk.percent, 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "critical": disk.percent > 95,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "critical": True,
        }
