"""
Token Service
Token management business logic
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..jwt.manager import JWTManager
from ..models.token import Token, TokenBlacklist, TokenType
from ..models.user import User


class TokenService:
    """
    Token Management Service
    Handles token operations and validation
    """

    def __init__(
        self,
        config: AuthConfig,
        security: SecurityManager,
        jwt_manager: JWTManager,
        db: Session
    ):
        """
        Initialize token service

        Args:
            config: Authentication configuration
            security: Security manager
            jwt_manager: JWT manager
            db: Database session
        """
        self.config = config
        self.security = security
        self.jwt_manager = jwt_manager
        self.db = db

    def create_token_pair(
        self,
        user: User,
        scopes: Optional[List[str]] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create token pair (access + refresh)

        Args:
            user: User object
            scopes: Token scopes
            additional_claims: Additional claims

        Returns:
            Token pair with metadata
        """
        # Generate tokens
        access_token = self.jwt_manager.generate_access_token(
            user=user,
            scopes=scopes,
            additional_claims=additional_claims
        )

        refresh_token = self.jwt_manager.generate_refresh_token(user=user)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': self.config.jwt_access_token_expire_minutes * 60,
            'expires_at': datetime.utcnow() + timedelta(minutes=self.config.jwt_access_token_expire_minutes),
            'user_id': user.id,
            'email': user.email,
            'role': user.role
        }

    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        Verify and decode token

        Args:
            token: JWT token
            token_type: Expected token type

        Returns:
            Token claims or None
        """
        return self.jwt_manager.verify_token(token, token_type)

    def revoke_token(self, jti: str, reason: str = "User action") -> bool:
        """
        Revoke single token

        Args:
            jti: JWT ID
            reason: Revocation reason

        Returns:
            True if successful
        """
        return self.jwt_manager.revoke_token(jti, reason)

    def revoke_all_user_tokens(
        self,
        user_id: int,
        token_type: Optional[str] = None,
        reason: str = "User action"
    ) -> int:
        """
        Revoke all user tokens

        Args:
            user_id: User ID
            token_type: Optional token type filter
            reason: Revocation reason

        Returns:
            Number of tokens revoked
        """
        return self.jwt_manager.revoke_all_user_tokens(user_id, token_type, reason)

    def rotate_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Rotate refresh token

        Args:
            refresh_token: Current refresh token

        Returns:
            New token pair or None
        """
        result = self.jwt_manager.rotate_refresh_token(refresh_token)
        if not result:
            return None

        new_access, new_refresh = result

        return {
            'access_token': new_access,
            'refresh_token': new_refresh,
            'token_type': 'bearer',
            'expires_in': self.config.jwt_access_token_expire_minutes * 60,
        }

    def get_user_tokens(
        self,
        user_id: int,
        token_type: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get user tokens

        Args:
            user_id: User ID
            token_type: Filter by token type
            active_only: Only active tokens
            limit: Maximum number of results

        Returns:
            List of token information
        """
        query = self.db.query(Token).filter(Token.user_id == user_id)

        if token_type:
            query = query.filter(Token.token_type == token_type)

        if active_only:
            query = query.filter(
                and_(
                    Token.expires_at > datetime.utcnow(),
                    Token.revoked_at.is_(None)
                )
            )

        tokens = query.order_by(desc(Token.issued_at)).limit(limit).all()

        return [token.to_dict() for token in tokens]

    def get_token_info(self, jti: str) -> Optional[Dict[str, Any]]:
        """
        Get token information by JTI

        Args:
            jti: JWT ID

        Returns:
            Token information or None
        """
        token = self.db.query(Token).filter_by(jti=jti).first()
        return token.to_dict() if token else None

    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted

        Args:
            jti: JWT ID

        Returns:
            True if blacklisted
        """
        return self.jwt_manager.is_token_blacklisted(jti)

    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Clean up expired tokens

        Returns:
            Cleanup statistics
        """
        count = self.jwt_manager.cleanup_expired_tokens()

        # Also clean up expired blacklist entries
        expired_blacklist = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < datetime.utcnow()
        ).all()

        blacklist_count = len(expired_blacklist)
        for entry in expired_blacklist:
            self.db.delete(entry)

        self.db.commit()

        return {
            'tokens_cleaned': count,
            'blacklist_entries_cleaned': blacklist_count,
        }

    def get_token_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get token statistics

        Args:
            user_id: Optional user ID filter

        Returns:
            Token statistics
        """
        query = self.db.query(Token)

        if user_id:
            query = query.filter(Token.user_id == user_id)

        # Get counts by type
        access_tokens = query.filter(
            and_(
                Token.token_type == 'access',
                Token.expires_at > datetime.utcnow(),
                Token.revoked_at.is_(None)
            )
        ).count()

        refresh_tokens = query.filter(
            and_(
                Token.token_type == 'refresh',
                Token.expires_at > datetime.utcnow(),
                Token.revoked_at.is_(None)
            )
        ).count()

        # Get expired tokens
        expired = query.filter(Token.expires_at < datetime.utcnow()).count()

        # Get revoked tokens
        revoked = query.filter(Token.revoked_at.isnot(None)).count()

        return {
            'active_access_tokens': access_tokens,
            'active_refresh_tokens': refresh_tokens,
            'expired_tokens': expired,
            'revoked_tokens': revoked,
            'total_tokens': access_tokens + refresh_tokens + expired + revoked,
        }

    def get_active_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get active user sessions

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        now = datetime.utcnow()
        tokens = self.db.query(Token).filter(
            and_(
                Token.user_id == user_id,
                Token.expires_at > now,
                Token.revoked_at.is_(None)
            )
        ).order_by(desc(Token.issued_at)).all()

        sessions = []
        for token in tokens:
            sessions.append({
                'jti': token.jti,
                'token_type': token.token_type,
                'issued_at': token.issued_at.isoformat(),
                'expires_at': token.expires_at.isoformat(),
                'scope': token.scope,
                'roles': token.roles,
                'fingerprint': token.fingerprint,
            })

        return sessions

    def force_logout_all(self, user_id: int) -> int:
        """
        Force logout all user sessions

        Args:
            user_id: User ID

        Returns:
            Number of sessions terminated
        """
        count = self.revoke_all_user_tokens(
            user_id,
            reason="Force logout all sessions"
        )

        self.security.log_security_event(
            'FORCE_LOGOUT_ALL',
            user_id=str(user_id),
            details={'sessions_terminated': count}
        )

        return count
