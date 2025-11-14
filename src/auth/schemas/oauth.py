"""
OAuth Schemas
Pydantic schemas for OAuth 2.0 / OpenID Connect
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from ..models.oauth import OAuthProvider


class OAuthAuthorize(BaseModel):
    """Schema for OAuth authorization request"""
    provider: OAuthProvider
    state: str
    scope: Optional[str] = None
    redirect_uri: Optional[str] = None


class OAuthAuthorizeResponse(BaseModel):
    """Schema for OAuth authorization response"""
    authorization_url: str
    state: str


class OAuthCallback(BaseModel):
    """Schema for OAuth callback"""
    code: str
    state: str


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response"""
    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class OAuthUserInfo(BaseModel):
    """Schema for OAuth user information"""
    provider: str
    provider_user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    picture: Optional[str] = None
    verified: bool = False


class OAuthConnection(BaseModel):
    """Schema for OAuth connection"""
    provider: str
    provider_username: Optional[str] = None
    provider_email: Optional[str] = None
    connected_at: datetime
    has_token: bool
    token_expires_at: Optional[datetime] = None


class OAuthProviderConfig(BaseModel):
    """Schema for OAuth provider configuration"""
    provider: OAuthProvider
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None
    is_active: bool = True
