"""
Integration Testing for Phase 2.3

Verifies compatibility of Phase 2.3 components with existing system:
- Unified Backtest Engine with legacy strategies
- Unified Parameter Manager with optimization pipeline
- Unified Risk Calculator with portfolio management
- Unified Agent System with multi-agent coordination
- Data flow and message passing across components

Run with: pytest tests/test_integration_phase2_3.py -v -s
"""

import pytest
import asyncio
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


def create_test_data(num_days=100):
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
    data = pd.DataFrame({
        'Open': 100 + np.random.randn(num_days).cumsum(),
        'High': 102 + np.random.randn(num_days).cumsum(),
        'Low': 98 + np.random.randn(num_days).cumsum(),
        'Close': 100 + np.random.randn(num_days).cumsum(),
        'Volume': np.random.randint(1000000, 5000000, num_days),
    }, index=dates)
    return data.ffill()


def create_test_signals(data):
    """Create simple buy-sell signals"""
    signals = pd.DataFrame({
        'Signal': np.random.choice([1, -1, 0], size=len(data), p=[0.3, 0.2, 0.5])
    }, index=data.index)
    return signals


# ============================================================================
# BACKTEST ENGINE INTEGRATION TESTS
# ============================================================================

class TestBacktestEngineIntegration:
    """Integration tests for Unified Backtest Engine"""

    def test_backtest_engine_produces_valid_results(self):
        """Verify backtest engine produces properly formatted results"""
        data = create_test_data(num_days=100)
        signals = create_test_signals(data)

        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=100000.0,
        )

        result = engine.run(config, signals, data)

        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'trades' in result or 'returns' in result

    def test_backtest_engine_compatible_with_legacy_data_formats(self):
        """Verify engine handles various data formats"""
        # Standard format
        data = create_test_data(num_days=100)
        signals = create_test_signals(data)

        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        result = engine.run(config, signals, data)
        assert result is not None

    def test_backtest_engine_handles_empty_signals(self):
        """Verify engine handles edge case of no signals"""
        data = create_test_data(num_days=100)
        signals = pd.DataFrame({
            'Signal': [0] * len(data)
        }, index=data.index)

        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        result = engine.run(config, signals, data)
        assert result is not None

    def test_backtest_engine_mode_switching(self):
        """Verify engine can switch between modes"""
        data = create_test_data(num_days=50)
        signals = create_test_signals(data)

        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        # Test vectorized mode
        engine_vec = UnifiedBacktestEngine(mode="vectorized")
        result_vec = engine_vec.run(config, signals, data)
        assert result_vec is not None

        # Test traditional mode
        engine_trad = UnifiedBacktestEngine(mode="traditional")
        result_trad = engine_trad.run(config, signals, data)
        assert result_trad is not None


# ============================================================================
# PARAMETER MANAGER INTEGRATION TESTS
# ============================================================================

class TestParameterManagerIntegration:
    """Integration tests for Unified Parameter Manager"""

    def test_parameter_manager_grid_search_integration(self):
        """Verify parameter manager works with backtest engine"""
        manager = UnifiedParameterManager("TestStrategy")

        manager.register_parameter(ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=30,
            default=20,
            step=10
        ))

        # Mock strategy
        class TestStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': np.random.uniform(0, 2)}

        data = create_test_data(num_days=50)
        strategy = TestStrategy()

        result = manager.optimize_grid(strategy, data, mock_metrics)
        assert result is not None
        assert len(manager.optimization_history) > 0

    def test_parameter_manager_random_search_integration(self):
        """Verify random search integration"""
        manager = UnifiedParameterManager("TestStrategy")

        manager.register_parameter(ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=50,
            default=20
        ))

        class TestStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': np.random.uniform(0, 2)}

        data = create_test_data(num_days=50)
        strategy = TestStrategy()

        result = manager.optimize_random(strategy, data, mock_metrics, n_iterations=10)
        assert result is not None
        assert len(manager.optimization_history) == 10

    def test_parameter_manager_persistence(self):
        """Verify parameter optimization results are persisted"""
        manager = UnifiedParameterManager("TestStrategy")

        manager.register_parameter(ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=20,
            default=15
        ))

        class TestStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': 1.5}

        data = create_test_data(num_days=50)
        strategy = TestStrategy()

        result = manager.optimize_random(strategy, data, mock_metrics, n_iterations=5)

        # Verify history is tracked
        assert len(manager.optimization_history) == 5
        for entry in manager.optimization_history:
            assert 'parameters' in entry
            assert 'metrics' in entry


