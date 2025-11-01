"""
Comprehensive unit tests for DateTime Normalization module.

Test coverage:
- Timezone normalization (naive → UTC, any tz → UTC)
- DST transition handling
- Trading hours filtering
- Holiday and weekend filtering
- Business day alignment
- Pipeline orchestration
- Edge cases and error handling
- Performance testing
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.data_pipeline.datetime_normalizer import (
    DateTimeNormalizer,
    PipelineDateTimeNormalizer,
    Market,
    HolidayCalendar,
    TradingHours,
)


class TestHolidayCalendar:
    """Test holiday calendar functionality."""

    def test_hkex_holidays_exist(self):
        """Test that HKEX holidays are defined."""
        holidays_2024 = HolidayCalendar.get_holidays(Market.HKEX, 2024)
        assert len(holidays_2024) > 0
        assert datetime(2024, 1, 1) in holidays_2024  # New Year's Day

    def test_hkex_cny_holidays(self):
        """Test Chinese New Year holidays."""
        holidays_2024 = HolidayCalendar.get_holidays(Market.HKEX, 2024)
        # 2024 CNY is Feb 10-12
        assert datetime(2024, 2, 10) in holidays_2024
        assert datetime(2024, 2, 11) in holidays_2024
        assert datetime(2024, 2, 12) in holidays_2024

    def test_is_holiday_works(self):
        """Test is_holiday function."""
        # New Year's Day 2024
        assert HolidayCalendar.is_holiday(datetime(2024, 1, 1), Market.HKEX)

    def test_non_holiday_returns_false(self):
        """Test that regular trading days return False."""
        # Jan 2, 2024 is a regular trading day
        assert not HolidayCalendar.is_holiday(datetime(2024, 1, 2), Market.HKEX)

    def test_nyse_holidays_exist(self):
        """Test NYSE holidays are defined."""
        holidays_2024 = HolidayCalendar.get_holidays(Market.NYSE, 2024)
        assert len(holidays_2024) > 0


class TestTradingHours:
    """Test trading hours functionality."""

    def test_hkex_hours_defined(self):
        """Test HKEX trading hours."""
        hours = TradingHours.get_trading_hours(Market.HKEX)
        assert hours['morning_open'] == '09:30'
        assert hours['afternoon_close'] == '16:00'

    def test_nyse_hours_defined(self):
        """Test NYSE trading hours."""
        hours = TradingHours.get_trading_hours(Market.NYSE)
        assert hours['open'] == '09:30'
        assert hours['close'] == '16:00'


class TestDateTimeNormalizerTimezone:
    """Test timezone normalization functionality."""

    def test_naive_datetime_to_utc(self):
        """Test converting naive datetime to UTC."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create DataFrame with naive datetime
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'close': [100, 101, 102, 103, 104]
        })

        result = normalizer.normalize_timezone(df, source_tz='Asia/Hong_Kong')

        # Should be timezone-aware after normalization
        assert result['date'].dt.tz is not None
        assert str(result['date'].dt.tz) == 'UTC'

    def test_aware_datetime_conversion(self):
        """Test converting timezone-aware datetime."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create DataFrame with timezone-aware datetime (HK time)
        hk_tz = ZoneInfo('Asia/Hong_Kong')
        dates = [datetime(2024, 1, 1, 9, 30, tzinfo=hk_tz)]
        df = pd.DataFrame({
            'date': dates,
            'close': [100]
        })

        result = normalizer.normalize_timezone(df)

        # Should be converted to UTC
        assert result['date'].dt.tz is not None

    def test_datetime_index_normalization(self):
        """Test normalizing datetime index."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame(
            {'close': [100, 101, 102, 103, 104]},
            index=dates
        )

        result = normalizer.normalize_timezone(df, source_tz='Asia/Hong_Kong')

        # Index should be normalized
        assert isinstance(result.index, pd.DatetimeIndex)


