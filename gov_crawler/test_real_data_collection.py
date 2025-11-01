#!/usr/bin/env python3
"""
真實數據收集測試腳本
測試確保所有數據都是真實的，絕對不使用 mock 數據
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加適配器路徑
sys.path.append(str(Path(__file__).parent / 'adapters' / 'real_data'))

from collect_real_data_only import RealDataOnlyCollector

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_real_data_warning():
    """打印真實數據警告"""
    print("\n" + "=" * 80)
    print("🔴 真實數據收集測試")
    print("=" * 80)
    print("⚠️  此測試將從真實數據源收集數據")
    print("🚫 絕不使用 mock 數據")
    print("✅ 所有數據必須來自官方 API 或網站")
    print("=" * 80 + "\n")

async def test_hibor_adapter():
    """測試 HKMA HIBOR 適配器"""
    print("正在測試 HKMA HIBOR 適配器...")

    from hibor.hkma_hibor_adapter import HKMAHiborAdapter

    adapter = HKMAHiborAdapter()
    print(f"✓ 創建 {adapter.name} 適配器")

    # 測試數據源信息
    info = adapter.get_data_source_info()
    print(f"✓ 數據源: {info['source']}")
    print(f"✓ 僅真實數據: {info['data_type']}")
    print(f"✓ Mock 禁用: {not info['mock_enabled']}")

    # 測試連接
    async with adapter:
        connected = await adapter.test_connection()
        print(f"✓ 連接狀態: {'成功' if connected else '失敗'}")

        # 測試數據描述
        desc = adapter.get_data_description()
        print(f"✓ 支持期限: {desc['supported_maturities']}")

    print("✅ HKMA HIBOR 適配器測試完成\n")

async def test_csd_adapter():
    """測試 C&SD 經濟數據適配器"""
    print("正在測試 C&SD 經濟數據適配器...")

    from economic.csd_economic_adapter import CSDEconomicAdapter

    adapter = CSDEconomicAdapter()
    print(f"✓ 創建 {adapter.name} 適配器")

    # 測試數據源信息
    info = adapter.get_data_source_info()
    print(f"✓ 數據源: {info['source']}")
    print(f"✓ 僅真實數據: {info['data_type']}")
    print(f"✓ Mock 禁用: {not info['mock_enabled']}")

    # 測試連接
    async with adapter:
        connected = await adapter.test_connection()
        print(f"✓ 連接狀態: {'成功' if connected else '失敗'}")

        # 測試支持的指標
        indicators = adapter.get_supported_indicators()
        print(f"✓ 支持指標: {indicators}")

    print("✅ C&SD 經濟數據適配器測試完成\n")

async def test_full_collection():
    """測試完整收集流程"""
    print("正在測試完整真實數據收集流程...")

    collector = RealDataOnlyCollector()
    print(f"✓ 創建真實數據收集器")
    print(f"✓ 初始化 {len(collector.adapters)} 個適配器")

    # 收集今天和昨天的數據
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"✓ 設置收集時間範圍: {start_date} 到 {end_date}")

    # 禁用 mock 數據模式
    collector.disable_mock_data_mode()
    print("✓ Mock 數據模式已禁用")

    # 收集數據
    results = await collector.collect_all_real_data(start_date, end_date)

    # 驗證結果
    validation_passed = await collector.validate_real_data_only(results)

    if validation_passed:
        print("✅ 數據驗證通過 - 所有數據均為真實數據")
    else:
        print("❌ 數據驗證失敗 - 可能存在 mock 數據")

    print(f"✓ 成功收集: {results['successful_collections']}/{len(collector.adapters)}")
    print(f"✓ 真實數據記錄: {results['real_data_confirmed']}")
    print(f"✓ 拒絕 mock 數據: {results['mock_data_rejected']}")

    # 生成報告
    report_text = collector.generate_collection_report(results)
    print("\n" + report_text)

    print("✅ 完整收集流程測試完成\n")

async def test_mock_data_rejection():
    """測試 mock 數據拒絕機制"""
    print("正在測試 mock 數據拒絕機制...")

    from base_real_adapter import RealDataAdapter, MockDataError
    import pandas as pd

    # 創建一個假的適配器來測試
    class TestAdapter(RealDataAdapter):
        def __init__(self):
            super().__init__("Test Adapter", "http://test.com")

        async def fetch_real_data(self, start_date, end_date):
            # 返回包含 mock 標記的數據
            df = pd.DataFrame({
                'date': pd.date_range('2023-01-01', '2023-01-05'),
                'value': [1, 2, 3, 4, 5],
                'is_mock': [True, True, True, True, True]  # 明確標記為 mock
            })
            return df

    adapter = TestAdapter()
    print("✓ 創建測試適配器（包含 mock 數據）")

    try:
        async with adapter:
            df = await adapter.fetch_real_data('2023-01-01', '2023-01-05')

            # 嘗試驗證數據
            is_real = await adapter.validate_data_is_real(df)

            if not is_real:
                print("✅ 成功檢測並拒絕 mock 數據")
            else:
                print("❌ 未能檢測 mock 數據")

    except MockDataError as e:
        print(f"✅ Mock 數據錯誤被正確拋出: {str(e)}")

    print("✅ Mock 數據拒絕機制測試完成\n")

async def main():
    """主測試函數"""
    print_real_data_warning()

    tests = [
        ("HKMA HIBOR 適配器", test_hibor_adapter),
        ("C&SD 經濟數據適配器", test_csd_adapter),
        ("完整收集流程", test_full_collection),
        ("Mock 數據拒絕", test_mock_data_rejection),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🧪 執行測試: {test_name}")
        print("-" * 80)
        try:
            await test_func()
            passed += 1
            print(f"✅ 測試通過: {test_name}\n")
        except Exception as e:
            failed += 1
            print(f"❌ 測試失敗: {test_name}")
            print(f"   錯誤: {str(e)}\n")

    print("=" * 80)
    print("測試結果總結")
    print("=" * 80)
    print(f"✅ 通過: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📊 成功率: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 所有測試通過！真實數據收集系統工作正常")
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗，請檢查配置")

    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
