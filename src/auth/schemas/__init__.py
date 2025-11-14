"""
Authentication Schemas
Pydantic schemas for API validation
"""

from .user import *
from .token import *
from .api_key import *
from .oauth import *
from .certificate import *

__all__ = [
    # User schemas
    'UserCreate',
    'UserLogin',
    'UserResponse',
    'UserUpdate',
    'PasswordChange',
    'PasswordReset',
    'PasswordResetConfirm',
    'MFASetup',
    'MFASecret',
    'MFABackupCodes',

    # Token schemas
    'TokenPair',
    'TokenRefresh',
    'TokenResponse',

    # API Key schemas
    'APIKeyCreate',
    'APIKeyResponse',
    'APIKeyUpdate',
    'APIKeyUsage',

    # OAuth schemas
    'OAuthAuthorize',
    'OAuthCallback',

    # Certificate schemas
    'CertificateCreate',
    'CertificateResponse',
    'CertificateVerify',
    'CSRCreate',
    'CSRResponse',
]