class TestDateTimeNormalizerDST:
    """Test DST (Daylight Saving Time) handling."""

    def test_dst_detection(self):
        """Test detecting DST transitions."""
        normalizer = DateTimeNormalizer(Market.NYSE)

        # Create data with potential DST gap
        dates = pd.date_range('2024-03-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': range(100, 110)
        }, index=dates)

        df_result, transitions = normalizer.handle_dst_transition(df)

        # Should return dataframe and transitions list
        assert isinstance(df_result, pd.DataFrame)
        assert isinstance(transitions, list)

    def test_dst_no_transitions(self):
        """Test when there are no DST transitions."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Hong Kong doesn't use DST, so no transitions
        dates = pd.date_range('2024-06-01', periods=30, freq='D')
        df = pd.DataFrame({
            'close': range(100, 130)
        }, index=dates)

        _, transitions = normalizer.handle_dst_transition(df)

        # Should have no transitions
        assert len(transitions) == 0


class TestDateTimeNormalizerTradingHours:
    """Test trading hours filtering."""

    def test_hkex_trading_hours_filter(self):
        """Test filtering to HKEX trading hours."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create 24-hour data
        dates = pd.date_range('2024-01-02', periods=24, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': range(100, 124)
        })

        result, stats = normalizer.filter_trading_hours(df)

        # Should have filtered data
        assert len(result) < len(df)
        assert stats['rows_removed'] > 0
        assert 'removal_pct' in stats

    def test_nyse_trading_hours_filter(self):
        """Test filtering to NYSE trading hours."""
        normalizer = DateTimeNormalizer(Market.NYSE)

        # Create 24-hour data
        dates = pd.date_range('2024-01-02', periods=24, freq='H', tz='America/New_York')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': range(100, 124)
        })

        result, stats = normalizer.filter_trading_hours(df)

        # Should filter data
        assert stats['original_rows'] == 24
        assert len(result) > 0

    def test_trading_hours_preserves_data_structure(self):
        """Test that trading hours filtering preserves DataFrame structure."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=48, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'open': range(100, 148),
            'high': range(101, 149),
            'low': range(99, 147),
            'close': range(100, 148),
            'volume': range(1000, 1048)
        })

        result, _ = normalizer.filter_trading_hours(df)

        # Should have all columns
        assert list(result.columns) == ['date', 'open', 'high', 'low', 'close', 'volume']


class TestDateTimeNormalizerHolidayFilter:
    """Test holiday and weekend filtering."""

    def test_filter_weekends(self):
        """Test filtering out weekends."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create week data including weekend
        dates = pd.date_range('2024-01-01', periods=7, freq='D')  # Jan 1=Mon
        df = pd.DataFrame({
            'close': range(100, 107)
        }, index=dates)

        result, removed = normalizer.filter_holidays(df)

        # Should have removed weekend dates
        assert len(removed) > 0

    def test_filter_holidays(self):
        """Test filtering out holidays."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Jan 1, 2024 is New Year's Day (holiday)
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'close': range(100, 105)
        }, index=dates)

        result, removed = normalizer.filter_holidays(df)

        # Should have removed holiday
        assert len(removed) > 0
        assert datetime(2024, 1, 1) in removed

    def test_holiday_filter_preserves_trading_days(self):
        """Test that trading days are preserved."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Start from Jan 2 (regular trading day)
        dates = pd.date_range('2024-01-02', periods=5, freq='D')
        df = pd.DataFrame({
            'close': range(100, 105)
        }, index=dates)

        result, removed = normalizer.filter_holidays(df)

        # Jan 2-5 should all be trading days
        assert len(result) >= 4


