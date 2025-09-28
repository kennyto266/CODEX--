#!/usr/bin/env python3
"""
測試導入修復
"""

def test_imports():
    """測試所有關鍵導入"""
    try:
        print("🔍 測試導入修復...")
        
        # 測試基礎導入
        print("1. 測試基礎模組...")
        from src.core import SystemConfig
        print("   ✅ SystemConfig 導入成功")
        
        # 測試數據適配器
        print("2. 測試數據適配器...")
        from src.data_adapters.data_service import DataService
        print("   ✅ DataService 導入成功")
        
        from src.data_adapters.http_api_adapter import HttpApiDataAdapter
        print("   ✅ HttpApiDataAdapter 導入成功")
        
        from src.data_adapters.yahoo_finance_adapter import YahooFinanceAdapter
        print("   ✅ YahooFinanceAdapter 導入成功")
        
        from src.data_adapters.alpha_vantage_adapter import AlphaVantageAdapter
        print("   ✅ AlphaVantageAdapter 導入成功")
        
        from src.data_adapters.ccxt_crypto_adapter import CCXTCryptoAdapter
        print("   ✅ CCXTCryptoAdapter 導入成功")
        
        # 測試真實代理
        print("3. 測試真實代理...")
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst
        print("   ✅ EnhancedQuantitativeAnalyst 導入成功")
        
        from src.agents.real_agents.enhanced_ml_models import EnhancedMLModels
        print("   ✅ EnhancedMLModels 導入成功")
        
        # 測試交易API
        print("4. 測試交易API...")
        from src.trading.broker_apis import InteractiveBrokersAPI, TDAmeritradeAPI
        print("   ✅ Trading APIs 導入成功")
        
        # 測試風險管理
        print("5. 測試風險管理...")
        from src.risk_management.risk_calculator import RiskCalculator
        print("   ✅ RiskCalculator 導入成功")
        
        # 測試回測引擎
        print("6. 測試回測引擎...")
        from src.backtest.base_backtest import BaseBacktestEngine, BacktestConfig
        print("   ✅ BaseBacktestEngine 導入成功")
        
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        print("   ✅ EnhancedBacktestEngine 導入成功")
        
        # 測試監控系統
        print("7. 測試監控系統...")
        from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        print("   ✅ EnhancedMonitoringSystem 導入成功")
        
        # 測試合規檢查
        print("8. 測試合規檢查...")
        from src.security.compliance_checker import ComplianceChecker
        print("   ✅ ComplianceChecker 導入成功")
        
        # 測試代理協調器
        print("9. 測試代理協調器...")
        from src.agents.coordinator import AgentCoordinator
        print("   ✅ AgentCoordinator 導入成功")
        
        print("\n🎉 所有導入測試通過！系統已修復完成！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ 系統可以正常使用了！")
        print("📋 下一步:")
        print("   1. 運行 python real_system_launcher.py 啟動真實系統")
        print("   2. 查看 REAL_SYSTEM_GUIDE.md 了解詳細使用方法")
        print("   3. 配置環境變量（如需要）")
    else:
        print("\n❌ 還有導入問題需要修復")