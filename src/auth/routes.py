"""
Authentication Routes
FastAPI routes for authentication and authorization
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .core.config import AuthConfig
from .core.security import SecurityManager
from .jwt.manager import JWTManager
from .password.manager import PasswordManager
from .api_keys.manager import APIKeyManager
from .oauth.manager import OAuthManager
from .certificates.manager import CertificateManager
from .middleware.auth import (
    get_current_user,
    get_current_verified_user,
    require_permission,
    require_role,
    require_api_key_scope,
)
from .models.user import User, UserRole, UserPermission
from .models.token import TokenType
from .models.security_event import SecurityEvent, SecurityEventType
from .schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    MFASecret,
    UserSessionInfo,
)
from .schemas.token import TokenPair, TokenRefresh, TokenResponse
from .schemas.api_key import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    APIKeyUpdate,
    APIKeyUsage,
    APIKeyStatistics,
)
from .schemas.oauth import (
    OAuthAuthorizeResponse,
    OAuthCallback,
    OAuthTokenResponse,
    OAuthUserInfo,
    OAuthConnection,
)
from .schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
    CertificateWithKey,
    CertificateVerify,
    CertificateVerifyResponse,
    CSRCreate,
    CSRResponse,
    CertificateRequestResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Global instances (will be initialized in main app)
config: Optional[AuthConfig] = None
security_manager: Optional[SecurityManager] = None
db: Optional[Session] = None
jwt_manager: Optional[JWTManager] = None
password_manager: Optional[PasswordManager] = None
api_key_manager: Optional[APIKeyManager] = None
oauth_manager: Optional[OAuthManager] = None
cert_manager: Optional[CertificateManager] = None


def initialize_auth_components(app_config: AuthConfig, app_security: SecurityManager, app_db: Session):
    """Initialize authentication components (called from main app)"""
    global config, security_manager, db, jwt_manager, password_manager, api_key_manager, oauth_manager, cert_manager
    config = app_config
    security_manager = app_security
    db = app_db
    jwt_manager = JWTManager(config, security_manager, db)
    password_manager = PasswordManager(config, security_manager)
    api_key_manager = APIKeyManager(config, security_manager, db)
    oauth_manager = OAuthManager(config, security_manager, db)
    cert_manager = CertificateManager(config, security_manager, db)


# ========== USER AUTHENTICATION ==========

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, request: Request):
    """Register a new user"""
    if db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Validate password strength
    password_check = password_manager.validate_password_strength(user_data.password)
    if not password_check['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {'; '.join(password_check['feedback'])}"
        )

    # Hash password
    hashed_password = password_manager.hash_password(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.VIEWER.value,
        is_active=True,
        is_verified=False,
    )

    # Set password expiration
    if config.password_expiration_days:
        user.password_expires_at = password_manager.calculate_password_expiry()

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log event
    security_manager.log_security_event(
        'USER_CREATED',
        user_id=str(user.id),
        details={
            'email': user.email,
            'username': user.username
        }
    )

    return user


@router.post("/login", response_model=TokenPair)
async def login(credentials: UserLogin, request: Request):
    """Login with email and password"""
    # Get user
    user = db.query(User).filter_by(email=credentials.email).first()
    if not user:
        security_manager.log_security_event(
            'LOGIN_FAILURE',
            details={'email': credentials.email, 'reason': 'user_not_found'}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if account is locked
    if user.is_account_locked():
        security_manager.log_security_event(
            'LOGIN_BLOCKED_LOCKED',
            user_id=str(user.id),
            details={'email': credentials.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Please try again later."
        )

    # Verify password
    is_valid, needs_rehash = password_manager.verify_password(
        credentials.password,
        user.hashed_password,
        user.id
    )

    if not is_valid:
        # Increment failed attempts
        user.login_attempts += 1
        user.password_failed_attempts += 1

        # Lock account if too many attempts
        if user.password_failed_attempts >= config.max_login_attempts:
            user.lock_account(config.lockout_duration_minutes)
            security_manager.log_security_event(
                'ACCOUNT_LOCKED',
                user_id=str(user.id),
                details={'reason': 'too_many_failed_attempts'}
            )
        else:
            security_manager.log_security_event(
                'LOGIN_FAILURE',
                user_id=str(user.id),
                details={'email': credentials.email, 'attempts': user.login_attempts}
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if password is expired
    if password_manager.is_password_expired(user):
        security_manager.log_security_event(
            'PASSWORD_EXPIRED',
            user_id=str(user.id),
            details={'email': credentials.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password has expired. Please reset your password."
        )

    # Re-hash password if needed
    if needs_rehash:
        new_hash = password_manager.hash_password(credentials.password, user.id)
        user.hashed_password = new_hash

    # Success - reset failed attempts
    user.login_attempts = 0
    user.password_failed_attempts = 0
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.client.host if request.client else None
    user.unlock_account()
    db.commit()

    # Generate tokens
    access_token = jwt_manager.generate_access_token(user)
    refresh_token = jwt_manager.generate_refresh_token(user)

    # Log success
    security_manager.log_security_event(
        'LOGIN_SUCCESS',
        user_id=str(user.id),
        details={
            'email': user.email,
            'last_login': user.last_login.isoformat()
        }
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.jwt_access_token_expire_minutes * 60,
        expires_at=datetime.utcnow() + timedelta(minutes=config.jwt_access_token_expire_minutes)
    )


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token"""
    # Verify refresh token
    claims = jwt_manager.verify_token(token_data.refresh_token, 'refresh')
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user
    user = db.query(User).filter_by(id=claims['user_id']).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Rotate tokens
    rotated = jwt_manager.rotate_refresh_token(token_data.refresh_token)
    if not rotated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

    new_access, new_refresh = rotated

    security_manager.log_security_event(
        'TOKEN_REFRESHED',
        user_id=str(user.id),
        details={'jti': claims.get('jti')}
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=config.jwt_access_token_expire_minutes * 60,
        user_id=user.id,
        email=user.email,
        role=user.role
    )


