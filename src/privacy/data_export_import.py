"""
加密數據導入導出系統
安全地導出和導入數據，確保數據安全
"""

import os
import json
import csv
import zipfile
import logging
import hashlib
import tempfile
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd

from encryption import AESGCM256
from .data_flow_audit import DataFlowAuditor, DataFlowType, DataClassification

logger = logging.getLogger('quant_system.privacy')

# 簡單的加密包裝器
class SimpleEncryption:
    def __init__(self, key: Optional[bytes] = None):
        self.aes = AESGCM256()
        self.key = key or self.aes.generate_key()

    def encrypt(self, data: bytes, aad: Optional[bytes] = None) -> Dict[str, Any]:
        return self.aes.encrypt(data, self.key, aad=aad)

    def decrypt(self, encrypted: Dict[str, Any], aad: Optional[bytes] = None) -> bytes:
        return self.aes.decrypt(encrypted, self.key, aad=aad)

class ExportFormat(Enum):
    """導出格式"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PARQUET = "parquet"
    ENCRYPTED = "encrypted"  # 自定義加密格式

class DataCategory(Enum):
    """數據類別"""
    STRATEGY = "strategy"
    PORTFOLIO = "portfolio"
    TRANSACTION = "transaction"
    ANALYSIS = "analysis"
    CONFIG = "config"
    BACKUP = "backup"

@dataclass
class DataPackage:
    """數據包"""
    package_id: str
    created_at: str
    data_type: str
    category: DataCategory
    format: ExportFormat
    encrypted: bool
    compression: bool
    item_count: int
    total_size: int
    checksum: str
    metadata: Dict[str, Any]
    version: str = "1.0"

class EncryptedDataManager:
    """
    加密數據管理器
    負責數據的安全導出和導入
    """

    def __init__(self,
                 export_dir: str = 'export',
                 master_key: Optional[bytes] = None):
        """
        初始化加密數據管理器

        Args:
            export_dir: 導出目錄
            master_key: 主密鑰
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # 初始化加密
        self.encryption = SimpleEncryption()
        self.master_key = master_key or self.encryption.key

        # 審計器
        self.auditor = DataFlowAuditor(str(self.export_dir / 'audit'))

        # 導出元數據
        self.manifest_file = self.export_dir / 'manifest.json'

        # 記錄審計事件
        self.auditor.log_event(
            event_type=DataFlowType.LOCAL_PROCESS,
            source="system",
            destination="data_manager",
            data_type="initialization",
            classification=DataClassification.INTERNAL,
            encrypted=True
        )

        logger.info(f"加密數據管理器已初始化，導出目錄: {self.export_dir}")

    def export_data(self,
                   data: Any,
                   file_name: str,
                   data_type: str,
                   category: DataCategory = DataCategory.ANALYSIS,
                   format: ExportFormat = ExportFormat.JSON,
                   encrypt: bool = True,
                   compress: bool = True,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        導出數據

        Args:
            data: 要導出的數據
            file_name: 文件名
            data_type: 數據類型
            category: 數據類別
            format: 導出格式
            encrypt: 是否加密
            compress: 是否壓縮
            metadata: 元數據

        Returns:
            導出文件路徑
        """
        import secrets

        # 生成包ID
        package_id = f"{file_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

        try:
            # 準備數據
            serialized_data, size = self._serialize_data(data, format)

            # 壓縮
            if compress:
                import gzip
                serialized_data = gzip.compress(serialized_data)

            # 加密
            if encrypt:
                encrypted_package = self.encryption.encrypt(
                    serialized_data,
                    self.master_key,
                    aad=package_id.encode('utf-8')
                )

                # 轉換為JSON格式以便保存
                serialized_data = json.dumps({
                    'iv': encrypted_package['iv'].hex(),
                    'ciphertext': encrypted_package['ciphertext'].hex(),
                    'tag': encrypted_package['tag'].hex()
                }).encode('utf-8')

            # 計算校驗和
            checksum = hashlib.sha256(serialized_data).hexdigest()

            # 保存文件
            output_file = self.export_dir / f"{package_id}.{format.value}"
            with open(output_file, 'wb') as f:
                f.write(serialized_data)

            # 創建數據包
            package = DataPackage(
                package_id=package_id,
                created_at=datetime.utcnow().isoformat(),
                data_type=data_type,
                category=category,
                format=format,
                encrypted=encrypt,
                compression=compress,
                item_count=1,
                total_size=size,
                checksum=checksum,
                metadata=metadata or {}
            )

            # 保存包信息
            self._save_package_info(package)

            # 記錄審計事件
            self.auditor.log_event(
                event_type=DataFlowType.LOCAL_WRITE,
                source="memory:data",
                destination=str(output_file),
                data_type=data_type,
                classification=DataClassification.CONFIDENTIAL,
                size_bytes=size,
                encrypted=encrypt
            )

            logger.info(f"數據已導出: {package_id}, 大小: {size} 字節")
            return str(output_file)

        except Exception as e:
            logger.error(f"導出數據失敗: {e}")
            raise

    def export_batch(self,
                    data_items: List[Dict[str, Any]],
                    batch_name: str,
                    format: ExportFormat = ExportFormat.JSON,
                    encrypt: bool = True,
                    compress: bool = True) -> str:
        """
        批量導出數據

        Args:
            data_items: 數據項列表，每項包含 {data, name, type, category, metadata}
            batch_name: 批次名稱
            format: 導出格式
            encrypt: 是否加密
            compress: 是否壓縮

        Returns:
            導出文件路徑
        """
        import secrets

        # 生成包ID
        batch_id = f"{batch_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

        try:
            total_size = 0
            exported_files = []

            # 導出每個數據項
            for item in data_items:
                file_name = f"{batch_id}_{item['name']}"
                exported_file = self.export_data(
                    data=item['data'],
                    file_name=file_name,
                    data_type=item.get('type', 'unknown'),
                    category=item.get('category', DataCategory.ANALYSIS),
                    format=format,
                    encrypt=encrypt,
                    compress=compress,
                    metadata=item.get('metadata', {})
                )
                exported_files.append(exported_file)
                total_size += Path(exported_file).stat().st_size

            # 創建批次清單
            manifest = {
                'batch_id': batch_id,
                'created_at': datetime.utcnow().isoformat(),
                'item_count': len(data_items),
                'total_size': total_size,
                'format': format.value,
                'encrypted': encrypt,
                'compressed': compress,
                'files': exported_files
            }

            # 保存清單
            manifest_file = self.export_dir / f"{batch_id}_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"批次導出完成: {batch_id}, 包含 {len(data_items)} 項")
            return str(manifest_file)

        except Exception as e:
            logger.error(f"批次導出失敗: {e}")
            raise

    def import_data(self,
                   file_path: str,
                   expected_format: Optional[ExportFormat] = None) -> Any:
        """
        導入數據

        Args:
            file_path: 文件路徑
            expected_format: 預期格式

        Returns:
            導入的數據
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            # 讀取文件
            with open(file_path, 'rb') as f:
                data_bytes = f.read()

            # 獲取包信息
            package_info = self._get_package_info(file_path.stem)

            if not package_info:
                raise ValueError(f"未找到包信息: {file_path.stem}")

            # 解密
            if package_info['encrypted']:
                try:
                    encrypted_data = json.loads(data_bytes.decode('utf-8'))
                    iv = bytes.fromhex(encrypted_data['iv'])
                    ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
                    tag = bytes.fromhex(encrypted_data['tag'])

                    data_bytes = self.encryption.decrypt(
                        {'iv': iv, 'ciphertext': ciphertext, 'tag': tag},
                        self.master_key,
                        aad=package_info['package_id'].encode('utf-8')
                    )
                except Exception as e:
                    logger.error(f"解密失敗: {e}")
                    raise

            # 解壓
            if package_info['compression']:
                import gzip
                data_bytes = gzip.decompress(data_bytes)

            # 反序列化
            data = self._deserialize_data(data_bytes, package_info['format'])

            # 記錄審計事件
            self.auditor.log_event(
                event_type=DataFlowType.FILE_READ,
                source=str(file_path),
                destination="memory:data",
                data_type=package_info['data_type'],
                classification=DataClassification.CONFIDENTIAL,
                size_bytes=len(data_bytes),
                encrypted=package_info['encrypted']
            )

            logger.info(f"數據已導入: {package_info['package_id']}")
            return data

        except Exception as e:
            logger.error(f"導入數據失敗: {e}")
            raise

    def import_batch(self, manifest_file: str) -> List[Any]:
        """
        批量導入數據

        Args:
            manifest_file: 清單文件

        Returns:
            導入的數據列表
        """
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        imported_data = []
        for file_path in manifest['files']:
            try:
                data = self.import_data(file_path)
                imported_data.append(data)
            except Exception as e:
                logger.error(f"導入文件失敗 {file_path}: {e}")

        logger.info(f"批次導入完成: {manifest['batch_id']}, 成功 {len(imported_data)} 項")
        return imported_data

    def _serialize_data(self, data: Any, format: ExportFormat) -> tuple[bytes, int]:
        """序列化數據"""
        if format == ExportFormat.JSON:
            if isinstance(data, (dict, list)):
                serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
            else:
                serialized = json.dumps({'value': data}).encode('utf-8')
        elif format == ExportFormat.CSV:
            if isinstance(data, pd.DataFrame):
                import io
                buf = io.StringIO()
                data.to_csv(buf, index=False)
                serialized = buf.getvalue().encode('utf-8')
            elif isinstance(data, list):
                import io
                buf = io.StringIO()
                if data and isinstance(data[0], dict):
                    writer = csv.DictWriter(buf, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    serialized = buf.getvalue().encode('utf-8')
                else:
                    serialized = '\n'.join(str(item) for item in data).encode('utf-8')
            else:
                serialized = str(data).encode('utf-8')
        elif format == ExportFormat.EXCEL:
            if isinstance(data, pd.DataFrame):
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False)
                serialized = buf.getvalue()
            else:
                raise ValueError("Excel格式需要pandas DataFrame")
        elif format == ExportFormat.PARQUET:
            if isinstance(data, pd.DataFrame):
                serialized = data.to_parquet()
            else:
                raise ValueError("Parquet格式需要pandas DataFrame")
        else:
            serialized = str(data).encode('utf-8')

        return serialized, len(serialized)

    def _deserialize_data(self, data_bytes: bytes, format: ExportFormat) -> Any:
        """反序列化數據"""
        if format == ExportFormat.JSON:
            return json.loads(data_bytes.decode('utf-8'))
        elif format == ExportFormat.CSV:
            from io import StringIO
            df = pd.read_csv(StringIO(data_bytes.decode('utf-8')))
            return df
        elif format == ExportFormat.EXCEL:
            from io import BytesIO
            df = pd.read_excel(BytesIO(data_bytes))
            return df
        elif format == ExportFormat.PARQUET:
            df = pd.read_parquet(BytesIO(data_bytes))
            return df
        else:
            return data_bytes.decode('utf-8')

    def _save_package_info(self, package: DataPackage):
        """保存包信息"""
        info_file = self.export_dir / f"{package.package_id}_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(package), f, indent=2, ensure_ascii=False)

    def _get_package_info(self, package_id: str) -> Optional[Dict[str, Any]]:
        """獲取包信息"""
        info_file = self.export_dir / f"{package_id}_info.json"
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def list_exports(self) -> List[Dict[str, Any]]:
        """列出所有導出"""
        exports = []
        for info_file in self.export_dir.glob('*_info.json'):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    exports.append(json.load(f))
            except Exception as e:
                logger.error(f"讀取導出信息失敗: {e}")

        return sorted(exports, key=lambda x: x['created_at'], reverse=True)

    def verify_export(self, package_id: str) -> Dict[str, Any]:
        """
        驗證導出文件

        Args:
            package_id: 包ID

        Returns:
            驗證結果
        """
        info = self._get_package_info(package_id)
        if not info:
            return {'valid': False, 'error': '包信息不存在'}

        data_file = self.export_dir / f"{package_id}.{info['format']}"
        if not data_file.exists():
            return {'valid': False, 'error': '數據文件不存在'}

        # 計算校驗和
        with open(data_file, 'rb') as f:
            data = f.read()
            checksum = hashlib.sha256(data).hexdigest()

        valid = checksum == info['checksum']

        return {
            'valid': valid,
            'expected_checksum': info['checksum'],
            'actual_checksum': checksum,
            'size': len(data),
            'expected_size': info['total_size']
        }

    def create_portable_package(self,
                               data: Any,
                               package_name: str,
                               include_key: bool = False) -> str:
        """
        創建便攜式數據包（包含密鑰）

        Args:
            data: 數據
            package_name: 包名
            include_key: 是否包含密鑰（危險！僅用於完全信任的環境）

        Returns:
            導出文件路徑
        """
        if include_key:
            logger.warning("包含密鑰的便攜包存在安全風險！")

        # 導出數據
        export_file = self.export_data(
            data=data,
            file_name=package_name,
            data_type="portable_package",
            category=DataCategory.BACKUP,
            format=ExportFormat.ENCRYPTED,
            encrypt=True,
            compress=True
        )

        # 創建便攜包元信息
        portable_info = {
            'package_name': package_name,
            'created_at': datetime.utcnow().isoformat(),
            'includes_key': include_key,
            'export_file': export_file
        }

        if include_key:
            portable_info['master_key'] = self.master_key.hex()

        info_file = Path(export_file).with_suffix('.portable')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(portable_info, f, indent=2, ensure_ascii=False)

        logger.info(f"便攜式數據包已創建: {package_name}")
        return str(info_file)

    def get_export_statistics(self) -> Dict[str, Any]:
        """獲取導出統計"""
        exports = self.list_exports()
        if not exports:
            return {'message': '無導出'}

        total_size = sum(e['total_size'] for e in exports)
        encrypted_count = sum(1 for e in exports if e['encrypted'])
        compressed_count = sum(1 for e in exports if e['compression'])

        return {
            'total_exports': len(exports),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'encrypted_exports': encrypted_count,
            'encrypted_rate': round(encrypted_count / len(exports) * 100, 2),
            'compressed_exports': compressed_count,
            'compression_rate': round(compressed_count / len(exports) * 100, 2),
            'oldest_export': min(e['created_at'] for e in exports),
            'newest_export': max(e['created_at'] for e in exports)
        }

    def delete_export(self, package_id: str) -> bool:
        """
        刪除導出

        Args:
            package_id: 包ID

        Returns:
            是否成功
        """
        try:
            # 刪除數據文件
            info = self._get_package_info(package_id)
            if info:
                data_file = self.export_dir / f"{package_id}.{info['format']}"
                if data_file.exists():
                    data_file.unlink()

            # 刪除信息文件
            info_file = self.export_dir / f"{package_id}_info.json"
            if info_file.exists():
                info_file.unlink()

            logger.info(f"導出已刪除: {package_id}")
            return True

        except Exception as e:
            logger.error(f"刪除導出失敗: {e}")
            return False

# 便捷函數
def export_trading_data(data: Dict[str, Any], encrypt: bool = True) -> str:
    """便捷函數：導出交易數據"""
    manager = EncryptedDataManager()
    return manager.export_data(
        data=data,
        file_name="trading_data",
        data_type="trading",
        category=DataCategory.TRANSACTION,
        encrypt=encrypt
    )

def import_trading_data(file_path: str) -> Any:
    """便捷函數：導入交易數據"""
    manager = EncryptedDataManager()
    return manager.import_data(file_path)
