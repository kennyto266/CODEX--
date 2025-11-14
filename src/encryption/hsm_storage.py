"""HSM Storage Module"""

import os
import json
import logging
from typing import Dict, Optional, List
from abc import ABC, abstractmethod
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

logger = logging.getLogger(__name__)


class HSMStorage(ABC):
    @abstractmethod
    def store_key(self, key_id: str, key: bytes) -> bool:
        pass
    
    @abstractmethod
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        pass
    
    @abstractmethod
    def list_keys(self) -> List[str]:
        pass


class SoftwareHSM(HSMStorage):
    def __init__(self, storage_path: str = ".hsm", master_password: Optional[str] = None):
        self.storage_path = storage_path
        self.keys_dir = os.path.join(storage_path, "keys")
        self.metadata_file = os.path.join(storage_path, "metadata.json")
        
        os.makedirs(self.keys_dir, exist_ok=True)
        
        if master_password is None:
            self.master_password = secrets.token_urlsafe(32)
            logger.warning(f"Auto-generated master password: {self.master_password}")
        else:
            self.master_password = master_password
        
        self.fernet = self._get_fernet()
        self.metadata = self._load_metadata()
    
    def _get_fernet(self):
        salt = b"hsm_salt_2024"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = Fernet.generate_key()
        return Fernet(key)
    
    def _load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {"keys": {}}
    
    def _save_metadata(self):
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    def store_key(self, key_id: str, key: bytes) -> bool:
        try:
            encrypted_key = self.fernet.encrypt(key)
            key_path = os.path.join(self.keys_dir, f"{key_id}.key")
            
            with open(key_path, "wb") as f:
                f.write(encrypted_key)
            
            self.metadata["keys"][key_id] = {
                "stored_time": secrets.token_hex(16),
                "size": len(key)
            }
            self._save_metadata()
            
            return True
        except Exception as e:
            logger.error(f"Failed to store key {key_id}: {e}")
            return False
    
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        if key_id not in self.metadata["keys"]:
            return None
        
        key_path = os.path.join(self.keys_dir, f"{key_id}.key")
        if not os.path.exists(key_path):
            return None
        
        try:
            with open(key_path, "rb") as f:
                encrypted_key = f.read()
            decrypted_key = self.fernet.decrypt(encrypted_key)
            return decrypted_key
        except Exception as e:
            logger.error(f"Failed to retrieve key {key_id}: {e}")
            return None
    
    def delete_key(self, key_id: str) -> bool:
        if key_id not in self.metadata["keys"]:
            return False
        
        key_path = os.path.join(self.keys_dir, f"{key_id}.key")
        if os.path.exists(key_path):
            os.remove(key_path)
        
        del self.metadata["keys"][key_id]
        self._save_metadata()
        return True
    
    def list_keys(self) -> List[str]:
        return list(self.metadata["keys"].keys())


class HardwareHSMAdapter(HSMStorage):
    def __init__(self, config: Dict):
        self.config = config
        self.connected = False
        logger.info("Hardware HSM adapter initialized (placeholder)")
    
    def connect(self) -> bool:
        logger.warning("Hardware HSM not implemented - using software fallback")
        self.connected = False
        return False
    
    def store_key(self, key_id: str, key: bytes) -> bool:
        if not self.connected:
            logger.error("Not connected to hardware HSM")
            return False
        return True
    
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        if not self.connected:
            return None
        return None
    
    def delete_key(self, key_id: str) -> bool:
        if not self.connected:
            return False
        return True
    
    def list_keys(self) -> List[str]:
        if not self.connected:
            return []
        return []


class HSMFactory:
    @staticmethod
    def create_hsm(hsm_type: str = "software", **kwargs) -> HSMStorage:
        if hsm_type.lower() == "software":
            return SoftwareHSM(**kwargs)
        elif hsm_type.lower() == "hardware":
            return HardwareHSMAdapter(kwargs)
        else:
            raise ValueError(f"Unknown HSM type: {hsm_type}")


class HSMError(Exception):
    pass