@router.post("/logout")
async def logout(request: Request):
    """Logout and revoke tokens"""
    if hasattr(request.state, 'user'):
        user = request.state.user
        # Revoke all user tokens
        count = jwt_manager.revoke_all_user_tokens(user.id, reason="User logout")
        security_manager.log_security_event(
            'LOGOUT',
            user_id=str(user.id),
            details={'tokens_revoked': count}
        )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    # Check if email/username is taken
    if user_data.email and user_data.email != current_user.email:
        if db.query(User).filter_by(email=user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    if user_data.username and user_data.username != current_user.username:
        if db.query(User).filter_by(username=user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use"
            )

    # Update fields
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    security_manager.log_security_event(
        'USER_UPDATED',
        user_id=str(current_user.id),
        details={'fields_updated': list(user_data.dict(exclude_unset=True).keys())}
    )

    return current_user


@router.post("/password/change")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    # Verify current password
    is_valid, _ = password_manager.verify_password(
        password_data.current_password,
        current_user.hashed_password,
        current_user.id
    )
    if not is_valid:
        security_manager.log_security_event(
            'PASSWORD_CHANGE_FAILED',
            user_id=str(current_user.id),
            details={'reason': 'invalid_current_password'}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Check password history
    if current_user.password_history:
        password_history = json.loads(current_user.password_history)
        if not password_manager.check_password_history(
            password_data.new_password,
            password_history,
            config.password_max_history
        ):
            security_manager.log_security_event(
                'PASSWORD_CHANGE_FAILED',
                user_id=str(current_user.id),
                details={'reason': 'in_password_history'}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use a password from your password history"
            )

    # Validate new password strength
    password_check = password_manager.validate_password_strength(password_data.new_password)
    if not password_check['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {'; '.join(password_check['feedback'])}"
        )

    # Update password
    new_hash = password_manager.hash_password(password_data.new_password, current_user.id)
    current_user.hashed_password = new_hash
    current_user.password_created_at = datetime.utcnow()

    # Update password history
    current_user.password_history = json.dumps(
        password_manager.update_password_history(current_user, password_data.new_password)
    )

    # Reset expiration if configured
    if config.password_expiration_days:
        current_user.password_expires_at = password_manager.calculate_password_expiry()

    db.commit()

    security_manager.log_security_event(
        'PASSWORD_CHANGED',
        user_id=str(current_user.id)
    )

    return {"message": "Password changed successfully"}


@router.post("/password/reset")
async def request_password_reset(reset_data: PasswordReset):
    """Request password reset"""
    user = db.query(User).filter_by(email=reset_data.email).first()
    if user:
        token = password_manager.create_password_reset_token(user)
        db.commit()
        # In production, send email with token
        # email_service.send_password_reset_email(user.email, token)

        security_manager.log_security_event(
            'PASSWORD_RESET_REQUESTED',
            user_id=str(user.id)
        )

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password/reset/confirm")
async def confirm_password_reset(reset_data: PasswordResetConfirm):
    """Confirm password reset"""
    # Find user with valid reset token
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token,
        User.password_reset_expires > datetime.utcnow(),
        User.password_reset_used == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Validate new password
    password_check = password_manager.validate_password_strength(reset_data.new_password)
    if not password_check['valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too weak: {'; '.join(password_check['feedback'])}"
        )

    # Update password
    new_hash = password_manager.hash_password(reset_data.new_password, user.id)
    user.hashed_password = new_hash
    user.password_created_at = datetime.utcnow()
    user.password_failed_attempts = 0
    user.unlock_account()

    # Use the reset token
    password_manager.use_password_reset_token(reset_data.token, user)

    # Update password history
    user.password_history = json.dumps(
        password_manager.update_password_history(user, reset_data.new_password)
    )

    # Reset expiration
    if config.password_expiration_days:
        user.password_expires_at = password_manager.calculate_password_expiry()

    db.commit()

    security_manager.log_security_event(
        'PASSWORD_RESET_COMPLETED',
        user_id=str(user.id)
    )

    return {"message": "Password reset successfully"}


# ========== API KEY MANAGEMENT ==========

@router.post("/api-keys", response_model=APIKeyWithSecret)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new API key"""
    # Check permissions
    if not current_user.has_permission(UserPermission.API_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    result = api_key_manager.generate_api_key(
        user=current_user,
        name=key_data.name,
        scopes=key_data.scopes,
        expiration_days=key_data.expiration_days,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        ip_whitelist=key_data.ip_whitelist,
        description=key_data.description
    )

    return APIKeyWithSecret(
        **result,
        id=0,  # Will be set by database
        is_active=True,
        is_revoked=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.fromisoformat(result['expires_at']),
        last_used_at=None,
        usage_count=0,
        is_expired=False
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys"""
    if not current_user.has_permission(UserPermission.API_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return api_key_manager.list_user_api_keys(current_user.id)


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get API key details"""
    key = api_key_manager.get_api_key(key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return key.to_dict()


@router.put("/api-keys/{key_id}")
async def update_api_key(
    key_id: str,
    key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update API key"""
    if not api_key_manager.update_api_key(
        key_id=key_id,
        user_id=current_user.id,
        name=key_data.name,
        description=key_data.description,
        scopes=key_data.scopes,
        rate_limit_per_hour=key_data.rate_limit_per_hour,
        expiration_days=key_data.expiration_days,
        ip_whitelist=key_data.ip_whitelist
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return {"message": "API key updated successfully"}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete API key"""
    if not api_key_manager.delete_api_key(key_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return {"message": "API key deleted successfully"}


@router.post("/api-keys/{key_id}/rotate")
async def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Rotate API key"""
    result = api_key_manager.rotate_api_key(key_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return result


@router.get("/api-keys/{key_id}/usage", response_model=List[APIKeyUsage])
async def get_api_key_usage(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get API key usage history"""
    key = api_key_manager.get_api_key(key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return api_key_manager.get_api_key_usage(key_id)


@router.get("/api-keys/{key_id}/statistics", response_model=APIKeyStatistics)
async def get_api_key_statistics(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get API key usage statistics"""
    key = api_key_manager.get_api_key(key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    stats = api_key_manager.get_api_key_statistics(key_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No usage data found"
        )

    return APIKeyStatistics(**stats)


# ========== OAUTH 2.0 / OPENID CONNECT ==========

@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(
    provider: str,
    state: Optional[str] = None,
    scope: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Start OAuth authorization flow"""
    from .models.oauth import OAuthProvider

    try:
        oauth_provider = OAuthProvider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )

    scopes = scope.split(' ') if scope else None

    result = oauth_manager.get_authorization_url(
        provider=oauth_provider,
        state=state,
        scope=scopes,
        redirect_uri=redirect_uri
    )

    return OAuthAuthorizeResponse(**result)


@router.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    request: Request
):
    """Handle OAuth callback"""
    from .models.oauth import OAuthProvider

    try:
        oauth_provider = OAuthProvider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )

    # Exchange code for token
    token_data = oauth_manager.exchange_code_for_token(
        provider=oauth_provider,
        code=callback_data.code,
        state=callback_data.state,
        redirect_uri=str(request.url)
    )

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )

    # Get user info
    user_info = oauth_manager.get_user_info(
        provider=oauth_provider,
        access_token=token_data['access_token']
    )

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info"
        )

    # Handle login
    user = oauth_manager.handle_oauth_login(oauth_provider, user_info)

    # Generate tokens
    access_token = jwt_manager.generate_access_token(user)
    refresh_token = jwt_manager.generate_refresh_token(user)

    return OAuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.jwt_access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        scope=' '.join(oauth_manager._get_default_scopes(oauth_provider))
    )


@router.get("/oauth/connections", response_model=List[OAuthConnection])
async def list_oauth_connections(current_user: User = Depends(get_current_user)):
    """List OAuth connections"""
    return oauth_manager.list_oauth_connections(current_user.id)


@router.delete("/oauth/{provider}/unlink")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Unlink OAuth account"""
    from .models.oauth import OAuthProvider

    try:
        oauth_provider = OAuthProvider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )

    if not oauth_manager.unlink_oauth_account(current_user.id, oauth_provider):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth account not found"
        )

    return {"message": "OAuth account unlinked successfully"}


# ========== CERTIFICATE MANAGEMENT ==========

@router.post("/certificates", response_model=CertificateWithKey)
async def create_certificate(
    cert_data: CertificateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new certificate"""
    if not current_user.has_permission(UserPermission.SYSTEM_CONFIG):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    result = cert_manager.generate_certificate(
        name=cert_data.name,
        subject_cn=cert_data.subject_cn,
        subject_o=cert_data.subject_o,
        subject_ou=cert_data.subject_ou,
        subject_c=cert_data.subject_c,
        subject_st=cert_data.subject_st,
        subject_l=cert_data.subject_l,
        subject_email=cert_data.subject_email,
        san_dns_names=cert_data.san_dns_names,
        san_ip_addresses=cert_data.san_ip_addresses,
        san_emails=cert_data.san_emails,
        algorithm=cert_data.algorithm,
        key_size=cert_data.key_size,
        validity_days=cert_data.validity_days,
        certificate_type=cert_data.certificate_type,
        auto_renew=cert_data.auto_renew
    )

    return CertificateWithKey(
        **result,
        type=cert_data.certificate_type,
        algorithm=cert_data.algorithm,
        key_size=cert_data.key_size,
        is_active=True,
        is_revoked=False,
        not_before=datetime.fromisoformat(result['not_before']),
        not_after=datetime.fromisoformat(result['not_after']),
        sha256_fingerprint=result['sha256_fingerprint'],
        days_until_expiry=0,
        needs_renewal=False,
        created_at=datetime.utcnow()
    )


@router.get("/certificates", response_model=List[CertificateResponse])
async def list_certificates(
    current_user: User = Depends(get_current_user)
):
    """List certificates"""
    if not current_user.has_permission(UserPermission.SYSTEM_CONFIG):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return cert_manager.list_certificates()


@router.post("/certificates/verify", response_model=CertificateVerifyResponse)
async def verify_certificate(
    verify_data: CertificateVerify
):
    """Verify certificate"""
    result = cert_manager.verify_certificate(verify_data.certificate_pem)
    return CertificateVerifyResponse(**result)


@router.post("/csr", response_model=CSRResponse)
async def create_csr(
    csr_data: CSRCreate,
    current_user: User = Depends(get_current_user)
):
    """Create certificate signing request"""
    if not current_user.has_permission(UserPermission.SYSTEM_CONFIG):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    result = cert_manager.create_csr(
        name=csr_data.name,
        subject_cn=csr_data.subject_cn,
        subject_o=csr_data.subject_o,
        subject_ou=csr_data.subject_ou,
        subject_c=csr_data.subject_c,
        subject_st=csr_data.subject_st,
        subject_l=csr_data.subject_l,
        subject_email=csr_data.subject_email,
        san_dns_names=csr_data.san_dns_names,
        san_ip_addresses=csr_data.san_ip_addresses,
        san_emails=csr_data.san_emails,
        algorithm=csr_data.algorithm,
        key_size=csr_data.key_size
    )

    return CSRResponse(**result)
