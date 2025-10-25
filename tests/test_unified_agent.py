"""
Unified Agent System Tests

Tests for the unified agent framework consolidating all 23 agent implementations.

Run with: pytest tests/test_unified_agent.py -v -m agent_system
"""

import pytest
import asyncio
from datetime import datetime

from src.core.unified_agent import (
    UnifiedAgent,
    BaseRole,
    Message,
    AgentConfig,
    AgentStatus,
    SimpleMessageQueue,
)
from src.core.role_provider import (
    RoleProvider,
    CoordinatorRole,
    DataScientistRole,
    QuantitativeAnalystRole,
    PortfolioManagerRole,
    QuantitativeEngineerRole,
    QuantitativeTraderRole,
    ResearchAnalystRole,
    RiskAnalystRole,
    RealDataScientistRole,
    RealQuantitativeAnalystRole,
    RealPortfolioManagerRole,
    RealQuantitativeEngineerRole,
    RealQuantitativeTraderRole,
    RealResearchAnalystRole,
    RealRiskAnalystRole,
    RealDataAnalyzerRole,
    HKDataScientistRole,
    HKQuantitativeAnalystRole,
    HKPortfolioManagerRole,
    HKQuantitativeEngineerRole,
    HKQuantitativeTraderRole,
    HKResearchAnalystRole,
    HKRiskAnalystRole,
)


# ============================================================================
# UNIFIED AGENT TESTS
# ============================================================================

