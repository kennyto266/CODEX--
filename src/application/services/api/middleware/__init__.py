"""
API中间件模块
提供错误处理、认证、安全等功能
"""

from .errors import (
    APIError,
    ValidationAPIError,
    NotFoundError,
    UnauthorizedError,
    PermissionDeniedError,
    RateLimitError,
    ExternalServiceError,
    setup_error_handlers,
)

__all__ = [
    "APIError",
    "ValidationAPIError",
    "NotFoundError",
    "UnauthorizedError",
    "PermissionDeniedError",
    "RateLimitError",
    "ExternalServiceError",
    "setup_error_handlers",
]
