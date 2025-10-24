"""
Tests for Parameter Optimizer Module

Test Coverage:
- Parameter grid generation
- Grid search functionality
- Parallel optimization
- Result caching and deduplication
- Optimization reporting
- Progress tracking
"""

import pytest
import numpy as np
import pandas as pd
import asyncio
from unittest.mock import Mock, patch

from src.backtest.parameter_optimizer import (
    ParameterGrid,
    ParameterOptimizer,
    GridSearchOptimizer,
    OptimizationResult,
    OptimizationReport,
    OptimizationProgressCallback,
)


class TestParameterGrid:
    """Test parameter grid generation."""

    def test_simple_grid(self):
        """Test generating simple parameter grid."""
        grid = ParameterGrid({
            'period': [10, 20, 30],
            'threshold': [0.5, 1.0],
        })

        combinations = grid.generate_combinations()

        assert len(combinations) == 6  # 3 * 2
        assert combinations[0] == {'period': 10, 'threshold': 0.5}
        assert combinations[-1] == {'period': 30, 'threshold': 1.0}

    def test_single_parameter(self):
        """Test grid with single parameter."""
        grid = ParameterGrid({
            'period': [10, 20, 30, 40],
        })

        combinations = grid.generate_combinations()

        assert len(combinations) == 4
        assert combinations[1] == {'period': 20}

    def test_large_grid(self):
        """Test large parameter grid."""
        grid = ParameterGrid({
            'period': list(range(10, 50)),  # 40 values (10-49)
            'threshold': [0.5, 1.0, 1.5],    # 3 values
            'atr_period': [14, 21],           # 2 values
        })

        size = grid.get_grid_size()
        assert size == 40 * 3 * 2  # 240

        combinations = grid.generate_combinations()
        assert len(combinations) == 240

    def test_empty_grid(self):
        """Test empty grid."""
        grid = ParameterGrid({})

        combinations = grid.generate_combinations()
        # Empty product creates one empty dict combination
        assert len(combinations) == 1
        assert combinations[0] == {}

    def test_grid_size(self):
        """Test grid size calculation."""
        grid = ParameterGrid({
            'a': [1, 2, 3],
            'b': [10, 20],
        })

        assert grid.get_grid_size() == 6


