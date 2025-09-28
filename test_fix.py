#!/usr/bin/env python3
"""
測試修復 - 驗證導入問題是否解決
"""

def test_risk_management_import():
    """測試風險管理模組導入"""
    try:
        print("🔍 測試風險管理模組導入...")
        from src.risk_management import RiskCalculator, RiskMetrics, RiskLimits
        print("✅ RiskCalculator, RiskMetrics, RiskLimits 導入成功")
        return True
    except ImportError as e:
        print(f"❌ 風險管理導入錯誤: {e}")
        return False

def test_enhanced_quantitative_analyst():
    """測試增強型量化分析師導入"""
    try:
        print("🔍 測試增強型量化分析師導入...")
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst
        print("✅ EnhancedQuantitativeAnalyst 導入成功")
        return True
    except ImportError as e:
        print(f"❌ 增強型量化分析師導入錯誤: {e}")
        return False

def test_all_components():
    """測試所有組件"""
    print("🚀 測試所有組件導入...")
    
    tests = [
        ("核心模組", lambda: __import__('src.core', fromlist=['SystemConfig'])),
        ("數據服務", lambda: __import__('src.data_adapters.data_service', fromlist=['DataService'])),
        ("HTTP API適配器", lambda: __import__('src.data_adapters.http_api_adapter', fromlist=['HttpApiDataAdapter'])),
        ("風險管理", test_risk_management_import),
        ("增強型量化分析師", test_enhanced_quantitative_analyst),
        ("回測引擎", lambda: __import__('src.backtest.base_backtest', fromlist=['BaseBacktestEngine'])),
        ("增強回測引擎", lambda: __import__('src.backtest.enhanced_backtest_engine', fromlist=['EnhancedBacktestEngine'])),
        ("監控系統", lambda: __import__('src.monitoring.enhanced_monitoring', fromlist=['EnhancedMonitoringSystem'])),
        ("合規檢查", lambda: __import__('src.security.compliance_checker', fromlist=['ComplianceChecker'])),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
    
    print(f"\n📊 測試結果: {success_count}/{total_tests} 通過")
    return success_count == total_tests

if __name__ == "__main__":
    print("🔧 測試修復結果")
    print("=" * 40)
    
    success = test_all_components()
    
    if success:
        print("\n🎉 所有測試通過！系統已修復！")
        print("✅ 現在可以運行:")
        print("   python start_real_system.py")
    else:
        print("\n❌ 還有問題需要修復")