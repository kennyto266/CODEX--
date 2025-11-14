"""
Encrypted File System Module
"""

import os
import json
import logging
import time
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
from .aes_gcm import AESGCM256, AuthenticationError
from .key_derivation import PBKDF2KeyDerivation

logger = logging.getLogger(__name__)


class EncryptedFileSystem:
    def __init__(self, key: Optional[bytes] = None):
        self.aes = AESGCM256()
        self.kdf = PBKDF2KeyDerivation()
        self.key = key or self.aes.generate_key()
    
    def encrypt_file(self, file_path: str, key: Optional[bytes] = None, output_path: Optional[str] = None) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'File not found: {file_path}')
        
        encryption_key = key or self.key
        if output_path is None:
            output_path = file_path + '.enc'
        
        file_stat = os.stat(file_path)
        metadata = {
            'original_path': str(Path(file_path).absolute()),
            'file_size': file_stat.st_size,
            'modified_time': file_stat.st_mtime,
            'encryption_time': time.time()
        }
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        metadata_bytes = json.dumps(metadata, separators=(',', ':')).encode('utf-8')
        combined_data = metadata_bytes + b'|||METADATA_END|||' + file_data
        
        encrypted = self.aes.encrypt(combined_data, encryption_key)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted['iv'])
            f.write(encrypted['tag'])
            f.write(encrypted['ciphertext'])
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path: str, key: Optional[bytes] = None, output_path: Optional[str] = None) -> Tuple[str, Dict]:
        if not os.path.exists(encrypted_file_path):
            raise FileNotFoundError(f'File not found: {encrypted_file_path}')
        
        decryption_key = key or self.key
        if output_path is None:
            if encrypted_file_path.endswith('.enc'):
                output_path = encrypted_file_path[:-4] + '.decrypted'
            else:
                output_path = encrypted_file_path + '.decrypted'
        
        with open(encrypted_file_path, 'rb') as f:
            iv = f.read(self.aes.IV_SIZE)
            tag = f.read(self.aes.TAG_SIZE)
            ciphertext = f.read()
        
        encrypted_data = {'iv': iv, 'tag': tag, 'ciphertext': ciphertext}
        
        try:
            decrypted_data = self.aes.decrypt(encrypted_data, decryption_key)
        except AuthenticationError:
            raise AuthenticationError('File authentication failed')
        
        separator = b'|||METADATA_END|||'
        if separator not in decrypted_data:
            raise ValueError('Invalid encrypted file format')
        
        metadata_bytes, file_data = decrypted_data.split(separator, 1)
        metadata = json.loads(metadata_bytes.decode('utf-8'))
        
        with open(output_path, 'wb') as f:
            f.write(file_data)
        
        os.utime(output_path, (metadata['modified_time'], metadata['modified_time']))
        
        return output_path, metadata
    
    def verify_file_integrity(self, encrypted_file_path: str, key: Optional[bytes] = None) -> bool:
        if not os.path.exists(encrypted_file_path):
            return False
        
        verification_key = key or self.key
        
        with open(encrypted_file_path, 'rb') as f:
            iv = f.read(self.aes.IV_SIZE)
            tag = f.read(self.aes.TAG_SIZE)
            ciphertext = f.read()
        
        encrypted_data = {'iv': iv, 'tag': tag, 'ciphertext': ciphertext}
        
        return self.aes.verify_integrity(encrypted_data, verification_key)


class EncryptedFileError(Exception):
    pass
