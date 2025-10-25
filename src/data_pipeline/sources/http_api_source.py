"""
HTTP API Data Source Implementation

This module provides a generic HTTP API data source adapter that can fetch
data from any REST API endpoint. It implements the IDataSource interface.

Used by: Data pipeline for fetching data from external APIs
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from abc import abstractmethod

from .base_source import (
    IDataSource,
    ValidationResult,
    DataMetadata,
)

logger = logging.getLogger("hk_quant_system.http_api_source")


class HttpApiDataSource(IDataSource):
    """Generic HTTP API Data Source for fetching OHLCV data from REST APIs."""

    def __init__(
        self,
        base_url: str,
        endpoint: str = "/",
        api_key: Optional[str] = None,
        timeout: int = 30,
        retry_max: int = 3,
    ):
        """
        Initialize HTTP API data source.

        Args:
            base_url: Base URL of the API (e.g., 'http://18.180.162.113:9191')
            endpoint: API endpoint path (e.g., '/inst/getInst')
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30)
            retry_max: Maximum number of retry attempts (default: 3)

        Example:
            >>> source = HttpApiDataSource(
            ...     base_url="http://18.180.162.113:9191",
            ...     endpoint="/inst/getInst"
            ... )
            >>> data = source.fetch_raw("0700.hk", "2023-01-01", "2024-01-01")
        """
        self.base_url = base_url
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.retry_max = retry_max
        self.last_metadata: Optional[DataMetadata] = None
        self.session = requests.Session()

    def fetch_raw(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch raw data from HTTP API.

        Args:
            symbol: Stock symbol (e.g., '0700.hk')
            start_date: Start date for data fetch
            end_date: End date for data fetch
            **kwargs: Additional API parameters

        Returns:
            Dictionary containing:
                - data: Raw OHLCV data as dict/list
                - symbol: Stock symbol
                - start_date: Start date
                - end_date: End date
                - source: 'http_api'
                - raw_format: Format of raw data

        Raises:
            Exception: If API call fails after retries
        """
        url = f"{self.base_url}{self.endpoint}"

        # Calculate duration in days
        duration_days = (end_date - start_date).days

        # Prepare request parameters
        params = {
            'symbol': symbol.lower(),
            'duration': max(duration_days, 1),
        }

        # Add any additional parameters
        params.update(kwargs)

        # Add API key if provided
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        # Retry logic
        last_error = None
        for attempt in range(self.retry_max):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()

                logger.info(
                    f"Successfully fetched data for {symbol} "
                    f"from {url} (attempt {attempt + 1})"
                )

                return {
                    'data': data,
                    'symbol': symbol,
                    'start_date': start_date,
                    'end_date': end_date,
                    'source': 'http_api',
                    'raw_format': 'json',
                }

            except requests.RequestException as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff
                if attempt < self.retry_max - 1:
                    logger.warning(
                        f"API request failed (attempt {attempt + 1}/{self.retry_max}). "
                        f"Retrying in {wait_time}s... Error: {e}"
                    )
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"API request failed after {self.retry_max} attempts: {e}")

        raise Exception(
            f"Failed to fetch data from {url} after {self.retry_max} attempts. "
            f"Last error: {last_error}"
        )

    def validate(self, raw_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate raw data from API.

        Args:
            raw_data: Raw data dictionary from fetch_raw()

        Returns:
            ValidationResult with quality assessment
        """
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            data = raw_data.get('data', {})

            # Check if data is empty
            if not data:
                errors.append("Empty response from API")
                quality_score = 0.0

            # Check data structure
            elif isinstance(data, list):
                if len(data) == 0:
                    errors.append("Empty data list from API")
                    quality_score = 0.0
                else:
                    # Validate first record
                    first_record = data[0]
                    required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
                    missing_fields = [
                        f for f in required_fields
                        if f not in first_record
                    ]

                    if missing_fields:
                        warnings.append(f"Missing fields: {missing_fields}")
                        quality_score *= 0.8

                    # Check data quality
                    if len(data) < 5:
                        warnings.append(f"Only {len(data)} records received")
                        quality_score *= 0.7

            elif isinstance(data, dict):
                # Handle dict response
                if 'data' in data:
                    inner_data = data['data']
                    if isinstance(inner_data, list) and len(inner_data) < 5:
                        warnings.append(f"Only {len(inner_data)} records in nested data")
                        quality_score *= 0.7

            # Check for API errors
            if 'error' in data or 'message' in data:
                error_msg = data.get('error') or data.get('message')
                errors.append(f"API error: {error_msg}")
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
        """
        Get metadata about the data source.

        Returns:
            DataMetadata with source information
        """
        if self.last_metadata is None:
            self.last_metadata = DataMetadata(
                symbol='unknown',
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now(),
                record_count=0,
                source_name='http_api',
                last_updated=datetime.now(),
                data_frequency='daily',
                has_missing_data=False,
            )

        return self.last_metadata

    @property
    def source_name(self) -> str:
        """Return source name."""
        return f"http_api ({self.base_url})"

    def convert_to_dataframe(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert raw API response to pandas DataFrame.

        Args:
            raw_data: Raw data from fetch_raw()

        Returns:
            DataFrame with OHLCV columns
        """
        data = raw_data.get('data', [])

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame(data)

        # Standardize column names
        column_mapping = {
            'date': 'Date',
            'Date': 'Date',
            'open': 'Open',
            'Open': 'Open',
            'high': 'High',
            'High': 'High',
            'low': 'Low',
            'Low': 'Low',
            'close': 'Close',
            'Close': 'Close',
            'volume': 'Volume',
            'Volume': 'Volume',
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Ensure Date is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

        # Ensure numeric columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df


class CentralizedHKEXHttpSource(HttpApiDataSource):
    """
    Specialized HTTP API source for centralized HKEX endpoint.

    Uses the unified HTTP API: http://18.180.162.113:9191
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize centralized HKEX HTTP source.

        Args:
            api_key: Optional API key for authentication

        Example:
            >>> source = CentralizedHKEXHttpSource()
            >>> raw = source.fetch_raw("0700.hk", "2023-01-01", "2024-01-01")
            >>> df = source.convert_to_dataframe(raw)
        """
        super().__init__(
            base_url="http://18.180.162.113:9191",
            endpoint="/inst/getInst",
            api_key=api_key,
            timeout=30,
            retry_max=3,
        )

    def fetch_raw(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch HKEX data from centralized endpoint.

        Args:
            symbol: HKEX symbol (e.g., '0700.hk')
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters

        Returns:
            Raw data dictionary
        """
        # Ensure lowercase symbol
        symbol = symbol.lower()
        if not symbol.endswith('.hk'):
            symbol = f"{symbol}.hk"

        return super().fetch_raw(symbol, start_date, end_date, **kwargs)

    @property
    def source_name(self) -> str:
        """Return source name."""
        return "centralized_hkex_api"
