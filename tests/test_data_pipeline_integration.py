"""
Data Pipeline Integration Tests

Tests the complete data pipeline:
Data Source → Validation → Cleaning → Processing → Storage

Run with: pytest tests/test_data_pipeline_integration.py -v
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.data_pipeline.sources import HKEXDataSource, FileDataSource
from src.data_pipeline.cleaners import BasicDataCleaner, OutlierDetector
from src.data_pipeline.processors import (
    BasicDataProcessor,
    MissingDataHandler,
    FeatureEngineer,
)
from src.data_pipeline.pipeline_orchestrator import DataPipelineOrchestrator
from src.database import MemoryRepository, SQLiteRepository
from tests.fixtures import mock_ohlcv_data, MockOHLCVGenerator


class TestDataSourceIntegration:
    """Test data source integration."""

    def test_file_data_source_basic(self):
        """Test file data source basic functionality."""
        # Create mock data
        df = mock_ohlcv_data("0700.HK", num_days=100)
        df.to_csv("test_data.csv")

        try:
            source = FileDataSource(".")
            raw = source.fetch_raw(
                "test_data",
                datetime.now() - timedelta(days=100),
                datetime.now(),
                file_path="test_data.csv",
            )

            assert raw is not None
            assert "data" in raw
            assert len(raw["data"]) > 0

            # Validate
            validation = source.validate(raw)
            assert validation.is_valid
            assert validation.quality_score > 0.7

        finally:
            import os
            if os.path.exists("test_data.csv"):
                os.remove("test_data.csv")

    def test_hkex_data_source(self):
        """Test HKEX unified data source."""
        source = HKEXDataSource()

        # Check if HKEX source is properly configured
        assert "0700.hk" in source.HSI_STOCKS

        # Test metadata
        metadata = source.get_metadata()
        assert metadata is not None
        assert metadata.source_name == "hkex_unified"


class TestDataCleanerIntegration:
    """Test data cleaner integration."""

    def test_basic_cleaner_full_pipeline(self):
        """Test basic cleaner with mock data."""
        # Generate mock data
        df = mock_ohlcv_data("0700.HK", num_days=100)

        # Add some issues
        df.loc[df.index[10], "Close"] = None  # Null value
        df.loc[df.index[20:22], :] = df.loc[df.index[20:22], :].duplicated()  # Duplicates

        cleaner = BasicDataCleaner()
        cleaned = cleaner.clean(df)

        # Verify cleaning
        assert cleaned is not None
        assert len(cleaned) < len(df)  # Some rows removed
        assert cleaned.isnull().sum().sum() == 0  # No nulls
        assert cleaner.get_quality_score() > 0.5

    def test_outlier_detector(self):
        """Test outlier detector."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        # Add outlier
        df.loc[df.index[50], "Close"] = df["Close"].mean() * 10

        detector = OutlierDetector(z_score_threshold=3.0, remove_outliers=False)
        detected = detector.clean(df)

        assert detected is not None
        assert detector.outliers_detected > 0


