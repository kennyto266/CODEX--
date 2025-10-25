"""
Comprehensive unit tests for Database Layer.

Test coverage:
- Database connection and pooling
- SQLAlchemy ORM model functionality
- CRUD operations (Create, Read, Update, Delete)
- Batch operations
- Query optimization
- Transaction handling
- Edge cases and error handling
- Performance testing
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from src.data_pipeline.database import (
    OHLCVData, DatabaseConnection, DataRepository,
    DatabaseManager, create_database_manager,
    get_test_database_url, Base
)


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    db_url = get_test_database_url()
    manager = DatabaseManager(db_url)
    manager.initialize()
    yield manager
    manager.close()


@pytest.fixture
def session(test_db):
    """Create database session."""
    return test_db.create_session()


@pytest.fixture
def sample_record():
    """Create sample OHLCV record."""
    return OHLCVData(
        symbol='0700.HK',
        date=datetime(2024, 1, 2, tzinfo=timezone.utc),
        open_price=100.0,
        high_price=102.5,
        low_price=99.5,
        close_price=101.0,
        volume=1000000,
        quality_score=0.95,
        is_outlier=0,
        source='test'
    )


@pytest.fixture
def sample_dataframe():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range('2024-01-01', periods=10, freq='D', tz='UTC')
    df = pd.DataFrame({
        'open': np.random.uniform(100, 102, 10),
        'high': np.random.uniform(102, 105, 10),
        'low': np.random.uniform(98, 100, 10),
        'close': np.random.uniform(100, 102, 10),
        'volume': np.random.randint(1000000, 5000000, 10),
    }, index=dates)
    return df


class TestOHLCVDataModel:
    """Test OHLCVData model."""

    def test_model_creation(self, sample_record):
        """Test creating OHLCVData instance."""
        assert sample_record.symbol == '0700.HK'
        assert sample_record.close_price == 101.0
        assert sample_record.volume == 1000000

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            'symbol': '0388.HK',
            'date': datetime(2024, 1, 2, tzinfo=timezone.utc),
            'open': 50.0,
            'high': 52.0,
            'low': 49.0,
            'close': 51.0,
            'volume': 500000,
            'quality_score': 0.9,
        }
        record = OHLCVData.from_dict(data)
        assert record.symbol == '0388.HK'
        assert record.close_price == 51.0

    def test_to_dict(self, sample_record):
        """Test converting to dictionary."""
        data = sample_record.to_dict()
        assert data['symbol'] == '0700.HK'
        assert data['close_price'] == 101.0
        assert 'id' in data

    def test_repr(self, sample_record):
        """Test string representation."""
        repr_str = repr(sample_record)
        assert '0700.HK' in repr_str
        assert '101.0' in repr_str


class TestDatabaseConnection:
    """Test database connection management."""

    def test_connection_creation(self):
        """Test creating database connection."""
        conn = DatabaseConnection(get_test_database_url())
        assert conn.engine is not None
        assert conn.SessionLocal is not None
        conn.close()

    def test_create_tables(self):
        """Test creating database tables."""
        conn = DatabaseConnection(get_test_database_url())
        conn.create_tables()

        # Should not raise error
        inspector_obj = inspect(conn.engine)
        tables = inspector_obj.get_table_names()
        assert 'ohlcv_data' in tables
        conn.close()

    def test_session_creation(self):
        """Test creating database session."""
        conn = DatabaseConnection(get_test_database_url())
        session = conn.get_session()
        assert session is not None
        session.close()
        conn.close()

    def test_connection_pooling(self):
        """Test connection pooling."""
        conn = DatabaseConnection(get_test_database_url(), pool_size=5)
        sessions = [conn.get_session() for _ in range(5)]
        assert len(sessions) == 5
        for s in sessions:
            s.close()
        conn.close()


class TestDataRepository:
    """Test data repository operations."""

    def test_insert_single_record(self, test_db, sample_record):
        """Test inserting single record."""
        repo = test_db.get_repository()
        result = repo.insert_record(sample_record)
        assert result.id is not None
        assert result.symbol == '0700.HK'

    def test_insert_batch(self, test_db):
        """Test batch insert."""
        repo = test_db.get_repository()
        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1+i, tzinfo=timezone.utc),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
            )
            for i in range(5)
        ]
        count = repo.insert_batch(records)
        assert count == 5

    def test_insert_dataframe(self, test_db, sample_dataframe):
        """Test inserting DataFrame."""
        repo = test_db.get_repository()
        count = repo.insert_dataframe(sample_dataframe, '0700.HK', source='test')
        assert count == 10

    def test_get_by_symbol_date(self, test_db, sample_record):
        """Test retrieving record by symbol and date."""
        repo = test_db.get_repository()
        repo.insert_record(sample_record)

        result = repo.get_by_symbol_date('0700.HK', sample_record.date)
        assert result is not None
        assert result.symbol == '0700.HK'
        assert result.close_price == 101.0

    def test_get_by_symbol_range(self, test_db, sample_dataframe):
        """Test retrieving records by date range."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')

        start = datetime(2024, 1, 3, tzinfo=timezone.utc)
        end = datetime(2024, 1, 7, tzinfo=timezone.utc)
        results = repo.get_by_symbol_range('0700.HK', start, end)

        assert len(results) > 0
        # Ensure dates are comparable (both timezone-aware or both naive)
        for r in results:
            if r.date.tzinfo is None:
                r_date = r.date.replace(tzinfo=timezone.utc)
            else:
                r_date = r.date
            assert r_date >= start and r_date <= end

    def test_get_by_symbol(self, test_db, sample_dataframe):
        """Test retrieving all records for symbol."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')

        results = repo.get_by_symbol('0700.HK')
        assert len(results) == 10

    def test_get_by_symbol_limit(self, test_db, sample_dataframe):
        """Test retrieving limited records."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')

        results = repo.get_by_symbol('0700.HK', limit=5)
        assert len(results) == 5

    def test_update_record(self, test_db, sample_record):
        """Test updating record."""
        repo = test_db.get_repository()
        inserted = repo.insert_record(sample_record)
        record_id = inserted.id

        updates = {'quality_score': 0.85}
        updated = repo.update_record(record_id, updates)
        assert updated.quality_score == 0.85

    def test_get_high_quality(self, test_db):
        """Test retrieving high-quality records."""
        repo = test_db.get_repository()
        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1+i, tzinfo=timezone.utc),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
                quality_score=0.5 + (i * 0.1)
            )
            for i in range(5)
        ]
        repo.insert_batch(records)

        high_quality = repo.get_high_quality('0700.HK', min_quality=0.7)
        assert len(high_quality) >= 3

    def test_get_outliers(self, test_db):
        """Test retrieving outlier records."""
        repo = test_db.get_repository()
        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1+i, tzinfo=timezone.utc),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
                is_outlier=i % 2
            )
            for i in range(5)
        ]
        repo.insert_batch(records)

        outliers = repo.get_outliers('0700.HK')
        assert len(outliers) >= 2

    def test_to_dataframe(self, test_db, sample_dataframe):
        """Test converting records to DataFrame."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')
        records = repo.get_by_symbol('0700.HK')

        df = repo.to_dataframe(records)
        assert len(df) == 10
        assert 'close' in df.columns or 'close_price' in df.columns

    def test_count_by_symbol(self, test_db, sample_dataframe):
        """Test counting records."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')
        repo.insert_dataframe(sample_dataframe, '0388.HK')

        count_0700 = repo.count_by_symbol('0700.HK')
        count_0388 = repo.count_by_symbol('0388.HK')

        assert count_0700 == 10
        assert count_0388 == 10

    def test_delete_by_symbol_date(self, test_db, sample_record):
        """Test deleting record by symbol and date."""
        repo = test_db.get_repository()
        repo.insert_record(sample_record)

        result = repo.delete_by_symbol_date('0700.HK', sample_record.date)
        assert result == 1

    def test_delete_by_symbol(self, test_db, sample_dataframe):
        """Test deleting all records for symbol."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')

        result = repo.delete_by_symbol('0700.HK')
        assert result == 10

    def test_get_date_range(self, test_db, sample_dataframe):
        """Test getting date range."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')

        min_date, max_date = repo.get_date_range('0700.HK')
        assert min_date is not None
        assert max_date is not None
        assert min_date <= max_date

    def test_get_all_symbols(self, test_db, sample_dataframe):
        """Test getting all symbols."""
        repo = test_db.get_repository()
        repo.insert_dataframe(sample_dataframe, '0700.HK')
        repo.insert_dataframe(sample_dataframe, '0388.HK')
        repo.insert_dataframe(sample_dataframe, '1398.HK')

        symbols = repo.get_all_symbols()
        assert len(symbols) == 3
        assert '0700.HK' in symbols


