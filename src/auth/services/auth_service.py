"""
Authentication Service
Main authentication business logic
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..jwt.manager import JWTManager
from ..password.manager import PasswordManager
from ..api_keys.manager import APIKeyManager
from ..oauth.manager import OAuthManager
from ..certificates.manager import CertificateManager
from ..models.user import User
from ..models.security_event import SecurityEvent


class AuthService:
    """
    Main Authentication Service
    Orchestrates all authentication components
    """

    def __init__(
        self,
        config: AuthConfig,
        security: SecurityManager,
        db: Session,
        jwt_manager: JWTManager,
        password_manager: PasswordManager,
        api_key_manager: APIKeyManager,
        oauth_manager: OAuthManager,
        cert_manager: CertificateManager
    ):
        """
        Initialize authentication service

        Args:
            config: Authentication configuration
            security: Security manager
            db: Database session
            jwt_manager: JWT manager
            password_manager: Password manager
            api_key_manager: API key manager
            oauth_manager: OAuth manager
            cert_manager: Certificate manager
        """
        self.config = config
        self.security = security
        self.db = db
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager
        self.api_key_manager = api_key_manager
        self.oauth_manager = oauth_manager
        self.cert_manager = cert_manager

    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Authentication result with user and tokens, or None
        """
        # Get user
        user = self.db.query(User).filter_by(email=email).first()
        if not user or not user.is_active:
            self.security.log_security_event(
                'LOGIN_FAILURE',
                details={'email': email, 'reason': 'user_not_found', 'ip': ip_address}
            )
            return None

        # Check if account is locked
        if user.is_account_locked():
            self.security.log_security_event(
                'LOGIN_BLOCKED_LOCKED',
                user_id=str(user.id),
                details={'email': email, 'ip': ip_address}
            )
            return None

        # Verify password
        is_valid, needs_rehash = self.password_manager.verify_password(
            password,
            user.hashed_password,
            user.id
        )

        if not is_valid:
            # Increment failed attempts
            user.login_attempts += 1
            user.password_failed_attempts += 1

            # Lock account if too many attempts
            if user.password_failed_attempts >= self.config.max_login_attempts:
                user.lock_account(self.config.lockout_duration_minutes)
                self.security.log_security_event(
                    'ACCOUNT_LOCKED',
                    user_id=str(user.id),
                    details={'reason': 'too_many_failed_attempts', 'ip': ip_address}
                )
            else:
                self.security.log_security_event(
                    'LOGIN_FAILURE',
                    user_id=str(user.id),
                    details={'email': email, 'attempts': user.login_attempts, 'ip': ip_address}
                )

            self.db.commit()
            return None

        # Check if password is expired
        if self.password_manager.is_password_expired(user):
            self.security.log_security_event(
                'PASSWORD_EXPIRED',
                user_id=str(user.id),
                details={'email': email, 'ip': ip_address}
            )
            return None

        # Re-hash password if needed
        if needs_rehash:
            new_hash = self.password_manager.hash_password(password, user.id)
            user.hashed_password = new_hash

        # Success - reset failed attempts
        user.login_attempts = 0
        user.password_failed_attempts = 0
        user.last_login = self.security.security_manager.now()
        user.last_login_ip = ip_address
        user.unlock_account()

        # Generate device fingerprint
        device_fingerprint = self.security.generate_device_fingerprint(
            user_agent or '',
            ip_address or ''
        )
        if device_fingerprint not in (user.device_fingerprints or []):
            # Add new device to list
            devices = []
            if user.device_fingerprints:
                try:
                    devices = eval(user.device_fingerprints)
                except:
                    devices = []
            devices.append(device_fingerprint)
            # Keep only last 10 devices
            user.device_fingerprints = str(devices[-10:])

        self.db.commit()

        # Generate tokens
        access_token = self.jwt_manager.generate_access_token(user)
        refresh_token = self.jwt_manager.generate_refresh_token(user)

        # Log success
        self.security.log_security_event(
            'LOGIN_SUCCESS',
            user_id=str(user.id),
            details={
                'email': user.email,
                'last_login': user.last_login.isoformat(),
                'ip': ip_address,
                'device_fingerprint': device_fingerprint
            }
        )

        return {
            'user': user,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'device_fingerprint': device_fingerprint
        }

    def revoke_all_user_sessions(
        self,
        user_id: int,
        reason: str = "User action"
    ) -> int:
        """
        Revoke all user sessions and tokens

        Args:
            user_id: User ID
            reason: Revocation reason

        Returns:
            Number of tokens revoked
        """
        count = self.jwt_manager.revoke_all_user_tokens(user_id, reason=reason)

        # Deactivate all API keys
        keys = self.api_key_manager.list_user_api_keys(user_id)
        for key in keys:
            self.api_key_manager.revoke_api_key(key['key_id'], user_id)

        self.security.log_security_event(
            'ALL_SESSIONS_REVOKED',
            user_id=str(user_id),
            details={
                'reason': reason,
                'tokens_revoked': count,
                'api_keys_revoked': len(keys)
            }
        )

        return count

    def check_security_status(self, user_id: int) -> Dict[str, Any]:
        """
        Check user security status

        Args:
            user_id: User ID

        Returns:
            Security status information
        """
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            return {}

        # Get active token counts
        token_counts = self.jwt_manager.get_active_tokens_count(user_id)

        # Get API key count
        api_keys = self.api_key_manager.list_user_api_keys(user_id)
        active_keys = sum(1 for k in api_keys if k['is_active'] and not k['is_revoked'])

        # Check password status
        password_expired = self.password_manager.is_password_expired(user)
        password_check = self.password_manager.validate_password_strength(
            'dummy'  # Just to get policy
        )

        # Get OAuth connections
        oauth_connections = self.oauth_manager.list_oauth_connections(user_id)

        return {
            'account_locked': user.is_account_locked(),
            'password_expired': password_expired,
            'mfa_enabled': user.mfa_enabled,
            'active_tokens': token_counts,
            'active_api_keys': active_keys,
            'oauth_connections': len(oauth_connections),
            'security_score': self._calculate_security_score(user, token_counts, active_keys, password_expired),
        }

    def _calculate_security_score(
        self,
        user: User,
        token_counts: dict,
        active_keys: int,
        password_expired: bool
    ) -> int:
        """Calculate user security score (0-100)"""
        score = 100

        # Subtract for issues
        if user.is_account_locked():
            score -= 30
        if password_expired:
            score -= 20
        if not user.mfa_enabled:
            score -= 15
        if token_counts.get('total', 0) > 5:
            score -= 10
        if active_keys > 3:
            score -= 10
        if user.password_failed_attempts > 0:
            score -= 5

        return max(0, score)

    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data (tokens, API keys, etc.)

        Returns:
            Cleanup statistics
        """
        stats = {
            'tokens_cleaned': 0,
            'api_keys_cleaned': 0,
            'certificates_cleaned': 0,
        }

        # Clean expired tokens
        stats['tokens_cleaned'] = self.jwt_manager.cleanup_expired_tokens()

        # Clean expired API keys
        stats['api_keys_cleaned'] = self.api_key_manager.cleanup_expired_keys()

        # Clean expired certificates
        stats['certificates_cleaned'] = self.cert_manager.cleanup_expired_certificates()

        self.security.log_security_event(
            'CLEANUP_COMPLETED',
            details=stats
        )

        return stats

    def get_security_report(self, user_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive security report

        Args:
            user_id: User ID

        Returns:
            Security report
        """
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            return {}

        # Get security events
        events = self.db.query(SecurityEvent).filter_by(
            user_id=user_id
        ).order_by(
            SecurityEvent.timestamp.desc()
        ).limit(100).all()

        # Get recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = self.security.security_manager.now() - timedelta(days=30)
        recent_events = [e for e in events if e.timestamp > thirty_days_ago]

        return {
            'user': user.to_dict(),
            'security_status': self.check_security_status(user_id),
            'recent_events': [e.to_dict() for e in recent_events],
            'total_events': len(events),
            'login_history': [
                e.to_dict() for e in events
                if e.event_type == 'LOGIN_SUCCESS'
            ][:10],
            'security_alerts': [
                e.to_dict() for e in recent_events
                if e.severity in ['WARNING', 'ERROR', 'CRITICAL']
            ],
        }
