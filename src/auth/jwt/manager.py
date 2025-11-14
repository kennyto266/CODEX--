"""
JWT Authentication Manager (T106)
Enterprise-grade JWT implementation with access and refresh tokens
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..models.token import Token, TokenType, TokenBlacklist
from ..models.user import User, UserPermission

logger = logging.getLogger("hk_quant_system.auth.jwt")


class JWTManager:
    """
    JWT Authentication Manager
    Handles JWT token generation, validation, and management
    """

    def __init__(self, config: AuthConfig, security: SecurityManager, db_session: Session):
        """
        Initialize JWT manager

        Args:
            config: Authentication configuration
            security: Security manager instance
            db_session: Database session
        """
        self.config = config
        self.security = security
        self.db = db_session
        self._private_key = None
        self._public_key = None
        self._load_keys()

    def _load_keys(self) -> None:
        """Load RSA key pair for JWT signing"""
        try:
            # In production, load from secure key storage
            # For development, generate ephemeral keys
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Get public key
            public_key = private_key.public_key()

            # Serialize private key
            self._private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            # Serialize public key
            self._public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

        except Exception as e:
            logger.error(f"Failed to load JWT keys: {e}")
            # Fallback to symmetric key for development
            self._private_key = self.config.jwt_secret_key.encode()
            self._public_key = self.config.jwt_secret_key.encode()

    def generate_access_token(
        self,
        user: User,
        scopes: Optional[List[str]] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate JWT access token

        Args:
            user: User object
            scopes: List of token scopes
            additional_claims: Additional custom claims

        Returns:
            Encoded JWT access token
        """
        now = datetime.utcnow()
        jti = self.security.generate_jti()
        expires = now + self.config.get_jwt_access_token_expire()

        # Build claims
        claims = {
            'iss': self.config.jwt_issuer,
            'sub': str(user.id),  # Subject (user ID)
            'aud': self.config.jwt_audience,
            'iat': now,
            'exp': expires,
            'jti': jti,
            'token_type': 'access',
            'user_id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.role,
        }

        # Add scopes
        if scopes:
            claims['scope'] = ' '.join(scopes)

        # Add custom claims
        if additional_claims:
            claims.update(additional_claims)

        # Store token in database
        token = Token(
            jti=jti,
            token_type=TokenType.ACCESS.value,
            user_id=user.id,
            subject=str(user.id),
            audience=self.config.jwt_audience,
            issuer=self.config.jwt_issuer,
            roles=user.role,
            scopes=json.dumps(scopes) if scopes else None,
            issued_at=now,
            expires_at=expires,
            fingerprint=None  # Will be set if needed
        )
        self.db.add(token)
        self.db.commit()

        # Log token creation
        self.security.log_security_event(
            'TOKEN_CREATED',
            user_id=str(user.id),
            details={
                'jti': jti,
                'token_type': 'access',
                'expires': expires.isoformat()
            }
        )

        # Encode token
        try:
            if self.config.jwt_algorithm.startswith('RS') or self.config.jwt_algorithm.startswith('ES'):
                token_str = jwt.encode(
                    claims,
                    self._private_key,
                    algorithm=self.config.jwt_algorithm
                )
            else:
                # HS256/HS384/HS512
                token_str = jwt.encode(
                    claims,
                    self.config.jwt_secret_key,
                    algorithm=self.config.jwt_algorithm
                )
            return token_str
        except Exception as e:
            logger.error(f"Failed to encode JWT token: {e}")
            raise

    def generate_refresh_token(
        self,
        user: User,
        access_token_jti: Optional[str] = None
    ) -> str:
        """
        Generate JWT refresh token

        Args:
            user: User object
            access_token_jti: JTI of associated access token

        Returns:
            Encoded JWT refresh token
        """
        now = datetime.utcnow()
        jti = self.security.generate_jti()
        expires = now + self.config.get_jwt_refresh_token_expire()

        claims = {
            'iss': self.config.jwt_issuer,
            'sub': str(user.id),
            'aud': self.config.jwt_audience,
            'iat': now,
            'exp': expires,
            'jti': jti,
            'token_type': 'refresh',
            'user_id': user.id,
            'email': user.email,
        }

        # Store token in database
        token = Token(
            jti=jti,
            token_type=TokenType.REFRESH.value,
            user_id=user.id,
            subject=str(user.id),
            audience=self.config.jwt_audience,
            issuer=self.config.jwt_issuer,
            issued_at=now,
            expires_at=expires,
        )
        self.db.add(token)
        self.db.commit()

        # Log token creation
        self.security.log_security_event(
            'TOKEN_CREATED',
            user_id=str(user.id),
            details={
                'jti': jti,
                'token_type': 'refresh',
                'expires': expires.isoformat()
            }
        )

        # Encode token
        try:
            if self.config.jwt_algorithm.startswith('RS') or self.config.jwt_algorithm.startswith('ES'):
                token_str = jwt.encode(
                    claims,
                    self._private_key,
                    algorithm=self.config.jwt_algorithm
                )
            else:
                token_str = jwt.encode(
                    claims,
                    self.config.jwt_secret_key,
                    algorithm=self.config.jwt_algorithm
                )
            return token_str
        except Exception as e:
            logger.error(f"Failed to encode refresh token: {e}")
            raise

    def verify_token(
        self,
        token: str,
        token_type: str = 'access'
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type (access, refresh, etc.)

        Returns:
            Decoded token claims or None if invalid
        """
        try:
            # Check token blacklist if enabled
            if self.config.token_blacklist_enabled:
                # Decode without verification to get JTI
                unverified = jwt.decode(
                    token,
                    options={"verify_signature": False}
                )
                jti = unverified.get('jti')

                if jti and self.is_token_blacklisted(jti):
                    self.security.log_security_event(
                        'TOKEN_BLACKLISTED',
                        details={'jti': jti, 'token': token[:20] + '...'}
                    )
                    return None

            # Verify and decode token
            if self.config.jwt_algorithm.startswith('RS') or self.config.jwt_algorithm.startswith('ES'):
                decoded = jwt.decode(
                    token,
                    self._public_key,
                    algorithms=[self.config.jwt_algorithm],
                    audience=self.config.jwt_audience,
                    issuer=self.config.jwt_issuer
                )
            else:
                decoded = jwt.decode(
                    token,
                    self.config.jwt_secret_key,
                    algorithms=[self.config.jwt_algorithm],
                    audience=self.config.jwt_audience,
                    issuer=self.config.jwt_issuer
                )

            # Verify token type
            if decoded.get('token_type') != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {decoded.get('token_type')}")
                return None

            # Verify token is not revoked
            jti = decoded.get('jti')
            if jti:
                token_record = self.db.query(Token).filter_by(jti=jti).first()
                if token_record and token_record.is_revoked():
                    self.security.log_security_event(
                        'TOKEN_REVOKED',
                        user_id=decoded.get('user_id'),
                        details={'jti': jti}
                    )
                    return None

            # Update last activity
            if jti:
                token_record = self.db.query(Token).filter_by(jti=jti).first()
                if token_record:
                    token_record.updated_at = datetime.utcnow()
                    self.db.commit()

            return decoded

        except ExpiredSignatureError:
            self.security.log_security_event(
                'TOKEN_EXPIRED',
                details={'token': token[:20] + '...'}
            )
            logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            self.security.log_security_event(
                'INVALID_TOKEN',
                details={'error': str(e), 'token': token[:20] + '...'}
            )
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def revoke_token(self, jti: str, reason: str = "User requested revocation") -> bool:
        """
        Revoke JWT token

        Args:
            jti: JWT ID to revoke
            reason: Revocation reason

        Returns:
            True if successful
        """
        try:
            # Find token
            token = self.db.query(Token).filter_by(jti=jti).first()
            if not token:
                return False

            # Revoke token
            token.revoke()
            self.db.commit()

            # Add to blacklist if enabled
            if self.config.token_blacklist_enabled:
                blacklist_entry = TokenBlacklist(
                    jti=jti,
                    user_id=token.user_id,
                    token_type=token.token_type,
                    reason=reason,
                    expires_at=token.expires_at
                )
                self.db.add(blacklist_entry)
                self.db.commit()

            # Log revocation
            self.security.log_security_event(
                'TOKEN_REVOKED',
                user_id=str(token.user_id),
                details={'jti': jti, 'reason': reason}
            )

            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def revoke_all_user_tokens(
        self,
        user_id: int,
        token_type: Optional[str] = None,
        reason: str = "Security event - force logout"
    ) -> int:
        """
        Revoke all tokens for a user

        Args:
            user_id: User ID
            token_type: Optional token type filter
            reason: Revocation reason

        Returns:
            Number of tokens revoked
        """
        try:
            query = self.db.query(Token).filter(
                and_(
                    Token.user_id == user_id,
                    Token.revoked_at.is_(None),
                    Token.expires_at > datetime.utcnow()
                )
            )

            if token_type:
                query = query.filter(Token.token_type == token_type)

            tokens = query.all()
            count = 0

            for token in tokens:
                self.revoke_token(token.jti, reason)
                count += 1

            return count
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            return 0

    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted

        Args:
            jti: JWT ID

        Returns:
            True if blacklisted
        """
        try:
            if not self.config.token_blacklist_enabled:
                return False

            blacklist = self.db.query(TokenBlacklist).filter_by(jti=jti).first()
            if not blacklist:
                return False

            # Check if blacklist entry is expired
            if blacklist.is_expired():
                self.db.delete(blacklist)
                self.db.commit()
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    def rotate_refresh_token(
        self,
        refresh_token: str
    ) -> Optional[tuple[str, str]]:
        """
        Rotate refresh token (new refresh + access token)

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) or None
        """
        try:
            # Verify refresh token
            claims = self.verify_token(refresh_token, 'refresh')
            if not claims:
                return None

            # Get user
            user = self.db.query(User).filter_by(id=claims['user_id']).first()
            if not user or not user.is_active:
                return None

            # Revoke old refresh token
            self.revoke_token(claims['jti'], "Token rotation")

            # Generate new tokens
            new_access = self.generate_access_token(user)
            new_refresh = self.generate_refresh_token(user)

            return new_access, new_refresh

        except Exception as e:
            logger.error(f"Failed to rotate refresh token: {e}")
            return None

    def decode_token_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token claims without verification (for debugging)

        Args:
            token: JWT token

        Returns:
            Decoded claims or None
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False, "verify_aud": False}
            )
        except Exception as e:
            logger.error(f"Failed to decode token claims: {e}")
            return None

    def get_user_permissions_from_token(self, token: str) -> List[str]:
        """
        Extract user permissions from token

        Args:
            token: JWT token

        Returns:
            List of user permissions
        """
        claims = self.verify_token(token)
        if not claims:
            return []

        # Get scope from claims
        scope = claims.get('scope', '')
        if scope:
            return scope.split(' ')

        return []

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired and old tokens

        Returns:
            Number of tokens cleaned up
        """
        try:
            # Find expired tokens
            expired_tokens = self.db.query(Token).filter(
                Token.expires_at < datetime.utcnow()
            ).all()

            count = 0
            for token in expired_tokens:
                # Revoke if not already revoked
                if not token.is_revoked():
                    token.revoke()
                count += 1

            # Find expired blacklist entries
            expired_blacklist = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at < datetime.utcnow()
            ).all()

            for entry in expired_blacklist:
                self.db.delete(entry)

            self.db.commit()
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            self.db.rollback()
            return 0

    def get_active_tokens_count(self, user_id: int) -> Dict[str, int]:
        """
        Get count of active tokens for user

        Args:
            user_id: User ID

        Returns:
            Dictionary of token type counts
        """
        try:
            now = datetime.utcnow()
            tokens = self.db.query(Token).filter(
                and_(
                    Token.user_id == user_id,
                    Token.expires_at > now,
                    Token.revoked_at.is_(None)
                )
            ).all()

            counts = {
                'access': 0,
                'refresh': 0,
                'total': 0
            }

            for token in tokens:
                counts[token.token_type] = counts.get(token.token_type, 0) + 1
                counts['total'] += 1

            return counts
        except Exception as e:
            logger.error(f"Failed to get active tokens count: {e}")
            return {'access': 0, 'refresh': 0, 'total': 0}
