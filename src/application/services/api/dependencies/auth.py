"""
认证和授权依赖注入
提供API密钥验证、用户认证和权限检查功能
"""

import hashlib
from fastapi import Response
import hmac
import time
from typing import Any, Dict, List, Optional, Set

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from src.api.middleware.errors import (
    APIError,
    PermissionDeniedError,
    UnauthorizedError,
)

logger = structlog.get_logger("api.auth")

# 安全方案
security = HTTPBearer(auto_error=False)

# 模拟的API密钥存储（实际应该从环境变量或数据库读取）
API_KEYS = {
    "dev_key_123": {
        "name": "开发环境",
        "permissions": ["read", "write", "backtest"],
        "rate_limit": 1000,  # 每小时
    },
    "admin_key_456": {
        "name": "管理员",
        "permissions": ["read", "write", "backtest", "config", "admin"],
        "rate_limit": 10000,
    },
    "readonly_key_789": {
        "name": "只读用户",
        "permissions": ["read"],
        "rate_limit": 500,
    },
}

# 用户权限枚举
class Permission(BaseModel):
    """权限模型"""
    name: str
    description: str
    level: int = Field(ge=0, le=100)


# 预定义权限
AVAILABLE_PERMISSIONS = {
    "read": Permission(name="read", description="读取权限", level=10),
    "write": Permission(name="write", description="写入权限", level=20),
    "backtest": Permission(name="backtest", description="回测权限", level=30),
    "config": Permission(name="config", description="配置权限", level=40),
    "admin": Permission(name="admin", description="管理员权限", level=100),
}


class User(BaseModel):
    """用户模型"""
    id: str
    name: str
    permissions: List[str]
    api_key: str
    rate_limit: int
    created_at: float
    last_access: Optional[float] = None


class APIKeyData(BaseModel):
    """API密钥数据模型"""
    key: str
    user: User
    rate_limit: int
    permissions: Set[str]


def get_api_key(request: Request) -> Optional[str]:
    """
    从请求中提取API密钥

    支持从以下位置获取API密钥：
    1. HTTP Authorization Bearer 头
    2. X-API-Key 头
    3. 查询参数 api_key

    Args:
        request: FastAPI请求对象

    Returns:
        API密钥字符串或None
    """
    # 方法1: 从 Authorization Bearer 头获取
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    # 方法2: 从 X-API-Key 头获取
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        return api_key_header.strip()

    # 方法3: 从查询参数获取
    api_key_query = request.query_params.get("api_key")
    if api_key_query:
        return api_key_query.strip()

    return None


def require_api_key(request: Request) -> APIKeyData:
    """
    验证API密钥

    Args:
        request: FastAPI请求对象

    Returns:
        验证通过的API密钥数据

    Raises:
        UnauthorizedError: API密钥无效或缺失
        PermissionDeniedError: 权限不足
    """
    api_key = get_api_key(request)

    if not api_key:
        logger.warning("API密钥缺失", client_ip=request.client.host)
        raise UnauthorizedError("Missing API key")

    # 验证API密钥
    if api_key not in API_KEYS:
        logger.warning("无效的API密钥", api_key=api_key[:8] + "...", client_ip=request.client.host)
        raise UnauthorizedError("Invalid API key")

    key_data = API_KEYS[api_key]

    # 创建用户对象
    user = User(
        id=hashlib.md5(api_key.encode()).hexdigest()[:8],
        name=key_data["name"],
        permissions=key_data["permissions"],
        api_key=api_key,
        rate_limit=key_data["rate_limit"],
        created_at=time.time(),
    )

    # 更新最后访问时间
    user.last_access = time.time()

    logger.info(
        "API密钥验证成功",
        user_id=user.id,
        user_name=user.name,
        permissions=user.permissions,
        client_ip=request.client.host,
    )

    return APIKeyData(
        key=api_key,
        user=user,
        rate_limit=user.rate_limit,
        permissions=set(user.permissions),
    )


