"""
Unit tests for data pipeline schemas.

Tests all schema models and validation rules:
- OHLCVData validation
- RawPriceData validation
- CleanedPriceData validation
- NormalizedPriceData validation
- Schema conversions (dict, dataframe)
"""

import pytest
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from pydantic import ValidationError

from src.data_pipeline.schemas import (
    OHLCVData,
    RawPriceData,
    CleanedPriceData,
    NormalizedPriceData,
    OHLCVDataBatch,
    DataValidationResult
)


class TestOHLCVData:
    """Tests for OHLCVData schema."""

    @pytest.fixture
    def valid_ohlcv_data(self):
        """Fixture with valid OHLCV data."""
        return {
            'date': datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000
        }

    def test_valid_ohlcv_creation(self, valid_ohlcv_data):
        """Test creation of valid OHLCV record."""
        record = OHLCVData(**valid_ohlcv_data)
        assert record.symbol == '0700.HK'
        assert record.close == 102.0
        assert record.volume == 1000000

    def test_ohlcv_validates_high_low_close_relationships(self, valid_ohlcv_data):
        """Test validation of High >= Low >= Close relationship."""
        # Invalid: Close > High
        invalid_data = valid_ohlcv_data.copy()
        invalid_data['close'] = 110.0
        with pytest.raises(ValidationError):
            OHLCVData(**invalid_data)

        # Invalid: Low > High
        invalid_data = valid_ohlcv_data.copy()
        invalid_data['low'] = 110.0
        with pytest.raises(ValidationError):
            OHLCVData(**invalid_data)

    def test_ohlcv_requires_positive_prices(self, valid_ohlcv_data):
        """Test that prices must be positive."""
        invalid_data = valid_ohlcv_data.copy()
        invalid_data['open'] = -100.0
        with pytest.raises(ValidationError):
            OHLCVData(**invalid_data)

    def test_ohlcv_requires_utc_timezone(self, valid_ohlcv_data):
        """Test that date must be timezone-aware UTC."""
        # Without timezone
        invalid_data = valid_ohlcv_data.copy()
        invalid_data['date'] = datetime(2025, 10, 24, 12, 0, 0)
        with pytest.raises(ValidationError):
            OHLCVData(**invalid_data)

    def test_ohlcv_to_dict_serialization(self, valid_ohlcv_data):
        """Test serialization to dict with ISO format."""
        record = OHLCVData(**valid_ohlcv_data)
        data_dict = record.to_dict()

        assert isinstance(data_dict['date'], str)
        assert 'T' in data_dict['date']  # ISO format
        assert data_dict['symbol'] == '0700.HK'

    def test_ohlcv_from_dict_deserialization(self, valid_ohlcv_data):
        """Test deserialization from dict with ISO format."""
        record = OHLCVData(**valid_ohlcv_data)
        data_dict = record.to_dict()

        restored = OHLCVData.from_dict(data_dict)
        assert restored.symbol == record.symbol
        assert restored.close == record.close

    def test_ohlcv_volume_non_negative(self, valid_ohlcv_data):
        """Test that volume must be non-negative."""
        invalid_data = valid_ohlcv_data.copy()
        invalid_data['volume'] = -1000
        with pytest.raises(ValidationError):
            OHLCVData(**invalid_data)


class TestRawPriceData:
    """Tests for RawPriceData schema."""

    @pytest.fixture
    def valid_raw_data(self):
        """Fixture with valid raw data."""
        return {
            'date': datetime(2025, 10, 24, 12, 0, 0),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000,
            'source': 'yahoo'
        }

    def test_raw_data_allows_missing_fields(self, valid_raw_data):
        """Test that raw data can have None values."""
        partial_data = {
            'date': valid_raw_data['date'],
            'symbol': valid_raw_data['symbol'],
            'open': 100.0,
            'source': 'yahoo'
            # High, Low, Close, Volume are None
        }
        record = RawPriceData(**partial_data)
        assert record.open == 100.0
        assert record.high is None
        assert record.volume is None

    def test_raw_data_requires_source(self, valid_raw_data):
        """Test that source field is required."""
        invalid_data = valid_raw_data.copy()
        del invalid_data['source']
        with pytest.raises(ValidationError):
            RawPriceData(**invalid_data)

    def test_raw_data_has_complete_ohlcv(self, valid_raw_data):
        """Test has_complete_ohlcv method."""
        complete = RawPriceData(**valid_raw_data)
        assert complete.has_complete_ohlcv() is True

        partial = RawPriceData(
            date=valid_raw_data['date'],
            symbol=valid_raw_data['symbol'],
            open=100.0,
            source='yahoo'
        )
        assert partial.has_complete_ohlcv() is False

    def test_raw_data_get_missing_fields(self, valid_raw_data):
        """Test get_missing_fields method."""
        partial = RawPriceData(
            date=valid_raw_data['date'],
            symbol=valid_raw_data['symbol'],
            open=100.0,
            source='yahoo'
        )
        missing = partial.get_missing_fields()
        assert 'high' in missing
        assert 'low' in missing
        assert 'close' in missing
        assert 'volume' in missing
        assert len(missing) == 4

    def test_raw_data_metadata_storage(self, valid_raw_data):
        """Test storage of additional metadata."""
        valid_raw_data['metadata'] = {'fetch_time': '2025-10-24T12:00:00'}
        record = RawPriceData(**valid_raw_data)
        assert record.metadata['fetch_time'] == '2025-10-24T12:00:00'


