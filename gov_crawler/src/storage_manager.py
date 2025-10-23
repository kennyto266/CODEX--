"""
GOV 爬蟲系統 - 存儲管理模塊
"""

import logging
import os
import pandas as pd
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


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
            from datetime import timedelta
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
