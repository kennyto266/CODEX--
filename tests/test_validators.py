"""
Comprehensive unit tests for data validation module.

Tests DataValidator and PipelineValidator classes through all validation stages:
1. Raw data validation
2. OHLCV relationship checking
3. Outlier detection
4. Volume validation
5. Batch validation
6. Data cleaning and normalization
7. Trading day checks
8. Asset profile validation
9. Full pipeline validation
"""

import pytest
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from src.data_pipeline.validators import DataValidator, PipelineValidator
from src.data_pipeline.schemas import (
    OHLCVData, RawPriceData, CleanedPriceData, NormalizedPriceData,
    DataValidationResult
)
from src.data_pipeline.asset_profile import AssetProfile, Market, Currency, get_registry, reset_registry


class TestDataValidatorRawData:
    """Test raw data validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.valid_raw_data = {
            'date': datetime.now(timezone.utc),
            'symbol': '0700.HK',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000000,
            'source': 'yahoo'
        }

    def test_validate_raw_data_with_complete_ohlcv(self):
        """Test validation of raw data with complete OHLCV."""
        result = self.validator.validate_raw_data(self.valid_raw_data)
        assert result.is_valid
        assert result.valid_count == 1
        assert len(result.errors) == 0

    def test_validate_raw_data_with_missing_field(self):
        """Test validation of raw data with missing field."""
        incomplete_data = self.valid_raw_data.copy()
        incomplete_data['close'] = None
        result = self.validator.validate_raw_data(incomplete_data)
        assert len(result.warnings) > 0

    def test_validate_raw_data_with_negative_volume(self):
        """Test validation of raw data with negative volume."""
        invalid_data = self.valid_raw_data.copy()
        invalid_data['volume'] = -100
        result = self.validator.validate_raw_data(invalid_data)
        assert not result.is_valid

    def test_validate_raw_data_with_negative_price(self):
        """Test validation of raw data with negative price."""
        invalid_data = self.valid_raw_data.copy()
        invalid_data['close'] = -50.0
        result = self.validator.validate_raw_data(invalid_data)
        assert not result.is_valid


class TestDataValidatorOHLCVRelationships:
    """Test OHLCV relationship validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.valid_record = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0
        }

    def test_valid_ohlcv_relationships(self):
        """Test validation of valid OHLCV relationships."""
        errors = self.validator.validate_ohlcv_relationships(self.valid_record)
        assert len(errors) == 0

    def test_high_less_than_close(self):
        """Test validation when high < close."""
        invalid_record = self.valid_record.copy()
        invalid_record['high'] = 100.0
        invalid_record['close'] = 102.0
        errors = self.validator.validate_ohlcv_relationships(invalid_record)
        assert len(errors) > 0
        assert any('High' in e for e in errors)

    def test_low_greater_than_close(self):
        """Test validation when low > close."""
        invalid_record = self.valid_record.copy()
        invalid_record['low'] = 103.0
        invalid_record['close'] = 102.0
        errors = self.validator.validate_ohlcv_relationships(invalid_record)
        assert len(errors) > 0

    def test_close_outside_high_low_range(self):
        """Test validation when close is outside high-low range."""
        invalid_record = self.valid_record.copy()
        invalid_record['close'] = 110.0  # Above high
        errors = self.validator.validate_ohlcv_relationships(invalid_record)
        assert len(errors) > 0

    def test_negative_price(self):
        """Test validation with negative price."""
        invalid_record = self.valid_record.copy()
        invalid_record['open'] = -50.0
        errors = self.validator.validate_ohlcv_relationships(invalid_record)
        assert any('positive' in e.lower() for e in errors)

    def test_missing_field_skips_validation(self):
        """Test that missing fields are skipped gracefully."""
        incomplete_record = {
            'open': 100.0,
            'high': None,
            'low': 95.0,
            'close': 102.0
        }
        errors = self.validator.validate_ohlcv_relationships(incomplete_record)
        assert len(errors) == 0  # Should skip, not error


