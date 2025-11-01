"""
Data schemas for OHLCV (Open, High, Low, Close, Volume) data pipeline.

This module defines Pydantic models for different stages of the data pipeline:
1. OHLCVData: Standard OHLCV format used throughout the system
2. RawPriceData: Raw data as fetched from data sources
3. CleanedPriceData: Data after validation and cleaning
4. NormalizedPriceData: Data after datetime normalization to UTC

All models include validation rules to ensure data integrity.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd


class OHLCVData(BaseModel):
    """
    Standard OHLCV (Open, High, Low, Close, Volume) data format.

    This is the canonical format used throughout the backtesting system.
    All price data must conform to this schema.
    """

    date: datetime = Field(..., description="Trading date in UTC")
    symbol: str = Field(..., description="Asset symbol (e.g., '0700.HK')")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="Highest price of the day")
    low: float = Field(..., gt=0, description="Lowest price of the day")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume in shares")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('date')
    @classmethod
    def validate_date_is_utc(cls, v):
        """Ensure date is timezone-aware (UTC)."""
        if v.tzinfo is None:
            raise ValueError("Date must be timezone-aware (UTC)")
        return v

    @model_validator(mode='after')
    def validate_ohlc_relationships(self):
        """Validate OHLC price relationships."""
        high = self.high
        low = self.low
        close = self.close
        open_price = self.open

        # High must be >= all other prices
        if high < low:
            raise ValueError("High must be >= Low")
        if high < close:
            raise ValueError("High must be >= Close")
        if high < open_price:
            raise ValueError("High must be >= Open")

        # Low must be <= all other prices
        if low > high:
            raise ValueError("Low must be <= High")
        if low > close:
            raise ValueError("Low must be <= Close")
        if low > open_price:
            raise ValueError("Low must be <= Open")

        # Close must be between High and Low
        if close > high or close < low:
            raise ValueError("Close must be between High and Low")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO format datetime."""
        data = self.dict()
        data['date'] = self.date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OHLCVData':
        """Create from dictionary, parsing ISO format datetime."""
        data_copy = data.copy()
        if isinstance(data_copy.get('date'), str):
            data_copy['date'] = datetime.fromisoformat(data_copy['date'])
        return cls(**data_copy)


