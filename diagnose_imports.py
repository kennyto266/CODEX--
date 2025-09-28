#!/usr/bin/env python3
"""
診斷導入問題
"""

import sys
import traceback

def test_import(module_name, description):
    """測試單個導入"""
    try:
        print(f"🔍 測試 {description}...")
        exec(f"import {module_name}")
        print(f"✅ {description} 導入成功")
        return True
    except ImportError as e:
        print(f"❌ {description} 導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ {description} 其他錯誤: {e}")
        traceback.print_exc()
        return False

def main():
    """主診斷函數"""
    print("🔧 診斷導入問題")
    print("=" * 50)
    
    tests = [
        ("src.core", "核心模組"),
        ("src.data_adapters.data_service", "數據服務"),
        ("src.data_adapters.http_api_adapter", "HTTP API適配器"),
        ("src.data_adapters.yahoo_finance_adapter", "Yahoo Finance適配器"),
        ("src.data_adapters.alpha_vantage_adapter", "Alpha Vantage適配器"),
        ("src.data_adapters.ccxt_crypto_adapter", "CCXT加密貨幣適配器"),
        ("src.agents.real_agents.base_real_agent", "基礎真實代理"),
        ("src.agents.real_agents.real_data_analyzer", "真實數據分析器"),
        ("src.agents.real_agents.ml_integration", "機器學習集成"),
        ("src.agents.real_agents.enhanced_ml_models", "增強ML模型"),
        ("src.agents.real_agents.enhanced_quantitative_analyst", "增強型量化分析師"),
        ("src.trading.base_trading_api", "基礎交易API"),
        ("src.trading.broker_apis", "經紀商API"),
        ("src.risk_management.risk_calculator", "風險計算器"),
        ("src.backtest.base_backtest", "基礎回測"),
        ("src.backtest.enhanced_backtest_engine", "增強回測引擎"),
        ("src.monitoring.enhanced_monitoring", "增強監控"),
        ("src.security.compliance_checker", "合規檢查器"),
        ("src.agents.coordinator", "代理協調器"),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for module_name, description in tests:
        if test_import(module_name, description):
            success_count += 1
        print()
    
    print("=" * 50)
    print(f"📊 診斷結果: {success_count}/{total_tests} 通過")
    
    if success_count == total_tests:
        print("🎉 所有導入都正常！系統可以正常使用！")
        return True
    else:
        print("❌ 還有導入問題需要修復")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)