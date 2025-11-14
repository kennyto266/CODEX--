"""
API Key Schemas
Pydantic schemas for API key management
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from ..models.api_key import APIKeyScope


class APIKeyBase(BaseModel):
    """Base API key schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: List[APIKeyScope]
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=100000)


class APIKeyCreate(APIKeyBase):
    """Schema for creating API key"""
    expiration_days: Optional[int] = Field(None, ge=1, le=365)
    ip_whitelist: Optional[List[str]] = None


class APIKeyResponse(APIKeyBase):
    """Schema for API key response"""
    id: int
    key_id: str
    is_active: bool
    is_revoked: bool
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int
    is_expired: bool

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """Schema for API key with secret (only shown on creation)"""
    secret_key: str


class APIKeyUpdate(BaseModel):
    """Schema for updating API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: Optional[List[APIKeyScope]] = None
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    expiration_days: Optional[int] = Field(None, ge=1, le=365)
    ip_whitelist: Optional[List[str]] = None


class APIKeyUsage(BaseModel):
    """Schema for API key usage"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    ip_address: Optional[str] = None
    response_size: int
    response_time_ms: Optional[int] = None


class APIKeyStatistics(BaseModel):
    """Schema for API key statistics"""
    key_id: str
    total_requests: int
    total_bytes: int
    avg_response_time_ms: int
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None
    top_endpoints: List[dict]
    status_codes: List[dict]
