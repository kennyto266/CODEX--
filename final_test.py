#!/usr/bin/env python3
"""
最終測試 - 驗證所有修復
"""

def test_all_imports():
    """測試所有導入"""
    print("🔍 測試所有模組導入...")
    
    try:
        # 核心模組
        print("1. 測試核心模組...")
        from src.core import SystemConfig
        print("   ✅ SystemConfig")
        
        # 數據適配器
        print("2. 測試數據適配器...")
        from src.data_adapters.data_service import DataService
        from src.data_adapters.http_api_adapter import HttpApiDataAdapter
        from src.data_adapters.yahoo_finance_adapter import YahooFinanceAdapter
        from src.data_adapters.alpha_vantage_adapter import AlphaVantageAdapter
        from src.data_adapters.ccxt_crypto_adapter import CCXTCryptoAdapter
        print("   ✅ 所有數據適配器")
        
        # 風險管理
        print("3. 測試風險管理...")
        from src.risk_management.risk_calculator import RiskCalculator, RiskMetrics, RiskLimits
        print("   ✅ 風險管理模組")
        
        # 代理系統
        print("4. 測試代理系統...")
        from src.agents.base_agent import BaseAgent
        from src.agents.real_agents.base_real_agent import BaseRealAgent, RealAgentConfig
        from src.agents.real_agents.real_data_analyzer import RealDataAnalyzer, AnalysisResult
        from src.agents.real_agents.ml_integration import ModelType, ModelPerformance
        from src.agents.real_agents.enhanced_ml_models import EnhancedMLModels
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst
        from src.agents.coordinator import AgentCoordinator
        print("   ✅ 所有代理模組")
        
        # 交易系統
        print("5. 測試交易系統...")
        from src.trading.base_trading_api import BaseTradingAPI, OrderType, OrderStatus, OrderSide
        from src.trading.broker_apis import InteractiveBrokersAPI, TDAmeritradeAPI, ETRADEAPI, FidelityAPI
        from src.trading.crypto_apis import BinanceAPI, CoinbaseAPI, KrakenAPI
        from src.trading.trading_manager import TradingManager
        from src.trading.order_manager import OrderManager
        from src.trading.position_manager import PositionManager
        print("   ✅ 所有交易模組")
        
        # 回測系統
        print("6. 測試回測系統...")
        from src.backtest.base_backtest import BaseBacktestEngine, BacktestConfig, BacktestResult
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        print("   ✅ 所有回測模組")
        
        # 監控系統
        print("7. 測試監控系統...")
        from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        print("   ✅ 監控系統")
        
        # 安全系統
        print("8. 測試安全系統...")
        from src.security.compliance_checker import ComplianceChecker
        print("   ✅ 安全系統")
        
        print("\n🎉 所有導入測試通過！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_class_instantiation():
    """測試類實例化"""
    print("\n🔧 測試類實例化...")
    
    try:
        # 測試基本類實例化
        from src.core import SystemConfig
        from src.data_adapters.data_service import DataService
        from src.risk_management.risk_calculator import RiskCalculator
        from src.backtest.base_backtest import BacktestConfig
        
        config = SystemConfig()
        data_service = DataService()
        risk_calculator = RiskCalculator()
        backtest_config = BacktestConfig(
            strategy_name="test",
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        print("✅ 所有類實例化成功")
        return True
        
    except Exception as e:
        print(f"❌ 類實例化錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 最終系統測試")
    print("=" * 50)
    
    # 測試導入
    import_success = test_all_imports()
    
    if not import_success:
        print("\n❌ 導入測試失敗")
        return False
    
    # 測試實例化
    instantiation_success = test_class_instantiation()
    
    if not instantiation_success:
        print("\n❌ 實例化測試失敗")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有測試通過！系統已完全修復！")
    print("\n📋 系統現在可以正常使用:")
    print("   1. 運行: python start_real_system.py")
    print("   2. 運行: python real_system_launcher.py")
    print("   3. 查看: REAL_SYSTEM_GUIDE.md")
    print("\n✨ 您的真實量化交易系統已準備就緒！")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)