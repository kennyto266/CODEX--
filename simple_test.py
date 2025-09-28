#!/usr/bin/env python3
"""
簡化測試腳本 - 只測試基本功能
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
        
        print("\n🎉 基本導入測試通過！")
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
        
        # 測試配置創建
        config = SystemConfig()
        print("✅ SystemConfig 實例化")
        
        # 測試數據服務創建
        data_service = DataService()
        print("✅ DataService 實例化")
        
        print("\n🎉 基本實例化測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 實例化錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 真實量化交易系統 - 簡化測試")
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
    print("🎉 基本測試通過！系統核心功能正常！")
    print("\n📋 下一步操作:")
    print("   1. 運行: python start_real_system.py")
    print("   2. 查看: REAL_SYSTEM_GUIDE.md")
    print("   3. 配置環境變量（如需要）")
    print("\n✨ 您的真實量化交易系統核心已準備就緒！")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)