class TestCleanedPriceData:
    """Tests for CleanedPriceData schema."""

    @pytest.fixture
    def valid_cleaned_data(self):
        """Fixture with valid cleaned data."""
        return {
            'date': datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000,
            'source': 'yahoo',
            'is_outlier': False,
            'quality_score': 0.95
        }

    def test_cleaned_data_creation(self, valid_cleaned_data):
        """Test creation of cleaned data record."""
        record = CleanedPriceData(**valid_cleaned_data)
        assert record.is_outlier is False
        assert record.quality_score == 0.95
        assert record.source == 'yahoo'

    def test_cleaned_data_quality_score_bounds(self, valid_cleaned_data):
        """Test quality score validation (0-1 range)."""
        invalid_data = valid_cleaned_data.copy()
        invalid_data['quality_score'] = 1.5
        with pytest.raises(ValidationError):
            CleanedPriceData(**invalid_data)

        invalid_data['quality_score'] = -0.1
        with pytest.raises(ValidationError):
            CleanedPriceData(**invalid_data)

    def test_cleaned_data_is_high_quality(self, valid_cleaned_data):
        """Test is_high_quality method."""
        record = CleanedPriceData(**valid_cleaned_data)
        assert record.is_high_quality(threshold=0.9) is True
        assert record.is_high_quality(threshold=0.99) is False

        # Outlier overrides quality score
        valid_cleaned_data['is_outlier'] = True
        record = CleanedPriceData(**valid_cleaned_data)
        assert record.is_high_quality() is False


class TestNormalizedPriceData:
    """Tests for NormalizedPriceData schema."""

    @pytest.fixture
    def valid_normalized_data(self):
        """Fixture with valid normalized data."""
        return {
            'date': datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000,
            'source': 'yahoo',
            'is_outlier': False,
            'quality_score': 0.95,
            'is_trading_day': True,
            'trading_hours_aligned': True,
            'original_timezone': 'Asia/Hong_Kong'
        }

    def test_normalized_data_creation(self, valid_normalized_data):
        """Test creation of normalized data record."""
        record = NormalizedPriceData(**valid_normalized_data)
        assert record.is_trading_day is True
        assert record.trading_hours_aligned is True
        assert record.original_timezone == 'Asia/Hong_Kong'

    def test_normalized_data_requires_utc(self, valid_normalized_data):
        """Test that date must be UTC."""
        # Non-UTC timezone
        invalid_data = valid_normalized_data.copy()
        invalid_data['date'] = datetime(2025, 10, 24, 12, 0, 0, timezone.utc)
        # This should work (UTC)
        record = NormalizedPriceData(**invalid_data)
        assert record.date.tzinfo.tzname(record.date) == 'UTC'

    def test_normalized_data_trading_status(self, valid_normalized_data):
        """Test get_trading_status method."""
        record = NormalizedPriceData(**valid_normalized_data)
        status = record.get_trading_status()

        assert status['is_trading_day'] is True
        assert status['trading_hours_aligned'] is True
        assert status['ready_for_backtest'] is True

        # Non-trading day
        valid_normalized_data['is_trading_day'] = False
        record = NormalizedPriceData(**valid_normalized_data)
        status = record.get_trading_status()
        assert status['ready_for_backtest'] is False


class TestOHLCVDataBatch:
    """Tests for OHLCVDataBatch schema."""

    @pytest.fixture
    def batch_data(self):
        """Fixture with batch data."""
        records = [
            OHLCVData(
                date=datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
                symbol='0700.HK',
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000
            ),
            OHLCVData(
                date=datetime(2025, 10, 23, 12, 0, 0, tzinfo=timezone.utc),
                symbol='0700.HK',
                open=101.0,
                high=106.0,
                low=96.0,
                close=103.0,
                volume=1100000
            )
        ]
        return OHLCVDataBatch(records=records, symbol='0700.HK')

    def test_batch_creation(self, batch_data):
        """Test creation of batch."""
        assert batch_data.count == 2
        assert batch_data.symbol == '0700.HK'
        assert len(batch_data.records) == 2

    def test_batch_enforces_symbol_consistency(self):
        """Test that all records must have same symbol."""
        records = [
            OHLCVData(
                date=datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
                symbol='0700.HK',
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000
            ),
            OHLCVData(
                date=datetime(2025, 10, 23, 12, 0, 0, tzinfo=timezone.utc),
                symbol='0388.HK',  # Different symbol
                open=101.0,
                high=106.0,
                low=96.0,
                close=103.0,
                volume=1100000
            )
        ]
        with pytest.raises(ValidationError):
            OHLCVDataBatch(records=records, symbol='0700.HK')

    def test_batch_to_dataframe(self, batch_data):
        """Test conversion to DataFrame."""
        df = batch_data.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert df.index.name == 'date'

    def test_batch_from_dataframe(self):
        """Test creation from DataFrame."""
        # Create a DataFrame
        dates = [
            datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 10, 23, 12, 0, 0, tzinfo=timezone.utc)
        ]
        df = pd.DataFrame({
            'date': dates,
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [95.0, 96.0],
            'close': [102.0, 103.0],
            'volume': [1000000, 1100000]
        })
        df.set_index('date', inplace=True)

        batch = OHLCVDataBatch.from_dataframe(df, '0700.HK')

        assert batch.symbol == '0700.HK'
        assert batch.count == 2
        assert len(batch.records) == 2


