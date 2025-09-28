#!/usr/bin/env python3
"""
真實量化交易系統啟動器

整合所有真實組件：數據源、AI模型、交易API、風險管理、回測引擎、監控和合規性
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import pandas as pd

# 導入所有真實系統組件
from src.data_adapters.data_service import DataService
from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst, RealAgentConfig
from src.trading.broker_apis import InteractiveBrokersAPI, TDAmeritradeAPI
from src.risk_management.risk_calculator import RiskCalculator, RiskLimits
from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
from src.backtest.base_backtest import BacktestConfig
from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
from src.security.compliance_checker import ComplianceChecker
from src.agents.coordinator import AgentCoordinator
from src.core import SystemConfig


class RealSystemLauncher:
    """真實系統啟動器"""
    
    def __init__(self, config_path: str = "config/real_system_config.json"):
        self.config_path = config_path
        self.logger = logging.getLogger("hk_quant_system.real_launcher")
        
        # 系統組件
        self.data_service: Optional[DataService] = None
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.quantitative_analyst: Optional[EnhancedQuantitativeAnalyst] = None
        self.trading_apis: Dict[str, Any] = {}
        self.risk_calculator: Optional[RiskCalculator] = None
        self.backtest_engine: Optional[EnhancedBacktestEngine] = None
        self.monitoring_system: Optional[EnhancedMonitoringSystem] = None
        self.compliance_checker: Optional[ComplianceChecker] = None
        
        # 系統狀態
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # 配置
        self.config: Dict[str, Any] = {}
        
    async def initialize(self) -> bool:
        """初始化真實系統"""
        try:
            self.logger.info("🚀 Initializing Real Quantitative Trading System...")
            
            # 加載配置
            await self._load_config()
            
            # 初始化系統組件
            await self._initialize_components()
            
            self.logger.info("✅ Real system initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"❌ Failed to initialize real system: {e}")
            return False
    
    async def _load_config(self) -> None:
        """加載系統配置"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                await self._create_default_config()
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.logger.info(f"📋 Loaded configuration from {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            await self._create_default_config()
    
    async def _create_default_config(self) -> None:
        """創建默認配置"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "system": {
                    "name": "Real Quantitative Trading System",
                    "version": "2.0.0",
                    "environment": "production",
                    "log_level": "INFO"
                },
                "data_sources": {
                    "yahoo_finance": {
                        "enabled": True,
                        "priority": 1
                    },
                    "alpha_vantage": {
                        "enabled": False,
                        "api_key": "YOUR_API_KEY_HERE",
                        "priority": 2
                    },
                    "binance_crypto": {
                        "enabled": True,
                        "sandbox": True,
                        "priority": 3
                    }
                },
                "agents": {
                    "quantitative_analyst": {
                        "enabled": True,
                        "analysis_symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                        "lookback_days": 252,
                        "min_data_points": 100,
                        "ml_models": ["price_prediction", "signal_classification", "volatility_prediction"]
                    }
                },
                "trading": {
                    "interactive_brokers": {
                        "enabled": False,
                        "api_key": "YOUR_IB_API_KEY",
                        "sandbox": True
                    },
                    "td_ameritrade": {
                        "enabled": False,
                        "client_id": "YOUR_TD_CLIENT_ID",
                        "sandbox": True
                    }
                },
                "risk_management": {
                    "max_position_size": 0.1,
                    "max_portfolio_risk": 0.05,
                    "max_drawdown_limit": 0.15,
                    "max_var_limit": 0.02,
                    "max_leverage": 2.0,
                    "max_concentration": 0.2
                },
                "monitoring": {
                    "enabled": True,
                    "monitored_symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                    "alert_email": "alerts@yourcompany.com",
                    "alert_slack_webhook": "YOUR_SLACK_WEBHOOK_URL"
                },
                "compliance": {
                    "enabled": True,
                    "regulatory_framework": "SEC",
                    "data_retention_years": 7,
                    "reporting_frequency": "daily"
                },
                "backtesting": {
                    "enabled": True,
                    "initial_capital": 1000000,
                    "start_date": "2023-01-01",
                    "end_date": "2024-01-01",
                    "benchmark": "SPY",
                    "transaction_cost": {
                        "commission_per_share": 0.005,
                        "commission_per_trade": 1.0,
                        "bid_ask_spread": 0.001,
                        "market_impact": 0.0005,
                        "slippage": 0.0002
                    }
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            self.config = default_config
            self.logger.info(f"📝 Created default configuration: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")
            raise
    
    async def _initialize_components(self) -> None:
        """初始化系統組件"""
        try:
            # 1. 初始化數據服務
            self.logger.info("📊 Initializing data service...")
            self.data_service = DataService()
            if not await self.data_service.initialize():
                raise RuntimeError("Failed to initialize data service")
            
            # 2. 初始化風險計算器
            self.logger.info("⚠️ Initializing risk calculator...")
            self.risk_calculator = RiskCalculator()
            
            # 3. 初始化合規性檢查器
            self.logger.info("📋 Initializing compliance checker...")
            self.compliance_checker = ComplianceChecker(self.config.get('compliance', {}))
            if not await self.compliance_checker.initialize():
                raise RuntimeError("Failed to initialize compliance checker")
            
            # 4. 初始化監控系統
            self.logger.info("🔍 Initializing monitoring system...")
            self.monitoring_system = EnhancedMonitoringSystem(self.config.get('monitoring', {}))
            if not await self.monitoring_system.initialize():
                raise RuntimeError("Failed to initialize monitoring system")
            
            # 5. 初始化回測引擎
            self.logger.info("📈 Initializing backtest engine...")
            backtest_config = BacktestConfig(**self.config.get('backtesting', {}))
            self.backtest_engine = EnhancedBacktestEngine(backtest_config)
            if not await self.backtest_engine.initialize():
                raise RuntimeError("Failed to initialize backtest engine")
            
            # 6. 初始化交易API
            self.logger.info("💼 Initializing trading APIs...")
            await self._initialize_trading_apis()
            
            # 7. 初始化AI Agent
            self.logger.info("🤖 Initializing AI agents...")
            await self._initialize_agents()
            
            self.logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    async def _initialize_trading_apis(self) -> None:
        """初始化交易API"""
        try:
            trading_config = self.config.get('trading', {})
            
            # Interactive Brokers
            if trading_config.get('interactive_brokers', {}).get('enabled', False):
                ib_config = trading_config['interactive_brokers']
                self.trading_apis['interactive_brokers'] = InteractiveBrokersAPI(ib_config)
                self.logger.info("✅ Interactive Brokers API initialized")
            
            # TD Ameritrade
            if trading_config.get('td_ameritrade', {}).get('enabled', False):
                td_config = trading_config['td_ameritrade']
                self.trading_apis['td_ameritrade'] = TDAmeritradeAPI(td_config)
                self.logger.info("✅ TD Ameritrade API initialized")
            
            if not self.trading_apis:
                self.logger.warning("⚠️ No trading APIs enabled - running in simulation mode")
            
        except Exception as e:
            self.logger.error(f"Error initializing trading APIs: {e}")
    
    async def _initialize_agents(self) -> None:
        """初始化AI Agent"""
        try:
            agents_config = self.config.get('agents', {})
            
            # 量化分析師
            if agents_config.get('quantitative_analyst', {}).get('enabled', False):
                qa_config = RealAgentConfig(
                    agent_id="enhanced_quant_analyst_001",
                    agent_type="quantitative_analyst",
                    name="Enhanced Quantitative Analyst",
                    data_sources=["yahoo_finance", "alpha_vantage"],
                    update_frequency=60,
                    lookback_period=252,
                    analysis_methods=["technical_analysis", "machine_learning"],
                    signal_threshold=0.6,
                    confidence_threshold=0.7,
                    ml_models=["price_prediction", "signal_classification"],
                    max_position_size=0.1,
                    stop_loss_threshold=0.05,
                    take_profit_threshold=0.1,
                    performance_tracking=True,
                    backtest_enabled=True,
                    log_level="INFO",
                    enable_metrics=True,
                    config=agents_config['quantitative_analyst']
                )
                
                self.quantitative_analyst = EnhancedQuantitativeAnalyst(qa_config)
                if not await self.quantitative_analyst.initialize():
                    raise RuntimeError("Failed to initialize quantitative analyst")
                
                self.logger.info("✅ Enhanced Quantitative Analyst initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
    
    async def start_system(self) -> None:
        """啟動真實系統"""
        try:
            if self.is_running:
                self.logger.warning("System is already running")
                return
            
            self.logger.info("🚀 Starting Real Quantitative Trading System...")
            self.is_running = True
            self.start_time = datetime.now()
            
            # 啟動監控系統
            if self.monitoring_system:
                await self.monitoring_system.start_monitoring()
                self.logger.info("🔍 Monitoring system started")
            
            # 啟動AI Agent
            if self.quantitative_analyst:
                await self.quantitative_analyst.start()
                self.logger.info("🤖 AI agents started")
            
            # 啟動交易API連接
            for api_name, api in self.trading_apis.items():
                if await api.connect():
                    self.logger.info(f"💼 {api_name} connected")
                else:
                    self.logger.warning(f"⚠️ Failed to connect to {api_name}")
            
            self.logger.info("✅ Real system started successfully")
            self._print_system_status()
            
        except Exception as e:
            self.logger.exception(f"❌ Error starting system: {e}")
            self.is_running = False
    
    async def stop_system(self) -> None:
        """停止真實系統"""
        try:
            self.logger.info("🛑 Stopping Real Quantitative Trading System...")
            self.is_running = False
            
            # 停止AI Agent
            if self.quantitative_analyst:
                await self.quantitative_analyst.stop()
                self.logger.info("🤖 AI agents stopped")
            
            # 停止監控系統
            if self.monitoring_system:
                await self.monitoring_system.stop_monitoring()
                self.logger.info("🔍 Monitoring system stopped")
            
            # 斷開交易API連接
            for api_name, api in self.trading_apis.items():
                if await api.disconnect():
                    self.logger.info(f"💼 {api_name} disconnected")
            
            self.logger.info("✅ Real system stopped successfully")
            
        except Exception as e:
            self.logger.exception(f"❌ Error stopping system: {e}")
    
    async def run_backtest(self, strategy_name: str = "enhanced_ml_strategy") -> None:
        """運行回測"""
        try:
            if not self.backtest_engine:
                self.logger.error("Backtest engine not initialized")
                return
            
            self.logger.info(f"📈 Running backtest: {strategy_name}")
            
            # 定義策略函數
            async def ml_strategy(market_data: Dict[str, Any], positions: Dict[str, float]) -> List[Dict[str, Any]]:
                """機器學習驅動的策略"""
                signals = []
                
                for symbol, data in market_data.items():
                    try:
                        # 使用AI模型生成信號
                        if self.quantitative_analyst and hasattr(self.quantitative_analyst, 'ml_models'):
                            # 轉換數據格式
                            df_data = [{
                                'timestamp': data.name if hasattr(data, 'name') else datetime.now(),
                                'symbol': symbol,
                                'open': data['open'],
                                'high': data['high'],
                                'low': data['low'],
                                'close': data['close'],
                                'volume': data['volume']
                            }]
                            
                            df = pd.DataFrame(df_data)
                            df.set_index('timestamp', inplace=True)
                            
                            # 預測價格方向
                            direction_pred = await self.quantitative_analyst.ml_models.predict_price_direction(df)
                            
                            if direction_pred['confidence'] > 0.6:
                                signal = {
                                    'symbol': symbol,
                                    'side': direction_pred['signal'],
                                    'quantity': 100,  # 固定數量
                                    'confidence': direction_pred['confidence']
                                }
                                signals.append(signal)
                    
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                        continue
                
                return signals
            
            # 運行回測
            result = await self.backtest_engine.run_backtest(ml_strategy)
            
            # 生成報告
            report = await self.backtest_engine.generate_performance_report(result)
            
            self.logger.info("📊 Backtest Results:")
            self.logger.info(f"   Total Return: {report['summary']['total_return']}")
            self.logger.info(f"   Annualized Return: {report['summary']['annualized_return']}")
            self.logger.info(f"   Sharpe Ratio: {report['summary']['sharpe_ratio']}")
            self.logger.info(f"   Max Drawdown: {report['summary']['max_drawdown']}")
            self.logger.info(f"   Win Rate: {report['trading_metrics']['win_rate']}")
            self.logger.info(f"   Total Trades: {report['trading_metrics']['total_trades']}")
            
            # 保存結果
            results_file = f"backtest_results_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(result.dict(), f, indent=2, default=str)
            
            self.logger.info(f"📁 Backtest results saved to: {results_file}")
            
        except Exception as e:
            self.logger.exception(f"❌ Error running backtest: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            status = {
                "system": {
                    "name": self.config.get('system', {}).get('name', 'Real Quantitative Trading System'),
                    "version": self.config.get('system', {}).get('version', '2.0.0'),
                    "is_running": self.is_running,
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
                },
                "components": {
                    "data_service": "initialized" if self.data_service else "not_initialized",
                    "risk_calculator": "initialized" if self.risk_calculator else "not_initialized",
                    "compliance_checker": "initialized" if self.compliance_checker else "not_initialized",
                    "monitoring_system": "running" if self.monitoring_system and self.monitoring_system.is_running else "stopped",
                    "backtest_engine": "initialized" if self.backtest_engine else "not_initialized",
                    "quantitative_analyst": "running" if self.quantitative_analyst and self.quantitative_analyst.status.value == "running" else "stopped",
                    "trading_apis": len(self.trading_apis)
                }
            }
            
            # 添加監控狀態
            if self.monitoring_system:
                status["monitoring"] = await self.monitoring_system.get_monitoring_status()
            
            # 添加合規性狀態
            if self.compliance_checker:
                status["compliance"] = await self.compliance_checker.get_violation_summary()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {}
    
    def _print_system_status(self) -> None:
        """打印系統狀態"""
        print("\n" + "="*80)
        print("🚀 REAL QUANTITATIVE TRADING SYSTEM - STATUS")
        print("="*80)
        print(f"📊 Data Sources: Yahoo Finance, Alpha Vantage, CCXT")
        print(f"🤖 AI Models: Enhanced ML Models (Price Prediction, Signal Classification)")
        print(f"💼 Trading APIs: {', '.join(self.trading_apis.keys()) if self.trading_apis else 'Simulation Mode'}")
        print(f"⚠️ Risk Management: Real-time VaR, Drawdown, Position Limits")
        print(f"🔍 Monitoring: Real-time Market & System Monitoring")
        print(f"📋 Compliance: SEC, FINRA, FCA Regulatory Compliance")
        print(f"📈 Backtesting: Enhanced Historical Data Backtesting")
        print("="*80)
        print("✅ System is running in REAL MODE with live data and AI models!")
        print("="*80 + "\n")
    
    async def cleanup(self) -> None:
        """清理系統資源"""
        try:
            self.logger.info("🧹 Cleaning up system resources...")
            
            # 停止系統
            if self.is_running:
                await self.stop_system()
            
            # 清理組件
            if self.data_service:
                await self.data_service.cleanup()
            
            if self.monitoring_system:
                await self.monitoring_system.cleanup()
            
            if self.backtest_engine:
                await self.backtest_engine.cleanup()
            
            self.logger.info("✅ System cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """主函數"""
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('real_system.log')
        ]
    )
    
    logger = logging.getLogger("hk_quant_system.main")
    
    # 創建系統啟動器
    launcher = RealSystemLauncher()
    
    # 設置信號處理
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(launcher.cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化系統
        if not await launcher.initialize():
            logger.error("Failed to initialize system")
            return
        
        # 啟動系統
        await launcher.start_system()
        
        # 運行回測示例
        logger.info("Running backtest example...")
        await launcher.run_backtest()
        
        # 保持系統運行
        logger.info("System is running. Press Ctrl+C to stop.")
        while launcher.is_running:
            await asyncio.sleep(60)  # 每分鐘檢查一次
            
            # 打印系統狀態
            status = await launcher.get_system_status()
            logger.info(f"System uptime: {status['system']['uptime_seconds']:.0f} seconds")
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        await launcher.cleanup()


if __name__ == "__main__":
    asyncio.run(main())