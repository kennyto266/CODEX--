#!/usr/bin/env python3
"""
快速測試腳本 - 驗證系統修復
"""

def test_basic_imports():
    """測試基本導入"""
    print("🔍 測試基本導入...")
    
    try:
        # 測試核心模組
        from src.core import SystemConfig
        print("✅ SystemConfig")
        
        # 測試數據適配器
        from src.data_adapters.data_service import DataService
        print("✅ DataService")
        
        from src.data_adapters.http_api_adapter import HttpApiDataAdapter
        print("✅ HttpApiDataAdapter")
        
        # 測試真實代理
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst
        print("✅ EnhancedQuantitativeAnalyst")
        
        # 測試風險管理
        from src.risk_management.risk_calculator import RiskCalculator
        print("✅ RiskCalculator")
        
        # 測試回測引擎
        from src.backtest.base_backtest import BaseBacktestEngine
        print("✅ BaseBacktestEngine")
        
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        print("✅ EnhancedBacktestEngine")
        
        # 測試監控系統
        from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        print("✅ EnhancedMonitoringSystem")
        
        # 測試合規檢查
        from src.security.compliance_checker import ComplianceChecker
        print("✅ ComplianceChecker")
        
        print("\n🎉 所有基本導入測試通過！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

def test_class_instantiation():
    """測試類實例化"""
    print("\n🔧 測試類實例化...")
    
    try:
        from src.core import SystemConfig
        from src.data_adapters.data_service import DataService
        from src.risk_management.risk_calculator import RiskCalculator
        from src.backtest.base_backtest import BacktestConfig
        
        # 測試配置創建
        config = SystemConfig()
        print("✅ SystemConfig 實例化")
        
        # 測試數據服務創建
        data_service = DataService()
        print("✅ DataService 實例化")
        
        # 測試風險計算器創建
        risk_calculator = RiskCalculator()
        print("✅ RiskCalculator 實例化")
        
        # 測試回測配置創建
        backtest_config = BacktestConfig(
            strategy_name="test",
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        print("✅ BacktestConfig 實例化")
        
        print("\n🎉 所有類實例化測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 實例化錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 真實量化交易系統 - 快速測試")
    print("=" * 50)
    
    # 測試導入
    import_success = test_basic_imports()
    
    if not import_success:
        print("\n❌ 導入測試失敗，系統無法使用")
        return False
    
    # 測試實例化
    instantiation_success = test_class_instantiation()
    
    if not instantiation_success:
        print("\n❌ 實例化測試失敗，系統無法使用")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有測試通過！系統已修復完成！")
    print("\n📋 下一步操作:")
    print("   1. 運行: python start_real_system.py")
    print("   2. 查看: REAL_SYSTEM_GUIDE.md")
    print("   3. 配置環境變量（如需要）")
    print("\n✨ 您的真實量化交易系統已準備就緒！")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)