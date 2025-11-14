"""
Authentication and Authorization System
Phase 5: Data Privacy & Security Implementation

This module provides enterprise-grade security features including:
- JWT Authentication (T106)
- OAuth 2.0 / OpenID Connect (T107)
- Password Security (T108)
- API Key Management (T109)
- Certificate Management (T110)
"""

from .core.config import AuthConfig
from .core.security import SecurityManager
from .jwt.manager import JWTManager
from .password.manager import PasswordManager
from .api_keys.manager import APIKeyManager
from .oauth.manager import OAuthManager
from .certificates.manager import CertificateManager

__all__ = [
    'AuthConfig',
    'SecurityManager',
    'JWTManager',
    'PasswordManager',
    'APIKeyManager',
    'OAuthManager',
    'CertificateManager',
]

__version__ = '5.0.0'
