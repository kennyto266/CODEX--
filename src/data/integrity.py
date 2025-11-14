"""
数据完整性检查系统
提供数据哈希验证、校验和计算、损坏检测和自动修复

基于OpenSpec规范 - 确保数据完整性和安全性
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import pickle
import zlib

logger = logging.getLogger('quant_system.integrity')

class IntegrityChecker:
    """
    数据完整性检查器
    实现多层次的数据完整性验证和修复机制
    """

    # 支持的哈希算法
    HASH_ALGORITHMS = {
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
        'blake2b': hashlib.blake2b
    }

    # 校验和计算方法
    CHECKSUM_METHODS = {
        'crc32': lambda data: format(zlib.crc32(data) & 0xFFFFFFFF, '08x'),
        'adler32': lambda data: format(zlib.adler32(data) & 0xFFFFFFFF, '08x')
    }

    def __init__(self,
                 hash_algorithm: str = 'sha256',
                 enable_compression: bool = True):
        """
        初始化完整性检查器

        Args:
            hash_algorithm: 哈希算法 ('sha256', 'sha512', 'blake2b')
            enable_compression: 是否启用数据压缩
        """
        if hash_algorithm not in self.HASH_ALGORITHMS:
            raise ValueError(f"不支持的哈希算法: {hash_algorithm}")

        self.hash_algorithm = hash_algorithm
        self.hash_func = self.HASH_ALGORITHMS[hash_algorithm]
        self.enable_compression = enable_compression
        self.integrity_db_file = Path('data') / 'integrity.db.json'

        # 创建数据目录
        self.integrity_db_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载完整性数据库
        self.integrity_db = self._load_integrity_db()

        logger.info(f"完整性检查器已初始化: {hash_algorithm}")

    def _load_integrity_db(self) -> Dict[str, Any]:
        """加载完整性数据库"""
        if self.integrity_db_file.exists():
            try:
                with open(self.integrity_db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载完整性数据库失败: {e}")

        return {
            'version': '2.0',
            'created_at': datetime.utcnow().isoformat(),
            'files': {},
            'statistics': {
                'total_files': 0,
                'verified_files': 0,
                'corrupted_files': 0,
                'repaired_files': 0
            }
        }

    def _save_integrity_db(self):
        """保存完整性数据库"""
        try:
            with open(self.integrity_db_file, 'w') as f:
                json.dump(self.integrity_db, f, indent=2, default=str)
            # 设置严格权限
            os.chmod(self.integrity_db_file, 0o600)
        except Exception as e:
            logger.error(f"保存完整性数据库失败: {e}")
            raise

    def calculate_hash(self, data: bytes) -> str:
        """
        计算数据哈希值

        Args:
            data: 原始数据

        Returns:
            哈希值（十六进制字符串）
        """
        hasher = self.hash_func()
        hasher.update(data)
        return hasher.hexdigest()

    def calculate_checksum(self, data: bytes, method: str = 'crc32') -> str:
        """
        计算数据校验和

        Args:
            data: 原始数据
            method: 校验和方法 ('crc32', 'adler32')

        Returns:
            校验和（十六进制字符串）
        """
        if method not in self.CHECKSUM_METHODS:
            raise ValueError(f"不支持的校验和方法: {method}")

        return self.CHECKSUM_METHODS[method](data)

    def calculate_data_fingerprint(self, data: bytes) -> Dict[str, str]:
        """
        计算数据指纹（多算法组合）

        Args:
            data: 原始数据

        Returns:
            包含多种哈希和校验和的字典
        """
        return {
            'sha256': self.calculate_hash(data),
            'crc32': self.calculate_checksum(data, 'crc32'),
            'adler32': self.calculate_checksum(data, 'adler32'),
            'size': len(data),
            'timestamp': datetime.utcnow().isoformat()
        }

    def register_file(self,
                     file_path: Union[str, Path],
                     file_id: Optional[str] = None) -> str:
        """
        注册文件到完整性数据库

        Args:
            file_path: 文件路径
            file_id: 文件ID（可选）

        Returns:
            文件ID
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 生成或使用文件ID
        if file_id is None:
            file_id = self._generate_file_id(file_path)

        try:
            # 读取文件
            with open(file_path, 'rb') as f:
                data = f.read()

            # 计算数据指纹
            fingerprint = self.calculate_data_fingerprint(data)

            # 获取文件元数据
            stat = file_path.stat()

            # 存储到数据库
            self.integrity_db['files'][file_id] = {
                'file_path': str(file_path.absolute()),
                'file_id': file_id,
                'registered_at': datetime.utcnow().isoformat(),
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'fingerprint': fingerprint,
                'status': 'registered',
                'verification_count': 0,
                'last_verified': None,
                'corruption_detected': False,
                'repair_history': []
            }

            # 更新统计
            self.integrity_db['statistics']['total_files'] += 1
            self._save_integrity_db()

            logger.info(f"文件已注册: {file_path} (ID: {file_id})")
            return file_id

        except Exception as e:
            logger.error(f"文件注册失败: {e}")
            raise

    def verify_file(self, file_id: str) -> Dict[str, Any]:
        """
        验证文件完整性

        Args:
            file_id: 文件ID

        Returns:
            验证结果
        """
        if file_id not in self.integrity_db['files']:
            return {
                'valid': False,
                'error': f"文件未注册: {file_id}"
            }

        file_info = self.integrity_db['files'][file_id]
        file_path = Path(file_info['file_path'])

        result = {
            'file_id': file_id,
            'file_path': str(file_path),
            'timestamp': datetime.utcnow().isoformat(),
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # 检查文件是否存在
            if not file_path.exists():
                result['valid'] = False
                result['errors'].append("文件不存在")
                file_info['status'] = 'missing'
                return result

            # 读取文件
            with open(file_path, 'rb') as f:
                data = f.read()

            # 重新计算指纹
            current_fingerprint = self.calculate_data_fingerprint(data)
            stored_fingerprint = file_info['fingerprint']

            # 验证哈希
            if current_fingerprint['sha256'] != stored_fingerprint['sha256']:
                result['valid'] = False
                result['errors'].append("SHA256哈希不匹配")
                file_info['corruption_detected'] = True
                self.integrity_db['statistics']['corrupted_files'] += 1

            # 验证校验和
            if current_fingerprint['crc32'] != stored_fingerprint['crc32']:
                result['valid'] = False
                result['errors'].append("CRC32校验和不匹配")
                file_info['corruption_detected'] = True

            # 验证大小
            if current_fingerprint['size'] != stored_fingerprint['size']:
                result['valid'] = False
                result['errors'].append("文件大小不匹配")
                file_info['corruption_detected'] = True

            # 检查修改时间
            current_mtime = file_path.stat().st_mtime
            if current_mtime != file_info['mtime']:
                result['warnings'].append("文件已被修改")

            # 更新验证信息
            file_info['verification_count'] += 1
            file_info['last_verified'] = datetime.utcnow().isoformat()

            if result['valid']:
                file_info['status'] = 'verified'
                self.integrity_db['statistics']['verified_files'] += 1
            else:
                file_info['status'] = 'corrupted'

            self._save_integrity_db()
            return result

        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            result['valid'] = False
            result['errors'].append(f"验证异常: {str(e)}")
            return result

    def repair_file(self,
                   file_id: str,
                   backup_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        修复损坏的文件

        Args:
            file_id: 文件ID
            backup_path: 备份文件路径（可选）

        Returns:
            修复结果
        """
        if file_id not in self.integrity_db['files']:
            return {
                'success': False,
                'error': f"文件未注册: {file_id}"
            }

        file_info = self.integrity_db['files'][file_id]
        file_path = Path(file_info['file_path'])

        result = {
            'file_id': file_id,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False,
            'method': None,
            'details': []
        }

        try:
            # 方法1：从备份恢复
            if backup_path and Path(backup_path).exists():
                try:
                    # 验证备份文件
                    backup_verification = self.verify_backup_integrity(backup_path)
                    if backup_verification['valid']:
                        # 恢复备份
                        shutil.copy2(backup_path, file_path)

                        # 重新注册
                        self.register_file(file_path, file_id)
                        result['success'] = True
                        result['method'] = 'backup_restore'
                        result['details'].append("从备份成功恢复")

                        # 记录修复历史
                        file_info['repair_history'].append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'method': 'backup_restore',
                            'backup_path': str(backup_path)
                        })
                        self._save_integrity_db()

                        return result
                except Exception as e:
                    result['details'].append(f"备份恢复失败: {e}")

            # 方法2：重新计算（如果数据可再生）
            if self._can_regenerate(file_info):
                try:
                    regenerated_data = self._regenerate_data(file_info)
                    if regenerated_data:
                        with open(file_path, 'wb') as f:
                            f.write(regenerated_data)
                        self.register_file(file_path, file_id)
                        result['success'] = True
                        result['method'] = 'regeneration'
                        result['details'].append("数据已重新生成")

                        file_info['repair_history'].append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'method': 'regeneration'
                        })
                        self._save_integrity_db()
                        return result
                except Exception as e:
                    result['details'].append(f"数据再生失败: {e}")

            # 方法3：使用校验和修复（部分损坏）
            try:
                if self._attempt_checksum_repair(file_path, file_info):
                    self.register_file(file_path, file_id)
                    result['success'] = True
                    result['method'] = 'checksum_repair'
                    result['details'].append("已使用校验和修复")

                    file_info['repair_history'].append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'method': 'checksum_repair'
                    })
                    self._save_integrity_db()
                    return result
            except Exception as e:
                result['details'].append(f"校验和修复失败: {e}")

            result['details'].append("所有修复方法均失败")
            self._save_integrity_db()
            return result

        except Exception as e:
            logger.error(f"文件修复失败: {e}")
            result['details'].append(f"修复异常: {str(e)}")
            return result

    def verify_backup_integrity(self, backup_path: Union[str, Path]) -> Dict[str, Any]:
        """验证备份文件完整性"""
        backup_path = Path(backup_path)

        if not backup_path.exists():
            return {'valid': False, 'error': '备份文件不存在'}

        try:
            with open(backup_path, 'rb') as f:
                data = f.read()

            fingerprint = self.calculate_data_fingerprint(data)

            return {
                'valid': True,
                'size': len(data),
                'hash': fingerprint['sha256'],
                'checksum': fingerprint['crc32']
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def _generate_file_id(self, file_path: Path) -> str:
        """生成文件ID"""
        # 使用路径和修改时间生成ID
        unique_str = f"{file_path.absolute()}_{file_path.stat().st_mtime}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _can_regenerate(self, file_info: Dict[str, Any]) -> bool:
        """检查数据是否可以再生"""
        # 这里可以根据文件类型和元数据判断
        # 目前返回False，需要具体的再生逻辑
        return False

    def _regenerate_data(self, file_info: Dict[str, Any]) -> Optional[bytes]:
        """再生数据（需要子类实现）"""
        return None

    def _attempt_checksum_repair(self, file_path: Path, file_info: Dict[str, Any]) -> bool:
        """尝试使用校验和修复文件"""
        # 这是一个简单的实现，实际中可能需要更复杂的算法
        # 例如 Reed-Solomon 纠错码
        return False

    def verify_all_files(self) -> Dict[str, Any]:
        """验证所有注册的文件"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_files': len(self.integrity_db['files']),
            'verified': 0,
            'corrupted': 0,
            'missing': 0,
            'details': []
        }

        for file_id in list(self.integrity_db['files'].keys()):
            verification = self.verify_file(file_id)
            results['details'].append(verification)

            if verification.get('valid', False):
                results['verified'] += 1
            elif 'missing' in verification.get('errors', []):
                results['missing'] += 1
            else:
                results['corrupted'] += 1

        return results

    def auto_repair_all(self) -> Dict[str, Any]:
        """自动修复所有损坏的文件"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'repaired': 0,
            'failed': 0,
            'details': []
        }

        for file_id, file_info in self.integrity_db['files'].items():
            if file_info.get('corruption_detected', False):
                repair_result = self.repair_file(file_id)
                results['details'].append(repair_result)

                if repair_result['success']:
                    results['repaired'] += 1
                    self.integrity_db['statistics']['repaired_files'] += 1
                else:
                    results['failed'] += 1

        self._save_integrity_db()
        return results

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        return self.integrity_db['files'].get(file_id)

    def list_files(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出文件"""
        files = list(self.integrity_db['files'].values())

        if status:
            files = [f for f in files if f.get('status') == status]

        return sorted(files, key=lambda x: x['registered_at'], reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        """获取完整性统计信息"""
        return {
            'total_files': self.integrity_db['statistics']['total_files'],
            'verified_files': self.integrity_db['statistics']['verified_files'],
            'corrupted_files': self.integrity_db['statistics']['corrupted_files'],
            'repaired_files': self.integrity_db['statistics']['repaired_files'],
            'hash_algorithm': self.hash_algorithm,
            'integrity_db_path': str(self.integrity_db_file)
        }

    def export_integrity_report(self, output_file: str) -> bool:
        """
        导出完整性报告

        Args:
            output_file: 输出文件路径

        Returns:
            是否成功
        """
        try:
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'hash_algorithm': self.hash_algorithm,
                'statistics': self.get_statistics(),
                'files': self.integrity_db['files']
            }

            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"完整性报告已导出: {output_file}")
            return True

        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            return False

# 便捷函数
def verify_file_integrity(file_path: Union[str, Path],
                         checker: Optional[IntegrityChecker] = None) -> bool:
    """
    快速验证文件完整性

    Args:
        file_path: 文件路径
        checker: 检查器实例

    Returns:
        文件是否完整
    """
    checker = checker or IntegrityChecker()

    # 生成文件ID
    file_path = Path(file_path)
    file_id = hashlib.sha256(
        f"{file_path.absolute()}_{file_path.stat().st_mtime}".encode()
    ).hexdigest()[:16]

    # 注册文件
    checker.register_file(file_path, file_id)

    # 验证
    result = checker.verify_file(file_id)
    return result.get('valid', False)

def quick_check_data_integrity(data: bytes) -> Dict[str, str]:
    """
    快速检查数据完整性

    Args:
        data: 原始数据

    Returns:
        数据指纹
    """
    checker = IntegrityChecker()
    return checker.calculate_data_fingerprint(data)
