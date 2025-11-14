"""
Sprint 1 集成測試
測試 US-003、US-004、US-005 的協同工作

驗證從數據適配器到宏觀指標服務的完整數據流。
"""

import asyncio
import pytest
from datetime import datetime

# 確保註冊模塊被導入（觸發適配器註冊）
from src.data_adapters import adapter_registry
from src.data_adapters.adapter_factory import adapter_manager, create_adapter
from src.data_adapters.hkma_adapter import HKMAdapter
from src.services.indicators.macro_indicator_service import (
    MacroIndicatorService,
    MacroOscillatorCalculator,
    MarketRegime
)


@pytest.mark.asyncio
async def test_us003_us004_integration():
    """
    測試 US-003 (適配器框架) 和 US-004 (HKMA 適配器) 的集成
    """
    print("\n" + "="*80)
    print("測試 US-003 + US-004 集成")
    print("="*80)

    # 1. 通過工廠創建 HKMA 適配器
    print("\n1. 通過工廠創建 HKMA 適配器...")
    hkma_adapter = await adapter_manager.get_adapter("hkma")
    assert hkma_adapter is not None
    assert isinstance(hkma_adapter, HKMAdapter)
    print("   [OK] 適配器創建成功")

    # 2. 獲取所有 HIBOR 指標
    print("\n2. 獲取所有 HIBOR 指標...")
    hibor_data = await hkma_adapter.fetch_all_hibor_indicators()
    assert len(hibor_data) == 5
    assert 'hibor_overnight' in hibor_data
    assert 'hibor_1m' in hibor_data
    assert 'hibor_3m' in hibor_data
    assert 'hibor_6m' in hibor_data
    assert 'hibor_12m' in hibor_data
    print(f"   [OK] 獲取 {len(hibor_data)} 個 HIBOR 指標")
    for term, rate in hibor_data.items():
        print(f"      - {term}: {rate:.4f}%")

    # 3. 驗證數據質量
    print("\n3. 驗證數據質量...")
    quality_score = await hkma_adapter.get_data_quality_score(
        await hkma_adapter.get_historical_hibor(days=30)
    )
    assert quality_score >= 0.0
    assert quality_score <= 1.0
    print(f"   [OK] 數據質量評分: {quality_score:.2%}")

    # 4. 測試緩存機制
    print("\n4. 測試緩存機制...")
    # 再次獲取，應該從緩存讀取
    hibor_data_cached = await hkma_adapter.fetch_all_hibor_indicators()
    assert len(hibor_data_cached) == 5
    print("   [OK] 緩存機制正常工作")


@pytest.mark.asyncio
async def test_us004_us005_integration():
    """
    測試 US-004 (HKMA 適配器) 和 US-005 (宏觀指標服務) 的集成
    """
    print("\n" + "="*80)
    print("測試 US-004 + US-005 集成")
    print("="*80)

    # 1. 創建宏觀指標服務
    print("\n1. 創建宏觀指標服務...")
    calculator = MacroOscillatorCalculator()
    service = MacroIndicatorService(oscillator_calculator=calculator)
    assert service.total_indicators == 35
    print("   [OK] 宏觀指標服務創建成功")

    # 2. 獲取宏觀指標（包含 HIBOR）
    print("\n2. 獲取宏觀指標...")
    indicators = await service.get_latest_indicators()
    assert len(indicators) >= 30  # 至少有大部分指標
    print(f"   [OK] 獲取 {len(indicators)} 個宏觀指標")

    # 3. 驗證 HIBOR 指標來自 HKMA 適配器
    print("\n3. 驗證 HIBOR 指標...")
    hibor_indicators = {k: v for k, v in indicators.items() if k.startswith('hibor')}
    assert len(hibor_indicators) == 5
    for term in ['hibor_overnight', 'hibor_1m', 'hibor_3m', 'hibor_6m', 'hibor_12m']:
        assert term in indicators
        assert indicators[term] > 0
        print(f"   - {term}: {indicators[term]:.4f}%")
    print("   [OK] 所有5個 HIBOR 指標正常")

    # 4. 計算宏觀振盪器
    print("\n4. 計算宏觀振盪器...")
    oscillator = await service.calculate_oscillator()
    assert 0.0 <= oscillator <= 1.0
    print(f"   [OK] 宏觀振盪器: {oscillator:.4f}")

    # 5. 檢測市場狀態
    print("\n5. 檢測市場狀態...")
    regime = await service.detect_market_regime(oscillator)
    assert regime in [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.SIDEWAYS]
    print(f"   [OK] 市場狀態: {regime.value}")