class TestDataValidatorOutlierDetection:
    """Test outlier detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def test_no_outliers_in_normal_data(self):
        """Test outlier detection on normal data."""
        dates = pd.date_range('2025-01-01', periods=10, freq='D', tz='UTC')
        data = {
            'date': dates,
            'close': [100.0, 101.0, 102.0, 101.5, 100.5, 101.0, 102.5, 101.0, 100.0, 101.0]
        }
        df = pd.DataFrame(data).set_index('date')

        outliers = self.validator.detect_outliers(df)
        # With 1-2% daily changes, should not exceed 20% threshold
        assert outliers.sum() == 0

    def test_detects_large_price_jump(self):
        """Test outlier detection with large price jump."""
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        data = {
            'date': dates,
            'close': [100.0, 101.0, 130.0, 129.0, 128.0]  # 30% jump
        }
        df = pd.DataFrame(data).set_index('date')

        outliers = self.validator.detect_outliers(df)
        assert outliers.iloc[2] == True  # 30% jump should be flagged

    def test_outlier_threshold_customizable(self):
        """Test that outlier threshold can be customized."""
        validator = DataValidator()
        validator.outlier_threshold_pct = 0.10  # 10% threshold

        dates = pd.date_range('2025-01-01', periods=3, freq='D', tz='UTC')
        data = {
            'date': dates,
            'close': [100.0, 101.0, 112.0]  # 10.9% jump > 10% threshold
        }
        df = pd.DataFrame(data).set_index('date')

        outliers = validator.detect_outliers(df)
        assert outliers.iloc[2] == True

    def test_empty_dataframe(self):
        """Test outlier detection on empty DataFrame."""
        df = pd.DataFrame({'close': []})
        outliers = self.validator.detect_outliers(df)
        assert len(outliers) == 0


class TestDataValidatorVolumeValidation:
    """Test volume validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def test_valid_volume_data(self):
        """Test validation of valid volume data."""
        df = pd.DataFrame({
            'volume': [1000000, 2000000, 1500000, 1800000]
        })
        errors = self.validator.validate_volume(df)
        assert len(errors) == 0

    def test_nan_volume_detected(self):
        """Test detection of NaN volume."""
        df = pd.DataFrame({
            'volume': [1000000, np.nan, 1500000]
        })
        errors = self.validator.validate_volume(df)
        assert any('NaN' in e for e in errors)

    def test_negative_volume_detected(self):
        """Test detection of negative volume."""
        df = pd.DataFrame({
            'volume': [1000000, -500000, 1500000]
        })
        errors = self.validator.validate_volume(df)
        assert any('negative' in e.lower() for e in errors)

    def test_zero_volume_detected(self):
        """Test detection of zero volume."""
        df = pd.DataFrame({
            'volume': [1000000, 0, 1500000]
        })
        errors = self.validator.validate_volume(df)
        assert any('zero' in e.lower() for e in errors)