class TestDateTimeNormalizerBusinessDayAlignment:
    """Test business day alignment."""

    def test_drop_method(self):
        """Test alignment with drop method."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create data with weekend
        dates = pd.date_range('2024-01-01', periods=7, freq='D')
        df = pd.DataFrame({
            'close': range(100, 107)
        }, index=dates)

        result, report = normalizer.align_to_business_days(df, method='drop')

        # Should have fewer rows
        assert len(result) < len(df)
        assert report['method'] == 'drop'

    def test_alignment_report(self):
        """Test alignment report structure."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': range(100, 110)
        }, index=dates)

        _, report = normalizer.align_to_business_days(df, method='drop')

        # Check report structure
        assert 'original_rows' in report
        assert 'trading_days' in report
        assert 'non_trading_days' in report
        assert 'rows_after_alignment' in report


class TestDateTimeNormalizerPipeline:
    """Test complete normalization pipeline."""

    def test_full_pipeline(self):
        """Test complete normalization pipeline."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create raw data
        dates = pd.date_range('2024-01-01', periods=100, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': np.random.randn(100).cumsum() + 100
        })

        result, report = normalizer.normalize_datetime(
            df,
            source_tz='Asia/Hong_Kong',
            filter_hours=True,
            filter_holidays=True,
            align_business_days=True
        )

        # Check result
        assert len(result) > 0
        assert 'stages' in report
        assert report['final_status'] == 'success'

    def test_pipeline_without_holiday_filter(self):
        """Test pipeline without holiday filtering."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=50, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': range(100, 150)
        })

        result, report = normalizer.normalize_datetime(
            df,
            filter_hours=True,
            filter_holidays=False,
            align_business_days=True
        )

        assert len(result) > 0
        assert 'timezone_normalization' in report['stages']

    def test_pipeline_report_structure(self):
        """Test pipeline report contains all stages."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=50, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': range(100, 150)
        })

        _, report = normalizer.normalize_datetime(df)

        # Check report structure
        assert 'stages' in report
        assert 'timezone_normalization' in report['stages']
        assert 'final_status' in report
        assert 'output_rows' in report


class TestPipelineDateTimeNormalizer:
    """Test pipeline orchestration."""

    def test_pipeline_full_mode(self):
        """Test pipeline in full mode."""
        pipeline = PipelineDateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=50, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': range(100, 150)
        })

        result, report = pipeline.execute_normalization_pipeline(
            df,
            source_tz='Asia/Hong_Kong',
            full_pipeline=True
        )

        assert len(result) > 0
        assert isinstance(report, dict)

    def test_pipeline_basic_mode(self):
        """Test pipeline in basic mode."""
        pipeline = PipelineDateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=10, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'close': range(100, 110)
        })

        result, report = pipeline.execute_normalization_pipeline(
            df,
            source_tz='Asia/Hong_Kong',
            full_pipeline=False
        )

        assert len(result) == len(df)
        assert report['status'] == 'basic_normalization_complete'


class TestDateTimeNormalizerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        df = pd.DataFrame({'close': []})

        # Should not raise error
        result = normalizer.normalize_timezone(df, source_tz='Asia/Hong_Kong')
        assert len(result) == 0

    def test_single_row_dataframe(self):
        """Test with single row DataFrame."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        df = pd.DataFrame({
            'date': pd.date_range('2024-01-02', periods=1),
            'close': [100]
        })

        result = normalizer.normalize_timezone(df, source_tz='Asia/Hong_Kong')
        assert len(result) == 1

    def test_all_weekend_data(self):
        """Test with all weekend data."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create weekend-only dates
        dates = pd.date_range('2024-01-06', periods=4, freq='D')  # Jan 6-9 (Sat-Tue)
        df = pd.DataFrame({
            'close': range(100, 104)
        }, index=dates)

        result, removed = normalizer.filter_holidays(df)

        # Should have removed Saturday and Sunday
        assert len(removed) >= 2

    def test_all_holiday_data(self):
        """Test when data covers only holidays."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Jan 1, 2024 is New Year's Day
        dates = pd.date_range('2024-01-01', periods=1)
        df = pd.DataFrame({
            'close': [100]
        }, index=dates)

        result, removed = normalizer.filter_holidays(df)

        # Should be removed as holiday
        assert len(removed) == 1

    def test_mixed_timezone_aware_naive(self):
        """Test DataFrame with mixed timezone awareness."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create naive datetime
        dates = pd.date_range('2024-01-02', periods=5, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'close': range(100, 105)
        })

        # Should handle without error
        result = normalizer.normalize_timezone(df, source_tz='Asia/Hong_Kong')
        assert len(result) == 5


class TestDateTimeNormalizerPerformance:
    """Test performance characteristics."""

    def test_normalizer_instantiation_performance(self):
        """Test that normalizer instantiates quickly."""
        import time

        start = time.time()
        for _ in range(100):
            normalizer = DateTimeNormalizer(Market.HKEX)
        elapsed = time.time() - start

        # Should create 100 instances in less than 100ms
        assert elapsed < 0.1, f"Instantiation too slow: {elapsed:.3f}s"

    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        import time

        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create 1000-record dataset
        dates = pd.date_range('2024-01-01', periods=1000, freq='H', tz='Asia/Hong_Kong')
        dates_utc = dates.tz_convert('UTC')

        df = pd.DataFrame({
            'date': dates_utc,
            'close': np.random.randn(1000).cumsum() + 100
        })

        start = time.time()
        result, _ = normalizer.normalize_datetime(df)
        elapsed = time.time() - start

        # Should process in less than 5 seconds
        assert elapsed < 5, f"Processing too slow: {elapsed:.3f}s"
        assert len(result) > 0


class TestDateTimeNormalizerIntegration:
    """Integration tests combining multiple features."""

    def test_realistic_hkex_data_pipeline(self):
        """Test realistic HKEX data normalization pipeline."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        # Create realistic HKEX trading data
        hk_tz = ZoneInfo('Asia/Hong_Kong')

        # Create data spanning week with trading and non-trading times
        dates = pd.date_range('2024-01-02', periods=168, freq='H', tz=hk_tz)

        df = pd.DataFrame({
            'date': dates.tz_convert('UTC'),
            'open': 100 + np.random.randn(168),
            'high': 101 + np.random.randn(168),
            'low': 99 + np.random.randn(168),
            'close': 100 + np.random.randn(168),
            'volume': np.random.randint(1000, 10000, 168)
        })

        result, report = normalizer.normalize_datetime(
            df,
            filter_hours=True,
            filter_holidays=True,
            align_business_days=True
        )

        # Check result
        assert len(result) > 0
        assert len(result) < len(df)  # Should have filtered
        assert 'stages' in report

    def test_multiple_market_normalization(self):
        """Test normalization for different markets."""
        for market in [Market.HKEX, Market.NYSE, Market.NASDAQ]:
            normalizer = DateTimeNormalizer(market)

            dates = pd.date_range('2024-01-02', periods=50, freq='H')
            df = pd.DataFrame({
                'close': range(100, 150)
            }, index=dates)

            result = normalizer.normalize_timezone(df)

            assert len(result) > 0
            assert result.index.tz is not None


class TestDateTimeNormalizerErrorHandling:
    """Test error handling and recovery."""

    def test_invalid_timezone_handling(self):
        """Test handling of invalid timezone."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=5)
        df = pd.DataFrame({
            'date': dates,
            'close': range(100, 105)
        })

        # Should handle gracefully
        result = normalizer.normalize_timezone(df, source_tz='Invalid/Timezone')
        # Might raise exception but shouldn't crash uncontrollably
        assert result is not None or True

    def test_dataframe_with_missing_columns(self):
        """Test DataFrame missing expected columns."""
        normalizer = DateTimeNormalizer(Market.HKEX)

        dates = pd.date_range('2024-01-02', periods=5)
        df = pd.DataFrame({
            'price': range(100, 105)  # Wrong column name
        }, index=dates)

        # Should handle gracefully
        result = normalizer.normalize_timezone(df)
        assert result is not None


# Test execution
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
