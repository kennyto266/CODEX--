"""
错误处理中间件
统一处理API异常和错误响应
"""

import time
import traceback
from typing import Any, Dict, Optional

import structlog
from pydantic import BaseModel
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger("api.middleware.errors")


class APIError(Exception):
    """自定义API异常基类"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationAPIError(APIError):
    """验证错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class NotFoundError(APIError):
    """资源未找到错误"""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} '{resource_id}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id},
        )


class UnauthorizedError(APIError):
    """未授权错误"""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class PermissionDeniedError(APIError):
    """权限不足错误"""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            status_code=403,
        )


class RateLimitError(APIError):
    """频率限制错误"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class ExternalServiceError(APIError):
    """外部服务错误"""

    def __init__(self, service: str, original_error: Exception):
        super().__init__(
            message=f"External service '{service}' error: {str(original_error)}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={
                "service": service,
                "original_error": str(original_error),
            },
        )


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: bool = True
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: float


def setup_error_handlers(app: FastAPI) -> None:
    """
    为FastAPI应用注册全局错误处理程序

    Args:
        app: FastAPI应用实例
    """
    # 通用异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """处理所有未捕获的异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        # 记录异常
        logger.error(
            "未捕获的异常",
            request_id=request_id,
            url=str(request.url),
            method=request.method,
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback=traceback.format_exc(),
        )

        # 根据异常类型返回不同响应
        if isinstance(exc, APIError):
            return create_error_response(
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
            )
        elif isinstance(exc, StarletteHTTPException):
            return create_error_response(
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                message=str(exc.detail),
                request_id=request_id,
            )
        elif isinstance(exc, ValidationError):
            return create_error_response(
                status_code=422,
                error_code="VALIDATION_ERROR",
                message="数据验证失败",
                details={"validation_errors": exc.errors()},
                request_id=request_id,
            )
        else:
            # 未知异常，返回500错误
            return create_error_response(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="服务器内部错误",
                request_id=request_id,
            )

    # HTTP异常处理
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """处理HTTP异常"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.warning(
            "HTTP异常",
            request_id=request_id,
            url=str(request.url),
            status_code=exc.status_code,
            detail=str(exc.detail),
        )

        return create_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id,
        )

    # 验证错误处理
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """处理Pydantic验证错误"""
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.warning(
            "数据验证错误",
            request_id=request_id,
            url=str(request.url),
            validation_errors=exc.errors(),
        )

        return create_error_response(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="请求数据验证失败",
            details={"validation_errors": exc.errors()},
            request_id=request_id,
        )

    logger.info("错误处理中间件已注册")


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    创建标准错误响应

    Args:
        status_code: HTTP状态码
        error_code: 错误代码
        message: 错误消息
        details: 错误详情
        request_id: 请求ID

    Returns:
        JSONResponse: 错误响应
    """
    error_response = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=time.time(),
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
    )


def log_error(
    level: str,
    message: str,
    request: Request,
    **kwargs,
) -> None:
    """
    记录错误日志

    Args:
        level: 日志级别 (debug, info, warning, error, critical)
        message: 错误消息
        request: FastAPI请求对象
        **kwargs: 其他日志字段
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else "unknown",
        **kwargs,
    }

    log_func = getattr(logger, level, logger.error)
    log_func(message, **log_data)