class TestOptimizationResult:
    """Test optimization result handling."""

    def test_result_creation(self):
        """Test creating optimization result."""
        result = OptimizationResult(
            parameters={'period': 20, 'threshold': 1.0},
            return_pct=0.15,
            sharpe_ratio=1.5,
            max_drawdown=-0.2,
            win_rate=0.55,
            profit_factor=1.8,
            total_trades=50,
            execution_time=0.1,
        )

        assert result.return_pct == 0.15
        assert result.sharpe_ratio == 1.5

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = OptimizationResult(
            parameters={'period': 20},
            return_pct=0.1,
            sharpe_ratio=1.0,
            max_drawdown=-0.2,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            execution_time=0.05,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['return_pct'] == 0.1
        assert result_dict['parameters'] == {'period': 20}

    def test_result_to_series(self):
        """Test converting result to pandas Series."""
        result = OptimizationResult(
            parameters={'period': 20},
            return_pct=0.1,
            sharpe_ratio=1.0,
            max_drawdown=-0.2,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            execution_time=0.05,
        )

        series = result.to_series()

        assert isinstance(series, pd.Series)
        assert series['return_pct'] == 0.1


class TestOptimizationReport:
    """Test optimization report generation."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results."""
        results = []
        for i in range(5):
            result = OptimizationResult(
                parameters={'period': 10 + i * 5},
                return_pct=0.1 + i * 0.05,
                sharpe_ratio=1.0 + i * 0.2,
                max_drawdown=-0.2 - i * 0.05,
                win_rate=0.5 + i * 0.05,
                profit_factor=1.5 + i * 0.1,
                total_trades=30 + i * 10,
                execution_time=0.05,
            )
            results.append(result)

        return results

    def test_report_creation(self, sample_results):
        """Test creating optimization report."""
        report = OptimizationReport(
            total_combinations=5,
            completed_combinations=5,
            execution_time=1.0,
            best_result=max(sample_results, key=lambda r: r.return_pct),
            worst_result=min(sample_results, key=lambda r: r.return_pct),
            average_return=np.mean([r.return_pct for r in sample_results]),
            results=sample_results,
        )

        assert report.total_combinations == 5
        assert report.completed_combinations == 5
        assert report.best_result.return_pct == max(r.return_pct for r in sample_results)

    def test_get_top_results(self, sample_results):
        """Test getting top results."""
        report = OptimizationReport(
            total_combinations=5,
            completed_combinations=5,
            execution_time=1.0,
            best_result=max(sample_results, key=lambda r: r.return_pct),
            worst_result=min(sample_results, key=lambda r: r.return_pct),
            average_return=np.mean([r.return_pct for r in sample_results]),
            results=sample_results,
        )

        top_3 = report.get_top_results(3)

        assert len(top_3) == 3
        assert top_3[0].return_pct >= top_3[1].return_pct >= top_3[2].return_pct

    def test_get_by_criteria(self, sample_results):
        """Test filtering results by criteria."""
        report = OptimizationReport(
            total_combinations=5,
            completed_combinations=5,
            execution_time=1.0,
            best_result=max(sample_results, key=lambda r: r.return_pct),
            worst_result=min(sample_results, key=lambda r: r.return_pct),
            average_return=np.mean([r.return_pct for r in sample_results]),
            results=sample_results,
        )

        criteria = {
            'sharpe_ratio': (1.2, float('inf')),  # Sharpe >= 1.2
            'return_pct': (0.15, float('inf')),   # Return >= 15%
        }

        filtered = report.get_by_criteria(criteria)

        assert len(filtered) > 0
        assert all(r.sharpe_ratio >= 1.2 for r in filtered)
        assert all(r.return_pct >= 0.15 for r in filtered)

    def test_report_to_dataframe(self, sample_results):
        """Test converting report to DataFrame."""
        report = OptimizationReport(
            total_combinations=5,
            completed_combinations=5,
            execution_time=1.0,
            best_result=max(sample_results, key=lambda r: r.return_pct),
            worst_result=min(sample_results, key=lambda r: r.return_pct),
            average_return=np.mean([r.return_pct for r in sample_results]),
            results=sample_results,
        )

        df = report.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'return_pct' in df.columns


class TestParameterOptimizer:
    """Test parameter optimizer functionality."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        async def dummy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        mock_engine = Mock()
        return ParameterOptimizer(dummy_strategy, mock_engine, max_workers=2)

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.strategy_func is not None
        assert optimizer.max_workers == 2
        assert optimizer.cache_enabled is True

    def test_cache_key_generation(self):
        """Test cache key generation."""
        params1 = {'period': 20, 'threshold': 1.0}
        params2 = {'threshold': 1.0, 'period': 20}

        key1 = ParameterOptimizer._get_cache_key(params1)
        key2 = ParameterOptimizer._get_cache_key(params2)

        # Should be same regardless of parameter order
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_optimize_single_combination(self, optimizer):
        """Test optimizing single parameter combination."""
        grid = ParameterGrid({'period': [20]})

        ohlcv = pd.DataFrame({
            'close': np.ones(100),
        })

        report = await optimizer.optimize(grid, ohlcv)

        assert report.completed_combinations == 1
        assert len(report.results) == 1

    @pytest.mark.asyncio
    async def test_optimize_multiple_combinations(self, optimizer):
        """Test optimizing multiple parameter combinations."""
        grid = ParameterGrid({
            'period': [10, 20, 30],
            'threshold': [0.5, 1.0],
        })

        ohlcv = pd.DataFrame({
            'close': np.ones(100),
        })

        report = await optimizer.optimize(grid, ohlcv)

        assert report.completed_combinations == 6
        assert len(report.results) == 6

    @pytest.mark.asyncio
    async def test_optimize_with_callback(self, optimizer):
        """Test optimization with progress callback."""
        grid = ParameterGrid({
            'period': [10, 20],
        })

        ohlcv = pd.DataFrame({
            'close': np.ones(100),
        })

        progress_calls = []

        async def progress_callback(current, total, result):
            progress_calls.append((current, total))

        report = await optimizer.optimize(grid, ohlcv, callback=progress_callback)

        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2)
        assert progress_calls[1] == (2, 2)

    @pytest.mark.asyncio
    async def test_cache_functionality(self, optimizer):
        """Test result caching."""
        grid = ParameterGrid({'period': [20]})

        ohlcv = pd.DataFrame({
            'close': np.ones(100),
        })

        # First run
        report1 = await optimizer.optimize(grid, ohlcv)

        stats_before = optimizer.get_cache_stats()
        initial_cache_size = stats_before['cache_size']

        # Second run (should hit cache)
        report2 = await optimizer.optimize(grid, ohlcv)

        stats_after = optimizer.get_cache_stats()

        assert stats_after['cache_hits'] > stats_before['cache_hits']

    @pytest.mark.asyncio
    async def test_parallel_optimization(self, optimizer):
        """Test parallel optimization."""
        grid = ParameterGrid({
            'period': [10, 20, 30],
        })

        ohlcv = pd.DataFrame({
            'close': np.ones(100),
        })

        report = await optimizer.optimize_parallel(grid, ohlcv)

        assert report.completed_combinations == 3
        assert len(report.results) == 3

    def test_clear_cache(self, optimizer):
        """Test clearing cache."""
        # Add something to cache
        key = "test_key"
        result = OptimizationResult(
            parameters={},
            return_pct=0.1,
            sharpe_ratio=1.0,
            max_drawdown=-0.2,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            execution_time=0.05,
        )
        optimizer.result_cache[key] = result

        assert len(optimizer.result_cache) > 0

        optimizer.clear_cache()

        assert len(optimizer.result_cache) == 0

    def test_cache_stats(self, optimizer):
        """Test cache statistics."""
        stats = optimizer.get_cache_stats()

        assert 'cache_size' in stats
        assert 'total_evaluations' in stats
        assert 'cache_hits' in stats
        assert 'hit_rate' in stats


class TestGridSearchOptimizer:
    """Test simplified grid search optimizer."""

    def test_grid_search_basic(self):
        """Test basic grid search."""
        mock_engine = Mock()
        optimizer = GridSearchOptimizer(mock_engine)

        async def dummy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        params = {
            'period': [10, 20],
            'threshold': [0.5, 1.0],
        }

        ohlcv = pd.DataFrame({
            'close': np.ones(50),
        })

        df = optimizer.search(dummy_strategy, params, ohlcv)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4  # 2 * 2

    def test_get_best_parameters(self):
        """Test getting best parameters."""
        mock_engine = Mock()
        optimizer = GridSearchOptimizer(mock_engine)

        async def dummy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        params = {
            'period': [10, 20, 30],
        }

        ohlcv = pd.DataFrame({
            'close': np.ones(50),
        })

        df = optimizer.search(dummy_strategy, params, ohlcv)

        best = optimizer.get_best_parameters(metric='return', top_n=1)

        assert len(best) == 1


class TestProgressCallback:
    """Test progress callback functionality."""

    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test progress tracking."""
        callback = OptimizationProgressCallback(total=10, print_interval=5)

        result = OptimizationResult(
            parameters={},
            return_pct=0.1,
            sharpe_ratio=1.0,
            max_drawdown=-0.2,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            execution_time=0.05,
        )

        await callback(5, 10, result)
        await callback(10, 10, result)

        progress = callback.get_progress()
        assert progress == 100.0

    @pytest.mark.asyncio
    async def test_progress_percentage(self):
        """Test progress percentage calculation."""
        callback = OptimizationProgressCallback(total=20, print_interval=10)

        result = OptimizationResult(
            parameters={},
            return_pct=0.1,
            sharpe_ratio=1.0,
            max_drawdown=-0.2,
            win_rate=0.5,
            profit_factor=1.5,
            total_trades=30,
            execution_time=0.05,
        )

        await callback(10, 20, result)
        assert callback.get_progress() == 50.0


class TestOptimizationIntegration:
    """Integration tests for optimization module."""

    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self):
        """Test complete optimization workflow."""
        async def ma_strategy(data, state):
            close = data['close'].values
            if len(close) < state.get('period', 20):
                return (np.array([0.0]), np.array([0.0]))

            period = state.get('period', 20)
            sma = pd.Series(close).rolling(period).mean().values

            entry = 1.0 if close[-1] > sma[-1] else 0.0
            return (np.array([entry]), np.array([0.0]))

        mock_engine = Mock()
        optimizer = ParameterOptimizer(ma_strategy, mock_engine)

        grid = ParameterGrid({
            'period': [10, 20, 30],
        })

        ohlcv = pd.DataFrame({
            'close': np.random.uniform(100, 120, 100),
        })

        report = await optimizer.optimize(grid, ohlcv)

        assert report.completed_combinations == 3
        assert report.best_result is not None
        assert report.worst_result is not None

    @pytest.mark.asyncio
    async def test_large_grid_optimization(self):
        """Test optimization with large parameter grid."""
        async def dummy_strategy(data, state):
            return (np.zeros(len(data)), np.zeros(len(data)))

        mock_engine = Mock()
        optimizer = ParameterOptimizer(dummy_strategy, mock_engine, max_workers=4)

        grid = ParameterGrid({
            'a': list(range(1, 6)),      # 5 values
            'b': list(range(10, 15)),    # 5 values
            'c': [0.5, 1.0, 1.5],        # 3 values
        })

        ohlcv = pd.DataFrame({
            'close': np.ones(50),
        })

        report = await optimizer.optimize(grid, ohlcv)

        assert report.completed_combinations == 5 * 5 * 3  # 75
