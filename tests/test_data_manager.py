"""
Tests for DataManager module.

Test Coverage:
- DataCache initialization and operations
- Cache statistics tracking
- Cache expiration and TTL
- DataManager initialization
- Data loading with caching
- Data persistence
- Data updates
- Asset management
- Cache and database statistics
- Context manager support
- Error handling
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

from src.data_pipeline.data_manager import DataManager, DataCache, CacheStats
from src.data_pipeline.asset_profile import AssetProfile, Market, Currency, reset_registry


class TestCacheStats:
    """Test CacheStats tracking."""

    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.operations == 0

    def test_record_hit(self):
        """Test recording cache hit."""
        stats = CacheStats()
        stats.record_hit()
        assert stats.hits == 1
        assert stats.operations == 1

    def test_record_miss(self):
        """Test recording cache miss."""
        stats = CacheStats()
        stats.record_miss()
        assert stats.misses == 1
        assert stats.operations == 1

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        assert abs(stats.hit_rate - 2/3) < 0.01

    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()

        result = stats.to_dict()
        assert result['hits'] == 1
        assert result['misses'] == 1
        assert 'hit_rate' in result
        assert 'miss_rate' in result

    def test_stats_reset(self):
        """Test resetting stats."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()
        assert stats.operations == 2

        stats.reset()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.operations == 0