class RawPriceData(BaseModel):
    """
    Raw price data as fetched from data sources.

    This represents unprocessed data directly from sources (Yahoo Finance, HKEX, etc.)
    May contain missing values, outliers, or timezone-naive datetimes.
    """

    date: datetime = Field(..., description="Date (may not be UTC)")
    symbol: str = Field(..., description="Asset symbol")
    open: Optional[float] = Field(None, description="Opening price (may be None)")
    high: Optional[float] = Field(None, description="Highest price (may be None)")
    low: Optional[float] = Field(None, description="Lowest price (may be None)")
    close: Optional[float] = Field(None, description="Closing price (may be None)")
    volume: Optional[int] = Field(None, ge=0, description="Volume (may be None)")
    source: str = Field(..., description="Data source (e.g., 'yahoo', 'hkex', 'csv')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('volume')
    @classmethod
    def validate_volume_non_negative(cls, v):
        """Volume cannot be negative."""
        if v is not None and v < 0:
            raise ValueError("Volume cannot be negative")
        return v

    @field_validator('open', 'high', 'low', 'close')
    @classmethod
    def validate_prices_positive(cls, v):
        """Prices must be positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Prices must be positive")
        return v

    def has_complete_ohlcv(self) -> bool:
        """Check if record has all required OHLCV values."""
        return all([
            self.open is not None,
            self.high is not None,
            self.low is not None,
            self.close is not None,
            self.volume is not None
        ])

    def get_missing_fields(self) -> List[str]:
        """Get list of missing OHLCV fields."""
        missing = []
        for field in ['open', 'high', 'low', 'close', 'volume']:
            if getattr(self, field) is None:
                missing.append(field)
        return missing


class CleanedPriceData(OHLCVData):
    """
    Validated and cleaned price data.

    Extends OHLCVData with additional metadata about data quality and cleaning operations.
    All OHLCV values are guaranteed to be present and valid.
    """

    is_outlier: bool = Field(default=False, description="Whether this record is a statistical outlier")
    cleaning_notes: Optional[str] = Field(None, description="Notes about cleaning operations")
    source: str = Field(..., description="Original data source")
    quality_score: float = Field(default=1.0, ge=0, le=1, description="Data quality score (0-1)")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('quality_score')
    @classmethod
    def validate_quality_score(cls, v):
        """Quality score must be between 0 and 1."""
        if not (0 <= v <= 1):
            raise ValueError("Quality score must be between 0 and 1")
        return v

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """Check if data meets quality threshold."""
        return self.quality_score >= threshold and not self.is_outlier


class NormalizedPriceData(CleanedPriceData):
    """
    Normalized price data with standardized datetime.

    Extends CleanedPriceData with timezone-aware UTC datetimes and additional
    normalization metadata.
    This is the final stage before feeding into the backtest engine.
    """

    original_date: Optional[datetime] = Field(None, description="Original datetime before normalization")
    original_timezone: Optional[str] = Field(None, description="Original timezone (e.g., 'Asia/Hong_Kong')")
    is_trading_day: bool = Field(default=True, description="Whether this is a trading day")
    trading_hours_aligned: bool = Field(default=True, description="Whether time is within trading hours")
    normalization_notes: Optional[str] = Field(None, description="Notes about normalization operations")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @model_validator(mode='after')
    def validate_date_is_utc_normalized(self):
        """Validate that date is UTC and aware."""
        date = self.date
        if date.tzinfo is None or date.tzinfo.tzname(date) != 'UTC':
            raise ValueError("Date must be UTC timezone-aware")
        return self

    def get_trading_status(self) -> Dict[str, Any]:
        """Get trading status summary."""
        return {
            'is_trading_day': self.is_trading_day,
            'trading_hours_aligned': self.trading_hours_aligned,
            'ready_for_backtest': self.is_trading_day and self.trading_hours_aligned
        }


class OHLCVDataBatch(BaseModel):
    """Batch of OHLCV records for efficient processing."""

    records: List[OHLCVData] = Field(..., description="List of OHLCV records")
    symbol: str = Field(..., description="Symbol for all records in batch")
    count: int = Field(default=0, ge=0, description="Number of records")
    date_range: Dict[str, str] = Field(default_factory=dict, description="Min and max dates in ISO format")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @model_validator(mode='after')
    def validate_batch_consistency(self):
        """Validate batch consistency."""
        records = self.records
        symbol = self.symbol

        # All records must have the same symbol
        if records:
            if not all(r.symbol == symbol for r in records):
                raise ValueError("All records must have the same symbol")

            # Update count from records
            object.__setattr__(self, 'count', len(records))

            # Calculate date range
            dates = [r.date for r in records]
            object.__setattr__(self, 'date_range', {
                'min': min(dates).isoformat(),
                'max': max(dates).isoformat()
            })

        return self

    def to_dataframe(self) -> pd.DataFrame:
        """Convert batch to pandas DataFrame."""
        data = [
            {
                'date': r.date,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume
            }
            for r in self.records
        ]
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, symbol: str) -> 'OHLCVDataBatch':
        """Create batch from pandas DataFrame."""
        records = []
        for date, row in df.iterrows():
            record = OHLCVData(
                date=date,
                symbol=symbol,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume'])
            )
            records.append(record)

        return cls(records=records, symbol=symbol)


class DataValidationResult(BaseModel):
    """Result of data validation operation."""

    is_valid: bool = Field(..., description="Whether data passed validation")
    record_count: int = Field(default=0, description="Number of records validated")
    valid_count: int = Field(default=0, description="Number of valid records")
    invalid_count: int = Field(default=0, description="Number of invalid records")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="List of validation warnings")
    summary: str = Field(default="", description="Summary of validation results")

    def add_error(self, index: int, field: str, message: str) -> None:
        """Add a validation error."""
        self.errors.append({
            'index': index,
            'field': field,
            'message': message
        })
        self.invalid_count += 1

    def add_warning(self, index: int, field: str, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append({
            'index': index,
            'field': field,
            'message': message
        })

    def generate_summary(self) -> str:
        """Generate summary of validation results."""
        if self.is_valid:
            self.summary = f"Validation passed: {self.valid_count}/{self.record_count} records valid"
        else:
            self.summary = (
                f"Validation failed: {self.valid_count}/{self.record_count} records valid, "
                f"{self.invalid_count} errors, {len(self.warnings)} warnings"
            )
        return self.summary
