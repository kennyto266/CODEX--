"""
隱私保護備份系統
本地加密備份，確保數據安全
"""

import os
import json
import shutil
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import tarfile

from encryption import AESGCM256
from encryption.encrypted_fs import EncryptedFileSystem

logger = logging.getLogger('quant_system.privacy')

# 簡單的加密包裝器
class SimpleEncryption:
    def __init__(self, key: Optional[bytes] = None):
        self.aes = AESGCM256()
        self.key = key or self.aes.generate_key()

    def encrypt(self, data: bytes) -> Dict[str, Any]:
        return self.aes.encrypt(data, self.key)

    def decrypt(self, encrypted: Dict[str, Any]) -> bytes:
        return self.aes.decrypt(encrypted, self.key)

class PrivacyBackupManager:
    """
    隱私備份管理器
    創建和管理本地加密備份
    """

    def __init__(self,
                 backup_dir: str = 'backups/encrypted',
                 master_key: Optional[bytes] = None):
        """
        初始化備份管理器

        Args:
            backup_dir: 備份目錄
            master_key: 主密鑰
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 初始化加密
        self.encryption = SimpleEncryption(master_key)

        # 備份元數據文件
        self.metadata_file = self.backup_dir / 'backup_metadata.json'

        # 加載元數據
        self.metadata = self._load_metadata()

        # 保留策略
        self.retention_days = 30  # 默認保留30天
        self.max_backups = 10     # 最多保留10個備份

        # 加密文件系統
        self.encrypted_fs = EncryptedFileSystem(
            root_dir=str(self.backup_dir / 'encrypted_data'),
            master_key=master_key
        )

        logger.info(f"隱私備份管理器已初始化，目錄: {self.backup_dir}")

    def _load_metadata(self) -> Dict[str, Any]:
        """加載備份元數據"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加載備份元數據失敗: {e}")

        return {
            'backups': {},
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

    def _save_metadata(self):
        """保存備份元數據"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            os.chmod(self.metadata_file, 0o600)
        except Exception as e:
            logger.error(f"保存備份元數據失敗: {e}")
            raise

    def create_backup(self,
                     source_paths: List[str],
                     backup_name: Optional[str] = None,
                     compression: bool = True,
                     encrypt: bool = True) -> str:
        """
        創建備份

        Args:
            source_paths: 源路徑列表
            backup_name: 備份名稱（可選）
            compression: 是否壓縮
            encrypt: 是否加密

        Returns:
            備份ID
        """
        import secrets

        # 生成備份ID
        if backup_name is None:
            backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        else:
            backup_id = backup_name

        backup_dir = self.backup_dir / backup_id
        backup_dir.mkdir(exist_ok=True)

        logger.info(f"開始創建備份: {backup_id}")

        try:
            # 準備備份數據
            backup_data = {
                'backup_id': backup_id,
                'created_at': datetime.utcnow().isoformat(),
                'source_paths': source_paths,
                'compressed': compression,
                'encrypted': encrypt,
                'total_size': 0,
                'file_count': 0,
                'files': []
            }

            # 處理每個源路徑
            for source_path in source_paths:
                source = Path(source_path)
                if not source.exists():
                    logger.warning(f"源路徑不存在: {source_path}")
                    continue

                if source.is_file():
                    files_to_backup = [source]
                else:
                    files_to_backup = [p for p in source.rglob('*') if p.is_file()]

                for file_path in files_to_backup:
                    # 計算相對路徑
                    rel_path = file_path.relative_to(source) if source.is_dir() else file_path.name

                    # 讀取文件數據
                    with open(file_path, 'rb') as f:
                        file_data = f.read()

                    backup_data['total_size'] += len(file_data)
                    backup_data['file_count'] += 1

                    # 壓縮
                    if compression:
                        file_data = gzip.compress(file_data)

                    # 加密
                    if encrypt:
                        encrypted = self.encryption.encrypt(file_data)
                        file_data = json.dumps(encrypted).encode('utf-8')

                    # 保存文件
                    file_backup_path = backup_dir / f"{file_path.name}.{'gz' if compression else ''}{'.enc' if encrypt else ''}"
                    with open(file_backup_path, 'wb') as f:
                        f.write(file_data)

                    # 記錄文件信息
                    backup_data['files'].append({
                        'original_path': str(file_path),
                        'backup_path': str(file_backup_path),
                        'relative_path': str(rel_path),
                        'size': len(file_data),
                        'compressed': compression,
                        'encrypted': encrypt
                    })

            # 保存元數據
            metadata_file = backup_dir / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(backup_data, f, indent=2)

            # 更新主元數據
            self.metadata['backups'][backup_id] = {
                'id': backup_id,
                'path': str(backup_dir),
                'created_at': backup_data['created_at'],
                'source_paths': source_paths,
                'size': backup_data['total_size'],
                'file_count': backup_data['file_count'],
                'compressed': compression,
                'encrypted': encrypt
            }
            self._save_metadata()

            # 執行清理策略
            self._apply_retention_policy()

            logger.info(f"備份創建完成: {backup_id}, "
                       f"文件數: {backup_data['file_count']}, "
                       f"大小: {backup_data['total_size']} 字節")
            return backup_id

        except Exception as e:
            logger.error(f"創建備份失敗: {e}")
            # 清理失敗的備份
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            raise

    def restore_backup(self,
                      backup_id: str,
                      target_dir: str,
                      overwrite: bool = False) -> bool:
        """
        恢復備份

        Args:
            backup_id: 備份ID
            target_dir: 目標目錄
            overwrite: 是否覆蓋

        Returns:
            是否成功
        """
        if backup_id not in self.metadata['backups']:
            logger.error(f"備份不存在: {backup_id}")
            return False

        backup_info = self.metadata['backups'][backup_id]
        backup_dir = Path(backup_info['path'])
        target_path = Path(target_dir)

        if target_path.exists() and not overwrite:
            logger.error(f"目標目錄已存在: {target_dir}")
            return False

        logger.info(f"開始恢復備份: {backup_id}")

        try:
            # 讀取元數據
            metadata_file = backup_dir / 'metadata.json'
            with open(metadata_file, 'r') as f:
                backup_data = json.load(f)

            # 創建目標目錄
            target_path.mkdir(parents=True, exist_ok=True)

            # 恢復每個文件
            for file_info in backup_data['files']:
                backup_file_path = Path(file_info['backup_path'])
                target_file_path = target_path / file_info['relative_path']

                # 確保目標目錄存在
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                # 讀取備份文件
                with open(backup_file_path, 'rb') as f:
                    file_data = f.read()

                # 解密
                if backup_data['encrypted']:
                    encrypted_data = json.loads(file_data.decode('utf-8'))
                    file_data = self.encryption.decrypt(encrypted_data)

                # 解壓
                if backup_data['compressed']:
                    file_data = gzip.decompress(file_data)

                # 寫入目標文件
                with open(target_file_path, 'wb') as f:
                    f.write(file_data)

            logger.info(f"備份恢復完成: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"恢復備份失敗: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有備份"""
        return list(self.metadata['backups'].values())

    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """獲取備份信息"""
        if backup_id not in self.metadata['backups']:
            return None

        backup_info = self.metadata['backups'][backup_id]
        backup_dir = Path(backup_info['path'])
        metadata_file = backup_dir / 'metadata.json'

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                detailed_info = json.load(f)
                backup_info.update(detailed_info)

        return backup_info

    def delete_backup(self, backup_id: str) -> bool:
        """
        刪除備份

        Args:
            backup_id: 備份ID

        Returns:
            是否成功
        """
        if backup_id not in self.metadata['backups']:
            logger.error(f"備份不存在: {backup_id}")
            return False

        try:
            backup_info = self.metadata['backups'][backup_id]
            backup_dir = Path(backup_info['path'])

            # 安全刪除
            self._secure_delete_directory(backup_dir)

            # 從元數據中移除
            del self.metadata['backups'][backup_id]
            self._save_metadata()

            logger.info(f"備份已刪除: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"刪除備份失敗: {e}")
            return False

    def _secure_delete_directory(self, directory: Path):
        """安全刪除目錄"""
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                # 覆蓋文件
                file_size = file_path.stat().st_size
                with open(file_path, 'r+b') as f:
                    for _ in range(3):
                        f.seek(0)
                        f.write(os.urandom(file_size))
                        f.flush()
                        os.fsync(f.fileno())
                os.remove(file_path)

        # 刪除空目錄
        shutil.rmtree(directory)

    def _apply_retention_policy(self):
        """應用保留策略"""
        # 按時間排序備份
        backups = sorted(
            self.metadata['backups'].values(),
            key=lambda x: x['created_at'],
            reverse=True
        )

        # 刪除超出的備份
        if len(backups) > self.max_backups:
            for backup in backups[self.max_backups:]:
                self.delete_backup(backup['id'])

        # 刪除過期的備份
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['created_at'])
            if backup_date < cutoff_date:
                self.delete_backup(backup['id'])

        logger.debug("保留策略已應用")

    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        驗證備份完整性

        Args:
            backup_id: 備份ID

        Returns:
            驗證結果
        """
        if backup_id not in self.metadata['backups']:
            return {'valid': False, 'error': '備份不存在'}

        backup_info = self.metadata['backups'][backup_id]
        backup_dir = Path(backup_info['path'])
        metadata_file = backup_dir / 'metadata.json'

        result = {
            'backup_id': backup_id,
            'valid': True,
            'errors': []
        }

        try:
            # 檢查元數據文件
            if not metadata_file.exists():
                result['valid'] = False
                result['errors'].append('元數據文件不存在')
                return result

            # 讀取元數據
            with open(metadata_file, 'r') as f:
                backup_data = json.load(f)

            # 驗證每個文件
            for file_info in backup_data['files']:
                backup_file_path = Path(file_info['backup_path'])
                if not backup_file_path.exists():
                    result['valid'] = False
                    result['errors'].append(f"備份文件不存在: {backup_file_path}")
                    continue

                # 嘗試解密/解壓（如果需要）
                try:
                    with open(backup_file_path, 'rb') as f:
                        file_data = f.read()

                    if backup_data['encrypted']:
                        encrypted_data = json.loads(file_data.decode('utf-8'))
                        self.encryption.decrypt(encrypted_data)

                    if backup_data['compressed']:
                        if backup_data['encrypted']:
                            encrypted_data = json.loads(file_data.decode('utf-8'))
                            file_data = self.encryption.decrypt(encrypted_data)
                        gzip.decompress(file_data)

                except Exception as e:
                    result['valid'] = False
                    result['errors'].append(f"文件損壞 {backup_file_path}: {e}")

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"驗證過程中發生錯誤: {e}")

        logger.info(f"備份驗證完成: {backup_id}, 有效: {result['valid']}")
        return result

    def create_full_system_backup(self) -> str:
        """
        創建完整系統備份

        Returns:
            備份ID
        """
        # 系統關鍵路徑
        system_paths = [
            'config',
            'data',
            'keys',
            'logs',
            'src/encryption',
            'src/privacy',
            'src/security.py',
            '.env'
        ]

        # 過濾存在的路徑
        existing_paths = [p for p in system_paths if Path(p).exists()]

        logger.info(f"創建完整系統備份，{len(existing_paths)} 個路徑")
        return self.create_backup(
            source_paths=existing_paths,
            backup_name=f"full_system_backup_{datetime.utcnow().strftime('%Y%m%d')}",
            compression=True,
            encrypt=True
        )

    def get_backup_statistics(self) -> Dict[str, Any]:
        """獲取備份統計"""
        backups = list(self.metadata['backups'].values())
        if not backups:
            return {'message': '無備份'}

        total_size = sum(b['size'] for b in backups)
        total_files = sum(b['file_count'] for b in backups)

        return {
            'total_backups': len(backups),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_files': total_files,
            'oldest_backup': min(b['created_at'] for b in backups),
            'newest_backup': max(b['created_at'] for b in backups),
            'encrypted_backups': sum(1 for b in backups if b.get('encrypted', False)),
            'compressed_backups': sum(1 for b in backups if b.get('compressed', False))
        }
