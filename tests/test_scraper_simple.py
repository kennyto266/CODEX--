"""
Simple scraper integration test (English output only)
"""

import asyncio
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data_adapters.alternative_data_service import AlternativeDataService
from src.data_adapters.hkex_data_collector import HKEXDataCollector
from src.data_adapters.gov_data_collector import GovDataCollector
from src.data_adapters.kaggle_data_collector import KaggleDataCollector


async def test_hkex_scraper():
    """Test HKEX scraper"""
    print("\n" + "="*60)
    print("Testing HKEX Data Collector")
    print("="*60)

    collector = HKEXDataCollector(mode="mock")

    try:
        connected = await collector.connect()
        print(f"[OK] Connected: {connected}")

        indicators = await collector.list_indicators()
        print(f"[OK] Indicators: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"     - {ind}")

        print("\n[Fetching Data]")
        data = await collector.fetch_data(
            "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"[OK] Rows: {len(data)}")
        print(f"[OK] Columns: {list(data.columns)}")
        print(f"[OK] First row:")
        print(data.head(1))

        print("\n[Real-time Data]")
        realtime = await collector.get_realtime_data("hsi_implied_volatility")
        print(f"[OK] IV: {realtime['value']:.2f}%")

        print("\n[Health Check]")
        health = await collector.health_check()
        print(f"[OK] Status: {health['status']}")
        print(f"[OK] Connected: {health['is_connected']}")
        print(f"[OK] Cache size: {health['cache_size']}")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gov_scraper():
    """Test Government data scraper"""
    print("\n" + "="*60)
    print("Testing Government Data Collector")
    print("="*60)

    collector = GovDataCollector(mode="mock")

    try:
        connected = await collector.connect()
        print(f"[OK] Connected: {connected}")

        indicators = await collector.list_indicators()
        print(f"[OK] Indicators: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"     - {ind}")

        print("\n[Fetching HIBOR Data]")
        hibor_data = await collector.fetch_data(
            "hibor_3m", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"[OK] Rows: {len(hibor_data)}")
        print(f"[OK] Average Rate: {hibor_data['value'].mean():.3f}%")

        print("\n[Fetching Visitor Data]")
        visitor_data = await collector.fetch_data(
            "visitor_arrivals_total", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"[OK] Rows: {len(visitor_data)}")
        print(f"[OK] Total Visitors: {visitor_data['value'].sum():,.0f}")

        print("\n[Real-time Data]")
        realtime = await collector.get_realtime_data("unemployment_rate")
        print(f"[OK] Unemployment Rate: {realtime['value']:.1f}%")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kaggle_scraper():
    """Test Kaggle scraper"""
    print("\n" + "="*60)
    print("Testing Kaggle Data Collector")
    print("="*60)

    collector = KaggleDataCollector(mode="mock")

    try:
        connected = await collector.connect()
        print(f"[OK] Connected: {connected}")

        indicators = await collector.list_indicators()
        print(f"[OK] Indicators: {len(indicators)}")
        for ind in indicators[:3]:
            print(f"     - {ind}")

        print("\n[Fetching GDP Data]")
        gdp_data = await collector.fetch_data(
            "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"[OK] Rows: {len(gdp_data)}")
        print(f"[OK] Average GDP: HKD {gdp_data['value'].mean():,.0f}")

        print("\n[Fetching HSI Data]")
        hsi_data = await collector.fetch_data(
            "hsi_historical", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"[OK] Rows: {len(hsi_data)}")
        print(f"[OK] Average Index: {hsi_data['value'].mean():.0f}")

        await collector.disconnect()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service():
    """Test service integration"""
    print("\n" + "="*60)
    print("Testing Alternative Data Service")
    print("="*60)

    service = AlternativeDataService()

    try:
        print("[Initializing Service]")
        initialized = await service.initialize(mode="mock")
        print(f"[OK] Initialized: {initialized}")

        print("\n[Adapter List]")
        adapters = await service.list_adapters()
        print(f"[OK] Available adapters: {adapters}")

        print("\n[Cross-adapter Data Fetching]")

        hkex_data = await service.get_data(
            "hkex", "hsi_futures_volume", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"[OK] HKEX data rows: {len(hkex_data)}")

        gov_data = await service.get_data(
            "government", "hibor_overnight", date(2024, 1, 1), date(2024, 1, 31)
        )
        print(f"[OK] Gov data rows: {len(gov_data)}")

        kg_data = await service.get_data(
            "kaggle", "hong_kong_gdp", date(2024, 1, 1), date(2024, 12, 31)
        )
        print(f"[OK] Kaggle data rows: {len(kg_data)}")

        print("\n[Overall Health Check]")
        health = await service.health_check()
        print(f"[OK] Overall Status: {health['overall_status']}")
        print(f"[OK] Active Adapters: {len(health['adapters'])}")

        for adapter_name, status in health['adapters'].items():
            print(f"     - {adapter_name}: {status.get('status', 'unknown')}")

        await service.cleanup()
        print(f"\n[OK] Service cleanup completed")
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Scraper Integration Test")
    print("="*60)

    results = {
        "HKEX Collector": await test_hkex_scraper(),
        "Government Collector": await test_gov_scraper(),
        "Kaggle Collector": await test_kaggle_scraper(),
        "Data Service": await test_service(),
    }

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:.<40} {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nOverall: {passed}/{total} passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Scraper functionality works correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