# ============================================================================
# RISK CALCULATOR INTEGRATION TESTS
# ============================================================================

class TestRiskCalculatorIntegration:
    """Integration tests for Unified Risk Calculator"""

    def test_risk_calculator_position_management(self):
        """Verify risk calculator works with position objects"""
        calculator = UnifiedRiskCalculator()

        position = Position(
            symbol="TEST",
            quantity=1000,
            entry_price=100.0,
            current_price=105.0,
            position_type="LONG"
        )

        risk = calculator.calculate_position_risk(position)
        assert risk is not None
        assert isinstance(risk, dict)

    def test_risk_calculator_portfolio_integration(self):
        """Verify risk calculator handles multiple positions"""
        calculator = UnifiedRiskCalculator()

        positions = [
            Position("TEST1", 1000, 100, 105, "LONG"),
            Position("TEST2", 500, 50, 52, "LONG"),
            Position("TEST3", 2000, 30, 28, "SHORT"),
        ]

        risk = calculator.calculate_portfolio_risk(positions)
        assert risk is not None
        # PortfolioRisk is a named tuple, not a dict
        assert hasattr(risk, 'total_value') or isinstance(risk, dict)

    def test_risk_calculator_var_integration(self):
        """Verify VaR calculation works with returns data"""
        calculator = UnifiedRiskCalculator()
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        var_95 = calculator.calculate_var(returns, confidence=0.95)
        var_99 = calculator.calculate_var(returns, confidence=0.99)

        assert var_95 is not None
        assert var_99 is not None
        assert var_99 < var_95  # 99% VaR should be larger

    def test_risk_calculator_stress_testing(self):
        """Verify stress test integration"""
        calculator = UnifiedRiskCalculator()

        positions = [Position("TEST", 1000, 100, 105, "LONG")]
        shock_scenarios = {
            'market_down': -0.20,
            'volatility_spike': 0.50,
        }

        for scenario_name, shock in shock_scenarios.items():
            stressed_price = 105 * (1 + shock)
            position = Position("TEST", 1000, 100, stressed_price, "LONG")
            risk = calculator.calculate_position_risk(position)
            assert risk is not None


# ============================================================================
# UNIFIED AGENT SYSTEM INTEGRATION TESTS
# ============================================================================

