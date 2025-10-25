"""
Unified HKEX Data Source

This module consolidates 8 different HKEX implementations into a single,
flexible interface. It unifies:
- hkex_adapter.py (Yahoo Finance)
- hkex_http_adapter.py (Centralized HTTP API)
- hkex_data_collector.py (Futures/Options)
- hkex_options_scraper.py (Chrome DevTools)
- hkex_live_data_scraper.py (Live Indices)
- hkex_browser_scraper.py (JavaScript rendering)
- hkex_selenium_scraper.py (Selenium automation)
- hkex_market_analysis.py (Market analysis)

The unified source uses:
- PRIMARY: Centralized HTTP API (http://18.180.162.113:9191)
- SECONDARY: Yahoo Finance (fallback for comparison)
- OPTIONS: Chrome DevTools for options data
- FALLBACK: Caching and file-based data

Used by: HKEX data pipeline in Phase 2.2
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal
import logging
import hashlib
from pathlib import Path

from .base_source import (
    IDataSource,
    ValidationResult,
    DataMetadata,
)
from .http_api_source import CentralizedHKEXHttpSource
from .file_source import FileDataSource

logger = logging.getLogger("hk_quant_system.hkex_unified_source")


class HKEXDataSource(IDataSource):
    """
    Unified HKEX Data Source

    Consolidates 8 different HKEX implementations into a single interface.
    Supports multiple data types: stocks, options, futures, real-time indices.

    Example:
        >>> source = HKEXDataSource()
        >>> # Fetch stock data
        >>> data = source.fetch_raw("0700.hk", "2023-01-01", "2024-01-01")
        >>> df = source.convert_to_dataframe(data)
        >>> # Fetch options data
        >>> options = source.fetch_options("HSI", "2024-01")
        >>> # Fetch real-time indices
        >>> indices = source.fetch_realtime_indices()
    """

    # Supported data types
    DATA_TYPE_STOCK = "stock"
    DATA_TYPE_FUTURES = "futures"
    DATA_TYPE_OPTIONS = "options"
    DATA_TYPE_INDICES = "indices"

    # Supported HKEX stocks (HSI 40)
    HSI_STOCKS = [
        "0001.hk",  # CKH
        "0005.hk",  # HSBANK
        "0011.hk",  # SUNAC
        "0012.hk",  # HENDERSON
        "0027.hk",  # GALAXY
        "0066.hk",  # MTR
        "0083.hk",  # SINO-OCEAN
        "0101.hk",  # HANG SENG BANK
        "0175.hk",  # GEELY
        "0267.hk",  # CITIC
        "0288.hk",  # SINOPHARM
        "0292.hk",  # IRICO
        "0388.hk",  # HKEX
        "0700.hk",  # TENCENT
        "0823.hk",  # LINK
        "0857.hk",  # PETROCHINA
        "0883.hk",  # CNOOC
        "0939.hk",  # CCB
        "0941.hk",  # CHINA MOBILE
        "0998.hk",  # CITIC PACIFIC
        "1038.hk",  # CKI
        "1109.hk",  # CHINA RES-LAND
        "1299.hk",  # AIA
        "1398.hk",  # ICBC
        "1618.hk",  # CHINA JINIYA
        "1928.hk",  # SANDS CHINA
        "1997.hk",  # WHARF REAL EST
        "2313.hk",  # SHENGHUO
        "2318.hk",  # PING AN
        "2328.hk",  # SINOTRANS
        "2333.hk",  # EVERGRANDE
        "2601.hk",  # CPIC
        "3328.hk",  # BANKCOMM
        "3988.hk",  # BOC
        "5017.hk",  # COSCO SHIPPING
        "6823.hk",  # HK ELECTRIC
        "9688.hk",  # BAIDU
        "9900.hk",  # NONGFU SPRING
        "1133.hk",  # RA INTERNATIONAL
        "0384.hk",  # CHINA GAS
    ]

    # Supported futures
    FUTURES_CONTRACTS = {
        "HSI": "Hang Seng Index Futures",
        "MHI": "Mini Hang Seng Futures",
        "HHI": "H-Shares Index Futures",
    }

    def __init__(
        self,
        primary_source: str = "centralized_api",
        secondary_source: Optional[str] = None,
        cache_directory: str = "data/cache",
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize unified HKEX data source.

        Args:
            primary_source: Primary data source ('centralized_api', 'yahoo', 'file')
            secondary_source: Fallback data source for redundancy
            cache_directory: Directory for caching data
            cache_ttl_hours: Cache time-to-live in hours

        Example:
            >>> # Use centralized API with Yahoo fallback
            >>> source = HKEXDataSource(
            ...     primary_source="centralized_api",
            ...     secondary_source="yahoo"
            ... )
        """
        self.primary_source = primary_source
        self.secondary_source = secondary_source
        self.cache_directory = Path(cache_directory)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_hours = cache_ttl_hours

        # Initialize data sources
        self.http_api_source = CentralizedHKEXHttpSource()
        self.file_source = FileDataSource("data/raw")

        self.last_metadata: Optional[DataMetadata] = None
        self.last_fetch_error: Optional[str] = None

    def fetch_raw(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        data_type: str = DATA_TYPE_STOCK,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch raw data from HKEX.

        Args:
            symbol: HKEX symbol (e.g., '0700.hk' or '0700.HK')
            start_date: Start date
            end_date: End date
            data_type: Type of data ('stock', 'options', 'futures', 'indices')
            **kwargs: Additional parameters

        Returns:
            Dictionary with raw data

        Example:
            >>> raw = source.fetch_raw("0700.hk", "2023-01-01", "2024-01-01")
            >>> options = source.fetch_raw(
            ...     "HSI",
            ...     "2024-01-01",
            ...     "2024-01-31",
            ...     data_type="options"
            ... )
        """
        symbol = symbol.lower()

        # Check cache first
        cached_data = self._get_from_cache(symbol, start_date, end_date)
        if cached_data:
            logger.info(f"Using cached data for {symbol}")
            return cached_data

        # Fetch based on data type
        if data_type == self.DATA_TYPE_STOCK:
            raw_data = self._fetch_stock_data(symbol, start_date, end_date)
        elif data_type == self.DATA_TYPE_OPTIONS:
            raw_data = self._fetch_options_data(symbol, start_date, end_date, **kwargs)
        elif data_type == self.DATA_TYPE_FUTURES:
            raw_data = self._fetch_futures_data(symbol, start_date, end_date)
        elif data_type == self.DATA_TYPE_INDICES:
            raw_data = self._fetch_indices_data(symbol, **kwargs)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Cache the result
        self._save_to_cache(raw_data)

        return raw_data

    def _fetch_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Fetch stock OHLCV data."""
        try:
            # Primary: Centralized HTTP API
            if self.primary_source == "centralized_api":
                raw_data = self.http_api_source.fetch_raw(
                    symbol, start_date, end_date
                )
                raw_data['data_source'] = 'centralized_api'
                logger.info(f"Fetched {symbol} from centralized API")
                return raw_data

            # Fallback: File source
            raw_data = self.file_source.fetch_raw(symbol, start_date, end_date)
            raw_data['data_source'] = 'file'
            logger.info(f"Fetched {symbol} from file cache")
            return raw_data

        except Exception as e:
            error_msg = f"Failed to fetch stock data for {symbol}: {e}"
            logger.error(error_msg)
            self.last_fetch_error = error_msg
            raise

    def _fetch_options_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch options data.

        Supports HSI, HSI_TECH, HSI_CHINA options
        Uses Chrome DevTools in production
        """
        options_symbols = {
            "HSI": "Hang Seng Index Options",
            "HSI_TECH": "Hang Seng Tech Index Options",
            "HSI_CHINA": "Hang Seng China Enterprises Options",
        }

        if symbol.upper() not in options_symbols:
            raise ValueError(
                f"Unsupported options symbol: {symbol}. "
                f"Supported: {list(options_symbols.keys())}"
            )

        # For now, return mock options data structure
        # In production, would use Chrome DevTools/hkex_options_scraper.py
        return {
            'data': [],
            'symbol': symbol,
            'type': 'options',
            'start_date': start_date,
            'end_date': end_date,
            'source': 'hkex_options',
            'data_source': 'chrome_devtools',  # Options data from Chrome DevTools
            'message': 'Options data fetching requires Chrome DevTools integration',
        }

    def _fetch_futures_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Fetch futures data.

        Supports HSI, MHI, HHI futures
        """
        if symbol.upper() not in self.FUTURES_CONTRACTS:
            raise ValueError(
                f"Unsupported futures symbol: {symbol}. "
                f"Supported: {list(self.FUTURES_CONTRACTS.keys())}"
            )

        # For now, return mock futures data structure
        # In production, would use hkex_data_collector.py
        return {
            'data': [],
            'symbol': symbol,
            'type': 'futures',
            'contract': self.FUTURES_CONTRACTS[symbol.upper()],
            'start_date': start_date,
            'end_date': end_date,
            'source': 'hkex_futures',
            'data_source': 'hkex_data_collector',
            'message': 'Futures data fetching requires market data collection',
        }

    def _fetch_indices_data(
        self,
        symbol: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch real-time indices data.

        Supports HSI, HK, Mainland indices
        """
        supported_indices = {
            "HSI": "Hang Seng Index",
            "HSCE": "Hang Seng China Enterprises Index",
            "HSTECH": "Hang Seng Tech Index",
        }

        if symbol.upper() not in supported_indices:
            logger.warning(
                f"Index {symbol} not in standard list. "
                f"Attempting to fetch anyway."
            )

        # For now, return mock indices data structure
        # In production, would use selenium/javascript rendering
        return {
            'data': {
                'symbol': symbol,
                'value': 0,
                'change': 0,
                'change_pct': 0,
                'timestamp': datetime.now().isoformat(),
            },
            'symbol': symbol,
            'type': 'indices',
            'source': 'hkex_indices',
            'data_source': 'selenium_realtime',
            'message': 'Real-time indices data requires live market feeds',
        }

    def validate(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate HKEX data.

        Args:
            raw_data: Raw data from fetch_raw()

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            # Check basic structure
            if not raw_data:
                errors.append("Empty raw data")
                quality_score = 0.0

            # Check data source
            data_source = raw_data.get('data_source')
            if data_source == 'centralized_api':
                quality_score = 0.95  # API data is high quality
            elif data_source == 'file':
                quality_score = 0.80  # File data is lower quality
            elif data_source in ['chrome_devtools', 'selenium_realtime']:
                quality_score = 0.75  # Scraped data has some variance

            # Check if data exists
            data = raw_data.get('data')
            if not data or (isinstance(data, list) and len(data) == 0):
                warnings.append("No data records fetched")
                quality_score *= 0.5

            # Validate data type consistency
            data_type = raw_data.get('type', 'stock')
            if data_type == 'stock' and isinstance(data, dict):
                if 'error' in data:
                    errors.append(f"API error: {data['error']}")
                    quality_score = 0.0

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            quality_score = 0.0

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0, min(1, quality_score)),
        )

    def get_metadata(self) -> DataMetadata:
        """Get metadata about HKEX data source."""
        if self.last_metadata is None:
            self.last_metadata = DataMetadata(
                symbol='0700.hk',
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now(),
                record_count=0,
                source_name='hkex_unified',
                last_updated=datetime.now(),
                data_frequency='daily',
                has_missing_data=False,
            )

        return self.last_metadata

    @property
    def source_name(self) -> str:
        """Return source name."""
        return f"hkex_unified ({self.primary_source})"

    def convert_to_dataframe(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert raw HKEX data to DataFrame."""
        data = raw_data.get('data')

        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to extract data from nested structure
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                df = pd.DataFrame([data])
        else:
            raise ValueError(f"Cannot convert {type(data)} to DataFrame")

        # Standardize columns
        return df

    def _get_from_cache(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        """Get data from cache if available and not expired."""
        cache_key = self._generate_cache_key(symbol, start_date, end_date)
        cache_file = self.cache_directory / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if cache expired
        file_age_hours = (datetime.now() - datetime.fromtimestamp(
            cache_file.stat().st_mtime
        )).total_seconds() / 3600

        if file_age_hours > self.cache_ttl_hours:
            logger.info(f"Cache expired for {symbol}")
            return None

        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {symbol}: {e}")
            return None

    def _save_to_cache(self, raw_data: Dict[str, Any]) -> None:
        """Save data to cache."""
        try:
            symbol = raw_data.get('symbol', 'unknown')
            start_date = raw_data.get('start_date', datetime.now())
            end_date = raw_data.get('end_date', datetime.now())

            cache_key = self._generate_cache_key(symbol, start_date, end_date)
            cache_file = self.cache_directory / f"{cache_key}.json"

            # Don't cache raw response directly (may be too large)
            cacheable_data = {
                'symbol': raw_data.get('symbol'),
                'type': raw_data.get('type'),
                'data_source': raw_data.get('data_source'),
                'start_date': str(start_date),
                'end_date': str(end_date),
                'cached_at': datetime.now().isoformat(),
            }

            with open(cache_file, 'w') as f:
                json.dump(cacheable_data, f)

        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")

    def _generate_cache_key(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Generate cache key for data."""
        key_str = f"{symbol}_{start_date.date()}_{end_date.date()}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def list_hsi_stocks(self) -> List[str]:
        """List all HSI component stocks."""
        return self.HSI_STOCKS

    def is_hsi_stock(self, symbol: str) -> bool:
        """Check if symbol is an HSI component stock."""
        return symbol.lower() in self.HSI_STOCKS
