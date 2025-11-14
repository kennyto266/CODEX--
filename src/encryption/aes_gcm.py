"""
AES-256-GCM Encryption Core Module
"""

import os
import logging
from typing import Union, Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)


class AESGCM256:
    KEY_SIZE = 32
    IV_SIZE = 12
    TAG_SIZE = 16
    
    def __init__(self, backend=None):
        self.backend = backend or default_backend()
        
    def generate_key(self) -> bytes:
        return os.urandom(self.KEY_SIZE)
    
    def encrypt(self, plaintext, key, aad=None, iv=None):
        if len(key) != self.KEY_SIZE:
            raise ValueError(f'Key must be {self.KEY_SIZE} bytes')
        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        if iv is None:
            iv = os.urandom(self.IV_SIZE)
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        if aad:
            encryptor.authenticate_additional_data(aad)
        
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag
        
        return {'iv': iv, 'ciphertext': ciphertext, 'tag': tag}
    
    def decrypt(self, encrypted_data, key, aad=None):
        if len(key) != self.KEY_SIZE:
            raise ValueError(f'Key must be {self.KEY_SIZE} bytes')
        
        iv = encrypted_data.get('iv')
        ciphertext = encrypted_data.get('ciphertext')
        tag = encrypted_data.get('tag')
        
        if not all([iv, ciphertext, tag]):
            raise ValueError('Missing encryption components')
        
        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
            decryptor = cipher.decryptor()
            
            if aad:
                decryptor.authenticate_additional_data(aad)
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext
            
        except InvalidTag:
            raise AuthenticationError('Authentication tag verification failed')
    
    def encrypt_file(self, file_path, key, output_path=None, chunk_size=8192):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'File not found: {file_path}')
        
        if output_path is None:
            output_path = file_path + '.enc'
        
        iv = os.urandom(self.IV_SIZE)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        with open(file_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            outfile.write(iv)
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                encrypted_chunk = encryptor.update(chunk)
                outfile.write(encrypted_chunk)
            tag = encryptor.finalize()
            outfile.write(tag)
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path, key, output_path=None):
        if not os.path.exists(encrypted_file_path):
            raise FileNotFoundError(f'File not found: {encrypted_file_path}')
        
        if output_path is None:
            if encrypted_file_path.endswith('.enc'):
                output_path = encrypted_file_path[:-4] + '.decrypted'
            else:
                output_path = encrypted_file_path + '.decrypted'
        
        with open(encrypted_file_path, 'rb') as infile:
            iv = infile.read(self.IV_SIZE)
            encrypted_data = infile.read()
            ciphertext = encrypted_data[:-self.TAG_SIZE]
            tag = encrypted_data[-self.TAG_SIZE:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        
        with open(output_path, 'wb') as outfile:
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            outfile.write(plaintext)
        
        return output_path
    
    def stream_encrypt(self, input_stream, output_stream, key, chunk_size=8192):
        iv = os.urandom(self.IV_SIZE)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        output_stream.write(iv)
        while True:
            chunk = input_stream.read(chunk_size)
            if not chunk:
                break
            encrypted_chunk = encryptor.update(chunk)
            output_stream.write(encrypted_chunk)
        tag = encryptor.finalize()
        output_stream.write(tag)
        
        return {'iv': iv, 'tag': tag}
    
    def stream_decrypt(self, input_stream, output_stream, key, chunk_size=8192):
        iv = input_stream.read(self.IV_SIZE)
        encrypted_data = input_stream.read()
        ciphertext = encrypted_data[:-self.TAG_SIZE]
        tag = encrypted_data[-self.TAG_SIZE:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        
        offset = 0
        while offset < len(ciphertext):
            chunk_end = min(offset + chunk_size, len(ciphertext))
            chunk = ciphertext[offset:chunk_end]
            decrypted_chunk = decryptor.update(chunk)
            output_stream.write(decrypted_chunk)
            offset = chunk_end
        
        decryptor.finalize()
    
    def verify_integrity(self, encrypted_data, key):
        try:
            self.decrypt(encrypted_data, key)
            return True
        except AuthenticationError:
            return False
        except Exception:
            return False


class AuthenticationError(Exception):
    pass


class InvalidKeyError(Exception):
    pass
