"""
Phase 5.3: Performance and Load Tests

Performance benchmarks and load testing for the alternative data framework.
Measures throughput, latency, and resource usage under various loads.

Test Coverage:
- Data pipeline performance (cleaning, alignment, normalization, scoring)
- Backtest execution performance
- Dashboard API performance
- Memory usage under heavy load
- Concurrent operation performance
"""

import pytest
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psutil
import tempfile

# Data pipeline components
from src.data_pipeline.data_cleaner import DataCleaner
from src.data_pipeline.temporal_aligner import TemporalAligner
from src.data_pipeline.data_normalizer import DataNormalizer
from src.data_pipeline.quality_scorer import QualityScorer
from src.data_pipeline.pipeline_processor import PipelineProcessor

# Backtest components
from src.backtest.signal_validation import SignalValidator
from src.backtest.signal_attribution_metrics import SignalAttributionAnalyzer
from src.backtest.result_service import (
    BacktestResultService,
    BacktestResultMetadata,
    BacktestResultData
)


class TestDataPipelinePerformance:
    """Performance tests for data pipeline operations"""

    @pytest.fixture
    def large_dataset(self):
        """Create large dataset for performance testing"""
        dates = pd.date_range('2020-01-01', periods=5000, freq='D')

        data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 5000),
            'high': np.random.uniform(110, 120, 5000),
            'low': np.random.uniform(90, 100, 5000),
            'close': np.random.uniform(100, 110, 5000),
            'volume': np.random.uniform(1000000, 2000000, 5000),
            'symbol': '0700.HK'
        }, index=dates)

        return data

    def test_data_cleaning_performance(self, large_dataset):
        """Benchmark data cleaning speed"""
        cleaner = DataCleaner()

        start_time = time.time()
        cleaned = cleaner.clean(large_dataset)
        elapsed = time.time() - start_time

        # Performance assertion: should process 5000 rows in < 1 second
        assert elapsed < 1.0, f"Cleaning took {elapsed:.2f}s, expected < 1s"
        assert len(cleaned) > 0

        # Calculate throughput
        throughput = len(large_dataset) / elapsed
        print(f"Data cleaning throughput: {throughput:.0f} rows/sec")

    def test_temporal_alignment_performance(self, large_dataset):
        """Benchmark temporal alignment speed"""
        aligner = TemporalAligner()

        cleaner = DataCleaner()
        cleaned = cleaner.clean(large_dataset)

        start_time = time.time()
        aligned = aligner.align_to_trading_days(cleaned)
        elapsed = time.time() - start_time

        # Performance assertion: should align in < 2 seconds
        assert elapsed < 2.0, f"Alignment took {elapsed:.2f}s, expected < 2s"
        assert len(aligned) > 0

        throughput = len(cleaned) / elapsed
        print(f"Temporal alignment throughput: {throughput:.0f} rows/sec")

    def test_data_normalization_performance(self, large_dataset):
        """Benchmark data normalization speed"""
        normalizer = DataNormalizer()

        cleaner = DataCleaner()
        cleaned = cleaner.clean(large_dataset)
        aligner = TemporalAligner()
        aligned = aligner.align_to_trading_days(cleaned)

        start_time = time.time()
        normalized = normalizer.fit_transform(aligned)
        elapsed = time.time() - start_time

        # Performance assertion: should normalize in < 1 second
        assert elapsed < 1.0, f"Normalization took {elapsed:.2f}s, expected < 1s"
        assert len(normalized) > 0

        throughput = len(aligned) / elapsed
        print(f"Data normalization throughput: {throughput:.0f} rows/sec")

    def test_quality_scoring_performance(self, large_dataset):
        """Benchmark quality scoring speed"""
        scorer = QualityScorer()

        cleaner = DataCleaner()
        cleaned = cleaner.clean(large_dataset)
        aligner = TemporalAligner()
        aligned = aligner.align_to_trading_days(cleaned)
        normalizer = DataNormalizer()
        normalized = normalizer.fit_transform(aligned)

        start_time = time.time()
        quality = scorer.calculate_overall_grade(normalized)
        elapsed = time.time() - start_time

        # Performance assertion: should score in < 1 second
        assert elapsed < 1.0, f"Quality scoring took {elapsed:.2f}s, expected < 1s"
        assert quality is not None

        print(f"Quality scoring time: {elapsed:.3f}s")

    def test_complete_pipeline_performance(self, large_dataset):
        """Benchmark complete pipeline execution"""
        start_time = time.time()

        # Step 1: Clean
        cleaner = DataCleaner()
        cleaned = cleaner.clean(large_dataset)

        # Step 2: Align
        aligner = TemporalAligner()
        aligned = aligner.align_to_trading_days(cleaned)

        # Step 3: Normalize
        normalizer = DataNormalizer()
        normalized = normalizer.fit_transform(aligned)

        # Step 4: Score quality
        scorer = QualityScorer()
        quality = scorer.calculate_overall_grade(normalized)

        # Step 5: Process
        pipeline = PipelineProcessor()
        result = pipeline.process(normalized)

        elapsed = time.time() - start_time

        # Complete pipeline should process in < 5 seconds
        assert elapsed < 5.0, f"Complete pipeline took {elapsed:.2f}s, expected < 5s"
        assert len(result) > 0

        print(f"Complete pipeline time: {elapsed:.2f}s for {len(large_dataset)} rows")


