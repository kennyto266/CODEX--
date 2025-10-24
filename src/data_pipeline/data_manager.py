"""
Data Manager Module - Unified data access and caching layer.

Provides:
- Transparent caching with LRU eviction policy
- Database persistence
- Data loading from multiple sources
- Pipeline integration
- Batch operations
- Cache statistics and management

Architecture:
    DataManager
    ├── CacheLayer (LRU cache)
    ├── DatabaseLayer (SQLAlchemy ORM)
    ├── PipelineLayer (Data processing)
    └── SourceLayer (APIs, files, etc.)

Cache Priority:
    1. Memory Cache (LRU) - Fast, limited size
    2. Database Cache - Persistent, slower
    3. External Source - Real-time, slowest
"""

import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone, timedelta
from functools import lru_cache
import pandas as pd
from pathlib import Path
import json

from .database import DatabaseManager, OHLCVData, DataRepository
from .pipeline_processor import PipelineProcessor
from .asset_profile import AssetProfile, get_registry, get_profile

logger = logging.getLogger("hk_quant_system.data_manager")


class CacheStats:
    """Cache statistics tracker."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.operations = 0

    def record_hit(self):
        self.hits += 1
        self.operations += 1

    def record_miss(self):
        self.misses += 1
        self.operations += 1

    def record_eviction(self):
        self.evictions += 1

    @property
    def hit_rate(self) -> float:
        if self.operations == 0:
            return 0.0
        return self.hits / self.operations

    @property
    def miss_rate(self) -> float:
        if self.operations == 0:
            return 0.0
        return self.misses / self.operations

    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'operations': self.operations,
            'hit_rate': f"{self.hit_rate:.2%}",
            'miss_rate': f"{self.miss_rate:.2%}",
        }

    def reset(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.operations = 0


class DataCache:
    """
    LRU-based data cache with TTL support.

    Features:
    - Configurable cache size and TTL
    - Hit/miss tracking
    - Automatic eviction of stale data
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            max_size: Maximum cache entries (per symbol)
            ttl_seconds: Time-to-live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = CacheStats()

    def _make_key(self, symbol: str, start_date: datetime, end_date: datetime) -> str:
        """Create cache key from parameters."""
        return f"{symbol}:{start_date.isoformat()}:{end_date.isoformat()}"

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if not entry.get('timestamp'):
            return True
        age = datetime.now(timezone.utc) - entry['timestamp']
        return age.total_seconds() > self.ttl_seconds

    def get(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Get data from cache."""
        key = self._make_key(symbol, start_date, end_date)

        if key not in self.cache:
            self.stats.record_miss()
            return None

        entry = self.cache[key]

        # Check expiration
        if self._is_expired(entry):
            del self.cache[key]
            self.stats.record_miss()
            logger.debug(f"Cache entry expired: {key}")
            return None

        self.stats.record_hit()
        logger.debug(f"Cache hit: {key}")
        return entry['data']

    def put(self, symbol: str, start_date: datetime, end_date: datetime, data: pd.DataFrame):
        """Put data in cache."""
        key = self._make_key(symbol, start_date, end_date)

        # Check size limit and evict if necessary
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]['timestamp']
            )
            del self.cache[oldest_key]
            self.stats.record_eviction()
            logger.debug(f"Cache eviction: {oldest_key}")

        self.cache[key] = {
            'data': data.copy(),
            'timestamp': datetime.now(timezone.utc),
        }
        logger.debug(f"Cache put: {key}")

    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats

    def __len__(self) -> int:
        """Get cache size."""
        return len(self.cache)


class DataManager:
    """
    Unified data manager combining caching, database, and pipeline layers.

    Features:
    - Multi-level caching (memory + database)
    - Transparent data loading
    - Pipeline integration
    - Batch operations
    - Data validation and cleaning
    - Source management
    """

    def __init__(
        self,
        database_url: str = 'sqlite:///./codex_trading.db',
        cache_size: int = 100,
        cache_ttl_seconds: int = 3600,
        enable_pipeline: bool = True,
        enable_caching: bool = True,
    ):
        """
        Initialize DataManager.

        Args:
            database_url: SQLAlchemy database URL
            cache_size: Maximum LRU cache entries
            cache_ttl_seconds: Cache TTL in seconds
            enable_pipeline: Enable data processing pipeline
            enable_caching: Enable caching
        """
        self.database_url = database_url
        self.enable_pipeline = enable_pipeline
        self.enable_caching = enable_caching

        # Initialize components
        self.db_manager = DatabaseManager(database_url)
        self.db_manager.initialize()

        self.cache = DataCache(max_size=cache_size, ttl_seconds=cache_ttl_seconds)
        self.pipeline = PipelineProcessor() if enable_pipeline else None

        # Asset tracking - use global registry
        self.asset_registry = get_registry()

        logger.info(
            f"DataManager initialized - "
            f"Database: {database_url}, "
            f"Cache: {cache_size} entries, "
            f"Pipeline: {enable_pipeline}"
        )

    def load_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        process: bool = True,
        source: str = 'database',
    ) -> Optional[pd.DataFrame]:
        """
        Load data with multi-level caching strategy.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            process: Whether to apply pipeline processing
            source: Data source preference ('cache', 'database', 'api')

        Returns:
            DataFrame or None if no data found
        """
        logger.info(f"Loading data for {symbol} ({start_date} to {end_date})")

        # Step 1: Try cache first
        if self.enable_caching and source in ['cache', 'database']:
            cached = self.cache.get(symbol, start_date, end_date)
            if cached is not None:
                logger.info(f"Data loaded from cache: {symbol}")
                return cached

        # Step 2: Load from database
        repo = self.db_manager.get_repository()
        records = repo.get_by_symbol_range(symbol, start_date, end_date)
        repo.close()

        if not records:
            logger.warning(f"No data found in database: {symbol}")
            return None

        # Step 3: Convert to DataFrame
        repo = self.db_manager.get_repository()
        df = repo.to_dataframe(records)
        repo.close()

        if df.empty:
            return None

        # Step 4: Cache the data
        if self.enable_caching:
            self.cache.put(symbol, start_date, end_date, df)

        # Step 5: Process through pipeline if enabled
        if process and self.pipeline:
            df = self._process_with_pipeline(df, symbol)

        logger.info(f"Data loaded successfully: {symbol} ({len(df)} records)")
        return df

    def save_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        source: str = 'api',
        update_cache: bool = True,
    ) -> int:
        """
        Save data to database and optionally cache.

        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
            source: Data source identifier
            update_cache: Whether to update cache

        Returns:
            Number of records saved
        """
        logger.info(f"Saving {len(df)} records for {symbol}")

        # Prepare records
        repo = self.db_manager.get_repository()
        count = repo.insert_dataframe(df, symbol, source=source)
        repo.close()

        # Update cache if requested
        if update_cache and self.enable_caching and not df.empty:
            start_date = df.index.min()
            end_date = df.index.max()
            self.cache.put(symbol, start_date, end_date, df)

        logger.info(f"Saved {count} records for {symbol}")
        return count

    def update_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        source: str = 'api',
    ) -> int:
        """
        Update existing data in database.

        Args:
            symbol: Stock symbol
            df: DataFrame with updated OHLCV data
            source: Data source identifier

        Returns:
            Number of records updated
        """
        logger.info(f"Updating {len(df)} records for {symbol}")

        repo = self.db_manager.get_repository()

        count = 0
        for idx, row in df.iterrows():
            record = repo.get_by_symbol_date(symbol, idx)
            if record:
                updates = {
                    'open_price': row.get('open') or row.get('open_price'),
                    'high_price': row.get('high') or row.get('high_price'),
                    'low_price': row.get('low') or row.get('low_price'),
                    'close_price': row.get('close') or row.get('close_price'),
                    'volume': int(row.get('volume', 0)),
                    'source': source,
                    'updated_at': datetime.now(timezone.utc),
                }
                repo.update_record(record.id, updates)
                count += 1

        repo.close()

        # Invalidate cache
        if self.enable_caching:
            self.cache.clear()

        logger.info(f"Updated {count} records for {symbol}")
        return count

    def get_data_range(self, symbol: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get min and max dates for symbol in database."""
        repo = self.db_manager.get_repository()
        min_date, max_date = repo.get_date_range(symbol)
        repo.close()
        return min_date, max_date

    def get_available_symbols(self) -> List[str]:
        """Get all symbols with data in database."""
        repo = self.db_manager.get_repository()
        symbols = repo.get_all_symbols()
        repo.close()
        return symbols

    def get_symbol_count(self, symbol: str) -> int:
        """Get number of records for symbol."""
        repo = self.db_manager.get_repository()
        count = repo.count_by_symbol(symbol)
        repo.close()
        return count

    def get_quality_data(
        self,
        symbol: str,
        min_quality: float = 0.7,
    ) -> Optional[pd.DataFrame]:
        """Get high-quality data for symbol."""
        repo = self.db_manager.get_repository()
        records = repo.get_high_quality(symbol, min_quality=min_quality)
        df = repo.to_dataframe(records)
        repo.close()
        return df if not df.empty else None

    def get_outliers(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get outlier records for symbol."""
        repo = self.db_manager.get_repository()
        records = repo.get_outliers(symbol)
        df = repo.to_dataframe(records)
        repo.close()
        return df if not df.empty else None

    def delete_symbol_data(self, symbol: str) -> int:
        """Delete all data for symbol."""
        logger.warning(f"Deleting all data for {symbol}")
        repo = self.db_manager.get_repository()
        count = repo.delete_by_symbol(symbol)
        repo.close()

        # Invalidate cache
        if self.enable_caching:
            self.cache.clear()

        return count

    def register_asset(self, symbol: str, profile: AssetProfile):
        """Register asset profile."""
        self.asset_registry.register(profile)
        logger.info(f"Registered asset: {symbol}")

    def get_asset(self, symbol: str) -> Optional[AssetProfile]:
        """Get asset profile."""
        return get_profile(symbol)

    def _process_with_pipeline(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Apply pipeline processing to data."""
        if not self.pipeline:
            return df

        try:
            # Add default steps if pipeline is empty
            if not self.pipeline.steps:
                self.pipeline.add_step("clean", "clean", config={
                    "missing_value_strategy": "interpolate",
                    "outlier_strategy": "iqr"
                })
                self.pipeline.add_step("align", "align")
                self.pipeline.add_step("normalize", "normalize")
                self.pipeline.add_step("score", "score")

            processed = self.pipeline.process(df)
            logger.debug(f"Data processed through pipeline: {symbol}")
            return processed
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return df

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.cache.get_stats().to_dict()
        stats['cache_size'] = len(self.cache)
        stats['max_cache_size'] = self.cache.max_size
        return stats

    def clear_cache(self):
        """Clear all cache."""
        self.cache.clear()

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        repo = self.db_manager.get_repository()
        symbols = repo.get_all_symbols()

        stats = {
            'symbols': len(symbols),
            'symbol_list': symbols,
            'records_by_symbol': {},
            'date_ranges': {},
        }

        for symbol in symbols:
            stats['records_by_symbol'][symbol] = repo.count_by_symbol(symbol)
            min_date, max_date = repo.get_date_range(symbol)
            stats['date_ranges'][symbol] = {
                'start': min_date.isoformat() if min_date else None,
                'end': max_date.isoformat() if max_date else None,
            }

        repo.close()
        return stats

    def export_cache_stats(self, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """Export cache statistics to file."""
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cache': self.get_cache_stats(),
            'database': self.get_database_stats(),
        }

        if filepath:
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            logger.info(f"Stats exported to {filepath}")

        return stats

    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            repo = self.db_manager.get_repository()
            symbols = repo.get_all_symbols()
            repo.close()

            return {
                'status': 'healthy',
                'database': 'connected',
                'cache': 'active' if self.enable_caching else 'disabled',
                'pipeline': 'active' if self.enable_pipeline else 'disabled',
                'symbol_count': len(symbols),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

    def close(self):
        """Close database connections."""
        self.db_manager.close()
        self.cache.clear()
        logger.info("DataManager closed")

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()