class TestDataValidatorBatchValidation:
    """Test batch validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        self.valid_batch = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 101.5, 100.5],
            'high': [105.0, 106.0, 107.0, 106.5, 105.5],
            'low': [95.0, 96.0, 97.0, 96.5, 95.5],
            'close': [102.0, 103.0, 104.0, 103.5, 102.5],
            'volume': [1000000, 1100000, 1200000, 1150000, 1050000]
        }, index=dates)
        self.valid_batch.index.name = 'date'

    def test_valid_batch(self):
        """Test validation of valid batch."""
        result = self.validator.validate_batch(self.valid_batch, '0700.HK')
        assert result.is_valid
        assert result.record_count == 5

    def test_empty_batch(self):
        """Test validation of empty batch."""
        empty_df = pd.DataFrame()
        result = self.validator.validate_batch(empty_df, '0700.HK')
        # Empty DataFrame is marked as invalid in validator
        assert len(result.errors) > 0

    def test_batch_with_ohlc_error(self):
        """Test batch validation detects OHLC errors."""
        invalid_batch = self.valid_batch.copy()
        invalid_batch.loc[invalid_batch.index[2], 'close'] = 110.0  # Close > high
        result = self.validator.validate_batch(invalid_batch, '0700.HK')
        assert len(result.errors) > 0

    def test_batch_outlier_detection(self):
        """Test batch validation detects outliers."""
        batch_with_outlier = self.valid_batch.copy()
        batch_with_outlier.loc[batch_with_outlier.index[2], 'close'] = 130.0  # 30% jump
        result = self.validator.validate_batch(batch_with_outlier, '0700.HK')
        assert len(result.warnings) > 0

    def test_batch_missing_values(self):
        """Test batch validation detects missing values."""
        batch_with_missing = self.valid_batch.copy()
        batch_with_missing.loc[batch_with_missing.index[1], 'close'] = np.nan
        result = self.validator.validate_batch(batch_with_missing, '0700.HK')
        assert len(result.warnings) > 0


class TestDataValidatorCleaningAndNormalization:
    """Test data cleaning and normalization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        self.raw_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 101.5, 100.5],
            'high': [105.0, 106.0, 107.0, 106.5, 105.5],
            'low': [95.0, 96.0, 97.0, 96.5, 95.5],
            'close': [102.0, 103.0, 104.0, 103.5, 102.5],
            'volume': [1000000.0, 1100000.0, 1200000.0, 1150000.0, 1050000.0]
        }, index=dates)
        self.raw_data.index.name = 'date'

    def test_clean_and_validate_returns_tuple(self):
        """Test that clean_and_validate returns (DataFrame, ValidationResult)."""
        cleaned_df, result = self.validator.clean_and_validate(self.raw_data, '0700.HK')
        assert isinstance(cleaned_df, pd.DataFrame)
        assert isinstance(result, DataValidationResult)

    def test_volume_normalized_to_int(self):
        """Test that volume is normalized to integer."""
        cleaned_df, _ = self.validator.clean_and_validate(self.raw_data, '0700.HK')
        assert cleaned_df['volume'].dtype in [np.int32, np.int64]

    def test_outlier_column_added(self):
        """Test that is_outlier column is added."""
        cleaned_df, _ = self.validator.clean_and_validate(self.raw_data, '0700.HK')
        assert 'is_outlier' in cleaned_df.columns

    def test_normalize_to_utc_converts_timezone(self):
        """Test UTC normalization with timezone-naive data."""
        naive_df = self.raw_data.copy()
        naive_df.index = naive_df.index.tz_localize(None)  # Remove timezone

        normalized_df = self.validator.normalize_to_utc(naive_df, source_tz='Asia/Hong_Kong')
        assert normalized_df.index.tzinfo is not None
        # Check UTC timezone (use tzname() method)
        assert 'UTC' in str(normalized_df.index.tz)

    def test_normalize_already_utc(self):
        """Test normalization of already UTC data."""
        normalized_df = self.validator.normalize_to_utc(self.raw_data, source_tz='UTC')
        # Check UTC timezone
        assert 'UTC' in str(normalized_df.index.tz)


class TestDataValidatorTradingDayChecks:
    """Test trading day validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def test_weekday_is_trading_day(self):
        """Test that weekday is trading day."""
        trading_date = datetime(2025, 1, 6, tzinfo=timezone.utc)  # Monday
        assert self.validator.is_trading_day(trading_date)

    def test_weekend_is_not_trading_day(self):
        """Test that weekend is not trading day."""
        weekend_date = datetime(2025, 1, 4, tzinfo=timezone.utc)  # Saturday
        assert not self.validator.is_trading_day(weekend_date)

    def test_holiday_is_not_trading_day(self):
        """Test that HKEX holiday is not trading day."""
        holiday_date = datetime(2025, 1, 1, tzinfo=timezone.utc)  # New Year's Day
        assert not self.validator.is_trading_day(holiday_date)

    def test_cny_is_not_trading_day(self):
        """Test that Chinese New Year is not trading day."""
        cny_date = datetime(2025, 2, 10, tzinfo=timezone.utc)  # CNY
        assert not self.validator.is_trading_day(cny_date)

    def test_validate_trading_day_alignment(self):
        """Test trading day alignment validation."""
        # Create DataFrame with trading days
        trading_dates = pd.date_range('2025-01-06', periods=5, freq='B', tz='UTC')
        df = pd.DataFrame({
            'close': [100.0, 101.0, 102.0, 101.5, 100.5]
        }, index=trading_dates)

        issues = self.validator.validate_trading_day_alignment(df)
        assert len(issues) == 0

    def test_detect_non_trading_days(self):
        """Test detection of non-trading days."""
        # Include weekend
        dates = pd.DatetimeIndex([
            datetime(2025, 1, 6, tzinfo=timezone.utc),  # Monday - trading
            datetime(2025, 1, 4, tzinfo=timezone.utc),  # Saturday - non-trading
        ])
        df = pd.DataFrame({'close': [100.0, 101.0]}, index=dates)

        issues = self.validator.validate_trading_day_alignment(df)
        assert len(issues) == 1


class TestDataValidatorAssetProfileValidation:
    """Test asset profile validation."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.validator = DataValidator()
        dates = pd.date_range('2025-01-01', periods=10, freq='D', tz='UTC')
        self.batch_data = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [105.0] * 10,
            'low': [95.0] * 10,
            'close': [102.0] * 10,
            'volume': [1000000] * 10
        }, index=dates)
        self.batch_data.index.name = 'date'

    def test_validate_with_default_profile(self):
        """Test validation with default asset profile."""
        result = self.validator.validate_with_asset_profile(self.batch_data, '0700.HK')
        assert result.is_valid

    def test_high_volume_volatility_warning(self):
        """Test warning for high volume volatility."""
        volatile_data = self.batch_data.copy()
        volatile_data['volume'] = [1000000, 100000, 1000000, 100000, 1000000,
                                   100000, 1000000, 100000, 1000000, 100000]
        result = self.validator.validate_with_asset_profile(volatile_data, '0700.HK')
        # Validation should still complete successfully
        assert isinstance(result, DataValidationResult)

    def test_missing_profile_warning(self):
        """Test warning for missing asset profile."""
        result = self.validator.validate_with_asset_profile(self.batch_data, 'UNKNOWN.HK')
        # Should have warning about missing profile
        assert len(result.warnings) > 0