def get_current_user(request: Request) -> User:
    """
    获取当前认证用户

    Args:
        request: FastAPI请求对象

    Returns:
        当前用户对象

    Raises:
        UnauthorizedError: 未认证
    """
    try:
        api_key_data = require_api_key(request)
        return api_key_data.user
    except APIError as e:
        if isinstance(e, UnauthorizedError):
            raise
        raise UnauthorizedError("Authentication required")


def get_permissions(request: Request) -> Set[str]:
    """
    获取当前用户权限

    Args:
        request: FastAPI请求对象

    Returns:
        用户权限集合

    Raises:
        UnauthorizedError: 未认证
    """
    api_key_data = require_api_key(request)
    return api_key_data.permissions


def has_permission(request: Request, permission: str) -> bool:
    """
    检查当前用户是否具有指定权限

    Args:
        request: FastAPI请求对象
        permission: 权限名称

    Returns:
        是否具有权限
    """
    try:
        permissions = get_permissions(request)
        return permission in permissions
    except UnauthorizedError:
        return False


def require_permission(permission: str):
    """
    依赖注入：要求指定权限

    Args:
        permission: 权限名称

    Returns:
        依赖注入函数

    Raises:
        PermissionDeniedError: 权限不足
    """
    def dependency(request: Request) -> User:
        user = get_current_user(request)

        if permission not in user.permissions:
            logger.warning(
                "权限不足",
                user_id=user.id,
                required_permission=permission,
                user_permissions=user.permissions,
            )
            raise PermissionDeniedError(
                f"Required permission: {permission}"
            )

        return user

    return dependency


def require_admin():
    """
    依赖注入：要求管理员权限

    Returns:
        依赖注入函数

    Raises:
        PermissionDeniedError: 非管理员用户
    """
    return require_permission("admin")


def verify_api_key_signature(
    api_key: str,
    timestamp: str,
    signature: str,
    secret: Optional[str] = None,
) -> bool:
    """
    验证API密钥签名（用于更安全的API调用）

    Args:
        api_key: API密钥
        timestamp: 时间戳
        signature: 请求签名
        secret: 密钥secret（可选）

    Returns:
        签名是否有效
    """
    # 构建待签名字符串
    message = f"{api_key}:{timestamp}"

    # 如果没有提供secret，使用默认secret（实际应该从安全存储获取）
    if not secret:
        secret = "default_secret_change_in_production"

    # 计算签名
    expected_signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    # 验证签名
    return hmac.compare_digest(signature, expected_signature)


def create_api_key(
    name: str,
    permissions: List[str],
    rate_limit: int = 1000,
) -> Dict[str, Any]:
    """
    创建新的API密钥

    Args:
        name: 密钥名称
        permissions: 权限列表
        rate_limit: 频率限制

    Returns:
        新创建的API密钥信息
    """
    import secrets

    # 生成随机API密钥
    api_key = secrets.token_urlsafe(32)

    # 验证权限
    valid_permissions = set(permissions) & set(AVAILABLE_PERMISSIONS.keys())
    if valid_permissions != set(permissions):
        invalid = set(permissions) - set(AVAILABLE_PERMISSIONS.keys())
        raise ValueError(f"Invalid permissions: {invalid}")

    # 存储密钥（实际应该保存到数据库）
    API_KEYS[api_key] = {
        "name": name,
        "permissions": list(valid_permissions),
        "rate_limit": rate_limit,
    }

    logger.info(
        "创建API密钥",
        key_name=name,
        permissions=list(valid_permissions),
        rate_limit=rate_limit,
    )

    return {
        "api_key": api_key,
        "name": name,
        "permissions": list(valid_permissions),
        "rate_limit": rate_limit,
    }


def revoke_api_key(api_key: str) -> bool:
    """
    撤销API密钥

    Args:
        api_key: 要撤销的API密钥

    Returns:
        是否成功撤销
    """
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        logger.info("撤销API密钥", api_key=api_key[:8] + "...")
        return True
    return False


# 安全头设置
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}


def add_security_headers(response: "Response") -> None:
    """
    为响应添加安全头

    Args:
        response: FastAPI响应对象
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
