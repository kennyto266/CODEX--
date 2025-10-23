"""
GOV 爬蟲系統 - 存儲管理模塊 (Phase 2 優化版)

功能優化：
- 增量更新機制
- 數據壓縮支持
- 備份管理
- 大文件分批讀取
- 文件完整性檢查
- 索引管理
"""

import logging
import os
import pandas as pd
import json
import gzip
import shutil
import hashlib
from typing import Dict, Any, Optional, List, Iterator
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """文件元數據"""
    filename: str
    filepath: str
    size_bytes: int
    created_at: str
    modified_at: str
    checksum: str  # MD5 校驗和
    rows_count: Optional[int] = None
    compressed: bool = False


class StorageManager:
    """數據存儲管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化存儲管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.raw_data_dir = config['storage']['raw_data_dir']
        self.processed_data_dir = config['storage']['processed_data_dir']
        self.metadata_dir = config['storage']['metadata_dir']
        self.archive_dir = config['storage']['archive_dir']

        # 創建必要的目錄
        self._create_directories()

    def _create_directories(self) -> None:
        """創建必要的目錄結構"""
        directories = [
            self.raw_data_dir,
            self.processed_data_dir,
            self.metadata_dir,
            self.archive_dir
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"確保目錄存在: {directory}")

    def save_raw_data(self, dataset_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        保存原始數據

        Args:
            dataset_name: 數據集名稱
            data: 原始數據字典

        Returns:
            保存的文件路徑
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{dataset_name}_{timestamp}.json"
            filepath = os.path.join(self.raw_data_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"原始數據已保存: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存原始數據失敗: {e}")
            return None

    def save_processed_data(self, dataset_name: str, df: pd.DataFrame, format: str = 'csv') -> Optional[str]:
        """
        保存處理後的數據

        Args:
            dataset_name: 數據集名稱
            df: 數據 DataFrame
            format: 文件格式 ('csv', 'json', 'parquet')

        Returns:
            保存的文件路徑
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == 'csv':
                filename = f"{dataset_name}_{timestamp}.csv"
                filepath = os.path.join(self.processed_data_dir, filename)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')

            elif format == 'json':
                filename = f"{dataset_name}_{timestamp}.json"
                filepath = os.path.join(self.processed_data_dir, filename)
                df.to_json(filepath, orient='records', force_ascii=False, indent=2)

            elif format == 'parquet':
                filename = f"{dataset_name}_{timestamp}.parquet"
                filepath = os.path.join(self.processed_data_dir, filename)
                df.to_parquet(filepath, index=False)

            else:
                logger.error(f"不支持的文件格式: {format}")
                return None

            logger.info(f"處理後的數據已保存: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存處理後的數據失敗: {e}")
            return None

    def save_metadata(self, dataset_name: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        保存元信息

        Args:
            dataset_name: 數據集名稱
            metadata: 元信息字典

        Returns:
            保存的文件路徑
        """
        try:
            metadata['last_updated'] = datetime.now().isoformat()
            filename = f"{dataset_name}_metadata.json"
            filepath = os.path.join(self.metadata_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"元信息已保存: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存元信息失敗: {e}")
            return None

    def load_metadata(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """
        加載元信息

        Args:
            dataset_name: 數據集名稱

        Returns:
            元信息字典
        """
        try:
            filename = f"{dataset_name}_metadata.json"
            filepath = os.path.join(self.metadata_dir, filename)

            if not os.path.exists(filepath):
                logger.warning(f"元信息文件不存在: {filepath}")
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            logger.info(f"元信息已加載: {filepath}")
            return metadata

        except Exception as e:
            logger.error(f"加載元信息失敗: {e}")
            return None

    def load_processed_data(self, dataset_name: str, format: str = 'csv') -> Optional[pd.DataFrame]:
        """
        加載最新的處理後的數據

        Args:
            dataset_name: 數據集名稱
            format: 文件格式

        Returns:
            數據 DataFrame
        """
        try:
            # 查找最新的文件
            if format == 'csv':
                extension = '.csv'
            elif format == 'json':
                extension = '.json'
            elif format == 'parquet':
                extension = '.parquet'
            else:
                logger.error(f"不支持的文件格式: {format}")
                return None

            files = [f for f in os.listdir(self.processed_data_dir)
                    if f.startswith(dataset_name) and f.endswith(extension)]

            if not files:
                logger.warning(f"未找到 {dataset_name} 的 {format} 文件")
                return None

            # 獲取最新的文件
            latest_file = sorted(files)[-1]
            filepath = os.path.join(self.processed_data_dir, latest_file)

            if format == 'csv':
                df = pd.read_csv(filepath)
            elif format == 'json':
                df = pd.read_json(filepath)
            elif format == 'parquet':
                df = pd.read_parquet(filepath)

            logger.info(f"數據已加載: {filepath}")
            return df

        except Exception as e:
            logger.error(f"加載處理後的數據失敗: {e}")
            return None

    def list_files(self, directory: str = 'raw', limit: int = 10) -> list:
        """
        列出目錄中的文件

        Args:
            directory: 目錄類型 ('raw', 'processed', 'metadata', 'archive')
            limit: 返回的最大文件數

        Returns:
            文件列表
        """
        try:
            if directory == 'raw':
                target_dir = self.raw_data_dir
            elif directory == 'processed':
                target_dir = self.processed_data_dir
            elif directory == 'metadata':
                target_dir = self.metadata_dir
            elif directory == 'archive':
                target_dir = self.archive_dir
            else:
                logger.error(f"不認識的目錄類型: {directory}")
                return []

            files = sorted(os.listdir(target_dir), reverse=True)[:limit]
            logger.info(f"列出 {directory} 目錄中的 {len(files)} 個文件")
            return files

        except Exception as e:
            logger.error(f"列出文件失敗: {e}")
            return []

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        獲取存儲統計信息

        Args:
            None

        Returns:
            統計信息字典
        """
        try:
            stats = {
                'raw_data_count': len(os.listdir(self.raw_data_dir)),
                'processed_data_count': len(os.listdir(self.processed_data_dir)),
                'metadata_count': len(os.listdir(self.metadata_dir)),
                'archive_count': len(os.listdir(self.archive_dir)),
                'total_size_bytes': 0
            }

            # 計算總大小
            for directory in [self.raw_data_dir, self.processed_data_dir, self.metadata_dir, self.archive_dir]:
                for file in os.listdir(directory):
                    filepath = os.path.join(directory, file)
                    if os.path.isfile(filepath):
                        stats['total_size_bytes'] += os.path.getsize(filepath)

            logger.info(f"存儲統計: {stats}")
            return stats

        except Exception as e:
            logger.error(f"獲取存儲統計失敗: {e}")
            return {}

    def archive_old_data(self, days_old: int = 30) -> int:
        """
        存檔舊數據

        Args:
            days_old: 多少天以上的數據視為舊數據

        Returns:
            存檔的文件數
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            archived_count = 0

            for directory in [self.raw_data_dir, self.processed_data_dir]:
                for file in os.listdir(directory):
                    filepath = os.path.join(directory, file)
                    if os.path.isfile(filepath):
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < cutoff_date:
                            archive_path = os.path.join(self.archive_dir, file)
                            os.rename(filepath, archive_path)
                            archived_count += 1
                            logger.info(f"文件已存檔: {file}")

            logger.info(f"總共存檔 {archived_count} 個文件")
            return archived_count

        except Exception as e:
            logger.error(f"存檔舊數據失敗: {e}")
            return 0

    def cleanup_old_data(self, days_old: int = 90) -> int:
        """
        清理舊數據

        Args:
            days_old: 多少天以上的數據視為應清理的舊數據

        Returns:
            刪除的文件數
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0

            for directory in [self.archive_dir]:
                for file in os.listdir(directory):
                    filepath = os.path.join(directory, file)
                    if os.path.isfile(filepath):
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < cutoff_date:
                            os.remove(filepath)
                            deleted_count += 1
                            logger.info(f"文件已刪除: {file}")

            logger.info(f"總共刪除 {deleted_count} 個文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理舊數據失敗: {e}")
            return 0

    # ========== Phase 2: 新增優化存儲方法 ==========

    @staticmethod
    def _calculate_file_checksum(filepath: str) -> str:
        """
        計算文件的 MD5 校驗和

        Args:
            filepath: 文件路徑

        Returns:
            MD5 校驗和
        """
        md5_hash = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def compress_data(self, filepath: str) -> Optional[str]:
        """
        壓縮數據文件（使用 gzip）

        Args:
            filepath: 源文件路徑

        Returns:
            壓縮後的文件路徑
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"文件不存在: {filepath}")
                return None

            # 如果已是 .gz 文件，跳過
            if filepath.endswith('.gz'):
                logger.info(f"文件已壓縮: {filepath}")
                return filepath

            compressed_path = f"{filepath}.gz"

            # 壓縮文件
            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 獲取文件大小（壓縮前後對比）
            original_size = os.path.getsize(filepath)
            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = (1 - compressed_size / original_size) * 100

            logger.info(f"文件已壓縮: {filepath} → {compressed_path} "
                       f"({compression_ratio:.1f}% 縮減)")

            # 刪除原始文件
            os.remove(filepath)

            return compressed_path

        except Exception as e:
            logger.error(f"壓縮文件失敗: {e}")
            return None

    def decompress_data(self, filepath: str) -> Optional[str]:
        """
        解壓數據文件

        Args:
            filepath: 壓縮文件路徑

        Returns:
            解壓後的文件路徑
        """
        try:
            if not filepath.endswith('.gz'):
                logger.warning(f"文件不是 gzip 格式: {filepath}")
                return filepath

            decompressed_path = filepath[:-3]  # 移除 .gz 後綴

            with gzip.open(filepath, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"文件已解壓: {filepath} → {decompressed_path}")
            return decompressed_path

        except Exception as e:
            logger.error(f"解壓文件失敗: {e}")
            return None

    def create_backup(self, dataset_name: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        備份數據集

        Args:
            dataset_name: 數據集名稱
            backup_dir: 備份目錄（如果為 None，使用 archive_dir）

        Returns:
            備份文件路徑
        """
        try:
            backup_dir = backup_dir or self.archive_dir

            # 查找最新的處理數據
            files = [f for f in os.listdir(self.processed_data_dir)
                    if f.startswith(dataset_name)]

            if not files:
                logger.warning(f"找不到 {dataset_name} 的數據")
                return None

            latest_file = sorted(files)[-1]
            source_path = os.path.join(self.processed_data_dir, latest_file)

            # 創建備份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{dataset_name}_backup_{timestamp}.gz"
            backup_path = os.path.join(backup_dir, backup_filename)

            # 壓縮備份
            with open(source_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"已創建備份: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"創建備份失敗: {e}")
            return None

    def restore_backup(self, backup_path: str, restore_dir: Optional[str] = None) -> Optional[str]:
        """
        從備份恢復數據

        Args:
            backup_path: 備份文件路徑
            restore_dir: 恢復目錄（如果為 None，使用 processed_data_dir）

        Returns:
            恢復的文件路徑
        """
        try:
            restore_dir = restore_dir or self.processed_data_dir

            if not os.path.exists(backup_path):
                logger.warning(f"備份文件不存在: {backup_path}")
                return None

            # 生成恢復文件名
            backup_filename = os.path.basename(backup_path)
            if backup_filename.endswith('.gz'):
                restore_filename = backup_filename[:-3] + f"_restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                restore_filename = backup_filename + f"_restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            restore_path = os.path.join(restore_dir, restore_filename)

            # 解壓備份
            with gzip.open(backup_path, 'rb') as f_in:
                with open(restore_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"已從備份恢復: {backup_path} → {restore_path}")
            return restore_path

        except Exception as e:
            logger.error(f"恢復備份失敗: {e}")
            return None

    def read_large_file_chunked(self, filepath: str, chunksize: int = 10000) -> Iterator[pd.DataFrame]:
        """
        分批讀取大文件（避免一次性加載到內存）

        Args:
            filepath: 文件路徑
            chunksize: 每批行數

        Returns:
            DataFrame 生成器
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"文件不存在: {filepath}")
                return

            file_size = os.path.getsize(filepath)
            logger.info(f"開始分批讀取文件: {filepath} (大小: {file_size / 1024 / 1024:.2f} MB)")

            if filepath.endswith('.csv'):
                for chunk in pd.read_csv(filepath, chunksize=chunksize):
                    yield chunk
            elif filepath.endswith('.json'):
                df = pd.read_json(filepath)
                for i in range(0, len(df), chunksize):
                    yield df.iloc[i:i + chunksize]
            elif filepath.endswith('.parquet'):
                df = pd.read_parquet(filepath)
                for i in range(0, len(df), chunksize):
                    yield df.iloc[i:i + chunksize]
            else:
                logger.error(f"不支持的文件格式: {filepath}")

        except Exception as e:
            logger.error(f"讀取文件失敗: {e}")

    def verify_file_integrity(self, filepath: str, expected_checksum: Optional[str] = None) -> bool:
        """
        驗證文件完整性

        Args:
            filepath: 文件路徑
            expected_checksum: 期望的校驗和（如果為 None，與最新備份比對）

        Returns:
            是否完整
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"文件不存在: {filepath}")
                return False

            actual_checksum = self._calculate_file_checksum(filepath)

            if expected_checksum:
                is_valid = actual_checksum == expected_checksum
                logger.info(f"文件完整性驗證: {filepath} - {'✓ 有效' if is_valid else '✗ 無效'}")
                return is_valid
            else:
                logger.info(f"文件校驗和: {filepath} - {actual_checksum}")
                return True

        except Exception as e:
            logger.error(f"驗證文件完整性失敗: {e}")
            return False

    def create_index(self, dataset_name: str, index_columns: List[str]) -> Optional[str]:
        """
        為數據創建索引文件

        Args:
            dataset_name: 數據集名稱
            index_columns: 要索引的列

        Returns:
            索引文件路徑
        """
        try:
            # 加載最新的數據
            df = self.load_processed_data(dataset_name, format='csv')
            if df is None:
                logger.warning(f"找不到 {dataset_name} 的數據")
                return None

            # 創建索引
            index_data = {
                'dataset': dataset_name,
                'created_at': datetime.now().isoformat(),
                'total_rows': len(df),
                'columns': list(df.columns),
                'index_columns': index_columns,
                'unique_values': {}
            }

            # 計算各列的唯一值
            for col in index_columns:
                if col in df.columns:
                    unique_vals = df[col].unique()
                    index_data['unique_values'][col] = {
                        'count': len(unique_vals),
                        'values': unique_vals[:100].tolist()  # 限制前 100 個
                    }

            # 保存索引
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            index_filename = f"{dataset_name}_index_{timestamp}.json"
            index_path = os.path.join(self.metadata_dir, index_filename)

            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            logger.info(f"已創建索引: {index_path}")
            return index_path

        except Exception as e:
            logger.error(f"創建索引失敗: {e}")
            return None

    def incremental_update(self, dataset_name: str, new_data: pd.DataFrame,
                          key_columns: Optional[List[str]] = None) -> Optional[str]:
        """
        增量更新數據（只保存新增/修改的記錄）

        Args:
            dataset_name: 數據集名稱
            new_data: 新數據 DataFrame
            key_columns: 用於識別重複記錄的列（如 None，則視為全新數據）

        Returns:
            更新後的文件路徑
        """
        try:
            # 加載現有數據
            existing_df = self.load_processed_data(dataset_name, format='csv')

            if existing_df is None or existing_df.empty:
                # 沒有現有數據，直接保存新數據
                logger.info(f"未找到現有數據，保存新數據集: {dataset_name}")
                return self.save_processed_data(dataset_name, new_data, format='csv')

            # 使用 key_columns 進行增量合併
            if key_columns:
                # 移除新數據中已存在的記錄
                merged_df = existing_df.copy()
                new_records = new_data[~new_data[key_columns].isin(existing_df[key_columns].values).all(axis=1)]
                merged_df = pd.concat([merged_df, new_records], ignore_index=True)

                logger.info(f"增量更新: {len(new_records)} 個新記錄，共 {len(merged_df)} 行")
            else:
                # 如果沒有 key_columns，則追加新數據
                merged_df = pd.concat([existing_df, new_data], ignore_index=True)
                merged_df = merged_df.drop_duplicates()

                logger.info(f"追加新數據: {len(new_data)} 行，共 {len(merged_df)} 行")

            return self.save_processed_data(dataset_name, merged_df, format='csv')

        except Exception as e:
            logger.error(f"增量更新失敗: {e}")
            return None

    def get_file_metadata(self, filepath: str) -> Optional[FileMetadata]:
        """
        獲取文件元數據

        Args:
            filepath: 文件路徑

        Returns:
            文件元數據
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"文件不存在: {filepath}")
                return None

            stat_info = os.stat(filepath)
            checksum = self._calculate_file_checksum(filepath)

            # 嘗試獲取行數
            rows_count = None
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                    rows_count = len(df)
                elif filepath.endswith('.json'):
                    df = pd.read_json(filepath)
                    rows_count = len(df)
                elif filepath.endswith('.parquet'):
                    df = pd.read_parquet(filepath)
                    rows_count = len(df)
            except Exception as e:
                logger.debug(f"無法獲取行數: {e}")

            metadata = FileMetadata(
                filename=os.path.basename(filepath),
                filepath=filepath,
                size_bytes=stat_info.st_size,
                created_at=datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                checksum=checksum,
                rows_count=rows_count,
                compressed=filepath.endswith('.gz')
            )

            logger.info(f"已獲取文件元數據: {filepath}")
            return metadata

        except Exception as e:
            logger.error(f"獲取文件元數據失敗: {e}")
            return None
