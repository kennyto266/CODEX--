"""
Parameter Manager and Risk Calculator Integration Tests

Tests for unified parameter management and risk calculation systems.

Run with: pytest tests/test_parameter_and_risk.py -v -m calculation_layer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.parameter_manager import (
    UnifiedParameterManager,
    ParameterBounds,
)
from src.core.risk_calculator import (
    UnifiedRiskCalculator,
    Position,
    PortfolioRisk,
)
from tests.fixtures import mock_ohlcv_data, MockStrategy


class TestParameterManager:
    """Test unified parameter manager."""

    @pytest.mark.calculation_layer
    def test_parameter_registration(self):
        """Test registering parameters."""
        manager = UnifiedParameterManager("TestStrategy")

        bounds = ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=50,
            default=20,
            description="Lookback period"
        )

        manager.register_parameter(bounds)

        assert "period" in manager.parameters
        assert manager.get_parameter("period") == 20

    @pytest.mark.calculation_layer
    def test_parameter_validation(self):
        """Test parameter value validation."""
        manager = UnifiedParameterManager()

        bounds = ParameterBounds(
            name="threshold",
            param_type="float",
            min_value=0.0,
            max_value=1.0,
            default=0.5,
        )

        manager.register_parameter(bounds)

        # Valid value
        assert manager.set_parameter("threshold", 0.7)

        # Invalid value (out of bounds)
        assert not manager.set_parameter("threshold", 1.5)

        # Invalid type
        assert not manager.set_parameter("threshold", "invalid")

    @pytest.mark.calculation_layer
    def test_parameter_bounds_types(self):
        """Test different parameter types."""
        manager = UnifiedParameterManager()

        # Int parameter
        manager.register_parameter(
            ParameterBounds("int_param", "int", 1, 10, default=5)
        )

        # Float parameter
        manager.register_parameter(
            ParameterBounds("float_param", "float", 0.0, 1.0, default=0.5)
        )

        # Bool parameter
        manager.register_parameter(
            ParameterBounds("bool_param", "bool", default=True)
        )

        # Choice parameter
        manager.register_parameter(
            ParameterBounds(
                "choice_param",
                "choice",
                choices=["A", "B", "C"],
                default="A"
            )
        )

        assert manager.set_parameter("int_param", 7)
        assert manager.set_parameter("float_param", 0.75)
        assert manager.set_parameter("bool_param", False)
        assert manager.set_parameter("choice_param", "B")

    @pytest.mark.calculation_layer
    def test_grid_search_optimization(self):
        """Test grid search parameter optimization."""
        manager = UnifiedParameterManager("GridTestStrategy")

        manager.register_parameter(
            ParameterBounds("window", "int", 10, 30, 10, step=10)
        )
        manager.register_parameter(
            ParameterBounds("threshold", "float", 0.1, 0.5, 0.3, step=0.2)
        )

        # Mock metrics function
        def mock_metrics_func(data, signals):
            # Return higher score for certain parameters
            window = manager.get_parameter("window")
            return {
                'sharpe_ratio': 1.0 if window == 20 else 0.5,
                'total_return': 0.1,
            }

        # Mock strategy
        strategy = MockStrategy()

        # Get mock data
        data = mock_ohlcv_data("0700.HK", num_days=50)

        # Run optimization
        result = manager.optimize_grid(
            strategy,
            data,
            mock_metrics_func,
        )

        assert result is not None
        assert "best_parameters" in result
        assert "best_score" in result

    @pytest.mark.calculation_layer
    def test_random_search_optimization(self):
        """Test random search parameter optimization."""
        manager = UnifiedParameterManager("RandomTestStrategy")

        manager.register_parameter(
            ParameterBounds("window", "int", 5, 50, default=20)
        )
        manager.register_parameter(
            ParameterBounds("threshold", "float", 0.0, 1.0, default=0.5)
        )

        def mock_metrics_func(data, signals):
            # Random-ish score
            return {'sharpe_ratio': np.random.uniform(0, 2)}

        strategy = MockStrategy()
        data = mock_ohlcv_data("0700.HK", num_days=50)

        result = manager.optimize_random(
            strategy,
            data,
            mock_metrics_func,
            n_iterations=10,
        )

        assert result is not None
        assert len(manager.optimization_history) == 10

    @pytest.mark.calculation_layer
    def test_parameter_persistence(self, tmp_path):
        """Test saving and loading parameters."""
        manager1 = UnifiedParameterManager("PersistenceTest")

        manager1.register_parameter(
            ParameterBounds("param1", "int", 1, 100, default=50)
        )
        manager1.register_parameter(
            ParameterBounds("param2", "float", 0.0, 1.0, default=0.5)
        )

        manager1.set_parameter("param1", 75)
        manager1.set_parameter("param2", 0.8)

        # Save
        filepath = tmp_path / "params.json"
        manager1.save_parameters(str(filepath))

        # Load into new manager
        manager2 = UnifiedParameterManager("PersistenceTest")
        manager2.register_parameter(
            ParameterBounds("param1", "int", 1, 100, default=50)
        )
        manager2.register_parameter(
            ParameterBounds("param2", "float", 0.0, 1.0, default=0.5)
        )

        assert manager2.load_parameters(str(filepath))
        assert manager2.get_parameter("param1") == 75
        assert manager2.get_parameter("param2") == 0.8

    @pytest.mark.calculation_layer
    def test_optimization_summary(self):
        """Test optimization summary generation."""
        manager = UnifiedParameterManager("SummaryTest")

        manager.register_parameter(
            ParameterBounds("window", "int", 10, 30, default=20)
        )

        # Mock history
        manager.optimization_history = [
            {"parameters": {"window": 10}, "score": 0.5},
            {"parameters": {"window": 15}, "score": 1.0},
            {"parameters": {"window": 20}, "score": 1.5},
            {"parameters": {"window": 25}, "score": 1.2},
            {"parameters": {"window": 30}, "score": 0.8},
        ]
        manager.best_score = 1.5
        manager.best_parameters = {"window": 20}

        summary = manager.get_optimization_summary()

        assert summary["total_iterations"] == 5
        assert summary["best_score"] == 1.5
        assert summary["strategy_name"] == "SummaryTest"


class TestRiskCalculator:
    """Test unified risk calculator."""

    @pytest.mark.calculation_layer
    def test_position_risk_calculation(self):
        """Test single position risk metrics."""
        calculator = UnifiedRiskCalculator()

        position = Position(
            symbol="0700.HK",
            quantity=1000,
            entry_price=100.0,
            current_price=105.0,
            position_type="LONG"
        )

        risk = calculator.calculate_position_risk(position)

        assert risk["market_value"] == 105000.0
        assert risk["unrealized_pnl"] == 5000.0
        assert risk["unrealized_pnl_pct"] == 0.05

    @pytest.mark.calculation_layer
    def test_var_calculation(self):
        """Test Value at Risk calculation."""
        calculator = UnifiedRiskCalculator()

        # Generate random returns
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        var_95 = calculator.calculate_var(returns, confidence=0.95)
        var_99 = calculator.calculate_var(returns, confidence=0.99)

        # VaR should be negative (represent losses)
        assert var_95 < 0
        assert var_99 < 0
        # 99% VaR should be more negative than 95% VaR
        assert var_99 < var_95

    @pytest.mark.calculation_layer
    def test_cvar_calculation(self):
        """Test Conditional VaR calculation."""
        calculator = UnifiedRiskCalculator()

        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        cvar = calculator.calculate_cvar(returns, confidence=0.95)

        # CVaR should be more extreme than VaR
        assert cvar is not None
        assert isinstance(cvar, (float, np.floating))

    @pytest.mark.calculation_layer
    def test_portfolio_risk_calculation(self):
        """Test portfolio-level risk metrics."""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("0700.HK", 1000, 100, 105, "LONG"),
            Position("0388.HK", 500, 50, 52, "LONG"),
            Position("1398.HK", 2000, 30, 28, "SHORT"),
        ]

        portfolio_risk = calculator.calculate_portfolio_risk(positions)

        assert portfolio_risk.total_value > 0
        assert 0 <= portfolio_risk.concentration_index <= 1
        assert portfolio_risk.largest_position_pct > 0
        assert 0 <= portfolio_risk.margin_ratio <= 2.0

    @pytest.mark.calculation_layer
    def test_portfolio_risk_limits(self):
        """Test portfolio risk limit checking."""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("0700.HK", 1000, 100, 100, "LONG"),
        ]

        portfolio_risk = calculator.calculate_portfolio_risk(positions)

        # Check if risk is acceptable with default limits
        is_acceptable, warnings = portfolio_risk.is_risk_acceptable()

        assert isinstance(is_acceptable, bool)
        assert isinstance(warnings, list)

    @pytest.mark.calculation_layer
    def test_hedge_ratio_calculation(self):
        """Test hedge ratio calculation."""
        calculator = UnifiedRiskCalculator()

        # Position with beta 1.0
        position_size = 100000
        instrument_beta = 1.0
        hedge_beta = 0.5

        hedge_ratio = calculator.calculate_hedge_ratio(
            position_size,
            instrument_beta,
            hedge_beta,
        )

        # Should need more units of lower-beta hedge instrument
        assert hedge_ratio == 200000

    @pytest.mark.calculation_layer
    def test_stress_testing(self):
        """Test portfolio stress testing."""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("0700.HK", 1000, 100, 100, "LONG"),
            Position("0388.HK", 500, 50, 50, "LONG"),
        ]

        stress_scenarios = {
            "market_crash_10": {"0700.HK": -0.10, "0388.HK": -0.10},
            "market_crash_20": {"0700.HK": -0.20, "0388.HK": -0.20},
            "tech_spike": {"0700.HK": 0.15, "0388.HK": 0.20},
        }

        results = calculator.stress_test(positions, stress_scenarios)

        assert len(results) == 3
        # Under crash scenario, portfolio should lose value
        assert results["market_crash_10"] < 0
        assert results["market_crash_20"] < results["market_crash_10"]

    @pytest.mark.calculation_layer
    def test_risk_metrics_summary(self):
        """Test risk metrics summary generation."""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("0700.HK", 1000, 100, 105, "LONG"),
            Position("0388.HK", 500, 50, 48, "SHORT"),
        ]

        summary = calculator.get_risk_metrics_summary(positions)

        assert "total_value" in summary
        assert "var_95" in summary
        assert "concentration" in summary
        assert "margin_ratio" in summary


class TestIntegration:
    """Integration tests for parameter and risk systems."""

    @pytest.mark.calculation_layer
    def test_parameter_optimization_with_risk_constraints(self):
        """Test parameter optimization respecting risk constraints."""
        param_manager = UnifiedParameterManager("RiskAwareOptimization")
        risk_calc = UnifiedRiskCalculator()

        param_manager.register_parameter(
            ParameterBounds("position_size", "float", 0.1, 0.5, 0.3)
        )

        def metrics_with_risk_penalty(data, signals):
            position_size = param_manager.get_parameter("position_size")

            # Base Sharpe ratio
            sharpe = np.random.uniform(0.5, 2.0)

            # Apply penalty if position size too large
            if position_size > 0.4:
                sharpe *= 0.8

            return {"sharpe_ratio": sharpe}

        strategy = MockStrategy()
        data = mock_ohlcv_data("0700.HK", num_days=50)

        result = param_manager.optimize_random(
            strategy,
            data,
            metrics_with_risk_penalty,
            n_iterations=5,
        )

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "calculation_layer"])