class TestDataCache:
    """Test DataCache functionality."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = DataCache(max_size=50, ttl_seconds=1800)
        assert cache.max_size == 50
        assert cache.ttl_seconds == 1800
        assert len(cache) == 0

    def test_cache_put_get(self):
        """Test putting and getting data from cache."""
        cache = DataCache()
        df = pd.DataFrame({
            'open': [100, 101],
            'close': [101, 102],
        })

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        cache.put('0700.hk', start_date, end_date, df)
        retrieved = cache.get('0700.hk', start_date, end_date)

        assert retrieved is not None
        assert len(retrieved) == 2

    def test_cache_miss(self):
        """Test cache miss."""
        cache = DataCache()
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        result = cache.get('0700.hk', start_date, end_date)
        assert result is None
        assert cache.stats.misses == 1

    def test_cache_hit(self):
        """Test cache hit."""
        cache = DataCache()
        df = pd.DataFrame({'close': [100, 101]})

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        cache.put('0700.hk', start_date, end_date, df)
        cache.get('0700.hk', start_date, end_date)

        assert cache.stats.hits == 1

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = DataCache(ttl_seconds=1)
        df = pd.DataFrame({'close': [100, 101]})

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        cache.put('0700.hk', start_date, end_date, df)

        # Wait for expiration
        import time
        time.sleep(1.1)

        result = cache.get('0700.hk', start_date, end_date)
        assert result is None

    def test_cache_eviction(self):
        """Test cache eviction when max size reached."""
        cache = DataCache(max_size=2)
        df = pd.DataFrame({'close': [100]})

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        # Add 3 entries, should evict oldest
        cache.put('0700.hk', start_date, end_date, df)
        cache.put('0388.hk', start_date, end_date, df)
        cache.put('1398.hk', start_date, end_date, df)

        assert len(cache) == 2
        assert cache.stats.evictions == 1

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = DataCache()
        df = pd.DataFrame({'close': [100]})

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        cache.put('0700.hk', start_date, end_date, df)
        assert len(cache) == 1

        cache.clear()
        assert len(cache) == 0


class TestDataManager:
    """Test DataManager functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'
            db_url = f'sqlite:///{db_path}'
            yield db_url

    @pytest.fixture
    def manager(self, temp_db):
        """Create DataManager instance."""
        manager = DataManager(
            database_url=temp_db,
            cache_size=50,
            cache_ttl_seconds=3600,
            enable_pipeline=False,  # Disable pipeline for unit tests
        )
        yield manager
        manager.close()

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'open': np.random.uniform(100, 120, 100),
            'high': np.random.uniform(120, 130, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 120, 100),
            'volume': np.random.randint(1000000, 10000000, 100),
            'quality_score': np.random.uniform(0.7, 1.0, 100),
        }, index=dates)

    def test_manager_initialization(self, temp_db):
        """Test DataManager initialization."""
        manager = DataManager(database_url=temp_db, enable_pipeline=False)
        assert manager.enable_caching is True
        assert manager.enable_pipeline is False
        assert manager.asset_registry is not None
        manager.close()

    def test_save_data(self, manager, sample_data):
        """Test saving data."""
        count = manager.save_data('0700.hk', sample_data)
        assert count == 100

        # Verify data was saved
        symbols = manager.get_available_symbols()
        assert '0700.hk' in symbols

    def test_load_data_from_database(self, manager, sample_data):
        """Test loading data from database."""
        manager.save_data('0700.hk', sample_data)

        start_date = sample_data.index[0]
        end_date = sample_data.index[-1]

        loaded = manager.load_data('0700.hk', start_date, end_date, process=False)
        assert loaded is not None
        assert len(loaded) == 100

    def test_cache_hit_on_reload(self, manager, sample_data):
        """Test cache hit when reloading data."""
        manager.save_data('0700.hk', sample_data)

        start_date = sample_data.index[0]
        end_date = sample_data.index[-1]

        # First load - cache miss
        manager.load_data('0700.hk', start_date, end_date, process=False)
        initial_hits = manager.get_cache_stats()['hits']

        # Second load - cache hit
        manager.load_data('0700.hk', start_date, end_date, process=False)
        final_hits = manager.get_cache_stats()['hits']

        # Second load should have more hits than first
        assert final_hits > initial_hits

    def test_update_data(self, manager, sample_data):
        """Test updating data."""
        manager.save_data('0700.hk', sample_data)

        # Modify some data
        updated_data = sample_data.copy()
        updated_data['close'] = updated_data['close'] * 1.1

        count = manager.update_data('0700.hk', updated_data)
        assert count == 100

    def test_get_data_range(self, manager, sample_data):
        """Test getting data range."""
        manager.save_data('0700.hk', sample_data)

        min_date, max_date = manager.get_data_range('0700.hk')
        assert min_date is not None
        assert max_date is not None
        assert min_date < max_date

    def test_get_available_symbols(self, manager, sample_data):
        """Test getting available symbols."""
        manager.save_data('0700.hk', sample_data)
        manager.save_data('0388.hk', sample_data)

        symbols = manager.get_available_symbols()
        assert '0700.hk' in symbols
        assert '0388.hk' in symbols

    def test_get_symbol_count(self, manager, sample_data):
        """Test getting record count."""
        manager.save_data('0700.hk', sample_data)
        count = manager.get_symbol_count('0700.hk')
        assert count == 100

    def test_get_quality_data(self, manager, sample_data):
        """Test getting high-quality data."""
        manager.save_data('0700.hk', sample_data)

        quality_data = manager.get_quality_data('0700.hk', min_quality=0.8)
        # Some records may have quality > 0.8 based on random data
        assert quality_data is None or isinstance(quality_data, pd.DataFrame)

    def test_delete_symbol_data(self, manager, sample_data):
        """Test deleting symbol data."""
        manager.save_data('0700.hk', sample_data)
        count = manager.delete_symbol_data('0700.hk')
        assert count == 100

        # Verify data was deleted
        symbols = manager.get_available_symbols()
        assert '0700.hk' not in symbols

    def test_register_asset(self, manager):
        """Test registering asset profile."""
        profile = AssetProfile(
            symbol='9999.hk',
            name='Test Company',
            market=Market.HKEX,
            currency=Currency.HKD,
        )
        manager.register_asset('9999.hk', profile)
        retrieved = manager.get_asset('9999.hk')
        assert retrieved is not None
        assert retrieved.symbol == '9999.hk'

    def test_cache_statistics(self, manager, sample_data):
        """Test cache statistics."""
        manager.save_data('0700.hk', sample_data)

        start_date = sample_data.index[0]
        end_date = sample_data.index[-1]

        manager.load_data('0700.hk', start_date, end_date, process=False)
        manager.load_data('0700.hk', start_date, end_date, process=False)

        stats = manager.get_cache_stats()
        assert stats['hits'] >= 1
        assert 'hit_rate' in stats

    def test_database_statistics(self, manager, sample_data):
        """Test database statistics."""
        manager.save_data('0700.hk', sample_data)

        stats = manager.get_database_stats()
        assert stats['symbols'] >= 1
        assert '0700.hk' in stats['symbol_list']
        assert stats['records_by_symbol']['0700.hk'] == 100

    def test_clear_cache(self, manager, sample_data):
        """Test clearing cache."""
        manager.save_data('0700.hk', sample_data)

        start_date = sample_data.index[0]
        end_date = sample_data.index[-1]

        manager.load_data('0700.hk', start_date, end_date, process=False)
        assert len(manager.cache) > 0

        manager.clear_cache()
        assert len(manager.cache) == 0

    def test_health_check(self, manager, sample_data):
        """Test health check."""
        health = manager.health_check()
        assert health['status'] == 'healthy'
        assert 'database' in health
        assert 'cache' in health

        manager.save_data('0700.hk', sample_data)
        health = manager.health_check()
        assert health['symbol_count'] == 1

    def test_context_manager(self, temp_db):
        """Test context manager support."""
        with DataManager(database_url=temp_db, enable_pipeline=False) as manager:
            assert manager is not None
        # Manager should be closed after context exit

    def test_export_cache_stats(self, manager, sample_data):
        """Test exporting cache statistics."""
        manager.save_data('0700.hk', sample_data)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'stats.json'
            stats = manager.export_cache_stats(filepath=filepath)

            assert filepath.exists()
            assert 'cache' in stats
            assert 'database' in stats

    def test_multi_symbol_workflow(self, manager, sample_data):
        """Test workflow with multiple symbols."""
        symbols = ['0700.hk', '0388.hk', '1398.hk']

        for symbol in symbols:
            manager.save_data(symbol, sample_data)

        # Verify all symbols saved
        available = manager.get_available_symbols()
        for symbol in symbols:
            assert symbol in available

        # Verify counts
        for symbol in symbols:
            count = manager.get_symbol_count(symbol)
            assert count == 100

    def test_load_nonexistent_data(self, manager):
        """Test loading non-existent data."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = manager.load_data('0000.hk', start_date, end_date, process=False)
        assert result is None

    def test_disable_caching(self, temp_db, sample_data):
        """Test DataManager with caching disabled."""
        manager = DataManager(
            database_url=temp_db,
            enable_caching=False,
            enable_pipeline=False,
        )

        manager.save_data('0700.hk', sample_data)

        start_date = sample_data.index[0]
        end_date = sample_data.index[-1]

        manager.load_data('0700.hk', start_date, end_date, process=False)
        stats = manager.get_cache_stats()

        # No cache operations should be recorded
        assert stats['operations'] == 0

        manager.close()

    def test_large_dataset(self, manager):
        """Test handling large dataset."""
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        large_data = pd.DataFrame({
            'open': np.random.uniform(100, 120, 1000),
            'high': np.random.uniform(120, 130, 1000),
            'low': np.random.uniform(90, 100, 1000),
            'close': np.random.uniform(100, 120, 1000),
            'volume': np.random.randint(1000000, 10000000, 1000),
        }, index=dates)

        count = manager.save_data('0700.hk', large_data)
        assert count == 1000

        start_date = large_data.index[0]
        end_date = large_data.index[-1]

        loaded = manager.load_data('0700.hk', start_date, end_date, process=False)
        assert len(loaded) == 1000
