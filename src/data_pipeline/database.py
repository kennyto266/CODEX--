"""
Database Layer for CODEX Quantitative Trading System.

Provides:
- SQLAlchemy ORM models for OHLCV data
- Database schema with proper indexing
- Connection pooling and session management
- Query optimization
- Alembic migration support
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime,
    Index, event, pool, select
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# SQLAlchemy base for all models
Base = declarative_base()


class OHLCVData(Base):
    """
    OHLCV (Open, High, Low, Close, Volume) data model.

    Represents daily trading data for a security.
    """
    __tablename__ = 'ohlcv_data'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Data identification
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)

    # OHLCV data
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    # Data quality metrics
    quality_score = Column(Float, nullable=True)  # 0-1 range
    is_outlier = Column(Integer, nullable=True)   # 0 or 1

    # Technical indicators (optional)
    sma_20 = Column(Float, nullable=True)
    ema_12 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)

    # Metadata
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date', unique=True),
        Index('idx_date', 'date'),
        Index('idx_symbol', 'symbol'),
        Index('idx_quality_score', 'quality_score'),
    )

    def __repr__(self):
        return f"<OHLCVData(symbol={self.symbol}, date={self.date}, close={self.close_price})>"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OHLCVData':
        """Create OHLCVData instance from dictionary."""
        return cls(
            symbol=data.get('symbol'),
            date=data.get('date'),
            open_price=data.get('open_price') or data.get('open'),
            high_price=data.get('high_price') or data.get('high'),
            low_price=data.get('low_price') or data.get('low'),
            close_price=data.get('close_price') or data.get('close'),
            volume=data.get('volume'),
            quality_score=data.get('quality_score'),
            is_outlier=data.get('is_outlier'),
            sma_20=data.get('sma_20'),
            ema_12=data.get('ema_12'),
            rsi_14=data.get('rsi_14'),
            bb_upper=data.get('bb_upper'),
            bb_lower=data.get('bb_lower'),
            source=data.get('source'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert OHLCVData instance to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'date': self.date,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'quality_score': self.quality_score,
            'is_outlier': self.is_outlier,
            'sma_20': self.sma_20,
            'ema_12': self.ema_12,
            'rsi_14': self.rsi_14,
            'bb_upper': self.bb_upper,
            'bb_lower': self.bb_lower,
            'source': self.source,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class DatabaseConnection:
    """
    Database connection manager with connection pooling.

    Handles:
    - Connection creation and pooling
    - Session management
    - Engine lifecycle
    """

    def __init__(self,
                 database_url: str,
                 pool_size: int = 10,
                 max_overflow: int = 20,
                 echo: bool = False):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo,
            pool_pre_ping=True  # Test connections before using
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        self.engine.dispose()


class DataRepository:
    """
    Data access layer for OHLCV data.

    Provides methods for:
    - Inserting/updating records
    - Querying data
    - Batch operations
    - Transaction management
    """

    def __init__(self, session: Session):
        """Initialize repository with session."""
        self.session = session

    def insert_record(self, record: OHLCVData) -> OHLCVData:
        """Insert single OHLCV record."""
        self.session.add(record)
        self.session.commit()
        return record

    def insert_batch(self, records: List[OHLCVData]) -> int:
        """
        Insert batch of OHLCV records.

        Args:
            records: List of OHLCVData instances

        Returns:
            Number of records inserted
        """
        self.session.bulk_save_objects(records)
        self.session.commit()
        return len(records)

    def insert_dataframe(self, df: pd.DataFrame, symbol: str, source: str = 'api') -> int:
        """
        Insert DataFrame as OHLCV records.

        Args:
            df: DataFrame with OHLCV columns
            symbol: Stock symbol
            source: Data source identifier

        Returns:
            Number of records inserted
        """
        records = []
        for idx, row in df.iterrows():
            record = OHLCVData(
                symbol=symbol,
                date=idx if isinstance(idx, datetime) else row.get('date'),
                open_price=row.get('open') or row.get('open_price'),
                high_price=row.get('high') or row.get('high_price'),
                low_price=row.get('low') or row.get('low_price'),
                close_price=row.get('close') or row.get('close_price'),
                volume=int(row.get('volume', 0)),
                quality_score=row.get('quality_score'),
                is_outlier=row.get('is_outlier'),
                sma_20=row.get('sma_20'),
                ema_12=row.get('ema_12'),
                rsi_14=row.get('rsi_14'),
                bb_upper=row.get('bb_upper'),
                bb_lower=row.get('bb_lower'),
                source=source,
            )
            records.append(record)

        return self.insert_batch(records)

    def update_record(self, record_id: int, updates: Dict[str, Any]) -> OHLCVData:
        """Update existing record."""
        record = self.session.query(OHLCVData).filter(OHLCVData.id == record_id).first()
        if record:
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.session.commit()
        return record

    def get_by_symbol_date(self, symbol: str, date: datetime) -> Optional[OHLCVData]:
        """Get record by symbol and date."""
        return self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.date == date
        ).first()

    def get_by_symbol_range(self, symbol: str, start_date: datetime, end_date: datetime) -> List[OHLCVData]:
        """Get records for symbol within date range."""
        return self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.date >= start_date,
            OHLCVData.date <= end_date
        ).order_by(OHLCVData.date).all()

    def get_by_symbol(self, symbol: str, limit: Optional[int] = None) -> List[OHLCVData]:
        """Get all records for symbol."""
        query = self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol
        ).order_by(OHLCVData.date.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_high_quality(self, symbol: str, min_quality: float = 0.7) -> List[OHLCVData]:
        """Get high-quality records for symbol."""
        return self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.quality_score >= min_quality
        ).order_by(OHLCVData.date).all()

    def get_outliers(self, symbol: str) -> List[OHLCVData]:
        """Get outlier records for symbol."""
        return self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.is_outlier == 1
        ).all()

    def to_dataframe(self, records: List[OHLCVData]) -> pd.DataFrame:
        """Convert records to DataFrame."""
        if not records:
            return pd.DataFrame()

        data = [record.to_dict() for record in records]
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df

    def count_by_symbol(self, symbol: str) -> int:
        """Count records for symbol."""
        return self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol
        ).count()

    def delete_by_symbol_date(self, symbol: str, date: datetime) -> int:
        """Delete record by symbol and date."""
        result = self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.date == date
        ).delete()
        self.session.commit()
        return result

    def delete_by_symbol(self, symbol: str) -> int:
        """Delete all records for symbol."""
        result = self.session.query(OHLCVData).filter(
            OHLCVData.symbol == symbol
        ).delete()
        self.session.commit()
        return result

    def get_date_range(self, symbol: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get min and max dates for symbol."""
        min_date = self.session.query(OHLCVData.date).filter(
            OHLCVData.symbol == symbol
        ).order_by(OHLCVData.date.asc()).first()

        max_date = self.session.query(OHLCVData.date).filter(
            OHLCVData.symbol == symbol
        ).order_by(OHLCVData.date.desc()).first()

        return (min_date[0] if min_date else None, max_date[0] if max_date else None)

    def get_all_symbols(self) -> List[str]:
        """Get all distinct symbols in database."""
        results = self.session.query(OHLCVData.symbol).distinct().all()
        return [r[0] for r in results]

    def close(self):
        """Close session."""
        self.session.close()


