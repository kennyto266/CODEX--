"""
API Key Management System (T109)
Enterprise-grade API key generation, validation, and usage tracking
"""

import json
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..models.api_key import APIKey, APIKeyScope, APIKeyUsage
from ..models.user import User
from ..models.security_event import SecurityEvent, SecurityEventType

logger = logging.getLogger("hk_quant_system.auth.api_keys")


class APIKeyManager:
    """
    API Key Management System
    Handles API key lifecycle and usage tracking
    """

    def __init__(self, config: AuthConfig, security: SecurityManager, db_session: Session):
        """
        Initialize API key manager

        Args:
            config: Authentication configuration
            security: Security manager instance
            db_session: Database session
        """
        self.config = config
        self.security = security
        self.db = db_session

    def generate_api_key(
        self,
        user: User,
        name: str,
        scopes: List[APIKeyScope],
        expiration_days: Optional[int] = None,
        rate_limit_per_hour: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate new API key

        Args:
            user: User object
            name: API key name
            scopes: List of scopes
            expiration_days: Key expiration in days
            rate_limit_per_hour: Rate limit per hour
            ip_whitelist: List of allowed IP addresses
            description: Optional description

        Returns:
            Dictionary with key_id and secret_key
        """
        # Generate unique key ID
        key_id = self._generate_key_id()

        # Generate secret key
        secret_key = self._generate_secret_key()

        # Hash the secret key for storage
        hashed_key = hashlib.sha256(secret_key.encode()).hexdigest()

        # Calculate expiration
        if expiration_days is None:
            expiration_days = self.config.api_key_default_expiration_days
        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        # Create API key record
        api_key = APIKey(
            user_id=user.id,
            key_id=key_id,
            hashed_key=hashed_key,
            name=name,
            description=description,
            expires_at=expires_at,
            rate_limit_per_hour=rate_limit_per_hour or self.config.api_key_default_rate_limit,
            ip_whitelist=json.dumps(ip_whitelist) if ip_whitelist else None,
        )

        self.db.add(api_key)
        self.db.flush()  # Get ID before adding scopes

        # Add scopes
        for scope in scopes:
            api_key_scope = APIKeyScope(value=scope.value)
            self.db.add(api_key_scope)
            api_key.scopes.append(api_key_scope)

        self.db.commit()

        # Log key creation
        self.security.log_security_event(
            'API_KEY_CREATED',
            user_id=str(user.id),
            details={
                'key_id': key_id,
                'name': name,
                'scopes': [s.value for s in scopes],
                'expires_at': expires_at.isoformat()
            }
        )

        return {
            'key_id': key_id,
            'secret_key': f"{key_id}.{secret_key}",
            'expires_at': expires_at.isoformat(),
            'scopes': [s.value for s in scopes],
        }

    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        # Use timestamp + random data for uniqueness
        timestamp = int(datetime.utcnow().timestamp())
        random_part = secrets.token_hex(8)
        return f"{self.config.api_key_prefix}_{timestamp}_{random_part}"

    def _generate_secret_key(self) -> str:
        """Generate secret key"""
        return secrets.token_urlsafe(self.config.api_key_length)

    def validate_api_key(self, key_string: str) -> Optional[APIKey]:
        """
        Validate API key

        Args:
            key_string: Full API key (key_id.secret_key)

        Returns:
            APIKey object if valid, None otherwise
        """
        try:
            # Parse key
            if '.' not in key_string:
                return None

            key_id, secret_key = key_string.split('.', 1)

            # Get API key record
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                self.security.log_security_event(
                    'API_KEY_INVALID',
                    details={'key_id': key_id, 'reason': 'not_found'}
                )
                return None

            # Check if active and not revoked
            if not api_key.is_active or api_key.is_revoked:
                self.security.log_security_event(
                    'API_KEY_INVALID',
                    user_id=str(api_key.user_id),
                    details={'key_id': key_id, 'reason': 'inactive'}
                )
                return None

            # Check expiration
            if api_key.is_expired():
                self.security.log_security_event(
                    'API_KEY_EXPIRED',
                    user_id=str(api_key.user_id),
                    details={'key_id': key_id}
                )
                return None

            # Verify secret key
            hashed_input = hashlib.sha256(secret_key.encode()).hexdigest()
            if not hmac.compare_digest(api_key.hashed_key, hashed_input):
                self.security.log_security_event(
                    'API_KEY_INVALID',
                    user_id=str(api_key.user_id),
                    details={'key_id': key_id, 'reason': 'invalid_secret'}
                )
                return None

            # Update last used
            api_key.last_used_at = datetime.utcnow()
            self.db.commit()

            return api_key

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None

    def check_api_key_permission(self, api_key: APIKey, required_scope: APIKeyScope) -> bool:
        """
        Check if API key has required scope

        Args:
            api_key: APIKey object
            required_scope: Required scope

        Returns:
            True if authorized
        """
        return api_key.has_scope(required_scope)

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """
        Get API key by ID

        Args:
            key_id: API key ID

        Returns:
            APIKey object or None
        """
        return self.db.query(APIKey).filter_by(key_id=key_id).first()

    def list_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all API keys for a user

        Args:
            user_id: User ID

        Returns:
            List of API key dictionaries
        """
        keys = self.db.query(APIKey).filter_by(user_id=user_id).all()
        return [key.to_dict() for key in keys]

    def revoke_api_key(self, key_id: str, user_id: Optional[int] = None) -> bool:
        """
        Revoke API key

        Args:
            key_id: API key ID
            user_id: Optional user ID for authorization

        Returns:
            True if successful
        """
        try:
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                return False

            if user_id and api_key.user_id != user_id:
                return False

            api_key.is_revoked = True
            api_key.is_active = False
            self.db.commit()

            self.security.log_security_event(
                'API_KEY_REVOKED',
                user_id=str(api_key.user_id),
                details={'key_id': key_id}
            )

            return True
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False

    def delete_api_key(self, key_id: str, user_id: Optional[int] = None) -> bool:
        """
        Delete API key

        Args:
            key_id: API key ID
            user_id: Optional user ID for authorization

        Returns:
            True if successful
        """
        try:
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                return False

            if user_id and api_key.user_id != user_id:
                return False

            # Log before deletion
            self.security.log_security_event(
                'API_KEY_DELETED',
                user_id=str(api_key.user_id),
                details={'key_id': key_id}
            )

            self.db.delete(api_key)
            self.db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

    def rotate_api_key(
        self,
        key_id: str,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, str]]:
        """
        Rotate API key (generate new secret)

        Args:
            key_id: API key ID
            user_id: Optional user ID for authorization

        Returns:
            New key information or None
        """
        try:
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                return None

            if user_id and api_key.user_id != user_id:
                return None

            # Generate new secret
            new_secret = self._generate_secret_key()
            new_hashed = hashlib.sha256(new_secret.encode()).hexdigest()

            # Update key
            api_key.hashed_key = new_hashed
            api_key.last_used_at = None  # Reset usage
            self.db.commit()

            self.security.log_security_event(
                'API_KEY_ROTATED',
                user_id=str(api_key.user_id),
                details={'key_id': key_id}
            )

            return {
                'key_id': key_id,
                'secret_key': f"{key_id}.{new_secret}",
                'expires_at': api_key.expires_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to rotate API key: {e}")
            return None

    def update_api_key(
        self,
        key_id: str,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scopes: Optional[List[APIKeyScope]] = None,
        rate_limit_per_hour: Optional[int] = None,
        expiration_days: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None
    ) -> bool:
        """
        Update API key properties

        Args:
            key_id: API key ID
            user_id: Optional user ID for authorization
            name: New name
            description: New description
            scopes: New scopes
            rate_limit_per_hour: New rate limit
            expiration_days: New expiration in days
            ip_whitelist: New IP whitelist

        Returns:
            True if successful
        """
        try:
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                return False

            if user_id and api_key.user_id != user_id:
                return False

            # Update fields
            if name is not None:
                api_key.name = name
            if description is not None:
                api_key.description = description
            if rate_limit_per_hour is not None:
                api_key.rate_limit_per_hour = rate_limit_per_hour
            if ip_whitelist is not None:
                api_key.ip_whitelist = json.dumps(ip_whitelist)

            if scopes is not None:
                # Clear existing scopes
                api_key.scopes.clear()
                # Add new scopes
                for scope in scopes:
                    api_key_scope = APIKeyScope(value=scope.value)
                    self.db.add(api_key_scope)
                    api_key.scopes.append(api_key_scope)

            if expiration_days is not None:
                api_key.expires_at = datetime.utcnow() + timedelta(days=expiration_days)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            return False

    def log_api_key_usage(
        self,
        api_key: APIKey,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_size: int = 0,
        response_time_ms: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> None:
        """
        Log API key usage

        Args:
            api_key: APIKey object
            endpoint: Requested endpoint
            method: HTTP method
            status_code: Response status code
            ip_address: Client IP
            user_agent: Client user agent
            response_size: Response size in bytes
            response_time_ms: Response time in milliseconds
            request_id: Request ID
        """
        try:
            usage = APIKeyUsage(
                api_key_id=api_key.id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                response_size=response_size,
                response_time_ms=response_time_ms,
                request_id=request_id,
            )

            self.db.add(usage)

            # Update API key usage stats
            api_key.usage_count += 1
            api_key.usage_bytes += response_size

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log API key usage: {e}")

    def get_api_key_usage(
        self,
        key_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get API key usage history

        Args:
            key_id: API key ID
            start_date: Start date
            end_date: End date
            limit: Maximum number of records

        Returns:
            List of usage records
        """
        try:
            query = self.db.query(APIKeyUsage).join(APIKey).filter(APIKey.key_id == key_id)

            if start_date:
                query = query.filter(APIKeyUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(APIKeyUsage.timestamp <= end_date)

            usage = query.order_by(desc(APIKeyUsage.timestamp)).limit(limit).all()

            return [
                {
                    'timestamp': u.timestamp.isoformat(),
                    'endpoint': u.endpoint,
                    'method': u.method,
                    'status_code': u.status_code,
                    'ip_address': u.ip_address,
                    'response_size': u.response_size,
                    'response_time_ms': u.response_time_ms,
                }
                for u in usage
            ]
        except Exception as e:
            logger.error(f"Failed to get API key usage: {e}")
            return []

    def get_api_key_statistics(self, key_id: str) -> Dict[str, Any]:
        """
        Get API key usage statistics

        Args:
            key_id: API key ID

        Returns:
            Statistics dictionary
        """
        try:
            api_key = self.db.query(APIKey).filter_by(key_id=key_id).first()
            if not api_key:
                return {}

            # Get usage statistics
            stats = self.db.query(
                func.count(APIKeyUsage.id).label('total_requests'),
                func.sum(APIKeyUsage.response_size).label('total_bytes'),
                func.avg(APIKeyUsage.response_time_ms).label('avg_response_time'),
                func.min(APIKeyUsage.timestamp).label('first_used'),
                func.max(APIKeyUsage.timestamp).label('last_used'),
            ).filter(APIKeyUsage.api_key_id == api_key.id).first()

            # Get endpoint statistics
            endpoints = self.db.query(
                APIKeyUsage.endpoint,
                func.count(APIKeyUsage.id).label('count')
            ).filter(
                APIKeyUsage.api_key_id == api_key.id
            ).group_by(APIKeyUsage.endpoint).all()

            # Get status code statistics
            status_codes = self.db.query(
                APIKeyUsage.status_code,
                func.count(APIKeyUsage.id).label('count')
            ).filter(
                APIKeyUsage.api_key_id == api_key.id
            ).group_by(APIKeyUsage.status_code).all()

            return {
                'key_id': key_id,
                'total_requests': stats.total_requests or 0,
                'total_bytes': int(stats.total_bytes or 0),
                'avg_response_time_ms': int(stats.avg_response_time or 0),
                'first_used': stats.first_used.isoformat() if stats.first_used else None,
                'last_used': stats.last_used.isoformat() if stats.last_used else None,
                'top_endpoints': [{'endpoint': e[0], 'count': e[1]} for e in endpoints],
                'status_codes': [{'code': s[0], 'count': s[1]} for s in status_codes],
            }
        except Exception as e:
            logger.error(f"Failed to get API key statistics: {e}")
            return {}

    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired API keys

        Returns:
            Number of keys cleaned up
        """
        try:
            expired = self.db.query(APIKey).filter(
                APIKey.expires_at < datetime.utcnow()
            ).all()

            count = 0
            for key in expired:
                if not key.is_revoked:
                    self.security.log_security_event(
                        'API_KEY_EXPIRED',
                        user_id=str(key.user_id),
                        details={'key_id': key.key_id}
                    )

                key.is_active = False
                key.is_revoked = True
                count += 1

            self.db.commit()
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    def check_rate_limit(
        self,
        api_key: APIKey,
        period: str = 'hour'
    ) -> bool:
        """
        Check if API key is within rate limit

        Args:
            api_key: APIKey object
            period: Rate limit period (hour, day)

        Returns:
            True if within limit
        """
        try:
            now = datetime.utcnow()
            if period == 'hour':
                # Calculate time window (last hour)
                window_start = now - timedelta(hours=1)
                limit = api_key.rate_limit_per_hour
            elif period == 'day':
                # Calculate time window (last day)
                window_start = now - timedelta(days=1)
                limit = api_key.rate_limit_per_day
            else:
                return True  # Unknown period, allow

            # Count requests in window
            count = self.db.query(APIKeyUsage).filter(
                and_(
                    APIKeyUsage.api_key_id == api_key.id,
                    APIKeyUsage.timestamp >= window_start
                )
            ).count()

            if count >= limit:
                self.security.log_security_event(
                    'RATE_LIMIT_EXCEEDED',
                    user_id=str(api_key.user_id),
                    details={
                        'key_id': api_key.key_id,
                        'period': period,
                        'count': count,
                        'limit': limit
                    }
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow on error

    def check_ip_whitelist(self, api_key: APIKey, ip_address: str) -> bool:
        """
        Check if IP is in whitelist

        Args:
            api_key: APIKey object
            ip_address: Client IP address

        Returns:
            True if allowed
        """
        if not api_key.ip_whitelist:
            return True  # No whitelist, allow all

        try:
            whitelist = json.loads(api_key.ip_whitelist)
            return ip_address in whitelist
        except (json.JSONDecodeError, TypeError):
            return True  # Invalid whitelist, allow all