class TestDatabaseManager:
    """Test high-level database manager."""

    def test_manager_creation(self):
        """Test creating database manager."""
        manager = create_database_manager(test=True)
        assert manager is not None
        manager.close()

    def test_manager_initialization(self):
        """Test database initialization."""
        manager = create_database_manager(test=True)

        # Should have created tables
        conn = manager.connection
        inspector_obj = inspect(conn.engine)
        tables = inspector_obj.get_table_names()
        assert 'ohlcv_data' in tables

        manager.close()

    def test_manager_repository(self, test_db):
        """Test getting repository from manager."""
        repo = test_db.get_repository()
        assert isinstance(repo, DataRepository)

    def test_manager_context_manager(self):
        """Test using manager as context manager."""
        with create_database_manager(test=True) as manager:
            repo = manager.get_repository()
            assert repo is not None


class TestDatabaseIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self):
        """Test complete CRUD workflow."""
        with create_database_manager(test=True) as manager:
            repo = manager.get_repository()

            # Create
            record = OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 2, tzinfo=timezone.utc),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
            )
            repo.insert_record(record)

            # Read
            retrieved = repo.get_by_symbol('0700.HK')
            assert len(retrieved) == 1

            # Update
            repo.update_record(retrieved[0].id, {'quality_score': 0.95})

            # Delete
            repo.delete_by_symbol('0700.HK')
            assert repo.count_by_symbol('0700.HK') == 0

    def test_multi_symbol_workflow(self):
        """Test working with multiple symbols."""
        with create_database_manager(test=True) as manager:
            repo = manager.get_repository()

            dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
            df = pd.DataFrame({
                'open': np.random.uniform(100, 102, 20),
                'high': np.random.uniform(102, 105, 20),
                'low': np.random.uniform(98, 100, 20),
                'close': np.random.uniform(100, 102, 20),
                'volume': np.random.randint(1000000, 5000000, 20),
            }, index=dates)

            repo.insert_dataframe(df, '0700.HK')
            repo.insert_dataframe(df, '0388.HK')
            repo.insert_dataframe(df, '1398.HK')

            symbols = repo.get_all_symbols()
            assert len(symbols) == 3

            for symbol in symbols:
                assert repo.count_by_symbol(symbol) == 20


class TestDatabaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe_insert(self, test_db):
        """Test inserting empty DataFrame."""
        repo = test_db.get_repository()
        empty_df = pd.DataFrame()
        count = repo.insert_dataframe(empty_df, '0700.HK')
        assert count == 0

    def test_single_row_dataframe(self, test_db):
        """Test inserting single row DataFrame."""
        repo = test_db.get_repository()
        df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000],
        }, index=pd.date_range('2024-01-01', periods=1, freq='D', tz='UTC'))

        count = repo.insert_dataframe(df, '0700.HK')
        assert count == 1

    def test_duplicate_insert_different_symbols(self, test_db):
        """Test inserting same date for different symbols."""
        repo = test_db.get_repository()
        date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        record1 = OHLCVData(
            symbol='0700.HK', date=date,
            open_price=100, high_price=102, low_price=99, close_price=101, volume=1000000
        )
        record2 = OHLCVData(
            symbol='0388.HK', date=date,
            open_price=50, high_price=52, low_price=49, close_price=51, volume=500000
        )

        repo.insert_record(record1)
        repo.insert_record(record2)

        assert repo.count_by_symbol('0700.HK') == 1
        assert repo.count_by_symbol('0388.HK') == 1

    def test_query_nonexistent_symbol(self, test_db):
        """Test querying nonexistent symbol."""
        repo = test_db.get_repository()
        result = repo.get_by_symbol('NONEXISTENT')
        assert len(result) == 0

    def test_get_nonexistent_record(self, test_db):
        """Test getting nonexistent record."""
        repo = test_db.get_repository()
        result = repo.get_by_symbol_date('0700.HK', datetime(2024, 1, 1, tzinfo=timezone.utc))
        assert result is None


class TestDatabasePerformance:
    """Test performance characteristics."""

    def test_batch_insert_performance(self, test_db):
        """Test performance of batch insert."""
        import time
        repo = test_db.get_repository()

        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
            )
            for i in range(1000)
        ]

        start = time.time()
        repo.insert_batch(records)
        elapsed = time.time() - start

        # Should insert 1000 records in < 5 seconds
        assert elapsed < 5, f"Batch insert took {elapsed:.2f}s"

    def test_large_query_performance(self, test_db):
        """Test performance of large queries."""
        import time
        repo = test_db.get_repository()

        # Insert 1000 records
        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i),
                open_price=100.0,
                high_price=102.0,
                low_price=99.0,
                close_price=101.0,
                volume=1000000,
            )
            for i in range(1000)
        ]
        repo.insert_batch(records)

        # Query all records
        start = time.time()
        results = repo.get_by_symbol('0700.HK')
        elapsed = time.time() - start

        assert len(results) == 1000
        # Should query 1000 records in < 2 seconds
        assert elapsed < 2, f"Query took {elapsed:.2f}s"

    def test_dataframe_conversion_performance(self, test_db):
        """Test performance of converting to DataFrame."""
        import time
        repo = test_db.get_repository()

        # Insert 1000 records
        records = [
            OHLCVData(
                symbol='0700.HK',
                date=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i),
                open_price=100.0 + (i % 5),
                high_price=102.0 + (i % 5),
                low_price=99.0 + (i % 5),
                close_price=101.0 + (i % 5),
                volume=1000000 + i,
            )
            for i in range(1000)
        ]
        repo.insert_batch(records)
        results = repo.get_by_symbol('0700.HK')

        # Convert to DataFrame
        start = time.time()
        df = repo.to_dataframe(results)
        elapsed = time.time() - start

        assert len(df) == 1000
        # Should convert 1000 records in < 1 second
        assert elapsed < 1, f"Conversion took {elapsed:.2f}s"


# Test execution
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
