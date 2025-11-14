"""
Authentication Core Configuration
Enterprise-grade security configuration with environment variable support
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from datetime import timedelta


class AuthConfig(BaseSettings):
    """Centralized authentication configuration"""

    # JWT Configuration (T106)
    jwt_secret_key: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR",
        description="Secret key for JWT signing (use strong random key in production)"
    )
    jwt_algorithm: str = Field(
        default="RS256",
        description="JWT signing algorithm (RS256 recommended for production)"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    jwt_issuer: str = Field(
        default="hk-quant-system",
        description="JWT issuer identifier"
    )
    jwt_audience: str = Field(
        default="hk-quant-system-users",
        description="JWT audience identifier"
    )

    # OAuth 2.0 Configuration (T107)
    oauth_google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth client ID"
    )
    oauth_google_client_secret: Optional[str] = Field(
        default=None,
        description="Google OAuth client secret"
    )
    oauth_microsoft_client_id: Optional[str] = Field(
        default=None,
        description="Microsoft OAuth client ID"
    )
    oauth_microsoft_client_secret: Optional[str] = Field(
        default=None,
        description="Microsoft OAuth client secret"
    )
    oauth_redirect_uri: str = Field(
        default="http://localhost:8001/auth/callback",
        description="OAuth redirect URI"
    )

    # Password Security Configuration (T108)
    password_min_length: int = Field(
        default=12,
        description="Minimum password length"
    )
    password_require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letters in password"
    )
    password_require_numbers: bool = Field(
        default=True,
        description="Require numbers in password"
    )
    password_require_special: bool = Field(
        default=True,
        description="Require special characters in password"
    )
    password_max_history: int = Field(
        default=5,
        description="Number of previous passwords to remember"
    )
    password_expiration_days: Optional[int] = Field(
        default=None,
        description="Password expiration in days (None for no expiration)"
    )
    password_hash_algorithm: str = Field(
        default="argon2id",
        description="Password hashing algorithm (argon2id, bcrypt, scrypt, pbkdf2)"
    )
    password_hash_memory_kb: int = Field(
        default=65536,
        description="Memory usage for argon2id in KB"
    )
    password_hash_time_cost: int = Field(
        default=3,
        description="Time cost for argon2id"
    )
    password_hash_parallelism: int = Field(
        default=1,
        description="Parallelism for argon2id"
    )

    # API Key Management Configuration (T109)
    api_key_prefix: str = Field(
        default="hkqs",
        description="API key prefix for identification"
    )
    api_key_length: int = Field(
        default=48,
        description="API key length (excluding prefix)"
    )
    api_key_default_expiration_days: int = Field(
        default=90,
        description="Default API key expiration in days"
    )
    api_key_max_expiration_days: int = Field(
        default=365,
        description="Maximum API key expiration in days"
    )
    api_key_rotation_days: int = Field(
        default=30,
        description="Days before expiration to rotate API key"
    )
    api_key_default_rate_limit: int = Field(
        default=1000,
        description="Default rate limit per hour"
    )

    # Certificate Management Configuration (T110)
    cert_ca_cert_path: str = Field(
        default="certs/ca.crt",
        description="CA certificate path"
    )
    cert_ca_key_path: str = Field(
        default="certs/ca.key",
        description="CA private key path"
    )
    cert_server_cert_path: str = Field(
        default="certs/server.crt",
        description="Server certificate path"
    )
    cert_server_key_path: str = Field(
        default="certs/server.key",
        description="Server private key path"
    )
    cert_validity_days: int = Field(
        default=365,
        description="Certificate validity period in days"
    )
    cert_renewal_threshold_days: int = Field(
        default=30,
        description="Days before expiration to renew certificate"
    )
    cert_country: str = Field(
        default="HK",
        description="Certificate country"
    )
    cert_state: str = Field(
        default="Hong Kong",
        description="Certificate state/province"
    )
    cert_city: str = Field(
        default="Hong Kong",
        description="Certificate city"
    )
    cert_organization: str = Field(
        default="HK Quant System",
        description="Certificate organization"
    )
    cert_organizational_unit: str = Field(
        default="IT Department",
        description="Certificate organizational unit"
    )

    # Security Settings
    max_login_attempts: int = Field(
        default=5,
        description="Maximum login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=30,
        description="Account lockout duration in minutes"
    )
    session_timeout_minutes: int = Field(
        default=60,
        description="Session timeout in minutes"
    )
    enable_mfa: bool = Field(
        default=True,
        description="Enable multi-factor authentication"
    )
    mfa_issuer: str = Field(
        default="HK Quant System",
        description="MFA issuer name"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Rate limit requests per minute"
    )
    rate_limit_burst: int = Field(
        default=20,
        description="Rate limit burst size"
    )

    # Token Blacklisting
    token_blacklist_enabled: bool = Field(
        default=True,
        description="Enable token blacklisting"
    )
    token_blacklist_store: str = Field(
        default="redis",
        description="Token blacklist storage (redis, database, memory)"
    )
    token_blacklist_expire_seconds: int = Field(
        default=86400,
        description="Token blacklist expiration in seconds"
    )

    # Token Caching
    token_cache_enabled: bool = Field(
        default=True,
        description="Enable token caching"
    )
    token_cache_expire_seconds: int = Field(
        default=300,
        description="Token cache expiration in seconds"
    )

    # Logging
    security_log_enabled: bool = Field(
        default=True,
        description="Enable security event logging"
    )
    security_log_level: str = Field(
        default="INFO",
        description="Security log level (DEBUG, INFO, WARNING, ERROR)"
    )

    # CORS Settings
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8001"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator('jwt_secret_key')
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently random"""
        if v == "CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR":
            import secrets
            return secrets.token_urlsafe(64)
        return v

    @validator('password_hash_algorithm')
    def validate_hash_algorithm(cls, v):
        """Validate password hash algorithm"""
        allowed = ['argon2id', 'bcrypt', 'scrypt', 'pbkdf2_sha256', 'pbkdf2_sha512']
        if v not in allowed:
            raise ValueError(f"Invalid hash algorithm. Must be one of: {allowed}")
        return v

    @validator('jwt_algorithm')
    def validate_jwt_algorithm(cls, v):
        """Validate JWT signing algorithm"""
        allowed = ['RS256', 'ES256', 'HS256', 'PS256']
        if v not in allowed:
            raise ValueError(f"Invalid JWT algorithm. Must be one of: {allowed}")
        return v

    @validator('security_log_level')
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"Invalid log level. Must be one of: {allowed}")
        return v

    def get_jwt_access_token_expire(self) -> timedelta:
        """Get JWT access token expiration as timedelta"""
        return timedelta(minutes=self.jwt_access_token_expire_minutes)

    def get_jwt_refresh_token_expire(self) -> timedelta:
        """Get JWT refresh token expiration as timedelta"""
        return timedelta(days=self.jwt_refresh_token_expire_days)

    def get_password_policy(self) -> dict:
        """Get password policy as dictionary"""
        return {
            'min_length': self.password_min_length,
            'require_uppercase': self.password_require_uppercase,
            'require_lowercase': self.password_require_lowercase,
            'require_numbers': self.password_require_numbers,
            'require_special': self.password_require_special,
            'max_history': self.password_max_history,
            'expiration_days': self.password_expiration_days,
        }

    def get_api_key_settings(self) -> dict:
        """Get API key settings as dictionary"""
        return {
            'prefix': self.api_key_prefix,
            'length': self.api_key_length,
            'default_expiration_days': self.api_key_default_expiration_days,
            'max_expiration_days': self.api_key_max_expiration_days,
            'rotation_days': self.api_key_rotation_days,
            'default_rate_limit': self.api_key_default_rate_limit,
        }

    def get_cert_settings(self) -> dict:
        """Get certificate settings as dictionary"""
        return {
            'ca_cert_path': self.cert_ca_cert_path,
            'ca_key_path': self.cert_ca_key_path,
            'server_cert_path': self.cert_server_cert_path,
            'server_key_path': self.cert_server_key_path,
            'validity_days': self.cert_validity_days,
            'renewal_threshold_days': self.cert_renewal_threshold_days,
            'country': self.cert_country,
            'state': self.cert_state,
            'city': self.cert_city,
            'organization': self.cert_organization,
            'organizational_unit': self.cert_organizational_unit,
        }


# Global configuration instance
auth_config = AuthConfig()