class DatabaseManager:
    """
    High-level database manager combining connection and repository.
    """

    def __init__(self, database_url: str, pool_size: int = 10, echo: bool = False):
        """Initialize database manager."""
        self.connection = DatabaseConnection(database_url, pool_size=pool_size, echo=echo)
        self.repository = None

    def initialize(self):
        """Initialize database and create tables."""
        self.connection.create_tables()

    def get_repository(self) -> DataRepository:
        """Get data repository instance."""
        if not self.repository:
            session = self.connection.get_session()
            self.repository = DataRepository(session)
        return self.repository

    def create_session(self) -> Session:
        """Create new database session."""
        return self.connection.get_session()

    def close(self):
        """Close connection."""
        if self.repository:
            self.repository.close()
        self.connection.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


# Default SQLite configuration for development
def get_development_database_url() -> str:
    """Get development database URL (SQLite)."""
    return 'sqlite:///./codex_trading.db'


def get_test_database_url() -> str:
    """Get test database URL (in-memory SQLite)."""
    return 'sqlite:///:memory:'


def create_database_manager(database_url: Optional[str] = None, test: bool = False) -> DatabaseManager:
    """
    Factory function to create database manager.

    Args:
        database_url: Custom database URL
        test: Whether to use test database

    Returns:
        Configured DatabaseManager instance
    """
    if test:
        url = get_test_database_url()
    elif database_url:
        url = database_url
    else:
        url = get_development_database_url()

    manager = DatabaseManager(url)
    manager.initialize()
    return manager