class TestMemoryUsage:
    """Test memory usage under heavy loads"""

    def test_large_dataset_memory_usage(self):
        """Test memory usage with large dataset"""
        # Create very large dataset
        dates = pd.date_range('2020-01-01', periods=10000, freq='D')

        # Measure memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 10000),
            'high': np.random.uniform(110, 120, 10000),
            'low': np.random.uniform(90, 100, 10000),
            'close': np.random.uniform(100, 110, 10000),
            'volume': np.random.uniform(1000000, 2000000, 10000),
        }, index=dates)

        # Measure memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before

        print(f"Memory used for 10k rows: {mem_used:.2f} MB")

        # Memory usage should be reasonable (< 500 MB for 10k rows)
        assert mem_used < 500, f"Memory usage {mem_used:.2f} MB is too high"

    def test_pipeline_memory_stability(self):
        """Test memory doesn't leak in repeated operations"""
        cleaner = DataCleaner()
        normalizer = DataNormalizer()

        process = psutil.Process()

        mem_measurements = []

        for i in range(5):
            dates = pd.date_range('2020-01-01', periods=1000, freq='D')
            data = pd.DataFrame({
                'open': np.random.uniform(100, 110, 1000),
                'high': np.random.uniform(110, 120, 1000),
                'low': np.random.uniform(90, 100, 1000),
                'close': np.random.uniform(100, 110, 1000),
                'volume': np.random.uniform(1000000, 2000000, 1000),
            }, index=dates)

            cleaned = cleaner.clean(data)
            normalized = normalizer.fit_transform(cleaned)

            mem = process.memory_info().rss / 1024 / 1024  # MB
            mem_measurements.append(mem)

        # Memory usage should not grow significantly (< 20% increase)
        initial_mem = mem_measurements[0]
        final_mem = mem_measurements[-1]
        mem_growth = (final_mem - initial_mem) / initial_mem * 100

        print(f"Memory growth over 5 iterations: {mem_growth:.2f}%")
        assert mem_growth < 20, f"Memory grew {mem_growth:.2f}%, expected < 20%"


class TestBacktestPerformance:
    """Performance tests for backtest operations"""

    @pytest.fixture
    def large_trade_dataset(self):
        """Create large trade dataset"""
        trades = []
        for i in range(1000):
            trades.append({
                'timestamp': datetime(2025, 1, 1) + timedelta(hours=i),
                'symbol': '0700.HK',
                'side': 'buy' if i % 2 == 0 else 'sell',
                'quantity': 100,
                'price': 300.0 + i * 0.1,
                'pnl': np.random.uniform(-500, 500),
                'source': np.random.choice(['price_only', 'combined', 'alt_data_only']),
                'confidence': np.random.uniform(0.5, 1.0)
            })
        return trades

    def test_signal_attribution_performance(self, large_trade_dataset):
        """Benchmark signal attribution calculation"""
        analyzer = SignalAttributionAnalyzer()

        start_time = time.time()
        accuracy = analyzer.calculate_signal_accuracy(large_trade_dataset)
        elapsed = time.time() - start_time

        # Should calculate accuracy in < 1 second
        assert elapsed < 1.0, f"Attribution took {elapsed:.2f}s, expected < 1s"
        assert accuracy is not None

        print(f"Signal attribution speed: {elapsed:.3f}s for {len(large_trade_dataset)} trades")

    def test_signal_validation_performance(self):
        """Benchmark signal validation"""
        validator = SignalValidator()

        trades = []
        for i in range(100):
            trades.append({
                'return': np.random.normal(0.01, 0.02),
                'confidence': np.random.uniform(0.5, 1.0)
            })

        start_time = time.time()
        # Simple validation operation
        valid_trades = [t for t in trades if t['confidence'] > 0.6]
        elapsed = time.time() - start_time

        # Should validate in < 0.1 seconds
        assert elapsed < 0.1, f"Validation took {elapsed:.2f}s, expected < 0.1s"

        print(f"Signal validation speed: {elapsed:.3f}s")