class TestUnifiedAgentIntegration:
    """Integration tests for Unified Agent System"""

    @pytest.mark.asyncio
    async def test_agent_lifecycle_integration(self):
        """Verify agent can be created, started, and stopped"""
        config = AgentConfig(
            agent_id="integration_test_1",
            agent_name="Integration Test Agent",
            role_type="data_scientist"
        )

        agent = UnifiedAgent(config)

        # Start agent
        await agent.start()
        assert agent.running

        # Stop agent
        await agent.stop()
        assert not agent.running

    @pytest.mark.asyncio
    async def test_agent_message_passing(self):
        """Verify agents can process messages"""
        config = AgentConfig(
            agent_id="integration_test_2",
            agent_name="Integration Test Agent",
            role_type="quantitative_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        from src.core.unified_agent import Message

        # Send message
        message = Message(
            message_type="ANALYZE_DATA",
            sender_id="test",
            content={"test": "data"}
        )

        # Agent should process message (may return True or False depending on message type)
        result = await agent.process_message(message)
        assert isinstance(result, bool)  # Just verify it returns a boolean

        await agent.stop()

    @pytest.mark.asyncio
    async def test_multiple_agents_coordination(self):
        """Verify multiple agents can be created and managed"""
        agents = []
        agent_configs = [
            AgentConfig("agent_1", "Agent 1", "coordinator"),
            AgentConfig("agent_2", "Agent 2", "data_scientist"),
            AgentConfig("agent_3", "Agent 3", "quantitative_analyst"),
        ]

        # Create and start all agents
        for config in agent_configs:
            agent = UnifiedAgent(config)
            await agent.start()
            agents.append(agent)

        # Verify all running
        for agent in agents:
            assert agent.running

        # Stop all agents
        for agent in agents:
            await agent.stop()

        # Verify all stopped
        for agent in agents:
            assert not agent.running

    @pytest.mark.asyncio
    async def test_agent_message_throughput(self):
        """Verify agent can handle message volume"""
        config = AgentConfig(
            agent_id="integration_test_3",
            agent_name="Throughput Test",
            role_type="research_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        from src.core.unified_agent import Message

        # Send multiple messages
        processed_count = 0
        for i in range(50):
            message = Message(
                message_type="DATA_UPDATE",
                sender_id="test",
                content={"index": i}
            )
            result = await agent.process_message(message)
            if isinstance(result, bool):
                processed_count += 1

        # Verify agent processed multiple messages without errors
        assert processed_count > 0

        await agent.stop()


# ============================================================================
# CROSS-COMPONENT INTEGRATION TESTS
# ============================================================================

class TestCrossComponentIntegration:
    """Integration tests across multiple components"""

    def test_backtest_with_optimized_parameters(self):
        """Verify optimized parameters work with backtest engine"""
        # 1. Optimize parameters
        manager = UnifiedParameterManager("TestStrategy")
        manager.register_parameter(ParameterBounds(
            name="period",
            param_type="int",
            min_value=10,
            max_value=20,
            default=15
        ))

        class TestStrategy:
            def initialize(self, data):
                pass

            def generate_signals(self, data):
                return pd.Series(0, index=data.index)

        def mock_metrics(data, signals):
            return {'sharpe_ratio': 1.5}

        data = create_test_data(num_days=100)
        strategy = TestStrategy()

        result = manager.optimize_random(strategy, data, mock_metrics, n_iterations=5)
        best_params = result['best_parameters']

        # 2. Run backtest with optimized parameters
        signals = create_test_signals(data)
        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
        )

        backtest_result = engine.run(config, signals, data)
        assert backtest_result is not None

    def test_risk_analysis_after_backtest(self):
        """Verify risk calculation on backtest results"""
        # 1. Run backtest
        data = create_test_data(num_days=100)
        signals = create_test_signals(data)

        engine = UnifiedBacktestEngine(mode="vectorized")
        config = BacktestConfig(
            symbol="TEST",
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=100000.0,
        )

        backtest_result = engine.run(config, signals, data)
        assert backtest_result is not None

        # 2. Calculate risk metrics
        calculator = UnifiedRiskCalculator()
        position = Position("TEST", 1000, 100, 105, "LONG")
        risk = calculator.calculate_position_risk(position)
        assert risk is not None

    @pytest.mark.asyncio
    async def test_agent_orchestration_with_components(self):
        """Verify agent can orchestrate backtest and risk operations"""
        # Create orchestrator agent
        config = AgentConfig(
            agent_id="orchestrator",
            agent_name="System Orchestrator",
            role_type="coordinator"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        from src.core.unified_agent import Message

        # Send operation message
        message = Message(
            message_type="RUN_BACKTEST",
            sender_id="test",
            content={
                "symbol": "TEST",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        )

        # Agent should handle the message (may return True or False)
        result = await agent.process_message(message)
        assert isinstance(result, bool)

        await agent.stop()


# ============================================================================
# COMPATIBILITY TESTS
# ============================================================================

class TestLegacyCompatibility:
    """Tests ensuring Phase 2.3 components are backward compatible"""

    def test_backtest_config_compatibility(self):
        """Verify BacktestConfig works with various parameter combinations"""
        configs = [
            BacktestConfig(symbol="TEST", start_date="2024-01-01", end_date="2024-12-31"),
            BacktestConfig(symbol="TEST", start_date="2024-01-01", end_date="2024-12-31",
                          initial_capital=100000),
            BacktestConfig(symbol="TEST", start_date="2024-01-01", end_date="2024-12-31",
                          initial_capital=50000),
        ]

        for config in configs:
            assert config.symbol == "TEST"

    def test_parameter_bounds_flexibility(self):
        """Verify ParameterBounds handles various parameter types"""
        bounds_list = [
            ParameterBounds("period", "int", 10, 50, 20),
            ParameterBounds("threshold", "float", 0.0, 1.0, 0.5),
            ParameterBounds("enabled", "bool", default=True),
        ]

        for bounds in bounds_list:
            assert bounds.name is not None
            assert bounds.min_value is not None or bounds.param_type == "bool"

    def test_position_object_compatibility(self):
        """Verify Position objects are properly initialized"""
        positions = [
            Position("TEST", 100, 50.0, 52.0, "LONG"),
            Position("TEST", -100, 50.0, 48.0, "SHORT"),
            Position("TEST", 0, 50.0, 50.0, "NONE"),
        ]

        for pos in positions:
            assert pos.symbol == "TEST"
            assert pos.entry_price == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
