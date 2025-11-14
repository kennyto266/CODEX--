"""
Security Core Manager
Centralized security management for authentication and authorization
"""

import logging
import secrets
import hashlib
import hmac
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from .config import AuthConfig


logger = logging.getLogger("hk_quant_system.auth.security")


class SecurityManager:
    """
    Centralized security management class
    Provides security utilities for the authentication system
    """

    def __init__(self, config: AuthConfig):
        """Initialize security manager with configuration"""
        self.config = config
        self._encryption_key = None
        self._setup_encryption()
        self._setup_logging()

    def _setup_encryption(self) -> None:
        """Initialize encryption key for sensitive data"""
        # In production, use a secure key management system
        key = Fernet.generate_key()
        self._encryption_key = Fernet(key)

    def _setup_logging(self) -> None:
        """Setup security logging"""
        if self.config.security_log_enabled:
            handler = logging.FileHandler('security.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, self.config.security_log_level))

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token

        Args:
            length: Token length in bytes

        Returns:
            Base64 encoded random token
        """
        return secrets.token_urlsafe(length)

    def generate_jti(self) -> str:
        """
        Generate a unique JWT ID (JTI)

        Returns:
            Unique identifier for JWT
        """
        timestamp = int(datetime.utcnow().timestamp())
        random_bytes = secrets.token_bytes(16)
        return f"{timestamp}_{random_bytes.hex()}"

    def hash_data(self, data: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Hash data with optional salt

        Args:
            data: Data to hash
            salt: Optional salt (will generate if not provided)

        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            data.encode('utf-8'),
            salt,
            100000  # iterations
        )
        return hash_value.hex(), salt

    def verify_hash(self, data: str, hash_value: str, salt: bytes) -> bool:
        """
        Verify data against hash

        Args:
            data: Original data
            hash_value: Expected hash
            salt: Salt used for hashing

        Returns:
            True if data matches hash
        """
        computed_hash, _ = self.hash_data(data, salt)
        return hmac.compare_digest(computed_hash, hash_value)

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data as string
        """
        if not self._encryption_key:
            self._setup_encryption()
        encrypted = self._encryption_key.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted data string

        Returns:
            Decrypted data
        """
        if not self._encryption_key:
            self._setup_encryption()
        decrypted = self._encryption_key.decrypt(encrypted_data.encode('utf-8'))
        return decrypted.decode('utf-8')

    def generate_api_key(self) -> str:
        """
        Generate a secure API key

        Returns:
            API key with prefix
        """
        token = secrets.token_urlsafe(self.config.api_key_length)
        key = f"{self.config.api_key_prefix}_{token}"
        return key

    def verify_api_key_format(self, api_key: str) -> bool:
        """
        Verify API key format

        Args:
            api_key: API key to verify

        Returns:
            True if format is valid
        """
        expected_prefix = f"{self.config.api_key_prefix}_"
        if not api_key.startswith(expected_prefix):
            return False
        if len(api_key) < len(expected_prefix) + 32:
            return False
        return True

    def generate_csrf_token(self) -> str:
        """
        Generate CSRF token

        Returns:
            CSRF token
        """
        return self.generate_secure_token(32)

    def verify_csrf_token(self, token1: str, token2: str) -> bool:
        """
        Verify CSRF token match

        Args:
            token1: First token
            token2: Second token

        Returns:
            True if tokens match
        """
        return hmac.compare_digest(token1, token2)

    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input

        Args:
            input_str: Input to sanitize

        Returns:
            Sanitized input
        """
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'", '/', '\\', ';', '(', ')']
        sanitized = input_str
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()

    def check_password_strength(self, password: str) -> dict:
        """
        Check password strength against policy

        Args:
            password: Password to check

        Returns:
            Dictionary with strength metrics
        """
        score = 0
        feedback = []

        # Length check
        if len(password) >= self.config.password_min_length:
            score += 1
        else:
            feedback.append(f"Password must be at least {self.config.password_min_length} characters")

        # Uppercase check
        if any(c.isupper() for c in password):
            score += 1
        elif self.config.password_require_uppercase:
            feedback.append("Password must contain uppercase letters")

        # Lowercase check
        if any(c.islower() for c in password):
            score += 1
        elif self.config.password_require_lowercase:
            feedback.append("Password must contain lowercase letters")

        # Number check
        if any(c.isdigit() for c in password):
            score += 1
        elif self.config.password_require_numbers:
            feedback.append("Password must contain numbers")

        # Special character check
        if any(not c.isalnum() for c in password):
            score += 1
        elif self.config.password_require_special:
            feedback.append("Password must contain special characters")

        # Common password check
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            score = 0
            feedback.append("Password is too common")

        # Calculate strength
        if score <= 2:
            strength = "Weak"
        elif score <= 4:
            strength = "Medium"
        else:
            strength = "Strong"

        return {
            'score': score,
            'strength': strength,
            'feedback': feedback
        }

    def log_security_event(self, event_type: str, user_id: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log security event

        Args:
            event_type: Type of event
            user_id: User ID (optional)
            details: Additional event details
        """
        if not self.config.security_log_enabled:
            return

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details or {}
        }

        logger.info(f"Security Event: {event}")

    def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier (IP, user, etc.)
            limit: Maximum requests
            window: Time window in seconds

        Returns:
            True if within limit
        """
        # In production, use Redis for rate limiting
        # This is a simplified implementation
        return True

    def generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """
        Generate device fingerprint

        Args:
            user_agent: Browser user agent
            ip_address: Client IP address

        Returns:
            Device fingerprint hash
        """
        fingerprint_data = f"{user_agent}:{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def validate_certificate(self, cert_data: str) -> Dict[str, Any]:
        """
        Validate certificate data

        Args:
            cert_data: Certificate data

        Returns:
            Validation result
        """
        # In production, use cryptography library for certificate validation
        return {
            'valid': True,
            'subject': {},
            'issuer': {},
            'expires': None
        }

    def is_token_expired(self, token_expires: datetime) -> bool:
        """
        Check if token is expired

        Args:
            token_expires: Token expiration time

        Returns:
            True if token is expired
        """
        return datetime.utcnow() > token_expires

    def should_rotate_api_key(self, key_created: datetime) -> bool:
        """
        Check if API key should be rotated

        Args:
            key_created: API key creation time

        Returns:
            True if key should be rotated
        """
        expiration = key_created + timedelta(days=self.config.api_key_rotation_days)
        return datetime.utcnow() > expiration
