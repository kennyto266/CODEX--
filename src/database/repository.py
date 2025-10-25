"""
Data Repository Interface and Implementation

Provides abstraction for data storage operations.
Supports in-memory cache, SQLite, and future database backends.

Used by: Data pipeline for persistence and retrieval
"""

import pandas as pd
import sqlite3
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger("hk_quant_system.repository")


class IDataRepository(ABC):
    """Abstract interface for data repository."""

    @abstractmethod
    def save(self, symbol: str, df: pd.DataFrame, data_type: str = "stock") -> None:
        """Save data."""
        pass

    @abstractmethod
    def load(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Load data."""
        pass

    @abstractmethod
    def exists(self, symbol: str) -> bool:
        """Check if data exists."""
        pass

    @abstractmethod
    def delete(self, symbol: str) -> None:
        """Delete data."""
        pass

    @abstractmethod
    def list_symbols(self) -> List[str]:
        """List all available symbols."""
        pass


class MemoryRepository(IDataRepository):
    """In-memory data repository."""

    def __init__(self):
        """Initialize memory repository."""
        self.data: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def save(self, symbol: str, df: pd.DataFrame, data_type: str = "stock") -> None:
        """Save data to memory."""
        self.data[symbol] = df.copy()
        self.metadata[symbol] = {
            'data_type': data_type,
            'saved_at': datetime.now().isoformat(),
            'rows': len(df),
            'columns': list(df.columns),
        }
        logger.info(f"Saved {symbol} to memory ({len(df)} rows)")

    def load(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """Load data from memory."""
        if symbol not in self.data:
            return None

        df = self.data[symbol].copy()

        if isinstance(df.index, pd.DatetimeIndex):
            df = df[(df.index >= start_date) & (df.index <= end_date)]

        return df

    def exists(self, symbol: str) -> bool:
        """Check if symbol exists."""
        return symbol in self.data

    def delete(self, symbol: str) -> None:
        """Delete symbol data."""
        if symbol in self.data:
            del self.data[symbol]
            if symbol in self.metadata:
                del self.metadata[symbol]
            logger.info(f"Deleted {symbol} from memory")

    def list_symbols(self) -> List[str]:
        """List all symbols."""
        return list(self.data.keys())

    def clear(self) -> None:
        """Clear all data."""
        self.data.clear()
        self.metadata.clear()


class SQLiteRepository(IDataRepository):
    """SQLite-based data repository."""

    def __init__(self, db_path: str = "data/quant_data.db"):
        """Initialize SQLite repository."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    UNIQUE(symbol, date)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    symbol TEXT PRIMARY KEY,
                    data_type TEXT,
                    saved_at TEXT,
                    last_updated TEXT,
                    total_rows INTEGER
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_date
                ON stock_data(symbol, date)
            """)

            conn.commit()

    def save(self, symbol: str, df: pd.DataFrame, data_type: str = "stock") -> None:
        """Save data to SQLite."""
        if df.empty:
            logger.warning(f"Cannot save empty DataFrame for {symbol}")
            return

        with sqlite3.connect(self.db_path) as conn:
            # Convert DataFrame to records
            records = []

            for idx, row in df.iterrows():
                date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)

                records.append((
                    symbol,
                    date_str,
                    row.get('Open'),
                    row.get('High'),
                    row.get('Low'),
                    row.get('Close'),
                    row.get('Volume'),
                ))

            # Insert or replace
            conn.executemany(
                """
                INSERT OR REPLACE INTO stock_data
                (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )

            # Update metadata
            conn.execute(
                """
                INSERT OR REPLACE INTO metadata
                (symbol, data_type, saved_at, last_updated, total_rows)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    data_type,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    len(df),
                ),
            )

            conn.commit()

        logger.info(f"Saved {symbol} to SQLite ({len(df)} rows)")

    def load(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[pd.DataFrame]:
        """Load data from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT date, open, high, low, close, volume
                FROM stock_data
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(
                    symbol,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                ),
                parse_dates=['date'],
            )

            if df.empty:
                return None

            df.set_index('date', inplace=True)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

            return df

    def exists(self, symbol: str) -> bool:
        """Check if symbol exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM stock_data WHERE symbol = ? LIMIT 1",
                (symbol,),
            )
            return cursor.fetchone() is not None

    def delete(self, symbol: str) -> None:
        """Delete symbol data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM stock_data WHERE symbol = ?", (symbol,))
            conn.execute("DELETE FROM metadata WHERE symbol = ?", (symbol,))
            conn.commit()

        logger.info(f"Deleted {symbol} from SQLite")

    def list_symbols(self) -> List[str]:
        """List all symbols."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT symbol FROM stock_data ORDER BY symbol"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data_type, saved_at, last_updated, total_rows FROM metadata WHERE symbol = ?",
                (symbol,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return {
                'symbol': symbol,
                'data_type': row[0],
                'saved_at': row[1],
                'last_updated': row[2],
                'total_rows': row[3],
            }
