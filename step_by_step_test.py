#!/usr/bin/env python3
"""
逐步測試導入問題
"""

def test_step_by_step():
    """逐步測試每個導入"""
    print("🔍 逐步測試導入...")
    
    # 步驟1: 測試核心模組
    try:
        print("1. 測試核心模組...")
        from src.core import SystemConfig
        print("   ✅ SystemConfig 導入成功")
    except Exception as e:
        print(f"   ❌ SystemConfig 導入失敗: {e}")
        return False
    
    # 步驟2: 測試數據適配器
    try:
        print("2. 測試數據適配器...")
        from src.data_adapters.data_service import DataService
        print("   ✅ DataService 導入成功")
    except Exception as e:
        print(f"   ❌ DataService 導入失敗: {e}")
        return False
    
    try:
        from src.data_adapters.http_api_adapter import HttpApiDataAdapter
        print("   ✅ HttpApiDataAdapter 導入成功")
    except Exception as e:
        print(f"   ❌ HttpApiDataAdapter 導入失敗: {e}")
        return False
    
    # 步驟3: 測試風險管理
    try:
        print("3. 測試風險管理...")
        from src.risk_management.risk_calculator import RiskCalculator, RiskMetrics, RiskLimits
        print("   ✅ RiskCalculator 導入成功")
    except Exception as e:
        print(f"   ❌ RiskCalculator 導入失敗: {e}")
        return False
    
    # 步驟4: 測試基礎代理
    try:
        print("4. 測試基礎代理...")
        from src.agents.base_agent import BaseAgent
        print("   ✅ BaseAgent 導入成功")
    except Exception as e:
        print(f"   ❌ BaseAgent 導入失敗: {e}")
        return False
    
    # 步驟5: 測試真實代理基礎類
    try:
        print("5. 測試真實代理基礎類...")
        from src.agents.real_agents.base_real_agent import BaseRealAgent, RealAgentConfig
        print("   ✅ BaseRealAgent 導入成功")
    except Exception as e:
        print(f"   ❌ BaseRealAgent 導入失敗: {e}")
        return False
    
    # 步驟6: 測試數據分析器
    try:
        print("6. 測試數據分析器...")
        from src.agents.real_agents.real_data_analyzer import RealDataAnalyzer, AnalysisResult
        print("   ✅ RealDataAnalyzer 導入成功")
    except Exception as e:
        print(f"   ❌ RealDataAnalyzer 導入失敗: {e}")
        return False
    
    # 步驟7: 測試ML集成
    try:
        print("7. 測試ML集成...")
        from src.agents.real_agents.ml_integration import ModelType, ModelPerformance
        print("   ✅ ML Integration 導入成功")
    except Exception as e:
        print(f"   ❌ ML Integration 導入失敗: {e}")
        return False
    
    # 步驟8: 測試增強ML模型
    try:
        print("8. 測試增強ML模型...")
        from src.agents.real_agents.enhanced_ml_models import EnhancedMLModels
        print("   ✅ EnhancedMLModels 導入成功")
    except Exception as e:
        print(f"   ❌ EnhancedMLModels 導入失敗: {e}")
        return False
    
    # 步驟9: 測試增強型量化分析師
    try:
        print("9. 測試增強型量化分析師...")
        from src.agents.real_agents.enhanced_quantitative_analyst import EnhancedQuantitativeAnalyst
        print("   ✅ EnhancedQuantitativeAnalyst 導入成功")
    except Exception as e:
        print(f"   ❌ EnhancedQuantitativeAnalyst 導入失敗: {e}")
        return False
    
    # 步驟10: 測試其他組件
    try:
        print("10. 測試其他組件...")
        from src.backtest.base_backtest import BaseBacktestEngine
        from src.backtest.enhanced_backtest_engine import EnhancedBacktestEngine
        from src.monitoring.enhanced_monitoring import EnhancedMonitoringSystem
        from src.security.compliance_checker import ComplianceChecker
        print("   ✅ 其他組件導入成功")
    except Exception as e:
        print(f"   ❌ 其他組件導入失敗: {e}")
        return False
    
    print("\n🎉 所有導入測試通過！")
    return True

if __name__ == "__main__":
    print("🚀 逐步導入測試")
    print("=" * 40)
    
    success = test_step_by_step()
    
    if success:
        print("\n✅ 系統導入問題已修復！")
        print("📋 下一步:")
        print("   1. 運行 python start_real_system.py")
        print("   2. 查看 REAL_SYSTEM_GUIDE.md")
    else:
        print("\n❌ 還有導入問題需要修復")