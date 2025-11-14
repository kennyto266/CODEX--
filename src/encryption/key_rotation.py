"""Key Rotation Module"""

import os
import json
import logging
import time
from typing import Dict, List, Optional
from .aes_gcm import AESGCM256
from .encrypted_fs import EncryptedFileSystem

logger = logging.getLogger(__name__)


class KeyRotationManager:
    def __init__(self, storage_path: str = '.key_rotation'):
        self.storage_path = storage_path
        self.aes = AESGCM256()
        self.efs = EncryptedFileSystem()
        
        os.makedirs(storage_path, exist_ok=True)
        self.metadata_file = os.path.join(storage_path, 'metadata.json')
        self.keys_dir = os.path.join(storage_path, 'keys')
        
        os.makedirs(self.keys_dir, exist_ok=True)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'keys': {},
            'current_key_id': None,
            'rotation_history': []
        }
    
    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def add_key(self, key_id: str, key: bytes, description: str = ''):
        self.metadata['keys'][key_id] = {
            'description': description,
            'created_time': time.time(),
            'usage_count': 0,
            'is_current': False
        }
        
        key_path = os.path.join(self.keys_dir, f'{key_id}.key')
        with open(key_path, 'wb') as f:
            f.write(key)
        
        if self.metadata['current_key_id'] is None:
            self.metadata['current_key_id'] = key_id
            self.metadata['keys'][key_id]['is_current'] = True
        
        self._save_metadata()
    
    def get_key(self, key_id: str):
        if key_id not in self.metadata['keys']:
            return None
        
        key_path = os.path.join(self.keys_dir, f'{key_id}.key')
        if not os.path.exists(key_path):
            return None
        
        with open(key_path, 'rb') as f:
            key = f.read()
        
        self.metadata['keys'][key_id]['usage_count'] += 1
        self._save_metadata()
        
        return key
    
    def get_current_key(self):
        current_id = self.metadata['current_key_id']
        if current_id:
            return self.get_key(current_id)
        return None
    
    def set_current_key(self, key_id: str):
        if key_id not in self.metadata['keys']:
            raise ValueError(f'Key not found: {key_id}')
        
        for k_id in self.metadata['keys']:
            self.metadata['keys'][k_id]['is_current'] = (k_id == key_id)
        
        self.metadata['current_key_id'] = key_id
        self._save_metadata()
    
    def rotate_key(self, old_key_id: str, new_key: bytes, new_key_id: str = None):
        if old_key_id not in self.metadata['keys']:
            raise ValueError(f'Old key not found: {old_key_id}')
        
        if new_key_id is None:
            timestamp = int(time.time())
            new_key_id = f'key_v{timestamp}'
        
        self.add_key(new_key_id, new_key, f'Rotated from {old_key_id}')
        self.set_current_key(new_key_id)
        
        rotation_record = {
            'from_key': old_key_id,
            'to_key': new_key_id,
            'time': time.time()
        }
        self.metadata['rotation_history'].append(rotation_record)
        self._save_metadata()
        
        return new_key_id
    
    def should_rotate(self, key_id: str, max_age_days: int = 90, max_usage: int = 10000) -> bool:
        if key_id not in self.metadata['keys']:
            return False
        
        key_info = self.metadata['keys'][key_id]
        age_days = (time.time() - key_info['created_time']) / 86400
        
        if age_days > max_age_days:
            return True
        
        if key_info['usage_count'] > max_usage:
            return True
        
        return False
    
    def list_keys(self) -> List[Dict]:
        return [
            {
                'key_id': k_id,
                'is_current': info['is_current'],
                'created_time': info['created_time'],
                'usage_count': info['usage_count']
            }
            for k_id, info in self.metadata['keys'].items()
        ]


class KeyRotationError(Exception):
    pass
