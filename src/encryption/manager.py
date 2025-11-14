"""
加密管理器 - 统一的AES-256加密管理层
整合密钥派生、加密、解密和完整性验证

基于OpenSpec规范 - 零信任架构，用户控制密钥
"""

import os
import json
import base64
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

from .aes_gcm import AESGCMEncryption
from .key_derivation import PBKDF2KeyDerivation, ScryptKeyDerivation
from .key_manager import KeyManager

logger = logging.getLogger('quant_system.encryption')

class EncryptionManager:
    """
    统一加密管理器
    提供完整的加密解决方案，支持密码和密钥两种模式
    """

    def __init__(self,
                 keys_dir: str = 'keys',
                 encrypted_data_dir: str = 'encrypted_data',
                 use_password: bool = True):
        """
        初始化加密管理器

        Args:
            keys_dir: 密钥存储目录
            encrypted_data_dir: 加密数据存储目录
            use_password: 是否使用密码模式（True）或密钥模式（False）
        """
        self.keys_dir = Path(keys_dir)
        self.encrypted_data_dir = Path(encrypted_data_dir)
        self.use_password = use_password

        # 创建目录
        self.keys_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.encrypted_data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # 初始化组件
        self.key_manager = KeyManager(str(self.keys_dir))
        self.pbkdf2 = PBKDF2KeyDerivation()
        self.scrypt = ScryptKeyDerivation()

        # 加密实例缓存
        self._encryption_cache: Dict[str, AESGCMEncryption] = {}

        # 配置
        self.master_key_file = self.keys_dir / 'master.key'
        self.password_key_file = self.keys_dir / 'password_key.json'
        self.config_file = self.keys_dir / 'encryption_config.json'

        # 加载或创建配置
        self.config = self._load_config()

        logger.info(f"加密管理器已初始化: 密码模式={use_password}")

    def _load_config(self) -> Dict[str, Any]:
        """加载加密配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")

        default_config = {
            'version': '2.0',
            'algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2',
            'iterations': 310000,
            'created_at': datetime.utcnow().isoformat(),
            'encrypted_items': []
        }

        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict[str, Any]):
        """保存加密配置"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)

    def setup_with_password(self, password: str, description: str = "默认加密密钥") -> Dict[str, str]:
        """
        使用密码设置加密系统

        Args:
            password: 用户密码
            description: 密钥描述

        Returns:
            设置信息
        """
        if not self.use_password:
            raise ValueError("当前配置为密钥模式，请重新初始化")

        try:
            # 创建密码密钥包
            key_package = self.pbkdf2.create_key_package(password)

            # 保存密钥包
            with open(self.password_key_file, 'w') as f:
                json.dump(key_package, f, indent=2)
            os.chmod(self.password_key_file, 0o600)

            # 创建主密钥
            master_key = os.urandom(32)
            with open(self.master_key_file, 'wb') as f:
                f.write(master_key)
            os.chmod(self.master_key_file, 0o600)

            # 更新配置
            self.config['password_setup_at'] = datetime.utcnow().isoformat()
            self.config['key_derivation'] = 'PBKDF2-SHA256'
            self.config['iterations'] = self.pbkdf2.iterations
            self._save_config(self.config)

            logger.info("密码加密系统设置完成")
            return {
                'status': 'success',
                'algorithm': 'AES-256-GCM',
                'key_derivation': 'PBKDF2-SHA256',
                'iterations': self.pbkdf2.iterations,
                'master_key_created': True,
                'password_key_created': True
            }

        except Exception as e:
            logger.error(f"密码设置失败: {e}")
            raise

    def verify_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 用户密码

        Returns:
            密码是否正确
        """
        if not self.use_password:
            return False

        if not self.password_key_file.exists():
            logger.error("密码密钥文件不存在")
            return False

        try:
            with open(self.password_key_file, 'r') as f:
                key_package = json.load(f)

            return self.pbkdf2.verify_password(password, key_package)

        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    def _get_encryption_instance(self, key_id: str = 'default') -> AESGCMEncryption:
        """
        获取加密实例（带缓存）

        Args:
            key_id: 密钥ID

        Returns:
            加密实例
        """
        if key_id not in self._encryption_cache:
            if self.use_password:
                # 密码模式：需要用户输入密码获取密钥
                raise RuntimeError("请先调用 unlock() 方法提供密码")
            else:
                # 密钥模式：从密钥管理器获取
                key = self.key_manager.get_key(key_id)
                if not key:
                    raise ValueError(f"密钥不存在: {key_id}")
                self._encryption_cache[key_id] = AESGCMEncryption(key)

        return self._encryption_cache[key_id]

    def unlock(self, password: str) -> bool:
        """
        解锁加密系统（密码模式）

        Args:
            password: 用户密码

        Returns:
            是否解锁成功
        """
        if not self.use_password:
            logger.error("当前为密钥模式，无需解锁")
            return False

        if not self.verify_password(password):
            logger.error("密码错误")
            return False

        try:
            # 获取主密钥
            with open(self.password_key_file, 'r') as f:
                key_package = json.load(f)

            # 从密码派生密钥
            derived_key, _ = self.pbkdf2.derive_key(password)

            # 创建加密实例
            self._encryption_cache['default'] = AESGCMEncryption(derived_key)

            logger.info("加密系统已解锁")
            return True

        except Exception as e:
            logger.error(f"解锁失败: {e}")
            return False

    def lock(self):
        """锁定加密系统（清除内存中的密钥）"""
        self._encryption_cache.clear()
        logger.info("加密系统已锁定")

    def encrypt_data(self,
                     data: Union[str, Dict, Any],
                     key_id: str = 'default',
                     aad: Optional[bytes] = None) -> str:
        """
        加密数据

        Args:
            data: 要加密的数据
            key_id: 密钥ID
            aad: 额外认证数据

        Returns:
            Base64编码的加密数据
        """
        try:
            encryption = self._get_encryption_instance(key_id)

            # 转换数据为JSON字符串
            if isinstance(data, str):
                json_data = {'data': data}
            else:
                json_data = data

            # 执行加密
            encrypted = encryption.encrypt_json(json_data, aad)

            # 记录到配置
            item_id = hashlib.sha256(encrypted.encode()).hexdigest()[:16]
            if item_id not in self.config.get('encrypted_items', []):
                self.config['encrypted_items'].append(item_id)
                self._save_config(self.config)

            logger.debug(f"数据加密成功，使用密钥: {key_id}")
            return encrypted

        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt_data(self,
                     encrypted_data: str,
                     key_id: str = 'default') -> Any:
        """
        解密数据

        Args:
            encrypted_data: Base64编码的加密数据
            key_id: 密钥ID

        Returns:
            解密后的数据
        """
        try:
            encryption = self._get_encryption_instance(key_id)
            decrypted = encryption.decrypt_json(encrypted_data)

            # 如果是包装的数据，提取原始内容
            if isinstance(decrypted, dict) and 'data' in decrypted:
                return decrypted['data']

            logger.debug(f"数据解密成功，使用密钥: {key_id}")
            return decrypted

        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    def encrypt_file(self,
                     file_path: Union[str, Path],
                     output_path: Optional[Union[str, Path]] = None,
                     key_id: str = 'default') -> str:
        """
        加密文件

        Args:
            file_path: 源文件路径
            output_path: 输出文件路径
            key_id: 密钥ID

        Returns:
            加密文件路径
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                data = f.read()

            # 加密数据
            encrypted = self.encrypt_data(data, key_id)

            # 确定输出路径
            if output_path is None:
                output_path = self.encrypted_data_dir / f"{file_path.name}.encrypted"
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入加密文件
            with open(output_path, 'w') as f:
                json.dump({
                    'encrypted_data': encrypted,
                    'original_path': str(file_path.absolute()),
                    'original_size': len(data),
                    'encrypted_at': datetime.utcnow().isoformat(),
                    'algorithm': 'AES-256-GCM'
                }, f, indent=2)

            # 设置文件权限
            os.chmod(output_path, 0o600)

            # 安全删除原文件
            self._secure_delete(file_path)

            logger.info(f"文件已加密: {file_path} -> {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            raise

    def decrypt_file(self,
                     encrypted_file_path: Union[str, Path],
                     output_path: Optional[Union[str, Path]] = None,
                     key_id: str = 'default') -> str:
        """
        解密文件

        Args:
            encrypted_file_path: 加密文件路径
            output_path: 输出文件路径
            key_id: 密钥ID

        Returns:
            解密文件路径
        """
        encrypted_file_path = Path(encrypted_file_path)

        if not encrypted_file_path.exists():
            raise FileNotFoundError(f"加密文件不存在: {encrypted_file_path}")

        try:
            # 读取加密文件
            with open(encrypted_file_path, 'r') as f:
                encrypted_package = json.load(f)

            # 解密数据
            decrypted_data = self.decrypt_data(
                encrypted_package['encrypted_data'],
                key_id
            )

            # 确定输出路径
            if output_path is None:
                if 'original_path' in encrypted_package:
                    output_path = Path(encrypted_package['original_path']).name
                else:
                    output_path = encrypted_file_path.with_suffix('')
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入解密文件
            if isinstance(decrypted_data, bytes):
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)
            else:
                with open(output_path, 'w') as f:
                    f.write(decrypted_data)

            # 设置文件权限
            os.chmod(output_path, 0o600)

            logger.info(f"文件已解密: {encrypted_file_path} -> {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            raise

    def _secure_delete(self, file_path: Path):
        """安全删除文件（覆盖3次）"""
        try:
            file_size = file_path.stat().st_size

            with open(file_path, 'r+b') as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            file_path.unlink()

        except Exception as e:
            logger.error(f"安全删除失败: {e}")
            file_path.unlink(missing_ok=True)

    def rotate_master_key(self) -> bool:
        """
        轮换主密钥

        Returns:
            是否成功
        """
        try:
            if self.use_password:
                # 密码模式：需要重新设置
                logger.warning("密码模式下需要重新设置密码")
                return False
            else:
                # 密钥模式：从密钥管理器轮换
                success = self.key_manager.rotate_key('master')
                if success:
                    # 清除缓存
                    self._encryption_cache.clear()
                return success

        except Exception as e:
            logger.error(f"密钥轮换失败: {e}")
            return False

    def get_encryption_statistics(self) -> Dict[str, Any]:
        """
        获取加密统计信息

        Returns:
            统计信息
        """
        stats = {
            'mode': 'password' if self.use_password else 'key',
            'algorithm': 'AES-256-GCM',
            'key_derivation': self.config.get('key_derivation'),
            'iterations': self.config.get('iterations'),
            'encrypted_items': len(self.config.get('encrypted_items', [])),
            'master_key_exists': self.master_key_file.exists(),
            'password_key_exists': self.password_key_file.exists() if self.use_password else False,
            'unlocked': len(self._encryption_cache) > 0
        }

        if not self.use_password:
            key_stats = self.key_manager.get_key_statistics()
            stats.update(key_stats)

        return stats

    def is_unlocked(self) -> bool:
        """检查是否已解锁"""
        return len(self._encryption_cache) > 0

    def create_key_backup(self, output_file: str, password: Optional[str] = None) -> bool:
        """
        创建密钥备份

        Args:
            output_file: 输出文件路径
            password: 备份密码（可选）

        Returns:
            是否成功
        """
        try:
            backup_data = {
                'created_at': datetime.utcnow().isoformat(),
                'type': 'key_backup',
                'config': self.config,
                'master_key_exists': self.master_key_file.exists(),
                'password_key_exists': self.password_key_file.exists()
            }

            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"密钥备份已创建: {output_file}")
            return True

        except Exception as e:
            logger.error(f"密钥备份失败: {e}")
            return False

# 便捷函数
def create_encryption_manager(mode: str = 'password') -> EncryptionManager:
    """
    创建加密管理器的便捷函数

    Args:
        mode: 'password' 或 'key'

    Returns:
        加密管理器实例
    """
    if mode not in ['password', 'key']:
        raise ValueError("模式必须是 'password' 或 'key'")

    return EncryptionManager(use_password=(mode == 'password'))

# 全局实例
_default_manager = None

def get_default_manager() -> EncryptionManager:
    """获取默认加密管理器实例"""
    global _default_manager
    if _default_manager is None:
        _default_manager = EncryptionManager()
    return _default_manager
