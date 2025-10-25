"""
Comprehensive unit tests for data cleaning engine.

Tests CleaningEngine and PipelineCleaner classes:
1. Missing data handling strategies
2. Outlier detection and normalization
3. Quality scoring
4. Technical indicator enhancement
5. Full cleaning pipeline
"""

import pytest
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from src.data_pipeline.cleaners import (
    CleaningEngine, QualityScorer, PipelineCleaner,
    MissingDataStrategy, OutlierNormalizationStrategy
)


class TestQualityScorer:
    """Test quality scoring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = QualityScorer()
        dates = pd.date_range('2025-01-01', periods=10, freq='D', tz='UTC')
        self.df = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [105.0] * 10,
            'low': [95.0] * 10,
            'close': [102.0] * 10,
            'volume': [1000000] * 10
        }, index=dates)

    def test_completeness_perfect(self):
        """Test completeness scoring with complete data."""
        record = self.df.iloc[0]
        score = self.scorer.score_completeness(record)
        assert score == 1.0

    def test_completeness_with_missing(self):
        """Test completeness scoring with missing values."""
        record = self.df.iloc[0].copy()
        record['close'] = np.nan
        score = self.scorer.score_completeness(record)
        assert score < 1.0

    def test_ohlc_logic_valid(self):
        """Test OHLC logic scoring with valid data."""
        record = self.df.iloc[0]
        score = self.scorer.score_ohlc_logic(record)
        assert score == 1.0

    def test_ohlc_logic_invalid_close(self):
        """Test OHLC logic scoring with invalid close."""
        record = self.df.iloc[0].copy()
        record['close'] = 110.0  # Close > High
        score = self.scorer.score_ohlc_logic(record)
        assert score == 0.0

    def test_volume_positive(self):
        """Test volume scoring with positive volume."""
        record = self.df.iloc[0]
        score = self.scorer.score_volume(record)
        assert score == 1.0

    def test_volume_zero(self):
        """Test volume scoring with zero volume."""
        record = self.df.iloc[0].copy()
        record['volume'] = 0
        score = self.scorer.score_volume(record)
        assert score < 1.0

    def test_volume_negative(self):
        """Test volume scoring with negative volume."""
        record = self.df.iloc[0].copy()
        record['volume'] = -100
        score = self.scorer.score_volume(record)
        assert score == 0.0

    def test_outlier_detection_normal(self):
        """Test outlier scoring with normal price change."""
        score = self.scorer.score_outliers(0.05, threshold=0.20)  # 5% change
        assert score == 1.0

    def test_outlier_detection_moderate(self):
        """Test outlier scoring with moderate outlier."""
        score = self.scorer.score_outliers(0.25, threshold=0.20)  # 25% change
        assert score < 1.0 and score > 0.0

    def test_outlier_detection_severe(self):
        """Test outlier scoring with severe outlier."""
        score = self.scorer.score_outliers(0.70, threshold=0.20)  # 70% change
        assert score == 0.0

    def test_consistency_edge_cases(self):
        """Test consistency scoring at edges."""
        score_first = self.scorer.score_consistency(self.df, 0)
        score_last = self.scorer.score_consistency(self.df, len(self.df) - 1)
        assert score_first == 1.0
        assert score_last == 1.0

    def test_overall_quality_score(self):
        """Test overall quality score calculation."""
        score = self.scorer.calculate_quality_score(self.df, 5)
        assert 0.0 <= score <= 1.0


class TestCleaningEngineMissingData:
    """Test missing data handling strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range('2025-01-01', periods=10, freq='D', tz='UTC')
        self.df_with_missing = pd.DataFrame({
            'open': [100.0, np.nan, 102.0, 103.0, np.nan, 105.0, 106.0, 107.0, 108.0, 109.0],
            'high': [105.0, np.nan, 107.0, 108.0, np.nan, 110.0, 111.0, 112.0, 113.0, 114.0],
            'low': [95.0, np.nan, 97.0, 98.0, np.nan, 100.0, 101.0, 102.0, 103.0, 104.0],
            'close': [102.0, np.nan, 104.0, 105.0, np.nan, 107.0, 108.0, 109.0, 110.0, 111.0],
            'volume': [1000000, np.nan, 1100000, 1150000, np.nan, 1200000, 1250000, 1300000, 1350000, 1400000]
        }, index=dates)

    def test_forward_fill_strategy(self):
        """Test forward fill missing data strategy."""
        engine = CleaningEngine(missing_strategy=MissingDataStrategy.FORWARD_FILL)
        result = engine.handle_missing_data(self.df_with_missing)
        # Forward fill should propagate values
        assert not result.isnull().any().any()
        assert result.iloc[1]['close'] == result.iloc[0]['close']

    def test_backward_fill_strategy(self):
        """Test backward fill missing data strategy."""
        engine = CleaningEngine(missing_strategy=MissingDataStrategy.BACKWARD_FILL)
        result = engine.handle_missing_data(self.df_with_missing)
        assert not result.isnull().any().any()

    def test_interpolate_strategy(self):
        """Test interpolation missing data strategy."""
        engine = CleaningEngine(missing_strategy=MissingDataStrategy.INTERPOLATE)
        result = engine.handle_missing_data(self.df_with_missing)
        assert not result.isnull().any().any()

    def test_drop_strategy(self):
        """Test drop missing data strategy."""
        engine = CleaningEngine(missing_strategy=MissingDataStrategy.DROP)
        result = engine.handle_missing_data(self.df_with_missing)
        # Should remove rows with NaN
        assert len(result) < len(self.df_with_missing)
        assert not result.isnull().any().any()