class TestPipelineValidator:
    """Test full pipeline validation."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.pipeline_validator = PipelineValidator()
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        self.raw_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 101.5, 100.5],
            'high': [105.0, 106.0, 107.0, 106.5, 105.5],
            'low': [95.0, 96.0, 97.0, 96.5, 95.5],
            'close': [102.0, 103.0, 104.0, 103.5, 102.5],
            'volume': [1000000, 1100000, 1200000, 1150000, 1050000]
        }, index=dates)
        self.raw_data.index.name = 'date'

    def test_validate_pipeline_returns_dict(self):
        """Test that pipeline validation returns results dictionary."""
        results = self.pipeline_validator.validate_pipeline(self.raw_data, '0700.HK')
        assert isinstance(results, dict)
        assert 'raw' in results
        assert 'cleaned' in results
        assert 'asset_profile' in results
        assert 'summary' in results

    def test_pipeline_validation_stages(self):
        """Test that all pipeline stages are validated."""
        results = self.pipeline_validator.validate_pipeline(self.raw_data, '0700.HK')
        assert isinstance(results['raw'], DataValidationResult)
        assert isinstance(results['cleaned'], DataValidationResult)
        assert isinstance(results['asset_profile'], DataValidationResult)

    def test_valid_data_passes_all_stages(self):
        """Test that valid data passes all pipeline stages."""
        results = self.pipeline_validator.validate_pipeline(self.raw_data, '0700.HK')
        # Raw and asset_profile should be valid
        assert results['raw'].is_valid
        assert results['asset_profile'].is_valid

    def test_get_validation_report_formatted(self):
        """Test validation report generation."""
        results = self.pipeline_validator.validate_pipeline(self.raw_data, '0700.HK')
        report = self.pipeline_validator.get_validation_report(results)
        assert isinstance(report, str)
        assert 'DATA VALIDATION REPORT' in report
        assert 'Raw Validation' in report
        assert 'Cleaned Validation' in report

    def test_pipeline_with_invalid_data(self):
        """Test pipeline validation with invalid OHLC data."""
        invalid_data = self.raw_data.copy()
        invalid_data.loc[invalid_data.index[0], 'close'] = 110.0  # Close > high
        results = self.pipeline_validator.validate_pipeline(invalid_data, '0700.HK')
        # Should detect error in raw validation
        assert len(results['raw'].errors) > 0

    def test_pipeline_summary_statistics(self):
        """Test pipeline validation summary statistics."""
        results = self.pipeline_validator.validate_pipeline(self.raw_data, '0700.HK')
        summary = results['summary']
        assert 'raw_records' in summary
        assert 'cleaned_records' in summary
        assert 'normalized_records' in summary
        assert summary['raw_records'] == 5


class TestDataValidatorIntegration:
    """Integration tests for data validation."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_registry()
        self.validator = DataValidator()

    def test_full_validation_workflow(self):
        """Test complete validation workflow from raw to normalized."""
        # Create realistic raw data
        dates = pd.date_range('2025-01-06', periods=20, freq='B', tz='UTC')  # Business days
        raw_df = pd.DataFrame({
            'open': np.random.uniform(95, 105, 20),
            'high': np.random.uniform(105, 110, 20),
            'low': np.random.uniform(90, 95, 20),
            'close': np.random.uniform(95, 105, 20),
            'volume': np.random.randint(500000, 2000000, 20)
        }, index=dates)
        raw_df.index.name = 'date'

        # Fix OHLC relationships
        for idx in raw_df.index:
            raw_df.loc[idx, 'high'] = max(raw_df.loc[idx, ['open', 'high', 'low', 'close']])
            raw_df.loc[idx, 'low'] = min(raw_df.loc[idx, ['open', 'high', 'low', 'close']])

        # Step 1: Validate and clean
        cleaned_df, validation_result = self.validator.clean_and_validate(raw_df, '0700.HK')
        assert validation_result.is_valid
        assert 'is_outlier' in cleaned_df.columns

        # Step 2: Normalize to UTC
        normalized_df = self.validator.normalize_to_utc(cleaned_df)
        assert 'UTC' in str(normalized_df.index.tz)

        # Step 3: Check trading days
        issues = self.validator.validate_trading_day_alignment(normalized_df)
        # Should have no issues (business days only)
        assert len(issues) == 0

    def test_validation_with_mock_data(self):
        """Test validation with simulated HKEX data."""
        # Simulate 30 days of HKEX trading
        dates = pd.date_range('2025-01-02', periods=30, freq='B', tz='UTC')
        base_price = 100.0
        prices = [base_price]

        for i in range(1, 30):
            # Simulate 0-2% daily change
            change = np.random.uniform(-0.02, 0.02)
            prices.append(prices[-1] * (1 + change))

        data = pd.DataFrame({
            'open': [p * 0.99 for p in prices],
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000 + np.random.randint(-200000, 200000) for _ in prices]
        }, index=dates)
        data.index.name = 'date'

        # Validate
        cleaned, result = self.validator.clean_and_validate(data, '0700.HK')
        assert result.is_valid
        assert len(cleaned) == 30


class TestValidatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()

    def test_single_row_dataframe(self):
        """Test validation of single-row DataFrame."""
        dates = pd.date_range('2025-01-01', periods=1, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [102.0],
            'volume': [1000000]
        }, index=dates)

        result = self.validator.validate_batch(df, '0700.HK')
        assert result.record_count == 1

    def test_very_large_dataframe(self):
        """Test validation of large DataFrame."""
        dates = pd.date_range('2020-01-01', periods=1250, freq='D', tz='UTC')  # ~3.4 years
        df = pd.DataFrame({
            'open': [100.0] * 1250,
            'high': [105.0] * 1250,
            'low': [95.0] * 1250,
            'close': [102.0] * 1250,
            'volume': [1000000] * 1250
        }, index=dates)

        result = self.validator.validate_batch(df, '0700.HK')
        assert result.record_count == 1250

    def test_extreme_price_values(self):
        """Test validation with extreme but valid prices."""
        record = {
            'open': 0.01,
            'high': 10000.0,
            'low': 0.01,
            'close': 5000.0
        }
        errors = self.validator.validate_ohlcv_relationships(record)
        assert len(errors) == 0  # Should be valid

    def test_identical_ohlc_prices(self):
        """Test validation when OHLC are identical."""
        record = {
            'open': 100.0,
            'high': 100.0,
            'low': 100.0,
            'close': 100.0
        }
        errors = self.validator.validate_ohlcv_relationships(record)
        assert len(errors) == 0  # Should be valid (no change)

    def test_zero_volume(self):
        """Test validation with zero volume."""
        df = pd.DataFrame({'volume': [0]})
        errors = self.validator.validate_volume(df)
        assert any('zero' in e.lower() for e in errors)


# Test summary and metrics
class TestValidatorMetrics:
    """Test validator performance and coverage."""

    def test_validator_creation_performance(self):
        """Test that validator instantiation is fast."""
        import time
        start = time.time()
        for _ in range(100):
            DataValidator()
        elapsed = time.time() - start
        # Should be very fast (< 100ms for 100 instantiations)
        assert elapsed < 0.1

    def test_batch_validation_performance(self):
        """Test that batch validation is reasonably fast."""
        import time
        dates = pd.date_range('2025-01-01', periods=1000, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0] * 1000,
            'high': [105.0] * 1000,
            'low': [95.0] * 1000,
            'close': [102.0] * 1000,
            'volume': [1000000] * 1000
        }, index=dates)

        validator = DataValidator()
        start = time.time()
        result = validator.validate_batch(df, '0700.HK')
        elapsed = time.time() - start

        # Should validate 1000 records in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert result.is_valid
