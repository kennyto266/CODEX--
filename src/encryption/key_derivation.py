"""
PBKDF2 Key Derivation Module
"""

import os
import re
import logging
import secrets
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class PBKDF2KeyDerivation:
    DEFAULT_ITERATIONS = 100000
    MIN_ITERATIONS = 100000
    MAX_ITERATIONS = 1000000
    KEY_LENGTH = 32
    SALT_LENGTH = 32
    
    def __init__(self, iterations=None):
        self.iterations = iterations or self.DEFAULT_ITERATIONS
        if self.iterations < self.MIN_ITERATIONS:
            raise ValueError(f'Iterations must be at least {self.MIN_ITERATIONS}')
        self.backend = default_backend()
        self._cache = {}
    
    def generate_salt(self) -> bytes:
        return secrets.token_bytes(self.SALT_LENGTH)
    
    def validate_password_strength(self, password: str, min_length: int = 12) -> bool:
        if len(password) < min_length:
            return False
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?\":{}|<>]', password))
        return has_upper and has_lower and has_digit and has_special
    
    def derive_key(self, password: str, salt: Optional[bytes] = None, iterations: Optional[int] = None) -> bytes:
        cache_key = (password, salt, iterations or self.iterations)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if salt is None:
            salt = self.generate_salt()
        elif len(salt) != self.SALT_LENGTH:
            raise ValueError(f'Salt must be {self.SALT_LENGTH} bytes')
        
        iter_count = iterations or self.iterations
        
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.KEY_LENGTH,
                salt=salt,
                iterations=iter_count,
                backend=self.backend
            )
            key = kdf.derive(password.encode('utf-8'))
            self._cache[cache_key] = key
            return key
        except Exception as e:
            logger.error(f'Key derivation failed: {e}')
            raise Exception(f'Key derivation failed: {e}')
    
    def derive_key_with_salt(self, password: str, salt: Optional[bytes] = None) -> Dict[str, bytes]:
        if salt is None:
            salt = self.generate_salt()
        key = self.derive_key(password, salt)
        return {'key': key, 'salt': salt}
    
    def verify_key(self, password: str, salt: bytes, target_key: bytes, iterations: Optional[int] = None) -> bool:
        try:
            derived_key = self.derive_key(password, salt, iterations)
            return secrets.compare_digest(derived_key, target_key)
        except Exception:
            return False
    
    def get_derivation_info(self) -> Dict[str, Any]:
        return {
            'iterations': self.iterations,
            'key_length': self.KEY_LENGTH,
            'salt_length': self.SALT_LENGTH,
            'algorithm': 'PBKDF2-HMAC-SHA256'
        }
    
    def clear_cache(self):
        self._cache.clear()


class WeakPasswordError(Exception):
    pass


class KeyDerivationError(Exception):
    pass