class TestCleaningEngineOutliers:
    """Test outlier normalization strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range('2025-01-01', periods=10, freq='D', tz='UTC')
        self.df_with_outliers = pd.DataFrame({
            'open': [100.0, 101.0, 130.0, 129.0, 128.0, 100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 135.0, 134.0, 133.0, 105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [95.0, 96.0, 125.0, 124.0, 123.0, 95.0, 96.0, 97.0, 98.0, 99.0],
            'close': [102.0, 103.0, 132.0, 131.0, 130.0, 102.0, 103.0, 104.0, 105.0, 106.0],
            'volume': [1000000] * 10
        }, index=dates)

    def test_outlier_detection(self):
        """Test outlier detection."""
        engine = CleaningEngine()
        _, is_outlier = engine.normalize_outliers(self.df_with_outliers)
        # Row 2 should be detected as outlier (30% jump)
        assert is_outlier.iloc[2] == True

    def test_flag_strategy(self):
        """Test flag outlier strategy (no modification)."""
        engine = CleaningEngine(outlier_strategy=OutlierNormalizationStrategy.FLAG)
        result, is_outlier = engine.normalize_outliers(self.df_with_outliers)
        # Data should be unchanged
        assert (result['close'] == self.df_with_outliers['close']).all()

    def test_clip_strategy(self):
        """Test clip outlier strategy."""
        engine = CleaningEngine(outlier_strategy=OutlierNormalizationStrategy.CLIP)
        result, is_outlier = engine.normalize_outliers(self.df_with_outliers)
        # Should handle clipping (may or may not modify depending on bounds)
        assert len(result) == len(self.df_with_outliers)
        # At least some outliers should be detected
        assert is_outlier.sum() > 0

    def test_smooth_strategy(self):
        """Test smooth outlier strategy."""
        engine = CleaningEngine(outlier_strategy=OutlierNormalizationStrategy.SMOOTH)
        result, is_outlier = engine.normalize_outliers(self.df_with_outliers)
        # Should handle smoothing
        assert len(result) == len(self.df_with_outliers)
        # At least some outliers should be detected
        assert is_outlier.sum() > 0

    def test_remove_strategy(self):
        """Test remove outlier strategy."""
        engine = CleaningEngine(outlier_strategy=OutlierNormalizationStrategy.REMOVE)
        result, is_outlier = engine.normalize_outliers(self.df_with_outliers)
        # Outlier rows should be removed
        assert len(result) < len(self.df_with_outliers)


class TestCleaningEngineQualityScores:
    """Test quality score calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        self.df_good = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'volume': [1000000, 1100000, 1200000, 1150000, 1300000]
        }, index=dates)

        self.df_poor = pd.DataFrame({
            'open': [100.0, np.nan, 102.0, np.nan, 104.0],
            'high': [105.0, np.nan, 107.0, np.nan, 109.0],
            'low': [95.0, np.nan, 97.0, np.nan, 99.0],
            'close': [110.0, np.nan, 104.0, np.nan, 106.0],  # Invalid close
            'volume': [-100, np.nan, 1200000, 0, 1300000]  # Negative, zero
        }, index=dates)

    def test_quality_scores_good_data(self):
        """Test quality scores for good data."""
        engine = CleaningEngine()
        scores = engine.calculate_quality_scores(self.df_good)
        assert (scores > 0.7).all()  # Good data should score high

    def test_quality_scores_poor_data(self):
        """Test quality scores for poor data."""
        engine = CleaningEngine()
        scores = engine.calculate_quality_scores(self.df_poor)
        assert (scores >= 0.0).all() and (scores <= 1.0).all()
        assert scores.iloc[0] < 0.7  # Invalid close, negative volume

    def test_quality_scores_range(self):
        """Test that quality scores are within 0-1 range."""
        engine = CleaningEngine()
        scores = engine.calculate_quality_scores(self.df_good)
        assert (scores >= 0.0).all() and (scores <= 1.0).all()


