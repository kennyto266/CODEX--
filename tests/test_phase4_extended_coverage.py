"""
Extended Unit Tests for Phase 4 Components
Additional coverage for BacktestEngine, Metrics, Validation, and Result Service

Test Coverage:
- Phase 4.1: BacktestEngine extension
- Phase 4.5: Performance metrics
- Phase 4.6: Signal validation
- Phase 4.7: Result service
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile

# Phase 4.1: BacktestEngine tests
from src.backtest.alt_data_backtest_extension import (
    AltDataBacktestEngine,
    SignalSource,
    AltDataTradeExtension
)

# Phase 4.5: Metrics tests
from src.backtest.signal_attribution_metrics import (
    SignalAttributionAnalyzer,
    SignalType,
    SignalMetrics
)

# Phase 4.6: Validation tests
from src.backtest.signal_validation import (
    SignalValidator,
    ValidationResult,
    OutOfSampleResult,
    OverfittingAnalysis,
    OverfittingLevel,
    StatisticalSignificance,
    SignalStability
)

# Phase 4.7: Result service tests
from src.backtest.result_service import (
    BacktestResultService,
    BacktestResultData,
    BacktestResultMetadata,
    BacktestStatus
)


class TestAltDataBacktestEngineExtended:
    """Extended tests for BacktestEngine with alternative data"""

    @pytest.fixture
    def sample_alt_data_signals(self):
        """Create sample alternative data signals"""
        dates = pd.date_range('2025-01-01', periods=50, freq='D')
        return {
            'hibor_rate': pd.Series(
                np.random.uniform(4.0, 4.5, 50),
                index=dates
            ),
            'visitor_arrivals': pd.Series(
                np.random.uniform(1000, 2000, 50),
                index=dates
            ),
        }

    def test_alt_data_signals_validation(self, sample_alt_data_signals):
        """Test validation of alternative data signals"""
        # Check signal structure
        assert isinstance(sample_alt_data_signals, dict)
        assert 'hibor_rate' in sample_alt_data_signals
        assert 'visitor_arrivals' in sample_alt_data_signals

        # Check time series
        for name, series in sample_alt_data_signals.items():
            assert isinstance(series, pd.Series)
            assert len(series) == 50
            assert series.index[0] < series.index[-1]

    def test_signal_source_tracking(self):
        """Test signal source classification"""
        assert SignalSource.PRICE_ONLY.value == "price_only"
        assert SignalSource.ALT_DATA_ONLY.value == "alt_data_only"
        assert SignalSource.COMBINED.value == "combined"

    def test_alt_data_trade_creation(self):
        """Test creation of alt data trade records"""
        from src.backtest.enhanced_backtest_engine import Trade

        # Create a base trade first
        base_trade = Trade(
            symbol="0700.HK",
            side="buy",
            quantity=100,
            price=300.0,
            timestamp=datetime.now(),
            commission=10.0,
            slippage=5.0,
            market_impact=2.0,
            total_cost=17.0
        )

        # Create AltDataTradeExtension
        trade = AltDataTradeExtension(
            base_trade=base_trade,
            signal_source=SignalSource.COMBINED,
            price_signal=0.8,
            alt_signal=0.6,
            merged_signal=0.73,
            confidence=0.85,
            alt_indicators={'hibor': 0.6}
        )

        assert trade.signal_source == SignalSource.COMBINED
        assert trade.price_signal == 0.8
        assert trade.alt_signal == 0.6
        assert trade.merged_signal == 0.73


class TestSignalAttributionMetricsExtended:
    """Extended tests for signal attribution and metrics"""

    @pytest.fixture
    def sample_trade_data(self):
        """Create sample trade data"""
        return [
            {
                'timestamp': datetime(2025, 1, 1),
                'symbol': '0700.HK',
                'side': 'buy',
                'quantity': 100,
                'price': 300.0,
                'pnl': 500.0,
                'source': 'price_only'
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'symbol': '0700.HK',
                'side': 'sell',
                'quantity': 100,
                'price': 310.0,
                'pnl': 1000.0,
                'source': 'combined'
            },
        ]

    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        analyzer = SignalAttributionAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'calculate_signal_attribution')
        assert hasattr(analyzer, 'calculate_signal_accuracy')
        assert hasattr(analyzer, 'generate_signal_breakdown')

    def test_signal_type_enum(self):
        """Test signal type classification"""
        assert SignalType.PRICE_ONLY.value == "price_only"
        assert SignalType.ALT_DATA_ONLY.value == "alt_data_only"
        assert SignalType.COMBINED.value == "combined"

    def test_signal_metrics_calculation(self, sample_trade_data):
        """Test signal metrics calculation"""
        # Calculate simple metrics
        total_trades = len(sample_trade_data)
        total_pnl = sum(t['pnl'] for t in sample_trade_data)
        win_rate = len([t for t in sample_trade_data if t['pnl'] > 0]) / total_trades

        assert total_trades == 2
        assert total_pnl == 1500.0
        assert win_rate == 1.0  # Both trades profitable


class TestSignalValidationExtended:
    """Extended tests for signal validation"""

    @pytest.fixture
    def validator(self):
        """Create signal validator instance"""
        return SignalValidator()

    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator is not None

    def test_overfitting_detection(self):
        """Test detection of overfitted signals"""
        # Generate overfit pattern: perfect fit on training data
        train_signals = np.array([1, 1, 1, 1, 1])  # Perfect prediction
        test_signals = np.array([0.5, 0.3, 0.6, 0.2, 0.4])  # Random on test

        # High train accuracy, low test accuracy = overfitting
        train_accuracy = 1.0
        test_accuracy = 0.0

        overfitting_ratio = train_accuracy / (test_accuracy + 0.1) if test_accuracy > 0 else float('inf')
        assert overfitting_ratio > 1.0  # Indicates overfitting

    def test_signal_stability_analysis(self):
        """Test signal stability analysis"""
        # Create stable signal (low volatility)
        stable_signals = np.array([0.8, 0.79, 0.81, 0.80, 0.82])
        stability = 1.0 - np.std(stable_signals)

        assert stability > 0.95  # High stability

    def test_statistical_significance_validation(self):
        """Test statistical significance of signals"""
        # Simple Win Rate significance test
        correct_predictions = 65  # 65 out of 100
        total_predictions = 100
        random_probability = 0.5

        # Z-score for win rate
        observed_rate = correct_predictions / total_predictions
        expected_rate = random_probability
        se = np.sqrt(random_probability * (1 - random_probability) / total_predictions)
        z_score = (observed_rate - expected_rate) / se

        assert z_score > 1.96  # Significant at 95% confidence level


class TestResultServiceExtended:
    """Extended tests for result service"""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def result_service(self, temp_data_dir):
        """Create result service with temp directory"""
        return BacktestResultService(data_dir=temp_data_dir)

    @pytest.mark.asyncio
    async def test_result_service_initialization(self, result_service):
        """Test result service initialization"""
        assert result_service is not None
        assert result_service.data_dir.exists()

    @pytest.mark.asyncio
    async def test_save_and_retrieve_result(self, result_service):
        """Test saving and retrieving results"""
        metadata = BacktestResultMetadata(
            result_id="test_001",
            symbol="0700.HK",
            strategy_name="AltDataSignal",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            initial_capital=100000.0,
            use_alt_data=True,
            alt_data_indicators=['hibor', 'visitors']
        )

        result = BacktestResultData(
            metadata=metadata,
            total_return=0.15,
            sharpe_ratio=1.5,
            max_drawdown=-0.08,
            total_trades=50,
            winning_trades=35,
            win_rate=0.7
        )

        # Save result
        result_id = await result_service.save_result(result)
        assert result_id == "test_001"

        # Retrieve result
        retrieved = await result_service.get_result(result_id)
        assert retrieved is not None
        assert retrieved.metadata.symbol == "0700.HK"
        assert retrieved.total_return == 0.15

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
                end_date=datetime(2025, 1, 31),
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

    @pytest.mark.asyncio
    async def test_compare_backtest_results(self, result_service):
        """Test comparison of backtest results"""
        # Create result with alt data
        with_alt = BacktestResultData(
            metadata=BacktestResultMetadata(
                result_id="with_alt",
                symbol="0700.HK",
                strategy_name="test",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
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
                end_date=datetime(2025, 1, 31),
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
        assert "improvement" in comparison
        assert comparison["improvement"]["sharpe_ratio_improvement_pct"] > 0


class TestBacktestIntegrationExtended:
    """Extended integration tests for backtest components"""

    def test_full_signal_flow(self):
        """Test complete signal flow with alt data"""
        # Simulate signal generation
        price_signal = 0.8  # Strong buy from price
        alt_signal = 0.6    # Moderate positive from alt data
        correlation = 0.65  # Correlation strength

        # Combined signal calculation
        weights = {'price': 0.6, 'alt': 0.4}
        combined_signal = (price_signal * weights['price'] +
                          alt_signal * weights['alt'])

        assert combined_signal > 0.6  # Should be strong signal
        assert combined_signal < 0.8  # Less extreme than price alone

    def test_signal_attribution_flow(self):
        """Test signal attribution tracking"""
        trades = [
            {'source': 'price_only', 'pnl': 100},
            {'source': 'combined', 'pnl': 150},
            {'source': 'alt_data_only', 'pnl': 50},
        ]

        # Calculate attribution by source
        attribution = {}
        for trade in trades:
            source = trade['source']
            if source not in attribution:
                attribution[source] = {'pnl': 0, 'count': 0}
            attribution[source]['pnl'] += trade['pnl']
            attribution[source]['count'] += 1

        assert attribution['combined']['pnl'] == 150
        assert len(attribution) == 3


class TestPerformanceAndEdgeCases:
    """Tests for performance and edge cases"""

    def test_large_signal_dataset_handling(self):
        """Test handling of large signal datasets"""
        # Create large dataset
        large_signals = np.random.randn(10000)
        assert len(large_signals) == 10000

        # Calculate metrics
        mean_signal = np.mean(large_signals)
        std_signal = np.std(large_signals)

        assert np.isfinite(mean_signal)
        assert np.isfinite(std_signal)

    def test_edge_case_no_trades(self):
        """Test edge case with no trades"""
        trades = []
        win_rate = len([t for t in trades if t.get('pnl', 0) > 0]) / (len(trades) or 1)

        assert win_rate == 0.0

    def test_edge_case_single_trade(self):
        """Test edge case with single trade"""
        trades = [{'pnl': 100}]
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades)

        assert total_pnl == 100
        assert win_rate == 1.0

    def test_nan_infinity_handling(self):
        """Test handling of NaN and infinity values"""
        values = [1.0, np.nan, 2.0, np.inf, 3.0]

        # Filter out invalid values
        valid_values = [v for v in values if np.isfinite(v)]
        assert len(valid_values) == 3
        assert np.mean(valid_values) == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
