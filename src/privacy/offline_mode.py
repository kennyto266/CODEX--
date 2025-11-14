"""
離線模式系統
實現100%本地數據處理，支持完全離線運行
"""

import os
import json
import sqlite3
import logging
import pickle
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np

from .data_flow_audit import DataFlowAuditor, DataFlowType, DataClassification

logger = logging.getLogger('quant_system.privacy')

class SyncStatus(Enum):
    """同步狀態"""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    OFFLINE = "offline"
    ERROR = "error"

class DataSource(Enum):
    """數據源"""
    LOCAL_CACHE = "local_cache"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    USER_INPUT = "user_input"
    BULK_IMPORT = "bulk_import"

@dataclass
class CachedDataItem:
    """緩存數據項"""
    key: str
    data_type: str
    source: DataSource
    size_bytes: int
    created_at: str
    last_accessed: str
    access_count: int
    hash_checksum: str
    sync_status: SyncStatus
    metadata: Dict[str, Any]

class OfflineModeManager:
    """
    離線模式管理器
    管理本地數據緩存，確保100%離線運行
    """

    def __init__(self,
                 cache_dir: str = 'cache/offline',
                 db_path: Optional[str] = None,
                 max_cache_size_gb: float = 5.0):
        """
        初始化離線模式管理器

        Args:
            cache_dir: 緩存目錄
            db_path: 元數據數據庫路徑（默認：cache_dir/metadata.db）
            max_cache_size_gb: 最大緩存大小（GB）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 設置默認數據庫路徑
        if db_path is None:
            self.db_path = str(self.cache_dir / 'metadata.db')
        else:
            self.db_path = db_path

        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # 轉換為字節

        # 審計器
        self.auditor = DataFlowAuditor(str(self.cache_dir / 'audit'))

        # 初始化數據庫
        self._init_database()

        # 緩存統計
        self.stats = {
            'total_items': 0,
            'total_size': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # 數據同步狀態
        self.sync_status: Dict[str, SyncStatus] = {}

        # 阻止的外部端點
        self.blocked_endpoints = {
            'api.github.com',
            'raw.githubusercontent.com',
            'pypi.org',
            'pipenv.pypa.io'
        }

        logger.info(f"離線模式管理器已初始化，緩存目錄: {self.cache_dir}")

    def _init_database(self):
        """初始化元數據數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_items (
                key TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                source TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                hash_checksum TEXT NOT NULL,
                sync_status TEXT NOT NULL,
                metadata TEXT,
                UNIQUE(key)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_type
            ON cached_items(data_type)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sync_status
            ON cached_items(sync_status)
        ''')

        conn.commit()
        conn.close()

        logger.debug("元數據數據庫已初始化")

    def cache_data(self,
                   key: str,
                   data: Any,
                   data_type: str,
                   source: DataSource = DataSource.USER_INPUT,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        緩存數據

        Args:
            key: 緩存鍵
            data: 數據（可為pandas DataFrame、dict、list等）
            data_type: 數據類型
            source: 數據源
            metadata: 元數據

        Returns:
            是否成功
        """
        try:
            # 序列化數據
            if isinstance(data, pd.DataFrame):
                # DataFrame特殊處理
                data_bytes = data.to_parquet()
            elif isinstance(data, (dict, list)):
                data_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
            else:
                data_bytes = pickle.dumps(data)

            # 計算校驗和
            checksum = hashlib.sha256(data_bytes).hexdigest()

            # 創建文件路徑
            safe_key = key.replace('/', '_').replace('\\', '_')
            file_path = self.cache_dir / f"{safe_key}.cache"

            # 寫入文件
            with open(file_path, 'wb') as f:
                f.write(data_bytes)

            size_bytes = len(data_bytes)

            # 保存元數據
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO cached_items
                (key, data_type, source, file_path, size_bytes, created_at,
                 last_accessed, access_count, hash_checksum, sync_status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key, data_type, source.value, str(file_path), size_bytes,
                now, now, 0, checksum, SyncStatus.SYNCED.value,
                json.dumps(metadata or {})
            ))

            conn.commit()
            conn.close()

            # 更新統計
            self.stats['total_items'] += 1
            self.stats['total_size'] += size_bytes

            # 記錄審計事件
            self.auditor.log_event(
                event_type=DataFlowType.LOCAL_WRITE,
                source=source.value,
                destination=f"cache:{key}",
                data_type=data_type,
                classification=DataClassification.INTERNAL,
                size_bytes=size_bytes,
                encrypted=False
            )

            logger.debug(f"數據已緩存: {key}, 大小: {size_bytes} 字節")
            return True

        except Exception as e:
            logger.error(f"緩存數據失敗: {e}")
            return False

    def get_cached_data(self, key: str) -> Optional[Any]:
        """
        獲取緩存數據

        Args:
            key: 緩存鍵

        Returns:
            緩存的數據
        """
        try:
            # 查找元數據
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cached_items WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                self.stats['cache_misses'] += 1
                logger.debug(f"緩存未命中: {key}")
                return None

            # 讀取文件
            file_path = Path(row[3])
            if not file_path.exists():
                logger.warning(f"緩存文件不存在: {file_path}")
                return None

            with open(file_path, 'rb') as f:
                data_bytes = f.read()

            # 反序列化
            if row[1] == 'dataframe':  # data_type
                data = pd.read_parquet(data_bytes)
            elif row[1] in ['dict', 'list']:
                data = json.loads(data_bytes.decode('utf-8'))
            else:
                data = pickle.loads(data_bytes)

            # 更新訪問信息
            self._update_access_info(key)

            self.stats['cache_hits'] += 1
            logger.debug(f"緩存命中: {key}")
            return data

        except Exception as e:
            logger.error(f"獲取緩存數據失敗: {e}")
            return None

    def _update_access_info(self, key: str):
        """更新訪問信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()
        cursor.execute('''
            UPDATE cached_items
            SET last_accessed = ?, access_count = access_count + 1
            WHERE key = ?
        ''', (now, key))

        conn.commit()
        conn.close()

    def is_offline(self) -> bool:
        """檢查是否處於離線模式"""
        return True  # 離線模式總是返回True

    def load_data(self,
                  symbol: str,
                  days: int = 365,
                  use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        加載本地股票數據

        Args:
            symbol: 股票代碼
            days: 天數
            use_cache: 是否使用緩存

        Returns:
            股票數據DataFrame
        """
        # 構建緩存鍵
        cache_key = f"stock_data_{symbol}_{days}"

        # 嘗試從緩存獲取
        if use_cache:
            cached_data = self.get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data

        # 從本地文件加載
        data_file = Path(f"data/hkex/{symbol.lower()}_daily.json")
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 轉換為DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df.tail(days)  # 取最後N天

            # 緩存數據
            self.cache_data(cache_key, df, 'dataframe', DataSource.FILE_SYSTEM)

            # 記錄審計事件
            self.auditor.log_event(
                event_type=DataFlowType.FILE_READ,
                source=str(data_file),
                destination=f"memory:{cache_key}",
                data_type="stock_data",
                classification=DataClassification.INTERNAL
            )

            return df

        logger.warning(f"未找到本地數據文件: {data_file}")
        return None

    def calculate_indicators(self,
                            data: pd.DataFrame,
                            indicators: List[str]) -> Dict[str, Any]:
        """
        計算技術指標（離線模式）

        Args:
            data: 價格數據
            indicators: 指標列表

        Returns:
            計算結果
        """
        results = {}

        for indicator in indicators:
            try:
                if indicator == 'ma':
                    # 移動平均線
                    results['ma5'] = data['close'].rolling(5).mean()
                    results['ma20'] = data['close'].rolling(20).mean()
                    results['ma60'] = data['close'].rolling(60).mean()

                elif indicator == 'rsi':
                    # RSI
                    delta = data['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    results['rsi'] = 100 - (100 / (1 + rs))

                elif indicator == 'macd':
                    # MACD
                    exp1 = data['close'].ewm(span=12).mean()
                    exp2 = data['close'].ewm(span=26).mean()
                    macd = exp1 - exp2
                    signal = macd.ewm(span=9).mean()
                    results['macd'] = macd
                    results['signal'] = signal
                    results['histogram'] = macd - signal

                elif indicator == 'bb':
                    # 布林帶
                    sma = data['close'].rolling(20).mean()
                    std = data['close'].rolling(20).std()
                    results['bb_upper'] = sma + (std * 2)
                    results['bb_lower'] = sma - (std * 2)
                    results['bb_middle'] = sma

                # 記錄審計事件
                self.auditor.log_event(
                    event_type=DataFlowType.LOCAL_PROCESS,
                    source="data:prices",
                    destination=f"indicators:{indicator}",
                    data_type=indicator,
                    classification=DataClassification.INTERNAL,
                    encrypted=False
                )

            except Exception as e:
                logger.error(f"計算指標 {indicator} 失敗: {e}")
                results[indicator] = None

        return results

    def generate_trading_signals(self,
                                 data: pd.DataFrame,
                                 strategy: str = 'ma') -> List[Dict[str, Any]]:
        """
        生成交易信號（離線模式）

        Args:
            data: 價格數據
            strategy: 策略名稱

        Returns:
            交易信號列表
        """
        signals = []

        if strategy == 'ma':
            # 移動平均策略
            ma5 = data['close'].rolling(5).mean()
            ma20 = data['close'].rolling(20).mean()

            for i in range(1, len(data)):
                if ma5.iloc[i] > ma20.iloc[i] and ma5.iloc[i-1] <= ma20.iloc[i-1]:
                    signals.append({
                        'date': data.index[i],
                        'action': 'BUY',
                        'price': data['close'].iloc[i],
                        'reason': 'MA5 crosses above MA20'
                    })
                elif ma5.iloc[i] < ma20.iloc[i] and ma5.iloc[i-1] >= ma20.iloc[i-1]:
                    signals.append({
                        'date': data.index[i],
                        'action': 'SELL',
                        'price': data['close'].iloc[i],
                        'reason': 'MA5 crosses below MA20'
                    })

        # 記錄審計事件
        if signals:
            self.auditor.log_event(
                event_type=DataFlowType.LOCAL_PROCESS,
                source="data:prices",
                destination="signals:trading",
                data_type="trading_signals",
                classification=DataClassification.CONFIDENTIAL,
                encrypted=False
            )

        return signals

    def get_cache_status(self) -> Dict[str, Any]:
        """獲取緩存狀態"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*), SUM(size_bytes) FROM cached_items')
        count, total_size = cursor.fetchone()
        conn.close()

        # 計算命中率
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_items': count or 0,
            'total_size_bytes': total_size or 0,
            'total_size_mb': round((total_size or 0) / (1024 * 1024), 2),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'max_cache_size_gb': self.max_cache_size / (1024 ** 3),
            'usage_percent': round((total_size or 0) / self.max_cache_size * 100, 2)
        }

    def cleanup_cache(self, days_old: int = 30) -> int:
        """
        清理舊緩存

        Args:
            days_old: 保留天數

        Returns:
            清理的文件數
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key, file_path FROM cached_items
            WHERE last_accessed < ?
        ''', (cutoff_date.isoformat(),))

        files_to_delete = cursor.fetchall()
        deleted_count = 0

        for key, file_path in files_to_delete:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"刪除緩存文件失敗: {e}")

        # 從數據庫刪除
        cursor.execute('DELETE FROM cached_items WHERE last_accessed < ?', (cutoff_date.isoformat(),))
        conn.commit()
        conn.close()

        logger.info(f"已清理 {deleted_count} 個舊緩存文件")
        return deleted_count

    def sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sync_status, COUNT(*) as count
            FROM cached_items
            GROUP BY sync_status
        ''')

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        return {
            'status_distribution': status_counts,
            'last_sync': datetime.utcnow().isoformat(),
            'offline_mode': True
        }

    def export_cache_manifest(self, output_file: str):
        """
        導出緩存清單

        Args:
            output_file: 輸出文件
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cached_items')
        rows = cursor.fetchall()
        conn.close()

        columns = [description[0] for description in cursor.description]
        manifest = [dict(zip(columns, row)) for row in rows]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"緩存清單已導出: {output_file}")

# 便捷函數
def get_offline_manager() -> OfflineModeManager:
    """獲取離線模式管理器實例"""
    return OfflineModeManager()

def is_offline() -> bool:
    """檢查是否離線"""
    return True

def load_local_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """便捷函數：加載本地數據"""
    manager = get_offline_manager()
    return manager.load_data(symbol, days)

def calculate_ma(data: pd.DataFrame) -> Dict[str, pd.Series]:
    """便捷函數：計算移動平均"""
    manager = get_offline_manager()
    return manager.calculate_indicators(data, ['ma'])