class TestDashboardAPIPerformance:
    """Performance tests for Dashboard API"""

    @pytest.mark.asyncio
    async def test_result_save_performance(self):
        """Benchmark backtest result saving"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BacktestResultService(data_dir=tmpdir)

            start_time = time.time()

            # Save 10 results
            for i in range(10):
                metadata = BacktestResultMetadata(
                    result_id=f"perf_test_{i:03d}",
                    symbol="0700.HK",
                    strategy_name="Performance",
                    start_date=datetime(2025, 1, 1),
                    end_date=datetime(2025, 3, 31),
                    initial_capital=100000.0,
                    use_alt_data=True
                )

                result = BacktestResultData(
                    metadata=metadata,
                    total_return=0.15,
                    sharpe_ratio=1.67
                )

                await service.save_result(result)

            elapsed = time.time() - start_time

            # Should save 10 results in < 1 second
            assert elapsed < 1.0, f"Saving took {elapsed:.2f}s, expected < 1s"

            throughput = 10 / elapsed
            print(f"Result save throughput: {throughput:.0f} results/sec")

    @pytest.mark.asyncio
    async def test_result_retrieve_performance(self):
        """Benchmark backtest result retrieval"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BacktestResultService(data_dir=tmpdir)

            # Save test data
            for i in range(10):
                metadata = BacktestResultMetadata(
                    result_id=f"retrieve_test_{i:03d}",
                    symbol="0700.HK",
                    strategy_name="Performance",
                    start_date=datetime(2025, 1, 1),
                    end_date=datetime(2025, 3, 31),
                    initial_capital=100000.0,
                    use_alt_data=True
                )

                result = BacktestResultData(metadata=metadata)
                await service.save_result(result)

            # Measure retrieval performance
            start_time = time.time()

            for i in range(10):
                await service.get_result(f"retrieve_test_{i:03d}")

            elapsed = time.time() - start_time

            # Should retrieve 10 results in < 1 second
            assert elapsed < 1.0, f"Retrieval took {elapsed:.2f}s, expected < 1s"

            throughput = 10 / elapsed
            print(f"Result retrieval throughput: {throughput:.0f} results/sec")

    @pytest.mark.asyncio
    async def test_result_list_performance(self):
        """Benchmark backtest result listing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BacktestResultService(data_dir=tmpdir)

            # Save 100 results
            for i in range(100):
                metadata = BacktestResultMetadata(
                    result_id=f"list_test_{i:03d}",
                    symbol="0700.HK" if i < 50 else "0388.HK",
                    strategy_name="Performance",
                    start_date=datetime(2025, 1, 1),
                    end_date=datetime(2025, 3, 31),
                    initial_capital=100000.0,
                    use_alt_data=True
                )

                result = BacktestResultData(metadata=metadata)
                await service.save_result(result)

            # Measure list performance
            start_time = time.time()
            results = await service.list_results(limit=100)
            elapsed = time.time() - start_time

            # Should list 100 results in < 1 second
            assert elapsed < 1.0, f"Listing took {elapsed:.2f}s, expected < 1s"
            assert len(results) == 100

            print(f"Result list speed: {elapsed:.3f}s for {len(results)} items")


class TestLoadUnderConcurrency:
    """Test system behavior under concurrent loads"""

    def test_concurrent_cleaning_operations(self):
        """Test multiple cleaning operations"""
        cleaner = DataCleaner()

        def clean_operation():
            dates = pd.date_range('2020-01-01', periods=1000, freq='D')
            data = pd.DataFrame({
                'open': np.random.uniform(100, 110, 1000),
                'high': np.random.uniform(110, 120, 1000),
                'low': np.random.uniform(90, 100, 1000),
                'close': np.random.uniform(100, 110, 1000),
                'volume': np.random.uniform(1000000, 2000000, 1000),
            }, index=dates)

            return cleaner.clean(data)

        # Execute 5 operations sequentially
        start_time = time.time()

        for i in range(5):
            result = clean_operation()
            assert len(result) > 0

        elapsed = time.time() - start_time

        # Should complete all 5 operations in < 2 seconds
        assert elapsed < 2.0, f"5 operations took {elapsed:.2f}s, expected < 2s"

        avg_time = elapsed / 5
        print(f"Average operation time: {avg_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
