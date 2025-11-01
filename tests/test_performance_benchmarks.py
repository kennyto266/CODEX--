"""
Performance Benchmarking for Phase 2.3

Measures performance of key calculation layer components:
- Backtest execution speed
- Parameter optimization time
- Agent initialization time
- Risk calculation performance

Run with: pytest tests/test_performance_benchmarks.py -v -s
"""

import pytest
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import (
    UnifiedBacktestEngine,
    BacktestConfig,
    UnifiedParameterManager,
    ParameterBounds,
    UnifiedRiskCalculator,
    Position,
    UnifiedAgent,
    AgentConfig,
)


def create_sample_data(num_days=100):
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
    data = pd.DataFrame({
        'Open': 100 + np.random.randn(num_days).cumsum(),
        'High': 102 + np.random.randn(num_days).cumsum(),
        'Low': 98 + np.random.randn(num_days).cumsum(),
        'Close': 100 + np.random.randn(num_days).cumsum(),
        'Volume': np.random.randint(1000000, 5000000, num_days),
    }, index=dates)
    return data.fillna(method='ffill')


def create_sample_signals(data):
    """Create simple buy-sell signals"""
    signals = pd.DataFrame({
        'Signal': np.random.choice([1, -1, 0], size=len(data), p=[0.3, 0.2, 0.5])
    }, index=data.index)
    return signals


# ============================================================================
# BACKTEST PERFORMANCE TESTS
# ============================================================================

class TestBacktestPerformance:
    """Performance tests for backtest engine"""

    def test_backtest_speed_vectorized(self):
        """Measure vectorized backtest speed"""
        data = create_sample_data(num_days=250)  # 1 year of daily data
        signals = create_sample_signals(data)

        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=100000.0,
        )

        start_time = time.time()
        result = engine.run(config, signals, data)
        elapsed = time.time() - start_time

        print(f"\n[OK] Vectorized Backtest Performance:")
        print(f"  - Data points: {len(data)}")
        print(f"  - Execution time: {elapsed:.4f} seconds")
        print(f"  - Speed: {len(data) / elapsed:.0f} bars/second")

        assert result is not None
        assert elapsed < 1.0, f"Vectorized backtest took too long: {elapsed}s"

    def test_backtest_speed_traditional(self):
        """Measure traditional backtest speed"""
        data = create_sample_data(num_days=100)  # Smaller for traditional mode
        signals = create_sample_signals(data)

        engine = UnifiedBacktestEngine(mode="traditional")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=100000.0,
        )

        start_time = time.time()
        result = engine.run(config, signals, data)
        elapsed = time.time() - start_time

        print(f"\n[OK] Traditional Backtest Performance:")
        print(f"  - Data points: {len(data)}")
        print(f"  - Execution time: {elapsed:.4f} seconds")
        print(f"  - Speed: {len(data) / elapsed:.0f} bars/second")

        assert result is not None


# ============================================================================
# PARAMETER OPTIMIZATION PERFORMANCE TESTS
# ============================================================================

class TestParameterOptimizationPerformance:
    """Performance tests for parameter optimization"""

    def test_grid_search_performance(self):
        """Measure grid search optimization speed"""
        manager = UnifiedParameterManager("TestStrategy")

        manager.register_parameter(ParameterBounds(
            name="period1",
            param_type="int",
            min_value=10,
            max_value=30,
            default=20,
            step=10
        ))

        manager.register_parameter(ParameterBounds(
            name="period2",
            param_type="int",
            min_value=20,
            max_value=40,
            default=30,
            step=10
        ))

        # Mock strategy
        class MockStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': np.random.uniform(0, 2)}

        data = create_sample_data(num_days=50)
        strategy = MockStrategy()

        start_time = time.time()
        result = manager.optimize_grid(strategy, data, mock_metrics)
        elapsed = time.time() - start_time

        print(f"\n[OK] Grid Search Performance:")
        print(f"  - Iterations: {len(manager.optimization_history)}")
        print(f"  - Execution time: {elapsed:.4f} seconds")
        print(f"  - Time per iteration: {elapsed/len(manager.optimization_history)*1000:.2f} ms")

        assert result is not None

    def test_random_search_performance(self):
        """Measure random search optimization speed"""
        manager = UnifiedParameterManager("TestStrategy")

        manager.register_parameter(ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=50,
            default=20
        ))

        class MockStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': np.random.uniform(0, 2)}

        data = create_sample_data(num_days=50)
        strategy = MockStrategy()

        start_time = time.time()
        result = manager.optimize_random(strategy, data, mock_metrics, n_iterations=20)
        elapsed = time.time() - start_time

        print(f"\n[OK] Random Search Performance:")
        print(f"  - Iterations: {len(manager.optimization_history)}")
        print(f"  - Execution time: {elapsed:.4f} seconds")
        print(f"  - Time per iteration: {elapsed/len(manager.optimization_history)*1000:.2f} ms")

        assert result is not None


# ============================================================================
# RISK CALCULATION PERFORMANCE TESTS
# ============================================================================

