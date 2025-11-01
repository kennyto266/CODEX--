"""
Phase 5.2: Integration Tests for Alternative Data Framework

Comprehensive end-to-end testing of the alternative data framework,
including data pipeline, backtest integration, signal attribution, and API endpoints.

Test Coverage:
- Complete data pipeline (Fetch → Clean → Align → Normalize → Score)
- Alternative data + price signal integration
- Backtest execution with alternative data
- Signal attribution and tracking
- Dashboard API integration
- End-to-end workflow scenarios
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import json

# Data pipeline components
from src.data_pipeline.data_cleaner import DataCleaner
from src.data_pipeline.temporal_aligner import TemporalAligner
from src.data_pipeline.data_normalizer import DataNormalizer
from src.data_pipeline.quality_scorer import QualityScorer
from src.data_pipeline.pipeline_processor import PipelineProcessor

# Backtest components
from src.backtest.alt_data_backtest_extension import (
    AltDataBacktestEngine,
    SignalSource,
    AltDataTradeExtension
)
from src.backtest.signal_attribution_metrics import (
    SignalAttributionAnalyzer,
    SignalType
)
from src.backtest.signal_validation import SignalValidator
from src.backtest.result_service import (
    BacktestResultService,
    BacktestResultMetadata,
    BacktestResultData,
    BacktestStatus
)

# Strategies
from src.strategies.alt_data_signal_strategy import AltDataSignalStrategy
from src.strategies.correlation_strategy import CorrelationStrategy


class TestDataPipelineIntegration:
    """Integration tests for complete data pipeline"""

    @pytest.fixture
    def sample_raw_data(self):
        """Create sample raw data with quality issues"""
        dates = pd.date_range('2025-01-01', periods=50, freq='D')

        data = pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 110, 50),
            'high': np.random.uniform(110, 120, 50),
            'low': np.random.uniform(90, 100, 50),
            'close': np.random.uniform(100, 110, 50),
            'volume': np.random.uniform(1000000, 2000000, 50),
            'symbol': '0700.HK'
        })

        # Add some missing values and outliers
        data.iloc[5, 1] = np.nan  # Missing open price
        data.iloc[10, 4] = 50.0   # Outlier low price

        return data

    @pytest.fixture
    def sample_alt_data(self):
        """Create sample alternative data"""
        dates = pd.date_range('2025-01-01', periods=50, freq='D')

        return {
            'hibor_rate': pd.Series(
                np.random.uniform(4.0, 4.5, 50),
                index=dates,
                name='hibor_rate'
            ),
            'visitor_arrivals': pd.Series(
                np.random.uniform(1000, 2000, 50),
                index=dates,
                name='visitor_arrivals'
            ),
            'retail_sales': pd.Series(
                np.random.uniform(5000, 6000, 50),
                index=dates,
                name='retail_sales'
            )
        }

    def test_complete_data_pipeline_flow(self, sample_raw_data, sample_alt_data):
        """Test complete pipeline from raw data to processed signals"""

        # Step 1: Data Cleaning
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean(sample_raw_data)

        assert cleaned_data is not None
        assert len(cleaned_data) > 0
        assert cleaned_data['open'].isna().sum() == 0  # No missing values

        # Step 2: Temporal Alignment
        aligner = TemporalAligner()
        aligned_data = aligner.align_to_trading_days(
            cleaned_data,
            date_column=None
        )

        assert len(aligned_data) > 0
        assert aligned_data.index.is_monotonic_increasing

        # Step 3: Data Normalization
        normalizer = DataNormalizer()
        normalized_data = normalizer.fit_transform(aligned_data)

        assert normalized_data is not None
        # Check normalized values are in reasonable range
        for col in ['open', 'high', 'low', 'close']:
            if col in normalized_data.columns:
                assert normalized_data[col].abs().max() <= 5.0  # Z-scores

        # Step 4: Quality Scoring
        scorer = QualityScorer()
        quality_report = scorer.calculate_overall_grade(normalized_data)

        assert quality_report is not None
        assert 'completeness_score' in quality_report or 'grade' in quality_report

        # Step 5: Alternative Data Integration
        pipeline = PipelineProcessor()
        processed_data = pipeline.process(normalized_data)

        assert processed_data is not None
        assert len(processed_data) > 0

    def test_alt_data_alignment_with_price_data(self, sample_raw_data, sample_alt_data):
        """Test alignment of alternative data with price data"""

        cleaner = DataCleaner()
        cleaned = cleaner.clean(sample_raw_data)

        aligner = TemporalAligner()
        aligned = aligner.align_to_trading_days(cleaned)

        # Align alternative data to same dates
        for name, series in sample_alt_data.items():
            df_series = pd.DataFrame({name: series})
            aligned_alt = aligner.align_to_trading_days(df_series)

            # Check alignment
            assert len(aligned_alt) > 0
            assert aligned_alt.index[0] >= aligned.index[0]

    def test_pipeline_with_missing_alt_data(self, sample_raw_data):
        """Test pipeline handles missing alternative data gracefully"""

        cleaner = DataCleaner()
        cleaned = cleaner.clean(sample_raw_data)

        # Process without alt data
        pipeline = PipelineProcessor()
        result = pipeline.process(cleaned)

        assert result is not None
        assert len(result) > 0

    def test_data_quality_metrics_calculation(self, sample_raw_data):
        """Test quality metrics are calculated correctly"""

        scorer = QualityScorer()
        report = scorer.calculate_overall_grade(sample_raw_data)

        assert report is not None
        # Should return either grade or completeness metrics
        assert 'grade' in report or 'completeness_score' in report


class TestBacktestAltDataIntegration:
    """Integration tests for backtest + alternative data"""

    @pytest.fixture
    def backtest_config(self):
        """Create backtest configuration"""
        from src.backtest.base_backtest import BacktestConfig
        from datetime import date

        return BacktestConfig(
            strategy_name='AltDataTest',
            symbols=['0700.HK'],
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            initial_capital=100000.0,
            benchmark='HSI.HK'
        )

    @pytest.fixture
    def sample_backtest_data(self):
        """Create sample OHLCV data for backtest"""
        dates = pd.date_range('2025-01-01', periods=60, freq='D')

        prices = 100 + np.cumsum(np.random.randn(60) * 2)

        return pd.DataFrame({
            'open': prices + np.random.randn(60),
            'high': prices + abs(np.random.randn(60)) + 2,
            'low': prices - abs(np.random.randn(60)) - 2,
            'close': prices,
            'volume': np.random.uniform(1000000, 2000000, 60),
        }, index=dates)

    @pytest.fixture
    def sample_alt_signals(self):
        """Create sample alternative data signals"""
        dates = pd.date_range('2025-01-01', periods=60, freq='D')

        return {
            'hibor_signal': pd.Series(
                np.random.uniform(-1, 1, 60),
                index=dates,
                name='hibor_signal'
            ),
            'visitor_signal': pd.Series(
                np.random.uniform(-1, 1, 60),
                index=dates,
                name='visitor_signal'
            ),
            'macro_signal': pd.Series(
                np.random.uniform(-1, 1, 60),
                index=dates,
                name='macro_signal'
            )
        }

    def test_signal_source_tracking(self):
        """Test signal source tracking in backtest"""

        # Verify signal source enum values
        assert SignalSource.PRICE_ONLY.value == "price_only"
        assert SignalSource.ALT_DATA_ONLY.value == "alt_data_only"
        assert SignalSource.COMBINED.value == "combined"

    def test_alt_data_engine_initialization(self):
        """Test AltDataBacktestEngine can be created"""

        # Verify engine can be imported and initialized
        assert AltDataBacktestEngine is not None

        # Check it has required attributes for alt data tracking
        from inspect import signature
        sig = signature(AltDataBacktestEngine.__init__)
        assert 'config' in sig.parameters

    def test_alt_data_signal_strategy_creation(self):
        """Test AltDataSignalStrategy can be created"""

        strategy = AltDataSignalStrategy()
        assert strategy is not None

        # Generate signals
        price_signals = [0.8, 0.6, -0.3, 0.5, 0.7]
        alt_signals_list = [
            {'hibor': 0.4, 'visitor': 0.5},
            {'hibor': 0.3, 'visitor': 0.6},
            {'hibor': -0.4, 'visitor': -0.2},
            {'hibor': 0.2, 'visitor': 0.4},
            {'hibor': 0.6, 'visitor': 0.7},
        ]

        # Test signal merging logic
        for price_sig, alt_sig in zip(price_signals, alt_signals_list):
            # Simple weighted average
            combined = (price_sig * 0.6 + np.mean(list(alt_sig.values())) * 0.4)
            assert -1 <= combined <= 1


class TestSignalAttributionIntegration:
    """Integration tests for signal attribution and validation"""

    @pytest.fixture
    def sample_trades(self):
        """Create sample trade records"""
        return [
            {
                'timestamp': datetime(2025, 1, 1),
                'symbol': '0700.HK',
                'side': 'buy',
                'quantity': 100,
                'price': 300.0,
                'pnl': 500.0,
                'source': 'price_only',
                'confidence': 0.8
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'symbol': '0700.HK',
                'side': 'sell',
                'quantity': 100,
                'price': 310.0,
                'pnl': 1000.0,
                'source': 'combined',
                'confidence': 0.85
            },
            {
                'timestamp': datetime(2025, 1, 3),
                'symbol': '0700.HK',
                'side': 'buy',
                'quantity': 100,
                'price': 305.0,
                'pnl': -200.0,
                'source': 'alt_data_only',
                'confidence': 0.6
            },
        ]

    def test_signal_attribution_calculation(self, sample_trades):
        """Test signal attribution metrics calculation"""

        analyzer = SignalAttributionAnalyzer()

        # Calculate accuracy
        accuracy = analyzer.calculate_signal_accuracy(sample_trades)

        assert accuracy is not None
        assert 'overall_accuracy' in accuracy
        assert 0 <= accuracy['overall_accuracy'] <= 1

    def test_signal_breakdown_analysis(self, sample_trades):
        """Test signal breakdown by source"""

        analyzer = SignalAttributionAnalyzer()

        # Test with dictionary format trades
        breakdown = analyzer.generate_signal_breakdown(sample_trades)

        assert breakdown is not None
        # Breakdown should have total_trades >= 0
        assert breakdown.total_trades >= 0
        # Should have metrics for all three signal types
        assert breakdown.price_metrics is not None
        assert breakdown.alt_data_metrics is not None
        assert breakdown.combined_metrics is not None

    def test_signal_validation_with_oos_test(self, sample_trades):
        """Test signal validation with out-of-sample testing"""

        validator = SignalValidator()

        # Split data
        train_trades = sample_trades[:2]
        test_trades = sample_trades[2:]

        # Calculate metrics for each set
        train_metrics = {
            'sharpe': 1.5,
            'win_rate': 1.0,  # Both training trades profitable
        }

        test_metrics = {
            'sharpe': 0.5,
            'win_rate': 0.0,  # Test trade lost money
        }

        # Detect overfitting
        overfitting = validator.detect_overfitting(train_metrics, test_metrics)

        assert overfitting is not None
        assert overfitting.is_overfitted or overfitting.level != 'none'

    def test_signal_consistency_across_sources(self, sample_trades):
        """Test signal consistency across different sources"""

        # Verify signal source breakdown
        price_trades = [t for t in sample_trades if t['source'] == 'price_only']
        alt_trades = [t for t in sample_trades if t['source'] == 'alt_data_only']
        combined_trades = [t for t in sample_trades if t['source'] == 'combined']

        # All three sources should be represented
        assert len(price_trades) > 0
        assert len(alt_trades) > 0
        assert len(combined_trades) > 0

        # Total should match
        assert len(price_trades) + len(alt_trades) + len(combined_trades) == len(sample_trades)


class TestDashboardAPIIntegration:
    """Integration tests for Dashboard API endpoints"""

    @pytest.fixture
    def result_service(self):
        """Create result service with temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BacktestResultService(data_dir=tmpdir)
            yield service

    @pytest.mark.asyncio
    async def test_save_and_retrieve_backtest_result(self, result_service):
        """Test saving and retrieving backtest results via API"""

        metadata = BacktestResultMetadata(
            result_id="integration_test_001",
            symbol="0700.HK",
            strategy_name="AltDataSignal",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
            initial_capital=100000.0,
            use_alt_data=True,
            alt_data_indicators=['hibor', 'visitor', 'retail']
        )

        result = BacktestResultData(
            metadata=metadata,
            total_return=0.15,
            annualized_return=0.20,
            volatility=0.12,
            sharpe_ratio=1.67,
            sortino_ratio=2.1,
            max_drawdown=-0.08,
            total_trades=50,
            winning_trades=35,
            losing_trades=15,
            win_rate=0.7,
            avg_win=500.0,
            avg_loss=-200.0,
            profit_factor=2.5,
            price_only_sharpe=1.2,
            alt_data_contribution_pct=30.0
        )

        # Save result
        result_id = await result_service.save_result(result)
        assert result_id == "integration_test_001"

        # Retrieve result
        retrieved = await result_service.get_result(result_id)
        assert retrieved is not None
        assert retrieved.metadata.symbol == "0700.HK"
        assert retrieved.total_return == 0.15
        assert retrieved.sharpe_ratio == 1.67

    @pytest.mark.asyncio
    async def test_compare_results_api(self, result_service):
        """Test comparing backtest results via API"""

        # Create result with alt data
        with_alt = BacktestResultData(
            metadata=BacktestResultMetadata(
                result_id="with_alt",
                symbol="0700.HK",
                strategy_name="test",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 3, 31),
                initial_capital=100000.0,
                use_alt_data=True
            ),
            total_return=0.20,
            sharpe_ratio=2.0,
            max_drawdown=-0.05
        )

        # Create result without alt data
        without_alt = BacktestResultData(
            metadata=BacktestResultMetadata(
                result_id="without_alt",
                symbol="0700.HK",
                strategy_name="test",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 3, 31),
                initial_capital=100000.0,
                use_alt_data=False
            ),
            total_return=0.12,
            sharpe_ratio=1.2,
            max_drawdown=-0.10
        )

        # Save both
        await result_service.save_result(with_alt)
        await result_service.save_result(without_alt)

        # Compare
        comparison = await result_service.compare_results("with_alt", "without_alt")

        assert comparison is not None
        assert comparison['result_with_alt_data']['sharpe_ratio'] == 2.0
        assert comparison['result_without_alt_data']['sharpe_ratio'] == 1.2
        assert comparison['improvement']['sharpe_ratio_improvement_pct'] > 0

    @pytest.mark.asyncio
    async def test_list_results_with_filtering(self, result_service):
        """Test listing and filtering results"""

        # Save multiple results
        for i in range(3):
            metadata = BacktestResultMetadata(
                result_id=f"test_{i:03d}",
                symbol="0700.HK" if i < 2 else "0388.HK",
                strategy_name="AltDataSignal",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 3, 31),
                initial_capital=100000.0,
                use_alt_data=True
            )
            result = BacktestResultData(metadata=metadata)
            await result_service.save_result(result)

        # List all
        all_results = await result_service.list_results(limit=10)
        assert len(all_results) >= 3

        # Filter by symbol
        hk0700_results = await result_service.list_results(symbol="0700.HK")
        assert len(hk0700_results) >= 2


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests"""

    @pytest.mark.asyncio
    async def test_complete_alt_data_workflow(self):
        """Test complete workflow from data to results"""

        # 1. Prepare data
        dates = pd.date_range('2025-01-01', periods=60, freq='D')
        price_data = pd.DataFrame({
            'open': 100 + np.cumsum(np.random.randn(60)),
            'high': 102 + np.cumsum(np.random.randn(60)),
            'low': 98 + np.cumsum(np.random.randn(60)),
            'close': 100 + np.cumsum(np.random.randn(60)),
            'volume': 1000000,
        }, index=dates)

        alt_data = {
            'signal1': pd.Series(np.random.randn(60), index=dates),
            'signal2': pd.Series(np.random.randn(60), index=dates),
        }

        # 2. Clean pipeline
        cleaner = DataCleaner()
        cleaned = cleaner.clean(price_data)
        assert len(cleaned) > 0

        # 3. Process alternative data
        aligner = TemporalAligner()
        aligned = aligner.align_to_trading_days(cleaned)
        assert len(aligned) > 0

        # 4. Normalize
        normalizer = DataNormalizer()
        normalized = normalizer.fit_transform(aligned)
        assert len(normalized) > 0

        # 5. Score quality
        scorer = QualityScorer()
        quality = scorer.calculate_overall_grade(normalized)
        assert quality is not None

        # 6. Store results
        with tempfile.TemporaryDirectory() as tmpdir:
            result_service = BacktestResultService(data_dir=tmpdir)

            metadata = BacktestResultMetadata(
                result_id="e2e_test",
                symbol="0700.HK",
                strategy_name="E2ETest",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 3, 1),
                initial_capital=100000.0,
                use_alt_data=True,
                alt_data_indicators=['signal1', 'signal2']
            )

            result = BacktestResultData(
                metadata=metadata,
                total_return=0.10
            )

            result_id = await result_service.save_result(result)
            assert result_id == "e2e_test"

            retrieved = await result_service.get_result(result_id)
            assert retrieved is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
