"""
Token Schemas
Pydantic schemas for JWT token handling
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    """Base token schema"""
    access_token: str
    token_type: str = "bearer"


class TokenPair(TokenBase):
    """Schema for token pair (access + refresh)"""
    refresh_token: str
    expires_in: int = Field(..., description="Access token expiration in seconds")
    expires_at: datetime


class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None
    user_id: int
    email: str
    role: str


class TokenClaims(BaseModel):
    """Schema for JWT token claims"""
    iss: str
    sub: str
    aud: str
    exp: int
    iat: int
    jti: str
    token_type: str
    user_id: int
    email: str
    username: str
    role: str
    scope: Optional[str] = None


class TokenBlacklistEntry(BaseModel):
    """Schema for token blacklist entry"""
    jti: str
    user_id: int
    token_type: str
    reason: str
    revoked_at: datetime
    expires_at: datetime
