"""
密鑰管理器
管理密鑰的生成、存儲、輪換和銷毀
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from .aes_gcm import AESGCMEncryption
from .key_derivation import PBKDF2KeyDerivation, ScryptKeyDerivation

logger = logging.getLogger('quant_system.privacy')

class KeyManager:
    """
    密鑰管理器
    實現密鑰的完整生命週期管理
    """

    def __init__(self, keys_dir: str = 'keys'):
        """
        初始化密鑰管理器

        Args:
            keys_dir: 密鑰存儲目錄
        """
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(mode=0o700, exist_ok=True)
        self.metadata_file = self.keys_dir / 'keys_metadata.json'
        self.rotation_schedule_file = self.keys_dir / 'rotation_schedule.json'

        # 密鑰元數據
        self.metadata = self._load_metadata()

        # 密鑰輪換配置
        self.rotation_interval_days = 90  # 90天輪換一次
        self.rotation_warning_days = 7   # 提前7天警告

        logger.info("密鑰管理器已初始化")

    def _load_metadata(self) -> Dict[str, Any]:
        """加載密鑰元數據"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加載密鑰元數據失敗: {e}")

        return {
            'keys': {},
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0'
        }

    def _save_metadata(self):
        """保存密鑰元數據"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            # 設置嚴格權限
            os.chmod(self.metadata_file, 0o600)
        except Exception as e:
            logger.error(f"保存密鑰元數據失敗: {e}")
            raise

    def generate_master_key(self, key_id: str, description: str = "") -> Dict[str, Any]:
        """
        生成主密鑰

        Args:
            key_id: 密鑰ID
            description: 密鑰描述

        Returns:
            密鑰信息字典
        """
        # 生成新密鑰
        key = os.urandom(32)
        key_file = self.keys_dir / f"{key_id}.key"

        # 保存密鑰
        with open(key_file, 'wb') as f:
            f.write(key)
        os.chmod(key_file, 0o600)

        # 記錄元數據
        self.metadata['keys'][key_id] = {
            'id': key_id,
            'file': str(key_file),
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None,
            'last_rotated': None,
            'rotation_count': 0,
            'description': description,
            'status': 'active',
            'algorithm': 'AES-256'
        }
        self._save_metadata()

        logger.info(f"主密鑰已生成: {key_id}")
        return self.metadata['keys'][key_id]

    def get_key(self, key_id: str) -> Optional[bytes]:
        """
        獲取密鑰

        Args:
            key_id: 密鑰ID

        Returns:
            密鑰字節串
        """
        if key_id not in self.metadata['keys']:
            logger.error(f"密鑰不存在: {key_id}")
            return None

        key_info = self.metadata['keys'][key_id]
        if key_info['status'] != 'active':
            logger.warning(f"密鑰 {key_id} 狀態非活躍")
            return None

        try:
            with open(key_info['file'], 'rb') as f:
                key = f.read()

            # 更新最後使用時間
            self.metadata['keys'][key_id]['last_used'] = datetime.utcnow().isoformat()
            self._save_metadata()

            return key

        except Exception as e:
            logger.error(f"讀取密鑰失敗: {e}")
            return None

    def rotate_key(self, key_id: str) -> bool:
        """
        輪換密鑰

        Args:
            key_id: 密鑰ID

        Returns:
            是否成功
        """
        if key_id not in self.metadata['keys']:
            logger.error(f"密鑰不存在: {key_id}")
            return False

        try:
            # 生成新密鑰
            new_key = os.urandom(32)
            old_key_file = self.keys_dir / f"{key_id}.key"

            # 備份舊密鑰
            backup_file = self.keys_dir / f"{key_id}.key.backup.{int(time.time())}"
            if old_key_file.exists():
                old_key_file.rename(backup_file)

            # 保存新密鑰
            with open(old_key_file, 'wb') as f:
                f.write(new_key)

            # 更新元數據
            self.metadata['keys'][key_id]['last_rotated'] = datetime.utcnow().isoformat()
            self.metadata['keys'][key_id]['rotation_count'] += 1
            self._save_metadata()

            logger.info(f"密鑰輪換完成: {key_id}")
            return True

        except Exception as e:
            logger.error(f"密鑰輪換失敗: {e}")
            return False

    def revoke_key(self, key_id: str) -> bool:
        """
        撤銷密鑰

        Args:
            key_id: 密鑰ID

        Returns:
            是否成功
        """
        if key_id not in self.metadata['keys']:
            logger.error(f"密鑰不存在: {key_id}")
            return False

        try:
            key_info = self.metadata['keys'][key_id]
            key_file = Path(key_info['file'])

            # 覆蓋並刪除密鑰文件
            if key_file.exists():
                with open(key_file, 'r+b') as f:
                    f.write(os.urandom(os.path.getsize(key_file)))
                os.remove(key_file)

            # 更新元數據
            self.metadata['keys'][key_id]['status'] = 'revoked'
            self.metadata['keys'][key_id]['revoked_at'] = datetime.utcnow().isoformat()
            self._save_metadata()

            logger.warning(f"密鑰已撤銷: {key_id}")
            return True

        except Exception as e:
            logger.error(f"密鑰撤銷失敗: {e}")
            return False

    def list_keys(self) -> List[Dict[str, Any]]:
        """列出所有密鑰"""
        return list(self.metadata['keys'].values())

    def get_rotation_schedule(self) -> List[Dict[str, Any]]:
        """獲取密鑰輪換計劃"""
        schedule = []
        now = datetime.utcnow()

        for key_id, key_info in self.metadata['keys'].items():
            if key_info['status'] != 'active':
                continue

            last_rotated = key_info.get('last_rotated') or key_info['created_at']
            last_rotated_date = datetime.fromisoformat(last_rotated)

            days_since_rotation = (now - last_rotated_date).days
            days_until_rotation = self.rotation_interval_days - days_since_rotation

            if days_until_rotation <= self.rotation_warning_days:
                schedule.append({
                    'key_id': key_id,
                    'last_rotated': last_rotated,
                    'days_since_rotation': days_since_rotation,
                    'days_until_rotation': days_until_rotation,
                    'priority': 'critical' if days_until_rotation <= 0 else 'warning'
                })

        return schedule

    def get_key_statistics(self) -> Dict[str, Any]:
        """獲取密鑰統計信息"""
        keys = self.metadata['keys']
        now = datetime.utcnow()

        stats = {
            'total_keys': len(keys),
            'active_keys': sum(1 for k in keys.values() if k['status'] == 'active'),
            'revoked_keys': sum(1 for k in keys.values() if k['status'] == 'revoked'),
            'keys_to_rotate': len(self.get_rotation_schedule()),
            'oldest_key_age_days': 0,
            'average_rotation_count': 0
        }

        if keys:
            ages = []
            rotation_counts = []

            for key_info in keys.values():
                created = datetime.fromisoformat(key_info['created_at'])
                age_days = (now - created).days
                ages.append(age_days)
                rotation_counts.append(key_info.get('rotation_count', 0))

            stats['oldest_key_age_days'] = max(ages)
            stats['average_rotation_count'] = sum(rotation_counts) / len(rotation_counts)

        return stats

    def export_key_metadata(self, output_file: str):
        """導出密鑰元數據（不包含實際密鑰）"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'metadata': self.metadata
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"密鑰元數據已導出到: {output_file}")