class TestUnifiedAgent:
    """Test UnifiedAgent core functionality"""

    @pytest.mark.agent_system
    def test_agent_initialization(self):
        """Test agent initialization"""
        config = AgentConfig(
            agent_id="agent_001",
            agent_name="Test Agent",
            role_type="data_scientist"
        )

        agent = UnifiedAgent(config)

        assert agent.agent_id == "agent_001"
        assert agent.agent_name == "Test Agent"
        assert agent.status == AgentStatus.IDLE
        assert not agent.running

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_agent_start_stop(self):
        """Test agent start and stop"""
        config = AgentConfig(
            agent_id="agent_001",
            agent_name="Test Agent",
            role_type="coordinator"
        )

        agent = UnifiedAgent(config)

        # Start agent
        started = await agent.start()
        assert started
        assert agent.status == AgentStatus.RUNNING
        assert agent.running

        # Stop agent
        await agent.stop()
        assert agent.status == AgentStatus.STOPPED
        assert not agent.running

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_message_processing(self):
        """Test message processing"""
        config = AgentConfig(
            agent_id="agent_001",
            agent_name="Test Agent",
            role_type="data_scientist"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        # Create and send message
        message = Message(
            message_type="ANALYZE_DATA",
            sender_id="test_sender",
            content={"data": "test_data"}
        )

        success = await agent.process_message(message)
        assert agent.metrics['messages_received'] > 0

        await agent.stop()

    @pytest.mark.agent_system
    def test_agent_status_reporting(self):
        """Test agent status reporting"""
        config = AgentConfig(
            agent_id="agent_001",
            agent_name="Test Agent",
            role_type="portfolio_manager"
        )

        agent = UnifiedAgent(config)
        status = agent.get_status()

        assert status['agent_id'] == "agent_001"
        assert status['agent_name'] == "Test Agent"
        assert status['role_type'] == "portfolio_manager"
        assert 'metrics' in status

    @pytest.mark.agent_system
    def test_agent_metrics_collection(self):
        """Test agent metrics collection"""
        config = AgentConfig(
            agent_id="agent_001",
            agent_name="Test Agent",
            role_type="risk_analyst"
        )

        agent = UnifiedAgent(config)
        metrics = agent.get_metrics()

        assert 'messages_received' in metrics
        assert 'messages_processed' in metrics
        assert 'messages_failed' in metrics
        assert 'errors' in metrics


# ============================================================================
# MESSAGE TESTS
# ============================================================================

class TestMessage:
    """Test message system"""

    @pytest.mark.agent_system
    def test_message_creation(self):
        """Test message creation"""
        msg = Message(
            message_type="TEST",
            sender_id="agent_001",
            recipient_id="agent_002",
            content={"key": "value"}
        )

        assert msg.message_type == "TEST"
        assert msg.sender_id == "agent_001"
        assert msg.recipient_id == "agent_002"
        assert msg.content["key"] == "value"
        assert msg.timestamp is not None

    @pytest.mark.agent_system
    def test_message_to_dict(self):
        """Test message serialization"""
        msg = Message(
            message_type="TEST",
            sender_id="agent_001",
            content={"key": "value"}
        )

        msg_dict = msg.to_dict()

        assert msg_dict['type'] == "TEST"
        assert msg_dict['sender'] == "agent_001"
        assert msg_dict['content']['key'] == "value"


# ============================================================================
# ROLE PROVIDER TESTS
# ============================================================================

class TestRoleProvider:
    """Test role provider and factory"""

    @pytest.mark.agent_system
    def test_role_provider_initialization(self):
        """Test role provider initialization"""
        provider = RoleProvider()

        assert provider is not None
        available = provider.get_available_roles()
        assert len(available) == 23  # 8 core + 8 real + 7 hk

    @pytest.mark.agent_system
    def test_core_role_creation(self):
        """Test creation of core roles"""
        provider = RoleProvider()

        core_roles = [
            'coordinator', 'data_scientist', 'quantitative_analyst',
            'portfolio_manager', 'quantitative_engineer', 'quantitative_trader',
            'research_analyst', 'risk_analyst'
        ]

        for role_type in core_roles:
            role = provider.create_role(role_type)
            assert role is not None
            assert isinstance(role, BaseRole)

    @pytest.mark.agent_system
    def test_real_role_creation(self):
        """Test creation of real roles"""
        provider = RoleProvider()

        real_roles = [
            'real_data_scientist', 'real_quantitative_analyst',
            'real_portfolio_manager', 'real_quantitative_engineer',
            'real_quantitative_trader', 'real_research_analyst',
            'real_risk_analyst', 'real_data_analyzer'
        ]

        for role_type in real_roles:
            role = provider.create_role(role_type)
            assert role is not None
            assert isinstance(role, BaseRole)

    @pytest.mark.agent_system
    def test_hk_prompt_role_creation(self):
        """Test creation of HK prompt roles"""
        provider = RoleProvider()

        hk_roles = [
            'hk_data_scientist', 'hk_quantitative_analyst',
            'hk_portfolio_manager', 'hk_quantitative_engineer',
            'hk_quantitative_trader', 'hk_research_analyst',
            'hk_risk_analyst'
        ]

        for role_type in hk_roles:
            role = provider.create_role(role_type)
            assert role is not None
            assert isinstance(role, BaseRole)

    @pytest.mark.agent_system
    def test_unknown_role_creation(self):
        """Test creation of unknown role type"""
        provider = RoleProvider()

        role = provider.create_role("unknown_role")
        assert role is None

    @pytest.mark.agent_system
    def test_role_categorization(self):
        """Test role categorization"""
        provider = RoleProvider()

        categories = provider.list_roles_by_category()

        assert 'core' in categories
        assert 'real' in categories
        assert 'hk_prompt' in categories
        assert len(categories['core']) == 8
        assert len(categories['real']) == 8
        assert len(categories['hk_prompt']) == 7

    @pytest.mark.agent_system
    def test_custom_role_registration(self):
        """Test registering custom role"""
        provider = RoleProvider()

        class CustomRole(BaseRole):
            async def initialize(self, agent) -> bool:
                return True

            async def process_message(self, message, agent) -> bool:
                return True

            async def cleanup(self):
                pass

        provider.register_role("custom_role", CustomRole)

        available = provider.get_available_roles()
        assert "custom_role" in available

        role = provider.create_role("custom_role")
        assert role is not None


# ============================================================================
# CORE ROLES TESTS
# ============================================================================

class TestCoreRoles:
    """Test core agent role implementations"""

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_coordinator_role(self):
        """Test Coordinator role"""
        config = AgentConfig(
            agent_id="coordinator_001",
            agent_name="Coordinator",
            role_type="coordinator"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, CoordinatorRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_data_scientist_role(self):
        """Test DataScientist role"""
        config = AgentConfig(
            agent_id="ds_001",
            agent_name="Data Scientist",
            role_type="data_scientist"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, DataScientistRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_quantitative_analyst_role(self):
        """Test QuantitativeAnalyst role"""
        config = AgentConfig(
            agent_id="qa_001",
            agent_name="Quantitative Analyst",
            role_type="quantitative_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, QuantitativeAnalystRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_portfolio_manager_role(self):
        """Test PortfolioManager role"""
        config = AgentConfig(
            agent_id="pm_001",
            agent_name="Portfolio Manager",
            role_type="portfolio_manager"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, PortfolioManagerRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_quantitative_engineer_role(self):
        """Test QuantitativeEngineer role"""
        config = AgentConfig(
            agent_id="qe_001",
            agent_name="Quantitative Engineer",
            role_type="quantitative_engineer"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, QuantitativeEngineerRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_quantitative_trader_role(self):
        """Test QuantitativeTrader role"""
        config = AgentConfig(
            agent_id="qt_001",
            agent_name="Quantitative Trader",
            role_type="quantitative_trader"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, QuantitativeTraderRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_research_analyst_role(self):
        """Test ResearchAnalyst role"""
        config = AgentConfig(
            agent_id="ra_001",
            agent_name="Research Analyst",
            role_type="research_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, ResearchAnalystRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_risk_analyst_role(self):
        """Test RiskAnalyst role"""
        config = AgentConfig(
            agent_id="risk_001",
            agent_name="Risk Analyst",
            role_type="risk_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, RiskAnalystRole)

        await agent.stop()


# ============================================================================
# REAL ROLES TESTS
# ============================================================================

class TestRealRoles:
    """Test real agent role implementations with ML"""

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_real_data_scientist_role(self):
        """Test RealDataScientist role"""
        config = AgentConfig(
            agent_id="real_ds_001",
            agent_name="Real Data Scientist",
            role_type="real_data_scientist"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, RealDataScientistRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_real_quantitative_analyst_role(self):
        """Test RealQuantitativeAnalyst role"""
        config = AgentConfig(
            agent_id="real_qa_001",
            agent_name="Real Quantitative Analyst",
            role_type="real_quantitative_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, RealQuantitativeAnalystRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_real_data_analyzer_role(self):
        """Test RealDataAnalyzer role"""
        config = AgentConfig(
            agent_id="real_analyzer_001",
            agent_name="Real Data Analyzer",
            role_type="real_data_analyzer"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, RealDataAnalyzerRole)

        await agent.stop()


# ============================================================================
# HK PROMPT ROLES TESTS
# ============================================================================

class TestHKPromptRoles:
    """Test HK Prompt agent role implementations"""

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_hk_data_scientist_role(self):
        """Test HKDataScientist role"""
        config = AgentConfig(
            agent_id="hk_ds_001",
            agent_name="HK Data Scientist",
            role_type="hk_data_scientist"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, HKDataScientistRole)

        await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_hk_quantitative_analyst_role(self):
        """Test HKQuantitativeAnalyst role"""
        config = AgentConfig(
            agent_id="hk_qa_001",
            agent_name="HK Quantitative Analyst",
            role_type="hk_quantitative_analyst"
        )

        agent = UnifiedAgent(config)
        await agent.start()

        assert agent.role is not None
        assert isinstance(agent.role, HKQuantitativeAnalystRole)

        await agent.stop()


# ============================================================================
# MESSAGE QUEUE TESTS
# ============================================================================

class TestSimpleMessageQueue:
    """Test simple message queue"""

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_message_queue_operations(self):
        """Test message queue put and get"""
        queue = SimpleMessageQueue()

        # Put message
        msg = Message(
            message_type="TEST",
            sender_id="agent_001"
        )
        await queue.put(msg)

        # Get message
        retrieved = await queue.get(timeout=1.0)
        assert retrieved is not None
        assert retrieved.message_type == "TEST"

    @pytest.mark.agent_system
    def test_message_queue_empty(self):
        """Test message queue empty check"""
        queue = SimpleMessageQueue()

        assert queue.empty()

    @pytest.mark.agent_system
    def test_message_queue_size(self):
        """Test message queue size"""
        queue = SimpleMessageQueue()

        assert queue.size() == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestUnifiedAgentIntegration:
    """Integration tests for unified agent system"""

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_all_agent_types_startup(self):
        """Test that all 23 agent types can start"""
        provider = RoleProvider()
        all_roles = provider.get_available_roles()

        for role_type in all_roles:
            config = AgentConfig(
                agent_id=f"test_{role_type}",
                agent_name=f"Test {role_type}",
                role_type=role_type
            )

            agent = UnifiedAgent(config)
            started = await agent.start()
            assert started, f"Failed to start agent with role {role_type}"

            await agent.stop()

    @pytest.mark.agent_system
    @pytest.mark.asyncio
    async def test_multiple_agents_communication(self):
        """Test communication between multiple agents"""
        # Create coordinator
        coord_config = AgentConfig(
            agent_id="coordinator",
            agent_name="Main Coordinator",
            role_type="coordinator"
        )
        coordinator = UnifiedAgent(coord_config)
        await coordinator.start()

        # Create data scientist
        ds_config = AgentConfig(
            agent_id="data_scientist",
            agent_name="Main Data Scientist",
            role_type="data_scientist"
        )
        data_scientist = UnifiedAgent(ds_config)
        await data_scientist.start()

        # Send message from coordinator to data scientist
        await coordinator.send_message(
            "data_scientist",
            "ANALYZE_DATA",
            {"data": "test"}
        )

        # Stop agents
        await coordinator.stop()
        await data_scientist.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "agent_system"])
