"""
Encryption Module for CODEX Quantitative Trading System

This module provides comprehensive encryption capabilities for protecting
sensitive trading data, strategies, and user information.
"""

try:
    from .aes_gcm import AESGCM256
    from .key_derivation import PBKDF2KeyDerivation
    from .encrypted_fs import EncryptedFileSystem
    from .key_rotation import KeyRotationManager
    from .hsm_storage import HSMStorage, SoftwareHSM, HSMFactory
    from .aes_gcm import AuthenticationError, InvalidKeyError
    
    __all__ = [
        'AESGCM256',
        'PBKDF2KeyDerivation',
        'EncryptedFileSystem',
        'KeyRotationManager',
        'HSMStorage',
        'SoftwareHSM',
        'HSMFactory',
        'AuthenticationError',
        'InvalidKeyError',
    ]
    
except ImportError as e:
    print(f"Warning: Could not import encryption modules: {e}")
    __all__ = []

__version__ = '1.0.0'
