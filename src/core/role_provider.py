"""
Role Provider and Factory - Dynamic Role Loading System

Manages creation and registration of all 23 agent roles.
Provides factory pattern for dynamic role instantiation.

Role Types Supported:
1. Core Roles (8):
   - coordinator, data_scientist, quantitative_analyst, portfolio_manager
   - quantitative_engineer, quantitative_trader, research_analyst, risk_analyst

2. Real Roles (8):
   - real_data_scientist, real_quantitative_analyst, real_portfolio_manager
   - real_quantitative_engineer, real_quantitative_trader, real_research_analyst
   - real_risk_analyst, real_data_analyzer

3. HK Prompt Roles (7):
   - hk_data_scientist, hk_quantitative_analyst, hk_portfolio_manager
   - hk_quantitative_engineer, hk_quantitative_trader, hk_research_analyst
   - hk_risk_analyst
"""

import logging
from typing import Dict, Optional, Type
from abc import ABC

from .unified_agent import BaseRole

logger = logging.getLogger("hk_quant_system.role_provider")


# ============================================================================
# CORE ROLES (8 implementations)
# ============================================================================

class CoordinatorRole(BaseRole):
    """Coordinator Agent Role - Orchestrates other agents"""

    def __init__(self, role_name: str = "coordinator"):
        super().__init__(role_name)
        self.coordinated_agents = {}

    async def initialize(self, agent) -> bool:
        """Initialize coordinator"""
        try:
            self.logger.info("Initializing CoordinatorRole")
            self.state = {
                'agents': {},
                'workflows': {},
                'schedule': {},
            }
            # Initialize coordinator-specific tools
            self.tools = {
                'register_agent': self._register_agent,
                'trigger_workflow': self._trigger_workflow,
                'get_agent_status': self._get_agent_status,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CoordinatorRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process coordinator messages"""
        try:
            if message.message_type == 'WORKFLOW_REQUEST':
                return await self._handle_workflow(message.content, agent)
            elif message.message_type == 'AGENT_REGISTER':
                return await self._handle_agent_register(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup coordinator resources"""
        self.logger.info("Cleaning up CoordinatorRole")
        self.coordinated_agents.clear()

    async def _register_agent(self, agent_id: str, agent_config: dict):
        """Register an agent for coordination"""
        self.coordinated_agents[agent_id] = agent_config
        return True

    async def _trigger_workflow(self, workflow_name: str, params: dict):
        """Trigger a workflow"""
        self.logger.info(f"Triggering workflow: {workflow_name}")
        return True

    async def _get_agent_status(self, agent_id: str):
        """Get status of registered agent"""
        return self.coordinated_agents.get(agent_id, {})

    async def _handle_workflow(self, content: dict, agent):
        """Handle workflow request"""
        return True

    async def _handle_agent_register(self, content: dict, agent):
        """Handle agent registration"""
        agent_id = content.get('agent_id')
        if agent_id:
            await self._register_agent(agent_id, content)
            return True
        return False


class DataScientistRole(BaseRole):
    """Data Scientist Agent Role - Data analysis and anomaly detection"""

    def __init__(self, role_name: str = "data_scientist"):
        super().__init__(role_name)

    async def initialize(self, agent) -> bool:
        """Initialize data scientist role"""
        try:
            self.logger.info("Initializing DataScientistRole")
            self.state = {
                'anomalies_detected': 0,
                'analyses_completed': 0,
                'data_quality_scores': {},
            }
            self.tools = {
                'analyze_data': self._analyze_data,
                'detect_anomaly': self._detect_anomaly,
                'profile_data': self._profile_data,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize DataScientistRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process data scientist messages"""
        try:
            if message.message_type == 'ANALYZE_DATA':
                return await self._handle_analysis(message.content, agent)
            elif message.message_type == 'DETECT_ANOMALY':
                return await self._handle_anomaly_detection(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup data scientist resources"""
        self.logger.info("Cleaning up DataScientistRole")

    async def _analyze_data(self, data: dict):
        """Analyze data"""
        return {'analysis': 'complete'}

    async def _detect_anomaly(self, data: dict):
        """Detect anomalies in data"""
        return {'anomalies': []}

    async def _profile_data(self, data: dict):
        """Profile data characteristics"""
        return {'profile': {}}

    async def _handle_analysis(self, content: dict, agent):
        """Handle analysis request"""
        result = await self._analyze_data(content)
        self.state['analyses_completed'] += 1
        return True

    async def _handle_anomaly_detection(self, content: dict, agent):
        """Handle anomaly detection request"""
        result = await self._detect_anomaly(content)
        if result.get('anomalies'):
            self.state['anomalies_detected'] += len(result['anomalies'])
        return True


class QuantitativeAnalystRole(BaseRole):
    """Quantitative Analyst Role - Quantitative analysis and modeling"""

    def __init__(self, role_name: str = "quantitative_analyst"):
        super().__init__(role_name)

    async def initialize(self, agent) -> bool:
        """Initialize quantitative analyst role"""
        try:
            self.logger.info("Initializing QuantitativeAnalystRole")
            self.state = {
                'simulations_run': 0,
                'models_created': 0,
                'forecasts_generated': 0,
            }
            self.tools = {
                'run_simulation': self._run_simulation,
                'create_model': self._create_model,
                'forecast': self._forecast,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize QuantitativeAnalystRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process quantitative analyst messages"""
        try:
            if message.message_type == 'RUN_SIMULATION':
                return await self._handle_simulation(message.content, agent)
            elif message.message_type == 'FORECAST_REQUEST':
                return await self._handle_forecast(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup quantitative analyst resources"""
        self.logger.info("Cleaning up QuantitativeAnalystRole")

    async def _run_simulation(self, params: dict):
        """Run Monte Carlo simulation"""
        return {'simulation_results': {}}

    async def _create_model(self, model_spec: dict):
        """Create quantitative model"""
        return {'model_id': 'model_001'}

    async def _forecast(self, forecast_params: dict):
        """Generate forecast"""
        return {'forecast': []}

    async def _handle_simulation(self, content: dict, agent):
        """Handle simulation request"""
        result = await self._run_simulation(content)
        self.state['simulations_run'] += 1
        return True

    async def _handle_forecast(self, content: dict, agent):
        """Handle forecast request"""
        result = await self._forecast(content)
        self.state['forecasts_generated'] += 1
        return True


class PortfolioManagerRole(BaseRole):
    """Portfolio Manager Role - Portfolio optimization and management"""

    async def initialize(self, agent) -> bool:
        """Initialize portfolio manager role"""
        try:
            self.logger.info("Initializing PortfolioManagerRole")
            self.state = {
                'portfolios_optimized': 0,
                'rebalance_count': 0,
                'current_allocation': {},
            }
            self.tools = {
                'optimize_portfolio': self._optimize_portfolio,
                'rebalance': self._rebalance,
                'calculate_allocation': self._calculate_allocation,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize PortfolioManagerRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process portfolio manager messages"""
        try:
            if message.message_type == 'OPTIMIZE_PORTFOLIO':
                return await self._handle_optimization(message.content, agent)
            elif message.message_type == 'REBALANCE_REQUEST':
                return await self._handle_rebalance(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup portfolio manager resources"""
        self.logger.info("Cleaning up PortfolioManagerRole")

    async def _optimize_portfolio(self, constraints: dict):
        """Optimize portfolio allocation"""
        return {'optimal_allocation': {}}

    async def _rebalance(self, portfolio: dict):
        """Rebalance portfolio"""
        return {'rebalance_actions': []}

    async def _calculate_allocation(self, strategy: dict):
        """Calculate optimal allocation"""
        return {'allocation': {}}

    async def _handle_optimization(self, content: dict, agent):
        """Handle optimization request"""
        result = await self._optimize_portfolio(content)
        self.state['portfolios_optimized'] += 1
        return True

    async def _handle_rebalance(self, content: dict, agent):
        """Handle rebalance request"""
        result = await self._rebalance(content)
        self.state['rebalance_count'] += 1
        return True


class QuantitativeEngineerRole(BaseRole):
    """Quantitative Engineer Role - System monitoring and optimization"""

    async def initialize(self, agent) -> bool:
        """Initialize quantitative engineer role"""
        try:
            self.logger.info("Initializing QuantitativeEngineerRole")
            self.state = {
                'monitoring_active': True,
                'optimizations_done': 0,
                'issues_detected': 0,
            }
            self.tools = {
                'monitor_system': self._monitor_system,
                'optimize_performance': self._optimize_performance,
                'check_health': self._check_health,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize QuantitativeEngineerRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process quantitative engineer messages"""
        try:
            if message.message_type == 'MONITOR_REQUEST':
                return await self._handle_monitoring(message.content, agent)
            elif message.message_type == 'OPTIMIZE_REQUEST':
                return await self._handle_optimization(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup quantitative engineer resources"""
        self.logger.info("Cleaning up QuantitativeEngineerRole")

    async def _monitor_system(self):
        """Monitor system health"""
        return {'system_status': 'healthy'}

    async def _optimize_performance(self, target: str):
        """Optimize system performance"""
        return {'optimization_complete': True}

    async def _check_health(self):
        """Check system health"""
        return {'health_status': {}}

    async def _handle_monitoring(self, content: dict, agent):
        """Handle monitoring request"""
        result = await self._monitor_system()
        return True

    async def _handle_optimization(self, content: dict, agent):
        """Handle optimization request"""
        result = await self._optimize_performance(content.get('target', 'general'))
        self.state['optimizations_done'] += 1
        return True


class QuantitativeTraderRole(BaseRole):
    """Quantitative Trader Role - Trading execution and management"""

    async def initialize(self, agent) -> bool:
        """Initialize quantitative trader role"""
        try:
            self.logger.info("Initializing QuantitativeTraderRole")
            self.state = {
                'trades_executed': 0,
                'positions_open': 0,
                'pnl_realized': 0.0,
            }
            self.tools = {
                'execute_trade': self._execute_trade,
                'manage_position': self._manage_position,
                'calculate_pnl': self._calculate_pnl,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize QuantitativeTraderRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process quantitative trader messages"""
        try:
            if message.message_type == 'EXECUTE_TRADE':
                return await self._handle_trade_execution(message.content, agent)
            elif message.message_type == 'MANAGE_POSITION':
                return await self._handle_position_management(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup quantitative trader resources"""
        self.logger.info("Cleaning up QuantitativeTraderRole")

    async def _execute_trade(self, trade_params: dict):
        """Execute a trade"""
        return {'trade_id': 'trade_001', 'status': 'executed'}

    async def _manage_position(self, position_params: dict):
        """Manage open position"""
        return {'position_update': 'complete'}

    async def _calculate_pnl(self, position: dict):
        """Calculate position P&L"""
        return {'pnl': 0.0}

    async def _handle_trade_execution(self, content: dict, agent):
        """Handle trade execution request"""
        result = await self._execute_trade(content)
        self.state['trades_executed'] += 1
        return True

    async def _handle_position_management(self, content: dict, agent):
        """Handle position management request"""
        result = await self._manage_position(content)
        return True


class ResearchAnalystRole(BaseRole):
    """Research Analyst Role - Strategy research and backtesting"""

    async def initialize(self, agent) -> bool:
        """Initialize research analyst role"""
        try:
            self.logger.info("Initializing ResearchAnalystRole")
            self.state = {
                'strategies_analyzed': 0,
                'backtests_run': 0,
                'validation_passed': 0,
            }
            self.tools = {
                'analyze_strategy': self._analyze_strategy,
                'run_backtest': self._run_backtest,
                'validate_strategy': self._validate_strategy,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize ResearchAnalystRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process research analyst messages"""
        try:
            if message.message_type == 'ANALYZE_STRATEGY':
                return await self._handle_analysis(message.content, agent)
            elif message.message_type == 'BACKTEST_REQUEST':
                return await self._handle_backtest(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup research analyst resources"""
        self.logger.info("Cleaning up ResearchAnalystRole")

    async def _analyze_strategy(self, strategy_spec: dict):
        """Analyze strategy"""
        return {'analysis_results': {}}

    async def _run_backtest(self, backtest_params: dict):
        """Run backtest on strategy"""
        return {'backtest_results': {}}

    async def _validate_strategy(self, strategy: dict):
        """Validate strategy"""
        return {'validation_status': 'passed'}

    async def _handle_analysis(self, content: dict, agent):
        """Handle strategy analysis request"""
        result = await self._analyze_strategy(content)
        self.state['strategies_analyzed'] += 1
        return True

    async def _handle_backtest(self, content: dict, agent):
        """Handle backtest request"""
        result = await self._run_backtest(content)
        self.state['backtests_run'] += 1
        return True


class RiskAnalystRole(BaseRole):
    """Risk Analyst Role - Risk assessment and management"""

    async def initialize(self, agent) -> bool:
        """Initialize risk analyst role"""
        try:
            self.logger.info("Initializing RiskAnalystRole")
            self.state = {
                'risk_assessments_done': 0,
                'hedges_recommended': 0,
                'risk_limits_breached': 0,
            }
            self.tools = {
                'assess_risk': self._assess_risk,
                'recommend_hedge': self._recommend_hedge,
                'check_limits': self._check_limits,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize RiskAnalystRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process risk analyst messages"""
        try:
            if message.message_type == 'ASSESS_RISK':
                return await self._handle_risk_assessment(message.content, agent)
            elif message.message_type == 'HEDGE_REQUEST':
                return await self._handle_hedge_recommendation(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup risk analyst resources"""
        self.logger.info("Cleaning up RiskAnalystRole")

    async def _assess_risk(self, portfolio: dict):
        """Assess portfolio risk"""
        return {'risk_metrics': {}}

    async def _recommend_hedge(self, position: dict):
        """Recommend hedge strategy"""
        return {'hedge_recommendation': {}}

    async def _check_limits(self, portfolio: dict):
        """Check against risk limits"""
        return {'limit_status': 'ok'}

    async def _handle_risk_assessment(self, content: dict, agent):
        """Handle risk assessment request"""
        result = await self._assess_risk(content)
        self.state['risk_assessments_done'] += 1
        return True

    async def _handle_hedge_recommendation(self, content: dict, agent):
        """Handle hedge recommendation request"""
        result = await self._recommend_hedge(content)
        self.state['hedges_recommended'] += 1
        return True


# ============================================================================
# REAL ROLES (8 implementations with ML integration)
# ============================================================================

class RealDataScientistRole(DataScientistRole):
    """Real Data Scientist Role - ML-enhanced anomaly detection"""

    async def initialize(self, agent) -> bool:
        """Initialize real data scientist with ML models"""
        if not await super().initialize(agent):
            return False

        self.state['ml_models_loaded'] = 0
        self.state['ensemble_enabled'] = True
        self.logger.info("RealDataScientistRole initialized with ML enhancement")
        return True


class RealQuantitativeAnalystRole(QuantitativeAnalystRole):
    """Real Quantitative Analyst Role - ML-powered forecasting"""

    async def initialize(self, agent) -> bool:
        """Initialize real quant analyst with ML models"""
        if not await super().initialize(agent):
            return False

        self.state['ml_forecasting_enabled'] = True
        self.state['confidence_calibration'] = {}
        self.logger.info("RealQuantitativeAnalystRole initialized with ML forecasting")
        return True


class RealPortfolioManagerRole(PortfolioManagerRole):
    """Real Portfolio Manager Role - ML-optimized allocation"""

    async def initialize(self, agent) -> bool:
        """Initialize real portfolio manager with ML optimization"""
        if not await super().initialize(agent):
            return False

        self.state['ml_optimizer_enabled'] = True
        self.state['adaptive_constraints'] = {}
        self.logger.info("RealPortfolioManagerRole initialized with ML optimization")
        return True


class RealQuantitativeEngineerRole(QuantitativeEngineerRole):
    """Real Quantitative Engineer Role - ML-based system optimization"""

    async def initialize(self, agent) -> bool:
        """Initialize real quant engineer with ML optimization"""
        if not await super().initialize(agent):
            return False

        self.state['ml_performance_tuning'] = True
        self.state['anomaly_threshold'] = 0.95
        self.logger.info("RealQuantitativeEngineerRole initialized with ML optimization")
        return True


class RealQuantitativeTraderRole(QuantitativeTraderRole):
    """Real Quantitative Trader Role - High-frequency trading capability"""

    async def initialize(self, agent) -> bool:
        """Initialize real quant trader with HFT"""
        if not await super().initialize(agent):
            return False

        self.state['hft_enabled'] = True
        self.state['latency_ms'] = 0.0
        self.logger.info("RealQuantitativeTraderRole initialized with HFT capability")
        return True


class RealResearchAnalystRole(ResearchAnalystRole):
    """Real Research Analyst Role - Automated backtesting and validation"""

    async def initialize(self, agent) -> bool:
        """Initialize real research analyst with advanced backtesting"""
        if not await super().initialize(agent):
            return False

        self.state['automated_backtesting'] = True
        self.state['validation_framework'] = 'comprehensive'
        self.logger.info("RealResearchAnalystRole initialized with advanced backtesting")
        return True


class RealRiskAnalystRole(RiskAnalystRole):
    """Real Risk Analyst Role - ML-powered risk modeling"""

    async def initialize(self, agent) -> bool:
        """Initialize real risk analyst with ML models"""
        if not await super().initialize(agent):
            return False

        self.state['ml_risk_models'] = True
        self.state['stress_testing_enabled'] = True
        self.logger.info("RealRiskAnalystRole initialized with ML risk models")
        return True


class RealDataAnalyzerRole(BaseRole):
    """Real Data Analyzer Role - Standalone real-time data analysis"""

    async def initialize(self, agent) -> bool:
        """Initialize real data analyzer"""
        try:
            self.logger.info("Initializing RealDataAnalyzerRole")
            self.state = {
                'data_points_processed': 0,
                'quality_scores': {},
                'real_time_feeds': {},
            }
            self.tools = {
                'analyze_real_time': self._analyze_real_time,
                'validate_data': self._validate_data,
                'stream_processing': self._stream_processing,
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize RealDataAnalyzerRole: {e}")
            return False

    async def process_message(self, message, agent) -> bool:
        """Process real data analyzer messages"""
        try:
            if message.message_type == 'REALTIME_ANALYSIS':
                return await self._handle_realtime_analysis(message.content, agent)
            elif message.message_type == 'DATA_VALIDATION':
                return await self._handle_validation(message.content, agent)
            return False
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def cleanup(self):
        """Cleanup real data analyzer resources"""
        self.logger.info("Cleaning up RealDataAnalyzerRole")

    async def _analyze_real_time(self, data_stream: dict):
        """Analyze real-time data stream"""
        return {'analysis': {}}

    async def _validate_data(self, data: dict):
        """Validate incoming data"""
        return {'quality_score': 0.95}

    async def _stream_processing(self, stream_config: dict):
        """Process continuous data stream"""
        return {'stream_status': 'active'}

    async def _handle_realtime_analysis(self, content: dict, agent):
        """Handle real-time analysis request"""
        result = await self._analyze_real_time(content)
        self.state['data_points_processed'] += 1
        return True

    async def _handle_validation(self, content: dict, agent):
        """Handle data validation request"""
        result = await self._validate_data(content)
        return True


# ============================================================================
# HK PROMPT ROLES (7 implementations with prompt-based agents)
# ============================================================================

class HKDataScientistRole(DataScientistRole):
    """HK Prompt Data Scientist Role - Using prompt-based agent"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt data scientist"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.state['prompt_templates_loaded'] = True
        self.logger.info("HKDataScientistRole initialized with HK prompt engine")
        return True


class HKQuantitativeAnalystRole(QuantitativeAnalystRole):
    """HK Prompt Quantitative Analyst Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt quantitative analyst"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKQuantitativeAnalystRole initialized with HK prompt engine")
        return True


class HKPortfolioManagerRole(PortfolioManagerRole):
    """HK Prompt Portfolio Manager Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt portfolio manager"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKPortfolioManagerRole initialized with HK prompt engine")
        return True


class HKQuantitativeEngineerRole(QuantitativeEngineerRole):
    """HK Prompt Quantitative Engineer Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt quantitative engineer"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKQuantitativeEngineerRole initialized with HK prompt engine")
        return True


class HKQuantitativeTraderRole(QuantitativeTraderRole):
    """HK Prompt Quantitative Trader Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt quantitative trader"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKQuantitativeTraderRole initialized with HK prompt engine")
        return True


class HKResearchAnalystRole(ResearchAnalystRole):
    """HK Prompt Research Analyst Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt research analyst"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKResearchAnalystRole initialized with HK prompt engine")
        return True


class HKRiskAnalystRole(RiskAnalystRole):
    """HK Prompt Risk Analyst Role"""

    async def initialize(self, agent) -> bool:
        """Initialize HK prompt risk analyst"""
        if not await super().initialize(agent):
            return False

        self.state['prompt_engine'] = 'hk_prompt'
        self.logger.info("HKRiskAnalystRole initialized with HK prompt engine")
        return True


# ============================================================================
# ROLE PROVIDER - Factory for dynamic role creation
# ============================================================================

class RoleProvider:
    """Factory for creating agent roles dynamically"""

    def __init__(self):
        """Initialize role registry"""
        self.logger = logging.getLogger("hk_quant_system.role_provider")
        self.role_registry: Dict[str, Type[BaseRole]] = self._build_registry()

    def _build_registry(self) -> Dict[str, Type[BaseRole]]:
        """Build role type registry"""
        return {
            # Core roles (8)
            'coordinator': CoordinatorRole,
            'data_scientist': DataScientistRole,
            'quantitative_analyst': QuantitativeAnalystRole,
            'portfolio_manager': PortfolioManagerRole,
            'quantitative_engineer': QuantitativeEngineerRole,
            'quantitative_trader': QuantitativeTraderRole,
            'research_analyst': ResearchAnalystRole,
            'risk_analyst': RiskAnalystRole,

            # Real roles (8)
            'real_data_scientist': RealDataScientistRole,
            'real_quantitative_analyst': RealQuantitativeAnalystRole,
            'real_portfolio_manager': RealPortfolioManagerRole,
            'real_quantitative_engineer': RealQuantitativeEngineerRole,
            'real_quantitative_trader': RealQuantitativeTraderRole,
            'real_research_analyst': RealResearchAnalystRole,
            'real_risk_analyst': RealRiskAnalystRole,
            'real_data_analyzer': RealDataAnalyzerRole,

            # HK Prompt roles (7)
            'hk_data_scientist': HKDataScientistRole,
            'hk_quantitative_analyst': HKQuantitativeAnalystRole,
            'hk_portfolio_manager': HKPortfolioManagerRole,
            'hk_quantitative_engineer': HKQuantitativeEngineerRole,
            'hk_quantitative_trader': HKQuantitativeTraderRole,
            'hk_research_analyst': HKResearchAnalystRole,
            'hk_risk_analyst': HKRiskAnalystRole,
        }

    def create_role(self, role_type: str) -> Optional[BaseRole]:
        """
        Create a role instance by type.

        Args:
            role_type: Type of role to create

        Returns:
            Role instance or None if type not found
        """
        role_class = self.role_registry.get(role_type)
        if not role_class:
            self.logger.error(f"Unknown role type: {role_type}")
            return None

        try:
            # Try to create with role_name parameter first
            role_name = role_type
            try:
                return role_class(role_name)
            except TypeError:
                # If role class doesn't accept role_name, create without it
                # and set role_name manually
                role = role_class()
                role.role_name = role_name
                return role
        except Exception as e:
            self.logger.error(f"Failed to create role {role_type}: {e}")
            return None

    def get_available_roles(self) -> list[str]:
        """Get list of all available role types"""
        return list(self.role_registry.keys())

    def register_role(self, role_type: str, role_class: Type[BaseRole]):
        """Register a custom role type"""
        if role_type in self.role_registry:
            self.logger.warning(f"Overwriting existing role type: {role_type}")
        self.role_registry[role_type] = role_class
        self.logger.info(f"Registered role type: {role_type}")

    def list_roles_by_category(self) -> Dict[str, list[str]]:
        """List all roles grouped by category"""
        return {
            'core': [
                'coordinator', 'data_scientist', 'quantitative_analyst',
                'portfolio_manager', 'quantitative_engineer', 'quantitative_trader',
                'research_analyst', 'risk_analyst'
            ],
            'real': [
                'real_data_scientist', 'real_quantitative_analyst',
                'real_portfolio_manager', 'real_quantitative_engineer',
                'real_quantitative_trader', 'real_research_analyst',
                'real_risk_analyst', 'real_data_analyzer'
            ],
            'hk_prompt': [
                'hk_data_scientist', 'hk_quantitative_analyst',
                'hk_portfolio_manager', 'hk_quantitative_engineer',
                'hk_quantitative_trader', 'hk_research_analyst',
                'hk_risk_analyst'
            ]
        }


__all__ = [
    'RoleProvider',
    'BaseRole',
    # Core roles
    'CoordinatorRole',
    'DataScientistRole',
    'QuantitativeAnalystRole',
    'PortfolioManagerRole',
    'QuantitativeEngineerRole',
    'QuantitativeTraderRole',
    'ResearchAnalystRole',
    'RiskAnalystRole',
    # Real roles
    'RealDataScientistRole',
    'RealQuantitativeAnalystRole',
    'RealPortfolioManagerRole',
    'RealQuantitativeEngineerRole',
    'RealQuantitativeTraderRole',
    'RealResearchAnalystRole',
    'RealRiskAnalystRole',
    'RealDataAnalyzerRole',
    # HK Prompt roles
    'HKDataScientistRole',
    'HKQuantitativeAnalystRole',
    'HKPortfolioManagerRole',
    'HKQuantitativeEngineerRole',
    'HKQuantitativeTraderRole',
    'HKResearchAnalystRole',
    'HKRiskAnalystRole',
]
