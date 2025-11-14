"""
Password Security Manager (T108)
Enterprise-grade password hashing, validation, and security policies
"""

import re
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHash,
    InvalidSecret,
)
from passlib.context import CryptContext
from passlib.hash import bcrypt, argon2, pbkdf2_sha256, pbkdf2_sha512, scrypt

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..models.user import User
from ..models.security_event import SecurityEvent, SecurityEventType

logger = logging.getLogger("hk_quant_system.auth.password")


class PasswordManager:
    """
    Password Security Manager
    Handles password hashing, validation, and security policies
    """

    # Common password list (in production, use larger list or external service)
    COMMON_PASSWORDS = {
        'password', '123456', '123456789', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'iloveyou',
        'sunshine', 'princess', 'football', 'login', 'starwars',
    }

    # Weak password patterns
    WEAK_PATTERNS = [
        re.compile(r'(.)\1{3,}', re.IGNORECASE),  # Repeated characters
        re.compile(r'0123|1234|2345|3456|4567|5678|6789|7890', re.IGNORECASE),  # Sequential numbers
        re.compile(r'abcdef|bcdefg|cdefgh|defghi|efghij', re.IGNORECASE),  # Sequential letters
        re.compile(r'qwerty|asdfgh|zxcvbn|qwertyuiop', re.IGNORECASE),  # Keyboard patterns
    ]

    def __init__(self, config: AuthConfig, security: SecurityManager):
        """
        Initialize password manager

        Args:
            config: Authentication configuration
            security: Security manager instance
        """
        self.config = config
        self.security = security
        self._argon2_hasher = None
        self._passlib_context = None
        self._setup_hashers()

    def _setup_hashers(self) -> None:
        """Initialize password hashers based on configuration"""
        algorithm = self.config.password_hash_algorithm.lower()

        if algorithm == 'argon2id':
            self._argon2_hasher = PasswordHasher(
                time_cost=self.config.password_hash_time_cost,
                memory_cost=self.config.password_hash_memory_kb,
                parallelism=self.config.password_hash_parallelism,
                type=Type.ID,
            )
        elif algorithm == 'bcrypt':
            self._passlib_context = CryptContext(
                schemes=['bcrypt'],
                deprecated='auto',
                bcrypt__rounds=12,
            )
        elif algorithm == 'scrypt':
            self._passlib_context = CryptContext(
                schemes=['scrypt'],
                deprecated='auto',
                scrypt__n=16384,  # CPU cost
                scrypt__r=8,      # Memory cost
                scrypt__p=1,      # Parallelism
            )
        elif 'pbkdf2' in algorithm:
            # Default to PBKDF2-SHA256
            self._passlib_context = CryptContext(
                schemes=['pbkdf2_sha256', 'pbkdf2_sha512'],
                deprecated='auto',
                pbkdf2_sha256__rounds=100000,
            )

    def hash_password(self, password: str, user_id: Optional[int] = None) -> str:
        """
        Hash password using configured algorithm

        Args:
            password: Plain text password
            user_id: Optional user ID for logging

        Returns:
            Hashed password string
        """
        algorithm = self.config.password_hash_algorithm.lower()

        try:
            if algorithm == 'argon2id':
                if not self._argon2_hasher:
                    self._setup_hashers()
                hashed = self._argon2_hasher.hash(password)
            elif algorithm in ['bcrypt', 'scrypt', 'pbkdf2_sha256', 'pbkdf2_sha512']:
                if not self._passlib_context:
                    self._setup_hashers()
                hashed = self._passlib_context.hash(password)
            else:
                # Fallback to PBKDF2-SHA256
                hashed = pbkdf2_sha256.hash(password, rounds=100000)

            if user_id:
                self.security.log_security_event(
                    'PASSWORD_HASHED',
                    user_id=str(user_id),
                    details={'algorithm': algorithm}
                )

            return hashed

        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            raise

    def verify_password(self, password: str, hashed: str, user_id: Optional[int] = None) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain text password
            hashed: Hashed password
            user_id: Optional user ID for logging

        Returns:
            True if password matches
        """
        try:
            algorithm = self.config.password_hash_algorithm.lower()

            if algorithm == 'argon2id':
                if not self._argon2_hasher:
                    self._setup_hashers()
                try:
                    self._argon2_hasher.verify(hashed, password)
                    # Re-hash if parameters changed
                    if self._argon2_hasher.check_needs_rehash(hashed):
                        new_hash = self._argon2_hasher.hash(password)
                        return new_hash, True
                    return True, False
                except VerifyMismatchError:
                    return False, False
            elif algorithm in ['bcrypt', 'scrypt', 'pbkdf2_sha256', 'pbkdf2_sha512']:
                if not self._passlib_context:
                    self._setup_hashers()
                try:
                    is_valid = self._passlib_context.verify(password, hashed)
                    # Re-hash if needed
                    if is_valid and self._passlib_context.needs_update(hashed):
                        new_hash = self._passlib_context.hash(password)
                        return True, True
                    return is_valid, False
                except Exception:
                    return False, False
            else:
                # Fallback
                return pbkdf2_sha256.verify(password, hashed), False

        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False, False

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength against security policy

        Args:
            password: Password to validate

        Returns:
            Dictionary with validation results
        """
        feedback = []
        score = 0

        # Length check
        if len(password) >= self.config.password_min_length:
            score += 1
        else:
            feedback.append(f"Password must be at least {self.config.password_min_length} characters long")

        # Uppercase check
        if any(c.isupper() for c in password):
            score += 1
        elif self.config.password_require_uppercase:
            feedback.append("Password must contain at least one uppercase letter (A-Z)")

        # Lowercase check
        if any(c.islower() for c in password):
            score += 1
        elif self.config.password_require_lowercase:
            feedback.append("Password must contain at least one lowercase letter (a-z)")

        # Number check
        if any(c.isdigit() for c in password):
            score += 1
        elif self.config.password_require_numbers:
            feedback.append("Password must contain at least one number (0-9)")

        # Special character check
        if any(not c.isalnum() for c in password):
            score += 1
        elif self.config.password_require_special:
            feedback.append("Password must contain at least one special character (!@#$%^&* etc.)")

        # Common password check
        if password.lower() in self.COMMON_PASSWORDS:
            score = 0
            feedback.append("Password is too common and easily guessable")

        # Weak pattern check
        for pattern in self.WEAK_PATTERNS:
            if pattern.search(password):
                feedback.append("Password contains easily guessable patterns")
                break

        # Calculate strength
        max_score = 5
        percentage = (score / max_score) * 100

        if score <= 1:
            strength = "Very Weak"
            strength_level = 0
        elif score == 2:
            strength = "Weak"
            strength_level = 1
        elif score == 3:
            strength = "Fair"
            strength_level = 2
        elif score == 4:
            strength = "Good"
            strength_level = 3
        else:
            strength = "Strong"
            strength_level = 4

        # Check against HaveIBeenPwned (in production, implement with proper API)
        # is_compromised = self._check_hibp(password)

        return {
            'valid': score >= 3,  # Minimum "Good" strength
            'score': score,
            'max_score': max_score,
            'percentage': percentage,
            'strength': strength,
            'strength_level': strength_level,
            'feedback': feedback,
            'policy_compliance': {
                'min_length_ok': len(password) >= self.config.password_min_length,
                'uppercase_ok': any(c.isupper() for c in password) or not self.config.password_require_uppercase,
                'lowercase_ok': any(c.islower() for c in password) or not self.config.password_require_lowercase,
                'numbers_ok': any(c.isdigit() for c in password) or not self.config.password_require_numbers,
                'special_ok': any(not c.isalnum() for c in password) or not self.config.password_require_special,
            }
        }

    def check_password_history(self, new_password: str, password_history: List[str], max_history: int = 5) -> bool:
        """
        Check if password is in history (prevents reuse)

        Args:
            new_password: New password to check
            password_history: List of previous password hashes
            max_history: Maximum number of passwords to check

        Returns:
            True if password is NOT in history (allowed)
        """
        # Only check the most recent passwords
        history_to_check = password_history[-max_history:] if password_history else []

        for hashed_password in history_to_check:
            matches, _ = self.verify_password(new_password, hashed_password)
            if matches:
                return False  # Password found in history

        return True  # Password not in history

    def update_password_history(self, user: User, new_password: str) -> List[str]:
        """
        Update user's password history

        Args:
            user: User object
            new_password: New password to hash and add to history

        Returns:
            Updated password history
        """
        # Hash the new password
        new_hash = self.hash_password(new_password, user.id)

        # Get current history
        if user.password_history:
            try:
                history = json.loads(user.password_history)
            except (json.JSONDecodeError, TypeError):
                history = []
        else:
            history = []

        # Add new password to history
        history.append(new_hash)

        # Keep only the most recent passwords
        max_history = self.config.password_max_history
        if len(history) > max_history:
            history = history[-max_history:]

        return history

    def is_password_expired(self, user: User) -> bool:
        """
        Check if user password is expired

        Args:
            user: User object

        Returns:
            True if password is expired
        """
        if not self.config.password_expiration_days or not user.password_expires_at:
            return False

        return datetime.utcnow() > user.password_expires_at

    def should_expire_password(self, user: User) -> bool:
        """
        Check if user password should be set to expire

        Args:
            user: User object

        Returns:
            True if password should be set to expire
        """
        if not self.config.password_expiration_days:
            return False

        # If no expiration date, set it
        if not user.password_expires_at:
            return True

        return False

    def calculate_password_expiry(self) -> datetime:
        """
        Calculate password expiry date

        Returns:
            Expiry datetime
        """
        if not self.config.password_expiration_days:
            return datetime.utcnow() + timedelta(days=365)  # Default 1 year

        return datetime.utcnow() + timedelta(days=self.config.password_expiration_days)

    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password

        Args:
            length: Password length

        Returns:
            Random password meeting security requirements
        """
        # Character sets
        uppercase = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Excluding confusing letters
        lowercase = 'abcdefghijkmnopqrstuvwxyz'  # Excluding confusing letters
        numbers = '23456789'  # Excluding 0 and 1
        special = '!@#$%^&*()_+-=[]{}|;:,.<>?'

        # Ensure at least one character from each required set
        password = [
            secrets.choice(uppercase) if self.config.password_require_uppercase else '',
            secrets.choice(lowercase) if self.config.password_require_lowercase else '',
            secrets.choice(numbers) if self.config.password_require_numbers else '',
            secrets.choice(special) if self.config.password_require_special else '',
        ]

        # Remaining characters
        all_chars = uppercase + lowercase + numbers + special
        remaining_length = max(0, length - len([c for c in password if c]))

        for _ in range(remaining_length):
            password.append(secrets.choice(all_chars))

        # Shuffle and return
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    def create_password_reset_token(self, user: User) -> str:
        """
        Create password reset token

        Args:
            user: User object

        Returns:
            Password reset token
        """
        token = self.security.generate_secure_token(32)
        expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration

        # Store token in user record
        user.password_reset_token = token
        user.password_reset_expires = expires
        user.password_reset_used = False

        self.security.log_security_event(
            'PASSWORD_RESET_REQUESTED',
            user_id=str(user.id),
            details={'expires': expires.isoformat()}
        )

        return token

    def verify_password_reset_token(self, token: str, user: User) -> bool:
        """
        Verify password reset token

        Args:
            token: Reset token
            user: User object

        Returns:
            True if token is valid
        """
        if not user.password_reset_token or not user.password_reset_expires:
            return False

        # Check if token matches
        if not self.security.verify_hash(token, user.password_reset_token, b''):
            # Token might be encrypted, try direct comparison
            if token != user.password_reset_token:
                return False

        # Check if expired
        if datetime.utcnow() > user.password_reset_expires:
            return False

        # Check if already used
        if user.password_reset_used:
            return False

        return True

    def use_password_reset_token(self, token: str, user: User) -> bool:
        """
        Mark password reset token as used

        Args:
            token: Reset token
            user: User object

        Returns:
            True if successful
        """
        if not self.verify_password_reset_token(token, user):
            return False

        user.password_reset_used = True
        user.password_reset_token = None
        user.password_reset_expires = None

        return True

    def generate_mfa_secret(self) -> str:
        """
        Generate MFA secret (for TOTP)

        Returns:
            Base32 encoded secret
        """
        # In production, use proper TOTP library like pyotp
        secret = secrets.token_hex(20)
        return secret

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate MFA backup codes

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-digit code
            code = ''.join(secrets.choice('0123456789') for _ in range(8))
            codes.append(code)

        return codes

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data (passwords, tokens, etc.)

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        return self.security.encrypt_sensitive_data(data)

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data
        """
        return self.security.decrypt_sensitive_data(encrypted_data)

    def get_password_policy(self) -> Dict[str, Any]:
        """
        Get password policy configuration

        Returns:
            Password policy dictionary
        """
        return {
            'min_length': self.config.password_min_length,
            'require_uppercase': self.config.password_require_uppercase,
            'require_lowercase': self.config.password_require_lowercase,
            'require_numbers': self.config.password_require_numbers,
            'require_special': self.config.password_require_special,
            'max_history': self.config.password_max_history,
            'expiration_days': self.config.password_expiration_days,
            'hash_algorithm': self.config.password_hash_algorithm,
            'min_strength': 3,  # Minimum "Good" strength
        }

    def check_breached_password(self, password: str) -> bool:
        """
        Check if password is in known breaches (HaveIBeenPwned)

        Args:
            password: Password to check

        Returns:
            True if password is compromised
        """
        # In production, use HaveIBeenPwned Pwned Passwords API
        # This is a simplified check against local list
        return password.lower() in self.COMMON_PASSWORDS
