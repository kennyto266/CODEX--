"""
Authentication Middleware
FastAPI middleware for authentication and authorization
"""

import json
from typing import Optional, Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..jwt.manager import JWTManager
from ..api_keys.manager import APIKeyManager
from ..models.user import User, UserPermission

logger = logging.getLogger("hk_quant_system.auth.middleware")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for authentication
    Handles JWT token and API key authentication
    """

    def __init__(self, app, config: AuthConfig, security: SecurityManager, db_session):
        """
        Initialize middleware

        Args:
            app: FastAPI application
            config: Authentication configuration
            security: Security manager instance
            db_session: Database session
        """
        super().__init__(app)
        self.config = config
        self.security = security
        self.db = db_session
        self.jwt_manager = JWTManager(config, security, db_session)
        self.api_key_manager = APIKeyManager(config, security, db_session)
        self.scheme = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request"""
        # Skip auth for certain paths
        if self._should_skip_auth(request):
            return await call_next(request)

        # Get authentication method
        auth_result = await self._authenticate(request)

        if auth_result is None:
            if self._requires_auth(request):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "message": "Authentication required",
                        "code": "AUTH_REQUIRED"
                    }
                )
        else:
            # Store user info in request state
            request.state.user = auth_result.get('user')
            request.state.auth_method = auth_result.get('method')
            request.state.auth_scopes = auth_result.get('scopes', [])

        response = await call_next(request)
        return response

    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this path"""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/health",
            "/auth/login",
            "/auth/register",
            "/auth/token/refresh",
            "/auth/token/reset",
            "/auth/verify",
            "/static/",
        ]

        path = request.url.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _requires_auth(self, request: Request) -> bool:
        """Check if endpoint requires authentication"""
        # All API endpoints under /api require auth (except those in skip list)
        return request.url.path.startswith("/api/") or request.url.path.startswith("/auth/")

    async def _authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate request using JWT or API key

        Args:
            request: FastAPI request

        Returns:
            Authentication result or None
        """
        # Try API key authentication
        api_key = self._extract_api_key(request)
        if api_key:
            result = await self._authenticate_api_key(api_key, request)
            if result:
                return result

        # Try JWT token authentication
        credentials = await self._extract_jwt_token(request)
        if credentials:
            result = await self._authenticate_jwt(credentials, request)
            if result:
                return result

        return None

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("ApiKey "):
            return auth_header[7:]  # Remove "ApiKey " prefix

        # Check X-API-Key header
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return api_key_header

        # Check query parameter (not recommended for production)
        api_key_query = request.query_params.get("api_key")
        if api_key_query:
            return api_key_query

        return None

    async def _extract_jwt_token(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Extract JWT token from request"""
        credentials = await self.scheme(request)
        return credentials

    async def _authenticate_api_key(self, api_key: str, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using API key"""
        try:
            api_key_obj = self.api_key_manager.validate_api_key(api_key)
            if not api_key_obj:
                # Log failed authentication
                self.security.log_security_event(
                    'API_KEY_INVALID',
                    details={
                        'path': request.url.path,
                        'method': request.method,
                        'ip': request.client.host if request.client else None
                    }
                )
                return None

            # Check IP whitelist
            client_ip = request.client.host if request.client else None
            if client_ip and not self.api_key_manager.check_ip_whitelist(api_key_obj, client_ip):
                self.security.log_security_event(
                    'API_KEY_IP_REJECTED',
                    user_id=str(api_key_obj.user_id),
                    details={
                        'key_id': api_key_obj.key_id,
                        'ip': client_ip
                    }
                )
                return None

            # Log successful authentication
            self.security.log_security_event(
                'API_KEY_AUTHENTICATED',
                user_id=str(api_key_obj.user_id),
                details={
                    'key_id': api_key_obj.key_id,
                    'path': request.url.path
                }
            )

            return {
                'user': api_key_obj.user,
                'method': 'api_key',
                'key_id': api_key_obj.key_id,
                'scopes': [s.value for s in api_key_obj.scopes]
            }

        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return None

    async def _authenticate_jwt(self, credentials: HTTPAuthorizationCredentials, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using JWT token"""
        try:
            # Verify token
            claims = self.jwt_manager.verify_token(credentials.credentials, 'access')
            if not claims:
                return None

            # Get user
            user = self.db.query(User).filter_by(id=claims['user_id']).first()
            if not user or not user.is_active:
                return None

            # Check if account is locked
            if user.is_account_locked():
                self.security.log_security_event(
                    'LOGIN_BLOCKED_LOCKED',
                    user_id=str(user.id),
                    details={'path': request.url.path}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked"
                )

            # Log successful authentication
            self.security.log_security_event(
                'JWT_AUTHENTICATED',
                user_id=str(user.id),
                details={
                    'path': request.url.path,
                    'jti': claims.get('jti')
                }
            )

            return {
                'user': user,
                'method': 'jwt',
                'claims': claims,
                'scopes': claims.get('scope', '').split(' ') if claims.get('scope') else []
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return None


# Dependency for getting current user
async def get_current_user(request: Request) -> User:
    """Get current authenticated user"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user


# Dependency for getting current user with verification
async def get_current_verified_user(request: Request) -> User:
    """Get current authenticated and verified user"""
    user = await get_current_user(request)
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified"
        )
    return user


# Dependency for checking permissions
def require_permission(permission: UserPermission):
    """Check if user has required permission"""
    async def dependency(request: Request):
        user = await get_current_user(request)
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return user
    return dependency


# Dependency for checking role
def require_role(*allowed_roles: str):
    """Check if user has one of the allowed roles"""
    async def dependency(request: Request):
        user = await get_current_user(request)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of {', '.join(allowed_roles)}"
            )
        return user
    return dependency


# Dependency for checking API key scope
def require_api_key_scope(*required_scopes: str):
    """Check if API key has required scopes"""
    async def dependency(request: Request):
        if not hasattr(request.state, 'auth_method'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key authentication required"
            )

        if request.state.auth_method != 'api_key':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key authentication required"
            )

        if not hasattr(request.state, 'auth_scopes'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No scopes available"
            )

        user_scopes = request.state.auth_scopes
        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Scope required: {scope}"
                )

        return request.state.user
    return dependency
