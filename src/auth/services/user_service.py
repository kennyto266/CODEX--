"""
User Service
User management business logic
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..password.manager import PasswordManager
from ..models.user import User, UserRole, UserPermission
from ..models.security_event import SecurityEvent, SecurityEventType
from ..models.api_key import APIKey


class UserService:
    """
    User Management Service
    Handles user lifecycle and management operations
    """

    def __init__(
        self,
        config: AuthConfig,
        security: SecurityManager,
        password_manager: PasswordManager,
        db: Session
    ):
        """
        Initialize user service

        Args:
            config: Authentication configuration
            security: Security manager
            password_manager: Password manager
            db: Database session
        """
        self.config = config
        self.security = security
        self.password_manager = password_manager
        self.db = db

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.VIEWER,
        is_active: bool = True,
        is_verified: bool = False
    ) -> Optional[User]:
        """
        Create new user

        Args:
            email: User email
            username: Username
            password: Password
            full_name: Full name
            role: User role
            is_active: Active status
            is_verified: Verified status

        Returns:
            Created user or None
        """
        # Check if user exists
        if self.db.query(User).filter(
            or_(
                User.email == email,
                User.username == username
            )
        ).first():
            return None

        # Validate password strength
        password_check = self.password_manager.validate_password_strength(password)
        if not password_check['valid']:
            return None

        # Hash password
        hashed_password = self.password_manager.hash_password(password)

        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role.value,
            is_active=is_active,
            is_verified=is_verified,
        )

        # Set password expiration
        if self.config.password_expiration_days:
            user.password_expires_at = self.password_manager.calculate_password_expiry()

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Log event
        self.security.log_security_event(
            'USER_CREATED',
            user_id=str(user.id),
            details={
                'email': user.email,
                'username': user.username,
                'role': user.role
            }
        )

        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return self.db.query(User).filter_by(id=user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User or None
        """
        return self.db.query(User).filter_by(email=email).first()

    def update_user(
        self,
        user_id: int,
        **updates
    ) -> Optional[User]:
        """
        Update user

        Args:
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated user or None
        """
        user = self.get_user(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ['full_name', 'is_active', 'is_verified', 'role']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

        # Log event
        self.security.log_security_event(
            'USER_UPDATED',
            user_id=str(user_id),
            details={'fields_updated': list(updates.keys())}
        )

        return user

    def delete_user(self, user_id: int) -> bool:
        """
        Delete user (soft delete)

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        # Soft delete - deactivate
        user.is_active = False
        self.db.commit()

        # Log event
        self.security.log_security_event(
            'USER_DELETED',
            user_id=str(user_id)
        )

        return True

    def list_users(
        self,
        active_only: bool = True,
        role: Optional[UserRole] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        List users

        Args:
            active_only: Only active users
            role: Filter by role
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of users
        """
        query = self.db.query(User)

        if active_only:
            query = query.filter(User.is_active == True)

        if role:
            query = query.filter(User.role == role.value)

        return query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()

    def count_users(
        self,
        active_only: bool = True,
        role: Optional[UserRole] = None
    ) -> int:
        """
        Count users

        Args:
            active_only: Only active users
            role: Filter by role

        Returns:
            User count
        """
        query = self.db.query(User)

        if active_only:
            query = query.filter(User.is_active == True)

        if role:
            query = query.filter(User.role == role.value)

        return query.count()

    def activate_user(self, user_id: int) -> bool:
        """
        Activate user

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        user.is_active = True
        self.db.commit()

        self.security.log_security_event(
            'USER_ACTIVATED',
            user_id=str(user_id)
        )

        return True

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        user.is_active = False
        self.db.commit()

        self.security.log_security_event(
            'USER_DEACTIVATED',
            user_id=str(user_id)
        )

        return True

    def verify_user(self, user_id: int) -> bool:
        """
        Verify user

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        user.is_verified = True
        self.db.commit()

        self.security.log_security_event(
            'USER_VERIFIED',
            user_id=str(user_id)
        )

        return True

    def lock_user(self, user_id: int, lock_duration_minutes: Optional[int] = None) -> bool:
        """
        Lock user account

        Args:
            user_id: User ID
            lock_duration_minutes: Lock duration (uses config default if None)

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        duration = lock_duration_minutes or self.config.lockout_duration_minutes
        user.lock_account(duration)
        self.db.commit()

        self.security.log_security_event(
            'ACCOUNT_LOCKED',
            user_id=str(user_id),
            details={'duration_minutes': duration}
        )

        return True

    def unlock_user(self, user_id: int) -> bool:
        """
        Unlock user account

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        user = self.get_user(user_id)
        if not user:
            return False

        user.unlock_account()
        self.db.commit()

        self.security.log_security_event(
            'ACCOUNT_UNLOCKED',
            user_id=str(user_id)
        )

        return True

    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get user statistics

        Args:
            user_id: User ID

        Returns:
            User statistics
        """
        user = self.get_user(user_id)
        if not user:
            return {}

        # Get API key count
        api_key_count = self.db.query(APIKey).filter_by(user_id=user_id).count()
        active_api_key_count = self.db.query(APIKey).filter(
            and_(
                APIKey.user_id == user_id,
                APIKey.is_active == True,
                APIKey.is_revoked == False,
                APIKey.expires_at > datetime.utcnow()
            )
        ).count()

        # Get login count (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        login_count = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.user_id == user_id,
                SecurityEvent.event_type == 'LOGIN_SUCCESS',
                SecurityEvent.timestamp > thirty_days_ago
            )
        ).count()

        return {
            'user_id': user_id,
            'email': user.email,
            'username': user.username,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'account_age_days': (datetime.utcnow() - user.account_created_at).days,
            'days_since_last_login': (
                (datetime.utcnow() - user.last_login).days
                if user.last_login else None
            ),
            'password_expires_in_days': (
                (user.password_expires_at - datetime.utcnow()).days
                if user.password_expires_at else None
            ),
            'total_api_keys': api_key_count,
            'active_api_keys': active_api_key_count,
            'login_count_30d': login_count,
        }

    def get_users_nearing_password_expiry(self, days: int = 30) -> List[User]:
        """
        Get users whose passwords are nearing expiration

        Args:
            days: Days threshold

        Returns:
            List of users
        """
        if not self.config.password_expiration_days:
            return []

        threshold = datetime.utcnow() + timedelta(days=days)

        return self.db.query(User).filter(
            and_(
                User.is_active == True,
                User.password_expires_at <= threshold,
                User.password_expires_at > datetime.utcnow()
            )
        ).all()

    def bulk_update_user_roles(
        self,
        user_ids: List[int],
        new_role: UserRole
    ) -> int:
        """
        Update role for multiple users

        Args:
            user_ids: List of user IDs
            new_role: New role

        Returns:
            Number of users updated
        """
        updated = 0
        for user_id in user_ids:
            user = self.get_user(user_id)
            if user and user.role != new_role.value:
                old_role = user.role
                user.role = new_role.value
                updated += 1

                self.security.log_security_event(
                    'ROLE_CHANGED',
                    user_id=str(user_id),
                    details={
                        'old_role': old_role,
                        'new_role': new_role.value
                    }
                )

        if updated > 0:
            self.db.commit()

        return updated