class TestRiskCalculationPerformance:
    """Performance tests for risk calculations"""

    def test_position_risk_calculation_speed(self):
        """Measure single position risk calculation speed"""
        calculator = UnifiedRiskCalculator()

        position = Position(
            symbol="TEST",
            quantity=1000,
            entry_price=100.0,
            current_price=105.0,
            position_type="LONG"
        )

        start_time = time.time()
        for _ in range(1000):
            risk = calculator.calculate_position_risk(position)
        elapsed = time.time() - start_time

        print(f"\n[OK] Position Risk Calculation Performance:")
        print(f"  - Iterations: 1000")
        print(f"  - Total time: {elapsed:.4f} seconds")
        print(f"  - Time per calculation: {elapsed/1000*1000:.4f} ms")

        assert risk is not None

    def test_portfolio_risk_calculation_speed(self):
        """Measure portfolio risk calculation speed"""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("TEST1", 1000, 100, 105, "LONG"),
            Position("TEST2", 500, 50, 52, "LONG"),
            Position("TEST3", 2000, 30, 28, "SHORT"),
        ]

        start_time = time.time()
        for _ in range(100):
            risk = calculator.calculate_portfolio_risk(positions)
        elapsed = time.time() - start_time

        print(f"\n[OK] Portfolio Risk Calculation Performance:")
        print(f"  - Positions: {len(positions)}")
        print(f"  - Iterations: 100")
        print(f"  - Total time: {elapsed:.4f} seconds")
        print(f"  - Time per calculation: {elapsed/100*1000:.4f} ms")

        assert risk is not None

    def test_var_calculation_speed(self):
        """Measure VaR calculation speed"""
        calculator = UnifiedRiskCalculator()
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        start_time = time.time()
        for _ in range(100):
            var_95 = calculator.calculate_var(returns, confidence=0.95)
            var_99 = calculator.calculate_var(returns, confidence=0.99)
        elapsed = time.time() - start_time

        print(f"\n[OK] VaR Calculation Performance:")
        print(f"  - Data points: {len(returns)}")
        print(f"  - Iterations: 100")
        print(f"  - Total time: {elapsed:.4f} seconds")
        print(f"  - Time per calculation: {elapsed/100*1000:.4f} ms")

        assert var_95 is not None


# ============================================================================
# AGENT SYSTEM PERFORMANCE TESTS
# ============================================================================

class TestAgentPerformance:
    """Performance tests for agent system"""

    @pytest.mark.asyncio
    async def test_agent_startup_time(self):
        """Measure agent initialization time"""
        agent_types = [
            'coordinator', 'data_scientist', 'quantitative_analyst',
            'portfolio_manager', 'quantitative_engineer', 'quantitative_trader',
            'research_analyst', 'risk_analyst'
        ]

        startup_times = {}

        for agent_type in agent_types:
            config = AgentConfig(
                agent_id=f"perf_test_{agent_type}",
                agent_name=f"Performance Test {agent_type}",
                role_type=agent_type
            )

            agent = UnifiedAgent(config)

            start_time = time.time()
            await agent.start()
            elapsed = time.time() - start_time

            startup_times[agent_type] = elapsed
            await agent.stop()

        print(f"\n[OK] Agent Startup Performance:")
        avg_time = sum(startup_times.values()) / len(startup_times)
        print(f"  - Average startup time: {avg_time*1000:.2f} ms")
        print(f"  - All agents:")
        for agent_type, t in sorted(startup_times.items()):
            print(f"    - {agent_type}: {t*1000:.2f} ms")

        assert avg_time < 0.1, f"Average startup too slow: {avg_time}s"

    @pytest.mark.asyncio
    async def test_message_processing_speed(self):
        """Measure message processing speed"""
        config = AgentConfig(
            agent_id="perf_test_msg",
            agent_name="Performance Test",
            role_type="data_scientist"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        from src.core.unified_agent import Message

        start_time = time.time()
        for i in range(100):
            message = Message(
                message_type="ANALYZE_DATA",
                sender_id="test",
                content={"data": f"test_{i}"}
            )
            await agent.process_message(message)
        elapsed = time.time() - start_time

        print(f"\n[OK] Message Processing Performance:")
        print(f"  - Messages: 100")
        print(f"  - Total time: {elapsed:.4f} seconds")
        print(f"  - Time per message: {elapsed/100*1000:.4f} ms")

        await agent.stop()

        assert elapsed < 1.0, f"Message processing too slow: {elapsed}s"


# ============================================================================
# SUMMARY BENCHMARKS
# ============================================================================

class TestPerformanceSummary:
    """Summary performance benchmarks"""

    @pytest.mark.slow
    def test_full_pipeline_performance(self):
        """Measure full calculation pipeline performance"""
        print("\n" + "="*60)
        print("FULL CALCULATION PIPELINE PERFORMANCE SUMMARY")
        print("="*60)

        # 1. Backtest
        data = create_sample_data(num_days=250)
        signals = create_sample_signals(data)
        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(symbol="TEST", start_date=data.index[0], end_date=data.index[-1])

        start = time.time()
        engine.run(config, signals, data)
        backtest_time = time.time() - start

        # 2. Parameters
        manager = UnifiedParameterManager("Test")
        manager.register_parameter(ParameterBounds("p", "int", 10, 20, 15))

        class MS:
            def initialize(self, d): pass
            def generate_signals(self, d): return pd.Series(0, index=d.index)

        start = time.time()
        manager.optimize_random(MS(), data[:50], lambda d, s: {'sharpe_ratio': 1.0}, n_iterations=10)
        param_time = time.time() - start

        # 3. Risk
        calc = UnifiedRiskCalculator()
        positions = [Position("T", 1000, 100, 105, "LONG")]

        start = time.time()
        for _ in range(100):
            calc.calculate_portfolio_risk(positions)
        risk_time = time.time() - start

        print(f"\nComponent Performance:")
        print(f"  - Backtest (250 bars): {backtest_time*1000:.2f} ms")
        print(f"  - Parameter Optimization (10 iterations): {param_time*1000:.2f} ms")
        print(f"  - Risk Calculation (100x): {risk_time*1000:.2f} ms")
        print(f"  - Total: {(backtest_time + param_time + risk_time)*1000:.2f} ms")
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