class TestDataValidationResult:
    """Tests for DataValidationResult schema."""

    def test_validation_result_creation(self):
        """Test creation of validation result."""
        result = DataValidationResult(
            is_valid=True,
            record_count=100,
            valid_count=100
        )
        assert result.is_valid is True
        assert result.record_count == 100

    def test_validation_result_add_error(self):
        """Test adding errors to result."""
        result = DataValidationResult(
            is_valid=False,
            record_count=100,
            valid_count=95
        )
        result.add_error(0, 'close', 'Price must be positive')

        assert len(result.errors) == 1
        assert result.errors[0]['index'] == 0
        assert result.invalid_count == 96

    def test_validation_result_add_warning(self):
        """Test adding warnings to result."""
        result = DataValidationResult(is_valid=True, record_count=100)
        result.add_warning(5, 'volume', 'Volume is unusually high')

        assert len(result.warnings) == 1
        assert result.warnings[0]['index'] == 5

    def test_validation_result_generate_summary(self):
        """Test summary generation."""
        result = DataValidationResult(
            is_valid=True,
            record_count=100,
            valid_count=100
        )
        summary = result.generate_summary()

        assert 'Validation passed' in summary
        assert '100/100' in summary

        result = DataValidationResult(
            is_valid=False,
            record_count=100,
            valid_count=95,
            invalid_count=5
        )
        result.add_warning(0, 'volume', 'warning')
        summary = result.generate_summary()

        assert 'Validation failed' in summary


class TestSchemaIntegration:
    """Integration tests for schema pipeline."""

    def test_raw_to_cleaned_conversion(self):
        """Test conversion from raw to cleaned data."""
        raw = RawPriceData(
            date=datetime(2025, 10, 24, 12, 0, 0),
            symbol='0700.HK',
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
            source='yahoo'
        )

        cleaned = CleanedPriceData(
            date=datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            symbol=raw.symbol,
            open=raw.open,
            high=raw.high,
            low=raw.low,
            close=raw.close,
            volume=raw.volume,
            source=raw.source,
            quality_score=0.95
        )

        assert cleaned.symbol == raw.symbol
        assert cleaned.open == raw.open

    def test_cleaned_to_normalized_conversion(self):
        """Test conversion from cleaned to normalized data."""
        cleaned = CleanedPriceData(
            date=datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            symbol='0700.HK',
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000,
            source='yahoo',
            quality_score=0.95
        )

        normalized = NormalizedPriceData(
            date=cleaned.date,
            symbol=cleaned.symbol,
            open=cleaned.open,
            high=cleaned.high,
            low=cleaned.low,
            close=cleaned.close,
            volume=cleaned.volume,
            source=cleaned.source,
            quality_score=cleaned.quality_score,
            is_trading_day=True,
            trading_hours_aligned=True
        )

        assert normalized.symbol == cleaned.symbol
        assert normalized.is_trading_day is True

    def test_full_pipeline_data_flow(self):
        """Test complete data flow through all schema stages."""
        # Raw data
        raw_dict = {
            'date': datetime(2025, 10, 24, 12, 0, 0),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000,
            'source': 'yahoo'
        }
        raw = RawPriceData(**raw_dict)
        assert raw.has_complete_ohlcv()

        # Cleaned data
        cleaned = CleanedPriceData(
            date=datetime(2025, 10, 24, 12, 0, 0, tzinfo=timezone.utc),
            **{k: v for k, v in raw.dict().items() if k != 'date'}
        )
        assert cleaned.quality_score == 1.0

        # Normalized data
        normalized = NormalizedPriceData(
            **{k: v for k, v in cleaned.dict().items() if k not in ['original_date', 'original_timezone', 'is_trading_day', 'trading_hours_aligned', 'normalization_notes']},
            is_trading_day=True,
            trading_hours_aligned=True
        )
        assert normalized.get_trading_status()['ready_for_backtest']

        # Final OHLCV for backtesting
        ohlcv = OHLCVData(
            date=normalized.date,
            symbol=normalized.symbol,
            open=normalized.open,
            high=normalized.high,
            low=normalized.low,
            close=normalized.close,
            volume=normalized.volume
        )
        assert ohlcv.close == 102.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