class TestCleaningEnginePipeline:
    """Test complete cleaning pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range('2025-01-01', periods=20, freq='D', tz='UTC')
        self.df_raw = pd.DataFrame({
            'open': [100.0 + i * 0.5 for i in range(20)],
            'high': [105.0 + i * 0.5 for i in range(20)],
            'low': [95.0 + i * 0.5 for i in range(20)],
            'close': [102.0 + i * 0.5 for i in range(20)],
            'volume': [1000000 + i * 10000 for i in range(20)]
        }, index=dates)

    def test_clean_data_returns_tuple(self):
        """Test that clean_data returns tuple."""
        engine = CleaningEngine()
        result_df, report = engine.clean_data(self.df_raw, '0700.HK')
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(report, dict)

    def test_clean_data_adds_quality_scores(self):
        """Test that quality scores are added."""
        engine = CleaningEngine()
        result_df, _ = engine.clean_data(self.df_raw, '0700.HK')
        assert 'quality_score' in result_df.columns

    def test_clean_data_adds_outlier_flag(self):
        """Test that outlier flag is added."""
        engine = CleaningEngine()
        result_df, _ = engine.clean_data(self.df_raw, '0700.HK')
        assert 'is_outlier' in result_df.columns

    def test_cleaning_report_structure(self):
        """Test cleaning report structure."""
        engine = CleaningEngine()
        _, report = engine.clean_data(self.df_raw, '0700.HK')
        assert 'symbol' in report
        assert 'original_records' in report
        assert 'final_records' in report
        assert 'steps' in report
        assert len(report['steps']) >= 3

    def test_enhance_with_indicators(self):
        """Test technical indicator enhancement."""
        engine = CleaningEngine()
        result_df, _ = engine.clean_data(self.df_raw, '0700.HK')
        enhanced = engine.enhance_with_indicators(result_df, ['sma', 'ema', 'rsi', 'bb'])
        assert 'sma_20' in enhanced.columns
        assert 'ema_12' in enhanced.columns
        assert 'rsi_14' in enhanced.columns
        assert 'bb_upper' in enhanced.columns
        assert 'bb_lower' in enhanced.columns


class TestPipelineCleaner:
    """Test complete cleaning pipeline orchestration."""

    def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range('2025-01-06', periods=20, freq='B', tz='UTC')
        self.df_raw = pd.DataFrame({
            'open': [100.0 + i * 0.5 for i in range(20)],
            'high': [105.0 + i * 0.5 for i in range(20)],
            'low': [95.0 + i * 0.5 for i in range(20)],
            'close': [102.0 + i * 0.5 for i in range(20)],
            'volume': [1000000 + i * 10000 for i in range(20)]
        }, index=dates)

    def test_pipeline_execution(self):
        """Test complete pipeline execution."""
        cleaner = PipelineCleaner()
        result_df, report = cleaner.execute_cleaning_pipeline(self.df_raw, '0700.HK')
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(report, dict)

    def test_pipeline_report_structure(self):
        """Test pipeline report structure."""
        cleaner = PipelineCleaner()
        _, report = cleaner.execute_cleaning_pipeline(self.df_raw, '0700.HK')
        assert 'symbol' in report
        assert 'stages' in report
        assert 'validation' in report['stages']
        assert 'cleaning' in report['stages']
        assert 'post_validation' in report['stages']

    def test_pipeline_with_indicators(self):
        """Test pipeline with indicator enhancement."""
        cleaner = PipelineCleaner()
        result_df, report = cleaner.execute_cleaning_pipeline(
            self.df_raw, '0700.HK', enhance_indicators=True
        )
        assert 'enhancement' in report['stages']
        assert 'sma_20' in result_df.columns

    def test_pipeline_output_quality(self):
        """Test that pipeline output maintains quality."""
        cleaner = PipelineCleaner()
        result_df, report = cleaner.execute_cleaning_pipeline(self.df_raw, '0700.HK')
        # All required OHLCV columns should be present
        assert all(col in result_df.columns for col in ['open', 'high', 'low', 'close', 'volume'])


class TestCleaningEngineEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_row_dataframe(self):
        """Test cleaning of single-row DataFrame."""
        dates = pd.date_range('2025-01-01', periods=1, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [102.0],
            'volume': [1000000]
        }, index=dates)

        engine = CleaningEngine()
        result, report = engine.clean_data(df, '0700.HK')
        assert len(result) >= 1

    def test_empty_dataframe(self):
        """Test cleaning of empty DataFrame."""
        df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        engine = CleaningEngine()
        result, report = engine.clean_data(df, '0700.HK')
        assert len(result) == 0

    def test_all_nan_dataframe(self):
        """Test cleaning of DataFrame with all NaN values."""
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [np.nan] * 5,
            'high': [np.nan] * 5,
            'low': [np.nan] * 5,
            'close': [np.nan] * 5,
            'volume': [np.nan] * 5
        }, index=dates)

        engine = CleaningEngine(missing_strategy=MissingDataStrategy.FORWARD_FILL)
        result, report = engine.clean_data(df, '0700.HK')
        # Should handle gracefully
        assert len(result) == len(df)

    def test_extreme_prices(self):
        """Test cleaning with extreme but valid prices."""
        dates = pd.date_range('2025-01-01', periods=5, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [0.01, 0.02, 0.03, 0.04, 0.05],
            'high': [10000.0, 10001.0, 10002.0, 10003.0, 10004.0],
            'low': [0.01, 0.02, 0.03, 0.04, 0.05],
            'close': [5000.0, 5001.0, 5002.0, 5003.0, 5004.0],
            'volume': [1000000] * 5
        }, index=dates)

        engine = CleaningEngine()
        result, report = engine.clean_data(df, '0700.HK')
        assert len(result) == 5


class TestCleaningEnginePerformance:
    """Test performance characteristics."""

    def test_large_dataset_performance(self):
        """Test performance on large dataset."""
        import time
        dates = pd.date_range('2020-01-01', periods=1000, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0 + i * 0.1 for i in range(1000)],
            'high': [105.0 + i * 0.1 for i in range(1000)],
            'low': [95.0 + i * 0.1 for i in range(1000)],
            'close': [102.0 + i * 0.1 for i in range(1000)],
            'volume': [1000000] * 1000
        }, index=dates)

        engine = CleaningEngine()
        start = time.time()
        result, report = engine.clean_data(df, '0700.HK')
        elapsed = time.time() - start

        # Should process 1000 records in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert len(result) == 1000

    def test_engine_instantiation_performance(self):
        """Test performance of engine instantiation."""
        import time
        start = time.time()
        for _ in range(100):
            CleaningEngine()
        elapsed = time.time() - start

        # Should create 100 instances in < 100ms
        assert elapsed < 0.1
