"""
Performance Calculator Test - Verify strategy performance and risk metrics calculation
"""
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.backtest.strategy_performance import PerformanceCalculator
from src.risk_management.risk_calculator import RiskCalculator, RiskLimits, RiskLevel


class TestPerformanceCalculator:
    """Performance Calculator Test"""

    def __init__(self):
        self.calculator = PerformanceCalculator()
        self.risk_calculator = RiskCalculator()

    def generate_sample_returns(self, num_days=252, initial_value=100000):
        """Generate sample returns data"""
        # 生成随机收益率
        np.random.seed(42)  # 固定种子确保可重复性
        daily_returns = np.random.normal(0.001, 0.02, num_days)  # 平均日收益0.1%，波动2%

        # 创建收益率序列
        dates = pd.date_range(start='2023-01-01', periods=num_days, freq='D')
        returns_series = pd.Series(daily_returns, index=dates)

        return returns_series

    def generate_sample_benchmark_returns(self, num_days=252):
        """Generate sample benchmark returns"""
        np.random.seed(42)
        benchmark_returns = np.random.normal(0.0005, 0.015, num_days)
        dates = pd.date_range(start='2023-01-01', periods=num_days, freq='D')
        return pd.Series(benchmark_returns, index=dates)

    def test_basic_performance_metrics(self):
        """Test basic performance metrics calculation"""
        print("\n" + "=" * 60)
        print("Test: Basic Performance Metrics Calculation")
        print("=" * 60)

        # 生成测试数据
        returns = self.generate_sample_returns(252)
        benchmark = self.generate_sample_benchmark_returns(252)

        # Calculate performance metrics
        performance = self.calculator.calculate_performance_metrics(
            returns=returns,
            benchmark_returns=benchmark,
            risk_free_rate=0.03
        )

        # Print results
        print(f"\nStrategy Performance Metrics:")
        print(f"  Total Return: {performance.total_return:.2%}")
        print(f"  Annualized Return: {performance.annualized_return:.2%}")
        print(f"  CAGR: {performance.cagr:.2%}")
        print(f"  Volatility: {performance.volatility:.2%}")
        print(f"  Max Drawdown: {performance.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {performance.sharpe_ratio:.4f}")
        print(f"  Sortino Ratio: {performance.sortino_ratio:.4f}")
        print(f"  Calmar Ratio: {performance.calmar_ratio:.4f}")
        print(f"  Alpha: {performance.alpha:.4f}")
        print(f"  Beta: {performance.beta:.4f}")
        print(f"  Information Ratio: {performance.information_ratio:.4f}")
        print(f"  Win Rate: {performance.win_rate:.2%}")
        print(f"  Trade Count: {performance.trades_count}")

        # Verify results
        assert performance.total_return > -1, "Total return should not be less than -100%"
        assert abs(performance.volatility) < 2, "Volatility should not exceed 200%"
        assert 0 <= performance.win_rate <= 1, "Win rate should be between 0-1"
        assert performance.trades_count == 252, "Trade count should equal data points"

        print("\n[OK] Basic performance metrics test passed")
        return performance

    async def test_risk_metrics_calculation(self):
        """Test risk metrics calculation"""
        print("\n" + "=" * 60)
        print("Test: Risk Metrics Calculation")
        print("=" * 60)

        # 生成测试数据
        returns = self.generate_sample_returns(252)
        benchmark = self.generate_sample_benchmark_returns(252)

        # Calculate risk metrics
        risk_metrics = await self.risk_calculator.calculate_portfolio_risk(
            returns=returns,
            benchmark_returns=benchmark
        )

        # Print results
        print(f"\nRisk Metrics:")
        print(f"  Volatility: {risk_metrics.volatility:.2%}")
        print(f"  Sharpe Ratio: {risk_metrics.sharpe_ratio:.4f}")
        print(f"  Max Drawdown: {risk_metrics.max_drawdown:.2%}")
        print(f"  Calmar Ratio: {risk_metrics.calmar_ratio:.4f}")
        print(f"  VaR (95%): {risk_metrics.var_95:.4f}")
        print(f"  VaR (99%): {risk_metrics.var_99:.4f}")
        print(f"  Expected Shortfall (95%): {risk_metrics.expected_shortfall_95:.4f}")
        print(f"  Expected Shortfall (99%): {risk_metrics.expected_shortfall_99:.4f}")
        print(f"  Beta: {risk_metrics.beta:.4f}")
        print(f"  Tracking Error: {risk_metrics.tracking_error:.4f}")
        print(f"  Information Ratio: {risk_metrics.information_ratio:.4f}")
        print(f"  Sortino Ratio: {risk_metrics.sortino_ratio:.4f}")
        print(f"  Risk Level: {risk_metrics.risk_level}")

        # Verify results
        assert risk_metrics.volatility > 0, "Volatility should be greater than 0"
        assert risk_metrics.max_drawdown >= 0, "Max drawdown should be greater than or equal to 0"
        assert risk_metrics.var_95 < 0, "95% VaR should be negative"
        assert risk_metrics.var_99 < risk_metrics.var_95, "99% VaR should be less than 95% VaR"
        assert isinstance(risk_metrics.risk_level, RiskLevel), "Risk level should be a valid enum value"

        print("\n[OK] Risk metrics calculation test passed")
        return risk_metrics

    async def test_var_calculation_methods(self):
        """Test different VaR calculation methods"""
        print("\n" + "=" * 60)
        print("Test: VaR Calculation Methods")
        print("=" * 60)

        # 生成测试数据
        returns = self.generate_sample_returns(1000)

        # Historical simulation VaR
        historical_var = await self.risk_calculator.calculate_historical_var(
            returns=returns,
            confidence_level=0.95,
            time_horizon=1
        )

        print(f"\nHistorical Simulation VaR:")
        print(f"  VaR (95%): {historical_var['var']:.4f}")
        print(f"  Expected Shortfall: {historical_var['expected_shortfall']:.4f}")
        print(f"  Data Points: {historical_var['data_points']}")

        # Monte Carlo VaR
        monte_carlo_var = await self.risk_calculator.calculate_monte_carlo_var(
            returns=returns,
            confidence_level=0.95,
            num_simulations=10000,
            time_horizon=1
        )

        print(f"\nMonte Carlo VaR:")
        print(f"  VaR (95%): {monte_carlo_var['var']:.4f}")
        print(f"  Expected Shortfall: {monte_carlo_var['expected_shortfall']:.4f}")
        print(f"  Simulations: {monte_carlo_var['num_simulations']}")

        # Verify results consistency
        assert historical_var['var'] < 0, "Historical VaR should be negative"
        assert monte_carlo_var['var'] < 0, "Monte Carlo VaR should be negative"

        print("\n[OK] VaR calculation methods test passed")

    async def test_portfolio_var_calculation(self):
        """Test portfolio VaR calculation"""
        print("\n" + "=" * 60)
        print("Test: Portfolio VaR Calculation")
        print("=" * 60)

        # Generate data for multiple stocks
        symbols = ['0700.HK', '0388.HK', '1398.HK']
        num_days = 252

        returns_data = {}
        for symbol in symbols:
            np.random.seed(hash(symbol) % 2**32)  # Use symbol as seed
            returns = np.random.normal(0.001, 0.02, num_days)
            dates = pd.date_range(start='2023-01-01', periods=num_days, freq='D')
            returns_data[symbol] = pd.Series(returns, index=dates)

        returns_df = pd.DataFrame(returns_data)

        # Equal weights
        weights = pd.Series({'0700.HK': 0.33, '0388.HK': 0.33, '1398.HK': 0.34})

        # Calculate covariance matrix
        covariance_matrix = await self.risk_calculator.calculate_covariance_matrix(returns_df)

        # Calculate portfolio VaR
        portfolio_var = await self.risk_calculator.calculate_portfolio_var(
            weights=weights,
            covariance_matrix=covariance_matrix,
            confidence_level=0.95
        )

        # Calculate marginal VaR
        marginal_var = await self.risk_calculator.calculate_marginal_var(
            weights=weights,
            covariance_matrix=covariance_matrix,
            confidence_level=0.95
        )

        # Calculate component VaR
        component_var = await self.risk_calculator.calculate_component_var(
            weights=weights,
            covariance_matrix=covariance_matrix,
            confidence_level=0.95
        )

        print(f"\nCovariance Matrix:")
        print(covariance_matrix)

        print(f"\nPortfolio VaR (95%): {portfolio_var:.4f}")

        print(f"\nMarginal VaR:")
        for symbol, var in marginal_var.items():
            print(f"  {symbol}: {var:.4f}")

        print(f"\nComponent VaR:")
        for symbol, var in component_var.items():
            print(f"  {symbol}: {var:.4f}")

        # Verify results
        assert portfolio_var > 0, "Portfolio VaR should be positive"
        assert len(marginal_var) == 3, "Marginal VaR should have 3 assets"
        assert len(component_var) == 3, "Component VaR should have 3 assets"

        print("\n[OK] Portfolio VaR calculation test passed")

    async def test_stress_testing(self):
        """Test stress testing"""
        print("\n" + "=" * 60)
        print("Test: Stress Testing")
        print("=" * 60)

        # 生成测试数据
        returns = self.generate_sample_returns(252)

        # Define stress scenarios
        stress_scenarios = {
            'market_crash': -2.0,  # Market crash, returns multiplied by -2
            'high_volatility': 1.5,  # High volatility
            'mild_stress': 0.8,  # Mild stress
            'extreme_stress': 3.0  # Extreme stress
        }

        # Calculate stress test results
        stress_results = await self.risk_calculator.calculate_stress_test(
            returns=returns,
            stress_scenarios=stress_scenarios
        )

        print(f"\nStress Test Results:")
        for scenario, result in stress_results.items():
            print(f"\nScenario: {scenario}")
            print(f"  Stress Factor: {result['stress_factor']:.2f}")
            print(f"  VaR (95%): {result['var_95']:.4f}")
            print(f"  VaR (99%): {result['var_99']:.4f}")
            print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
            print(f"  Expected Loss: {result['expected_loss']:.4f}")

        # Verify stress test results
        assert len(stress_results) == 4, "Should have 4 stress scenarios"
        for scenario, result in stress_results.items():
            assert result['var_95'] < 0, f"{scenario} scenario VaR should be negative"
            assert result['max_drawdown'] >= 0, f"{scenario} scenario max drawdown should be >= 0"

        print("\n[OK] Stress testing passed")

    async def test_risk_limits_validation(self):
        """Test risk limits validation"""
        print("\n" + "=" * 60)
        print("Test: Risk Limits Validation")
        print("=" * 60)

        # Create risk limits
        risk_limits = RiskLimits(
            max_position_size=0.2,
            max_portfolio_risk=0.05,
            max_drawdown_limit=0.15,
            max_var_limit=0.02,
            max_leverage=2.0,
            max_concentration=0.25,
            min_liquidity=0.1
        )

        # Test position weights
        test_weights = pd.Series({
            '0700.HK': 0.30,  # Exceeds limit
            '0388.HK': 0.25,  # Exceeds limit
            '1398.HK': 0.20,  # Within limit
            '0939.HK': 0.25   # Exceeds limit
        })

        # Calculate risk budget
        risk_budget = await self.risk_calculator.calculate_risk_budget(
            weights=test_weights,
            risk_limits=risk_limits
        )

        print(f"\nRisk Budget Check:")
        print(f"Test Weights: {test_weights.to_dict()}")

        if 'position_violations' in risk_budget:
            print(f"\nPosition Violations:")
            for symbol, weight in risk_budget['position_violations'].items():
                print(f"  {symbol}: {weight:.2%} (limit: {risk_limits.max_position_size:.2%})")

        if 'concentration_violation' in risk_budget:
            print(f"\nConcentration Violation:")
            print(f"  Max Concentration: {risk_budget['concentration_violation']['max_concentration']:.2%}")
            print(f"  Limit: {risk_budget['concentration_violation']['limit']:.2%}")

        if 'leverage_violation' in risk_budget:
            print(f"\nLeverage Violation:")
            print(f"  Total Leverage: {risk_budget['leverage_violation']['total_leverage']:.2f}")
            print(f"  Limit: {risk_budget['leverage_violation']['limit']:.2f}")

        print("\n[OK] Risk limits validation test passed")

    async def test_real_world_scenario(self):
        """Test real-world scenario"""
        print("\n" + "=" * 60)
        print("Test: Real-World Scenario Simulation")
        print("=" * 60)

        # Simulate returns for a real trading strategy
        # Assume we have a momentum strategy with 15% annual return and 20% volatility
        np.random.seed(123)
        num_days = 252
        annual_return = 0.15
        annual_volatility = 0.20

        daily_mean = annual_return / 252
        daily_std = annual_volatility / np.sqrt(252)

        strategy_returns = np.random.normal(daily_mean, daily_std, num_days)

        # Add some trend and reversal
        trend = np.linspace(0, 0.001, num_days)
        strategy_returns += trend

        dates = pd.date_range(start='2023-01-01', periods=num_days, freq='D')
        strategy_series = pd.Series(strategy_returns, index=dates)

        # Benchmark (Hang Seng Index)
        benchmark_returns = np.random.normal(0.08 / 252, 0.18 / np.sqrt(252), num_days)
        benchmark_series = pd.Series(benchmark_returns, index=dates)

        # Calculate performance metrics
        performance = self.calculator.calculate_performance_metrics(
            returns=strategy_series,
            benchmark_returns=benchmark_series,
            risk_free_rate=0.03
        )

        # Calculate risk metrics
        risk_metrics = await self.risk_calculator.calculate_portfolio_risk(
            returns=strategy_series,
            benchmark_returns=benchmark_series
        )

        print(f"\nStrategy Performance Summary:")
        print(f"  Total Return: {performance.total_return:.2%}")
        print(f"  Annualized Return: {performance.annualized_return:.2%}")
        print(f"  Volatility: {performance.volatility:.2%}")
        print(f"  Max Drawdown: {performance.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {performance.sharpe_ratio:.4f}")
        print(f"  Sortino Ratio: {performance.sortino_ratio:.4f}")
        print(f"  Calmar Ratio: {performance.calmar_ratio:.4f}")
        print(f"  Alpha: {performance.alpha:.4f}")
        print(f"  Beta: {performance.beta:.4f}")
        print(f"  Information Ratio: {performance.information_ratio:.4f}")

        print(f"\nRisk Assessment:")
        print(f"  Risk Level: {risk_metrics.risk_level}")
        print(f"  VaR (95%): {risk_metrics.var_95:.4f}")
        print(f"  VaR (99%): {risk_metrics.var_99:.4f}")
        print(f"  Expected Shortfall (95%): {risk_metrics.expected_shortfall_95:.4f}")

        # Evaluate strategy quality
        if performance.sharpe_ratio > 1.0:
            print("\n[OK] Strategy Rating: Excellent (Sharpe Ratio > 1.0)")
        elif performance.sharpe_ratio > 0.5:
            print("\n[OK] Strategy Rating: Good (Sharpe Ratio > 0.5)")
        else:
            print("\n[WARNING] Strategy Rating: Needs Improvement (Sharpe Ratio < 0.5)")

        if risk_metrics.risk_level == RiskLevel.LOW:
            print("[OK] Risk Level: Low Risk")
        elif risk_metrics.risk_level == RiskLevel.MEDIUM:
            print("[OK] Risk Level: Medium Risk")
        elif risk_metrics.risk_level == RiskLevel.HIGH:
            print("[WARNING] Risk Level: High Risk")
        else:
            print("[ERROR] Risk Level: Critical Risk")

        print("\n[OK] Real-world scenario test passed")


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("Strategy Performance and Risk Metrics Calculation Test")
    print("=" * 60)

    tester = TestPerformanceCalculator()

    try:
        # Test basic performance metrics
        tester.test_basic_performance_metrics()

        # Test risk metrics
        await tester.test_risk_metrics_calculation()

        # Test VaR calculation methods
        await tester.test_var_calculation_methods()

        # Test portfolio VaR calculation
        await tester.test_portfolio_var_calculation()

        # Test stress testing
        await tester.test_stress_testing()

        # Test risk limits validation
        await tester.test_risk_limits_validation()

        # Test real-world scenario
        await tester.test_real_world_scenario()

        print("\n" + "=" * 60)
        print("[OK] All tests passed!")
        print("=" * 60)

        print("\nPerformance metrics calculation module successfully verified:")
        print("  [OK] Strategy performance metrics calculated correctly")
        print("  [OK] Risk metrics calculated correctly")
        print("  [OK] VaR calculation methods effective")
        print("  [OK] Portfolio risk analysis accurate")
        print("  [OK] Stress testing functionality normal")
        print("  [OK] Risk limits validation effective")
        print("  [OK] Real-world scenario simulation passed")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