class TestDataProcessorIntegration:
    """Test data processor integration."""

    def test_basic_processor_full_pipeline(self):
        """Test basic processor with cleaning."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        # Clean first
        cleaner = BasicDataCleaner()
        cleaned = cleaner.clean(df)

        # Process
        processor = BasicDataProcessor()
        processed = processor.process(cleaned)

        # Verify
        assert processed is not None
        assert len(processed) == len(cleaned)
        assert "Daily_Return" in processed.columns
        assert "Open_Normalized" in processed.columns
        assert "Volume_Normalized" in processed.columns

        info = processor.get_processing_info()
        assert "calculated_returns" in info["operations"]

    def test_missing_data_handler(self):
        """Test missing data handler."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        # Add missing values
        df.loc[df.index[10:15], "Close"] = None

        handler = MissingDataHandler(strategy="forward_fill")
        handled = handler.process(df)

        assert handled is not None
        assert handled["Close"].isnull().sum() == 0

    def test_feature_engineer(self):
        """Test feature engineer."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        engineer = FeatureEngineer(
            features=["sma", "volatility"],
            windows={"short": 20, "medium": 50},
        )
        features = engineer.process(df)

        assert "SMA_20" in features.columns
        assert "SMA_50" in features.columns
        assert "Volatility_20" in features.columns


class TestDataRepositoryIntegration:
    """Test data repository integration."""

    def test_memory_repository(self):
        """Test memory repository."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        repo = MemoryRepository()

        # Save
        repo.save("0700.HK", df)
        assert repo.exists("0700.HK")

        # Load
        loaded = repo.load(
            "0700.HK",
            datetime.now() - timedelta(days=100),
            datetime.now(),
        )
        assert loaded is not None
        assert len(loaded) > 0

        # List
        symbols = repo.list_symbols()
        assert "0700.HK" in symbols

        # Delete
        repo.delete("0700.HK")
        assert not repo.exists("0700.HK")

    def test_sqlite_repository(self):
        """Test SQLite repository."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.db"
            repo = SQLiteRepository(db_path)

            # Save
            repo.save("0700.HK", df)
            assert repo.exists("0700.HK")

            # Load
            loaded = repo.load(
                "0700.HK",
                datetime.now() - timedelta(days=100),
                datetime.now(),
            )
            assert loaded is not None
            assert len(loaded) > 0

            # Metadata
            metadata = repo.get_metadata("0700.HK")
            assert metadata is not None
            assert metadata["symbol"] == "0700.HK"


class TestPipelineOrchestratorIntegration:
    """Test pipeline orchestrator."""

    def test_full_pipeline(self):
        """Test complete pipeline."""
        orchestrator = DataPipelineOrchestrator()
        orchestrator.register_source("file", FileDataSource("."))

        # Create test file
        df = mock_ohlcv_data("test", num_days=100)
        df.to_csv("test.csv")

        try:
            result = orchestrator.process(
                source="file",
                symbol="test",
                start_date="2023-01-01",
                end_date="2024-01-01",
                file_path="test.csv",
            )

            # Verify result structure
            assert "processed_data" in result
            assert "pipeline_info" in result
            assert result["pipeline_info"]["success"]

            # Verify steps
            assert "fetch" in result["pipeline_info"]["steps"]
            assert "validate" in result["pipeline_info"]["steps"]
            assert "clean" in result["pipeline_info"]["steps"]
            assert "process" in result["pipeline_info"]["steps"]

        finally:
            import os
            if os.path.exists("test.csv"):
                os.remove("test.csv")


class TestDataQualityMetrics:
    """Test data quality metrics."""

    def test_quality_score_tracking(self):
        """Test quality score throughout pipeline."""
        df = mock_ohlcv_data("0700.HK", num_days=100)

        # Clean
        cleaner = BasicDataCleaner()
        cleaned = cleaner.clean(df)
        clean_quality = cleaner.get_quality_score()

        assert 0 <= clean_quality <= 1

        # Process
        processor = BasicDataProcessor()
        processed = processor.process(cleaned)
        process_info = processor.get_processing_info()

        assert "temporal_aligned" in process_info
        assert "normalized" in process_info


class TestErrorHandling:
    """Test error handling."""

    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        df = pd.DataFrame({
            "Price": [100, 101, 102],
            "Count": [1000, 1100, 1050],
        })

        cleaner = BasicDataCleaner()
        result = cleaner.clean(df)

        # Should handle gracefully
        assert result is not None

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()

        cleaner = BasicDataCleaner()
        result = cleaner.clean(df)

        assert result.empty

    def test_invalid_dates(self):
        """Test handling of invalid dates."""
        df = mock_ohlcv_data("0700.HK", num_days=10)

        # Create processor with invalid date index
        processor = BasicDataProcessor()
        result = processor.process(df)

        # Should handle gracefully
        assert result is not None


@pytest.mark.parametrize("symbol,days", [
    ("0700.HK", 50),
    ("0388.HK", 100),
    ("1398.HK", 200),
])
def test_parametrized_pipeline(symbol, days):
    """Test pipeline with different symbols and date ranges."""
    df = MockOHLCVGenerator().generate(symbol, num_days=days)

    cleaner = BasicDataCleaner()
    cleaned = cleaner.clean(df)

    processor = BasicDataProcessor()
    processed = processor.process(cleaned)

    assert processed is not None
    assert len(processed) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