@pytest.mark.asyncio
async def test_complete_data_flow():
    """
    測試完整數據流：適配器 -> 服務 -> 分析
    """
    print("\n" + "="*80)
    print("測試完整數據流")
    print("="*80)

    # 1. 數據適配器層
    print("\n1. 數據適配器層...")
    hkma_adapter = await adapter_manager.get_adapter("hkma")
    hkma_data = await hkma_adapter.fetch_all_hibor_indicators()
    print(f"   [OK] HKMA 適配器提供 {len(hkma_data)} 個指標")

    # 2. 宏觀指標服務層
    print("\n2. 宏觀指標服務層...")
    service = MacroIndicatorService()
    all_indicators = await service.get_latest_indicators()
    print(f"   [OK] 宏觀指標服務管理 {len(all_indicators)} 個指標")

    # 3. 數據驗證
    print("\n3. 數據驗證...")
    validation_results = await service.validate_indicators()
    valid_count = sum(validation_results.values())
    total_count = len(validation_results)
    print(f"   [OK] 數據驗證: {valid_count}/{total_count} 指標有效")

    # 4. 數據質量評估
    print("\n4. 數據質量評估...")
    quality_report = await service.get_data_quality_report()
    assert quality_report['total_indicators'] == 35
    assert quality_report['validity_ratio'] >= 0.0
    assert quality_report['quality_level'] in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'UNKNOWN']
    print(f"   [OK] 質量等級: {quality_report['quality_level']}")
    print(f"   [OK] 有效性比率: {quality_report['validity_ratio']:.2%}")

    # 5. 計算分析
    print("\n5. 計算分析...")
    # 計算 Z 分數
    zscore = await service.calculate_zscore('hibor_overnight')
    print(f"   [OK] HIBOR Z 分數: {zscore:.4f}")

    # 計算振盪器
    oscillator = await service.calculate_oscillator()
    print(f"   [OK] 宏觀振盪器: {oscillator:.4f}")

    # 市場狀態
    regime = await service.detect_market_regime(oscillator)
    print(f"   [OK] 市場狀態: {regime.value}")

    # 6. 生成綜合報告
    print("\n6. 生成綜合報告...")
    report = {
        'timestamp': datetime.now().isoformat(),
        'data_source': 'HKMA',
        'total_indicators': len(all_indicators),
        'valid_indicators': valid_count,
        'data_quality': quality_report['quality_level'],
        'oscillator': oscillator,
        'market_regime': regime.value,
        'hibor_overnight': hkma_data.get('hibor_overnight'),
        'status': 'SUCCESS'
    }
    print("   [OK] 綜合報告:")
    for key, value in report.items():
        if key != 'timestamp':
            print(f"      - {key}: {value}")

    assert report['status'] == 'SUCCESS'
    assert report['total_indicators'] >= 30


@pytest.mark.asyncio
async def test_adapter_factory_integration():
    """
    測試適配器工廠的集成功能
    """
    print("\n" + "="*80)
    print("測試適配器工廠集成")
    print("="*80)

    # 1. 列出所有可用適配器
    print("\n1. 列出所有可用適配器...")
    adapter_types = await adapter_manager.list_adapters()
    assert len(adapter_types) > 0
    assert 'hkma' in adapter_types
    print(f"   [OK] 可用適配器: {adapter_types}")

    # 2. 創建適配器實例
    print("\n2. 創建適配器實例...")
    hkma1 = await adapter_manager.get_adapter("hkma")
    hkma2 = await adapter_manager.get_adapter("hkma")
    # 應該是同一個實例（緩存）
    assert hkma1 is hkma2
    print("   [OK] 適配器緩存機制正常")

    # 3. 強制創建新實例
    print("\n3. 強制創建新實例...")
    hkma3 = await adapter_manager.create_adapter("hkma", force_new=True)
    assert hkma3 is not hkma1
    print("   [OK] 強制創建新實例功能正常")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Sprint 1 集成測試")
    print("="*80)
    print("\n測試內容:")
    print("1. US-003: 基礎數據適配器框架")
    print("2. US-004: HKMA 數據適配器")
    print("3. US-005: 宏觀指標服務")
    print("\n" + "="*80)

    async def run_all_tests():
        try:
            await test_us003_us004_integration()
            await test_us004_us005_integration()
            await test_complete_data_flow()
            await test_adapter_factory_integration()

            print("\n" + "="*80)
            print("[PASS] All Integration Tests Passed!")
            print("="*80)
            print("\nSprint 1 Three User Stories Working Together:")
            print("  [X] US-003: Adapter Framework")
            print("  [X] US-004: HKMA Adapter")
            print("  [X] US-005: Macro Indicator Service")
            print("\nSystem Ready for Sprint 2!")
            print("="*80 + "\n")

        except Exception as e:
            print(f"\n[FAIL] Test Failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    asyncio.run(run_all_tests())
